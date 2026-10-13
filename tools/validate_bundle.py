"""Verify every packaged file against records/file-manifest.json."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()
def validate(root):
 manifest=json.loads((root/'records/file-manifest.json').read_text(encoding='utf-8'))
 errors=[]
 for row in manifest['files']:
  p=(root/row['path']).resolve()
  if not p.is_relative_to(root.resolve()):errors.append('Unsafe path: '+row['path']);continue
  if not p.is_file():errors.append('Missing: '+row['path']);continue
  if p.stat().st_size!=row['bytes'] or digest(p)!=row['sha256']:errors.append('Changed: '+row['path'])
 if errors:raise ValueError('\n'.join(errors))
 return {'verified_files':len(manifest['files']),'total_bytes':sum(x['bytes'] for x in manifest['files']),'passed':True}
if __name__=='__main__':
 try:print(json.dumps(validate(ROOT),indent=2))
 except Exception as ex:print(str(ex),file=sys.stderr);sys.exit(1)
