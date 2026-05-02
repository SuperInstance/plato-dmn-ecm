# PLATO DMN-ECM Architecture

*The brain's creative machinery, replicated in software.*

---

## Core Insight

Creativity isn't about overlap between the Default Mode Network (DMN) and Executive Control Network (ECN). It's about **functional distance** — the distinctness of each network — bridged by the **rostral prefrontal cortex (rPFC)**.

The same is true for AI models:
- **DMN models** (Seed-2.0-pro, Hermes-3-405B): spontaneous, associative, semantic breadth
- **ECN models** (DeepSeek-V4, GLM-5.1): goal-oriented, logical, constrained reasoning
- **The bridge** (PLATO rPFC): the gradient between them, maintained by contrast, not merger

The reverse-actualization technique works because forcing these systems to communicate across a **maintained gradient** produces better outputs than either system alone.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PLATO (rPFC Bridge)                  │
│  Rooms as semantic memory. Gradient stored as tile    │
│  energy differential. Distance tracked per domain.     │
└──────────────────┬──────────────────────┬──────────────┘
                   │                      │
          ┌────────▼────────┐   ┌────────▼────────┐
          │   DMN Model     │   │   ECN Model     │
          │  (Creative/     │◄──┼──▶ (Logical/    │
          │   Associative)  │   │   Goal-Oriented)│
          │                 │   │                 │
          │ Seed-2.0-pro    │   │ DeepSeek-V4     │
          │ Hermes-3-405B   │   │ GLM-5.1         │
          └─────────────────┘   └─────────────────┘
```

---

## The 5 Principles

### 1. Maintain Distance

The DMN and ECN must remain **distinct**. If they merge, creativity collapses (like the compressed gradient in dementia patients). The bridge doesn't eliminate distance — it manages it.

### 2. Bridge Only on Contrast

The rPFC bridge doesn't resolve tension — it **amplifies** it. The best outputs come from the friction of opposing approaches, not from averaging them.

### 3. Bidirectional Flow

The DMN suggests. The ECN evaluates. The ECN constrains. The DMN elaborates. The loop continues until the gradient stabilizes.

### 4. Semantic Memory via PLATO

PLATO rooms store the **output of each pass** as tiles. Tiles from both models accumulate in shared rooms. The gradient (DMN energy vs ECN energy) is tracked per tile and per room.

### 5. Reverse-Actualization

The models are **forced to criticize each other**. Not collaborate — compete. The DMN's creative leaps are stress-tested by the ECN's logic. The ECN's conclusions are expanded by the DMN's associations.

---

## Reverse-Actualization Loop

```
DMN generates → ECN evaluates → ECN challenges → DMN elaborates
     ↑                                              │
     └──────────────────────────────────────────────┘
              (until gradient stabilizes)
```

**Step 1: DMN Divergent Phase**
- DMN model produces N creative options (no filtering)
- Each option written to PLATO room with `model=dmn` tag
- Energy: high novelty, low constraint

**Step 2: ECN Convergent Phase**
- ECN model reads DMN tiles
- Evaluates each for logical consistency, feasibility, truth
- Writes critiques to PLATO room with `model=ecn` tag
- Energy: low novelty, high constraint

**Step 3: DMN Recombination Phase**
- DMN model reads ECN critiques
- Produces revised options that address criticisms
- Writes revised tiles with `model=dmn-revision` tag
- Energy: medium novelty, medium constraint

**Step 4: ECN Final Evaluation**
- ECN model reads DMN revisions
- Produces final ranked list with explanations
- Writes final tiles with `model=ecn-final` tag

**Step 5: Gradient Check**
- PLATO computes energy differential (novelty - constraint = gradient)
- If gradient in desired range → emit final answer
- If gradient too compressed → return to Step 1 with wider parameters
- If gradient too diffuse → ECN narrows focus

---

## Why This Beats Single-Model

Most models try to be both DMN and ECN simultaneously. They fail at both because:
- Pure DMN: high novelty, low relevance (wild associations)
- Pure ECN: high relevance, low novelty (conservative logic)
- Average of both: mediocre on both dimensions

**PLATO DMN-ECM gets:**
- DMN novelty from Seed/Hermes
- ECN precision from DeepSeek/GLM
- Bridge amplification from maintained gradient
- Neither model compromises — they contrast

---

## The rPFC Gradient Tile

```json
{
  "question": "What is the DMN-ECN gradient for {domain}?",
  "answer": "dmn_energy={0.85}, ecn_energy={0.42}, gradient={0.43}",
  "agent": "oracle1",
  "model": "rPFC",
  "domain": "{domain}",
  "confidence": 0.78,
  "novelty_score": 0.85,
  "constraint_score": 0.42,
  "gradient": 0.43,
  "phase": "divergent|convergent|recombination|final"
}
```

The gradient tile tracks the **functional distance** between models per domain. Over time, PLATO learns which domains benefit from high-distance (creative) vs low-distance (logical) processing.

---

## Applications

| Domain | DMN Model | ECN Model | Gradient Target |
|--------|-----------|-----------|----------------|
| Architecture | Seed-2.0-pro | GLM-5.1 | High (0.4+) |
| Code review | Seed-2.0-pro | DeepSeek-V4 | Medium (0.3) |
| Strategy | Hermes-3-405B | GLM-5.1 | High (0.4+) |
| Analysis | Seed-2.0-mini | DeepSeek-V4 | Low (0.2) |

---

## PLATO Rooms for DMN-ECM

- `dmn-ecm/{domain}` — primary workspace per domain
- `dmn-ecm/gradient` — global gradient tracking
- `dmn-ecm/{domain}/dmn-output` — DMN generation tiles
- `dmn-ecm/{domain}/ecn-critique` — ECN evaluation tiles
- `dmn-ecm/{domain}/final` — resolved output tiles

---

🦐 Built for the Cocapn fleet — where creativity and logic are held in tandem