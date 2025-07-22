#!/usr/bin/env python3
"""
Web Interface Integration Test

Tests the complete integration between the pipeline and web interface including:
- API endpoint functionality
- WebSocket real-time updates
- File upload/download
- Job management
- Error handling
- User interface components

Usage:
    python test_web_integration.py [--host HOST] [--port PORT] [--headless]
"""

import os
import sys
import asyncio
import logging
import json
import time
import requests
import websocket
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime
import threading
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class WebTestResult:
    """Container for web test results."""
    test_name: str
    endpoint: str
    success: bool
    response_time: float
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WebIntegrationTester:
    """Comprehensive web interface integration tester."""
    
    def __init__(self, host: str = "localhost", port: int = 3000, api_port: int = 8000):
        """
        Initialize web integration tester.
        
        Args:
            host: Web interface host
            port: Web interface port
            api_port: API backend port
        """
        self.host = host
        self.port = port
        self.api_port = api_port
        self.base_url = f"http://{host}:{port}"
        self.api_url = f"http://{host}:{api_port}"
        self.ws_url = f"ws://{host}:{api_port}/ws"
        
        self.test_results: List[WebTestResult] = []
        self.websocket_messages: List[Dict[str, Any]] = []
        self.websocket_connected = False
        
        logger.info(f"Web Integration Tester initialized")
        logger.info(f"  Web URL: {self.base_url}")
        logger.info(f"  API URL: {self.api_url}")
        logger.info(f"  WebSocket: {self.ws_url}")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all web integration tests.
        
        Returns:
            Complete test results
        """
        start_time = time.time()
        
        logger.info("🌐 Starting Web Interface Integration Tests")
        
        # Test 1: API Health Check
        await self._test_api_health()
        
        # Test 2: Web Interface Accessibility
        await self._test_web_interface()
        
        # Test 3: API Endpoints
        await self._test_api_endpoints()
        
        # Test 4: WebSocket Connection
        await self._test_websocket_connection()
        
        # Test 5: File Operations
        await self._test_file_operations()
        
        # Test 6: Job Management
        await self._test_job_management()
        
        # Test 7: Error Handling
        await self._test_error_handling()
        
        # Test 8: Performance Testing
        await self._test_performance()
        
        # Generate final results
        return self._generate_results(time.time() - start_time)
    
    async def _test_api_health(self) -> None:
        """Test API health and basic connectivity."""
        test_start = time.time()
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            self.test_results.append(WebTestResult(
                test_name="api_health",
                endpoint="/health",
                success=response.status_code == 200,
                response_time=time.time() - test_start,
                status_code=response.status_code,
                response_data=response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            ))
            
            if response.status_code == 200:
                logger.info("✅ API health check passed")
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                
        except Exception as e:
            self.test_results.append(WebTestResult(
                test_name="api_health",
                endpoint="/health",
                success=False,
                response_time=time.time() - test_start,
                error=str(e)
            ))
            logger.error(f"❌ API health check error: {e}")
    
    async def _test_web_interface(self) -> None:
        """Test web interface accessibility."""
        test_start = time.time()
        
        try:
            response = requests.get(self.base_url, timeout=10)
            
            # Check if it's a valid HTML response
            is_html = 'text/html' in response.headers.get('content-type', '')
            
            self.test_results.append(WebTestResult(
                test_name="web_interface",
                endpoint="/",
                success=response.status_code == 200 and is_html,
                response_time=time.time() - test_start,
                status_code=response.status_code,
                response_data={
                    "content_type": response.headers.get('content-type'),
                    "content_length": len(response.content),
                    "is_html": is_html
                }
            ))
            
            if response.status_code == 200 and is_html:
                logger.info("✅ Web interface accessible")
            else:
                logger.error(f"❌ Web interface failed: {response.status_code}")
                
        except Exception as e:
            self.test_results.append(WebTestResult(
                test_name="web_interface",
                endpoint="/",
                success=False,
                response_time=time.time() - test_start,
                error=str(e)
            ))
            logger.error(f"❌ Web interface error: {e}")
    
    async def _test_api_endpoints(self) -> None:
        """Test core API endpoints."""
        endpoints = [
            {"path": "/api/v1/health", "method": "GET", "expected": 200},
            {"path": "/api/v1/status", "method": "GET", "expected": 200},
            {"path": "/api/v1/jobs", "method": "GET", "expected": 200},
            {"path": "/api/v1/projects", "method": "GET", "expected": 200}
        ]
        
        for endpoint_info in endpoints:
            test_start = time.time()
            
            try:
                if endpoint_info["method"] == "GET":
                    response = requests.get(f"{self.api_url}{endpoint_info['path']}", timeout=10)
                else:
                    # Add support for other methods if needed
                    continue
                
                success = response.status_code == endpoint_info["expected"]
                
                self.test_results.append(WebTestResult(
                    test_name=f"api_endpoint_{endpoint_info['path'].split('/')[-1]}",
                    endpoint=endpoint_info['path'],
                    success=success,
                    response_time=time.time() - test_start,
                    status_code=response.status_code,
                    response_data=response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                ))
                
                if success:
                    logger.info(f"✅ Endpoint {endpoint_info['path']} OK")
                else:
                    logger.error(f"❌ Endpoint {endpoint_info['path']} failed: {response.status_code}")
                    
            except Exception as e:
                self.test_results.append(WebTestResult(
                    test_name=f"api_endpoint_{endpoint_info['path'].split('/')[-1]}",
                    endpoint=endpoint_info['path'],
                    success=False,
                    response_time=time.time() - test_start,
                    error=str(e)
                ))
                logger.error(f"❌ Endpoint {endpoint_info['path']} error: {e}")
    
    async def _test_websocket_connection(self) -> None:
        """Test WebSocket connection and real-time updates."""
        test_start = time.time()
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                self.websocket_messages.append(data)
                logger.debug(f"WebSocket message: {data}")
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
        
        def on_open(ws):
            self.websocket_connected = True
            logger.info("WebSocket connected")
            
            # Send test message
            test_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }
            ws.send(json.dumps(test_message))
        
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            self.websocket_connected = False
            logger.info("WebSocket closed")
        
        try:
            # Create WebSocket connection
            ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=on_message,
                on_open=on_open,
                on_error=on_error,
                on_close=on_close
            )
            
            # Run in background thread
            wst = threading.Thread(target=ws.run_forever)
            wst.daemon = True
            wst.start()
            
            # Wait for connection
            await asyncio.sleep(2)
            
            # Test connection
            success = self.websocket_connected
            
            # Close connection
            if self.websocket_connected:
                ws.close()
                await asyncio.sleep(1)
            
            self.test_results.append(WebTestResult(
                test_name="websocket_connection",
                endpoint=self.ws_url,
                success=success,
                response_time=time.time() - test_start,
                response_data={
                    "connected": success,
                    "messages_received": len(self.websocket_messages)
                }
            ))
            
            if success:
                logger.info("✅ WebSocket connection test passed")
            else:
                logger.error("❌ WebSocket connection test failed")
                
        except Exception as e:
            self.test_results.append(WebTestResult(
                test_name="websocket_connection",
                endpoint=self.ws_url,
                success=False,
                response_time=time.time() - test_start,
                error=str(e)
            ))
            logger.error(f"❌ WebSocket test error: {e}")
    
    async def _test_file_operations(self) -> None:
        """Test file upload and download operations."""
        test_start = time.time()
        
        try:
            # Create a test file
            test_content = "Test file content for web integration"
            test_file_path = Path("test_upload.txt")
            test_file_path.write_text(test_content)
            
            # Test file upload (if endpoint exists)
            upload_success = False
            try:
                with open(test_file_path, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(
                        f"{self.api_url}/api/v1/upload",
                        files=files,
                        timeout=30
                    )
                upload_success = response.status_code in [200, 201]
                upload_response = response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            except Exception as e:
                upload_response = {"error": str(e)}
            
            # Test file download (if endpoint exists)
            download_success = False
            try:
                response = requests.get(
                    f"{self.api_url}/api/v1/download/test_upload.txt",
                    timeout=30
                )
                download_success = response.status_code == 200
            except Exception:
                pass
            
            # Clean up test file
            if test_file_path.exists():
                test_file_path.unlink()
            
            self.test_results.append(WebTestResult(
                test_name="file_operations",
                endpoint="/api/v1/upload",
                success=upload_success or download_success,  # At least one should work
                response_time=time.time() - test_start,
                response_data={
                    "upload_success": upload_success,
                    "download_success": download_success,
                    "upload_response": upload_response
                }
            ))
            
            if upload_success or download_success:
                logger.info("✅ File operations test passed")
            else:
                logger.warning("⚠️  File operations endpoints not available (this is normal)")
                
        except Exception as e:
            self.test_results.append(WebTestResult(
                test_name="file_operations",
                endpoint="/api/v1/upload",
                success=False,
                response_time=time.time() - test_start,
                error=str(e)
            ))
            logger.error(f"❌ File operations test error: {e}")
    
    async def _test_job_management(self) -> None:
        """Test job creation and management."""
        test_start = time.time()
        
        try:
            # Test job creation
            job_data = {
                "type": "test_job",
                "config": {
                    "prompt": "Test prompt for web integration",
                    "duration": 5
                }
            }
            
            create_success = False
            job_id = None
            
            try:
                response = requests.post(
                    f"{self.api_url}/api/v1/jobs",
                    json=job_data,
                    timeout=30
                )
                create_success = response.status_code in [200, 201]
                if create_success:
                    job_response = response.json()
                    job_id = job_response.get("job_id") or job_response.get("id")
            except Exception as e:
                logger.debug(f"Job creation endpoint not available: {e}")
            
            # Test job status retrieval
            status_success = False
            if job_id:
                try:
                    response = requests.get(
                        f"{self.api_url}/api/v1/jobs/{job_id}",
                        timeout=10
                    )
                    status_success = response.status_code == 200
                except Exception as e:
                    logger.debug(f"Job status endpoint error: {e}")
            
            self.test_results.append(WebTestResult(
                test_name="job_management",
                endpoint="/api/v1/jobs",
                success=create_success or status_success,
                response_time=time.time() - test_start,
                response_data={
                    "create_success": create_success,
                    "status_success": status_success,
                    "job_id": job_id
                }
            ))
            
            if create_success or status_success:
                logger.info("✅ Job management test passed")
            else:
                logger.warning("⚠️  Job management endpoints not fully implemented")
                
        except Exception as e:
            self.test_results.append(WebTestResult(
                test_name="job_management",
                endpoint="/api/v1/jobs",
                success=False,
                response_time=time.time() - test_start,
                error=str(e)
            ))
            logger.error(f"❌ Job management test error: {e}")
    
    async def _test_error_handling(self) -> None:
        """Test error handling scenarios."""
        test_start = time.time()
        
        error_scenarios = [
            {
                "name": "invalid_endpoint",
                "url": f"{self.api_url}/api/v1/nonexistent",
                "expected_status": 404
            },
            {
                "name": "invalid_method",
                "url": f"{self.api_url}/api/v1/health",
                "method": "POST",
                "expected_status": 405
            },
            {
                "name": "invalid_json",
                "url": f"{self.api_url}/api/v1/jobs",
                "method": "POST",
                "data": "{invalid json}",
                "expected_status": 400
            }
        ]
        
        error_results = []
        
        for scenario in error_scenarios:
            try:
                if scenario.get("method") == "POST":
                    if "data" in scenario:
                        response = requests.post(
                            scenario["url"],
                            data=scenario["data"],
                            headers={"Content-Type": "application/json"},
                            timeout=10
                        )
                    else:
                        response = requests.post(scenario["url"], timeout=10)
                else:
                    response = requests.get(scenario["url"], timeout=10)
                
                expected_status = scenario["expected_status"]
                success = response.status_code == expected_status
                
                error_results.append({
                    "scenario": scenario["name"],
                    "success": success,
                    "expected_status": expected_status,
                    "actual_status": response.status_code
                })
                
            except Exception as e:
                error_results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "error": str(e)
                })
        
        overall_success = all(result.get("success", False) for result in error_results)
        
        self.test_results.append(WebTestResult(
            test_name="error_handling",
            endpoint="/api/v1/*",
            success=overall_success,
            response_time=time.time() - test_start,
            response_data={"scenarios": error_results}
        ))
        
        if overall_success:
            logger.info("✅ Error handling test passed")
        else:
            logger.warning("⚠️  Some error handling scenarios failed")
    
    async def _test_performance(self) -> None:
        """Test basic performance metrics."""
        test_start = time.time()
        
        try:
            # Test multiple rapid requests
            response_times = []
            success_count = 0
            
            for i in range(10):
                request_start = time.time()
                try:
                    response = requests.get(f"{self.api_url}/health", timeout=5)
                    response_time = time.time() - request_start
                    response_times.append(response_time)
                    
                    if response.status_code == 200:
                        success_count += 1
                        
                except Exception:
                    response_times.append(5.0)  # Timeout value
            
            avg_response_time = sum(response_times) / len(response_times)
            success_rate = success_count / len(response_times)
            
            # Performance criteria
            performance_good = (
                avg_response_time < 1.0 and  # Average under 1 second
                success_rate > 0.9 and      # 90%+ success rate
                max(response_times) < 2.0    # No request over 2 seconds
            )
            
            self.test_results.append(WebTestResult(
                test_name="performance",
                endpoint="/health",
                success=performance_good,
                response_time=time.time() - test_start,
                response_data={
                    "avg_response_time": avg_response_time,
                    "max_response_time": max(response_times),
                    "min_response_time": min(response_times),
                    "success_rate": success_rate,
                    "total_requests": len(response_times)
                }
            ))
            
            if performance_good:
                logger.info(f"✅ Performance test passed (avg: {avg_response_time:.3f}s)")
            else:
                logger.warning(f"⚠️  Performance test concerns (avg: {avg_response_time:.3f}s)")
                
        except Exception as e:
            self.test_results.append(WebTestResult(
                test_name="performance",
                endpoint="/health",
                success=False,
                response_time=time.time() - test_start,
                error=str(e)
            ))
            logger.error(f"❌ Performance test error: {e}")
    
    def _generate_results(self, total_duration: float) -> Dict[str, Any]:
        """Generate comprehensive test results."""
        passed_tests = [r for r in self.test_results if r.success]
        failed_tests = [r for r in self.test_results if not r.success]
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "summary": {
                "total_tests": len(self.test_results),
                "passed": len(passed_tests),
                "failed": len(failed_tests),
                "success_rate": len(passed_tests) / len(self.test_results) * 100 if self.test_results else 0
            },
            "configuration": {
                "web_url": self.base_url,
                "api_url": self.api_url,
                "websocket_url": self.ws_url
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "endpoint": r.endpoint,
                    "success": r.success,
                    "response_time": r.response_time,
                    "status_code": r.status_code,
                    "error": r.error,
                    "response_data": r.response_data
                }
                for r in self.test_results
            ],
            "websocket_data": {
                "messages_received": len(self.websocket_messages),
                "messages": self.websocket_messages
            },
            "recommendations": self._generate_recommendations()
        }
        
        return results
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if not r.success]
        
        if not failed_tests:
            recommendations.append("✅ All tests passed! Web interface is ready for use.")
            return recommendations
        
        # Check for critical failures
        critical_failures = [
            r for r in failed_tests 
            if r.test_name in ["api_health", "web_interface"]
        ]
        
        if critical_failures:
            recommendations.append("🚨 Critical: API or web interface not accessible")
            recommendations.append("   • Check if services are running")
            recommendations.append("   • Verify correct host/port configuration")
            recommendations.append("   • Check firewall and network settings")
        
        # Check for WebSocket issues
        if any(r.test_name == "websocket_connection" and not r.success for r in failed_tests):
            recommendations.append("⚠️  WebSocket connection failed")
            recommendations.append("   • Real-time updates may not work")
            recommendations.append("   • Check WebSocket endpoint configuration")
        
        # Check for performance issues
        perf_test = next((r for r in self.test_results if r.test_name == "performance"), None)
        if perf_test and not perf_test.success:
            recommendations.append("⚡ Performance issues detected")
            recommendations.append("   • Consider server optimization")
            recommendations.append("   • Check server resources")
        
        return recommendations


def print_web_results(results: Dict[str, Any]) -> None:
    """Print formatted web integration test results."""
    print("\n" + "="*60)
    print("🌐 WEB INTEGRATION TEST RESULTS")
    print("="*60)
    
    print(f"\n📊 SUMMARY:")
    summary = results["summary"]
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   ✅ Passed: {summary['passed']}")
    print(f"   ❌ Failed: {summary['failed']}")
    print(f"   📈 Success Rate: {summary['success_rate']:.1f}%")
    print(f"   ⏱️  Duration: {results['total_duration']:.2f}s")
    
    print(f"\n🔧 CONFIGURATION:")
    config = results["configuration"]
    print(f"   Web Interface: {config['web_url']}")
    print(f"   API Backend: {config['api_url']}")
    print(f"   WebSocket: {config['websocket_url']}")
    
    print(f"\n📋 TEST RESULTS:")
    for test in results["test_results"]:
        status = "✅ PASS" if test["success"] else "❌ FAIL"
        endpoint = test["endpoint"][:30] + "..." if len(test["endpoint"]) > 30 else test["endpoint"]
        print(f"   {status} {test['test_name']:20s} {endpoint:25s} ({test['response_time']:.3f}s)")
        
        if test["status_code"]:
            print(f"      Status: {test['status_code']}")
        if test["error"]:
            print(f"      Error: {test['error']}")
    
    # WebSocket summary
    ws_data = results["websocket_data"]
    if ws_data["messages_received"] > 0:
        print(f"\n📡 WEBSOCKET DATA:")
        print(f"   Messages Received: {ws_data['messages_received']}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"   {i}. {rec}")
    
    print("\n" + "="*60)


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Web Interface Integration Test"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to test (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Web interface port (default: 3000)"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="API backend port (default: 8000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create tester
    tester = WebIntegrationTester(
        host=args.host,
        port=args.port,
        api_port=args.api_port
    )
    
    # Run tests
    results = await tester.run_all_tests()
    
    # Print results
    print_web_results(results)
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_path}")
    
    # Exit with appropriate code
    exit_code = 0 if results["summary"]["failed"] == 0 else 1
    print(f"\n🚪 Exiting with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())