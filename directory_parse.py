import requests
import re
import pprint as pp
import time
from datetime import datetime

in_filename = 'example_list.txt'
with open(in_filename, 'r') as fle:
    search_terms = [l.strip() for l in fle.readlines()]
re_program = re.compile(r'(?<=<PRE>)(?:.*\n)*(?=</PRE>)')
re_name_program = re.compile(r'(?P<last_name>.*),\s'
                             r'(?P<first_name>\S*)'
                             r'(\s+(?P<middle_name>.+)\.?)?')
re_email_program = re.compile(r'(?P<email>\w+@\w+?\.\w+)')
re_special = {'name': (re_name_program,
                       ['first_name', 'middle_name', 'last_name']),
              'email': (re_email_program, ['email', ]),
              'url': (re.compile(r'(?<=href=[\"\'])(?P<url>.*)'
                                 r'(?=[\"\'])'),
                      ['url', ])}
metadata = {'entry_source': lambda a, b: in_filename,
            'entry_in mit_directory?': lambda a, b: 'TRUE' if a else 'FALSE',
            'entry_add_date': lambda a, b: datetime.now().strftime('%m/%d/%Y'),
            'search_term': lambda a, b: b}
address_fmt = 'http://web.mit.edu/bin/cgicso?options=general&query=%s'

preferred_order = ['first_name',
                   'middle_name',
                   'last_name',
                   'email',
                   'department',
                   'entry_source',
                   'year',
                   'title',
                   'office',
                   'school',
                   'url',
                   'phone',
                   'phone2',
                   'Fax',
                   'address',
                   'address2',
                   'search_term',
                   'entry_in mit_directory?',
                   'entry_add_date']

results = {}
result_keys = set()
match_count = 0
for i, term in enumerate(search_terms):
    tries = 0
    while True:
        tries += 1
        r = requests.get(address_fmt % term)
        code = r.status_code
        if code == 200:
            break
        elif code == 500:
            pause_time = 1
            pp.pprint('Too many requests, taking a %3.1f minute pause.'
                      % pause_time)
            time.sleep(pause_time * 60)
        else:
            if tries > 5:
                pp.pprint(('Unknown Status Code: %d ... Search: \'%s\''
                           ' ... continuing to next search.')
                          % (code, term))
                break
            else:
                pp.pprint(('Unknown Status Code: %d ... Search: \'%s\''
                           ' ... trying again.')
                          % (code, term))
                time.sleep(1)
    m = re_program.search(r.text)
    pp.pprint('%3d | %3d (/ %3d) --- EC: %3d --- \'%s\''
              % (i, match_count, len(search_terms), code, term))

    lns = {}
    if m:
        txt = m.group(0)
        txt = txt.replace('&amp;', '&')
        txt = txt.replace('&#39;', '\'')
        for l in txt.strip().split('\n'):
            if ':' in l:
                kv = l.split(':')
                k, v = map(lambda x: x.strip(), (kv[0], ':'.join(kv[1:])))
                if k in re_special:
                    rpgm, sub_keys = re_special[k]
                    rmtch = rpgm.search(v)
                    for sub_k in sub_keys:
                        if rmtch and sub_k in rmtch.groupdict() \
                                and rmtch.group(sub_k):
                            lns[sub_k] = rmtch.group(sub_k)
                else:
                    lns[k] = v
    is_match = bool(len(lns))
    for k, v in metadata.items():
        lns[k] = v(is_match, term)
    results[term] = lns
    result_keys = result_keys.union(lns.keys())
    match_count += 1 if is_match else 0

if results:
    extra_result_keys = [k for k in result_keys if k not in preferred_order]
    result_keys = preferred_order + extra_result_keys
    results_table = [result_keys]
    for k, v in results.items():
        entry = [v[rk] if rk in v else '' for rk in result_keys]
        results_table.append(entry)
        # pp.pprint(results_table)
    with open(in_filename.split('.')[0] + '.out', 'w+') as fle:
        [fle.write('\t'.join(l) + '\n') for l in results_table]


