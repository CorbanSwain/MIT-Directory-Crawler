import requests
import re
import pprint as pp
import time
from datetime import datetime
import csv
import matplotlib.pyplot as plt
import numpy as np
from plotting_utils import *
from textwrap import fill
from enum import Enum


bgsa_colors = [
    '#633366',
    '#352552',
    '#3F508C',
    '#FF4D00',
    '#8C3F42',
]


class MITSchool(str, Enum):
    eng = 'Engineering'
    hass = 'Humanities, Arts, & Social Sciences'
    arch= 'Architecture & Planning'
    science = 'Science'
    sloan = 'Sloan'
    other = 'Other'

    @staticmethod
    def from_dir_name(nme):
        if nme == 'School Of Engineering':
            return MITSchool.eng
        elif nme == 'Humanities, Arts, & Soc Sci':
            return MITSchool.hass
        elif nme == 'School Of Arch. And Planning':
            return MITSchool.arch
        elif nme == 'School Of Science':
            return MITSchool.science
        elif nme == 'Alfred P. Sloan Sch. Of Mgt.':
            return MITSchool.sloan
        else:
            return MITSchool.other


mit_grad_data = {
    MITSchool.arch: 28,
    MITSchool.eng: 72,
    MITSchool.hass: 4,
    MITSchool.sloan: 62,
    MITSchool.science: 18,
    MITSchool.other: 0,
}


def read_csv_file(in_filename):
    table = []
    with open(in_filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        column_names = []
        line_count = 0
        for i_row, row in enumerate(csv_reader):
            if i_row == 0:
                column_names = row
            else:
                table.append({k: row[i] for i, k in enumerate(column_names)})
            line_count = i_row
        line_count += 1
        print(f'Processed {line_count} lines from csv file.')
    return table


def get_mit_directory_info(search_terms):
    cache_name = 'mit_dir_cache'
    cache = load_obj(cache_name) or dict()
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
    metadata = {'entry_source': lambda _, __: in_filename,
                'entry_in mit_directory?': lambda a, _: 'TRUE' if a else 'FALSE',
                'entry_add_date': lambda _, __: datetime.now().strftime('%m/%d/%Y'),
                'search_term': lambda _, b: b}
    address_fmt = 'http://web.mit.edu/bin/cgicso?options=general&query=%s'

    results = {}
    result_keys = set()
    match_count = 0
    for i, term in enumerate(search_terms):
        if term not in cache:
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

            rtext = r.text
            cache[term] = rtext
            save_obj(cache, cache_name)
        else:
            code = -1
            rtext = cache[term]

        m = re_program.search(rtext)
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

    return results, result_keys


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


def get_department_event_counts(table):
    event_list = dict()
    for entry in table:
        if entry['category'] in ['summer_intern', 'undergrad']:
            pass
        try:
            if 'school' not in entry:
                dpt = 'other'
            else:
                dpt = entry['school']
            event = entry['event']

            if len(dpt) == 0:
                dpt = 'other'

            if event not in event_list:
                event_list[event] = dict()

            if dpt not in event_list[event]:
                event_list[event][dpt] = 0

            event_list[event][dpt] += 1
        except KeyError:
            pass

    pp.pprint(event_list)
    event_totals = {k: sum(v.values()) for k, v in event_list.items()}

    percent_list = dict()
    for evt in event_list:
        percent_list[evt] = dict()
        for k, v in event_list[evt].items():
            percent_list[evt][k] = v # / event_totals[evt]

    cum_percents = dict()
    for _, evtpct in percent_list.items():
        for k, v in evtpct.items():
            if k not in cum_percents:
                cum_percents[k] = []
            cum_percents[k].append(v)

    for k, v in cum_percents.items():
        cum_percents[k] = sum(v) / len(v)

    return cum_percents


def get_person_event_counts(table):
    person_list = dict()
    for entry in table:
        try:
            person_list[entry['mit_id']].add(entry['event'])
        except KeyError:
            person_list[entry['mit_id']] = set()
            person_list[entry['mit_id']].add(entry['event'])
    for k in person_list:
        person_list[k] = len(person_list[k])
    return person_list


def plot_person_histogram(table):
    fig, ax = plt.subplots(1, 1, figsize=(8, 4))
    person_counts = get_person_event_counts(table)
    x = np.array([v for v in person_counts.values()])
    ax.hist(x, np.max(x) - 1, edgecolor='k', facecolor='#633366')

    ax.set_xlabel('Number of Attendences')
    ax.set_ylabel('Number of People')
    despine(ax, right=True, top=True)


def plot_event_breakdown_pie(table):
    fig = plt.figure(figsize=(11, 5))
    gs = plt.GridSpec(2, 12, figure=fig)
    ax = plt.subplot(gs[:, 7:])
    event_pcts = get_department_event_counts(table)
    labels = event_pcts.keys()
    labels = [MITSchool.from_dir_name(l) for l in labels]
    i_other = labels.index(MITSchool.other)
    labels.append(labels.pop(i_other))
    mit_vals = [mit_grad_data[l] for l in labels if l is not MITSchool.other]
    labels = [l.replace('&', '\&') for l in labels]
    labels = [fill(l, 20) for l in labels]
    vals = list(event_pcts.values())
    vals.append(vals.pop(i_other))
    tot = sum(vals)
    wedges, texts, autotexts = ax.pie(vals,
                                      autopct=lambda pct: '\\textbf{%d} \\%%' %
                                                          round(pct),
                                      pctdistance=0.7,
                                      colors=bgsa_colors + [(.9, .9, .9), ],
                                      wedgeprops=dict(edgecolor=None,
                                                      width=0.6),
                                      textprops=dict(color='w'),
                                      )
    ax.text(0, 0,
            '\\textbf{%d}' % tot,
            horizontalalignment='center',
            verticalalignment='bottom',
            fontsize='xx-large')
    ax.text(0, 0,
            'Average No. Attendees\nat \\textbf{BGSA} Events\n(Fall \'18)',
            horizontalalignment='center',
            verticalalignment='top',
            fontsize='small')
    autotexts[-1].set_color('k')
    ax = plt.subplot(gs[:, 0:2])
    ax.axis('off')
    plt.figlegend(wedges,
                  labels,
                  title='\\textbf{MIT Schools}',
                  title_fontsize=10,
                  mode=None,
                  bbox_to_anchor=ax.get_position(),
                  frameon=False)

    mit_tot = sum(mit_vals)
    ax = plt.subplot(gs[:, 2:7])
    ax.pie(mit_vals,
           autopct=lambda pct: '\\textbf{%d} \\%%' %
                               round(pct),
           pctdistance=0.7,
           colors=bgsa_colors,
           wedgeprops=dict(edgecolor=None,
                           width=0.6,
                           alpha=0.8),
           textprops=dict(color='w'),
           )
    ax.text(0, 0,
            '\\textbf{%d}' % mit_tot,
            horizontalalignment='center',
            verticalalignment='bottom',
            fontsize='xx-large',
            alpha=0.8,
            )
    ax.text(0, 0,
            'Black MIT\nGraduate Students\n(\'18--\'19)',
            horizontalalignment='center',
            verticalalignment='top',
            alpha=0.8,
            fontsize='small')
    plt.tight_layout()


if __name__ == '__main__':
    in_filename = 'all_event_attendees.csv'
    table = read_csv_file(in_filename)
    emails = [d['email'] for d in table]
    mit_ids = [s.split('@')[0] for s in emails]
    for i, idd in enumerate(mit_ids):
        table[i]['mit_id'] = idd
    results, result_keys = get_mit_directory_info(mit_ids)

    table_original = table
    for i, entry in enumerate(table):
        idd = entry['mit_id']
        for k, v in results[idd].items():
            table[i][k] = v

    set_font_defaults()
    plot_person_histogram(table)
    plot_event_breakdown_pie(table)
    multipage('bgsa_event_stats', fmt='png')
    plt.show()

    # if results:
    #     extra_result_keys = [k for k in result_keys if k not in preferred_order]
    #     result_keys = preferred_order + extra_result_keys
    #     results_table = [result_keys]
    #     for k, v in results.items():
    #         entry = [v[rk] if rk in v else '' for rk in result_keys]
    #         results_table.append(entry)
    #         # pp.pprint(results_table)
    #     with open(in_filename.split('.')[0] + '.out', 'w+') as fle:
    #         [fle.write('\t'.join(l) + '\n') for l in results_table]