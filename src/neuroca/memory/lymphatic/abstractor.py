"""
Abstractor Module for Lymphatic Memory System

This module implements the Abstractor component of the Lymphatic Memory tier in the
NeuroCognitive Architecture (NCA). The Abstractor is responsible for:

1. Extracting high-level concepts and patterns from working memory
2. Consolidating related information into abstract representations
3. Identifying key relationships between concepts
4. Reducing dimensionality of memory representations
5. Supporting the formation of long-term memory structures

The Abstractor serves as a critical bridge between short-term working memory and
long-term semantic/episodic storage by transforming concrete experiences into
generalized knowledge structures.

Usage:
    abstractor = Abstractor(config)
    abstract_representation = abstractor.process(memory_items)
    consolidated_concepts = abstractor.consolidate(abstract_representation)

Typical workflow:
    1. Receive memory items from working memory
    2. Extract key concepts and relationships
    3. Generate abstract representations
    4. Consolidate similar concepts
    5. Return abstracted memory for storage in semantic/episodic systems
"""

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from neuroca.config.settings import AbstractorConfig
from neuroca.core.exceptions import AbstractionError, ConfigurationError
from neuroca.memory.base import MemoryComponent, MemoryItem
from neuroca.memory.utils.metrics import track_processing_time
from neuroca.memory.utils.validation import validate_memory_items

# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class AbstractConcept:
    """
    Represents an abstracted concept derived from multiple memory items.
    
    Attributes:
        concept_id: Unique identifier for the concept
        name: Human-readable name of the concept
        source_items: List of memory item IDs that contributed to this concept
        attributes: Dictionary of attributes that define this concept
        confidence: Confidence score for this abstraction (0.0-1.0)
        created_at: Timestamp when this concept was created
        updated_at: Timestamp when this concept was last updated
        relationships: Dictionary mapping related concept IDs to relationship types
        embedding: Vector representation of this concept (if available)
    """
    concept_id: str
    name: str
    source_items: list[str]
    attributes: dict[str, Any]
    confidence: float
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    relationships: dict[str, str] = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    
    def __post_init__(self):
        """Validate the concept after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        if not self.concept_id:
            self.concept_id = str(uuid.uuid4())
    
    def update(self, new_attributes: dict[str, Any], new_confidence: Optional[float] = None) -> None:
        """
        Update the concept with new attributes and optionally a new confidence score.
        
        Args:
            new_attributes: New attributes to merge with existing ones
            new_confidence: New confidence score (if provided)
        """
        self.attributes.update(new_attributes)
        if new_confidence is not None:
            if not 0.0 <= new_confidence <= 1.0:
                raise ValueError("Confidence must be between 0.0 and 1.0")
            self.confidence = new_confidence
        self.updated_at = time.time()
    
    def add_relationship(self, related_concept_id: str, relationship_type: str) -> None:
        """
        Add a relationship to another concept.
        
        Args:
            related_concept_id: ID of the related concept
            relationship_type: Type of relationship (e.g., "is_a", "part_of", "similar_to")
        """
        self.relationships[related_concept_id] = relationship_type
        self.updated_at = time.time()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the concept to a dictionary representation."""
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "source_items": self.source_items,
            "attributes": self.attributes,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "relationships": self.relationships,
            "embedding": self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'AbstractConcept':
        """Create a concept from a dictionary representation."""
        return cls(
            concept_id=data["concept_id"],
            name=data["name"],
            source_items=data["source_items"],
            attributes=data["attributes"],
            confidence=data["confidence"],
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            relationships=data.get("relationships", {}),
            embedding=data.get("embedding")
        )


class Abstractor(MemoryComponent):
    """
    The Abstractor component processes memory items to extract abstract concepts,
    patterns, and relationships.
    
    It serves as a key component in the lymphatic memory system, transforming
    concrete experiences into generalized knowledge structures that can be
    efficiently stored and retrieved.
    """
    
    def __init__(self, config: Optional[AbstractorConfig] = None):
        """
        Initialize the Abstractor with configuration settings.
        
        Args:
            config: Configuration settings for the Abstractor
                   If None, default configuration will be used
        
        Raises:
            ConfigurationError: If the provided configuration is invalid
        """
        self.config = config or AbstractorConfig()
        self._validate_config()
        
        # Internal storage for concepts being processed
        self._concept_cache: dict[str, AbstractConcept] = {}
        
        # Tracking metrics
        self._processed_items_count = 0
        self._generated_concepts_count = 0
        
        logger.info(f"Abstractor initialized with config: {self.config}")
    
    def _validate_config(self) -> None:
        """
        Validate the configuration settings.
        
        Raises:
            ConfigurationError: If any configuration setting is invalid
        """
        try:
            if not 0.0 <= self.config.similarity_threshold <= 1.0:
                raise ConfigurationError("similarity_threshold must be between 0.0 and 1.0")
            
            if self.config.min_items_for_abstraction < 1:
                raise ConfigurationError("min_items_for_abstraction must be at least 1")
            
            if self.config.max_attributes_per_concept < 1:
                raise ConfigurationError("max_attributes_per_concept must be at least 1")
                
        except AttributeError as e:
            raise ConfigurationError(f"Missing required configuration: {str(e)}")
    
    @track_processing_time
    def process(self, memory_items: list[MemoryItem]) -> list[AbstractConcept]:
        """
        Process a list of memory items to extract abstract concepts.
        
        Args:
            memory_items: List of memory items to process
        
        Returns:
            List of extracted abstract concepts
        
        Raises:
            AbstractionError: If abstraction process fails
            ValueError: If input validation fails
        """
        logger.debug(f"Processing {len(memory_items)} memory items for abstraction")
        
        try:
            # Validate input
            validate_memory_items(memory_items)
            
            if not memory_items:
                logger.warning("No memory items provided for abstraction")
                return []
            
            # Extract features from memory items
            features = self._extract_features(memory_items)
            
            # Identify patterns and clusters
            clusters = self._identify_clusters(features)
            
            # Generate abstract concepts from clusters
            concepts = self._generate_concepts(clusters, memory_items)
            
            # Update metrics
            self._processed_items_count += len(memory_items)
            self._generated_concepts_count += len(concepts)
            
            logger.info(f"Generated {len(concepts)} abstract concepts from {len(memory_items)} memory items")
            return concepts
            
        except ValueError as e:
            logger.error(f"Validation error during abstraction: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Abstraction process failed: {str(e)}", exc_info=True)
            raise AbstractionError(f"Failed to abstract memory items: {str(e)}")
    
    def _extract_features(self, memory_items: list[MemoryItem]) -> list[dict[str, Any]]:
        """
        Extract relevant features from memory items for abstraction.
        
        Args:
            memory_items: List of memory items to extract features from
        
        Returns:
            List of feature dictionaries
        """
        features = []
        
        for item in memory_items:
            try:
                # Extract key attributes based on item type
                item_features = {
                    "item_id": item.id,
                    "content_type": item.content_type,
                    "importance": getattr(item, "importance", 0.5),
                    "recency": getattr(item, "timestamp", time.time()),
                    "keywords": self._extract_keywords(item),
                    "entities": self._extract_entities(item),
                    "sentiment": self._analyze_sentiment(item),
                    "embedding": getattr(item, "embedding", None)
                }
                
                # Add content-specific features
                if hasattr(item, "content") and item.content and isinstance(item.content, dict):
                    for key, value in item.content.items():
                        if key not in item_features and self._is_relevant_attribute(key):
                            item_features[key] = value
                
                features.append(item_features)
                
            except Exception as e:
                logger.warning(f"Failed to extract features from item {item.id}: {str(e)}")
                # Continue with other items rather than failing completely
        
        logger.debug(f"Extracted features from {len(features)} memory items")
        return features
    
    def _extract_keywords(self, item: MemoryItem) -> list[str]:
        """
        Extract keywords from a memory item.
        
        Args:
            item: Memory item to extract keywords from
        
        Returns:
            List of keywords
        """
        # This is a simplified implementation
        # In a production system, this would use NLP techniques
        keywords = []
        
        if hasattr(item, "keywords") and item.keywords:
            keywords.extend(item.keywords)
        
        if hasattr(item, "content"):
            if isinstance(item.content, str):
                # Simple keyword extraction based on word frequency
                # In production, use proper NLP libraries
                words = item.content.lower().split()
                # Filter out common stop words (simplified)
                stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "with", "by"}
                keywords.extend([w for w in words if w not in stop_words and len(w) > 3])
            elif isinstance(item.content, dict) and "keywords" in item.content:
                keywords.extend(item.content["keywords"])
        
        # Return unique keywords
        return list(set(keywords))[:self.config.max_keywords_per_item]
    
    def _extract_entities(self, item: MemoryItem) -> list[str]:
        """
        Extract named entities from a memory item.
        
        Args:
            item: Memory item to extract entities from
        
        Returns:
            List of entities
        """
        # Simplified implementation
        # In production, use NER from spaCy or similar
        entities = []
        
        if hasattr(item, "entities") and item.entities:
            entities.extend(item.entities)
        
        if hasattr(item, "content") and isinstance(item.content, dict):
            if "entities" in item.content:
                entities.extend(item.content["entities"])
            elif "people" in item.content:
                entities.extend(item.content["people"])
            elif "locations" in item.content:
                entities.extend(item.content["locations"])
        
        return list(set(entities))
    
    def _analyze_sentiment(self, item: MemoryItem) -> float:
        """
        Analyze sentiment of a memory item.
        
        Args:
            item: Memory item to analyze
        
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        # Simplified implementation
        # In production, use a proper sentiment analysis library
        if hasattr(item, "sentiment"):
            return item.sentiment
        
        if hasattr(item, "content"):
            if isinstance(item.content, dict) and "sentiment" in item.content:
                return item.content["sentiment"]
        
        # Default neutral sentiment
        return 0.0
    
    def _is_relevant_attribute(self, attribute: str) -> bool:
        """
        Determine if an attribute is relevant for abstraction.
        
        Args:
            attribute: Attribute name to check
        
        Returns:
            True if the attribute is relevant, False otherwise
        """
        # Ignore internal/system attributes
        if attribute.startswith("_"):
            return False
        
        # Ignore common metadata fields that don't contribute to abstraction
        ignored_attributes = {
            "id", "created_at", "updated_at", "timestamp", "version", 
            "source", "raw_content", "processed", "hash"
        }
        
        return attribute not in ignored_attributes
    
    def _identify_clusters(self, features: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        """
        Identify clusters of related features based on similarity.
        
        Args:
            features: List of feature dictionaries
        
        Returns:
            List of clusters, where each cluster is a list of feature dictionaries
        """
        # Skip clustering if we don't have enough items
        if len(features) < self.config.min_items_for_abstraction:
            logger.debug(f"Not enough items ({len(features)}) for clustering, minimum is {self.config.min_items_for_abstraction}")
            return [[f] for f in features]  # Each item in its own cluster
        
        # Simple clustering based on keyword/entity overlap
        # In production, use more sophisticated clustering algorithms
        clusters = []
        unassigned = features.copy()
        
        while unassigned:
            # Start a new cluster with the first unassigned item
            current = unassigned.pop(0)
            current_cluster = [current]
            
            # Find similar items
            i = 0
            while i < len(unassigned):
                item = unassigned[i]
                if self._calculate_similarity(current, item) >= self.config.similarity_threshold:
                    current_cluster.append(item)
                    unassigned.pop(i)
                else:
                    i += 1
            
            clusters.append(current_cluster)
        
        logger.debug(f"Identified {len(clusters)} clusters from {len(features)} items")
        return clusters
    
    def _calculate_similarity(self, item1: dict[str, Any], item2: dict[str, Any]) -> float:
        """
        Calculate similarity between two items based on their features.
        
        Args:
            item1: First item features
            item2: Second item features
        
        Returns:
            Similarity score (0.0-1.0)
        """
        # If embeddings are available, use cosine similarity
        if "embedding" in item1 and "embedding" in item2 and item1["embedding"] and item2["embedding"]:
            return self._cosine_similarity(item1["embedding"], item2["embedding"])
        
        # Otherwise, use feature overlap
        score = 0.0
        total_weight = 0.0
        
        # Compare keywords (higher weight)
        keyword_similarity = self._jaccard_similarity(
            set(item1.get("keywords", [])), 
            set(item2.get("keywords", []))
        )
        score += keyword_similarity * 0.4
        total_weight += 0.4
        
        # Compare entities (higher weight)
        entity_similarity = self._jaccard_similarity(
            set(item1.get("entities", [])), 
            set(item2.get("entities", []))
        )
        score += entity_similarity * 0.4
        total_weight += 0.4
        
        # Compare content type
        if item1.get("content_type") == item2.get("content_type"):
            score += 0.1
        total_weight += 0.1
        
        # Compare sentiment
        sentiment_diff = abs(item1.get("sentiment", 0) - item2.get("sentiment", 0))
        sentiment_similarity = max(0, 1 - sentiment_diff)
        score += sentiment_similarity * 0.1
        total_weight += 0.1
        
        # Normalize score
        return score / total_weight if total_weight > 0 else 0.0
    
    def _jaccard_similarity(self, set1: set[Any], set2: set[Any]) -> float:
        """
        Calculate Jaccard similarity between two sets.
        
        Args:
            set1: First set
            set2: Second set
        
        Returns:
            Jaccard similarity (0.0-1.0)
        """
        if not set1 and not set2:
            return 1.0  # Both empty sets are considered identical
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Cosine similarity (0.0-1.0)
        """
        if len(vec1) != len(vec2):
            logger.warning(f"Vector dimensions don't match: {len(vec1)} vs {len(vec2)}")
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _generate_concepts(
        self, 
        clusters: list[list[dict[str, Any]]], 
        memory_items: list[MemoryItem]
    ) -> list[AbstractConcept]:
        """
        Generate abstract concepts from clusters of features.
        
        Args:
            clusters: List of feature clusters
            memory_items: Original memory items (for reference)
        
        Returns:
            List of abstract concepts
        """
        concepts = []
        item_map = {item.id: item for item in memory_items}
        
        for cluster in clusters:
            # Skip clusters that are too small
            if len(cluster) < self.config.min_items_for_abstraction:
                continue
            
            try:
                # Extract common attributes
                common_keywords = self._find_common_elements([item.get("keywords", []) for item in cluster])
                common_entities = self._find_common_elements([item.get("entities", []) for item in cluster])
                
                # Generate a name for the concept
                concept_name = self._generate_concept_name(common_keywords, common_entities, cluster)
                
                # Calculate confidence based on cluster cohesion
                confidence = self._calculate_cluster_confidence(cluster)
                
                # Collect source item IDs
                source_items = [item["item_id"] for item in cluster]
                
                # Generate a stable concept ID based on content
                concept_id = self._generate_concept_id(concept_name, source_items)
                
                # Create attributes dictionary
                attributes = {
                    "common_keywords": common_keywords[:self.config.max_keywords_per_concept],
                    "common_entities": common_entities[:self.config.max_entities_per_concept],
                    "content_type": self._most_common_value([item.get("content_type") for item in cluster]),
                    "average_sentiment": sum(item.get("sentiment", 0) for item in cluster) / len(cluster),
                    "cluster_size": len(cluster),
                    "importance": self._calculate_importance(cluster, item_map)
                }
                
                # Add additional attributes if they appear in most items
                for key in self._find_common_attributes(cluster):
                    if key not in attributes and len(attributes) < self.config.max_attributes_per_concept:
                        attributes[key] = self._most_common_value([item.get(key) for item in cluster if key in item])
                
                # Create embedding by averaging item embeddings (if available)
                embedding = self._average_embeddings([item.get("embedding") for item in cluster])
                
                # Create the concept
                concept = AbstractConcept(
                    concept_id=concept_id,
                    name=concept_name,
                    source_items=source_items,
                    attributes=attributes,
                    confidence=confidence,
                    embedding=embedding
                )
                
                concepts.append(concept)
                
                # Cache the concept for future reference
                self._concept_cache[concept_id] = concept
                
            except Exception as e:
                logger.warning(f"Failed to generate concept from cluster: {str(e)}")
                # Continue with other clusters
        
        return concepts
    
    def _find_common_elements(self, lists: list[list[Any]]) -> list[Any]:
        """
        Find elements that appear in multiple lists.
        
        Args:
            lists: List of lists to analyze
        
        Returns:
            List of common elements sorted by frequency
        """
        if not lists:
            return []
        
        # Count occurrences of each element
        counts = {}
        for lst in lists:
            for item in lst:
                counts[item] = counts.get(item, 0) + 1
        
        # Filter elements that appear in at least half of the lists
        threshold = max(1, len(lists) // 2)
        common = [item for item, count in counts.items() if count >= threshold]
        
        # Sort by frequency
        return sorted(common, key=lambda x: counts[x], reverse=True)
    
    def _find_common_attributes(self, items: list[dict[str, Any]]) -> list[str]:
        """
        Find attribute keys that appear in multiple items.
        
        Args:
            items: List of item dictionaries
        
        Returns:
            List of common attribute keys
        """
        if not items:
            return []
        
        # Count occurrences of each attribute key
        counts = {}
        for item in items:
            for key in item:
                if self._is_relevant_attribute(key):
                    counts[key] = counts.get(key, 0) + 1
        
        # Filter keys that appear in at least half of the items
        threshold = max(1, len(items) // 2)
        common = [key for key, count in counts.items() if count >= threshold]
        
        # Sort by frequency
        return sorted(common, key=lambda x: counts[x], reverse=True)
    
    def _most_common_value(self, values: list[Any]) -> Any:
        """
        Find the most common value in a list.
        
        Args:
            values: List of values
        
        Returns:
            Most common value
        """
        if not values:
            return None
        
        # Count occurrences
        counts = {}
        for value in values:
            if value is not None:
                counts[value] = counts.get(value, 0) + 1
        
        # Return the most common value
        return max(counts.items(), key=lambda x: x[1])[0] if counts else None
    
    def _generate_concept_name(
        self, 
        keywords: list[str], 
        entities: list[str], 
        cluster: list[dict[str, Any]]
    ) -> str:
        """
        Generate a descriptive name for a concept.
        
        Args:
            keywords: Common keywords in the cluster
            entities: Common entities in the cluster
            cluster: The cluster of items
        
        Returns:
            Concept name
        """
        # Try to use the most common entity
        if entities:
            return entities[0].title()
        
        # Try to use the most common keyword
        if keywords:
            return keywords[0].title()
        
        # Use the most common content type
        content_types = [item.get("content_type") for item in cluster if "content_type" in item]
        if content_types:
            content_type = self._most_common_value(content_types)
            return f"{content_type.replace('_', ' ').title()} Concept"
        
        # Fallback
        return f"Abstract Concept {uuid.uuid4().hex[:8]}"
    
    def _generate_concept_id(self, name: str, source_items: list[str]) -> str:
        """
        Generate a stable concept ID based on content.
        
        Args:
            name: Concept name
            source_items: Source item IDs
        
        Returns:
            Concept ID
        """
        # Sort source items for stability
        sorted_items = sorted(source_items)
        
        # Create a hash of the name and source items
        content = name + "".join(sorted_items)
        hash_obj = hashlib.sha256(content.encode())
        
        return f"concept-{hash_obj.hexdigest()[:16]}"
    
    def _calculate_cluster_confidence(self, cluster: list[dict[str, Any]]) -> float:
        """
        Calculate confidence score for a cluster based on cohesion.
        
        Args:
            cluster: Cluster of items
        
        Returns:
            Confidence score (0.0-1.0)
        """
        if len(cluster) <= 1:
            return 0.5  # Default confidence for single-item clusters
        
        # Calculate average pairwise similarity
        total_similarity = 0.0
        pair_count = 0
        
        for i in range(len(cluster)):
            for j in range(i + 1, len(cluster)):
                similarity = self._calculate_similarity(cluster[i], cluster[j])
                total_similarity += similarity
                pair_count += 1
        
        avg_similarity = total_similarity / pair_count if pair_count > 0 else 0.0
        
        # Adjust confidence based on cluster size
        size_factor = min(1.0, len(cluster) / self.config.optimal_cluster_size)
        
        # Combine factors
        confidence = 0.7 * avg_similarity + 0.3 * size_factor
        
        return min(1.0, max(0.1, confidence))
    
    def _calculate_importance(self, cluster: list[dict[str, Any]], item_map: dict[str, MemoryItem]) -> float:
        """
        Calculate importance score for a concept based on source items.
        
        Args:
            cluster: Cluster of items
            item_map: Mapping of item IDs to memory items
        
        Returns:
            Importance score (0.0-1.0)
        """
        # Average importance of source items
        total_importance = 0.0
        count = 0
        
        for item in cluster:
            item_id = item.get("item_id")
            if item_id in item_map:
                importance = getattr(item_map[item_id], "importance", 0.5)
                total_importance += importance
                count += 1
        
        avg_importance = total_importance / count if count > 0 else 0.5
        
        # Adjust based on cluster size
        size_factor = min(1.0, len(cluster) / self.config.optimal_cluster_size)
        
        # Combine factors
        return min(1.0, max(0.1, 0.7 * avg_importance + 0.3 * size_factor))
    
    def _average_embeddings(self, embeddings: list[Optional[list[float]]]) -> Optional[list[float]]:
        """
        Average multiple embeddings into a single embedding.
        
        Args:
            embeddings: List of embeddings
        
        Returns:
            Averaged embedding or None if no valid embeddings
        """
        # Filter out None values
        valid_embeddings = [e for e in embeddings if e is not None]
        
        if not valid_embeddings:
            return None
        
        # Check dimensions
        dim = len(valid_embeddings[0])
        if not all(len(e) == dim for e in valid_embeddings):
            logger.warning("Embeddings have inconsistent dimensions, cannot average")
            return None
        
        # Calculate average
        avg_embedding = [0.0] * dim
        for embedding in valid_embeddings:
            for i, value in enumerate(embedding):
                avg_embedding[i] += value
        
        avg_embedding = [val / len(valid_embeddings) for val in avg_embedding]
        
        # Normalize
        magnitude = sum(val * val for val in avg_embedding) ** 0.5
        if magnitude > 0:
            avg_embedding = [val / magnitude for val in avg_embedding]
        
        return avg_embedding
    
    @track_processing_time
    def consolidate(self, concepts: list[AbstractConcept]) -> list[AbstractConcept]:
        """
        Consolidate similar concepts into more general abstractions.
        
        Args:
            concepts: List of concepts to consolidate
        
        Returns:
            List of consolidated concepts
        
        Raises:
            AbstractionError: If consolidation process fails
        """
        logger.debug(f"Consolidating {len(concepts)} concepts")
        
        try:
            if len(concepts) <= 1:
                return concepts
            
            # Find similar concepts
            consolidated = []
            remaining = concepts.copy()
            
            while remaining:
                current = remaining.pop(0)
                similar = []
                
                # Find similar concepts
                i = 0
                while i < len(remaining):
                    if self._are_concepts_similar(current, remaining[i]):
                        similar.append(remaining.pop(i))
                    else:
                        i += 1
                
                if not similar:
                    # No similar concepts found, keep as is
                    consolidated.append(current)
                else:
                    # Merge similar concepts
                    merged = self._merge_concepts(current, similar)
                    consolidated.append(merged)
            
            logger.info(f"Consolidated {len(concepts)} concepts into {len(consolidated)} concepts")
            return consolidated
            
        except Exception as e:
            logger.error(f"Consolidation process failed: {str(e)}", exc_info=True)
            raise AbstractionError(f"Failed to consolidate concepts: {str(e)}")
    
    def _are_concepts_similar(self, concept1: AbstractConcept, concept2: AbstractConcept) -> bool:
        """
        Determine if two concepts are similar enough to be consolidated.
        
        Args:
            concept1: First concept
            concept2: Second concept
        
        Returns:
            True if concepts are similar, False otherwise
        """
        # Check embeddings first if available
        if concept1.embedding and concept2.embedding:
            similarity = self._cosine_similarity(concept1.embedding, concept2.embedding)
            if similarity >= self.config.concept_similarity_threshold:
                return True
        
        # Check keyword overlap
        keywords1 = set(concept1.attributes.get("common_keywords", []))
        keywords2 = set(concept2.attributes.get("common_keywords", []))
        keyword_similarity = self._jaccard_similarity(keywords1, keywords2)
        
        # Check entity overlap
        entities1 = set(concept1.attributes.get("common_entities", []))
        entities2 = set(concept2.attributes.get("common_entities", []))
        entity_similarity = self._jaccard_similarity(entities1, entities2)
        
        # Calculate overall similarity
        overall_similarity = 0.5 * keyword_similarity + 0.5 * entity_similarity
        
        return overall_similarity >= self.config.concept_similarity_threshold
    
    def _merge_concepts(self, base: AbstractConcept, similar: list[AbstractConcept]) -> AbstractConcept:
        """
        Merge similar concepts into a single consolidated concept.
        
        Args:
            base: Base concept
            similar: List of similar concepts to merge
        
        Returns:
            Consolidated concept
        """
        # Combine source items
        all_concepts = [base] + similar
        source_items = list(set().union(*[set(c.source_items) for c in all_concepts]))
        
        # Combine keywords and entities
        all_keywords = []
        all_entities = []
        
        for concept in all_concepts:
            all_keywords.extend(concept.attributes.get("common_keywords", []))
            all_entities.extend(concept.attributes.get("common_entities", []))
        
        # Count frequencies
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        entity_counts = {}
        for entity in all_entities:
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
        
        # Select most common
        common_keywords = sorted(keyword_counts.keys(), key=lambda k: keyword_counts[k], reverse=True)
        common_entities = sorted(entity_counts.keys(), key=lambda e: entity_counts[e], reverse=True)
        
        # Generate name for consolidated concept
        if common_entities:
            name = common_entities[0].title()
        elif common_keywords:
            name = common_keywords[0].title()
        else:
            name = base.name
        
        # Calculate average importance
        avg_importance = sum(c.attributes.get("importance", 0.5) for c in all_concepts) / len(all_concepts)
        
        # Create attributes
        attributes = {
            "common_keywords": common_keywords[:self.config.max_keywords_per_concept],
            "common_entities": common_entities[:self.config.max_entities_per_concept],
            "content_type": base.attributes.get("content_type"),
            "average_sentiment": sum(c.attributes.get("average_sentiment", 0) for c in all_concepts) / len(all_concepts),
            "cluster_size": sum(c.attributes.get("cluster_size", 1) for c in all_concepts),
            "importance": avg_importance,
            "consolidated_from": [c.concept_id for c in all_concepts]
        }
        
        # Calculate confidence
        confidence = sum(c.confidence for c in all_concepts) / len(all_concepts)
        
        # Average embeddings
        embedding = self._average_embeddings([c.embedding for c in all_concepts])
        
        # Combine relationships
        relationships = {}
        for concept in all_concepts:
            relationships.update(concept.relationships)
        
        # Create consolidated concept
        consolidated = AbstractConcept(
            concept_id=f"consolidated-{uuid.uuid4().hex[:12]}",
            name=name,
            source_items=source_items,
            attributes=attributes,
            confidence=confidence,
            embedding=embedding,
            relationships=relationships
        )
        
        return consolidated
    
    def get_metrics(self) -> dict[str, Any]:
        """
        Get performance metrics for the Abstractor.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "processed_items_count": self._processed_items_count,
            "generated_concepts_count": self._generated_concepts_count,
            "concept_cache_size": len(self._concept_cache),
            "average_concepts_per_batch": (
                self._generated_concepts_count / (self._processed_items_count / self.config.min_items_for_abstraction)
                if self._processed_items_count > 0 else 0
            )
        }
    
    def clear_cache(self) -> None:
        """Clear the internal concept cache."""
        self._concept_cache.clear()
        logger.info("Abstractor concept cache cleared")
    
    def save_state(self, file_path: str) -> None:
        """
        Save the current state of the Abstractor to a file.
        
        Args:
            file_path: Path to save the state to
        
        Raises:
            IOError: If saving fails
        """
        try:
            state = {
                "concept_cache": {k: v.to_dict() for k, v in self._concept_cache.items()},
                "metrics": self.get_metrics()
            }
            
            with open(file_path, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Abstractor state saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save Abstractor state: {str(e)}", exc_info=True)
            raise OSError(f"Failed to save Abstractor state: {str(e)}")
    
    def load_state(self, file_path: str) -> None:
        """
        Load the state of the Abstractor from a file.
        
        Args:
            file_path: Path to load the state from
        
        Raises:
            IOError: If loading fails
        """
        try:
            with open(file_path) as f:
                state = json.load(f)
            
            # Restore concept cache
            self._concept_cache = {
                k: AbstractConcept.from_dict(v) 
                for k, v in state.get("concept_cache", {}).items()
            }
            
            # Restore metrics
            metrics = state.get("metrics", {})
            self._processed_items_count = metrics.get("processed_items_count", 0)
            self._generated_concepts_count = metrics.get("generated_concepts_count", 0)
            
            logger.info(f"Abstractor state loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load Abstractor state: {str(e)}", exc_info=True)
            raise OSError(f"Failed to load Abstractor state: {str(e)}")