# 親 brief erratum 1 — 段 3 が是正した記述 (2026-08-06)

- `authority: none`
- `default_effect: no-state-change`
- 本文書は同ディレクトリ `brief.md` の erratum である。**初回の brief 本文は書き換えない。**

段 3 の 2 レンズが独立に指摘し、親がコードで再照合して採用した是正である。判定・裁定の
前提として使うのは brief 本文でなく本 erratum の値である。

## E1. 実測 8 の待ち時間が誤り (8 秒 → 16 秒)

brief 実測 8 は「1 attempt あたり subprocess 10 本 + sleep 8 秒」と書いた。正しくは
`for attempt in range(1, 6)` が `attempt < 5` のときだけ 2 秒 sleep するので 1 command あたり
4 回 × 2 秒 = 8 秒、command は `racctjob` / `racctreq` の 2 本なので **1 回の
`_collect_accounting` あたり 16 秒**である。同 brief の (P3) は 16 秒と書いており、本文内で矛盾していた。

さらに射程も過剰だった。(a) `_collect_accounting` は request ID を得た attempt でだけ呼ばれる。
(b) `signal_observer.py` 側は permission を初回で検出して停止するため、5 回 retry しない。
(c) 16 秒は固定 sleep の分だけで、subprocess の timeout 上限を含む総所要ではない。

## E2. 実測 6 の「`.e` は manifest 束縛付き」が全経路では成り立たない

brief 実測 6 は `.e` を「manifest 束縛 + sha256 + size 照合付きで保存・解析されている」と書いた。
保存経路については正しいが、**判定に使う `valid` は manifest 束縛を要求しない**。
`_saved_nqsv_stderr_accounting` は `scheduler_root.glob("*.e")` で未改名ファイルも候補に入れ、
戻り値の `valid` は `bool(matching_blocks) and not errors` である。manifest 束縛を要求するのは
`termination_cause_evidence_available` と `termination_mechanics_evidence_available` だけで、
resolve の終端実証 path 3 は弱い方の `valid` を qstat 不在と組み合わせて採用する。
親はこの箇所を自分でコード照合し、real 所見として採用した (裁定 R-10)。

## E3. (P2) の「唯一の外部会計信号」が字義上は偽

`rbudgetcheck` を「sudo 不要な唯一の外部会計信号」と書いたが、`qstat -J -f` の保存 raw にも
scheduler 由来の job 単位 Memory / CPU Time counter が存在する。ただし終端後は消え、
Started / Ended / Elapse を持たず、現行 parser も host 列しか読まないため、
**request 束縛の最終会計の代替にはならない**という結論自体は変わらない。
`rbudgetcheck` が group 単位で request 束縛不能である点も変わらない。

## E4. 成果物影響の射程を「直接 schema consumer」まで狭める

brief は「CC 合成の certified 選択・材料レポートへは一切流れない」と書いた。**直接の
schema consumer が probe controller / observer と証拠 artifact に閉じている**ことは段 2 が
確認したが、これは因果的に無関係であることの証明ではない。段 3 レンズ A は、T-399 の
authoritative attempt が D130 条件 3 を前進させ、[T-360] の変異 harness 計算ノード束ねの
着手前提として明記されている経路を挙げた。会計・cause 設計がその attempt の authority を
反転させれば研究状態の側は動く。よって主張は
**「直接の schema consumer は存在しない。研究状態の依存は残る」**まで狭める。

## E5. 実測 4 は維持 (段 2 が一次資料で裏付けた)

brief 実測 4 (「`.e` に job 単位 record は無い」) は、段 2 が 2-node leg (t361-flock,
`nodes=2`) の実 artifact で裏を取り、request block を持つ `.e` が 1 個 + size 0 の `.e` が 1 個で、
`Number of Jobs: 2` という総数の 1 行があるだけだと確認した。**是正不要**。
brief が「未実証」としていた点だけが解消した。
