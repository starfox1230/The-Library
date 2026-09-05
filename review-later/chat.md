# Standing instructions

These are cards I marked Review Later while doing normal Anki reviews.

Speed Streak intentionally lets me defer deeper thinking so I do not interrupt a fast review session. I flagged these cards because something about the concept, wording, card design, or my understanding deserved attention.

Go through the flagged cards with me conversationally. For each item, help me determine why I likely flagged it and whether any action is needed. Consider:

- Is there a conceptual misunderstanding that needs clarification?
- Is the existing card poorly worded or ambiguous?
- Does the card need additional context?
- Should the card be simplified or split?
- Should a new clarifying card be created?
- Is the card redundant or low-value?
- Should it be deleted or suspended?
- Is the card actually fine, and I simply needed an explanation?
- Does something require further reading or verification?

Do not merely quiz me on the cards. The purpose is to process the deferred problems I noticed during Anki review.

Throughout the conversation, keep a running action list. At the end, organize the results into:

EDIT EXISTING CARDS
- Specific changes that should be made to existing cards.

CREATE NEW CARDS
- New cards or clarifying cards that should be created.

DELETE / SUSPEND
- Cards that are redundant, misleading, low-value, or should otherwise be removed from active review.

CONCEPTS CLARIFIED — NO CARD CHANGE
- Things I misunderstood or needed explained, but where the existing card is acceptable.

NEEDS FURTHER RESEARCH
- Items that require checking a source or learning more before changing anything.

NO ACTION
- Flagged cards that ultimately need no change.

Be flexible if the conversation reveals another useful category or task.

---

# Anki Speed Streak — Review Later

Updated: 2026-09-05 07:16 Central Daylight Time
Cards: 15

## Card 1

Deck: Saved Cards
Flagged: 2026-08-12T20:19:09-05:00
Last seen: 2026-09-05T07:15:42-05:00
Card ID: 1786559000557
Note ID: 1786559000556

Question:
00:12

An acute fracture of the posterolateral talar process is a [...].

Answer:
00:12

An acute fracture of the posterolateral talar process is a Shepherd fracture.

This is traumatic rather than an unfused ossification center.

Source: Notion Radiology entry.

## Card 2

Deck: .NEW::Visual
Flagged: 2026-09-05T07:01:12-05:00
Last seen: 2026-09-05T07:01:12-05:00
Card ID: 1783397643310
Note ID: 1783397643309

Question:
00:12

Most likely diagnosis?

[...]

Answer:
00:12

Most likely diagnosis?

Necrotizing fasciitis -- Soft-tissue gas in the medial thigh

Core Radiology 2nd ed., MSK: 980. Gas bubbles in soft tissues on radiograph or CT are the characteristic imaging clue.

Full source page:

## Card 3

Deck: .NEW::Visual
Flagged: 2026-07-06T06:36:12-05:00
Last seen: 2026-09-05T06:59:46-05:00
Card ID: 1775676310599
Note ID: 1775676310599

Question:
html { overflow: scroll; overflow-x: hidden; }
.card {
	font-family: Menlo, baskerville, adobe caslon pro, sans;
	text-align: center;
	color: #D7DEE9; /*dark #A6ABB9 light #D7DEE9*/
	line-height: 1.6em;
	background-color: #333B45;
}
#kard {
	padding: 0px 0px;
	background-color:;
	max-width: 700px;
	margin: 0 auto;
	word-wrap: break-word;
}
.tags { color: #F87b57; opacity: 0; font-size: 10px; background-color: ; width: 100%; height: ; text-align: center; text-transform: uppercase; position: fixed; padding: 0px; top:0; left: 0; right 0;}
.tags:active { opacity: 1; position: fixed; cursor: pointer;} .tags:hover { cursor: pointer;}
tr {font-size: 12px; }
b { color: IndianRed !important; }
u { text-decoration: none; color: #5EB3B3;}
a { color: LightGray !important; text-decoration: none; font-size: 10px; font-style: normal;  }
::-webkit-scrollbar {
    /*display: none;   remove scrollbar space */
    background: #fff;   /* optional: just make scrollbar invisible */
    width: 0px; }
::-webkit-scrollbar-thumb { background: #bbb; }
/* mobile is both iphone and ipad */
.mobile .tags:hover { opacity: 1; position: relative;}
/* OCCLUSION CSS START - don't edit this */
#io-overlay {
  position:absolute;
  top:0;
  width:100%;
  z-index:3
}
#io-original {
  position:relative;
  top:0;
  width:100%;
  z-index:2
}
#io-wrapper {
  position:relative;
  width: 100%;
}
/* OCCLUSION CSS END */
/* OTHER STYLES */
#io-header{
  font-size: 14px;
  margin-bottom: 10px;
}
#io-footer{
  max-width: 80%;
  margin-left: auto;
  margin-right: auto;
  margin-top: 0.8em;
margin-bottom: 0.8em;
  font-style: italic;
 font-size: 14px;
}
#io-extra-wrapper{
  /* the wrapper is needed to center the
  left-aligned blocks below it */
  width: 80%;
  margin-left: auto;
  margin-right: auto;
  margin-top: 0.5em;
}
#io-extra{
  text-align:center;
  display: inline-block;
}
.io-extra-entry{
  margin-top: 0.8em;
  font-size: 14px;
  text-align:left;
}
.io-field-descr{
  margin-bottom: 0.2em;
  font-weight: bold;
  font-size: 14px;
}
#io-revl-btn {
  font-size: 12px;
	margin-top: 15px;
    background-color: #333B45; /*#4CAF50;  Green */
    border: solid #A6ABB9 2px;
    color: #A6ABB9;
    text-align: center;
    text-decoration: none;
    display: inline-block;
	font-family: Menlo, sans;
border-radius: 0px;
}
#io-revl-btn:hover {
background-color: ;/* #cccccc;  Green */
    color: ;
cursor: pointer;
}
function countdown( elementName, minutes, seconds )
{
    var element, endTime, hours, mins, msLeft, time;
    function twoDigits( n )
    {
        return (n <= 9 ? "0" + n : n);
    }
    function updateTimer()
    {
        msLeft = endTime - (+new Date);
        if ( msLeft < 1000 ) {
            element.innerHTML = "<span style='color:#CC5B5B'>TIME</span>";
        } else {
            time = new Date( msLeft );
            hours = time.getUTCHours();
            mins = time.getUTCMinutes();
            element.innerHTML = (hours ? hours + ':' + twoDigits( mins ) : mins) + ':' + twoDigits( time.getUTCSeconds() );
            setTimeout( updateTimer, time.getUTCMilliseconds() + 500 );
        }
    }
    element = document.getElementById( elementName );
    endTime = (+new Date) + 1000 * (60*minutes + seconds) + 500;
    updateTimer();
}
countdown("s2", 0, 10 ); //2nd value is the minute, 3rd is the seconds

Answer:
SHOW ALL

## Card 4

Deck: .NEW::Audio
Flagged: 2026-09-04T12:42:43-05:00
Last seen: 2026-09-05T06:56:57-05:00
Card ID: 1782588006937
Note ID: 1782588006936

Question:
00:12

Pseudopermeative bone appearance extending to the cortex suggests benign entities such as [...].

Answer:
00:12

Pseudopermeative bone appearance extending to the cortex suggests benign entities such as osteoporosis or osseous hemangioma.

Source Core Radiology, 2nd edition, section 13.03, Bone Tumors, printed pages MSK 934-936.

Periosteal reaction morphology, margin analysis, matrix, age, and location were selected as board-relevant discriminators for nonspecific bone lesions.

## Card 5

Deck: Saved Cards
Flagged: 2026-09-05T06:54:07-05:00
Last seen: 2026-09-05T06:54:07-05:00
Card ID: 1785498425560
Note ID: 1785498425559

Question:
00:12

How should the focal CTA appearance of an ulcer-like projection be described?

[...]

Answer:
00:12

How should the focal CTA appearance of an ulcer-like projection be described?

Contrast outpouching

Reworked from user-selected existing Anki notes. Diagnosis recognition and exact radiologic phrase retrieval are tested on separate cards.

## Card 6

Deck: .NEW::Visual
Flagged: 2026-09-05T05:20:27-05:00
Last seen: 2026-09-05T06:51:12-05:00
Card ID: 1783397643260
Note ID: 1783397643259

Question:
00:12

What do the red arrows indicate on these MRI images?

[...]

Answer:
00:12

What do the red arrows indicate on these MRI images?

Enlarged median nerve with fat interdigitating between fascicles

Core Radiology 2nd ed., MSK: 964. Fat interdigitating between nerve fascicles is pathognomonic for fibrolipomatous hamartoma.

Full source page:

## Card 7

Deck: .NEW::Audio
Flagged: 2026-09-05T05:23:58-05:00
Last seen: 2026-09-05T05:23:58-05:00
Card ID: 1744132293503
Note ID: 1744132293503

Question:
00:12

What is the most common underlying cause of Budd-Chiari syndrome?

[...]

Answer:
00:08

What is the most common underlying cause of Budd-Chiari syndrome?

Intrinsic webs within the hepatic veins or IVC

Explanation: While hypercoagulable states are a significant cause, membranous webs obstructing outflow are considered the most common etiology globally, particularly in certain regions.

## Card 8

Deck: .NEW::Visual
Flagged: 2026-09-03T05:33:26-05:00
Last seen: 2026-09-05T05:10:30-05:00
Card ID: 1779059682569
Note ID: 1779059682568

Question:
00:12

39-year-old female with a history of non-Hodgkin’s lymphoma who completed several cycles of chemotherapy two weeks ago. Most likely diagnosis?

[...]

Answer:
00:12

39-year-old female with a history of non-Hodgkin’s lymphoma who completed several cycles of chemotherapy two weeks ago. Most likely diagnosis?

marrow stimulation in setting of colony-stimulating factors

Q1. Correct; difficulty: moderate. The sagittal positron-emission tomography (PET) shows diffuse marrow uptake of fluorodeoxyglucose (FDG) throughout the spine and sternum (red arrows) as well as several sites of FDG uptake in enlarged abdominal lymph nodes (yellow arrows). Correct answer: Use of colony-stimulating factors.

## Card 9

Deck: Saved Cards
Flagged: 2026-09-05T05:09:58-05:00
Last seen: 2026-09-05T05:09:58-05:00
Card ID: 1787199507850
Note ID: 1787199507848

Question:
00:12

Area postrema involvement in aquaporin-4-positive NMOSD can cause [what classic symptoms].

Answer:
00:12

Area postrema involvement in aquaporin-4-positive NMOSD can cause intractable nausea and vomiting/hiccups.

Area postrema involvement produces a characteristic dorsal medullary or floor-of-the-fourth-ventricle T2 abnormality.

Source: Notion Radiology entry.

## Card 10

Deck: .Core Backlog
Flagged: 2026-09-05T05:01:35-05:00
Last seen: 2026-09-05T05:01:35-05:00
Card ID: 1779914758349
Note ID: 1779914758348

Question:
00:12

A nasal wall mass with a cerebriform enhancement pattern is characteristic of [...].

Answer:
00:12

A nasal wall mass with a cerebriform enhancement pattern is characteristic of inverted papilloma.

Q6. Incorrect; difficulty: hard. The CT demonstrates a mass located in the lateral nasal wall with focal coarse calcifications (yellow arrow), as well as bony resorption and extension into the maxillary sinus (green arrow).

## Card 11

Deck: .NEW::Audio
Flagged: 2026-08-09T22:03:42-05:00
Last seen: 2026-09-05T05:00:48-05:00
Card ID: 1753054854801
Note ID: 1753054854800

Question:
00:12

A Rastelli procedure is used for [...]

Answer:
00:08

A Rastelli procedure is used for d-Transposition of the great arteries with a large VSD and pulmonary outflow obstruction.

## Card 12

Deck: .NEW::Visual
Flagged: 2026-09-02T06:14:33-05:00
Last seen: 2026-09-05T04:57:02-05:00
Card ID: 1760542763450
Note ID: 1760542763450

Question:
00:12

Diagnosis?

[...]

Answer:
00:08

Diagnosis?

lipomyelomeningocele

## Card 13

Deck: .NEW::Audio
Flagged: 2026-09-04T12:51:08-05:00
Last seen: 2026-09-05T04:56:31-05:00
Card ID: 1760561943141
Note ID: 1760561943140

Question:
00:12

Differentiate lipomyelocele from lipomyelomeningocele on imaging.

[...]

Answer:
00:08

Differentiate lipomyelocele from lipomyelomeningocele on imaging.

lipomyelocele = placode-fat interface without CSF sac protruding beyond placode
lipomyelomeningocele = placode-fat interface plus meningeal and CSF protrusion beyond the placode

## Card 14

Deck: .NEW::Visual
Flagged: 2026-08-13T13:19:44-05:00
Last seen: 2026-09-05T04:56:13-05:00
Card ID: 1776199228458
Note ID: 1776199228458

Question:
00:12

Most likely diagnosis?

[...]

Answer:
00:12

Most likely diagnosis?

ameloblastoma

## Card 15

Deck: .NEW::Audio
Flagged: 2026-04-22T07:19:27-05:00
Last seen: 2026-09-05T04:51:31-05:00
Card ID: 1776822423085
Note ID: 1776822423084

Question:
00:12

A classic secondary cardiac MRI sign of constrictive pericarditis is [...] septal bounce.

Answer:
00:12

A classic secondary cardiac MRI sign of constrictive pericarditis is diastolic septal bounce.
