"""
Webhook API endpoints for Directus CMS integration - Fixed validation issues.
"""
import hashlib
import hmac
import json
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.integrated_translation_service import IntegratedTranslationService
from ..services.field_mapper import FieldMapper
from ..config import settings
from ..services import TranslationError