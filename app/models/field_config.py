"""Field Configuration Models for LocPlat Translation Service"""

from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from typing import Dict, Any

Base = declarative_base()


class FieldConfig(Base):
    """Database model for storing field mapping configurations."""
    __tablename__ = 'field_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(255), nullable=False, index=True)
    collection_name = Column(String(255), nullable=False, index=True)
    
    # Field configuration
    field_paths = Column(JSON, nullable=False, default=list)
    field_types = Column(JSON, nullable=True, default=dict)
    
    # Directus-specific configurations
    is_translation_collection = Column(Boolean, default=False)
    primary_collection = Column(String(255), nullable=True)
    directus_translation_pattern = Column(String(50), nullable=True, default='collection_translations')
    
    # Language-specific configurations
    rtl_field_mapping = Column(JSON, nullable=True, default=dict)
    language_field_overrides = Column(JSON, nullable=True, default=dict)
    
    # Processing configurations
    batch_processing = Column(Boolean, default=False)
    preserve_html_structure = Column(Boolean, default=True)
    content_sanitization = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional configuration
    custom_transformations = Column(JSON, nullable=True, default=dict)
    validation_rules = Column(JSON, nullable=True, default=dict)

    def __repr__(self):
        return f"<FieldConfig(id={self.id}, client='{self.client_id}', collection='{self.collection_name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for JSON serialization."""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'collection_name': self.collection_name,
            'field_paths': self.field_paths or [],
            'field_types': self.field_types or {},
            'is_translation_collection': self.is_translation_collection,
            'primary_collection': self.primary_collection,
            'directus_translation_pattern': self.directus_translation_pattern,
            'rtl_field_mapping': self.rtl_field_mapping or {},
            'language_field_overrides': self.language_field_overrides or {},
            'batch_processing': self.batch_processing,
            'preserve_html_structure': self.preserve_html_structure,
            'content_sanitization': self.content_sanitization,
            'custom_transformations': self.custom_transformations or {},
            'validation_rules': self.validation_rules or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldConfig':
        """Create a FieldConfig instance from a dictionary."""
        data = data.copy()
        data.pop('id', None)
        data.pop('created_at', None)
        data.pop('updated_at', None)
        return cls(**data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update the instance with values from a dictionary."""
        updatable_fields = {
            'field_paths', 'field_types', 'is_translation_collection',
            'primary_collection', 'directus_translation_pattern',
            'rtl_field_mapping', 'language_field_overrides',
            'batch_processing', 'preserve_html_structure',
            'content_sanitization', 'custom_transformations',
            'validation_rules'
        }
        
        for key, value in data.items():
            if key in updatable_fields and hasattr(self, key):
                setattr(self, key, value)


class FieldProcessingLog(Base):
    """Log model for tracking field processing operations."""
    __tablename__ = 'field_processing_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(255), nullable=False, index=True)
    collection_name = Column(String(255), nullable=False, index=True)
    field_config_id = Column(Integer, nullable=True)
    operation_type = Column(String(50), nullable=False)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def create_tables(engine):
    """Create all field mapping related tables."""
    Base.metadata.create_all(engine)


__all__ = ['FieldConfig', 'FieldProcessingLog', 'Base', 'create_tables']
