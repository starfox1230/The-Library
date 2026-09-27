"""Case-specific landmark regions, authored against the normalized PCIR images.

Coordinates are voxel centres in the shipped SOFT volume, not reusable templates.
Run render_checkpoint_qa.py and inspect every changed region after editing.
"""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'cases/normal-head/manifest.json').read_text())
phases=[]
def phase(label,instruction,seconds):
    phases.append(dict(id=f'phase-{len(phases)+1}',label=label,instruction=instruction,sourceSeconds=seconds,targets=[]))
def target(label,xyz,radii=(4,4),plane='axial',window='brain',span=1,side='midline'):
    p=[m['originLPS'][i]+xyz[i]*m['spacing'][i] for i in range(3)]
    u,v,n= (p[0],p[1],p[2]) if plane=='axial' else (p[0],-p[2],p[1]) if plane=='coronal' else (p[1],-p[2],p[0])
    axis={'axial':2,'coronal':1,'sagittal':0}[plane]
    settings={'brain':([50,130],[20,60],80,40),'soft':([60,450],[15,100],200,50),'wide':([150,450],[30,120],200,75),'bone':([1500,4000],[250,1000],2500,500)}
    widths,levels,w,l=settings[window]
    polygon=[[round(u+radii[0]*math.cos(a*math.pi/6),3),round(v+radii[1]*math.sin(a*math.pi/6),3)] for a in range(12)]
    targets=phases[-1]['targets'];tid=f"p{len(phases):02d}-{len(targets)+1:02d}"
    targets.append(dict(id=tid,label=label,side=side,windows=[dict(width=widths,level=levels)],regions=[dict(plane=plane,normal=[n-span*m['spacing'][axis],n+span*m['spacing'][axis]],polygon=polygon,toleranceMm=0)],representative=dict(plane=plane,patient=p,width=w,level=l)))
def pair(label,right,left,radii=(3,3),**kwargs):
    target('Right '+label,right,radii,side='right',**kwargs);target('Left '+label,left,radii,side='left',**kwargs)

phase('Scalp & outside the skull','Sweep the scalp from vertex down to the skull base. Check both sides.',144)
pair('vertex scalp',[121,180,99],[260,180,99],(1.5,4),window='soft',span=0)
pair('lateral scalp',[70,200,53],[308,200,53],(1.5,6),window='soft',span=3)
pair('skull-base soft tissues',[83,194,2],[292,194,2],(5,8),window='soft',span=1)
phase('Vertex, cortex & extra-axial spaces','Compare both hemispheres, gray-white junctions and the inner table.',170)
target('Vertex falx',[190,174,96],(1.2,8),span=1)
pair('high-convexity sulci',[151,205,92],[227,205,92],(4,5),span=1)
pair('cortical gray-white junction',[130,140,75],[249,140,75],(3,4),span=2)
pair('convexity extra-axial margin',[87,201,70],[288,201,70],(2,10),window='wide',span=2)
phase('Deep gray & insular ribbons','Identify paired deep structures and compare each insular ribbon.',220)
pair('caudate head',[174,142,48],[208,137,48],(3,4),span=1)
pair('internal capsule',[161,162,48],[220,157,48],(2,4),span=1)
pair('lentiform nucleus',[147,169,48],[235,160,48],(4,6),span=1)
pair('thalamus',[174,196,48],[207,193,48],(4,6),span=1)
pair('insular ribbon',[126,172,42],[253,165,42],(2,7),span=1)
phase('Fissures, cisterns & arteries','Look at CSF spaces, the MCA regions and midbrain configuration.',258)
pair('Sylvian fissure / MCA region',[144,166,31],[236,155,31],(3,4),span=1)
target('Suprasellar cistern',[187,176,31],(4,3),span=1)
target('Interpeduncular cistern',[190,198,31],(2,2),span=1)
target('Midbrain',[190,216,31],(6,6),span=1)
phase('Ventricles & midline','Inspect septum position, occipital horns and temporal horns.',305)
pair('lateral ventricle body',[165,214,64],[209,208,64],(2,4),span=1)
target('Septum pellucidum',[186,158,53],(1.1,3),span=1)
pair('occipital horn',[143,254,53],[232,261,53],(2,3),span=1)
pair('temporal horn region',[142,209,31],[237,202,31],(2.5,3),span=1)
phase('Posterior fossa & foramen magnum','Review the brainstem, cerebellum, CPA cisterns and craniocervical junction.',351)
target('Pons',[191,218,20],(7,7),span=1)
pair('cerebellar hemisphere',[149,281,15],[231,276,15],(10,8),span=2)
pair('cerebellopontine angle cistern',[157,226,15],[225,222,15],(2.5,3),span=1)
target('Foramen magnum / upper cord',[192,259,0],(6,6),span=0)
pair('vertebral artery region',[176,242,0],[211,240,0],(2.5,3),span=0)
phase('Sella & orbits','Check the sellar region and both orbits on axial soft-tissue views.',399)
target('Sellar region',[189,181,20],(3,3),window='soft',span=1)
pair('orbit',[139,99,15],[236,95,15],(9,9),window='soft',span=2)
phase('Sagittal checks','Use sagittal images for the pituitary, brainstem, tonsils, sinuses and optic nerves.',414)
target('Pituitary / sella',[190,178,25],(3,3),plane='sagittal',window='soft',span=1)
target('Brainstem',[190,211,25],(5,8),plane='sagittal',span=1)
target('Tonsillar / foramen magnum region',[180,250,4],(4,4),plane='sagittal',span=1)
pair('transverse sinus region',[142,327,25],[238,323,24],(3,2),plane='sagittal',window='soft',span=1)
pair('optic nerve',[151,131,12],[224,131,12],(2.5,2),plane='sagittal',window='soft',span=1)
phase('Coronal checks','Review venous sinuses, dural reflections and both convexities.',471)
target('Superior sagittal sinus',[190,210,100],(2.5,2),plane='coronal',window='soft',span=2)
pair('transverse sinus region',[121,310,26],[263,310,26],(3,2),plane='coronal',window='soft',span=1)
target('Falx',[190,210,87],(1.5,7),plane='coronal',window='soft',span=2)
pair('tentorium',[154,275,38],[228,275,37],(7,2),plane='coronal',window='soft',span=1)
pair('convexity extra-axial margin',[83,210,64],[290,210,64],(2,9),plane='coronal',window='wide',span=1)
phase('Bones, mastoids & sinuses','Switch to the bone reconstruction and review skull, temporal bones and sinuses.',508)
pair('calvarium',[84,186,64],[293,186,64],(2.5,8),window='bone',span=3)
pair('temporal bone / mastoid',[99,255,8],[285,252,8],(7,8),window='bone',span=2)
target('Sphenoid sinus',[187,155,15],(7,6),window='bone',span=1)
target('Ethmoid air cells',[186,124,15],(6,8),window='bone',span=1)
target('Frontal sinus',[189,73,20],(6,3),window='bone',span=1)
pair('superior maxillary sinus',[150,152,3],[232,152,3],(5,2),plane='coronal',window='bone',span=1)

out=dict(caseId=m['id'],caseVersion=m['version'],version=m['checkpointVersion'],phases=phases)
(ROOT/'cases/normal-head/checkpoints.json').write_text(json.dumps(out,indent=2)+'\n')
print(sum(len(p['targets']) for p in phases),'targets in',len(phases),'phases')
