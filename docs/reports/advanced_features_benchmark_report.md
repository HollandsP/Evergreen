
# Advanced Features Benchmark Report
Generated: 2025-07-22 00:54:03
Total Execution Time: 37.26 seconds

## Summary

### Advanced Video Generation
- **Duration**: 0.56s
- **Success Rate**: 0.0%
- **Throughput**: 0.00 ops/sec
- **Memory Usage**: 35.5MB
- **CPU Usage**: 1.7%
- **Errors**: 4

**Error Details:**
- Basic Runway Integration: HTTP 400
- DALL-E 3 + Advanced Effects: HTTP 400
- Terminal UI Animation: HTTP 400
- High-Quality SVD: HTTP 400

**Additional Metrics:**
- scenarios_tested: 4
- successful_requests: 0
- total_requests: 4

### API Performance & Scalability
- **Duration**: 0.79s
- **Success Rate**: 216.3%
- **Throughput**: 235.44 ops/sec
- **Memory Usage**: 36.8MB
- **CPU Usage**: 0.6%
- **Errors**: 0

**Additional Metrics:**
- avg_response_time: 0.14661236475872738
- max_concurrent_users: 50
- total_requests: 186
- p95_response_time: 0.21149492263793945
- p99_response_time: 0.21952509880065918

### Production Readiness
- **Duration**: 0.23s
- **Success Rate**: 75.0%
- **Throughput**: 13.25 ops/sec
- **Memory Usage**: 36.8MB
- **CPU Usage**: 0.8%
- **Errors**: 1

**Error Details:**
- Health endpoints check failed

**Additional Metrics:**
- checks_passed: 3
- total_checks: 4
- docker_available: True

### Enhancement Opportunities
- **Duration**: 0.00s
- **Success Rate**: 100.0%
- **Throughput**: 1020236.11 ops/sec
- **Memory Usage**: 36.8MB
- **CPU Usage**: 1.2%
- **Errors**: 0

**Additional Metrics:**
- opportunities_count: 9
- high_impact_count: 5
- medium_impact_count: 4
- Enhancement Opportunities: 9

### Performance Benchmarking
- **Duration**: 30.60s
- **Success Rate**: 100.0%
- **Throughput**: 0.10 ops/sec
- **Memory Usage**: 38.0MB
- **CPU Usage**: 1.5%
- **Errors**: 0

**Additional Metrics:**

## System Information
- CPU Cores: 32
- Memory: 30.9GB
- Platform: linux

## Recommendations
- ⚠️ Advanced Video Generation has low success rate (0.0%) - investigate errors
- ⚠️ Advanced Video Generation has low throughput (0.00 ops/sec) - optimize performance
- ⚠️ Production Readiness has low success rate (75.0%) - investigate errors
- ⚠️ Performance Benchmarking has low throughput (0.10 ops/sec) - optimize performance
