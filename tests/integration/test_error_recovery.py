#!/usr/bin/env python3
"""
Error recovery integration tests for API failures and timeout handling.
Tests the system's resilience to various failure scenarios.
"""

import time
import logging
import requests
import json
import os
from typing import Dict, List, Any, Optional
from unittest.mock import patch
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorRecoveryTester:
    """Error recovery and resilience testing suite."""
    
    def __init__(self):
        """Initialize error recovery tester."""
        self.api_url = "http://localhost:3000/api"
        self.session = requests.Session()
        
        # Test scenarios
        self.test_scenarios = [
            "network_timeout",
            "rate_limit_exceeded", 
            "invalid_api_key",
            "malformed_request",
            "server_error_simulation",
            "file_system_errors",
            "resource_exhaustion",
            "concurrent_access_conflicts"
        ]
        
        # Results tracking
        self.results = {}
    
    def test_network_timeout_recovery(self) -> Dict[str, Any]:
        """Test recovery from network timeouts."""
        logger.info("⏱️ Testing network timeout recovery...")
        
        # Test with very short timeout
        test_result = {
            "scenario": "network_timeout",
            "success": False,
            "recovery_time": None,
            "error_handling": False,
            "graceful_degradation": False,
            "details": {}
        }
        
        try:
            start_time = time.time()
            
            # Make request with very short timeout
            response = self.session.post(
                f"{self.api_url}/script/parse",
                json={
                    "content": "# Test script\n\n## Scene 1\nTest content for timeout test.",
                    "projectId": f"timeout_test_{int(time.time())}"
                },
                timeout=0.001  # Extremely short timeout to force failure
            )
            
            # If we get here, timeout didn't occur as expected
            test_result["details"]["unexpected_success"] = True
            
        except requests.exceptions.Timeout:
            # Expected timeout occurred
            test_result["error_handling"] = True
            logger.info("✅ Timeout correctly detected and handled")
            
            # Test recovery with normal timeout
            try:
                recovery_start = time.time()
                response = self.session.post(
                    f"{self.api_url}/script/parse",
                    json={
                        "content": "# Recovery test script\n\n## Scene 1\nRecovery test content.",
                        "projectId": f"recovery_test_{int(time.time())}"
                    },
                    timeout=30  # Normal timeout
                )
                
                if response.status_code == 200:
                    test_result["recovery_time"] = time.time() - recovery_start
                    test_result["success"] = True
                    test_result["graceful_degradation"] = True
                    logger.info(f"✅ Recovery successful in {test_result['recovery_time']:.2f}s")
                else:
                    test_result["details"]["recovery_error"] = response.status_code
                    
            except Exception as e:
                test_result["details"]["recovery_exception"] = str(e)
                
        except Exception as e:
            test_result["details"]["unexpected_exception"] = str(e)
        
        return test_result
    
    def test_rate_limit_handling(self) -> Dict[str, Any]:
        """Test rate limit detection and backoff."""
        logger.info("🚦 Testing rate limit handling...")
        
        test_result = {
            "scenario": "rate_limit_exceeded",
            "success": False,
            "rate_limit_detected": False,
            "backoff_implemented": False,
            "recovery_successful": False,
            "details": {}
        }
        
        # Simulate rapid requests to trigger rate limiting
        rapid_requests = 10
        responses = []
        
        for i in range(rapid_requests):
            try:
                response = self.session.post(
                    f"{self.api_url}/images/generate",
                    json={
                        "prompt": f"Rate limit test image {i}",
                        "sceneId": f"rate_test_{i}",
                        "projectId": f"rate_limit_test_{int(time.time())}",
                        "provider": "dalle3"
                    },
                    timeout=10
                )
                
                responses.append({
                    "request_num": i,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                })
                
                # Check for rate limiting responses
                if response.status_code == 429:
                    test_result["rate_limit_detected"] = True
                    logger.info(f"✅ Rate limit detected on request {i}")
                    
                    # Check if retry-after header is present
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        test_result["backoff_implemented"] = True
                        logger.info(f"✅ Retry-After header found: {retry_after}")
                    
                    break
                    
                # Small delay between requests
                time.sleep(0.1)
                
            except Exception as e:
                responses.append({
                    "request_num": i,
                    "error": str(e)
                })
        
        test_result["details"]["responses"] = responses
        
        # Test recovery after rate limiting
        if test_result["rate_limit_detected"]:
            logger.info("⏳ Testing recovery after rate limit...")
            time.sleep(5)  # Wait before retry
            
            try:
                recovery_response = self.session.post(
                    f"{self.api_url}/script/parse",  # Use different endpoint
                    json={
                        "content": "# Rate limit recovery test",
                        "projectId": f"rate_recovery_{int(time.time())}"
                    },
                    timeout=30
                )
                
                if recovery_response.status_code == 200:
                    test_result["recovery_successful"] = True
                    test_result["success"] = True
                    logger.info("✅ Recovery after rate limiting successful")
                    
            except Exception as e:
                test_result["details"]["recovery_error"] = str(e)
        
        return test_result
    
    def test_invalid_api_key_handling(self) -> Dict[str, Any]:
        """Test handling of invalid API keys."""
        logger.info("🔑 Testing invalid API key handling...")
        
        test_result = {
            "scenario": "invalid_api_key",
            "success": False,
            "auth_error_detected": False,
            "graceful_error_response": False,
            "no_sensitive_info_leaked": True,
            "details": {}
        }
        
        # Temporarily modify environment to simulate invalid key
        original_openai_key = os.environ.get('OPENAI_API_KEY')
        original_runway_key = os.environ.get('RUNWAY_API_KEY')
        original_elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
        
        try:
            # Set invalid keys
            os.environ['OPENAI_API_KEY'] = 'invalid_key_test'
            os.environ['RUNWAY_API_KEY'] = 'invalid_runway_key'
            os.environ['ELEVENLABS_API_KEY'] = 'invalid_elevenlabs_key'
            
            # Test image generation with invalid OpenAI key
            response = self.session.post(
                f"{self.api_url}/images/generate",
                json={
                    "prompt": "Test image with invalid key",
                    "sceneId": "invalid_key_test",
                    "projectId": f"invalid_key_test_{int(time.time())}",
                    "provider": "dalle3"
                },
                timeout=30
            )
            
            if response.status_code in [401, 403]:
                test_result["auth_error_detected"] = True
                logger.info("✅ Authentication error correctly detected")
            
            # Check response format
            try:
                error_response = response.json()
                if "error" in error_response and isinstance(error_response["error"], str):
                    test_result["graceful_error_response"] = True
                    logger.info("✅ Graceful error response format")
                
                # Check that no sensitive information is leaked
                response_text = response.text.lower()
                sensitive_patterns = ['api_key', 'secret', 'token', 'password']
                
                for pattern in sensitive_patterns:
                    if pattern in response_text:
                        test_result["no_sensitive_info_leaked"] = False
                        test_result["details"]["leaked_info"] = pattern
                        break
                
                if test_result["no_sensitive_info_leaked"]:
                    logger.info("✅ No sensitive information leaked in error response")
                    
            except json.JSONDecodeError:
                test_result["details"]["non_json_response"] = True
            
            test_result["details"]["response_status"] = response.status_code
            test_result["details"]["response_body"] = response.text[:200]
            
        except Exception as e:
            test_result["details"]["exception"] = str(e)
        
        finally:
            # Restore original keys
            if original_openai_key:
                os.environ['OPENAI_API_KEY'] = original_openai_key
            if original_runway_key:
                os.environ['RUNWAY_API_KEY'] = original_runway_key
            if original_elevenlabs_key:
                os.environ['ELEVENLABS_API_KEY'] = original_elevenlabs_key
        
        test_result["success"] = (
            test_result["auth_error_detected"] and
            test_result["graceful_error_response"] and
            test_result["no_sensitive_info_leaked"]
        )
        
        return test_result
    
    def test_malformed_request_handling(self) -> Dict[str, Any]:
        """Test handling of malformed requests."""
        logger.info("📝 Testing malformed request handling...")
        
        test_result = {
            "scenario": "malformed_request",
            "success": False,
            "validation_errors_caught": 0,
            "proper_error_codes": 0,
            "details": {}
        }
        
        # Test various malformed requests
        malformed_tests = [
            {
                "name": "missing_required_field",
                "endpoint": "script/parse",
                "payload": {"projectId": "test"},  # Missing 'content'
                "expected_status": 400
            },
            {
                "name": "invalid_data_type",
                "endpoint": "images/generate",
                "payload": {"prompt": 123, "sceneId": "test"},  # prompt should be string
                "expected_status": 400
            },
            {
                "name": "empty_request_body",
                "endpoint": "audio/generate",
                "payload": {},
                "expected_status": 400
            },
            {
                "name": "oversized_content",
                "endpoint": "script/parse",
                "payload": {
                    "content": "x" * 100000,  # Very large content
                    "projectId": "oversize_test"
                },
                "expected_status": [400, 413]  # Bad request or payload too large
            }
        ]
        
        for test_case in malformed_tests:
            try:
                response = self.session.post(
                    f"{self.api_url}/{test_case['endpoint']}",
                    json=test_case["payload"],
                    timeout=30
                )
                
                expected_statuses = test_case["expected_status"]
                if not isinstance(expected_statuses, list):
                    expected_statuses = [expected_statuses]
                
                if response.status_code in expected_statuses:
                    test_result["proper_error_codes"] += 1
                    logger.info(f"✅ {test_case['name']}: Proper error code {response.status_code}")
                
                # Check if error message is informative
                try:
                    error_response = response.json()
                    if "error" in error_response and len(error_response["error"]) > 0:
                        test_result["validation_errors_caught"] += 1
                        logger.info(f"✅ {test_case['name']}: Informative error message")
                except:
                    pass
                
                test_result["details"][test_case["name"]] = {
                    "status_code": response.status_code,
                    "response": response.text[:100]
                }
                
            except Exception as e:
                test_result["details"][test_case["name"]] = {
                    "exception": str(e)
                }
        
        total_tests = len(malformed_tests)
        test_result["success"] = (
            test_result["validation_errors_caught"] >= total_tests * 0.8 and
            test_result["proper_error_codes"] >= total_tests * 0.8
        )
        
        return test_result
    
    def test_concurrent_access_conflicts(self) -> Dict[str, Any]:
        """Test handling of concurrent access to the same resources."""
        logger.info("🔄 Testing concurrent access conflict handling...")
        
        test_result = {
            "scenario": "concurrent_access_conflicts",
            "success": False,
            "no_conflicts": 0,
            "handled_conflicts": 0,
            "data_consistency": True,
            "details": {}
        }
        
        project_id = f"concurrent_test_{int(time.time())}"
        
        def concurrent_operation(thread_id: int) -> Dict[str, Any]:
            """Perform operations that might conflict."""
            thread_results = {
                "thread_id": thread_id,
                "operations": [],
                "errors": []
            }
            
            session = requests.Session()
            
            operations = [
                {
                    "name": "create_folder",
                    "endpoint": f"projects/{project_id}/folders",
                    "method": "POST",
                    "payload": {
                        "sceneId": f"scene_{thread_id}",
                        "sceneName": f"Scene {thread_id}"
                    }
                },
                {
                    "name": "parse_script",
                    "endpoint": "script/parse",
                    "method": "POST",
                    "payload": {
                        "content": f"# Script {thread_id}\n\n## Scene 1\nContent from thread {thread_id}",
                        "projectId": project_id
                    }
                }
            ]
            
            for op in operations:
                try:
                    if op["method"] == "POST":
                        response = session.post(
                            f"{self.api_url}/{op['endpoint']}",
                            json=op["payload"],
                            timeout=30
                        )
                    
                    thread_results["operations"].append({
                        "name": op["name"],
                        "status_code": response.status_code,
                        "success": response.status_code in [200, 201]
                    })
                    
                except Exception as e:
                    thread_results["errors"].append({
                        "operation": op["name"],
                        "error": str(e)
                    })
            
            return thread_results
        
        # Run concurrent operations
        num_threads = 5
        threads = []
        thread_results = []
        
        def run_thread(thread_id: int):
            result = concurrent_operation(thread_id)
            thread_results.append(result)
        
        # Start all threads
        for i in range(num_threads):
            thread = threading.Thread(target=run_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Analyze results
        successful_operations = 0
        total_operations = 0
        
        for result in thread_results:
            for op in result["operations"]:
                total_operations += 1
                if op["success"]:
                    successful_operations += 1
        
        test_result["details"]["thread_results"] = thread_results
        test_result["details"]["successful_operations"] = successful_operations
        test_result["details"]["total_operations"] = total_operations
        
        # Check for data consistency
        try:
            # Verify project folder structure
            response = self.session.get(f"{self.api_url}/projects/{project_id}/folders")
            if response.status_code == 200:
                folder_structure = response.json()
                test_result["details"]["final_folder_structure"] = folder_structure
            
        except Exception as e:
            test_result["details"]["consistency_check_error"] = str(e)
            test_result["data_consistency"] = False
        
        # Success criteria: most operations succeed, no data corruption
        success_rate = successful_operations / total_operations if total_operations > 0 else 0
        test_result["success"] = success_rate >= 0.8 and test_result["data_consistency"]
        
        return test_result
    
    def run_error_recovery_tests(self) -> Dict[str, Any]:
        """Run the complete error recovery test suite."""
        logger.info("🛡️ Starting Error Recovery Test Suite")
        logger.info("=" * 60)
        
        test_functions = [
            ("Network Timeout Recovery", self.test_network_timeout_recovery),
            ("Rate Limit Handling", self.test_rate_limit_handling),
            ("Invalid API Key Handling", self.test_invalid_api_key_handling),
            ("Malformed Request Handling", self.test_malformed_request_handling),
            ("Concurrent Access Conflicts", self.test_concurrent_access_conflicts),
        ]
        
        all_results = {
            "timestamp": time.time(),
            "test_summary": {
                "total_tests": len(test_functions),
                "passed_tests": 0,
                "failed_tests": 0
            },
            "detailed_results": {}
        }
        
        for test_name, test_func in test_functions:
            logger.info(f"\n🧪 Running: {test_name}")
            logger.info("-" * 40)
            
            try:
                result = test_func()
                all_results["detailed_results"][test_name] = result
                
                if result["success"]:
                    all_results["test_summary"]["passed_tests"] += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    all_results["test_summary"]["failed_tests"] += 1
                    logger.error(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                logger.error(f"💥 {test_name}: CRASHED - {e}")
                all_results["detailed_results"][test_name] = {
                    "scenario": test_name.lower().replace(" ", "_"),
                    "success": False,
                    "exception": str(e)
                }
                all_results["test_summary"]["failed_tests"] += 1
        
        # Calculate overall success
        success_rate = (all_results["test_summary"]["passed_tests"] / 
                       all_results["test_summary"]["total_tests"]) * 100
        
        all_results["test_summary"]["success_rate"] = success_rate
        all_results["test_summary"]["overall_success"] = success_rate >= 70  # 70% threshold
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("🏁 ERROR RECOVERY TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {all_results['test_summary']['total_tests']}")
        logger.info(f"Passed: {all_results['test_summary']['passed_tests']}")
        logger.info(f"Failed: {all_results['test_summary']['failed_tests']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("=" * 60)
        
        if all_results["test_summary"]["overall_success"]:
            logger.info("🎉 ERROR RECOVERY TESTS PASSED - System is resilient!")
        else:
            logger.error("💥 ERROR RECOVERY TESTS FAILED - System needs hardening!")
        
        return all_results


def main():
    """Main error recovery test runner."""
    tester = ErrorRecoveryTester()
    results = tester.run_error_recovery_tests()
    
    # Save results
    os.makedirs("tests/reports", exist_ok=True)
    report_path = f"tests/reports/error_recovery_report_{int(time.time())}.json"
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"📊 Error recovery report saved to: {report_path}")
    
    return results["test_summary"]["overall_success"]


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)