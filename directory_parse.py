import requests
import re
import pprint as pp
import time

in_filename = 'bgsa_mailman_roster.txt'
with open(in_filename, 'r') as fle:
    search_terms = [l.strip() for l in fle.readlines()]
re_program = re.compile(r'(?<=<PRE>\s{6}name:\s)'
                        '(?P<last_name>.*),\s+'
                        '(?P<first_name>.*)(?=\n)')
match_group_keys = ['first_name', 'last_name']
address_fmt = 'http://web.mit.edu/bin/cgicso?options=general&query=%s'

results = {}
repeats = 1
match_count = 0
for _ in range(repeats):
    for i, term in enumerate(search_terms):
        tries = 0
        while True:
            tries += 1
            time.sleep(0.1)
            r = requests.get(address_fmt % term)
            if r.status_code is 200:
                break
            elif r.status_code is 500:
                pause_time = 60
                pp.pprint('Too many requests, taking a %d s pause.'
                          % pause_time)
                time.sleep(pause_time)
            else:
                if tries > 5:
                    pp.pprint(('Unknown Status Code: %d ... Search: \'%s\''
                               ' ... continuing.')
                              % (term, r.status_code))
                    break
                else:
                    pp.pprint(('Unknown Status Code: %d ... Search: \'%s\''
                               ' ... trying again.')
                              % (term, r.status_code))
        m = re_program.search(r.text)
        pp.pprint('%3d | %3d (/ %3d) --- EC: %3d ---\'%s\''
                  % (i, match_count, len(search_terms), r.status_code, term))
        results[term] = [m.group(k) if m else '' for k in match_group_keys]
        match_count += 1 if m else 0
   
if results: 
    results = [[k,] + v for k, v in results.items()]
    match_group_keys.insert(0, 'search_term')
    results.insert(0, match_group_keys)
    pp.pprint(results)
    with open('output.csv', 'w+') as fle:
        [fle.write(', '.join(l) + '\n') for l in results]


