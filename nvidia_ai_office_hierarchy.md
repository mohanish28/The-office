**
## NVIDIA AI Office — LLM models assigned to company roles with approval hierarchy and fine-tuning plans

 # ⚡ Your AI Office — Powered by NVIDIA NIM
 Real NVIDIA models · Role-specific fine-tuning · Approval hierarchy

 🏢 Org Chart

 🔄 Approval Flow

 🤖 Model Assignments

 🎯 Fine-Tuning Plan

 

 

 

 👑 Owner — You

 
 👑

 YOU — Owner / CEO

 Business Approval Gate

 Final Authority 
 

 

 ⬆ All output reviewed before reaching you

 

 🧠 Level 1 — CTO Agent (Top Reviewer)

 
 🧠

 CTO Agent

 nemotron-3-super-120b-a12b

 Top Reviewer · 1M ctx 
 

 

 ⬆ Reviewed by CTO before escalating

 

 ⚡ Level 2 — Senior Engineering Lead

 
 
 ⚡

 Senior Engineer Lead

 kimi-k2.6

 1T MoE · Multimodal 
 
 
 📋

 Product Manager

 minimax-m2.7

 230B · Office + Reasoning 
 
 

 

 
 🛠️ Level 3 — Engineering Department

 
 ⚙️ Engineering Dept

 

 
 🖥️

 Frontend Dev

 deepseek-v4-flash

 284B · Fast UI 
 

 
 🗄️

 Backend Dev

 deepseek-v4-pro

 1M ctx · Deep Logic 
 

 
 🔗

 API Engineer

 glm-5.1

 Agentic · Tool Use 
 

 
 ☁️

 DevOps / Infra

 mistral-medium-3.5

 128B · Agentic 
 

 
 

 

 
 🔍 Level 4 — Quality & Data

 

 
 🧪 QA Pipeline

 
 ✅

 QA Engineer

 mistral-small-4-119b

 Logic Testing 
 
 
 🛡️

 Safety Reviewer

 nemotron-3-content-safety

 Free · Safety Gate 
 
 

 
 📊 Data Dept

 
 🔍

 Data Extractor

 nemotron-ocr-v1

 OCR · Tables 
 
 
 📈

 RAG / Search

 llama-nemotron-rerank-vl

 RAG · Reranker 
 
 

 

 
 

 

 
 How work moves through your AI office

 
 1

 
 🗂️ Task Created by Product Manager

 PM Agent receives the goal and breaks it into a structured spec: acceptance criteria, edge cases, API contracts. No code is written until the spec is approved by Senior Lead.

 minimax-m2.7 → outputs: spec document

 
 
 ↓

 
 2

 
 🛠️ Workers Execute in Parallel

 Frontend Dev writes React components. Backend Dev writes server logic. API Engineer writes endpoints. DevOps writes infra config. All work in parallel on their piece of the spec.

 deepseek-v4-flash · deepseek-v4-pro · glm-5.1 · mistral-medium-3.5

 
 
 ↓

 
 3

 
 🧪 QA + Safety Gate

 QA Engineer runs logic/unit tests and checks for bugs. Safety Reviewer scans for policy violations, hallucinations, or harmful content. ❌ If either fails → sent back to Level 3 with feedback. ✅ If both pass → escalates.

 mistral-small-4 + nemotron-3-content-safety

 
 
 ↩ REJECTED? Worker gets feedback and revises (max 3 iterations)

 ↓ if APPROVED

 
 4

 
 ⚡ Senior Engineer Lead Reviews

 kimi-k2.6 does a holistic code review: architecture quality, performance issues, integration consistency, and whether it matches the PM spec. Can request specific changes before escalating.

 kimi-k2.6 → verdict: APPROVE / REVISE

 
 
 ↩ REVISE? Specific file sent back to responsible worker

 ↓ if APPROVED

 
 5

 
 🧠 CTO Agent — Final Technical Review

 Nemotron Super reads the entire codebase with its 1M token context. Checks system-level concerns: scalability, security, tech debt, API contracts. Writes a review report before escalating to you.

 nemotron-3-super-120b-a12b → outputs: CTO review report

 
 
 ↓

 
 6

 
 👑 YOU — Business Approval

 You receive a clean summary: what was built, the CTO's assessment, test results, and a deploy recommendation. You approve → it ships. You reject → any level can be targeted for revision.

 Human decision gate — no model bypasses this

 
 

 ✅ APPROVED by Owner → Deploy via DevOps Agent (mistral-medium-3.5)

 
 

 

 

 Click a row to learn why this model fits this role

 
 🧠

 
 CTO / Top Reviewer

 nvidia/nemotron-3-super-120b-a12b

 
 
 Agentic reasoning, code review, planning
 1M context MoE Tool calling 

 
 120B (active: 12B)
 Downloadable 

 

 
 ⚡

 
 Senior Engineer Lead

 moonshotai/kimi-k2.6

 
 
 Long-horizon coding, vision, agentic
 1T MoE Multimodal Agentic 

 
 1T params
 Downloadable 

 

 
 📋

 
 Product Manager

 minimaxai/minimax-m2.7

 
 
 Specs, planning, office tasks, reasoning
 230B MoE Office 

 
 230B params
 Downloadable 

 

 
 🖥️

 
 Frontend Developer

 deepseek-ai/deepseek-v4-flash

 
 
 React, Vue, UI/UX code, fast generation
 284B MoE 1M ctx Fast 

 
 284B params
 Downloadable 

 

 
 🗄️

 
 Backend Developer

 deepseek-ai/deepseek-v4-pro

 
 
 Node.js, Python, DBs, server architecture
 1M ctx MoE Deep logic 

 
 MoE architecture
 Downloadable 

 

 
 🔗

 
 API Engineer

 z-ai/glm-5.1

 
 
 REST, GraphQL, tool use, integrations
 Agentic Tool Use Long-horizon 

 
 Flagship MoE
 Downloadable 

 

 
 ☁️

 
 DevOps / Infra

 mistralai/mistral-medium-3.5-128b

 
 
 Docker, CI/CD, Terraform, K8s configs
 128B Coding Agentic 

 
 128B params
 Downloadable 

 

 
 🧪

 
 QA Engineer

 mistralai/mistral-small-4-119b-2603

 
 
 Unit tests, integration tests, bug detection
 Reasoning 119B MoE 

 
 119B MoE
 Downloadable 

 

 
 🛡️

 
 Safety Reviewer

 nvidia/nemotron-3-content-safety

 
 
 Hallucination, safety, policy checks
 Free API Multilingual Multimodal 

 
 NVIDIA native
 FREE endpoint 

 

 
 

 

 

 Fine-tune each model for its specific role using NVIDIA NeMo

 
 
 🧠

 CTO Agent — nemotron-3-super-120b-a12b
Method: LoRA · Framework: NVIDIA NeMo
 
 
 
 Training Data
Architecture Decision Records (ADRs), senior code reviews, system design docs, RFC templates
 
 Goal
Output structured JSON review reports. Always cite specific line numbers. Use consistent APPROVE/REVISE/REJECT format
 
 Key Prompt
System: "You are CTO. Review all code for scalability, security, and spec compliance. Output structured verdict."
 
 
 

 
 
 🖥️

 Frontend Dev — deepseek-v4-flash
Method: SFT (Supervised Fine-Tuning) · Dataset: UI code pairs
 
 
 
 Training Data
10K+ React/Vue component examples, Figma-to-code pairs, Tailwind CSS examples, accessibility-compliant UI
 
 Goal
Always output single-file components. Include PropTypes. Add comments. Follow your company's component naming convention
 
 Key Prompt
System: "You are a Frontend Dev. Output clean, accessible React components following [company] style guide."
 
 
 

 
 
 🗄️

 Backend Dev — deepseek-v4-pro
Method: LoRA · Dataset: API + DB patterns
 
 
 
 Training Data
REST API implementations, PostgreSQL/MongoDB schemas, auth flows (JWT/OAuth), error handling patterns
 
 Goal
Always include input validation, error codes, logging. Follow your specific DB schema conventions and naming
 
 Key Prompt
System: "You are a Backend Dev. Write Node.js/Python APIs that are secure, validated, and production-ready."
 
 
 

 
 
 🔗

 API Engineer — glm-5.1
Method: P-Tuning · Dataset: OpenAPI specs + integration docs
 
 
 
 Training Data
OpenAPI 3.0 spec examples, Postman collections, webhook patterns, OAuth flows, SDK wrappers
 
 Goal
Always generate OpenAPI spec + implementation together. Follow versioning conventions. Include retry logic
 
 Key Prompt
System: "You are an API Engineer. Design and implement REST/GraphQL endpoints with full OpenAPI documentation."
 
 
 

 
 
 🧪

 QA Engineer — mistral-small-4-119b
Method: SFT · Dataset: Test suites + bug reports
 
 
 
 Training Data
Jest/Pytest test files, Cypress E2E tests, bug report templates, edge case catalogs
 
 Goal
Output: (1) unit tests (2) edge case list (3) verdict PASS/FAIL with specific failure reasons
 
 Key Prompt
System: "You are a QA Engineer. Review code and write comprehensive tests. Output a structured test report."
 
 
 

 
 🛠️ Fine-Tuning Stack

 
 Framework:** NVIDIA NeMo + NIM microservices | 
 **Methods:** LoRA · SFT · P-Tuning

 **Infra:** NVIDIA A100/H100 GPU · NGC containers

 **Deploy:** Each fine-tuned model → NIM endpoint → called via OpenAI-compatible API