# [T-2566] 段 1 brief — 静的 tail 本走 driver

**研究前進.** 論文 B-10 の静的 backoff 右 tail (物理 1000 マイクロ秒超) の記述的特性化は、
事前登録 `docs/b10-backoff-static-tail-preregistration.md` §8.1 の投入前条件 5 件が未充足のため
本格 cohort を投入できない。本 wave が 5 件を実装し実測で示せば、本走投入の唯一の blocker が外れる。
完了判定 = 5 件それぞれについて production 経路を通す probe が緑になること。

**scope.** (1) 同書 §5 の spec を parse する consumer と、その発火の実測。(2) 性能測定の rep ごとの
整数カウンタを WAL へ保存し、abort 率の再計算経路を実測。(3) observation ごとの出所 field を
WAL envelope から導出。(4) 1 cell あたり 5 本の正しさ記録の発行。(5) 正しさ検査の mode 座標の記録。
(6) 上記を使う本走 driver・loader・report materializer (`run_kind` = `t2500-tail-formal`、
report schema = `t2500-backoff-static-tail-formal-report/v1`、成果物 stem =
`t2500-backoff-static-tail-formal`)。

**scope 外.** 本走の投入。格子・動作点・判定値のコード定数による置換。既存 3 系列
(`extended` / `t2266-tail` / `t2418-explore`) の受理集合・成果物・report schema・`EXTENDED_SWEEP_US`
の変更。事前登録文書の bytes 変更。仮想リスク向けの gate・検査・台帳・一般化の追加。

**確定済みユーザー裁定.** D1921 (格子は表現上限起点の半オクターブ、境界参照 1000 は飽和述語に入れない)。
D1922 (3 分類 + 整数カウンタからの再計算、丸め値 fallback 禁止)。裁定項45 (`check_docs.py` へ
本文検査を足さない)。実装面の著者は Codex `role=author` (D95 決定 2)。

**不変条件.** 規律 2 を緩めない (anomaly 検出は即 reject、正しさ反復を時間都合で減らさない)。
既存 3 系列の受理集合・成果物・report schema を 1 bit も変えない。格子・動作点・測定順・判定値は
spec から引数として渡す。`document_blob_sha256` は file の raw bytes の SHA-256 であって Git blob ID
ではない (先例 `b10_backoff_shape_sweep.py` の `prereg_blob_sha` と別物 — 取り違え禁止)。
`spec_sha256` は marker 行の内側から code fence 2 行を除いた UTF-8 bytes・LF・末尾改行 1 つ・
canonical 化なし。抽出 bytes がそのまま JSON として parse できることも要求する。

**実測済みの前提** (親が今回 explore の現物で再確認。詳細は `02-measured-premises.md`)。
explore の WAL は 1 cell あたり `verify_done` 1 本、`abort_counts_` は 0 件、`bench_done` payload に
rep ごとの整数カウンタが無い。`verify_done.payload.workload` は `{"tag": "legacy"}`。
§8.1 の 5 件はいずれも現状未充足であることを確認した。覆す新事実は無い。

**(P1) 親の provisional 裁定・攻撃対象.** (P1-a) 実装は新規 module に置き、exact 閉包の登録簿へ
明示登録する (既存 driver への 4 つ目 run_kind 同居は既存 3 系列の受理集合を壊す危険が大きい)。
(P1-b) 実測の下限は、新規の計算ノード計測を行わず、既存 explore の実 WAL・実 campaign lock・
実 CCBench stdout bytes を入力に production 経路を通す probe とする。(P1-c) rep ごとの整数カウンタは
`calibrator/runner.py` の rep observation に載せ、`bench_done` の payload key 閉包を最小拡張する。
(P1-d) 1 cell 5 本の正しさ記録は既存の correctness workload repetition 機構で満たす。

**成果物の形.** 本走 driver・loader・report materializer と、その単体テスト。投入前条件 1 件につき
probe 1 本と実測ログ。既存 3 系列の受理集合が不変であることを示す焦点走の結果。

**並列分割方針.** 段 5 は 3 所有に分ける — (A) spec consumer と 2 つの hash 定義、
(B) rep ごと整数カウンタの保存経路と再計算、(C) driver・loader・report と正しさ反復・mode 座標。
段 6 は敵対レビュー 2 本 + 変異 matrix + 受入再走。
