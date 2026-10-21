"""PTA Visual Academy — standalone Streamlit entry point."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from educational_content import MODULES, WELL_TESTS, MODELS, REFERENCES, REFERENCE_STATUS
from well_tests import (SCHEDULES, history_figure, status_at, well_svg, style_figure,
                        time_grid, PURPLE, TEAL, ORANGE)
from diagnostics import diagnostic_figure, signature, reservoir_svg
from superposition import (Reservoir, unit_response, pressure_history, rate_history,
                           rate_increments, horner, buildup_superposition_function)
from exercises import render_exercises

st.set_page_config(page_title="PTA Visual Academy | Petroleum Academia", page_icon="◉", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container{padding-top:2rem;max-width:1550px} h1{letter-spacing:-1.2px}
[data-testid="stSidebar"]{border-right:1px solid #e9e4ef}
.eyebrow{color:#49176D;font-size:12px;font-weight:700;letter-spacing:1.8px;margin-bottom:9px}
.hero{background:linear-gradient(115deg,#f3edf8,#faf8fc);border:1px solid #e8dfef;border-radius:16px;padding:25px 30px;margin-bottom:23px}
.hero h1{font-size:36px;margin:0 0 6px;padding:0;line-height:1.2}.hero p{color:#756b80;margin:0;padding:0;font-size:15px}
.badge{font-size:11px;background:#e7dcf0;color:#49176D;border-radius:20px;padding:5px 10px;display:inline-block;margin-bottom:12px}
.lesson-note{border-left:3px solid #168B8B;padding:10px 15px;background:#f2f9f8;font-size:14px;border-radius:0 8px 8px 0;margin:10px 0 18px}
[data-testid="stMetricValue"]{font-size:25px} [data-testid="stMetricLabel"]{color:#74697e}
</style>""", unsafe_allow_html=True)


def chart(fig, key=None, selectable=False):
    return st.plotly_chart(fig, width="stretch", key=key,
        config={"displaylogo": False, "scrollZoom": False},
        **({"on_select": "rerun", "selection_mode": "points"} if selectable else {}))


def source_link(key):
    title, url = REFERENCES[key]
    st.caption(f"Technical reading: [{title}]({url})")


def note(text):
    st.markdown(f'<div class="lesson-note">{text}</div>', unsafe_allow_html=True)


def fundamentals():
    st.subheader("A well test, one moment at a time")
    st.caption("Select an operation, follow its timeline, and connect rate changes to pressure behavior.")
    name = st.selectbox("Explore a well test", list(WELL_TESTS), index=1, key="well_test")
    content = WELL_TESTS[name]
    left, right = st.columns([2.25, 1], gap="large")
    if name in SCHEDULES:
        with left:
            end = SCHEDULES[name][2]
            current = st.slider("Move through the test · elapsed time (hr)", 0.0, float(end),
                                min(36.0, end * .6), .1, key=f"time_{content['code']}")
            fig, pressure = history_figure(name, current)
            chart(fig)
            st.caption("Simplified operational illustration • E1 line-source pressure response; ideal instantaneous sandface rate changes, no storage or skin.")
            if name == "Interference / Pulse Testing":
                st.caption("Active-well rate is shown above observation-well pressure at 650 ft spacing. The observation well remains shut in.")
            status, q = status_at(name, current)
        with right:
            st.image(well_svg(status, name == "Interference / Pulse Testing"), width="stretch")
            st.metric("Active-well rate · STB/day", f"{q:,.0f}")
            st.metric("Observed pressure · psia", f"{pressure:,.1f}")
            st.caption("Rate convention: + production · − injection · 0 shut-in. Arrows represent ideal sandface flow.")
    else:
        formation = name.startswith("Formation")
        stages = (["Set probe", "Withdraw sample", "Pressure recovery"] if formation else
                  ["Before injection", "Fracture injection", "Shut-in / closure", "After-closure observation"])
        with left:
            st.info("Simplified illustrated explanation • No pressure-response solver for this operation in Phase 1.")
            stage = st.select_slider("Walk through the operation", options=stages)
            st.markdown(f"### {stage}")
            details = ({"Set probe": "Establish a seal against the formation and verify tool contact.",
                        "Withdraw sample": "A small withdrawal lowers local probe pressure and admits formation fluid.",
                        "Pressure recovery": "Stop withdrawal and observe recovery toward local formation pressure."} if formation else
                       {"Before injection": "Establish the pressure baseline and verify injection and gauge systems.",
                        "Fracture injection": "Pressure exceeds the initiation requirement and a small induced fracture accepts fluid.",
                        "Shut-in / closure": "Pressure declines as fluid leaks off and fracture compliance changes. Closure requires a justified interpretation method.",
                        "After-closure observation": "Later pressure behavior may constrain formation properties if the assumed flow regime is established."})
            st.write(details[stage])
            note(content["takeaway"])
        with right:
            status = "Sampling" if stage == "Withdraw sample" else "Fracturing" if stage == "Fracture injection" else "Shut in"
            st.image(well_svg(status, kind="formation" if formation else "dfit"), width="stretch")
    if name in SCHEDULES:
        note(content["takeaway"])
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("#### Why run this test?")
        st.write(content["purpose"])
        with st.expander("How it is conducted & what to measure", expanded=True):
            st.write(content["procedure"])
            st.markdown(f"**Measurements.** {content['measurements']}")
    with b:
        st.markdown("#### What can it tell us?")
        st.write(content["outputs"])
        with st.expander("Assumptions & operational challenges"):
            st.write(content["limitations"])
            st.markdown(f"**In practice.** {content['challenges']}")
    source_link("formation" if name.startswith("Formation") else "dfit" if name.startswith("Diagnostic") else "line_source")
    with st.expander("Synthetic example properties"):
        st.write("For the six rate/pressure examples: pi = 4,000 psia, k = 50 mD, h = 50 ft, φ = 0.20, μ = 1 cP, B = 1.2 reservoir bbl/STB, ct = 1.5 × 10⁻⁵ psi⁻¹ and evaluation radius rw = 0.35 ft (650 ft for the observation well). The line-source approximation is not an exact finite-radius wellbore response at the earliest times.")


def diagnostics():
    st.subheader("Learn to read the derivative")
    st.caption("Follow a characteristic interval. Change one control. Explain the physics behind the shape.")
    category = st.radio("Teaching window", ["Early Time", "Middle Time", "Late Time"], horizontal=True)
    st.caption("ET, MTR and LTR are teaching categories. Flow regimes can appear in different windows depending on the well and reservoir.")
    left, right = st.columns([2.3, 1], gap="large")
    with right:
        ids = [key for key, model in MODELS.items() if model["category"] == category]
        model_id = st.selectbox("Diagnostic signature", ids, format_func=lambda key: MODELS[key]["name"], key=f"model_{category}")
        model = MODELS[model_id]
        scale, secondary = 1.0, 1.0
        if model_id in ("storage", "changing_storage", "skin", "radial", "homogeneous", "infinite"):
            scale = st.slider("Relative wellbore storage C", .2, 8.0, 1.0, .1, key=f"scale_{model_id}")
            if model_id in ("storage", "skin"):
                secondary = st.slider("Skin-transition strength (qualitative)", 1.0, 5.0, 2.0, .1, key=f"second_{model_id}")
            elif model_id == "changing_storage":
                secondary = st.slider("Storage-change magnitude", .1, 3.0, 1.0, .1)
        elif model_id in ("dual_pss", "dual_transient"):
            secondary = st.slider("Storativity ratio ω", .02, .5, .1, .01, key=f"omega_{model_id}")
            scale = 10 ** st.slider("log₁₀ relative transfer λ", -1.0, 1.0, 0.0, .1, key=f"lambda_{model_id}")
        elif model_id == "composite":
            scale = st.slider("Relative interface radius", .3, 5.0, 1.0, .1)
            secondary = st.slider("Outer / inner mobility ratio", .2, 5.0, .5, .1)
        elif model_id in ("linear", "bilinear", "spherical"):
            label = {"linear": "Relative fracture extent", "bilinear": "Relative conductivity (higher → earlier radial flow)", "spherical": "Relative limited-entry scale"}[model_id]
            value = st.slider(label, .3, 5.0, 1.0, .1, key=f"scale_{model_id}")
            scale = 1 / value if model_id == "bilinear" else value ** 2
        else:
            label = "Relative channel width" if model_id == "channel" else "Relative drainage size" if model_id == "closed" else "Relative boundary distance"
            scale = st.slider(label, .3, 5.0, 1.0, .1, key=f"scale_{model_id}")
            if model_id == "constant_pressure":
                secondary = st.slider("Support strength (qualitative)", .5, 2.0, 1.0, .1)
            if model_id == "intersecting":
                secondary = st.slider("Ideal wedge angle (degrees)", 60, 180, 90, 30)
        show_guides = st.toggle("Show characteristic slope guide", value=True)
        st.image(reservoir_svg(model["geometry"]), width="stretch")
        st.caption(model["short_description"])
        st.caption("Controls use relative teaching scales. No numerical rock, fracture or boundary estimates are inferred.")
    with left:
        st.markdown("**Educational Diagnostic Signature — Not a Quantitative Model Fit**")
        event = chart(diagnostic_figure(model_id, scale, secondary, show_guides), key=f"diagnostic_{model_id}", selectable=True)
        view = st.radio("Reveal an explanation", ["Highlighted flow regime", "How the derivative is calculated"], horizontal=True)
        if view == "Highlighted flow regime":
            slope = model["expected_derivative_slope"]
            slope_text = "No universal slope" if slope is None else f"Expected derivative slope ≈ {slope:+g}"
            st.markdown(f"#### {model['characteristic_flow_regime']} · {slope_text}")
            st.write(model["physical_explanation"])
            if event and event.selection.points:
                selected = event.selection.points[0]
                t, _, d, _ = signature(model_id, scale, secondary)
                index = int(np.argmin(abs(np.log(t) - np.log(float(selected["x"])))))
                slope_local = np.gradient(np.log(d), np.log(t))[index]
                st.caption(f"Selected relative time: {t[index]:.3g} · local derivative slope: {slope_local:+.2f}. A local slope in a transition is not a flow-regime identification.")
        else:
            st.latex(r"p'=\frac{d\Delta p}{d\ln t}\quad;\quad p'_i=\frac{m_L L_R+m_R L_L}{L_L+L_R}")
            st.write("L are adjacent log-time intervals; m are pressure secant slopes. The three-point Bourdet weighting handles unequal log intervals. Here, a smooth teaching derivative is integrated to form Δp, then the numerical Bourdet derivative is recomputed from that pressure. Endpoint secants are hidden.")
    with st.expander("Interpretation implications, pitfalls & alternatives", expanded=True):
        a, b = st.columns(2)
        a.markdown(f"**What it may imply.** {model['interpretation_implications']}")
        a.markdown(f"**Controlling parameters.** {model['controlling_parameters']}")
        b.markdown(f"**Common mistake.** {model['typical_interpretation_mistakes']}")
        b.markdown(f"**Alternatives.** {model['alternatives']}")
        st.caption(model["diagnostic_limitations"] + " Boundary templates illustrate constant-rate drawdown, not late buildup.")
        source_link(model["reference"])


def contribution_plots(starts, rates, end, key):
    t = time_grid(starts, end)
    p, parts = pressure_history(t, starts, rates)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.1,
                        row_heights=[.22, .36, .42])
    fig.add_trace(go.Scatter(x=t, y=rate_history(t, starts, rates), name="Total rate", line=dict(color=TEAL, shape="hv")), row=1, col=1)
    for i, (part, dq, color) in enumerate(zip(parts, rate_increments(rates), [PURPLE, ORANGE, TEAL])):
        fig.add_trace(go.Scatter(x=t, y=part, name=f"Δq{i+1} = {dq:+g} STB/day", line=dict(color=color, width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=t, y=p, name="Combined pressure", line=dict(color=PURPLE, width=3)), row=3, col=1)
    for row, label in enumerate(["Rate · STB/day", "Signed Δpᵢ · psi", "Pressure · psia"], 1):
        fig.update_yaxes(title_text=label, row=row, col=1)
    fig.update_xaxes(title_text="Physical elapsed time · hr", row=3, col=1)
    style_figure(fig, 690)
    chart(fig)
    focus = st.slider("Inspect contributions at elapsed time (hr)", .01, float(end), min(float(end), starts[-1] + 12.0), key=key)
    pressure, contributions = pressure_history([focus], starts, rates)
    lags = np.maximum(focus - np.asarray(starts), 0)
    st.dataframe(pd.DataFrame({"Start tᵢ · hr": starts, "Period rate · STB/day": rates,
        "Δqᵢ · STB/day": rate_increments(rates), "Active?": [focus > start for start in starts],
        "Active age · hr": lags, "g(age) · psi/(STB/day)": unit_response(lags),
        "Signed Δpᵢ · psi": contributions[:, 0]}), hide_index=True, width="stretch")
    st.caption(f"Σ signed Δpᵢ = {contributions.sum():.3f} psi → p = 4,000 − Σ Δpᵢ = {pressure[0]:.3f} psia. Inactive steps contribute zero.")


def superposition_lab():
    st.subheader("Every rate change leaves a pressure response")
    st.caption("Physics-based calculations • Homogeneous infinite-acting, single-phase line-source model.")
    part = st.selectbox("Laboratory experiment", ["A · Single constant rate", "B · Two & three rate steps", "C · Pressure buildup", "D · Horner time", "E · Multirate superposition time"])
    st.latex(r"p(t)=p_i-\sum_i\Delta q_i\,g(t-t_i),\qquad \Delta q_i=q_i-q_{i-1},\quad q_0=0")
    if part.startswith("A"):
        q = st.slider("Constant production rate · STB/day", 50, 1000, 500, 50)
        t = np.geomspace(.00001, 96, 650)
        g = unit_response(t)
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.10)
        for row, y, title, color in [(1, np.full_like(t, q), "Rate · STB/day", TEAL),
                                    (2, g, "g(t) · psi/(STB/day)", ORANGE),
                                    (3, q*g, "Drawdown · psi", PURPLE)]:
            fig.add_trace(go.Scatter(x=t, y=y, name=title, line=dict(color=color, width=2.5)), row=row, col=1)
            fig.update_yaxes(title_text=title, row=row, col=1)
        fig.update_xaxes(title_text="Elapsed time · hr", row=3, col=1)
        chart(style_figure(fig, 650))
        note("Doubling q doubles Δp at every time in this linear model. The unit-rate response g(t) stays the same.")
    elif part.startswith("B"):
        count = st.radio("Number of rate periods", [2, 3], index=1, horizontal=True)
        cols = st.columns(3)
        q1 = cols[0].slider("Period 1 rate · STB/day", 0, 1000, 500, 50)
        q2 = cols[1].slider("Period 2 rate · STB/day", 0, 1000, 300, 50)
        q3 = cols[2].slider("Period 3 rate · STB/day", 0, 1000, 0, 50, disabled=count == 2)
        a, b = st.columns(2)
        duration1 = a.slider("Period 1 duration · hr", 1, 96, 24)
        duration2 = b.slider("Period 2 duration · hr", 1, 96, 48, disabled=count == 2)
        starts = [0, duration1] + ([duration1 + duration2] if count == 3 else [])
        rates = [q1, q2] + ([q3] if count == 3 else [])
        contribution_plots(starts, rates, starts[-1] + 72, "step_focus")
        note("A negative Δq is a reduction in production. For example, 500 → 300 STB/day gives Δq = −200 STB/day while the well still produces at +300 STB/day.")
    elif part.startswith("C"):
        a, b = st.columns(2)
        q = a.slider("Pre-shut-in production · STB/day", 100, 1000, 500, 50)
        tp = b.slider("Production duration tp · hr", 1, 168, 24)
        st.latex(r"p(t)=p_i-qg(t)+qg(t-t_p),\quad t>t_p")
        contribution_plots([0, tp], [q, 0], tp + 96, "buildup_focus")
        note("The +q production step continues mathematically forever. A −q step at shut-in cancels its rate, giving zero net rate and a recovering combined pressure.")
    elif part.startswith("D"):
        a, b = st.columns(2)
        tp = a.number_input("Production time tp · hr", min_value=1.0, max_value=1000.0, value=24.0)
        dt = b.number_input("Shut-in elapsed time Δt · hr", min_value=.01, max_value=1000.0, value=6.0)
        H, logH, te = horner(tp, dt)
        a, b, c = st.columns(3)
        a.metric("Horner ratio H", f"{float(H):.4f}")
        b.metric("log₁₀(H)", f"{float(logH):.4f}")
        c.metric("Equivalent time te · hr", f"{float(te):.4f}")
        st.latex(r"H=\frac{t_p+\Delta t}{\Delta t},\qquad t_e=\frac{t_p\Delta t}{t_p+\Delta t}\quad\text{(Agarwal equivalent time)}")
        elapsed = np.geomspace(.01, max(1000, dt), 400)
        p, _ = pressure_history(tp + elapsed, [0, tp], [500, 0])
        point, _ = pressure_history([tp + dt], [0, tp], [500, 0])
        fig = go.Figure(go.Scatter(x=np.log10(1 + tp / elapsed), y=p, name="E1 buildup, q = 500 STB/day", line=dict(color=PURPLE, width=3)))
        fig.add_trace(go.Scatter(x=[logH], y=point, mode="markers", name="Selected shut-in time", marker=dict(color=ORANGE, size=12)))
        fig.update_xaxes(title_text="log₁₀ Horner ratio H · dimensionless", autorange="reversed")
        fig.update_yaxes(title_text="Shut-in pressure · psia")
        chart(style_figure(fig, 410))
        note("Time progresses toward H = 1. The near-straight Horner interval relies on the late-time radial logarithmic approximation for both rate contributions. The plotted pressure uses E1 throughout.")
    else:
        multirate_time()
    with st.expander("Unit response, units & assumptions"):
        st.latex(r"g(t)=\frac{Bq_u\mu}{4\pi kh}E_1\!\left(\frac{r^2}{4\eta t}\right),\qquad \eta=\frac{k}{\phi\mu c_t},\quad t>0")
        st.write("The expression is evaluated in SI units, then converted to psi per STB/day. qu is 1 STB/day converted to m³/s; μ is Pa·s, k is m², h and r are m, ct is Pa⁻¹ and t is seconds. g(t≤0)=0. SciPy E1 handles short times without a logarithmic approximation.")
        st.write("Fixed example: k=50 mD, h=50 ft, φ=0.20, μ=1 cP, B=1.2, ct=1.5×10⁻⁵ psi⁻¹, r=0.35 ft, pi=4,000 psia. Assumes an initially uniform, infinite, homogeneous, isotropic, fully penetrating, slightly compressible single-phase system with constant properties. Storage, skin, finite-radius effects, boundaries and gas pseudopressure are omitted.")
        source_link("line_source")


def multirate_time():
    a, b = st.columns(2)
    q1 = a.slider("First production rate · STB/day", 100, 1000, 500, 50)
    q2 = b.slider("Last production rate qref · STB/day", 100, 1000, 300, 50)
    starts, rates = [0, 24, 72], [q1, q2, 0]
    st.write(f"Recorded history: 0–24 hr at {q1} STB/day; 24–72 hr at {q2} STB/day; shut in at 72 hr.")
    st.latex(r"F(t)=\sum_i\frac{\Delta q_i}{q_{\rm ref}}\ln\!\left(\frac{t-t_i}{1\;\mathrm{hr}}\right),\quad q_{\rm ref}=q_{\rm last\ flowing},\quad t>t_{\rm shut}")
    st.write("F is the normalized radial log-time function, including the shut-in decrement. Since the rate increments sum to zero after shut-in, the reference time unit cancels. Constant-rate buildup gives F = ln(H). This lesson plots F directly; some software uses its antilog exp(F).")
    dt = np.geomspace(.02, 400, 400)
    p, _ = pressure_history(72 + dt, starts, rates)
    F, _ = buildup_superposition_function(72 + dt, starts, rates)
    left, right = st.columns(2)
    for col, x, xlabel in [(left, np.log10(dt), "log₁₀(Δt / 1 hr)"), (right, F, "Normalized radial log-time F")]:
        fig = go.Figure(go.Scatter(x=x, y=p, name="Shut-in pressure", line=dict(color=PURPLE if col is left else TEAL, width=3)))
        fig.update_xaxes(title_text=xlabel)
        if col is right:
            fig.update_xaxes(autorange="reversed")
        fig.update_yaxes(title_text="Pressure · psia")
        with col:
            st.markdown("**Ordinary elapsed time**" if col is left else "**Rate-history-aware coordinate**")
            chart(style_figure(fig, 345))
    focus = st.slider("Inspect shut-in elapsed time Δt · hr", .02, 400.0, 6.0, .02)
    ft, terms = buildup_superposition_function([72 + focus], starts, rates)
    lags = 72 + focus - np.array(starts)
    st.dataframe(pd.DataFrame({"Start tᵢ · hr": starts, "Δqᵢ · STB/day": rate_increments(rates),
        "Δqᵢ / qref": rate_increments(rates) / q2, "t−tᵢ · hr": lags,
        "ln((t−tᵢ)/1 hr)": np.log(lags), "Weighted term": terms[:, 0]}), hide_index=True, width="stretch")
    st.caption(f"F = sum of weighted terms = {ft[0]:.6f}. Pressure is still calculated from E1 superposition. The log-time transform linearizes only when all significant rate contributions satisfy the radial logarithmic approximation.")
    source_link("superposition")
    with st.expander("Elapsed time, Horner ratio, equivalent time and F"):
        st.write("Physical elapsed time is the clock time since a specified event; Δt here begins at shut-in. H=(tp+Δt)/Δt is a dimensionless constant-rate buildup ratio. Agarwal equivalent time te=tpΔt/(tp+Δt) has time units and is used for particular buildup/drawdown comparisons. F is a rate-weighted, dimensionless radial logarithmic coordinate for the specified complete rate history. None is interchangeable with the others; radial superposition time can distort non-radial regimes.")


with st.sidebar:
    st.markdown('<div class="eyebrow">PETROLEUM ACADEMIA</div>', unsafe_allow_html=True)
    st.markdown("### PTA Visual Academy")
    st.caption("See the response. Understand the physics.")
    st.divider()
    module = st.radio("LEARNING MODULES", MODULES, format_func=lambda x: f"{MODULES.index(x)+1:02d}  {x}")
    st.divider()
    st.caption("PHASE 1 · TEACHING EDITION")
    st.caption("8 well-test lessons  \n17 diagnostic signatures  \n3 practice cases")
    with st.expander("About the teaching models"):
        st.write("Physics-based E1 calculations power the superposition lab and six idealized operational sequences. Diagnostic templates are dimensionless qualitative illustrations. Formation testing and DFIT use conceptual schematics.")

st.markdown('''<div class="hero"><span class="badge">PETROLEUM ACADEMIA · INTERACTIVE LEARNING</span>
<h1>PTA Visual Academy</h1><p>Interactive Well Testing &amp; Pressure Transient Analysis Education</p></div>''', unsafe_allow_html=True)
st.caption(f"MODULE {MODULES.index(module)+1:02d} / 04")
if module == MODULES[0]:
    fundamentals()
elif module == MODULES[1]:
    diagnostics()
elif module == MODULES[2]:
    superposition_lab()
else:
    render_exercises()
st.divider()
with st.expander("Technical references & acknowledgements"):
    st.write(REFERENCE_STATUS)
    for title, url in REFERENCES.values():
        st.markdown(f"- [{title}]({url})")
    st.caption("Independent educational material by Petroleum Academia. Source listing does not imply endorsement by the referenced authors or vendors.")
