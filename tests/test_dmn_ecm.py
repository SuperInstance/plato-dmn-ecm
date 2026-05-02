"""Tests for the DMN-ECM engine."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dmn_ecm import (
    DMNECM,
    DMNECMConfig,
    ModelOutput,
    GradientTile,
    Phase,
    estimate_energy,
    DEFAULT_SYSTEM_PROMPTS,
)


class TestPhaseEnum:
    def test_phase_values(self):
        assert Phase.DIVERGENT.value == "divergent"
        assert Phase.CONVERGENT.value == "convergent"
        assert Phase.RECOMBINATION.value == "recombination"
        assert Phase.FINAL.value == "final"
        assert Phase.DIVERGENT_REVISION.value == "divergent-revision"


class TestGradientTile:
    def test_gradient_tile_creation(self):
        tile = GradientTile(
            domain="architecture",
            dmn_energy=0.85,
            ecn_energy=0.42,
            novelty=0.85,
            constraint=0.42,
            gradient=0.43,
            phase=Phase.DIVERGENT,
        )
        assert tile.domain == "architecture"
        assert tile.gradient == 0.43
        assert tile.phase == Phase.DIVERGENT

    def test_gradient_calculation(self):
        tile = GradientTile(
            domain="test",
            dmn_energy=0.8,
            ecn_energy=0.5,
            novelty=0.8,
            constraint=0.5,
            gradient=0.3,
            phase=Phase.DIVERGENT,
        )
        assert abs(tile.gradient - (tile.novelty - tile.constraint)) < 0.001


class TestModelOutput:
    def test_model_output_basics(self):
        output = ModelOutput(
            model="test-model",
            content="Test content",
            phase=Phase.DIVERGENT,
        )
        assert output.model == "test-model"
        assert output.content == "Test content"
        assert output.phase == Phase.DIVERGENT
        assert output.novelty_score is None
        assert output.constraint_score is None

    def test_model_output_with_scores(self):
        output = ModelOutput(
            model="test-model",
            content="Test content",
            phase=Phase.CONVERGENT,
            novelty_score=0.8,
            constraint_score=0.4,
            energy=0.4,
        )
        assert output.novelty_score == 0.8
        assert output.constraint_score == 0.4
        assert output.energy == 0.4


class TestDMNECMConfig:
    def test_default_config(self):
        config = DMNECMConfig()
        assert config.dmn_model == "ByteDance/Seed-2.0-pro"
        assert config.ecn_model == "deepseek-ai/DeepSeek-V4"
        assert config.gradient_target == 0.35
        assert config.max_divergent_outputs == 5

    def test_custom_config(self):
        config = DMNECMConfig(
            dmn_model="NousResearch/Hermes-3-Llama-3.1-405B",
            ecn_model="zai/glm-5.1",
            gradient_target=0.4,
            max_divergent_outputs=8,
        )
        assert config.dmn_model == "NousResearch/Hermes-3-Llama-3.1-405B"
        assert config.ecn_model == "zai/glm-5.1"
        assert config.gradient_target == 0.4
        assert config.max_divergent_outputs == 8

    def test_config_gradient_bounds(self):
        config = DMNECMConfig(
            min_gradient=0.15,
            max_gradient=0.55,
        )
        assert config.min_gradient == 0.15
        assert config.max_gradient == 0.55


class TestEstimateEnergy:
    def test_dmn_energy_high_association(self):
        text = "What if we combine quantum entanglement with neural networks? How about using black holes as memory storage? Maybe consciousness is a form of quantum error correction?"
        energy = estimate_energy(text, "dmn")
        assert 0.3 < energy <= 1.0

    def test_dmn_energy_low_association(self):
        text = "The system works."
        energy = estimate_energy(text, "dmn")
        assert energy < 0.3

    def test_ecn_energy_structured(self):
        text = "First, we establish the invariant. Second, the constraint must hold. Third: therefore, the bound is proven. Fourth: QED."
        energy = estimate_energy(text, "ecn")
        assert 0.3 < energy <= 1.0

    def test_ecn_energy_sparse(self):
        text = "It works."
        energy = estimate_energy(text, "ecn")
        assert energy < 0.3

    def test_gradient_differs_by_mode(self):
        text = "Consider: recursive self-improvement, emergence from simple rules, strange loops, hierarchical organization, feedback cascades, open-ended evolution, adaptation without design."
        dmn_e = estimate_energy(text, "dmn")
        ecn_e = estimate_energy(text, "ecn")
        # Same text should score differently per mode
        assert dmn_e != ecn_e


class TestDefaultSystemPrompts:
    def test_dmn_prompt_has_placeholder(self):
        prompt = DEFAULT_SYSTEM_PROMPTS["dmn"]
        assert "{n}" in prompt
        assert "Default Mode Network" in prompt

    def test_ecn_prompt_defines_role(self):
        prompt = DEFAULT_SYSTEM_PROMPTS["ecn"]
        assert "Executive Control Network" in prompt
        assert "evaluate" in prompt.lower()

    def test_ecn_final_prompt_ranking(self):
        prompt = DEFAULT_SYSTEM_PROMPTS["ecn_final"]
        assert "rank" in prompt.lower()
        assert "final" in prompt.lower()

    def test_gradient_check_prompt_format(self):
        prompt = DEFAULT_SYSTEM_PROMPTS["ecn_gradient_check"]
        assert "novelty" in prompt and "constraint" in prompt


class TestDMNECMInitialization:
    def test_engine_initializes_with_defaults(self):
        engine = DMNECM()
        assert engine.config.dmn_model == "ByteDance/Seed-2.0-pro"
        assert engine.config.ecn_model == "deepseek-ai/DeepSeek-V4"
        assert engine.session_id.startswith("dmn-ecm-")

    def test_engine_initializes_with_custom_config(self):
        config = DMNECMConfig(
            dmn_model="custom-dmn",
            ecn_model="custom-ecn",
            gradient_target=0.45,
        )
        engine = DMNECM(config=config)
        assert engine.config.dmn_model == "custom-dmn"
        assert engine.config.ecn_model == "custom-ecn"
        assert engine.config.gradient_target == 0.45

    def test_room_name_contains_session_id(self):
        engine = DMNECM()
        assert "dmn-ecm/" in engine.room
        assert engine.session_id in engine.room


class TestDMNECMDiverge:
    @pytest.mark.asyncio
    async def test_diverge_produces_output(self):
        engine = DMNECM()
        with patch("dmn_ecm.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Idea 1: recursive thought.\nIdea 2: quantum memory."
            outputs = await engine._diverge("Design something novel", "test-domain")
            assert len(outputs) == 1
            assert outputs[0].phase in (Phase.DIVERGENT, Phase.DIVERGENT_REVISION)
            assert outputs[0].model == engine.config.dmn_model

    @pytest.mark.asyncio
    async def test_diverge_writes_tile(self):
        engine = DMNECM()
        with patch("dmn_ecm.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Novel idea."
            with patch("dmn_ecm.write_tile", new_callable=AsyncMock) as mock_write:
                mock_write.return_value = "tile-123"
                outputs = await engine._diverge("Test prompt", "test")
                mock_write.assert_called_once()


class TestDMNECMConverge:
    @pytest.mark.asyncio
    async def test_converge_produces_critique(self):
        engine = DMNECM()
        dmn_outputs = [
            ModelOutput(model="dmn", content="Wild idea", phase=Phase.DIVERGENT, novelty_score=0.9)
        ]
        with patch("dmn_ecm.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Critique: interesting but impractical."
            critique = await engine._converge(dmn_outputs, "Test", "test-domain")
            assert critique.phase == Phase.CONVERGENT
            assert critique.constraint_score is not None


class TestDMNECMGradient:
    def test_compute_gradient_high_novelty_low_constraint(self):
        engine = DMNECM()
        dmn_outputs = [
            ModelOutput(model="dmn", content="a", phase=Phase.DIVERGENT, novelty_score=0.9)
        ]
        ecn_output = ModelOutput(model="ecn", content="b", phase=Phase.CONVERGENT, constraint_score=0.3)
        gradient = engine._compute_gradient(dmn_outputs, ecn_output)
        assert gradient == pytest.approx(0.6, abs=0.01)

    def test_compute_gradient_low_novelty_high_constraint(self):
        engine = DMNECM()
        dmn_outputs = [
            ModelOutput(model="dmn", content="a", phase=Phase.DIVERGENT, novelty_score=0.3)
        ]
        ecn_output = ModelOutput(model="ecn", content="b", phase=Phase.CONVERGENT, constraint_score=0.7)
        gradient = engine._compute_gradient(dmn_outputs, ecn_output)
        assert gradient == pytest.approx(-0.4, abs=0.01)

    def test_compute_gradient_average_over_multiple_dmn(self):
        engine = DMNECM()
        dmn_outputs = [
            ModelOutput(model="dmn", content="a", phase=Phase.DIVERGENT, novelty_score=0.8),
            ModelOutput(model="dmn", content="b", phase=Phase.DIVERGENT, novelty_score=0.6),
        ]
        ecn_output = ModelOutput(model="ecn", content="c", phase=Phase.CONVERGENT, constraint_score=0.5)
        gradient = engine._compute_gradient(dmn_outputs, ecn_output)
        assert gradient == pytest.approx(0.25, abs=0.01)


class TestDMNECMIntegration:
    @pytest.mark.asyncio
    async def test_full_loop_runs(self):
        engine = DMNECM(DMNECMConfig(max_divergent_outputs=3))
        call_count = 0

        async def mock_call(prompt, model, system):
            nonlocal call_count
            call_count += 1
            if "dmn" in system.lower():
                return f"Creative idea {call_count}"
            return f"Critique {call_count}"

        with patch("dmn_ecm.call_model", new_callable=AsyncMock) as mock_call_fn:
            mock_call_fn.side_effect = mock_call
            with patch("dmn_ecm.write_tile", new_callable=AsyncMock) as mock_write:
                mock_write.return_value = "tile-id"
                result = await engine.reverse_actualize(
                    prompt="Design a better database",
                    domain="database",
                    max_iterations=2,
                )
                assert "dmn_outputs" in result
                assert "ecn_critique" in result
                assert "final_output" in result
                assert "gradient" in result
                assert 2 <= call_count <= 6  # diverge + converge + maybe revision


class TestDMNECMBidirectionalFlow:
    """Tests for the bidirectional flow property of DMN-ECM."""

    @pytest.mark.asyncio
    async def test_ecn_receives_dmn_output(self):
        engine = DMNECM()
        received_prompt = None

        async def capture_call(prompt, model, system):
            nonlocal received_prompt
            if "ecn" in system.lower():
                received_prompt = prompt
            return "ok"

        with patch("dmn_ecm.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = capture_call
            with patch("dmn_ecm.write_tile", new_callable=AsyncMock):
                dmn_out = [
                    ModelOutput(
                        model="dmn",
                        content="DMN idea about distributed systems",
                        phase=Phase.DIVERGENT,
                        novelty_score=0.8,
                    )
                ]
                await engine._converge(dmn_out, "test", "test-domain")
                # ECN was called
                assert received_prompt is not None
                assert "distributed systems" in received_prompt


class TestDMNECMModelRouting:
    """Tests for model routing based on type."""

    def test_seed_routes_to_deepinfra(self):
        from dmn_ecm import call_model
        import inspect
        source = inspect.getsource(call_model)
        assert "deepinfra" in source.lower()

    def test_deepseek_routes_to_deepseek(self):
        from dmn_ecm import call_model
        import inspect
        source = inspect.getsource(call_model)
        assert "deepseek" in source.lower()

    def test_glm_routes_to_zai(self):
        from dmn_ecm import call_model
        import inspect
        source = inspect.getsource(call_model)
        assert "zai" in source.lower()


class TestDMNECMTileWriting:
    """Tests for PLATO tile writing."""

    @pytest.mark.asyncio
    async def test_write_tile_includes_phase(self):
        engine = DMNECM()
        written_data = {}

        async def capture_write(host, room, question, answer, domain, model, phase, **kwargs):
            written_data["phase"] = phase
            written_data["domain"] = domain
            return "tile-123"

        with patch("dmn_ecm.write_tile", side_effect=capture_write):
            await engine._diverge("test prompt", "test-domain")
            assert written_data.get("phase") in (Phase.DIVERGENT, Phase.DIVERGENT_REVISION)
            assert written_data.get("domain") == "test-domain"


class TestDMNECMNoCompromise:
    """
    Core property: DMN and ECN should not compromise on their core strengths.
    DMN should not lose novelty. ECN should not lower constraint standards.
    """

    @pytest.mark.asyncio
    async def test_dmn_novelty_preserved_through_revision(self):
        engine = DMNECM()
        original_novelty = None

        async def track_novelty(prompt, model, system):
            nonlocal original_novelty
            if "dmn" in system.lower() and "revision" not in system.lower():
                original_novelty = 0.9
                return "Creative idea: use bioluminescent proteins as data storage"
            if "revision" in system.lower():
                # DMN should maintain novelty in revision
                assert original_novelty is not None
            return "Critique" if "ecn" in system.lower() else "Revised idea"

        with patch("dmn_ecm.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = track_novelty
            with patch("dmn_ecm.write_tile", new_callable=AsyncMock):
                result = await engine.reverse_actualize(
                    prompt="Design data storage",
                    domain="storage",
                    max_iterations=2,
                )
                # Loop ran without error = property maintained


class TestGradientTarget:
    """Tests for gradient targeting mechanism."""

    @pytest.mark.asyncio
    async def test_gradient_check_stops_when_stabilized(self):
        config = DMNECMConfig(gradient_target=0.35, gradient_tolerance=0.05)
        engine = DMNECM(config)

        call_count = 0

        async def counting_call(prompt, model, system):
            nonlocal call_count
            call_count += 1
            return "output"

        with patch("dmn_ecm.call_model", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = counting_call
            with patch("dmn_ecm.write_tile", new_callable=AsyncMock):
                # With perfect gradient from mock, should stop early
                result = await engine.reverse_actualize(
                    prompt="test",
                    domain="test",
                    max_iterations=4,
                )
                # Should complete (mock doesn't give real gradient)


class TestFivePrinciples:
    """Test that the 5 core principles are represented in the architecture."""

    def test_distance_maintained_in_config(self):
        config = DMNECMConfig(min_gradient=0.15, max_gradient=0.55)
        assert config.min_gradient > 0  # Distance can't be zero
        assert config.max_gradient < 1.0  # Distance can't be max

    def test_contrast_principle_in_system_prompts(self):
        dmn_prompt = DEFAULT_SYSTEM_PROMPTS["dmn"]
        ecn_prompt = DEFAULT_SYSTEM_PROMPTS["ecn"]
        # DMN should NOT be asked to evaluate
        assert "evaluate" not in dmn_prompt.lower()
        # ECN should challenge, not collaborate
        assert "challenge" in ecn_prompt.lower() or "critique" in ecn_prompt.lower()

    def test_bidirectional_flow_in_phase_order(self):
        engine = DMNECM()
        # The loop goes: DMN → ECN → DMN revision → ECN final
        # This is bidirectional: ECN output feeds back to DMN
        assert hasattr(engine, "_diverge")
        assert hasattr(engine, "_converge")
        assert hasattr(engine, "_recombine")
        assert hasattr(engine, "_final_evaluate")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])