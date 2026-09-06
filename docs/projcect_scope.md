# Project Scope

## Domain

Education and scholarship-related government schemes in India.

## Initial Corpus

50–75 selected schemes.

## Primary Sources

1. National Scholarship Portal
2. National Government Services Portal
3. Karnataka Government Department of Minorities

## Retrieval Methods

1. BM25
2. all-MiniLM-L6-v2
3. all-mpnet-base-v2

## Benchmark

Natural-language citizen queries containing:

- Direct queries
- Colloquial queries
- Constraint-based queries
- Ambiguous queries
- Difficult queries
- Multi-constraint queries
- Hard-negative queries
- Missing-information queries
- Boundary-condition queries

## Retrieval Metrics

- Precision@K
- Recall@K
- MRR
- nDCG
- Top-1 relevance
- Top-3 relevance
- Retrieval latency

## Eligibility

Deterministic rules engine with:

- Eligible
- Not Eligible
- Insufficient Information

## Rule Management

Each rule will contain:

- Rule version
- Effective-from date
- Superseded/expiry date
- Last verified date
- Official source URL
- Update history

## Important Constraint

The LLM will not independently generate eligibility rules
or government policy information.