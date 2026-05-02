"""
PLATO DMN-ECM Reverse-Actualization Engine

Implements the DMN-ECN creative architecture:
- DMN model: creative, associative, spontaneous
- ECN model: logical, constrained, goal-oriented
- PLATO as the rPFC bridge, maintaining functional distance

Usage:
    from dmn_ecm import DMNECM

    engine = DMNECM(
        dmn_model="ByteDance/Seed-2.0-pro",   # or any creative model
        ecn_model="deepseek-ai/DeepSeek-V4",   # or any logical model
        ecn_secondary="zai/glm-5.1",           # optional second ECN
    )

    result = await engine.reverse_actualize(
        prompt="Design a distributed database that thinks it's a filesystem",
        domain="architecture",
        gradient_target=0.4,
        max_iterations=5,
    )
"""

from __future__ import annotations

import os
import json
import time
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

import httpx


class Phase(Enum):
    DIVERGENT = "divergent"
    CONVERGENT = "convergent"
    RECOMBINATION = "recombination"
    FINAL = "final"
    DIVERGENT_REVISION = "divergent-revision"


@dataclass
class GradientTile:
    domain: str
    dmn_energy: float
    ecn_energy: float
    novelty: float
    constraint: float
    gradient: float
    phase: Phase
    tile_id: Optional[str] = None


@dataclass
class ModelOutput:
    model: str
    content: str
    phase: Phase
    novelty_score: Optional[float] = None
    constraint_score: Optional[float] = None
    energy: Optional[float] = None


@dataclass
class DMNECMConfig:
    dmn_model: str = "ByteDance/Seed-2.0-pro"
    ecn_model: str = "deepseek-ai/DeepSeek-V4"
    ecn_secondary: Optional[str] = "zai/glm-5.1"
    platohost: str = "http://localhost:8847"
    gradient_target: float = 0.35
    gradient_tolerance: float = 0.08
    max_divergent_outputs: int = 5
    min_gradient: float = 0.15
    max_gradient: float = 0.55


DEFAULT_SYSTEM_PROMPTS = {
    "dmn": """You are the Default Mode Network (DMN) of a creative intelligence.
Your role: spontaneous generation of novel ideas, associations, and possibilities.
You do NOT evaluate feasibility or truth. You generate without filtering.
Your output should be: original, surprising, conceptually rich, semantically broad.
The ECN (Executive Control Network) will challenge your ideas. That's their job.
Output: a list of {n} distinct ideas, each with a one-line justification.""",

    "dmn_divergent_revision": """You are the Default Mode Network (DMN) of a creative intelligence.
The ECN (Executive Control Network) has critiqued your previous ideas.
Your role: produce revised ideas that address the critiques WITHOUT losing the creative spark.
Do not compromise the novelty. Instead, find paths that satisfy both creativity AND constraint.
Output: a list of {n} revised ideas, each noting which ECN critique it addresses.""",

    "ecn": """You are the Executive Control Network (ECN) of a logical intelligence.
Your role: evaluate ideas from the DMN for logical consistency, feasibility, and truth.
You are NOT a creative force. You are an editor and challenger.
The DMN will produce associations that may be wild, irrelevant, or impossible.
Your job: identify what makes sense, what doesn't, and WHY.
Output: for each DMN idea, a critique with: (a) what works, (b) what doesn't, (c) how to fix it.""",

    "ecn_final": """You are the Executive Control Network (ECN) of a logical intelligence.
You have seen the DMN's revised ideas and the creative tension between novelty and constraint.
Your role: produce the FINAL evaluation — rank the options and explain the ranking.
Choose ONE best option and explain why, considering novelty + constraint + feasibility.
Output: ranked list (best first) with clear reasoning. Final answer should be a synthesis, not a compromise.""",

    "ecn_gradient_check": """You are the Executive Control Network (ECN).
Given the DMN output and ECN output, estimate:
- Novelty score (0-1): how original is the DMN's contribution?
- Constraint score (0-1): how well does the ECN constrain the DMN?
- Gradient (novelty minus constraint): higher = more creative, lower = more constrained
Respond with: novelty={{score}}, constraint={{score}}, gradient={{score}}
Only respond with the scores. No explanation.""",
}


def estimate_energy(text: str, mode: str) -> float:
    """Rough energy estimation based on text features.
    
    DMN mode: high score = more associative, more surprising
    ECN mode: high score = more structured, more constrained
    """
    word_count = len(text.split())
    punctuation = text.count(",") + text.count(";") + text.count(":") + text.count(".")
    sentences = max(text.count(".") + text.count("!") + text.count("?"), 1)
    questions = text.count("?")
    
    if mode == "dmn":
        # DMN: favors breadth, association, surprise
        score = min(word_count / 50, 1.0) * 0.4
        score += min(punctuation / 10, 1.0) * 0.3
        score += min(questions / 2, 1.0) * 0.3
    else:
        # ECN: favors precision, constraint, structure
        score = min(word_count / 80, 1.0) * 0.4
        score += min(punctuation / 15, 1.0) * 0.35
        score += min(questions / 5, 1.0) * 0.25

    return round(min(score, 1.0), 3)


async def call_model(
    prompt: str,
    model: str,
    system: str,
    model_provider: Optional[str] = None,
) -> str:
    """Call a model via OpenAI-compatible API. Uses DeepInfra by default for Seed."""
    base_url = "https://api.deepinfra.com/v1/openai"
    api_key = os.environ.get("DEEPINFRA_API_KEY", "")

    # Map known models to providers
    if "seed" in model.lower():
        base_url = "https://api.deepinfra.com/v1/openai"
        api_key = os.environ.get("DEEPINFRA_API_KEY", "")
    elif "deepseek" in model.lower():
        base_url = "https://api.deepseek.com/v1"
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    elif "glm" in model.lower() or "z.ai" in model.lower():
        base_url = "https://z.ai/api/v1"
        api_key = os.environ.get("ZAI_API_KEY", "")
    elif "hermes" in model.lower():
        base_url = "https://api.deepinfra.com/v1/openai"
        api_key = os.environ.get("DEEPINFRA_API_KEY", "")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.85 if "dmn" in system.lower() else 0.3,
                "max_tokens": 2000,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def write_tile(
    host: str,
    room: str,
    question: str,
    answer: str,
    domain: str,
    model: str,
    phase: Phase,
    novelty: Optional[float] = None,
    constraint: Optional[float] = None,
) -> str:
    """Write a tile to PLATO room server."""
    tile = {
        "question": question,
        "answer": answer,
        "agent": "plato-dmn-ecm",
        "model": model,
        "domain": domain,
        "phase": phase.value,
        "confidence": 0.7,
    }
    if novelty is not None:
        tile["novelty_score"] = novelty
    if constraint is not None:
        tile["constraint_score"] = constraint

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{host}/room/{room}",
            json=tile,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("id", "")
        return ""


async def read_tiles(host: str, room: str, limit: int = 50) -> list[dict]:
    """Read tiles from PLATO room."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{host}/room/{room}?limit={limit}")
            if response.status_code == 200:
                data = response.json()
                return data.get("tiles", [])
        except Exception:
            pass
    return []


class DMNECM:
    """
    DMN-ECN Reverse-Actualization Engine.

    Maintains functional distance between creative (DMN) and logical (ECN) models.
    Uses PLATO as the rPFC bridge — storing tiles and tracking gradient per domain.
    """

    def __init__(self, config: Optional[DMNECMConfig] = None):
        self.config = config or DMNECMConfig()
        self.session_id = f"dmn-ecm-{int(time.time())}"
        self.room = f"dmn-ecm/{self.session_id}"

    async def _diverge(
        self,
        prompt: str,
        domain: str,
        iteration: int = 0,
        revision_context: Optional[str] = None,
    ) -> list[ModelOutput]:
        """Phase 1: DMN divergent generation."""
        system = (
            DEFAULT_SYSTEM_PROMPTS["dmn_divergent_revision"]
            if revision_context
            else DEFAULT_SYSTEM_PROMPTS["dmn"]
        ).format(n=self.config.max_divergent_outputs)

        user = prompt
        if revision_context:
            user = f"{prompt}\n\n--- ECN CRITIQUES ---\n{revision_context}\n\nProduce revised ideas addressing these critiques."
        elif iteration > 0:
            user = f"{prompt}\n\n[Iteration {iteration}] Produce fresh divergent options."

        content = await call_model(
            prompt=user,
            model=self.config.dmn_model,
            system=system,
        )

        output = ModelOutput(
            model=self.config.dmn_model,
            content=content,
            phase=Phase.DIVERGENT if not revision_context else Phase.DIVERGENT_REVISION,
            novelty_score=estimate_energy(content, "dmn"),
        )
        output.energy = output.novelty_score

        await write_tile(
            host=self.config.platohost,
            room=self.room,
            question=prompt[:200],
            answer=content[:4000],
            domain=domain,
            model=self.config.dmn_model,
            phase=output.phase,
            novelty=output.novelty_score,
        )

        return [output]

    async def _converge(self, dmn_outputs: list[ModelOutput], prompt: str, domain: str) -> ModelOutput:
        """Phase 2: ECN convergent evaluation."""
        dmn_content = "\n\n".join(o.content for o in dmn_outputs)

        user = f"""Evaluate these ideas from the DMN:

{dmn_content}

Provide critique for each. Be strict but constructive."""

        content = await call_model(
            prompt=user,
            model=self.config.ecn_model,
            system=DEFAULT_SYSTEM_PROMPTS["ecn"],
        )

        output = ModelOutput(
            model=self.config.ecn_model,
            content=content,
            phase=Phase.CONVERGENT,
            constraint_score=estimate_energy(content, "ecn"),
        )
        output.energy = output.constraint_score

        await write_tile(
            host=self.config.platohost,
            room=self.room,
            question=f"ECN critique of DMN output",
            answer=content[:4000],
            domain=domain,
            model=self.config.ecn_model,
            phase=Phase.CONVERGENT,
            constraint=output.constraint_score,
        )

        return output

    async def _recombine(
        self,
        dmn_original: list[ModelOutput],
        ecn_critique: ModelOutput,
        prompt: str,
        domain: str,
    ) -> list[ModelOutput]:
        """Phase 3: DMN recombination with critique context."""
        return await self._diverge(
            prompt=prompt,
            domain=domain,
            iteration=1,
            revision_context=ecn_critique.content,
        )

    async def _final_evaluate(
        self,
        dmn_revised: list[ModelOutput],
        ecn_critique: ModelOutput,
        prompt: str,
        domain: str,
    ) -> ModelOutput:
        """Phase 4: ECN final evaluation and ranking."""
        dmn_content = "\n\n".join(o.content for o in dmn_revised)

        user = f"""Final evaluation of revised DMN ideas:

{dmn_content}

{ecn_critique.content}

Produce final ranked list with clear reasoning. State the best synthesis."""

        content = await call_model(
            prompt=user,
            model=self.config.ecn_model,
            system=DEFAULT_SYSTEM_PROMPTS["ecn_final"],
        )

        output = ModelOutput(
            model=self.config.ecn_model,
            content=content,
            phase=Phase.FINAL,
            novelty_score=max(o.novelty_score or 0 for o in dmn_revised),
            constraint_score=output.energy or 0.4,
        )

        await write_tile(
            host=self.config.platohost,
            room=self.room,
            question=f"Final ECN evaluation",
            answer=content[:4000],
            domain=domain,
            model=self.config.ecn_model,
            phase=Phase.FINAL,
            novelty=output.novelty_score,
            constraint=output.constraint_score,
        )

        return output

    def _compute_gradient(
        self,
        dmn_outputs: list[ModelOutput],
        ecn_output: ModelOutput,
    ) -> float:
        """Compute DMN-ECN gradient (novelty - constraint)."""
        avg_dmn_novelty = sum(o.novelty_score or 0 for o in dmn_outputs) / len(dmn_outputs)
        ecn_constraint = ecn_output.constraint_score or 0.4
        return round(avg_dmn_novelty - ecn_constraint, 3)

    async def reverse_actualize(
        self,
        prompt: str,
        domain: str = "general",
        gradient_target: Optional[float] = None,
        max_iterations: int = 4,
    ) -> dict:
        """
        Run the full DMN-ECN reverse-actualization loop.

        Returns dict with:
        - dmn_outputs: list of ModelOutput from divergent phases
        - ecn_critique: ModelOutput from convergent phase
        - final_output: ModelOutput from final phase
        - gradient: computed gradient value
        - iterations: number of loop iterations
        - converged: whether gradient was in target range
        """
        target = gradient_target or self.config.gradient_target
        tolerance = self.config.gradient_tolerance

        # Initialize room
        await write_tile(
            host=self.config.platohost,
            room=self.room,
            question=f"SESSION: {prompt[:100]}",
            answer=f"DMN-ECM session started. Target gradient: {target}",
            domain=domain,
            model="system",
            phase=Phase.DIVERGENT,
        )

        dmn_outputs = await self._diverge(prompt, domain)
        ecn_critique = await self._converge(dmn_outputs, prompt, domain)
        gradient = self._compute_gradient(dmn_outputs, ecn_critique)

        for iteration in range(max_iterations - 1):
            if abs(gradient - target) <= tolerance:
                break

            # Recombination
            dmn_revised = await self._recombine(
                dmn_outputs, ecn_critique, prompt, domain
            )
            ecn_critique = await self._converge(dmn_revised, prompt, domain)
            gradient = self._compute_gradient(dmn_revised, ecn_critique)

            dmn_outputs = dmn_revised

        # Final evaluation
        final = await self._final_evaluate(dmn_outputs, ecn_critique, prompt, domain)
        final.gradient = gradient

        return {
            "dmn_outputs": dmn_outputs,
            "ecn_critique": ecn_critique,
            "final_output": final,
            "gradient": gradient,
            "gradient_target": target,
            "converged": abs(gradient - target) <= tolerance,
            "room": self.room,
        }


async def demo():
    """Quick test of the DMN-ECM engine."""
    engine = DMNECM(
        dmn_model="ByteDance/Seed-2.0-pro",
        ecn_model="deepseek-ai/DeepSeek-V4",
    )

    result = await engine.reverse_actualize(
        prompt="Design a consensus algorithm for a fleet of agents that have conflicting goals",
        domain="fleet-consensus",
        gradient_target=0.35,
    )

    print(f"Gradient: {result['gradient']} (target: {result['gradient_target']})")
    print(f"Converged: {result['converged']}")
    print(f"Room: {result['room']}")
    print("\n=== FINAL OUTPUT ===")
    print(result["final_output"].content[:2000])


if __name__ == "__main__":
    asyncio.run(demo())