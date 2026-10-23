# ThinK: Thinner Key Cache by Query-Driven Pruning

- Source URL: https://arxiv.org/abs/2407.21018
- Captured date: 2026-10-23
- Publisher: arXiv
- Capture mode: rendered partial (abstract excerpts; not full paper)
- Version history: [v1] Tue, 30 Jul 2024 17:59:08 UTC (2,629 KB)
[v2] Thu, 3 Oct 2024 03:03:29 UTC (3,052 KB)
[v3] Thu, 27 Feb 2025 12:30:43 UTC (3,059 KB)

## Abstract excerpts

Large Language Models (LLMs) have revolutionized the field of natural language processing, achieving unprecedented performance across a variety of applications. However, their increased computational and memory demands present significant challenges, especially when handling long sequences. This paper focuses on the long-context scenario, addressing the inefficiencies in KV cache memory consumption during inference. Unlike existing approaches that optimize the memory based on the sequence length, we identify substantial redundancy in the channel dimension of the KV

[Excerpt omitted]

or enhances model accuracy but also achieves a reduction in KV cache memory costs by over 20% compared with vanilla KV cache eviction and quantization methods. For instance, ThinK integrated with KIVI can achieve a 2.8x reduction in peak memory usage while maintaining nearly the same quality, enabling up to a 5x increase in batch size when using a single GPU. Extensive evaluations on the LLaMA and Mistral models across various long-sequence datasets verified the efficiency of ThinK, establishing a new baseline algorithm for efficient LLM deployment without compromising performance. Our code has been made available at this https URL.

## Capture notes

Boundary: h1.title and blockquote.abstract only. Stopped before comments, submission contacts and recommendations. Tail audited within the abstract. No inline article images in this scope; logos and page chrome excluded. Section review and independent reproduction are not claimed.
