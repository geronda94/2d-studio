with open('backend/validation.py', 'r') as f:
    content = f.read()

monotonic_check = """
        # монотонность start_time (локальное время слайда, мс — см. AGENTS.md §8)
        prev, prev_idx = None, None
        for i, item in enumerate(payload):
            if isinstance(item, dict):
                t = item.get("start_time")
                if isinstance(t, (int, float)) and not isinstance(t, bool):
                    if prev is not None and t < prev:
                        errors.append({
                            "path": f"{path}[{i}].start_time", "type": "non_monotonic_start_time",
                            "message": f"start_time {t} < {prev} из {path}[{prev_idx}] — элементы должны идти по нарастающей"})
                    else:
                        prev, prev_idx = t, i
        return errors"""

import re
content = re.sub(r'(\s+)return errors', monotonic_check, content, count=1, flags=re.DOTALL)

with open('backend/validation.py', 'w') as f:
    f.write(content)
