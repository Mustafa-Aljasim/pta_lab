# PTA Visual Academy

**Interactive Well Testing & Pressure Transient Analysis Education**  
An independent Phase 1 teaching application for Petroleum Academia. It does not import, modify or integrate with PTA Learning Lab. All plots, SVG schematics and lesson text are original.

## Install and run

Use Python 3.12 (the validated version). From this folder:

```bash
pip install -r requirements.txt
streamlit run app.py
```

From the parent workspace on Windows:

```powershell
cd E:\Code_Folder\Pta_lab\pta_visual_academy
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the localhost URL printed by Streamlit. Startup opens **Well Testing Fundamentals → Pressure Buildup**, with an illustration, synchronized rate/pressure plots, timeline and explanation already visible. No uploads or setup are needed. Use the sidebar to switch between the four modules.

For Streamlit Community Cloud, place this folder's contents at the root of a GitHub repository, including `.streamlit/config.toml`, then select `app.py` as the entry point. The application uses only the five packages in `requirements.txt`; no secrets, database, server backend or local reference files are required. It can also run from the subfolder as `pta_visual_academy/app.py`; place the theme configuration in the repository-root `.streamlit/` directory in that layout. Cloud publication has not been performed.

## Four working modules

1. **Well Testing Fundamentals:** eight lesson selectors; six synthetic rate/pressure histories; live timeline, pressure marker, rate marker, status and flow arrows; two additional illustrated workflows.
2. **PTA Diagnostic Explorer:** 17 qualitative signatures, early/middle/late teaching categories, one or two meaningful controls per signature, characteristic slope guides, model-specific SVGs, point selection and compact explanations/pitfalls/alternatives.
3. **Superposition Laboratory:** constant-rate scaling, two/three rate steps, signed individual contributions and inspection tables, buildup cancellation, Horner calculations and a multirate radial log-time comparison.
4. **Practice & Interpretation:** three submitted-answer exercises, with reasoning feedback and explicit interpretation ambiguity. No persistent grades or profiles.

### Well-test lessons

| Test | Implementation |
|---|---|
| Pressure Drawdown (PDD) | Controlled production after an initial shut-in |
| Pressure Buildup (PBU) | 24 hr production followed by shut-in and recovery |
| Injection / Pressure Falloff | Negative signed injection rate, shut-in and pressure decline |
| Interference / Pulse Testing | Pulsed active-well rate, delayed pressure at a separate shut-in observation well 650 ft away |
| Multirate / Deliverability Testing | Three liquid-production rates then shut-in; not a gas deliverability solver |
| Drill Stem Test (DST) | Two idealized flow/shut-in sequences; no drill-string hydraulics |
| Formation Testing (MDT/RFT) | Probe setting, sample withdrawal and local pressure-recovery illustrations only |
| Diagnostic Fracture Injection Test (DFIT) | Injection, closure and after-closure conceptual stages only |

The first six use the same linear line-source pressure kernel as the laboratory. Their operational arrangements remain simplified. The timeline is a manual time animation, requiring no JavaScript animation framework. Schematic arrows describe ideal sandface conditions; surface shut-in and real afterflow need not coincide. The observation well always has zero rate.

### Diagnostic catalog

All signatures are prominently marked **Educational Diagnostic Signature — Not a Quantitative Model Fit**.

| Teaching category | Signature | Highlighted derivative slope / feature |
|---|---|---|
| Early | Constant Wellbore Storage | +1; pressure/derivative overlap |
| Early | Changing Wellbore Storage | Changing slope; no universal exponent |
| Early | Skin / WBS Transition | Storage-to-radial hump; no separate universal skin slope |
| Early | Linear Flow | +1/2 |
| Early | Bilinear Flow | +1/4 |
| Early | Spherical Flow | −1/2 (derivative, not pressure change) |
| Middle | Infinite Acting Radial Flow (IARF) | 0; radial plateau |
| Middle | Homogeneous Reservoir | 0 during radial flow |
| Middle | Dual Porosity PSS | Interporosity valley |
| Middle | Dual Porosity Transient | Broad exchange transition |
| Middle | Radial Composite | Two mobility-dependent plateau levels |
| Late | Infinite Acting / No Detected Boundary | Continued plateau; does not prove an infinite reservoir |
| Late | Single Sealing Fault | Transition toward an ideal doubled plateau |
| Late | Constant-Pressure Boundary | Declining derivative under pressure support |
| Late | Channel / Parallel Faults | Late +1/2 linear-flow interval |
| Late | Closed Reservoir / Pseudo-Steady-State Flow | Late +1 constant-rate depletion |
| Late | Intersecting Sealing Faults | Ideal wedge plateau scaling approximately as 360° / angle |

Teaching windows are not timing laws. A slope guide is drawn only for a characteristic interval with a supported exponent. Boundary signatures are for constant-rate **drawdown**; late buildup can behave differently. Sliders use relative scales, not inferred physical storage, fracture lengths or distances. The labels state this explicitly.

The templates prescribe a positive smooth derivative `D(t)`, integrate `Δp = ∫D dln(t)`, then recompute the plotted derivative using a three-point Bourdet weighting. Thus pressure and derivative are internally consistent, but **neither is a reservoir-model solution**. Points can be selected on the plot to inspect time and local derivative slope. The explanation selector also works without point selection.

## Superposition equations and conventions

Positive rate is production; negative rate is physical injection. The rate increment is `Δq_i = q_i − q_(i−1)`, with zero rate before time zero. A negative increment does not necessarily mean fluid injection.

For a constant-property, infinite, homogeneous, isotropic, fully penetrating, slightly compressible single-phase system:

```text
p(t) = pi − Σ Δq_i g(t − t_i)

g(t) = [B q_u μ / (4πkh)] E1[r²/(4ηt)]       t > 0
g(t) = 0                                     t ≤ 0
η = k / (φ μ ct)
```

`g` is psi per STB/day. Inside the kernel, SI units are used: `q_u = 1 STB/day` converted to m³/s, μ in Pa·s, k in m², lengths in m, ct in Pa⁻¹, time in seconds and pressure in Pa. Pressure is converted to psi at the output. `B` converts stock-tank to reservoir volume. Conversion constants:

| Field unit | SI equivalent |
|---|---:|
| 1 psi | 6894.757293168 Pa |
| 1 ft | 0.3048 m |
| 1 mD | 9.869233 × 10⁻¹⁶ m² |
| 1 STB | 0.158987294928 m³ |
| 1 cP | 0.001 Pa·s |

SciPy `exp1` evaluates the exponential integral directly, including short times; the logarithmic approximation is not used to generate the principal pressure histories. A line source evaluated at `rw` approximates well pressure; it is not an exact finite-radius early-time well model. Storage, skin, boundaries, fracture propagation, non-Darcy flow, multiphase behavior and gas pseudopressure are omitted.

Fixed example properties: pi=4000 psia; k=50 mD; h=50 ft; φ=0.20; μ=1 cP; B=1.2 reservoir bbl/STB; ct=1.5×10⁻⁵ psi⁻¹; rw=0.35 ft. The observation-well example evaluates the same kernel at 650 ft rather than at rw. These are provided inputs, not inferred parameters.

For buildup after production at `q` for `tp`:

```text
p(tp + Δt) = pi − q g(tp + Δt) + q g(Δt)
H = (tp + Δt) / Δt
te = tp Δt / (tp + Δt)             Agarwal equivalent time, in hours
```

`H` is dimensionless. `log10(H)` is shown separately. The semilog example plots E1 pressure against `log10(H)`, with the axis reversed so recovery progresses toward `H=1`. Horner straight-line behavior requires the late radial logarithmic limit for the significant contributions.

For the final shut-in following multirate production, this application defines the **normalized radial log-time function** explicitly:

```text
F(t) = Σ (Δq_i/qref) ln[(t − t_i)/(1 hr)]
qref = last positive flowing rate before final shut-in
t > final shut-in time
```

Include the final shut-in decrement. After shut-in, `ΣΔq_i=0`, so the chosen reference time unit cancels. A single production period gives `F=ln(H)`. Some software calls the antilog `exp(F)` its superposition radial time. Here, `F` itself is plotted against pressure, and every weighted term is shown. In the radial log limit, `pi−p ≈ A qref F`, where `A` is the unit-rate natural-log pressure coefficient. The actual pressure always comes from the E1 kernel. This coordinate is not a universal transform for fracture or spherical flow and is not interchangeable with physical elapsed time, H or te.

## Validation

Run the small suite using the standard library (no extra test dependencies):

```bash
python -m unittest discover -s tests -v
```

**Result: 15 tests passed.** Validated with Python 3.12.10, Streamlit 1.62.0, Plotly 6.9.0, NumPy 2.5.2, Pandas 3.0.5 and SciPy 1.18.1. Native Streamlit `AppTest` exercises all eight well-test selectors, all 17 diagnostic selectors and sensitivity controls, all five laboratory experiments, two/three-period switching, Horner input updates and all three exercise submissions without application exceptions.

Engineering checks cover independently calculated field-unit E1 values, zero/pre-step causality, superposition linearity, increments and constant-rate limit, buildup/falloff recovery, Horner and equivalent time, reduction of the multirate function to ln(H), agreement with the late radial limit, unequal-log-spacing Bourdet weights, positive finite log-log data, expected characteristic slopes, parameter sensitivity, schematic status and moving time markers. Streamlit's bare-mode `ScriptRunContext` warning during `AppTest` is expected.

## Technical reading and verification status

The three requested local reference files were **not available**: KAPPA *Dynamic Data Analysis v5.60.02*, Spivey & Lee *Applied Well Test Interpretation*, and IHS Markit *Well Testing Fundamentals*. Their edition-specific chapter/section details remain unverified; no chapter citations to these editions are invented. The application has a references expander with the same disclosure.

Public primary/vendor sources consulted for standard theory:

- [Elsevier publisher sample: Well Testing Analysis](https://booksite.elsevier.com/samplechapters/9780750677332/9780750677332.PDF) — exponential-integral radial response and rate-change superposition.
- [S&P Global / IHS WellTest: Superposition Time](https://www.ihsenergy.ca/support/documentation_ca/WellTest/2024/content/html_files/reference_materials/time_functions/superposition_time.htm) — rate increments and flow-regime-dependent time-function conventions.
- [SPE: Well Test Analysis in Practice](https://jpt.spe.org/twa/well-test-analysis-practice) — diagnostic methodology, flow-regime checks and interpretation ambiguity.
- [KAPPA technical library](https://www.kappaeng.com/papers) — source of the DDA reference, without an assertion that v5.60.02 was inspected.
- [SLB: Wireline formation test](https://glossary.slb.com/en/terms/w/wireline_formation_test) — formation-testing terminology.
- [S&P Global / IHS: Power-law flow-regime exponents](https://www.ihsenergy.ca/support/documentation_ca/Harmony/content/html_files/reference_material/analysis_method_theory/beta_derivative_theory.htm) — supporting exponents for storage, linear, bilinear and spherical flow; the app plots the Bourdet pressure derivative, not the beta derivative.
- [EPA: Characterizing Mechanical and Flow Properties Using Injection Falloff Tests](https://19january2017snapshot.epa.gov/sites/production/files/documents/characterizingmechanicalandflowpropertiesusinginjectionfallofftests.pdf) — fracture-injection/falloff context.

No copyrighted figures or substantial text were copied. Petroleum Academia's use of references does not imply endorsement by their authors or vendors.

## Files and extension

```text
pta_visual_academy/
    app.py                    Navigation and lesson UI
    well_tests.py             Operational histories, charts, original SVGs
    diagnostics.py            Qualitative signatures, Bourdet derivative, SVGs
    superposition.py          Unit-aware E1 calculations and time functions
    exercises.py              Three practice cases
    educational_content.py    Lesson/model dictionaries and references
    requirements.txt
    README.md
    .streamlit/config.toml    Petroleum Academia theme
    tests/                    15 meaningful validation cases
```

Add lesson text and model metadata in `educational_content.py`, then add the qualitative shape in `diagnostics.signature` if a new signature is needed. Preserve the distinction between actual linear diffusion calculations, qualitative diagnostic templates and operational illustrations. The app intentionally provides no field-data upload, quantitative model fitting, simulation, accounts or reports.
