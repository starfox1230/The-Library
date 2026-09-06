"""Read-only instruction preflight; no remote calls or card generation."""
import argparse, hashlib, json, sys
from pathlib import Path

GUIDES = Path(__file__).resolve().parents[1]
SCOPES = {
    "notion": ["ANKI_COACHING_WORKFLOW.md", "NIGHTLY_ORCHESTRATION.md"],
    "conversation": ["RADIOLOGY_CONVERSATION_ANKI_WORKFLOW.md"],
    "saved": ["NIGHTLY_ORCHESTRATION.md", "ANKI_COACHING_WORKFLOW.md", "VISUAL_STUDY_AND_ANKI_SPEC.md"],
    "cards": ["NIGHTLY_ORCHESTRATION.md", "ANKI_COACHING_WORKFLOW.md", "VISUAL_STUDY_AND_ANKI_SPEC.md"],
    "nightly": ["NIGHTLY_ORCHESTRATION.md", "ANKI_COACHING_WORKFLOW.md", "VISUAL_STUDY_AND_ANKI_SPEC.md", "CORE_RADIOLOGY_WORKFLOW.md", "BOARDVITALS_WORKFLOW.md"],
}
def inspect(scope):
    names = ["RUN_RADIOLOGY_CARDS.md", "CARD_STYLE_GUIDE.md", "APKG_PACKAGING.md"] + SCOPES[scope]
    records, errors = [], []
    obsolete = "C:" + "\\Users\\sterl\\OneDrive\\Documents\\GitHub\\The-Library"
    for name in names:
        path = GUIDES / name
        if not path.is_file():
            errors.append("Missing required guide: " + str(path))
            continue
        data = path.read_bytes()
        if obsolete in data.decode("utf-8"):
            errors.append("Obsolete repository path in " + name)
        records.append({"name":name,"path":str(path),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data)})
    return {"scope":scope,"guide_root":str(GUIDES),"instructions":records,"errors":errors,
            "meaning":"Availability and file fingerprints only. Read guides, inspect source-specific dependencies and verify remote outputs separately."}
if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope",choices=SCOPES,default="notion")
    args=parser.parse_args()
    result=inspect(args.scope)
    print(json.dumps(result,indent=2))
    sys.exit(bool(result["errors"]))

