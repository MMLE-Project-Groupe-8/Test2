from basic_client import BioreactorClient, USER, PASSWORD
import math
import argparse
import statistics
from typing import List


def _extract_Y(res):
	"""Try to extract a numeric Y value from the API response dict.

	Heuristics: prefer keys 'Y' or 'y', then search for the first numeric
	value in the top-level dict or one-level nested dicts.
	"""
	if not isinstance(res, dict):
		return None
	for key in ("Y", "y", "yield", "output", "Output"):
		if key in res:
			v = res[key]
			if isinstance(v, (int, float)):
				return float(v)
			try:
				return float(v)
			except Exception:
				pass
	for v in res.values():
		if isinstance(v, (int, float)):
			return float(v)
		if isinstance(v, dict):
			for v2 in v.values():
				if isinstance(v2, (int, float)):
					return float(v2)
	return None


def sweep_and_collect(client: BioreactorClient, temps: List[float], repeats: int, **recipe_kwargs):
	means = []
	stdevs = []
	counts = []
	for T in temps:
		print(f"Running T={T} (repeats={repeats})...")
		samples = []
		for i in range(repeats):
			try:
				result = client.run("micro", T=float(T), **recipe_kwargs)
			except Exception as e:
				print(f"  run {i+1}/{repeats} failed: {e}")
				continue
			y = _extract_Y(result)
			if y is None:
				print(f"  run {i+1}/{repeats}: could not extract Y from response: {result}")
			else:
				samples.append(y)
				print(f"  run {i+1}/{repeats}: Y={y}")
		if len(samples) == 0:
			means.append(float('nan'))
			stdevs.append(float('nan'))
			counts.append(0)
		else:
			m = statistics.mean(samples)
			s = statistics.stdev(samples) if len(samples) > 1 else 0.0
			means.append(m)
			stdevs.append(s)
			counts.append(len(samples))
	return means, stdevs, counts


def main():
	p = argparse.ArgumentParser(description="Sweep temperature and plot Y vs T with error bars")
	p.add_argument("--start", type=float, default=20.0, help="start temperature")
	p.add_argument("--end", type=float, default=60.0, help="end temperature")
	p.add_argument("--steps", type=int, default=11, help="number of temperature steps between start and end (inclusive)")
	p.add_argument("--repeats", type=int, default=3, help="how many runs per temperature")
	p.add_argument("--pH", type=float, default=6.5)
	p.add_argument("--F1", type=float, default=0.5)
	p.add_argument("--F2", type=float, default=0.5)
	p.add_argument("--F3", type=float, default=0.5)
	p.add_argument("--no-plot", action="store_true", help="do not show plot; just print results")
	args = p.parse_args()

	if args.steps < 2:
		raise SystemExit("--steps must be >= 2")
	if args.repeats < 1:
		raise SystemExit("--repeats must be >= 1")

	temps = [args.start + i * (args.end - args.start) / (args.steps - 1) for i in range(args.steps)]

	client = BioreactorClient()
	client.login(USER, PASSWORD)

	means, stdevs, counts = sweep_and_collect(
		client, temps, args.repeats, pH=args.pH, F1=args.F1, F2=args.F2, F3=args.F3
	)

	# compute standard error of the mean (std / sqrt(n)) where possible
	sems = []
	for s, n in zip(stdevs, counts):
		if n <= 1:
			sems.append(0.0 if n == 1 else float('nan'))
		else:
			sems.append(s / math.sqrt(n))

	print("\nSummary (T, mean Y, stdev, sem, n):")
	for T, m, s, se, n in zip(temps, means, stdevs, sems, counts):
		print(f"  {T:.3g}\t{m:.6g}\t{s:.6g}\t{se:.6g}\t{n}")

	if args.no_plot:
		return

	try:
		import matplotlib.pyplot as plt
	except Exception:
		print("matplotlib not available; skipping plot. Use --no-plot to suppress this message.")
		return

	# filter out temperatures with NaN means
	temps_plot = []
	means_plot = []
	sems_plot = []
	for T, m, se in zip(temps, means, sems):
		if m is None or (isinstance(m, float) and math.isnan(m)):
			continue
		temps_plot.append(T)
		means_plot.append(m)
		sems_plot.append(se)

	plt.errorbar(temps_plot, means_plot, yerr=sems_plot, marker='o', linestyle='-')
	plt.xlabel("Temperature (T)")
	plt.ylabel("Y (mean)")
	plt.title("Y vs Temperature (error bars = SEM)")
	plt.grid(True)
	plt.tight_layout()
	plt.show()


if __name__ == '__main__':
	main()