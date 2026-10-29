"""Derive a service-free inline prototype from the rendered synthetic app.

Usage: python dev/make_inline_preview.py ABSOLUTE_THREAD_PREVIEW_PATH
The response fragment is written outside the Library, to the calling chat.
"""
from pathlib import Path
import re
import sys

source = Path(__file__).parent / 'qa-output/preview.html'
destination = Path(sys.argv[1])
assert destination.is_absolute()
html = source.read_text(encoding='utf-8')
css = re.search(r'<style>(.*?)</style>', html, re.S).group(1)
css = css[css.index('#cr-app'):]
# Product colors already use light-dark() with a root-scoped theme override.
# The inline frame grows with content; production sticky behavior is verified
# separately against the actual full-page app, without a surrounding iframe.
css += '\n#cr-app .report-dock {position:static;max-height:none;}\n#cr-app .report-dock .diff-scroll {overflow:visible;min-height:0;}\n'
body = re.search(r'<body>(.*?)</body>', html, re.S).group(1)
start = body.index('async function analyzeCase(')
end = body.index("$('search').addEventListener", start)
body = body[:start] + body[end:]
body = body.replace('if(!syntheticPreview)runQueue();', '')
body = re.sub(r"\$\('report-form'\)\.addEventListener\('submit',.*?\);\nrender\(\);",
              "$('report-form').addEventListener('submit',event=>event.preventDefault());\nrender();", body, flags=re.S)
state_script = r"""
const root=document.getElementById('cr-app');
function restore(state){const s=state?.privateContent;if(!s)return;if(['oldest','newest','major','change-high','change-low'].includes(s.order))$('order').value=s.order;selectedFilters.clear();const filters=Array.isArray(s.filters)?s.filters:[s.filter];for(const key of filters)if(['major','minor','wording','review','pending','none'].includes(key))selectedFilters.add(key);if(typeof s.combinedView==='boolean'){combinedView=s.combinedView;$('combined-view').checked=combinedView;root.classList.toggle('dual-view',combinedView);$('combined-view-value').value=combinedView?'1':'0';}if(typeof s.showReportWording==='boolean'){showReportWording=s.showReportWording;$('report-wording-value').value=showReportWording?'1':'0';}wordingOverrides.clear();for(const entry of (Array.isArray(s.wordingOverrides)?s.wordingOverrides:[]))if(Array.isArray(entry)&&typeof entry[0]==='string'&&/^\d+$/.test(entry[0])&&Number(entry[0])<cases.length&&typeof entry[1]==='boolean')wordingOverrides.set(entry[0],entry[1]);render();}
restore(window.openai?.widgetState);
window.addEventListener('openai:set_globals',event=>restore(event.detail?.globals?.widgetState));
function saveState(){const state={filters:[...selectedFilters],order:$('order').value,combinedView,showReportWording,wordingOverrides:[...wordingOverrides]};window.openai?.setWidgetState?.({modelContent:{prototype:'Case review controls',...state},privateContent:state})?.catch(()=>{});}
for(const id of ['order','combined-view'])$(id).addEventListener('change',saveState);
root.addEventListener('click',event=>{if(event.target.closest('.filter-chip,#reset-filters,.evidence-toggle,.wording-apply-all'))saveState();});
"""
body = re.sub(r'render\(\);\s*\}\)\(\);', lambda _m:
    "combinedView=true;$('combined-view').checked=true;$('combined-view-value').value='1';$('cr-app').classList.add('dual-view');opened.add('0');render();\n" + state_script + '\n})();', body, count=1)
assert 'restore(window.openai?.widgetState)' in body
assert 'fetch(' not in body and 'runQueue(' not in body
with destination.open('w', encoding='utf-8') as stream:
    stream.write('<style>')
    stream.write(css)
    stream.write('</style>\n')
    stream.write(body)
print('Inline prototype updated:', destination)
