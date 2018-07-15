import requests
import re
import pprint as pp
import time

in_filename = 'in_file.txt'
with open(in_filename, 'r') as fle:
    search_terms = [l.strip() for l in fle.readlines()]

re_program = re.compile(r'(?<=<PRE>\s{6}name:\s)'
                        '(?P<last_name>.*),\s+'
                        '(?P<first_name>.*)(?=\n)')
match_group_keys = ['first_name',
                    'last_name']
address_fmt = 'http://web.mit.edu/bin/cgicso?options=general&query=%s'

results = {}
for _ in range(2):
    for term in search_terms:
        time.sleep(5)
        page_txt = requests.get(address_fmt % term).text
        pp.pprint(page_txt)
        m = re_program.search(page_txt)
        if m:
            out = [m.group(k) for k in match_group_keys]
            results[term] = out
    pp.pprint(len(results))
   
if results: 
    results = [[k,] + v for k, v in results.items()]
    match_group_keys.insert(0, 'search_term')
    results.insert(0, match_group_keys)
    pp.pprint(results)
    with open('output.csv', 'w+') as fle:
        [fle.write(', '.join(l) + '\n') for l in results]


