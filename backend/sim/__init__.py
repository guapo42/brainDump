"""Simulation test harness (specs/02).

Deterministic, no-Docker, no-LLM validation of backend logic. Depends only on the
shared domain models + Store Protocol. Must never import infra (neo4j, chromadb,
openai, instructor, fastapi, connectors) — enforced by import-linter.
"""
