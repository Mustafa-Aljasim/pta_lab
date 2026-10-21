"""Qualitative derivative templates integrated to internally consistent pressure curves."""
import numpy as np
import plotly.graph_objects as go
from scipy.integrate import cumulative_trapezoid
from educational_content import MODELS
from well_tests import PURPLE, TEAL, ORANGE, style_figure


def bourdet_derivative(time, pressure):
    """Three-point Bourdet weighted local derivative with respect to ln(time).

    No smoothing or field interpretation is intended here. Endpoints use one-sided
    secants and are omitted from the teaching plot to avoid endpoint artifacts.
    """
    t, p = np.asarray(time, float), np.asarray(pressure, float)
    if (t.ndim != 1 or p.shape != t.shape or len(t) < 3 or np.any(t <= 0)
            or np.any(np.diff(t) <= 0) or not np.all(np.isfinite(t))
            or not np.all(np.isfinite(p))):
        raise ValueError("Use at least three finite pressure samples at increasing positive times.")
    x = np.log(t)
    left, right = np.diff(x)[:-1], np.diff(x)[1:]
    secants = np.diff(p) / np.diff(x)
    middle = (secants[:-1] * right + secants[1:] * left) / (left + right)
    return np.r_[secants[0], middle, secants[-1]]


def signature(model_id, scale=1.0, secondary=1.0):
    """Return t, Δp, Bourdet derivative, highlighted mask. No dimensional inversion.

    scale controls relative storage, feature extent, or boundary distance.
    secondary is model-specific (skin-like hump, omega, mobility, or angle).
    Boundary appearance uses distance² scaling only as a teaching analogy.
    """
    if model_id not in MODELS:
        raise KeyError(model_id)
    if scale <= 0 or secondary <= 0:
        raise ValueError("Teaching controls must be positive.")
    t = np.geomspace(1e-5, 1e6, 1500)
    x = np.log10(t)
    tau = 0.03 * scale if model_id in ("storage", "changing_storage", "skin", "radial", "homogeneous", "infinite") else 0.001
    d = 0.5 * t / (t + tau)
    mask = (t > tau * .0005) & (t < tau * .08)

    def sigmoid(center, width=.32):
        return 1 / (1 + np.exp(-(x - np.log10(center)) / width))

    if model_id in ("storage", "skin"):
        d *= 1 + (secondary - 1) * np.exp(-.5 * ((x - np.log10(tau * 5)) / .45) ** 2)
        if model_id == "skin":
            mask = (t > tau) & (t < tau * 70)
    elif model_id == "changing_storage":
        d *= 1 + .9 * secondary * np.exp(-.5 * ((x - np.log10(tau * 2)) / .65) ** 2)
        mask = (t > tau * .1) & (t < tau * 50)
    elif model_id in ("linear", "bilinear", "spherical"):
        slope = MODELS[model_id]["expected_derivative_slope"]
        end = 30 * scale
        start = end / 1e4
        # A pure power-law interval bracketed by smooth storage/radial transitions.
        power = .5 * (t / end) ** slope
        early = 1 / (1 + (t / start) ** 4)
        late = 1 / (1 + (end / t) ** 4)
        d = early * (.5 * (start / end) ** slope * t / start) + (1 - early) * ((1 - late) * power + late * .5)
        mask = (t > start * 10) & (t < end / 10)
    elif model_id in ("radial", "homogeneous", "infinite"):
        mask = (t > max(10, tau * 100)) & (t < 1e5)
    elif model_id in ("dual_pss", "dual_transient"):
        center = 25 / scale
        omega = secondary
        depth = .88 * (1 - omega)
        width = .45 if model_id == "dual_pss" else .95
        d *= 1 - depth * np.exp(-.5 * ((x - np.log10(center)) / width) ** 2)
        mask = (t > center / 15) & (t < center * 15)
    elif model_id == "composite":
        center = 30 * scale ** 2
        d *= 1 + (1 / secondary - 1) * sigmoid(center)
        mask = (t > center / 10) & (t < center * 10)
    elif model_id in ("fault", "intersecting"):
        center = 30 * scale ** 2
        ratio = 2 if model_id == "fault" else 360 / secondary
        d *= 1 + (ratio - 1) * sigmoid(center)
        mask = (t > center * 30) & (t < min(center * 3000, 8e5))
    elif model_id == "constant_pressure":
        center = 30 * scale ** 2
        d *= (1 + t / center) ** (-secondary)
        mask = (t > center) & (t < center * 100)
    elif model_id in ("channel", "closed"):
        center = 30 * scale ** 2
        slope = .5 if model_id == "channel" else 1
        d *= (1 + (t / center) ** 3) ** (slope / 3)
        mask = (t > center * 10) & (t < min(center * 1000, 8e5))

    # Integrate dΔp/dln(t). Extrapolate the initial local power law down to zero.
    # Every template starts in a unit-slope interval; p(t_min)=d(t_min).
    pressure = d[0] + cumulative_trapezoid(d, np.log(t), initial=0)
    derivative = bourdet_derivative(t, pressure)
    return t, pressure, derivative, mask


def diagnostic_figure(model_id, scale=1.0, secondary=1.0, show_guides=True):
    t, p, d, mask = signature(model_id, scale, secondary)
    model = MODELS[model_id]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t[1:-1], y=p[1:-1], mode="lines", name="Pressure change Δp",
                            line=dict(color=PURPLE, width=2.5)))
    fig.add_trace(go.Scatter(x=t[1:-1], y=d[1:-1], mode="lines", name="Bourdet derivative",
                            line=dict(color=TEAL, width=3)))
    fig.add_trace(go.Scatter(x=t[mask], y=d[mask], mode="lines", name="Selected regime",
                            line=dict(color=ORANGE, width=5)))
    fig.add_vrect(x0=t[mask][0], x1=t[mask][-1], fillcolor=ORANGE, opacity=.055, line_width=0)
    slope = model["expected_derivative_slope"]
    if show_guides and slope is not None:
        center = np.flatnonzero(mask)[len(np.flatnonzero(mask)) // 2]
        gx = np.geomspace(t[mask][0], t[mask][-1], 40)
        gy = d[center] * 1.5 * (gx / t[center]) ** slope
        label = {1: "+1", .5: "+½", .25: "+¼", 0: "0", -.5: "−½"}[slope]
        fig.add_trace(go.Scatter(x=gx, y=gy, mode="lines", name=f"Slope guide {label}",
                                line=dict(color="#93899D", width=1.5, dash="dash")))
    style_figure(fig, 525)
    fig.update_xaxes(type="log", title_text="Relative elapsed time · dimensionless", exponentformat="power")
    fig.update_yaxes(type="log", title_text="Normalized Δp and dΔp/dln(t) · dimensionless", exponentformat="power")
    fig.update_layout(clickmode="event+select")
    return fig


def reservoir_svg(geometry):
    """Original plan views; geometry changes with the selected diagnostic."""
    field = '<circle cx="170" cy="105" r="20" fill="none" stroke="#168B8B"/><circle cx="170" cy="105" r="43" fill="none" stroke="#168B8B" opacity=".6"/><circle cx="170" cy="105" r="68" fill="none" stroke="#168B8B" opacity=".3"/>'
    if geometry == "storage":
        field = '<rect x="139" y="35" width="62" height="139" rx="10" fill="#D8D0E6"/><rect x="148" y="79" width="44" height="84" rx="5" fill="#168B8B" opacity=".5"/><path d="M155 59 H185 M170 49 V69" stroke="#49176D" stroke-width="3"/>'
    elif geometry == "fracture":
        field = '<path d="M63 105 H277" stroke="#49176D" stroke-width="5"/>'
        for x in range(85, 270, 35):
            field += f'<path d="M{x} 40 V83 M{x-5} 76 L{x} 85 L{x+5} 76 M{x} 170 V127 M{x-5} 134 L{x} 125 L{x+5} 134" stroke="#168B8B" fill="none" stroke-width="2"/>'
    elif geometry == "spherical":
        field += '<ellipse cx="170" cy="105" rx="68" ry="23" fill="none" stroke="#168B8B"/><ellipse cx="170" cy="105" rx="23" ry="68" fill="none" stroke="#168B8B"/>'
    elif geometry == "dual":
        field = "".join(f'<rect x="{x}" y="{y}" width="38" height="32" rx="3" fill="#E2D4C0"/>' for x in range(45, 300, 48) for y in range(30, 180, 42))
    elif geometry == "composite":
        field = '<circle cx="170" cy="105" r="70" fill="#D7EBE9" stroke="#168B8B" stroke-dasharray="5 4"/><circle cx="170" cy="105" r="33" fill="#E4D8EF" stroke="#49176D"/>'
    elif geometry in ("fault", "support", "channel", "closed", "intersecting"):
        boundary_color = TEAL if geometry == "support" else PURPLE
        field += f'<path d="M275 27 V183" stroke="{boundary_color}" stroke-width="7"/>'
        if geometry in ("channel", "closed"):
            field += '<path d="M65 27 V183" stroke="#49176D" stroke-width="7"/>'
        if geometry == "closed":
            field += '<path d="M65 27 H275 M65 183 H275" stroke="#49176D" stroke-width="7"/>'
        if geometry == "intersecting":
            field += '<path d="M65 32 H275" stroke="#49176D" stroke-width="7"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 215" role="img" aria-label="{geometry} conceptual reservoir schematic">
    <rect x="1" y="1" width="338" height="213" rx="14" fill="#F5F3F8"/>{field}
    <circle cx="170" cy="105" r="7" fill="#49176D" stroke="white" stroke-width="2"/>
    <text x="170" y="203" text-anchor="middle" font-family="Arial" font-size="11" fill="#71677E">Conceptual geometry · not to scale</text></svg>'''
