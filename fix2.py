with open("bot/ai.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if i == 414:
        new_lines.append(line)
        continue
    if i == 415:
        # skip `        if content:`
        continue
    new_lines.append(line)

with open("bot/ai.py", "w") as f:
    f.writelines(new_lines)
