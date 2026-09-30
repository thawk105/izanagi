---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-vhash-manuscript-v2
seq: 1
title: [T-2958] VHash md_41: 本文第 2 稿 — 初稿の後に着地した md_18・md_29・md_31・md_32・md_34・md_36 と D2322 で空欄を埋め、no_room・完了率・構成 E の安全性・区間 GC・batchR の書き方を現況へ揃えた (insight のみ、branch worktree-vhash-manuscript-v2)
---

## 本文

- 依頼: 並行 VHash wave の md_41 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_41.txt`、共通指示 common.txt)。新規の計測・探索・実装・論証はしていない (0 node 時間)。初稿 (md_38) は書き換えていない。
- 正本: `output/insights/2026-09-30/vhash-manuscript-draft-v2/README.md` (第 2 稿。冒頭に初稿からの主な変更の表、付録 E に訂正と追記の一覧)。
- 前提の固定: 題名と重心は案 2 で確定 (D2322 項 1)、付録 A は却下理由だけに短くした。比較相手は ro-gcflag 修正入りを主、stock を同じ round の対照とし、(a) 修正の効果と (b) 本案の効果を別の行にした (D2322 項 2)。起点の (b) の値は修正なしの土台で取ったものと明記した。
- 埋めた空欄: md_18 (§6.10)、md_28 (§6.4、md_29 が統合)、md_29 (§6.7〜§6.10)、md_31 (§3.3.1・§6.4・§6.6)、md_32 (§6.9・§8)、md_34 (§6.3・§6.7)、md_36 (§4.2・§4.3・§4.3.1)。残した空欄は md_33・md_35・md_37・md_39 の 4 つ。
- 範囲を揃えた箇所: `no_room` は abort の確定ではない (md_31 §3.3) / 完了率は操作数型と待機型を分けた / 構成 E の安全性は md_36 §3.2 の W*×GC・境界の読み・A2 の 3 箇所で書き、修理 (md_39) の欄を空けた / 区間 GC の試作の遅さを方式一般の欠点にしない / batchR の伸びしろは stock の欠陥込みで、修正で縮む分への帰属を保留し U0 の勝ち筋にしない / md_31 の図は予備結果とし E-max と方策 c を別の行にした。値はすべて当時の観測として残した (規律 7)。
- 段 6 (read-only review 1 本、事実照合と過大主張の 2 レンズ): must-fix 1 (§6.4 の図が方策 c は成功前の `no_room` だけで D を評価すると描いていた)・should-fix 1 (§6.8 で修正後も残る境界年齢 12.5〜14.3 ms を (a) の行に置いた)。焦点再レビュー 3 巡 (上限): 1 巡目 NO-GO (成功後の D の言い過ぎ、batchR の帰属の断定)、2 巡目 NO-GO (§6.10 が第 2 段の比較相手を D2329 項 3 の二択のまま書いた、冒頭の表の参照)、3 巡目 GO。所見はすべて real、棄却 0。
- 受入の空振り: 縮小受入を 3 回投げ、1 回目は postcheck の競走 (main の前進)、2・3 回目は受入の post-claim merge が取り込んだ main の上で direct gate の fold dry-run が `base-mismatch` で止まった。着手後に第 42 回 /rulings (D2330) が T-2958 の本文を書き換えていたためで、取り込み後の本文から digest を取り直し、同裁定の追記 (初稿の注・付録 A の「ユーザー未決」、`vhash-workload-space` の「H4 の 2 場合」) を更新文に反映した。受入の log の「direct gate 1」は 0 始まりの番号で、2 本目の fold dry-run を指す。
- 親の自己訂正: §6.8 の模式図の記号が md_22 の (a)(b) と D2322 の (a)(b) で重なっていたので図を要因 1・2 に改めた。2 巡目の直しで D2329 項 3 を不正確に言い換えたのを、送る前に逐語へ直した。
- 実 repo を読む検査: 記録 commit の前に `python3 tools/check_docs.py` 違反なし、`python3 tools/spool_fold.py --dry-run` rc=0。受入は縮小受入 (D2316) を land の前に取る。
- エージェント工数: Codex review 1・focus 3 (いずれも read-only、gpt-6-sol・medium)。段 2・3 は省いた (設計択一・正しさ防壁・受理集合に触れない docs-only)。実装面の差分ゼロのため変異 matrix は免除。

## 次の一手差分

### 更新

- [T-2958] **P2・継続**: VHash 論文の本文第 2 稿 (`output/insights/2026-09-30/vhash-manuscript-draft-v2/README.md`) の付録 C に残る空欄 (md_33・md_35・md_37・md_39) を各 wave の着地後に埋め、【確認段で差し替え】を確認段の走行の後に置き換える。md_37 (`output/insights/2026-09-30/vhash-hot-block-cicada-v2/README.md`、D2331) は第 2 稿の着手後に着地したので、次の改版で最初に §6.7 へ入れる。題名と重心 (案 2) と比較相手の書き方 (修正入りを主、stock を同じ round の対照) は D2322 で確定済みで、初稿の冒頭の注・付録 A の「ユーザー未決」は第 2 稿で D2322 に合わせた (初稿は書き換えない)。付録 B の 2 項 (CAS と進行保証、TicToc の timestamp history) は第 2 稿の §8 と §7 の (a) で扱った。`vhash-workload-space` の「H4 の 2 場合」に残る「確認待ち」の記述は、その一次資料を所有する改版で D2322 に合わせる。構成 E の試作の書き込み検査の走査中の回収 (md_36 §3.2) を直した試作で測り直した値が出たら、§4.3.1・§6.2〜§6.4 に追記する (旧い値は当時の観測として残す)。
  base: 7c42ac4bcd4c9b5a56fec92befafa616eca224389cb01cb2d1e3ac353ce82f68
