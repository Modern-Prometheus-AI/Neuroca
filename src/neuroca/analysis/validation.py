"""
Post-Transfer Validation and LLM Integration System

This module implements comprehensive validation mechanisms to ensure successful
transfer and integration of codebase summaries with target LLM systems.
"""

import asyncio
import json
import logging
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationTask:
    """Individual validation task definition"""
    name: str
    description: str
    query: str
    expected_response_type: str
    ground_truth: Optional[str] = None
    max_tokens: int = 1000
    timeout_seconds: int = 30
    critical: bool = False


@dataclass
class ValidationResult:
    """Result of a validation task execution"""
    task_name: str
    success: bool
    response: str
    response_time: float
    token_count: int
    accuracy_score: float
    hallucination_detected: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ValidationSuite:
    """Complete validation suite configuration"""
    name: str
    description: str
    tasks: List[ValidationTask]
    ground_truth_data: Dict[str, Any]
    evaluation_criteria: Dict[str, Any]
    performance_thresholds: Dict[str, float]


class LLMInterface(ABC):
    """Abstract interface for LLM integration"""
    
    @abstractmethod
    async def query(self, prompt: str, max_tokens: int = 1000) -> Tuple[str, Dict[str, Any]]:
        """Send query to LLM and get response with metadata"""
        pass
    
    @abstractmethod
    async def upload_context(self, context_data: str) -> bool:
        """Upload context data to LLM system"""
        pass
    
    @abstractmethod
    async def get_system_info(self) -> Dict[str, Any]:
        """Get information about the LLM system"""
        pass


class OpenAIInterface(LLMInterface):
    """OpenAI API interface implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        
    async def query(self, prompt: str, max_tokens: int = 1000) -> Tuple[str, Dict[str, Any]]:
        """Query OpenAI API"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            
            start_time = time.time()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            response_time = time.time() - start_time
            
            content = response.choices[0].message.content
            metadata = {
                "model": self.model,
                "response_time": response_time,
                "tokens_used": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def upload_context(self, context_data: str) -> bool:
        """Upload context data (simulate by testing query with context)"""
        try:
            test_prompt = f"Based on this codebase context: {context_data[:1000]}...\n\nWhat is the main purpose of this codebase?"
            response, _ = await self.query(test_prompt, max_tokens=100)
            return len(response) > 10  # Basic success check
        except Exception as e:
            logger.error(f"Context upload test failed: {e}")
            return False
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "provider": "OpenAI",
            "model": self.model,
            "base_url": self.base_url,
            "context_window": 128000 if "gpt-4" in self.model else 4096,
            "max_tokens": 4096
        }


class AnthropicInterface(LLMInterface):
    """Anthropic Claude API interface implementation"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        
    async def query(self, prompt: str, max_tokens: int = 1000) -> Tuple[str, Dict[str, Any]]:
        """Query Anthropic API"""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            start_time = time.time()
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            response_time = time.time() - start_time
            
            content = response.content[0].text
            metadata = {
                "model": self.model,
                "response_time": response_time,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def upload_context(self, context_data: str) -> bool:
        """Upload context data (simulate by testing query with context)"""
        try:
            test_prompt = f"Based on this codebase context: {context_data[:1000]}...\n\nWhat is the main purpose of this codebase?"
            response, _ = await self.query(test_prompt, max_tokens=100)
            return len(response) > 10
        except Exception as e:
            logger.error(f"Context upload test failed: {e}")
            return False
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "provider": "Anthropic",
            "model": self.model,
            "context_window": 200000,
            "max_tokens": 4096
        }


class PostTransferValidator:
    """Engine for post-transfer validation of LLM integration"""
    
    def __init__(self, llm_interface: LLMInterface, validation_suite: ValidationSuite):
        self.llm = llm_interface
        self.suite = validation_suite
        self.results: List[ValidationResult] = []
        
    async def run_full_validation(self, summary_bundle_path: str) -> Dict[str, Any]:
        """Run complete post-transfer validation suite"""
        logger.info("Starting post-transfer validation")
        
        # Load summary bundle
        context_data = await self._load_summary_bundle(summary_bundle_path)
        
        # Test LLM system connectivity
        system_info = await self.llm.get_system_info()
        logger.info(f"Connected to {system_info['provider']} - {system_info['model']}")
        
        # Upload context to LLM
        upload_success = await self.llm.upload_context(context_data)
        if not upload_success:
            logger.error("Failed to upload context to LLM system")
            return {"status": "failed", "reason": "context_upload_failed"}
        
        # Execute validation tasks
        for task in self.suite.tasks:
            result = await self._execute_validation_task(task, context_data)
            self.results.append(result)
            
            if task.critical and not result.success:
                logger.error(f"Critical validation task failed: {task.name}")
                return {"status": "failed", "reason": f"critical_task_failed: {task.name}"}
        
        # Analyze results
        validation_report = await self._analyze_validation_results()
        
        # Generate final assessment
        overall_success = validation_report["overall_score"] >= 0.8
        
        return {
            "status": "passed" if overall_success else "failed",
            "overall_score": validation_report["overall_score"],
            "task_results": validation_report["task_summary"],
            "system_info": system_info,
            "detailed_results": [asdict(r) for r in self.results],
            "recommendations": validation_report["recommendations"]
        }
    
    async def _load_summary_bundle(self, bundle_path: str) -> str:
        """Load and prepare summary bundle for LLM context"""
        bundle_file = Path(bundle_path)
        
        if not bundle_file.exists():
            raise FileNotFoundError(f"Summary bundle not found: {bundle_path}")
        
        # Load the summary bundle
        with open(bundle_file, 'r') as f:
            bundle_data = json.load(f)
        
        # Extract key context information
        context_parts = []
        
        # Add global overview
        if bundle_data.get("global_overview"):
            context_parts.append(f"# Project Overview\n{bundle_data['global_overview']}")
        
        # Add hierarchical summaries
        if bundle_data.get("hierarchical_summaries"):
            context_parts.append("# Architecture Summary")
            for level, summary in bundle_data["hierarchical_summaries"].items():
                context_parts.append(f"## {level}\n{summary}")
        
        # Add metadata summary
        if bundle_data.get("metadata"):
            metadata = bundle_data["metadata"]
            context_parts.append(f"""
# Codebase Metadata
- Total Files: {metadata.get('total_files', 'unknown')}
- Total Lines of Code: {metadata.get('total_loc', 'unknown')}
- Primary Languages: {metadata.get('languages', 'unknown')}
- Quality Score: {metadata.get('quality_score', 'unknown')}
""")
        
        return "\n\n".join(context_parts)
    
    async def _execute_validation_task(self, task: ValidationTask, context_data: str) -> ValidationResult:
        """Execute a single validation task"""
        logger.info(f"Executing validation task: {task.name}")
        
        try:
            # Prepare prompt with context
            full_prompt = f"""Context: {context_data}

Task: {task.description}

Query: {task.query}

Please provide a comprehensive response based on the provided codebase context."""
            
            # Execute query
            start_time = time.time()
            response, metadata = await self.llm.query(full_prompt, task.max_tokens)
            response_time = time.time() - start_time
            
            # Evaluate response
            accuracy_score = await self._evaluate_response_accuracy(task, response)
            hallucination_detected = await self._detect_hallucination(response, context_data)
            
            return ValidationResult(
                task_name=task.name,
                success=accuracy_score >= 0.7,  # 70% accuracy threshold
                response=response,
                response_time=response_time,
                token_count=metadata.get("tokens_used", 0),
                accuracy_score=accuracy_score,
                hallucination_detected=hallucination_detected,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Validation task failed: {task.name} - {e}")
            return ValidationResult(
                task_name=task.name,
                success=False,
                response="",
                response_time=0.0,
                token_count=0,
                accuracy_score=0.0,
                hallucination_detected=False,
                error_message=str(e)
            )
    
    async def _evaluate_response_accuracy(self, task: ValidationTask, response: str) -> float:
        """Evaluate the accuracy of LLM response"""
        if not task.ground_truth:
            # Basic heuristic evaluation
            return self._heuristic_accuracy_score(task, response)
        
        # Compare with ground truth
        return self._compare_with_ground_truth(task.ground_truth, response)
    
    def _heuristic_accuracy_score(self, task: ValidationTask, response: str) -> float:
        """Heuristic-based accuracy scoring"""
        score = 0.0
        
        # Check response length (not too short, not too long)
        if 50 <= len(response) <= 2000:
            score += 0.2
        
        # Check for relevant keywords based on task type
        task_keywords = {
            "architecture": ["class", "function", "module", "component", "system"],
            "testing": ["test", "pytest", "coverage", "unit", "integration"],
            "dependencies": ["import", "package", "library", "dependency", "requirement"],
            "functionality": ["feature", "functionality", "capability", "purpose", "goal"]
        }
        
        task_type = task.expected_response_type.lower()
        keywords = task_keywords.get(task_type, [])
        
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in response.lower())
        if keywords:
            score += 0.4 * (keyword_matches / len(keywords))
        
        # Check for structured response
        if any(marker in response for marker in ["##", "**", "1.", "-", "*"]):
            score += 0.2
        
        # Check for code examples if appropriate
        if "code" in task.expected_response_type.lower() and "```" in response:
            score += 0.2
        
        return min(score, 1.0)
    
    def _compare_with_ground_truth(self, ground_truth: str, response: str) -> float:
        """Compare response with ground truth using similarity metrics"""
        # Simple token-based similarity
        ground_truth_tokens = set(ground_truth.lower().split())
        response_tokens = set(response.lower().split())
        
        intersection = ground_truth_tokens.intersection(response_tokens)
        union = ground_truth_tokens.union(response_tokens)
        
        if not union:
            return 0.0
        
        jaccard_similarity = len(intersection) / len(union)
        return jaccard_similarity
    
    async def _detect_hallucination(self, response: str, context_data: str) -> bool:
        """Detect potential hallucinations in the response"""
        # Simple hallucination detection heuristics
        
        # Check for specific file/module names that don't exist in context
        response_lower = response.lower()
        
        # Look for specific claims that might be hallucinated
        hallucination_indicators = [
            "uses react",  # If not a React project
            "uses vue",    # If not a Vue project
            "uses angular", # If not an Angular project
            "written in go", # If not a Go project
            "uses kubernetes", # If not using Kubernetes
            "mongodb database", # If not using MongoDB
        ]
        
        for indicator in hallucination_indicators:
            if indicator in response_lower and indicator not in context_data.lower():
                return True
        
        return False
    
    async def _analyze_validation_results(self) -> Dict[str, Any]:
        """Analyze all validation results and generate summary"""
        if not self.results:
            return {
                "overall_score": 0.0,
                "task_summary": {},
                "recommendations": ["No validation tasks were executed"]
            }
        
        # Calculate overall metrics
        total_tasks = len(self.results)
        successful_tasks = len([r for r in self.results if r.success])
        avg_accuracy = sum(r.accuracy_score for r in self.results) / total_tasks
        avg_response_time = sum(r.response_time for r in self.results) / total_tasks
        total_tokens = sum(r.token_count for r in self.results)
        hallucinations_detected = len([r for r in self.results if r.hallucination_detected])
        
        # Calculate overall score
        success_rate = successful_tasks / total_tasks
        hallucination_penalty = hallucinations_detected * 0.1
        overall_score = max(0.0, avg_accuracy * success_rate - hallucination_penalty)
        
        # Task summary
        task_summary = {}
        for result in self.results:
            task_summary[result.task_name] = {
                "success": result.success,
                "accuracy": result.accuracy_score,
                "response_time": result.response_time,
                "hallucination": result.hallucination_detected
            }
        
        # Generate recommendations
        recommendations = []
        
        if success_rate < 0.8:
            recommendations.append("Consider improving context data quality or LLM prompt engineering")
        
        if avg_response_time > 30:
            recommendations.append("Response times are high - consider optimizing queries or using faster model")
        
        if hallucinations_detected > 0:
            recommendations.append(f"Detected {hallucinations_detected} potential hallucinations - review context completeness")
        
        if avg_accuracy < 0.7:
            recommendations.append("Low accuracy scores - review ground truth data and evaluation criteria")
        
        if not recommendations:
            recommendations.append("All validation metrics are within acceptable ranges")
        
        return {
            "overall_score": overall_score,
            "success_rate": success_rate,
            "avg_accuracy": avg_accuracy,
            "avg_response_time": avg_response_time,
            "total_tokens_used": total_tokens,
            "hallucinations_detected": hallucinations_detected,
            "task_summary": task_summary,
            "recommendations": recommendations
        }


def create_default_validation_suite() -> ValidationSuite:
    """Create default validation suite for codebase summarization"""
    
    tasks = [
        ValidationTask(
            name="architecture_overview",
            description="Describe the overall architecture of this codebase",
            query="What is the main architecture pattern used in this codebase? Describe the key components and their relationships.",
            expected_response_type="architecture",
            critical=True
        ),
        ValidationTask(
            name="testing_framework",
            description="Identify the testing frameworks and approach",
            query="What testing frameworks and methodologies are used in this project? What is the test coverage?",
            expected_response_type="testing"
        ),
        ValidationTask(
            name="dependencies_analysis",
            description="List and analyze main dependencies",
            query="What are the main dependencies and libraries used in this project? List the most important ones.",
            expected_response_type="dependencies"
        ),
        ValidationTask(
            name="core_functionality",
            description="Explain the core functionality",
            query="What is the main purpose and core functionality of this codebase? What problems does it solve?",
            expected_response_type="functionality",
            critical=True
        ),
        ValidationTask(
            name="code_quality",
            description="Assess code quality and standards",
            query="What can you tell me about the code quality, coding standards, and best practices used in this project?",
            expected_response_type="quality"
        ),
        ValidationTask(
            name="deployment_approach",
            description="Describe deployment and infrastructure",
            query="How is this application deployed? What infrastructure and deployment strategies are used?",
            expected_response_type="deployment"
        )
    ]
    
    ground_truth_data = {
        "architecture": "FastAPI-based cognitive agent system with modular components",
        "testing": "pytest with comprehensive coverage requirements (90% overall)",
        "dependencies": "Python 3.9+, FastAPI, pytest, Poetry for dependency management",
        "functionality": "LLM integration and cognitive processing for automated analysis",
        "quality": "High standards with pre-commit hooks, linting, and automated testing",
        "deployment": "Docker containerization with CI/CD pipeline support"
    }
    
    evaluation_criteria = {
        "accuracy_threshold": 0.7,
        "response_time_limit": 30.0,
        "max_hallucinations": 1,
        "min_success_rate": 0.8
    }
    
    performance_thresholds = {
        "overall_score": 0.8,
        "success_rate": 0.8,
        "avg_accuracy": 0.7,
        "max_response_time": 30.0
    }
    
    return ValidationSuite(
        name="Default Codebase Validation",
        description="Standard validation suite for codebase summarization transfer",
        tasks=tasks,
        ground_truth_data=ground_truth_data,
        evaluation_criteria=evaluation_criteria,
        performance_thresholds=performance_thresholds
    )


async def validate_llm_transfer(
    llm_interface: LLMInterface,
    summary_bundle_path: str,
    validation_suite: ValidationSuite = None
) -> Dict[str, Any]:
    """Convenience function to validate LLM transfer"""
    
    if validation_suite is None:
        validation_suite = create_default_validation_suite()
    
    validator = PostTransferValidator(llm_interface, validation_suite)
    return await validator.run_full_validation(summary_bundle_path)
