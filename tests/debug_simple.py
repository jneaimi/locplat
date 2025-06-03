#!/usr/bin/env python3
"""
LocPlat API Debugging Script - Simple Version
=============================================

This script tests all API endpoints to identify and fix the issues causing 500/422 errors.
"""

import requests
import json
import time
from typing import Dict, Any

class LocPlatDebugger:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        
    def test_endpoint(self, name: str, method: str, url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """Test an API endpoint and record results."""
        print(f"\n🧪 Testing: {name}")
        print(f"   {method} {url}")
        
        try:
            start_time = time.time()
            
            if headers is None:
                headers = {"Content-Type": "application/json"}
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers)
            else:
                response = requests.request(method, url, json=data, headers=headers)
            
            duration = (time.time() - start_time) * 1000
            
            # Try to parse as JSON
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            success = 200 <= response.status_code < 300
            
            print(f"   Status: {response.status_code}")
            if success:
                print(f"   ✅ Success ({duration:.1f}ms)")
                if isinstance(response_data, dict):
                    print(f"   Response keys: {list(response_data.keys())}")
            else:
                print(f"   ❌ Failed ({duration:.1f}ms)")
                print(f"   Error: {response_data}")
            
            self.test_results.append({
                "name": name,
                "method": method,
                "url": url,
                "status": response.status_code,
                "success": success,
                "duration_ms": duration,
                "response": response_data
            })
            
            return success, response.status_code, response_data
            
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")
            self.test_results.append({
                "name": name,
                "method": method,
                "url": url,
                "status": 0,
                "success": False,
                "duration_ms": 0,
                "error": str(e)
            })
            return False, 0, str(e)
    
    def run_all_tests(self):
        """Run comprehensive API tests."""
        print("🚀 Starting LocPlat API Debugging")
        print("=" * 50)
        
        # 1. Health Check
        self.test_endpoint(
            "Health Check",
            "GET",
            f"{self.base_url}/health"
        )
        
        # 2. Field Configuration - CREATE
        field_config_data = {
            "client_id": "debug_client",
            "collection_name": "debug_articles",
            "field_paths": ["title", "description", "content.text", "author.bio"],
            "field_types": {
                "title": "text",
                "description": "textarea", 
                "content.text": "wysiwyg",
                "author.bio": "text"
            },
            "batch_processing": True,
            "preserve_html_structure": True
        }        
        success, status, response = self.test_endpoint(
            "Field Configuration - Create",
            "POST",
            f"{self.base_url}/api/v1/field-mapping/config",
            field_config_data
        )
        
        # 3. Field Configuration - GET
        if success:
            self.test_endpoint(
                "Field Configuration - Get",
                "GET", 
                f"{self.base_url}/api/v1/field-mapping/config/debug_client/debug_articles"
            )
        
        # 4. Field Extraction Test
        extraction_data = {
            "client_id": "debug_client",
            "collection_name": "debug_articles",
            "content": {
                "title": "Sample Article Title",
                "description": "This is a sample article description for testing field extraction.",
                "content": {
                    "text": "<h1>Sample Content</h1><p>This is sample HTML content with <strong>formatting</strong>.</p>"
                },
                "author": {
                    "name": "John Doe",
                    "bio": "Tech writer and developer"
                },
                "metadata": {
                    "category": "Technology",
                    "tags": ["testing", "api", "locplat"]
                }
            }
        }
        
        self.test_endpoint(
            "Field Extraction",
            "POST",
            f"{self.base_url}/api/v1/field-mapping/extract",
            extraction_data
        )
        
        # 5. Translation Providers
        self.test_endpoint(
            "Translation Providers",
            "GET",
            f"{self.base_url}/api/v1/translate/providers"
        )
        
        # Print summary
        print("\n" + "=" * 50)
        print("🏁 Testing Complete - Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for test in self.test_results if test.get("success", False))
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests / total_tests * 100):.1f}%")
        
        # Show failed tests
        if failed_tests > 0:
            print(f"\n❌ Failed Tests ({failed_tests}):")
            for test in self.test_results:
                if not test.get("success", False):
                    print(f"  - {test['name']}: {test.get('status', 'Error')} - {test.get('error', test.get('response', 'Unknown error'))}")
        
        return successful_tests, failed_tests


if __name__ == "__main__":
    debugger = LocPlatDebugger()
    debugger.run_all_tests()
