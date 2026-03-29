"""Runtime model loading and prediction services."""

from pharma_os.ml.inference.contracts import (
	EligibilityInferenceRequest,
	EligibilityInferenceResult,
	RecruitmentInferenceRequest,
	RecruitmentInferenceResult,
	SafetyInferenceRequest,
	SafetyInferenceResult,
)
from pharma_os.ml.inference.feature_prep import (
	prepare_eligibility_features_for_inference,
	prepare_recruitment_features_for_inference,
	prepare_safety_features_for_inference,
)
from pharma_os.ml.inference.orchestration import (
	run_all_inference_use_cases,
	run_eligibility_inference,
	run_recruitment_inference,
	run_safety_inference,
)
from pharma_os.ml.inference.reporting import persist_inference_summary

__all__ = [
	"EligibilityInferenceRequest",
	"SafetyInferenceRequest",
	"RecruitmentInferenceRequest",
	"EligibilityInferenceResult",
	"SafetyInferenceResult",
	"RecruitmentInferenceResult",
	"prepare_eligibility_features_for_inference",
	"prepare_safety_features_for_inference",
	"prepare_recruitment_features_for_inference",
	"run_eligibility_inference",
	"run_safety_inference",
	"run_recruitment_inference",
	"run_all_inference_use_cases",
	"persist_inference_summary",
]
