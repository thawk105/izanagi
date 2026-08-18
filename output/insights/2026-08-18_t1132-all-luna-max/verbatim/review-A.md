A-01 — historical v1 の異 model 条件が production で検査されない

- 発火条件: v1 の `consult/sol` と `consult/luna` を同じ model にした commit を `snapshot_authority(..., commit=<sha>)` へ渡す。`other_model == consult_models[0]` だけを検査するため通る。
- file:line: `tools/dev_waves/launch_authority.py:102`、`tools/codex_worker_launch.py:3497`
- 成果物影響: malformed な v1 authority に紐づく過去 receipt が再監査を通り、受理集合が広がる。
- must-fix

A-02 — v2 の段別 model assert が source mapping を検査できない

- 発火条件: `derive_launch` が全 stage を `other_model` から返す、または consult lane の index を取り違えても、v2 の全値が同じため `["gpt-5.6-luna"] * 7` の assert は通る。
- file:line: `orchestrator/tests/test_dev_wave_launch_authority.py:123`、`:190`、実装側 `tools/dev_waves/launch_authority.py:482`
- 成果物影響: 現行 v2 の model 値は変わらないが、段別 routing の回帰を検出できない。v1 の lane swap なら過去 consult receipt の再監査を誤拒否し得る。
- nit

live guard は空文字、部分一致、複数行、fence、HTML comment、U+2028/U+2029、全角記号、NFC 差を静的には fail-closed にしている。`as_dict()` と digest の出力構造も不変。段 6 pin の反転は、旧 `[high]` 受理・`[max]` 拒否から、新 `[max]` 受理・`[high]` 拒否へ対称に変わっており、decoy 検査の削減は見当たらない。pytest は未実走。

## 総括

NO-GO。A-01 は過去 receipt の受理境界を広げる must-fix。