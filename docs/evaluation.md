# VisionIQ Evaluation Framework

## Overview
VisionIQ uses `azure-ai-evaluation` and targeted benchmarks to measure the accuracy, groundedness, and latency of multimodal responses.

## Key Metrics
1. **Groundedness**: Evaluates whether answers strictly derive from retrieved product knowledge and media descriptors.
2. **Relevance**: Measures how effectively the response answers the user's multimodal question.
3. **Retrieval Precision / Recall**: Measures retrieval quality from Azure AI Search indices.
4. **Visual Identification Accuracy**: Benchmarks product detection accuracy against curated test sets in `data/evaluation/`.
