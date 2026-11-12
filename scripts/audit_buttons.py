import re
import glob

print("--- AUDITING BUTTON TITLES ---")
for path in glob.glob("services/**/*.py", recursive=True):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(r'[\'"]title[\'"]:\s*[\'"]([^\'"]+)[\'"]', content):
        t = m.group(1)
        if len(t) > 20:
            print(f"File {path}: len={len(t)} -> '{t}'")
