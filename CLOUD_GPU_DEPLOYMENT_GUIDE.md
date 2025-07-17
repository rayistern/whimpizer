# Cloud GPU Deployment Guide
## Offloading CSM Processing to Pay-on-Demand GPU Services

This guide shows you how to deploy CSM (Conversational Speech Model) to cloud GPU services for dramatically faster and more cost-effective audiobook generation.

## 🎯 **Why Cloud GPU?**

### **Cost Comparison** (1000-word audiobook)
- **Local CPU**: 15-20 minutes generation time
- **RunPod A100**: 1-2 minutes @ $0.02-0.04 total cost
- **Thunder Compute A100**: 1-2 minutes @ $0.01-0.02 total cost

### **Benefits**
- ⚡ **10-20x faster** generation with GPU acceleration
- 💰 **Lower cost** for occasional use (pay only when generating)
- 🔧 **No local setup** required - works on any machine
- 📈 **Unlimited scale** - generate multiple audiobooks in parallel

---

## 🥇 **Recommended Providers**

### **#1. RunPod (Best Overall)**
- **Cost**: A100 80GB @ $1.19/hour (pay-per-second)
- **Best For**: Production audiobook generation
- **Pros**: Custom containers, API endpoints, fast cold starts
- **Setup Time**: 30 minutes

### **#2. Thunder Compute (Cheapest)**
- **Cost**: A100 40GB @ $0.66/hour 
- **Best For**: Development and testing
- **Pros**: VSCode integration, lowest cost
- **Setup Time**: 15 minutes

### **#3. Modal (Easiest)**
- **Cost**: ~$2-3/hour for A100
- **Best For**: Serverless deployment
- **Pros**: Python-native, zero cold starts
- **Setup Time**: 20 minutes

---

## 🚀 **Quick Start: RunPod Deployment**

### **Step 1: Setup RunPod Account**

```bash
# 1. Sign up at runpod.io
# 2. Add credit ($10 minimum)
# 3. Get API key from Account settings
```

### **Step 2: Deploy CSM Container**

```bash
# Clone deployment files
git clone <your-repo>
cd cloud_deployment/runpod/

# Build and push container (or use pre-built)
docker build -t your-username/csm-runpod .
docker push your-username/csm-runpod

# Or use our pre-built container:
# docker.io/whimperizer/csm-runpod:latest
```

### **Step 3: Create RunPod Endpoint**

1. Go to **RunPod Console → Serverless**
2. Click **New Endpoint**
3. Configure:
   - **Name**: csm-audiobook-generator
   - **Container Image**: `your-username/csm-runpod:latest`
   - **GPU**: A100 80GB (recommended) or A100 40GB
   - **Container Disk**: 10GB
   - **Max Workers**: 3-5 (for parallel processing)

4. **Advanced Settings**:
   ```json
   {
     "env": {
       "HF_HOME": "/tmp/huggingface",
       "NO_TORCH_COMPILE": "1"
     }
   }
   ```

5. Click **Deploy**

### **Step 4: Configure Whimperizer**

Add to `config/audio_config.yaml`:

```yaml
audio:
  enabled: true
  cloud_gpu:
    enabled: true
    provider: "runpod"
    api_key: "your-runpod-api-key"
    endpoint_url: "https://api.runpod.ai/v2/your-endpoint-id/run"
    fallback_to_local: true  # Use local if cloud fails
```

### **Step 5: Test & Generate**

```bash
# Test cloud GPU connection
python src/test_cloud_gpu.py

# Generate audiobook with cloud GPU
python src/pipeline.py --urls urls.csv --groups your-group --audio-only
```

---

## 🔧 **Detailed Provider Setup**

### **RunPod Setup (Recommended)**

#### **Container Deployment**
```bash
# Build container
cd cloud_deployment/runpod/
docker build -t csm-runpod:latest .

# Test locally (optional)
docker run --gpus all -p 8000:8000 csm-runpod:latest

# Push to registry
docker tag csm-runpod:latest your-username/csm-runpod:latest
docker push your-username/csm-runpod:latest
```

#### **Endpoint Configuration**
- **GPU Type**: A100 80GB (best performance) or A100 40GB (cheaper)
- **Max Workers**: 3-5 (allows parallel processing)
- **Container Disk**: 10GB (for model caching)
- **Timeout**: 300 seconds (5 minutes)

#### **Cost Optimization**
- **Pay-per-second**: Only charged when actively generating
- **Auto-scaling**: Spins down when not in use
- **Batch processing**: Process multiple segments together

### **Thunder Compute Setup (Cheapest)**

```bash
# 1. Sign up at thundercompute.com
# 2. Create API key
# 3. Deploy VM with CSM
```

**Configuration**:
```yaml
cloud_gpu:
  provider: "thunder"
  api_key: "your-thunder-api-key"
  endpoint_url: "your-vm-endpoint"
  instance_type: "A100_40GB"
```

### **Modal Setup (Serverless)**

```python
# modal_csm.py
import modal

app = modal.App("csm-audiobook")

@app.function(
    image=modal.Image.debian_slim().pip_install([
        "torch", "torchaudio", "transformers", "soundfile"
    ]),
    gpu="A100",
    timeout=300
)
def generate_speech(text: str, speaker: int = 0):
    # CSM generation code here
    pass

# Deploy: modal deploy modal_csm.py
```

---

## 🔄 **Pipeline Integration**

### **Updated Audio Configuration**

```yaml
# config/audio_config.yaml
audio:
  enabled: true
  
  # Cloud GPU settings
  cloud_gpu:
    enabled: true
    provider: "runpod"  # or "thunder", "modal"
    api_key: "${RUNPOD_API_KEY}"  # Environment variable
    endpoint_url: "https://api.runpod.ai/v2/your-endpoint/run"
    
    # Fallback settings
    fallback_to_local: true
    max_retries: 3
    timeout_seconds: 300
    
    # Performance settings
    batch_size: 5  # Process multiple segments together
    parallel_workers: 3  # Concurrent requests
```

### **Environment Variables**

```bash
# .env file
RUNPOD_API_KEY=your-api-key-here
THUNDER_API_KEY=your-thunder-key
MODAL_API_KEY=your-modal-key

# Optional: Provider priority
CLOUD_GPU_PROVIDERS=runpod,thunder,modal
```

### **Updated Pipeline Usage**

```bash
# Force cloud GPU
python src/pipeline.py --urls urls.csv --groups group1 --cloud-gpu

# Cloud GPU with fallback
python src/pipeline.py --urls urls.csv --groups group1 --audio-only

# Local only (disable cloud)
python src/pipeline.py --urls urls.csv --groups group1 --local-audio
```

---

## 📊 **Cost Analysis**

### **Real-World Examples**

| Content Type | Words | Local CPU | RunPod A100 | Thunder A100 | Modal A100 |
|--------------|-------|-----------|-------------|--------------|------------|
| Short story  | 500   | 8 min     | 30 sec ($0.01) | 30 sec ($0.005) | 30 sec ($0.02) |
| Medium story | 2000  | 30 min    | 2 min ($0.04)  | 2 min ($0.02)   | 2 min ($0.08)  |
| Full book    | 10000 | 2.5 hours | 8 min ($0.16)  | 8 min ($0.09)   | 8 min ($0.33)  |

### **Break-Even Analysis**
- **Occasional use** (< 10 books/month): Cloud GPU wins
- **Heavy use** (> 50 books/month): Consider dedicated GPU
- **Development/testing**: Cloud GPU ideal

---

## 🔧 **Advanced Configuration**

### **Multi-Provider Fallback**

```python
# Automatic provider switching
providers = [
    create_runpod_config(api_key, endpoint_url),
    create_thunder_config(api_key, endpoint_url),
    create_modal_config(api_key, function_url)
]

cloud_manager = CloudGPUManager(providers)
audio = cloud_manager.generate_speech(text, speaker)
```

### **Performance Optimization**

```yaml
# Batch processing for efficiency
cloud_gpu:
  batch_processing:
    enabled: true
    max_batch_size: 10
    timeout_per_batch: 60
    
  # Caching for repeated content
  caching:
    enabled: true
    cache_duration_hours: 24
    
  # Parallel processing
  parallel:
    max_workers: 5
    queue_size: 20
```

### **Monitoring & Logging**

```yaml
# Enhanced logging for cloud operations
logging:
  cloud_gpu:
    enabled: true
    log_requests: true
    log_timing: true
    log_costs: true
    
  # Metrics collection
  metrics:
    provider_performance: true
    cost_tracking: true
    error_rates: true
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **1. Container Won't Start**
```bash
# Check logs
runpod logs your-endpoint-id

# Common fixes:
# - Increase container disk to 15GB
# - Check Docker image exists
# - Verify environment variables
```

#### **2. Model Loading Fails**
```bash
# Pre-cache model in container
RUN python -c "
from transformers import AutoProcessor, CsmForConditionalGeneration
AutoProcessor.from_pretrained('sesame/csm-1b')
CsmForConditionalGeneration.from_pretrained('sesame/csm-1b')
"
```

#### **3. Timeout Errors**
```yaml
# Increase timeouts
cloud_gpu:
  timeout_seconds: 600  # 10 minutes
  
# Or use streaming for long content
processing:
  streaming: true
  chunk_size: 1000  # characters
```

#### **4. High Costs**
```bash
# Monitor usage
runpod billing usage

# Optimize:
# - Use smaller GPU for testing
# - Enable auto-shutdown
# - Batch multiple requests
```

### **Performance Tuning**

```python
# Container optimization
dockerfile_additions = """
# Pre-compile models
RUN python -c "import torch; torch.jit.script(model)"

# Optimize memory
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Enable optimizations
ENV TORCH_CUDNN_V8_API_ENABLED=1
"""
```

---

## 📈 **Scaling for Production**

### **High-Volume Processing**

```yaml
# Production configuration
cloud_gpu:
  provider: "runpod"
  
  # Multi-region deployment
  regions: ["us-east-1", "us-west-2", "eu-west-1"]
  
  # Auto-scaling
  scaling:
    min_workers: 1
    max_workers: 10
    target_utilization: 70
    
  # Load balancing
  load_balancing:
    strategy: "round_robin"  # or "least_latency"
    health_checks: true
```

### **Enterprise Features**

```python
# Custom model deployment
class EnterpriseCSMClient(CloudGPUClient):
    def __init__(self, config):
        super().__init__(config)
        self.custom_voices = self.load_custom_voices()
        
    def generate_with_custom_voice(self, text, voice_id):
        # Custom voice implementation
        pass
```

---

## 💡 **Best Practices**

### **Cost Optimization**
1. **Batch requests** when possible
2. **Use smaller GPUs** for development
3. **Enable auto-shutdown** on idle
4. **Monitor usage** regularly
5. **Cache common generations**

### **Performance**
1. **Pre-load models** in containers
2. **Use appropriate GPU sizes**
3. **Enable parallel processing**
4. **Optimize text chunking**
5. **Monitor latency metrics**

### **Reliability**
1. **Configure multiple providers**
2. **Enable local fallback**
3. **Set appropriate timeouts**
4. **Monitor error rates**
5. **Implement retry logic**

---

## 🎉 **Next Steps**

1. **Choose provider** based on your needs
2. **Deploy test endpoint** with sample content
3. **Benchmark performance** vs local generation
4. **Configure production** settings
5. **Monitor and optimize** costs

Your Whimperizer can now leverage cloud GPUs for lightning-fast, cost-effective audiobook generation! 🚀

---

*For support, check the troubleshooting section or open an issue on GitHub.*