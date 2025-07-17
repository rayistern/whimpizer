#!/usr/bin/env python3
"""
Cloud GPU Test Script

Test cloud GPU connectivity and functionality for CSM audio generation.
Validates provider configurations and measures performance.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from audio.cloud_gpu_client import (
    CloudGPUClient, CloudGPUManager, CloudGPUConfig,
    create_runpod_config, create_modal_config, create_thunder_config
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_provider_config(provider_name: str, config: CloudGPUConfig) -> dict:
    """Test a single provider configuration"""
    print(f"\n🧪 Testing {provider_name.upper()} Configuration")
    print("=" * 50)
    
    try:
        # Initialize client
        client = CloudGPUClient(config)
        print(f"✅ Client initialized successfully")
        
        # Test text
        test_text = "Hello, this is a test of the cloud GPU audio generation system."
        
        print(f"📝 Test text: '{test_text}'")
        print(f"⏱️  Starting generation...")
        
        # Measure generation time
        start_time = time.time()
        
        try:
            audio_tensor = client.generate_speech(
                text=test_text,
                speaker=0,  # Narrator voice
                max_length_ms=5000
            )
            
            generation_time = time.time() - start_time
            
            print(f"✅ Generation successful!")
            print(f"   Duration: {generation_time:.2f} seconds")
            print(f"   Audio shape: {audio_tensor.shape}")
            print(f"   Audio length: {audio_tensor.shape[-1] / 24000:.2f} seconds")
            
            # Cost estimation
            cost_info = client.estimate_cost(len(test_text), generation_time)
            print(f"   Estimated cost: ${cost_info['estimated_cost_usd']:.4f}")
            
            return {
                "success": True,
                "generation_time": generation_time,
                "audio_shape": list(audio_tensor.shape),
                "cost_estimate": cost_info['estimated_cost_usd'],
                "provider_info": client.get_provider_info()
            }
            
        except Exception as e:
            print(f"❌ Generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider_info": client.get_provider_info()
            }
            
    except Exception as e:
        print(f"❌ Client initialization failed: {str(e)}")
        return {
            "success": False,
            "error": f"Initialization failed: {str(e)}"
        }


def test_fallback_system(configs: list) -> dict:
    """Test multi-provider fallback system"""
    print(f"\n🔄 Testing Multi-Provider Fallback System")
    print("=" * 50)
    
    try:
        manager = CloudGPUManager(configs)
        
        test_text = "Testing the fallback system with multiple providers."
        
        print(f"📝 Test text: '{test_text}'")
        print(f"🔀 Available providers: {[c.provider for c in configs]}")
        
        start_time = time.time()
        audio_tensor = manager.generate_speech(
            text=test_text,
            speaker=1,  # Greg voice
            max_length_ms=5000
        )
        generation_time = time.time() - start_time
        
        active_provider = manager.get_current_provider()
        
        print(f"✅ Fallback system successful!")
        print(f"   Active provider: {active_provider}")
        print(f"   Generation time: {generation_time:.2f} seconds")
        print(f"   Audio shape: {audio_tensor.shape}")
        
        return {
            "success": True,
            "active_provider": active_provider,
            "generation_time": generation_time,
            "audio_shape": list(audio_tensor.shape)
        }
        
    except Exception as e:
        print(f"❌ Fallback system failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def load_config_from_env() -> list:
    """Load cloud GPU configurations from environment variables"""
    configs = []
    
    # RunPod configuration
    runpod_api_key = os.getenv('RUNPOD_API_KEY')
    runpod_endpoint = os.getenv('RUNPOD_ENDPOINT_URL')
    
    if runpod_api_key and runpod_endpoint:
        configs.append(create_runpod_config(runpod_api_key, runpod_endpoint))
        print(f"✅ RunPod configuration loaded")
    else:
        print(f"⚠️  RunPod configuration missing (RUNPOD_API_KEY or RUNPOD_ENDPOINT_URL)")
    
    # Thunder Compute configuration
    thunder_api_key = os.getenv('THUNDER_API_KEY')
    thunder_endpoint = os.getenv('THUNDER_ENDPOINT_URL')
    
    if thunder_api_key and thunder_endpoint:
        configs.append(create_thunder_config(thunder_api_key, thunder_endpoint))
        print(f"✅ Thunder Compute configuration loaded")
    else:
        print(f"⚠️  Thunder Compute configuration missing (THUNDER_API_KEY or THUNDER_ENDPOINT_URL)")
    
    # Modal configuration
    modal_api_key = os.getenv('MODAL_API_KEY')
    modal_function_url = os.getenv('MODAL_FUNCTION_URL')
    
    if modal_api_key and modal_function_url:
        configs.append(create_modal_config(modal_api_key, modal_function_url))
        print(f"✅ Modal configuration loaded")
    else:
        print(f"⚠️  Modal configuration missing (MODAL_API_KEY or MODAL_FUNCTION_URL)")
    
    return configs


def performance_benchmark(configs: list) -> dict:
    """Run performance benchmark across providers"""
    print(f"\n🏎️  Performance Benchmark")
    print("=" * 50)
    
    benchmark_texts = [
        "Short test sentence.",
        "This is a medium length test sentence for audio generation benchmarking.",
        "This is a longer test sentence that contains more words and should take more time to generate, allowing us to measure the performance characteristics of different cloud GPU providers."
    ]
    
    results = {}
    
    for config in configs:
        provider_name = config.provider
        print(f"\n📊 Benchmarking {provider_name.upper()}")
        
        provider_results = {
            "provider": provider_name,
            "tests": [],
            "avg_generation_time": 0,
            "total_cost": 0
        }
        
        try:
            client = CloudGPUClient(config)
            
            for i, text in enumerate(benchmark_texts):
                print(f"   Test {i+1}: {len(text)} characters")
                
                start_time = time.time()
                audio = client.generate_speech(text, speaker=0)
                generation_time = time.time() - start_time
                
                cost_info = client.estimate_cost(len(text), generation_time)
                
                test_result = {
                    "text_length": len(text),
                    "generation_time": generation_time,
                    "cost": cost_info['estimated_cost_usd'],
                    "audio_duration": audio.shape[-1] / 24000
                }
                
                provider_results["tests"].append(test_result)
                provider_results["total_cost"] += test_result["cost"]
                
                print(f"      Time: {generation_time:.2f}s, Cost: ${test_result['cost']:.4f}")
            
            # Calculate averages
            provider_results["avg_generation_time"] = sum(t["generation_time"] for t in provider_results["tests"]) / len(provider_results["tests"])
            
            results[provider_name] = provider_results
            
        except Exception as e:
            print(f"   ❌ Benchmark failed: {str(e)}")
            results[provider_name] = {"error": str(e)}
    
    return results


def print_summary_report(results: dict):
    """Print a summary report of all tests"""
    print(f"\n📊 CLOUD GPU TEST SUMMARY REPORT")
    print("=" * 60)
    
    successful_providers = []
    failed_providers = []
    
    for provider, result in results.items():
        if result.get("success", False):
            successful_providers.append(provider)
        else:
            failed_providers.append(provider)
    
    print(f"✅ Successful providers: {len(successful_providers)}")
    for provider in successful_providers:
        print(f"   - {provider.upper()}")
    
    print(f"\n❌ Failed providers: {len(failed_providers)}")
    for provider in failed_providers:
        print(f"   - {provider.upper()}: {results[provider].get('error', 'Unknown error')}")
    
    # Cost comparison
    print(f"\n💰 Cost Comparison (for standard test):")
    for provider in successful_providers:
        if provider in results and "cost_estimate" in results[provider]:
            cost = results[provider]["cost_estimate"]
            print(f"   {provider.upper()}: ${cost:.4f}")
    
    # Performance comparison
    print(f"\n⏱️  Performance Comparison:")
    for provider in successful_providers:
        if provider in results and "generation_time" in results[provider]:
            time_taken = results[provider]["generation_time"]
            print(f"   {provider.upper()}: {time_taken:.2f} seconds")
    
    print(f"\n🎯 Recommendations:")
    if len(successful_providers) > 0:
        print(f"   - Primary provider: Use {successful_providers[0].upper()}")
        if len(successful_providers) > 1:
            print(f"   - Fallback providers: {', '.join(p.upper() for p in successful_providers[1:])}")
        print(f"   - Enable fallback_to_local: true for reliability")
    else:
        print(f"   - No cloud providers working - use local generation only")
        print(f"   - Check API keys and endpoint URLs")
        print(f"   - Verify network connectivity")


def main():
    """Main test function"""
    print("🚀 Cloud GPU Test Suite for CSM Audio Generation")
    print("=" * 60)
    
    # Load configurations
    print("\n📋 Loading Configuration")
    configs = load_config_from_env()
    
    if not configs:
        print("\n❌ No valid configurations found!")
        print("   Please set environment variables for at least one provider:")
        print("   - RunPod: RUNPOD_API_KEY, RUNPOD_ENDPOINT_URL")
        print("   - Thunder: THUNDER_API_KEY, THUNDER_ENDPOINT_URL") 
        print("   - Modal: MODAL_API_KEY, MODAL_FUNCTION_URL")
        return False
    
    print(f"   Found {len(configs)} valid configuration(s)")
    
    # Test individual providers
    individual_results = {}
    for config in configs:
        result = test_provider_config(config.provider, config)
        individual_results[config.provider] = result
    
    # Test fallback system (if multiple providers)
    fallback_result = None
    if len(configs) > 1:
        fallback_result = test_fallback_system(configs)
    
    # Run performance benchmark
    benchmark_results = performance_benchmark(configs)
    
    # Print summary report
    print_summary_report(individual_results)
    
    # Save detailed results
    import json
    results_file = "cloud_gpu_test_results.json"
    detailed_results = {
        "individual_tests": individual_results,
        "fallback_test": fallback_result,
        "benchmark_results": benchmark_results,
        "timestamp": time.time()
    }
    
    with open(results_file, 'w') as f:
        json.dump(detailed_results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    # Return success if at least one provider works
    return any(result.get("success", False) for result in individual_results.values())


if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        print(f"\n{'✅ Tests completed successfully!' if success else '❌ Tests failed!'}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite crashed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)