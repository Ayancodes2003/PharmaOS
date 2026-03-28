"""Pipeline domain configuration for ingestion, validation, and preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from pharma_os.pipelines.common.contracts import PipelineDomain
from pharma_os.pipelines.preprocessing.domains import (
    preprocess_adverse_events,
    preprocess_drug_exposures,
    preprocess_patients,
    preprocess_trials,
)
from pharma_os.pipelines.validation import (
    ADVERSE_EVENTS_VALIDATION_SPEC,
    DRUG_EXPOSURES_VALIDATION_SPEC,
    PATIENTS_VALIDATION_SPEC,
    TRIALS_VALIDATION_SPEC,
    ValidationSpec,
)


@dataclass(frozen=True)
class DomainPipelineConfig:
    """Configuration bundle for a domain pipeline."""

    domain: PipelineDomain
    validation_spec: ValidationSpec
    preprocessor: Callable[[pd.DataFrame], pd.DataFrame]


DOMAIN_PIPELINE_CONFIGS: dict[PipelineDomain, DomainPipelineConfig] = {
    PipelineDomain.PATIENTS: DomainPipelineConfig(
        domain=PipelineDomain.PATIENTS,
        validation_spec=PATIENTS_VALIDATION_SPEC,
        preprocessor=preprocess_patients,
    ),
    PipelineDomain.TRIALS: DomainPipelineConfig(
        domain=PipelineDomain.TRIALS,
        validation_spec=TRIALS_VALIDATION_SPEC,
        preprocessor=preprocess_trials,
    ),
    PipelineDomain.ADVERSE_EVENTS: DomainPipelineConfig(
        domain=PipelineDomain.ADVERSE_EVENTS,
        validation_spec=ADVERSE_EVENTS_VALIDATION_SPEC,
        preprocessor=preprocess_adverse_events,
    ),
    PipelineDomain.DRUG_EXPOSURES: DomainPipelineConfig(
        domain=PipelineDomain.DRUG_EXPOSURES,
        validation_spec=DRUG_EXPOSURES_VALIDATION_SPEC,
        preprocessor=preprocess_drug_exposures,
    ),
}

SUPPORTED_STRUCTURED_DOMAINS: tuple[PipelineDomain, ...] = (
    PipelineDomain.PATIENTS,
    PipelineDomain.TRIALS,
    PipelineDomain.ADVERSE_EVENTS,
    PipelineDomain.DRUG_EXPOSURES,
)
