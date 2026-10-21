"""Three lightweight interpretation cases, with feedback only after submission."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from diagnostics import signature
from superposition import rate_increments
from well_tests import style_figure, PURPLE, TEAL, ORANGE


def practice_figure(model_id, regions=False):
    t, p, d, _ = signature(model_id)
    fig = go.Figure()
    for values, name, color in [(p, "Normalized pressure change", PURPLE), (d, "Derivative", TEAL)]:
        fig.add_trace(go.Scatter(x=t, y=values, name=name, line=dict(color=color, width=3)))
    if regions:
        for lo, hi, label in [(1e-5, .002, "A"), (.002, .5, "B"), (.5, 1e3, "C")]:
            fig.add_vrect(x0=lo, x1=hi, fillcolor=ORANGE, opacity=.06, line_width=1,
                          annotation_text=label, annotation_position="top left")
    fig.update_xaxes(type="log", range=[-5, 3] if regions else [-5, 6], title_text="Relative time · dimensionless")
    fig.update_yaxes(type="log", title_text="Normalized pressure / derivative · dimensionless")
    return style_figure(fig, 430)


def render_exercises():
    st.subheader("Make an interpretation. Then test your reasoning.")
    st.caption("Three short exercises • Qualitative teaching examples • Feedback is local to this session.")
    exercise = st.selectbox("Practice case", ["1 · Identify WBS and IARF", "2 · Boundary interpretation", "3 · Superposition rate changes"])
    if exercise.startswith("1"):
        st.write("Select the interval dominated by wellbore storage and the interval most consistent with infinite acting radial flow.")
        st.plotly_chart(practice_figure("storage", True), width="stretch", config={"displaylogo": False})
        with st.form("regimes"):
            a, b = st.columns(2)
            storage = a.selectbox("Wellbore storage region", ["Choose a region", "A", "B", "C"])
            radial = b.selectbox("IARF region", ["Choose a region", "A", "B", "C"])
            submitted = st.form_submit_button("Check reasoning", type="primary")
        if submitted:
            if storage == "Choose a region" or radial == "Choose a region":
                st.warning("Select both regions, then submit again.")
            else:
                (st.success if storage == "A" and radial == "C" else st.info)("WBS: A · Transition: B · IARF: C")
                st.write("In A, Δp and its derivative nearly overlap with slope +1. B bends between regimes. In C, the derivative approaches a horizontal plateau: slope ≈ 0. A plateau is evidence to check against rate history and completion context, not a unique reservoir diagnosis.")
    elif exercise.startswith("2"):
        st.write("The derivative rises toward a second late plateau. Which explanations deserve investigation?")
        st.plotly_chart(practice_figure("fault"), width="stretch", config={"displaylogo": False})
        with st.form("boundary"):
            choices = st.multiselect("Possible explanations", ["A sealing boundary", "Lower outer-region mobility", "Incorrect or incomplete rate history", "Unique proof of one sealing fault"])
            submitted = st.form_submit_button("Reveal interpretation", type="primary")
        if submitted:
            if not choices:
                st.warning("Choose at least one explanation, then submit again.")
            else:
                st.info("A sealing-boundary-like response is plausible; the signature is not unique.")
                st.write("An ideal single sealing plane can produce a second radial plateau at twice the first level in constant-rate drawdown. A lower-mobility outer region can also raise the derivative. Incomplete rates or neighboring-well interference may mimic a late change. Compare sustained plateau levels, rate quality, geometry and independent evidence.")
                if "Unique proof of one sealing fault" in choices:
                    st.warning("Derivative shape alone does not uniquely prove one fault. Late buildup need not preserve the ideal drawdown doubling behavior.")
    else:
        starts, rates = [0, 24, 72], [500, 300, 0]
        fig = go.Figure(go.Scatter(x=[0, 24, 72, 96], y=[500, 300, 0, 0], name="Production rate",
                                  line=dict(color=TEAL, width=3, shape="hv")))
        fig.update_xaxes(title_text="Elapsed time · hr")
        fig.update_yaxes(title_text="Rate · STB/day")
        st.plotly_chart(style_figure(fig, 330), width="stretch", config={"displaylogo": False})
        st.write("Before time zero, q = 0. Enter the three signed rate increments in STB/day.")
        with st.form("increments"):
            cols = st.columns(3)
            answers = [cols[i].number_input(f"Δq{i+1} · STB/day", -2000, 2000, 0, 50) for i in range(3)]
            submitted = st.form_submit_button("Show calculations", type="primary")
        if submitted:
            expected = rate_increments(rates)
            (st.success if np.allclose(answers, expected) else st.info)("Rate increments: +500, −200, −300 STB/day.")
            st.dataframe(pd.DataFrame({"Time · hr": starts, "Calculation": ["500 − 0", "300 − 500", "0 − 300"],
                "Δq · STB/day": expected, "Your answer": answers}), hide_index=True, width="stretch")
            st.write("The −200 step reduces production to +300; it does not inject fluid. The −300 step at 72 hr shuts in the well. Each rate increment multiplies its own time-shifted unit response in the superposition sum.")
