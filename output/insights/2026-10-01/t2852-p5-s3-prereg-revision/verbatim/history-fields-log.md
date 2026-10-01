# T-2867 本走 (v1) の LLM 系列の coder 入力の自系列の履歴 — 欄の有無だけの集計 (段 6 所見 A-1 の裏取り)

コマンド (cwd = /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-contrast-run/v1/rounds):

```
python3 -c "
import json,glob,collections
c=collections.Counter(); n=0; files=sorted(glob.glob('llm-*/a*/coder-input.json'))
for f in files:
    d=json.load(open(f)); n+=1
    for r in d['self_history']:
        c[(r['outcome'], r['verifier_digest'] is not None, r['reject_subtype'] is not None)]+=1
print('coder-input files', n, '(llm-cpp', sum(f.startswith('llm-cpp') for f in files), '/ llm-ir', sum(f.startswith('llm-ir') for f in files), ')')
print('history rows (延べ、機会ごとの累積):', sum(c.values()))
print('(outcome, verifier_digest あり, reject_subtype あり): 件数')
for k,v in sorted(c.items(), key=lambda x:-x[1]): print(k, v)
"
```

生出力:

```
2026-10-01 10:21:57 JST
coder-input files 249 (llm-cpp 121 / llm-ir 128 )
history rows (延べ、機会ごとの累積): 1638
(outcome, verifier_digest あり, reject_subtype あり): 件数
('certified', False, False) 1626
('rejected', False, True) 12
```

- 読んだ欄は `self_history` の各行の `outcome` と、`verifier_digest`・`reject_subtype` の有無だけ。throughput は履歴に無い。score・endpoint・report は開いていない。
- 行数は機会ごとの coder 入力に累積して載る履歴の延べ数で、一意な候補の数ではない。
