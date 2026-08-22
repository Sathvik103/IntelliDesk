import math
from typing import List, Dict, Any
from .interfaces import RankingModelInterface


class DeterministicWeightedRanker(RankingModelInterface):
    """
    TEMPORARY PLACEHOLDER RANKING IMPLEMENTATION
    ============================================

    This is a deterministic, hand-tuned weighted scoring component used during
    development while the external ML model (Random Forest, XGBoost, etc.) is
    being trained separately.

    This is NOT machine learning. It makes no statistical claims and does not
    learn from data. It exists purely so the assignment pipeline produces
    sensible results while the real ML model is being developed.

    When the external ML model is ready, it will implement RankingModelInterface
    and be injected via AssignmentService(ranking_model=ExternalMLModel()).
    No Django views, models, or APIs will need to change.

    Current Weight Distribution (Temporary — subject to change):
    ┌─────────────────────────────────────────┬────────┐
    │ Factor                                  │ Weight │
    ├─────────────────────────────────────────┼────────┤
    │ Geographic Proximity (Distance)         │   50%  │
    │ Workload & Bandwidth Availability       │   20%  │
    │ Domain Skill Proficiency (1–5)          │   15%  │
    │ Experience                              │    8%  │
    │ Historical Performance (Rating/Success) │    7%  │
    └─────────────────────────────────────────┴────────┘
    """

    def get_model_name(self) -> str:
        return "placeholder-deterministic-v2"

    def rank_candidates(self, candidates_features: List[Dict[str, Any]]) -> List[float]:
        scores = [self._compute_single_score(feat) for feat in candidates_features]
        return [round(s, 4) for s in scores]

    def _compute_single_score(self, feat: Dict[str, Any]) -> float:
        # ── 1. Distance Score (50%) ────────────────────────────────────────────
        # Exponential decay: 0 km → 1.0, 5 km → ~0.78, 10 km → ~0.61, 20 km → ~0.37
        # Using a gentler decay (lambda=0.05) so large distances still differentiate.
        dist_km = float(feat.get('distance_km', 1.0))
        distance_score = math.exp(-0.05 * max(0.0, dist_km))

        # ── 2. Workload Score (20%) ────────────────────────────────────────────
        # Employees with less current load rank higher.
        active_jobs = float(feat.get('current_active_jobs', 0))
        max_jobs = max(1.0, float(feat.get('max_active_jobs', 3)))
        load_ratio = min(1.0, active_jobs / max_jobs)
        workload_score = max(0.0, 1.0 - load_ratio)

        # ── 3. Domain Proficiency Score (15%) ──────────────────────────────────
        # Scaled from 1–5 range to [0.2, 1.0].
        proficiency = float(feat.get('domain_proficiency', 3))
        proficiency_score = min(1.0, max(0.2, proficiency / 5.0))

        # ── 4. Experience Score (8%) ───────────────────────────────────────────
        # Capped at 15 years for diminishing returns.
        experience_yrs = float(feat.get('experience_years', 1))
        experience_score = min(1.0, max(0.05, experience_yrs / 15.0))

        # ── 5. Historical Performance Score (7%) ───────────────────────────────
        avg_rating = float(feat.get('historical_avg_rating', 5.0))
        rating_score = min(1.0, max(0.0, avg_rating / 5.0))
        success_rate = float(feat.get('historical_success_rate', 1.0))
        success_score = min(1.0, max(0.0, success_rate))
        historical_score = 0.5 * rating_score + 0.5 * success_score

        # ── Weighted Composition ───────────────────────────────────────────────
        final_score = (
            0.50 * distance_score +
            0.20 * workload_score +
            0.15 * proficiency_score +
            0.08 * experience_score +
            0.07 * historical_score
        )

        # Clamp to valid range
        return min(0.99, max(0.01, final_score))

