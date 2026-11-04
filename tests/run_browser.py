"""Start an isolated synthetic app, run browser checks, then stop it."""
import os,subprocess,tempfile,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
r=os.environ.get('RSCRIPT','Rscript')
with tempfile.TemporaryDirectory(prefix='olsd-pilot-browser-') as directory:
 env=dict(os.environ,OLSD_BACKEND='folder',OLSD_DATA_DIR=directory,OLSD_PILOT_TEST_URL='http://127.0.0.1:3011',OLSD_PILOT_FIXTURE=str(Path(directory)/'snapshot.xlsx'))
 # Prevent accidental use of inherited Connect identity in local tests.
 for key in ['CONNECT_SERVER','CONNECT_API_KEY','POSIT_PRODUCT','RSTUDIO_PRODUCT']:env.pop(key,None)
 subprocess.run([r,'-e','if(Sys.getenv("OLSD_USE_RENV")=="true") renv::load();source("tests/seed_browser.R")'],cwd=root,env=env,check=True)
 with open('/tmp/olsd-pilot-browser-server.log','w') as log:
  server=subprocess.Popen([r,'-e','if(Sys.getenv("OLSD_USE_RENV")=="true") renv::load();shiny::runApp(".",port=3011,host="127.0.0.1",launch.browser=FALSE)'],cwd=root,env=env,stdout=log,stderr=log)
  try:
   for i in range(100):
    if server.poll() is not None:raise RuntimeError('Shiny exited; see /tmp/olsd-pilot-browser-server.log')
    try:
     urllib.request.urlopen(env['OLSD_PILOT_TEST_URL'],timeout=1);break
    except Exception:time.sleep(.1)
   subprocess.run(['python',str(root/'tests/browser.py')],env=env,cwd=root,check=True)
  finally:server.terminate();server.wait(timeout=10)
