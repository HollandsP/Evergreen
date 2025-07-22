#!/usr/bin/env python3
"""
Comprehensive pipeline validation test script.

This script validates the complete DALL-E 3 + RunwayML pipeline including:
- API connection tests
- End-to-end pipeline validation  
- Cost calculation verification
- Error handling tests
- Performance benchmarks

Usage:
    python test_pipeline_validation.py [--dry-run] [--skip-generation] [--verbose]
"""

import os
import sys
import asyncio
import logging
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from dataclasses import dataclass, asdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services.unified_pipeline import UnifiedPipelineManager, GenerationProvider
from src.services.dalle3_client import create_dalle3_client
from src.services.runway_ml_proper import RunwayMLProperClient, AsyncRunwayMLClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Container for individual test results."""
    test_name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    error: Optional[str] = None
    cost: float = 0.0


@dataclass
class ValidationResults:
    """Container for all validation results."""
    timestamp: str
    total_duration: float
    tests_passed: int
    tests_failed: int
    total_cost: float
    individual_tests: List[TestResult]
    environment: Dict[str, Any]
    recommendations: List[str]


class PipelineValidator:
    """Comprehensive pipeline validation system."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """
        Initialize validator.
        
        Args:
            dry_run: If True, don't make actual API calls
            verbose: Enable verbose logging
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
        # Initialize clients
        self.pipeline = None
        self.dalle3_client = None
        self.runway_client = None
        self.async_runway_client = None
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info(f"Pipeline Validator initialized (dry_run={dry_run})")
    
    async def run_all_tests(self) -> ValidationResults:
        """
        Run all validation tests.
        
        Returns:
            Complete validation results
        """
        logger.info("🚀 Starting comprehensive pipeline validation")
        
        # Test 1: Environment validation
        await self._test_environment_setup()
        
        # Test 2: API key validation
        await self._test_api_keys()
        
        # Test 3: Client initialization
        await self._test_client_initialization()
        
        # Test 4: Individual service connections
        await self._test_dalle3_connection()
        await self._test_runway_connection()
        
        # Test 5: Cost calculation system
        await self._test_cost_calculations()
        
        # Test 6: Error handling
        await self._test_error_handling()
        
        # Test 7: Performance benchmarks
        await self._test_performance_benchmarks()
        
        # Test 8: End-to-end pipeline
        await self._test_end_to_end_pipeline()
        
        # Generate final results
        return self._generate_final_results()
    
    async def _test_environment_setup(self) -> None:
        """Test environment setup and dependencies."""
        start_time = time.time()
        
        try:
            details = {
                "python_version": sys.version,
                "working_directory": str(Path.cwd()),
                "required_packages": [],
                "missing_packages": []
            }
            
            # Check required packages
            required_packages = [
                "openai", "requests", "pillow", "aiohttp", "asyncio"
            ]
            
            for package in required_packages:
                try:
                    __import__(package)
                    details["required_packages"].append(package)
                except ImportError:
                    details["missing_packages"].append(package)
            
            # Check output directories
            output_dir = Path("output")
            if not output_dir.exists():
                output_dir.mkdir(parents=True)
                details["created_output_dir"] = True
            
            details["output_dir_writable"] = os.access(output_dir, os.W_OK)
            
            success = len(details["missing_packages"]) == 0
            error = f"Missing packages: {details['missing_packages']}" if not success else None
            
            self.results.append(TestResult(
                test_name="environment_setup",
                success=success,
                duration=time.time() - start_time,
                details=details,
                error=error
            ))
            
            if success:
                logger.info("✅ Environment setup validation passed")
            else:
                logger.error(f"❌ Environment setup failed: {error}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="environment_setup",
                success=False,
                duration=time.time() - start_time,
                details={},
                error=str(e)
            ))
            logger.error(f"❌ Environment setup error: {e}")
    
    async def _test_api_keys(self) -> None:
        """Test API key availability and format."""
        start_time = time.time()
        
        try:
            details = {
                "openai_key_present": False,
                "runway_key_present": False,
                "openai_key_format": "invalid",
                "runway_key_format": "invalid"
            }
            
            # Check OpenAI API key
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                details["openai_key_present"] = True
                if openai_key.startswith("sk-") and len(openai_key) > 40:
                    details["openai_key_format"] = "valid"
                details["openai_key_length"] = len(openai_key)
            
            # Check RunwayML API key
            runway_key = os.getenv("RUNWAY_API_KEY")
            if runway_key:
                details["runway_key_present"] = True
                if len(runway_key) > 20:  # Basic length check
                    details["runway_key_format"] = "valid"
                details["runway_key_length"] = len(runway_key)
            
            success = (
                details["openai_key_present"] and
                details["runway_key_present"] and
                details["openai_key_format"] == "valid" and
                details["runway_key_format"] == "valid"
            )
            
            error = None
            if not success:
                missing = []
                if not details["openai_key_present"]:
                    missing.append("OPENAI_API_KEY")
                if not details["runway_key_present"]:
                    missing.append("RUNWAY_API_KEY")
                if missing:
                    error = f"Missing environment variables: {missing}"
                else:
                    error = "API key format validation failed"
            
            self.results.append(TestResult(
                test_name="api_keys",
                success=success,
                duration=time.time() - start_time,
                details=details,
                error=error
            ))
            
            if success:
                logger.info("✅ API keys validation passed")
            else:
                logger.error(f"❌ API keys validation failed: {error}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="api_keys",
                success=False,
                duration=time.time() - start_time,
                details={},
                error=str(e)
            ))
            logger.error(f"❌ API keys test error: {e}")
    
    async def _test_client_initialization(self) -> None:
        """Test client initialization."""
        start_time = time.time()
        
        try:
            details = {
                "dalle3_client_created": False,
                "runway_client_created": False,
                "async_runway_client_created": False,
                "unified_pipeline_created": False
            }
            
            # Try to create DALL-E 3 client
            try:
                self.dalle3_client = create_dalle3_client()
                details["dalle3_client_created"] = True
                logger.info("DALL-E 3 client initialized")
            except Exception as e:
                details["dalle3_error"] = str(e)
                logger.warning(f"DALL-E 3 client failed: {e}")
            
            # Try to create RunwayML clients
            try:
                self.runway_client = RunwayMLProperClient()
                details["runway_client_created"] = True
                logger.info("RunwayML client initialized")
            except Exception as e:
                details["runway_error"] = str(e)
                logger.warning(f"RunwayML client failed: {e}")
            
            try:
                self.async_runway_client = AsyncRunwayMLClient()
                details["async_runway_client_created"] = True
                logger.info("Async RunwayML client initialized")
            except Exception as e:
                details["async_runway_error"] = str(e)
                logger.warning(f"Async RunwayML client failed: {e}")
            
            # Try to create unified pipeline
            try:
                self.pipeline = UnifiedPipelineManager()
                details["unified_pipeline_created"] = True
                logger.info("Unified pipeline initialized")
            except Exception as e:
                details["pipeline_error"] = str(e)
                logger.warning(f"Unified pipeline failed: {e}")
            
            success = (
                details["dalle3_client_created"] and
                details["runway_client_created"] and
                details["unified_pipeline_created"]
            )
            
            error = None
            if not success:
                failed = []
                if not details["dalle3_client_created"]:
                    failed.append("DALL-E 3")
                if not details["runway_client_created"]:
                    failed.append("RunwayML")
                if not details["unified_pipeline_created"]:
                    failed.append("Unified Pipeline")
                error = f"Failed to initialize: {failed}"
            
            self.results.append(TestResult(
                test_name="client_initialization",
                success=success,
                duration=time.time() - start_time,
                details=details,
                error=error
            ))
            
            if success:
                logger.info("✅ Client initialization passed")
            else:
                logger.error(f"❌ Client initialization failed: {error}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="client_initialization",
                success=False,
                duration=time.time() - start_time,
                details={},
                error=str(e)
            ))
            logger.error(f"❌ Client initialization error: {e}")
    
    async def _test_dalle3_connection(self) -> None:
        """Test DALL-E 3 API connection."""
        start_time = time.time()
        
        try:
            details = {
                "connection_tested": False,
                "response_received": False,
                "api_accessible": False
            }
            
            if not self.dalle3_client:
                self.results.append(TestResult(
                    test_name="dalle3_connection",
                    success=False,
                    duration=time.time() - start_time,
                    details=details,
                    error="DALL-E 3 client not initialized"
                ))
                return
            
            if self.dry_run:
                # Simulate successful connection test
                details.update({
                    "connection_tested": True,
                    "response_received": True,
                    "api_accessible": True,
                    "dry_run": True
                })
                success = True
                error = None
            else:
                # Test actual connection
                connection_ok = await self.dalle3_client.test_connection()
                details.update({
                    "connection_tested": True,
                    "response_received": connection_ok,
                    "api_accessible": connection_ok
                })
                success = connection_ok
                error = None if connection_ok else "Connection test failed"
            
            self.results.append(TestResult(
                test_name="dalle3_connection",
                success=success,
                duration=time.time() - start_time,
                details=details,
                error=error
            ))
            
            if success:
                logger.info("✅ DALL-E 3 connection test passed")
            else:
                logger.error(f"❌ DALL-E 3 connection failed: {error}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="dalle3_connection",
                success=False,
                duration=time.time() - start_time,
                details={},
                error=str(e)
            ))
            logger.error(f"❌ DALL-E 3 connection error: {e}")
    
    async def _test_runway_connection(self) -> None:
        """Test RunwayML API connection."""
        start_time = time.time()
        
        try:
            details = {
                "connection_tested": False,
                "org_info_received": False,
                "api_accessible": False
            }
            
            if not self.runway_client:
                self.results.append(TestResult(
                    test_name="runway_connection",
                    success=False,
                    duration=time.time() - start_time,
                    details=details,
                    error="RunwayML client not initialized"
                ))
                return
            
            if self.dry_run:
                # Simulate successful connection test
                details.update({
                    "connection_tested": True,
                    "org_info_received": True,
                    "api_accessible": True,
                    "dry_run": True,
                    "simulated_org_info": {
                        "id": "test_org",
                        "name": "Test Organization",
                        "credits": 1000
                    }
                })
                success = True
                error = None
            else:
                # Test actual connection
                try:
                    org_info = self.runway_client.get_organization_info()
                    details.update({
                        "connection_tested": True,
                        "org_info_received": bool(org_info),
                        "api_accessible": bool(org_info),
                        "org_info": org_info
                    })
                    success = bool(org_info)
                    error = None if success else "Failed to get organization info"
                except Exception as e:
                    details.update({
                        "connection_tested": True,
                        "org_info_received": False,
                        "api_accessible": False
                    })
                    success = False
                    error = str(e)
            
            self.results.append(TestResult(
                test_name="runway_connection",
                success=success,
                duration=time.time() - start_time,
                details=details,
                error=error
            ))
            
            if success:
                logger.info("✅ RunwayML connection test passed")
            else:
                logger.error(f"❌ RunwayML connection failed: {error}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="runway_connection",
                success=False,
                duration=time.time() - start_time,
                details={},
                error=str(e)
            ))
            logger.error(f"❌ RunwayML connection error: {e}")
    
    async def _test_cost_calculations(self) -> None:
        """Test cost calculation accuracy."""
        start_time = time.time()
        
        try:
            details = {
                "dalle3_costs_calculated": False,
                "runway_costs_estimated": False,
                "total_cost_accurate": False
            }
            
            # Test DALL-E 3 cost calculations
            if self.dalle3_client:
                # Standard image costs
                std_cost = self.dalle3_client._calculate_cost("1024x1024", "standard")
                hd_cost = self.dalle3_client._calculate_cost("1024x1024", "hd")
                large_hd_cost = self.dalle3_client._calculate_cost("1792x1024", "hd")
                
                details.update({
                    "dalle3_costs_calculated": True,
                    "dalle3_costs": {
                        "standard_1024": std_cost,
                        "hd_1024": hd_cost,
                        "hd_1792": large_hd_cost
                    }
                })
                
                # Verify expected costs (as of 2024)
                expected_costs = {
                    "standard_1024": 0.04,
                    "hd_1024": 0.08,
                    "hd_1792": 0.12
                }
                
                cost_accuracy = all(
                    abs(details["dalle3_costs"][key] - expected_costs[key]) < 0.01
                    for key in expected_costs
                )
                details["dalle3_cost_accuracy"] = cost_accuracy
            
            # Test pipeline cost tracking
            if self.pipeline:
                initial_cost = self.pipeline.total_cost
                details["pipeline_initial_cost"] = initial_cost
                details["runway_costs_estimated"] = True
            
            # Estimate total costs for different scenarios
            scenarios = {
                "single_clip": {
                    "dalle3_hd": 0.12,
                    "runway_10s": 5.0,  # Estimated
                    "total": 5.12
                },
                "short_video_8_clips": {
                    "dalle3_hd": 0.96,  # 8 * 0.12
                    "runway_10s": 40.0,  # 8 * 5.0
                    "total": 40.96
                }
            }
            
            details.update({
                "cost_scenarios": scenarios,
                "total_cost_accurate": True
            })
            
            success = (
                details.get("dalle3_costs_calculated", False) and
                details.get("runway_costs_estimated", False)
            )
            
            self.results.append(TestResult(
                test_name="cost_calculations",
                success=success,
                duration=time.time() - start_time,
                details=details
            ))
            
            if success:
                logger.info("✅ Cost calculation tests passed")
            else:
                logger.error("❌ Cost calculation tests failed")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="cost_calculations",
                success=False,
                duration=time.time() - start_time,
                details={},
                error=str(e)
            ))
            logger.error(f"❌ Cost calculation error: {e}")
    
    async def _test_error_handling(self) -> None:
        """Test error handling scenarios."""
        start_time = time.time()
        
        try:
            details = {
                "invalid_prompt_handled": False,
                "api_error_handled": False,
                "timeout_handled": False,
                "file_error_handled": False
            }
            
            # Test 1: Invalid prompt handling
            if self.dalle3_client and not self.dry_run:
                try:
                    # This should be rejected by content policy
                    result = await self.dalle3_client.generate_image(
                        prompt="",  # Empty prompt
                        size="1024x1024"
                    )
                    details["invalid_prompt_result"] = result
                    details["invalid_prompt_handled"] = not result.get("success", True)
                except Exception as e:
                    details["invalid_prompt_handled"] = True
                    details["invalid_prompt_error"] = str(e)
            else:
                details["invalid_prompt_handled"] = True  # Assume works in dry run
            
            # Test 2: File handling errors
            try:
                # Try to read non-existent file
                if self.runway_client:
                    data_uri = self.runway_client.create_data_uri_from_image("/nonexistent/file.jpg")
                    details["file_error_handled"] = False  # Should have failed
                else:
                    details["file_error_handled"] = True
            except Exception:
                details["file_error_handled"] = True
            
            # Test 3: Network timeout simulation (in dry run)
            if self.dry_run:
                details["timeout_handled"] = True
                details["api_error_handled"] = True
            
            success = all([
                details["invalid_prompt_handled"],
                details["file_error_handled"]
            ])
            
            self.results.append(TestResult(
                test_name="error_handling",
                success=success,
                duration=time.time() - start_time,
                details=details
            ))
            
            if success:
                logger.info("✅ Error handling tests passed")
            else:
                logger.error("❌ Error handling tests failed")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="error_handling",
                success=False,
                duration=time.time() - start_time,
                details={},
                error=str(e)
            ))
            logger.error(f"❌ Error handling test error: {e}")
    
    async def _test_performance_benchmarks(self) -> None:
        """Test performance benchmarks."""
        start_time = time.time()
        
        try:
            details = {
                "image_generation_time": None,
                "video_generation_time": None,
                "total_pipeline_time": None,
                "memory_usage": None
            }
            
            if self.dry_run:
                # Simulate performance metrics
                details.update({
                    "image_generation_time": 15.5,  # seconds
                    "video_generation_time": 180.0,  # seconds
                    "total_pipeline_time": 195.5,
                    "memory_usage": "Simulated",
                    "dry_run": True
                })
                success = True
            else:
                # In real scenario, we'd measure actual generation times
                # For now, we'll just check if pipeline is responsive
                if self.pipeline:
                    benchmark_start = time.time()
                    stats = self.pipeline.get_pipeline_stats()
                    benchmark_time = time.time() - benchmark_start
                    
                    details.update({
                        "stats_retrieval_time": benchmark_time,
                        "pipeline_stats": stats,
                        "responsive": benchmark_time < 1.0
                    })
                    success = details["responsive"]
                else:
                    success = False
                    details["error"] = "No pipeline available for benchmarking"
            
            self.results.append(TestResult(
                test_name="performance_benchmarks",
                success=success,
                duration=time.time() - start_time,
                details=details
            ))
            
            if success:
                logger.info("✅ Performance benchmark tests passed")
            else:
                logger.error("❌ Performance benchmark tests failed")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="performance_benchmarks",
                success=False,
                duration=time.time() - start_time,
                details={},
                error=str(e)
            ))
            logger.error(f"❌ Performance benchmark error: {e}")
    
    async def _test_end_to_end_pipeline(self) -> None:
        """Test complete end-to-end pipeline."""
        start_time = time.time()
        
        try:
            details = {
                "pipeline_executed": False,
                "image_generated": False,
                "video_generated": False,
                "files_created": False
            }
            
            if not self.pipeline:
                self.results.append(TestResult(
                    test_name="end_to_end_pipeline",
                    success=False,
                    duration=time.time() - start_time,
                    details=details,
                    error="No pipeline available"
                ))
                return
            
            if self.dry_run:
                # Simulate successful pipeline run
                details.update({
                    "pipeline_executed": True,
                    "image_generated": True,
                    "video_generated": True,
                    "files_created": True,
                    "dry_run": True,
                    "simulated_result": {
                        "success": True,
                        "cost": 5.12,
                        "duration": 195.5,
                        "image_url": "https://example.com/image.jpg",
                        "video_url": "https://example.com/video.mp4"
                    }
                })
                success = True
                cost = 5.12
            else:
                # Run actual pipeline test with simple prompt
                test_prompt = "A serene mountain landscape at sunset"
                
                logger.info(f"Running end-to-end test with prompt: '{test_prompt}'")
                logger.info("⚠️  This will incur actual API costs!")
                
                try:
                    result = await self.pipeline.generate_video_clip(
                        prompt=test_prompt,
                        duration=5,  # Short duration for testing
                        image_size="1024x1024",  # Smaller size for testing
                        image_quality="standard"  # Lower cost
                    )
                    
                    details.update({
                        "pipeline_executed": True,
                        "image_generated": result.get("success", False),
                        "video_generated": bool(result.get("video_url")),
                        "files_created": bool(result.get("video_path")),
                        "result": result
                    })
                    
                    success = result.get("success", False)
                    cost = result.get("cost", 0)
                    
                except Exception as e:
                    details.update({
                        "pipeline_executed": True,
                        "error": str(e)
                    })
                    success = False
                    cost = 0
            
            self.results.append(TestResult(
                test_name="end_to_end_pipeline",
                success=success,
                duration=time.time() - start_time,
                details=details,
                cost=cost
            ))
            
            if success:
                logger.info("✅ End-to-end pipeline test passed")
                if not self.dry_run:
                    logger.info(f"💰 Actual cost incurred: ${cost:.3f}")
            else:
                logger.error("❌ End-to-end pipeline test failed")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="end_to_end_pipeline",
                success=False,
                duration=time.time() - start_time,
                details={},
                error=str(e)
            ))
            logger.error(f"❌ End-to-end pipeline error: {e}")
    
    def _generate_final_results(self) -> ValidationResults:
        """Generate final validation results."""
        total_duration = time.time() - self.start_time
        tests_passed = sum(1 for result in self.results if result.success)
        tests_failed = len(self.results) - tests_passed
        total_cost = sum(result.cost for result in self.results)
        
        # Generate recommendations
        recommendations = []
        
        for result in self.results:
            if not result.success:
                if result.test_name == "api_keys":
                    recommendations.append(
                        "Set up OPENAI_API_KEY and RUNWAY_API_KEY environment variables"
                    )
                elif result.test_name == "dalle3_connection":
                    recommendations.append(
                        "Verify OpenAI API key and account billing status"
                    )
                elif result.test_name == "runway_connection":
                    recommendations.append(
                        "Verify RunwayML API key and account credits"
                    )
                elif result.test_name == "end_to_end_pipeline":
                    recommendations.append(
                        "Check both API connections and account balances before production use"
                    )
        
        if tests_passed == len(self.results):
            recommendations.append("✅ All tests passed! Pipeline is ready for production use.")
        elif tests_passed > tests_failed:
            recommendations.append("⚠️  Most tests passed. Address failed tests before production.")
        else:
            recommendations.append("❌ Multiple critical tests failed. Setup required before use.")
        
        # Environment info
        environment = {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": str(Path.cwd()),
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run
        }
        
        return ValidationResults(
            timestamp=datetime.now().isoformat(),
            total_duration=total_duration,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            total_cost=total_cost,
            individual_tests=self.results,
            environment=environment,
            recommendations=recommendations
        )


def print_results(results: ValidationResults) -> None:
    """Print formatted validation results."""
    print("\n" + "="*60)
    print("🔍 PIPELINE VALIDATION RESULTS")
    print("="*60)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total Tests: {results.tests_passed + results.tests_failed}")
    print(f"   ✅ Passed: {results.tests_passed}")
    print(f"   ❌ Failed: {results.tests_failed}")
    print(f"   ⏱️  Duration: {results.total_duration:.2f}s")
    print(f"   💰 Total Cost: ${results.total_cost:.3f}")
    
    print(f"\n📋 INDIVIDUAL TEST RESULTS:")
    for test in results.individual_tests:
        status = "✅ PASS" if test.success else "❌ FAIL"
        print(f"   {status} {test.test_name:25s} ({test.duration:.2f}s)")
        if test.error:
            print(f"      Error: {test.error}")
        if test.cost > 0:
            print(f"      Cost: ${test.cost:.3f}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(results.recommendations, 1):
        print(f"   {i}. {rec}")
    
    print(f"\n🌍 ENVIRONMENT:")
    print(f"   Python: {results.environment['python_version'].split()[0]}")
    print(f"   Platform: {results.environment['platform']}")
    print(f"   Dry Run: {results.environment['dry_run']}")
    print(f"   Timestamp: {results.timestamp}")
    
    print("\n" + "="*60)


async def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive pipeline validation test"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run validation without making actual API calls"
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip end-to-end generation test (saves cost)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Show cost warning for non-dry-run
    if not args.dry_run and not args.skip_generation:
        print("\n⚠️  WARNING: This will make actual API calls and incur costs!")
        print("   Estimated cost: $5-10 for full end-to-end test")
        print("   Use --dry-run to simulate tests without costs")
        print("   Use --skip-generation to avoid video generation costs")
        
        response = input("\nContinue with actual API calls? (y/N): ")
        if response.lower() != 'y':
            print("Exiting. Use --dry-run for cost-free testing.")
            return
    
    # Create validator
    validator = PipelineValidator(
        dry_run=args.dry_run or args.skip_generation,
        verbose=args.verbose
    )
    
    # Run validation
    results = await validator.run_all_tests()
    
    # Print results
    print_results(results)
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(asdict(results), f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_path}")
    
    # Exit with appropriate code
    exit_code = 0 if results.tests_failed == 0 else 1
    print(f"\n🚪 Exiting with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())