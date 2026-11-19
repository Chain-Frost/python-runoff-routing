"""Read-only, research-exposed CMD 6.44 v6 routing and ordered network execution.

The stored candidate is a transcription of owner-authorised reconstructed procedures,
not independent native decoding. No filesystem or process effects occur in these kernels.
"""

import math
from dataclasses import dataclass
from itertools import pairwise

from .geometry import Geometry, ReachGeometry
from .models import Event
from .power import bounded_power
from .precision import UnsupportedNumericPath, internal_store, safe64, store
from .preparation import Preparation


@dataclass(frozen=True, slots=True)
class State:
    """Actual accepted Q/S (binary32), plus target-dependent binary64 residual."""

    q: float
    s: float
    r: float


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    """An actually executed alternating-coordinate candidate update."""

    iteration: int
    coordinate: str
    trial: State
    anchor: State
    candidate: State
    budget: float
    accepted: bool


@dataclass(frozen=True, slots=True)
class StepRecord:
    """An active or leading-zero nonlinear sample, with its actual carry."""

    index: int
    target: float
    previous_q: float
    previous_s: float
    previous_i: float
    current_i: float
    candidates: tuple[CandidateRecord, ...]
    carried_q: float
    carried_s: float
    carried_i: float


@dataclass(frozen=True, slots=True)
class ReachResult:
    """Complete reached horizon in original encounter order."""

    reach_id: int
    coefficient: float
    coefficient_seconds: float
    duration_seconds: float
    exponent: float
    membership: tuple[int, ...]
    incoming: tuple[float, ...]
    processed_peak: float
    epsilon: float
    q: tuple[float, ...]
    s: tuple[float, ...]
    states: tuple[State, ...]
    steps: tuple[StepRecord, ...]
    is_linear: bool


@dataclass(frozen=True, slots=True)
class PrintResult:
    """One code-7 print in the immutable original control order."""

    control_index_one_based: int
    membership: tuple[int, ...]
    q: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class NetworkResult:
    """All routed states, every code-7 print and the final outlet."""

    reaches: tuple[ReachResult, ...]
    outlet: tuple[float, ...]
    prints: tuple[PrintResult, ...]


def _residual(q: float, s: float, target: float, dt: float) -> float:
    return safe64(safe64(safe64(s / dt) + safe64(q * 0.5)) - target)


def _from_q(q: float, target: float, a: float, dt: float, m: float) -> State:
    storage = internal_store(safe64(a * bounded_power(q, m)))
    return State(q, storage, _residual(q, storage, target, dt))


def _from_s(s: float, target: float, a: float, dt: float, m: float) -> State:
    if m == 0:
        message = "zero-exponent inverse path is uncharacterized"
        raise UnsupportedNumericPath(message)
    discharge = bounded_power(internal_store(safe64(s / a)), internal_store(safe64(1 / m)))
    return State(discharge, s, _residual(discharge, s, target, dt))


def _choose_anchor(trial: State, anchor: State, candidate: State) -> State:
    opposite = trial.r < 0 < anchor.r or anchor.r < 0 < trial.r
    keep_anchor = safe64(candidate.r * anchor.r) <= 0 if opposite else abs(trial.r) >= abs(anchor.r)
    return anchor if keep_anchor else trial


def _one_step(
    previous: State,
    before: float,
    current: float,
    a: float,
    dt: float,
    budget: float,
    m: float,
    limit: int,
    sample: int,
) -> tuple[State, float, tuple[CandidateRecord, ...]]:
    target = max(
        0.0,
        safe64(safe64(previous.s / dt) + safe64(safe64(safe64(before + current) - previous.q) * 0.5)),
    )
    anchor = State(previous.q, previous.s, _residual(previous.q, previous.s, target, dt))
    seed = internal_store(safe64(safe64(previous.q + current) * 0.5))
    trial = _from_q(seed, target, a, dt, m)
    candidates: list[CandidateRecord] = []
    separation = internal_store(1e-30)
    adjustment = internal_store(0.9)
    for iteration in range(1, limit + 1):
        # Repeated before *every* update, including the first; preserve iteration parity.
        if abs(trial.q - anchor.q) < separation:
            trial = _from_q(internal_store(safe64(trial.q + safe64(budget * adjustment))), target, a, dt, m)
        denominator = safe64(trial.r - anchor.r)
        if abs(denominator) < separation:
            candidate = _from_q(0.0, target, a, dt, m)
            chosen_coordinate = "q-fallback"
        else:
            odd = iteration % 2 == 1
            trial_coordinate, saved = (trial.q, anchor.q) if odd else (trial.s, anchor.s)
            projected = safe64(trial_coordinate - safe64(safe64(trial_coordinate - saved) / denominator * trial.r))
            proposal = internal_store(max(0.0, projected))
            chosen_coordinate = "q" if odd else "s"
            candidate = _from_q(proposal, target, a, dt, m) if odd else _from_s(proposal, target, a, dt, m)
        accepted = abs(candidate.r) < budget
        candidates.append(CandidateRecord(iteration, chosen_coordinate, trial, anchor, candidate, budget, accepted))
        if accepted:
            return candidate, target, tuple(candidates)
        anchor = _choose_anchor(trial, anchor, candidate)
        trial = candidate
    message = f"sample {sample}: no candidate accepted within {limit} updates"
    raise UnsupportedNumericPath(message)


def _linear_states(incoming: tuple[float, ...], k: float, hours: float) -> tuple[State, ...]:
    # Retain live p53 Q between updates: do NOT carry the emitted binary32 value.
    twice = safe64(k + k)
    denominator = safe64(twice + hours)
    if denominator <= 0:
        message = "linear denominator not positive"
        raise UnsupportedNumericPath(message)
    inflow_factor = safe64(hours / denominator)
    retention = safe64(safe64(twice - hours) / denominator)
    carried = 0.0
    states = [State(0.0, 0.0, 0.0)]
    for before, current in pairwise(incoming):
        carried = max(0.0, safe64(safe64(safe64(before + current) * inflow_factor) + safe64(carried * retention)))
        states.append(State(store(carried), store(safe64(safe64(3600 * k) * carried)), 0.0))
    return tuple(states)


def route_reach(
    incoming: tuple[float, ...],
    geometry: ReachGeometry,
    seconds: float,
    membership: tuple[int, ...],
    *,
    exponent: float = 0.8,
    limit: int = 50,
    hours: float | None = None,
) -> ReachResult:
    """Return a complete v6 reach and actual histories; no native fallback."""
    _validate_reach_input(incoming, limit)
    m = store(exponent)
    if m < 0:
        message = "negative exponents unsupported"
        raise UnsupportedNumericPath(message)
    k = store(geometry.coefficient)
    if m == 1.0 and hours is None:
        message = "linear routing requires the actual stored input timestep hours"
        raise UnsupportedNumericPath(message)
    h = store(hours) if hours is not None else 0.0
    peak = max(incoming[1:], default=0.0)
    budget = max(store(1e-8), safe64(peak * store(0.001)))
    if geometry.length_km == 0.0:
        if k != 0.0 or geometry.coefficient_seconds != 0.0:
            message = "zero-length copy reach has nonzero routing coefficient"
            raise UnsupportedNumericPath(message)
        # Only terminal code 5 is admitted by the typed model. Native CMD
        # evidence establishes exact full-horizon Q copy, including wet flow.
        states = tuple(State(q, 0.0, 0.0) for q in incoming)
        return ReachResult(
            geometry.reach_id,
            k,
            geometry.coefficient_seconds,
            seconds,
            m,
            membership,
            incoming,
            peak,
            budget,
            incoming,
            (0.0,) * len(incoming),
            states,
            (),
            False,
        )
    if m == 1.0:
        states = _linear_states(incoming, k, h)
        return ReachResult(
            geometry.reach_id,
            k,
            geometry.coefficient_seconds,
            seconds,
            m,
            membership,
            incoming,
            peak,
            budget,
            tuple(s.q for s in states),
            tuple(s.s for s in states),
            states,
            (),
            True,
        )
    a = store(safe64(k * 3600))
    dt = store(seconds)
    if a <= 0 or dt <= 0:
        message = "stored coefficient or duration not positive"
        raise UnsupportedNumericPath(message)
    states = [State(0.0, a if m == 0.0 else 0.0, 0.0)]
    steps: list[StepRecord] = []
    for index, current in enumerate(incoming[1:], 1):
        before, prev = incoming[index - 1], states[-1]
        if before == 0 and current == 0 and prev.q == 0 and (prev.s == 0 or m == 0):
            nxt, target, candidates = prev, 0.0, ()
        else:
            try:
                nxt, target, candidates = _one_step(prev, before, current, a, dt, budget, m, limit, index)
            except UnsupportedNumericPath as e:
                message = f"reach {geometry.reach_id}, sample {index}: {e}"
                raise UnsupportedNumericPath(message) from e
        states.append(nxt)
        steps.append(StepRecord(index, target, prev.q, prev.s, before, current, candidates, nxt.q, nxt.s, current))
    return ReachResult(
        geometry.reach_id,
        k,
        a,
        dt,
        m,
        membership,
        incoming,
        peak,
        budget,
        tuple(state.q for state in states),
        tuple(state.s for state in states),
        tuple(states),
        tuple(steps),
        False,
    )


def _add_stored(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
    if len(left) != len(right):
        message = "branch horizons differ"
        raise UnsupportedNumericPath(message)
    return tuple(internal_store(safe64(a + b)) for a, b in zip(left, right, strict=True))


def _require_code_two_running_branch(code: int, active: tuple[float, ...] | None) -> None:
    """Code 2 adds to an existing running branch; it cannot initialise one."""
    if code == 2 and active is None:
        message = "code-2 source needs an existing running hydrograph"
        raise UnsupportedNumericPath(message)


def route_network(  # noqa: C901 -- preserve explicit ordered CMD source/branch/print control cases
    event: Event, geometry: Geometry, preparation: Preparation
) -> NetworkResult:
    """Execute the ordered code-1/2/3/4/5/7 machine, preserving independent branches."""
    active: tuple[float, ...] | None = None
    members: tuple[int, ...] = ()
    stack: list[tuple[tuple[float, ...], tuple[int, ...]]] = []
    reaches: list[ReachResult] = []
    prints: list[PrintResult] = []
    next_source = 0
    next_reach = 0
    for control_index, control in enumerate(event.controls, start=1):
        _require_code_two_running_branch(control.code, active)
        if control.code in (1, 2):
            source = preparation.hydrographs[next_source]
            next_source += 1
            if active is None:
                active = source
                members = (next_source,)
            else:
                active = _add_stored(active, source)
                members = (*members, next_source)
        elif control.code == 3:
            if active is None:
                message = "invalid active branch"
                raise UnsupportedNumericPath(message)
            stack.append((active, members))
            active = None
            members = ()
        elif control.code == 4:
            active, members = _join_branch(active, members, stack)
        elif control.code == 7:
            if active is None:
                message = "code-7 print has no active hydrograph"
                raise UnsupportedNumericPath(message)
            prints.append(PrintResult(control_index, members, active))
        if control.code in (1, 2, 5):
            if active is None:
                message = "reach has no active source"
                raise UnsupportedNumericPath(message)
            geom = geometry.reaches[next_reach]
            next_reach += 1
            reached = route_reach(
                active, geom, preparation.seconds, members, exponent=event.m.stored, hours=event.h.stored
            )
            reaches.append(reached)
            active = reached.q
    if active is None or stack or next_source != event.source_count:
        message = "event not complete"
        raise UnsupportedNumericPath(message)
    return NetworkResult(tuple(reaches), active, tuple(prints))


def _validate_reach_input(incoming: tuple[float, ...], limit: int) -> None:
    if type(limit) is not int or not 1 <= limit <= 50:
        message = "iteration limit must be integer 1..50"
        raise UnsupportedNumericPath(message)
    if len(incoming) < 2 or incoming[0] != 0:
        message = "reach requires initial zero and nonempty horizon"
        raise UnsupportedNumericPath(message)
    if any(not math.isfinite(x) or x < 0 or internal_store(x) != x for x in incoming):
        message = "inflow must be finite nonnegative stored binary32"
        raise UnsupportedNumericPath(message)


def _join_branch(
    active: tuple[float, ...] | None, members: tuple[int, ...], stack: list[tuple[tuple[float, ...], tuple[int, ...]]]
) -> tuple[tuple[float, ...], tuple[int, ...]]:
    if active is None or not stack:
        message = "invalid confluence"
        raise UnsupportedNumericPath(message)
    saved, saved_members = stack.pop()
    active = _add_stored(active, saved)
    members = (*members, *saved_members)
    return active, members
