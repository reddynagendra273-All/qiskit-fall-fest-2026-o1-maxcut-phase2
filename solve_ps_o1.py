
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

import qff_phase2 as official


# --------------------------------------------------
# 1. LOAD THE OFFICIAL PS-O1 INSTANCE
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR / "instances.json", encoding="utf-8") as f:
    instances = json.load(f)

ps_o1 = instances["PS-O1"]
weighted_edges = [
    (int(a), int(b), float(w))
    for a, b, w in ps_o1["weighted_edges"]
]
n = ps_o1["num_vertices"]

settings = instances["benchmark_settings"]
shots = settings["shots"]
seeds = ps_o1["initialization_seeds"]

print("=" * 60)
print("PS-O1: QAOA MAX-CUT BENCHMARK")
print("=" * 60)
print("Vertices:", n)
print("Weighted edges:", len(weighted_edges))
print("Initialization seeds:", seeds)
print("Official shots:", shots)
print("Official optimization level:", settings["optimization_level"])
print("Official transpiler seed:", settings["seed_transpiler"])
print("Official simulator seed:", settings["seed_simulator"])


# --------------------------------------------------
# 2. BUILD THE P=1 QAOA CIRCUIT
# --------------------------------------------------

def build_qaoa(gamma, beta, measure=False):
    qc = QuantumCircuit(n, n) if measure else QuantumCircuit(n)

    # Prepare an equal superposition of all bitstrings.
    qc.h(range(n))

    # Weighted Max-Cut cost layer.
    for u, v, weight in weighted_edges:
        qc.rzz(-gamma * weight, u, v)

    # QAOA mixer layer.
    for q in range(n):
        qc.rx(2 * beta, q)

    if measure:
        qc.measure(range(n), range(n))

    return qc


# --------------------------------------------------
# 3. CALCULATE THE EXACT IDEAL EXPECTED CUT
# --------------------------------------------------

def cut_weight(bits):
    return sum(
        weight
        for u, v, weight in weighted_edges
        if bits[u] != bits[v]
    )


def ideal_expected_cut(gamma, beta):
    qc = build_qaoa(gamma, beta)
    probabilities = Statevector.from_instruction(qc).probabilities()

    expected = 0.0

    for index, probability in enumerate(probabilities):
        bits = tuple((index >> q) & 1 for q in range(n))
        expected += probability * cut_weight(bits)

    return float(expected)


# --------------------------------------------------
# 4. FIVE REQUIRED PARAMETER INITIALIZATIONS
# --------------------------------------------------

runs = []

print("\nOptimizing QAOA parameters using ideal statevectors...")

for seed in seeds:
    rng = np.random.default_rng(seed)

    initial = [
        rng.uniform(0.0, np.pi),
        rng.uniform(0.0, np.pi / 2),
    ]

    result = minimize(
        lambda params: -ideal_expected_cut(params[0], params[1]),
        initial,
        method="COBYLA",
        options={"maxiter": 100, "rhobeg": 0.2, "tol": 1e-5},
    )

    gamma = float(result.x[0])
    beta = float(result.x[1])
    expected = ideal_expected_cut(gamma, beta)

    runs.append({
        "seed": int(seed),
        "gamma": gamma,
        "beta": beta,
        "expected_cut": expected,
        "success": bool(result.success),
        "iterations": int(result.nfev),
    })

    print(
        f"Seed {seed}: gamma={gamma:.5f}, beta={beta:.5f}, "
        f"ideal expected cut={expected:.5f}"
    )

# Select the best ideal expected-cut result.
best = max(runs, key=lambda item: item["expected_cut"])

print("\nBest initialization:", best["seed"])
print("Selected gamma:", best["gamma"])
print("Selected beta:", best["beta"])
print("Best ideal expected cut:", best["expected_cut"])


# --------------------------------------------------
# 5. LOAD PROCESSORS B AND D
# --------------------------------------------------

processor_b = official.PROCESSOR_B

processor_d = official.load_processor(
    str(BASE_DIR / "processors" / "processor_D.json")
)

errors = official.validate_processor_d(processor_d, required_qubits=n)

if errors:
    raise ValueError("Processor D validation failed: " + "; ".join(errors))

print("\nProcessor D validation: OK")

processors = [processor_b, processor_d]

# Build the same logical QAOA circuit for each processor.
logical_circuit = build_qaoa(
    best["gamma"], best["beta"], measure=True
)


# --------------------------------------------------
# 6. OFFICIAL TRANSPILATION, METRICS AND NOISY RUN
# --------------------------------------------------

benchmark_results = []

for processor in processors:
    print("\n" + "-" * 60)
    print("Evaluating:", processor["name"])

    metrics = official.circuit_metrics(logical_circuit, processor)

    if not metrics["executable"]:
        print("Not executable:", metrics["reason"])
        benchmark_results.append({
            "processor": processor["name"],
            "executable": False,
            "reason": metrics["reason"],
        })
        continue

    # Use the official transpilation helper.
    transpiled = official.transpile_for(logical_circuit, processor)

    # Official noisy simulator and official shot count.
    simulator = official.simulator(noisy=True, processor=processor)
    counts = simulator.run(transpiled, shots=shots).result().get_counts()

    total_shots = sum(counts.values())
    average_cut = 0.0
    best_sampled_cut = 0.0

    for bitstring, count in counts.items():
        bits = official.counts_to_x(bitstring)
        score = cut_weight(bits)

        average_cut += score * count
        best_sampled_cut = max(best_sampled_cut, score)

    average_cut /= total_shots

    result = {
        **metrics,
        "shots": shots,
        "average_cut": average_cut,
        "best_sampled_cut": best_sampled_cut,
        "counts": counts,
    }
    benchmark_results.append(result)

    print("Logical CX:", metrics["logical_cx"])
    print("Transpiled CX:", metrics["cx"])
    print("CX overhead:", metrics["cx_overhead"])
    print("SWAPs:", metrics["swaps"])
    print("Circuit depth:", metrics["depth"])
    print("Two-qubit depth:", metrics["two_q_depth"])
    print("Noisy average cut:", round(average_cut, 5))
    print("Best sampled cut:", best_sampled_cut)
    print("Most frequent bitstring:", max(counts, key=counts.get))


# --------------------------------------------------
# 7. SAVE RESULTS WITHOUT MODIFYING OFFICIAL FILES
# --------------------------------------------------

output = {
    "problem_statement": "PS-O1",
    "num_vertices": n,
    "weighted_edges": [list(edge) for edge in weighted_edges],
    "qaoa_depth": 1,
    "initialization_runs": runs,
    "selected_parameters": {
        "seed": best["seed"],
        "gamma": best["gamma"],
        "beta": best["beta"],
        "ideal_expected_cut": best["expected_cut"],
    },
    "benchmark_settings": settings,
    "processor_results": benchmark_results,
}

output_path = BASE_DIR / "phase2_results.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, default=str)

print("\n" + "=" * 60)
print("Benchmark finished.")
print("Results saved to:", output_path)
print("Official starter files were not modified.")
print("=" * 60)
