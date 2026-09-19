---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2384-terminal-outer-shape
seq: 2
---

## {{D:terminal-outer-shape-gate-impl}}. 8c formal consumer の FC07 は terminal record の外枠を exact に閉じ、「重複」は projection 内の terminal 件数 1 と読む (D1730 の実装)

**決定:** `orchestrator/campaign/reflux_formal_consumer.py` の `_validate_wal_outcomes()` は、ordered WAL projection の末尾 record を読む前に
helper `_wal_terminal_shape_valid(records)` を FC07 で要求する。helper は (1) 末尾 record の outer key 集合が `{variant, stage, env_tag, ts, payload}` と
exact 一致、(2) `variant` / `env_tag` が `str`、`ts` が bool でない有限数、`payload` が `dict`、(3) projection 内で root `stage` が
`STAGE_COMMIT` / `STAGE_ABORT` の record がちょうど 1 件、を検査する。D1730 が名指した「重複」は (3) の読みで実装し、JSON の重複 key
(上流 `strict_json_loads` / `parse_line` が拒否済み) とは別に扱う。root shadow は (1) の帰結として拒否される。payload の key 集合は閉じず、
非 terminal record の外枠は検査せず、`_wal_trigger` / `_wal_field` / 既存の commit・abort 判定式 / reason code は変えない。
実装 commit は `2579b4638` (Codex author)。一次資料は `output/insights/2026-09-20/t2384-terminal-outer-shape/README.md`。

**理由:**
- D1665 の `_wal_trigger` (FC05C) と同じ検査項目を terminal へ写像したもので、新しい検査層ではない (D1730 の「同じ形」)。
- 実環境の campaign 実走 log 32 file・terminal 490 件で outer 5 key は exact 490/490、`ts` は float 490/490、attempt 世代 16 件は attempt ごとに
  terminal 1 件だった (DW-O13 実測)。gate が要求する値は到達可能で、過剰拒否の実例は 0。
- 「terminal はちょうど 1 件」は producer の終了経路 (`pipeline.py` の各 abort が 1 件 emit して return、abort 済み commit を拒む、recovery は
  active attempt にだけ追記) と整合し、`[trigger, commit, abort]` のような末尾だけ正常な projection を閉じる。同一 stage の重複だけを禁じる読みでは
  `commit → abort` が残る。
- gate を `stage` 比較より前に置いた結果、変異 B-057-M5 の逐語 (`terminal.get("stage")` → `_wal_field(terminal, "stage")`) は exact key 集合の下で
  等価になる (root `stage` が必ず存在し `_wal_field` は root を返す)。M5 が露出した欠陥の再現は「gate 無効化 + M5」の合成変異で示す。

**却下した選択肢:**
- helper に末尾性項 (`terminal.get("stage") in (STAGE_COMMIT, STAGE_ABORT)`) を残す — 既存の outcome 別 stage 判定と過剰決定になり、単独変異の証拠にならない (DW-M03)。件数 1 と既存判定の積で末尾性は成立する。
- `_wal_field(terminal, ...)` を payload 直読みへ置換する — gate 後に死ぬ fallback は `stage` の分だけで、`build_attempt_id` / `verify_configs` / `reason` / `verify` は exact 外枠に含まれず payload fallback が必須。D1730 の「他の判定式は変えない」にも反する。
- `_wal_trigger` と key 集合の定数を共有する — 既存 gate の bytes が変わる。
- 到達不能な述語 (`payload` の型、`ts` の有限性) を落とす — D1665 と同型に保つ方を採り、変異は登録せず到達不能と記録した。

**限界:** certified 選択集合は変わらない (consumer は全検査通過後も `P6Unavailable`)。rejected 側の本番 projection が FC07 で止まる件 (D1715 の限界節) は
解消していない。新 test は canonical-list 経路だけで、frame 経路 (`parse_line` を通る) の外枠は上流に依存し本 wave では実測していない。
abort の attempt 単位一意性は code 経路の確認で、実走の観測は commit 16 件のみ。
