---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-layer3-screening-currency
seq: 1
title: 層 3 の bench-first screening 射影を回帰 pin し、名指し campaign の材料レポートを保存した — B-9 の 3 項を実測で仕分けた (コード + docs、branch worktree-dev-wave-layer3-screening-currency、変異 matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- **依頼は「B-9 を進める」だったが、3 項のうち着手できるのは 1 項もなかった。**
  実測の結果は (a) 済 / (b) 裁定で停止 / (c) 発効条件待ち である。
  - **(a) 対象拡張は 2026-08-25 に閉じていた。** 描画を可能にしたのは schema の 2 段の変更で、
    renderer ではない。`b8318b956` ([T-1291]) が `screening` / `screening_disabled` を
    排他制約つき optional property として足し、`ed251424d` が `settled` を boolean と null の
    2 型へ広げた。**`ed251424d` の commit message 自身が「名指し artifact が build_report を
    最後まで通ることを親が実測で確認した」と記録している。**
  - **(b) 値改変に対する深い一致検査は [T-326] の 2026-08-03 ユーザー裁定 (択 b) で
    「実施しない」と決まっている。** 本体着手には択 (a) の再裁定が要る。**ユーザー手番。**
  - **(c) 機序仮説層 v3 は原料が 0 件。** 凍結設計が要求する `runs/agent_outputs.jsonl` は
    repo 内に存在しない。DW-G04 により実装せず、残件として起票した。
- **論文ストーリー最新版 (2026-09-14) の 6 箇所が、書かれた時点で既に偽だった。**
  §1 / §2 第 3 幕 / §3 / §6 / §7 / §8 の B-9 が bench-first screening campaign を
  対象外あるいは未対応として扱っている。**4 版 (2026-08-26 / 09-02 / 09-05 / 09-14) 続けて
  運ばれた。** 凍結物は編集せず、`docs/paper-story/README.md` の stale 注記へ 1 項積み、
  同 README の「執筆時点で腐っている箇所は無い」を撤回した。F1 の再発として台帳へ追記した。
- **親の brief は 3 箇所で覆された。**
  - 段 2 プランが「4 点すべてに producer が例外を出す負例を置ける」という前提を否定した。
    `_assert_bijection` は source-ref の対応しか検査せず、view の値を比較しない。
    負例は変異 matrix が担うものだった。
  - 段 3 レンズ A が「6f169f90 は admitted」を否定した。実出力は
    `admission_decision.admission_status = historical-not-reclassified`、
    `certifying_input = false`、`current_verifier_conformance = unknown`、epoch `E0` である。
    親は test 定数名 `ADMITTED_HISTORICAL_CAMPAIGNS` を receipt の値と取り違えていた。
  - 段 6 レビュー B が「renderer 側 `ed251424d`」を否定した。同 commit は
    `layer3_report.py` を 1 行も変えていない。
- **段 4 の変異事前登録 5 件のうち 4 件が過剰決定で、実装後に再照準した。**
  既存テストまたは producer 自身の fail-closed が先に殺すためである。初版は erratum として残した。
- **この wave が新しく得た検出力は 3 点だけである** — view の値の完全性、reject の
  `source_ref` の指し先、架空 verification の不在。**それはちょうど producer が強制していない
  3 性質であり、[T-326] が所見として記録した内容そのものである。**
  残る 2 本 (多重集合への参加、件数同一改変の拒否) は `_assert_bijection` が無条件に
  強制しているため単独で殺す変異を構成できず、確認用の pin として置いた。kill には数えない。
- **隣接訂正を 1 件行った。** `docs/glossary.md` の `low-fidelity proxy` 項が bench-first
  screening v2 を「方針採用済み・未実装」と書き続けていた。`docs/phase3.md` は同じ機構を
  2026-07-15 実装済みと書いている。glossary は `LIVING_DOCS` の現況文書なので直した。
- **wave slug と branch 名に未採番の T 番号を使ってしまい、段 6 で改名した (near miss)。**
  禁止は `docs/spool/worklog/README.md` に 2026-09-02 の実測つきで書かれていたが、
  その文書を読むのは段 7 で、branch を切るのは wave 開始時である。**規約が発火点より後の
  文書にあった。** 段 8 で pointer を入れようとしたが、`DW-O20` は 1218/1000 bytes、
  `DW-C01` は 1117/1000 bytes でどちらも節予算に収まらなかった (実測)。予算上限の引き上げは
  既裁定で不可なので、[T-375] / [T-376] と同じ形で起票した。
- エージェント工数: codex 子 6 本 (plan 1・consult 2・author 1・review 2、いずれも
  `gpt-6-astra` / `reasoning=medium`)。fix 子は所見が実装側に無かったため起動していない。

## 次の一手差分

### 新規

- {{T:layer3-mechanism-hypothesis-v3}} **P3・発効条件待ち**: 層 3 の機序仮説層 (v3) を実装する。
  設計は `output/insights/2026-07-16_layer3-mechanism-wiring-design.md` に凍結済みで、
  `runs/agent_outputs.jsonl` (append-only、stage は `planner_proposed` / `coder_proposed` /
  `critic_attributed` の 3 種) を loop harness が書き、renderer が
  `mechanism_hypotheses` を `critic_attributed` の決定論射影として出す。
  **発効条件は「次に agent 出力が生まれる loop 再走と同時」で、現時点で当該 artifact は
  repo 内に 0 件である** (DW-G04 により本 wave では実装しない)。
  着手条件 = `runs/agent_outputs.jsonl` を生む loop 再走が予定されたとき。
  B-9 の残り 1 項である (もう 1 項の深い一致検査は [T-326] が「実施しない」と裁定済み)。
- {{T:dev-wave-slug-numbering-pointer}} **P3・docs 予算待ち**: wave 開始時に読む節
  (`DW-C01` または `DW-O20`) へ「wave slug と branch 名に未採番の T 番号を使わない」の
  pointer を足す。正本は `docs/spool/worklog/README.md` にあるが、それを読むのは段 7 で、
  branch を切るのは wave 開始時なので、現状は規約が発火点より後の文書にある。
  **本 wave の段 8 で実測したところ収容できなかった** — 追記すると `DW-O20` が
  1218 bytes / 予算 1000、`DW-C01` が 1117 bytes / 予算 1000 になる。
  予算上限の引き上げは既裁定で不可 ([T-375] / [T-376] と同型)。
  再訪条件 = [T-959] が L2 の空き枠を設計し収容先ができたとき。
