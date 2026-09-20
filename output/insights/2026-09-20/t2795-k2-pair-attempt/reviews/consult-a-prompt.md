単独段 dispatch: stage=consult; lane=sol; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair

必読事項の射影 (この列挙にある file が読めなければ即停止。**この停止規則は本射影 file 限定であり、自分で導出した path の不在では検査を打ち切らない**):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/diagnosis-pair-0001.md — 親の診断メモ (事実・機構の読み・provisional 裁定 P-A〜P-E)。**攻撃対象。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/brief.md — 親の段 1 brief (scope・裁定・不変条件)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/evidence/attempt-0001/job.stderr — 実 job の traceback (逐語)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/evidence/attempt-0001/job.stdout — 実 job の stdout (逐語)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/orchestrator/campaign/campaign_claim.py — claim leaf。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/orchestrator/campaign/loop.py — `_authorize_measurement` / `run_campaign` (150〜260 行と 480〜560 行)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/orchestrator/campaign/p3_s4_loop.py — `_run_stock_control_resolved` (1931〜2020 行) と `main` の `--stock-control` 分岐 (3200〜3300 行)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/tools/pegasus/p3_s4_loop_pegasus.sh — job body (95〜106 行、585〜635 行)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/tools/pegasus/README.md — 「同 job pair (stock 対照、T-2795 / D2172 項 3)」節 (373 行〜)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/decisions.md — D464 (19324 行〜)、D553 (22566 行〜)、D2172 項 3 (68552 行〜)、D2183 (69130 行〜) だけを読む。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-20/t2795-pair-launcher/README.md — §0・§2・§7。

## 依頼 (レンズ A: 既存経路の有無と診断への攻撃)

親は「K2 手動 loop の同 job pair (候補 + stock 対照) を 1 job で投入したところ、stock 側の driver (2 起動目) が `campaign_claim.acquire_claim` の
`O_EXCL` で拒否され (候補側 driver が同 identity の claim を残したまま終了)、stock は build にも到達しなかった。launcher も claim leaf も変えずに
同 job・同 campaign の stock 対照を得る既存経路は無い (P-A)」と診断した。**この診断を最も強い形で攻撃せよ。** 具体的には:

1. `campaign_claim` / `loop._authorize_measurement` / `p3_s4_loop` / job body に、同 job 内の 2 起動目が同 identity の claim を通れる既存経路
   (env・flag・record の一致による再取得、claim root の切替、reservation 不要契約、`_scan_protocol_conflicts` の生存判定が同 path にも効く読み、等) が
   あるか。あるなら file:line で示し、それが D2183 の「同 campaign・同 WAL」を満たすかを言え。無いなら「無い」と書け (不在の断定は読んだ範囲を明記)。
2. 親の機構の読み (診断メモ「機構の読み」節) に誤りがあるか。特に「D464 の生存判定は別 path の同 protocol digest 走査にだけ効き、同 identity path の
   `O_EXCL` は所有者の生死を見ない」の当否を code で確かめよ。
3. 「T-2795 wave の test はこの経路 (実 `run_campaign` の `_authorize_measurement` + reservation 必須契約) を通していない」の当否。
   `orchestrator/tests/test_p3_s4_loop.py` の stock 経路 test と `test_p3_s4_loop_job_contract.py` を見て、通していたなら file:line を示せ。
4. 候補 (1 起動目) が certified で `1 committed` になったこと自体に、この失敗が影響するか (候補の記録の有効性)。
5. 親が見落としている第 3 の失敗原因 (claim 以外) があるか。stdout / stderr の逐語から。

## 出力形式

markdown。見出しは `## 攻撃 1`〜`## 攻撃 5`、`## 成立しなかった攻撃` (成立しなかった項目は正直にそう書け。全項目を無理に成立させるな)、
`## 総括` (3〜6 行、P-A の当否を 1 行目に)。各主張に file:line を付ける。書込みは禁止。テスト実測は親が行うので pytest 緑を要求しない (静的検査でよい)。
予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
