import os,subprocess,tempfile
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
java=Path(os.environ.get('JAVA_HOME','/usr'))/'bin/java'
with tempfile.TemporaryDirectory(prefix='tvretro-status-') as folder:
 subprocess.run([str(java.with_name('javac')),'-source','1.8','-target','1.8','-d',folder,str(repo/'apps/tv-casa/src/com/ansub/tvhome/LocalTransferServer.java'),str(repo/'tests/TransferStatusTests.java')],check=True)
 subprocess.run([str(java),'-cp',folder,'TransferStatusTests'],check=True)
