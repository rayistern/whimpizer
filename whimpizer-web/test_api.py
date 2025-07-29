#!/usr/bin/env python3
"""
Simple test script for Whimpizer Web API
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_providers():
    """Test providers endpoint"""
    print("\n🤖 Testing providers endpoint...")
    response = requests.get(f"{API_BASE}/api/providers")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        providers = response.json()
        print(f"Found {len(providers)} providers:")
        for provider in providers:
            print(f"  - {provider['display_name']}: {provider['models']}")
    return response.status_code == 200

def test_job_submission():
    """Test job submission"""
    print("\n📝 Testing job submission...")
    
    job_data = {
        "urls": ["https://example.com", "https://httpbin.org/html"],
        "config": {
            "ai_provider": "openai",
            "ai_model": "gpt-4",
            "pdf_style": "handwritten",
            "temperature": 0.7
        }
    }
    
    response = requests.post(
        f"{API_BASE}/api/jobs", 
        json=job_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Job ID: {result['job_id']}")
        print(f"Status: {result['status']}")
        print(f"Status URL: {result['status_url']}")
        return result['job_id']
    else:
        print(f"Error: {response.text}")
        return None

def test_job_status(job_id):
    """Test job status checking"""
    print(f"\n📊 Testing job status for {job_id}...")
    
    for i in range(3):
        response = requests.get(f"{API_BASE}/api/jobs/{job_id}/status")
        print(f"Status check {i+1}: {response.status_code}")
        
        if response.status_code == 200:
            job_info = response.json()
            print(f"  Status: {job_info['status']}")
            print(f"  Progress: {job_info['progress']}%")
            print(f"  Message: {job_info['message']}")
            
            if job_info['status'] in ['completed', 'failed']:
                break
                
        time.sleep(2)

def test_job_list():
    """Test job listing"""
    print("\n📋 Testing job listing...")
    response = requests.get(f"{API_BASE}/api/jobs")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total jobs: {result['total']}")
        print(f"Jobs on page: {len(result['jobs'])}")
        
        for job in result['jobs'][:3]:  # Show first 3 jobs
            print(f"  - {job['id']}: {job['status']} ({job['progress']}%)")

def main():
    """Run all tests"""
    print("🧪 Whimpizer Web API Tests\n")
    
    # Test 1: Health check
    if not test_health():
        print("❌ Health check failed - is the server running?")
        return
    
    # Test 2: Providers
    if not test_providers():
        print("❌ Providers endpoint failed")
        return
    
    # Test 3: Job submission
    job_id = test_job_submission()
    if not job_id:
        print("❌ Job submission failed")
        return
    
    # Test 4: Job status
    test_job_status(job_id)
    
    # Test 5: Job listing
    test_job_list()
    
    print("\n✅ All tests completed!")
    print("\n📝 Next steps:")
    print("1. Check the API docs: http://localhost:8000/api/docs")
    print("2. Monitor job processing in Docker logs: docker-compose logs -f backend")
    print("3. Add your AI API key to .env for actual processing")

if __name__ == "__main__":
    main()