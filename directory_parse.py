import requests
import re
import pprint as pp

in_filename = 'bgsa_mailman_roster.txt'

with open(in_filename, 'r') as fle:
    search_terms = [l.strip() for l in fle.readlines()]

re_program = re.compile(r'(?<=<PRE>\s{6}name:\s)'
                        '(?P<last_name>.*),\s+'
                        '(?P<first_name>.*)(?=\n)')
match_group_keys = ['first_name',
                    'last_name']
address_fmt = 'http://web.mit.edu/bin/cgicso?options=general&query=%s'

results = []
for term in search_terms:
    page_txt = requests.get(address_fmt % term).text
    m = re_program.search(page_txt)
    out = [m.group(k) if m else '' for k in match_group_keys]
    out = [term,] + out
    results.append(out)
        
match_group_keys.insert(0, 'search_term')
results.insert(0, match_group_keys)

pp.pprint(results)

with open('output.csv', 'w+') as fle:
    [fle.write(', '.join(l) + '\n') for l in results]
    
    
