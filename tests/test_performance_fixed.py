#!/usr/bin/env python3
"""
Performance and resource usage testing for core services.
This test validates resource cleanup, memory leaks, and performance bottlenecks.
"""

import sys
import os
import time
import tempfile
import subprocess
import psutil
import threading
from unittest.mock import Mock, patch

sys.path.insert(0, '/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen')

def test_runway_resource_usage():
    """Test Runway service resource usage during video generation."""
    
    print("🔍 Testing Runway service resource usage...")
    
    from src.services.runway_client import RunwayClient
    
    # Monitor process during video generation
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    initial_fds = len(process.open_files())
    
    client = RunwayClient()
    
    # Generate multiple videos to test resource accumulation
    jobs = []
    for i in range(5):
        job = client.generate_video(f"test prompt {i}", duration=3.0)
        jobs.append(job)
    
    # Check status multiple times
    for _ in range(3):
        for job in jobs:
            status = client.get_generation_status(job['id'])
    
    # Download videos
    for job in jobs:
        status = client.get_generation_status(job['id'])
        if status.get('video_url'):
            data = client.download_video(status['video_url'])
    
    # Check resource usage
    final_memory = process.memory_info().rss
    final_fds = len(process.open_files())
    
    memory_growth = final_memory - initial_memory
    fd_growth = final_fds - initial_fds
    
    print(f"   Memory growth: {memory_growth / 1024 / 1024:.1f} MB")
    print(f"   File descriptor growth: {fd_growth}")
    
    # Check for excessive resource usage
    if memory_growth > 50 * 1024 * 1024:  # 50MB
        print(f"   ⚠️ WARNING: High memory growth ({memory_growth / 1024 / 1024:.1f} MB)")
    
    if fd_growth > 5:
        print(f"   ⚠️ WARNING: File descriptor leak ({fd_growth} FDs)")
    
    if memory_growth < 50 * 1024 * 1024 and fd_growth <= 5:
        print("   ✅ Resource usage within acceptable limits")
        return True
    else:
        print("   ❌ Excessive resource usage detected")
        return False


def test_video_worker_performance():
    """Test video generation worker performance characteristics."""
    
    print("\n🔍 Testing video generation worker performance...")
    
    # Test script parsing performance
    start_time = time.time()
    
    # Read the video generation worker to analyze complexity
    worker_file = '/mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/workers/tasks/video_generation.py'
    
    try:
        with open(worker_file, 'r') as f:
            content = f.read()
        
        parse_time = time.time() - start_time
        
        # Analyze function complexity
        functions = {}
        lines = content.split('\n')
        current_function = None
        
        for line in lines:
            if line.strip().startswith('def '):
                current_function = line.strip().split('(')[0].replace('def ', '')
                functions[current_function] = 0
            elif current_function and line.strip():
                functions[current_function] += 1
        
        # Calculate complexity metrics
        total_lines = len([l for l in lines if l.strip()])
        avg_function_length = sum(functions.values()) / len(functions) if functions else 0
        max_function_length = max(functions.values()) if functions else 0
        complex_functions = [f for f, length in functions.items() if length > 80]
        
        print(f"   Total lines: {total_lines}")
        print(f"   Functions: {len(functions)}")
        print(f"   Average function length: {avg_function_length:.1f} lines")
        print(f"   Longest function: {max_function_length} lines")
        print(f"   Complex functions (>80 lines): {len(complex_functions)}")
        
        # Performance assessment
        performance_score = 0
        issues = []
        
        if avg_function_length > 50:
            issues.append(f"High average function complexity ({avg_function_length:.1f} lines)")
        else:
            performance_score += 25
        
        if max_function_length > 100:
            issues.append(f"Extremely long function ({max_function_length} lines)")
        else:
            performance_score += 25
        
        if len(complex_functions) > 3:
            issues.append(f"Too many complex functions ({len(complex_functions)})")
        else:
            performance_score += 25
        
        if total_lines < 2000:
            performance_score += 25
        else:
            issues.append(f"Worker file too large ({total_lines} lines)")
        
        print(f"   Performance score: {performance_score}/100")
        
        if issues:
            print("   ❌ Performance issues found:")
            for issue in issues:
                print(f"      - {issue}")
            return False
        else:
            print("   ✅ Performance characteristics acceptable")
            return True
    
    except Exception as e:
        print(f"   ❌ Error analyzing worker performance: {e}")
        return False


def test_concurrent_service_usage():
    """Test concurrent usage of services for thread safety."""
    
    print("\n🔍 Testing concurrent service usage...")
    
    from src.services.elevenlabs_client import ElevenLabsClient
    from src.services.runway_client import RunwayClient
    
    results = []
    errors = []
    
    def worker_thread(thread_id, service_type):
        try:
            if service_type == 'elevenlabs':
                client = ElevenLabsClient(api_key="test_key")
                # Test basic operations
                result = client.validate_api_key()
                results.append((thread_id, service_type, 'success', result))
            
            elif service_type == 'runway':
                client = RunwayClient()
                # Test video generation
                job = client.generate_video("test prompt")
                status = client.get_generation_status(job['id'])
                results.append((thread_id, service_type, 'success', status['status']))
        
        except Exception as e:
            errors.append((thread_id, service_type, str(e)))
    
    # Start multiple threads
    threads = []
    for i in range(6):
        service_type = 'elevenlabs' if i % 2 == 0 else 'runway'
        thread = threading.Thread(target=worker_thread, args=(i, service_type))
        threads.append(thread)
        thread.start()
    
    # Wait for completion with timeout
    for thread in threads:
        thread.join(timeout=10)
    
    print(f"   Successful operations: {len(results)}")
    print(f"   Errors: {len(errors)}")
    
    if errors:
        print("   ❌ Concurrent usage errors:")
        for thread_id, service, error in errors:
            print(f"      Thread {thread_id} ({service}): {error}")
        return False
    else:
        print("   ✅ Concurrent usage handled correctly")
        return True


def test_memory_leak_simulation():
    """Simulate extended usage to detect memory leaks."""
    
    print("\n🔍 Testing for memory leaks...")
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    from src.services.runway_client import RunwayClient
    
    # Simulate extended usage
    client = RunwayClient()
    
    for i in range(20):
        # Generate job
        job = client.generate_video(f"test prompt {i}")
        
        # Check status
        status = client.get_generation_status(job['id'])
        
        # Download if available
        if status.get('video_url'):
            data = client.download_video(status['video_url'])
            del data  # Explicit cleanup
        
        # Check memory every 5 iterations
        if i % 5 == 0:
            current_memory = process.memory_info().rss
            growth = current_memory - initial_memory
            print(f"   Iteration {i}: Memory growth {growth / 1024 / 1024:.1f} MB")
    
    final_memory = process.memory_info().rss
    total_growth = final_memory - initial_memory
    
    print(f"   Total memory growth: {total_growth / 1024 / 1024:.1f} MB")
    
    # Memory growth should be reasonable for 20 operations
    if total_growth < 100 * 1024 * 1024:  # Less than 100MB
        print("   ✅ No significant memory leak detected")
        return True
    else:
        print(f"   ❌ Potential memory leak: {total_growth / 1024 / 1024:.1f} MB growth")
        return False


def main():
    """Run all performance tests."""
    
    print("⚡ PERFORMANCE AND RESOURCE TESTING")
    print("=" * 50)
    
    results = {
        'runway_resources': test_runway_resource_usage(),
        'worker_performance': test_video_worker_performance(),
        'concurrent_usage': test_concurrent_service_usage(),
        'memory_leaks': test_memory_leak_simulation()
    }
    
    print("\n📋 PERFORMANCE TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name}: PASSED")
        elif result is False:
            print(f"❌ {test_name}: FAILED")
        else:
            print(f"⚠️ {test_name}: SKIPPED")
    
    print(f"\n📊 RESULTS: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print(f"\n⚠️ Performance issues detected in {failed} areas")
        print("\n💡 RECOMMENDED OPTIMIZATIONS:")
        print("1. Reduce function complexity in video generation worker")
        print("2. Improve resource cleanup in service operations")
        print("3. Add timeout and resource limits to subprocess calls")
        print("4. Implement proper connection pooling for API clients")
        print("5. Add memory usage monitoring and cleanup")
        
        return 1
    else:
        print("\n✅ All performance tests passed!")
        return 0


if __name__ == "__main__":
    exit(main())