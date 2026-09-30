---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: dev-wave-vhash-ceiling-vs-sota
seq: 3
---

## 新規

### {{F:fix-ruling-partial-expectation-permission}}. fix 裁定が既存 test の期待値の変更を 1 か所ずつしか許可せず、fix 子が同じ test の別の assert との衝突で 3 回止まった [手順漏れ]

- 事象: md_42 (dev-wave-vhash-ceiling-vs-sota) の段 6 で、FR-2 (見積りと 1 job 300 s の gate) を直す fix 4 が、同じ wave の fix 1 で作った予算 gate の test (M15) の正例と衝突して編集途中で停止。親が正例の入力だけ入れ替えを許可した fix 5 は、同じ test の負例 (単独 7,201 s の build job を allow_over_budget で通す) と衝突して編集 0 で停止。M15 を全列挙した fix 6 は通ったが、FR2-5 (理由の構造化) を直す fix 7 が fix 6 の test の「理由は文字列で受理」と衝突して編集 0 で停止。land 調整役へ FAIL-2・FAIL を出し、4 回目は投げずに運用担保で閉じた。
- 根本原因: 親が fix 裁定で、変える gate の挙動に従属する test の assert を全部並べず、衝突が見えた 1 か所ずつ許可を足した。fix 子は「既存テストの期待値を変更しない」を守って止まるので、許可の漏れの数だけ 1 巡 (10〜20 分) を捨てる。F729 (規則が広すぎる側) とは逆の、許可が狭すぎる側の型。
- 恒久対応: memory `fix-ruling-enumerate-dependent-expectations` (fix 裁定で、変える対象の直後に従属して変わる期待を列挙し、許可する期待と変えてはならない期待を分けて書く)。land 調整役が手順の改修提案 (md_2) に「対象 test 関数の全 assert を裁定に逐語で並べて可否を付ける」を集約する。
- 再発検知: fix 子の報告が「既存テストの期待値と衝突」で止まったら、次の fix を投げる前に、衝突した test 関数の全 assert を裁定へ並べ直す。同じ根で 2 回止まったら 3 回目の前に land 調整役へ FAIL-2 を送る (2026-10-01 のユーザー指示)。

## 再発

### F383

- **再発: 2026-10-01** — md_42 の変異本走 2 回目 (固定 commit の計測用 checkout に `tools/mutation_harness.py` を直接当てる) の走行中に、親が集計のため同じ checkout から driver を import して `orchestrator/campaign/__pycache__` を作り、harness の復元検査が「stale bytecode cache を除去できない」で 8 本目の後に停止した。書いたのは docs ではなく bytecode cache だが、「本走中に同じ作業木へ書く」型は同じ。cache を消し、残り 12 本を新しい spec で 3 回目として完走させた。以後、集計の import は別の checkout から `PYTHONDONTWRITEBYTECODE=1` で行った。

### F71

- **再発: 2026-10-01** — md_42 の変異本走 1 回目で、`unittest` の `subTest` を使う test の失敗が pytest の `FAILED` 行に出ない (`-rf` の要約に test 名が載らない) ため、M1・M2 は他の test の赤だけが抽出されて node の不一致 (MISMATCH)、M8 は抽出 0 件で harness が停止した。login の自走 probe (`python3 <test>` の unittest 出力) では KILLED と完全一致だった。期待 node を dispatch の観測に改め、M8 は自走 probe の結果を証拠に本走から外した。同じ subTest は受入全走の junit 合成も壊した (pytest が subtest 15 個を suite の `tests` 属性に数え、`tools/acceptance_shards.py` の件数照合 `junit-tests` で受領証が出ない)。subTest を外して (9ea29f9df) M1・M2・M8 を取り直し、dispatch の本走で登録どおりになった。新しい test で subTest を使わない。
