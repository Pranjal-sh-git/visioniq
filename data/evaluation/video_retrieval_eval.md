# Video Temporal Retrieval & Grounded QA Evaluation Benchmark (Day 4)

**Execution Date**: 2026-09-17 | **Model**: `gpt-5-mini` + Whisper ASR | **Index**: Azure AI Search `video-segments`

## Executive Metrics

- **Timestamp Retrieval Accuracy**: **60.0%** (9/15)
- **Grounded QA Correctness**: **60.0%** (9/15)
- **Hallucination Rate**: **0.0%** (0/15)
- **Mean Response Latency**: **4598.17 ms**
- **Pipeline Failure Rate**: **0.0%**

## Detailed Per-Question Evaluation Results

| Q ID | Question | Expected Segment | Retrieved Interval | Timestamp Correct? | Classification | Latency (ms) |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: |
| VQ01 | How many people can fit in the audience in this area? | `0.0s - 26.0s` | `0.0s - 26.0s` | ✅ Correct | **Correct** | 16430.11 ms |
| VQ02 | What is the speaker's name in the video? | `0.0s - 26.0s` | `NONE` | ❌ Incorrect | **Incorrect (False Negative)** | 2205.04 ms |
| VQ03 | Why did the speaker pick this specific area? | `0.0s - 26.0s` | `NONE` | ❌ Incorrect | **Incorrect (False Negative)** | 2141.85 ms |
| VQ04 | What is the purpose of this video recording? | `0.0s - 26.0s` | `NONE` | ❌ Incorrect | **Incorrect (False Negative)** | 2868.07 ms |
| VQ05 | Does the speaker mention having standing room for speeches? | `0.0s - 26.0s` | `0.0s - 26.0s` | ✅ Correct | **Correct** | 7148.7 ms |
| VQ06 | What did the speaker say about recommendations or feedback? | `20.0s - 31.0s` | `NONE` | ❌ Incorrect | **Incorrect (False Negative)** | 2506.39 ms |
| VQ07 | How is the audio and video quality according to the speaker? | `0.0s - 26.0s` | `NONE` | ❌ Incorrect | **Incorrect (False Negative)** | 2422.49 ms |
| VQ08 | Does the speaker hope that everything sounds and looks good? | `0.0s - 26.0s` | `NONE` | ❌ Incorrect | **Incorrect (False Negative)** | 2627.76 ms |
| VQ09 | What is the speaker testing in the area? | `0.0s - 26.0s` | `0.0s - 26.0s` | ✅ Correct | **Correct** | 6109.81 ms |
| VQ10 | Can the speaker comfortably deliver speeches in this room? | `0.0s - 26.0s` | `0.0s - 26.0s` | ✅ Correct | **Correct** | 8129.13 ms |
| VQ11 | What did the speaker say about deep sea scuba diving in Antarctica? | `NONE` | `NONE` | ✅ Correct | **Correctly Refused (Honest)** | 2272.14 ms |
| VQ12 | What are the horsepower specs of the Tesla Cybertruck mentioned? | `NONE` | `NONE` | ✅ Correct | **Correctly Refused (Honest)** | 4150.67 ms |
| VQ13 | What is the recipe for homemade pasta shown in the video? | `NONE` | `NONE` | ✅ Correct | **Correctly Refused (Honest)** | 2914.37 ms |
| VQ14 | What was the stock market price of Apple in the video? | `NONE` | `NONE` | ✅ Correct | **Correctly Refused (Honest)** | 4634.02 ms |
| VQ15 | What is the battery life of the wireless headphones tested in this video? | `NONE` | `NONE` | ✅ Correct | **Correctly Refused (Honest)** | 2412.0 ms |
