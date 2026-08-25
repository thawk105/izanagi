---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1594-nonattributable-landing
seq: 3
---

## 新規

### {{F:synthetic-fixture-reference-closure}}. 正本へ新しい D 参照と path 参照を書いた結果、合成 fixture の不足で焦点走が 315 件赤になった [テスト代表性] [手順漏れ]

- 事象: `docs/dev-wave/operations.md` の `DW-O18` を書き換えて `D690` と
  `orchestrator/tests/flaky_test_holds.py` を参照させたところ、焦点走が **315 failed** になった。
  実 repo に対する `python3 tools/check_docs.py` は rc=0 で緑だった。
- 根本原因: `orchestrator/tests/test_check_docs.py` の `_build_min_repo()` が作る合成 repo に
  `D690` 見出しと当該 path が存在せず、参照実在検査が毎回 2 件余分に発火した。
  finding 集合を厳密一致で検査する既存テストが軒並み落ちた。**壊れていたのは fixture の完全性
  であって、検査でも実装差分でもなかった。**
- 恒久対応: 合成 repo へ不足していた参照実体を足す。**allowlist や条件分岐で新しい参照だけを
  免除してはならない** — それは受理集合を広げる方向であり、参照実在検査の意味を空洞化する。
  同型の追加として `tools/check_acceptance_reds.py` と `F242` 見出しも足した。
- 再発検知: 正本へ新しい `D<番号>` / path 参照を書く wave は、合成 repo にその実体があるかを
  編集と同じ commit で照合する。実 repo の checker が緑であることは、合成 repo が緑であることを
  含意しない。

### {{F:mutation-single-reason-broken-by-budget}}. 節を 10 bytes 伸ばしたことで、事前登録した変異の赤理由が 2 つになった [恒真ゲート] [手順漏れ]

- 事象: 変異 M3 (`受理は\`child-green\`だけ。` を別文言へ置換) が、exact 不一致の 1 件だけを
  期待していたのに **L2 単節予算超過の finding も併発**し、単一理由性が破れた。
  段 6 のレビュー指摘に応じて `DW-O18` を 988 → 998 bytes へ改訂した副作用である。
  同型で M6 も、合成 repo に `tools/check_acceptance_reds.py` が無いためパス実在検査が併発していた。
- 根本原因: 変異の単一理由性は**変異後の状態**に依存するのに、事前登録時点の節 bytes だけで
  判定していた。予算に張り付いた節では、文言を増やす向きの変異が予算検査を道連れにする。
- 恒久対応: 予算に張り付いた節へ変異を登録するときは、**全変異の変異後 bytes を実測**してから
  登録する。増やす向きが超過するなら削除形へ変える。注入先の節も、余裕のある節を選ぶ
  (本件では `DW-O19` = 998 bytes を避け `DW-O16` = 552 bytes を使った)。
- 再発検知: 変異事前登録の直前に、各変異の変異後 bytes と併発しうる検査層を 1 件ずつ書き出す。
  `DW-M01` の「同じ入力を拒否する層が前後に無いこと」は、**予算検査も層に数える**。

### {{F:stale-authority-points-at-removed-tool}}. 機構から削除済みの判定器を正本が指し続け、どの checker も検出しなかった [ドリフト] [恒真ゲート]

- 事象: D690 決定 2 で `tools/dev_wave_wait.py` から判定器の自動起動経路が到達不能化された後も、
  `DW-O18` は「rc=0+non-attributable-only は受理成功」と**存在しない受理経路**を正本として
  書き続けていた。実測で `grep -c check_acceptance_reds tools/dev_wave_wait.py` = 0。
- 根本原因: 正本と機構の対応を検査する仕組みが無い。docs の byte 予算・節構造・孤児検査は
  「書式が正しいか」しか見ず、「書いてある道具が今も存在し、書いてある挙動をするか」は見ない。
  この空白が、受入が赤で戻った wave のセッションごとの手作業回避を生んだ。
- 恒久対応: 当該記述を削除し、廃止語 (`non-attributable-only`、`tools/check_acceptance_reds.py`) を
  `docs/dev-wave/operations.md` の可視本文から 0 件必須とする禁止語検査を新設した。
  **backtick の有無で迂回できないよう平文 substring で照合する。**
- 再発検知: 機構から経路を削除する wave は、その経路を記述している正本を同じ commit で
  検索して消す。禁止語検査は「消したことを固定する」だけで、「消し忘れを見つける」ことはしない。
