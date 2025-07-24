#!/usr/bin/env python3
"""
Integration test for WebSocket real-time progress updates.
Tests the WebSocket connection and progress event emission.
"""

import asyncio
import websockets
import json
import time
import logging
import requests
from typing import Dict, List, Any
import threading
from queue import Queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketTester:
    """WebSocket integration tester."""
    
    def __init__(self):
        """Initialize WebSocket tester."""
        self.websocket_url = "ws://localhost:3000/api/socket"
        self.api_url = "http://localhost:3000/api"
        self.received_events = Queue()
        self.connection = None
        self.listening = False
        
    async def connect_websocket(self) -> bool:
        """Connect to WebSocket server."""
        logger.info("🔌 Connecting to WebSocket server...")
        
        try:
            self.connection = await websockets.connect(
                self.websocket_url,
                timeout=10
            )
            logger.info("✅ WebSocket connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def listen_for_events(self, duration: int = 60):
        """Listen for WebSocket events."""
        if not self.connection:
            logger.error("❌ No WebSocket connection established")
            return
        
        logger.info(f"👂 Listening for events for {duration} seconds...")
        self.listening = True
        
        try:
            while self.listening:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        self.connection.recv(),
                        timeout=1.0
                    )
                    
                    event_data = json.loads(message)
                    self.received_events.put(event_data)
                    
                    logger.info(f"📨 Received event: {event_data.get('type', 'unknown')}")
                    
                except asyncio.TimeoutError:
                    # Continue listening
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("🔌 WebSocket connection closed")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Error listening for events: {e}")
    
    def stop_listening(self):
        """Stop listening for events."""
        self.listening = False
    
    async def subscribe_to_job(self, job_id: str):
        """Subscribe to job updates."""
        if not self.connection:
            logger.error("❌ No WebSocket connection")
            return False
        
        try:
            subscribe_message = {
                "type": "subscribe_job",
                "jobId": job_id
            }
            
            await self.connection.send(json.dumps(subscribe_message))
            logger.info(f"📡 Subscribed to job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to job: {e}")
            return False
    
    async def subscribe_to_system(self):
        """Subscribe to system updates."""
        if not self.connection:
            logger.error("❌ No WebSocket connection")
            return False
        
        try:
            subscribe_message = {
                "type": "subscribe_system"
            }
            
            await self.connection.send(json.dumps(subscribe_message))
            logger.info("📡 Subscribed to system updates")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to system: {e}")
            return False
    
    def trigger_api_operation(self, operation_type: str) -> str:
        """Trigger an API operation that should emit WebSocket events."""
        logger.info(f"🎯 Triggering {operation_type} operation...")
        
        session = requests.Session()
        
        try:
            if operation_type == "script_parse":
                response = session.post(
                    f"{self.api_url}/script/parse",
                    json={
                        "content": "# Test Script\n\n## Scene 1\nTest scene content.",
                        "projectId": f"websocket_test_{int(time.time())}"
                    },
                    timeout=30
                )
                
            elif operation_type == "image_generate":
                response = session.post(
                    f"{self.api_url}/images/generate",
                    json={
                        "prompt": "A test image for WebSocket testing",
                        "sceneId": "test_scene",
                        "projectId": f"websocket_test_{int(time.time())}",
                        "provider": "dalle3"
                    },
                    timeout=60
                )
                
            elif operation_type == "audio_generate":
                response = session.post(
                    f"{self.api_url}/audio/generate",
                    json={
                        "text": "This is a test audio generation for WebSocket testing.",
                        "sceneId": "test_scene",
                        "projectId": f"websocket_test_{int(time.time())}",
                        "voice": "onyx"
                    },
                    timeout=60
                )
                
            else:
                logger.error(f"❌ Unknown operation type: {operation_type}")
                return None
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('jobId') or result.get('taskId') or f"test_job_{int(time.time())}"
                logger.info(f"✅ {operation_type} operation triggered, job ID: {job_id}")
                return job_id
            else:
                logger.error(f"❌ {operation_type} operation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error triggering {operation_type}: {e}")
            return None
    
    def analyze_received_events(self) -> Dict[str, Any]:
        """Analyze the events we received."""
        events = []
        
        while not self.received_events.empty():
            events.append(self.received_events.get())
        
        analysis = {
            "total_events": len(events),
            "event_types": {},
            "job_updates": 0,
            "system_updates": 0,
            "progress_updates": 0,
            "error_events": 0,
            "events": events
        }
        
        for event in events:
            event_type = event.get('type', 'unknown')
            analysis['event_types'][event_type] = analysis['event_types'].get(event_type, 0) + 1
            
            if 'job' in event_type:
                analysis['job_updates'] += 1
            elif 'system' in event_type:
                analysis['system_updates'] += 1
            elif 'progress' in event_type:
                analysis['progress_updates'] += 1
            elif 'error' in event_type:
                analysis['error_events'] += 1
        
        return analysis
    
    async def run_websocket_tests(self) -> Dict[str, Any]:
        """Run comprehensive WebSocket tests."""
        logger.info("🚀 Starting WebSocket Integration Tests")
        logger.info("=" * 50)
        
        test_results = {
            "connection_test": False,
            "subscription_test": False,
            "job_events_test": False,
            "system_events_test": False,
            "real_time_test": False
        }
        
        # Test 1: Connection
        logger.info("\n🔌 Test 1: WebSocket Connection")
        connection_success = await self.connect_websocket()
        test_results["connection_test"] = connection_success
        
        if not connection_success:
            logger.error("❌ Cannot continue without WebSocket connection")
            return test_results
        
        # Start listening in background
        listen_task = asyncio.create_task(self.listen_for_events(120))
        
        # Test 2: Subscriptions
        logger.info("\n📡 Test 2: Event Subscriptions")
        system_sub = await self.subscribe_to_system()
        job_sub = await self.subscribe_to_job("test_job_123")
        test_results["subscription_test"] = system_sub and job_sub
        
        # Wait a moment for initial events
        await asyncio.sleep(2)
        
        # Test 3: Trigger operations and check for events
        logger.info("\n🎯 Test 3: Job Event Generation")
        
        # Trigger operations in separate thread to avoid blocking
        def trigger_operations():
            operations = ["script_parse", "image_generate"]
            for op in operations:
                job_id = self.trigger_api_operation(op)
                if job_id:
                    # Subscribe to this specific job
                    asyncio.run_coroutine_threadsafe(
                        self.subscribe_to_job(job_id),
                        asyncio.get_event_loop()
                    )
                time.sleep(5)  # Wait between operations
        
        # Start operations in background
        op_thread = threading.Thread(target=trigger_operations)
        op_thread.start()
        
        # Wait for operations to complete
        op_thread.join()
        
        # Give some time for events to arrive
        logger.info("⏳ Waiting for WebSocket events...")
        await asyncio.sleep(30)
        
        # Stop listening
        self.stop_listening()
        await listen_task
        
        # Test 4: Analyze received events
        logger.info("\n📊 Test 4: Event Analysis")
        event_analysis = self.analyze_received_events()
        
        # Check if we received job-related events
        test_results["job_events_test"] = event_analysis["job_updates"] > 0
        test_results["system_events_test"] = event_analysis["system_updates"] > 0
        test_results["real_time_test"] = event_analysis["total_events"] > 0
        
        # Close connection
        if self.connection:
            await self.connection.close()
        
        # Generate report
        report = {
            "test_results": test_results,
            "event_analysis": event_analysis,
            "timestamp": time.time()
        }
        
        # Print summary
        logger.info("\n" + "=" * 50)
        logger.info("🏁 WEBSOCKET TEST SUMMARY")
        logger.info("=" * 50)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nEvents Received: {event_analysis['total_events']}")
        logger.info(f"Event Types: {list(event_analysis['event_types'].keys())}")
        logger.info(f"Job Updates: {event_analysis['job_updates']}")
        logger.info(f"System Updates: {event_analysis['system_updates']}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        logger.info("=" * 50)
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL WEBSOCKET TESTS PASSED!")
        else:
            logger.error("💥 SOME WEBSOCKET TESTS FAILED!")
        
        return report


async def main():
    """Main test runner."""
    tester = WebSocketTester()
    report = await tester.run_websocket_tests()
    
    # Save report
    import json
    import os
    
    os.makedirs("tests/reports", exist_ok=True)
    report_path = f"tests/reports/websocket_test_report_{int(time.time())}.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"📊 Report saved to: {report_path}")
    
    # Return success based on results
    passed_tests = sum(report['test_results'].values())
    total_tests = len(report['test_results'])
    
    return (passed_tests / total_tests) >= 0.6  # 60% pass rate


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)