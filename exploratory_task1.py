import argparse
import csv
import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from API_group08_with_password import BioreactorClient, USER, PASSWORD, BASE_URL

SCALE_ORDER = ["micro", "bench", "pilot"]
VARIABLE_RANGES = {
    "T": (20.0, 60.0),
    "pH": (3.0, 9.5),
    "F1": (0.0, 2.0),
    "F2": (0.0, 2.0),
    "F3": (0.0, 2.0),
}
DEFAULT_RECIPE = {
    "T": 40.0,
    "pH": 6.25,
    "F1": 1.0,
    "F2": 1.0,
    "F3": 1.0,
}

RESULTS_CSV = Path("exploratory_task1_results.csv")
PLOT_FILE = Path("exploratory_task1_plot.png")


def extract_observation(result: dict) -> tuple[float, float]:
    """Extract Y and cost from the API response."""
    y = None
    cost = None
    if isinstance(result, dict):
        y = result.get("Y")
        if y is None:
            y = result.get("y")
        if y is None:
            y = result.get("product")
        if y is None:
            y = result.get("amount")
        if y is None and "result" in result:
            y = result["result"].get("Y") if isinstance(result["result"], dict) else None

        cost = result.get("cost")
        if cost is None:
            cost = result.get("Cost")
        if cost is None and "result" in result:
            cost = result["result"].get("cost") if isinstance(result["result"], dict) else None

    if y is None or cost is None:
        raise ValueError(f"Unable to parse API response for Y and cost: {json.dumps(result)}")

    return float(y), float(cost)


def run_exploration(client: BioreactorClient, n_points: int = 5, wait_seconds: float = 0.2) -> list[dict]:
    results = []
    for scale in SCALE_ORDER:
        for variable, (low, high) in VARIABLE_RANGES.items():
            grid = np.linspace(low, high, n_points)
            print(f"Exploring {variable} on {scale} scale ({n_points} points)")
            for value in grid:
                recipe = DEFAULT_RECIPE.copy()
                recipe[variable] = float(value)
                result = client.run(scale=scale, **recipe)
                y, cost = extract_observation(result)
                row = {
                    "scale": scale,
                    "variable": variable,
                    "value": float(value),
                    "Y": y,
                    "cost": cost,
                    **recipe,
                }
                results.append(row)
                print(
                    f"  {scale:5s} {variable:2s}={value:6.3f} -> Y={y:.4f}, cost={cost:.2f}"
                )
                time.sleep(wait_seconds)
    return results


def save_results(results: list[dict], path: Path) -> None:
    if not results:
        return
    fieldnames = list(results[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved exploratory results to {path}")


def plot_results(results: list[dict], path: Path) -> None:
    fig, axes = plt.subplots(len(VARIABLE_RANGES), 1, figsize=(10, 18), constrained_layout=True)
    if len(VARIABLE_RANGES) == 1:
        axes = [axes]

    for ax, (variable, (low, high)) in zip(axes, VARIABLE_RANGES.items()):
        for scale in SCALE_ORDER:
            scale_results = [r for r in results if r["scale"] == scale and r["variable"] == variable]
            scale_results.sort(key=lambda r: r["value"])
            x = [r["value"] for r in scale_results]
            y = [r["Y"] for r in scale_results]
            ax.plot(x, y, marker="o", label=scale)
        ax.set_title(f"Dependence of Y on {variable}")
        ax.set_xlabel(variable)
        ax.set_ylabel("Y")
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.legend()

    fig.suptitle("Exploratory dependence of Y on recipe variables at each scale", fontsize=16)
    fig.savefig(path, dpi=200)
    print(f"Saved plot to {path}")
    plt.show()


def summarize_results(results: list[dict]) -> None:
    summary = {}
    for row in results:
        scale = row["scale"]
        summary.setdefault(scale, []).append(row["Y"])
    print("\nSummary by scale:")
    for scale in SCALE_ORDER:
        values = summary.get(scale, [])
        if not values:
            continue
        print(
            f"  {scale:6s}: runs={len(values)}, mean_Y={np.mean(values):.4f}, "
            f"std_Y={np.std(values, ddof=1):.4f}, min_Y={np.min(values):.4f}, max_Y={np.max(values):.4f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a small exploratory campaign and visualize the dependence of Y on recipe variables at each scale."
    )
    parser.add_argument(
        "--points",
        type=int,
        default=5,
        help="Number of values per recipe variable to probe (default: 5)",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=0.2,
        help="Seconds to wait between API requests (default: 0.2)",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not display the plot interactively.",
    )
    args = parser.parse_args()

    client = BioreactorClient(BASE_URL)
    client.login(USER, PASSWORD)
    print("Logged in successfully.")

    results = run_exploration(client, n_points=args.points, wait_seconds=args.wait)
    save_results(results, RESULTS_CSV)
    summarize_results(results)
    plot_results(results, PLOT_FILE)

    if args.no_show:
        plt.close("all")


if __name__ == "__main__":
    main()
