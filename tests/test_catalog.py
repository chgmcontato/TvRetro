"""Deterministic catalogue parser/matcher checks. No network or ROMs required."""
import os
from pathlib import Path
import subprocess
import tempfile

repo=Path(__file__).resolve().parents[1]
java=Path(os.environ.get('JAVA_HOME','/usr'))/'bin/java'
with tempfile.TemporaryDirectory(prefix='tvretro-catalog-test-') as folder:
 subprocess.run([str(java.with_name('javac')),'-d',folder,str(repo/'apps/tv-casa/src/com/ansub/tvhome/ThumbnailCatalog.java'),str(repo/'tests/CatalogTests.java')],check=True)
 subprocess.run([str(java),'-cp',folder,'CatalogTests'],check=True)
