from typing import Dict, Any

from .distance import calculate_haversine_distance


class FeatureBuilder:
    """
    Extracts standardized feature vectors for an employee
    evaluated against a specific service request.

    These features are:
    1. Passed to the ranking model.
    2. Stored in Assignment.features_snapshot.
    """

    @staticmethod
    def build_features(service_request, employee) -> Dict[str, Any]:

        # ========================================================
        # 1. Distance Calculation
        # ========================================================

        req_lat = (
            float(service_request.latitude)
            if service_request.latitude
            else 0.0
        )

        req_lng = (
            float(service_request.longitude)
            if service_request.longitude
            else 0.0
        )

        emp_lat = (
            float(employee.current_latitude)
            if employee.current_latitude
            else 0.0
        )

        emp_lng = (
            float(employee.current_longitude)
            if employee.current_longitude
            else 0.0
        )

        distance_km = calculate_haversine_distance(
            req_lat,
            req_lng,
            emp_lat,
            emp_lng
        )

        # ========================================================
        # 2. Skill Proficiency in Target Domain
        # ========================================================

        skill_entry = employee.skills.filter(
            domain=service_request.domain
        ).first()

        domain_proficiency = (
            skill_entry.proficiency_level
            if skill_entry
            else 3
        )

        domain_experience_years = (
            skill_entry.years_of_experience
            if skill_entry
            else employee.experience_years
        )

        # ========================================================
        # 3. Workload & Concurrency
        # ========================================================

        active_assignments_count = employee.assignments.filter(
            status__in=[
                "ASSIGNED",
                "ACCEPTED",
                "IN_PROGRESS"
            ]
        ).count()

        max_active_jobs = (
            employee.max_active_assignments
            or 3
        )

        workload_ratio = round(
            active_assignments_count
            / max(1, max_active_jobs),
            3
        )

        # ========================================================
        # 4. Historical Track Record
        # ========================================================

        past_assignments = employee.assignments.filter(
            status="COMPLETED"
        )

        domain_past_assignments = past_assignments.filter(
            request__domain=service_request.domain
        )

        previous_jobs_in_domain = (
            domain_past_assignments.count()
        )

        feedbacks = [
            assignment.request.feedback
            for assignment in past_assignments
            if hasattr(
                assignment.request,
                "feedback"
            )
        ]

        if feedbacks:

            # ----------------------------------------------------
            # Historical success rate
            # ----------------------------------------------------

            resolved_count = sum(
                1
                for feedback in feedbacks
                if feedback.is_resolved
            )

            historical_success_rate = round(
                resolved_count / len(feedbacks),
                3
            )

            # ----------------------------------------------------
            # Historical rating
            # ----------------------------------------------------

            historical_avg_rating = round(
                sum(
                    feedback.rating
                    for feedback in feedbacks
                )
                / len(feedbacks),
                2
            )

            # ----------------------------------------------------
            # Average resolution time
            # ----------------------------------------------------

            resolution_times = [
                feedback.resolution_time_minutes
                for feedback in feedbacks
                if feedback.resolution_time_minutes > 0
            ]

            avg_res_time = (
                round(
                    sum(resolution_times)
                    / len(resolution_times),
                    1
                )
                if resolution_times
                else 60.0
            )

            # ----------------------------------------------------
            # Historical SLA success rate
            # ----------------------------------------------------

            sla_met_count = sum(
                1
                for feedback in feedbacks
                if feedback.met_sla
            )

            sla_success_rate = round(
                sla_met_count / len(feedbacks),
                3
            )

        else:

            historical_success_rate = 1.0

            historical_avg_rating = 5.0

            avg_res_time = (
                float(
                    service_request.domain.sla_hours
                )
                * 60
            )

            sla_success_rate = 1.0

        # ========================================================
        # 5. Priority & SLA
        # ========================================================

        sla_hours = (
            service_request.domain.sla_hours
        )

        # ========================================================
        # 6. Final Feature Dictionary
        # ========================================================

        features = {

            # ----------------------------------------------------
            # Identifiers / metadata
            # ----------------------------------------------------

            "employee_id": str(
                employee.id
            ),

            "employee_name": (
                employee.user.get_full_name()
                or employee.user.username
            ),

            "request_id": str(
                service_request.id
            ),

            "domain_id": str(
                service_request.domain_id
            ),

            "domain_name": (
                service_request.domain.name
            ),

            # ----------------------------------------------------
            # EXACT FEATURES USED BY KERAS MODEL
            # ----------------------------------------------------

            "skill_proficiency": (
                domain_proficiency
            ),

            "experience_years": (
                employee.experience_years
            ),

            "historical_success_rate": (
                historical_success_rate
            ),

            "average_resolution_hours": (
                avg_res_time / 60.0
            ),

            "sla_success_rate": (
                sla_success_rate
            ),

            "distance_km": (
                distance_km
            ),

            "workload_ratio": (
                workload_ratio
            ),

            # Keep priority as the categorical
            # value expected by the saved encoder.
            "priority": (
                service_request.priority
            ),

            # ----------------------------------------------------
            # Additional backend / audit information
            # ----------------------------------------------------

            "domain_proficiency": (
                domain_proficiency
            ),

            "domain_experience_years": (
                domain_experience_years
            ),

            "previous_jobs_in_domain": (
                previous_jobs_in_domain
            ),

            "historical_avg_rating": (
                historical_avg_rating
            ),

            "average_resolution_time": (
                avg_res_time
            ),

            "current_active_jobs": (
                active_assignments_count
            ),

            "max_active_jobs": (
                max_active_jobs
            ),

            "availability": (
                1.0
                if employee.is_available
                else 0.0
            ),

            "sla_remaining": (
                sla_hours
            ),
        }

        return features