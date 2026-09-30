# 段 6 裁定 5 — md_33 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: 親の SMOKE 4 回目 (request 39181.nqsv、Elapse 208 s、`runs/smoke-4/result-SMOKE.json` と `runs/smoke-4/raw/SMOKE/*.stderr`)。対象 = b432b81ed (patch は変えない) と job dir の起動器。実機で見つかった欠陥 (親の実機 blocker、DW-O16 の巡数とは別枠)。fix 前の snapshot は `snapshot-pre-fix5/`。

**smoke-4 の実測:**
- stock・E-max 6 run (default K t4・BD t8、best R t4・BB t8、E-max A10 t8) は `pass`、M の違反 0。
- 壊し U・API は `expected-detection` (各 1 件が帰属)。旧壊し skip-read-recheck は `expected-cycle-detection`。
- 壊し B: default BD t8 は `reached=1255 changed=1041 committed=1255 rts_raised=1041`、違反 `B_RETIRED` 3,294 件 (事象 gc_pool 2,620・reuse_pool 674)。best BB t8 は `reached=1373 changed=1087 committed=1373 rts_raised=1087`、`B_RETIRED` 3,875 件 (gc_pool 3,001・reuse_pool 824・reuse_inline 50)。起動器は `judgment_error: ValueError: break counters out of order` で `fail`。
- 親が raw stderr を awk で数えた帰属: 違反の (thid, tx_seq) が `rts_raised=1` の EVENT の (thid, tx_seq) に含まれるもの = 3,294 / 3,294 と 3,875 / 3,875。(thid, tx_seq, ver) で一致するもの = 908 / 3,294 と 1,077 / 3,875 (EVENT が tx ごとに 1 つの版しか書かないため)。

| ID | 裁定 | 処置 (U2、起動器だけ) |
|---|---|---|
| D5 壊し B の計数の順序検査 | real (must-fix)。壊し B の `committed` は選んだ tx の commit 数 (read-only は必ず commit) で、`changed` (実際に下限を上げた tx) の部分集合ではない。md_3 の形 (reached ≥ changed ≥ committed) を B に当てるのは定義の食い違い | B と MV-B では `reached ≥ changed`・`reached ≥ committed`・`changed = rts_raised` を要求し、`changed ≥ committed` は要求しない。U・API・旧壊しは従来の順序のまま |
| D6 B の帰属の鍵 | real (must-fix)。**段 4 裁定 v2 の B の帰属鍵を改訂する: (thid, tx_seq, ver) → (thid, tx_seq)、ただし `rts_raised=1` の EVENT に限る。** 壊しは tx 単位で読み取り下限を動かし、その tx が読んだ全版が回収の対象になるので、帰属は tx 単位が機序に合う。違反行の `ver` はその tx の read set の要素であること自体が M の照合で保証される (登録済みの要素だけを終了照合する) | B の帰属を `(thid, tx_seq)` ∈ {`rts_raised=1` の EVENT} にする。EVENT の (thid, tx_seq) の重複は拒否のまま。U・API の鍵は変えない |
| D7 分類の再計算 | 採用 | 記録済みの run (result と raw) から分類だけをやり直す `--reclassify <result-*.json>` を足す (build・実行・判定器は再実行しない、判定器の JSON は記録済みのものを読む)。出力は新しい path に書き、元の result は変えない |

**変異 MV-B の kill 判定**も D5 の順序で読む。
