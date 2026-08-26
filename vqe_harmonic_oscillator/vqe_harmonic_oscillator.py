"""Approximate a harmonic oscillator ground state with a small VQE circuit."""

from argparse import ArgumentParser
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy.optimize import minimize


def harmonic_oscillator_hamiltonian() -> SparsePauliOp:
    """Return H = n + 1/2 for four levels encoded in two qubits.

    With |q1 q0> representing levels |0>, |1>, |2>, and |3>, the number
    operator is n = 3/2 I - 1/2 Z0 - Z1. We use units where hbar*omega = 1.
    """
    return SparsePauliOp.from_list(
        [("II", 2.0), ("IZ", -0.5), ("ZI", -1.0)]
    )


def build_ansatz() -> tuple[QuantumCircuit, ParameterVector]:
    """Build a shallow, parameterized two-qubit trial-state circuit."""
    angles = ParameterVector("theta", 4)
    circuit = QuantumCircuit(2)
    circuit.ry(angles[0], 0)
    circuit.ry(angles[1], 1)
    circuit.cx(0, 1)
    circuit.ry(angles[2], 0)
    circuit.ry(angles[3], 1)
    return circuit, angles


def state_and_energy(
    values: np.ndarray,
    circuit: QuantumCircuit,
    angles: ParameterVector,
    hamiltonian: SparsePauliOp,
) -> tuple[Statevector, float]:
    """Bind trial parameters and calculate the exact expectation value <H>."""
    bound_circuit = circuit.assign_parameters(dict(zip(angles, values)))
    state = Statevector.from_instruction(bound_circuit)
    energy = float(np.real(state.expectation_value(hamiltonian)))
    return state, energy


def run_vqe(seed: int, maxiter: int):
    """Optimize the ansatz and return the circuit, result, and energy history."""
    circuit, angles = build_ansatz()
    hamiltonian = harmonic_oscillator_hamiltonian()
    rng = np.random.default_rng(seed)
    initial_values = rng.uniform(-np.pi, np.pi, len(angles))
    history: list[float] = []

    def objective(values: np.ndarray) -> float:
        _, energy = state_and_energy(values, circuit, angles, hamiltonian)
        history.append(energy)
        return energy

    result = minimize(
        objective,
        initial_values,
        method="COBYLA",
        options={"maxiter": maxiter, "tol": 1e-6},
    )
    final_state, final_energy = state_and_energy(
        result.x, circuit, angles, hamiltonian
    )
    return circuit, angles, result, final_state, final_energy, history


def save_plots(
    output_dir: Path,
    circuit: QuantumCircuit,
    angles: ParameterVector,
    parameters: np.ndarray,
    state: Statevector,
    history: list[float],
) -> None:
    """Save the ansatz, optimization history, levels, and final probabilities."""
    bound = circuit.assign_parameters(dict(zip(angles, parameters)))
    figure = bound.draw(output="mpl", style="iqp", fold=-1)
    figure.savefig(output_dir / "vqe_circuit.png", dpi=160, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(7, 4))
    axis.plot(range(1, len(history) + 1), history, color="#6f5bd3")
    axis.axhline(0.5, color="#24a0a8", linestyle="--", label="Exact ground energy")
    axis.set(xlabel="Energy evaluation", ylabel="Energy", title="VQE convergence")
    axis.legend()
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / "vqe_convergence.png", dpi=160)
    plt.close(figure)

    levels = np.arange(4)
    energies = levels + 0.5
    figure, axis = plt.subplots(figsize=(6, 4))
    axis.hlines(energies, 0, 1, colors="#24a0a8", linewidth=2)
    for level, energy in zip(levels, energies):
        axis.text(1.04, energy, f"n={level}: E={energy:.1f}", va="center")
    axis.set(xlim=(-0.05, 1.65), ylim=(0, 4), xticks=[], ylabel="Energy")
    axis.set_title("Truncated harmonic-oscillator levels")
    figure.tight_layout()
    figure.savefig(output_dir / "energy_levels.png", dpi=160)
    plt.close(figure)

    probabilities = state.probabilities()
    labels = ["|00> (n=0)", "|01> (n=1)", "|10> (n=2)", "|11> (n=3)"]
    figure, axis = plt.subplots(figsize=(7, 4))
    bars = axis.bar(labels, probabilities, color="#6f5bd3")
    axis.bar_label(bars, labels=[f"{value:.1%}" for value in probabilities], padding=3)
    axis.set(ylabel="Probability", title="Optimized trial-state probabilities", ylim=(0, 1.08))
    axis.tick_params(axis="x", rotation=15)
    figure.tight_layout()
    figure.savefig(output_dir / "optimized_state.png", dpi=160)
    plt.close(figure)


def parse_args():
    """Read command-line options."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7, help="initial-point random seed")
    parser.add_argument("--maxiter", type=int, default=250, help="maximum optimizer evaluations")
    parser.add_argument("--output-dir", type=Path, default=Path("plots"), help="plot directory")
    return parser.parse_args()


def main() -> None:
    """Run VQE, print an interpretation, and save learning plots."""
    args = parse_args()
    if args.maxiter < 1:
        raise SystemExit("--maxiter must be a positive integer")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    circuit, angles, result, state, energy, history = run_vqe(args.seed, args.maxiter)
    save_plots(args.output_dir, circuit, angles, result.x, state, history)

    print("Parameterized VQE ansatz:\n")
    print(circuit.draw(output="text"))
    print(f"\nOptimizer success: {result.success}")
    print(f"Energy evaluations: {len(history)}")
    print(f"VQE ground energy: {energy:.8f}")
    print("Exact ground energy: 0.50000000")
    print(f"Absolute error: {abs(energy - 0.5):.2e}")
    print(f"Plots saved in: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
