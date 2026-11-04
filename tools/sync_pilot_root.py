"""Publish pilot/ as a root-layout branch. Run from the public source repository."""
import argparse,subprocess
p=argparse.ArgumentParser();p.add_argument('--push',action='store_true');args=p.parse_args()
branch='production/posit-connect-pilot-root'
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
if git('branch','--show-current')!= 'production/posit-connect-pilot':raise SystemExit('Run from production/posit-connect-pilot in the public source repository.')
if git('status','--porcelain'):raise SystemExit('Commit source changes before synchronizing the delivery branch.')
source=git('rev-parse','HEAD');tree=git('rev-parse',source+':pilot')
remote=subprocess.run(['git','fetch','origin',branch],capture_output=True,text=True)
if remote.returncode==0:parent=git('rev-parse','FETCH_HEAD')
else:
 try:parent=git('rev-parse','refs/heads/'+branch)
 except subprocess.CalledProcessError:parent='627c2113268f0120bdde575a8c587facaa304bd4'
if git('rev-parse',parent+'^{tree}')==tree:
 commit=parent
else:commit=git('commit-tree',tree,'-p',parent,'-m','Sync root-layout pilot from '+source)
git('update-ref','refs/heads/'+branch,commit)
if args.push:subprocess.run(['git','push','origin','refs/heads/'+branch],check=True)
print(commit)
