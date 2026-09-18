# Product Identification Evaluation Benchmark (Day 4)

**Execution Date**: 2026-09-17 | **Model**: OpenAI CLIP (`clip-ViT-B-32`) | **Index**: Azure AI Search `product-catalog`

## Executive Metrics

- **Top-1 Accuracy (In-Catalog)**: **65.0%** (13/20)
- **Top-3 Accuracy (In-Catalog)**: **80.0%** (16/20)
- **Out-of-Catalog Rejection Rate**: **100.0%** (5/5)
- **Mean Response Latency**: **3073.11 ms**
- **Failure / Error Rate**: **0.0%**

## Detailed Per-Image Evaluation Results

| Test ID | Test Image Description | Expected GT | Top-1 Match | Top-1 Score | Top-1 Hit | Top-3 Hit | Confident? | Latency (ms) |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| T01 | Sony WH-1000XM5 (Catalog Photo) | `P001` | [P001] Sony Sony WH-1000XM5 | 1.0000 | ✅ | ✅ | ✅ True | 23123.04 ms |
| T02 | Sony WH-1000XM5 (Secondary Angle) | `P001` | [P004] Sennheiser Sennheiser Momentum 4 Wireless | 0.9397 | ❌ | ✅ | ✅ True | 1738.59 ms |
| T03 | Bose QuietComfort Ultra | `P002` | [P002] Bose Bose QuietComfort Ultra | 1.0000 | ✅ | ✅ | ✅ True | 1865.62 ms |
| T04 | Apple AirPods Max | `P003` | [P003] Apple Apple AirPods Max | 1.0000 | ✅ | ✅ | ✅ True | 1644.55 ms |
| T05 | Sennheiser Momentum 4 | `P004` | [P004] Sennheiser Sennheiser Momentum 4 Wireless | 1.0000 | ✅ | ✅ | ✅ True | 1540.3 ms |
| T06 | Audio-Technica ATH-M50xBT2 | `P005` | [P005] Audio-Technica Audio-Technica ATH-M50xBT2 | 1.0000 | ✅ | ✅ | ✅ True | 1514.51 ms |
| T07 | Bowers & Wilkins Px7 S2e | `P006` | [P006] Bowers & Wilkins Bowers & Wilkins Px7 S2e | 1.0000 | ✅ | ✅ | ✅ True | 1564.72 ms |
| T08 | Herman Miller Aeron Chair | `P007` | [P007] Herman Miller Herman Miller Aeron Chair | 1.0000 | ✅ | ✅ | ✅ True | 1942.97 ms |
| T09 | Steelcase Gesture | `P008` | [P008] Steelcase Steelcase Gesture | 1.0000 | ✅ | ✅ | ✅ True | 1999.91 ms |
| T10 | Secretlab Titan Evo | `P009` | [P009] Secretlab Secretlab Titan Evo | 1.0000 | ✅ | ✅ | ✅ True | 2164.46 ms |
| T11 | Autonomous ErgoChair Pro | `P010` | [P010] Autonomous Autonomous ErgoChair Pro | 1.0000 | ✅ | ✅ | ✅ True | 2219.38 ms |
| T12 | Haworth Fern Chair | `P012` | [P012] Haworth Haworth Fern | 0.8811 | ✅ | ✅ | ✅ True | 1695.74 ms |
| T13 | Humanscale Freedom Chair | `P013` | [P011] IKEA IKEA Markus | 1.0000 | ❌ | ✅ | ✅ True | 1768.55 ms |
| T14 | Nike Air Zoom Pegasus 40 | `P011` | [P014] Nike Nike Air Max 270 | 1.0000 | ❌ | ❌ | ✅ True | 2267.16 ms |
| T15 | Nike Air Max 270 | `P014` | [P019] Salomon Salomon XT-6 | 0.8173 | ❌ | ✅ | ○ False | 1696.18 ms |
| T16 | Adidas Ultraboost Light | `P015` | [P001] Sony Sony WH-1000XM5 | 0.8502 | ❌ | ❌ | ✅ True | 1917.97 ms |
| T17 | New Balance 990v6 | `P016` | [P016] New Balance New Balance 990v6 | 1.0000 | ✅ | ✅ | ✅ True | 2161.46 ms |
| T18 | On Running Cloudmonster | `P017` | [P017] On Running On Cloudmonster | 1.0000 | ✅ | ✅ | ✅ True | 2762.9 ms |
| T19 | Hoka Clifton 9 | `P018` | [P016] New Balance New Balance 990v6 | 0.8267 | ❌ | ❌ | ○ False | 1662.91 ms |
| T20 | Salomon XT-6 | `P019` | [P018] Hoka Hoka Clifton 9 | 1.0000 | ❌ | ❌ | ✅ True | 1679.78 ms |
| T21 | Mechanical Keyboard (Out-of-Catalog) | `OUT_OF_CATALOG` | [P007] Herman Miller Herman Miller Aeron Chair | 0.8296 | — | — | ○ False | 5854.2 ms |
| T22 | Coffee Espresso Machine (Out-of-Catalog) | `OUT_OF_CATALOG` | [P008] Steelcase Steelcase Gesture | 0.7505 | — | — | ○ False | 6660.78 ms |
| T23 | DSLR Camera Lens (Out-of-Catalog) | `OUT_OF_CATALOG` | [P001] Sony Sony WH-1000XM5 | 0.8055 | — | — | ○ False | 1592.2 ms |
| T24 | Ceramic Coffee Mug (Out-of-Catalog) | `OUT_OF_CATALOG` | [P008] Steelcase Steelcase Gesture | 0.8233 | — | — | ○ False | 1872.96 ms |
| T25 | Bicycle Road Frame (Out-of-Catalog) | `OUT_OF_CATALOG` | [P012] Haworth Haworth Fern | 0.7941 | — | — | ○ False | 1916.92 ms |
