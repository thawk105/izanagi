# 段 1 brief への追補 (親が段 2 の指摘を受けて訂正した前提)

`brief.md` の以下の記述は**誤り**である。攻撃の対象は訂正後の前提とする。

## 訂正 1 (real、親が実測で確認) — 凍結 baseline は live 再生成される

`brief.md` の不変条件は「`test_reflux_originless_compatibility.py` の凍結 baseline が持つ planner sha は
`output/` 保存済み journal 内の値なので role file 編集では動かない」と書いた。**これは誤り。**

親が同 file を読み直して実測した事実:
- `test_reflux_originless_compatibility.py:60-105` は `A.run_trial(**arguments)` を**実走**し、
  生成された `report.json` と `attempts.jsonl` から bundle を組む。保存済み `output/` は読まない。
- したがって `journals/*/*/provenance/role_file_sha256` は **live な `planner-v4.md` bytes** から計算される。
- 同 file `:574-595` に `_extend_t2145_role_source_baseline()` という先例があり、T-2145 の auditor
  source pin 変更時に同じ baseline を追随させている。

**scope に追加する**: `orchestrator/tests/test_reflux_originless_compatibility.py` へ T-2145 と同型の
T-2249 追随 helper を足す。これは新規 gate の新設ではなく、同一変更の consumer 追随である。

## 訂正 2 (real) — planner の編集は 2 行

`brief.md` は「`planner-v4.md:35` の行を削除」と書いたが、`:34` の `"abort_rate_pct": 7.9,` の
trailing comma を同時に除かないと入力例が不正 JSON になり、`tools/check_codex_agents.py` の
`json.loads()` が拒否する。編集は `:34-35` の 2 行をまとめて行う。

## 訂正 3 (real) — 変更 file 数

`brief.md` の「4 file」は誤り。role 2 + ledger 1 + adapter 2 + originless baseline 1 = **6 file**。

## 訂正 4 (real) — 研究前進の主張は planner に限る

`p3_autonomous_workload_trial.py` の `ROLE_FILES` は coder に
`coder-v4-autonomous-trigger-gating.md` を結んでおり、`coder-v4-autonomous.md` ではない。
よって「稼働中の試行の因果入力に誤りが残っている」という研究前進の主張が成り立つのは
**planner-v4.md についてだけ**である。`coder-v4-autonomous.md` 側は、稼働 consumer を持たない
role 定義の記述是正であり、主張の強さが違う。

## 親の独立実測 (dogfood、段 2 の主張とは別に親が測った)

repo 外の probe で `orchestrator.codex_roles.spec.expected_adapters(<worktree>)` を呼び、
返る 14 adapter 全部を on-disk bytes と比較した結果は **mismatch=0**
(`coder-v4-autonomous.json` 9719 bytes / `planner-v4.json` 8532 bytes、いずれも SAME)。
つまり「`expected_adapters()` の出力で adapter を上書きする」手順は、現行 bytes を byte 一致で
再現する経路として実測済みである。着手前の `tools/check_codex_agents.py` は rc=0。

## 親の provisional 裁定 (P2) — 攻撃対象

**(P2)** role 本文・ledger pin・adapter の**全 surface を一斉に旧 bytes へ戻す coordinated rollback**
は、既存テストでは SURVIVED になる見込みである (既存テストは coder 例の `delta_pct is None` を
独立 literal として pin していない)。親の provisional 裁定は
「新規検査の追加は scope 外なので SURVIVED を等価変異として記録し、KILLED 必須にしない」。
この裁定が規律 2 を緩めることにならないかを検査せよ。
