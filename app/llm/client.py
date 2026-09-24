"""
Sends a system prompt and a user prompt to the LLM and returns its response.

For now this returns a fixed, predictable response instead of calling a
real model. This lets us test the guardrail logic without needing Ollama
running. The real Ollama call will replace the body of this function later.
"""
from __future__ import annotations


def query_llm(system_prompt: str, prompt: str) -> str:
    return (
        "DISPATCH RECOMMENDATION\n"
        "------------------------\n"
        f"{prompt}\n"
        "Action: Units dispatched per validated incident data."
    )
