"""
Reasoning Prompt Templates for NeuroCognitive Architecture (NCA)

This module provides a collection of prompt templates and utilities for enhancing
the reasoning capabilities of Large Language Models (LLMs) within the NCA system.
It implements various reasoning strategies including:

- Chain-of-thought reasoning
- Tree-of-thought reasoning
- Step-by-step problem solving
- Analogical reasoning
- Counterfactual reasoning
- Causal reasoning

Each reasoning strategy is implemented as a template class that can be configured
and instantiated based on the specific reasoning needs of the application.

Usage:
    from neuroca.integration.prompts.reasoning import ChainOfThoughtPrompt
    
    # Create a chain-of-thought reasoning prompt
    cot_prompt = ChainOfThoughtPrompt(
        task="Solve the following math problem",
        examples=[{"problem": "...", "reasoning": "...", "answer": "..."}]
    )
    
    # Generate the prompt for a specific problem
    formatted_prompt = cot_prompt.format(problem="What is 25 * 13?")
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

from neuroca.core.exceptions import PromptValidationError, ReasoningError
from neuroca.core.utils.validation import validate_list, validate_string
from neuroca.integration.prompts.base import BasePromptTemplate

# Configure logger
logger = logging.getLogger(__name__)


class ReasoningStrategy(Enum):
    """Enumeration of supported reasoning strategies."""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    STEP_BY_STEP = "step_by_step"
    ANALOGICAL = "analogical"
    COUNTERFACTUAL = "counterfactual"
    CAUSAL = "causal"
    FIRST_PRINCIPLES = "first_principles"
    SOCRATIC = "socratic"


@dataclass
class ReasoningExample:
    """A dataclass representing an example for few-shot reasoning prompts."""
    problem: str
    reasoning: str
    answer: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the example fields after initialization."""
        validate_string(self.problem, "problem", min_length=1)
        validate_string(self.reasoning, "reasoning", min_length=1)
        validate_string(self.answer, "answer", min_length=1)


class BaseReasoningPrompt(BasePromptTemplate):
    """Base class for all reasoning prompt templates."""
    
    def __init__(
        self,
        strategy: ReasoningStrategy,
        task_description: str,
        examples: Optional[list[Union[dict[str, Any], ReasoningExample]]] = None,
        instruction_template: str = "",
        output_format: Optional[dict[str, Any]] = None,
        max_reasoning_steps: int = 5,
        **kwargs
    ):
        """
        Initialize a base reasoning prompt template.
        
        Args:
            strategy: The reasoning strategy to use
            task_description: Description of the task to be performed
            examples: Optional list of examples for few-shot learning
            instruction_template: Template string for the instruction
            output_format: Optional specification for the expected output format
            max_reasoning_steps: Maximum number of reasoning steps to allow
            **kwargs: Additional keyword arguments
        
        Raises:
            PromptValidationError: If any validation checks fail
        """
        super().__init__(**kwargs)
        
        self.strategy = strategy
        self.task_description = task_description
        self.instruction_template = instruction_template
        self.output_format = output_format
        self.max_reasoning_steps = max_reasoning_steps
        
        # Validate and process examples
        self.examples = []
        if examples:
            validate_list(examples, "examples")
            for example in examples:
                if isinstance(example, ReasoningExample):
                    self.examples.append(example)
                elif isinstance(example, dict):
                    try:
                        self.examples.append(ReasoningExample(**example))
                    except (TypeError, ValueError) as e:
                        raise PromptValidationError(f"Invalid example format: {e}")
                else:
                    raise PromptValidationError(
                        f"Example must be a dict or ReasoningExample, got {type(example)}"
                    )
        
        logger.debug(
            f"Initialized {self.strategy.value} reasoning prompt with "
            f"{len(self.examples)} examples"
        )
    
    def _format_examples(self) -> str:
        """
        Format the examples for inclusion in the prompt.
        
        Returns:
            A string containing the formatted examples
        """
        if not self.examples:
            return ""
        
        examples_text = "\n\nExamples:\n"
        for i, example in enumerate(self.examples, 1):
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Problem: {example.problem}\n"
            examples_text += f"Reasoning: {example.reasoning}\n"
            examples_text += f"Answer: {example.answer}\n"
        
        return examples_text
    
    def _format_output_instructions(self) -> str:
        """
        Format the output instructions based on the output format.
        
        Returns:
            A string containing the formatted output instructions
        """
        if not self.output_format:
            return ""
        
        output_instructions = "\n\nYour response should follow this format:\n"
        output_instructions += json.dumps(self.output_format, indent=2)
        return output_instructions
    
    def format(self, **kwargs) -> str:
        """
        Format the reasoning prompt with the provided arguments.
        
        Args:
            **kwargs: Arguments to format the prompt with
        
        Returns:
            The formatted prompt string
        
        Raises:
            PromptValidationError: If required arguments are missing
        """
        try:
            # Build the base prompt
            prompt = f"{self.task_description}\n\n"
            
            # Add strategy-specific instructions
            if self.instruction_template:
                prompt += self.instruction_template.format(**kwargs)
            
            # Add examples if available
            prompt += self._format_examples()
            
            # Add output format instructions if specified
            prompt += self._format_output_instructions()
            
            # Add the actual problem/question
            if "problem" in kwargs:
                prompt += f"\n\nProblem: {kwargs['problem']}\n"
            elif "question" in kwargs:
                prompt += f"\n\nQuestion: {kwargs['question']}\n"
            
            # Add reasoning prompt
            prompt += f"\nPlease use {self.strategy.value.replace('_', ' ')} reasoning to solve this problem."
            
            logger.debug(f"Generated {self.strategy.value} reasoning prompt")
            return prompt
            
        except KeyError as e:
            error_msg = f"Missing required argument for prompt formatting: {e}"
            logger.error(error_msg)
            raise PromptValidationError(error_msg)
        except Exception as e:
            error_msg = f"Error formatting reasoning prompt: {e}"
            logger.error(error_msg)
            raise ReasoningError(error_msg)


class ChainOfThoughtPrompt(BaseReasoningPrompt):
    """
    Chain-of-Thought reasoning prompt template.
    
    This template encourages the model to break down complex problems into
    a sequence of intermediate reasoning steps before arriving at the final answer.
    """
    
    def __init__(
        self,
        task_description: str,
        examples: Optional[list[Union[dict[str, Any], ReasoningExample]]] = None,
        output_format: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a Chain-of-Thought reasoning prompt.
        
        Args:
            task_description: Description of the task to be performed
            examples: Optional list of examples for few-shot learning
            output_format: Optional specification for the expected output format
            **kwargs: Additional keyword arguments
        """
        instruction_template = (
            "Think through this problem step-by-step. Break down your reasoning "
            "into clear, logical steps, and explain your thought process at each step. "
            "After working through the steps, provide your final answer."
        )
        
        super().__init__(
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
            task_description=task_description,
            examples=examples,
            instruction_template=instruction_template,
            output_format=output_format,
            **kwargs
        )


class TreeOfThoughtPrompt(BaseReasoningPrompt):
    """
    Tree-of-Thought reasoning prompt template.
    
    This template encourages the model to explore multiple reasoning paths
    and evaluate them to find the most promising solution approach.
    """
    
    def __init__(
        self,
        task_description: str,
        examples: Optional[list[Union[dict[str, Any], ReasoningExample]]] = None,
        num_branches: int = 3,
        depth: int = 2,
        output_format: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a Tree-of-Thought reasoning prompt.
        
        Args:
            task_description: Description of the task to be performed
            examples: Optional list of examples for few-shot learning
            num_branches: Number of alternative paths to explore at each step
            depth: Maximum depth of the reasoning tree
            output_format: Optional specification for the expected output format
            **kwargs: Additional keyword arguments
        """
        self.num_branches = num_branches
        self.depth = depth
        
        instruction_template = (
            f"For this problem, explore {num_branches} different approaches or perspectives. "
            f"For each approach, think up to {depth} steps ahead. "
            "Evaluate the promise of each approach, and then pursue the most promising one "
            "to its conclusion. Finally, provide your answer based on the best reasoning path."
        )
        
        super().__init__(
            strategy=ReasoningStrategy.TREE_OF_THOUGHT,
            task_description=task_description,
            examples=examples,
            instruction_template=instruction_template,
            output_format=output_format,
            **kwargs
        )


class StepByStepPrompt(BaseReasoningPrompt):
    """
    Step-by-Step reasoning prompt template.
    
    This template guides the model to solve problems by breaking them down
    into sequential, clearly defined steps.
    """
    
    def __init__(
        self,
        task_description: str,
        examples: Optional[list[Union[dict[str, Any], ReasoningExample]]] = None,
        output_format: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a Step-by-Step reasoning prompt.
        
        Args:
            task_description: Description of the task to be performed
            examples: Optional list of examples for few-shot learning
            output_format: Optional specification for the expected output format
            **kwargs: Additional keyword arguments
        """
        instruction_template = (
            "Solve this problem by following these steps:\n"
            "1. Understand what the problem is asking\n"
            "2. Identify the relevant information\n"
            "3. Plan your approach\n"
            "4. Execute the solution step by step\n"
            "5. Verify your answer\n\n"
            "Label each step clearly and show all your work."
        )
        
        super().__init__(
            strategy=ReasoningStrategy.STEP_BY_STEP,
            task_description=task_description,
            examples=examples,
            instruction_template=instruction_template,
            output_format=output_format,
            **kwargs
        )


class AnalogicalPrompt(BaseReasoningPrompt):
    """
    Analogical reasoning prompt template.
    
    This template encourages the model to solve problems by drawing analogies
    to similar problems or situations it has encountered before.
    """
    
    def __init__(
        self,
        task_description: str,
        examples: Optional[list[Union[dict[str, Any], ReasoningExample]]] = None,
        analogies: Optional[list[dict[str, str]]] = None,
        output_format: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize an Analogical reasoning prompt.
        
        Args:
            task_description: Description of the task to be performed
            examples: Optional list of examples for few-shot learning
            analogies: Optional list of analogies to include in the prompt
            output_format: Optional specification for the expected output format
            **kwargs: Additional keyword arguments
        """
        self.analogies = analogies or []
        
        analogies_text = ""
        if self.analogies:
            analogies_text = "\nConsider these analogies:\n"
            for i, analogy in enumerate(self.analogies, 1):
                analogies_text += f"{i}. {analogy['description']}\n"
            analogies_text += "\n"
        
        instruction_template = (
            "Solve this problem by drawing analogies to similar situations or problems. "
            "Identify patterns that might apply to this problem, and explain how the analogy "
            "helps you understand or solve the current problem."
            f"{analogies_text}"
        )
        
        super().__init__(
            strategy=ReasoningStrategy.ANALOGICAL,
            task_description=task_description,
            examples=examples,
            instruction_template=instruction_template,
            output_format=output_format,
            **kwargs
        )


class CounterfactualPrompt(BaseReasoningPrompt):
    """
    Counterfactual reasoning prompt template.
    
    This template guides the model to explore alternative scenarios by
    changing key assumptions or conditions of the problem.
    """
    
    def __init__(
        self,
        task_description: str,
        examples: Optional[list[Union[dict[str, Any], ReasoningExample]]] = None,
        counterfactuals: Optional[list[str]] = None,
        output_format: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a Counterfactual reasoning prompt.
        
        Args:
            task_description: Description of the task to be performed
            examples: Optional list of examples for few-shot learning
            counterfactuals: Optional list of counterfactual scenarios to consider
            output_format: Optional specification for the expected output format
            **kwargs: Additional keyword arguments
        """
        self.counterfactuals = counterfactuals or []
        
        counterfactuals_text = ""
        if self.counterfactuals:
            counterfactuals_text = "\nConsider these counterfactual scenarios:\n"
            for i, cf in enumerate(self.counterfactuals, 1):
                counterfactuals_text += f"{i}. What if {cf}?\n"
            counterfactuals_text += "\n"
        
        instruction_template = (
            "Analyze this problem by considering counterfactual scenarios - what would happen "
            "if key aspects of the problem were different? Identify the most important assumptions "
            "or conditions, and explore how changing them would affect the outcome."
            f"{counterfactuals_text}"
            "After exploring these counterfactuals, return to the original problem and provide your solution."
        )
        
        super().__init__(
            strategy=ReasoningStrategy.COUNTERFACTUAL,
            task_description=task_description,
            examples=examples,
            instruction_template=instruction_template,
            output_format=output_format,
            **kwargs
        )


class CausalPrompt(BaseReasoningPrompt):
    """
    Causal reasoning prompt template.
    
    This template guides the model to analyze cause-and-effect relationships
    to understand or solve problems.
    """
    
    def __init__(
        self,
        task_description: str,
        examples: Optional[list[Union[dict[str, Any], ReasoningExample]]] = None,
        output_format: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a Causal reasoning prompt.
        
        Args:
            task_description: Description of the task to be performed
            examples: Optional list of examples for few-shot learning
            output_format: Optional specification for the expected output format
            **kwargs: Additional keyword arguments
        """
        instruction_template = (
            "Analyze this problem by identifying cause-and-effect relationships. "
            "Consider:\n"
            "1. What are the key factors or variables involved?\n"
            "2. How do these factors influence each other?\n"
            "3. What are the direct and indirect causal relationships?\n"
            "4. Are there any feedback loops or complex interactions?\n\n"
            "Draw a causal chain or diagram if helpful, and explain your reasoning."
        )
        
        super().__init__(
            strategy=ReasoningStrategy.CAUSAL,
            task_description=task_description,
            examples=examples,
            instruction_template=instruction_template,
            output_format=output_format,
            **kwargs
        )


class FirstPrinciplesPrompt(BaseReasoningPrompt):
    """
    First Principles reasoning prompt template.
    
    This template encourages the model to break down complex problems into
    fundamental truths and build up from there.
    """
    
    def __init__(
        self,
        task_description: str,
        examples: Optional[list[Union[dict[str, Any], ReasoningExample]]] = None,
        principles: Optional[list[str]] = None,
        output_format: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a First Principles reasoning prompt.
        
        Args:
            task_description: Description of the task to be performed
            examples: Optional list of examples for few-shot learning
            principles: Optional list of first principles to consider
            output_format: Optional specification for the expected output format
            **kwargs: Additional keyword arguments
        """
        self.principles = principles or []
        
        principles_text = ""
        if self.principles:
            principles_text = "\nConsider these fundamental principles:\n"
            for i, principle in enumerate(self.principles, 1):
                principles_text += f"{i}. {principle}\n"
            principles_text += "\n"
        
        instruction_template = (
            "Approach this problem using first principles thinking. Break down the problem "
            "into its most fundamental elements or truths, and then build up your solution "
            "from these basic principles."
            f"{principles_text}"
            "Avoid relying on analogies or conventional wisdom unless you can derive them "
            "from first principles."
        )
        
        super().__init__(
            strategy=ReasoningStrategy.FIRST_PRINCIPLES,
            task_description=task_description,
            examples=examples,
            instruction_template=instruction_template,
            output_format=output_format,
            **kwargs
        )


class SocraticPrompt(BaseReasoningPrompt):
    """
    Socratic reasoning prompt template.
    
    This template guides the model to solve problems through a series of
    questions that lead to deeper understanding and insight.
    """
    
    def __init__(
        self,
        task_description: str,
        examples: Optional[list[Union[dict[str, Any], ReasoningExample]]] = None,
        guiding_questions: Optional[list[str]] = None,
        output_format: Optional[dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a Socratic reasoning prompt.
        
        Args:
            task_description: Description of the task to be performed
            examples: Optional list of examples for few-shot learning
            guiding_questions: Optional list of guiding questions
            output_format: Optional specification for the expected output format
            **kwargs: Additional keyword arguments
        """
        self.guiding_questions = guiding_questions or [
            "What do we know for certain?",
            "What assumptions are we making?",
            "What are the key concepts or definitions involved?",
            "What are the implications of each possible approach?",
            "How can we test or verify our conclusions?"
        ]
        
        questions_text = "\nConsider these guiding questions:\n"
        for i, question in enumerate(self.guiding_questions, 1):
            questions_text += f"{i}. {question}\n"
        
        instruction_template = (
            "Use the Socratic method to solve this problem. Ask yourself a series of "
            "probing questions that help clarify the problem and lead to a solution. "
            f"{questions_text}\n"
            "For each question, provide a thoughtful answer that advances your understanding. "
            "Continue this process until you reach a well-reasoned conclusion."
        )
        
        super().__init__(
            strategy=ReasoningStrategy.SOCRATIC,
            task_description=task_description,
            examples=examples,
            instruction_template=instruction_template,
            output_format=output_format,
            **kwargs
        )


def create_reasoning_prompt(
    strategy: Union[str, ReasoningStrategy],
    task_description: str,
    **kwargs
) -> BaseReasoningPrompt:
    """
    Factory function to create a reasoning prompt based on the specified strategy.
    
    Args:
        strategy: The reasoning strategy to use (string or ReasoningStrategy enum)
        task_description: Description of the task to be performed
        **kwargs: Additional arguments to pass to the prompt constructor
    
    Returns:
        An instance of the appropriate reasoning prompt class
    
    Raises:
        ValueError: If an invalid strategy is provided
    """
    # Convert string to enum if necessary
    if isinstance(strategy, str):
        try:
            strategy = ReasoningStrategy(strategy)
        except ValueError:
            valid_strategies = [s.value for s in ReasoningStrategy]
            raise ValueError(
                f"Invalid reasoning strategy: '{strategy}'. "
                f"Valid options are: {', '.join(valid_strategies)}"
            )
    
    # Create the appropriate prompt based on the strategy
    strategy_map = {
        ReasoningStrategy.CHAIN_OF_THOUGHT: ChainOfThoughtPrompt,
        ReasoningStrategy.TREE_OF_THOUGHT: TreeOfThoughtPrompt,
        ReasoningStrategy.STEP_BY_STEP: StepByStepPrompt,
        ReasoningStrategy.ANALOGICAL: AnalogicalPrompt,
        ReasoningStrategy.COUNTERFACTUAL: CounterfactualPrompt,
        ReasoningStrategy.CAUSAL: CausalPrompt,
        ReasoningStrategy.FIRST_PRINCIPLES: FirstPrinciplesPrompt,
        ReasoningStrategy.SOCRATIC: SocraticPrompt,
    }
    
    prompt_class = strategy_map.get(strategy)
    if not prompt_class:
        raise ValueError(f"No implementation found for strategy: {strategy}")
    
    logger.info(f"Creating {strategy.value} reasoning prompt")
    return prompt_class(task_description=task_description, **kwargs)


def extract_reasoning_steps(response: str) -> list[str]:
    """
    Extract reasoning steps from a model response.
    
    Args:
        response: The model's response text
    
    Returns:
        A list of extracted reasoning steps
    """
    # Try to extract numbered steps (e.g., "1. First step")
    numbered_steps = re.findall(r'(?:^|\n)(\d+\.\s*[^\n]+)', response)
    if numbered_steps:
        return [step.strip() for step in numbered_steps]
    
    # Try to extract steps labeled with "Step X:"
    labeled_steps = re.findall(r'(?:^|\n)(?:Step\s+\d+:?\s*|Step:?\s*)([^\n]+)', response, re.IGNORECASE)
    if labeled_steps:
        return [step.strip() for step in labeled_steps]
    
    # Fall back to paragraph-based extraction
    paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
    if len(paragraphs) > 1:
        # Filter out very short paragraphs and those that look like conclusions
        steps = [p for p in paragraphs if len(p) > 20 and not p.lower().startswith(('therefore', 'thus', 'in conclusion', 'finally'))]
        if steps:
            return steps
    
    # If all else fails, just split by newlines
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    return [line for line in lines if len(line) > 20]