# DR-Tulu Modal Deployment

Deploy the full DR-Tulu research agent on Modal with scale-to-zero pricing.

## Cost Estimate

| Usage | Monthly Cost |
|-------|--------------|
| Light (100 queries) | ~$5-10 |
| Medium (300 queries) | ~$15-20 |
| Heavy (500+ queries) | ~$25-40 |

With $5 free credits, you can run ~50-100 research queries to test.

## Prerequisites

1. **Modal Account**: Sign up at [modal.com](https://modal.com)
2. **API Keys** (all have free tiers):
   - [Serper.dev](https://serper.dev/) - Google Search (2,500 free/month)
   - [Semantic Scholar](https://api.semanticscholar.org/) - Academic papers (free, rate limited)
   - [Jina Reader](https://jina.ai/reader/) - Web content (1M tokens free/month)

## Quick Start

### 1. Install Modal CLI

```bash
pip install modal
```

### 2. Authenticate with Modal

```bash
modal token set --token-id YOUR_TOKEN_ID --token-secret YOUR_TOKEN_SECRET
```

Or use interactive login:
```bash
modal setup
```

### 3. Create Secrets (Secure - Never Committed)

**Option A: Via Modal Dashboard (Recommended)**
1. Go to [modal.com/secrets](https://modal.com/secrets)
2. Create a new secret named `dr-tulu-secrets`
3. Add these keys:
   - `SERPER_API_KEY`
   - `S2_API_KEY`
   - `JINA_API_KEY`

**Option B: Via CLI**
```bash
modal secret create dr-tulu-secrets \
  SERPER_API_KEY=your_serper_key \
  S2_API_KEY=your_s2_key \
  JINA_API_KEY=your_jina_key
```

### 4. Deploy

```bash
cd deploy/modal
modal deploy dr_tulu_modal.py
```

### 5. Test Your Deployment

```bash
# Run local tests first
modal run dr_tulu_modal.py

# After deploy, test the API
curl -X POST https://YOUR_APP_NAME--web-app.modal.run/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest advances in reinforcement learning?"}'
```

## API Endpoints

Once deployed, you'll get a URL like: `https://YOUR_USERNAME--dr-tulu-research-agent--web-app.modal.run`

### POST /research
Main research endpoint.

```bash
curl -X POST https://YOUR_URL/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current state of quantum computing?",
    "max_iterations": 5
  }'
```

Response:
```json
{
  "answer": "Comprehensive research report...",
  "thinking": "Reasoning process...",
  "tool_calls": [...],
  "iterations": 3
}
```

### POST /search/google
Direct Google search.

```bash
curl -X POST https://YOUR_URL/search/google \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning trends 2025", "num_results": 5}'
```

### POST /search/scholar
Academic paper search.

```bash
curl -X POST https://YOUR_URL/search/scholar \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer architecture", "num_results": 10}'
```

### POST /browse
Fetch webpage content.

```bash
curl -X POST https://YOUR_URL/browse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

### GET /health
Health check.

```bash
curl https://YOUR_URL/health
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Modal Cloud                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   Web API       │───▶│     ResearchAgent               │ │
│  │   (FastAPI)     │    │     Orchestrates research       │ │
│  │   Always-on*    │    │     Scales to zero              │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│                                    │                         │
│           ┌────────────────────────┼────────────────────┐   │
│           ▼                        ▼                    ▼   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────┐│
│  │  DRTuluModel    │    │    MCPTools     │    │  Secrets ││
│  │  (L4 GPU)       │    │    (CPU)        │    │  (Modal) ││
│  │  Scales to zero │    │  Serper, S2,    │    │  Secure  ││
│  └─────────────────┘    │  Jina           │    └──────────┘│
│                         └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘

* Web API container stays warm for 5 min, then scales to zero
```

## Customization

### Change GPU Type

Edit `dr_tulu_modal.py`:

```python
@app.cls(
    gpu=modal.gpu.L4(),      # Default: ~$0.50/hr, good for 8B
    # gpu=modal.gpu.T4(),    # Cheaper: ~$0.30/hr, slower
    # gpu=modal.gpu.A10G(),  # Faster: ~$1.00/hr
    ...
)
class DRTuluModel:
```

### Adjust Timeouts

```python
container_idle_timeout=300,  # Seconds before scale-to-zero (default: 5 min)
```

### Increase Concurrency

```python
allow_concurrent_inputs=10,  # Max parallel requests per container
```

## Monitoring

View logs and usage in the Modal dashboard:
- [modal.com/apps](https://modal.com/apps) - See deployed apps
- [modal.com/usage](https://modal.com/usage) - Monitor costs

## Troubleshooting

### "Model loading failed"
- The L4 GPU has 24GB VRAM. DR-Tulu-8B should fit, but try reducing `max_model_len` if issues occur.

### "Secret not found"
- Make sure you created the secret with exactly `dr-tulu-secrets` as the name
- Check: `modal secret list`

### Cold start is slow
- First request after idle takes ~60-90 seconds to load the model
- Subsequent requests are fast (~2-5 seconds)
- Consider keeping a warm instance for production

### API keys not working
- Verify keys work directly:
  ```bash
  curl -X POST "https://google.serper.dev/search" \
    -H "X-API-KEY: YOUR_KEY" \
    -H "Content-Type: application/json" \
    -d '{"q": "test"}'
  ```

## Frontend Integration

Use the API URL in your frontend:

```javascript
const response = await fetch('https://YOUR_URL/research', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What are the implications of AGI?',
    max_iterations: 5
  })
});

const result = await response.json();
console.log(result.answer);
```

## Support

- Modal docs: [modal.com/docs](https://modal.com/docs)
- DR-Tulu repo: [github.com/rlresearch/dr-tulu](https://github.com/rlresearch/dr-tulu)
