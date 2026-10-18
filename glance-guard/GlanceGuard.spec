from pathlib import Path
from PyInstaller.utils.hooks import collect_all
root=Path(SPECPATH)
if not (root / 'assets/face_landmarker.task').exists():
    raise RuntimeError('Run python tools/prepare_assets.py first')
data,binaries,hidden=collect_all('mediapipe')
a=Analysis([str(root/'main.py')],pathex=[str(root)],
    binaries=binaries,datas=data+[(str(root/'assets'),'assets')],hiddenimports=hidden,
    excludes=['IPython','jupyter','pytest','tkinter'])
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='GlanceGuard',console=False,
    icon=str(root/'assets/icon.ico'))
coll=COLLECT(exe,a.binaries,a.datas,name='GlanceGuard')
