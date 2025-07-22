#!/usr/bin/env python3
"""
Run All Tests Suite

Executes the complete test suite including pipeline validation,
demo scenarios, and web integration tests with comprehensive reporting.

Usage:
    python run_all_tests.py [--mode MODE] [--save-results] [--verbose]
"""

import os
import sys
import asyncio
import subprocess
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSuiteRunner:
    """Comprehensive test suite runner."""
    
    def __init__(self, mode: str = "safe", save_results: bool = False, verbose: bool = False):
        """
        Initialize test suite runner.
        
        Args:
            mode: Test mode - "safe" (no costs), "minimal" (low cost), "full" (complete)
            save_results: Whether to save detailed results
            verbose: Enable verbose logging
        """
        self.mode = mode
        self.save_results = save_results
        self.verbose = verbose
        self.start_time = time.time()
        
        # Results storage
        self.test_results = {}
        self.overall_success = True
        self.total_cost = 0.0
        
        # Output directory
        self.output_dir = Path("output") / "test_suite" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info(f"Test Suite Runner initialized")
        logger.info(f"  Mode: {mode}")
        logger.info(f"  Output: {self.output_dir}")
        logger.info(f"  Save Results: {save_results}")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run complete test suite based on selected mode.
        
        Returns:
            Comprehensive test results
        """
        logger.info("🧪 Starting Complete Test Suite")
        
        # Print mode information
        self._print_mode_info()
        
        # Check prerequisites
        if not self._check_prerequisites():
            return self._generate_failure_result("Prerequisites not met")
        
        # Run tests based on mode
        if self.mode == "safe":
            await self._run_safe_tests()
        elif self.mode == "minimal":
            await self._run_minimal_tests()
        elif self.mode == "full":
            await self._run_full_tests()
        else:
            return self._generate_failure_result(f"Unknown mode: {self.mode}")
        
        # Generate final results
        return self._generate_final_results()
    
    def _print_mode_info(self) -> None:
        """Print information about the selected test mode."""
        print("\n" + "="*60)
        print("🧪 TEST SUITE CONFIGURATION")
        print("="*60)
        
        mode_info = {
            "safe": {
                "description": "No API calls, simulated results only",
                "estimated_cost": "$0.00",
                "duration": "2-5 minutes",
                "tests": [
                    "Environment validation",
                    "Configuration checks", 
                    "Simulated pipeline test",
                    "Preview demo",
                    "Dry-run validation"
                ]
            },
            "minimal": {
                "description": "Minimal API calls for basic validation",
                "estimated_cost": "$1.00-3.00",
                "duration": "5-10 minutes",
                "tests": [
                    "API connection tests",
                    "Single scene generation",
                    "Basic web integration",
                    "Cost verification",
                    "Error handling"
                ]
            },
            "full": {
                "description": "Complete test suite with full validation",
                "estimated_cost": "$10.00-25.00",
                "duration": "15-30 minutes",
                "tests": [
                    "Full pipeline validation",
                    "Multi-scene demo",
                    "Web integration suite",
                    "Performance benchmarks",
                    "Comprehensive error testing"
                ]
            }
        }
        
        info = mode_info.get(self.mode, {"description": "Unknown mode"})
        
        print(f"\n📋 Selected Mode: {self.mode.upper()}")
        print(f"   Description: {info['description']}")
        print(f"   Estimated Cost: {info.get('estimated_cost', 'Unknown')}")
        print(f"   Expected Duration: {info.get('duration', 'Unknown')}")
        
        if "tests" in info:
            print(f"\n✅ Tests to Run:")
            for test in info["tests"]:
                print(f"   • {test}")
        
        print(f"\n📁 Output Directory: {self.output_dir}")
    
    def _check_prerequisites(self) -> bool:
        """Check if prerequisites are met."""
        print("\n" + "="*60)
        print("🔍 PREREQUISITE CHECK")
        print("="*60)
        
        prerequisites = {
            "python_version": sys.version_info >= (3, 8),
            "working_directory": Path.cwd().name == "Evergreen",
            "src_directory": (Path.cwd() / "src").exists(),
            "examples_directory": (Path.cwd() / "examples").exists()
        }
        
        # Check API keys for non-safe modes
        if self.mode != "safe":
            prerequisites.update({
                "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
                "runway_api_key": bool(os.getenv("RUNWAY_API_KEY"))
            })
        
        print("\n📋 Checking Prerequisites:")
        all_good = True
        
        for check, passed in prerequisites.items():
            status = "✅ OK" if passed else "❌ FAIL"
            print(f"   {status} {check.replace('_', ' ').title()}")
            if not passed:
                all_good = False
        
        if not all_good:
            print("\n❌ Prerequisites not met. Please resolve issues above.")
            
            # Provide specific guidance
            if not prerequisites.get("python_version", True):
                print("   • Upgrade to Python 3.8 or higher")
            
            if not prerequisites.get("working_directory", True):
                print("   • Run from the Evergreen project root directory")
            
            if not prerequisites.get("openai_api_key", True) and self.mode != "safe":
                print("   • Set OPENAI_API_KEY environment variable")
            
            if not prerequisites.get("runway_api_key", True) and self.mode != "safe":
                print("   • Set RUNWAY_API_KEY environment variable")
        else:
            print("\n✅ All prerequisites met!")
        
        return all_good
    
    async def _run_safe_tests(self) -> None:
        """Run safe tests with no API calls."""
        logger.info("🛡️ Running Safe Mode Tests")
        
        # Test 1: Pipeline validation (dry run)
        await self._run_test(
            "pipeline_validation",
            "python test_pipeline_validation.py --dry-run --output " + 
            str(self.output_dir / "pipeline_validation.json")
        )
        
        # Test 2: Demo preview
        await self._run_test(
            "demo_preview",
            "python examples/complete_pipeline_demo.py --preview-only --output-dir " +
            str(self.output_dir / "demo_preview")
        )
        
        # Test 3: Configuration validation
        await self._run_test(
            "config_validation",
            "python -c \"import src.services.unified_pipeline; print('Configuration OK')\""
        )
    
    async def _run_minimal_tests(self) -> None:
        """Run minimal tests with basic API validation."""
        logger.info("⚡ Running Minimal Mode Tests")
        
        # Test 1: Pipeline validation (skip generation)
        await self._run_test(
            "pipeline_validation",
            "python test_pipeline_validation.py --skip-generation --output " +
            str(self.output_dir / "pipeline_validation.json")
        )
        
        # Test 2: Single scene demo
        await self._run_test(
            "single_scene_demo",
            "python examples/complete_pipeline_demo.py --scene-count 1 --duration 5 --output-dir " +
            str(self.output_dir / "minimal_demo")
        )
        
        # Test 3: Basic web integration
        await self._run_test(
            "web_integration_basic",
            "python test_web_integration.py --output " +
            str(self.output_dir / "web_integration.json")
        )
    
    async def _run_full_tests(self) -> None:
        """Run complete test suite."""
        logger.info("🚀 Running Full Mode Tests")
        
        # Test 1: Complete pipeline validation
        await self._run_test(
            "pipeline_validation_full",
            "python test_pipeline_validation.py --output " +
            str(self.output_dir / "pipeline_validation.json")
        )
        
        # Test 2: Multi-scene demo
        await self._run_test(
            "multi_scene_demo",
            "python examples/complete_pipeline_demo.py --scene-count 3 --duration 10 --output-dir " +
            str(self.output_dir / "full_demo")
        )
        
        # Test 3: Complete web integration
        await self._run_test(
            "web_integration_full",
            "python test_web_integration.py --output " +
            str(self.output_dir / "web_integration.json")
        )
        
        # Test 4: Performance benchmarks
        await self._run_test(
            "performance_test",
            "python test_pipeline_validation.py --verbose --output " +
            str(self.output_dir / "performance.json")
        )
    
    async def _run_test(self, test_name: str, command: str) -> None:
        """
        Run a single test and capture results.
        
        Args:
            test_name: Name of the test
            command: Command to execute
        """
        print(f"\n🧪 Running {test_name}...")
        start_time = time.time()
        
        try:
            # Add verbose flag if enabled
            if self.verbose and "--verbose" not in command:
                command += " --verbose"
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            # Store results
            self.test_results[test_name] = {
                "command": command,
                "success": success,
                "duration": duration,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if success:
                print(f"   ✅ {test_name} completed successfully ({duration:.1f}s)")
            else:
                print(f"   ❌ {test_name} failed ({duration:.1f}s)")
                print(f"      Error: {result.stderr.strip()}")
                self.overall_success = False
            
            # Extract cost information if available
            self._extract_cost_info(test_name, result.stdout)
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"   ⏰ {test_name} timed out after {duration:.1f}s")
            
            self.test_results[test_name] = {
                "command": command,
                "success": False,
                "duration": duration,
                "error": "Timeout after 30 minutes"
            }
            self.overall_success = False
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ {test_name} error: {e}")
            
            self.test_results[test_name] = {
                "command": command,
                "success": False,
                "duration": duration,
                "error": str(e)
            }
            self.overall_success = False
    
    def _extract_cost_info(self, test_name: str, stdout: str) -> None:
        """Extract cost information from test output."""
        try:
            # Look for cost patterns in output
            lines = stdout.split('\n')
            for line in lines:
                if '$' in line and any(word in line.lower() for word in ['cost', 'total', 'spent']):
                    # Try to extract numeric cost
                    import re
                    matches = re.findall(r'\$(\d+\.?\d*)', line)
                    if matches:
                        cost = float(matches[0])
                        self.test_results[test_name]['extracted_cost'] = cost
                        self.total_cost += cost
                        break
        except Exception:
            pass  # Cost extraction is optional
    
    def _generate_failure_result(self, reason: str) -> Dict[str, Any]:
        """Generate result for failed test suite."""
        return {
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode,
            "success": False,
            "failure_reason": reason,
            "duration": time.time() - self.start_time
        }
    
    def _generate_final_results(self) -> Dict[str, Any]:
        """Generate comprehensive final results."""
        total_duration = time.time() - self.start_time
        
        # Count successes and failures
        successful_tests = [name for name, result in self.test_results.items() if result.get("success")]
        failed_tests = [name for name, result in self.test_results.items() if not result.get("success")]
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode,
            "overall_success": self.overall_success,
            "total_duration": total_duration,
            "summary": {
                "total_tests": len(self.test_results),
                "successful": len(successful_tests),
                "failed": len(failed_tests),
                "success_rate": len(successful_tests) / len(self.test_results) * 100 if self.test_results else 0
            },
            "costs": {
                "estimated_total": self.total_cost,
                "mode_budget": self._get_mode_budget()
            },
            "test_results": self.test_results,
            "output_directory": str(self.output_dir),
            "recommendations": self._generate_recommendations()
        }
        
        # Save results if requested
        if self.save_results:
            results_file = self.output_dir / "complete_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to: {results_file}")
        
        return results
    
    def _get_mode_budget(self) -> str:
        """Get budget information for the current mode."""
        budgets = {
            "safe": "$0.00",
            "minimal": "$1.00-3.00", 
            "full": "$10.00-25.00"
        }
        return budgets.get(self.mode, "Unknown")
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if self.overall_success:
            recommendations.append("🎉 All tests passed successfully!")
            
            if self.mode == "safe":
                recommendations.append("✅ Safe mode validation complete - ready for minimal testing")
                recommendations.append("💡 Next: Run with --mode minimal to test with actual API calls")
            elif self.mode == "minimal":
                recommendations.append("✅ Minimal testing complete - system ready for production")
                recommendations.append("💡 Next: Run with --mode full for comprehensive validation")
            else:  # full
                recommendations.append("✅ Full validation complete - system ready for production use")
                recommendations.append("🚀 Pipeline is fully operational and tested")
        else:
            # Analyze failures
            failed_tests = [name for name, result in self.test_results.items() if not result.get("success")]
            
            if "pipeline_validation" in failed_tests:
                recommendations.append("🚨 Pipeline validation failed - check API keys and connections")
            
            if any("demo" in test for test in failed_tests):
                recommendations.append("⚠️  Demo generation failed - verify API quotas and billing")
            
            if "web_integration" in failed_tests:
                recommendations.append("🌐 Web integration issues - check if services are running")
            
            recommendations.append("🔧 Review individual test logs for specific error details")
            recommendations.append("📚 Consult TEST_SUITE_README.md for troubleshooting guidance")
        
        # Cost recommendations
        if self.total_cost > 0:
            recommendations.append(f"💰 Total estimated cost: ${self.total_cost:.2f}")
            if self.total_cost > 20:
                recommendations.append("💡 Consider using --mode minimal for routine testing")
        
        return recommendations


def print_final_results(results: Dict[str, Any]) -> None:
    """Print formatted final results."""
    print("\n" + "="*60)
    print("🏁 COMPLETE TEST SUITE RESULTS")
    print("="*60)
    
    # Overall status
    status = "✅ SUCCESS" if results["overall_success"] else "❌ FAILURE"
    print(f"\n🎯 Overall Status: {status}")
    print(f"📊 Mode: {results['mode'].upper()}")
    print(f"⏱️  Total Duration: {results['total_duration']:.1f}s")
    
    # Summary
    summary = results["summary"]
    print(f"\n📈 Test Summary:")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   ✅ Successful: {summary['successful']}")
    print(f"   ❌ Failed: {summary['failed']}")
    print(f"   📊 Success Rate: {summary['success_rate']:.1f}%")
    
    # Cost information
    costs = results["costs"]
    if costs["estimated_total"] > 0:
        print(f"\n💰 Cost Information:")
        print(f"   Estimated Total: ${costs['estimated_total']:.2f}")
        print(f"   Mode Budget: {costs['mode_budget']}")
    
    # Individual test results
    print(f"\n📋 Individual Test Results:")
    for test_name, test_result in results["test_results"].items():
        status = "✅ PASS" if test_result["success"] else "❌ FAIL"
        duration = test_result["duration"]
        print(f"   {status} {test_name:25s} ({duration:.1f}s)")
        
        if "extracted_cost" in test_result:
            print(f"      💰 Cost: ${test_result['extracted_cost']:.2f}")
        
        if not test_result["success"] and "error" in test_result:
            print(f"      Error: {test_result['error']}")
    
    # Output files
    print(f"\n📁 Output Directory: {results['output_directory']}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"   {i}. {rec}")
    
    print("\n" + "="*60)


async def main():
    """Main test suite function."""
    parser = argparse.ArgumentParser(
        description="Complete Test Suite Runner"
    )
    parser.add_argument(
        "--mode",
        choices=["safe", "minimal", "full"],
        default="safe",
        help="Test mode: safe (no costs), minimal (low cost), full (complete)"
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save detailed results to JSON files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt for cost-incurring modes"
    )
    
    args = parser.parse_args()
    
    # Cost warning for non-safe modes
    if args.mode != "safe" and not args.confirm:
        mode_costs = {
            "minimal": "$1-3",
            "full": "$10-25"
        }
        
        print(f"\n⚠️  WARNING: {args.mode.upper()} mode will incur API costs!")
        print(f"   Estimated cost: {mode_costs.get(args.mode, 'Unknown')}")
        print(f"   Use --mode safe for cost-free testing")
        
        response = input(f"\nContinue with {args.mode} mode? (y/N): ")
        if response.lower() != 'y':
            print("Exiting. Use --mode safe for cost-free testing.")
            return
    
    # Run test suite
    runner = TestSuiteRunner(
        mode=args.mode,
        save_results=args.save_results,
        verbose=args.verbose
    )
    
    try:
        results = await runner.run_all_tests()
        print_final_results(results)
        
        # Exit with appropriate code
        exit_code = 0 if results["overall_success"] else 1
        print(f"\n🚪 Exiting with code {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())