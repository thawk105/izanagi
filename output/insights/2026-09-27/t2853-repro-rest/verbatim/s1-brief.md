# 段 1 brief — [T-2853] 再現パッケージの残り (新しい論文根拠 job dir の写し、R2 の投入単位と Elapse 見積り)

- 研究前進: VLDB EA&B の再現パッケージ (P6)。新しく論文根拠になった 3 系列 (T-2850 試走 v2・T-2849 MOCC 疎通・T-2865 段階 F) の実験データを job dir の撤去 (F1034 型) から守り、R2 の計算確認に出す見積りを Elapse 単価で揃える。完了判定 = 写しの sha256 全件一致と、図ごとの node 時間表 (出所の種別付き) と投入単位の推奨が insight にあること。
- scope: (i) 写しと照合 (repo 外 `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260927/`、前回の `archive_copy.py` を同一 bytes で再利用)。(ii) 計画稿 §2・§4 の所要を (a) Elapse で置き換え、投入単位を決める。計算の投入はしない。
- 確定済み裁定: D2212 項 4 (1 タスクの job 合計 2 node 時間以上は投入前確認)、D2219 項 1 (見積りは job Elapse の実測単価)、D320・D2212 項 6 (粗い provenance、凍結 chain は足さない)、D2211 項 10・D2212 項 5 (A-1 の新 attempt は保留)。公開範囲の最終確定は扱わない。
- 不変条件: 原本・submit checkout・trace 保全先は読むだけ。写しは正本ではない。gate・検査・台帳・一般化を足さない。repo のコード変更 0。
- 変更面 (repo): `output/insights/2026-09-27/t2853-repro-rest/README.md` と `verbatim/`、`docs/spool/` の worklog fragment。repo 外: 保存先 dir と `izanagi-repro-archive/README.md` の表 1 行。
- (P1) 写す範囲 = 前例 (2026-09-23 の b5-pilot など) どおり「job dir 全体から submit checkout (repo の写し) を除く」+「checkout 内の未追跡 campaign 原本・claim」。論文根拠かどうかの選別はせず、小さいので取りこぼしを避ける。T-2850 は走行 dir `dev-wave-t2850-trace-concurrent-verify/trial-v2/` (trees を除く) と集計 dir `dev-wave-t2850-trial-v2-followup/` 全体。trace-concurrent-verify の実装 wave の記録 (s2〜s6、変異、submit-tree 等) は試走 v2 のデータでないので写さない。
- (P2) 旧機 3 図 (fig1 の P2-2 表・fig2b・fig4) の Pegasus 単価は、同じ動作点 (48 thread・100 万 record・3 s・5 反復) の B-10 格子の Elapse を variant 1 つあたりに割った値 (104.5〜115.6 s) を当てる「試算」とする。(a) そのものではない。
- (P3) 投入単位の推奨 = 図 1 本 (後継図が前身を含む fig8b ⊃ fig8 はまとめる)。束ねない。確認要否は単位ごとに Elapse の和で判定。
- 受入・実測環境: 計算ノードは使わない (login で読み取り・写し・sha256 のみ)。受入全走は DW-S04 どおり段 6 で 1 回。
- 分割: 子は段 6 の read-only codex review 1 本 (軽量版、一次資料から事実を再抽出する docs wave)。調査子 (Explore sonnet) 3 本は棚卸しのみで、値は親が実測で照合済み。
