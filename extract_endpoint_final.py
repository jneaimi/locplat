
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
