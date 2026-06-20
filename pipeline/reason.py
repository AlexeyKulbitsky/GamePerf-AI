"""Evidence bundle + KB matches -> ranked hypotheses.

Single-shot prompt to a local model via Ollama (qwen2.5:7b-instruct).
Primary output is JSON, hypotheses with refs back to the evidence; the
markdown report is rendered from that. Hypotheses are meant to be
verified, not trusted.
"""
