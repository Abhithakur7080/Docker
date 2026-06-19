import os
import json

data = {}

for root, dirs, files in os.walk('.'):
    # Skip .git, node_modules etc if any
    if '.git' in root or '.gemini' in root:
        continue
    for file in files:
        if file.endswith('.md') or file.startswith('Dockerfile') or file.endswith('.yml'):
            if file == 'README.md' or file == 'practice_plan.md':
                continue
            path = os.path.join(root, file).replace('\\', '/')
            # remove leading './'
            if path.startswith('./'):
                path = path[2:]
            
            try:
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                data[path] = content
            except Exception as e:
                print(f"Error reading {path}: {e}")

js_content = f"window.COURSE_CONTENT = {json.dumps(data)};"

with open('course_data.js', 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"Successfully bundled {len(data)} files into course_data.js")
