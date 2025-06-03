#!/usr/bin/env python3
"""
LocPlat API Debugging Script
============================

This script tests all API endpoints to identify and fix the issues causing 500/422 errors.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

class LocPlatDebugger:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session = None
        self.test_results = []
        
    async def create_session(self):
        self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, name: str, method: str, url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """Test an API endpoint and record results."""
        print(f"\n🧪 Testing: {name}")
        print(f"   {method} {url}")
        
        try:
            start_time = time.time()
            
            if headers is None:
                headers = {"Content-Type": "application/json"}
            
            async with self.session.request(method, url, json=data, headers=headers) as response:
                duration = (time.time() - start_time) * 1000
                response_text = await response.text()
                
                # Try to parse as JSON
                try:
                    response_data = json.loads(response_text)
                except:
                    response_data = response_text
                
                success = 200 <= response.status < 300
                
                print(f"   Status: {response.status}")
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
                    "status": response.status,
                    "success": success,
                    "duration_ms": duration,
                    "response": response_data
                })
                
                return success, response.status, response_data
                
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
    
    async def run_all_tests(self):
        """Run comprehensive API tests."""
        await self.create_session()
        
        print("🚀 Starting LocPlat API Debugging")
        print("=" * 50)
        
        # 1. Health Check
        await self.test_endpoint(
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
        
        success, status, response = await self.test_endpoint(
            "Field Configuration - Create",
            "POST",
            f"{self.base_url}/api/v1/field-mapping/config",
            field_config_data
        )
        
        # 3. Field Configuration - GET
        if success:
            await self.test_endpoint(
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
        
        await self.test_endpoint(
            "Field Extraction",
            "POST",
            f"{self.base_url}/api/v1/field-mapping/extract",
            extraction_data
        )
        
        # 5. Translation Providers
        await self.test_endpoint(
            "Translation Providers",
            "GET",
            f"{self.base_url}/api/v1/translate/providers"
        )
        
        # 6. Translation Preview (structured)
        preview_data = {
            "content": extraction_data["content"],
            "client_id": "debug_client",
            "collection_name": "debug_articles",
            "target_lang": "ar"
        }
        
        await self.test_endpoint(
            "Translation Preview",
            "POST",
            f"{self.base_url}/api/v1/translate/preview",
            preview_data
        )
        
        # 7. Webhook Validation (correct format)
        webhook_validation_data = {
            "client_id": "debug_client",
            "collection": "debug_articles",
            "provider": "openai",
            "api_key": "sk-test12345678901234567890123456789012345678901234567890",
            "target_language": "ar"
        }
        
        await self.test_endpoint(
            "Webhook Validation",
            "POST",
            f"{self.base_url}/api/v1/webhooks/directus/validate",
            webhook_validation_data
        )
        
        # 8. Translation Request Validation 
        translation_validation_data = {
            "client_id": "debug_client",
            "collection_name": "debug_articles", 
            "provider": "openai",
            "api_key": "sk-test12345678901234567890123456789012345678901234567890",
            "source_lang": "en",
            "target_lang": "ar"
        }
        
        await self.test_endpoint(
            "Translation Request Validation",
            "POST",
            f"{self.base_url}/api/v1/translate/validate",
            translation_validation_data
        )
        
        # 9. Cache Statistics
        await self.test_endpoint(
            "Cache Statistics",
            "GET",
            f"{self.base_url}/api/v1/cache/stats"
        )
        
        # 10. Webhook Testing Endpoint
        webhook_test_data = {
            "sample_data": extraction_data["content"],
            "client_id": "debug_client",
            "collection": "debug_articles",
            "target_language": "ar",
            "provider": "openai",
            "api_key": "sk-test12345678901234567890123456789012345678901234567890",
            "dry_run": True
        }
        
        await self.test_endpoint(
            "Webhook Testing",
            "POST",
            f"{self.base_url}/api/v1/webhooks/directus/test",
            webhook_test_data
        )
        
        await self.close_session()
        
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
        
        # Show successful tests  
        if successful_tests > 0:
            print(f"\n✅ Successful Tests ({successful_tests}):")
            for test in self.test_results:
                if test.get("success", False):
                    print(f"  - {test['name']}: {test['status']} ({test['duration_ms']:.1f}ms)")
        
        # Save detailed results
        with open('debug_results.json', 'w') as f:
            json.dump({
                "timestamp": time.time(),
                "summary": {
                    "total": total_tests,
                    "successful": successful_tests,
                    "failed": failed_tests,
                    "success_rate": successful_tests / total_tests * 100
                },
                "test_results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: debug_results.json")
        
        return successful_tests, failed_tests


if __name__ == "__main__":
    debugger = LocPlatDebugger()
    asyncio.run(debugger.run_all_tests())
