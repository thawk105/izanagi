# error_buckets.py (逐語)

親の検算 script (権威にしない): setup error を testcase time で分ける。結果: pre 18 走 {>=30: 74, 2-30: 0, <2: 13}、post 24 走 {0,0,0}。

```python
"""親の検算: 前 regime の setup error を testcase time で分ける (>=30s = 実 timeout、<2s = fixture 例外 cache の再掲)。"""
import glob
import os
import sys
import time
import xml.etree.ElementTree as ET

root_dir = sys.argv[1]
since = time.mktime(time.strptime(sys.argv[2], '%Y-%m-%d %H:%M'))
pre = {'>=30': 0, '2-30': 0, '<2': 0}
post = {'>=30': 0, '2-30': 0, '<2': 0}
pre_runs = post_runs = 0
for session in sorted(glob.glob(root_dir + '/*/')):
    if os.path.getmtime(session) < since:
        continue
    for p in sorted(glob.glob(session + 'shard-*/junit.xml')):
        try:
            tree = ET.parse(p)
        except ET.ParseError:
            continue
        cases = [tc for tc in tree.getroot().iter('testcase') if 't1259' in (tc.get('classname') or '')]
        if not cases:
            continue
        suffixed = any((tc.get('name') or '').endswith('@real-repo') for tc in cases)
        bucket = post if suffixed else pre
        if suffixed:
            post_runs += 1
        else:
            pre_runs += 1
        for tc in cases:
            if tc.find('error') is None:
                continue
            t = float(tc.get('time') or 0)
            key = '>=30' if t >= 30 else ('2-30' if t >= 2 else '<2')
            bucket[key] += 1
print('pre runs', pre_runs, 'errors by time:', pre)
print('post runs', post_runs, 'errors by time:', post)

```
