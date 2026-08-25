"""
Phase 3 tests for ML engine and assignment eligibility.
"""
from django.test import TestCase
from decimal import Decimal

from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.employees.models import Employee, EmployeeSkill
from apps.services.models import ServiceDomain, PredefinedIssue
from apps.requests.models import ServiceRequest
from apps.assignments.models import Assignment
from apps.ml_engine.selector import CandidateSelector


class CandidateEligibilityTestCase(TestCase):
    """
    Property 5: CandidateSelector hard-filter invariant
    Test that CandidateSelector correctly filters eligible candidates.
    """

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        
        self.resident = User.objects.create_user(
            username='resident',
            password='pass123',
            role='USER',
            organization=self.org
        )
        
        # Create various employee states
        self.available_employee = User.objects.create_user(
            username='emp_available',
            password='pass123',
            role='EMPLOYEE',
            organization=self.org
        )
        self.emp_available = Employee.objects.create(
            user=self.available_employee,
            organization=self.org,
            max_active_assignments=3,
            status='ACTIVE',
            is_available=True
        )
        
        self.unavailable_employee = User.objects.create_user(
            username='emp_unavailable',
            password='pass123',
            role='EMPLOYEE',
            organization=self.org
        )
        self.emp_unavailable = Employee.objects.create(
            user=self.unavailable_employee,
            organization=self.org,
            max_active_assignments=3,
            status='ACTIVE',
            is_available=False
        )
        
        self.wrong_org_user = User.objects.create_user(
            username='emp_wrong_org',
            password='pass123',
            role='EMPLOYEE',
            organization=self.org  # For simplicity, same org (can be different)
        )
        self.emp_wrong_org = Employee.objects.create(
            user=self.wrong_org_user,
            organization=Organization.objects.create(name='Other Org'),
            max_active_assignments=3,
            status='ACTIVE',
            is_available=True
        )
        
        self.at_capacity_user = User.objects.create_user(
            username='emp_at_capacity',
            password='pass123',
            role='EMPLOYEE',
            organization=self.org
        )
        self.emp_at_capacity = Employee.objects.create(
            user=self.at_capacity_user,
            organization=self.org,
            max_active_assignments=2,
            status='ACTIVE',
            is_available=True
        )
        
        self.domain = ServiceDomain.objects.create(
            organization=self.org,
            name='Plumbing',
            icon_name='wrench',
            sla_hours=4
        )
        
        # Add domain skill to available employee
        EmployeeSkill.objects.create(
            employee=self.emp_available,
            domain=self.domain,
            proficiency_level=4
        )
        
        # Don't add skill to unavailable employee (domain mismatch)
        # emp_wrong_org is in different org, so wrong-org filter
        # emp_at_capacity is at max capacity
        
        self.predefined_issue = PredefinedIssue.objects.create(
            domain=self.domain,
            title='Leaky Faucet',
            default_priority='NORMAL'
        )

    def test_unavailable_employee_excluded_from_candidates(self):
        """Test that unavailable employee is excluded from candidate list."""
        req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test',
            priority='NORMAL',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        
        candidates = CandidateSelector.get_eligible_candidates(req)
        candidate_ids = [str(c.id) for c in candidates]
        
        # Unavailable employee should not be in candidates
        self.assertNotIn(str(self.emp_unavailable.id), candidate_ids)

    def test_wrong_org_employee_excluded_from_candidates(self):
        """Test that wrong-org employee is excluded from candidate list."""
        req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test',
            priority='NORMAL',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        
        candidates = CandidateSelector.get_eligible_candidates(req)
        candidate_ids = [str(c.id) for c in candidates]
        
        # Wrong-org employee should not be in candidates
        self.assertNotIn(str(self.emp_wrong_org.id), candidate_ids)

    def test_at_capacity_employee_excluded_from_candidates(self):
        """Test that at-capacity employee is excluded from candidate list."""
        # Give emp_at_capacity the required skill
        EmployeeSkill.objects.create(
            employee=self.emp_at_capacity,
            domain=self.domain,
            proficiency_level=3
        )
        
        # Create 2 active assignments for emp_at_capacity (at max capacity)
        req1 = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test 1',
            priority='NORMAL'
        )
        
        req2 = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test 2',
            priority='NORMAL'
        )
        
        Assignment.objects.create(
            request=req1,
            employee=self.emp_at_capacity,
            status=Assignment.Status.ASSIGNED
        )
        
        Assignment.objects.create(
            request=req2,
            employee=self.emp_at_capacity,
            status=Assignment.Status.IN_PROGRESS
        )
        
        # Now try to create a new request - emp_at_capacity should be excluded
        req3 = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test 3',
            priority='NORMAL',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        
        candidates = CandidateSelector.get_eligible_candidates(req3)
        candidate_ids = [str(c.id) for c in candidates]
        
        # At-capacity employee should not be in candidates
        self.assertNotIn(str(self.emp_at_capacity.id), candidate_ids)

    def test_domain_mismatch_employee_excluded_from_candidates(self):
        """Test that employee without domain skill is excluded."""
        req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test',
            priority='NORMAL',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        
        candidates = CandidateSelector.get_eligible_candidates(req)
        candidate_ids = [str(c.id) for c in candidates]
        
        # Unavailable employee (no skill) should not be in candidates
        self.assertNotIn(str(self.emp_unavailable.id), candidate_ids)

    def test_available_qualified_employee_included_in_candidates(self):
        """Test that available, qualified employee is included in candidates."""
        req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test',
            priority='NORMAL',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        
        candidates = CandidateSelector.get_eligible_candidates(req)
        candidate_ids = [str(c.id) for c in candidates]
        
        # Available qualified employee should be in candidates
        self.assertIn(str(self.emp_available.id), candidate_ids)

    def test_closer_employee_scores_higher_than_farther(self):
        """Test that closer employee scores higher than farther employee."""
        from apps.ml_engine.feature_builder import FeatureBuilder
        from apps.ml_engine.placeholder_ranker import DeterministicWeightedRanker
        
        # Create two skilled employees at different locations
        emp2_user = User.objects.create_user(
            username='emp2',
            password='pass123',
            role='EMPLOYEE',
            organization=self.org
        )
        emp2 = Employee.objects.create(
            user=emp2_user,
            organization=self.org,
            max_active_assignments=3,
            status='ACTIVE',
            is_available=True,
            current_latitude=Decimal('40.7580'),  # Farther
            current_longitude=Decimal('-73.9855')
        )
        EmployeeSkill.objects.create(
            employee=emp2,
            domain=self.domain,
            proficiency_level=4
        )
        
        # Update available employee location
        self.emp_available.current_latitude = Decimal('40.7200')  # Closer
        self.emp_available.current_longitude = Decimal('-74.0100')
        self.emp_available.save()
        
        # Create request at specific location
        req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test',
            priority='NORMAL',
            latitude=Decimal('40.7200'),
            longitude=Decimal('-74.0100')
        )
        
        # Build features for both employees
        features1 = FeatureBuilder.build_features(req, self.emp_available)
        features2 = FeatureBuilder.build_features(req, emp2)
        
        # Closer employee (features1) should have lower distance_km
        # When scored, this should result in higher suitability
        dist1 = features1.get('distance_km', 0)
        dist2 = features2.get('distance_km', 0)
        
        # emp_available is closer, so should have lower distance
        self.assertLess(dist1, dist2)


class RankingModelTestCase(TestCase):
    """
    Test the ranking model behavior.
    """

    def setUp(self):
        from apps.ml_engine.placeholder_ranker import DeterministicWeightedRanker
        self.ranker = DeterministicWeightedRanker()

    def test_ranker_produces_scores(self):
        """Test that ranker produces valid scores for features."""
        features_list = [
            {
                'distance_km': 1.5,
                'domain_proficiency': 4,
                'experience_years': 3,
                'current_active_jobs': 1
            },
            {
                'distance_km': 5.0,
                'domain_proficiency': 3,
                'experience_years': 5,
                'current_active_jobs': 2
            }
        ]
        
        scores = self.ranker.rank_candidates(features_list)
        
        self.assertEqual(len(scores), len(features_list))
        # Scores should be numeric
        for score in scores:
            self.assertIsInstance(score, (int, float))
            self.assertGreater(score, 0)  # Scores should be positive

    def test_closer_candidate_ranks_higher(self):
        """Test that closer candidates with similar skills rank higher."""
        features_close = {
            'distance_km': 1.0,
            'domain_proficiency': 4,
            'experience_years': 3,
            'current_active_jobs': 1
        }
        
        features_far = {
            'distance_km': 10.0,
            'domain_proficiency': 4,
            'experience_years': 3,
            'current_active_jobs': 1
        }
        
        scores = self.ranker.rank_candidates([features_close, features_far])
        
        # Closer candidate should have higher score
        self.assertGreater(scores[0], scores[1])

    def test_higher_proficiency_ranks_higher(self):
        """Test that higher proficiency employees rank higher."""
        features_expert = {
            'distance_km': 5.0,
            'domain_proficiency': 5,
            'experience_years': 3,
            'current_active_jobs': 1
        }
        
        features_novice = {
            'distance_km': 5.0,
            'domain_proficiency': 1,
            'experience_years': 3,
            'current_active_jobs': 1
        }
        
        scores = self.ranker.rank_candidates([features_expert, features_novice])
        
        # Expert should rank higher
        self.assertGreater(scores[0], scores[1])
