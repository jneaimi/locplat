#!/usr/bin/env python3
"""
LocPlat - End-to-End Translation Workflow Testing
=================================================

Comprehensive testing of the complete translation workflow including:
1. Database connectivity and field mapping
2. AI provider integration (OpenAI, Anthropic, Mistral, DeepSeek)
3. Directus webhook endpoints
4. Redis caching performance
5. HTML structure preservation
6. RTL language support
7. Batch processing optimization
8. Security validation
"""

import asyncio
import aiohttp
import json
import time
import hashlib
import hmac
from typing import Dict, Any, List
import os
from datetime import datetime

class LocPlatE2ETester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        # Sample test data
        self.sample_article = {
            "id": 1,
            "title": "Welcome to LocPlat",
            "description": "An AI-powered translation service designed for Directus CMS integration.",
            "content": {
                "text": "<h1>Getting Started</h1><p>This service provides <strong>seamless translation</strong> between English and Arabic/Bosnian languages.</p><ul><li>Fast processing</li><li>Cost-effective</li><li>Secure</li></ul>"
            },
            "author": {
                "name": "Test Author",
                "bio": "Technology writer specializing in AI and automation."
            },
            "metadata": {
                "keywords": ["AI", "translation", "Directus", "automation"],
                "category": "Technology"
            }
        }
        
        # RTL test content
        self.rtl_test_content = {
            "id": 2,
            "title": "Arabic Content Test",
            "description": "Testing RTL language support and proper field mapping for Arabic translations.",
            "content": {
                "text": "<div dir='rtl'><h2>Arabic Support</h2><p>This content will be translated to Arabic, preserving HTML structure and RTL directionality.</p></div>"
            }
        }
        
        # Batch processing test
        self.batch_test_content = {
            "id": 3,
            "items": [
                {"title": "Item 1", "description": "First item description"},
                {"title": "Item 2", "description": "Second item description"},
                {"title": "Item 3", "description": "Third item description"},
                {"title": "Item 4", "description": "Fourth item description"},
                {"title": "Item 5", "description": "Fifth item description"}
            ]
        }
