# Quantum Superposition Demo

A small, hands-on introduction to quantum computing with Python and Qiskit.
Build a one-qubit circuit, create superposition, run it on a local simulator,
and turn the results into plots. No quantum-computing experience is required.

## What you will learn

- What a qubit is and how it differs from a classical bit
- How a Hadamard gate creates an equal superposition
- How to construct and simulate a Qiskit circuit
- Why quantum measurement is probabilistic
- The difference between ideal probabilities and sampled results

## The idea in one minute

A classical bit is either `0` or `1`. A qubit can be in a combination of the
two basis states. Every qubit begins in state $|0\rangle$. Applying a Hadamard
gate, written $H$, creates

$$
|\psi\rangle = H|0\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}.
$$

Both amplitudes are $1/\sqrt{2}$. Squaring their magnitudes gives a probability
of $1/2$, so measurement returns `0` half the time and `1` half the time in the
long run. One measurement produces only one classical answer—it does not show
the superposition itself.

```text
start in |0>  ->  apply H  ->  measure  ->  classical result: 0 or 1
```

## Project structure

```text
quantum-superposition-demo/
├── superposition_demo.py   # circuit, simulation, and plotting code
├── requirements.txt        # packages needed to run it
├── plots/                  # generated images are saved here
└── README.md               # this learning guide
```

## Set up

Python 3.10 or newer is recommended. From a terminal:

```bash
cd quantum-superposition-demo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead.

## Run the experiment

```bash
python superposition_demo.py
```

The terminal prints the circuit and a result similar to:

```text
     ┌───┐┌─┐
  q: ┤ H ├┤M├
     └───┘└╥┘
c: 1/══════╩═
           0

Measurement counts (1,000 shots): {'0': 503, '1': 497}
```

Exact counts can differ because measurement is random. A fixed simulator seed
makes the tutorial reproducible on the same Qiskit version.

Three images are created in `plots/`:

| Plot | What it explains |
| --- | --- |
| `circuit.png` | The Hadamard gate and measurement |
| `ideal_probabilities.png` | Exact 50/50 probabilities before measurement |
| `measurement_counts.png` | Observed results from repeated measurements |

Try more measurements or display the saved images in windows:

```bash
python superposition_demo.py --shots 10000 --show
```

Run `python superposition_demo.py --help` to see every option.

## How the code works

1. `build_superposition_circuit()` creates a `QuantumCircuit`, then adds an `H`
   gate and measurement.
2. `simulate()` adapts the circuit for `AerSimulator` and runs it many times.
   Each repetition is called a **shot**.
3. The three `save_*_plot()` functions visualize the circuit, exact state, and
   sampled counts.
4. `main()` connects these steps and prints a short interpretation.

The ideal state is calculated using a circuit without measurement. This matters
because measurement collapses the quantum state to one observed outcome.

## Experiments to try

Change one thing, rerun the script, and explain what you observe:

1. Use `--shots 10`, then `--shots 10000`. Which is closer to 50/50?
2. Remove `circuit.h(0)`. Why do all measurements become `0`?
3. Add a second Hadamard after the first. Two Hadamards cancel:
   $HH|0\rangle=|0\rangle$.
4. Replace `circuit.h(0)` with `circuit.x(0)`. The X gate acts like a NOT gate,
   changing $|0\rangle$ to $|1\rangle$.
5. Change the random seed with `--seed 7` and compare the counts.

## Common problems

- **`ModuleNotFoundError`**: activate `.venv` and reinstall the requirements.
- **Plot windows do not open**: PNG files are still saved in `plots/`. Use
  `--show` only when a graphical display is available.
- **Counts are not exactly equal**: expected—finite random samples fluctuate
  around the theoretical probabilities.

## Where to go next

Try a two-qubit Bell-state circuit: apply `H` to the first qubit, then a
controlled NOT (`cx`) from the first qubit to the second. This introduces
**entanglement**.

Official learning resources:

- [Qiskit documentation](https://quantum.cloud.ibm.com/docs/en/guides)
- [IBM Quantum Learning](https://quantum.cloud.ibm.com/learning)

## License

This project is covered by the license in the repository root.
