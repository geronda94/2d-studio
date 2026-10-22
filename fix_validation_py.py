with open('backend/validation.py', 'r') as f:
    content = f.read()

import re
content = re.sub(r'# монотонность start_time.*?return errors', 'return errors', content, flags=re.DOTALL)

with open('backend/validation.py', 'w') as f:
    f.write(content)
