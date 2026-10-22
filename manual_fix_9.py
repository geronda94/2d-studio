import os

f = 'core/src/components/ui/ChatMockup.vue'
content = open(f).read()

# Fix the user sender quote
content = content.replace("`user'", "'user'")

# Fix the background evaluation
# background: (msg.sender === 'user' || msg.role === 'user') ? 'var(--color-primary)' : (msg.isError ? undefined : '${getColorAlpha('var(--text-primary)', 0.1)}'),
# to:
# background: (msg.sender === 'user' || msg.role === 'user') ? 'var(--color-primary)' : (msg.isError ? undefined : getColorAlpha('var(--text-primary)', 0.1)),
content = content.replace(
    "'${getColorAlpha('var(--text-primary)', 0.1)}'",
    "getColorAlpha('var(--text-primary)', 0.1)"
)

# Check if there are other similar '${getColorAlpha...}' broken strings
import re
content = re.sub(r"'?\$\{?getColorAlpha\('([^']+)',\s*([0-9.]+)\)\}?'?", r"getColorAlpha('\1', \2)", content)

open(f, 'w').write(content)
print("Fixed ChatMockup.vue")
