"""Operational teaching sequences and original SVG cross-sections."""
from html import escape
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from superposition import Reservoir, pressure_history, rate_history

PURPLE, TEAL, ORANGE = "#49176D", "#168B8B", "#DC8A39"
SCHEDULES = {
    "Pressure Drawdown": ([0, 4], [0, 500], 72),
    "Pressure Buildup": ([0, 24], [500, 0], 72),
    "Injection / Pressure Falloff": ([0, 4, 28], [0, -450, 0], 72),
    "Interference / Pulse Testing": ([0, 8, 20, 36, 48], [0, 600, 0, 600, 0], 96),
    "Multirate / Deliverability Testing": ([0, 18, 42, 66], [250, 500, 350, 0], 96),
    "Drill Stem Test": ([0, 2, 4, 10, 28], [0, 250, 0, 500, 0], 60),
}


def time_grid(starts, end, points=650):
    fine = [np.asarray(starts), np.linspace(0, end, points)]
    for start in starts:
        fine.append(start + np.geomspace(1e-5, end - start, 130))
    return np.unique(np.concatenate(fine))


def test_history(name, current_time=None):
    starts, rates, end = SCHEDULES[name]
    t = time_grid(starts, end)
    if current_time is not None:
        t = np.unique(np.r_[t, current_time])
    observation = name == "Interference / Pulse Testing"
    p, _ = pressure_history(t, starts, rates, radius_ft=650 if observation else None)
    return t, rate_history(t, starts, rates), p


def status_at(name, time):
    starts, rates, _ = SCHEDULES[name]
    q = float(rate_history(time, starts, rates))
    return ("Producing" if q > 0 else "Injecting" if q < 0 else "Shut in"), q


def style_figure(fig, height=450):
    fig.update_layout(template="plotly_white", height=height,
        font=dict(family="Arial, sans-serif", size=13, color="#444058"),
        margin=dict(l=30, r=22, t=28, b=35),
        legend=dict(orientation="h", y=1.10, x=0),
        hovermode="x unified", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF")
    fig.update_xaxes(showgrid=True, gridcolor="#EFEDF3", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EFEDF3", zeroline=False)
    return fig


def history_figure(name, current_time):
    t, q, p = test_history(name, current_time)
    index = int(np.argmin(abs(t - current_time)))
    observation = name == "Interference / Pulse Testing"
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.14, row_heights=[0.32, 0.68])
    fig.add_trace(go.Scatter(x=t, y=q, mode="lines", line=dict(color=TEAL, width=2.5, shape="hv"),
        fill="tozeroy", fillcolor="rgba(22,139,139,.07)", name="Active-well rate" if observation else "Rate",
        hovertemplate="%{y:.0f} STB/day<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=p, mode="lines", line=dict(color=PURPLE, width=3),
        name="Observation pressure" if observation else "Bottomhole pressure",
        hovertemplate="%{y:.2f} psia<extra></extra>"), row=2, col=1)
    for row, values, color in [(1, q, TEAL), (2, p, PURPLE)]:
        fig.add_vline(x=current_time, line_dash="dot", line_color=ORANGE, row=row, col=1)
        fig.add_trace(go.Scatter(x=[current_time], y=[values[index]], mode="markers",
            marker=dict(color=color, size=10, line=dict(color="white", width=2)),
            showlegend=False, hoverinfo="skip"), row=row, col=1)
    for start in SCHEDULES[name][0][1:]:
        fig.add_vline(x=start, line_color="#DDD7E6", line_dash="dash")
    fig.update_yaxes(title_text="Rate · STB/day", row=1, col=1)
    fig.update_yaxes(title_text="Pressure · psia", row=2, col=1)
    fig.update_xaxes(title_text="Elapsed time · hr", row=2, col=1)
    style_figure(fig, 490)
    fig.update_layout(legend=dict(y=1.13))
    return fig, float(p[index])


def well_svg(status="Shut in", observation=False, kind="well"):
    """Original, accessible cross-section. Reservoir arrows show sandface conditions."""
    active = status in ("Producing", "Injecting", "Sampling", "Fracturing")
    injecting = status in ("Injecting", "Fracturing")
    color = ORANGE if injecting else TEAL
    arrows = ""
    if active:
        for y in (215, 248, 281):
            for left in (True, False):
                a, b = ((70, 143) if left else (282, 209))
                if injecting:
                    a, b = b, a
                arrows += f'<path d="M{a} {y} H{b}" stroke="{color}" stroke-width="3" marker-end="url(#arrow)"/>'
        y1, y2 = (102, 190) if injecting else (190, 102)
        arrows += f'<path d="M176 {y1} V{y2}" stroke="{color}" stroke-width="3" marker-end="url(#arrow)"/>'
    else:
        arrows = '<path d="M157 88 L194 109 M194 88 L157 109" stroke="#49176D" stroke-width="4"/>'
    observer = ""
    if observation:
        observer = '''<path d="M292 53 V300" stroke="#AAA0B8" stroke-width="14"/>
        <path d="M292 53 V300" stroke="white" stroke-width="7"/>
        <circle cx="292" cy="267" r="6" fill="#49176D"/>
        <text x="290" y="37" text-anchor="middle">Observation</text>
        <text x="290" y="331" text-anchor="middle">q = 0 · pressure gauge</text>'''
    specialty = ""
    if kind == "formation":
        if active:
            arrows = '<path d="M280 241 H227" stroke="#168B8B" stroke-width="3" marker-end="url(#arrow)"/>'
        specialty = '<rect x="182" y="229" width="29" height="25" rx="4" fill="#49176D"/><circle cx="214" cy="241" r="6" fill="#DC8A39"/><text x="220" y="221">Sealed probe</text>'
    if kind == "dfit":
        specialty = '<path d="M175 245 L112 235 L79 216 M175 245 L240 249 L275 276" stroke="#DC8A39" stroke-width="5" fill="none"/><text x="214" y="302">Induced fracture</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 365" role="img" aria-label="{escape(status)} well cross-section">
    <defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="{color}"/></marker>
    <pattern id="sand" width="19" height="16" patternUnits="userSpaceOnUse"><circle cx="4" cy="4" r="1" fill="#C5B6A2"/><circle cx="14" cy="12" r="1" fill="#C5B6A2"/></pattern></defs>
    <rect x="1" y="1" width="358" height="363" rx="15" fill="#FAF9FC"/>
    <path d="M17 70 H343 V168 H17Z" fill="#ECE9EF"/><path d="M17 168 H343 V312 H17Z" fill="#F4EADB"/>
    <path d="M17 168 H343 V312 H17Z" fill="url(#sand)"/><path d="M17 168 H343 M17 312 H343" stroke="#D5C5AF"/>
    <text x="29" y="151">Seal / overburden</text><text x="29" y="192" fill="#816944">Reservoir</text>
    <path d="M175 57 V299" stroke="#AAA0B8" stroke-width="27"/><path d="M175 57 V299" stroke="white" stroke-width="17"/>
    <path d="M145 62 H205" stroke="#49176D" stroke-width="5"/><rect x="161" y="43" width="28" height="18" rx="4" fill="#49176D"/>
    {arrows}{observer}{specialty}<text x="175" y="350" text-anchor="middle" fill="#49176D" font-weight="bold">{escape(status)} · idealized cross-section</text>
    <style>text{{font:11px Arial,sans-serif;fill:#655D72}}</style></svg>'''
