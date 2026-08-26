"""Create, simulate, and visualize a one-qubit superposition circuit."""

from argparse import ArgumentParser
from pathlib import Path

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
from qiskit_aer import AerSimulator


def build_superposition_circuit(measure: bool = True) -> QuantumCircuit:
    """Build H|0>, with an optional measurement into a classical bit."""
    circuit = QuantumCircuit(1, 1 if measure else 0)
    circuit.h(0)
    if measure:
        circuit.measure(0, 0)
    return circuit


def simulate(circuit: QuantumCircuit, shots: int, seed: int) -> dict[str, int]:
    """Run a circuit on a local simulator and return measurement counts."""
    simulator = AerSimulator()
    compiled = transpile(circuit, simulator)
    result = simulator.run(compiled, shots=shots, seed_simulator=seed).result()
    return result.get_counts(compiled)


def save_circuit_plot(circuit: QuantumCircuit, output_dir: Path) -> None:
    """Save a diagram of the gates and measurement."""
    figure = circuit.draw(output="mpl", style="iqp")
    figure.savefig(output_dir / "circuit.png", dpi=160, bbox_inches="tight")
    plt.close(figure)


def save_probability_plot(output_dir: Path) -> None:
    """Save the exact probabilities before measurement."""
    state = Statevector.from_instruction(build_superposition_circuit(measure=False))
    probabilities = state.probabilities_dict()
    labels = ["0", "1"]
    values = [probabilities.get(label, 0.0) for label in labels]

    figure, axis = plt.subplots(figsize=(6, 4))
    bars = axis.bar(labels, values, color=["#6f5bd3", "#24a0a8"])
    axis.bar_label(bars, labels=[f"{value:.0%}" for value in values], padding=3)
    axis.set(title="Ideal probabilities before measurement", xlabel="State", ylabel="Probability")
    axis.set_ylim(0, 1)
    figure.tight_layout()
    figure.savefig(output_dir / "ideal_probabilities.png", dpi=160)
    plt.close(figure)


def save_counts_plot(counts: dict[str, int], output_dir: Path, shots: int) -> None:
    """Save a histogram of the simulated measurement results."""
    figure = plot_histogram(
        counts, title=f"Measured results from {shots:,} shots", color="#6f5bd3"
    )
    figure.savefig(output_dir / "measurement_counts.png", dpi=160, bbox_inches="tight")
    plt.close(figure)


def parse_args():
    """Read command-line options."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--shots", type=int, default=1_000, help="number of measurements")
    parser.add_argument("--seed", type=int, default=42, help="simulator random seed")
    parser.add_argument("--output-dir", type=Path, default=Path("plots"), help="plot directory")
    parser.add_argument("--show", action="store_true", help="display plots after saving")
    return parser.parse_args()


def main() -> None:
    """Run the complete beginner experiment."""
    args = parse_args()
    if args.shots < 1:
        raise SystemExit("--shots must be a positive integer")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    circuit = build_superposition_circuit()
    counts = simulate(circuit, shots=args.shots, seed=args.seed)
    save_circuit_plot(circuit, args.output_dir)
    save_probability_plot(args.output_dir)
    save_counts_plot(counts, args.output_dir, args.shots)

    print("Quantum circuit:\n")
    print(circuit.draw(output="text"))
    print(f"\nMeasurement counts ({args.shots:,} shots): {counts}")
    print("The values should be close to 50% |0> and 50% |1>.")
    print(f"Plots saved in: {args.output_dir.resolve()}")

    if args.show:
        for image_path in sorted(args.output_dir.glob("*.png")):
            image = plt.imread(image_path)
            plt.figure(figsize=(8, 5))
            plt.imshow(image)
            plt.axis("off")
            plt.title(image_path.stem.replace("_", " ").title())
        plt.show()


if __name__ == "__main__":
    main()
