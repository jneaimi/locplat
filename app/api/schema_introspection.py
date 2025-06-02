                    "interface": "datetime",
                    "nullable": False
                },
                {
                    "field": "updated_at",
                    "type": "timestamp",
                    "interface": "datetime",
                    "nullable": True
                }
            ],
            "meta": {
                "collection": request.collection,
                "icon": "article",
                "note": "Articles collection with translatable content",
                "display_template": "{{title}}",
                "hidden": False,
                "singleton": False,
                "translations": []
            }
        }
        
        # Analyze fields for translatability
        field_mapper = FieldMapper(db)
        
        # Get existing field configuration if any
        existing_config = await field_mapper.get_field_config(
            request.client_id, 
            request.collection
        )
        
        # Identify translatable fields based on type and interface
        translatable_fields = []
        field_analysis = {}
        
        translatable_types = ["string", "text", "json"]
        translatable_interfaces = [
            "input", "input-rich-text-md", "input-rich-text-html", 
            "textarea", "wysiwyg", "input-multiline"
        ]
        
        # Common field names that typically contain translatable content
        translatable_field_names = [
            "title", "name", "description", "content", "body", "summary",
            "excerpt", "bio", "about", "intro", "caption", "alt_text",
            "meta_title", "meta_description", "seo_title", "seo_description"
        ]
        
        for field in mock_schema["fields"]:
            field_name = field["field"]
            field_type = field["type"]
            field_interface = field.get("interface", "")
            
            # Skip system fields
            if field_name in ["id", "created_at", "updated_at", "status", "sort"]:
                field_analysis[field_name] = {
                    "translatable": False,
                    "reason": "System field",
                    "confidence": 0
                }
                continue
                
            # Skip primary keys and foreign keys
            if field.get("primary_key") or field_name.endswith("_id"):
                field_analysis[field_name] = {
                    "translatable": False,
                    "reason": "Key field",
                    "confidence": 0
                }
                continue
            
            # Calculate translatability score
            score = 0
            reasons = []
            
            # Type-based scoring
            if field_type in translatable_types:
                score += 30
                reasons.append(f"Translatable type: {field_type}")
            
            # Interface-based scoring
            if field_interface in translatable_interfaces:
                score += 40
                reasons.append(f"Text input interface: {field_interface}")
            
            # Name-based scoring
            if any(name in field_name.lower() for name in translatable_field_names):
                score += 50
                reasons.append("Common translatable field name")
            
            # Special handling for JSON fields
            if field_type == "json":
                if "rich-text" in field_interface:
                    score += 30
                    reasons.append("Rich text JSON field")
                elif field_name in ["content", "body", "description"]:
                    score += 20
                    reasons.append("Content JSON field")
                else:
                    score -= 10
                    reasons.append("Generic JSON field")
            
            # Length considerations for string fields
            if field_type == "string" and field.get("length", 0) > 50:
                score += 10
                reasons.append("Long string field")
            
            is_translatable = score >= 50
            confidence = min(score / 100.0, 1.0)
            
            field_analysis[field_name] = {
                "translatable": is_translatable,
                "score": score,
                "confidence": confidence,
                "reasons": reasons,
                "type": field_type,
                "interface": field_interface
            }
            
            if is_translatable:
                translatable_fields.append(field_name)
        
        # Identify related collections
        related_collections = []
        for field in mock_schema["fields"]:
            if field.get("relation") and field["relation"].get("collection"):
                related_collections.append({
                    "field": field["field"],
                    "collection": field["relation"]["collection"],
                    "type": "many_to_one"
                })
        
        # Generate recommendations
        recommendations = {
            "suggested_field_paths": translatable_fields,
            "batch_processing": len(translatable_fields) > 2,
            "preserve_html_structure": any(
                "rich-text" in field.get("interface", "") 
                for field in mock_schema["fields"]
            ),
            "rtl_support_needed": True,  # Always recommend RTL for Arabic/Bosnian
            "translation_pattern": "collection_translations",
            "priority_fields": [
                field for field, analysis in field_analysis.items()
                if analysis.get("confidence", 0) > 0.8
            ],
            "optional_fields": [
                field for field, analysis in field_analysis.items()
                if 0.5 <= analysis.get("confidence", 0) <= 0.8
            ],
            "field_types": {
                field: analysis["type"] 
                for field, analysis in field_analysis.items()
                if analysis.get("translatable", False)
            }
        }
        
        # Check if user already has configuration
        if existing_config.get("field_paths"):
            recommendations["existing_configuration"] = {
                "has_config": True,
                "current_fields": existing_config["field_paths"],
                "suggested_additions": [
                    field for field in translatable_fields 
                    if field not in existing_config["field_paths"]
                ],
                "suggested_removals": [
                    field for field in existing_config["field_paths"]
                    if field not in translatable_fields
                ]
            }
        else:
            recommendations["existing_configuration"] = {
                "has_config": False,
                "setup_needed": True
            }
        
        return DirectusSchemaResponse(
            collection=request.collection,
            schema=mock_schema,
            suggested_translatable_fields=translatable_fields,
            related_collections=related_collections,
            field_analysis=field_analysis,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Schema introspection error: {str(e)}"
        ) from e


@schema_router.post("/schema/configure")
async def auto_configure_collection(
    request: DirectusSchemaRequest,
    db: Session = Depends(get_db)
):
    """
    Automatically configure field mapping based on schema introspection.
    
    This endpoint:
    1. Introspects the collection schema
    2. Identifies translatable fields automatically
    3. Creates a field configuration with optimal settings
    4. Returns the created configuration
    """
    try:
        # First, introspect the schema
        introspection_result = await introspect_collection_schema(request, db)
        
        # Create field configuration based on recommendations
        field_mapper = FieldMapper(db)
        
        recommendations = introspection_result.recommendations
        
        # Prepare field configuration
        field_config_data = {
            "client_id": request.client_id,
            "collection_name": request.collection,
            "field_paths": recommendations["suggested_field_paths"],
            "field_types": recommendations["field_types"],
            "batch_processing": recommendations["batch_processing"],
            "preserve_html_structure": recommendations["preserve_html_structure"],
            "directus_translation_pattern": recommendations["translation_pattern"]
        }
        
        # Save the configuration
        result = await field_mapper.save_field_config(**field_config_data)
        
        return {
            "success": True,
            "message": f"Auto-configured field mapping for collection '{request.collection}'",
            "configuration": result,
            "introspection": {
                "total_fields_analyzed": len(introspection_result.field_analysis),
                "translatable_fields_found": len(introspection_result.suggested_translatable_fields),
                "related_collections": len(introspection_result.related_collections),
                "confidence_distribution": {
                    "high": len(recommendations["priority_fields"]),
                    "medium": len(recommendations["optional_fields"]),
                    "low": len(introspection_result.suggested_translatable_fields) - 
                           len(recommendations["priority_fields"]) - 
                           len(recommendations["optional_fields"])
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Auto-configuration error: {str(e)}"
        ) from e


@schema_router.get("/schema/collections")
async def list_available_collections(
    client_id: str,
    db: Session = Depends(get_db)
):
    """
    List all available collections for a client.
    
    In production, this would connect to the Directus API to fetch
    all collections. For now, returns mock data.
    """
    try:
        # Mock collection data - in production this would come from Directus API
        mock_collections = [
            {
                "collection": "articles",
                "meta": {
                    "icon": "article",
                    "note": "Blog articles and posts",
                    "display_template": "{{title}}",
                    "field_count": 11
                },
                "configured": True,
                "translatable_fields": 3
            },
            {
                "collection": "pages",
                "meta": {
                    "icon": "pages",
                    "note": "Static pages content",
                    "display_template": "{{title}}",
                    "field_count": 8
                },
                "configured": False,
                "translatable_fields": 0
            },
            {
                "collection": "products",
                "meta": {
                    "icon": "shopping_cart",
                    "note": "E-commerce products",
                    "display_template": "{{name}} - {{price}}",
                    "field_count": 15
                },
                "configured": False,
                "translatable_fields": 0
            },
            {
                "collection": "categories",
                "meta": {
                    "icon": "folder",
                    "note": "Content categories",
                    "display_template": "{{name}}",
                    "field_count": 5
                },
                "configured": False,
                "translatable_fields": 0
            }
        ]
        
        # Check which collections have existing field configurations
        field_mapper = FieldMapper(db)
        
        for collection in mock_collections:
            existing_config = await field_mapper.get_field_config(
                client_id, 
                collection["collection"]
            )
            
            if existing_config.get("field_paths"):
                collection["configured"] = True
                collection["translatable_fields"] = len(existing_config["field_paths"])
                collection["last_updated"] = existing_config.get("updated_at")
            else:
                collection["configured"] = False
                collection["translatable_fields"] = 0
        
        return {
            "success": True,
            "collections": mock_collections,
            "total": len(mock_collections),
            "configured_count": sum(1 for c in mock_collections if c["configured"]),
            "unconfigured_count": sum(1 for c in mock_collections if not c["configured"])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Collections listing error: {str(e)}"
        ) from e
