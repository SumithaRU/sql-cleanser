# Difficulties & Performance Considerations

During implementation of the `/compare` module, the following challenges were encountered:

- **Large Dataset Sizes**: Generating a full in-memory diff for millions of rows can exhaust memory; consider chunked or streaming diff approaches for scalability.
- **LLM Latency**: Ollama LLaMA 3 8B responses can approach the 120s timeout, especially with large diff payloads; minimizing prompt size or moving heavy data offline may improve reliability.
- **SQL Parsing Edge Cases**: The regex-based `INSERT_REGEX` in `ingest.py` may fail on multi-line or complex SQL; consider leveraging `sqlparse` for robust statement splitting.
- **Primary Key Ambiguity**: Automatic PK inference via LLM may misidentify keys in tables with composite or non-standard naming; adding manual override options could be useful.
- **Filesystem Overhead**: Writing and zipping many small files introduces I/O overhead; batching writes or producing a single stream may optimize performance.
