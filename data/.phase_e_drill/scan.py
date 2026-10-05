import subprocess
import re
from pathlib import Path
files = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], text=True).splitlines()
patterns = [r'AKIA[0-9A-Z]{16}', r'gh[pousr]_[A-Za-z0-9]{30,}', r'sk-(?:proj-)?[A-Za-z0-9_-]{30,}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
found, env, count = [], [], 0
for name in files:
    path = Path(name)
    if path.name == '.env':
        env.append(name)
    if not path.is_file() or path.stat().st_size > 5000000:
        continue
    try:
        body = path.read_text(encoding='utf-8')
    except (UnicodeError, OSError):
        continue
    count += 1
    if any(re.search(pattern, body) for pattern in patterns):
        found.append(name)
print('Text files scanned:', count)
print('High-confidence credential candidate files:', found)
print('Tracked/nonignored .env files:', env)
assert not found and not env
