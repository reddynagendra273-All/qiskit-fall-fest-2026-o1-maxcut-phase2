# QFF 2026 Phase 2 — PS-O1 Weighted Max-Cut

This project contains our Phase 2 implementation and saved benchmark results for PS-O1, a weighted Max-Cut optimization problem. The project uses the Quantum Approximate Optimization Algorithm (QAOA), classical parameter optimization, processor-topology analysis, and ideal and noisy simulator experiments.

## 1. Problem Summary

The problem instance contains six logical vertices and nine weighted edges, with a total edge weight of 27.

Exhaustive evaluation of all 64 possible bitstrings gives an exact classical optimum cut weight of **22**. Under the project's stated bitstring convention, the optimal bitstrings are `001011` and `110100`, representing complementary partitions.

## 2. Benchmark Results

The following results were recorded for executable processor configurations.

| Processor | Condition | Mean Cut | Approximation Ratio | CX Gates | Circuit Depth | SWAPs |
|---|---|---:|---:|---:|---:|---:|
| B | Ideal | 17.76196 | 0.80736 | 21 | 37 | 1 |
| B | Noisy | 17.32202 | 0.78736 | 21 | 37 | 1 |
| D | Ideal | 17.71338 | 0.80515 | 18 | 29 | 0 |
| D | Noisy | 17.29614 | 0.78619 | 18 | 29 | 0 |

The approximation ratio is calculated as the mean cut divided by the exact classical optimum of 22.

Processor A is not executable for this instance because it provides five physical qubits, while the problem requires six logical qubits.

All reported values are from simulation, not measurements from physical quantum hardware. In these results, Processor D uses three fewer transpiled CX gates than Processor B, requires no inserted SWAP gates, and has a lower circuit depth. Processor B has a slightly higher noisy mean cut in this simulation, so circuit efficiency and solution quality should be considered separately.

## 3. Classical and Random Baselines

The exact classical optimum is **22**.

For a uniformly random bipartition, each edge has a probability of 0.5 of crossing the cut. Since the total edge weight is 27, the expected random cut weight is:

- Expected random cut: **13.5**
- Expected random approximation ratio: **13.5 / 22 ≈ 0.61364**

These values provide a reference for evaluating the QAOA results. The mean cut describes average performance across samples, while the best sampled cut describes the best solution observed. Finding an optimal bitstring in some shots does not mean that every shot is optimal.

## 4. QAOA Method

The implementation uses QAOA with circuit depth parameter **p = 1** and a weighted Max-Cut objective.

The classical optimizer uses COBYLA with a maximum of 100 iterations per initialization. Five initial parameter seeds, numbered 0 through 4, are used. Initial gamma and beta parameters are sampled uniformly from the interval [0, π].

The selected parameters are evaluated on the executable processor configurations under ideal and noisy simulation settings. Benchmark evaluations use 4096 shots.

## 5. Processor D Design

Processor D is a team-defined six-qubit processor configuration. Its topology is intended to support the weighted graph's problem interactions while reducing routing overhead.

The saved benchmark results show 18 transpiled CX gates, circuit depth 29, and zero inserted SWAP gates for Processor D. Processor B uses 21 CX gates, depth 37, and one SWAP gate in the same reported benchmark.

These metrics indicate lower circuit-resource requirements for Processor D in this run. They do not establish that Processor D is universally better, because solution quality and noise also affect the results.

The processor configuration and topology should be validated against the official Phase 2 requirements before final submission.

## 6. Bell-State Results

The saved Bell benchmark evaluates adjacent and farthest qubit pairs under ideal and noisy simulation conditions, using 4096 shots.

For an ideal Bell state, the expected correlations are XX = +1, YY = -1, and ZZ = +1. The noisy results show reduced correlations and lower estimated fidelity, particularly for the farthest pair.

These are simulator results under the configured noise model, not physical-hardware measurements.

Detailed Bell correlations and standard errors are recorded in `results/tables/bell.csv`.

## 7. Project Files

- `solve_ps_o1_phase2.py` — QAOA optimization and processor benchmark workflow.
- `qff_phase2.py` — challenge-provided helper module; retain the supplied version.
- `instances.json` — problem and benchmark configuration.
- `data/instance.json` — problem instance data.
- `processors/processor_A.json` — Processor A configuration.
- `processors/processor_B.json` — Processor B configuration.
- `processors/processor_D.json` — team-defined Processor D configuration.
- `processor_D_template.json` — Processor D template.
- `results/tables/results.csv` — saved processor benchmark results.
- `results/tables/bell.csv` — saved Bell-state correlations and standard errors.
- `results/figures/` — generated benchmark visualizations.
- `main.ipynb` — notebook for inspecting saved results and plots.
- `report.md` — detailed Phase 2 report.
- `requirements.txt` — project dependencies.
- `requirements-pinned-candidate.txt` — candidate pinned dependency versions.
- `example_usage.py` — example usage of the project utilities.

## 8. Setup and Reproduction

The challenge instructions specify Python 3.10–3.12. The environment used for the currently saved results was Python 3.14.7, so compatibility and reproducibility should be validated in a supported Python version before final submission.

Install the project dependencies from this directory:

```bash
python -m pip install -r requirements.txt
```

To run the benchmark from this standalone repository's root directory:

```bash
python solve_ps_o1_phase2.py
```

After the script completes, open `main.ipynb` in Jupyter or VS Code and run the notebook cells from this directory so its relative paths resolve correctly.

**Caution:** Re-running the solver may regenerate result files. Preserve the current saved results if you need to retain the benchmark run documented above.

## 9. Limitations

- The reported experiments use simulators rather than physical quantum processors.
- QAOA with p = 1 explores a limited parameterized circuit family.
- The best sampled cut is not representative of average performance by itself.
- Python 3.12 compatibility and complete reproduction of the saved results have not yet been verified.
- Processor D's final configuration should be checked against the official topology and noise requirements.

## 10. AI Assistance Disclosure

AI tools were used to assist with documentation structure, explanation, and review of the benchmark presentation. The team is responsible for checking the implementation, verifying results, and ensuring that the final submission follows the official challenge requirements.
