# SparseGPT: Massive Language Models Can Be Accurately Pruned in One-Shot

- Source URL: https://arxiv.org/abs/2301.00774
- Captured date: 2026-10-23
- Publisher: arXiv
- Capture mode: rendered partial (abstract excerpts; not full paper)
- Version history: [v1] Mon, 2 Jan 2023 17:48:56 UTC (183 KB)
[v2] Wed, 18 Jan 2023 17:13:49 UTC (183 KB)
[v3] Wed, 22 Mar 2023 12:33:46 UTC (242 KB)

## Abstract excerpts

We show for the first time that large-scale generative pretrained transformer (GPT) family models can be pruned to at least 50% sparsity in one-shot, without any retraining, at minimal loss of accuracy. This is achieved via a new pruning method called SparseGPT, specifically designed to work efficiently and accurately on massive GPT-family models. We can execute SparseGPT on the largest available open-source models, OPT-175B and BLOOM-176B, in under 4.5 hours, and can reach 60% unstructured sparsity with negligible increase in perplexity: remarkably, more than 100 billion weights from these models can be ignored at inference time. SparseGPT generalizes to semi-structured (2:4 and 4:8) patterns, and is compatible with weight quantization approaches. The code is available at: this https URL.

## Capture notes

Boundary: h1.title and blockquote.abstract only. Stopped before comments, submission contacts and recommendations. Tail audited within the abstract. No inline article images in this scope; logos and page chrome excluded. Section review and independent reproduction are not claimed.
