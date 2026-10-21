"""Linear single-phase line-source teaching calculations. Public API uses field units."""
from dataclasses import dataclass
import numpy as np
from scipy.special import exp1

PSI_PA = 6894.757293168
FT_M = 0.3048
MD_M2 = 9.869233e-16
STB_M3 = 0.158987294928


@dataclass(frozen=True)
class Reservoir:
    permeability_md: float = 50.0
    thickness_ft: float = 50.0
    porosity: float = 0.20
    viscosity_cp: float = 1.0
    volume_factor: float = 1.2
    compressibility_psi: float = 1.5e-5
    radius_ft: float = 0.35
    initial_pressure_psi: float = 4000.0

    def __post_init__(self):
        if not all(np.isfinite(v) and v > 0 for v in vars(self).values()):
            raise ValueError("Reservoir properties must be positive and finite.")
        if self.porosity >= 1:
            raise ValueError("Porosity must be less than one.")


def unit_response(elapsed_hours, reservoir=Reservoir(), radius_ft=None):
    """g(t) in psi/(STB/day); g=0 before activation. No skin or wellbore storage.

    g = B*q_unit*mu/(4*pi*k*h) E1[r²/(4*eta*t)], eta=k/(phi*mu*ct).
    Compute in SI, convert pressure to psi. E1 is evaluated without a log shortcut.
    At rw this is a line-source approximation, not a finite-radius well solution.
    """
    t = np.asarray(elapsed_hours, dtype=float)
    if not np.all(np.isfinite(t)):
        raise ValueError("Times must be finite.")
    radius = reservoir.radius_ft if radius_ft is None else float(radius_ft)
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("Radius must be positive and finite.")
    k = reservoir.permeability_md * MD_M2
    mu = reservoir.viscosity_cp * 1e-3
    ct = reservoir.compressibility_psi / PSI_PA
    eta = k / (reservoir.porosity * mu * ct)
    safe_t = np.where(t > 0, t, 1.0) * 3600
    u = (radius * FT_M) ** 2 / (4 * eta * safe_t)
    factor = (STB_M3 / 86400 * reservoir.volume_factor * mu
              / (4 * np.pi * k * reservoir.thickness_ft * FT_M) / PSI_PA)
    return np.where(t > 0, factor * exp1(u), 0.0)


def validate_schedule(starts, rates):
    starts, rates = np.asarray(starts, float), np.asarray(rates, float)
    if (starts.ndim != 1 or rates.ndim != 1 or len(starts) != len(rates)
            or not len(starts) or not np.all(np.isfinite(starts))
            or not np.all(np.isfinite(rates)) or starts[0] != 0
            or np.any(np.diff(starts) <= 0)):
        raise ValueError("Use equal-length finite schedules starting at zero with increasing times.")
    return starts, rates


def rate_increments(rates):
    rates = np.asarray(rates, float)
    if rates.ndim != 1 or not len(rates) or not np.all(np.isfinite(rates)):
        raise ValueError("Rates must be a nonempty finite vector.")
    return np.diff(np.r_[0.0, rates])


def rate_history(times, starts, rates):
    starts, rates = validate_schedule(starts, rates)
    t = np.asarray(times, float)
    index = np.searchsorted(starts, t, side="right") - 1
    return np.where(index >= 0, rates[np.maximum(index, 0)], 0.0)


def pressure_history(times, starts, rates, reservoir=Reservoir(), radius_ft=None):
    """Return absolute pressure and signed drawdown contributions (step, time)."""
    starts, rates = validate_schedule(starts, rates)
    t = np.atleast_1d(np.asarray(times, float))
    contributions = np.array([
        dq * unit_response(t - start, reservoir, radius_ft)
        for start, dq in zip(starts, rate_increments(rates))
    ])
    return reservoir.initial_pressure_psi - contributions.sum(axis=0), contributions


def horner(production_hours, shut_in_hours):
    tp, dt = np.asarray(production_hours, float), np.asarray(shut_in_hours, float)
    if np.any(tp <= 0) or np.any(dt <= 0) or not np.all(np.isfinite(tp)) or not np.all(np.isfinite(dt)):
        raise ValueError("Production and shut-in durations must be positive and finite.")
    ratio = 1 + tp / dt
    return ratio, np.log10(ratio), tp * dt / (tp + dt)


def buildup_superposition_function(times, starts, rates):
    """Normalized radial log-time F after final shut-in, normalized by last flowing q.

    F = sum_i (dq_i/q_ref)*ln((t-ti)/1 hr), including the shut-in decrement.
    All elapsed lags must be positive. For constant-rate buildup F=ln(H).
    This is a logarithmic radial-flow coordinate, NOT a substitute for the E1 kernel.
    """
    starts, rates = validate_schedule(starts, rates)
    if len(rates) < 2 or rates[-1] != 0 or rates[-2] <= 0:
        raise ValueError("This definition requires a final shut-in after positive production.")
    t = np.atleast_1d(np.asarray(times, float))
    lags = t[None, :] - starts[:, None]
    if not np.all(np.isfinite(t)) or np.any(lags <= 0):
        raise ValueError("Evaluate strictly after final shut-in.")
    terms = rate_increments(rates)[:, None] / rates[-2] * np.log(lags)
    return terms.sum(axis=0), terms
