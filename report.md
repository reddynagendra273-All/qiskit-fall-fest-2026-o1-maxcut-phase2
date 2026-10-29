# QFF 2026 Phase 2 - PS-O1 Weighted Max-Cut Report

## 1. Problem and Objective

PS-O1 focuses on solving a weighted Max-Cut problem with six logical vertices. Each vertex is assigned to one of two partitions. An edge contributes its weight to the cut when its endpoints belong to different partitions. The objective is to maximize the total weight of the cut edges.

The locked instance contains nine weighted edges with a total edge weight of 27. Exhaustive evaluation of all 64 possible bitstrings gives an exact classical optimum of 22. Under the stated `x0...x5` bitstring convention, the two optimal bitstrings are `001011` and `110100`. They represent complementary partitions.

## 2. Method

This work uses the depth-one (p = 1) Quantum Approximate Optimization Algorithm (QAOA). The circuit parameters are optimized against an ideal statevector objective using COBYLA with five initial seeds (0-4). The gamma and beta parameters are searched over the interval [0, pi].

The selected parameters are then evaluated using the configured ideal and noisy simulation settings for the available processor topologies.

Processor A has five physical qubits and cannot execute the six-qubit logical circuit. It is therefore marked as not executable rather than assigned performance values. Processor B has nine physical qubits, while Processor D is the team-designed six-qubit topology.

## 3. Benchmark Results

The recorded simulation results are summarized below.

| Processor | Condition | Mean Cut | Approximation Ratio | Best Sampled Cut | P(Optimal Set) | CX Gates | Depth | SWAPs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| B | Ideal | 17.76196 | 0.80736 | 22 | 0.13965 | 21 | 37 | 1 |
| B | Noisy | 17.32202 | 0.78736 | 22 | 0.12598 | 21 | 37 | 1 |
| D | Ideal | 17.71338 | 0.80515 | 22 | 0.13843 | 18 | 29 | 0 |
| D | Noisy | 17.29614 | 0.78619 | 22 | 0.12500 | 18 | 29 | 0 |

The approximation ratio is calculated as the mean cut divided by the exact classical optimum of 22.

All values are simulator results, not measurements from physical quantum hardware. Under the configured noise model, both executable processors show a reduction in mean cut and probability of sampling an optimal solution.

Processor D uses three fewer transpiled CX gates than Processor B (18 versus 21), has no inserted SWAP gates (versus one), and has a lower circuit depth (29 versus 37).

However, Processor B has a slightly higher noisy mean cut in this run: 17.32202 compared with 17.29614 for Processor D. This small difference should not be overinterpreted because the results depend on the selected parameters, transpilation, random seeds, shot count, and noise model.

## 4. Classical and Random Baselines

The exact classical optimum is 22, and the total edge weight is 27.

For a uniformly random bipartition, each edge has a probability of 0.5 of being cut. Therefore, the expected random cut weight is:

Expected random cut weight = 27 x 0.5 = 13.5

The expected approximation ratio relative to the exact optimum is:

Expected random approximation ratio = 13.5 / 22 = 0.61364

The `results.csv` file records `random_baseline=13.5`, which represents the expected random cut weight. This is different from the per-edge cut probability of 0.5 and the expected approximation ratio of approximately 0.61364.

## 5. Bell-State Experiment on Processor D

The Bell-state experiment evaluates an adjacent qubit pair (0, 2) and a farthest qubit pair (0, 1) under ideal and noisy simulation conditions. The correlation and fidelity results are stored in `results/tables/bell.csv`.

| Pair | Condition | XX | YY | ZZ | Fidelity +/- SE |
|---|---|---:|---:|---:|---:|
| Adjacent (0,2) | Ideal | 1.0000 | -1.0000 | 1.0000 | 1.0000 +/- 0.0000 |
| Adjacent (0,2) | Noisy | 0.9458 | -0.9521 | 0.9551 | 0.9633 +/- 0.0021 |
| Farthest (0,1) | Ideal | 1.0000 | -1.0000 | 1.0000 | 1.0000 +/- 0.0000 |
| Farthest (0,1) | Noisy | 0.9443 | -0.9341 | 0.9385 | 0.9542 +/- 0.0023 |

The target Bell state is the Phi-plus state, written as |Phi+>. Its expected correlations are XX = +1, YY = -1, and ZZ = +1.

In the reported noisy simulation, the farthest pair has a lower fidelity than the adjacent pair. Additional routing operations may contribute to this difference. This is an interpretation of the simulated topology and should not be treated as a physical hardware measurement.

## 6. Limitations and Risks

- The results are simulator-based and depend on the QAOA parameters, transpilation settings, random seeds, shot count, and noise model.
- The p = 1 QAOA circuit is a limited-depth heuristic and is not guaranteed to find the exact optimum consistently.
- Although the optimal cut of 22 was sampled in the reported runs, the best sampled cut alone does not represent typical solution quality. Mean cut and probability of sampling an optimal solution are also reported.
- Python 3.14.7 was used in the current local environment, while the starter README specifies Python 3.10-3.12. The project should be tested in Python 3.12 before claiming reproducibility in the specified environment.
- The final Processor D configuration should be validated and kept consistent with the configuration used to generate the report and figures.
- All reported results should be regenerated from the final committed code before submission.

## 7. Reproduction Steps

1. Set up a supported Python 3.12 environment.
2. Install the project's pinned, tested dependencies.
3. Verify `processors/processor_D.json` and the locked problem instance against the official challenge materials.
4. Run `python solve_ps_o1_phase2.py` from the project root.
5. Open `main.ipynb` in Jupyter and run all cells from top to bottom.
6. Confirm that the CSV tables and PNG figures are generated and that their values agree with this report.
7. Include any AI-assistance disclosure required by the event rules.

## 8. AI-Assistance Disclosure

AI assistance was used to help structure the documentation, review the analysis, and prepare reproducibility materials. The team is responsible for reviewing, understanding, validating, and taking responsibility for all submitted code, results, and claims.
