# 段 6 裁定 4 — md_33 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: 親の SMOKE 3 回目 (request 39102.nqsv、Elapse 191 s、`runs/smoke-3/result-SMOKE.json` と `runs/smoke-3/raw/SMOKE/*.stderr`)。対象 = 42c8eacfa。実機で見つかった欠陥なので DW-O16 の焦点再レビュー 3 巡の上限とは別枠 (親の実機 blocker)。fix 前の snapshot は `snapshot-pre-fix4/`。

**smoke-3 の実測 (親が result と raw stderr から読んだ値):**
- stock・E-max の 4 run (default K t4、best R t4、best E-max A10 t8、default BD t8) は `pass`、M の違反 0。
- 旧壊し skip-read-recheck (M の上) は `expected-cycle-detection`、witness 25 件が帰属。
- 壊し U: `CICADA_BREAK_FIRED … reached=166391 changed=1 committed=1`、違反行 1 件 `kind=v_U_MISSING_W … outcome=commit`。壊し API: `reached=764338 changed=1 committed=1`、違反行 1 件 `kind=v_API_EXTERNAL … outcome=pending`。壊し B (best BB t8): `reached=346 changed=7 committed=346 rts_raised=7 gcflag_set=346`、違反行 21 件 `kind=v_B_RETIRED … event=reuse_pool`。この 3 run は起動器が `ValueError: invalid M kind/outcome` で解析を拒否した。
- 壊し B (default BD t8): `reached=162 changed=1 … rts_raised=1`、M の違反 0 (未発火)。

| ID | 裁定 | 処置 (U1) |
|---|---|---|
| D3 違反行の `kind` に `v_` が付く | real (must-fix)。author-common.md の契約は `kind=<KIND>` (接頭辞なし)、集計 key だけが `v_<KIND>`。起動器の拒否は正しい | 違反行の `kind` を接頭辞なしの 13 種に直す。集計 key は変えない |
| D4 壊し B が default で到達しない | real (must-fix)。待機の最初に 1 回だけ下限を上げるので、待機中に進む `MinWts` に追随しない (default は 162 回中 1 回しか上げられず違反 0) | 待機 loop の各回 (50 µs ごと) に `ThreadRtsArray[thid]` を `max(現在値, MinWts−1)` へ上げ直し `GCFlag[thid]` を立て直す。選ぶ tx の間引きを 1/1024 → 1/64 にする。`rts_raised` は「1 回以上実際に上げた tx の数」とし EVENT の `rts_raised=1` 行の数と一致させる。待ち時間 (5 ms) は変えない |

起動器 (U2) は変えない。変異 `mv-b` は壊し B の変更後も当たることを U1 が確かめる。
