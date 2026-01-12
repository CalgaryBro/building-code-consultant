# Claude Project Notes

## Important Guidelines

### Port Management
- **NEVER try to free/stop services on ports** - If a port is in use, use an alternative free port instead
- For PostgreSQL, if port 5432 is busy, use 5433 or another available port
- Modify docker-compose.yml to use different ports rather than stopping system services

### Web Search & Data Fetching
When searching for information or downloading data from the internet:

1. **Use realistic browser headers** when making HTTP requests:
   ```bash
   curl -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
        -H "Accept: application/json" \
        "https://api.example.com/data"
   ```

2. **Implement delays between requests** to avoid rate limiting:
   ```bash
   sleep 2  # Wait 2 seconds between requests
   ```

3. **Check API documentation first** - Use WebSearch to find official API endpoints
4. **Prefer official data portals** - Calgary Open Data (data.calgary.ca), Open Alberta, NRC, etc.
5. **Save downloaded data** with descriptive filenames in the `/data/` directory
6. **Verify downloads** - Check file sizes and record counts after download

### Open Data Sources for This Project
- **Calgary Open Data**: https://data.calgary.ca/
- **Open Alberta**: https://open.alberta.ca/
- **NRC Publications**: https://nrc-publications.canada.ca/
- **Socrata API**: Use `resource/{dataset-id}.json` pattern with `$limit` parameter

### Database Configuration
- Primary database: PostgreSQL via Docker (pgvector image)
- Default port: 5432 (or next available if occupied)
- Connection string in `.env` file

### Resume Commands
See `Calgary_Code_Expert_System_Plan.md` section "Implementation Progress Log" for latest status and commands.

---

## AI Q&A System (LLM Service)

### Model Configuration
- **Model**: LiquidAI LFM2.5-1.2B-Instruct (GGUF Q4_K_M quantization)
- **Backend**: llama.cpp via llama-cpp-python 0.3.16+
- **Container**: `calgary_codes_llm` on port 8081
- **Memory**: ~700MB model file, ~1.5GB runtime
- **Context**: 4096 tokens (model supports up to 32K)

### LFM2.5 Recommended Parameters (from LiquidAI docs)
```python
temperature: 0.1
top_k: 50
top_p: 0.1
repeat_penalty: 1.05
```

### Key Files
- `app/backend/llm_service/main.py` - LLM FastAPI service
- `app/backend/llm_service/Dockerfile` - Container with llama-cpp-python
- `app/backend/app/api/chat.py` - Chat API with hybrid search
- `app/backend/docker-compose.yml` - LLM service configuration

### Hybrid Search System
The chat uses hybrid search combining:
1. **Vector search** - pgvector semantic similarity (all-MiniLM-L6-v2 embeddings)
2. **Keyword search** - PostgreSQL full-text search
3. **RRF fusion** - Reciprocal Rank Fusion to combine results

### Commands
```bash
# Start LLM service
docker compose up -d llm-service

# Check model status
curl http://localhost:8081/model-info

# Test chat endpoint
curl -X POST http://localhost:8002/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum stair width?"}'

# View logs
docker compose logs llm-service --tail 50
```

### Troubleshooting
- If model fails to load, ensure llama-cpp-python >= 0.3.16 (supports LFM2 architecture)
- Check `docker stats calgary_codes_llm` for resource usage
- Model download happens on first startup (~700MB from HuggingFace)

### Bug Fix: Consecutive Request Failure (2026-01-11)
**Issue:** LFM would fail with "llama_decode returned -1" on second consecutive request.
**Cause:** KV cache not being reset between requests in llama.cpp.
**Fix:** Added `_llm.reset()` call before each generation in `llm_service/main.py`.

---

## VLM Extraction Pipeline (2026-01-11)

### Overview
Re-extract ALL building codes using Qwen3-VL 30B via LM Studio to get clean, properly-spaced text (fixes pythonic extraction issues like "Part9ofDivisionB").

### Architecture
```
PDF Pages → Qwen3-VL 30B (LM Studio) → Clean JSON → all-MiniLM-L6-v2 → PostgreSQL/pgvector
           (one-time extraction)                    (384-dim embeddings)
```

### Key Files Created
| File | Purpose |
|------|---------|
| `app/scripts/vlm_extract_all.py` | Main VLM extraction script |
| `app/scripts/repopulate_db.py` | Database reload + embedding generation |
| `data/codes/vlm/*.json` | VLM extraction output files |

### VLM Extraction Script Usage
```bash
# Activate environment
source app/backend/.venv/bin/activate

# Test on single page
python app/scripts/vlm_extract_all.py --test

# Extract specific code
python app/scripts/vlm_extract_all.py --code nbc_part1

# Extract all codes (overnight ~15-16 hours)
python app/scripts/vlm_extract_all.py --all

# Resume from specific page
python app/scripts/vlm_extract_all.py --code nbc_part9 --resume 100
```

### Configuration
- **LM Studio Server:** http://10.0.0.133:8080
- **Model:** qwen/qwen3-vl-30b
- **DPI:** 300 (optimal for OCR)
- **Parameters:** temperature=0.7, top_p=0.8, top_k=20
- **Breaks:** 1-minute rest every 20 pages
- **Progress saves:** Every 10 pages

### Extraction Order & Estimates
| Code | Pages | Est. Time | Output File |
|------|-------|-----------|-------------|
| nbc_part1 | 41 | ~25 min | nbc_ae_2023_part1_vlm.json |
| nbc_part9_general | 23 | ~15 min | nbc_ae_2023_part9_general_vlm.json |
| nbc_part9 | 291 | ~4 hours | nbc_ae_2023_part9_vlm.json |
| necb | 300 | ~5 hours | necb_2020_vlm.json |
| nfc | 400 | ~6 hours | nfc_ae_2023_vlm.json |
| npc | 250 | ~4 hours | npc_2020_vlm.json |
| land_use_bylaw | 500 | ~8 hours | land_use_bylaw_vlm.json |

### Database Repopulation
```bash
# After extraction completes
python app/scripts/repopulate_db.py --source data/codes/vlm/ --backup --clear

# Verify database
python app/scripts/repopulate_db.py --verify
```

### JSON Output Schema
```json
{
  "metadata": {
    "code_name": "NBC(AE) 2023",
    "extraction_method": "vlm",
    "extraction_model": "qwen/qwen3-vl-30b",
    "extraction_date": "2026-01-11"
  },
  "articles": [
    {
      "article_number": "1.3.3.3",
      "title": "Application of Parts 9, 10 and 11",
      "full_text": "Complete verbatim text..."
    }
  ]
}
```

### Monitoring Extraction
```bash
# Watch live progress
tail -f vlm_extraction.log

# Check output files
ls -la data/codes/vlm/*.json

# Check progress
cat data/codes/vlm/*_vlm.progress.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Pages: {d[\"pages_extracted\"]}')"
```

### Database Schema Updates
Added extraction tracking columns to `articles` table:
- `extraction_model` (VARCHAR 100) - e.g., "qwen3-vl:30b"
- `extraction_confidence` (VARCHAR 20) - HIGH/MEDIUM/LOW
- `vlm_extracted` (BOOLEAN) - True if VLM extracted
- `extraction_date` (TIMESTAMP)

---

## SSL Certificate Fix (Fortinet Firewall)

This network has a Fortinet firewall doing SSL/TLS inspection. HTTPS connections are intercepted and re-signed with a Fortinet CA certificate.

### The Problem
- SSL verification fails for curl, git, pip, Python requests
- Error: `SSL certificate problem: unable to get local issuer certificate`

### Solution Applied
1. Created combined CA bundle including Fortinet certificate:
   ```bash
   # Extract server cert (includes Fortinet signature)
   echo | openssl s_client -connect github.com:443 -showcerts 2>/dev/null | \
       awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/{print}' > /tmp/fortinet_chain.pem

   # Combine with standard CAs
   cat /opt/homebrew/opt/ca-certificates/share/ca-certificates/cacert.pem \
       /tmp/fortinet_chain.pem > ~/.ssl/combined_ca.pem
   ```

2. Configure tools to use combined bundle:
   ```bash
   # For curl (use Homebrew curl with --cacert)
   /opt/homebrew/opt/curl/bin/curl --cacert ~/.ssl/combined_ca.pem https://example.com

   # For pip (trusts specific hosts)
   pip config set global.trusted-host "pypi.org files.pythonhosted.org github.com"

   # For git
   git config --global http.sslVerify false
   ```

### pip Configuration
`~/.config/pip/pip.conf`:
```ini
[global]
trusted-host = pypi.org
               files.pythonhosted.org
               github.com
               raw.githubusercontent.com
               codeload.github.com
```

---

## LFM2.5-VL via Transformers (Python 3.11)

The LFM2.5-VL vision model requires a specific transformers version not yet on PyPI.

### Setup
1. Create Python 3.11 venv (required for transformers 5.x):
   ```bash
   /opt/homebrew/bin/python3.11 -m venv app/backend/.venv311
   source app/backend/.venv311/bin/activate
   ```

2. Download and install transformers from specific commit:
   ```bash
   # Download using Homebrew curl with SSL cert
   /opt/homebrew/opt/curl/bin/curl --cacert ~/.ssl/combined_ca.pem -L -o /tmp/transformers.zip \
       "https://github.com/huggingface/transformers/archive/3c2517727ce28a30f5044e01663ee204deb1cdbe.zip"

   # Extract and install
   cd /tmp && unzip -q transformers.zip
   pip install /tmp/transformers-3c2517727ce28a30f5044e01663ee204deb1cdbe/
   pip install torch torchvision pillow
   ```

### Usage
```python
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image

model_id = "LiquidAI/LFM2.5-VL-1.6B"
device = "mps"  # Apple Silicon

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForImageTextToText.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    trust_remote_code=True,
    low_cpu_mem_usage=True,
).to(device)

image = Image.open("page.png")
conversation = [
    {"role": "user", "content": [
        {"type": "image", "image": image},
        {"type": "text", "text": "What article numbers are visible?"},
    ]},
]

inputs = processor.apply_chat_template(conversation, add_generation_prompt=True,
                                        return_tensors="pt", return_dict=True, tokenize=True)
inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
if 'pixel_values' in inputs:
    inputs['pixel_values'] = inputs['pixel_values'].half()

outputs = model.generate(**inputs, max_new_tokens=200, do_sample=True, temperature=0.7)
response = processor.batch_decode(outputs, skip_special_tokens=True)[0]
```

### Performance
- Model load: ~1s (cached)
- Inference: ~8-18s per image on Apple M4 Max
- Memory: ~3GB

---

## VLM Comparison: Qwen3-VL 30B vs LFM2.5-VL 1.6B (2026-01-11)

### Experiment Overview
Compared two vision-language models for building code PDF extraction:
- **Qwen3-VL 30B** - Large model via LM Studio (remote GPU server)
- **LFM2.5-VL 1.6B** - Small model via Transformers (local Mac MPS)

Test: Extract 10 pages (pages 30-39) from NBC-AE-2023.pdf and compare quality.

### Results Summary

| Metric | Qwen3-VL 30B | LFM2.5-VL 1.6B |
|--------|--------------|----------------|
| Model Size | 30B params | 1.6B params (18x smaller) |
| Hardware | LM Studio (GPU) | Local Mac (MPS) |
| Avg Time/Page | 35.0s | 19.5s |
| Avg Chars/Page | 3,341 | 2,121 (37% less) |
| Text Accuracy | ★★★★★ Excellent | ★★☆☆☆ Poor |
| Article Numbers | ✓ Correct | ⚠️ Often wrong |
| Hallucinations | Very Low | High |

### LFM2.5-VL Optimized Settings
After parameter tuning, these settings work best for LFM2.5-VL:
```python
# CRITICAL: Use greedy decoding to avoid FP16 overflow errors
image_size = (512, 664)  # Larger = better accuracy
do_sample = False        # Greedy decoding (REQUIRED)
max_new_tokens = 1000

# DO NOT use sampling - causes RuntimeError:
# "probability tensor contains either `inf`, `nan` or element < 0"
```

### Quality Issues with LFM2.5-VL

1. **Severe Hallucinations** - Generates repetitive sequences:
   ```
   # Expected: "Group D, business and personal services occupancies"
   # LFM output: "A.4.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1..."
   ```

2. **Wrong Article Numbers**:
   ```
   # Actual page content: "9.10.8.2. Fire-Resistance Ratings"
   # LFM output (before optimization): "S13.1 Floor-Resistance Ratings"
   ```

3. **Missing Content** - Extracts 37% less text on average

4. **Incorrect Definitions** - Sometimes reads completely different text

### Page-by-Page Results

| Page | Qwen Time | LFM Time | Qwen Chars | LFM Chars | Quality |
|------|-----------|----------|------------|-----------|---------|
| 30 | 20.8s | 11.6s | 1,325 | 1,673 | ✓ Good |
| 31 | 58.3s | 14.7s | 6,038 | 2,372 | ~ Moderate |
| 32 | 30.1s | 9.1s | 2,988 | 1,334 | ~ Moderate |
| 33 | 30.1s | 26.5s | 2,203 | 967 | ⚠️ Hallucination |
| 34 | 38.1s | 23.9s | 3,131 | 2,616 | ✓ Good |
| 35 | 34.7s | 22.6s | 3,230 | 740 | ⚠️ Hallucination |
| 36 | 31.7s | 22.5s | 3,248 | 3,761 | ✓ Good |
| 37 | 35.3s | 22.4s | 3,716 | 1,222 | ~ Moderate |
| 38 | 35.1s | 23.9s | 3,552 | 3,531 | ✓ Good |
| 39 | 35.6s | 17.9s | 3,979 | 2,997 | ✓ Good |

### Sample Comparison - Page 33 (Article 1.3.3.3)

**Qwen3-VL 30B (Correct):**
```
Division A
1.3.3.2.
Building Administrator may be used in determining compliance with
the requirements of this Code.
3) The Provincial Building Administrator may issue lists of materials
or products that satisfy the requirements of this Code...
```

**LFM2.5-VL 1.6B (Hallucinated):**
```
1.3.3.3. Application of Parts 9, 10 and 11
1.3.3.3.1. Part 9 of Division B applies to all buildings...
c) Group D. commercial occupancies (see Article A.4.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1...
[repetitive hallucination continues]
```

### Recommendations

| Use Case | Recommended Model |
|----------|-------------------|
| **Production OCR** | ✅ Qwen3-VL 30B |
| **Building codes** | ✅ Qwen3-VL 30B |
| **Quick preview** | ⚠️ LFM2.5-VL (faster but unreliable) |
| **Accurate extraction** | ✅ Qwen3-VL 30B |

### Conclusion
**LFM2.5-VL 1.6B is NOT suitable for building code extraction.** The 18x smaller model size results in:
- 37% less content extracted
- Frequent hallucinations and repetitions
- Incorrect article numbers
- Unreliable text accuracy

**Use Qwen3-VL 30B** for all production building code extraction tasks.

### Output Files
- `data/codes/vlm/lfm_comparison_10pages.json` - LFM2.5-VL extraction results
- `data/codes/vlm/nbc_ae_2023_part1_vlm.json` - Qwen3-VL extraction results

---

## Production VLM for Drawing Analysis

See **`VLM_Production_Architecture.md`** for full details.

### Recommended Model: Qwen3-VL-8B-Instruct

| Aspect | Details |
|--------|---------|
| **Model** | Qwen3-VL-8B-Instruct (GGUF) |
| **Accuracy** | 97% DocVQA |
| **VRAM** | 12-16 GB (Q8), 8 GB (Q4) |
| **Deployment** | Ollama, vLLM, llama.cpp |
| **Use Case** | Analyze uploaded architectural drawings for code violations |

### Quick Start with Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model (~6GB)
ollama pull qwen3-vl:8b

# Test
ollama run qwen3-vl:8b "Describe this floor plan" --image drawing.png
```

### Two-Model Architecture

```
PDF Extraction (batch):     Qwen3-VL-30B (LM Studio) → Best accuracy
Drawing Analysis (live):    Qwen3-VL-8B (Ollama)     → Fast, production-ready
```

### Key Use Cases

1. **Site Plan Analysis** - Extract setbacks, lot coverage, building footprint
2. **Floor Plan Analysis** - Room dimensions, stair widths, door sizes
3. **Code Violation Detection** - Compare extracted values against NBC/Land Use Bylaw
4. **Automated Compliance Reports** - Pass/Fail with code citations
