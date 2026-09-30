# 段 6 裁定 7 — md_33 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: chain-2 (fix6 = 2aff9ff54 の bytes、起動器 v5 sha256 1f480f34…) の結果。`runs/smoke-5/result-SMOKE.json`、`runs/main{1..5}-3/`、`runs/ident-3/result-IDENT.json`、`runs/mut-1/result-MUT.json`。実機で見つかった起動器の欠陥 (親の実機 blocker)。

**実測:**
- smoke-5: 10 run すべて期待どおり (stock・E-max 6 本 `pass`、壊し B default 3,273 件・best 3,715 件、U 1 件、API 1 件が `expected-detection`、旧壊し skip-read-recheck が `expected-cycle-detection`)。result の `failed` は同一性 2 組が `equal=false` のため true。
- MAIN-1〜5: rc 0。
- ident-3: 10 組すべて `equal=false`。ただし親が result から読んだところ、10 組すべてで全 TU の命令列 sha256・compile command・`nm`・`strings` の sha256 が一致し、trace 語 (`izanagi_trace`・`CICADA_TRACE`・`CICADA_M_`) の残存 0。違うのは前処理出力の sha256 だけ。起動器の前処理比較は行番号指令の行を除くが空行を残す (`launch_cicada_m.py` の identity)。md_3 の基準は「前処理出力は空行の増減だけ (空行以外の差分行 0)」。
- mut-1: `ValueError: MUT baseline must be a passing SMOKE result` で setup 停止 (smoke-5 の `failed` が同一性で true のため)。

| ID | 裁定 | 処置 (U2、起動器だけ) |
|---|---|---|
| D9 前処理比較が空行を数える | real (must-fix)。基準は md_3 と同じ「空行以外の差分 0」。命令列・compile command・symbol の一致の要求は変えない (弱めない) | 前処理出力は行番号指令と空行を除いて比べ、両側の空行以外の行の差分行数 (unified diff の +/- 行数) と空行数を result に記録する。`equal` は「命令列・command・symbol が一致 ∧ 空行以外の差分行 0 ∧ trace 語の残存 0」 |
| D10 変異の前提が SMOKE の result 全体の合否に依存する | real (must-fix)。変異に要るのは、対応する正例 (壊し B・U・API) が SMOKE で `expected-detection` であることと、その同 cell 対照が `pass` であることだけ | `--smoke-result` の検査を、該当 3 正例とその対照の分類に限る。同一性など他の項目の成否には依存しない |

取り直し: IDENT と MUT を別々の計測用 checkout から並行に 1 本ずつ (各 3 分程度)。SMOKE・MAIN は取り直さない (分類の規則は変えないので結果は変わらない)。
