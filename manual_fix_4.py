import os, glob

files = glob.glob('core/src/components/**/*.vue', recursive=True)
for file in files:
    content = open(file).read()
    if '""${' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '""${' in line:
                # specifically target the known issue in ProcessFunnel
                if 'getColorAlpha' in line:
                    lines[i] = line.replace('""${', '').replace('}``', '').replace('}`', '')
                    # wait, if it was :stroke="""${getColorAlpha...}``", replacing ""${ with nothing makes it :stroke="getColorAlpha...
                    # but wait! The original line is:
                    # :stroke=""${getColorAlpha(getStepColor(step, idx), 0.4)}`` 
                    # If we replace '""${' with '"' and '}``' with '"', it becomes :stroke="getColorAlpha(getStepColor(step, idx), 0.4)"
                    pass
        
        # Actually, let's just do a string replace on the exact known broken strings
        new_content = content.replace('""${getColorAlpha(getStepColor(step, idx), 0.4)}``', '"getColorAlpha(getStepColor(step, idx), 0.4)"')
        new_content = new_content.replace('""${getColorAlpha(getStepColor(step, idx), 0.2)}``', '"getColorAlpha(getStepColor(step, idx), 0.2)"')
        new_content = new_content.replace('""${getColorAlpha(\'var(--text-primary)\', 0.2)}``', '"getColorAlpha(\'var(--text-primary)\', 0.2)"')
        
        open(file, 'w').write(new_content)
        print("Fixed in", file)
