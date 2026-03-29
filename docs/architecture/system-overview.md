# PHARMA-OS System Overview

## Purpose

This document explains how PHARMA-OS components fit together as a single backend platform, with emphasis on practical runtime behavior rather than theoretical architecture.

## Layered Module Map

- core:
  - settings, lifecycle orchestration, shared exception model
- db:
  - SQLAlchemy domain entities and repositories
  - Mongo collections for agent traces and unstructured operational memory
- pipelines:
  - structured ingestion and preprocessing flow
- features and analytics marts:
  - domain feature generation and BI-facing aggregated marts
- ml:
  - training orchestration, artifact registry, inference execution
- agents:
  - grounded workflows for eligibility, safety, and research reasoning
- api:
  - FastAPI v1 route layer exposing system, data, prediction, agent, and operations capabilities
- analytics exports:
  - grouped Power BI-ready tables and refresh manifests

## End-to-End Runtime Flow

1. Data ingestion/preprocessing writes standardized stage artifacts.
2. Feature and mart generation produces model-ready features and analyst-friendly aggregates.
3. Training pipelines create use-case model artifacts and metadata.
4. Inference pipelines load artifacts and persist predictions/rankings.
5. Agent requests call repository-backed tools, then model/provider execution, then trace persistence.
6. API routes expose operational capabilities and status surfaces.
7. Export runner materializes grouped BI datasets and run manifests.

## Persistence Model

- PostgreSQL:
  - patient, trial, adverse event, exposure, prediction, ranking, and audit entities
- MongoDB:
  - agent trace documents and flexible operational context

This split supports strict relational integrity for core clinical entities while preserving flexibility for agent and trace payloads.

## Operational Surfaces

- Health and readiness probes:
  - /api/v1/system/health
  - /api/v1/system/readiness
- Runtime smoke script:
  - scripts/run_runtime_smoke.py
- BI manifest retrieval surfaces:
  - /api/v1/operations/exports/manifests
  - /api/v1/operations/exports/manifests/{export_run_id}

## Artifact Contracts

- data/*:
  - staged and transformed datasets
- artifacts/models:
  - trained model outputs and registry pointers
- artifacts/reports:
  - phase-specific run summaries and manifests
- artifacts/exports:
  - BI table outputs grouped by reporting domain

## Design Choices

- Keep orchestration scriptable and explicit through scripts/* rather than hidden automation.
- Keep configuration centralized through typed settings and environment variables.
- Keep deployment simple with Docker Compose for local reproducibility.
- Keep BI usability explicit through flat export tables and manifest metadata.
