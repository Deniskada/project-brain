from __future__ import annotations

import argparse
import os

from .architecture_parser import ArchitectureParser
from .storage import ArchitectureStorage


def main() -> None:
    parser = argparse.ArgumentParser(description="Build architecture graph and store it")
    parser.add_argument(
        "--project",
        default=os.getenv("PROJECT_PATH", "/projects/staffprobot"),
        help="Path to project to analyze",
    )
    parser.add_argument(
        "--snapshot-dir",
        default=os.getenv("ARCH_SNAPSHOT_DIR", "data"),
        help="Directory to write JSON snapshots",
    )
    args = parser.parse_args()

    arch = ArchitectureParser(project_path=args.project)
    graph = arch.parse()

    storage = ArchitectureStorage()
    storage.save_graph_to_redis(graph)
    storage.save_graph_to_chroma(graph)
    path = storage.snapshot_graph_json(graph, directory=args.snapshot_dir)
    print(f"Saved graph: nodes={graph.stats['total_nodes']} edges={graph.stats['total_edges']} snapshot={path}")


if __name__ == "__main__":
    main()


