#!/usr/bin/env python3
"""Generate Textbook Copier assets for Radiologic Physics - War Machine."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
import unicodedata

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pdf_text_compare import extract_pdf


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = REPO_ROOT / "apps" / "core-studying" / "War Machine Physics"
PDF_PATH = BOOK_DIR / "Radiologic physics _ war machine -- Prometheus Lionhart M_D.pdf"
TXT_DIR = BOOK_DIR / "TXT"
MANIFEST_PATH = BOOK_DIR / "index.json"

INVALID_FILENAME_CHARS_RE = re.compile(r'[<>:"/\\|?*]')
MULTISPACE_RE = re.compile(r"\s+")
MATCH_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class SectionSpec:
    title: str
    page_hint: int
    match_titles: tuple[str, ...] = ()

    @property
    def candidates(self) -> tuple[str, ...]:
        return self.match_titles or (self.title,)


@dataclass(frozen=True)
class ChapterSpec:
    key: str
    title: str
    start_page: int
    end_page: int
    sections: tuple[SectionSpec, ...]
    intro_titles: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolvedSection:
    title: str
    file_name: str
    heading_page: int
    heading_line: int
    end_page: int
    end_line_exclusive: int
    candidates: tuple[str, ...]


CHAPTER_SPECS: tuple[ChapterSpec, ...] = (
    ChapterSpec(
        key="01",
        title="X-Ray Production / Generation",
        start_page=8,
        end_page=29,
        intro_titles=("X-RAY PRODUCTION / GENERATION",),
        sections=(
            SectionSpec(
                "Electromagnetic Radiation",
                8,
                ("What is this “ Electromagnetic Radiation?”", "What is this Electromagnetic Radiation"),
            ),
            SectionSpec("X-Rays vs Gamma Rays", 9, ("This vs That: X-Rays vs Gamma Rays",)),
            SectionSpec(
                "Alpha and Beta Particles",
                10,
                ("Answer Time - Yup... Alpha and Beta Particles.", "Alpha Particles -"),
            ),
            SectionSpec("Atomic Structure", 11, ("Atomic Structure:",)),
            SectionSpec("X-Ray Production", 12, ("X-Ray Production:",)),
            SectionSpec("Housing vs Enclosure", 13, ("This vs That: Housing vs Enclosure",)),
            SectionSpec(
                "Characteristic Radiation and Auger Electrons",
                14,
                ("Characteristic Radiation (characteristic x- rays):",),
            ),
            SectionSpec("Bremsstrahlung", 16, ("Bremsstrahlung “ Brems” (radiative losses)",)),
            SectionSpec("Anatomy of the Spectrum", 17, ("Anatomy of the Spectrum",)),
            SectionSpec("X-Ray Generator", 18, ("X-Ray Generator:",)),
            SectionSpec("X-Ray Spectrum Manipulation", 19, ("X-Ray Spectrum Manipulation",)),
            SectionSpec("Changing Targets", 20, ("Changing Targets",)),
            SectionSpec("Half Value Layer (HVL)", 21, ("Half Value Layer (HVL):",)),
            SectionSpec(
                "Testable Trivia Recap and Rapid Review",
                22,
                ("Testable Trivia Recap and Rapid Review",),
            ),
            SectionSpec("DEXA Scan", 23, ("DEXA Scan",)),
            SectionSpec("Focal Spot", 24, ("Focus on the Focal Spot",)),
            SectionSpec(
                "Line Focus Principle",
                25,
                ("Changes in Angle / Line Focus Principal:", "Line Focus Principal"),
            ),
            SectionSpec("Heel Effect", 26, ("The Heel (Anode-Heel) Effect",)),
            SectionSpec(
                "Practical Applications of the Heel Effect",
                27,
                ("Practical Applications - There are two main ones:",),
            ),
            SectionSpec(
                "Effect of mA / kVp on the Focal Spot",
                28,
                ("Effect of mA / kVp on the Focal Spot",),
            ),
            SectionSpec("Misc Vocab and Unwanted Radiation", 29, ("— Misc Vocab", "Misc Vocab")),
        ),
    ),
    ChapterSpec(
        key="02",
        title="X-Ray Interaction With Matter",
        start_page=30,
        end_page=39,
        intro_titles=("X-Ray Interaction With Matter",),
        sections=(
            SectionSpec(
                "Diagnostic and Nondiagnostic Interactions",
                30,
                ("Occur at Dx Energy:",),
            ),
            SectionSpec("Compton Scattering", 31, ("Compton Scattering (“ The Bad Guy” ):",)),
            SectionSpec(
                "Photoelectric Interactions",
                32,
                ("Photoelectric Interactions (“ The Good Guy” ):",),
            ),
            SectionSpec("When Does the P.E. Occur?", 33, ("When does the P.E. Occur?",)),
            SectionSpec("K-Edge", 34, ("The “ K-Edge” - A Game of Shadows", "K Edge")),
            SectionSpec("Contrast and Dose", 35, ("Contrast and Dose",)),
            SectionSpec(
                "Pair Production and Photodisintegration",
                36,
                ("Low Yield Non-CIinical PhD Trivia", "Pair Production"),
            ),
            SectionSpec("Absorption", 37, ("Absorption",)),
            SectionSpec(
                "Linear Attenuation and Half Value Layer",
                38,
                ("Linear Attenuation and Half Value Layer",),
            ),
            SectionSpec("Rapid Review", 39, ("This vs That- Rapid Review",)),
        ),
    ),
    ChapterSpec(
        key="03",
        title="General X-Ray Concepts",
        start_page=40,
        end_page=53,
        intro_titles=("General X-Ray Concepts",),
        sections=(
            SectionSpec("Noise", 40, ("— (1) Noise", "(1) Noise")),
            SectionSpec("Gamesmanship", 41, ("Gamesmanship:",)),
            SectionSpec("Grid and Scatter", 42, ("Grid - Grids are used to reduce scatter.", "Scattering depends on:")),
            SectionSpec(
                "mA, kVp, and Signal-to-Noise Ratio",
                43,
                ("mA and kVp:", "Signal to Noise Ratio (SNR)"),
            ),
            SectionSpec("Gamesmanship Summary", 44, ("Gamesmanship Summary:",)),
            SectionSpec("Spatial Resolution", 45, ("— (2) Spatial Resolution", "(2) Spatial Resolution")),
            SectionSpec("Geometric Unsharpness", 46, ("Geometric Relationship - Influences Performance:",)),
            SectionSpec("Magnification", 47, ("Magnification:",)),
            SectionSpec(
                "MTF and DQE",
                48,
                ("Modulation Transfer Function (MTF)", "Modulation Transfer Function"),
            ),
            SectionSpec(
                "Digital Spatial Resolution Concepts",
                49,
                ("Spatial Resolution Concepts Related to Digital Imaging:",),
            ),
            SectionSpec(
                "Contrast Resolution",
                50,
                ("— (3) Contrast (“ Contrast Resolution” )", "(3) Contrast"),
            ),
            SectionSpec("Image Receptor Contrast - Digital", 51, ("Image Receptor Contrast - Digital",)),
            SectionSpec("Brightness", 52, ("— (4) Brightness", "(4) Brightness")),
        ),
    ),
    ChapterSpec(
        key="04",
        title="Image Detectors",
        start_page=54,
        end_page=63,
        intro_titles=("IMAGE DETECTORS",),
        sections=(
            SectionSpec("Digital vs Analog", 54, ("Digital vs Analog",)),
            SectionSpec("Dose", 55, ("Dose",)),
            SectionSpec("Spatial Resolution - Pixels", 55, ("Spatial Resolution — “ Pixels”", "Spatial Resolution - Pixels")),
            SectionSpec(
                "Rapid Review - Differences in Plain Film vs Digital",
                56,
                ("Rapid Review - Differences in Plain Film vs Digital",),
            ),
            SectionSpec(
                "Automatic Exposure Control (AEC)",
                56,
                ("Automatic Exposure Control - (AEC)",),
            ),
            SectionSpec(
                "Bit Depth and Digital Nuts and Bolts",
                57,
                ("Digital Nuts and Bolts - Types Trivia Etc..So on and So Forth.",),
            ),
            SectionSpec(
                "Computed Radiography (CR)",
                58,
                ("- CR - Computed Radiography or “ The Cassette Based System\"", "Storage Phosphors (CR)"),
            ),
            SectionSpec(
                "Digital Radiography (DR)",
                59,
                ("- DR - Digital Radiography or “ The Cassettelcss System\"", "Flat Panel Detectors (DR):"),
            ),
            SectionSpec(
                "Lateral Dispersion of Light",
                60,
                ("Lateral Dispersion of Light = Loss of Spatial Resolution",),
            ),
            SectionSpec("Direct DR Systems", 61, ("Direct:",)),
            SectionSpec("Fill Factor and DQE", 62, ("Fill Factor",)),
            SectionSpec("Spatial Resolution Tables", 63, ("Trivia Charts / Tables",)),
        ),
    ),
    ChapterSpec(
        key="05",
        title="Mammo",
        start_page=64,
        end_page=75,
        intro_titles=("MAMMO",),
        sections=(
            SectionSpec("Lower Energy", 64, ("Lower Energy",)),
            SectionSpec("Different Target", 65, ("Different Target",)),
            SectionSpec("K-Edge Filtration", 66, ("K-Edge Filtration", "K Edge Filtration")),
            SectionSpec(
                "Focal Spot, mA, and Exposure Time",
                67,
                ("Focal Spot / mA / Exposure Time",),
            ),
            SectionSpec("Heel Effect in Mammo", 67, ("Heel Effect - Refresher",)),
            SectionSpec("Beryllium Window", 68, ("The Beryllium Window:",)),
            SectionSpec("Compression", 68, ("Compression",)),
            SectionSpec("Grid", 69, ("Grid",)),
            SectionSpec("Magnification", 69, ("Magnification - Part 1",)),
            SectionSpec(
                "Magnification View and Air Gap",
                70,
                ("Magnification View - Part 2 “ The Air Gap”",),
            ),
            SectionSpec(
                "Comparing Mammo to General Radiography",
                71,
                ("Comparing and Contrasting Mammo to General Dx",),
            ),
            SectionSpec("Digital Mammography", 72, ("Digital Mammography",)),
            SectionSpec("PPV1, PPV2, and PPV3", 73, ("PPV1 PPV2 and PPV3",)),
            SectionSpec("MQSA", 74, ("MQSA",)),
        ),
    ),
    ChapterSpec(
        key="06",
        title="Fluoro",
        start_page=76,
        end_page=99,
        intro_titles=("FLUORO",),
        sections=(
            SectionSpec(
                "Fluoro vs Regular Diagnostic Radiography",
                76,
                ("So what is different?",),
            ),
            SectionSpec(
                "Last Image Hold vs Spot Image",
                76,
                ("This vs That - “ Last Image Hold” vs Spot Image",),
            ),
            SectionSpec(
                "Image Intensifier and Gains",
                77,
                ("Image Intensifier:",),
            ),
            SectionSpec(
                "Geometric vs Electronic Magnification",
                81,
                ("Geometric vs Electronic Magnification",),
            ),
            SectionSpec(
                "Dose Management and High Level Control",
                82,
                ("Dose & Compensation For Geometric Mag:",),
            ),
            SectionSpec("Fluoro Artifacts", 86, ("Artifacts:",)),
            SectionSpec(
                "Flat Panel Detector Systems and Vocabulary",
                88,
                ("Previously I mentioned that there were two different types of fluoro systems:",),
            ),
            SectionSpec(
                "FPD Artifacts and Spatial Resolution",
                91,
                ("Artifacts (FPD):",),
            ),
            SectionSpec(
                "Fluoro in IR and DSA",
                95,
                ("Fluoro in IR",),
            ),
            SectionSpec("Patient Dose and Positioning", 96, ("Patient Dose",)),
            SectionSpec(
                "Regulatory and Operator Doses",
                98,
                ("Regulatory Doses:",),
            ),
        ),
    ),
    ChapterSpec(
        key="07",
        title="CT",
        start_page=100,
        end_page=121,
        intro_titles=("CT",),
        sections=(
            SectionSpec(
                "CT Basics and Bow Tie Filters",
                100,
                ("Filtration Mechanisms:",),
            ),
            SectionSpec(
                "Scatter Reduction and Detector Types",
                101,
                ("Scatter Reduction:",),
            ),
            SectionSpec("CT Vocabulary and Sinogram", 102, ("Vocabulary:",)),
            SectionSpec("Pitch", 103, ("Pitch",)),
            SectionSpec("Hounsfield Units", 104, ("The Hounsfield Unit:",)),
            SectionSpec("Window Width and Level", 105, ("Window Width and Level:",)),
            SectionSpec(
                "How the Machine Makes a Picture",
                106,
                ("How the Machine Makes A Picture",),
            ),
            SectionSpec(
                "Axial vs Helical Acquisition",
                107,
                ("Acquiring the Raw Data",),
            ),
            SectionSpec(
                "Reconstruction Methods",
                108,
                ("Raw Date", "Raw Data"),
            ),
            SectionSpec(
                "Special Topics: Cardiac Imaging, CT Fluoro, and Dual Energy",
                109,
                ("Special Topic Cardiac Imaging",),
            ),
            SectionSpec("Signal to Noise", 110, ("Signal to Noise",)),
            SectionSpec("Contrast Resolution", 111, ("Contrast Resolution",)),
            SectionSpec("Spatial Resolution", 112, ("Spatial Resolution",)),
            SectionSpec(
                "CT Dose Measures",
                114,
                ("Radiation Dose Measures: CT Specific",),
            ),
            SectionSpec("DLP and Effective Dose", 115, ("“ DLP” - Dose Length Product-", "DLP")),
            SectionSpec("Dose Related Trivia", 116, ("Dose Related Trivia:",)),
            SectionSpec(
                "Beam Hardening Artifacts",
                117,
                ("CT Artifacts:", "Beam Hardening-"),
            ),
            SectionSpec("Partial Volume", 118, ("Partial Volume:",)),
            SectionSpec(
                "Under Sampling and Metal Artifact",
                119,
                ("Under Sampling:",),
            ),
            SectionSpec(
                "Ring and Helical Artifacts",
                120,
                ("Ring Artifact:",),
            ),
        ),
    ),
    ChapterSpec(
        key="08",
        title="Ultrasound",
        start_page=122,
        end_page=155,
        intro_titles=("Ultrasound",),
        sections=(
            SectionSpec(
                "Relative Intensity and Decibels",
                124,
                ("Relative Intensity- The dB.",),
            ),
            SectionSpec(
                "Interactions of Ultrasound with Matter",
                125,
                ("Interactions of Ultrasound with Matter",),
            ),
            SectionSpec(
                "Transducers and Damping",
                130,
                ("Ultrasound Transducers and Related Trivia",),
            ),
            SectionSpec("Transducer Arrays", 132, ("Transducer Arrays",)),
            SectionSpec(
                "Beam Properties and Focal Zone",
                133,
                ("Beam Properties",),
            ),
            SectionSpec(
                "Spatial Resolution",
                136,
                ("Spatial Resolution -", "Spatial Resolution"),
            ),
            SectionSpec("Artifacts and Assumptions", 140, ("Artifacts:",)),
            SectionSpec(
                "Multiple Echo Artifacts",
                141,
                ("Artifacts Associated with Multiple Echoes:",),
            ),
            SectionSpec(
                "Velocity Error Artifacts",
                143,
                ("Artifacts Related to Velocity Errors:",),
            ),
            SectionSpec(
                "Attenuation Error Artifacts and Modes",
                144,
                ("Artifacts Related to Attenuation Errors:",),
            ),
            SectionSpec("Doppler Basics", 145, ("Doppler",)),
            SectionSpec("Doppler Modes", 147, ("Pulsed Wave (Spectral) Doppler-",)),
            SectionSpec("Doppler Artifacts", 148, ("Doppler Artifacts:",)),
            SectionSpec("Image Optimization", 149, ("Image Optimization",)),
            SectionSpec("Harmonics", 150, ("Harmonics",)),
            SectionSpec("Compound Imaging", 151, ("Compound Imaging -",)),
            SectionSpec(
                "Safety and Obstetrics",
                153,
                ("Safety",),
            ),
        ),
    ),
    ChapterSpec(
        key="09",
        title="Nukes",
        start_page=156,
        end_page=195,
        intro_titles=("Nukes",),
        sections=(
            SectionSpec("Alpha Decay and Stability", 156, ("Alpha Decay",)),
            SectionSpec("Beta Minus Decay", 157, ("Beta Minus Decay:",)),
            SectionSpec(
                "Beta Positive Decay and Electron Capture",
                158,
                ("“ The Rich Guy” - Beta Positive Decay",),
            ),
            SectionSpec(
                "Isomeric Transition and Internal Conversion",
                160,
                ("Fell Me More About this “ Isometric Transition”",),
            ),
            SectionSpec("Rapid Review", 162, ("Summary / Rapid Review",)),
            SectionSpec("Production", 163, ("Production",)),
            SectionSpec(
                "Radioactive Decay and Half-Life",
                164,
                ("Radioactive Decay",),
            ),
            SectionSpec(
                "Gamma Camera Basics",
                165,
                ("How the Gamma Camera Works:",),
            ),
            SectionSpec("Collimators", 166, ("Collimator:",)),
            SectionSpec(
                "Scintillation Crystal, PMTs, and Downscatter",
                168,
                ("Scintillation Crystal-",),
            ),
            SectionSpec(
                "Star Artifact and Gamma Camera QC",
                170,
                ("Star Artifact:",),
            ),
            SectionSpec(
                "Safety Instruments and Counters",
                172,
                ("Safety:",),
            ),
            SectionSpec(
                "Dosimeters and Dose Calibrator QA",
                174,
                ("Device",),
            ),
            SectionSpec("Spill Management", 176, ("Minor Spill = You Clean It Up",)),
            SectionSpec(
                "Public Regulations and Reportable Events",
                177,
                ("Regulations Affecting the General Public",),
            ),
            SectionSpec(
                "Receiving and Shipping Radioactive Material",
                179,
                ("Receiving, Storing, and Disposing of Radioactive Material",),
            ),
            SectionSpec(
                "Tc-99m Generation and Purity",
                180,
                ("Tc-99",),
            ),
            SectionSpec(
                "Critical Organ and Target Organ",
                183,
                ("Critical Organ",),
            ),
            SectionSpec(
                "SPECT and PET Overview",
                184,
                ("SPECT",),
            ),
            SectionSpec(
                "Coincidence Detection and PET Limitations",
                186,
                ("Coincidence Detection",),
            ),
            SectionSpec(
                "PET Event Types and 2D vs 3D",
                187,
                ("Scatter",),
            ),
            SectionSpec(
                "Attenuation Correction and SUV",
                189,
                ("Attenuation Correction:",),
            ),
            SectionSpec(
                "Truncation Artifact and Pre-FDG Preparation",
                191,
                ("Truncation Artifact:",),
            ),
            SectionSpec("PET QA and Summary Chart", 193, ("PET QA",)),
        ),
    ),
    ChapterSpec(
        key="10",
        title="MRI",
        start_page=196,
        end_page=249,
        intro_titles=("MRI",),
        sections=(
            SectionSpec("How MRI Works", 196, ("How does MRI work?",)),
            SectionSpec(
                "Coordinate System and RF Pulse",
                197,
                ("What is this coordinate system", "What is this“ coordinate system” ?", "What is this RF Pulse"),
            ),
            SectionSpec("Precession Frequency", 198, ("Precession Frequency",)),
            SectionSpec(
                "RF Pulse Effects and Signal Measurement",
                199,
                ("What exactly does the RFpulse do?", "What exactly does the RF pulse do?"),
            ),
            SectionSpec("T1 Relaxation", 200, ("What is this Tl?", "T1 - Recovery of Longitudinal Magnetization")),
            SectionSpec(
                "T2 and T2* Relaxation",
                201,
                ("What is this T2?", "T2 - Decay of Transverse Magnetization"),
            ),
            SectionSpec("Echo and TE", 204, ("What is this “ Echo” you speak of?",)),
            SectionSpec(
                "T1, T2, and Proton Density",
                205,
                ("Tl and T2 - Clarified", "T1 and T2 - Clarified"),
            ),
            SectionSpec(
                "k-Space and Image Matrix",
                207,
                ("What is this k-Space and Image Matrix ?", "k-Space and Image Matrix"),
            ),
            SectionSpec(
                "Spatial Encoding",
                208,
                ("Localization of signal requires three steps:", "Spatial Encoding - How do you localize the signal from within the body?"),
            ),
            SectionSpec("Slice Thickness", 211, ("Slice Thickness",)),
            SectionSpec("Table Time", 212, ("(1) Table Time", "Table Time")),
            SectionSpec("Spatial Resolution", 214, ("Spatial Resolution",)),
            SectionSpec(
                "Signal to Noise and Bandwidth Tradeoffs",
                215,
                ("Signal to Noise",),
            ),
            SectionSpec("Modification Summary", 217, ("Modification",)),
            SectionSpec(
                "MRI Sequences and Fast Spin Echo",
                218,
                ("MRI Sequences",),
            ),
            SectionSpec("Inversion Recovery", 220, ("Inversion Recovery", "Inversion Recovery Sequence")),
            SectionSpec(
                "Gradient Echo, EPI, and Diffusion",
                221,
                ("GRF> Sequences", "Gradient Echo Sequences", "Echo-Plannar Imaging (EPI ) “ The Noisy One”"),
            ),
            SectionSpec(
                "Additional Sequences, Fat Saturation, and In/Out of Phase Imaging",
                224,
                ("Additional Sequences - Mentioned For Completeness:",),
            ),
            SectionSpec(
                "Chemical Shift Artifact and MR Contrast",
                228,
                ("Type 1Chemical Shift Artifact", "Chemical Shift Artifact", "MR Contrast (Gd+)"),
            ),
            SectionSpec("MRI Artifacts", 230, ("MRI Artifacts",)),
            SectionSpec(
                "Magnetic Field and Gradient Artifacts",
                235,
                ("Zipper Artifact",),
            ),
            SectionSpec("Special Topic Cardiac MRI", 240, ("Special Topic - Cardiac MRI",)),
            SectionSpec("Special Topic Breast MRI", 241, ("Special Topic - Breast MRI",)),
            SectionSpec(
                "MRI Safety Basics and Emergency Shutdown",
                242,
                ("I want you to think about MRI safety in two basic categories:", "Main Magnet -"),
            ),
            SectionSpec(
                "Translational Force, Acoustic Noise, and SAR",
                244,
                ("Translational Force",),
            ),
            SectionSpec(
                "Heating, QC, and MRI Zones",
                246,
                ("Misc Heating / Burning Issues:", "MRI“Zones”:", "MRI Zones"),
            ),
        ),
    ),
    ChapterSpec(
        key="11",
        title="Radiation Biology",
        start_page=250,
        end_page=268,
        intro_titles=("Radiation Biology",),
        sections=(
            SectionSpec("Kerma", 251, ("Kerma",)),
            SectionSpec("KAP", 252, ("KAP = Dose x Cross Sectional Area", "KAP")),
            SectionSpec(
                "Deterministic vs Stochastic Effects",
                253,
                ("This vs That - Risk Models; Deterministic vs Stochastic Effects",),
            ),
            SectionSpec(
                "Interaction of Radiation with Tissue",
                254,
                ("Interaction of Radiation with Tissue:",),
            ),
            SectionSpec(
                "LET and RBE",
                255,
                ("Charged Particle Tracks:",),
            ),
            SectionSpec(
                "Direct vs Indirect Radiation",
                256,
                ("This vs That: Direct vs Indirect Radiation",),
            ),
            SectionSpec("Effect on the Cell", 258, ("Effect on the Celt:", "Effect on the Cell:")),
            SectionSpec(
                "Repair and Blood Effects",
                259,
                ("Repair Shoulder (Quasithreshold)", "Key Points:", "Effect of Ionizing Radiation of Blood:"),
            ),
            SectionSpec("Acute Radiation Syndrome", 260, ("Acute Radiation Syndrome (ARS):",)),
            SectionSpec(
                "Triaging ARS and LD50/30",
                261,
                ("Triaging Patients with Possible ARS:",),
            ),
            SectionSpec(
                "Radiation Effects on a Fetus and Hereditary Risk",
                262,
                ("Radiation Effect on a Fetus:",),
            ),
            SectionSpec("Skin Problems and Cataracts", 263, ("Skin Problem",)),
            SectionSpec("Sterility and Infertility", 264, ("Sterility / Infertility",)),
            SectionSpec("Exposure Limits", 265, ("Exposure Limits",)),
            SectionSpec(
                "High Yield Radiation Biology/Safety Blitz",
                266,
                ("High Yield Radiation Biology/Safety Blitz:",),
            ),
        ),
    ),
    ChapterSpec(
        key="12",
        title="OA Officer",
        start_page=270,
        end_page=282,
        intro_titles=("Duties of the QA Officer",),
        sections=(
            SectionSpec("QC, QA, and QI", 270, ("This vs That: QC, QA, and QI",)),
            SectionSpec(
                "Latent vs Active Errors",
                272,
                ("Stirring Up Trouble - This vs That: - Latent vs Active Errors",),
            ),
            SectionSpec(
                "Blunt End vs Sharp End",
                273,
                ("Stirring Up Trouble - This vs That: Blunt End vs Sharp End:",),
            ),
            SectionSpec(
                "Hawthorne and Weber Effects",
                273,
                ("Making People Miserable - The Hawthorne Effect:",),
            ),
            SectionSpec(
                "Safety Champion and Benchmarking",
                274,
                ("Stirring Up Trouble - The Safety Champion",),
            ),
            SectionSpec(
                "Value Equation and KPI",
                275,
                ("Making People Miserable - The Value Equation:",),
            ),
            SectionSpec(
                "PDSA Cycle",
                276,
                ("Making People Miserable - PDSA Cycle - “ Improvement Cycle”",),
            ),
            SectionSpec(
                "Lean and Push vs Pull",
                277,
                ("Making People Miserable - Lean",),
            ),
            SectionSpec(
                "Standard Work, Waste, and Just-in-Time",
                278,
                ("“ Standard Work”", "Standard Work"),
            ),
            SectionSpec(
                "DMAIC and Six Sigma",
                279,
                ("Making People Miserable - DMAIC Methodology",),
            ),
            SectionSpec(
                "FMEA and Root Cause Analysis",
                280,
                ("Stirring Up Trouble - This vs That: FMEA vs PCA:",),
            ),
        ),
    ),
    ChapterSpec(
        key="13",
        title="The Trainee Caused a Complication",
        start_page=283,
        end_page=293,
        intro_titles=("The Trainee Caused a Complication",),
        sections=(
            SectionSpec("Medical Error", 283, ("What is this “ Medical Error",)),
            SectionSpec("Fundamental Errors", 284, ("Fundamental Errors:",)),
            SectionSpec("Radiology Errors", 285, ("Radiology Error- This vs That",)),
            SectionSpec(
                "Never Events, Sentinel Events, and Adverse Events",
                286,
                ("“ Never Event”",),
            ),
            SectionSpec(
                "Second Victim and Mistake vs Slip",
                287,
                ("Second Victim",),
            ),
            SectionSpec(
                "Skill-Rule-Knowledge Classification",
                288,
                ("Skill-Rule-Knowledge Classification Regarding Human Error",),
            ),
            SectionSpec(
                "Disclosure and Academic Practice",
                289,
                ("Must Read For Anyone Considering a Career in Academics",),
            ),
            SectionSpec(
                "Malpractice and Getting Sued",
                290,
                ("“ Getting Sued”", "Getting Sued"),
            ),
            SectionSpec(
                "Prevention and Human Factors Engineering",
                291,
                ("Prevention",),
            ),
            SectionSpec(
                "Steep Authority Gradient and SBAR",
                292,
                ("Steep Authority Gradient",),
            ),
            SectionSpec("Forcing Function", 293, ("Forcing Function",)),
        ),
    ),
    ChapterSpec(
        key="14",
        title="Just Culture",
        start_page=294,
        end_page=296,
        intro_titles=("Just Culture", "Just Culture"),
        sections=(
            SectionSpec("Just Culture Basics", 294, ("Just Culture",)),
            SectionSpec(
                "Human Error, Risk Behavior, and Reckless Behavior",
                295,
                ("Human Error (Slip) - Console",),
            ),
            SectionSpec(
                "Rapid Review: Mistake vs Slip/Lapse",
                296,
                ("Rapid Review: Mistake vs Slip/Lapse",),
            ),
        ),
    ),
    ChapterSpec(
        key="15",
        title="Communication Standards",
        start_page=297,
        end_page=299,
        intro_titles=("Communication Standards",),
        sections=(
            SectionSpec(
                "Communication Practice Standards",
                297,
                ("Communication Practice Standards:",),
            ),
            SectionSpec(
                "Documentation and Confirming Receipt",
                298,
                ("But you can just send them an email right???",),
            ),
            SectionSpec(
                "Informal Reads and Who to Notify",
                299,
                ("Ok do you have any other beefs with the paper? Yup.",),
            ),
        ),
    ),
    ChapterSpec(
        key="16",
        title="Charts & Graphs",
        start_page=300,
        end_page=304,
        intro_titles=("Charts & Graphs",),
        sections=(
            SectionSpec("Flow Charts", 300, ("Flow Charts",)),
            SectionSpec("Fishbone Diagram", 301, ("Fishbone Diagram (Cause and Effect)",)),
            SectionSpec("Pareto Charts", 302, ("Pareto Charts",)),
            SectionSpec("Shewhart Charts", 303, ("Shewhart Charts (Control Chart)",)),
            SectionSpec(
                "Receiver Operator Curves (ROC)",
                304,
                ("Receiver Operator Curve - ROC",),
            ),
        ),
    ),
    ChapterSpec(
        key="17",
        title="Patient Safety Goals",
        start_page=305,
        end_page=310,
        intro_titles=("Patient Safety Goals",),
        sections=(
            SectionSpec("Blood Transfusion", 305, ("Blood Transfusion-",)),
            SectionSpec("Medication Labeling", 306, ("Medications Labeling-",)),
            SectionSpec(
                "Medication Reconciliation and Central Venous Access",
                307,
                ("Medication Reconciling",),
            ),
            SectionSpec("Wrong Site Procedures", 308, ("Wrong Site",)),
            SectionSpec("Informed Consent", 309, ("Informed Consent:",)),
            SectionSpec(
                "Special Situations and Universal Protocol",
                310,
                ("Special Situations:",),
            ),
        ),
    ),
    ChapterSpec(
        key="18",
        title="Random Stuff Not Yet Covered",
        start_page=311,
        end_page=321,
        intro_titles=("Random Stuff Not Yet Covered",),
        sections=(
            SectionSpec("Validity vs Reliability", 311, ("Validity vs Reliability This vs That",)),
            SectionSpec("Image Gently", 312, ("Image Gently",)),
            SectionSpec("BEIR 7 Report", 313, ("Biologic Effects of Ionizing Radiation (BEIR) Committee",)),
            SectionSpec(
                "Appropriateness and Choosing Wisely",
                314,
                ("Appropriateness Trivia- Related to Unnecessary Exam / Dose Reduction",),
            ),
            SectionSpec(
                "Credentialing and Payment",
                315,
                ("Getting Paid",),
            ),
            SectionSpec(
                "Billing and Government Programs",
                316,
                ("Sustainable Growth Rate System (SGR)-",),
            ),
            SectionSpec(
                "CT Contrast Reactions and Premedication",
                317,
                ("CT Contrast - Reactions and Management:",),
            ),
            SectionSpec("Contrast Reaction Management", 318, ("Contrast Reaction Management",)),
            SectionSpec(
                "Contrast-Induced Nephropathy",
                319,
                ("Contrast Induced Nephropathy (CIN):",),
            ),
            SectionSpec(
                "Metformin, Gadolinium, and CPR",
                320,
                ("What is the deal with metformin?",),
            ),
        ),
    ),
    ChapterSpec(
        key="19",
        title="Biostatistics",
        start_page=323,
        end_page=331,
        sections=(
            SectionSpec("Normal Distribution", 323, ("The Normal Distribution:",)),
            SectionSpec(
                "Precision, Accuracy, and Statistical Significance",
                324,
                ("Precision and Accuracy:",),
            ),
            SectionSpec("Type I and Type II Errors", 325, ("Errors",)),
            SectionSpec("Statistical Epidemiology", 326, ("Statistical Epidemiology",)),
            SectionSpec("Sensitivity and Specificity", 327, ("Sensitivity =", "Disease")),
            SectionSpec(
                "Accuracy, Predictive Value, Validity, and Power",
                328,
                ("Accuracy - 1", "Accuracy"),
            ),
            SectionSpec("Risk and Number Needed to Treat", 329, ("Risk:",)),
            SectionSpec("Odds Ratio", 330, ("Odds Ratio:",)),
        ),
    ),
    ChapterSpec(
        key="20",
        title="Rapid Review",
        start_page=333,
        end_page=382,
        sections=(
            SectionSpec("X-Ray Production / Generation", 333, ("X-Ray Production / Generation",)),
            SectionSpec("X-Ray Interaction With Matter", 335, ("X-Ray Interaction with Matter",)),
            SectionSpec("General X-Ray Concepts", 337, ("General X-Ray Concepts",)),
            SectionSpec("Imaging Detectors", 339, ("Imaging Detectors",)),
            SectionSpec("Mammo", 341, ("Mammo",)),
            SectionSpec("Fluoro", 344, ("Fluoro",)),
            SectionSpec("CT Basics", 347, ("Pitch",)),
            SectionSpec("CT Spatial Resolution and Artifacts", 350, ("Spatial Resolution (CT)", "Factors That Affect Spatial Resolution")),
            SectionSpec("Ultrasound Basics", 352, ("Ultrasound",)),
            SectionSpec("Ultrasound Safety", 355, ("Safety:",)),
            SectionSpec("Nukes Decay and Gamma Camera", 356, ("Nukes",)),
            SectionSpec("Nuclear Regulations and Purity", 359, ("Recordable vs Reportable Events",)),
            SectionSpec("Critical Organs and PET", 360, ("Critical Organs:", "Target Organ")),
            SectionSpec("MRI Basics", 362, ("MRI",)),
            SectionSpec("MRI Special Topics and Safety", 365, ("Additional Sequences", "Cardiac MRI", "Breast MRI", "Safety")),
            SectionSpec("Radiation Biology", 367, ("Radiation Biology",)),
            SectionSpec("Pregnancy and Lactation", 369, ("Pregnancy and Lactation High Yield Summary",)),
            SectionSpec("Non-Interpretive Skills", 371, ("NIS",)),
            SectionSpec(
                "Contrast Premedication and Reaction Management",
                375,
                ("Routine Premedication",),
            ),
            SectionSpec(
                "Essential Numbers and Formulas",
                377,
                ("Essential Numbers and Formulas",),
            ),
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Textbook Copier text files and manifest for Radiologic Physics - War Machine."
    )
    parser.add_argument(
        "--extractor",
        choices=("auto", "pdfplumber", "fitz", "ghostscript"),
        default="fitz",
        help="Preferred PDF text extractor backend.",
    )
    return parser.parse_args()


def repair_mojibake(text: str) -> str:
    return MULTISPACE_RE.sub(" ", text.replace("\u00a0", " ").strip())


def safe_filename(title: str) -> str:
    ascii_title = (
        unicodedata.normalize("NFKD", title)
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u2212", "-")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    ascii_title = INVALID_FILENAME_CHARS_RE.sub("", ascii_title)
    ascii_title = MULTISPACE_RE.sub(" ", ascii_title).strip().strip(".")
    return ascii_title or "section"


def normalize_for_match(text: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", repair_mojibake(text))
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2212", "-")
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    return MATCH_RE.sub("", normalized)


def heading_match(combined: str, target: str) -> bool:
    if combined == target or combined.startswith(target):
        return True
    extra = len(combined) - len(target)
    return 0 < extra <= 5 and combined.endswith(target)


def find_heading_line(page_lines: list[str], title: str, *, start_line: int = 1) -> int | None:
    target = normalize_for_match(title)
    normalized_lines = [normalize_for_match(line) for line in page_lines]

    for start_index in range(max(0, start_line - 1), len(normalized_lines)):
        line = normalized_lines[start_index]
        if not line:
            continue

        combined = ""
        for end_index in range(start_index, min(len(normalized_lines), start_index + 6)):
            piece = normalized_lines[end_index]
            if not piece:
                continue
            combined += piece

            if heading_match(combined, target):
                return start_index + 1
            if not target.startswith(combined) and not combined.startswith(target):
                break

    return None


def find_heading_position(
    page_lines: list[list[str]],
    *,
    titles: tuple[str, ...],
    start_page: int,
    start_line: int,
    end_page: int,
) -> tuple[int, int]:
    for page_number in range(start_page, end_page + 1):
        page_start_line = start_line if page_number == start_page else 1
        matches = [
            find_heading_line(page_lines[page_number - 1], title, start_line=page_start_line)
            for title in titles
        ]
        valid_matches = [line_number for line_number in matches if line_number is not None]
        if valid_matches:
            return page_number, min(valid_matches)

    joined = " / ".join(titles)
    raise ValueError(
        f"Could not find heading {joined!r} between pages {start_page} and {end_page}"
    )


def advance_search_position(page_lines: list[list[str]], page: int, line: int) -> tuple[int, int]:
    if line < len(page_lines[page - 1]):
        return page, line + 1
    return page + 1, 1


def build_text(
    page_lines: list[list[str]],
    *,
    start_page: int,
    start_line: int,
    end_page: int,
    end_line_exclusive: int,
) -> str:
    lines: list[str] = []
    for page_number in range(start_page, end_page + 1):
        page = [repair_mojibake(line) for line in page_lines[page_number - 1]]
        from_index = start_line - 1 if page_number == start_page else 0
        to_index = end_line_exclusive - 1 if page_number == end_page else len(page)
        if to_index > from_index:
            lines.extend(page[from_index:to_index])
    return "\n".join(lines).strip() + "\n"


def text_starts_with_heading(text: str, title: str) -> bool:
    target = normalize_for_match(title)
    lines = [line for line in text.splitlines() if line.strip()]
    combined = ""

    for line in lines[:6]:
        combined += normalize_for_match(line)
        if heading_match(combined, target):
            return True
        if not target.startswith(combined) and not combined.startswith(target):
            return False

    return False


def text_starts_with_any_heading(text: str, titles: tuple[str, ...]) -> bool:
    return any(text_starts_with_heading(text, title) for title in titles)


def clean_section_start(text: str, titles: tuple[str, ...]) -> str:
    lines = text.splitlines()
    if not lines:
        return text

    first_line = lines[0]
    normalized_first = normalize_for_match(first_line)
    for title in titles:
        normalized_title = normalize_for_match(title)
        extra = len(normalized_first) - len(normalized_title)
        if normalized_first == normalized_title:
            lines[0] = title
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
        if 0 < extra <= 5 and normalized_first.endswith(normalized_title):
            lines[0] = title
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return text


def intro_is_substantive(text: str, intro_titles: tuple[str, ...]) -> bool:
    normalized_titles = {normalize_for_match(title) for title in intro_titles}
    filtered_lines: list[str] = []
    for line in text.splitlines():
        normalized = normalize_for_match(line)
        if not normalized:
            continue
        if normalized in normalized_titles:
            continue
        if normalized.startswith("prometheuslionhart"):
            continue
        if normalized.startswith("chapter"):
            continue
        filtered_lines.append(line.strip())
    return len(" ".join(filtered_lines)) >= 60


def build_manifest(chapters: list[tuple[ChapterSpec, list[ResolvedSection], str | None]]) -> dict[str, object]:
    manifest: dict[str, object] = {}
    for chapter, resolved_sections, intro_file in chapters:
        chapter_entry: dict[str, object] = {"title": chapter.title, "sections": {}}
        if intro_file is not None:
            chapter_entry["introTitle"] = "Introduction"
            chapter_entry["introFile"] = intro_file

        sections_map = chapter_entry["sections"]
        assert isinstance(sections_map, dict)
        for index, section in enumerate(resolved_sections, start=1):
            section_key = f"{chapter.key}.{index:02d}"
            sections_map[section_key] = {
                "title": section.title,
                "file": section.file_name,
            }
        manifest[f"Chapter{chapter.key}"] = chapter_entry
    return manifest


def resolve_chapter(
    chapter: ChapterSpec,
    page_lines: list[list[str]],
) -> tuple[list[ResolvedSection], str | None, str | None]:
    resolved_sections: list[ResolvedSection] = []
    cursor_page = chapter.start_page
    cursor_line = 1

    for index, section in enumerate(chapter.sections, start=1):
        desired_start_page = max(cursor_page, section.page_hint)
        desired_start_line = cursor_line if desired_start_page == cursor_page else 1

        try:
            heading_page, heading_line = find_heading_position(
                page_lines,
                titles=section.candidates,
                start_page=desired_start_page,
                start_line=desired_start_line,
                end_page=chapter.end_page,
            )
        except ValueError:
            heading_page, heading_line = find_heading_position(
                page_lines,
                titles=section.candidates,
                start_page=cursor_page,
                start_line=cursor_line,
                end_page=chapter.end_page,
            )

        file_name = f"TXT/{chapter.key}.{index:02d} - {safe_filename(section.title)}.txt"
        resolved_sections.append(
            ResolvedSection(
                title=section.title,
                file_name=file_name,
                heading_page=heading_page,
                heading_line=heading_line,
                end_page=chapter.end_page,
                end_line_exclusive=len(page_lines[chapter.end_page - 1]) + 1,
                candidates=section.candidates,
            )
        )
        cursor_page, cursor_line = advance_search_position(page_lines, heading_page, heading_line)

    for index in range(len(resolved_sections) - 1):
        current = resolved_sections[index]
        nxt = resolved_sections[index + 1]
        resolved_sections[index] = ResolvedSection(
            title=current.title,
            file_name=current.file_name,
            heading_page=current.heading_page,
            heading_line=current.heading_line,
            end_page=nxt.heading_page,
            end_line_exclusive=nxt.heading_line,
            candidates=current.candidates,
        )

    intro_text: str | None = None
    intro_file: str | None = None
    if chapter.intro_titles and resolved_sections:
        first = resolved_sections[0]
        try:
            intro_start_page, intro_start_line = find_heading_position(
                page_lines,
                titles=chapter.intro_titles,
                start_page=chapter.start_page,
                start_line=1,
                end_page=first.heading_page,
            )
        except ValueError:
            intro_start_page, intro_start_line = chapter.start_page, 1

        candidate_intro = build_text(
            page_lines,
            start_page=intro_start_page,
            start_line=intro_start_line,
            end_page=first.heading_page,
            end_line_exclusive=first.heading_line,
        )
        if intro_is_substantive(candidate_intro, chapter.intro_titles):
            intro_file = f"TXT/{chapter.key}.00 - Introduction.txt"
            intro_text = candidate_intro

    return resolved_sections, intro_file, intro_text


def main() -> int:
    args = parse_args()

    if not PDF_PATH.exists():
        raise SystemExit(f"Source PDF not found: {PDF_PATH}")

    extraction = extract_pdf(
        PDF_PATH,
        label="war-machine",
        extractor=args.extractor,
        strip_page_furniture=True,
    )
    page_lines = extraction.page_lines

    TXT_DIR.mkdir(parents=True, exist_ok=True)

    chapter_results: list[tuple[ChapterSpec, list[ResolvedSection], str | None]] = []
    intro_text_by_file: dict[str, str] = {}
    total_sections = 0

    for chapter in CHAPTER_SPECS:
        resolved_sections, intro_file, intro_text = resolve_chapter(chapter, page_lines)
        chapter_results.append((chapter, resolved_sections, intro_file))
        total_sections += len(resolved_sections)
        if intro_file is not None and intro_text is not None:
            intro_text_by_file[intro_file] = intro_text

        for section in resolved_sections:
            text = build_text(
                page_lines,
                start_page=section.heading_page,
                start_line=section.heading_line,
                end_page=section.end_page,
                end_line_exclusive=section.end_line_exclusive,
            )
            text = clean_section_start(text, section.candidates)
            if not text_starts_with_any_heading(text, section.candidates):
                raise ValueError(
                    f"{chapter.key} section {section.title!r} does not start with its heading"
                )
            (BOOK_DIR / section.file_name).write_text(text, encoding="utf-8")

    for intro_file, intro_text in intro_text_by_file.items():
        (BOOK_DIR / intro_file).write_text(intro_text, encoding="utf-8")

    manifest = build_manifest(chapter_results)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    intro_count = len(intro_text_by_file)
    print(
        f"Generated {len(CHAPTER_SPECS)} chapters, {total_sections} sections, and {intro_count} intro files "
        f"in {TXT_DIR.relative_to(REPO_ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
