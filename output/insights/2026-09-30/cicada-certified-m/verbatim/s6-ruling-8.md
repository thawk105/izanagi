# 段 6 裁定 8 — md_33 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: chain-3 (patch 2aff9ff54、起動器 v7 sha256 f293af49…)。`runs/ident-4/result-IDENT.json` (rc 0)、`runs/mut-2/result-MUT.json` (rc 1)。

**実測:**
- ident-4: 10 組すべて `equal=true` (default・best × ycsb・tpcc・bomb・sbomb の pin C 対 pin C + instr + M、default・best の E-max stack の M 無し対 M 有り)。Elapse 204 s。
- mut-2 (Elapse 58 s): MV-B `killed`、MV-API `killed`、MV-U `survived`。MV-U の run は `v_U_MISSING_W = 0`・違反 0、壊し U の診断 `reached=170085 changed=1 committed=1`、集計 `u_installed=822859 u_published=792650 u_w_rows=0`、checks のうち `u_reached` だけが false。

| ID | 裁定 | 処置 |
|---|---|---|
| D11 MV-U が単一理由で kill されない | real (must-fix、DW-M01)。`mv-u.patch` は `traceCommit` の `traceU()` の呼び出しごと止めるので、W 行の計数 (`u_w_rows`) も 0 になり、起動器の生存検査 `u_reached` が別の層として反応した。U の違反が消えたことは U 照合への依存を示すが、kill の判定は「照合の比較だけを常に合格にし、計数は残す」変異で行う (DW-M02: 別層の mask を疑い、実効 gate へ再照準) | U1: `mv-u.patch` を、`traceU()` の中の比較 (設置集合と公開集合、公開集合と W 行、wts) の違反判定だけを常に合格にし、`u_installed`・`u_published`・`u_w_rows` の計数は残す形に作り直す。MV-B・MV-API は変えない |
| erratum | 初回 MV-U (mut-2) の `survived` は消さずに一次資料の変異の表に残し、再照準の理由とともに書く |

取り直し: MUT を 1 本 (3 変異とも、約 1 分)。
