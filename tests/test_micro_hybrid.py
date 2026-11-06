"""Run the stop-start equation and presentation-boundary checks in normal CI."""
import subprocess


def test_micro_hybrid_model_and_cluster_boundaries():
    result = subprocess.run(
        ['node', '--test', 'tests/micro_hybrid/model.test.mjs'],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
