"""Field Mapping API Endpoints for LocPlat Translation Service"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from ..services.field_mapper import FieldMapper
from ..models.field_config import FieldConfig
from ..models.field_types import DirectusTranslationPattern, FieldType


from ..database import get_db


router = APIRouter(prefix="/api/v1/field-mapping", tags=["field-mapping"])


class FieldConfigRequest(BaseModel):
    """Request model for field configuration."""
    client_id: str = Field(..., description="Client identifier")
    collection_name: str = Field(..., description="Directus collection name")
    field_paths: List[str] = Field(default=[], description="List of field paths to translate")
    field_types: Dict[str, str] = Field(default={}, description="Field type mappings")
    is_translation_collection: bool = Field(default=False, description="Is this a translation collection")
    primary_collection: Optional[str] = Field(None, description="Primary collection name")
    directus_translation_pattern: str = Field(
        default=DirectusTranslationPattern.COLLECTION_TRANSLATIONS.value,
        description="Directus translation pattern"
    )
    rtl_field_mapping: Dict[str, Any] = Field(default={}, description="RTL language field mappings")
    batch_processing: bool = Field(default=False, description="Enable batch processing")
    preserve_html_structure: bool = Field(default=True, description="Preserve HTML structure")
    content_sanitization: bool = Field(default=True, description="Enable content sanitization")


class FieldConfigResponse(BaseModel):
    """Response model for field configuration."""
    id: int
    client_id: str
    collection_name: str
    field_paths: List[str]
    field_types: Dict[str, str]
    is_translation_collection: bool
    primary_collection: Optional[str]
    directus_translation_pattern: str
    rtl_field_mapping: Dict[str, Any]
    batch_processing: bool
    preserve_html_structure: bool
    content_sanitization: bool
    created_at: str
    updated_at: str


class FieldExtractionRequest(BaseModel):
    """Request model for field extraction."""
    client_id: str = Field(..., description="Client identifier")
    collection_name: str = Field(..., description="Directus collection name")
    content: Dict[str, Any] = Field(..., description="Content to extract fields from")
    language: Optional[str] = Field(None, description="Target language for RTL processing")


class FieldExtractionResponse(BaseModel):
    """Response model for field extraction."""
    extracted_fields: Dict[str, Any]
    field_count: int
    processing_time_ms: int
    has_batch_content: bool


@router.post("/config", response_model=FieldConfigResponse)
async def create_field_config(
    config: FieldConfigRequest,
    db: Session = Depends(get_db)
):
    """Create or update field configuration for a collection."""
    try:
        field_mapper = FieldMapper(db)
        
        # Save configuration
        await field_mapper.save_field_config(
            client_id=config.client_id,
            collection_name=config.collection_name,
            field_config=config.dict(exclude={'client_id', 'collection_name'})
        )
        
        # Get the saved configuration directly from database
        db_config = db.query(FieldConfig).filter_by(
            client_id=config.client_id,
            collection_name=config.collection_name
        ).first()
        
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve saved configuration"
            )
        
        return FieldConfigResponse(**db_config.to_dict())
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save field configuration: {str(e)}"
        )


@router.get("/config/{client_id}/{collection_name}", response_model=FieldConfigResponse)
async def get_field_config(
    client_id: str,
    collection_name: str,
    db: Session = Depends(get_db)
):
    """Get field configuration for a collection."""
    try:
        # Get directly from database to ensure all fields are present
        db_config = db.query(FieldConfig).filter_by(
            client_id=client_id,
            collection_name=collection_name
        ).first()
        
        if not db_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Field configuration not found"
            )
        
        return FieldConfigResponse(**db_config.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve field configuration: {str(e)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve field configuration: {str(e)}"
        )

@router.delete("/config/{client_id}/{collection_name}")
async def delete_field_config(
    client_id: str,
    collection_name: str,
    db: Session = Depends(get_db)
):
    """Delete field configuration for a collection."""
    try:
        config = db.query(FieldConfig).filter_by(
            client_id=client_id,
            collection_name=collection_name
        ).first()
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Field configuration not found"
            )
        
        db.delete(config)
        db.commit()
        
        return {"message": "Field configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete field configuration: {str(e)}"
        )


@router.get("/config/{client_id}")
async def list_client_configs(
    client_id: str,
    db: Session = Depends(get_db)
):
    """List all field configurations for a client."""
    try:
        configs = db.query(FieldConfig).filter_by(client_id=client_id).all()
        
        return {
            "client_id": client_id,
            "configurations": [config.to_dict() for config in configs],
            "total_count": len(configs)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list configurations: {str(e)}"
        )


@router.post("/validate")
async def validate_field_paths(
    content: Dict[str, Any],
    field_paths: List[str]
):
    """Validate that field paths exist in the provided content."""
    try:
        field_mapper = FieldMapper(db_session=None, enable_logging=False)
        
        validation_results = {}
        for path in field_paths:
            value = field_mapper._get_nested_value(content, path)
            validation_results[path] = {
                "exists": value is not None,
                "value_type": type(value).__name__ if value is not None else None,
                "detected_field_type": field_mapper._detect_field_type(value) if value is not None else None
            }
        
        return {
            "field_paths": validation_results,
            "total_valid": sum(1 for result in validation_results.values() if result["exists"]),
            "total_tested": len(field_paths)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate field paths: {str(e)}"
        )


@router.post("/extract", response_model=FieldExtractionResponse)
async def extract_fields(
    request: FieldExtractionRequest,
    db: Session = Depends(get_db)
):
    """Extract translatable fields from content based on configuration."""
    try:
        import time
        start_time = time.time()
        
        field_mapper = FieldMapper(db)
        
        # Get field configuration
        field_config = await field_mapper.get_field_config(
            client_id=request.client_id,
            collection_name=request.collection_name
        )
        
        if not field_config.get('field_paths'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No field paths configured for this collection"
            )
        
        # Extract fields
        extracted = field_mapper.extract_fields(
            content=request.content,
            field_config=field_config,
            language=request.language
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return FieldExtractionResponse(
            extracted_fields=extracted,
            field_count=len([k for k in extracted.keys() if k != '__batch__']),
            processing_time_ms=processing_time,
            has_batch_content='__batch__' in extracted
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract fields: {str(e)}"
        )
