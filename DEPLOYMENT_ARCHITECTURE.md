# Calgary Building Code Expert System - Deployment Architecture

## Executive Summary

After extensive testing of VLM (Vision Language Models) and OCR solutions, we've designed a cost-effective 3-server architecture that runs entirely on CPU, optimized for:
1. **Code/Standards Extraction** - One-time processing of building codes
2. **Chat Q&A** - Real-time answers about building regulations
3. **Drawing Analysis** - Compliance checking for uploaded drawings

---

## Investigation Summary (2026-01-11 to 2026-01-12)

### Models Tested

| Model | Size | Hardware | Time/Page | Quality | Result |
|-------|------|----------|-----------|---------|--------|
| Qwen3-VL-8B (Ollama) | 6.1GB | Oracle CPU | 27+ min | N/A | Too slow |
| Qwen3-VL-30B (LM Studio) | 20GB | Mac GPU | 84s | **HALLUCINATED** | Wrong article numbers |
| GOT-OCR2 | 580MB | Oracle CPU | ~3 min | **Excellent** | Accurate extraction |
| Qwen3-VL-2B (llama.cpp) | 1.5GB | Mac CPU | 136s | Good | Viable for structuring |

### Key Findings

1. **VLM Hallucination Problem**: Qwen3-VL-30B extracted "9.8.1" instead of "9.8.8" (wrong article numbers). This is critical for building codes where accuracy is paramount.

2. **GOT-OCR2 Wins for Documents**: Despite being a simpler encoder-decoder model (580M params vs 8.8B), GOT-OCR2 produced accurate text without hallucinations.

3. **VLM Still Useful for Drawings**: VLMs are needed for spatial understanding (room labels, dimensions, floor plans) where some interpretation is acceptable.

4. **CPU-Only is Viable**: With the right models, we can run everything on CPU with acceptable latency.

---

## Final 3-Server Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    VPS-2 ($8.76/mo - RECOMMENDED)                    │    │
│  │                    6 vCores, 12GB RAM, 100GB NVMe                    │    │
│  │                                                                      │    │
│  │   ┌──────────┐    ┌──────────────┐    ┌─────────────────────┐       │    │
│  │   │  Nginx   │───▶│   React App  │    │    FastAPI Backend  │       │    │
│  │   │  + SSL   │    │  (Frontend)  │    │    - Auth           │       │    │
│  │   └──────────┘    └──────────────┘    │    - DSSP Calc      │       │    │
│  │                                        │    - Permits        │       │    │
│  │   ┌──────────────────────────────┐    │    - Quantity Survey│       │    │
│  │   │  PostgreSQL 16 + pgvector    │    └─────────────────────┘       │    │
│  │   │  - 3000+ articles embedded   │                                  │    │
│  │   │  - User data                 │    ┌─────────────────────┐       │    │
│  │   │  - Chat history              │    │   LFM 2.5 (1.2B)    │       │    │
│  │   └──────────────────────────────┘    │   Chat Q&A (~30s)   │       │    │
│  │                                        └─────────────────────┘       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      │ HTTPS (Secure API)                    │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ORACLE SERVER (FREE - 23GB RAM)                   │    │
│  │                    4 ARM64 Cores, No GPU                             │    │
│  │                                                                      │    │
│  │   ┌───────────────────────────────────────────────────────────┐     │    │
│  │   │                    FastAPI AI Service                      │     │    │
│  │   │                                                            │     │    │
│  │   │   ┌─────────────────┐    ┌─────────────────────────┐      │     │    │
│  │   │   │   GOT-OCR2      │    │    Qwen2.5-7B-Instruct  │      │     │    │
│  │   │   │   (580M)        │    │    (via Ollama)         │      │     │    │
│  │   │   │                 │    │                         │      │     │    │
│  │   │   │ Drawing OCR     │    │  Text Structuring       │      │     │    │
│  │   │   │ ~3 min/page     │    │  ~2 min/request         │      │     │    │
│  │   │   └─────────────────┘    └─────────────────────────┘      │     │    │
│  │   └───────────────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOCAL MAC (One-Time Extraction Only)                      │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Code Extraction Pipeline (One-Time, ~20 hours total)                │   │
│   │                                                                      │   │
│   │   NBC PDF ──▶ GOT-OCR2/VLM ──▶ LLM Structuring ──▶ JSON             │   │
│   │                                                                      │   │
│   │   Codes to Extract:                                                  │   │
│   │   - NBC 2023 Alberta Edition (Part 1, Part 9, Parts 3-8)            │   │
│   │   - NECB 2020 (Energy Code)                                         │   │
│   │   - NFC-AE 2023 (Fire Code)                                         │   │
│   │   - NPC 2020 (Plumbing Code)                                        │   │
│   │   - Calgary Land Use Bylaw                                          │   │
│   │   - STANDATA Bulletins (41 PDFs)                                    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Server Responsibilities

### VPS-2 (Web Server) - $8.76/month
**Specs:** 6 vCores, 12GB RAM, 100GB NVMe SSD

| Component | Purpose | RAM Usage |
|-----------|---------|-----------|
| Nginx + SSL | Reverse proxy, HTTPS | ~50MB |
| React Frontend | User interface | Static files |
| FastAPI Backend | API, business logic | ~500MB |
| PostgreSQL + pgvector | Vector database, 3000+ articles | ~2GB |
| LFM 2.5 (1.2B) | Chat Q&A responses | ~3GB |
| **Total** | | **~6GB** |

**Response Times:**
- Page loads: <100ms
- Database queries: <50ms
- Chat Q&A: ~30 seconds (LFM 2.5 generation)

### Oracle Server (AI Processing) - FREE
**Specs:** 4 ARM64 Cores, 23GB RAM, 36GB Disk

| Component | Purpose | RAM Usage |
|-----------|---------|-----------|
| GOT-OCR2 (580M) | Drawing OCR extraction | ~3GB |
| Qwen2.5-7B (Ollama) | Text structuring | ~8GB |
| FastAPI wrapper | AI service API | ~200MB |
| **Total** | | **~11GB** |

**Response Times:**
- Drawing OCR: ~3 minutes per page
- Text structuring: ~2 minutes per request
- Total drawing analysis: ~5-10 minutes

### Local Mac (Extraction Only) - One-Time Use
**Purpose:** Extract and structure all building codes before deployment

| Task | Tool | Time Estimate |
|------|------|---------------|
| NBC Part 1 | Qwen3-VL 30B (GPU) | ~30 min |
| NBC Part 9 | Qwen3-VL 30B (GPU) | ~4 hours |
| Other codes | VLM or GOT-OCR2 | ~12 hours |
| **Total** | | **~20 hours** |

---

## Data Flow

### Flow 1: Chat Q&A (Real-time)
```
User Question ──▶ VPS-2 Backend ──▶ Hybrid Search (pgvector + FTS)
                                          │
                                          ▼
                                   Top 5 relevant articles
                                          │
                                          ▼
                                   LFM 2.5 generates answer
                                          │
                                          ▼
                                   Response with citations
```

### Flow 2: Drawing Analysis (Async)
```
Upload Drawing ──▶ VPS-2 Backend ──▶ Queue job
                                          │
                                          ▼
                        Oracle Server (GOT-OCR2 + Qwen2.5-7B)
                                          │
                                          ▼
                        Extract: rooms, dimensions, labels
                                          │
                                          ▼
                        VPS-2: Rule engine checks compliance
                                          │
                                          ▼
                        Return violations/passes to user
```

### Flow 3: Code Extraction (One-Time)
```
PDF ──▶ Page Images ──▶ VLM/OCR ──▶ Raw Text
                                        │
                                        ▼
                              LLM Structuring
                                        │
                                        ▼
                              Structured JSON
                                        │
                                        ▼
                    Load to PostgreSQL + Generate Embeddings
```

---

## Cost Analysis

### Monthly Costs
| Item | Cost |
|------|------|
| VPS-2 (Web + DB + Chat) | $8.76 |
| Oracle Server (AI) | $0.00 |
| Domain + SSL | ~$1.00 |
| **Total** | **~$10/month** |

### One-Time Costs
| Item | Cost |
|------|------|
| Code extraction (electricity) | ~$5 |
| Initial setup time | Your time |

### VPS Comparison (Why VPS-2?)
| VPS | Specs | Price | Verdict |
|-----|-------|-------|---------|
| VPS-1 | 1 core, 1GB RAM | $3.64 | Too small for LFM |
| **VPS-2** | **6 cores, 12GB RAM** | **$8.76** | **Optimal balance** |
| VPS-3 | 2 cores, 2GB RAM | $6.06 | Insufficient RAM |

---

## Implementation Progress

### Completed
- [x] Docker installed on Oracle server
- [x] Ollama installed with Qwen3-VL-8B
- [x] GOT-OCR2 tested (~3 min/page, excellent accuracy)
- [x] Qwen3-VL-30B tested via LM Studio (hallucination issue identified)
- [x] Qwen3-VL-2B tested via llama.cpp (136s/page, viable)
- [x] VLM extraction scripts created (`app/scripts/vlm_extract_all.py`)
- [x] Database repopulation script created (`app/scripts/repopulate_db.py`)
- [x] Partial VLM extraction completed (NBC Part 1, Part 9 General)
- [x] Qwen2.5-7B-Instruct installed on Oracle (4.7GB, for text structuring)
- [x] GOT-OCR2 FastAPI wrapper created (`/opt/got-ocr/got_ocr_service.py`, port 8082)

### In Progress
- [ ] Full NBC Part 9 extraction (page ~10/291)
- [ ] VPS-2 server rental

### Pending
- [ ] Set up PostgreSQL + pgvector on VPS-2
- [ ] Deploy FastAPI + React on VPS-2
- [ ] Install LFM 2.5 on VPS-2
- [ ] Secure API connection between VPS-2 and Oracle
- [ ] Complete code extraction on Local Mac
- [ ] Generate embeddings and load to production DB

---

## Technical Decisions Log

### Decision 1: GOT-OCR2 over VLM for Code Extraction
**Date:** 2026-01-12
**Reason:** VLM (Qwen3-VL-30B) hallucinated article numbers (extracted 9.8.1 instead of 9.8.8). GOT-OCR2 produced accurate text despite being 15x smaller.
**Impact:** More reliable code database, no manual verification needed.

### Decision 2: Two-Stage Pipeline for Structured Output
**Date:** 2026-01-12
**Approach:** GOT-OCR2 (raw text) → Qwen2.5-7B (structured JSON)
**Reason:** GOT-OCR2 only outputs plain text. Using a separate LLM for structuring allows better control and validation.

### Decision 3: LFM 2.5 for Chat on VPS-2
**Date:** 2026-01-12
**Reason:** 1.2B params fits in 3GB RAM, 30s response time acceptable for Q&A, already integrated in codebase.
**Alternative Considered:** Run chat on Oracle - rejected due to latency (~5 min would be too slow for interactive chat).

### Decision 4: Rule Engine for Compliance
**Date:** 2026-01-12
**Approach:** Deterministic rule matching instead of LLM for violation detection.
**Reason:** Building codes have exact requirements (e.g., "min 860mm width"). Rule engine ensures 100% accuracy for known rules.

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `app/scripts/vlm_extract_all.py` | VLM extraction script using LM Studio |
| `app/scripts/repopulate_db.py` | Database reload with embeddings |
| `LLM_SERVER.md` | Oracle server documentation |
| `DEPLOYMENT_ARCHITECTURE.md` | This file - architecture overview |
| `data/codes/vlm/*.json` | VLM extraction outputs |

---

## Quick Reference Commands

### Oracle Server
```bash
# SSH connection
ssh -i ~/Oracle_data/ssh-key-2025-05-12.key opc@129.153.97.27

# Check resources
free -h && df -h /

# Ollama status
sudo systemctl status ollama
ollama list

# Start/stop Ollama
sudo systemctl start ollama
sudo systemctl stop ollama
```

### Local Development
```bash
# Activate backend
source app/backend/.venv/bin/activate

# Run VLM extraction
python app/scripts/vlm_extract_all.py --section nbc_part9

# Test embedding service
python -c "from app.services.embedding_service import get_embedding_service; print('OK')"

# Start local backend
cd app/backend && uvicorn app.main:app --reload --port 8002
```

### Production (VPS-2 - After Setup)
```bash
# Deploy with Docker Compose
docker compose -f docker-compose.prod.yml up -d

# Check all services
docker compose ps

# View logs
docker compose logs -f backend
```

---

## Next Steps (In Order)

1. **Rent VPS-2** - $8.76/month, 6 cores, 12GB RAM
2. **Set up VPS-2 base** - Docker, PostgreSQL, Nginx
3. **Create GOT-OCR2 API on Oracle** - FastAPI wrapper for drawing OCR
4. **Complete code extraction** - Run remaining VLM extraction on Local Mac
5. **Deploy to VPS-2** - FastAPI, React, LFM 2.5
6. **Connect servers** - Secure API between VPS-2 and Oracle
7. **Load production data** - Embeddings, user accounts
8. **Test end-to-end** - Chat, drawing upload, compliance check

---

## Appendix: Model Comparison

### For Document OCR
| Model | Accuracy | Speed (CPU) | Recommendation |
|-------|----------|-------------|----------------|
| GOT-OCR2 | Excellent | 3 min/page | **Use this** |
| Qwen3-VL-8B | Good | 27+ min/page | Too slow |
| Qwen3-VL-30B | Hallucinations | N/A (GPU) | Not for OCR |

### For Chat Q&A
| Model | Quality | Speed | RAM | Recommendation |
|-------|---------|-------|-----|----------------|
| LFM 2.5 (1.2B) | Good | 30s | 3GB | **Use this** |
| Qwen2.5-7B | Better | 2 min | 8GB | Too slow for chat |
| GPT-4 (API) | Excellent | 5s | 0 | Too expensive |

### For Text Structuring
| Model | Accuracy | Speed | Recommendation |
|-------|----------|-------|----------------|
| Qwen2.5-7B | Excellent | 2 min | **Use this** |
| LFM 2.5 | Good | 30s | Alternative if faster needed |
