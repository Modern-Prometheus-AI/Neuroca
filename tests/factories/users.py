"""
User Factory for Test Data Generation.

This module provides factory classes for generating test user instances with realistic
and customizable data. It leverages the factory_boy library to create consistent test
objects that can be used across the test suite.

Usage:
    # Create a basic user
    user = UserFactory()
    
    # Create a user with specific attributes
    admin_user = UserFactory(role='admin', is_active=True)
    
    # Create a batch of users
    users = UserFactory.create_batch(size=5)
    
    # Create a user with a specific cognitive profile
    user_with_profile = UserFactory(cognitive_profile__attention_span=85)
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

import factory
import pytz
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice, FuzzyDateTime, FuzzyInteger

from neuroca.core.models.health import HealthMetrics
from neuroca.core.models.users import CognitiveProfile, User, UserPreferences, UserRole
from neuroca.db.database import db_session

# Constants for generating realistic test data
DEFAULT_PASSWORD = "securePassword123!"
USER_ROLES = [role.value for role in UserRole]
TIMEZONE_CHOICES = list(pytz.common_timezones)
COGNITIVE_TRAIT_RANGE = (1, 100)  # Range for cognitive metrics (1-100 scale)
HEALTH_METRIC_RANGE = (1, 100)    # Range for health metrics (1-100 scale)


class UserPreferencesFactory(factory.Factory):
    """Factory for generating UserPreferences instances for testing."""
    
    class Meta:
        model = UserPreferences
    
    theme = FuzzyChoice(['light', 'dark', 'system'])
    notifications_enabled = Faker('boolean', chance_of_getting_true=75)
    timezone = FuzzyChoice(TIMEZONE_CHOICES)
    language = FuzzyChoice(['en', 'es', 'fr', 'de', 'zh', 'ja'])
    session_timeout_minutes = FuzzyInteger(15, 120)
    accessibility_mode = Faker('boolean', chance_of_getting_true=10)
    
    @factory.post_generation
    def custom_settings(self, create: bool, extracted: Optional[dict[str, Any]], **kwargs):
        """
        Add custom settings to the UserPreferences instance.
        
        Args:
            create: Whether the factory is being used to create or build an object
            extracted: Dictionary of custom settings passed during factory instantiation
            **kwargs: Additional keyword arguments
        """
        if not create:
            return
            
        if extracted:
            self.custom_settings = extracted
        else:
            # Generate some random custom settings
            self.custom_settings = {
                'font_size': random.choice(['small', 'medium', 'large']),
                'auto_save': random.choice([True, False]),
                'dashboard_layout': random.choice(['compact', 'comfortable', 'spacious'])
            }


class CognitiveProfileFactory(factory.Factory):
    """Factory for generating CognitiveProfile instances for testing."""
    
    class Meta:
        model = CognitiveProfile
    
    attention_span = FuzzyInteger(*COGNITIVE_TRAIT_RANGE)
    memory_capacity = FuzzyInteger(*COGNITIVE_TRAIT_RANGE)
    learning_rate = FuzzyInteger(*COGNITIVE_TRAIT_RANGE)
    reasoning_ability = FuzzyInteger(*COGNITIVE_TRAIT_RANGE)
    creativity = FuzzyInteger(*COGNITIVE_TRAIT_RANGE)
    adaptability = FuzzyInteger(*COGNITIVE_TRAIT_RANGE)
    processing_speed = FuzzyInteger(*COGNITIVE_TRAIT_RANGE)
    
    @factory.post_generation
    def traits(self, create: bool, extracted: Optional[dict[str, int]], **kwargs):
        """
        Add additional cognitive traits to the profile.
        
        Args:
            create: Whether the factory is being used to create or build an object
            extracted: Dictionary of traits passed during factory instantiation
            **kwargs: Additional keyword arguments
        """
        if not create:
            return
            
        if extracted:
            self.traits = extracted
        else:
            # Generate some random additional traits
            self.traits = {
                'pattern_recognition': random.randint(*COGNITIVE_TRAIT_RANGE),
                'emotional_intelligence': random.randint(*COGNITIVE_TRAIT_RANGE),
                'spatial_awareness': random.randint(*COGNITIVE_TRAIT_RANGE)
            }


class HealthMetricsFactory(factory.Factory):
    """Factory for generating HealthMetrics instances for testing."""
    
    class Meta:
        model = HealthMetrics
    
    energy_level = FuzzyInteger(*HEALTH_METRIC_RANGE)
    stress_level = FuzzyInteger(*HEALTH_METRIC_RANGE)
    fatigue = FuzzyInteger(*HEALTH_METRIC_RANGE)
    last_updated = FuzzyDateTime(
        datetime.now(pytz.UTC) - timedelta(hours=24),
        datetime.now(pytz.UTC)
    )
    
    @factory.post_generation
    def metrics(self, create: bool, extracted: Optional[dict[str, Any]], **kwargs):
        """
        Add additional health metrics to the instance.
        
        Args:
            create: Whether the factory is being used to create or build an object
            extracted: Dictionary of metrics passed during factory instantiation
            **kwargs: Additional keyword arguments
        """
        if not create:
            return
            
        if extracted:
            self.metrics = extracted
        else:
            # Generate some random additional health metrics
            self.metrics = {
                'focus_quality': random.randint(*HEALTH_METRIC_RANGE),
                'recovery_rate': random.randint(*HEALTH_METRIC_RANGE),
                'cognitive_load': random.randint(*HEALTH_METRIC_RANGE)
            }


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    Factory for generating User instances for testing.
    
    This factory creates fully-populated User instances with related objects
    (preferences, cognitive profile, health metrics) for comprehensive testing.
    """
    
    class Meta:
        model = User
        sqlalchemy_session = db_session
        sqlalchemy_session_persistence = "commit"
    
    id = factory.LazyFunction(uuid.uuid4)
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password_hash = factory.LazyFunction(
        lambda: User.hash_password(DEFAULT_PASSWORD)
    )
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    role = FuzzyChoice(USER_ROLES)
    is_active = Faker('boolean', chance_of_getting_true=90)
    created_at = FuzzyDateTime(
        datetime.now(pytz.UTC) - timedelta(days=365),
        datetime.now(pytz.UTC)
    )
    last_login = factory.LazyAttribute(
        lambda o: datetime.now(pytz.UTC) - timedelta(days=random.randint(0, 30))
        if o.is_active else None
    )
    
    # Related objects
    preferences = factory.SubFactory(UserPreferencesFactory)
    cognitive_profile = factory.SubFactory(CognitiveProfileFactory)
    health_metrics = factory.SubFactory(HealthMetricsFactory)
    
    @factory.post_generation
    def tags(self, create: bool, extracted: Optional[list[str]], **kwargs):
        """
        Add tags to the user instance.
        
        Args:
            create: Whether the factory is being used to create or build an object
            extracted: List of tags passed during factory instantiation
            **kwargs: Additional keyword arguments
        """
        if not create:
            return
            
        if extracted:
            self.tags = extracted
        else:
            # Generate some random tags
            possible_tags = ['new_user', 'premium', 'beta_tester', 'researcher', 
                            'developer', 'content_creator', 'early_adopter']
            self.tags = random.sample(possible_tags, k=random.randint(0, 3))
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Override the create method to handle password hashing if a raw password is provided.
        
        Args:
            model_class: The model class being instantiated
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            The created model instance
        """
        # If a raw password is provided, hash it before creating the user
        if 'password' in kwargs:
            raw_password = kwargs.pop('password')
            kwargs['password_hash'] = User.hash_password(raw_password)
            
        return super()._create(model_class, *args, **kwargs)
    
    @factory.post_generation
    def set_admin(self, create: bool, extracted: bool, **kwargs):
        """
        Helper method to quickly create admin users.
        
        Args:
            create: Whether the factory is being used to create or build an object
            extracted: Boolean flag passed during factory instantiation
            **kwargs: Additional keyword arguments
        
        Usage:
            admin = UserFactory(set_admin=True)
        """
        if not create or extracted is None:
            return
            
        if extracted:
            self.role = UserRole.ADMIN.value
            # Admins typically have higher cognitive metrics
            self.cognitive_profile.reasoning_ability = max(85, self.cognitive_profile.reasoning_ability)
            self.cognitive_profile.adaptability = max(80, self.cognitive_profile.adaptability)


def create_test_users(count: int = 10) -> list[User]:
    """
    Utility function to create a diverse set of test users.
    
    This function creates a mix of regular users, admins, and users with various
    states (active/inactive) for comprehensive testing scenarios.
    
    Args:
        count: Number of test users to create
        
    Returns:
        List of created User instances
    """
    users = []
    
    # Create at least one admin
    users.append(UserFactory(set_admin=True))
    
    # Create at least one inactive user
    users.append(UserFactory(is_active=False))
    
    # Create remaining users with random attributes
    remaining_count = max(0, count - 2)
    if remaining_count > 0:
        users.extend(UserFactory.create_batch(size=remaining_count))
    
    return users