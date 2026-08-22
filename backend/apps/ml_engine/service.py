from typing import Optional, Tuple, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from apps.requests.models import ServiceRequest
from apps.assignments.models import Assignment
from apps.employees.models import Employee
from .selector import CandidateSelector
from .feature_builder import FeatureBuilder
from .placeholder_ranker import DeterministicWeightedRanker
from .interfaces import RankingModelInterface

class AssignmentService:
    """
    Automated Workforce Assignment Pipeline Coordinator
    
    Architecture Flow:
    1. Retrieve Request (Org, Domain, Geolocation, Priority)
    2. Stage 1: CandidateSelector hard eligibility filter
    3. Stage 2: FeatureBuilder extracts structured feature vector per eligible employee
    4. Stage 3: RankingModelInterface computes suitability scores
    5. Highest-ranked candidate is atomically assigned
    6. Historical snapshot (coordinates, distance, features, model version) logged in DB
    7. Fallback: If no candidate is eligible, request status transitions to QUEUED
    """

    def __init__(self, ranking_model: Optional[RankingModelInterface] = None):
        # Default to pluggable baseline ranker (can be injected with external ML ranker)
        self.ranking_model = ranking_model or DeterministicWeightedRanker()

    def set_ranking_model(self, ranking_model: RankingModelInterface):
        """Allows dynamic swapping of the ML model instance."""
        self.ranking_model = ranking_model

    def auto_assign(self, service_request: ServiceRequest) -> Tuple[Optional[Assignment], str]:
        """
        Executes automatic assignment for a service request.
        Returns: (Assignment instance or None, Status message)
        """
        # Hard Eligibility Filtering
        eligible_candidates = CandidateSelector.get_eligible_candidates(service_request)

        if not eligible_candidates:
            # Fallback: Queue request
            if service_request.status != ServiceRequest.Status.QUEUED:
                service_request.status = ServiceRequest.Status.QUEUED
                service_request.save(update_fields=['status', 'updated_at'])
            return None, "No eligible workforce candidates currently available. Request queued."

        # Extract features for each candidate
        features_list = [
            FeatureBuilder.build_features(service_request, emp)
            for emp in eligible_candidates
        ]

        # Compute suitability scores via Ranking Model
        scores = self.ranking_model.rank_candidates(features_list)

        # Rank candidates by score (descending)
        ranked_pairs = sorted(
            zip(eligible_candidates, scores, features_list),
            key=lambda x: x[1],
            reverse=True
        )

        best_candidate, best_score, best_features = ranked_pairs[0]

        # Atomic Assignment Transaction
        with transaction.atomic():
            assignment = Assignment.objects.create(
                request=service_request,
                employee=best_candidate,
                status=Assignment.Status.ASSIGNED,
                # Domain and priority snapshots
                domain_snapshot=service_request.domain,
                priority_snapshot=service_request.priority,
                # Geographic snapshots
                request_latitude_snapshot=service_request.latitude,
                request_longitude_snapshot=service_request.longitude,
                employee_latitude_snapshot=best_candidate.current_latitude,
                employee_longitude_snapshot=best_candidate.current_longitude,
                distance_km=best_features.get('distance_km', 0.0),
                # Employee state at assignment time
                active_workload_at_assignment=best_features.get('current_active_jobs', 0),
                skill_proficiency_snapshot=best_features.get('domain_proficiency', 0),
                experience_years_snapshot=best_features.get('experience_years', 0),
                is_available_snapshot=best_candidate.is_available,
                # SLA snapshot
                sla_hours_snapshot=service_request.domain.sla_hours,
                # Ranking
                suitability_score=best_score,
                ranking_model_version=self.ranking_model.get_model_name(),
                # Full feature vector JSON backup
                features_snapshot=best_features,
                notes=f"Auto-assigned with suitability score {best_score:.3f} using {self.ranking_model.get_model_name()}"
            )

            service_request.status = ServiceRequest.Status.ASSIGNED
            service_request.save(update_fields=['status', 'updated_at'])

        return assignment, f"Successfully assigned to {best_candidate} (Score: {best_score:.3f})"

    def inspect_candidates(self, service_request: ServiceRequest) -> List[Dict[str, Any]]:
        """
        Preview & audit helper for Admins: Returns all eligible candidates,
        their extracted feature vectors, and calculated ranking scores.
        """
        eligible_candidates = CandidateSelector.get_eligible_candidates(service_request)
        if not eligible_candidates:
            return []

        features_list = [
            FeatureBuilder.build_features(service_request, emp)
            for emp in eligible_candidates
        ]
        scores = self.ranking_model.rank_candidates(features_list)

        ranked = []
        for emp, score, feats in zip(eligible_candidates, scores, features_list):
            ranked.append({
                'employee_id': str(emp.id),
                'employee_name': emp.user.get_full_name() or emp.user.username,
                'role_title': emp.role.title if emp.role else 'Staff',
                'distance_km': feats.get('distance_km', 0.0),
                'suitability_score': score,
                'current_active_jobs': feats.get('current_active_jobs', 0),
                'domain_proficiency': feats.get('domain_proficiency', 3),
                'historical_avg_rating': feats.get('historical_avg_rating', 5.0),
                'features': feats,
            })

        return sorted(ranked, key=lambda x: x['suitability_score'], reverse=True)

    def reassign_request(self, service_request: ServiceRequest, reason: str = "") -> Tuple[Optional[Assignment], str]:
        """
        Reassigns an existing request to another eligible candidate (excluding previous assignee).
        """
        current_assignment = service_request.assignments.filter(
            status__in=[Assignment.Status.ASSIGNED, Assignment.Status.ACCEPTED, Assignment.Status.IN_PROGRESS]
        ).first()

        exclude_ids = [str(current_assignment.employee_id)] if current_assignment else []

        eligible_candidates = CandidateSelector.get_eligible_candidates(
            service_request,
            exclude_employee_ids=exclude_ids
        )

        if not eligible_candidates:
            if current_assignment:
                current_assignment.status = Assignment.Status.REASSIGNED
                current_assignment.reassigned_at = timezone.now()
                current_assignment.notes += f" | Reassignment attempt failed: {reason}"
                current_assignment.save()
            service_request.status = ServiceRequest.Status.QUEUED
            service_request.save(update_fields=['status', 'updated_at'])
            return None, "No alternative eligible candidate found. Request queued."

        features_list = [
            FeatureBuilder.build_features(service_request, emp)
            for emp in eligible_candidates
        ]
        scores = self.ranking_model.rank_candidates(features_list)

        ranked_pairs = sorted(
            zip(eligible_candidates, scores, features_list),
            key=lambda x: x[1],
            reverse=True
        )
        best_candidate, best_score, best_features = ranked_pairs[0]

        with transaction.atomic():
            if current_assignment:
                current_assignment.status = Assignment.Status.REASSIGNED
                current_assignment.reassigned_at = timezone.now()
                current_assignment.notes += f" | Reassigned: {reason}"
                current_assignment.save()

            new_assignment = Assignment.objects.create(
                request=service_request,
                employee=best_candidate,
                status=Assignment.Status.ASSIGNED,
                request_latitude_snapshot=service_request.latitude,
                request_longitude_snapshot=service_request.longitude,
                employee_latitude_snapshot=best_candidate.current_latitude,
                employee_longitude_snapshot=best_candidate.current_longitude,
                distance_km=best_features.get('distance_km', 0.0),
                # Employee state at assignment time
                active_workload_at_assignment=best_features.get('current_active_jobs', 0),
                skill_proficiency_snapshot=best_features.get('domain_proficiency', 0),
                experience_years_snapshot=best_features.get('experience_years', 0),
                is_available_snapshot=best_candidate.is_available,
                # Domain and priority snapshots
                domain_snapshot=service_request.domain,
                priority_snapshot=service_request.priority,
                # SLA snapshot
                sla_hours_snapshot=service_request.domain.sla_hours,
                # Reassignment tracking
                is_reassignment=True,
                reassignment_reason=reason,
                # Ranking
                suitability_score=best_score,
                ranking_model_version=self.ranking_model.get_model_name(),
                # Full feature vector JSON backup
                features_snapshot=best_features,
                notes=f"Reassigned from previous technician. Reason: {reason}"
            )

            service_request.status = ServiceRequest.Status.ASSIGNED
            service_request.save(update_fields=['status', 'updated_at'])

        return new_assignment, f"Reassigned to {best_candidate} (Score: {best_score:.3f})"
