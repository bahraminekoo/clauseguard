# ClauseGuard – AI Contract Risk Scanner

A privacy-first, retrieval-driven AI system that detects risky clauses in contracts with zero hallucinated citations.

Built with a deterministic agent architecture and fully self-hosted LLM inference.

Screenshot of dashboard here
Architecture diagram here

## Overview

ClauseGuard is an AI-assisted contract risk detection system designed to:

- Identify predefined high-risk clause categories
- Provide grounded explanations
- Reference exact clause text and page numbers
- Avoid hallucinated legal analysis

It is NOT:
- A legal advisory tool
- A contract drafting system
- An autonomous decision engine

It is a structured risk-flagging assistant.

## Design Principles

- Retrieval-First Validation
- Deterministic Risk Categories
- Source-Grounded Outputs
- Human-in-the-Loop Review
- Privacy-by-Design
- No Long-Term Document Storage

## System Architecture

PDF Upload -> Text Extraction -> Clause Chunking -> Vector Retrieval (FAISS) -> LLM Validation (Local) -> Structured JSON Output -> Risk Dashboard

## Agent-Orchestrated Pipeline

  - Orchestrator Agent (LangGraph)

  - Document Processing Agent

  - Retrieval Agent

  - Risk Validation Agent

## Retrieval-First Validation Explained

  - Embeddings retrieve candidate clauses

  - LLM validates only retrieved chunks

  - No open-ended scanning

  - Prevents hallucinated risks

## Tech Stack

## Backend
- Python 3.11
- FastAPI
- LangGraph
- FAISS
- Ollama (Local LLM Inference)

## Models
- Llama 3 8B (quantized)
- BGE embeddings

## Frontend
- Next.js
- TypeScript
- TailwindCSS

## Infrastructure
- Fully local deployment via Docker Compose
- No external API dependency

## Privacy Model

- All processing occurs locally
- No external API calls required
- No document persistence
- No training on user data
- In-memory processing only

## Quick Start

### 1. Clone repository
git clone ...
cd clauseguard

### 2. Start services
docker compose up

### 3. Access frontend
http://localhost:3000

## Requirements

- Docker
- 16GB RAM recommended
- Ollama installed

## Example Output

{
  "category": "Unlimited Liability",
  "confidence": 0.87,
  "page": 12,
  "explanation": "The clause imposes liability without limitation...",
  "clause_text": "Vendor shall be liable for all damages..."
}

## Model Abstraction

ClauseGuard supports interchangeable LLM providers:

- LocalProvider (Ollama)
- Future API providers

The architecture separates orchestration logic from model implementation,
making the system provider-agnostic.

## Testing

- Unit tests for chunking and retrieval
- Schema validation tests
- API endpoint tests
- Deterministic validation output checks

## Roadmap

- Multi-document comparison
- Severity scoring
- Jurisdiction-aware risk ontology
- SaaS deployment mode
- API-based inference support



