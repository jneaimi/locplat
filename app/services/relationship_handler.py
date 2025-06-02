"""
Collection Relationships Handler for Directus Integration
========================================================

Handles complex collection relationships including:
- Many-to-one relationships
- One-to-many relationships  
- Many-to-many relationships
- Circular reference prevention
- Deep nested structure support
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from ..services.field_mapper import FieldMapper
from ..services.integrated_translation_service import IntegratedTranslationService


class RelationshipType(Enum):
    """Types of Directus relationships."""
    MANY_TO_ONE = "many_to_one"  # Foreign key
    ONE_TO_MANY = "one_to_many"  # Reverse of foreign key
    MANY_TO_MANY = "many_to_many"  # Junction table
    ONE_TO_ONE = "one_to_one"  # Unique foreign key


@dataclass
class RelationshipConfig:
    """Configuration for a relationship between collections."""
    source_collection: str
    source_field: str
    target_collection: str
    target_field: str
    relationship_type: RelationshipType
    junction_collection: Optional[str] = None  # For many-to-many
    max_depth: int = 3  # Maximum traversal depth
    translate_related: bool = True  # Whether to translate related items


@dataclass
class TranslationContext:
    """Context for tracking translation state across relationships."""
    visited_items: Set[Tuple[str, Any]]  # (collection, item_id) pairs
    current_depth: int = 0
    max_depth: int = 3
    client_id: str = ""
    source_lang: str = "en"
    target_lang: str = "ar"
    provider: str = "openai"
    api_key: str = ""


class DirectusRelationshipHandler:
    """
    Handles complex Directus collection relationships for translation.
    """
    
    def __init__(self, field_mapper: FieldMapper, translation_service: IntegratedTranslationService):
        self.field_mapper = field_mapper
        self.translation_service = translation_service
        self.relationship_cache: Dict[str, List[RelationshipConfig]] = {}
        
    async def get_collection_relationships(self, collection: str) -> List[RelationshipConfig]:
        """
        Get all relationships for a collection.
        In production, this would query Directus API.
        """
        if collection in self.relationship_cache:
            return self.relationship_cache[collection]
            
        # Mock relationship data - in production this would come from Directus API
        mock_relationships = {
            "articles": [
                RelationshipConfig(
                    source_collection="articles",
                    source_field="category_id",
                    target_collection="categories",
                    target_field="id",
                    relationship_type=RelationshipType.MANY_TO_ONE
                ),
                RelationshipConfig(
                    source_collection="articles",
                    source_field="author_id",
                    target_collection="authors",
                    target_field="id",
                    relationship_type=RelationshipType.MANY_TO_ONE
                ),
                RelationshipConfig(
                    source_collection="articles",
                    source_field="id",
                    target_collection="comments",
                    target_field="article_id",
                    relationship_type=RelationshipType.ONE_TO_MANY
                ),
                RelationshipConfig(
                    source_collection="articles",
                    source_field="tags",
                    target_collection="tags",
                    target_field="id",
                    relationship_type=RelationshipType.MANY_TO_MANY,
                    junction_collection="articles_tags"
                )
            ],
            "categories": [
                RelationshipConfig(
                    source_collection="categories",
                    source_field="parent_id",
                    target_collection="categories",
                    target_field="id",
                    relationship_type=RelationshipType.MANY_TO_ONE
                ),
                RelationshipConfig(
                    source_collection="categories",
                    source_field="id",
                    target_collection="articles",
                    target_field="category_id",
                    relationship_type=RelationshipType.ONE_TO_MANY
                )
            ],
            "authors": [
                RelationshipConfig(
                    source_collection="authors",
                    source_field="id",
                    target_collection="articles",
                    target_field="author_id",
                    relationship_type=RelationshipType.ONE_TO_MANY
                )
            ],
            "comments": [
                RelationshipConfig(
                    source_collection="comments",
                    source_field="article_id",
                    target_collection="articles",
                    target_field="id",
                    relationship_type=RelationshipType.MANY_TO_ONE
                ),
                RelationshipConfig(
                    source_collection="comments",
                    source_field="parent_id",
                    target_collection="comments",
                    target_field="id",
                    relationship_type=RelationshipType.MANY_TO_ONE
                )
            ]
        }
        
        relationships = mock_relationships.get(collection, [])
        self.relationship_cache[collection] = relationships
        return relationships
    
    async def translate_with_relationships(
        self,
        content: Dict[str, Any],
        collection: str,
        context: TranslationContext
    ) -> Dict[str, Any]:
        """
        Translate content including related items.
        
        Args:
            content: The main content to translate
            collection: The collection name
            context: Translation context with settings and tracking
            
        Returns:
            Translated content with related items
        """
        # Prevent infinite recursion
        item_id = content.get("id", "unknown")
        item_key = (collection, item_id)
        
        if item_key in context.visited_items:
            return {"_circular_reference": True, "collection": collection, "id": item_id}
            
        if context.current_depth >= context.max_depth:
            return {"_max_depth_reached": True, "collection": collection, "id": item_id}
        
        # Mark this item as visited
        context.visited_items.add(item_key)
        
        try:
            # Translate the main content
            translated_content = await self._translate_main_content(
                content, collection, context
            )
            
            # Get relationships for this collection
            relationships = await self.get_collection_relationships(collection)
            
            # Process each relationship
            for relationship in relationships:
                if not relationship.translate_related:
                    continue
                    
                # Create new context for related items
                related_context = TranslationContext(
                    visited_items=context.visited_items.copy(),
                    current_depth=context.current_depth + 1,
                    max_depth=context.max_depth,
                    client_id=context.client_id,
                    source_lang=context.source_lang,
                    target_lang=context.target_lang,
                    provider=context.provider,
                    api_key=context.api_key
                )
                
                # Process relationship based on type
                if relationship.relationship_type == RelationshipType.MANY_TO_ONE:
                    translated_content = await self._handle_many_to_one(
                        translated_content, relationship, related_context
                    )
                elif relationship.relationship_type == RelationshipType.ONE_TO_MANY:
                    translated_content = await self._handle_one_to_many(
                        translated_content, relationship, related_context
                    )
                elif relationship.relationship_type == RelationshipType.MANY_TO_MANY:
                    translated_content = await self._handle_many_to_many(
                        translated_content, relationship, related_context
                    )
            
            return translated_content
            
        finally:
            # Remove from visited items when done with this branch
            context.visited_items.discard(item_key)
    
    async def _translate_main_content(
        self, 
        content: Dict[str, Any], 
        collection: str, 
        context: TranslationContext
    ) -> Dict[str, Any]:
        """Translate the main content fields."""
        try:
            result = await self.translation_service.translate_structured_content(
                content=content,
                client_id=context.client_id,
                collection_name=collection,
                source_lang=context.source_lang,
                target_lang=context.target_lang,
                provider=context.provider,
                api_key=context.api_key
            )
            return result
        except Exception as e:
            # Return original content if translation fails
            return {**content, "_translation_error": str(e)}
    
    async def _handle_many_to_one(
        self,
        content: Dict[str, Any],
        relationship: RelationshipConfig,
        context: TranslationContext
    ) -> Dict[str, Any]:
        """Handle many-to-one relationship (foreign key)."""
        source_field = relationship.source_field
        
        # Check if the foreign key field exists and has a value
        if source_field not in content or not content[source_field]:
            return content
        
        # For many-to-one, we might have the related object embedded
        related_item = content.get(source_field)
        
        # If it's just an ID, create a placeholder
        if isinstance(related_item, (int, str)):
            content[f"{source_field}_translated"] = {
                "id": related_item,
                "collection": relationship.target_collection,
                "_relation_type": "many_to_one",
                "_not_expanded": True
            }
            return content
        
        # If it's an object, translate it
        if isinstance(related_item, dict):
            translated_related = await self.translate_with_relationships(
                related_item,
                relationship.target_collection,
                context
            )
            content[f"{source_field}_translated"] = translated_related
        
        return content
    
    async def _handle_one_to_many(
        self,
        content: Dict[str, Any],
        relationship: RelationshipConfig,
        context: TranslationContext
    ) -> Dict[str, Any]:
        """Handle one-to-many relationship (reverse foreign key)."""
        # In one-to-many, the related items would be in a separate field
        # This is typically handled by Directus when expanding relationships
        
        related_field_name = f"{relationship.target_collection}_items"
        
        # Check if related items are included
        if related_field_name not in content:
            # Mock some related items for demonstration
            content[f"{related_field_name}_translated"] = {
                "_relation_type": "one_to_many",
                "_target_collection": relationship.target_collection,
                "_not_expanded": True,
                "count": 0
            }
            return content
        
        related_items = content[related_field_name]
        if not isinstance(related_items, list):
            return content
        
        # Translate each related item
        translated_items = []
        for item in related_items:
            if isinstance(item, dict):
                translated_item = await self.translate_with_relationships(
                    item,
                    relationship.target_collection,
                    context
                )
                translated_items.append(translated_item)
            else:
                translated_items.append(item)
        
        content[f"{related_field_name}_translated"] = translated_items
        return content
    
    async def _handle_many_to_many(
        self,
        content: Dict[str, Any],
        relationship: RelationshipConfig,
        context: TranslationContext
    ) -> Dict[str, Any]:
        """Handle many-to-many relationship (junction table)."""
        source_field = relationship.source_field
        
        # Check if the many-to-many field exists
        if source_field not in content:
            return content
        
        related_items = content[source_field]
        if not isinstance(related_items, list):
            return content
        
        # Translate each related item
        translated_items = []
        for item in related_items:
            if isinstance(item, dict):
                # For many-to-many, items might be in junction format
                if relationship.junction_collection and "item" in item:
                    # Junction table format: {id: 1, item: {actual_item_data}}
                    actual_item = item["item"]
                    translated_item = await self.translate_with_relationships(
                        actual_item,
                        relationship.target_collection,
                        context
                    )
                    translated_items.append({
                        **item,
                        "item_translated": translated_item
                    })
                else:
                    # Direct format
                    translated_item = await self.translate_with_relationships(
                        item,
                        relationship.target_collection,
                        context
                    )
                    translated_items.append(translated_item)
            else:
                translated_items.append(item)
        
        content[f"{source_field}_translated"] = translated_items
        return content
    
    async def analyze_relationship_complexity(
        self, 
        collection: str, 
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze the complexity of relationships for a collection.
        
        Returns information about relationship depth, circular references,
        and translation recommendations.
        """
        relationships = await self.get_collection_relationships(collection)
        
        # Traverse relationships to find complexity
        visited = set()
        complexity_info = {
            "collection": collection,
            "direct_relationships": len(relationships),
            "relationship_types": {},
            "circular_references": [],
            "max_depth_found": 0,
            "complexity_score": 0,
            "recommendations": []
        }
        
        # Count relationship types
        for rel in relationships:
            rel_type = rel.relationship_type.value
            complexity_info["relationship_types"][rel_type] = (
                complexity_info["relationship_types"].get(rel_type, 0) + 1
            )
        
        # Analyze depth and circular references
        await self._analyze_depth_recursively(
            collection, 0, max_depth, visited, complexity_info
        )
        
        # Calculate complexity score
        complexity_info["complexity_score"] = self._calculate_complexity_score(
            complexity_info
        )
        
        # Generate recommendations
        complexity_info["recommendations"] = self._generate_relationship_recommendations(
            complexity_info
        )
        
        return complexity_info
    
    async def _analyze_depth_recursively(
        self,
        collection: str,
        current_depth: int,
        max_depth: int,
        visited: Set[str],
        complexity_info: Dict[str, Any]
    ):
        """Recursively analyze relationship depth."""
        if current_depth >= max_depth or collection in visited:
            if collection in visited:
                complexity_info["circular_references"].append(collection)
            return
        
        visited.add(collection)
        complexity_info["max_depth_found"] = max(
            complexity_info["max_depth_found"], current_depth
        )
        
        relationships = await self.get_collection_relationships(collection)
        for rel in relationships:
            await self._analyze_depth_recursively(
                rel.target_collection,
                current_depth + 1,
                max_depth,
                visited.copy(),
                complexity_info
            )
    
    def _calculate_complexity_score(self, complexity_info: Dict[str, Any]) -> int:
        """Calculate a complexity score for the relationship structure."""
        score = 0
        
        # Base score from direct relationships
        score += complexity_info["direct_relationships"] * 10
        
        # Add score based on relationship types
        type_scores = {
            "many_to_one": 5,
            "one_to_many": 15,
            "many_to_many": 25,
            "one_to_one": 3
        }
        
        for rel_type, count in complexity_info["relationship_types"].items():
            score += type_scores.get(rel_type, 0) * count
        
        # Add score for depth
        score += complexity_info["max_depth_found"] * 20
        
        # Add penalty for circular references
        score += len(complexity_info["circular_references"]) * 50
        
        return score
    
    def _generate_relationship_recommendations(
        self, complexity_info: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on complexity analysis."""
        recommendations = []
        
        score = complexity_info["complexity_score"]
        
        if score < 50:
            recommendations.append("Low complexity - standard translation settings recommended")
        elif score < 150:
            recommendations.append("Medium complexity - consider limiting relationship depth to 2-3 levels")
        else:
            recommendations.append("High complexity - limit relationship depth to 1-2 levels for performance")
        
        if len(complexity_info["circular_references"]) > 0:
            recommendations.append("Circular references detected - ensure proper cycle detection is enabled")
        
        many_to_many_count = complexity_info["relationship_types"].get("many_to_many", 0)
        if many_to_many_count > 3:
            recommendations.append("Many many-to-many relationships - consider selective translation")
        
        one_to_many_count = complexity_info["relationship_types"].get("one_to_many", 0)
        if one_to_many_count > 5:
            recommendations.append("Many one-to-many relationships - use batch processing for better performance")
        
        if complexity_info["max_depth_found"] > 4:
            recommendations.append("Deep nesting detected - consider flattening structure or limiting depth")
        
        return recommendations


class RelationshipAwareTranslationService:
    """
    Enhanced translation service that handles relationships.
    """
    
    def __init__(self, field_mapper: FieldMapper, translation_service: IntegratedTranslationService):
        self.relationship_handler = DirectusRelationshipHandler(field_mapper, translation_service)
    
    async def translate_with_relationships(
        self,
        content: Dict[str, Any],
        client_id: str,
        collection_name: str,
        source_lang: str = "en",
        target_lang: str = "ar",
        provider: str = "openai",
        api_key: str = "",
        max_depth: int = 3,
        translate_related: bool = True
    ) -> Dict[str, Any]:
        """
        Translate content including all related items.
        
        Args:
            content: Content to translate
            client_id: Client identifier
            collection_name: Primary collection name
            source_lang: Source language code
            target_lang: Target language code
            provider: AI provider
            api_key: API key
            max_depth: Maximum relationship traversal depth
            translate_related: Whether to translate related items
            
        Returns:
            Translated content with relationships
        """
        context = TranslationContext(
            visited_items=set(),
            current_depth=0,
            max_depth=max_depth,
            client_id=client_id,
            source_lang=source_lang,
            target_lang=target_lang,
            provider=provider,
            api_key=api_key
        )
        
        return await self.relationship_handler.translate_with_relationships(
            content, collection_name, context
        )
    
    async def analyze_collection_relationships(
        self,
        collection: str,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """Analyze relationship complexity for a collection."""
        return await self.relationship_handler.analyze_relationship_complexity(
            collection, max_depth
        )
