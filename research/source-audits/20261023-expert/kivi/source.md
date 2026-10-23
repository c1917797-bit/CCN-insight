# KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache

- Source URL: https://arxiv.org/abs/2402.02750
- Captured date: 2026-10-23
- Publisher: arXiv
- Capture mode: rendered partial (abstract excerpts; not full paper)
- Version history: [v1] Mon, 5 Feb 2024 06:06:47 UTC (3,109 KB)
[v2] Thu, 25 Jul 2024 09:16:05 UTC (3,132 KB)

## Abstract excerpts

Efficiently serving large language models (LLMs) requires batching of many requests to reduce the cost per request. Yet, with larger batch sizes and longer context lengths, the key-value (KV) cache, which stores attention keys and values to avoid re-computations, significantly increases memory demands and becomes the new bottleneck in speed and memory usage. Additionally, the loading of the KV cache causes the computational core to be idle, which limits the inference speed. A straightforward and

[Excerpt omitted]

Our findings indicate that the key cache should be quantized per-channel, i.e., group elements along the channel dimension and quantize them together. In contrast, the value cache should be quantized per-token. From this analysis, we developed a tuning-free 2bit KV cache quantization algorithm named KIVI. With hardware-friendly implementation, KIVI can enable Llama, Falcon, and Mistral models to maintain almost the same quality while using 2.6× less peak memory (including model weight). This reduction in memory usage enables up to 4× larger batch size, bringing 2.35×∼3.47× throughput on real LLM inference workload. The source code is available at this https URL.

## Capture notes

Boundary: h1.title and blockquote.abstract only. Stopped before comments, submission contacts and recommendations. Tail audited within the abstract. No inline article images in this scope; logos and page chrome excluded. Section review and independent reproduction are not claimed.
