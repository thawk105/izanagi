# 段 6 裁定 1 — レビュー A・B (統合 2 = d149a5b72) の所見 (date 実測 17:09:53 の後に起草)

退避: 統合 2 の snapshot `snapshot-int2.patch` (`git diff 213d411c6 d149a5b72`)。

| 所見 | real/refuted | 採否 | 裁定と単位 |
|---|---|---|---|
| A1 B2 の判定に md_23 の旧予測が残る | real | 採用 | U2: post-B2 と B2 計器版の verdict から結果前の旧予測 (reached == 0 等) を外し、到達・変更・commit・検出を観測値として分類する (裁定 §3.2: post-B2 は検出を予測しない)。md_23 の旧 B2 patch は本 wave で使わない。 |
| A2 probe と changed event の結合が一対一でない | real | 採用 (C++ は変えない) | U2: (tx_wts, key, read_wts) の多重集合として、`changed` event と probe の read 行が完全に一致すること、`committed` event と probe の end=commit かつ changed 済みの事象の多重集合が一致することを要求し、合わなければ fail-closed。 |
| A3 stale-gap の changed が同時点の stock と確定しない | real | 採用 | U1: stock 第 1 段の比較走査の前後で `latest_` を読み、一致したときだけ changed / 非 changed を確定する (不一致は数回やり直し、なお不一致なら確定しない)。確定できなかった事象は `CICADA_BREAK_UNDETERMINED slug=post-stale-gap undetermined=<n>` を終了時に 1 行出す。U2: この行を必須として読み、分類の記録に残す。 |
| A4 post-B1 の「1 つ古い版」が hot の次要素で、疎な hot では物理の直後でない | real | 採用 | U1: post-B1 は `ver->next_` (物理の直後) から確定版を探す (md_23 の B1 の意味に合わせる)。 |
| A5 ABA 論証は stock と共通の寿命前提つき | real (記述) | 採用 | 一次資料で条件付きの結論として書く (親)。コード変更なし。 |
| B1 fig-write の保存で Path を計数値の辞書で上書き | real | 採用 | U2: 変数名を分け、実際の `_save()` を通す作図 test を足す。 |
| B2 図の腕の区別 | real | 採用 | U2: 腕ごとに色か marker を分け、fig-ro は GC ごとに線種を分ける。 |
| B3 estimate が build を二重計上 | refuted | 不採用 | 本 wave は fix 後の binary で独立の build job を投げ直す (smoke の build とは別の node 秒)。smoke (build を含む) と build job を両方数えるのが実際の投入と一致する。 |
| B4 固定 flag と旧壊しへの分岐 | real (nit) | 採用 | U2: `USE_ORIGINAL_POST_BREAKS` と旧 patch 側の分岐を削り、post 用 patch を直接指定する。 |

## 変異の追加事前登録 (fix 前、DW-M01)
- M10: probe と changed の多重集合照合を「少なくとも 1 つ一致」に戻す → 結合の test が kill。
- M11: post-B2 の verdict に旧予測 (reached == 0 を成功条件) を戻す → verdict の test が kill。
- M12: fig-write の保存で source の Path を上書きする → 作図の `_save` を通す test が kill。
- M13: stale-gap の `CICADA_BREAK_UNDETERMINED` 行が無くても受理する → 分類の test が kill。
(段 4 の M0〜M9 と合わせて実装後に単一理由性と期待 node を確かめて確定する。)
