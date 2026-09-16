---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t1642-trace0-scope-wording
seq: 1
title: [T-1642] TRACE=0 検査の射程文言を「必要条件の一つ」へ統一した — 効いたのはコメントでなく成果物 JSON の 1 文 (コード + docs、branch worktree-dev-wave-t1642-trace0-scope-wording、変異 matrix = 登録可能な変異なし)
---

## 本文

- **裁定の履行**: D780 決定 1 (2026-08-25 ユーザー裁定、/rulings 全件の択 (c)) に従い、
  成果物側の射程文言を統一した。決定 2 の別防壁 (実 compile command・全 TU・link object・
  trace symbol/data・build receipt の結合) は [T-1644] と同じ閉包でだけ起こすという順序に従い、
  本 wave では着手していない。
- **親の閉包が 1 箇所を取り逃がしていた**。段 1 のアンカー表は `D297` を検索鍵に使ったため、
  D297 の語を含まない `tools/pegasus/mocc_trace_pilot.sh:357`/`:426` の
  `Certifies the TRACE=0 preprocess identity gate.` を対象から落としていた。段 3 の敵対相談が
  「A1・A6 はコメントで成果物に出ず、この 2 行だけが artifact classification manifest という
  成果物 JSON へ出る」と指摘し、親が段 4 で編集対象へ追加した。**D780 が言う「成果物側の文言」に
  最も直接当たるのはこの 2 行だった。**
- **親の見立ての誤り**: 段 1 で親は「主張の強さが実際に下がるのは A6 (pilot の hard gate コメント)
  だけ」と書いたが、段 2・段 3・段 6 の 4 者が独立に「`hard gate` は失敗時の実行禁止の説明で
  あり、成功時の十分性を述べていない」と判定した。実際に弱まるのは A7 だけである。
- **段 6 敵対レビュー 2 本は must-fix ゼロ、nit 5 件。** 不採用にしたのは (a) A1 の compiler 留保の
  言い回しの変更、(b) A7 を 2 文に分ける案 — D780 決定 1 の逐語自体が「この検査は…必要条件の
  一つである」という構文なので、現行実装の方が逐語に近い。採用したのは記録側 3 件
  (横断 consumer 2 件の追記、過去記録の非編集理由の限定、「残った過大な表現がない」とは
  報告しないこと)。
- **変異事前登録はゼロ**。実装面の差分はあるので DW-S04 の免除条件には当たらないが、
  文言を守る実効 gate が repo に存在しない (placeholder 検査は文書族、禁止語検査は operations 本文が
  対象で `tools/` の文言に及ばない) ため、DW-M01 の単一理由性を満たす変異を登録できない。
  gate の新設は D780 決定 1 と依頼の scope 外。免除ではなく「登録可能な変異が存在しない」記録である。
- **実装子の `bash -n` が `guard_bash` に拒否された** (対象が Pegasus の dispatch-required 実行体)。
  pilot の構文検査は親の焦点走に含まれる `orchestrator/tests/test_mocc_trace_job_contract.py:76` が
  唯一の経路である。
- **受入 1 回目は非帰属赤 2 件で rc=70 だった**。`test_t1259_qsub_env_delivery_probe` の setup で
  `git ls-files --others` が 30 秒 timeout、`test_s8c_preregistration_predicates` が real-repo flock の
  deadline 超過。どちらも並行受入との競合で、本 wave の差分 (docstring・コメント・JSON の 1 文) とは
  因果が無い。`DW-O18` に従い 2 件を単独再走して 269 passed (rc=0) の非再現を確認し、load の下降局面で
  受入を再走して 23961 passed, 68 skipped の child-green を得た。hold 登録はしていない。
- 詳細は `output/insights/2026-09-16/t1642-trace0-scope-wording/README.md`。

## 次の一手差分

### 完了

- [T-1642] 成果物側の射程文言を D780 決定 1 の趣旨で統一した (checker の module docstring、
  pilot の gate コメント、artifact classification manifest の reason 2 箇所)。
  checker の受理集合・拒否条件・report schema・GUARANTEE 定数は不変。
  remaining: none
  base: bec39084fef206b53cf1a5a2ee39b32bab04dab8bfdeb3681ca7d8429620816e

### 新規

- {{T:past-record-scope-annotation}} **P3・ユーザー裁定待ち**: 過去記録の見出しと結果だけを
  引用したときに射程を過大に読める箇所 (`output/insights/2026-08-11/t816-fn2-trace-v2/README.md:38`
  の「規律 1 (TRACE=0 側の等価性)」見出し + `:40` の 3 本 pass、
  `docs/archive/worklog-phase3-0811-445.md:26` の「規律 1 の機械検証」+ 同結果) へ、
  日付つきの射程注記を追記するか。どちらも本文全体では完全除去を主張しておらず
  (前者は同文書 `:120-121` が保証を限定して名乗る)、[T-1642] の親は必須訂正としなかったが、
  段 3・段 6 の 2 者が追記を推奨した。追記するなら 1 行で閉じられる。遡及改変ではなく追記訂正。
