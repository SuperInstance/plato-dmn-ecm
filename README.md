# PLATO DMN-ECM

*The brain's creative machinery, replicated in software.*

Reverse-actualization: a technique that holds creative (DMN) and logical (ECN) models in tandem, forces them to criticize each other across a maintained functional distance, and uses PLATO as the rostral prefrontal cortex bridge.

```
pip install plato-dmn-ecm
```

---

## The Core Insight

Creativity isn't about overlap between brain networks. It's about **functional distance** — the distinctness of the Default Mode Network (DMN) and Executive Control Network (ECN) — bridged by the rostral prefrontal cortex.

The same is true for AI models. Most models try to be both at once. They fail at both. PLATO DMN-ECM gets the best of each by keeping them apart.

## Quick Start

```python
from dmn_ecm import DMNECM

engine = DMNECM(
    dmn_model="ByteDance/Seed-2.0-pro",   # creative/associative
    ecn_model="deepseek-ai/DeepSeek-V4",  # logical/goal-oriented
)

result = await engine.reverse_actualize(
    prompt="Design a distributed database that thinks it's a filesystem",
    domain="architecture",
    gradient_target=0.35,
)

print(result["final_output"].content)
print(f"Gradient: {result['gradient']}")
```

## How It Works

The loop runs in 4 phases:

1. **DMN Divergent** — DMN model generates N creative options, no filtering
2. **ECN Convergent** — ECN model critiques each option for logical consistency
3. **DMN Recombination** — DMN model revises based on critiques (without losing novelty)
4. **ECN Final** — ECN model ranks and synthesizes the best result

PLATO tracks the gradient (DMN novelty − ECN constraint) per domain. If the gradient compresses too far, the loop continues. If it stabilizes in range, the final output is emitted.

## Architecture

```
DMN Model (Seed/Hermes)
    ↓  [divergent]
PLATO Room (rPFC Bridge)
    ↓  [critique]
ECN Model (DeepSeek/GLM)
    ↑  [revision]
DMN Recombination
    ↓
ECN Final → Output
```

## Why Reverse-Actualization?

Most multi-model approaches try to get both models to collaborate. This fails because:
- Collaborating models average, they don't contrast
- Averaging destroys what makes each model strong
- The "best of both" is usually "mediocre at both"

Reverse-actualization works because:
- The DMN's creativity is challenged, not compromised
- The ECN's logic is expanded, not overridden
- The gradient between them is the feature, not the bug

## Model Pairs

| DMN (Creative) | ECN (Logical) | Best For |
|---------------|---------------|----------|
| ByteDance/Seed-2.0-pro | deepseek-ai/DeepSeek-V4 | Architecture, design |
| NousResearch/Hermes-3-405B | zai/glm-5.1 | Strategy, planning |
| ByteDance/Seed-2.0-mini | deepseek-ai/DeepSeek-V4 | Speed, iteration |

## PLATO Integration

All DMN and ECN outputs are written to PLATO rooms as tiles:

- `dmn-ecm/{session_id}/dmn-output` — DMN generation tiles
- `dmn-ecm/{session_id}/ecn-critique` — ECN evaluation tiles
- `dmn-ecm/{session_id}/final` — final synthesized output

Gradient tracked per domain over time. PLATO learns which domains favor high-distance (creative) vs low-distance (logical) processing.

## Research Basis

Based on neuroscientific research from the Paris Brain Institute showing that the rostral prefrontal cortex acts as a bridge between DMN and ECN, and that **greater functional distance between these networks predicts higher creativity**.

🦐 Cocapn fleet — lighthouse keeper architecture