"""
Test script for the /query/sse endpoint of the API.

This script demonstrates how to interact with the /query/sse endpoint that provides
real-time streaming responses using Server-Sent Events for query processing.

Usage:
    python test_query_sse.py
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/03/10
"""

import asyncio
import aiohttp
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:5001"
QUERY_SSE_ENDPOINT = f"{BASE_URL}/query/sse"

async def test_query_sse(query: str, thread_id: Optional[str] = None):
    """
    Test the /query/sse endpoint by sending a query and receiving streaming responses.
    
    Args:
        query: The user query to process
        thread_id: Optional thread ID for conversation continuity
        
    Returns:
        str: The thread ID from the response, or None if failed
    """
    payload = {
        "query": query,
        "thread_id": thread_id
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    print(f"🚀 Testing /query/sse endpoint with query: '{query}'")
    print(f"🧵 Thread ID: {thread_id if thread_id else 'New thread will be generated'}")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(QUERY_SSE_ENDPOINT, json=payload, headers=headers) as response:
                if response.status != 200:
                    print(f"❌ Error: HTTP {response.status}")
                    print(f"Response: {await response.text()}")
                    return None
                
                print("📡 Streaming response:")
                print("-" * 40)
                
                current_thread_id = None
                chunk_count = 0
                full_response = ""
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            
                            if data.get('type') == 'chunk':
                                chunk_count += 1
                                current_thread_id = data.get('thread_id')
                                chunk = data.get('chunk', {})
                                
                                # Extract content from chunk if available
                                if 'messages' in chunk and chunk['messages']:
                                    last_message = chunk['messages'][-1]
                                    if hasattr(last_message, 'content'):
                                        content = last_message.content
                                    elif isinstance(last_message, dict) and 'content' in last_message:
                                        content = last_message['content']
                                    else:
                                        content = str(last_message)
                                    
                                    print(f"📝 Chunk {chunk_count}: {content}")
                                    full_response += content
                                else:
                                    print(f"📦 Chunk {chunk_count}: {json.dumps(chunk, indent=2)}")
                            
                            elif data.get('type') == 'complete':
                                print("\n✅ Stream completed successfully!")
                                break
                            
                            elif data.get('type') == 'error':
                                print(f"\n❌ Stream error: {data.get('error')}")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Failed to parse JSON: {line}")
                            continue
                
                print("=" * 60)
                print(f"📊 Summary:")
                print(f"  - Total chunks received: {chunk_count}")
                print(f"  - Final thread ID: {current_thread_id}")
                print(f"  - Full response length: {len(full_response)} characters")
                
                return current_thread_id
                
    except aiohttp.ClientError as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

async def test_query_stream_steps_sse(query: str, thread_id: Optional[str] = None):
    """Test the /query/stream_steps/sse endpoint."""
    endpoint = f"{BASE_URL}/query/stream_steps/sse"
    payload = {
        "query": query,
        "thread_id": thread_id
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    print(f"🚀 Testing /query/stream_steps/sse endpoint with query: '{query}'")
    print(f"🧵 Thread ID: {thread_id if thread_id else 'New thread will be generated'}")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers) as response:
                if response.status != 200:
                    print(f"❌ Error: HTTP {response.status}")
                    print(f"Response: {await response.text()}")
                    return None
                
                print("📡 Streaming intermediate steps:")
                print("-" * 40)
                
                current_thread_id = None
                step_count = 0
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            
                            if data.get('type') == 'step':
                                step_count += 1
                                current_thread_id = data.get('thread_id')
                                step = data.get('step', {})
                                
                                print(f"\n🔄 Step {step_count}:")
                                print(f"  Type: {step.get('message_type', 'unknown')}")
                                if step.get('content'):
                                    print(f"  Content: {step['content'][:100]}..." if len(step['content']) > 100 else f"  Content: {step['content']}")
                                if step.get('tool_calls'):
                                    print(f"  Tool calls: {len(step['tool_calls'])}")
                                    for i, tool in enumerate(step['tool_calls'], 1):
                                        print(f"    {i}. {tool.get('name', 'unknown')}")
                                if step.get('artifact'):
                                    print(f"  Artifact: {step['artifact'][:100]}..." if len(step['artifact']) > 100 else f"  Artifact: {step['artifact']}")
                            
                            elif data.get('type') == 'complete':
                                print("\n✅ Stream completed successfully!")
                                break
                            
                            elif data.get('type') == 'error':
                                print(f"\n❌ Stream error: {data.get('error')}")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Failed to parse JSON: {line}")
                            continue
                
                print("=" * 60)
                print(f"📊 Summary:")
                print(f"  - Total steps received: {step_count}")
                print(f"  - Final thread ID: {current_thread_id}")
                
                return current_thread_id
                
    except aiohttp.ClientError as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

async def main():
    """Main function to run the /query/sse endpoint tests."""
    
    print("🧪 PAKTON API SSE Endpoints Test Suite")
    print("=" * 60)
    
    # Test /query/sse endpoint
    print("\n" + "=" * 60)
    print("TESTING /query/sse ENDPOINT")
    print("=" * 60)
    
    # Test 1: Simple query without thread ID
    print("\n🔍 Test 1: Simple query (new thread)")
    query1 = "Ok, what can you do for me? Give me an overview."
    thread_id = await test_query_sse(query1)
    
    # Test 2: Follow-up query with the same thread ID
    if thread_id:
        print(f"\n🔍 Test 2: Follow-up query (existing thread: {thread_id})")
        query2 = "Can you provide more details about your capabilities?"
        await test_query_sse(query2, thread_id)
    
    # Test /query/stream_steps/sse endpoint
    print("\n" + "=" * 60)
    print("TESTING /query/stream_steps/sse ENDPOINT")
    print("=" * 60)
    
    # Test 3: Stream steps with new thread
    print("\n🔍 Test 3: Stream steps query (new thread)")
    query3 = "What is the weather like today?"
    thread_id_steps = await test_query_stream_steps_sse(query3)
    
    # Test 4: Stream steps with existing thread
    if thread_id_steps:
        print(f"\n🔍 Test 4: Stream steps follow-up (existing thread: {thread_id_steps})")
        query4 = "Can you tell me more about that?"
        await test_query_stream_steps_sse(query4, thread_id_steps)
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
