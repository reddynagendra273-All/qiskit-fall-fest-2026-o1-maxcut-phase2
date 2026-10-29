

## Team PS-O1 work (additions)

- `solve_ps_o1_phase2.py` runs the p=1 QAOA optimization and simulator benchmark.
- `main.ipynb` loads the generated results, creates benchmark/topology/Bell plots, and performs sanity checks.
- `data/instance.json` records the PS-O1 graph and known classical baseline for documentation; verify it against the official locked `instances.json` before submission.
- `processors/processor_A.json` and `processors/processor_B.json` document the official topologies used in the comparison. Keep the official helper file `qff_phase2.py` unchanged.
- `report.md` summarizes the current simulator run. Re-run the solver and notebook before final submission and ensure all reported values match the regenerated artifacts.

**Reproducibility caution:** the challenge kit README specifies Python 3.10–3.12. The currently reported local Python version is 3.14.7, so repeat the full run in Python 3.12 before claiming official-environment reproducibility. All reported results are simulator results, not hardware measurements.

**AI assistance:** AI tools assisted with documentation and analysis. The team must review and verify all artifacts before submission.
