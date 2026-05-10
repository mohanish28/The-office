# Graph Report - .  (2026-05-10)

## Corpus Check
- Corpus is ~1,215 words - fits in a single context window. You may not need a graph.

## Summary
- 43 nodes · 53 edges · 8 communities detected
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.86)
- Token cost: 3,200 input · 2,800 output

## God Nodes (most connected - your core abstractions)
1. `Senior Engineering Lead â€” kimi-k2.6` - 8 edges
2. `CTO` - 8 edges
3. `Fine-Tuning Plan â€” NVIDIA NeMo + NIM` - 7 edges
4. `CTO Agent â€” nemotron-3-super-120b-a12b` - 6 edges
5. `Frontend Developer â€” deepseek-v4-flash` - 6 edges
6. `Product Manager â€” minimax-m2.7` - 4 edges
7. `Backend Developer â€” deepseek-v4-pro` - 4 edges
8. `API Engineer â€” glm-5.1` - 4 edges
9. `QA Engineer â€” mistral-small-4-119b` - 4 edges
10. `Approval Flow Pipeline (6-Step)` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Frontend Developer â€” deepseek-v4-flash` --semantically_similar_to--> `Frontend Developer`  [INFERRED] [semantically similar]
  nvidia_ai_office_hierarchy.md → startup_company_hierarchy.md
- `Owner / CEO (You)` --semantically_similar_to--> `CEO / Co-Founder`  [INFERRED] [semantically similar]
  nvidia_ai_office_hierarchy.md → startup_company_hierarchy.md
- `CTO Agent â€” nemotron-3-super-120b-a12b` --semantically_similar_to--> `CTO`  [INFERRED] [semantically similar]
  nvidia_ai_office_hierarchy.md → startup_company_hierarchy.md
- `Product Manager â€” minimax-m2.7` --semantically_similar_to--> `Product Manager`  [INFERRED] [semantically similar]
  nvidia_ai_office_hierarchy.md → startup_company_hierarchy.md
- `Backend Developer â€” deepseek-v4-pro` --semantically_similar_to--> `Backend Developer`  [INFERRED] [semantically similar]
  nvidia_ai_office_hierarchy.md → startup_company_hierarchy.md

## Hyperedges (group relationships)
- **QA + Safety Gate (Level 4 Quality Checkpoint)** — nvidia_qa_engineer, nvidia_safety_reviewer, nvidia_senior_engineer_lead [EXTRACTED 1.00]
- **Level 3 Parallel Worker Execution** — nvidia_frontend_dev, nvidia_backend_dev, nvidia_api_engineer, nvidia_devops_infra [EXTRACTED 1.00]
- **NVIDIA NIM + NeMo Fine-Tuning Deployment Stack** — nvidia_nemo_framework, nvidia_nim_platform, nvidia_finetuning_plan [EXTRACTED 1.00]

## Communities

### Community 0 - "QA Safety & Fine-Tuning Stack"
Cohesion: 0.22
Nodes (10): Fine-Tuning Plan â€” NVIDIA NeMo + NIM, Frontend Developer â€” deepseek-v4-flash, nvidia/nemotron-3-content-safety, deepseek-ai/deepseek-v4-flash, mistralai/mistral-small-4-119b-2603, NVIDIA NeMo Framework, NVIDIA NIM Platform, QA Engineer â€” mistral-small-4-119b (+2 more)

### Community 1 - "Command & Approval Chain"
Cohesion: 0.31
Nodes (9): Approval Flow Pipeline (6-Step), CTO Agent â€” nemotron-3-super-120b-a12b, moonshotai/kimi-k2.6, minimaxai/minimax-m2.7, nvidia/nemotron-3-super-120b-a12b, Owner / CEO (You), Product Manager â€” minimax-m2.7, Senior Engineering Lead â€” kimi-k2.6 (+1 more)

### Community 2 - "Startup Org Structure"
Cohesion: 0.22
Nodes (9): CEO / Co-Founder, CMO, Content Writer, COO, HR / People Ops, Legal / Finance (Outsourced), Marketing Lead, Sales Representative (+1 more)

### Community 3 - "Infrastructure & Integration Layer"
Cohesion: 0.25
Nodes (8): API Engineer â€” glm-5.1, DevOps / Infra â€” mistral-medium-3.5, z-ai/glm-5.1, mistralai/mistral-medium-3.5-128b, API Engineer, CTO, DevOps / Infra, Frontend Developer

### Community 4 - "Backend Development"
Cohesion: 0.67
Nodes (3): Backend Developer â€” deepseek-v4-pro, deepseek-ai/deepseek-v4-pro, Backend Developer

### Community 5 - "Data Extraction & Analysis"
Cohesion: 1.0
Nodes (2): Data Extractor â€” nemotron-ocr-v1, Data Analyst

### Community 6 - "RAG Search"
Cohesion: 1.0
Nodes (1): RAG / Search â€” llama-nemotron-rerank-vl

### Community 7 - "Product Design"
Cohesion: 1.0
Nodes (1): UI/UX Designer

## Knowledge Gaps
- **21 isolated node(s):** `Data Extractor â€” nemotron-ocr-v1`, `RAG / Search â€” llama-nemotron-rerank-vl`, `nvidia/nemotron-3-super-120b-a12b`, `moonshotai/kimi-k2.6`, `minimaxai/minimax-m2.7` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Data Extraction & Analysis`** (2 nodes): `Data Extractor â€” nemotron-ocr-v1`, `Data Analyst`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `RAG Search`** (1 nodes): `RAG / Search â€” llama-nemotron-rerank-vl`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Product Design`** (1 nodes): `UI/UX Designer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CTO` connect `Infrastructure & Integration Layer` to `QA Safety & Fine-Tuning Stack`, `Command & Approval Chain`, `Startup Org Structure`, `Backend Development`?**
  _High betweenness centrality (0.320) - this node is a cross-community bridge._
- **Why does `CEO / Co-Founder` connect `Startup Org Structure` to `Command & Approval Chain`, `Infrastructure & Integration Layer`?**
  _High betweenness centrality (0.301) - this node is a cross-community bridge._
- **Why does `Senior Engineering Lead â€” kimi-k2.6` connect `Command & Approval Chain` to `QA Safety & Fine-Tuning Stack`, `Infrastructure & Integration Layer`, `Backend Development`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `CTO` (e.g. with `Product Manager` and `CTO Agent â€” nemotron-3-super-120b-a12b`) actually correct?**
  _`CTO` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Data Extractor â€” nemotron-ocr-v1`, `RAG / Search â€” llama-nemotron-rerank-vl`, `nvidia/nemotron-3-super-120b-a12b` to the rest of the system?**
  _21 weakly-connected nodes found - possible documentation gaps or missing edges._