"""Find a two-spin transverse-field Ising ground state with VQE."""

from argparse import ArgumentParser
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy.optimize import minimize


def ising_hamiltonian(coupling: float, field: float) -> SparsePauliOp:
    """Return H = -J Z0 Z1 - h(X0 + X1) for two spins."""
    return SparsePauliOp.from_list(
        [("ZZ", -coupling), ("IX", -field), ("XI", -field)]
    )


def build_ansatz() -> tuple[QuantumCircuit, ParameterVector]:
    """Build a small real-valued trial circuit with one entangling gate."""
    angles = ParameterVector("theta", 4)
    circuit = QuantumCircuit(2)
    circuit.ry(angles[0], 0)
    circuit.ry(angles[1], 1)
    circuit.cx(0, 1)
    circuit.ry(angles[2], 0)
    circuit.ry(angles[3], 1)
    return circuit, angles


def state_and_energy(values, circuit, angles, hamiltonian):
    """Prepare a trial state and calculate its energy expectation value."""
    bound = circuit.assign_parameters(dict(zip(angles, values)))
    state = Statevector.from_instruction(bound)
    energy = float(np.real(state.expectation_value(hamiltonian)))
    return state, energy


def run_vqe(coupling: float, field: float, seed: int, maxiter: int):
    """Optimize the circuit parameters and record every energy evaluation."""
    hamiltonian = ising_hamiltonian(coupling, field)
    circuit, angles = build_ansatz()
    initial = np.random.default_rng(seed).uniform(-np.pi, np.pi, len(angles))
    history: list[float] = []

    def objective(values):
        _, energy = state_and_energy(values, circuit, angles, hamiltonian)
        history.append(energy)
        return energy

    result = minimize(
        objective,
        initial,
        method="COBYLA",
        options={"maxiter": maxiter, "tol": 1e-6},
    )
    state, energy = state_and_energy(result.x, circuit, angles, hamiltonian)
    exact_energies = np.linalg.eigvalsh(hamiltonian.to_matrix()).real
    return circuit, angles, result, state, energy, history, exact_energies


def spin_observables(state: Statevector) -> dict[str, float]:
    """Calculate useful correlations in the optimized state."""
    operators = {
        "<Z0 Z1>": SparsePauliOp.from_list([("ZZ", 1.0)]),
        "<X0>": SparsePauliOp.from_list([("IX", 1.0)]),
        "<X1>": SparsePauliOp.from_list([("XI", 1.0)]),
    }
    return {
        label: float(np.real(state.expectation_value(operator)))
        for label, operator in operators.items()
    }


def save_plots(output_dir, circuit, angles, parameters, state, history, exact_energies):
    """Save the optimized circuit and three result visualizations."""
    bound = circuit.assign_parameters(dict(zip(angles, parameters)))
    figure = bound.draw(output="mpl", style="iqp", fold=-1)
    figure.savefig(output_dir / "vqe_circuit.png", dpi=160, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(7, 4))
    axis.plot(range(1, len(history) + 1), history, color="#6f5bd3")
    axis.axhline(exact_energies[0], color="#24a0a8", linestyle="--", label="Exact ground energy")
    axis.set(xlabel="Energy evaluation", ylabel="Energy", title="Ising-model VQE convergence")
    axis.legend()
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / "vqe_convergence.png", dpi=160)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(6, 4))
    bars = axis.bar(range(4), exact_energies, color="#24a0a8")
    axis.bar_label(bars, labels=[f"{energy:.3f}" for energy in exact_energies], padding=3)
    axis.set(xticks=range(4), xticklabels=["E0", "E1", "E2", "E3"], ylabel="Energy")
    axis.set_title("Exact two-spin energy spectrum")
    figure.tight_layout()
    figure.savefig(output_dir / "energy_spectrum.png", dpi=160)
    plt.close(figure)

    probabilities = state.probabilities()
    labels = ["|00>", "|01>", "|10>", "|11>"]
    figure, axis = plt.subplots(figsize=(7, 4))
    bars = axis.bar(labels, probabilities, color="#6f5bd3")
    axis.bar_label(bars, labels=[f"{value:.1%}" for value in probabilities], padding=3)
    axis.set(ylabel="Probability", title="Optimized ground-state probabilities", ylim=(0, 0.5))
    figure.tight_layout()
    figure.savefig(output_dir / "ground_state_probabilities.png", dpi=160)
    plt.close(figure)


def parse_args():
    """Read command-line options."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--coupling", type=float, default=1.0, help="spin coupling J")
    parser.add_argument("--field", type=float, default=1.0, help="transverse field h")
    parser.add_argument("--seed", type=int, default=7, help="initial-point random seed")
    parser.add_argument("--maxiter", type=int, default=300, help="maximum energy evaluations")
    parser.add_argument("--output-dir", type=Path, default=Path("plots"), help="plot directory")
    return parser.parse_args()


def main() -> None:
    """Run the VQE experiment and print a compact interpretation."""
    args = parse_args()
    if args.maxiter < 1:
        raise SystemExit("--maxiter must be a positive integer")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data = run_vqe(args.coupling, args.field, args.seed, args.maxiter)
    circuit, angles, result, state, energy, history, exact_energies = data
    save_plots(args.output_dir, circuit, angles, result.x, state, history, exact_energies)
    observables = spin_observables(state)

    print("Parameterized VQE ansatz:\n")
    print(circuit.draw(output="text"))
    print(f"\nHamiltonian: H = -({args.coupling}) Z0Z1 - ({args.field})(X0 + X1)")
    print(f"Optimizer success: {result.success}")
    print(f"Energy evaluations: {len(history)}")
    print(f"VQE ground energy: {energy:.8f}")
    print(f"Exact ground energy: {exact_energies[0]:.8f}")
    print(f"Absolute error: {abs(energy - exact_energies[0]):.2e}")
    for label, value in observables.items():
        print(f"{label}: {value:.6f}")
    print(f"Plots saved in: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
