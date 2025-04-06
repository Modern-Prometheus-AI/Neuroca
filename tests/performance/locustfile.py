"""
Locust Performance Testing File for NeuroCognitive Architecture (NCA)

This file contains performance test scenarios for the NCA system using Locust.
It defines user behaviors that simulate real-world usage patterns and load on the system.

Usage:
    Run from project root with: locust -f neuroca/tests/performance/locustfile.py
    
    Command line options:
    - Set host: --host=http://localhost:8000
    - Set number of users: -u 100
    - Set spawn rate: -r 10
    - Set run time: -t 5m
    
    Example:
    locust -f neuroca/tests/performance/locustfile.py --host=http://localhost:8000 -u 100 -r 10 -t 5m

Requirements:
    - locust>=2.15.0
"""

import logging
import random
import time

from locust import HttpUser, TaskSet, between, events, task
from locust.exception import StopUser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("nca-performance")

# Test data for API requests
SAMPLE_PROMPTS = [
    "Explain the concept of neural networks",
    "How does memory consolidation work in the human brain?",
    "What are the key differences between working memory and long-term memory?",
    "Describe the process of neuroplasticity",
    "How do emotions affect cognitive processing?",
]

SAMPLE_CONTEXTS = [
    "academic research",
    "casual conversation",
    "technical documentation",
    "creative writing",
    "problem solving",
]

# API endpoints
ENDPOINTS = {
    "health": "/api/v1/health",
    "memory": {
        "working": "/api/v1/memory/working",
        "short_term": "/api/v1/memory/short-term",
        "long_term": "/api/v1/memory/long-term",
    },
    "cognition": "/api/v1/cognition/process",
    "integration": "/api/v1/integration/llm",
}


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """
    Event handler that runs when Locust initializes.
    Used to set up any required resources before tests begin.
    """
    logger.info("Initializing NCA performance tests")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Event handler that runs when the test starts.
    """
    logger.info("NCA performance test is starting")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Event handler that runs when the test stops.
    """
    logger.info("NCA performance test completed")


class MemoryTasks(TaskSet):
    """
    Task set for testing memory-related endpoints.
    Simulates operations on the three-tiered memory system.
    """
    
    def on_start(self):
        """
        Initialize user session data when a user starts.
        """
        self.user_data = {
            "session_id": f"test-session-{random.randint(1000, 9999)}",
            "memories": [],
        }
        logger.debug(f"Started memory tasks with session {self.user_data['session_id']}")
    
    @task(3)
    def create_working_memory(self):
        """
        Test creating an item in working memory.
        """
        try:
            payload = {
                "session_id": self.user_data["session_id"],
                "content": random.choice(SAMPLE_PROMPTS),
                "metadata": {
                    "context": random.choice(SAMPLE_CONTEXTS),
                    "timestamp": time.time(),
                    "priority": random.randint(1, 5),
                }
            }
            
            with self.client.post(
                ENDPOINTS["memory"]["working"], 
                json=payload,
                catch_response=True
            ) as response:
                if response.status_code == 201:
                    data = response.json()
                    memory_id = data.get("id")
                    if memory_id:
                        self.user_data["memories"].append(memory_id)
                        logger.debug(f"Created working memory: {memory_id}")
                    response.success()
                else:
                    response.failure(f"Failed to create working memory: {response.text}")
        except Exception as e:
            logger.error(f"Error in create_working_memory: {str(e)}")
    
    @task(2)
    def retrieve_working_memory(self):
        """
        Test retrieving items from working memory.
        """
        try:
            if not self.user_data["memories"]:
                return
                
            memory_id = random.choice(self.user_data["memories"])
            with self.client.get(
                f"{ENDPOINTS['memory']['working']}/{memory_id}",
                params={"session_id": self.user_data["session_id"]},
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    logger.debug(f"Retrieved working memory: {memory_id}")
                    response.success()
                elif response.status_code == 404:
                    # Memory might have been consolidated or expired
                    if memory_id in self.user_data["memories"]:
                        self.user_data["memories"].remove(memory_id)
                    response.success()
                else:
                    response.failure(f"Failed to retrieve working memory: {response.text}")
        except Exception as e:
            logger.error(f"Error in retrieve_working_memory: {str(e)}")
    
    @task(1)
    def consolidate_to_short_term(self):
        """
        Test consolidating working memory to short-term memory.
        """
        try:
            if not self.user_data["memories"]:
                return
                
            memory_ids = random.sample(
                self.user_data["memories"], 
                min(3, len(self.user_data["memories"]))
            )
            
            payload = {
                "session_id": self.user_data["session_id"],
                "memory_ids": memory_ids,
                "consolidation_metadata": {
                    "importance": random.randint(1, 10),
                    "emotional_valence": random.uniform(-1.0, 1.0),
                    "timestamp": time.time(),
                }
            }
            
            with self.client.post(
                ENDPOINTS["memory"]["short_term"], 
                json=payload,
                catch_response=True
            ) as response:
                if response.status_code == 201:
                    data = response.json()
                    consolidated_id = data.get("consolidated_id")
                    if consolidated_id:
                        # Remove working memories that were consolidated
                        for memory_id in memory_ids:
                            if memory_id in self.user_data["memories"]:
                                self.user_data["memories"].remove(memory_id)
                        
                        # Add the new consolidated memory
                        self.user_data["memories"].append(consolidated_id)
                        logger.debug(f"Consolidated to short-term memory: {consolidated_id}")
                    response.success()
                else:
                    response.failure(f"Failed to consolidate to short-term memory: {response.text}")
        except Exception as e:
            logger.error(f"Error in consolidate_to_short_term: {str(e)}")
    
    @task(1)
    def query_long_term_memory(self):
        """
        Test querying the long-term memory.
        """
        try:
            query = random.choice(SAMPLE_PROMPTS)
            params = {
                "session_id": self.user_data["session_id"],
                "query": query,
                "limit": 5,
                "min_relevance": 0.7,
            }
            
            with self.client.get(
                ENDPOINTS["memory"]["long_term"],
                params=params,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    logger.debug(f"Queried long-term memory with: {query}")
                    response.success()
                else:
                    response.failure(f"Failed to query long-term memory: {response.text}")
        except Exception as e:
            logger.error(f"Error in query_long_term_memory: {str(e)}")


class CognitionTasks(TaskSet):
    """
    Task set for testing cognition-related endpoints.
    Simulates cognitive processing operations.
    """
    
    def on_start(self):
        """
        Initialize user session data when a user starts.
        """
        self.user_data = {
            "session_id": f"test-session-{random.randint(1000, 9999)}",
        }
        logger.debug(f"Started cognition tasks with session {self.user_data['session_id']}")
    
    @task
    def process_cognitive_input(self):
        """
        Test the cognitive processing endpoint with various inputs.
        """
        try:
            payload = {
                "session_id": self.user_data["session_id"],
                "input": random.choice(SAMPLE_PROMPTS),
                "context": {
                    "domain": random.choice(SAMPLE_CONTEXTS),
                    "cognitive_load": random.uniform(0.1, 0.9),
                    "emotional_state": {
                        "valence": random.uniform(-1.0, 1.0),
                        "arousal": random.uniform(0.0, 1.0),
                    },
                },
                "processing_parameters": {
                    "depth": random.randint(1, 5),
                    "creativity": random.uniform(0.1, 0.9),
                    "precision": random.uniform(0.1, 0.9),
                }
            }
            
            with self.client.post(
                ENDPOINTS["cognition"], 
                json=payload,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    logger.debug(f"Processed cognitive input: {payload['input'][:30]}...")
                    response.success()
                else:
                    response.failure(f"Failed to process cognitive input: {response.text}")
        except Exception as e:
            logger.error(f"Error in process_cognitive_input: {str(e)}")


class IntegrationTasks(TaskSet):
    """
    Task set for testing LLM integration endpoints.
    Simulates interactions with the LLM integration layer.
    """
    
    def on_start(self):
        """
        Initialize user session data when a user starts.
        """
        self.user_data = {
            "session_id": f"test-session-{random.randint(1000, 9999)}",
        }
        logger.debug(f"Started integration tasks with session {self.user_data['session_id']}")
    
    @task
    def llm_integration_request(self):
        """
        Test the LLM integration endpoint.
        """
        try:
            payload = {
                "session_id": self.user_data["session_id"],
                "prompt": random.choice(SAMPLE_PROMPTS),
                "model_parameters": {
                    "temperature": random.uniform(0.1, 1.0),
                    "max_tokens": random.choice([50, 100, 200, 500]),
                    "top_p": random.uniform(0.9, 1.0),
                },
                "memory_integration": {
                    "use_working_memory": random.choice([True, False]),
                    "use_short_term_memory": random.choice([True, False]),
                    "use_long_term_memory": random.choice([True, False]),
                }
            }
            
            with self.client.post(
                ENDPOINTS["integration"], 
                json=payload,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    logger.debug(f"LLM integration request for: {payload['prompt'][:30]}...")
                    response.success()
                else:
                    response.failure(f"Failed LLM integration request: {response.text}")
        except Exception as e:
            logger.error(f"Error in llm_integration_request: {str(e)}")


class HealthCheckTasks(TaskSet):
    """
    Task set for testing health check endpoints.
    Used to monitor system health during load testing.
    """
    
    @task
    def check_health(self):
        """
        Test the health check endpoint.
        """
        try:
            with self.client.get(
                ENDPOINTS["health"],
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    if status == "healthy":
                        response.success()
                    else:
                        response.failure(f"Health check returned non-healthy status: {status}")
                        
                        # If system is in critical state, log detailed information
                        if data.get("details", {}).get("severity") == "critical":
                            logger.critical(f"System health critical: {data}")
                else:
                    response.failure(f"Health check failed with status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error in check_health: {str(e)}")


class NCAUser(HttpUser):
    """
    Main user class that simulates a user interacting with the NCA system.
    Includes a mix of different task sets to create realistic load patterns.
    """
    wait_time = between(1, 5)  # Wait between 1-5 seconds between tasks
    
    tasks = {
        MemoryTasks: 4,
        CognitionTasks: 3,
        IntegrationTasks: 2,
        HealthCheckTasks: 1,
    }
    
    def on_start(self):
        """
        Setup performed when a user starts.
        """
        logger.info(f"User started: {self.host}")
        
        # Verify system is available before starting tests
        try:
            response = self.client.get(ENDPOINTS["health"])
            if response.status_code != 200 or response.json().get("status") != "healthy":
                logger.error(f"System health check failed on startup: {response.text}")
                raise StopUser()
        except Exception as e:
            logger.error(f"Error during initial health check: {str(e)}")
            raise StopUser()
    
    def on_stop(self):
        """
        Cleanup performed when a user stops.
        """
        logger.info("User stopped")


# If running directly, provide usage information
if __name__ == "__main__":
    print(__doc__)