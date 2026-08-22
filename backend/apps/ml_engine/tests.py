from django.test import TestCase
from django.utils import timezone
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.services.models import ServiceDomain, PredefinedIssue
from apps.employees.models import Employee, EmployeeRole, EmployeeSkill, EmployeeSchedule
from apps.requests.models import ServiceRequest
from apps.assignments.models import Assignment
from apps.feedback.models import Feedback
from apps.ml_engine.distance import calculate_haversine_distance
from apps.ml_engine.selector import CandidateSelector
from apps.ml_engine.feature_builder import FeatureBuilder
from apps.ml_engine.placeholder_ranker import DeterministicWeightedRanker
from apps.ml_engine.service import AssignmentService

class DistanceCalculationTests(TestCase):
    def test_haversine_same_point(self):
        dist = calculate_haversine_distance(12.9716, 77.5946, 12.9716, 77.5946)
        self.assertEqual(dist, 0.0)

    def test_haversine_known_distance(self):
        # Bangalore Center (12.9716, 77.5946) to Electronic City (12.8399, 77.6770) ~17 km
        dist = calculate_haversine_distance(12.9716, 77.5946, 12.8399, 77.6770)
        self.assertGreater(dist, 14.0)
        self.assertLess(dist, 20.0)


class AssignmentEngineTests(TestCase):
    def setUp(self):
        self.org1 = Organization.objects.create(
            name="Alpha Community",
            org_type=Organization.OrgType.GATED_COMMUNITY,
            latitude=12.9300,
            longitude=77.6800
        )
        self.org2 = Organization.objects.create(
            name="Beta Colony",
            org_type=Organization.OrgType.RESIDENTIAL_COLONY,
            latitude=12.9500,
            longitude=77.7000
        )

        self.domain_elec = ServiceDomain.objects.create(
            organization=self.org1,
            name="Electrical",
            sla_hours=8
        )
        self.domain_plumb = ServiceDomain.objects.create(
            organization=self.org1,
            name="Plumbing",
            sla_hours=6
        )

        # Users
        self.user_resident = User.objects.create_user(
            username="test_resident",
            password="password123",
            organization=self.org1,
            role=User.Role.USER
        )

        self.user_emp1 = User.objects.create_user(
            username="electrician_close",
            password="password123",
            organization=self.org1,
            role=User.Role.EMPLOYEE,
            first_name="Close",
            last_name="Electrician"
        )
        self.emp1 = Employee.objects.create(
            user=self.user_emp1,
            organization=self.org1,
            experience_years=5,
            max_active_assignments=3,
            current_latitude=12.9310, # Very close: ~0.15 km
            current_longitude=77.6810,
            status=Employee.Status.ACTIVE,
            is_available=True
        )
        EmployeeSkill.objects.create(
            employee=self.emp1,
            domain=self.domain_elec,
            proficiency_level=5,
            years_of_experience=5
        )

        self.user_emp2 = User.objects.create_user(
            username="electrician_far",
            password="password123",
            organization=self.org1,
            role=User.Role.EMPLOYEE,
            first_name="Far",
            last_name="Electrician"
        )
        self.emp2 = Employee.objects.create(
            user=self.user_emp2,
            organization=self.org1,
            experience_years=2,
            max_active_assignments=3,
            current_latitude=12.9800, # Far away: ~6 km
            current_longitude=77.7400,
            status=Employee.Status.ACTIVE,
            is_available=True
        )
        EmployeeSkill.objects.create(
            employee=self.emp2,
            domain=self.domain_elec,
            proficiency_level=3,
            years_of_experience=2
        )

        # Employee from other organization (Must never be selected)
        self.user_other_org = User.objects.create_user(
            username="other_org_staff",
            password="password123",
            organization=self.org2,
            role=User.Role.EMPLOYEE
        )
        self.emp_other = Employee.objects.create(
            user=self.user_other_org,
            organization=self.org2,
            experience_years=10,
            max_active_assignments=5,
            current_latitude=12.9300,
            current_longitude=77.6800,
            status=Employee.Status.ACTIVE,
            is_available=True
        )
        # Create domain in org2
        domain_org2 = ServiceDomain.objects.create(organization=self.org2, name="Electrical")
        EmployeeSkill.objects.create(employee=self.emp_other, domain=domain_org2, proficiency_level=5)

    def test_candidate_selector_hard_filters(self):
        # Create a request in org1 for Electrical
        req = ServiceRequest.objects.create(
            organization=self.org1,
            user=self.user_resident,
            domain=self.domain_elec,
            custom_description="Power failure in unit",
            latitude=12.9300,
            longitude=77.6800,
            priority=ServiceRequest.Priority.HIGH
        )

        candidates = CandidateSelector.get_eligible_candidates(req, check_schedule=False)
        self.assertEqual(len(candidates), 2)
        self.assertIn(self.emp1, candidates)
        self.assertIn(self.emp2, candidates)
        self.assertNotIn(self.emp_other, candidates) # Cross-organization rejected

        # Mark emp1 unavailable
        self.emp1.is_available = False
        self.emp1.save()
        candidates_after_unavail = CandidateSelector.get_eligible_candidates(req, check_schedule=False)
        self.assertEqual(len(candidates_after_unavail), 1)
        self.assertIn(self.emp2, candidates_after_unavail)

    def test_feature_builder_and_ranking(self):
        req = ServiceRequest.objects.create(
            organization=self.org1,
            user=self.user_resident,
            domain=self.domain_elec,
            custom_description="Flickering lights",
            latitude=12.9300,
            longitude=77.6800,
            priority=ServiceRequest.Priority.NORMAL
        )

        feats1 = FeatureBuilder.build_features(req, self.emp1)
        feats2 = FeatureBuilder.build_features(req, self.emp2)

        self.assertIn('distance_km', feats1)
        self.assertIn('domain_proficiency', feats1)
        self.assertIn('current_active_jobs', feats1)
        self.assertIn('historical_success_rate', feats1)
        self.assertLess(feats1['distance_km'], feats2['distance_km'])

        ranker = DeterministicWeightedRanker()
        scores = ranker.rank_candidates([feats1, feats2])
        self.assertEqual(len(scores), 2)
        # Closer, higher proficiency employee must receive higher suitability score
        self.assertGreater(scores[0], scores[1])

    def test_auto_assignment_lifecycle(self):
        req = ServiceRequest.objects.create(
            organization=self.org1,
            user=self.user_resident,
            domain=self.domain_elec,
            custom_description="Main breaker tripping",
            latitude=12.9300,
            longitude=77.6800,
            priority=ServiceRequest.Priority.URGENT
        )

        service = AssignmentService()
        assignment, msg = service.auto_assign(req)

        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.employee, self.emp1) # Chosen closest & highest proficiency
        self.assertEqual(assignment.status, Assignment.Status.ASSIGNED)
        self.assertEqual(assignment.request.status, ServiceRequest.Status.ASSIGNED)
        self.assertGreater(assignment.suitability_score, 0.0)
        self.assertIn('distance_km', assignment.features_snapshot)
        # Verify explicit snapshot columns are populated
        self.assertEqual(assignment.priority_snapshot, 'URGENT')
        self.assertEqual(assignment.skill_proficiency_snapshot, 5)
        self.assertEqual(assignment.experience_years_snapshot, 5)
        self.assertTrue(assignment.is_available_snapshot)
        self.assertFalse(assignment.is_reassignment)
        self.assertEqual(assignment.ranking_model_version, 'placeholder-deterministic-v2')
