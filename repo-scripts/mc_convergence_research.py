"""Opt-in, analytically verifiable simulation-budget research for issue #148.

This is a synthetic research model, NOT a product sampler, hydrological
model, or RORBwin compatibility implementation. See the study report.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import math
import platform
import random
import statistics
import sys
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Any, cast

POLICY = "synthetic-response-v1/weighted-nearest-rank-v1"
ROOT_SEED = 1482026
DURATIONS = ("short", "long")
AEPS = (0.2, 0.1, 0.05, 0.02)
TP_PROBABILITY = 0.25
BANDS = (0.01, 0.02, 0.05)
ABS_TOLERANCE = 0.002  # dimensionless synthetic response units; not an engineering threshold
STAGE_VARIANTS: dict[str, tuple[tuple[int, int, str, str], ...]] = {
    "smoke": ((5, 4, "random_tp", "rank"),),
    "pilot": tuple((50, n, "random_tp", "rank") for n in (5, 10, 20, 50, 100, 200)),
    "confirmation": tuple((50, n, "random_tp", "rank") for n in (20, 50)),
    "bins": tuple((h, 1000 // h, "random_tp", "rank") for h in (25, 50, 100)),
    "tp": ((50, 20, "random_tp", "rank"), (50, 20, "paired_tp", "rank")),
    "interpolation": ((50, 20, "random_tp", "rank"), (50, 20, "random_tp", "linear")),
    "stable-independent-confirmation": tuple((50, n, "random_tp", "rank") for n in (5, 10, 20)),
}
REPLICATIONS = {
    "smoke": 2,
    "pilot": 30,
    "confirmation": 100,
    "bins": 30,
    "tp": 30,
    "interpolation": 30,
    "stable-independent-confirmation": 100,
}


@dataclass(frozen=True, slots=True)
class Response:
    """Q=max(0, slope*U+base+tp_bump*T-loss_width*V); U,V iid U(0,1)."""

    slope: float
    base: float
    tp_bump: float
    loss_width: float


# Two sites; deliberately includes a pronounced zero atom and near-tied duration maxima.
# Synthetic dimensionless outputs are NOT discharge [m3/s].
RESPONSES: dict[str, dict[str, Response]] = {
    "zero_atom": {
        "short": Response(1.0, -0.74, 0.12, 0.55),
        "long": Response(0.90, -0.64, 0.10, 0.55),
    },
    "near_tie": {
        "short": Response(1.20, -0.25, 0.09, 0.40),
        "long": Response(1.17, -0.225, 0.10, 0.40),
    },
}

# Deliberately low-variability NONDEGENERATE positive control, chosen in a separate
# exploratory screen. Confirmation uses fresh stage-derived streams. Do not infer
# that any real catchment has this population or tolerance.
STABLE_RESPONSES: dict[str, dict[str, Response]] = {
    "steady_site": {
        "short": Response(0.18, 1.0, 0.025, 0.08),
        "long": Response(0.16, 1.01, 0.020, 0.08),
    },
    "second_site": {
        "short": Response(0.14, 0.9, 0.030, 0.06),
        "long": Response(0.18, 0.88, 0.020, 0.09),
    },
}


def response_population(stage: str) -> dict[str, dict[str, Response]]:
    """Choose an immutable study population without mutating the baseline."""
    return STABLE_RESPONSES if stage == "stable-independent-confirmation" else RESPONSES


def _hinge_integral(x: float) -> float:
    """Antiderivative of clamp(x, 0, 1)."""
    if x <= 0.0:
        return 0.0
    if x < 1.0:
        return 0.5 * x * x
    return x - 0.5


def exact_survival(response: Response, peak: float, *, lower_u: float = 0.0, upper_u: float = 1.0) -> float:
    """Unnormalised P(Q>peak, lower_u<=U<upper_u), peak>=0, integrating V and TP exactly."""
    if not 0.0 <= lower_u <= upper_u <= 1.0 or peak < 0:
        message = "invalid integration range or peak"
        raise ValueError(message)
    result = 0.0
    for tp, probability in ((0, 1.0 - TP_PROBABILITY), (1, TP_PROBABILITY)):
        offset = response.base + response.tp_bump * tp - peak
        x0 = (response.slope * lower_u + offset) / response.loss_width
        x1 = (response.slope * upper_u + offset) / response.loss_width
        result += probability * response.loss_width / response.slope * (_hinge_integral(x1) - _hinge_integral(x0))
    return max(0.0, min(upper_u - lower_u, result))


def exact_quantile(response: Response, aep: float) -> float:
    """Find inf{q>=0: P(Q>q)<=aep}; exact integral, numerical bisection."""
    if not 0.0 < aep < 1.0:
        message = "AEP must be in (0, 1)"
        raise ValueError(message)
    if exact_survival(response, 0.0) <= aep:
        return 0.0
    left = 0.0
    right = response.slope + response.base + response.tp_bump
    for _ in range(70):
        mid = (left + right) / 2.0
        if exact_survival(response, mid) > aep:
            left = mid
        else:
            right = mid
    return (left + right) / 2.0


def endpoint_quantile_bounds(
    response: Response, aep: float, *, covered_upper_u: float = 0.98
) -> tuple[float, float | None]:
    """Conservative quantile bounds when U in (covered_upper_u, 1] is entirely unknown.

    The lower bound assigns no exceedances to missing mass; the upper bound
    allows all missing mass to exceed q. If AEP <= missing mass, no finite
    upper bound is asserted without an externally justified response support.
    """
    if not 0.0 < aep < 1.0 or not 0.0 < covered_upper_u < 1.0:
        message = "invalid AEP or incomplete upper endpoint"
        raise ValueError(message)
    missing = 1.0 - covered_upper_u

    def invert(target: float) -> float:
        if exact_survival(response, 0.0, upper_u=covered_upper_u) <= target:
            return 0.0
        low = 0.0
        high = max(0.0, response.slope + response.base + response.tp_bump)
        for _ in range(70):
            q = 0.5 * (low + high)
            if exact_survival(response, q, upper_u=covered_upper_u) > target:
                low = q
            else:
                high = q
        return 0.5 * (low + high)

    return invert(aep), invert(aep - missing) if aep > missing else None


def strata_edges(count: int) -> list[float]:
    """Equal z-bin spacing with unequal U masses; first/last bins cover all tails."""
    if count < 1:
        message = "at least one stratum is required"
        raise ValueError(message)
    normal = NormalDist()
    return [0.0, *(normal.cdf(-3.5 + 7.0 * i / count) for i in range(1, count)), 1.0]


def derive_seed(
    root: int, stage: str, replication: int, duration: str, strata: int, n: int, method: str, h: int
) -> int:
    """Stable stream-per-cell derivation, independent of worker/traversal order."""
    key = f"{POLICY}|{root}|{stage}|{replication}|{duration}|{strata}|{n}|{method}|{h}"
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:16], "big")


def weighted_quantile(peaks: list[tuple[float, float]], aep: float, *, method: str = "rank") -> float:
    """Research-only complete weighted inverse-CDF: rank or explicit linear variant."""
    if not peaks or not 0.0 < aep < 1.0:
        message = "missing peaks or invalid AEP"
        raise ValueError(message)
    if any(not math.isfinite(q) or q < 0.0 or not math.isfinite(w) or w <= 0.0 for q, w in peaks):
        message = "invalid or failed weighted event"
        raise ValueError(message)
    total = math.fsum(w for _, w in peaks)
    if abs(total - 1.0) > 1e-9:
        message = "missing probability mass: estimate is unavailable"
        raise ValueError(message)
    sorted_peaks = sorted(peaks, key=lambda pair: pair[0])
    target = (1.0 - aep) * total
    cumulative = 0.0
    last_q = 0.0
    for q, w in sorted_peaks:
        next_cumulative = cumulative + w
        if next_cumulative >= target - 1e-13:
            if method == "rank" or q == last_q:
                return q
            if method == "linear":
                fraction = max(0.0, min(1.0, (target - cumulative) / w))
                return last_q + fraction * (q - last_q)
            message = "unknown quantile method"
            raise ValueError(message)
        cumulative = next_cumulative
        last_q = q
    return sorted_peaks[-1][0]


def _evaluate(response: Response, u: float, v: float, tp: int) -> float:
    return max(0.0, response.slope * u + response.base + response.tp_bump * tp - response.loss_width * v)


def trial_peaks(
    *,
    root: int,
    stage: str,
    replication: int,
    duration: str,
    strata: int,
    n: int,
    tp_method: str,
    responses: dict[str, dict[str, Response]] | None = None,
) -> dict[str, list[tuple[float, float]]]:
    edges = strata_edges(strata)
    population = RESPONSES if responses is None else responses
    peaks: dict[str, list[tuple[float, float]]] = {site: [] for site in population}
    if tp_method == "paired_tp" and n % 2:
        message = "paired finite-TP integration requires an even allocation"
        raise ValueError(message)
    if tp_method not in {"random_tp", "paired_tp"}:
        message = "unknown finite-TP method"
        raise ValueError(message)
    for h in range(strata):
        low, high = edges[h : h + 2]
        mass = high - low
        # Reproducible scientific simulation; no cryptographic secrets are generated.
        rng = random.Random(derive_seed(root, stage, replication, duration, strata, n, tp_method, h))  # noqa: S311
        base_samples = n if tp_method == "random_tp" else n // 2
        for _ in range(base_samples):
            u = low + mass * rng.random()
            v = rng.random()
            tp_variants = (
                ((int(rng.random() < TP_PROBABILITY), mass / n),)
                if tp_method == "random_tp"
                else ((0, mass * (1 - TP_PROBABILITY) / base_samples), (1, mass * TP_PROBABILITY / base_samples))
            )
            for tp, weight in tp_variants:
                for site, response_by_duration in population.items():
                    peaks[site].append((_evaluate(response_by_duration[duration], u, v, tp), weight))
    return peaks


def one_trial(
    *,
    root: int,
    stage: str,
    replication: int,
    strata: int,
    n: int,
    tp_method: str,
    quantile_method: str,
    responses: dict[str, dict[str, Response]] | None = None,
) -> list[dict[str, Any]]:
    """Produce every site/duration/AEP and their envelope, with complete mass."""
    population = RESPONSES if responses is None else responses
    measured: dict[tuple[str, str, float], float] = {}
    for duration in DURATIONS:
        for site, peak_weights in trial_peaks(
            root=root,
            stage=stage,
            replication=replication,
            duration=duration,
            strata=strata,
            n=n,
            tp_method=tp_method,
            responses=population,
        ).items():
            for aep in AEPS:
                measured[(site, duration, aep)] = weighted_quantile(peak_weights, aep, method=quantile_method)
    rows: list[dict[str, Any]] = []
    for site, response_by_duration in population.items():
        for aep in AEPS:
            reference_by_duration = {d: exact_quantile(response_by_duration[d], aep) for d in DURATIONS}
            chosen_duration = max(DURATIONS, key=lambda d: measured[(site, d, aep)])
            ref_duration = max(DURATIONS, key=lambda d: reference_by_duration[d])
            for duration in (*DURATIONS, "envelope"):
                estimate = (
                    measured[(site, chosen_duration, aep)]
                    if duration == "envelope"
                    else measured[(site, duration, aep)]
                )
                exact = (
                    reference_by_duration[ref_duration] if duration == "envelope" else reference_by_duration[duration]
                )
                rows.append(
                    {
                        "site": site,
                        "duration": duration,
                        "aep": aep,
                        "estimate": estimate,
                        "exact": exact,
                        "error": estimate - exact,
                        "critical_duration": chosen_duration if duration == "envelope" else "",
                        "exact_critical_duration": ref_duration if duration == "envelope" else "",
                        "zero_probability": None
                        if duration == "envelope"
                        else 1.0 - exact_survival(response_by_duration[duration], 0.0),
                    }
                )
    return rows


def _optional_scipy_binomial_tail(k: int, n: int, p: float) -> float | None:
    """Research-only regularized beta tail; None when the extra is absent."""
    try:
        special = importlib.import_module("scipy.special")
    except ModuleNotFoundError as exc:
        if exc.name != "scipy":
            raise
        return None
    beta_tail = cast("Callable[[float, float, float], float]", special.betainc)
    return float(beta_tail(k, n - k + 1, p))


def binomial_upper_tail(k: int, n: int, p: float) -> float:
    """P(Binomial(n,p)>=k) without underflow at high replication counts.

    Sum the tail away from the binomial mode, starting from its log-PMF.
    The former p**n/(1-p)**n recurrence silently returned 0 or 1
    around the mode for large n. Optional SciPy improves accuracy for very
    large n via its regularized incomplete-beta implementation.
    """
    if not 0 <= k <= n or not math.isfinite(p) or not 0.0 <= p <= 1.0:
        message = "invalid binomial arguments"
        raise ValueError(message)
    if k == 0 or p == 1.0:
        return 1.0
    if p == 0.0:
        return 0.0
    if n >= 1_000_000:
        scipy_tail = _optional_scipy_binomial_tail(k, n, p)
        if scipy_tail is not None:
            return scipy_tail
    return _stdlib_binomial_upper_tail(k, n, p)


def _stdlib_binomial_upper_tail(k: int, n: int, p: float) -> float:
    """Sum the smaller binomial tail from a log-PMF without optional SciPy."""
    use_upper = k > n * p
    edge = k if use_upper else k - 1
    log_term = (
        math.lgamma(n + 1)
        - math.lgamma(edge + 1)
        - math.lgamma(n - edge + 1)
        + edge * math.log(p)
        + (n - edge) * math.log1p(-p)
    )
    term = math.exp(log_term)
    total = term
    if use_upper:
        odds = p / (1.0 - p)
        for x in range(edge, n):
            term *= (n - x) * odds / (x + 1)
            total += term
            if term <= total * 1e-16:
                break
        return min(1.0, total)
    odds = (1.0 - p) / p
    for x in range(edge, 0, -1):
        term *= x * odds / (n - x + 1)
        total += term
        if term <= total * 1e-16:
            break
    return max(0.0, 1.0 - total)


def lower_confidence_bound(successes: int, trials: int, alpha: float = 0.05) -> float:
    """Exact one-sided Clopper-Pearson lower bound (not normal/Wald)."""
    if not 0 <= successes <= trials or trials < 1 or not 0 < alpha < 1:
        message = "invalid confidence-bound arguments"
        raise ValueError(message)
    if successes == 0:
        return 0.0
    if successes == trials:
        return math.exp(math.log(alpha) / trials)
    low, high = 0.0, 1.0
    for _ in range(65):
        mid = (low + high) / 2
        if binomial_upper_tail(successes, trials, mid) > alpha:
            high = mid
        else:
            low = mid
    return (low + high) / 2


def upper_confidence_bound(successes: int, trials: int, alpha: float = 0.05) -> float:
    """Exact one-sided Clopper-Pearson upper bound, for rejection of adequacy."""
    if not 0 <= successes <= trials or trials < 1 or not 0 < alpha < 1:
        message = "invalid confidence-bound arguments"
        raise ValueError(message)
    if successes == trials:
        return 1.0
    if successes == 0:
        return -math.expm1(math.log(alpha) / trials)
    low, high = 0.0, 1.0
    for _ in range(65):
        mid = (low + high) / 2
        if binomial_upper_tail(successes + 1, trials, mid) > 1 - alpha:
            high = mid
        else:
            low = mid
    return (low + high) / 2


def sd_bootstrap_interval(values: list[float], seed_key: str, *, resamples: int = 400) -> tuple[float, float]:
    """Percentile bootstrap 95% interval for spread of ONE production run.

    Resample independent complete replications, never individual stratified events.
    This is diagnostic and not a rigorous simultaneous multi-output interval.
    """
    if len(values) < 2 or resamples < 20:
        message = "requires at least two replications and 20 resamples"
        raise ValueError(message)
    seed = int.from_bytes(hashlib.sha256(seed_key.encode("utf-8")).digest()[:16], "big")
    # Scientific bootstrap reuses seeded pseudorandom numbers, not cryptographic entropy.
    rng = random.Random(seed)  # noqa: S311
    estimates: list[float] = []
    for _ in range(resamples):
        drawn = rng.choices(values, k=len(values))
        estimates.append(statistics.stdev(drawn))
    estimates.sort()
    return estimates[int(0.025 * resamples)], estimates[math.ceil(0.975 * resamples) - 1]


def _variant_key(strata: int, n: int, tp_method: str, quantile_method: str) -> str:
    return f"h{strata}-n{n}-{tp_method}-{quantile_method}"


def _run_stage(
    stage: str, root: int, replications: int, budget: int, wall_cap: float
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    variants = STAGE_VARIANTS[stage]
    population = response_population(stage)
    requested = sum(strata * n * len(DURATIONS) * replications for strata, n, _, _ in variants)
    if requested > budget:
        message = f"requested {requested} evaluations exceeds explicit {budget} cap"
        raise ValueError(message)
    start = time.perf_counter()
    raw: list[dict[str, Any]] = []
    timing: list[dict[str, Any]] = []
    tracemalloc.start()
    try:
        for strata, n, tp_method, quantile_method in variants:
            key = _variant_key(strata, n, tp_method, quantile_method)
            for replication in range(replications):
                if time.perf_counter() - start > wall_cap:
                    message = "wall-time cap reached; incomplete stage is not publishable"
                    raise TimeoutError(message)
                tracemalloc.reset_peak()
                t0 = time.perf_counter()
                trial_rows = one_trial(
                    root=root,
                    stage=stage,
                    replication=replication,
                    strata=strata,
                    n=n,
                    tp_method=tp_method,
                    quantile_method=quantile_method,
                    responses=population,
                )
                elapsed = time.perf_counter() - t0
                _, peak_bytes = tracemalloc.get_traced_memory()
                timing.append(
                    {
                        "variant": key,
                        "replication": replication,
                        "elapsed_seconds": elapsed,
                        "peak_traced_mib": peak_bytes / (1024 * 1024),
                        "evaluations": strata * n * 2,
                    }
                )
                raw.extend({"variant": key, "replication": replication, **row} for row in trial_rows)
    finally:
        tracemalloc.stop()
    return raw, {"total_evaluations": requested, "wall_seconds": time.perf_counter() - start, "timing": timing}


def _summarise(raw: list[dict[str, Any]], timing: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str, float], list[dict[str, Any]]] = {}
    for row in raw:
        grouped.setdefault((row["variant"], row["site"], row["duration"], row["aep"]), []).append(row)
    metrics: list[dict[str, Any]] = []
    for (variant, site, duration, aep), rows in sorted(grouped.items()):
        estimates = [row["estimate"] for row in rows]
        exact = rows[0]["exact"]
        errors = [row["error"] for row in rows]
        abs_errors = sorted(abs(e) for e in errors)
        spread = statistics.stdev(estimates) if len(estimates) > 1 else 0.0
        sd_interval = sd_bootstrap_interval(estimates, f"{variant}|{site}|{duration}|{aep}")
        critical = {d: sum(row["critical_duration"] == d for row in rows) for d in DURATIONS}
        metrics.append(
            {
                "variant": variant,
                "site": site,
                "duration": duration,
                "aep": aep,
                "exact": exact,
                "mean": statistics.fmean(estimates),
                "sd_single_run": spread,
                "sd_bootstrap_95pct_interval": sd_interval,
                "cv_single_run": spread / abs(statistics.fmean(estimates)) if statistics.fmean(estimates) else None,
                "mean_bias": statistics.fmean(errors),
                "max_abs_error": max(abs_errors),
                "p90_abs_error": abs_errors[math.ceil(0.9 * len(abs_errors)) - 1],
                "n_replications": len(rows),
                "critical_duration_counts": critical if duration == "envelope" else {},
                "critical_duration_long_probability_95pct_interval": [
                    lower_confidence_bound(critical["long"], len(rows), 0.025),
                    upper_confidence_bound(critical["long"], len(rows), 0.025),
                ]
                if duration == "envelope"
                else None,
            }
        )
    whole: list[dict[str, Any]] = []
    keys = sorted({row["variant"] for row in raw})
    for variant in keys:
        group = [row for row in raw if row["variant"] == variant]
        repls = sorted({row["replication"] for row in group})
        passes = {str(band): 0 for band in BANDS}
        for replication in repls:
            rows = [row for row in group if row["replication"] == replication]
            for band in BANDS:
                if all(abs(row["error"]) <= max(ABS_TOLERANCE, band * abs(row["exact"])) for row in rows):
                    passes[str(band)] += 1
        variant_times = [row for row in timing if row["variant"] == variant]
        whole.append(
            {
                "variant": variant,
                "replications": len(repls),
                "pass_count_by_band": passes,
                "pass_rate_by_band": {band: count / len(repls) for band, count in passes.items()},
                "one_sided_95pct_lower_by_band": {
                    band: lower_confidence_bound(count, len(repls)) for band, count in passes.items()
                },
                "one_sided_95pct_upper_by_band": {
                    band: upper_confidence_bound(count, len(repls)) for band, count in passes.items()
                },
                "mean_seconds_per_run": statistics.fmean(row["elapsed_seconds"] for row in variant_times),
                "peak_traced_mib": max(row["peak_traced_mib"] for row in variant_times),
                "evaluations_per_run": variant_times[0]["evaluations"],
            }
        )
    return {"metrics": metrics, "whole_run": whole}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")


def run(
    stage: str,
    output: Path,
    *,
    root: int,
    replications: int | None,
    max_evaluations: int,
    max_wall_seconds: float,
    opt_in: bool,
) -> None:
    if stage != "smoke" and not opt_in:
        message = "non-smoke research stages require --opt-in"
        raise ValueError(message)
    if max_evaluations < 1 or max_wall_seconds <= 0:
        message = "positive explicit cost caps are required"
        raise ValueError(message)
    if output.exists():
        message = "research output directory must not exist (immutable result batches)"
        raise FileExistsError(message)
    count = REPLICATIONS[stage] if replications is None else replications
    if count < 2:
        message = "at least two independent replications required"
        raise ValueError(message)
    output.mkdir(parents=True)
    raw, performance = _run_stage(stage, root, count, max_evaluations, max_wall_seconds)
    summary = _summarise(raw, performance["timing"])
    with (output / "raw.csv").open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(raw[0]))
        writer.writeheader()
        writer.writerows(raw)
    _write_json(output / "summary.json", summary)
    population = response_population(stage)
    endpoints: list[dict[str, Any]] = []
    for site, durations in population.items():
        for duration, response in durations.items():
            for aep in AEPS:
                low, high = endpoint_quantile_bounds(response, aep)
                endpoints.append(
                    {
                        "site": site,
                        "duration": duration,
                        "aep": aep,
                        "known_probability_mass": 0.98,
                        "unmodelled_upper_probability_mass": 0.02,
                        "exact_complete_population_quantile": exact_quantile(response, aep),
                        "possible_quantile_lower": low,
                        "possible_quantile_upper": high,
                        "status": "unresolved_missing_tail",
                    }
                )
    _write_json(
        output / "endpoint_sensitivity.json",
        {"examples": endpoints, "note": "Bounds assume unknown missing mass, not that the actual tail has zero flow."},
    )
    _write_json(
        output / "manifest.json",
        {
            "policy": POLICY,
            "stage": stage,
            "variants": STAGE_VARIANTS[stage],
            "root_seed": root,
            "replications_per_variant": count,
            "distinct_replicates_across_stages": True,
            "stream_derivation": "SHA256(policy|root|stage|rep|duration|strata|n|tp_method|h) first 128 bits; MT19937 Python random.Random",
            "events_per_duration_and_scenario": [h * n for h, n, _, _ in STAGE_VARIANTS[stage]],
            "total_evaluations": performance["total_evaluations"],
            "wall_seconds": performance["wall_seconds"],
            "traced_peak_mib": max(t["peak_traced_mib"] for t in performance["timing"]),
            "absolute_tolerance": ABS_TOLERANCE,
            "relative_bands": BANDS,
            "whole_result_outputs": "all 2 sites x 4 AEPs x (2 durations + duration envelope) = 24 estimates",
            "required_pass_probability_study_setting": 0.95,
            "one_sided_confidence_study_setting": 0.95,
            "interpolation": "weighted nearest rank except linear sensitivity",
            "bin_boundaries": "equal standard-normal coordinate -3.5 to +3.5; outer bins extended to U=0 and U=1",
            "zero_runoff": "retained",
            "failed_mass": 0.0,
            "missing_mass": 0.0,
            "modelled_mass": 1.0,
            "response_parameters": {s: {d: asdict(r) for d, r in dd.items()} for s, dd in population.items()},
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "note": "Synthetic dimensionless study only; not RORB or a rainfall AEP-to-flow mapping acceptance",
        },
    )
    print(
        json.dumps(
            {
                "stage": stage,
                "reps": count,
                "output": str(output),
                "evaluations": performance["total_evaluations"],
                "wall_seconds": performance["wall_seconds"],
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=tuple(STAGE_VARIANTS), default="smoke")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root-seed", type=int, default=ROOT_SEED)
    parser.add_argument("--replications", type=int)
    parser.add_argument("--max-evaluations", type=int, default=1_200_000)
    parser.add_argument("--max-wall-seconds", type=float, default=180.0)
    parser.add_argument("--opt-in", action="store_true")
    args = parser.parse_args()
    run(
        args.stage,
        args.output,
        root=args.root_seed,
        replications=args.replications,
        max_evaluations=args.max_evaluations,
        max_wall_seconds=args.max_wall_seconds,
        opt_in=args.opt_in,
    )


if __name__ == "__main__":
    main()
