"""Generate the min-max CVRP (homogeneous fleet) validation / test datasets.

Run once from the repository root before training or testing:

    python scripts/generate_cvrp_data.py

This writes data/cvrp/n{N}_m{M}_seed24610.npz for N in {50, 100, 200} and
M in {3, 5, 7}. N=200 is outside the training range on purpose: it is the
zero-shot generalisation cell of the benchmark.
"""

import os

from parco.data.generate import generate_dataset

DATA_DIR = "data"
SEED = 24610
DATASET_SIZE = 1280  # same as the HCVRP test sets
CAPACITY = 50.0  # single capacity shared by all vehicles, all problem sizes
SIZE_AGENTS = {50: [3, 5, 7], 100: [3, 5, 7], 200: [3, 5, 7]}

if __name__ == "__main__":
    problem = "cvrp"
    print(50 * "=" + f"\nGenerating instances for {problem.upper()}...\n" + 50 * "=")
    for graph_size, agent_counts in SIZE_AGENTS.items():
        for num_agents in agent_counts:
            fname = os.path.join(
                DATA_DIR,
                problem,
                f"n{graph_size}_m{num_agents}_seed{SEED}.npz",
            )
            print(f"Generating instances: N {graph_size}, m {num_agents} -> {fname}")
            generate_dataset(
                problem=problem,
                filename=fname,
                data_dir=DATA_DIR,
                seed=SEED,
                dataset_size=DATASET_SIZE,
                graph_sizes=graph_size,
                num_agents=num_agents,
                capacity=CAPACITY,
            )
