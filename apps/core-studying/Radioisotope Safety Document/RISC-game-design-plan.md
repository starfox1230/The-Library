# RISC Chapter-Ordered Game Design Plan

## Source Notes
- Primary authority: the 8 source text files in `apps/core-studying/Radioisotope Safety Document/`.
- Helper only: `C:\Users\sterl\Downloads\RISC.docx`, used to surface high-yield framing, exam pitfalls, and figure-derived emphasis when the plain-text extraction is sparse.
- Design goal: map nearly all meaningful exam-relevant facts to a chapter-ordered campaign with subsection-level mini-games.
- Story tone: grounded authorized-user training mystery first, subtle government-project anomaly second, light late-game alien flavor only as optional texture.

## Campaign Spine
- Act 1, Chapters 1-2: the player starts authorized-user onboarding, learns safety language, and notices small inconsistencies in prior monitoring reports.
- Act 2, Chapters 3-4: package handling, inventories, and dose-limit records suggest a shipment chain and compliance trail that do not fully match the paperwork.
- Act 3, Chapters 5-6: patient administration, therapy workflow, and licensure systems expose a restricted protocol that normal staff are not supposed to see.
- Act 4, Chapters 7-8: an incident forces emergency response, and instrument/QC work becomes the way the player verifies what actually happened.

## Chapter 1. Introduction and Radiation Protection

### Chapter Overview
- Source scope: introductory material before 1.1 plus the full chapter on radiation protection and radiation areas.
- Learning goal: orient the player to what RISC covers, why the NRC rules matter, and how ALARA and area controls anchor all later decisions.
- Key intro facts: RISC is part of diagnostic and interventional radiology, contributes 25 Core questions and 10 Certifying essentials questions, counts toward the overall score, and is based on this document; the domain emphasizes practical radioisotope safety, handling, and regulatory compliance under Part 35 and related NRC material.
- Key intro facts: byproduct material is radioactive material yielded in or made radioactive by exposure to radiation incident to producing or using special nuclear material; this document is meant to supplement residency AU training and will be maintained as practice changes.
- Chapter story beat: the player is credentialed into a hospital radiation safety program and gets the first hint that routine badge reviews may be hiding a pattern.

### 1.1 ALARA program
**Source scope**
- Introduces baseline U.S. exposure context, ALARA, and annual ALARA oversight.

**Facts to teach**
- Annual average effective dose to the U.S. population from all sources, including background, is 500 to 600 mrem (5 to 6 mSv).
- ALARA means "as low as reasonably achievable" and frames judicious nuclear radiology use so exposure stays as low as possible while still supporting diagnosis.
- NRC requires annual review of the ALARA program by the RSO.

**Hard numbers and units**
- 500 to 600 mrem/year = 5 to 6 mSv/year.
- Review cadence: annual ALARA review by the RSO.

**Common confusions/exam traps**
- ALARA is not just a slogan; in this document it is tied to concrete review, staffing, shielding, and workflow behavior.
- Do not confuse the annual ALARA review with quarterly dosimetry review or every-3-month RSC review.

**Primary mini-game**
- `ALARA Control Room`: adjust time, distance, shielding, staffing, and scheduling levers to complete a day of cases while keeping a rolling exposure meter low.

**Optional micro-games**
- `Dose Budget Tuner`: choose the best workflow tweak for a scenario where patient care must continue but staff exposure is creeping upward.

**Story beat**
- The player inherits an ALARA dashboard with one quarter highlighted in red despite no incident report being attached.

**Repetition/unlock notes**
- Reuse the time-distance-shielding control loop in spill response, patient release, and dirty-bomb protection scenarios.

### 1.1.1 Radiation protection program
**Source scope**
- Defines public dose ceilings, core exposure-reduction principles, required program elements, and badge-processing expectations.

**Facts to teach**
- The highest dose to the public must not exceed 100 mrem/year (1 mSv/year).
- This public limit also applies to hospital staff outside the radiology/imaging department, including administration, support, nursing, engineering, and transport personnel.
- Time, shielding, and distance are the three main measures to reduce radiation exposure to personnel.
- The radiation protection program includes training and experience of AUs, inventory of sealed sources and leak testing, and a record of administered activity for diagnostic and therapeutic procedures.
- Personnel dosimeters used by licensees, except direct/indirect reading pocket ionization chambers and extremity dosimeters, must be processed and evaluated by a dosimetry processor.
- Personnel dosimetry records should be reviewed quarterly by the RSO.
- The RSC must review dosimetry records every 3 months.
- Individual dosimeters are required if personnel exposures are expected to exceed more than 10% of the annual occupational dose in a year.

**Hard numbers and units**
- Public limit: 100 mrem/year = 1 mSv/year.
- RSO review cadence: quarterly.
- RSC review cadence: every 3 months.
- Individual monitoring trigger: expected exposure >10% of annual occupational dose.

**Common confusions/exam traps**
- RSO quarterly review and RSC every-3-month review are functionally the same interval but different oversight roles.
- The >10% trigger is about expected occupational exposure, not actual exposure already received.

**Primary mini-game**
- `Badge Board Investigation`: inspect departmental dosimetry trends, decide who needs badges, and route concerning quarters to the right reviewer.

**Optional micro-games**
- `Protection Toolkit Match`: assign time, shielding, or distance fixes to short workflow scenarios.

**Story beat**
- Badge records suggest exposure clusters in staff who should have been outside the main radiation workflow.

**Repetition/unlock notes**
- This becomes the campaign's core "compliance board" mechanic whenever the player audits logs, release decisions, or records.

### 1.1.2 Audit program
**Source scope**
- Covers periodic audit requirements and independence expectations.

**Facts to teach**
- Planned audits must occur at least every 12 months.
- Audits verify compliance with all aspects of the radiation protection program.
- Audits must be performed by trained personnel who do not have direct responsibilities in the department or facility being audited.
- Audit results, including follow-up actions, must be documented and reviewed by hospital or facility administration.

**Hard numbers and units**
- Minimum audit interval: every 12 months.

**Common confusions/exam traps**
- The annual audit is separate from badge review, ALARA review, and daily or end-of-day surveys.
- Independence matters; the auditor should not be the person running the workflow being audited.

**Primary mini-game**
- `Annual Audit Prep`: assemble evidence, spot missing follow-up items, and choose which findings need escalation before the mock NRC visit.

**Optional micro-games**
- `Independence Check`: determine whether a proposed auditor is sufficiently removed from direct departmental responsibility.

**Story beat**
- The player discovers a prior audit that was signed off but never matched with its listed corrective actions.

**Repetition/unlock notes**
- Later chapters can reuse this as a "find the missing documentation" loop.

### 1.2 Radiation areas
**Source scope**
- Introduces restricted versus unrestricted areas and the logic behind posting and access control.

**Facts to teach**
- Nuclear radiology and radiation oncology departments contain restricted and unrestricted areas based on exposure rate and/or presence of radioactive materials.
- The chapter teaches area definitions through signage thresholds and room-use examples.

**Hard numbers and units**
- This section is primarily conceptual; the threshold values are taught in 1.2.1 to 1.2.3.

**Common confusions/exam traps**
- Area classification depends on radiation level and material use/storage, not simply on whether the room is in radiology.

**Primary mini-game**
- `Facility Mapper`: classify hospital spaces as restricted or unrestricted based on room use, material presence, and measured rates.

**Optional micro-games**
- `Posting Check`: decide whether a room needs a sign, an alarm, or neither.

**Story beat**
- A floor plan reveals one room marked "unrestricted" even though transport logs show repeated isotope traffic.

**Repetition/unlock notes**
- The map classification mechanic returns in inpatient therapy, spill quarantine, and public-access chapters.

### 1.2.1 Restricted areas
**Source scope**
- Defines common restricted-area activities and the radiation/high-radiation/very-high-radiation concepts shown in Figure 1.

**Facts to teach**
- Restricted-area activities include radiopharmaceutical preparation, administration, storage, and imaging.
- A "radiation area" is where effective dose could result in more than 5 mrem (0.05 mSv) in 1 hour at 30 cm from a source.
- The chapter's figure places "high radiation area" at the 100 mrem (1 mSv) in 1 hour at 30 cm threshold and requires a visible or audible alarm to control access.
- A "very high radiation area" is where absorbed dose levels could exceed 500 rad (5 Gy) in 1 hour at 1 meter from the source or any surface.
- Areas where licensed radioactive material is used or stored must have a "Caution Radioactive Materials" sign posted.

**Hard numbers and units**
- Radiation area: >5 mrem/hour at 30 cm = >0.05 mSv/hour at 30 cm.
- High radiation area threshold taught by the figure: 100 mrem/hour at 30 cm = 1 mSv/hour at 30 cm.
- Very high radiation area: >500 rad/hour at 1 m = >5 Gy/hour at 1 m.

**Common confusions/exam traps**
- The package label system in Chapter 3 is based on outside-package exposure, but room posting in this chapter is about area definition and access control.
- The figure-driven high-radiation threshold is an exam-style number even if the wording in the text extraction is imperfect.

**Primary mini-game**
- `Signage Patrol`: place the correct warning sign and access-control device in each restricted zone before staff arrive.

**Optional micro-games**
- `Alarm or No Alarm`: rapid-fire identify when a visible or audible alarm is required.

**Story beat**
- One restricted room has the right sign but no corresponding access alarm in the maintenance log.

**Repetition/unlock notes**
- Reappears whenever the player has to set up hot lab areas, therapy rooms, or emergency perimeters.

### 1.2.2 Public area
**Source scope**
- Defines unrestricted/public areas and exceptions tied to patient release and sealed-source dose rate.

**Facts to teach**
- Unrestricted areas include reception, waiting areas, office spaces, and reading rooms.
- These areas must have dose rates less than 2 mrem in any 1 hour (20 uSv/hour) or less than 100 mrem/year (1 mSv/year), excluding dose from administered patients and released patients.
- Rooms occupied by patients who meet release criteria do not need caution signs.
- A room or area with a sealed source does not need a caution sign if the radiation level at 30 cm from the source surface, container, or housing does not exceed 5 mrem (0.05 mSv) per hour.

**Hard numbers and units**
- Unrestricted-area rate limit: <2 mrem/hour = <20 uSv/hour.
- Unrestricted-area annual limit: <100 mrem/year = <1 mSv/year.
- No-sign sealed-source exception: <=5 mrem/hour at 30 cm = <=0.05 mSv/hour at 30 cm.

**Common confusions/exam traps**
- Patient-related exposures are excluded from this unrestricted-area posting threshold.
- Do not confuse the 5 mrem/hour no-sign sealed-source rule with the >5 mrem/hour radiation-area threshold.

**Primary mini-game**
- `Waiting Room Clearance`: inspect public-facing rooms and decide whether the measured rates are acceptable, need relocation, or need posting.

**Optional micro-games**
- `Release Exception Check`: choose whether a patient room still needs posting after a release decision.

**Story beat**
- The player notices that traffic from a supposedly public corridor lines up with after-hours isotope movement.

**Repetition/unlock notes**
- This public-versus-controlled-space judgment gets revisited in caregiver, visitor, and outpatient release chapters.

### 1.2.3 Caution signs
**Source scope**
- Covers the standard NRC symbol colors and label presentation.

**Facts to teach**
- The standard radiation symbol uses magenta, purple, or black on a yellow background.
- Licensees may label sources, source holders, or other device components without a color requirement.

**Hard numbers and units**
- No new dose thresholds; color and contrast are the key memory points.

**Common confusions/exam traps**
- Sign color rules apply to the standard symbol, but device-component labels do not have the same color requirement.

**Primary mini-game**
- `Sign Shop`: assemble compliant warning signs from color and wording options under time pressure.

**Optional micro-games**
- `Color Trap`: distinguish true NRC sign requirements from plausible but false design variants.

**Story beat**
- A mislabeled device component becomes the player's first concrete clue that someone has been working around standard procedure.

**Repetition/unlock notes**
- Reinforce sign-recognition visually whenever the player enters a new zone.

## Chapter 2. Radiation Biology

### Chapter Overview
- Source scope: the R-E-A-D framework, half-life concepts, dose concepts, radiobiology, deterministic effects, and stochastic risk.
- Learning goal: give the player enough physics/biology language to reason about radiation type, penetration, weighting, dose, tissue risk, and injury patterns.
- Chapter story beat: the player begins simulator training, and the "anomaly" first appears as a mismatch between expected dose behavior and a prior case log.

### 2.1 Radioactivity
**Source scope**
- Defines radioactivity, emitted radiation types, and activity units.

**Facts to teach**
- R-E-A-D stands for Radioactivity, Exposure, Absorbed dose, and Dose equivalent.
- Radioactivity is the process by which an unstable nucleus transitions to a stable configuration by emitting radiation.
- Activity is expressed in curie (Ci) or becquerel (Bq).
- 1 mCi = 37 MBq.
- Alpha particles are helium nuclei, travel about 10 to 100 um in tissue, have high LET, and are especially dangerous if ingested, inhaled, or used therapeutically.
- Beta particles are electrons or positrons; beta-minus can travel farther than alpha and can be stopped by a few millimeters of plastic.
- Example beta-minus range given: I-131 travels about 0.5 to 3.0 mm.
- Positrons annihilate with electrons and produce two 511 keV photons in opposite directions, the basis for PET imaging.
- Gamma rays are photons from the nucleus, with low LET and high penetration, and are used mainly for imaging.
- X-rays are photons created when beta-minus particles interact with nuclei and undergo Bremsstrahlung.
- Neutrons are free neutrons from nuclear breakup, can penetrate many materials, and can trigger chain reactions.

**Hard numbers and units**
- 1 mCi = 37 MBq.
- Alpha range: about 10 to 100 um.
- I-131 beta range example: 0.5 to 3.0 mm.
- Positron annihilation photons: 511 keV each.

**Common confusions/exam traps**
- Activity units (Ci/Bq) are not dose units.
- PET is built on positron annihilation photons, not on the positron itself traveling far in tissue.
- Bremsstrahlung comes up again in shielding, especially when beta interacts with high-Z material.

**Primary mini-game**
- `Emission Sorter`: classify emitted particles/photons by origin, penetration, LET, and best use in imaging versus therapy.

**Optional micro-games**
- `PET Pair Chase`: catch matched 511 keV photon pairs while ignoring decoys.

**Story beat**
- The simulator flags one historical isotope log as physically plausible on paper but biologically suspicious in use.

**Repetition/unlock notes**
- Radiation-type recognition becomes the foundation for later shielding, contamination, and therapy mechanics.

### 2.1.1 Half-life
**Source scope**
- Introduces physical, biological, and effective half-life.

**Facts to teach**
- Physical half-life (Tp) is the time for 50% of radionuclide nuclei to decay.
- Biological half-life (Tb) is the time for the radionuclide or radiopharmaceutical concentration in the body to fall to 50% of the original concentration.
- Effective half-life (Te) combines physical decay and biologic excretion.

**Hard numbers and units**
- Half-life always tracks the 50% point.
- Effective half-life formula emphasized by the helper document: Te = (Tp x Tb) / (Tp + Tb).

**Common confusions/exam traps**
- Physical half-life is a property of the radionuclide; biological half-life depends on the body and radiopharmaceutical handling.
- Effective half-life is always shorter than either physical or biological half-life alone.

**Primary mini-game**
- `Decay and Clearance`: drag physical and biologic decay sliders until the simulator lands on the correct effective half-life.

**Optional micro-games**
- `Half-Life Formula Forge`: build the correct formula from scrambled symbols before a timer runs out.

**Story beat**
- A short effective half-life should have kept a suspicious room clean faster than the real logs suggest.

**Repetition/unlock notes**
- Reuse effective-half-life math in patient release and waste decay scenarios.

### 2.2 Radiation dose
**Source scope**
- Normalized heading for the orphaned chapter 2 dose block that bridges exposure, absorbed dose, dose equivalent, and effective dose.

**Facts to teach**
- Exposure describes the amount of radiation present in air.
- Exposure units are roentgen (R) or coulomb/kilogram (C/kg).
- Typical measuring instruments include Geiger-Mueller counters and ionization chambers.
- Exposure is commonly measured in milliRoentgen (mR).
- One chest radiograph is given as about 10 mR.

**Hard numbers and units**
- Exposure units: R or C/kg.
- Common displayed unit: mR.
- Chest radiograph example: about 10 mR.

**Common confusions/exam traps**
- Exposure is radiation in air, not energy absorbed by tissue.
- Instruments that read exposure are not the same thing as biologic effect measures.

**Primary mini-game**
- `Dose Language Lab`: map scenario cards to exposure, absorbed dose, dose equivalent, or effective dose before the wrong unit gets charted.

**Optional micro-games**
- `Chest X-ray Benchmark`: place common exposure examples on a low-to-high timeline.

**Story beat**
- The player finds an old report that mixed exposure language and tissue-dose language in a way that could hide a true event.

**Repetition/unlock notes**
- This section sets the vocabulary every later calculation game relies on.

### 2.2.1 Absorbed dose
**Source scope**
- Defines tissue energy deposition and absorbed-dose units.

**Facts to teach**
- Absorbed dose is the amount of radiation energy deposited in tissue.
- For the same absorbed radiation, a smaller organ can have a larger absorbed-dose value than a larger organ because the energy is scaled by tissue mass.
- Units are gray (Gy) or rad.
- 100 rad = 1 Gy.

**Hard numbers and units**
- 100 rad = 1 Gy.

**Common confusions/exam traps**
- Absorbed dose is not automatically biologic harm; weighting comes later with dose equivalent and effective dose.

**Primary mini-game**
- `Energy Deposit Calibrator`: allocate the same radiation event to organs of different sizes and predict which gets the higher absorbed dose.

**Optional micro-games**
- `Rad-Gy Converter`: rapid unit conversion drill.

**Story beat**
- The player learns why the suspicious case could not have produced the recorded organ-dose pattern.

**Repetition/unlock notes**
- Use this conversion repeatedly before deterministic-effect and ARS sections.

### 2.2.2 Dose equivalent
**Source scope**
- Covers LET, quality/radiation weighting factors, RBE, and the move from absorbed dose to equivalent dose.

**Facts to teach**
- LET is the rate of energy transfer by radiation to a medium per unit length.
- Higher-LET radiation, such as alpha particles and neutrons, causes greater tissue damage than lower-LET radiation like beta, gamma, and x-ray.
- Historical quality factor Q(L) was replaced by radiation weighting factor wR in the modern framework.
- Dose equivalent quantifies relative biologic effectiveness by weighting absorbed dose.
- Organ- or tissue-equivalent dose is HT.
- Units are sievert (Sv) or rem, commonly mSv or mrem in diagnostic medicine.
- Weighting factors listed in the source are: x-rays 1, gamma rays 1, beta particles 1, slow neutrons 5, fast neutrons 10, alpha particles 20.

**Hard numbers and units**
- wR: x-ray 1, gamma 1, beta 1, slow neutrons 5, fast neutrons 10, alpha 20.
- Units: Sv/rem, often mSv/mrem.

**Common confusions/exam traps**
- High LET and high penetration are not the same thing.
- Neutrons and alpha particles score higher biologically even when the absorbed dose number alone looks similar.

**Primary mini-game**
- `Weighting Reactor`: assign the right radiation weighting factor to an exposure stream before the equivalent-dose meter locks.

**Optional micro-games**
- `LET Ladder`: sort emissions by LET and predicted tissue effect.

**Story beat**
- The player realizes the strange case used a shielding setup that makes sense only if someone misunderstood LET versus penetration.

**Repetition/unlock notes**
- This weighting mechanic returns in radiosensitivity, ARS, and contamination-risk decisions.

### 2.2.3 Effective dose
**Source scope**
- Covers tissue weighting factors, effective dose, TEDE, and background/context examples.

**Facts to teach**
- Effective dose scales organ/tissue-equivalent dose HT by tissue weighting factor wT.
- Effective dose formula is HE = sum of HT x wT across irradiated organs/tissues.
- Tissue weighting factors listed are: colon/lung/red bone marrow/stomach/breast 0.12; gonads 0.08; bladder/liver/esophagus/thyroid 0.04; bone surface/brain/salivary glands/skin 0.01.
- TEDE is defined by NRC regulations as effective dose equivalent from external exposure plus committed effective dose equivalent from internal exposure.
- The NRC glossary definition instead uses deep-dose equivalent plus committed effective dose equivalent, which can appear to exclude skin/eye dose from nonpenetrating radiation.
- Units for effective dose and TEDE are Sv or rem, typically mSv or mrem.
- Ci or Bq describes radioactivity of a substance, while mSv describes energy deposited in tissue and relative risk.
- Effective dose is treated linearly for relative-risk comparison; PET/CT is higher relative risk than a mammogram.
- Cancer risk is too small to observe below 100 mSv.
- Average U.S. natural background dose is about 3.1 mSv/year.
- Additional man-made dose is about 2.2 mSv/year, mostly medical.
- The source states that about 5.3 mSv/year from all radiation sources has not been shown to cause humans harm.

**Hard numbers and units**
- wT: 0.12, 0.08, 0.04, 0.01 groups as listed above.
- Observable cancer-risk note: below 100 mSv, too small to observe.
- Background: 3.1 mSv/year natural + 2.2 mSv/year man-made = about 5.3 mSv/year total.

**Common confusions/exam traps**
- Ci/Bq and mSv/mrem answer different questions: amount of radioactivity versus dose/risk.
- TEDE wording differs between the NRC regulation text and the glossary; that mismatch itself is memorable and testable.

**Primary mini-game**
- `Risk Ledger`: allocate organ doses and tissue weights to compute effective dose and TEDE before a report deadline expires.

**Optional micro-games**
- `Background Stack`: build a yearly exposure profile by sorting natural and man-made contributors.

**Story beat**
- The player sees that the background-dose explanation attached to a historical outlier does not fit the TEDE accounting.

**Repetition/unlock notes**
- Effective-dose and TEDE scoring become the campaign's main "true risk" meter.

### 2.3 Radiobiology
**Source scope**
- Defines categories of radiation effects and the major pathways of tissue injury.

**Facts to teach**
- Radiation effects are grouped as genetic/hereditary, somatic, and teratogenic.
- Somatic effects are further split into tissue reactions (deterministic) and stochastic effects.
- Direct injury causes single- or double-strand DNA breaks.
- Higher LET increases double-strand break burden.
- Cells are most radiosensitive in G2/M.
- Cells are most radioresistant in late S phase because of active DNA repair.
- Actively dividing cells are more radiosensitive than nondividing cells.
- Radiosensitive examples: hematopoietic cells, especially lymphocytes; spermatogonia; GI stem cells.
- Radioresistant examples: nerve and muscle cells.
- Indirect injury works through reactive oxygen species damaging proteins, DNA, and lipids.
- Water is an abundant oxygen source for indirect injury.
- Oxygen-rich environments increase vulnerability to indirect effects.

**Hard numbers and units**
- No new regulatory thresholds; the memory anchors are cell-cycle positions and named cell populations.

**Common confusions/exam traps**
- Direct and indirect pathways are both important; indirect damage is not a minor afterthought.
- Radiosensitivity tracks cell division and repair state more than gross organ size.

**Primary mini-game**
- `Cell Cycle Defense`: choose when a cell is most vulnerable or most protected as radiation pulses pass through a cycle clock.

**Optional micro-games**
- `Sensitive or Resistant`: sort tissues and cell types into radiosensitive versus radioresistant lanes.

**Story beat**
- A pathology consultant mentions that the questionable case injured a pattern of tissues that does not fit the declared exposure route.

**Repetition/unlock notes**
- Reuse cell-type sensitivity in ARS and deterministic-effect encounters.

### 2.3.1 Tissue reactions (deterministic effects)
**Source scope**
- Defines deterministic effects and lists common threshold-driven injuries.

**Facts to teach**
- Deterministic effects increase in severity with dose and have a threshold below which no effect is observed.
- They are typically observed relatively soon after exposure once threshold is exceeded.
- Example tissue effects in medical imaging/therapy include skin burns, erythema, hair loss, blistering, ulceration, lens opacification, and cataracts.
- The source table lists these thresholds and timing anchors: transient erythema/epilation at 2 Gy with about 24-hour onset; dry desquamation at 8 Gy with about 4-week onset; moist desquamation at 15 Gy with about 4-week onset.
- The table also lists delayed lens effects with dose thresholds: opacification after single acute exposure at 0.5 to 2 Gy, opacification with fractionation at 5 Gy, cataract after single acute exposure at 5 Gy, cataract after fractionation at 8 Gy.

**Hard numbers and units**
- Transient erythema/epilation: 2 Gy, about 24 hours.
- Dry desquamation: 8 Gy, about 4 weeks.
- Moist desquamation: 15 Gy, about 4 weeks.
- Opacification single acute: 0.5 to 2 Gy.
- Opacification fractionated: 5 Gy.
- Cataract single acute: 5 Gy.
- Cataract fractionated: 8 Gy.

**Common confusions/exam traps**
- Deterministic means threshold plus severity increases with dose.
- Cataract/opacification thresholds are easy to scramble; the game should force repeated pair matching.

**Primary mini-game**
- `Threshold Triage`: place patients on the correct deterministic-effect track based on dose and time-from-exposure clues.

**Optional micro-games**
- `Lens Damage Match`: pair lens effects with single-dose versus fractionated thresholds.

**Story beat**
- The player finds a follow-up note describing an effect timeline that contradicts the reported dose.

**Repetition/unlock notes**
- These thresholds should recur in later emergency and incident scenes as "clinical consequence" checks.

### 2.3.2 Linear no-threshold effects (stochastic)/Risks of radiation-induced cancer
**Source scope**
- Defines stochastic effects and the LNT model.

**Facts to teach**
- Stochastic effects increase in probability with dose, but severity does not depend on dose.
- There is no threshold dose; this is the linear no-threshold model.
- Main stochastic outcomes emphasized here are carcinogenesis and genetic effects.

**Hard numbers and units**
- No fixed injury threshold; the defining feature is absence of a threshold.

**Common confusions/exam traps**
- Stochastic is probability-driven, not severity-driven.
- Deterministic and stochastic effects should be contrasted directly in gameplay because exam stems often pivot on that distinction.

**Primary mini-game**
- `Risk Curve Decoder`: decide whether a scenario follows a threshold model or an LNT model before classifying the effect.

**Optional micro-games**
- `Probability Not Severity`: rapid-fire compare deterministic and stochastic features.

**Story beat**
- The anomaly file contains a warning memo that confuses deterministic injury language with cancer-risk language, suggesting sloppy or misleading reporting.

**Repetition/unlock notes**
- Keep the threshold-versus-no-threshold contrast visible in late incident debriefs.

## Chapter 3. Transfer and Management of Radioactive Materials

### Chapter Overview
- Source scope: transportation regulation, package handling, sealed sources, exempt quantities, use records, area surveys, and waste disposal.
- Learning goal: teach the logistics chain from shipment certificate to end-of-day survey to disposal, with emphasis on what gets labeled, monitored, retained, and reported.
- Chapter story beat: the player starts tracing physical movement of material and finds the first mismatch between internal activity, external label, and recorded receipt conditions.

### 3.1 Managing packages
**Source scope**
- Covers transportation oversight, package certification, and the logic of Type A versus Type B packaging.

**Facts to teach**
- About 3 million radioactive-material packages are shipped each year in the U.S. by highway, rail, air, or water.
- NRC and DOT share responsibility: NRC sets package design/manufacture requirements, while DOT regulates transport in transit and smaller-package labeling standards.
- NRC approves Type A and B packages and issues a Radioactive Material Package Certificate of Compliance.
- Certified packages must be shown by testing or analysis to withstand accident conditions.
- Applications address structural and thermal integrity, radiation shielding, nuclear criticality, material-content confinement, and operating/maintenance guidance.
- Type A containers are designed for normal handling and minor accidents and cover most clinical-use shipments.
- Type B packaging is designed to survive severe accidents.

**Hard numbers and units**
- Shipment volume anchor: about 3 million packages/year.

**Common confusions/exam traps**
- Package type is based on what is inside the shipment and what the packaging must survive; the transport label in 3.1.1 is based on radiation hazard outside the package.

**Primary mini-game**
- `Shipment Certification Desk`: review package applications and approve Type A or Type B based on contents, risk, and required survival conditions.

**Optional micro-games**
- `Transit Chain`: trace which agency owns which part of a shipment problem.

**Story beat**
- A shipment tied to the anomaly passed through the system on paperwork that looks valid but oddly incomplete.

**Repetition/unlock notes**
- Use package-versus-label distinctions again in spill, waste, and hot-lab routing.

### 3.1.1 Hazard levels and labeling
**Source scope**
- Teaches package labels, transport index, container labeling, and empty-container handling.

**Facts to teach**
- Radioactive package labels are based on the radiation hazard outside the package, not the activity inside the package.
- White I, Yellow II, and Yellow III are the common labels.
- The transport index (TI) is the highest radiation level at 1 meter from the package surface expressed in mrem/hour.
- White I does not carry a TI entry.
- Yellow II corresponds to surface radiation >0.5 to <=50 mrem/hour and <=1 mrem/hour at 1 meter, so TI <=1.
- Yellow III corresponds to surface radiation >50 to <=200 mrem/hour or >1 to <=10 mrem/hour at 1 meter, so TI >1 and <=10.
- Maximum TI for nonexclusive-use vehicles and exclusive-use open vehicles is 10.
- Radiation at 1 meter can exceed 10 mrem/hour only in exclusive-use closed vehicles.
- Each container of licensed material needs a durable visible label with the radiation symbol and "CAUTION, RADIOACTIVE MATERIAL" or "DANGER, RADIOACTIVE MATERIAL."
- The label must also include radionuclide(s), quantity of radioactivity, date, radiation levels, kinds of materials, and mass enrichment.
- Empty uncontaminated containers going to unrestricted areas must have the radioactive-material label removed, defaced, or otherwise clearly negated.

**Hard numbers and units**
- White I surface threshold: <=0.5 mrem/hour.
- Yellow II: surface >0.5 to <=50 mrem/hour; <=1 mrem/hour at 1 meter; TI <=1.
- Yellow III: surface >50 to <=200 mrem/hour or >1 to <=10 mrem/hour at 1 meter; TI >1 to <=10.
- Max TI for common carriers/open exclusive-use vehicles: 10.

**Common confusions/exam traps**
- This is one of the biggest exam traps: package label is based on outside radiation hazard, not inside activity.
- White I being the only label without a TI is easy to forget.

**Primary mini-game**
- `Label the Crate`: measure outside rates, assign White I/Yellow II/Yellow III, and write the correct TI before the truck departs.

**Optional micro-games**
- `Inside vs Outside`: choose whether a rule depends on package contents or external exposure.

**Story beat**
- The suspicious shipment's outside label did not match what the interior activity would have implied under normal handling.

**Repetition/unlock notes**
- Revisit this distinction whenever the player sees misleading paperwork.

### 3.1.2 Receipt of radioactive material shipments
**Source scope**
- Covers package receipt timing, contamination/radiation monitoring, damage review, and notification obligations.

**Facts to teach**
- Licensees should be able to receive packages promptly after carrier arrival.
- External surfaces of labeled packages must be monitored for contamination unless the package contains only gas or is an excepted package.
- All packages known to contain radioactive material must be checked with a GM detector for contamination, radiation levels, and package integrity problems such as crushing, wetness, or damage.
- Monitoring must occur as soon as practical, but no later than 3 hours after receipt during working hours or 3 hours from the beginning of the next working day if received after hours.
- If removable contamination or external radiation levels exceed limits, the final delivery carrier and NRC Headquarters Operations Center must be notified by telephone immediately.
- Licensees must maintain written procedures for safely opening packages and follow any package-specific special instructions.
- Licensees moving special-form sources in their own vehicles are exempt from contamination monitoring but still need radiation surveys to ensure the source remains properly lodged in its shield.

**Hard numbers and units**
- Receipt monitoring deadline: within 3 hours during working hours.
- After-hours receipt: within 3 hours of the next working day start.

**Common confusions/exam traps**
- The receipt-monitoring deadline is not "by the end of the day"; it is specifically tied to a 3-hour rule.
- Gas-only and excepted packages are the contamination-monitoring exceptions.

**Primary mini-game**
- `Receiving Bay Triage`: open the day's shipment queue and decide which package gets immediate GM survey, damage quarantine, or phone escalation.

**Optional micro-games**
- `3-Hour Clock`: place after-hours and in-hours arrivals on the correct monitoring deadline.

**Story beat**
- The problematic package was logged as received but never got a documented GM survey inside the required window.

**Repetition/unlock notes**
- This time-window mechanic should return whenever the player handles reportable deadlines.

### 3.2 Sealed sources
**Source scope**
- Covers sealed-source definition, regulation, leak testing, reporting, and diagnostic-device training.

**Facts to teach**
- Sealed sources are permanently bonded to a surface or encased in a metal capsule to reduce dispersion risk.
- NRC and Agreement States evaluate sealed sources and devices and issue registration certificates.
- NRC alone handles exempt products such as smoke detectors and gun sights.
- Each sealed source must be tested at intervals not exceeding 6 months.
- Without proof of a leak test within the previous 6 months, a transferred sealed source cannot be used until tested.
- A written report is required within 5 days if a leak test shows 185 Bq (0.005 uCi) or more removable contamination.
- The report must identify the source, radionuclide, estimated activity, test result and date, and corrective action.
- Diagnostic sealed-source/device AUs must be physicians, dentists, or podiatrists who are board certified or otherwise trained.
- Alternative training route listed here is 8 hours of classroom/lab instruction in basic radionuclide handling plus device-use training.

**Hard numbers and units**
- Leak-test interval: every 6 months or less.
- Reportable leak threshold: 185 Bq = 0.005 uCi removable contamination.
- Leak-report deadline: within 5 days.
- Alternate diagnostic-device training: 8 hours classroom/lab.

**Common confusions/exam traps**
- Semiannual leak testing is a classic number question.
- The reportable threshold is tiny and easy to misremember.

**Primary mini-game**
- `Leak Test Bench`: run semiannual tests, flag a leaking source, and build the report packet before the 5-day timer expires.

**Optional micro-games**
- `Seal or Scatter`: identify which devices count as sealed sources and which are exempt-product examples.

**Story beat**
- One sealed source in inventory has a clean serial trail but a missing test certificate just before the anomaly window.

**Repetition/unlock notes**
- Leak-threshold recall should return in medical-event and recordkeeping sections.

### 3.3 Exempt quantities
**Source scope**
- Lists examples of exempt quantities and exempt-product uses.

**Facts to teach**
- Examples include natural material and ores with naturally occurring radionuclides in natural state not intended for processing.
- Examples include byproduct material in electron tubes, self-luminous watches, and calibration/standardization instruments.
- Small quantities in check sources and calibration standards can be exempt for commercial distribution.
- Self-luminous products such as gunsights and exit signs may use tiny tritium-filled glass vials.
- Gas and aerosol detectors such as smoke detectors and chemical agent detectors may use coated foils with Am-241 or Ni-63.
- Capsules with 1 uCi carbon-14 urea each are exempt for in vivo diagnostic human use.

**Hard numbers and units**
- Carbon-14 urea capsule example: 1 uCi each.

**Common confusions/exam traps**
- Exempt examples are very list-like; this section benefits from repeated recognition rather than calculation.

**Primary mini-game**
- `Exemption Scanner`: sort items into exempt quantity, regulated byproduct, or exempt product categories.

**Optional micro-games**
- `Household or Hot Lab`: distinguish everyday exempt devices from controlled clinical materials.

**Story beat**
- The player realizes one item in the suspect chain looks harmless because it resembles an exempt-product category.

**Repetition/unlock notes**
- Reuse this recognition loop when the story involves disguised or mislabeled items.

### 3.4 Use records
**Source scope**
- Covers retention periods for surveys, calibrations, leak checks, and lifetime-license records.

**Facts to teach**
- Results of surveys, calibrations, and sealed-source leak checks must be retained for 3 years after the record is made.
- The following are retained for the duration of the license: external-dose survey results used in dose assessment; measurements/calculations used to determine radionuclide intake and internal dose; air sampling, surveys, and required bioassays; and measurements/calculations used to evaluate release of radioactive effluents to the environment.

**Hard numbers and units**
- Standard retention period in this section: 3 years.
- Some records are retained for the duration of the license.

**Common confusions/exam traps**
- Many records are 3-year records, but not all; some stay for the duration of the license.

**Primary mini-game**
- `Retention Vault`: file each record into the right retention shelf before an audit locks the archive.

**Optional micro-games**
- `3 Years or License Duration`: rapid recall sorter.

**Story beat**
- The missing anomaly records are suspicious because they belong to a retention category that should still exist.

**Repetition/unlock notes**
- This is the first full archive-management loop and should recur in 6.6.3.

### 3.5 Area surveys
**Source scope**
- Covers site surveys, decommissioning-relevant records, calibration expectations, and end-of-day GM surveys.

**Facts to teach**
- Licensees must perform surveys of areas, including subsurface when needed, to evaluate radiation levels and residual radioactivity.
- Records describing location and amount of subsurface residual radioactivity important for decommissioning must be retained.
- Instruments and equipment used for quantitative radiation measurement must be calibrated periodically for the radiation measured.
- A licensee shall survey with a GM meter at the end of each day of use.
- All areas where unsealed byproduct material requiring a written directive was prepared or administered must be surveyed.
- Required survey records are retained for 3 years and must include survey date, results, instrument, and surveyor.

**Hard numbers and units**
- Daily end-of-use survey requirement.
- Survey-record retention: 3 years.

**Common confusions/exam traps**
- End-of-day GM survey is separate from receipt monitoring and separate from decontamination wipe checks.

**Primary mini-game**
- `End-of-Day Sweep`: scan the department with the right instrument and catch every required survey point before shutdown.

**Optional micro-games**
- `Decommissioning Tag`: decide which survey findings must be kept with long-term site records.

**Story beat**
- The player notices a treated-patient area that should have been on the daily GM route but was skipped repeatedly.

**Repetition/unlock notes**
- This sweep mechanic is a natural replay loop between narrative chapters.

### 3.6 Waste management/disposal
**Source scope**
- Covers authorized disposal routes, sewer discharge, manifests, patient-excreta exception, and decay-in-storage.

**Facts to teach**
- Licensed material may be disposed of only by transfer to an authorized recipient, by decay in storage, or by release in effluents within authorized limits.
- Only specifically licensed persons may receive radioactive waste from others for treatment, incineration, decay in storage, or land disposal.
- Sanitary sewer discharge is allowed if material is readily soluble or readily dispersible biologic material and concentration limits are met.
- Annual sewer limits are 5 Ci (185 GBq) of H-3, 1 Ci (37 GBq) of C-14, and 1 Ci (37 GBq) of all other radioactive materials combined.
- Patient excreta from diagnosis or therapy are exempt from those sewer limitations.
- Shipments to licensed land-disposal facilities require the NRC Uniform Low-Level Radioactive Waste Manifest and generator certification.
- Decay in storage is allowed for byproduct material with physical half-life <=120 days.
- Before disposal, decay-in-storage waste must be surveyed with a GM meter at the surface and must be indistinguishable from background on the most sensitive scale with no interposed shielding.
- Radiation labels must be removed or obliterated before disposal, except as allowed for material staying within biomedical-waste containers after release.
- Disposal records must be kept for 3 years and include date, instrument, background level, measured surface level, and surveyor.

**Hard numbers and units**
- Sewer limits: H-3 5 Ci/year; C-14 1 Ci/year; all other combined 1 Ci/year.
- Decay-in-storage eligibility: physical half-life <=120 days.
- Disposal-record retention: 3 years.

**Common confusions/exam traps**
- Decay in storage requires both the half-life cutoff and a background-level survey.
- Patient excreta are exempt from sewer-discharge limits.

**Primary mini-game**
- `Waste Route Dispatcher`: choose sewer, decay-in-storage, transfer, or manifest-based disposal while staying inside half-life and annual-limit rules.

**Optional micro-games**
- `Background or Not`: decide whether a waste container can leave storage based on a GM reading and background comparison.

**Story beat**
- The anomaly trail jumps from a missing shipment to a waste stream that should not have cleared so quickly.

**Repetition/unlock notes**
- This section supports repeated logistics puzzles whenever the player clears contaminated items.

## Chapter 4. Regulatory Exposure Limits to Radioactive Materials

### Chapter Overview
- Source scope: worker dose limits, minors, pregnancy, public/caregiver exposure, and monitoring triggers.
- Learning goal: teach ceiling values, who gets monitored, what counts as compliance, and how public, worker, and embryo/fetus rules differ.
- Chapter story beat: dose history requests and monitoring records turn the mystery from a vague suspicion into a concrete exposure-tracking problem.

### 4.1 Regulatory exposure limits to radioactive materials
**Source scope**
- Introduces occupational training/right-to-know and the main annual worker dose limits.

**Facts to teach**
- Workers likely to receive more than 100 mrem (1 mSv)/year must receive adequate training to protect themselves against radiation.
- Workers have the right to know their radiation exposure and can ask the NRC to inspect if they believe safety problems exist.
- Adult annual limits are: whole body 5 rem (0.05 Sv), individual organ 50 rem (0.5 Sv), skin or extremity 50 rem (0.5 Sv), eye lens 15 rem (0.15 Sv).
- Minor annual limits are 10% of adult values: whole body 0.5 rem (0.005 Sv), individual organ 5 rem (0.05 Sv), skin or extremity 5 rem (0.05 Sv), eye lens 1.5 rem (0.015 Sv).
- If an adult radiation worker exceeds 5 rem in less than a year, including across multiple employers, the worker may not re-enter the radiation zone until the next calendar year.
- Doses received in excess of annual limits must be subtracted from limits for planned special exposures during the current year and lifetime.
- Assigned deep-dose equivalent should reflect the part of the body receiving the highest exposure.
- Assigned shallow-dose equivalent is averaged over the contiguous 10 square centimeters of skin receiving the highest exposure.
- Deep-dose, lens-dose, and shallow-dose equivalents may be assessed from surveys or other radiation measurements.
- NRC maintains worker-exposure data in REIRS.
- REIRS dose-history requests may cover up to 10 individuals at a time and require requester contact info plus individual identification data.

**Hard numbers and units**
- Training/right-to-know trigger: >100 mrem/year = >1 mSv/year.
- Adult limits: 5 rem whole body, 50 rem organ, 50 rem skin/extremity, 15 rem lens.
- Minor limits: 0.5 rem whole body, 5 rem organ, 5 rem skin/extremity, 1.5 rem lens.
- Skin averaging area: contiguous 10 square centimeters.
- REIRS request batch size: up to 10 individuals.

**Common confusions/exam traps**
- Minors are 10% of adult dose limits across categories.
- Whole-body, organ, skin/extremity, and lens limits are different ceilings and should not be collapsed into one number.

**Primary mini-game**
- `Dose Limit Console`: review worker roles and badge data, then assign the correct annual limit and action for each person.

**Optional micro-games**
- `REIRS Request Builder`: assemble the exact fields needed to request dose history.

**Story beat**
- A REIRS pull shows that one worker's exposure history does not line up with the hospital's local records.

**Repetition/unlock notes**
- Worker-limit matching should recur whenever the player sees a quarterly exposure spike.

### 4.1.1 Occupational dose limits for minors
**Source scope**
- Isolates the minor-worker rule.

**Facts to teach**
- Annual occupational dose limits for minors are 10% of the adult annual dose limits specified in 4.1.

**Hard numbers and units**
- Whole body 0.5 rem/year.
- Organ 5 rem/year.
- Skin/extremity 5 rem/year.
- Lens 1.5 rem/year.

**Common confusions/exam traps**
- "10% of adult" is the fast rule, but the game should still drill the actual converted values.

**Primary mini-game**
- `Student Rotation Limits`: approve or deny lab assignments for minor trainees based on projected dose.

**Optional micro-games**
- `Ten Percent Flash Cards`: instant conversion practice from adult to minor limits.

**Story beat**
- A student shadowing log becomes another clue that the department's official area classification may have been wrong.

**Repetition/unlock notes**
- Use minor-limit drills as short refresher interludes between heavier chapters.

### 4.2 Pregnant workers
**Source scope**
- Covers embryo/fetus limit, declaration rules, and compliance after late declaration.

**Facts to teach**
- Embryo/fetus limit for a declared pregnant worker is 0.5 rem (5 mSv) for the entire gestation.
- Members of the public are limited to 0.1 rem (1 mSv)/year.
- Visitor/caregiver/family member limit is 0.5 rem (5 mSv) for the duration of contact.
- If embryo/fetus dose has already exceeded 0.5 rem or is within 0.05 rem (0.5 mSv) of it by the time pregnancy is declared, the licensee is still deemed compliant if the additional dose during the remainder of pregnancy does not exceed 0.05 rem (0.5 mSv).
- A declared pregnant worker is one who voluntarily informs the employer in writing and gives the estimated date of conception.
- A separate written declaration should be submitted for each pregnancy.
- A pregnant worker may choose not to declare and may de-declare at any time.

**Hard numbers and units**
- Embryo/fetus gestation limit: 0.5 rem = 5 mSv.
- Late-declaration remainder allowance: 0.05 rem = 0.5 mSv.
- Public limit: 0.1 rem/year = 1 mSv/year.
- Visitor/caregiver duration limit: 0.5 rem = 5 mSv.

**Common confusions/exam traps**
- Pregnancy declaration is voluntary and reversible.
- The late-declaration rule creates a small remaining-dose window that is easy to miss.

**Primary mini-game**
- `Declaration Desk`: counsel workers through declare, do not declare, or de-declare choices while keeping dose projections compliant.

**Optional micro-games**
- `Remainder Allowance`: compute whether the remaining pregnancy dose stays inside the 0.05 rem window.

**Story beat**
- The anomaly file includes a handwritten pregnancy-declaration note that was never entered into the formal record.

**Repetition/unlock notes**
- Reuse declaration and counseling mechanics in therapy and breastfeeding chapters.

### 4.3 Public (including family and caregivers)
**Source scope**
- Covers public TEDE limits, visitor exceptions, and unrestricted-area limits.

**Facts to teach**
- TEDE to individual members of the public from licensed operation must not exceed 100 mrem (1 mSv) in a year.
- This excludes background radiation, the individual's own medical administrations, exposure to administered patients, and voluntary research participation.
- If public members enter controlled areas, public limits still apply.
- Visitors to a patient who cannot be released may receive more than 0.1 rem (1 mSv) if the dose does not exceed 0.5 rem (5 mSv) and the AU has determined the visit is appropriate.
- To protect the public, dose in any unrestricted area from external sources must not exceed 2 mrem/hour and 50 mrem/year (0.5 mSv/year) according to the chapter text.
- The source also states that a licensee may apply for prior NRC authorization to operate up to an annual limit printed as 50 mrem (listed in the text as 5 mSv/year); this line should be treated carefully during actual implementation because the text extraction appears inconsistent.

**Hard numbers and units**
- Public TEDE: 100 mrem/year = 1 mSv/year.
- Visitor exception ceiling: 0.5 rem = 5 mSv.
- Unrestricted-area external-source limit: 2 mrem/hour and 50 mrem/year = 0.5 mSv/year.

**Common confusions/exam traps**
- Visitor/caregiver rules are not the same as general public limits.
- This section includes a likely conversion mismatch in the source text; the design should preserve the stated rule but flag it for factual verification before game shipping.

**Primary mini-game**
- `Caregiver Exposure Planner`: decide whether a visitor can enter, how long they can stay, and whether a room still counts as safe for public access.

**Optional micro-games**
- `Who Counts as Public`: sort patients, caregivers, staff, and research volunteers by which limit applies.

**Story beat**
- Public-access calculations reveal that a supposedly safe corridor would only be safe if the official dose map were incomplete.

**Repetition/unlock notes**
- This becomes the backbone of visitor-control and release-instruction gameplay.

### 4.4 Embryo/fetus (radiation worker)
**Source scope**
- Cross-reference section pointing back to 4.2.

**Facts to teach**
- Embryo/fetus exposure rules for radiation workers are handled through the pregnant-worker rules in 4.2.

**Hard numbers and units**
- Same controlling limit as 4.2: 0.5 rem (5 mSv) for the entire gestation, with the 0.05 rem (0.5 mSv) remainder rule after late declaration.

**Common confusions/exam traps**
- This section is easy to skip because it is brief, but exam questions can still reference it explicitly.

**Primary mini-game**
- `Cross-Reference Recall`: pick the governing rule source for embryo/fetus questions without opening the full manual.

**Optional micro-games**
- `Duplicate or Distinct`: decide when a cross-reference section contains new content versus a pointer only.

**Story beat**
- The player sees how the department hid key pregnancy questions by burying them in cross-references rather than explicit workflow prompts.

**Repetition/unlock notes**
- Use this as a light review checkpoint, not a heavy standalone level.

### 4.5 Individual monitoring
**Source scope**
- Covers who must be monitored, what records must include, and how the RSO investigates outliers.

**Facts to teach**
- Adults likely to receive >10% of annual dose limits in a year from external sources must be monitored.
- Minors likely to receive >100 mrem, lens dose >150 mrem, or shallow skin/extremity dose >500 mrem in a year must be monitored.
- Declared pregnant workers likely to receive >100 mrem during the entire pregnancy from external sources must be monitored.
- Individuals entering a high or very high radiation area must be monitored.
- Dose records must include deep-dose equivalent, lens dose equivalent, shallow-dose equivalent to skin, shallow-dose equivalent to extremities, estimated radionuclide intake, and effective whole-body and organ dose.
- Records must be entered at least annually, remain clear and legible, and be protected from public disclosure due to privacy.
- Embryo/fetus dose records are kept with the declared pregnant worker's dose record, though the declaration itself may be stored separately.
- When a worker exceeds 10% of occupational exposure in a quarter, the RSO investigates for cause, including ALARA adherence and proper badge placement.

**Hard numbers and units**
- Adult monitoring trigger: >10% of annual limits.
- Minor triggers: >100 mrem whole body, >150 mrem lens, >500 mrem skin/extremity.
- Declared pregnant-worker trigger: >100 mrem during pregnancy.
- Investigation trigger in practice: >10% of occupational exposure in a quarter.

**Common confusions/exam traps**
- Monitoring triggers differ by population and dose category.
- Badge-placement review is part of the RSO investigation and is easy to forget in scenario questions.

**Primary mini-game**
- `Monitor or Not`: assign badges, ring dosimeters, or enhanced follow-up based on projected exposure and room-entry status.

**Optional micro-games**
- `Quarterly Spike Review`: inspect a badge outlier and choose the most likely operational explanation.

**Story beat**
- A quarterly outlier points straight at the room tied to the hidden protocol.

**Repetition/unlock notes**
- This is the main replay loop for periodic review between narrative chapters.

## Chapter 5. Radiopharmaceutical Administration

### Chapter Overview
- Source scope: radiopharmaceutical labeling, patient identity, fetal and lactation issues, dosage verification, administration safety, and shielding.
- Learning goal: teach how radiopharmaceuticals are prepared, verified, administered, and documented without causing dosage, identity, contamination, or release mistakes.
- Chapter story beat: the player moves from abstract compliance into direct patient care and starts seeing how one bad instruction can become a medical event.

### 5.1 Confirming dosage
**Source scope**
- Covers licensing context and the overall requirement to determine/verify activity before use.

**Facts to teach**
- Short-half-life radioisotopes are preferred to reduce patient dose and prolonged exposure.
- Many short-lived isotopes decay to stable elements within minutes, hours, or days, which helps patients leave the hospital sooner.
- FDA oversees clinical administration of radiopharmaceuticals to humans through NDA, ANDA, or IND pathways.
- Commercial distribution approval depends on FDA/state/pharmacy/PET facility registration and licensure status.
- Before medical use, radiopharmaceutical activities must be determined and recorded.

**Hard numbers and units**
- No single threshold here; this section establishes process and regulatory framing.

**Common confusions/exam traps**
- FDA approval/manufacturing oversight and NRC medical-use oversight coexist; they are not interchangeable.

**Primary mini-game**
- `Dose Verification Queue`: approve or reject incoming doses before they reach the patient workflow.

**Optional micro-games**
- `Regulator Match`: decide whether FDA, NRC, state pharmacy, or the AU owns the next action.

**Story beat**
- A dose enters the queue with valid chemistry paperwork but questionable clinical-use routing.

**Repetition/unlock notes**
- The verify-before-use loop anchors every later administration game.

### 5.1.1 Labeling
**Source scope**
- Covers syringe/vial labeling, nuclear-pharmacy data fields, patient-name rules, and tamper-evident delivery.

**Facts to teach**
- Each syringe or vial containing unsealed radioactive byproduct material must identify the radiopharmaceutical.
- Syringe/vial shields must also be labeled unless the syringe/vial label remains visible when shielded.
- Dosage labels must include radionuclide, chemical form, amount/activity and date/time measured, expiration date/time, quantity/volume/weight/count, dispensing nuclear pharmacy name/address/phone, prescription or lot number, and radiopharmaceutical name.
- Labels for radiolabeled blood components and radiotherapies must contain the patient's name.
- Delivery containers must have a tamper-evident seal.
- For diagnostic dosing when patient name is unavailable at dispensing, a 72-hour exemption is allowed; the patient's name must be associated with the prescription no later than 72 hours after dispensing and retained for 3 years.
- Administered-radiopharmaceutical records also include nuclear-pharmacy name/address, name of the end AU who is also a prescriber, and lot number.

**Hard numbers and units**
- Diagnostic naming exemption: 72 hours.
- Name-association record retention: 3 years.

**Common confusions/exam traps**
- Diagnostic doses get a 72-hour name exception, but radiolabeled blood components and therapies do not.
- Shield labels are still required unless the underlying label stays visible.

**Primary mini-game**
- `Hot Lab Label Builder`: assemble a fully compliant syringe or vial label before a nurse or tech can remove it from the pass-through.

**Optional micro-games**
- `72-Hour Follow-up`: resolve incomplete patient identity before the exemption window closes.

**Story beat**
- The player finds a therapy vial labeled cleanly except for one missing patient field that should never have been optional.

**Repetition/unlock notes**
- Label-building is a high-frequency loop that can recur every time a new isotope enters the story.

### 5.1.2 Outside of prescribed range for diagnostic and therapeutic dosage
**Source scope**
- Covers dosage determination methods and the +/-20% rule.

**Facts to teach**
- Unit dosages may be determined by direct measurement or decay correction from a predetermined activity.
- Other dosages may be determined by direct measurement, measurement plus calculation, or volumetric plus manufacturer-based calculation.
- AUs may prescribe a specific dosage or dosage range.
- Administered dosage may vary by +/-20% from the prescribed dosage.
- If the licensee knows the administered dosage differs by more than 20% and still gives it without a revised order, the licensee would be cited.
- An AU may direct administration more than 20% outside the original range for medical purposes, but must revise the prescription so the actual administered dosage falls within the revised range.
- The licensee must retain a record of the dosage determination.

**Hard numbers and units**
- Acceptable variance: +/-20%.

**Common confusions/exam traps**
- The more-than-20% threshold is not automatically forbidden if the AU revises the prescription first.
- This is one of the easiest sections to confuse with medical-event thresholds.

**Primary mini-game**
- `Range Override`: decide whether to administer, revise, hold, or escalate when the measured dose lands outside the current order.

**Optional micro-games**
- `Unit Dose or Calculated Dose`: choose the permitted determination method for each preparation.

**Story beat**
- The anomaly file shows a dose outside range that was clinically explainable, but the order was never revised.

**Repetition/unlock notes**
- This is a prime repeat mechanic because dosage-range judgment keeps appearing later in medical-event scenarios.

### 5.2 Patient identity
**Source scope**
- Covers two-identifier rules and temporary-ID handling.

**Facts to teach**
- Before radiopharmaceutical administration, patient identity must be confirmed with two identifiers.
- Acceptable identifiers include name, assigned ID number, telephone number, date of birth, person-specific identifier, or electronic identification such as barcode/RFID containing two or more person-specific identifiers.
- If identity cannot be verified, a temporary identification method must be used.
- Formal identification should occur as soon as possible, and new identifying information should replace the temporary method.
- No formal standard exists for alias use to protect anonymity; organizations should still use two identifiers.

**Hard numbers and units**
- Identity rule: two patient identifiers.

**Common confusions/exam traps**
- Barcode/RFID counts only if it includes two or more person-specific identifiers.
- Alias use does not eliminate the two-identifier requirement.

**Primary mini-game**
- `Two-ID Checkpoint`: verify identity in fast-paced clinical scenes without slowing the workflow so much that a dose decays out of range.

**Optional micro-games**
- `Alias Room`: decide whether a proposed identifier pair is adequate in privacy-sensitive cases.

**Story beat**
- A near-miss identity problem reveals that someone may have been relying on a single alias-based shortcut.

**Repetition/unlock notes**
- This rule should recur everywhere the player is tempted to rush.

### 5.3 Fetal dose (patient)
**Source scope**
- Covers embryo/fetus and nursing-child overexposure reporting and notification.

**Facts to teach**
- Licensees must telephone the NRC Operations Center by the next calendar day after discovering embryo/fetus dose >5 rem (50 mSv) from administration to a pregnant individual, unless specifically approved in advance by the AU.
- Licensees must also telephone by the next calendar day for dose to a nursing child >5 rem (50 mSv) TEDE or unintended permanent functional damage to an organ/system as determined by a physician.
- A written report to the NRC Regional Office is required within 15 days.
- Required report contents include licensee name, prescribing physician, brief event description, cause, effect on embryo/fetus or child, prevention steps, and certification of notification or why notification did not occur.
- The written report must exclude patient-identifying information.
- The licensee must notify the referring provider and the pregnant individual or mother within 24 hours after discovery of a reportable event, unless the referring provider will inform them or decides notification would be harmful.
- Notification cannot delay appropriate medical or remedial care.
- A responsible relative or guardian may be notified instead.
- If verbal notification is given, the licensee must offer a written description on request.

**Hard numbers and units**
- Telephone report trigger: >5 rem = >50 mSv.
- Telephone report deadline: next calendar day.
- Written report deadline: 15 days.
- Patient/mother notification deadline: 24 hours.

**Common confusions/exam traps**
- This is not the same as general medical-event reporting even though timelines overlap conceptually.
- The report must not include the individual or child's name.

**Primary mini-game**
- `Overexposure Response Clock`: triage who must be called, what must be documented, and what must be withheld for privacy.

**Optional micro-games**
- `24-Hour Notification`: choose whether the provider, mother, guardian, or both must be contacted first in edge cases.

**Story beat**
- The player uncovers a fetal-dose scare that was handled clinically but never fully reported administratively.

**Repetition/unlock notes**
- Keep the next-day/15-day/24-hour timing trio in later incident drills.

### 5.4 Breastfeeding/lactation (patient)
**Source scope**
- Covers ALARA-based breastfeeding interruption, written instructions, and radionuclide-specific guidance.

**Facts to teach**
- Breastfeeding patients may expose the child both internally through milk and externally from the mother's body.
- A nursing mother who received unsealed byproduct may be released if TEDE to any other individual, including the nursing child, is projected to stay <=500 mrem (5 mSv).
- If continued breastfeeding could expose the child to >100 mrem (1 mSv), written instructions are required on risks and on interruption/cessation.
- Before radioiodine therapy, oral and written precautions should be provided at least 6 weeks before the procedure so lactation can cease.
- Radionuclide-specific guidance given here: F-18 4-hour interruption; Ga-67 28 days; Ga-68 no interruption; I-123 NaI 3 days; I-131 NaI and I-124 NaI permanent cessation for the current child and stop breastfeeding 6 weeks before therapy; In-111 WBC 6 days; Lu-177 dotatate permanent cessation for current child; N-13 no interruption; Rb-82 no interruption; all Tc-99m-labeled radiopharmaceuticals 24 hours; Tl-201 chloride 4 days.
- Brachytherapy and seed-localization procedures generally require breastfeeding suspension while seeds remain in place, then resumption after removal.
- Y-90 microsphere radioembolization does not require breastfeeding interruption because Y-90 does not enter systemic circulation, breast tissue, or breast milk.

**Hard numbers and units**
- Release benchmark: <=500 mrem = <=5 mSv to others.
- Written-instruction trigger for nursing child: >100 mrem = >1 mSv.
- Radioiodine prep timing: at least 6 weeks before therapy.
- Interruption durations: F-18 4 hours, Ga-67 28 days, Ga-68 none, I-123 3 days, I-131/I-124 permanent cessation, In-111 WBC 6 days, Lu-177 dotatate permanent cessation, N-13 none, Rb-82 none, Tc-99m all 24 hours, Tl-201 4 days.

**Common confusions/exam traps**
- The 100 mrem instruction trigger is lower than the 500 mrem release benchmark.
- Permanent cessation applies to the current child for I-131/I-124 and Lu-177 dotatate.

**Primary mini-game**
- `Lactation Counseling Console`: select the correct interruption instruction and release advice for the administered radiopharmaceutical.

**Optional micro-games**
- `Stop, Pause, or None`: rapid-recall sort of radionuclides by breastfeeding guidance.

**Story beat**
- The player sees that patient counseling quality varies dramatically depending on who prepared the instructions.

**Repetition/unlock notes**
- This section is a strong spaced-repetition candidate because the isotope-specific durations are classic memory traps.

### 5.5 Administration of prescribed dosage
**Source scope**
- Introduces the physical act of administration and bridges into safe handling and shielding.

**Facts to teach**
- Radiopharmaceutical administration requires coordinated control of dose verification, staff protection, contamination prevention, and patient-release readiness.
- Criteria for release after unsealed byproduct or implant administration are handled later in 6.5.1.3.

**Hard numbers and units**
- This section is mainly a transition; numeric detail is in 5.5.1 and 5.5.2.

**Common confusions/exam traps**
- Administration is not complete when the dose enters the patient; contamination and release planning remain part of the workflow.

**Primary mini-game**
- `Administration Lane`: run a patient through the full handoff from verified dose to safe post-dose exit.

**Optional micro-games**
- `Next Step`: choose the most important immediate action after the dose is given.

**Story beat**
- What looks like a simple administration workflow becomes the point where the hidden protocol diverges from standard practice.

**Repetition/unlock notes**
- Use this as the chapter's central gameplay hub that branches into the detailed safety levels below.

### 5.5.1 Safe handling and administration
**Source scope**
- Covers room setup, ALARA during handling, contamination avoidance, bioassay note, and post-treatment surveys.

**Facts to teach**
- Administration should occur in a specific area or room separated from other operations and near where radiopharmaceuticals are stored.
- Transport to patient rooms often requires radiation-safety or nuclear-technology monitoring and assistance.
- Staff should use ALARA measures such as tongs/tweezers, warning staff about excretion, avoiding surface contamination, securing radioactive material when unattended, avoiding eating/drinking and oral contamination, and training workers.
- People administering volatile I-131 radiopharmaceuticals may be sampled for bioassay if >10 mCi.
- Syringe shields should be used during administration.
- For positron emitters, lead or tungsten may be used, but tungsten is preferred because it attenuates better at smaller thickness, is lighter, and is less toxic.
- Disposable gloves, body dosimeters, and finger dosimeters should be worn.
- Ring dosimeters go under a glove on the most exposed hand, on an exposed finger, with the badge facing the palm.
- Beta emitters can be stopped by lead, but the resulting Bremsstrahlung makes lead a poor shielding choice; low-Z materials such as acrylic or aluminum are preferred.
- After treatment, bedding, clothing, towels, food, and trays should be surveyed before removal or held for decay in storage.
- The patient should be surveyed before release and instructed how to minimize contamination and exposure.

**Hard numbers and units**
- Volatile I-131 bioassay consideration: >10 mCi.

**Common confusions/exam traps**
- Tungsten versus lead for positron emitters and low-Z shielding for beta emitters are high-yield contrast pairs.
- Ring badge orientation matters: under glove, exposed hand, facing the palm.

**Primary mini-game**
- `Admin Room Setup`: choose the right shield, PPE, tool, and waste route for a live administration without contaminating the room.

**Optional micro-games**
- `Badge Placement`: place body and ring dosimeters correctly on an avatar before the dose is drawn up.

**Story beat**
- The player finds an administration checklist that uses the wrong shielding logic for a positron case tied to the anomaly.

**Repetition/unlock notes**
- Repeat shield-selection and badge-placement mechanics often; they are ideal short loops.

### 5.5.2 Shielding for ionizing radiation
**Source scope**
- Covers equipment shielding, gamma emitters, airborne precautions, Xe-133 specifics, and radioactive-waste containers.

**Facts to teach**
- Shielding is a core ALARA principle and depends on understanding radionuclide emission type.
- Generators should be placed in a remote, well-shielded enclosure.
- Dose calibrators should be shielded to protect workers.
- Lead shielding should be used for Tc-99m and other gamma-emitting radiopharmaceuticals.
- Fume hoods should be used for potentially airborne radioactive materials.
- Xe-133 studies require additional lead shielding around the charcoal absorber canister, oxygen bag, and waste receptacle.
- Individualized Xe-133 room evacuation time calculations are required in rooms where ventilation scans are performed.
- Shielded containers or waste cans should be used for syringes and radioactive waste and kept as far from workers as practical.

**Hard numbers and units**
- No single threshold; the anchor facts are emission-type-specific shielding choices and the Xe-133 special-case workflow.

**Common confusions/exam traps**
- Beta-shielding logic lives in 5.5.1, while gamma-shielding logic is reinforced here.
- Xe-133 brings airborne and room-evacuation considerations that are easy to overlook.

**Primary mini-game**
- `Shielding Bay`: build the correct shielding layout for Tc-99m, PET, beta therapy, or Xe-133 ventilation with limited budget and space.

**Optional micro-games**
- `Gamma, Beta, PET, Gas`: pick the right shielding material and room control for each case.

**Story beat**
- The player learns the restricted protocol used a room never designed for its stated isotope.

**Repetition/unlock notes**
- This is a recurring "loadout" mechanic whenever a new isotope type appears.

## Chapter 6. Administrative and Practice Regulations, Responsibilities and Training

### Chapter Overview
- Source scope: NRC/Agreement State authority, key personnel roles, RAM licensing, written directives, therapy training, hot-lab operation, generator QC, and recordkeeping.
- Learning goal: teach who is allowed to do what, under which license and training pathway, with what documentation, release rules, and reporting obligations.
- Chapter story beat: the player follows the paper trail and discovers that the mystery is not just a safety problem; it may be an authorization problem.

### 6.1 Administrative/practice regulations, responsibilities and training
**Source scope**
- Covers regulatory authority over medical use of nuclear material and the Agreement State program.

**Facts to teach**
- Medical use licenses govern most internal or external administrations of byproduct material to human patients or research subjects.
- NRC or the responsible Agreement State has regulatory authority over possession and use of byproduct materials or other nuclear material in medicine.
- NRC oversees medical use through licensing, inspection, and enforcement, and consults medical experts.
- FDA oversees good manufacturing practices for radiopharmaceuticals, medical devices, x-ray machines, and accelerators.
- Agreement States receive portions of NRC authority through agreements signed by the governor and commission chair.
- NRC coordinates with Agreement States on event reporting and allegations involving those states.
- The source states that 39 states have entered agreements with the NRC.
- IMPEP requires periodic NRC review of Agreement State programs for adequacy and compatibility.

**Hard numbers and units**
- Agreement States noted in source: 39.

**Common confusions/exam traps**
- FDA and NRC authority overlap in the field but not in function.
- Agreement State status changes who regulates locally, not whether the work is regulated at all.

**Primary mini-game**
- `Regulatory Jurisdiction Board`: route a scenario to NRC, Agreement State, FDA, or local program based on what actually happened.

**Optional micro-games**
- `Who Owns the Problem`: decide which agency should hear an allegation or event first.

**Story beat**
- The player realizes the restricted protocol used regulatory fragmentation as camouflage.

**Repetition/unlock notes**
- This routing mechanic should recur whenever the player files a report or seeks approval.

### 6.2 Personnel
**Source scope**
- Introduces the main regulated personnel roles and why license status matters.

**Facts to teach**
- Key personnel covered are RSO, AU, ANP, AMP, and RSC members.
- The chapter's central idea is that licensed roles, formal attestation, and written responsibilities control who may act independently.

**Hard numbers and units**
- Role-specific quantitative details are carried by 6.2.1 to 6.2.5.

**Common confusions/exam traps**
- "Qualified" in practice often means more than clinically capable; it means correctly named, attested, and licensed.

**Primary mini-game**
- `Org Chart Lock`: place each person into the right regulated role before the system grants authority.

**Optional micro-games**
- `Who Can Do It`: choose whether a task belongs to an AU, ANP, RSO, AMP, committee, or supervised individual.

**Story beat**
- A name in the anomaly file appears on the workflow but not on the right part of the license.

**Repetition/unlock notes**
- This role-routing loop is essential and should be reused heavily.

### 6.2.1 Radiation safety officer
**Source scope**
- Covers RSO authority, certification/experience, ARSO delegation, and AU-as-RSO pathway.

**Facts to teach**
- A licensee must have an RSO with authority and responsibilities for the radiation protection program.
- The RSO must agree in writing to implement the program.
- ARSOs may be appointed in writing to support the RSO, and the RSO must assign their duties in writing.
- The RSO may not delegate the authority or responsibilities for implementing the radiation protection program.
- If an RSO or ARSO leaves or stops performing duties, the licensee must notify the NRC or Agreement State.
- The board-certification pathway described requires at least a bachelor's degree in physical or biological science, 5 or more years of professional health-physics experience, including at least 3 years in applied health physics, and passage of a specialty-board exam.
- Full-time radiation-safety experience includes shipping/receiving surveys, instrument checks, securing/controlling byproduct material, decontamination, and disposal.
- The licensee must give the RSO authority, organizational freedom, time, resources, and management prerogative to identify problems, initiate corrective action, stop unsafe operations, and verify corrective action.
- An AU may also be appointed RSO if the AU is identified on the license, has suitable radiation-safety experience, relevant training, written attestation from a preceptor RSO, and agrees in writing to implement the program.

**Hard numbers and units**
- Degree requirement: bachelor's or higher.
- Experience route: 5+ years professional health physics, including 3+ years applied health physics.

**Common confusions/exam traps**
- An ARSO can support but not replace the RSO's core responsibility.
- "Authority to stop unsafe operations" is one of the most testable RSO powers.

**Primary mini-game**
- `RSO Authority Simulator`: decide when to stop work, delegate support tasks, or escalate to management while preserving compliance.

**Optional micro-games**
- `Qualification Path`: build a valid RSO profile from degree, experience, attestation, and written acceptance cards.

**Story beat**
- The player learns the safest person in the system may also be the only one who can interrupt the hidden workflow.

**Repetition/unlock notes**
- RSO-stop-work decisions should recur whenever the story becomes risky.

### 6.2.2 Authorized user
**Source scope**
- Defines AU status, application review, attestation, and supervised delegation.

**Facts to teach**
- An AU is a physician, dentist, or podiatrist named on the license to authorize medical use of byproduct material.
- AU applicants submit training and experience specific to the proposed use.
- NRC or Agreement States evaluate AU qualifications case by case.
- A preceptor statement is required to show completion of training and ability to function independently.
- New medical uses require written attestation from someone knowledgeable about radiation safety and associated equipment.
- Under NRC rules cited here, a license amendment is not needed for a physician to begin work as an AU under the NRC license, but non-Type-A broad-scope licensees need to submit a copy of the Agreement State license to the NRC within 30 days.
- Only AUs and ANPs may use or prepare byproduct material in medicine, but they may delegate specific tasks to properly supervised and instructed individuals.
- AUs and ANPs remain the best judges of what supervised individuals may do and how much supervision is required.

**Hard numbers and units**
- Agreement State copy submission window: within 30 days in the situation described.

**Common confusions/exam traps**
- Task delegation is allowed, but responsibility stays with the AU or ANP.
- AU status depends on the intended use category, not just a general nuclear-medicine identity.

**Primary mini-game**
- `Authorization Routing`: approve, deny, or supervise task assignments based on whether the acting person is an AU, ANP, or supervised helper.

**Optional micro-games**
- `Attestation Check`: decide whether an application packet has the right attestation for a new use.

**Story beat**
- A physician in the anomaly chain was clinically senior but not clearly authorized for the specific use involved.

**Repetition/unlock notes**
- This role-based permission system should remain a core mechanic from here onward.

### 6.2.3 Authorized nuclear pharmacist
**Source scope**
- Covers ANP entry routes and the ANP-as-RSO/ARSO pathway.

**Facts to teach**
- An individual may begin as an ANP if board certified with recent training, identified as an ANP on an NRC or Agreement State license, or identified by a commercial nuclear pharmacy authorized to identify ANPs.
- An ANP may be chosen as an RSO or ARSO if they have suitable experience with similar byproduct material and meet similar requirements to an AU serving as RSO.
- The ANP must agree in writing to implement the radiation protection program.
- The licensee must apply to the NRC for an amendment and submit the ANP's training and experience to serve as RSO.

**Hard numbers and units**
- No new numeric threshold; this section is pathway-driven.

**Common confusions/exam traps**
- ANP authority is not identical to AU authority, but both can participate in supervised delegation structures.

**Primary mini-game**
- `Pharmacy Credential Gate`: verify whether a pharmacist may prepare, identify, or supervise a given radiopharmaceutical task.

**Optional micro-games**
- `Three Entry Paths`: match the pharmacist profile to the valid ANP pathway.

**Story beat**
- Pharmacy records reveal who really prepared the suspect material.

**Repetition/unlock notes**
- Keep pharmacy-role checks in any dose-preparation sequence.

### 6.2.4 Authorized medical physicist
**Source scope**
- Covers AMP-required devices and AMP eligibility to serve as RSO.

**Facts to teach**
- AMPs must be named on licenses authorizing medical uses of Sr-90 ophthalmic applicators, teletherapy units, photon-emitting remote afterloaders, and gamma stereotactic radiosurgery units.
- Similar to AU and ANP pathways, an AMP may be identified as an RSO by following comparable requirements.

**Hard numbers and units**
- No new numeric threshold; device categories are the memory anchors.

**Common confusions/exam traps**
- This section is device-specific and easy to skip, which makes it testable.

**Primary mini-game**
- `Device License Matcher`: pair advanced therapy devices with the personnel role that must appear on the license.

**Optional micro-games**
- `Need an AMP?`: choose whether the described device triggers AMP naming.

**Story beat**
- The player's search through old licenses exposes equipment that needed oversight from a role never listed.

**Repetition/unlock notes**
- Use as a short recognition level rather than a long simulation.

### 6.2.5 Radiation safety committee
**Source scope**
- Covers when an RSC is required, required membership, and committee authority.

**Facts to teach**
- Licensees authorized for two or more different types of byproduct-material use must have an RSC.
- Required members are an AU of each licensed type of use, the RSO, a nursing-service representative, and a management representative who is neither AU nor RSO.
- The committee may include other members as appropriate.
- The RSC oversees all uses of byproduct material under the license.
- RSC responsibilities include evaluating license applications, renewals, and amendments before submission and allowing individuals to work as AU, ANP, or AMP.

**Hard numbers and units**
- Trigger: two or more different types of use.

**Common confusions/exam traps**
- The committee is not optional once the license crosses the two-use threshold.
- Required membership composition is a memorization target.

**Primary mini-game**
- `Committee Table`: seat the right members and vote on a proposed amendment or personnel approval.

**Optional micro-games**
- `Need an RSC?`: decide whether a facility configuration crosses the trigger threshold.

**Story beat**
- Committee minutes are where the player first sees the hidden project approved in coded language.

**Repetition/unlock notes**
- This works well as a narrative branch-point between chapters.

### 6.3 Radioactive Materials (RAM) License
**Source scope**
- Covers what the NRC license is for and what an application must include.

**Facts to teach**
- NRC issues specific licenses for possession and use of byproduct, source, and special nuclear material.
- Licenses can later be modified through amendment or renewal.
- Applicants must show how use will meet NRC safety requirements.
- Applications include type, form, and intended quantity of material; facilities; user qualifications; and radiation protection programs.
- Licenses may include NRC conditions agreed to by the licensee.

**Hard numbers and units**
- No single numeric threshold; emphasis is on application content.

**Common confusions/exam traps**
- A license is not static; amendment and renewal are part of the operating life cycle.

**Primary mini-game**
- `License Application Builder`: assemble a complete RAM application from the minimum required content blocks.

**Optional micro-games**
- `Amend or Renew`: decide what type of license action fits a facility change.

**Story beat**
- The player sees that the strange project may have lived in amendment language rather than in the original license.

**Repetition/unlock notes**
- This gives structure to later broad-scope and MML sections.

### 6.3.1 Broad scope license
**Source scope**
- Covers Type A, B, and C broad-scope programs.

**Facts to teach**
- Type A broad-scope licenses are the largest programs, often large academic centers, and use an RSC, RSO, and internally developed criteria.
- Type B broad-scope programs are smaller and less diverse and use an RSO plus internally developed criteria.
- Type C broad-scope programs usually do not require significant quantities of radioactive material but need flexibility for a variety of materials; users are approved by the licensee based on training/experience.
- Type C examples given are nuclear cardiology clinics or small research labs needing small quantities.

**Hard numbers and units**
- No numeric thresholds in the text; the anchor is A/B/C distinction.

**Common confusions/exam traps**
- Type A versus Type B is often about scale and governance structure, especially RSC involvement.

**Primary mini-game**
- `Scope Classifier`: match a facility profile to Type A, Type B, or Type C broad scope.

**Optional micro-games**
- `Big Center or Small Clinic`: short-case identification drills.

**Story beat**
- The hidden work appears to have used broad-scope flexibility as cover.

**Repetition/unlock notes**
- Use as a short routing challenge, not a long level.

### 6.3.2 NRC Master Materials License
**Source scope**
- Covers MML purpose and oversight.

**Facts to teach**
- An MML is issued by NRC to federal organizations authorizing byproduct-material use at multiple sites under federal jurisdiction.
- It allows the federal agency to act in some regulatory capacities such as issuing permits, conducting inspections, handling allegations and incidents, and taking enforcement actions within its system.
- NRC still oversees MML licensees and inspects MMLs at least every 2 years.

**Hard numbers and units**
- NRC inspection interval for MMLs: at least every 2 years.

**Common confusions/exam traps**
- An MML does not eliminate NRC oversight; it restructures how oversight is carried out across a federal system.

**Primary mini-game**
- `Federal Oversight Map`: decide whether a multi-site event should be handled at site level, agency level, or NRC oversight level.

**Optional micro-games**
- `Every 2 Years`: timeline placement challenge for MML inspection cadence.

**Story beat**
- The player wonders whether the restricted protocol is protected by a federal oversight pathway ordinary staff never see.

**Repetition/unlock notes**
- This should feel like a late-midgame reveal, not a frequent mechanic.

### 6.4 Written directive
**Source scope**
- Defines written directives before the use-specific subsections.

**Facts to teach**
- A written directive is an AU's written order for administering byproduct material or radiation from byproduct material to a specific patient or research subject.

**Hard numbers and units**
- No numeric threshold in the definition itself.

**Common confusions/exam traps**
- The concept of a written directive matters before the player memorizes which uses do or do not require one.

**Primary mini-game**
- `Directive Gate`: decide whether the next planned administration can proceed only with a written directive, without one, or with a revised directive.

**Optional micro-games**
- `Directive Definition`: choose the legally meaningful definition from several near-miss options.

**Story beat**
- The hidden protocol depends on who can generate a directive and who can only carry it out.

**Repetition/unlock notes**
- This is the rule gate that later treatment levels should always route through.

### 6.4.1 Uptake, dilution, and excretion studies
**Source scope**
- Covers non-written-directive use plus training and work-experience requirements.

**Facts to teach**
- Unsealed byproduct material used for uptake, dilution, and excretion studies does not require a written directive.
- Material may come from a licensed manufacturer, PET radioactive drug producer, or preparation by an ANP or specially trained AU.
- RDRC-approved or IND byproduct material used for these studies also does not require a written directive.
- The AU must be a physician and have 60 hours of training and experience in basic radionuclide handling and radiation safety, including a minimum of 8 classroom/lab hours.
- Candidates must pass an exam administered by diplomates of the specialty board.
- Classroom/lab topics include radiation physics/instrumentation, radiation protection, math for use/measurement of radioactivity, chemistry of byproduct material for medical use, and radiation biology.
- Supervised work experience includes ordering/receiving/unpacking materials, instrument QC and survey-meter checks, dose calculation and preparation, administrative controls to prevent medical events, spill containment and decontamination, and administering radioactive drugs to patients or research subjects.
- A written attestation is required from a preceptor AU or residency program director representing faculty consensus including at least one AU.

**Hard numbers and units**
- Total training: 60 hours.
- Classroom/lab minimum: 8 hours.

**Common confusions/exam traps**
- This category does not require a written directive, which contrasts sharply with the therapy pathways.
- Training content includes both safety and operational tasks, not just lectures.

**Primary mini-game**
- `Study Path Credentialer`: complete the correct training/work steps before a trainee can independently run uptake/dilution/excretion studies.

**Optional micro-games**
- `Need a Directive?`: contrast this pathway with imaging/localization and written-directive-required pathways.

**Story beat**
- The player sees how one seemingly low-risk study pathway could still be abused if supervision is loose.

**Repetition/unlock notes**
- Good recurring permission-build mechanic for trainee progression.

### 6.4.2 Imaging and localization studies
**Source scope**
- Covers no-directive imaging/localization use and its AU pathway.

**Facts to teach**
- Except for quantities that require a written directive, unsealed byproduct material for imaging/localization studies may be used if obtained from a licensed manufacturer, PET producer, or ANP/AU preparation.
- RDRC-approved or FDA-accepted IND research imaging/localization studies also do not require a written directive.
- The AU must be a physician who is either board certified by an NRC/Agreement State-recognized board or has completed 700 hours of training and experience, including at least 80 classroom/lab hours.
- Candidates must pass an exam assessing radiation safety, radionuclide handling, and quality control.
- Classroom/lab topics mirror those in 6.4.1.

**Hard numbers and units**
- Total training: 700 hours.
- Classroom/lab minimum: 80 hours.

**Common confusions/exam traps**
- Imaging/localization can still avoid a written directive unless the quantity or use falls into a written-directive category.
- The 700-hour number here is distinct from the 700-hour written-directive pathway because the classroom-hour minimum changes.

**Primary mini-game**
- `Localization License Track`: assemble the correct training hours, board pathway, and source-of-material approvals for an imaging service.

**Optional micro-games**
- `80 or 200?`: compare classroom-hour requirements across AU pathways.

**Story beat**
- A clinician involved in the anomaly had just enough training for imaging but not clearly for the next step that followed.

**Repetition/unlock notes**
- This should reinforce the idea that similar-looking pathways can have different authorization ceilings.

### 6.4.3 Unsealed byproduct material requiring written directive
**Source scope**
- Covers the written-directive-required AU pathway for unsealed material.

**Facts to teach**
- Material requiring a written directive may be used if obtained from a licensed manufacturer meeting NRC/Agreement State requirements, or prepared by an ANP or AU or supervised individual.
- The AU pathway requires board certification by a recognized medical specialty board and completion of a residency in radiation therapy, nuclear medicine, or a related specialty.
- Required training includes 700 hours, including 200 classroom hours, plus an exam covering radiation safety, radionuclide handling, quality assurance, and clinical use.
- Training also includes safe dose preparation, administrative controls to prevent medical events, spill containment/decontamination, and drug administration.
- Work experience must include at least 3 cases in each of the following categories requested for AU status: oral administration of <=1.22 GBq (33 mCi) of NaI-131 requiring a directive; oral administration of >1.22 GBq (33 mCi) of NaI-131; parenteral administration of a radioactive drug primarily used for electron, beta, alpha, or photon energy <150 keV and requiring a directive.
- A written attestation from a preceptor AU or qualified residency program director is required.

**Hard numbers and units**
- Total training: 700 hours.
- Classroom training: 200 hours.
- Work experience: minimum 3 cases in each requested category.
- Oral NaI-131 category split: <=1.22 GBq (33 mCi) versus >1.22 GBq (33 mCi).
- Parenteral category includes photon energy <150 keV.

**Common confusions/exam traps**
- The 33 mCi oral I-131 split is about AU work-experience categories, not the 30 uCi written-directive trigger.
- The 700-hour total repeats here, but the classroom portion is larger than imaging/localization.

**Primary mini-game**
- `Directive-Level AU Builder`: complete the exact case mix and training packet needed to unlock independent written-directive practice.

**Optional micro-games**
- `Three Cases Each`: assign training cases to the correct AU category bucket.

**Story beat**
- The hidden program appears to have pushed someone across a written-directive boundary they were never formally cleared to cross.

**Repetition/unlock notes**
- This section should be revisited whenever the player tries to authorize higher-risk uses.

### 6.5 Radiopharmaceutical therapy
**Source scope**
- Introduces therapy-specific pregnancy screening.

**Facts to teach**
- A negative serum beta-hCG pregnancy test must be documented for potentially childbearing individuals under age 50 receiving therapeutic radiopharmaceuticals.
- The pregnancy test must be within 1 week of NaI-131 therapy.
- A test is not necessary after remote bilateral tubal ligation or hysterectomy.

**Hard numbers and units**
- Pregnancy-test timing: within 1 week.
- Age rule: under 50 years if potentially childbearing.

**Common confusions/exam traps**
- This is therapy-specific and easy to confuse with general pregnancy declaration rules for workers.

**Primary mini-game**
- `Therapy Clearance`: approve or hold a therapy case based on pregnancy-test timing and exclusion criteria.

**Optional micro-games**
- `Need the Test?`: quick edge-case screening.

**Story beat**
- One chart in the anomaly trail is missing the simplest pre-therapy safety proof of all.

**Repetition/unlock notes**
- Reuse as a short preflight gate before therapy levels.

### 6.5.1 Oral 131I NaI
**Source scope**
- Covers written-directive thresholds and baseline oral I-131 AU expectations.

**Facts to teach**
- The licensee must require a written directive dated and signed by an AU for oral administration of all I-131 quantities greater than 1.11 MBq (30 uCi).
- For quantities <=1.22 GBq (33 mCi), the AU must be a physician board certified by a recognized board or have completed 80 hours of classroom/lab training applicable to this use.
- For quantities >1.22 GBq (33 mCi), the AU must meet the same baseline physician requirements described here.

**Hard numbers and units**
- Written-directive trigger: >1.11 MBq = >30 uCi.
- Lower oral-therapy category: <=1.22 GBq = <=33 mCi.
- Alternate training route: 80 hours classroom/lab.

**Common confusions/exam traps**
- Classic pitfall: written directive is required for I-131 >30 uCi, not only for >33 mCi.
- The 33 mCi number matters for category split and release thresholds, but it is not the written-directive trigger.

**Primary mini-game**
- `I-131 Threshold Gate`: classify an oral I-131 order by whether it needs a directive, which AU category it belongs to, and whether the clinician is qualified.

**Optional micro-games**
- `30 uCi vs 33 mCi`: force repeated comparison of the two numbers in different scenarios.

**Story beat**
- The player spots the first unmistakable evidence that someone used the 33 mCi number where the 30 uCi rule should have controlled.

**Repetition/unlock notes**
- This threshold pair should be repeated aggressively across the campaign.

### 6.5.1.1 Inpatient
**Source scope**
- Covers inpatient therapy room setup, body-fluid precautions, visitors, surveys, and discharge readiness.

**Facts to teach**
- Inpatient therapeutic ionizing-radiation patients should be treated in a room with appropriate shielding such as lead or concrete.
- If shielding is unavailable, a corner private room away from stairwells/open areas is preferred, with head of bed against an outside wall.
- Additional protection can be placed between the door and patient.
- Before dosing, the room should be prepared with radiation-hazard and "no housekeeping services" signage, in-room linen/trash hampers, and plastic wrap on frequently touched surfaces like toilets, faucets, phones, and bedrails.
- Materials used in patient care stay in the room for the full hospital stay.
- Staff and visitors should minimize contact with body fluids.
- Anti-nausea planning matters because emesis is common.
- Male patients should sit to void, and all patients should flush twice with the lid closed.
- Vigorous hydration is encouraged to speed biologic elimination.
- Frequent showers during the first 2 weeks may reduce sweat-related contamination.
- In life-threatening emergencies, many facilities relax radiation restrictions to move the patient; CPR should use appropriate barriers.
- Pregnant visitors and visitors younger than 18 are prohibited.
- Visits are typically limited to 30 minutes and at least 6 feet away, depending on policy/state rules.
- Patient and room should be surveyed at prescribed points at least daily, including 1 meter from the chest, both sides of bed, foot of bed, doorway, visitor chair, inside/outside door, and adjacent patient wall.
- When the reading at 1 meter from the patient's chest is <=7 mrem/hour, the patient is generally considered safe for discharge, subject to state/facility variation.

**Hard numbers and units**
- Showers emphasized during first 2 weeks.
- Visitor limits commonly used: 30 minutes, at least 6 feet.
- Survey cadence: at least daily.
- Discharge benchmark: <=7 mrem/hour at 1 meter from chest.

**Common confusions/exam traps**
- "No housekeeping" and plastic-wrapped touch surfaces are memorable operational details.
- The 7 mrem/hour at 1 meter discharge benchmark is a major therapy number.

**Primary mini-game**
- `Therapy Room Prep`: set up the inpatient room, manage visitors, handle fluids, and keep survey points inside limits until discharge.

**Optional micro-games**
- `Room Survey Route`: walk the correct daily survey path around the room before time runs out.

**Story beat**
- The player's room-prep simulation mirrors a real room that was set up correctly on paper but not in practice.

**Repetition/unlock notes**
- This should be a long-form procedural level with repeatable survey and visitor-control subloops.

### 6.5.1.2 Outpatient
**Source scope**
- Covers outpatient I-131 release context and counseling around living destination.

**Facts to teach**
- NRC allows NaI-131 patients to be released when dose to third parties is not likely to exceed 500 mrem (5 mSv).
- The dose is assumed to affect family or caregivers most during the first few days after treatment.
- Treating physicians must consider living conditions and provide instructions that avoid unnecessary exposure.
- NRC strongly discourages recommending immediate hotel stays after outpatient thyroid treatment.
- If a patient insists on a hotel or other alternative location, the physician must still provide instructions on how to keep dose to others as low as possible.

**Hard numbers and units**
- Release benchmark to third parties: <=500 mrem = <=5 mSv.

**Common confusions/exam traps**
- Hotel guidance is not a formal numeric threshold but is a classic scenario detail.

**Primary mini-game**
- `Outpatient Release Counseling`: choose the safest discharge plan based on the patient's home situation, travel plan, and willingness to follow instructions.

**Optional micro-games**
- `Home or Hotel`: predict which living arrangement creates the biggest third-party exposure problem.

**Story beat**
- The player learns that the suspicious outpatient case was released to a setting nobody should have recommended.

**Repetition/unlock notes**
- Reuse counseling choices with different home and caregiver constraints.

### 6.5.1.3 Release criteria
**Source scope**
- Covers release based on projected TEDE, activity table, dose-rate table, breastfeeding instructions, and record retention.

**Facts to teach**
- A patient may be released if TEDE to any other individual is not likely to exceed 5 mSv (0.5 rem), or if administered activity is at or below Table 7 values.
- If dose to others is likely to exceed 1 mSv (0.1 rem), written instructions must be provided to keep doses ALARA.
- Table 7 values are: Cu-64 8.4 GBq/230 mCi or 0.27 mSv/hour (27 mrem/hour) at 1 meter; I-123 6.0 GBq/160 mCi or 0.26 mSv/hour (26 mrem/hour); I-125 implant 0.33 GBq/9 mCi or 0.01 mSv/hour (1 mrem/hour); I-131 1.2 GBq/33 mCi or 0.07 mSv/hour (7 mrem/hour); In-111 2.4 GBq/64 mCi or 0.2 mSv/hour (20 mrem/hour); Tc-99m 28 GBq/760 mCi or 0.58 mSv/hour (58 mrem/hour); Tl-201 16 GBq/430 mCi or 0.19 mSv/hour (19 mrem/hour); Y-90 not applicable.
- If breastfeeding child dose could exceed 1 mSv (0.1 rem) without interruption, instructions must include interruption/discontinuation guidance and consequences of nonadherence.
- Release-basis records must be kept for 3 years when TEDE is calculated using retained activity, occupancy factor <0.25 at 1 meter, biologic/effective half-life, or self-shielding by tissue.

**Hard numbers and units**
- Release TEDE ceiling: 5 mSv = 0.5 rem.
- Written-instruction trigger: >1 mSv = >0.1 rem to others.
- Key release numbers: I-131 33 mCi or 7 mrem/hour at 1 meter; other table rows as listed above.
- Occupancy-factor recordkeeping trigger: <0.25 at 1 meter.
- Record retention: 3 years.

**Common confusions/exam traps**
- Release can be justified by projected dose, activity, or dose rate.
- Another classic pitfall: 33 mCi is a release number, not the written-directive threshold.

**Primary mini-game**
- `Release Desk`: calculate whether the patient can go home, whether written instructions are needed, and which release basis must be archived.

**Optional micro-games**
- `Activity or Dose Rate`: choose the fastest valid release basis in a time-pressured scenario.

**Story beat**
- Release records reveal that the hidden protocol depended on assumptions like occupancy factor and self-shielding that were never clearly justified.

**Repetition/unlock notes**
- This is one of the campaign's biggest spaced-repetition levels because it combines thresholds, tables, and counseling.

### 6.5.2 Parenteral therapy (alpha, beta)
**Source scope**
- Covers AU expectations and supervised work-experience content for parenteral therapy.

**Facts to teach**
- AU for parenteral administration requiring a written directive must be a physician who is already an AU or equivalent under Agreement State rules, or a recognized-board-certified physician with appropriate training and supervised work experience.
- Work experience must include safe ordering, receiving, and unpacking of radioactive material; related radiation surveys; QC procedures; survey-meter checks; dose calculation and preparation; administrative controls to prevent medical events; spill containment and decontamination; and at least 3 cases of parenteral administration.
- Written attestation is required from a preceptor AU or qualifying residency program director.

**Hard numbers and units**
- Minimum supervised case count: at least 3 parenteral administrations.

**Common confusions/exam traps**
- Parenteral therapy is its own supervised-case pathway and should not be collapsed into oral I-131 rules.

**Primary mini-game**
- `Parenteral Therapy Sign-off`: complete the required supervised case set before independent administration unlocks.

**Optional micro-games**
- `Which Experience Counts`: choose whether a proposed prior case satisfies parenteral training requirements.

**Story beat**
- The player sees that someone touched parenteral therapy workflow without the full case history to back it up.

**Repetition/unlock notes**
- Works well as a gated progression mechanic between midgame and incident chapters.

### 6.6 Radiopharmacy ("hot lab")
**Source scope**
- Introduces hot-lab security and the role of the dose calibrator.

**Facts to teach**
- Licensed materials must be secured either by locked storage or constant surveillance.
- The hot lab is used to receive, store, and/or prepare radiopharmaceuticals for patient studies.
- The dose calibrator measures radioactivity in vials, syringes, capsules, and similar containers.
- The calibrator is often placed behind lead or leaded-glass shielding to protect the operator.
- Patient dosages and shielded vials are commonly placed or stored behind this shield.

**Hard numbers and units**
- No numeric threshold; this section is operational and spatial.

**Common confusions/exam traps**
- "Secured" can mean locked storage or constant surveillance.

**Primary mini-game**
- `Hot Lab Layout`: arrange the calibrator, shield, storage, pass-through, and surveillance coverage so the lab is both usable and compliant.

**Optional micro-games**
- `Locked or Watched`: decide whether a scenario satisfies the security rule.

**Story beat**
- The hot lab is where the player first finds physical traces that the hidden protocol was real.

**Repetition/unlock notes**
- Keep the hot-lab layout as a hub the player revisits between clinical missions.

### 6.6.1 Safe procedures
**Source scope**
- Covers annual safety instruction and care requirements for patients who cannot be released.

**Facts to teach**
- Radiation safety instruction must be provided initially and at least annually to personnel caring for patients or research subjects who cannot be released.
- Instruction must include patient control, visitor control, contamination and waste control, and notification of the RSO/designee and AU if a medical emergency or death occurs.
- The licensee must retain a record of who received instruction.
- Patients who cannot be released must be quartered in a private room with private sanitary facilities or with another similarly treated patient who also cannot be released.
- The room must be visibly posted with a "Radioactive Materials" sign.
- The door or chart must specify where and how long visitors may stay.
- Material/items removed from the room must either be monitored to background or handled as radioactive waste.
- RSO/designee and AU must be notified as soon as possible if the patient has a medical emergency or dies.

**Hard numbers and units**
- Safety-instruction cadence: initially and at least annually.

**Common confusions/exam traps**
- Annual instruction and room posting requirements are easy to conflate with the detailed inpatient I-131 setup section; both matter.

**Primary mini-game**
- `Unreleased Patient Unit`: manage a therapy patient's room, staff education, item handling, and emergency escalation without breaking isolation rules.

**Optional micro-games**
- `Background or Waste`: decide whether an item may leave the room normally.

**Story beat**
- Emergency notification logic becomes crucial when the suspicious case suddenly destabilizes.

**Repetition/unlock notes**
- Reuse as a procedural-control level during any hospitalized therapy scene.

### 6.6.2 Generator systems
**Source scope**
- Introduces generator systems before elution and QC details.

**Facts to teach**
- Generator systems are used to provide sterile, pyrogen-free product for human injection or compounding.
- Different commercial designs require different elution procedures.
- Breakthrough of parent radionuclide is a core QC concern.

**Hard numbers and units**
- Quantitative breakthrough limits appear in 6.6.2.2.

**Common confusions/exam traps**
- The generator section is a setup for elution and QC, not an isolated topic.

**Primary mini-game**
- `Generator Room`: choose the right generator workflow before the player can proceed to elution and breakthrough testing.

**Optional micro-games**
- `Parent or Daughter`: identify which radionuclide is the breakthrough risk.

**Story beat**
- Generator records suggest the hidden protocol may have depended on exploiting a QC blind spot.

**Repetition/unlock notes**
- Use this as a short gateway level before the more numeric QC section.

### 6.6.2.1 Elution
**Source scope**
- Covers purpose and variation of elution procedures.

**Facts to teach**
- Elution procedures are designed to yield a sterile, pyrogen-free product suitable for human injection or compounding.
- Exact elution technique varies by commercial generator design.

**Hard numbers and units**
- No numeric threshold; emphasis is on purpose and variability.

**Common confusions/exam traps**
- "One generator, one method" is false; commercial design differences matter.

**Primary mini-game**
- `Elution Sequence`: perform the correct generator-specific elution steps in order without compromising sterility.

**Optional micro-games**
- `Why Elute`: pick the best explanation for each step in the process.

**Story beat**
- A generator used in the anomaly was handled as though it were a different commercial model.

**Repetition/unlock notes**
- This can be a dexterity/order-memory subgame nested inside the QC level.

### 6.6.2.2 Quality control
**Source scope**
- Covers Mo-99, Sr-82, and Sr-85 breakthrough limits, daily testing, phone/written reporting, and the Ga-68 note.

**Facts to teach**
- A radiopharmaceutical administered to humans may not contain more than 0.15 kBq of Mo-99 per MBq of Tc-99m, more than 0.02 kBq of Sr-82 per MBq of Rb-82 chloride, or more than 0.2 kBq of Sr-85 per MBq of Rb-82.
- Eluates from each generator should be measured to demonstrate compliance.
- For Sr-82/Rb-82 generators, Sr-82 and Sr-85 concentration should be measured before the first patient of the day.
- Telephone reporting is required within 7 calendar days after discovery that an eluate exceeded the permissible concentration.
- A written report to NRC is required within 30 calendar days and must include actions taken, patient dose assessment, methodology if administered, probable cause, and assessment of equipment/procedure/training failure if breakthrough determination was wrong.
- Ga-68 can be produced by cyclotron or Ge-68/Ga-68 generator.
- Breakthrough of Ge-68 is possible and can unnecessarily increase patient dose.
- No NRC breakthrough limit comparable to Tc-99m or Rb-82 is specified for Ge-68/Ga-68 generators; applicants must commit individually to safety protocols.

**Hard numbers and units**
- Mo-99/Tc-99m limit: 0.15 kBq/MBq = 0.15 uCi/mCi.
- Sr-82/Rb-82 limit: 0.02 kBq/MBq = 0.02 uCi/mCi.
- Sr-85/Rb-82 limit: 0.2 kBq/MBq = 0.2 uCi/mCi.
- Sr testing cadence: before first patient of the day.
- Phone report: within 7 calendar days.
- Written report: within 30 calendar days.

**Common confusions/exam traps**
- The three numeric breakthrough limits are easy to scramble.
- Ga-68 is a classic "there is no specific NRC limit here" trap.

**Primary mini-game**
- `Breakthrough Analyzer`: test eluates, reject unsafe product, and file the correct report when a parent radionuclide breaks through.

**Optional micro-games**
- `0.15, 0.02, 0.2`: high-speed recall challenge for Mo/Sr breakthrough limits.

**Story beat**
- The player finally finds a technical route by which the hidden protocol could have changed real patient exposure.

**Repetition/unlock notes**
- This should be replayed often because it combines unit conversion, timing, and consequence.

### 6.6.3 Recordkeeping
**Source scope**
- Covers record integrity, lost/stolen material, 30-day written reports, and multiple record-retention categories.

**Facts to teach**
- Required records must remain legible, may be original or reproduced, may be electronic if they can produce complete records, and must be safeguarded against tampering and loss.
- Lost, stolen, or missing licensed material that could expose people in unrestricted areas must be reported by telephone.
- A written report within 30 days of that telephone report must include material description, circumstances of loss/theft, disposition, exposures and possible TEDE to people in unrestricted areas, recovery actions, and recurrence-prevention measures.
- Written reports within 30 days are also required after learning of occupational dose-limit exceedances, embryo/fetus/public limit exceedances, excessive air emissions, excessive radiation in restricted space, or 10 times unrestricted-area limits.
- Reports should include dose estimates, levels involved, cause, and corrective steps.
- For occupational overexposure, reports should include name, Social Security number, and date of birth labeled as Privacy Act information.
- RSO-authority and radiation-program-change records are kept for 5 years and include summary of actions and management signature.
- Written directives are retained for 3 years.
- Instrument/radiation-survey calibrations are retained for 3 years with model, serial, date, results, and performer.
- Dosage determinations are retained for 3 years and include radiopharmaceutical, patient name/ID, prescribed dose, determined dose with date/time or notation under 1.1 MBq (30 uCi), and the person who determined the dose.
- Leak tests are retained for 3 years and include model/serial, source identity, activity, test result, and tester.
- Semiannual physical inventories of sealed sources and brachytherapy sources are retained for 3 years.
- Ambient-radiation surveys are retained for 3 years and include date, result, instrument, and surveyor.
- Release-basis records for patients with unsealed material or implants are retained for 3 years when based on retained activity, occupancy factor <0.25 at 1 meter, or biologic/effective half-life.
- The source text also states that a record should be kept for 3 years that breastfeeding instructions were provided if continued breastfeeding could exceed 5 mSv (0.5 rem) to the infant or child.

**Hard numbers and units**
- Lost/stolen follow-up written report: 30 days.
- RSO/program-change records: 5 years.
- Most other listed categories here: 3 years.
- Dosage-determination notation threshold: <1.1 MBq = <30 uCi.
- Unrestricted-area escalation phrase: 10 times unrestricted-area limits.
- Occupancy-factor release-record trigger: <0.25 at 1 meter.

**Common confusions/exam traps**
- Recordkeeping is full of 3-year rules, but not everything is 3 years.
- Lost/stolen phone report plus 30-day written report is distinct from the 7-day/30-day generator breakthrough timeline.

**Primary mini-game**
- `Compliance Archive`: classify each event and file the correct report, privacy labels, and retention period before an inspector arrives.

**Optional micro-games**
- `Three Years, Five Years, or 30 Days`: mixed-timeline recall drill.

**Story beat**
- The truth of the hidden protocol survives only in fragments across record systems the player must piece together.

**Repetition/unlock notes**
- This should be the late-game mastery loop because it ties the entire campaign together.

## Chapter 7. Emergency Procedures, Accidents and Incidents, Special Circumstances

### Chapter Overview
- Source scope: medical/reportable events, spills, contamination limits, dirty-bomb emergencies, personal contamination, decontamination, and ARS.
- Learning goal: teach how to triage a bad day in nuclear medicine without losing sight of thresholds, sequence, life-saving priorities, and reporting significance.
- Chapter story beat: the anomaly becomes an active incident, and the player has to respond before there is time for perfect paperwork.

### 7.1 Medical events/reportable events
**Source scope**
- Defines what a medical event is and what it does and does not imply.

**Facts to teach**
- A medical event does not automatically mean patient harm; it means there may have been a problem in the facility's use of radioactive materials.
- A medical event occurs only if both a dose-difference threshold and a qualifying incident criterion are met.
- Dose-difference thresholds are: >5 rem (0.05 Sv) effective dose equivalent, >50 rem (0.5 Sv) to an organ/tissue, or >50 rem (0.5 Sv) shallow dose equivalent to the skin.
- Qualifying incidents are: dose off by at least 20% high or low, wrong drug, wrong route, wrong individual, wrong body part with >=50% excess to that area, or leaking sealed source used in treatment.
- NRC requires reporting because a medical event signals a problem in administration or quality assurance, not because harm is guaranteed.
- Harm can come from too much dose or from inadequate treatment if dose is too low.
- NRC analyzes events for enforcement and for trends that may need clarified rules or guidance.
- Severe events may prompt review by an independent medical consultant.

**Hard numbers and units**
- Medical-event dose thresholds: >5 rem EDE, >50 rem organ/tissue, >50 rem skin.
- Incident trigger examples: >=20% wrong dose, >=50% excess to wrong body area.

**Common confusions/exam traps**
- Both halves of the definition must be met.
- A medical event is not synonymous with patient harm.

**Primary mini-game**
- `Medical Event Judge`: decide whether a case crosses the legal definition of a medical event by checking both the dose threshold and the event type.

**Optional micro-games**
- `Both Must Be True`: pair each scenario with "event," "not event," or "needs more data."

**Story beat**
- The player realizes the anomaly was hidden partly by blurring "bad outcome," "bad paperwork," and "medical event."

**Repetition/unlock notes**
- This binary two-part test should recur in later debrief sequences.

### 7.2 Radiation spills
**Source scope**
- Introduces spill classification logic and the isotope-specific spill table.

**Facts to teach**
- Choosing major versus minor spill response depends on how much material spilled, who is affected, other hazards, spread risk, and radiotoxicity.
- For some short-lived spills, the best response may be restricted access until complete decay.
- Basic decision steps are: estimate activity spilled, compare with the dividing line in Table 8, and note whether evacuation is required.
- Table 8 thresholds are: Ac-225 any amount major; Pb-212 any amount major; Ra-223 any amount major; Xe-133 gas any amount evacuate; I-131 1 mCi minor/major line; Y-90 1 mCi; Lu-177 2 mCi; Cu-64 10 mCi major and 50 mCi evacuate; Ga-67 10 mCi major; In-111 10 mCi major; I-123 10 mCi major and 15 mCi evacuate; Rb-82 10 mCi major and 50 mCi evacuate; Ga-68 20 mCi major and 100 mCi evacuate; F-18 100 mCi major and 250 mCi evacuate; Tc-99m 100 mCi major and 400 mCi evacuate; Tl-201 100 mCi major.

**Hard numbers and units**
- Spill thresholds and evacuate levels listed above.

**Common confusions/exam traps**
- Some radionuclides have "any amount" or gas-driven evacuation rules rather than simple numeric minor-major cutoffs.
- Spill level tables are perfect spaced-repetition material because many values are similar.

**Primary mini-game**
- `Spill Table Dispatch`: identify isotope, estimate spilled activity, and launch minor, major, or evacuate response before contamination spreads.

**Optional micro-games**
- `1, 2, 10, 20, 100`: clustered threshold recall challenge.

**Story beat**
- The anomaly finally crosses from paperwork to live contamination risk.

**Repetition/unlock notes**
- This should be a signature replay mode because the numbers lend themselves to repetition.

### 7.2.1 Major spill - response and handling
**Source scope**
- Gives the ordered major-spill response sequence.

**Facts to teach**
- Major-spill response sequence is: clear the area, prevent the spread by covering but not cleaning, shield the source if possible without more contamination/exposure, close/secure the room, call the RSO immediately, decontaminate personnel, and let the RSO supervise cleanup and forms.
- Personnel decontamination includes removing contaminated clothing, flushing skin with lukewarm water, washing with mild soap, and if contamination remains, inducing perspiration under plastic and washing again.

**Hard numbers and units**
- No new thresholds; sequence order is the key memory item.

**Common confusions/exam traps**
- For a major spill, you cover but do not attempt routine cleanup before the RSO takes over.

**Primary mini-game**
- `Major Spill Triage`: perform the correct ordered actions while a contamination cloud expands across the room.

**Optional micro-games**
- `Sequence Lock`: place the seven major-spill steps in the correct order.

**Story beat**
- The player has to seal off the very room tied to the mystery before anyone can sanitize the evidence away.

**Repetition/unlock notes**
- This should be a timed order-memory game with increasing pressure.

### 7.2.2 Minor spill - response and handling
**Source scope**
- Gives the ordered minor-spill response sequence.

**Facts to teach**
- Minor-spill response sequence is: notify people in the area, cover with absorbent paper, clean up with gloves and absorbent paper, bag contaminated disposables into labeled radioactive waste, survey the area and yourself, report to the RSO, and document the spill and contamination survey.
- Survey should include surrounding area plus hands, clothing, and shoes.

**Hard numbers and units**
- No new thresholds; sequence order and self-check points are the memory anchors.

**Common confusions/exam traps**
- Unlike a major spill, minor-spill cleanup proceeds locally before reporting is complete.

**Primary mini-game**
- `Minor Spill Cleanup`: perform a careful cleanup without turning a minor spill into a major spread event.

**Optional micro-games**
- `Bag It Right`: decide which materials go into labeled radioactive waste.

**Story beat**
- A minor spill near the hidden protocol's supply chain becomes the player's chance to preserve evidence instead of losing it.

**Repetition/unlock notes**
- Use this as a lower-stakes practice loop before the major-spill version appears.

### 7.2.3 Surface contamination limits
**Source scope**
- Covers wipe methodology and restricted-area removable contamination limits.

**Facts to teach**
- Removable contamination is measured by wiping 100 cm2 with filter paper or soft absorbent paper using moderate pressure and measuring the activity on the wipe with an instrument of known efficiency.
- If the object has less surface area, limits are reduced proportionally and the entire surface should be wiped.
- Restricted-area surface contamination limits listed are: all alpha emitters 200 dpm/100 cm2; In-111, I-123, I-131, Lu-177, Y-90 at 2,000 dpm/100 cm2; Ga-67, Tc-99m, Tl-201 at 20,000 dpm/100 cm2.

**Hard numbers and units**
- Standard wipe area: 100 cm2.
- Limits: alpha 200; In-111/I-123/I-131/Lu-177/Y-90 2,000; Ga-67/Tc-99m/Tl-201 20,000 dpm/100 cm2.

**Common confusions/exam traps**
- Wipe area and proportional reduction matter.
- Alpha-contamination limit is much lower than the common gamma-emitter groups.

**Primary mini-game**
- `Wipe Test Lab`: perform contamination wipes and classify the surface as pass, restricted, or escalation-required.

**Optional micro-games**
- `200, 2000, 20000`: quick limit-matching drill.

**Story beat**
- Surface wipe results provide the first objective proof that the "officially clean" room was not clean.

**Repetition/unlock notes**
- These contamination tiers should recur anytime the player decontaminates or clears an area.

### 7.2.4 Medical/Nonmedical emergencies (e.g., "dirty bomb")
**Source scope**
- Covers dirty-bomb background, priorities, protection principles, and agency context.

**Facts to teach**
- Primary response is always to address life- or limb-threatening medical situations first.
- A dirty bomb is an RDD combining conventional explosive with radioactive material.
- Most RDDs would injure people more through the conventional explosive than through radiation.
- A dirty bomb is not a nuclear bomb and is described here as a "weapon of mass disruption," not mass destruction.
- Local contamination severity depends on explosive size, material amount/type, dispersal, and weather.
- Immediate health effects from expected low radiation levels are likely minimal.
- Radiation injury depends on absorbed dose, radiation type, distance, exposure route (external versus internal), and duration.
- Protection is afforded by minimizing time, maximizing distance, and shielding from external exposure and inhalation.
- Radioactive materials are widely used under more than 22,000 licenses, but most sources would not be useful in an RDD.
- NRC and Agreement States use multilayered source-security programs, and federal partners such as DHS, EPA, and FEMA are involved in RDD response.
- In personal-injury accidents involving radioactive material, medical care comes first and radiation control must not delay care; emergency personnel should be warned so they can protect themselves and limit spread.

**Hard numbers and units**
- U.S. licensing scale mentioned: more than 22,000 licenses.

**Common confusions/exam traps**
- Dirty-bomb fear is often larger than dirty-bomb radiation lethality.
- The correct first move is medical stabilization, not contamination perfectionism.

**Primary mini-game**
- `RDD Command`: triage injuries, establish time-distance-shielding controls, and communicate protective actions to responders and the public.

**Optional micro-games**
- `Mass Destruction or Disruption`: classify scenario language and spot exaggerated claims.

**Story beat**
- The mystery peaks when the player realizes the hidden protocol could trigger panic far beyond its direct dose consequences.

**Repetition/unlock notes**
- This works best as a long-form scenario level with branching outcomes.

### Derived: Personal contamination and decontamination
**Source scope**
- Derived entry from the unnumbered "Personal Contamination" and "Decontamination Procedures" blocks after 7.2.4.

**Facts to teach**
- Personal contamination response: remove contaminated lab PPE, wash the contaminated area with mild soap and water if possible, monitor the area, and repeat washing as needed.
- Surface/equipment decontamination response: mark the perimeter, notify the RSO, assemble cleaning supplies, scrub from borders to center in small areas, periodically check progress with wipes and portable instrument surveys, bag contaminated cleaning material as radioactive waste, and notify Environmental Health and Safety for follow-up survey.

**Hard numbers and units**
- No new thresholds; sequence and directionality are the memory anchors.

**Common confusions/exam traps**
- Personal decontamination is not identical to room decontamination.
- Cleaning should move from borders toward the center to avoid spreading contamination.

**Primary mini-game**
- `Decon Corridor`: alternate between treating a contaminated person and cleaning a contaminated lab space without cross-contaminating either one.

**Optional micro-games**
- `Border to Center`: pathing drill that punishes cleaning in the wrong direction.

**Story beat**
- The player is forced to decide whether to preserve evidence or over-clean a room before proper survey data are captured.

**Repetition/unlock notes**
- This is a strong tactile replay mechanic that can be reused in multiple chapters.

### Derived: Acute Radiation Syndrome
**Source scope**
- Derived entry from the unnumbered ARS block and figure references at the end of the chapter, with figure emphasis supplemented conservatively by the helper document.

**Facts to teach**
- ARS requires acute high-dose exposure >0.7 Gy, high dose rate over a short interval, external penetrating radiation, and exposure of more than 70% of the body.
- The four phases are prodromal, latent, manifest illness, and recovery or death.
- Higher doses shorten the interval between phases and worsen symptoms.
- ARS subsyndromes are hematopoietic, gastrointestinal, and neurovascular.
- Helper-supported figure details: hematopoietic syndrome appears around 2 to 10 Gy with pancytopenia, infection, and bleeding over weeks; gastrointestinal syndrome around 10 to 50 Gy with severe nausea/vomiting/diarrhea and GI hemorrhage over days; neurovascular syndrome above 50 Gy with seizures, ataxia, and coma over hours to days.
- Estimated LD50/60 for acute whole-body low-LET irradiation is 3.5 to 4.0 Gy without intervention.
- Supportive care raises LD50/60 to about 4.5 to 7 Gy.
- Intensive care, reverse isolation, and hematopoietic cell transplantation may raise LD50/60 to about 7 to 9 Gy.
- FDA-approved ARS treatments named here are filgrastim, PEGylated filgrastim, sargramostim, and romiplostim.
- Treatment also relies on fluids/electrolytes, blood products, antimicrobial prophylaxis, and careful management of infection, bleeding, nutrition, and electrolytes.

**Hard numbers and units**
- ARS entry criteria: >0.7 Gy and >70% body exposure.
- Hematopoietic: about 2 to 10 Gy.
- GI: about 10 to 50 Gy.
- Neurovascular: >50 Gy.
- LD50/60: 3.5 to 4.0 Gy without care; 4.5 to 7 Gy with supportive care; 7 to 9 Gy with intensive care/transplant.

**Common confusions/exam traps**
- ARS is not just "high dose"; it also depends on acute timing, penetrating external exposure, and whole-body fraction.
- Phase order and subsyndrome dose ranges are classic recall targets.

**Primary mini-game**
- `ARS Triage Ward`: diagnose phase and subsyndrome from symptoms and exposure history, then deploy the right supportive or colony-stimulating treatment path.

**Optional micro-games**
- `Phase Timeline`: place prodromal, latent, manifest illness, and recovery/death in order and tie each to likely symptoms.

**Story beat**
- The player finally sees what the hidden protocol was actually risking if it ever escaped controlled conditions.

**Repetition/unlock notes**
- This should function as a late-game capstone that tests recall from biology, dose, and emergency chapters at once.

## Chapter 8. Appendix 1. Radiation-Measuring Instrumentation and Quality Control Tests

### Chapter Overview
- Source scope: appendix-level instrumentation and QC concepts for counters, scintillation systems, ionization chambers, calibrators, and radio-TLC.
- Learning goal: teach the player which instrument answers which question, what each device can and cannot tell you, and how QC validates the mystery's physical evidence.
- Chapter story beat: the player stops trusting paperwork and starts trusting instruments.

### Derived: Geiger-Mueller counter
**Source scope**
- Derived entry from the first appendix block describing the GM counter.

**Facts to teach**
- A GM counter has a sealed gas-filled tube/chamber plus an information display.
- Radiation creates ion pairs in the gas, and the resulting current is displayed as counts.
- GM counters usually provide counts per minute.
- A GM counter indicates that ion pairs were created but does not identify radiation type or energy.

**Hard numbers and units**
- Common display unit: counts per minute.

**Common confusions/exam traps**
- A GM counter can tell you that something is being detected, but not what isotope or energy is responsible.

**Primary mini-game**
- `GM Sweep`: scan a room fast enough to find contamination while remembering the instrument's information limits.

**Optional micro-games**
- `What It Cannot Tell You`: choose when a GM reading is insufficient and a different instrument is needed.

**Story beat**
- The player realizes the earlier investigators used the right instrument to detect a problem but the wrong instrument to fully characterize it.

**Repetition/unlock notes**
- GM sweeps should recur as a quick transition game between story scenes.

### Derived: Well counter
**Source scope**
- Derived entry from the appendix block describing well counters.

**Facts to teach**
- Well counters perform high-sensitivity counting of radioactive specimens such as blood, urine, or wipe samples.
- They use a cylindrical scintillation crystal, usually thallium-doped sodium iodide, with a well and a photomultiplier tube.
- Modern systems may include a multichannel analyzer for isotope-selective counting and an automatic sample changer.
- High intrinsic and geometric efficiency make well counters extremely sensitive.
- They are reliable only up to about 37 kBq (0.001 mCi); above that, dead-time losses make counts inaccurate.

**Hard numbers and units**
- Reliable upper activity range: about 37 kBq = 0.001 mCi.

**Common confusions/exam traps**
- High sensitivity is a strength only within the device's count-rate limits.

**Primary mini-game**
- `Specimen Counter`: choose whether a wipe, blood, or urine sample belongs in the well counter and reject samples that are too hot to measure accurately.

**Optional micro-games**
- `Dead-Time Warning`: stop the player from trusting a falsely low count caused by excessive activity.

**Story beat**
- A forgotten wipe sample becomes decisive because a well counter can still read what the room survey missed.

**Repetition/unlock notes**
- Use as a precision-analysis minigame after broad GM survey levels.

### Derived: Scintillation detection systems
**Source scope**
- Derived entry from the appendix block on liquid and solid scintillation systems.

**Facts to teach**
- Scintillation systems use a material that flashes light when ionizing radiation interacts with it.
- Liquid scintillation counting is used to identify and quantify low levels of radioactivity, especially contamination or particulate-emitter samples such as beta and alpha emitters.
- Solid scintillators are sensitive to gamma radiation and can measure dose rates in the urem/hour range.

**Hard numbers and units**
- Sensitivity note: solid scintillators can measure dose rates in the urem/hour range.

**Common confusions/exam traps**
- Liquid scintillation is especially useful for low-level alpha/beta sample work, while solid scintillation is commonly associated with gamma detection.

**Primary mini-game**
- `Flash Chamber`: choose liquid or solid scintillation setup based on the sample and radiation type.

**Optional micro-games**
- `Light Means Radiation`: short association drill for scintillation principles.

**Story beat**
- The player starts differentiating which instruments can truly expose the hidden protocol's footprint.

**Repetition/unlock notes**
- Best used as a short instrumentation-choice loop.

### Derived: Ionization chamber/dose calibrator
**Source scope**
- Derived entry from the appendix block on ionization chambers and dose calibrators.

**Facts to teach**
- An ionization chamber measures ions in a medium using a gas-filled enclosure between anode and cathode.
- Ionization current is proportional to the number of ions created.
- Ionization chambers can be open or sealed depending on function.
- Open ionization chambers are typically used as personal dosimeters.
- Radioisotope dose calibrators are sealed ionization chambers widely used in nuclear medicine and calibrated to specific isotopes.
- Dose calibrator output is proportional to radiation dose/activity for the calibrated isotope.

**Hard numbers and units**
- No single threshold; the main facts are configuration and purpose.

**Common confusions/exam traps**
- The same physical principle supports both personal-dosimetry uses and isotope-specific dose-calibrator uses.

**Primary mini-game**
- `Calibrator Bench`: place a vial in the chamber, choose the isotope setting, and verify whether the measured activity supports safe dispensing.

**Optional micro-games**
- `Open or Sealed`: decide which chamber type fits the described use.

**Story beat**
- The final proof of the hidden protocol comes from calibrator data that cannot be explained away by sloppy paperwork.

**Repetition/unlock notes**
- This should be the appendix's central recurring mechanic because it connects directly back to Chapters 5 and 6.

### Derived: Radio-TLC
**Source scope**
- Derived entry from the appendix block on radio-thin-layer chromatography.

**Facts to teach**
- Radio-TLC is commonly used to analyze radiopharmaceutical purity or reaction conversion during radiosynthesis optimization.
- When there are only a few radioactive species, radio-TLC is preferred over radio-HPLC because it is simpler and faster.
- Many radio-TLC approaches are extensions or modifications of paper chromatography methods.

**Hard numbers and units**
- No numeric threshold; the memory point is use case and preferred context.

**Common confusions/exam traps**
- Radio-TLC is not the all-purpose "best" test; it is preferred when the species mix is simple and rapid analysis matters.

**Primary mini-game**
- `Purity Strip`: run a radiochemical purity check and decide whether the preparation is fit for use or needs to be rejected.

**Optional micro-games**
- `TLC or HPLC`: choose the simpler correct QC method based on species complexity.

**Story beat**
- The campaign closes with the player using basic QC science, not rumors, to confirm what the hidden project was doing.

**Repetition/unlock notes**
- Use as the final validation mechanic at the end of major chapter arcs.

## Final Design Principles
- Every subsection above should become at least one playable unit with failure states tied to the exact fact pattern of that subsection.
- Dense number sets should be repeated through escalating pattern-recognition loops rather than generic multiple-choice prompts.
- The mystery should motivate attention, not replace study value; every reveal should ride on the player correctly applying RISC knowledge.
- If this design is later adapted into an app, the safest progression model is chapter hub -> subsection level -> optional micro-game drills -> chapter debrief -> story reveal.
