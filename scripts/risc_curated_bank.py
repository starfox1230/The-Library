from __future__ import annotations


def item(stem, options, answer, explanation):
    return {
        "stem": stem,
        "options": options,
        "answer": answer,
        "explanation": explanation,
    }


CHAPTER_QUESTIONS = {
    1: [
        item(
            "Approximately how much effective dose does the average person in the United States receive each year from all radiation sources, including background radiation?",
            ["62 mrem (0.62 mSv)", "100 mrem (1 mSv)", "620 mrem (6.2 mSv)", "5 rem (50 mSv)"],
            "C",
            "The 2026 RISC document gives an annual average of about 620 mrem (6.2 mSv) from all sources. "
            "The 100 mrem value is the annual public dose limit from licensed operations, not average total exposure. "
            "Five rem is the annual whole-body occupational limit for an adult radiation worker.",
        ),
        item(
            "A nuclear medicine service can obtain a diagnostic study using several technically adequate protocols. Which approach best applies the ALARA principle?",
            [
                "Choose the protocol with the lowest exposure that still provides the required diagnostic information",
                "Choose the protocol with the shortest acquisition time regardless of image quality",
                "Keep exposure below the occupational limit, even if a lower exposure is readily achievable",
                "Avoid all radiation use unless the examination is therapeutic",
            ],
            "A",
            "ALARA means keeping exposure as low as reasonably achievable while still accomplishing the clinical purpose. "
            "It is not satisfied merely by remaining below a regulatory limit, and it does not require sacrificing the diagnostic objective. "
            "Acquisition time is only one consideration; time, distance, shielding, and protocol design must be considered together.",
        ),
        item(
            "Who is responsible for the required annual review of a facility's ALARA program?",
            ["Authorized user", "Radiation safety officer", "Radiation safety committee chair", "NRC inspector"],
            "B",
            "The radiation safety officer (RSO) performs the annual review of the ALARA program. "
            "Authorized users follow the program in clinical practice, and the radiation safety committee provides broader oversight, "
            "but the document specifically assigns the annual ALARA review to the RSO.",
        ),
        item(
            "A hospital employee who routinely transports patients but does not work in an imaging department is exposed to radiation from licensed operations. Which annual limit applies to that employee as a member of the public?",
            ["50 mrem (0.5 mSv)", "100 mrem (1 mSv)", "500 mrem (5 mSv)", "5 rem (50 mSv)"],
            "B",
            "Hospital staff outside radiology or imaging are treated as members of the public for this limit. "
            "Their dose from licensed operations must not exceed 100 mrem (1 mSv) per year. "
            "The 5-rem value is the adult occupational whole-body limit, and 500 mrem is the embryo/fetus limit for a declared pregnant worker.",
        ),
        item(
            "Which set contains the three principal methods for reducing occupational radiation exposure?",
            [
                "Collimation, filtration, and magnification",
                "Time, distance, and shielding",
                "Monitoring, reporting, and licensing",
                "Containment, ventilation, and decontamination",
            ],
            "B",
            "Time, distance, and shielding are the core exposure-reduction methods. "
            "The other choices contain useful practices in selected settings, but they are not the standard three-part radiation-protection framework.",
        ),
        item(
            "When is individual personnel dosimetry required on the basis of expected occupational exposure?",
            [
                "Whenever any exposure is possible",
                "When exposure is expected to exceed 10% of the applicable annual occupational limit",
                "Only after a worker exceeds an annual occupational limit",
                "When exposure is expected to exceed the annual public limit",
            ],
            "B",
            "Individual monitoring is required when a worker is likely to receive more than 10% of the applicable annual occupational dose limit. "
            "The decision is prospective; a facility should not wait for an overexposure. "
            "The public limit is not the threshold used to decide whether an occupational worker needs a dosimeter.",
        ),
        item(
            "Which oversight schedule correctly pairs the reviewer with personnel dosimetry records?",
            [
                "RSO monthly; radiation safety committee annually",
                "RSO quarterly; radiation safety committee every 3 months",
                "RSO annually; radiation safety committee quarterly",
                "RSO every 3 months; radiation safety committee every 12 months",
            ],
            "B",
            "The RSO should review personnel dosimetry records quarterly, and the radiation safety committee reviews them every 3 months. "
            "These intervals are equivalent in duration but involve different oversight roles. "
            "They should not be confused with the annual ALARA review or the at-least-annual audit.",
        ),
        item(
            "A department is selecting a person to perform its required radiation-protection audit. Which candidate is most appropriate?",
            [
                "The supervisor who directly manages the audited work",
                "A trained individual without direct responsibility for the audited department",
                "Any employee who has worn a dosimeter for at least 1 year",
                "Only an NRC employee",
            ],
            "B",
            "The audit must be performed by trained personnel who do not have direct responsibility for the department or facility being audited. "
            "This independence reduces conflicts of interest. The audit is required at least every 12 months, and its findings and follow-up actions "
            "must be documented and reviewed by facility administration.",
        ),
        item(
            "Which activity is most characteristic of a restricted radiation area?",
            [
                "Interpreting studies in a reading room",
                "Registering patients at reception",
                "Preparing and storing radiopharmaceuticals",
                "Scheduling examinations in an office",
            ],
            "C",
            "Radiopharmaceutical preparation, administration, storage, and imaging commonly occur in restricted areas because radioactive material is present or radiation levels require control. "
            "Reception, offices, waiting areas, and reading rooms are typical unrestricted areas.",
        ),
        item(
            "At what measured condition does an area meet the definition of a radiation area?",
            [
                "More than 2 mrem in 1 hour at 1 meter",
                "More than 5 mrem in 1 hour at 30 cm",
                "More than 100 mrem in 1 year at 30 cm",
                "More than 500 rad in 1 hour at 1 meter",
            ],
            "B",
            "A radiation area is one in which a person could receive more than 5 mrem (0.05 mSv) in 1 hour at 30 cm from the source. "
            "The 2-mrem-per-hour value is an unrestricted-area limit. The 500-rad-at-1-meter threshold defines a very high radiation area.",
        ),
        item(
            "A room is classified as a high radiation area. Which additional control is specifically required?",
            [
                "A visible or audible alarm to control access",
                "A written directive for every person entering",
                "A sealed-source leak test before each entry",
                "A transport index posted at the door",
            ],
            "A",
            "A high radiation area requires a visible or audible alarm or equivalent access control. "
            "Written directives govern specified medical administrations, leak tests apply to sealed sources, and transport indices apply to packages rather than rooms.",
        ),
        item(
            "Which condition defines a very high radiation area?",
            [
                "An absorbed dose that could exceed 5 rad in 1 hour at 30 cm",
                "An effective dose that could exceed 100 mrem in 1 hour at 30 cm",
                "An absorbed dose that could exceed 500 rad in 1 hour at 1 meter",
                "An annual dose that could exceed 5 rem anywhere in the room",
            ],
            "C",
            "A very high radiation area is one in which absorbed dose could exceed 500 rad (5 Gy) in 1 hour at 1 meter from the source or any surface. "
            "The other values describe different regulatory concepts and do not meet this definition.",
        ),
        item(
            "What posting is required where licensed radioactive material is routinely used or stored?",
            [
                "Caution: High Radiation Area",
                "Caution: Radioactive Materials",
                "Danger: Biohazard",
                "No posting is required if staff wear dosimeters",
            ],
            "B",
            "Areas where licensed radioactive material is used or stored require a 'Caution: Radioactive Materials' sign. "
            "A high-radiation-area sign is reserved for the corresponding radiation-level classification. Personnel monitoring does not replace required posting.",
        ),
        item(
            "Which pair of limits applies to an unrestricted area, excluding contributions from administered or released patients?",
            [
                "Less than 2 mrem in any hour and less than 100 mrem per year",
                "Less than 5 mrem in any hour and less than 500 mrem per year",
                "Less than 20 mrem in any hour and less than 1 rem per year",
                "Less than 100 mrem in any hour and less than 5 rem per year",
            ],
            "A",
            "An unrestricted area must remain below 2 mrem (20 uSv) in any 1 hour and below 100 mrem (1 mSv) per year. "
            "For this area-classification rule, dose contributions from administered patients and released patients are excluded.",
        ),
        item(
            "A hospitalized patient has received radioactive material and meets the applicable release criteria. What is required for the patient's room solely because the patient remains there?",
            [
                "A high-radiation-area alarm",
                "A caution sign until all activity has physically decayed",
                "No caution sign is required on that basis",
                "A transport index displayed at the entrance",
            ],
            "C",
            "A room occupied by a patient who meets release criteria does not require a caution sign solely because of the administered radioactive material. "
            "This exception does not eliminate other controls that might be required by measured radiation levels or material storage.",
        ),
        item(
            "A sealed source is stored in a room. At 30 cm from its container, the measured radiation level is 5 mrem per hour. Does the source alone require the room to be posted with a caution sign?",
            [
                "Yes, because any sealed source requires posting",
                "Yes, because the threshold is 2 mrem per hour",
                "No, because the level does not exceed 5 mrem per hour at 30 cm",
                "No, because sealed sources never require posting",
            ],
            "C",
            "A room with a sealed source need not be posted when the radiation level at 30 cm from the source surface, container, or housing does not exceed 5 mrem (0.05 mSv) per hour. "
            "This is a limited exception; higher levels or other licensed-material uses may still require posting.",
        ),
        item(
            "Which color combination is acceptable for the standard radiation warning symbol?",
            [
                "Red symbol on a white background only",
                "Magenta, purple, or black symbol on a yellow background",
                "Yellow symbol on a black background",
                "Green symbol on a white background",
            ],
            "B",
            "The standard radiation symbol may be magenta, purple, or black on a yellow background. "
            "The specified contrast is the important requirement; the other combinations are not the standard NRC warning-symbol format.",
        ),
        item(
            "Which labeling statement is correct for a radioactive source holder or device component?",
            [
                "It must always use a magenta symbol on yellow",
                "It must always use black lettering on white",
                "It may be labeled without a prescribed color requirement",
                "It may be labeled only by the manufacturer",
            ],
            "C",
            "Licensees may label sources, source holders, and other device components without a specific color requirement. "
            "That flexibility should not be confused with the color requirements for the standard posted radiation symbol.",
        ),
    ],
    2: [
        item(
            "The mnemonic R-E-A-D represents which four radiation quantities?",
            [
                "Radioactivity, exposure, absorbed dose, and dose equivalent",
                "Radiation, emission, attenuation, and decay",
                "Roentgen, effective dose, activity, and dose rate",
                "Radioactivity, energy, air kerma, and deterministic effect",
            ],
            "A",
            "R-E-A-D stands for radioactivity, exposure, absorbed dose, and dose equivalent. "
            "The mnemonic separates activity of a source from radiation in air, energy deposited in tissue, and biologically weighted dose.",
        ),
        item(
            "Which units measure the activity of a radioactive source?",
            ["Gray and rad", "Sievert and rem", "Curie and becquerel", "Roentgen and coulomb per kilogram"],
            "C",
            "Activity is measured in curies (Ci) or becquerels (Bq), and 1 mCi equals 37 MBq. "
            "Gray/rad measure absorbed dose, sievert/rem measure equivalent or effective dose, and roentgen or C/kg measure exposure in air.",
        ),
        item(
            "Which description best characterizes an alpha particle?",
            [
                "A massless photon with low LET and high penetration",
                "A helium nucleus with high LET and a very short tissue range",
                "An electron that is readily shielded by a few millimeters of plastic",
                "A free neutron capable of initiating nuclear reactions",
            ],
            "B",
            "An alpha particle contains two protons and two neutrons, has high linear energy transfer, and travels only about 10-100 um in tissue. "
            "Its short range limits external penetration, but alpha emitters can be highly damaging when inhaled, ingested, or delivered therapeutically.",
        ),
        item(
            "Which material is generally most appropriate for stopping beta particles while limiting bremsstrahlung production?",
            ["Acrylic", "Lead", "Tungsten", "Depleted uranium"],
            "A",
            "A few millimeters of a low-atomic-number material such as acrylic can stop beta particles. "
            "High-atomic-number materials such as lead or tungsten promote bremsstrahlung x-ray production when beta particles decelerate near nuclei.",
        ),
        item(
            "What is produced when a positron annihilates with an electron?",
            [
                "One 1,022-keV photon",
                "Two 511-keV photons traveling in opposite directions",
                "Two 140-keV photons traveling in the same direction",
                "An alpha particle and a neutrino",
            ],
            "B",
            "Positron-electron annihilation produces two 511-keV photons traveling in approximately opposite directions. "
            "Coincident detection of these photons is the physical basis of PET imaging. A single 140-keV photon is characteristic of technetium-99m, while beta-minus decay emits an electron rather than an annihilation pair.",
        ),
        item(
            "Which property makes gamma rays useful for general nuclear medicine imaging?",
            [
                "High LET and a tissue range of only a few micrometers",
                "Low LET and relatively high penetration",
                "Positive charge and direct ionization density",
                "Complete absorption by a few millimeters of plastic",
            ],
            "B",
            "Gamma rays are massless photons with low LET and high penetration, allowing photons emitted within the patient to reach an external detector. "
            "Alpha particles have high LET and short range, while plastic shielding is associated with beta particles.",
        ),
        item(
            "Bremsstrahlung x-rays are generated when which event occurs?",
            [
                "A positron annihilates with an electron",
                "A beta-minus particle is deflected near a high-atomic-number nucleus",
                "An alpha particle captures two electrons",
                "A gamma photon undergoes radioactive decay",
            ],
            "B",
            "Bremsstrahlung results when a beta-minus particle is deflected and decelerated near a nucleus, especially a high-Z nucleus such as lead or tungsten. "
            "This is why low-Z materials are preferred as the first layer of beta shielding.",
        ),
        item(
            "Which statement correctly distinguishes physical, biological, and effective half-life?",
            [
                "Physical half-life describes excretion; biological half-life describes nuclear decay",
                "Effective half-life accounts for both nuclear decay and biological clearance",
                "Effective half-life is always longer than physical and biological half-life",
                "Biological half-life is fixed for a radionuclide regardless of the compound or patient",
            ],
            "B",
            "Physical half-life describes nuclear decay, biological half-life describes removal from the body, and effective half-life combines both processes. "
            "Because either process can remove activity, effective half-life is shorter than either component half-life considered alone.",
        ),
        item(
            "A radionuclide has a physical half-life of 6 hours and a biological half-life of 3 hours. What is its effective half-life?",
            ["1 hour", "2 hours", "3 hours", "9 hours"],
            "B",
            "Effective half-life equals (physical half-life x biological half-life) divided by their sum. "
            "For 6 and 3 hours, (6 x 3)/(6 + 3) = 2 hours. It must be shorter than both the physical and biological half-lives.",
        ),
        item(
            "Which quantity describes radiation present in air and is measured in roentgen or coulomb per kilogram?",
            ["Activity", "Exposure", "Absorbed dose", "Dose equivalent"],
            "B",
            "Exposure describes radiation in air and is measured in roentgen or C/kg. "
            "Activity describes nuclear transformations, absorbed dose describes energy deposited per tissue mass, and dose equivalent incorporates radiation weighting.",
        ),
        item(
            "Approximately what exposure is associated with one chest radiograph in the RISC document?",
            ["1 mR", "10 mR", "100 mR", "1 R"],
            "B",
            "The document uses approximately 10 mR as the exposure equivalent of one chest radiograph. "
            "This is an exposure-in-air quantity, not an absorbed or effective patient dose.",
        ),
        item(
            "Which conversion between absorbed-dose units is correct?",
            ["1 rad = 100 Gy", "10 rad = 1 Gy", "100 rad = 1 Gy", "100 rem = 1 Gy"],
            "C",
            "One gray equals 100 rad. Gray and rad are absorbed-dose units; rem is a dose-equivalent unit and cannot be substituted without considering radiation weighting. Roentgen and coulomb per kilogram describe exposure in air, so they are not interchangeable with absorbed-dose units either.",
        ),
        item(
            "The same amount of energy is deposited in a kidney and a liver. Which organ has the greater absorbed dose?",
            ["The kidney, because its mass is smaller", "The liver, because its mass is larger", "They are equal because energy is equal", "It cannot be determined without a radiation weighting factor"],
            "A",
            "Absorbed dose is energy deposited per unit mass. For the same deposited energy, the smaller organ has the greater absorbed dose. "
            "Radiation weighting is needed for dose equivalent, not for the basic absorbed-dose comparison.",
        ),
        item(
            "Which radiation types have the highest linear energy transfer among the choices listed?",
            ["Beta particles and x-rays", "Gamma rays and x-rays", "Alpha particles and neutrons", "Positrons and gamma rays"],
            "C",
            "Alpha particles and neutrons have higher LET and produce denser ionization than beta particles, x-rays, or gamma rays. "
            "Higher LET is associated with greater biological damage for the same absorbed dose.",
        ),
        item(
            "What radiation weighting factor is assigned to alpha particles in the RISC table?",
            ["1", "5", "10", "20"],
            "D",
            "Alpha particles have a radiation weighting factor of 20. "
            "X-rays, gamma rays, and beta particles are assigned 1; slow neutrons are 5 and fast neutrons are 10 in the table.",
        ),
        item(
            "Which radiation type has a weighting factor of 10 in the RISC table?",
            ["Beta particles", "Fast neutrons", "Slow neutrons", "Gamma rays"],
            "B",
            "Fast neutrons have a weighting factor of 10. Slow neutrons are assigned 5, while beta particles and gamma rays are assigned 1. Alpha particles have the largest factor in the table, 20, reflecting their higher linear energy transfer.",
        ),
        item(
            "How is organ or tissue dose equivalent calculated?",
            [
                "Activity multiplied by tissue mass",
                "Absorbed dose multiplied by the radiation weighting factor",
                "Exposure divided by physical half-life",
                "Absorbed dose multiplied only by the tissue weighting factor",
            ],
            "B",
            "Dose equivalent accounts for radiation quality by multiplying absorbed dose by the radiation weighting factor. "
            "Tissue weighting is applied later when calculating effective dose, which accounts for organ sensitivity.",
        ),
        item(
            "Which organs share the highest tissue weighting factor listed in the RISC table?",
            [
                "Brain, skin, and bone surface",
                "Bladder, liver, esophagus, and thyroid",
                "Colon, lung, red bone marrow, stomach, and breast",
                "Gonads only",
            ],
            "C",
            "Colon, lung, red bone marrow, stomach, and breast each have a tissue weighting factor of 0.12. "
            "Gonads are 0.08; bladder, liver, esophagus, and thyroid are 0.04; brain, skin, salivary glands, and bone surface are 0.01.",
        ),
        item(
            "Which tissue weighting factor is assigned to the gonads?",
            ["0.01", "0.04", "0.08", "0.12"],
            "C",
            "The gonadal tissue weighting factor is 0.08. Colon, lung, red marrow, stomach, and breast are higher at 0.12; bladder, liver, esophagus, and thyroid are 0.04; and the lowest listed group is 0.01. These tissue factors describe relative contribution to stochastic risk, not radiation type.",
        ),
        item(
            "What does total effective dose equivalent (TEDE) combine under NRC regulations?",
            [
                "External effective dose equivalent and committed effective dose equivalent from internal exposure",
                "Only shallow dose to skin and extremities",
                "Activity administered and activity excreted",
                "Physical half-life and biological half-life",
            ],
            "A",
            "TEDE combines effective dose equivalent from external exposure with committed effective dose equivalent from internal exposure. "
            "It is intended to account for known internal and external exposure, not activity or half-life.",
        ),
        item(
            "A report lists a value in mCi and another value in mSv. What do these values represent, respectively?",
            [
                "Absorbed dose and activity",
                "Activity and biologically weighted dose",
                "Exposure in air and absorbed dose",
                "Biologically weighted dose and activity",
            ],
            "B",
            "mCi is a unit of activity, describing how many nuclear decays occur. mSv is a unit of equivalent or effective dose, reflecting energy deposition and relative biological risk. "
            "The quantities are related in a clinical calculation but are not interchangeable.",
        ),
        item(
            "Which radiation effect is passed to the progeny of an exposed individual?",
            ["Somatic effect", "Genetic or hereditary effect", "Deterministic skin effect", "Acute radiation syndrome"],
            "B",
            "Genetic or hereditary effects are transmitted to progeny. Somatic effects occur in the exposed person's tissues, while teratogenic effects are developmental abnormalities caused by in utero exposure.",
        ),
        item(
            "During which cell-cycle phase are cells generally most radiosensitive?",
            ["Late S phase", "G0 phase", "G2/M phase", "Early G1 only"],
            "C",
            "Cells are most radiosensitive during G2/M, when DNA is condensed and repair mechanisms have limited access. "
            "Late S phase is relatively radioresistant because DNA repair activity is robust.",
        ),
        item(
            "Which cell type is among the most radiosensitive?",
            ["Mature skeletal muscle cell", "Neuron", "Lymphocyte", "Adipocyte"],
            "C",
            "Lymphocytes and other hematopoietic cells are highly radiosensitive, as are spermatogonia and gastrointestinal stem cells. "
            "Nerve and muscle cells are comparatively radioresistant because they divide infrequently.",
        ),
        item(
            "Why does an oxygen-rich environment increase indirect radiation injury?",
            [
                "Oxygen prevents ionization of water",
                "Reactive oxygen species generated from water can damage DNA, proteins, and lipids",
                "Oxygen increases physical half-life",
                "Oxygen converts gamma rays into alpha particles",
            ],
            "B",
            "Indirect injury occurs when radiation interacts with water and generates reactive oxygen species. "
            "These reactive species damage DNA, proteins, and lipids; oxygen-rich tissues therefore show greater indirect radiation effect.",
        ),
        item(
            "What acute whole-body dose is approximately associated with an LD50/30?",
            ["0.4-0.5 Sv", "1-2 Sv", "4-5 Sv", "40-50 Sv"],
            "C",
            "The RISC document places the LD50/30 at roughly 400-450 rem, or about 4-5 Sv, delivered over a short period. "
            "LD50/30 means a dose expected to kill 50% of an exposed population within 30 days.",
        ),
        item(
            "Which statement best describes a deterministic tissue reaction?",
            [
                "Its probability increases with dose, but severity is independent of dose",
                "It has no threshold and is modeled linearly at low dose",
                "It has a threshold, and severity increases as dose increases above that threshold",
                "It is limited to hereditary effects",
            ],
            "C",
            "Deterministic effects have a threshold below which they are not observed, and severity increases with dose above that threshold. "
            "Examples include erythema, epilation, desquamation, lens opacification, and cataract.",
        ),
        item(
            "Which deterministic effect has the lowest threshold dose in the RISC summary table?",
            ["Transient erythema", "Dry desquamation", "Moist desquamation", "Lens opacification or cataract"],
            "D",
            "Lens opacification and cataract are listed with thresholds around 0.5 Gy, lower than transient erythema at 2 Gy, dry desquamation at 8 Gy, and moist desquamation at 15 Gy. "
            "Onset and threshold vary with dose pattern and fractionation.",
        ),
        item(
            "Which statement best describes a stochastic radiation effect?",
            [
                "Severity increases with dose after a fixed threshold",
                "Probability increases with dose, but severity does not depend on dose",
                "It occurs only after whole-body exposure above 4 Sv",
                "It is limited to skin and lens injury",
            ],
            "B",
            "For stochastic effects, increasing dose increases the probability that an effect will occur, but not its severity. "
            "The linear no-threshold model assumes no completely risk-free threshold and is used conservatively for carcinogenesis and genetic risk.",
        ),
    ],
    3: [
        item(
            "Which agency is primarily responsible for certifying radioactive-material package designs, while another agency regulates labeling and routine transport?",
            [
                "The NRC certifies package designs; the Department of Transportation regulates labeling and transport",
                "The FDA certifies package designs; the NRC regulates labeling and transport",
                "The Department of Transportation certifies package designs; the FDA regulates labeling and transport",
                "The NRC certifies package designs; the EPA regulates labeling and transport",
            ],
            "A",
            "The NRC reviews and certifies package designs for radioactive material. The Department of Transportation regulates transport requirements such as shipping papers, labels, and smaller packages. The FDA and EPA have other radiation-related roles but do not divide these transportation duties in this way.",
        ),
        item(
            "A shipment must withstand severe accident conditions, including impact, puncture, fire, and immersion. Which package type is required?",
            ["Excepted package", "Industrial package", "Type A package", "Type B package"],
            "D",
            "Type B packages are designed for high-activity contents and must withstand severe accident tests. Type A packages are designed for normal transport conditions and minor mishaps, not the full severe-accident sequence.",
        ),
        item(
            "What determines whether a radioactive shipment requires a Type A or Type B package?",
            [
                "The measured dose rate at 1 meter",
                "The activity and form of the radioactive contents",
                "The distance the shipment will travel",
                "Whether the carrier is a common or private carrier",
            ],
            "B",
            "Package type is based principally on the activity and form of the radioactive material inside. By contrast, the external radiation hazard determines which category of package label is used.",
        ),
        item(
            "How is the transport index assigned to a radioactive package?",
            [
                "It is the surface dose rate in mrem per hour",
                "It is the highest dose rate in mrem per hour measured 1 meter from the package",
                "It is the package activity in millicuries divided by 10",
                "It is the removable contamination level divided by the surface dose rate",
            ],
            "B",
            "The transport index is the highest radiation level, in mrem per hour, measured 1 meter from the package. It is used for spacing and transport controls. A Radioactive White-I package does not display a transport index.",
        ),
        item(
            "A package measures 0.4 mrem/hour at its surface and 0.2 mrem/hour at 1 meter. Which label is appropriate?",
            ["Radioactive White-I", "Radioactive Yellow-II", "Radioactive Yellow-III", "No radioactive label is permitted"],
            "A",
            "White-I is used when the surface dose rate is no more than 0.5 mrem/hour and the 1-meter dose rate is no more than 0.5 mrem/hour. Yellow-II and Yellow-III identify progressively greater external radiation hazards.",
        ),
        item(
            "A package measures 35 mrem/hour at its surface and has a transport index of 0.8. Which label is appropriate?",
            ["Radioactive White-I", "Radioactive Yellow-II", "Radioactive Yellow-III", "Excepted quantity"],
            "B",
            "Yellow-II applies when the surface dose rate is greater than 0.5 but no more than 50 mrem/hour and the transport index is no more than 1. Yellow-III is required if either the surface dose rate exceeds 50 mrem/hour or the transport index exceeds 1, within the applicable upper limits.",
        ),
        item(
            "A package has a surface dose rate of 40 mrem/hour and a dose rate of 2 mrem/hour at 1 meter. Which label is required?",
            ["Radioactive White-I", "Radioactive Yellow-II", "Radioactive Yellow-III", "The package cannot be transported under any circumstances"],
            "C",
            "Although the surface reading falls within the Yellow-II range, the 1-meter reading produces a transport index of 2. A transport index greater than 1 requires a Yellow-III label. Classification follows the more restrictive measurement.",
        ),
        item(
            "What is the usual maximum transport index for a package carried in a common-carrier vehicle or an open exclusive-use vehicle?",
            ["1", "5", "10", "50"],
            "C",
            "The usual maximum transport index is 10. A package with a transport index greater than 10 may be transported only under exclusive-use controls in a closed vehicle.",
        ),
        item(
            "Which information belongs on a radioactive package label?",
            [
                "Radionuclide identity, activity, and transport index when applicable",
                "Only the name and address of the recipient",
                "The patient's name and medical record number",
                "The package purchase price and insurance value",
            ],
            "A",
            "Radioactive labels communicate the contents and external hazard, including radionuclide identity, quantity or activity, and transport index for Yellow-II and Yellow-III packages. Patient identifiers and financial information are not package-label requirements.",
        ),
        item(
            "Before an empty, uncontaminated shipping container is discarded as ordinary waste, what must be done?",
            [
                "The container must be stored for ten physical half-lives",
                "All radioactive labels and markings must be removed or defaced",
                "The container must be returned to the NRC",
                "A transport index of zero must be written on every label",
            ],
            "B",
            "Radioactive labels and markings must be removed or defaced before an empty, uncontaminated package is released for unrestricted use or disposal. This prevents a nonradioactive package from being mistaken for a current radioactive shipment.",
        ),
        item(
            "A radioactive package arrives during normal working hours. By when must the required receipt surveys be completed?",
            [
                "Within 30 minutes",
                "Within 3 hours of receipt",
                "By the end of the calendar day",
                "Within 24 hours",
            ],
            "B",
            "Required monitoring must be performed as soon as practical, but no later than 3 hours after receipt during working hours. If the package arrives after hours, the 3-hour period begins at the start of the next working day.",
        ),
        item(
            "A package of radioactive material is delivered after the nuclear medicine department has closed. When does the 3-hour monitoring period begin?",
            [
                "At the time the delivery vehicle enters the property",
                "At midnight",
                "At the beginning of the next working day",
                "When the package is first opened",
            ],
            "C",
            "For an after-hours delivery, required monitoring must be completed within 3 hours after the beginning of the next working day. The clock does not wait until the package is opened.",
        ),
        item(
            "A receiving survey finds radiation or removable contamination above the applicable package limit. What is the appropriate immediate reporting action?",
            [
                "Notify the carrier and the NRC or Agreement State immediately",
                "Notify only the prescribing authorized user within 30 days",
                "Return the package without documenting the survey",
                "Wait for a confirmatory annual audit before reporting",
            ],
            "A",
            "When package limits are exceeded, the licensee must immediately notify both the final delivery carrier and the NRC or Agreement State. Delayed internal review does not replace prompt external notification.",
        ),
        item(
            "A sealed source has no leak-test certificate documenting a test within the preceding 6 months. What should the licensee do?",
            [
                "Continue using it until the next annual inventory",
                "Use it only for diagnostic procedures",
                "Remove it from use until it is tested",
                "Wipe the storage cabinet instead of the source",
            ],
            "C",
            "A source subject to leak testing may not be used or stored for use without a certificate showing a test within the preceding 6 months. It must be tested before returning to service.",
        ),
        item(
            "A sealed-source leak test detects 0.006 microcurie of removable contamination. What is required?",
            [
                "No action because the result is below 0.01 microcurie",
                "Remove the source from use and report the result within 5 days",
                "Repeat the test at the next 6-month interval",
                "Relabel the source as unsealed material and continue using it",
            ],
            "B",
            "A leak-test result of at least 0.005 microcurie (185 Bq) is reportable. The source must be withdrawn from use and the leak reported within 5 days. The result in the scenario exceeds that threshold.",
        ),
        item(
            "How long must records of radiation surveys, instrument calibrations, and sealed-source leak tests generally be retained?",
            ["1 year", "3 years", "5 years", "For the duration of the license in every case"],
            "B",
            "These operational records are generally retained for 3 years. Some other records, including specified individual monitoring and effluent records, have longer retention requirements, so the record category matters.",
        ),
        item(
            "When must an area survey be documented in a location where unsealed material requiring a written directive is prepared or administered?",
            [
                "At the end of each day the material is used",
                "Only after a spill",
                "Once each calendar quarter",
                "Only when an employee dose exceeds an investigational level",
            ],
            "A",
            "The area must be surveyed at the end of each day on which unsealed byproduct material requiring a written directive is prepared or administered. The record includes the date, results, instrument, and person performing the survey.",
        ),
        item(
            "Which radioactive material may be discharged to a sanitary sewer under the routine disposal provision?",
            [
                "Any solid source with a half-life under 120 days",
                "Material that is soluble or readily dispersible in water and remains within annual activity limits",
                "Any material released from a patient room",
                "Only tritium, regardless of annual quantity",
            ],
            "B",
            "Sewer disposal is limited to material that is soluble or readily dispersible in water and that remains within radionuclide-specific and total annual limits. Solid sealed sources do not qualify merely because they are short-lived.",
        ),
        item(
            "Which set gives the annual sanitary-sewer limits stated in the RISC document?",
            [
                "Tritium 5 Ci, carbon-14 1 Ci, and all other radionuclides combined 1 Ci",
                "Tritium 1 Ci, carbon-14 5 Ci, and all other radionuclides combined 10 Ci",
                "Tritium 10 Ci, carbon-14 10 Ci, and no combined limit for other radionuclides",
                "One curie total for all radionuclides, with no isotope-specific limits",
            ],
            "A",
            "The annual limits are 5 Ci of tritium, 1 Ci of carbon-14, and 1 Ci for all other radionuclides combined. These limits do not eliminate the requirement that the material be soluble or readily dispersible.",
        ),
        item(
            "How are radioactive materials contained in a patient's urine or feces treated for sanitary-sewer disposal limits?",
            [
                "They are prohibited from entering a sanitary sewer",
                "They count against the facility's annual radionuclide limits",
                "They are exempt from the sewer-disposal quantity limits",
                "They may be discharged only after ten physical half-lives",
            ],
            "C",
            "Radioactive material excreted by a patient is exempt from the routine sewer-disposal quantity limits. This patient-excreta exception should not be generalized to laboratory stock or other radioactive waste.",
        ),
        item(
            "Which waste is eligible for decay in storage under the RISC summary?",
            [
                "Material with a physical half-life of 120 days or less",
                "Material with a biological half-life of 120 days or less",
                "Any material whose dose rate is below 2 mrem/hour",
                "Only material containing technetium-99m",
            ],
            "A",
            "Decay in storage may be used for material with a physical half-life of 120 days or less. Biological half-life describes clearance from an organism and does not determine eligibility of stored waste.",
        ),
        item(
            "Before decay-in-storage waste is released as ordinary trash, how should it be surveyed?",
            [
                "At 1 meter with the waste behind its storage shielding",
                "At the container surface with a sensitive instrument and no intervening shielding",
                "Only by reviewing the calculated number of half-lives",
                "With a personnel dosimeter placed beside it overnight",
            ],
            "B",
            "The waste must be surveyed at the surface with an appropriate sensitive instrument, without shielding, and must be indistinguishable from background. A time calculation alone is not sufficient.",
        ),
        item(
            "What additional step is required after decay-in-storage waste is shown to be indistinguishable from background?",
            [
                "Add a new Radioactive White-I label",
                "Remove or deface radiation labels before disposal",
                "Send the waste to a low-level waste burial site",
                "Retain it for another 120 days",
            ],
            "B",
            "Once the waste passes the required survey, radiation labels and markings must be removed or defaced before ordinary disposal. Survey records must be retained for 3 years.",
        ),
        item(
            "Which statement best distinguishes a sealed source from unsealed radioactive material?",
            [
                "A sealed source is permanently bonded or encapsulated to prevent dispersion under normal use",
                "A sealed source emits only gamma radiation",
                "A sealed source contains less than 0.005 microcurie",
                "A sealed source never requires inventory or leak testing",
            ],
            "A",
            "A sealed source is constructed so radioactive material remains contained under normal conditions of use. The designation does not depend on radiation type or low activity, and many sealed sources require periodic inventory and leak testing.",
        ),
    ],
    4: [
        item(
            "Which adult occupational limits apply in a calendar year?",
            [
                "Whole body 5 rem, lens 15 rem, and skin or extremity 50 rem",
                "Whole body 0.5 rem, lens 1.5 rem, and skin or extremity 5 rem",
                "Whole body 50 rem, lens 15 rem, and skin or extremity 5 rem",
                "Whole body 5 rem, lens 50 rem, and skin or extremity 15 rem",
            ],
            "A",
            "The adult annual limits are 5 rem whole-body effective dose, 15 rem to the lens, and 50 rem to the skin, an extremity, or an individual organ. The second option gives the corresponding 10% limits for minors.",
        ),
        item(
            "What fraction of the adult occupational limits applies to a minor radiation worker?",
            ["The same limits", "One-half", "One-tenth", "One-hundredth"],
            "C",
            "A minor's annual occupational limits are 10% of the adult limits: 0.5 rem whole body, 1.5 rem to the lens, and 5 rem to skin, extremities, or an organ. The limits are not one-half of the adult values, and the ordinary public limit is a separate 0.1 rem per year.",
        ),
        item(
            "An adult radiation worker exceeds the 5-rem whole-body occupational limit in September. What is the consequence for the remainder of the calendar year?",
            [
                "The worker may continue unrestricted work if a second dosimeter is issued",
                "The worker may not enter a radiation zone until the next calendar year",
                "The worker's limit automatically increases to 10 rem after RSO approval",
                "Only fluoroscopic work is prohibited",
            ],
            "B",
            "After the annual whole-body occupational limit is exceeded, the worker cannot continue entering radiation zones during that calendar year. A new badge or local approval cannot raise a regulatory annual limit.",
        ),
        item(
            "A worker received dose during a planned special exposure. How is that dose handled in future planned special exposures?",
            [
                "It is ignored because it was authorized",
                "It is subtracted from the cumulative planned-special-exposure allowance",
                "It is counted only if it exceeded 5 rem",
                "It replaces the worker's routine occupational dose record",
            ],
            "B",
            "Dose from a planned special exposure is tracked separately but is subtracted from the applicable lifetime planned-special-exposure allowance. Authorization does not erase the dose. Accident and emergency doses above annual limits are handled similarly when determining remaining planned-special-exposure eligibility.",
        ),
        item(
            "How is deep-dose equivalent assigned when different parts of the body receive different penetrating-radiation doses?",
            [
                "Use the average of all monitored body locations",
                "Use the highest deep-dose equivalent measured at any monitored body location",
                "Use only the reading from the dominant hand",
                "Use the lowest reading to avoid double counting",
            ],
            "B",
            "For nonuniform exposure, the reported deep-dose equivalent is based on the highest dose to any monitored body location. Shallow dose is evaluated differently, using the highest dose averaged over a contiguous 10-square-centimeter skin area.",
        ),
        item(
            "What is the dose limit to the embryo or fetus of a declared pregnant worker for the entire pregnancy?",
            ["0.1 rem (1 mSv)", "0.5 rem (5 mSv)", "1.5 rem (15 mSv)", "5 rem (50 mSv)"],
            "B",
            "The limit is 0.5 rem (5 mSv) for the entire gestation after pregnancy is declared. This is distinct from the 0.1-rem annual public limit and the 5-rem adult occupational whole-body limit.",
        ),
        item(
            "Which action is required for a pregnancy to be treated as declared for occupational dose control?",
            [
                "The worker must submit a voluntary written declaration that includes the estimated date of conception",
                "The supervisor must infer pregnancy from scheduling requests",
                "A positive laboratory result must be sent directly to the NRC",
                "The worker must permanently leave all restricted areas",
            ],
            "A",
            "Declaration is voluntary and must be made in writing, including the estimated date of conception. A worker may also withdraw the declaration in writing; the employer should not infer or impose declaration.",
        ),
        item(
            "A worker has two pregnancies at different times while employed by the same licensee. How should declarations be handled?",
            [
                "The first declaration remains in force for all future pregnancies",
                "Each pregnancy requires a separate written declaration",
                "Only the first pregnancy is subject to the fetal dose limit",
                "The RSO may declare subsequent pregnancies verbally",
            ],
            "B",
            "Each pregnancy is a separate event and requires its own voluntary written declaration. A prior declaration does not automatically carry forward. The worker may choose not to declare or may withdraw a declaration in writing, so a supervisor cannot substitute a verbal declaration.",
        ),
        item(
            "What is the usual annual dose limit to an individual member of the public from licensed operations?",
            ["10 mrem (0.1 mSv)", "100 mrem (1 mSv)", "500 mrem (5 mSv)", "5 rem (50 mSv)"],
            "B",
            "The usual public limit is 100 mrem (1 mSv) per year from licensed operations. It excludes natural background and the person's own medical exposure, among specified exclusions.",
        ),
        item(
            "An authorized user approves a visitor to provide comfort and care to a patient who cannot yet be released. What maximum dose may that visitor receive?",
            ["0.1 rem (1 mSv)", "0.5 rem (5 mSv)", "1.5 rem (15 mSv)", "5 rem (50 mSv)"],
            "B",
            "A visitor providing comfort and care may receive up to 0.5 rem (5 mSv) when the authorized user approves the exposure in advance. This is a specific exception to the ordinary public limit.",
        ),
        item(
            "Which exposure is excluded when determining compliance with the public dose limit from licensed operations?",
            [
                "Dose from a facility's improperly shielded storage room",
                "Natural background radiation",
                "Dose to a visitor from handling a package",
                "Dose from airborne releases caused by the licensee",
            ],
            "B",
            "Natural background radiation is excluded, as are the individual's own medical exposure and specified patient-related or research exposures. Dose caused by the licensee's operations generally remains part of the compliance calculation.",
        ),
        item(
            "When is occupational monitoring generally required for an adult worker?",
            [
                "When the worker is likely to receive more than 10% of an applicable annual occupational limit",
                "Only after the worker exceeds an annual limit",
                "Whenever the worker enters a hospital",
                "Only when handling alpha emitters",
            ],
            "A",
            "Adult monitoring is required when an individual is likely to receive more than 10% of an applicable annual occupational limit. Monitoring is preventive and cannot wait until a limit has already been exceeded.",
        ),
        item(
            "Which projected annual dose requires monitoring of a minor?",
            [
                "More than 100 mrem whole body",
                "More than 25 mrem whole body",
                "More than 1.5 rem whole body",
                "Any measurable whole-body dose",
            ],
            "A",
            "A minor must be monitored when likely to receive more than 100 mrem deep-dose equivalent, more than 150 mrem to the lens, or more than 500 mrem shallow dose to skin or an extremity. These are monitoring triggers, not the minor's annual dose limits, which are higher.",
        ),
        item(
            "When is monitoring required for a declared pregnant worker on the basis of fetal dose?",
            [
                "When the embryo/fetus is likely to receive more than 100 mrem during the entire pregnancy",
                "Only when fetal dose is expected to exceed 500 mrem",
                "Whenever the worker remains employed after declaration",
                "Only during the first trimester",
            ],
            "A",
            "Monitoring is required if the embryo/fetus is likely to receive more than 100 mrem during the entire pregnancy. The regulatory dose limit is 500 mrem, so the monitoring trigger is intentionally lower.",
        ),
        item(
            "A worker's quarterly occupational dose exceeds 10% of an annual limit. What should the RSO do?",
            [
                "Wait until the annual report is issued",
                "Investigate the exposure, evaluate ALARA practices, and assess dosimeter placement",
                "Automatically suspend the worker's license",
                "Delete the reading if no symptoms occurred",
            ],
            "B",
            "The RSO should investigate quarterly exposures above 10% of an annual limit, including whether work practices remain ALARA and whether the dosimeter was worn appropriately. The trigger calls for review, not automatic punishment or alteration of the record.",
        ),
        item(
            "Which dose records should be maintained for a declared pregnant worker?",
            [
                "Only the worker's routine whole-body dose",
                "Only an estimated fetal dose at delivery",
                "The worker's occupational dose and the dose to the embryo/fetus",
                "No records unless the pregnancy limit is exceeded",
            ],
            "C",
            "The licensee maintains the declared worker's occupational dose record and the embryo/fetal dose record, with the fetal record linked to the worker's monitoring record. Recordkeeping begins before an exceedance occurs.",
        ),
        item(
            "Which statement about annual individual dose reports is correct?",
            [
                "They may omit internal dose whenever external dose is low",
                "They should preserve privacy while reporting the required monitoring results",
                "They are sent only to workers who exceed a limit",
                "They replace the licensee's underlying dose records",
            ],
            "B",
            "Required dose reports must convey the monitored dose while protecting personal information. Reporting does not replace the licensee's duty to retain the underlying records, and it is not limited only to overexposed workers.",
        ),
        item(
            "Which person must be monitored regardless of whether the projected dose is below 10% of the routine annual occupational limit?",
            [
                "A worker who enters a high or very high radiation area",
                "A receptionist outside the restricted area",
                "A visitor who remains in an unrestricted hallway",
                "A courier carrying an empty, surveyed package",
            ],
            "A",
            "Individuals entering high or very high radiation areas require monitoring because of the potential dose rates. The usual 10% projected-dose trigger is not the only monitoring criterion.",
        ),
    ],
    5: [
        item(
            "Why are short-lived radionuclides generally preferred for diagnostic radiopharmaceuticals?",
            [
                "They provide the needed imaging interval while reducing unnecessary retained activity and dose",
                "They eliminate the need to measure administered activity because decay corrects any preparation error",
                "They can be administered without FDA oversight",
                "They produce only nonionizing radiation",
            ],
            "A",
            "A diagnostic radionuclide should persist long enough to perform the study but decay promptly afterward, limiting unnecessary dose. A short half-life does not eliminate activity measurement, regulatory controls, or ionizing radiation.",
        ),
        item(
            "Which pathway permits routine marketing of a radiopharmaceutical for an approved clinical indication?",
            [
                "An FDA-approved new drug application or abbreviated new drug application",
                "A local radiation safety committee vote alone",
                "An investigational new drug application with no FDA involvement",
                "A package transport certificate issued by the Department of Transportation",
            ],
            "A",
            "Routine clinical marketing requires an FDA-approved NDA or ANDA. An IND governs investigational use, while a radiation safety committee and transportation regulators address different responsibilities.",
        ),
        item(
            "Which information should appear on a radiopharmaceutical container label?",
            [
                "Radionuclide, chemical form, activity with calibration date and time, expiration, and identifying pharmacy information",
                "Only the radionuclide name and radiation symbol",
                "The patient's complete medical history, allergies, prior examinations, and current laboratory results",
                "Only the prescribed activity, with no calibration time",
            ],
            "A",
            "The label must identify what the product is, how much activity it contains and when that activity applies, its expiration, and traceable pharmacy or lot information. Activity without a calibration time is incomplete because radioactive decay changes the quantity.",
        ),
        item(
            "Which preparation requires the intended patient's name on the label before delivery?",
            [
                "A unit dose of technetium-99m intended for a routine diagnostic scan",
                "A radiolabeled blood component prepared for reinjection",
                "A multidose vial retained in the hot lab",
                "A sealed calibration source",
            ],
            "B",
            "Radiolabeled blood components and therapeutic radiopharmaceuticals require patient-specific identification. Diagnostic doses may use a temporary process when the name is not yet available, but the dose must later be associated with the patient.",
        ),
        item(
            "A diagnostic unit dose is prepared before the patient's name is known. How long may the pharmacy use a temporary identifier before associating the dose with the patient?",
            ["24 hours", "48 hours", "72 hours", "7 days"],
            "C",
            "A diagnostic dose may be prepared using a temporary identifier when the patient's name is unavailable, but the patient association must be completed within 72 hours and retained as required. This limited diagnostic exception does not remove the need for traceability or permit patient-specific therapeutic products to remain unidentified.",
        ),
        item(
            "A prescribed activity is 10 mCi. The measured activity at administration is 7.8 mCi, and the authorized user did not revise the prescription. Which statement is correct?",
            [
                "The activity is acceptable because lower activities have no tolerance requirement",
                "The activity is outside the usual plus-or-minus 20% administration range",
                "The activity may be given if the technologist documents the difference afterward",
                "The activity is within tolerance because 2.2 mCi is less than 20 mCi",
            ],
            "B",
            "A measured activity should generally be within plus or minus 20% of the prescribed amount unless the authorized user revises the prescription beforehand. A dose of 7.8 mCi is 22% below 10 mCi, so it falls outside that range. The percentage is relative to the prescription, not an absolute millicurie difference.",
        ),
        item(
            "When may an authorized user modify a prescribed activity so that the available dose falls within the authorized range?",
            [
                "Before administration, by revising the prescription or written directive as applicable",
                "Only after administration and only if the dose was too low",
                "After administration, by asking the technologist to revise the recorded prescription to match the measured dose",
                "Never; a prescription cannot be changed",
            ],
            "A",
            "An authorized user may revise the prescription before administration, provided all applicable written-directive requirements are met. Retrospective alteration of a record does not cure an unauthorized administration.",
        ),
        item(
            "Which patient-identification practice is appropriate immediately before radiopharmaceutical administration?",
            [
                "Use the room number together with the scheduled examination because both are unique during the appointment",
                "Ask one staff member who the patient is",
                "Confirm two approved identifiers, such as full name and date of birth",
                "Use the radiopharmaceutical label as the sole identifier",
            ],
            "C",
            "Two independent patient identifiers are required. Room number, procedure, or staff recognition alone is not sufficiently specific. The administration record and product label must be matched to the identified patient.",
        ),
        item(
            "An unidentified emergency patient requires an urgent radiopharmaceutical study. What is the best approach?",
            [
                "Delay administration until registration supplies a permanent legal name and government-issued identification",
                "Use two temporary identifiers and formalize the identity as soon as possible",
                "Use the room number as the only identifier",
                "Administer the dose without creating any patient record",
            ],
            "B",
            "Urgent care need not wait for a permanent identity. The facility should assign two distinct temporary identifiers and reconcile them with the formal identity as soon as possible.",
        ),
        item(
            "Which event involving a pregnant patient must be reported under the fetal-dose provision?",
            [
                "Any diagnostic administration performed during pregnancy",
                "An embryo/fetal dose exceeding 5 rem that was not specifically approved in advance",
                "A fetal dose exceeding 100 mrem after any approved therapy",
                "Any administration to a patient younger than 50 years",
            ],
            "B",
            "An unintended embryo/fetal dose greater than 5 rem is reportable unless the dose was specifically approved in advance as part of the intended medical treatment. Pregnancy alone does not make every administration a reportable event.",
        ),
        item(
            "A reportable dose to an embryo, fetus, or nursing child is discovered. Which reporting sequence is required?",
            [
                "Telephone notification to the regulator by the next calendar day and a written report within 15 days",
                "A written report within 24 hours, with no telephone report",
                "Telephone notification within 30 days and a written report within 90 days",
                "Notification only during the next license renewal",
            ],
            "A",
            "The regulator is notified by telephone no later than the next calendar day, followed by a written report within 15 days. Patient-identifying information is not included in the regulatory report.",
        ),
        item(
            "How should a reportable fetal or nursing-child exposure affect urgent patient care?",
            [
                "Treatment must stop until the NRC completes its review",
                "Required reporting and notification should not delay medically necessary care",
                "Only nonradioactive treatment may continue",
                "The patient must be transferred to a federal facility",
            ],
            "B",
            "Regulatory reporting is important, but it must not delay necessary clinical care. The treating clinician should manage the patient while the facility completes the required notifications.",
        ),
        item(
            "A breastfeeding patient is released after radiopharmaceutical administration. What dose criterion protects the nursing child or other individual?",
            [
                "The expected dose should not exceed 500 mrem (5 mSv)",
                "The expected dose should not exceed 5 rem (50 mSv)",
                "No dose criterion applies after the patient leaves the facility",
                "The expected dose must be zero",
            ],
            "A",
            "Release is permitted when exposure to another individual is not likely to exceed 500 mrem (5 mSv). Written instructions are required when continued breastfeeding could give the child more than 100 mrem (1 mSv).",
        ),
        item(
            "When are written breastfeeding instructions required?",
            [
                "Whenever any diagnostic radiopharmaceutical is administered",
                "When continued breastfeeding could deliver more than 100 mrem (1 mSv) to the child",
                "Only when the expected child dose exceeds 500 mrem",
                "Only for technetium-99m studies",
            ],
            "B",
            "Written guidance on interruption or discontinuation is required when the nursing child could receive more than 100 mrem if breastfeeding continued. The 500-mrem value is the broader release-dose criterion, not the instruction trigger.",
        ),
        item(
            "What counseling is appropriate before therapeutic radioiodine for a patient who is breastfeeding?",
            [
                "Stop breastfeeding only on the morning of therapy",
                "Stop breastfeeding at least 6 weeks before treatment",
                "Continue breastfeeding with a lead apron over the infant",
                "Pump and discard milk for 4 hours, then resume",
            ],
            "B",
            "The RISC guidance calls for cessation of breastfeeding at least 6 weeks before therapeutic radioiodine. This reduces breast uptake and contamination risk; a brief interruption is not adequate.",
        ),
        item(
            "Which radiopharmaceutical requires permanent discontinuation of breastfeeding for the current child?",
            ["Fluorine-18 FDG", "Technetium-99m sestamibi", "Iodine-131 sodium iodide", "Nitrogen-13 ammonia"],
            "C",
            "Iodine-131 requires permanent discontinuation for the current child. Fluorine-18 generally requires a 4-hour interruption, technetium-99m products generally 24 hours, and nitrogen-13 no interruption in the RISC table.",
        ),
        item(
            "Which breastfeeding recommendation is paired correctly with the radiopharmaceutical?",
            [
                "Fluorine-18: 4-hour interruption",
                "Gallium-67: no interruption",
                "Technetium-99m: permanent discontinuation",
                "Indium-111 labeled leukocytes: 24-hour interruption",
            ],
            "A",
            "The table recommends 4 hours for fluorine-18. Gallium-67 requires a much longer interruption, technetium-99m products generally require 24 hours, and indium-111 labeled leukocytes require several days.",
        ),
        item(
            "Where should a ring dosimeter be worn while preparing radiopharmaceuticals?",
            [
                "Over the glove on the nondominant hand, detector facing away from the source",
                "Under the glove on the hand most likely to receive exposure, detector facing the palm",
                "At the wrist outside the lab coat, detector facing the elbow",
                "On either hand with the detector orientation ignored",
            ],
            "B",
            "The ring is worn under the glove on the hand expected to receive the greatest exposure, with the detector toward the palm. This position better estimates dose to the most exposed finger while keeping the dosimeter clean.",
        ),
        item(
            "Which syringe shielding is generally preferred when handling positron-emitting radiopharmaceuticals?",
            ["Thin aluminum only", "Tungsten", "Acrylic only", "No shielding because positrons have a short range"],
            "B",
            "High-density tungsten syringe shields are commonly used for positron emitters because annihilation photons require substantial attenuation. Positron range alone does not eliminate external photon exposure.",
        ),
        item(
            "Which material is preferred as the first layer of shielding for a high-energy beta emitter?",
            ["Lead", "Tungsten", "A low-atomic-number material such as acrylic", "Depleted uranium"],
            "C",
            "A low-Z material such as acrylic or aluminum reduces beta energy with less bremsstrahlung production. Dense high-Z lead placed directly against a beta source can increase bremsstrahlung; additional outer shielding may then be used for the secondary photons.",
        ),
        item(
            "Why should a patient be surveyed after administration before leaving the radiopharmacy or injection area?",
            [
                "To confirm that no contamination is present on the patient or nearby articles",
                "To recalculate the physical half-life",
                "To determine whether the prescribed activity was FDA approved",
                "To replace the preadministration identity check",
            ],
            "A",
            "A postadministration survey can identify contamination on the patient, chair, floor, or supplies so it can be controlled promptly. It complements rather than replaces activity measurement and patient identification.",
        ),
        item(
            "What additional monitoring is associated with handling more than 10 mCi of volatile iodine-131?",
            [
                "A bioassay program for potentially exposed personnel",
                "Daily chest radiographs",
                "A second transport index",
                "Continuous fetal monitoring",
            ],
            "A",
            "Because volatile iodine can be inhaled and concentrated by the thyroid, personnel handling quantities above the specified threshold require bioassay monitoring. External survey alone may miss internal uptake.",
        ),
        item(
            "Which control is most appropriate when working with a volatile radioiodine preparation?",
            [
                "Prepare it in a suitable fume hood or containment system",
                "Use only a lead apron",
                "Open all room doors to improve air circulation",
                "Rely on a ring dosimeter as the primary contamination control",
            ],
            "A",
            "A fume hood or appropriate containment controls airborne radioiodine. A lead apron and dosimeter measure or attenuate selected external exposure but do not prevent inhalation or room contamination.",
        ),
        item(
            "What is a key radiation-safety concern after a xenon-133 ventilation study?",
            [
                "The patient becomes a sealed source for 120 days",
                "Exhaled gas and collection-system waste require containment and adequate room-clearance time",
                "Bremsstrahlung from the patient's skin is the dominant hazard",
                "All room surfaces must be disposed of as low-level waste",
            ],
            "B",
            "Xenon-133 is a radioactive gas, so exhaled activity must be trapped or exhausted appropriately and the room may need a calculated clearance interval. The principal issue is airborne activity, not long-term sealed-source behavior.",
        ),
    ],
    6: [
        item(
            "Which agency licenses and inspects medical possession and use of byproduct material in a non-Agreement State?",
            ["Nuclear Regulatory Commission", "Food and Drug Administration", "Department of Transportation", "Environmental Protection Agency"],
            "A",
            "The NRC regulates possession and medical use of byproduct material in non-Agreement States through licensing, inspection, and enforcement. The FDA regulates products and manufacturing practices, while the DOT regulates transportation.",
        ),
        item(
            "What is the principal regulatory role of an Agreement State?",
            [
                "It assumes specified NRC authority to license and regulate byproduct material within the state",
                "It approves radioactive drugs and devices for interstate marketing after evaluating safety and clinical effectiveness",
                "It certifies every Type B shipping package used nationally",
                "It replaces all federal radiation regulations with voluntary guidance",
            ],
            "A",
            "Under an agreement authorized by the Atomic Energy Act, a state assumes portions of the NRC's regulatory authority. Its program remains subject to NRC review for adequacy and compatibility.",
        ),
        item(
            "What does the NRC evaluate through the Integrated Materials Performance Evaluation Program?",
            [
                "Whether Agreement State radiation-control programs remain adequate and compatible",
                "Whether radiopharmaceuticals used in Agreement States remain clinically effective for every approved indication",
                "Whether a carrier charged the correct shipping rate",
                "Whether a hospital's diagnostic images meet accreditation standards",
            ],
            "A",
            "IMPEP is the NRC's framework for periodically evaluating Agreement State and NRC materials programs for public-health protection and regulatory compatibility. It is not a drug-approval or image-quality program.",
        ),
        item(
            "An associate radiation safety officer is appointed to manage selected tasks. Which responsibility remains with the radiation safety officer?",
            [
                "Implementing the radiation protection program",
                "Performing every daily area survey personally",
                "Preparing every patient dose personally",
                "Signing every package receipt",
            ],
            "A",
            "The RSO may assign specific duties to an ARSO in writing, but cannot delegate the authority or responsibility for implementing the radiation protection program. Routine tasks may be performed by appropriately trained personnel.",
        ),
        item(
            "Which authority must management provide to the radiation safety officer?",
            [
                "Authority to identify problems, initiate corrective action, stop unsafe operations, and verify correction",
                "Authority to approve new radiopharmaceuticals for commercial marketing without separate FDA review",
                "Authority to waive occupational dose limits whenever an authorized user documents clinical necessity",
                "Authority to replace the NRC during an inspection",
            ],
            "A",
            "The RSO needs organizational freedom, resources, and authority to identify safety problems, act on them, stop unsafe work, and verify corrective actions. The RSO cannot waive regulations or assume another agency's role.",
        ),
        item(
            "Which individual meets the basic definition of an authorized user?",
            [
                "A physician, dentist, or podiatrist named on the license for specified medical uses",
                "Any nuclear medicine technologist who has completed annual safety training and works under general supervision",
                "Any pharmacist employed by the hospital",
                "The administrator who signs the radioactive-materials license",
            ],
            "A",
            "An authorized user is a qualified physician, dentist, or podiatrist identified for specified medical uses under the license. Supervised staff may perform delegated tasks but do not thereby become authorized users.",
        ),
        item(
            "Which task may an authorized user or authorized nuclear pharmacist delegate?",
            [
                "A specific medical-use or preparation task to a properly instructed and supervised individual",
                "Final responsibility for ensuring that all delegated work complies with the radioactive-materials license",
                "Authority to approve a new authorized user without required qualifications",
                "Authority to alter an NRC dose limit",
            ],
            "A",
            "AUs and ANPs may delegate defined tasks when the individual is properly trained and supervised. Delegation of a task does not transfer the authorized individual's regulatory responsibility.",
        ),
        item(
            "Which individual must be named on a license authorizing a gamma stereotactic radiosurgery unit?",
            ["Authorized medical physicist", "Authorized nuclear pharmacist", "Radiologic technologist", "Department of Transportation safety officer"],
            "A",
            "An authorized medical physicist is required for specified device-based uses, including gamma stereotactic radiosurgery, teletherapy, photon-emitting remote afterloaders, and strontium-90 ophthalmic applicators. An authorized nuclear pharmacist prepares radioactive drugs, while an authorized user directs medical administration; neither title automatically substitutes for the AMP role.",
        ),
        item(
            "When is a radiation safety committee required?",
            [
                "When the license authorizes two or more different types of byproduct-material use",
                "Whenever a facility employs more than two technologists",
                "Only after a reportable medical event demonstrates that the existing radiation-safety program was inadequate",
                "Only for a Type C broad-scope license",
            ],
            "A",
            "A licensee authorized for two or more different types of medical use must have an RSC to oversee the licensed uses. Staffing count and prior events do not determine the requirement.",
        ),
        item(
            "Which person is required on a radiation safety committee?",
            [
                "A management representative who is neither an authorized user nor the radiation safety officer",
                "A representative from the Department of Transportation",
                "Every technologist, nurse, and pharmacist who handles radioactive material anywhere in the institution",
                "The facility's malpractice insurer",
            ],
            "A",
            "Required membership includes the RSO, an AU for each type of permitted use, a nursing representative, and a management representative who is neither an AU nor the RSO. Other members may be added as appropriate.",
        ),
        item(
            "Which broad-scope license is most typical of a large academic medical center with diverse uses and an RSC?",
            ["Type A", "Type B", "Type C", "Master Materials License"],
            "A",
            "Type A is the broadest broad-scope license and is typical of large academic programs. Type B programs are smaller and less diverse, while Type C programs use smaller quantities and are common in small research or nuclear cardiology settings.",
        ),
        item(
            "Which description best fits a Type C broad-scope license?",
            [
                "A small program needing flexibility to possess varied materials in limited quantities",
                "A large academic program with the broadest range of medical uses",
                "A federal organization operating multiple medical and industrial sites under a single NRC oversight structure",
                "A commercial carrier transporting Type B packages",
            ],
            "A",
            "Type C broad-scope licenses provide flexibility for smaller programs that do not require large quantities, such as some nuclear cardiology clinics and small research laboratories. Type A is the largest and most diverse broad-scope category, and a Master Materials License applies to a federal organization operating multiple sites.",
        ),
        item(
            "What is a Master Materials License?",
            [
                "An NRC license allowing a federal organization to oversee byproduct-material use at multiple sites",
                "A state license limited to one private nuclear pharmacy",
                "An FDA authorization allowing one manufacturer to market all of its radiopharmaceuticals at multiple federal sites",
                "A shipping certificate valid for every Type A package",
            ],
            "A",
            "An MML lets a federal organization administer permits, inspections, and enforcement for multiple sites under its jurisdiction, while the NRC retains oversight and inspects the MML program at least every 2 years. It is a regulatory structure, not FDA approval of a manufacturer's products or a state broad-scope license.",
        ),
        item(
            "What is a written directive?",
            [
                "An authorized user's written order for a specified administration to a patient or research subject",
                "A technologist's note that a diagnostic study was completed",
                "A carrier's record of a package transport index",
                "An annual management statement defining the facility's ALARA goals, investigational levels, and audit schedule",
            ],
            "A",
            "A written directive is the authorized user's written order for administration of byproduct material or radiation from byproduct material to a specific patient or human research subject. It is distinct from routine charting and shipping documentation.",
        ),
        item(
            "Which use of unsealed byproduct material ordinarily does not require a written directive?",
            [
                "An uptake, dilution, or excretion study using an appropriately prepared radioactive drug",
                "Oral administration of iodine-131 above 30 microcuries",
                "Parenteral administration of an alpha-emitting therapeutic drug",
                "Administration of a therapeutic activity that requires a written directive",
            ],
            "A",
            "Uptake, dilution, and excretion studies ordinarily do not require a written directive. Therapeutic unsealed-material uses and oral iodine-131 above the specified activity do require one.",
        ),
        item(
            "What training is required for an authorized user performing uptake, dilution, and excretion studies under the described pathway?",
            [
                "60 hours total, including at least 8 hours of classroom and laboratory training",
                "80 hours total, all of which must be classroom training",
                "700 hours total, including at least 200 classroom hours",
                "Only the facility's annual in-service training",
            ],
            "A",
            "The uptake, dilution, and excretion pathway requires 60 hours of training and experience, including at least 8 classroom and laboratory hours, plus supervised work experience, examination, and attestation requirements. The much larger 700-hour pathways apply to imaging/localization or therapeutic written-directive uses.",
        ),
        item(
            "What training is required for the imaging and localization authorized-user pathway?",
            [
                "700 hours total, including at least 80 hours of classroom and laboratory training",
                "60 hours total, including 8 classroom hours",
                "700 hours total, including 200 classroom hours",
                "80 hours total with no supervised work experience",
            ],
            "A",
            "Imaging and localization require 700 hours of training and experience with at least 80 classroom and laboratory hours. The 200-classroom-hour requirement applies to the broader therapeutic written-directive pathway.",
        ),
        item(
            "Which training requirement applies to use of unsealed byproduct material that requires a written directive?",
            [
                "700 hours of training and experience, including 200 classroom hours",
                "700 hours of training and experience, including 80 classroom hours",
                "60 hours of training and experience, including 8 classroom hours",
                "Annual safety instruction only",
            ],
            "A",
            "The therapeutic written-directive pathway requires 700 hours, including 200 classroom hours, along with appropriate residency or board pathways, supervised experience, examination, and attestation. Imaging and localization also require 700 total hours but only 80 classroom and laboratory hours, which is the key distinction.",
        ),
        item(
            "For an authorized user seeking approval for a therapeutic administration category, how much case experience is required under the described alternate pathway?",
            ["At least 1 case in any category", "At least 3 cases in each requested category", "At least 10 cases total", "No case experience if an attestation is signed"],
            "B",
            "The individual must have supervised experience with at least three cases in each requested administration category. Written attestation complements rather than replaces the required case experience.",
        ),
        item(
            "A 42-year-old patient is scheduled for therapeutic iodine-131 and has no history of hysterectomy or bilateral tubal ligation. What must be documented?",
            [
                "A negative serum beta-hCG result obtained within 1 week before therapy",
                "A negative urine test obtained within 30 days",
                "A declaration that the patient is not breastfeeding, with no pregnancy test",
                "No pregnancy evaluation if the patient denies pregnancy",
            ],
            "A",
            "Potentially childbearing individuals under 50 require a documented negative serum beta-hCG within one week of iodine-131 therapy unless a stated exception such as hysterectomy or remote bilateral tubal ligation applies. A verbal denial of pregnancy or an older urine test does not meet the stated documentation requirement.",
        ),
        item(
            "At what oral iodine-131 activity is a written directive required?",
            ["Greater than 30 microcuries", "Greater than 1 millicurie", "Only greater than 33 millicuries", "Only when the patient will be hospitalized"],
            "A",
            "A written directive signed and dated by an authorized user is required for oral iodine-131 above 1.11 MBq, or 30 microcuries. The 33-mCi value distinguishes training categories, not the basic directive threshold.",
        ),
        item(
            "Which room preparation is appropriate before inpatient iodine-131 therapy?",
            [
                "Post radiation and no-housekeeping signs, place waste containers inside, and cover frequently touched surfaces",
                "Keep radioactive waste containers outside the room so housekeeping can remove them without entering",
                "Place linen and trash hampers in the hallway",
                "Leave the room unchanged and survey only after discharge",
            ],
            "A",
            "The room is prepared before dosing to control contamination: post the required signs, retain linen and waste inside, and cover frequently touched surfaces. These controls reduce spread and unnecessary staff exposure.",
        ),
        item(
            "A hospitalized iodine-131 therapy patient develops cardiac arrest. What is the first priority?",
            [
                "Provide emergency medical care using appropriate barriers and facility protocols",
                "Wait for the patient to meet release criteria so emergency staff are not exposed during resuscitation",
                "Complete a contamination survey before beginning CPR",
                "Move all emergency equipment out of the room",
            ],
            "A",
            "Immediate life-saving care takes priority. Staff should use barriers and radiation-safety precautions when feasible, but restrictions should not delay treatment of imminent death or severe harm.",
        ),
        item(
            "Which visitor policy is appropriate for a hospitalized iodine-131 therapy patient?",
            [
                "Exclude pregnant visitors and minors, and limit duration while maximizing distance",
                "Permit unrestricted visits by adults if they wear a surgical mask and remain on the opposite side of the bed",
                "Allow minors but prohibit adults older than 65",
                "Require all visitors to remain within 1 meter for accurate monitoring",
            ],
            "A",
            "Typical controls prohibit pregnant visitors and visitors younger than 18, limit visits to about 30 minutes, and maintain approximately 6 feet of distance. Local rules may be more restrictive.",
        ),
        item(
            "A daily survey measures 7 mrem/hour at 1 meter from an inpatient iodine-131 patient's chest. How should this result be interpreted?",
            [
                "It generally meets the dose-rate criterion for discharge, subject to facility and state requirements",
                "It requires continued hospitalization until the reading falls below 2 mrem per hour at the room doorway",
                "It exceeds the Yellow-III package limit",
                "It permits discharge only if no written instructions are provided",
            ],
            "A",
            "A reading of 7 mrem/hour or less at 1 meter is generally consistent with the iodine-131 release criterion cited in the document. Release still requires assessment of likely dose to others and applicable local requirements.",
        ),
        item(
            "When may a patient containing radioactive material be released from licensee control?",
            [
                "When dose to any other individual is not likely to exceed 500 mrem, or an applicable activity or dose-rate criterion is met",
                "Only after all measurable activity has decayed to background at both the patient's surface and 1 meter",
                "Whenever the patient requests discharge",
                "Only when the dose rate at contact is below background",
            ],
            "A",
            "Release is based on limiting likely dose to another person to 500 mrem (5 mSv), with radionuclide-specific activity or dose-rate criteria available as alternatives. Zero measurable activity is not required.",
        ),
        item(
            "When must a released patient receive written instructions for limiting dose to others?",
            [
                "When another individual's dose could exceed 100 mrem (1 mSv)",
                "Only when another individual's dose could exceed 500 mrem",
                "Only after iodine-131 therapy above 33 mCi",
                "Whenever any diagnostic tracer is administered",
            ],
            "A",
            "Written ALARA instructions are required if dose to another person could exceed 100 mrem. The 500-mrem value is the upper release criterion, so the instruction threshold is intentionally lower.",
        ),
        item(
            "How must licensed material in a hot lab or imaging area be secured?",
            [
                "In a locked area or under constant surveillance",
                "By posting a radiation sign and maintaining a written inventory even when the area remains unlocked",
                "By storing it beside the dose calibrator",
                "By documenting it in the annual audit",
            ],
            "A",
            "Licensed material must be protected against unauthorized access, either in locked storage or under constant surveillance. A sign or inventory record alone does not physically secure it.",
        ),
        item(
            "How often must personnel caring for patients who cannot be released receive radiation-safety instruction?",
            [
                "Initially and at least annually",
                "Every 3 years, coordinated with retention of written-directive and survey records",
                "Only after an incident or a substantial change in the patient's treatment plan",
                "Once at initial employment, with later instruction required only for authorized users",
            ],
            "A",
            "Instruction is required initially and at least annually. It covers patient and visitor control, contamination and waste, and notification of the RSO and authorized user during an emergency or death.",
        ),
        item(
            "Which arrangement is acceptable for a patient who cannot be released after unsealed-material therapy?",
            [
                "A private room with a private sanitary facility, or a room shared with another unreleasable therapy patient",
                "Any semiprivate room if a portable shield separates the patient from an untreated roommate",
                "A public waiting area with a portable shield",
                "A room shared with an unexposed pediatric patient",
            ],
            "A",
            "The patient should occupy a private room with a private sanitary facility or share only with another patient who received similar therapy and also cannot be released. Room signage and visitor controls are also required.",
        ),
        item(
            "An item is removed from the room of a patient who cannot be released. How should it be handled?",
            [
                "Survey it and release it only if indistinguishable from background, or manage it as radioactive waste",
                "Release it after wiping it with disinfectant if no visible liquid or patient-identifying material remains",
                "Treat it as ordinary waste if it has no visible contamination",
                "Store it for exactly 24 hours regardless of radionuclide",
            ],
            "A",
            "Items leaving the room must be monitored; if radioactivity is distinguishable from background, they are controlled as radioactive waste. Visual inspection or a fixed waiting period is not a substitute for measurement.",
        ),
        item(
            "What is the maximum molybdenum-99 breakthrough permitted in technetium-99m eluate for human administration?",
            [
                "0.15 microcurie of molybdenum-99 per millicurie of technetium-99m",
                "0.02 microcurie of molybdenum-99 per millicurie of technetium-99m",
                "0.2 microcurie of molybdenum-99 per millicurie of technetium-99m",
                "1 microcurie of molybdenum-99 per millicurie of technetium-99m",
            ],
            "A",
            "The molybdenum-99 limit is 0.15 microcurie per millicurie of technetium-99m. The 0.02 and 0.2 values apply to strontium-82 and strontium-85 breakthrough, respectively, in rubidium-82 eluate.",
        ),
        item(
            "When should strontium-82 and strontium-85 breakthrough be measured for a rubidium-82 generator?",
            [
                "Before the first patient of the day",
                "After the last patient of the week",
                "Only when image quality deteriorates",
                "At annual license renewal",
            ],
            "A",
            "Parent and contaminant strontium concentrations are checked before the first patient each day. This prevents administration of eluate that exceeds breakthrough limits. Waiting until the end of the day would allow every patient that day to receive an unverified product.",
        ),
        item(
            "An eluate exceeds an applicable radionuclide breakthrough limit. What reporting is required?",
            [
                "Telephone reporting within 7 calendar days and a written report within 30 calendar days",
                "Telephone reporting by the next calendar day followed by a written report within 15 calendar days",
                "A written report at the next annual audit",
                "No report if no patient received the eluate",
            ],
            "A",
            "The licensee reports the excessive measurement by telephone within 7 calendar days and submits a written report within 30 days. The written report addresses corrective action, cause, and patient dose assessment when applicable.",
        ),
        item(
            "How long must the licensee retain records of RSO authority and radiation-protection-program changes?",
            ["1 year", "3 years", "5 years", "Only until the next inspection"],
            "C",
            "Records documenting RSO authority and radiation-program changes are retained for 5 years. Many operational records, including written directives, surveys, calibrations, dosage determinations, and leak tests, are retained for 3 years.",
        ),
        item(
            "Which record is generally retained for 3 years?",
            [
                "A written directive",
                "The original radioactive-materials license only until renewal",
                "An RSO program-change record",
                "An employee's Social Security card",
            ],
            "A",
            "Copies of written directives are retained for 3 years, as are many calibration, survey, dosage, release, leak-test, and inventory records. RSO authority and program-change records have a 5-year retention period.",
        ),
        item(
            "Licensed material is discovered missing, and exposure to people in unrestricted areas appears possible. What is required?",
            [
                "Prompt telephone notification to the NRC followed by a written report within 30 days",
                "An internal incident report followed by notification only if a member of the public later receives a confirmed dose",
                "A written report after the next semiannual inventory",
                "Notification only if a member of the public reports symptoms",
            ],
            "A",
            "Potentially consequential lost, stolen, or missing licensed material requires telephone reporting, followed by a detailed written report within 30 days describing the material, circumstances, possible exposures, recovery efforts, and preventive measures. An internal incident report alone is insufficient when exposure in unrestricted areas appears possible.",
        ),
        item(
            "A licensee learns that an occupational or public dose limit was exceeded. By when is the written regulatory report required?",
            ["Within 24 hours", "Within 7 days", "Within 30 days", "At the next license renewal"],
            "C",
            "The document requires a written report within 30 days after learning of an excess occupational, fetal, minor, or public dose, as well as specified excessive emissions or area radiation levels. The deadline differs from next-day telephone reporting used for certain medical or fetal events.",
        ),
    ],
    7: [
        item(
            "Which combination is required for an administration error to meet the general NRC definition of a medical event?",
            [
                "A specified dose consequence threshold is exceeded and at least one qualifying error criterion is met",
                "Any deviation from the prescription, even if clinically insignificant",
                "Patient harm is confirmed by an independent consultant and the administered activity differs by at least 5%",
                "The authorized user requests that the event be reported",
            ],
            "A",
            "A medical event requires both parts of the definition: the administration must create a specified dose consequence and a qualifying error must also occur, such as a 20% dosage deviation, wrong drug, route, patient, body site, or leaking treatment source. Demonstrated injury is not required.",
        ),
        item(
            "Which dose consequence can satisfy the first part of the medical-event definition?",
            [
                "More than 5 rem effective dose equivalent",
                "More than 100 mrem to any monitored worker",
                "Any detectable dose to the skin",
                "A transport index greater than 1",
            ],
            "A",
            "The consequence thresholds include more than 5 rem effective dose equivalent, 50 rem to an organ or tissue, or 50 rem shallow dose to skin. Package transport indices and routine worker-monitoring levels are unrelated.",
        ),
        item(
            "An administered dosage differs from the prescribed dosage by 22%, but the resulting dose is below every medical-event consequence threshold. Is it a medical event under the two-part definition?",
            [
                "Yes, because any dosage difference of at least 20% is sufficient even when all dose consequence thresholds remain below the reporting levels",
                "No, because the dose consequence threshold and a qualifying error must both be present",
                "Yes, but only if the dosage was too high",
                "No, because dosage deviations are never reportable",
            ],
            "B",
            "A deviation of at least 20% is one qualifying error, but it does not by itself satisfy the definition. At least one specified dose consequence threshold must also be exceeded.",
        ),
        item(
            "Which administration error is specifically included among the qualifying medical-event criteria?",
            [
                "Giving the correct drug by the prescribed route 10 minutes late",
                "Giving the radioactive drug to the wrong individual",
                "Repeating an image because of patient motion",
                "Using a different syringe manufacturer",
            ],
            "B",
            "Administration to the wrong individual is a qualifying criterion. Other listed criteria include wrong drug, wrong route, dosage off by at least 20%, wrong body part with sufficient excess dose, and a leaking treatment source.",
        ),
        item(
            "What does designation as a medical event imply about patient harm?",
            [
                "It proves that permanent injury occurred",
                "It identifies a significant administration or quality-assurance problem but does not by itself prove harm",
                "It means the patient received no therapeutic benefit",
                "It applies only when an independent medical consultant confirms that the error caused a permanent clinical injury",
            ],
            "B",
            "The designation identifies a regulatory problem in the use of radioactive material. The authorized user must separately evaluate clinical harm, which may arise from excessive dose or from undertreatment; harm is not assumed from the label alone.",
        ),
        item(
            "Which factor is most important when deciding whether a spill should be managed as major or minor?",
            [
                "The physical size of the wet area, regardless of radionuclide, activity, affected people, or the likelihood of spread",
                "Activity and radiotoxicity together with spread, affected people, surfaces, and other hazards",
                "Whether the spill occurred during business hours",
                "Whether the radionuclide emits visible light",
            ],
            "B",
            "The decision uses isotope-specific activity guidance plus incident context, including radiotoxicity, potential spread, number of people affected, contaminated surfaces, and competing hazards. Area alone is not enough.",
        ),
        item(
            "What may be the safest management for a contained spill of a very short-lived radionuclide when immediate cleanup would increase exposure?",
            [
                "Restrict access and allow the activity to decay",
                "Spread the material over a larger area",
                "Dilute it into the sanitary sewer regardless of quantity",
                "Remove all shielding to speed physical decay",
            ],
            "A",
            "For selected short-lived spills, isolating the area until decay may produce less exposure and contamination spread than immediate cleanup. Shielding does not alter half-life, and uncontrolled dilution or spreading is inappropriate.",
        ),
        item(
            "What is the first action for a major radioactive spill when there is no immediate medical emergency?",
            [
                "Begin scrubbing from the center outward",
                "Clear uninvolved people from the area",
                "Carry contaminated objects to the hot lab",
                "Measure every person's dosimeter before restricting access",
            ],
            "B",
            "The major-spill sequence begins by clearing the area, then preventing spread, shielding if safe, securing the room, and calling the RSO. Unsupervised cleanup can spread contamination and increase exposure.",
        ),
        item(
            "After a major spill is covered with absorbent material, what should staff do next?",
            [
                "Immediately mop the area from the center outward before contamination can dry or move beyond the absorbent paper",
                "Limit movement of potentially contaminated personnel and secure the room",
                "Remove the absorbent paper to inspect the floor",
                "Send everyone home without monitoring",
            ],
            "B",
            "Covering the spill helps prevent spread, but staff should not attempt major-spill cleanup without RSO direction. Movement is limited, the room is secured, and the RSO is notified immediately.",
        ),
        item(
            "How should contaminated skin be decontaminated after a major spill?",
            [
                "Scrub vigorously with hot water and an abrasive cleanser",
                "Flush with lukewarm water and wash gently with mild soap",
                "Apply bleach and cover tightly",
                "Wait for physical decay without washing",
            ],
            "B",
            "Gentle washing with lukewarm water and mild soap limits skin injury, which could increase uptake. If contamination persists, controlled perspiration under plastic may be used before washing again under expert guidance.",
        ),
        item(
            "Which action belongs in the response to a minor spill?",
            [
                "Clean with disposable gloves and absorbent material, then survey the area and yourself",
                "Evacuate the entire building and leave the spill uncovered until a federal response team arrives",
                "Leave the spill uncovered until the RSO arrives",
                "Discard contaminated supplies in ordinary trash",
            ],
            "A",
            "For a minor spill, notify nearby people, cover and clean it with disposable materials, bag waste as radioactive, survey the area and personnel, report to the RSO, and document the incident. Unlike a major spill, trained staff may perform this limited cleanup rather than securing the room and waiting for RSO-supervised decontamination.",
        ),
        item(
            "When folding absorbent paper used to clean a minor radioactive spill, which surface should face outward?",
            ["The contaminated surface", "The clean surface", "Either surface if gloves are worn", "The wettest surface"],
            "B",
            "The paper is folded with the clean side outward to contain contamination, then placed with gloves and other disposable materials in a labeled bag for radioactive waste. Folding the contaminated surface outward would spread activity to gloves, the bag exterior, and surrounding surfaces.",
        ),
        item(
            "How is removable surface contamination measured?",
            [
                "By holding a calibrated exposure-rate survey meter 1 meter above the surface and recording the highest reading",
                "By wiping a defined area and counting the wipe with an instrument of known efficiency",
                "By reading the worker's whole-body dosimeter",
                "By calculating ten physical half-lives",
            ],
            "B",
            "A wipe test samples removable contamination from a known area, commonly 100 square centimeters, and the sample is measured with an appropriate detector whose efficiency is known. A survey-meter reading above the surface measures a radiation field and cannot by itself quantify removable contamination in dpm per area.",
        ),
        item(
            "Which restricted-area removable-contamination limit is paired correctly with the radionuclide group?",
            [
                "Alpha emitters: 200 dpm per 100 square centimeters",
                "Technetium-99m: 200 dpm per 100 square centimeters",
                "Iodine-131: 20,000 dpm per 100 square centimeters",
                "Gallium-67: 2,000 dpm per 100 square centimeters",
            ],
            "A",
            "The table lists 200 dpm/100 cm2 for alpha emitters, 2,000 for indium-111, iodine-123, iodine-131, lutetium-177, and yttrium-90, and 20,000 for gallium-67, technetium-99m, and thallium-201. The lower alpha limit reflects the greater hazard from alpha contamination, so the numerical groups should not be interchanged.",
        ),
        item(
            "A patient with life-threatening trauma may also be contaminated with radioactive material. What is the first priority?",
            [
                "Complete full-body decontamination and identify the radionuclide before allowing emergency personnel to begin treatment",
                "Treat the life- or limb-threatening condition while using reasonable contamination controls",
                "Wait until the radionuclide is identified",
                "Transfer the patient only after the dose rate reaches background",
            ],
            "B",
            "Emergency medical care takes priority. Responders should be informed and use practical exposure and contamination controls, but radiation concerns should not delay life- or limb-saving treatment.",
        ),
        item(
            "Which statement best distinguishes a radiological dispersal device from a nuclear weapon?",
            [
                "An RDD uses a conventional explosive to spread radioactive material and does not create a nuclear detonation",
                "An RDD produces a nuclear chain reaction but is designed to limit blast damage while maximizing radioactive fallout",
                "An RDD exposes an entire continent to lethal fallout",
                "An RDD contains no radioactive material",
            ],
            "A",
            "A dirty bomb or RDD combines conventional explosives with radioactive material. Its likely principal effects are blast injury, localized contamination, disruption, and anxiety, not a nuclear chain-reaction explosion.",
        ),
        item(
            "What most strongly determines the local contamination pattern after an RDD explosion?",
            [
                "Explosive size, radionuclide type and quantity, dispersal method, and weather",
                "The age, height, and construction materials of nearby buildings, independent of weather or the radioactive source",
                "The number of radiation workers in the area",
                "Whether the material was previously used in medicine",
            ],
            "A",
            "Contamination depends on the explosive, radioactive inventory, dispersal mechanism, and weather. Prompt isotope identification helps authorities select protective actions such as sheltering or evacuation. Building characteristics may influence local deposition, but they cannot replace the source and weather factors in the initial assessment.",
        ),
        item(
            "Which set lists the core protective actions for a radiological emergency?",
            [
                "Reduce time, increase distance, and use shielding or respiratory protection as appropriate",
                "Increase time, reduce distance, and remove shielding",
                "Rely only on personal dosimeters",
                "Wait for symptoms before leaving the area",
            ],
            "A",
            "Protection follows the familiar time-distance-shielding framework, with respiratory or contamination controls when internal exposure is possible. Dosimeters provide information but do not themselves reduce dose.",
        ),
        item(
            "Which exposure pattern is consistent with acute radiation syndrome?",
            [
                "An acute dose above about 0.7 Gy delivered rapidly to most of the body by penetrating radiation",
                "A small chronic dose limited to one fingertip",
                "Internal contamination with no significant absorbed dose",
                "A diagnostic chest radiograph",
            ],
            "A",
            "ARS requires a sufficiently high, rapidly delivered, penetrating dose to a large portion of the body, generally more than 70%. Local or low-dose exposures do not produce the classic whole-body syndrome.",
        ),
        item(
            "What is the usual sequence of acute radiation syndrome phases?",
            [
                "Prodromal, latent, manifest illness, then recovery or death",
                "Latent, prodromal, recovery, then manifest illness",
                "Manifest illness, latent, prodromal, then recovery",
                "Prodromal, recovery, latent, then manifest illness",
            ],
            "A",
            "ARS progresses through a prodromal phase, a latent interval, manifest illness, and then recovery or death. Higher doses shorten the intervals and worsen symptoms. The temporary improvement during the latent phase does not mean the injury has resolved; organ-specific illness follows.",
        ),
        item(
            "Which acute radiation subsyndrome is caused primarily by injury to bone marrow precursor cells?",
            ["Hematopoietic", "Gastrointestinal", "Neurovascular", "Cutaneous only"],
            "A",
            "The hematopoietic subsyndrome reflects marrow injury and loss of blood-cell production. Gastrointestinal and neurovascular syndromes occur at progressively higher doses and involve different critical tissues.",
        ),
        item(
            "What is the approximate LD50/60 for acute whole-body low-LET irradiation without medical intervention?",
            ["0.7-1 Gy", "3.5-4 Gy", "7-9 Gy", "15-20 Gy"],
            "B",
            "Without medical intervention, the estimated LD50/60 is about 3.5 to 4 Gy. Antibiotics and supportive care can raise survival, and intensive care with advanced hematologic support may raise it further.",
        ),
        item(
            "Which FDA-approved treatment supports neutrophil recovery in hematopoietic acute radiation syndrome?",
            ["Filgrastim", "Potassium iodide", "Prussian blue", "Calcium gluconate"],
            "A",
            "Filgrastim and pegfilgrastim stimulate neutrophil recovery; sargramostim supports additional marrow lineages. Potassium iodide and Prussian blue are decorporation or blocking agents for selected internal contaminants, not general ARS marrow treatment.",
        ),
        item(
            "Which agent promotes megakaryocyte and platelet recovery in acute radiation syndrome?",
            ["Romiplostim", "Filgrastim", "Atropine", "Naloxone"],
            "A",
            "Romiplostim is a thrombopoietin-receptor agonist that promotes megakaryocytes and platelets. Colony-stimulating factors such as filgrastim primarily support neutrophil recovery. Potassium iodide and Prussian blue address selected internal radionuclide exposures rather than radiation-induced thrombocytopenia.",
        ),
    ],
    8: [
        item(
            "What does a Geiger-Mueller survey meter primarily report?",
            [
                "The number of detected events, commonly displayed as counts per minute",
                "The radionuclide's photon energy spectrum with enough resolution to identify each photopeak",
                "The patient's organ absorbed dose",
                "The chemical identity of the radioactive compound",
            ],
            "A",
            "A GM detector produces a count for each detected ionizing event and is commonly used for contamination surveys. It does not reliably identify radionuclide energy or directly calculate patient organ dose.",
        ),
        item(
            "Why can a Geiger-Mueller meter detect contamination but not reliably identify the radionuclide?",
            [
                "Its gas amplification produces similar output pulses regardless of the original particle energy",
                "It contains no gas",
                "It responds only to visible light",
                "It preserves pulse height only after the sample has been chemically separated into individual radionuclides",
            ],
            "A",
            "In the Geiger region, each event triggers a large discharge, so pulse size no longer preserves the incident radiation energy. The detector is useful for counting events but not spectroscopy.",
        ),
        item(
            "Which instrument is best suited to measuring low levels of radioactivity in a blood, urine, or wipe sample?",
            ["Well counter", "Pocket ion chamber", "Dose calibrator", "Film badge"],
            "A",
            "A well counter surrounds the sample with a scintillation detector, providing high efficiency for small specimens and wipes. A dose calibrator measures much larger activities in radiopharmaceutical containers.",
        ),
        item(
            "What detector is commonly used in a gamma well counter?",
            [
                "Sodium iodide activated with thallium coupled to a photomultiplier tube",
                "A lead plate coupled to a thermometer that converts absorbed energy directly into counts",
                "An unshielded photographic film read continuously by an optical photomultiplier",
                "A plastic ion chamber filled with water and operated in the Geiger discharge region",
            ],
            "A",
            "A NaI(Tl) crystal converts gamma interactions into light, and a photomultiplier tube converts and amplifies that light into electrical pulses. This arrangement provides sensitive gamma counting.",
        ),
        item(
            "What capability does a multichannel analyzer add to a scintillation well counter?",
            [
                "It sorts pulses by energy, allowing energy-window selection and radionuclide discrimination",
                "It automatically corrects counting geometry and sterilizes the specimen before gross activity is measured",
                "It measures only total counts with no energy information",
                "It converts gamma radiation into beta radiation",
            ],
            "A",
            "A multichannel analyzer bins pulses by energy. Energy windows improve selectivity for a radionuclide and help reject scatter or other energies, unlike a simple gross-count display.",
        ),
        item(
            "Why should a highly active sample not be placed directly into a well counter designed for low-level samples?",
            [
                "Excessive count rate can cause dead-time losses and inaccurate results",
                "The sample's physical half-life will increase",
                "The sodium iodide crystal will convert the sample to a sealed source",
                "High activity prevents any ionization from occurring",
            ],
            "A",
            "Well counters are extremely sensitive but have limited count-rate capability; activity around or above 37 kBq (0.001 mCi) can produce dead-time errors. High-activity radiopharmaceutical doses belong in a dose calibrator.",
        ),
        item(
            "Which measurement is a liquid scintillation counter particularly suited to?",
            [
                "Low-level alpha or beta activity in a liquid sample",
                "Exposure rate outside a patient room",
                "Activity in a therapeutic iodine capsule before administration to a patient",
                "Transport index at 1 meter",
            ],
            "A",
            "Liquid scintillation counting is highly sensitive for low-energy beta and alpha emitters mixed with scintillation cocktail. External exposure rate and clinical-dose activity require different instruments.",
        ),
        item(
            "How does an ionization chamber measure radiation?",
            [
                "It collects charge from ion pairs produced in a gas between electrodes",
                "It counts light flashes from a scintillation crystal and sorts each pulse into a photon-energy channel",
                "It records radiation-induced darkening on film only",
                "It measures radioactive decay by weighing the sample",
            ],
            "A",
            "Radiation ionizes gas in the chamber, and an electric field collects the resulting charge as a current. Chamber geometry and electronics determine whether it functions as a survey meter, dosimeter, or dose calibrator.",
        ),
        item(
            "What distinguishes a dose calibrator from a portable ion-chamber survey meter?",
            [
                "A dose calibrator is a shielded well-type ion chamber calibrated to report activity for selected radionuclides",
                "A dose calibrator identifies unknown radionuclides by chemical analysis and high-resolution photon spectroscopy",
                "A dose calibrator measures only removable surface contamination",
                "A dose calibrator contains a Geiger-Mueller tube and reports counts per minute",
            ],
            "A",
            "A dose calibrator uses a sealed well ionization chamber and radionuclide-specific calibration settings to measure activity in vials, syringes, or capsules. A survey meter is optimized for radiation field measurements.",
        ),
        item(
            "Which instrument would best measure the exposure rate outside an iodine-131 therapy room?",
            [
                "Portable ionization-chamber survey meter",
                "Gamma well counter configured to report the total counts in a blood, urine, or wipe sample",
                "Liquid scintillation counter optimized for low-energy beta activity in a prepared liquid sample",
                "Radio-thin-layer chromatography scanner used to compare activity in separated chemical species",
            ],
            "A",
            "A portable ion chamber is appropriate for exposure-rate measurements in a radiation field. Well counters and liquid scintillation counters measure samples, while radio-TLC evaluates radiochemical composition.",
        ),
        item(
            "What question does radio-thin-layer chromatography answer during radiopharmaceutical quality control?",
            [
                "What fraction of the measured activity is present in the desired chemical form?",
                "What is the external dose rate at 1 meter from the patient or radiopharmaceutical container?",
                "How much occupational dose did a technologist receive this month?",
                "Is a shipping package contaminated on its exterior?",
            ],
            "A",
            "Radio-TLC separates chemical species and measures their associated activity, allowing calculation of radiochemical purity or reaction conversion. It does not replace radiation surveys or personnel monitoring.",
        ),
        item(
            "Why is radio-thin-layer chromatography often preferred over radio-HPLC for routine checks involving only a few expected species?",
            [
                "It is simpler and faster while providing adequate separation for the intended check",
                "It always provides greater chemical resolution and more precise species identification than a validated radio-HPLC method",
                "It requires no quality-control procedure",
                "It directly measures patient absorbed dose",
            ],
            "A",
            "For simple systems with a small number of expected species, radio-TLC is quick and practical. Radio-HPLC can provide greater analytical detail but is more complex and may not be necessary for routine kit checks.",
        ),
    ],
}
