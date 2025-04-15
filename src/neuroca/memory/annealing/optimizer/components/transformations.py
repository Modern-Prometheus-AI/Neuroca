"""
Memory Transformations Module for Annealing Optimizer

This module provides functions to generate neighboring states by applying transformations
to memory fragments during the annealing optimization process.
"""

import logging
import random
from typing import List

from neuroca.memory.models.memory_item import MemoryItem
from neuroca.memory.utils.similarity import calculate_similarity

# Configure logger
logger = logging.getLogger(__name__)


def clone_memories(memories: List[MemoryItem]) -> List[MemoryItem]:
    """
    Create a deep copy of memory fragments for optimization.

    Args:
        memories: List of memory fragments to clone

    Returns:
        Deep copy of memory fragments
    """
    return [memory.clone() for memory in memories]


def generate_neighbor(state: List[MemoryItem]) -> List[MemoryItem]:
    """
    Generate a neighboring state by applying a random transformation.

    Possible transformations:
    1. Merge two similar memories
    2. Split a memory into components
    3. Prune a low-relevance memory
    4. Adjust memory weights
    5. Reorder memories

    Args:
        state: Current state of memory fragments

    Returns:
        New state after applying transformation
    """
    if not state:
        return []

    # Create a copy of the state
    new_state = clone_memories(state)

    # Choose a random transformation
    transformation = random.choice([
        "merge", "adjust_weights", "reorder", "prune", "split"
    ])

    try:
        if transformation == "merge" and len(new_state) >= 2:
            apply_merge_transformation(new_state)
        elif transformation == "split" and new_state:
            apply_split_transformation(new_state)
        elif transformation == "prune" and new_state:
            apply_prune_transformation(new_state)
        elif transformation == "adjust_weights" and new_state:
            apply_adjust_weights_transformation(new_state)
        elif transformation == "reorder" and len(new_state) >= 2:
            apply_reorder_transformation(new_state)

    except Exception as e:
        # Log error but continue with original state
        logger.warning(f"Error generating neighbor state: {str(e)}")
        return state

    return new_state


def apply_merge_transformation(state: List[MemoryItem]) -> None:
    """
    Apply merge transformation to the state.

    Args:
        state: Current state to modify
    """
    # Merge two similar memories
    idx1, idx2 = random.sample(range(len(state)), 2)
    mem1, mem2 = state[idx1], state[idx2]

    # Only merge if similarity is above threshold
    if calculate_similarity(mem1, mem2) > 0.4:
        merged = merge_memories(mem1, mem2)
        # Replace the first memory with merged and remove the second
        smaller_idx, larger_idx = (idx1, idx2) if idx1 < idx2 else (idx2, idx1)
        state[smaller_idx] = merged
        state.pop(larger_idx)


def apply_split_transformation(state: List[MemoryItem]) -> None:
    """
    Apply split transformation to the state.

    Args:
        state: Current state to modify
    """
    # Split a memory into components
    idx = random.randrange(len(state))
    memory = state[idx]

    # Only split if memory is complex enough
    if len(memory.content) > 50:
        components = split_memory(memory)
        if len(components) > 1:
            # Replace original with first component and add others
            state[idx] = components[0]
            for comp in components[1:]:
                state.append(comp)


def apply_prune_transformation(state: List[MemoryItem]) -> None:
    """
    Apply prune transformation to the state.

    Args:
        state: Current state to modify
    """
    # Prune a low-relevance memory
    # Sort by relevance and consider bottom 30% as candidates
    candidates = sorted(
        range(len(state)),
        key=lambda i: state[i].relevance_score
    )
    prune_candidates = candidates[:max(1, int(len(candidates) * 0.3))]

    if prune_candidates:
        idx_to_prune = random.choice(prune_candidates)
        state.pop(idx_to_prune)


def apply_adjust_weights_transformation(state: List[MemoryItem]) -> None:
    """
    Apply adjust weights transformation to the state.

    Args:
        state: Current state to modify
    """
    # Adjust memory weights
    idx = random.randrange(len(state))
    memory = state[idx]

    # Adjust relevance score slightly
    adjustment = random.uniform(-0.1, 0.1)
    memory.relevance_score = max(0.0, min(1.0, memory.relevance_score + adjustment))


def apply_reorder_transformation(state: List[MemoryItem]) -> None:
    """
    Apply reorder transformation to the state.

    Args:
        state: Current state to modify
    """
    # Reorder memories (swap two random memories)
    idx1, idx2 = random.sample(range(len(state)), 2)
    state[idx1], state[idx2] = state[idx2], state[idx1]


def merge_memories(mem1: MemoryItem, mem2: MemoryItem) -> MemoryItem:
    """
    Merge two memory fragments into one.

    Args:
        mem1: First memory fragment
        mem2: Second memory fragment

    Returns:
        Merged memory fragment
    """
    # Create a new memory with combined content
    merged = mem1.clone()

    # Combine content intelligently
    if len(mem1.content) > len(mem2.content):
        # Use longer content as base
        merged.content = mem1.content
        # Add unique information from mem2
        if mem2.content not in mem1.content:
            merged.content += f" {mem2.content}"
    else:
        merged.content = mem2.content
        if mem1.content not in mem2.content:
            merged.content = f"{mem1.content} {merged.content}"

    # Take max of creation times
    merged.created_at = max(mem1.created_at, mem2.created_at)

    # Take max of relevance scores
    merged.relevance_score = max(mem1.relevance_score, mem2.relevance_score)

    # Combine tags
    merged.tags = list(set(mem1.tags + mem2.tags))

    return merged


def split_memory(memory: MemoryItem) -> List[MemoryItem]:
    """
    Split a memory fragment into multiple components.

    Args:
        memory: Memory fragment to split

    Returns:
        List of memory fragments after splitting
    """
    # Simple splitting by sentences
    content = memory.content
    sentences = [s.strip() for s in content.split('.') if s.strip()]

    # If not enough sentences return original
    if len(sentences) <= 1:
        return [memory]

    # Group sentences into 1-3 components
    num_components = min(3, max(1, len(sentences) // 2))
    components = []

    sentences_per_component = len(sentences) // num_components
    for i in range(num_components):
        start_idx = i * sentences_per_component
        end_idx = start_idx + sentences_per_component if i < num_components - 1 else len(sentences)

        component_content = '. '.join(sentences[start_idx:end_idx])
        if not component_content.endswith('.'):
            component_content += '.'

        component = memory.clone()
        component.content = component_content
        component.relevance_score = max(0.1, memory.relevance_score - 0.1)
        components.append(component)

    return components


def post_process(state: List[MemoryItem]) -> List[MemoryItem]:
    """
    Perform final post-processing on the optimized state.

    Args:
        state: Optimized state of memory fragments

    Returns:
        Post-processed memory fragments
    """
    if not state:
        return []

    # Create a copy for post-processing
    processed_state = clone_memories(state)

    # Sort memories by relevance (most relevant first)
    processed_state.sort(key=lambda m: m.relevance_score, reverse=True)

    # Normalize relevance scores to [0.1, 1.0] range
    if processed_state:
        min_relevance = min(m.relevance_score for m in processed_state)
        max_relevance = max(m.relevance_score for m in processed_state)

        if max_relevance > min_relevance:
            for memory in processed_state:
                normalized = 0.1 + 0.9 * (memory.relevance_score - min_relevance) / (max_relevance - min_relevance)
                memory.relevance_score = normalized

    return processed_state
