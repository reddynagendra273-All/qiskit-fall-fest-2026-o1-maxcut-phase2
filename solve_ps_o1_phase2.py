"""
PS-O1 Phase 2 benchmark runner for Qiskit Fall Fest 2026.
Keeps qff_phase2.py and instances.json unchanged.
Outputs:
  phase2_results.json
  results/tables/results.csv
  results/tables/bell.csv
"""
import csv
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

import qff_phase2 as official

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
TABLES_DIR = RESULTS_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

with open(BASE_DIR / "instances.json", encoding="utf-8") as f:
    instances = json.load(f)

ps_o1 = instances["PS-O1"]
weighted_edges = [
    (int(a), int(b), float(w))
    for a, b, w in ps_o1["weighted_edges"]
]
n = int(ps_o1["num_vertices"])
settings = instances["benchmark_settings"]
shots = int(settings["shots"])
seeds = [int(s) for s in ps_o1["initialization_seeds"]]
COST_MAX = sum(w for _, _, w in weighted_edges)

def cut_weight(bits):
    """bits is ordered x0, x1, ..., x(n-1)."""
    return float(sum(w for u, v, w in weighted_edges if bits[u] != bits[v]))

def exact_classical_optimum():
    scored = []
    for bits in itertools.product((0, 1), repeat=n):
        scored.append((cut_weight(bits), "".join(map(str, bits))))
    optimum = max(score for score, _ in scored)
    optimal_strings = [bits for score, bits in scored if np.isclose(score, optimum)]
    return float(optimum), optimal_strings

C_STAR, OPTIMAL_BITS = exact_classical_optimum()
OPTIMAL_SET = set(OPTIMAL_BITS)

def build_qaoa(gamma, beta, measure=False):
    qc = QuantumCircuit(n, n) if measure else QuantumCircuit(n)
    qc.h(range(n))
    for u, v, weight in weighted_edges:
        qc.rzz(-float(gamma) * weight, u, v)
    for q in range(n):
        qc.rx(2 * float(beta), q)
    if measure:
        qc.measure(range(n), range(n))
    return qc

def ideal_expected_cut(gamma, beta):
    state = Statevector.from_instruction(build_qaoa(gamma, beta))
    probs = state.probabilities()
    return float(sum(
        float(prob) * cut_weight(tuple((index >> q) & 1 for q in range(n)))
        for index, prob in enumerate(probs)
    ))


def counts_summary(counts):
    total = sum(counts.values())
    cut_sum = 0.0
    best_cut = 0.0
    optimal_count = 0

    for key, count in counts.items():
        bits_tuple = official.counts_to_x(key)
        bits = "".join(map(str, bits_tuple))
        score = cut_weight(bits_tuple)

        cut_sum += score * count
        best_cut = max(best_cut, score)

        if bits in OPTIMAL_SET:
            optimal_count += count

    mean_cut = cut_sum / total
    most_frequent_key = max(counts, key=counts.get)
    most_frequent_bits = "".join(
        map(str, official.counts_to_x(most_frequent_key))
    )

    return {
        "shots": total,
        "mean_cut": mean_cut,
        "best_sampled_cut": best_cut,
        "approx_ratio": mean_cut / C_STAR,
        "best_approx_ratio": best_cut / C_STAR,
        "p_opt": optimal_count / total,
        "most_frequent_bitstring": most_frequent_bits,
        "counts": counts,
    }


print("=" * 68)
print("QFF 2026 PHASE 2 — PS-O1 WEIGHTED MAX-CUT")
print("=" * 68)
print(f"Vertices={n}; edges={len(weighted_edges)}; total edge weight={COST_MAX:g}")
print(f"Exact classical optimum C*={C_STAR:g}")
print("All optimal bitstrings (x0...x5 convention):", OPTIMAL_BITS)
print("Seeds:", seeds, "| shots:", shots)
print("Official settings:", settings)

# Required five starts: both gamma and beta sampled uniformly from [0, pi].
runs = []
print("\nOptimizing p=1 QAOA using ideal statevectors (COBYLA, maxiter=100)...")
for seed in seeds:
    rng = np.random.default_rng(seed)
    initial = [rng.uniform(0.0, np.pi), rng.uniform(0.0, np.pi)]
    result = minimize(
        lambda params: -ideal_expected_cut(params[0], params[1]),
        initial,
        method="COBYLA",
        options={"maxiter": 100, "rhobeg": 0.2, "tol": 1e-5},
    )
    gamma, beta = map(float, result.x)
    run = {
        "seed": seed,
        "initial_gamma": float(initial[0]),
        "initial_beta": float(initial[1]),
        "gamma": gamma,
        "beta": beta,
        "expected_cut": ideal_expected_cut(gamma, beta),
        "success": bool(result.success),
        "iterations": int(result.nfev),
        "optimizer": "COBYLA",
        "max_iterations": 100,
        "objective": "exact ideal Statevector expected cut",
    }
    runs.append(run)
    print(
        f"seed={seed}: gamma={gamma:.6f}, beta={beta:.6f}, "
        f"ideal mean={run['expected_cut']:.6f}, nfev={run['iterations']}, "
        f"success={run['success']}"
    )

best = max(runs, key=lambda item: item["expected_cut"])
run_ratios = [r["expected_cut"] / C_STAR for r in runs]
print(f"\nSelected seed={best['seed']}; gamma={best['gamma']:.8f}; beta={best['beta']:.8f}")
print(f"Across-start mean ratio={np.mean(run_ratios):.6f}; std={np.std(run_ratios, ddof=1):.6f}")

processor_a = official.PROCESSOR_A
processor_b = official.PROCESSOR_B
processor_d = official.load_processor(str(BASE_DIR / "processors" / "processor_D.json"))
d_errors = official.validate_processor_d(processor_d, required_qubits=n)
if d_errors:
    raise ValueError("Processor D validation failed: " + "; ".join(d_errors))
processors = [processor_a, processor_b, processor_d]

logical_circuit = build_qaoa(best["gamma"], best["beta"], measure=True)
benchmark_rows = []
csv_rows = []

for processor in processors:
    metrics = official.circuit_metrics(logical_circuit, processor)
    if not metrics["executable"]:
        print(f"\n{processor['name']}: NOT EXECUTABLE — {metrics['reason']}")
        base = {
            "problem_id": "PS-O1",
            "processor": processor["name"].replace("Processor ", ""),
            "condition": "ideal",
            "executable": "false",
            "logical_qubits": n,
            "physical_qubits": processor["num_qubits"],
            "logical_cx": "",
            "cx": "",
            "depth": "",
            "two_q_depth": "",
            "swaps": "",
            "cx_overhead": "",
            "shots": "",
            "quality_metric": "",
            "quality_value": "",
            "p_opt": "",
            "classical_optimum": C_STAR,
            "random_baseline": COST_MAX / 2,
            "reason": metrics.get("reason", "not executable"),
        }
        csv_rows.append(base)
        base_noisy = dict(base)
        base_noisy["condition"] = "noisy"
        csv_rows.append(base_noisy)
        benchmark_rows.append({"processor": processor["name"], **metrics})
        continue

    print(f"\nEvaluating {processor['name']}...")
    transpiled = official.transpile_for(logical_circuit, processor)
    for noisy in (False, True):
        condition = "noisy" if noisy else "ideal"
        sim = official.simulator(noisy=noisy, processor=processor)
        counts = sim.run(transpiled, shots=shots).result().get_counts()
        summary = counts_summary(counts)
        record = {
            **metrics,
            "condition": condition,
            **{k: v for k, v in summary.items() if k != "counts"},
            "counts": counts,
            "shots": shots,
        }
        benchmark_rows.append(record)
        print(
            f"  {condition}: mean={summary['mean_cut']:.5f}, "
            f"r={summary['approx_ratio']:.5f}, "
            f"r_best={summary['best_approx_ratio']:.5f}, "
            f"P_opt={summary['p_opt']:.5f}, "
            f"best={summary['best_sampled_cut']:g}"
        )
        row = {
            "problem_id": "PS-O1",
            "processor": processor["name"].replace("Processor ", ""),
            "condition": condition,
            "executable": "true",
            "logical_qubits": metrics["logical_qubits"],
            "physical_qubits": metrics["physical_qubits"],
            "logical_cx": metrics["logical_cx"],
            "cx": metrics["cx"],
            "depth": metrics["depth"],
            "two_q_depth": metrics["two_q_depth"],
            "swaps": metrics["swaps"],
            "cx_overhead": metrics["cx_overhead"],
            "shots": shots,
            "quality_metric": "approx_ratio",
            "quality_value": f"{summary['approx_ratio']:.8f}",
            "p_opt": f"{summary['p_opt']:.8f}",
            "classical_optimum": C_STAR,
            "random_baseline": COST_MAX / 2,
            "best_sampled_cut": summary["best_sampled_cut"],
            "best_approx_ratio": f"{summary['best_approx_ratio']:.8f}",
            "mean_cut": f"{summary['mean_cut']:.8f}",
            "most_frequent_bitstring": summary["most_frequent_bitstring"],
            "reason": "",
        }
        csv_rows.append(row)

# Write official-format results CSV, retaining extra helpful columns.
results_csv = TABLES_DIR / "results.csv"
columns = [
    "problem_id", "processor", "condition", "executable", "logical_qubits",
    "physical_qubits", "logical_cx", "cx", "depth", "two_q_depth", "swaps",
    "cx_overhead", "shots", "quality_metric", "quality_value", "p_opt",
    "classical_optimum", "random_baseline", "best_sampled_cut",
    "best_approx_ratio", "mean_cut", "most_frequent_bitstring", "reason",
]
with open(results_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(csv_rows)

# Bell verification on D: one adjacent pair and a farthest-apart pair.
cm_d = official.coupling_map_from_edges(processor_d["edges"], processor_d["num_qubits"])
distances = []
for a in range(processor_d["num_qubits"]):
    for b in range(a + 1, processor_d["num_qubits"]):
        distances.append((cm_d.distance(a, b), a, b))
max_distance = max(item[0] for item in distances)
far_pair = next((a, b) for dist, a, b in distances if dist == max_distance)
adj_pair = tuple(processor_d["edges"][0])
bell_rows = []
print(f"\nBell experiment pairs on D: adjacent={adj_pair}; farthest={far_pair}; distance={max_distance}")
for pair_name, pair in (("adjacent", adj_pair), ("farthest", far_pair)):
    for noisy in (False, True):
        result = official.bell_experiment(processor_d, pair, noisy=noisy, shots=shots)
        row = {
            "processor": "D",
            "pair_type": pair_name,
            "q0": pair[0],
            "q1": pair[1],
            "pair_distance": result["pair_distance"],
            "condition": "noisy" if noisy else "ideal",
            "shots": result["shots"],
            "XX": result["XX"],
            "XX_se": result["XX_se"],
            "YY": result["YY"],
            "YY_se": result["YY_se"],
            "ZZ": result["ZZ"],
            "ZZ_se": result["ZZ_se"],
            "fidelity": result["fidelity"],
            "fidelity_se": result["fidelity_se"],
            "cx": result.get("cx", ""),
        }
        bell_rows.append(row)
        print(
            f"  {pair_name} {row['condition']}: XX={row['XX']:.4f}, "
            f"YY={row['YY']:.4f}, ZZ={row['ZZ']:.4f}, "
            f"F={row['fidelity']:.4f} ± {row['fidelity_se']:.4f}"
        )

bell_csv = TABLES_DIR / "bell.csv"
bell_columns = [
    "processor", "pair_type", "q0", "q1", "pair_distance", "condition",
    "shots", "XX", "XX_se", "YY", "YY_se", "ZZ", "ZZ_se",
    "fidelity", "fidelity_se", "cx",
]
with open(bell_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=bell_columns)
    writer.writeheader()
    writer.writerows(bell_rows)

output = {
    "problem_statement": "PS-O1",
    "num_vertices": n,
    "weighted_edges": [list(e) for e in weighted_edges],
    "total_edge_weight": COST_MAX,
    "qaoa_depth": 1,
    "classical_optimum": C_STAR,
    "optimal_bitstrings_x0_to_xn": OPTIMAL_BITS,
    "random_baseline_expected_cut": COST_MAX / 2,
    "random_baseline_approx_ratio": (COST_MAX / 2) / C_STAR,
    "initialization_runs": runs,
    "initialization_ratio_mean": float(np.mean(run_ratios)),
    "initialization_ratio_std": float(np.std(run_ratios, ddof=1)),
    "selected_parameters": {
        "seed": best["seed"],
        "gamma": best["gamma"],
        "beta": best["beta"],
        "ideal_expected_cut": best["expected_cut"],
        "optimizer": "COBYLA",
        "max_iterations": 100,
        "objective": "exact ideal Statevector expected cut",
    },
    "benchmark_settings": settings,
    "processor_results": benchmark_rows,
    "bell_results": bell_rows,
    "notes": [
        "All results are from local Aer simulation, not physical quantum hardware.",
        "Processor A is marked not executable because it has fewer qubits than PS-O1 requires.",
        "random_baseline is the expected cut for a uniformly random partition: half the total edge weight.",
    ],
}
output_path = BASE_DIR / "phase2_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, default=str)

print("\n" + "=" * 68)
print("FINISHED")
print("JSON:", output_path)
print("Results CSV:", results_csv)
print("Bell CSV:", bell_csv)
print("Starter files qff_phase2.py and instances.json were not modified.")
print("IMPORTANT: Results are simulator results, not hardware measurements.")
print("=" * 68)
