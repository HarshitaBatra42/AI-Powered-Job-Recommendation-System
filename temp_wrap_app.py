from pathlib import Path

file_path = Path('app.py')
text = file_path.read_text(encoding='utf-8')
needle = 'st.set_page_config('
idx = text.find(needle)
if idx == -1:
    raise SystemExit('needle not found')

lines = text.splitlines(True)
start_line = next(i for i, line in enumerate(lines) if needle in line)

if any('def main()' in line for line in lines[:start_line + 1]):
    raise SystemExit('app.py already wrapped')

new_lines = lines[:start_line] + ['def main():\n']
new_lines += [('    ' + line if line.strip() else line) for line in lines[start_line:]]
text2 = ''.join(new_lines)
if 'if __name__ == "__main__"' not in text2:
    text2 = text2.rstrip() + '\n\nif __name__ == "__main__":\n    main()\n'
file_path.write_text(text2, encoding='utf-8')
print('wrapped app.py successfully')
