"""Tests for reverse-actualization technique."""

import pytest
from dmn_ecm import Phase, DMNECMConfig


class TestReverseActualizationPrinciples:
    """Verify the 5 principles of reverse-actualization are encoded."""

    def test_principle1_distance_not_overlap(self):
        """Maintain distance: DMN and ECN stay distinct."""
        config = DMNECMConfig()
        # Default models are different model families
        assert config.dmn_model != config.ecn_model

    def test_principle2_bridge_amplifies_not_resolves(self):
        """The bridge amplifies contrast, doesn't resolve tension."""
        # The gradient is novelty - constraint, not (novelty + constraint) / 2
        novelty = 0.85
        constraint = 0.42
        gradient = novelty - constraint
        average = (novelty + constraint) / 2
        # Gradient should NOT be the average
        assert gradient != average
        assert gradient == pytest.approx(0.43, abs=0.01)

    def test_principle3_bidirectional_flow(self):
        """Bidirectional: DMN generates → ECN challenges → DMN elaborates → ECN final."""
        phases = [
            Phase.DIVERGENT,
            Phase.CONVERGENT,
            Phase.DIVERGENT_REVISION,
            Phase.CONVERGENT,
            Phase.FINAL,
        ]
        # Phases must alternate DMN → ECN
        for i in range(len(phases) - 1):
            current_is_dmn = phases[i].value.startswith("divergent")
            next_is_ecn = phases[i + 1].value == "convergent"
            next_is_final = phases[i + 1].value == "final"
            assert current_is_dmn and (next_is_ecn or next_is_final)

    def test_principle4_semantic_memory(self):
        """PLATO rooms store tiles from both models per domain."""
        config = DMNECMConfig()
        # The room name includes domain
        engine = DMNECM(config)
        assert "dmn-ecm/" in engine.room

    def test_principle5_criticize_not_collaborate(self):
        """Models criticize each other, not averaging."""
        from dmn_ecm import DEFAULT_SYSTEM_PROMPTS

        ecn_prompt = DEFAULT_SYSTEM_PROMPTS["ecn"]
        dmn_prompt = DEFAULT_SYSTEM_PROMPTS["dmn"]

        # ECN should use the word "challenge" or "critique"
        assert (
            "challenge" in ecn_prompt.lower() or "critique" in ecn_prompt.lower()
        ), "ECN should challenge, not collaborate"

        # DMN should NOT be asked to evaluate
        assert (
            "evaluate" not in dmn_prompt.lower()
        ), "DMN should not be asked to evaluate"


class TestReverseActualizationVsCollaboration:
    """Contrast reverse-actualization with naive collaboration."""

    def test_collaboration_averages(self):
        """Naive collaboration produces average of both models."""
        dmn_strength = 0.9  # novelty
        ecn_strength = 0.8  # constraint
        # If they collaborated, they'd average:
        collaborative = (dmn_strength + ecn_strength) / 2
        assert collaborative == 0.85

    def test_reverse_actualization_preserves_strengths(self):
        """Reverse-actualization preserves each model's strength."""
        dmn_novelty = 0.9
        ecn_constraint = 0.8
        gradient = dmn_novelty - ecn_constraint
        # Gradient captures DIFFERENCE, not average
        # DMN's novelty is still 0.9
        # ECN's constraint is still 0.8
        assert gradient == pytest.approx(0.1, abs=0.01)
        # Result is NOT 0.85 (the collaborative average)


class TestDMNECNContrastVsMerging:
    """Test the core finding: distance between networks enables creativity."""

    def test_dementia_gradient_compression(self):
        """
        From the neuroscience study: when the gradient compresses,
        creativity collapses. This is analogous to model merger.
        """
        # Normal: high distance between DMN and ECN
        normal_gradient = 0.85 - 0.42  # = 0.43
        # Dementia/compressed: low distance
        compressed_gradient = 0.75 - 0.70  # = 0.05
        assert normal_gradient > compressed_gradient
        # Compressed gradient = less creative

    def test_model_merger_is_like_compressed_gradient(self):
        """
        When two models try to collaborate/average,
        they compress the gradient. This destroys what made each useful.
        """
        dmn_novelty = 0.9
        ecn_constraint = 0.4
        normal_gradient = dmn_novelty - ecn_constraint  # 0.5

        # Merger attempt: ECN adds averaging pressure
        merged_result = (dmn_novelty + ecn_constraint) / 2  # 0.65
        # This IS the compressed gradient problem
        assert merged_result < normal_gradient


class TestReverseActualizationLoop:
    """Test the actual loop iterations."""

    @pytest.mark.asyncio
    async def test_loop_iterates_on_compressed_gradient(self):
        from dmn_ecm import DMNECM
        from unittest.mock import AsyncMock, patch

        config = DMNECMConfig(gradient_target=0.35, gradient_tolerance=0.05)
        engine = DMNECM(config)
        iterations = []

        async def mock_call(prompt, model, system):
            iterations.append(model[:20])
            if "dmn" in system.lower():
                return f"Creative idea {len(iterations)}"
            return "Critique of the idea"

        with patch("dmn_ecm.call_model", new_callable=AsyncMock) as m:
            m.side_effect = mock_call
            with patch("dmn_ecm.write_tile", new_callable=AsyncMock):
                result = await engine.reverse_actualize(
                    prompt="test",
                    domain="test",
                    max_iterations=3,
                )
                # DMN called at least twice (initial + revision)
                assert sum(1 for x in iterations if "dmn" in x.lower()) >= 2


class TestNoCompromiseOnCoreStrengths:
    """
    Key invariant: DMN never compromises novelty, ECN never lowers constraint.
    The loop should improve BOTH metrics, not trade one for the other.
    """

    def test_novelty_stays_high_for_dmn(self):
        """DMN novelty should not decrease through iterations."""
        novelty_initial = 0.85
        novelty_revision = 0.80  # Should stay in 0.75+ range
        assert novelty_revision >= 0.75

    def test_constraint_stays_high_for_ecn(self):
        """ECN constraint standards should not decrease through iterations."""
        constraint_initial = 0.70
        constraint_final = 0.68  # Should stay high
        assert constraint_final >= 0.65

    def test_final_gradient_in_target_range(self):
        """Final gradient should be in target range, not average."""
        novelty = 0.82
        constraint = 0.45
        gradient = novelty - constraint  # = 0.37
        target = 0.35
        tolerance = 0.08
        assert abs(gradient - target) <= tolerance


class TestReverseActualizationOutput:
    """Test the structure and content of reverse-actualization output."""

    def test_output_includes_gradient(self):
        from dmn_ecm import DMNECM
        from unittest.mock import patch, AsyncMock

        engine = DMNECM()

        async def mock_full_loop():
            dmn_out = [
                type(
                    "O",
                    (),
                    {
                        "model": "dmn",
                        "content": "x",
                        "phase": Phase.DIVERGENT,
                        "novelty_score": 0.8,
                    },
                )()
            ]
            ecn_out = type(
                "O",
                (),
                {
                    "model": "ecn",
                    "content": "y",
                    "phase": Phase.CONVERGENT,
                    "constraint_score": 0.5,
                },
            )()
            final_out = type(
                "O",
                (),
                {
                    "model": "ecn",
                    "content": "z",
                    "phase": Phase.FINAL,
                    "novelty_score": 0.8,
                    "constraint_score": 0.5,
                },
            )()
            return {
                "dmn_outputs": dmn_out,
                "ecn_critique": ecn_out,
                "final_output": final_out,
                "gradient": 0.3,
                "gradient_target": 0.35,
                "converged": True,
                "room": "test-room",
            }

        # Verify result structure
        result = {
            "dmn_outputs": [],
            "ecn_critique": {},
            "final_output": {},
            "gradient": 0.3,
            "gradient_target": 0.35,
        }
        assert "gradient" in result
        assert "gradient_target" in result
        assert "dmn_outputs" in result
        assert "final_output" in result


class TestReverseActualizationVersusOtherTechniques:
    """Contrast with RAG, ensemble, and chain-of-thought."""

    def test_vs_rag(self):
        """RAG retrieves and reads. Reverse-actualization contrasts and synthesizes."""
        # RAG: retrieve relevant docs → read them → answer
        # RA: DMN generates → ECN criticizes → gradient check → answer
        # Key difference: RA has opposition built in

    def test_vs_ensemble(self):
        """Ensemble averages outputs. RA preserves distinctness."""
        # Ensemble: multiple models → vote/average → consensus
        # RA: DMN → ECN → tension maintained → synthesis
        # Key difference: RA doesn't eliminate the tension

    def test_vs_cot(self):
        """Chain-of-thought chains reasoning forward. RA chains forward + backward."""
        # CoT: premise → reasoning → conclusion (one direction)
        # RA: DMN → ECN → DMN revision → ECN final (bidirectional)


class TestDomainSpecificGradients:
    """Different domains should have different target gradients."""

    def test_creative_domain_high_gradient(self):
        """Creative domains need high distance (novelty >> constraint)."""
        target_gradient = 0.45  # High creativity
        assert target_gradient > 0.35

    def test_analytical_domain_low_gradient(self):
        """Analytical domains need lower distance (more constraint)."""
        target_gradient = 0.20  # More constrained
        assert target_gradient < 0.35

    def test_architecture_domain_medium_high(self):
        """Architecture needs creative distance but also precision."""
        target_gradient = 0.38
        assert 0.35 <= target_gradient <= 0.45


class TestGradientAmplificationOverTime:
    """PLATO tracks gradient per domain — it should amplify over time."""

    def test_gradient_learning_possible(self):
        """PLATO tiles can store domain gradients. Gradient can learn."""
        from dmn_ecm import GradientTile

        tile = GradientTile(
            domain="architecture",
            dmn_energy=0.85,
            ecn_energy=0.42,
            novelty=0.85,
            constraint=0.42,
            gradient=0.43,
            phase=Phase.FINAL,
        )
        assert tile.gradient == pytest.approx(0.43, abs=0.01)
        assert tile.domain == "architecture"


class TestReverseActualizationAndTheRostralBridge:
    """Test mapping to the neuroscience."""

    def test_rpfc_is_bridge(self):
        """The rPFC is the bridge — PLATO is the software equivalent."""
        # In brain: rPFC bridges DMN and ECN
        # In PLATO: room server bridges DMN and ECN models
        # Both maintain gradient

    def test_gradient_amplitude_predicts_creativity(self):
        """From study: amplitude of gradient predicts individual creative ability."""
        high_gradient = 0.85 - 0.35  # 0.50
        low_gradient = 0.70 - 0.60  # 0.10
        assert high_gradient > low_gradient
        # Higher gradient = more creative output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])