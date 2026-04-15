import re
html = open('templates/block_builder_fragment.html', encoding='utf-8').read()
js = open('static/js/bb-blocks.js', encoding='utf-8').read()
html_types = re.findall(r'data-type=\"([^\"]+)\"', html)
js_types = re.findall(r'\n\s+([a-z]+):\s*\{', js)
missing = [ht for ht in html_types if ht not in js_types]
print('Missing:', missing)
