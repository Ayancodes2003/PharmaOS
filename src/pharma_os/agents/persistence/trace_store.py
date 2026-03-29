"""Agent trace persistence to MongoDB."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from pharma_os.agents.base import AgentResult, AgentTraceRecord, AgentTraceMetadata
from pharma_os.db.mongo_collections import get_agent_traces_collection

logger = logging.getLogger(__name__)


class TraceStore:
    """Stores and retrieves agent traces from MongoDB."""

    async def persist_trace(self, result: AgentResult) -> str | None:
        """Persist an agent trace to MongoDB.

        Args:
            result: AgentResult to persist

        Returns:
            Inserted document ID or None if persistence failed
        """
        try:
            trace_collection = get_agent_traces_collection()

            # Build metadata
            metadata = AgentTraceMetadata(
                agent_type=result.agent_type.value,
                agent_name=result.agent_type.value.replace("_", " ").title(),
                execution_time_ms=result.execution_time_ms,
                success=result.success,
                error=result.error,
                tool_calls_count=len(result.tool_calls_used),
            )

            # Build trace record
            trace_record = AgentTraceRecord(
                trace_id=result.trace_id,
                timestamp=datetime.utcnow(),
                metadata=metadata.dict(),
                request_type=result.agent_type.value,
                result_summary=str(result)[:500],  # Truncate for storage
                tool_calls=[{"tool_name": tc} for tc in result.tool_calls_used],
            )

            # Add full result if small enough
            try:
                result_dict = result.dict()
                if len(str(result_dict)) < 10000:  # Only persist if < 10KB
                    trace_record.full_result = result_dict
            except Exception:
                pass

            # Insert into MongoDB
            doc_result = await trace_collection.insert_one(trace_record.dict())

            logger.info(f"Persisted agent trace {result.trace_id}: {doc_result.inserted_id}")
            return str(doc_result.inserted_id)

        except Exception as e:
            logger.error(f"Error persisting trace: {e}")
            return None

    async def retrieve_trace(self, trace_id: str) -> dict[str, Any] | None:
        """Retrieve a trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            Trace document or None if not found
        """
        try:
            trace_collection = get_agent_traces_collection()
            trace = await trace_collection.find_one({"trace_id": trace_id})
            return trace
        except Exception as e:
            logger.error(f"Error retrieving trace: {e}")
            return None

    async def list_traces(
        self,
        agent_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List recent traces.

        Args:
            agent_type: Optional filter by agent type
            limit: Maximum number of traces to return

        Returns:
            List of trace documents
        """
        try:
            trace_collection = get_agent_traces_collection()

            query = {}
            if agent_type:
                query["metadata.agent_type"] = agent_type

            traces = await trace_collection.find(query).sort("timestamp", -1).limit(limit).to_list(length=limit)
            return traces
        except Exception as e:
            logger.error(f"Error listing traces: {e}")
            return []

    async def get_agent_statistics(self, agent_type: str | None = None) -> dict[str, Any]:
        """Get execution statistics for agents.

        Args:
            agent_type: Optional filter by agent type

        Returns:
            Statistics dictionary
        """
        try:
            trace_collection = get_agent_traces_collection()

            pipeline = []

            if agent_type:
                pipeline.append({"$match": {"metadata.agent_type": agent_type}})

            pipeline.extend([
                {
                    "$group": {
                        "_id": "$metadata.agent_type",
                        "total_executions": {"$sum": 1},
                        "success_count": {"$sum": {"$cond": ["$metadata.success", 1, 0]}},
                        "avg_execution_time": {"$avg": "$metadata.execution_time_ms"},
                        "total_tool_calls": {"$sum": "$metadata.tool_calls_count"},
                    }
                },
                {"$sort": {"total_executions": -1}},
            ])

            results = await trace_collection.aggregate(pipeline).to_list(length=None)
            return {result["_id"]: result for result in results}

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
