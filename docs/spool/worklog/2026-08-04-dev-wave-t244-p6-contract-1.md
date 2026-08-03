---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t244-p6-contract
seq: 1
title: [T-244] 択一 7 の P6 契約を設計した — 実測だけを禁止する cut は限界効果ゼロだと 2 レンズが独立に示し、択一 7 の「中間」が存在しないことが判明した (docs のみ、branch worktree-dev-wave-t244-p6-contract、実装差分なしのため変異 matrix と受入全走は対象外)
---

## 本文

- **ユーザー裁定 (worklog (126)) の「P6 を先に設計する」を実行し、設計を確定した。**
  設計判断は {{D:p6-inductive-contract}}、本文と逐語 = `output/insights/2026-08-03_t244-p6-contract/`
- **本 wave の中心成果は、択一 7 の問いの形が変わったことである。** 段 3 の敵対レンズ 2 本が
  **独立に**同じ定理へ到達した — 実測した候補だけを禁止する cut は、その各元が exact-mask cut の
  条件も満たすため、**受理集合への限界効果がゼロ**である。よって「exact-mask と座標 cut の中間」は
  連続体として存在せず、**帰納段を踏むか踏まないかの二者択一**になる。
  「根拠が要る」の正体は帰納の正当化であって測定の量ではない
- **T-244 本体は未解決のままである。** 本 wave が変えたのは「なぜ未解決なのかが構造的に判明した」
  という状態だけで、実装はゼロである
- **親の provisional 裁定 4 件のうち 2 件が反証され、1 件が限定された。** 段 2 と段 3 の 3 者が
  独立に (P1) を反証した — 親は「trigger-gating 軸には gate 述語から anomaly への因果路が
  構造的に無い」と書いたが、正しいのは「**骨格の配線**には無い」までで、
  「**機械が受理する候補集合**には無い」は偽であった。構文 gate は識別子 5 個の regex だけで
  代入・comma 式・副作用を制限せず、parser は「物理 1 行」しか課さない。
  draft v1 §2.3 が既に「parser は任意の非空 1 行 C++ を受理する」と書いていたのを親が見落とした。
  (P2) は「外側 envelope は軸非依存にできるが witness 契約は軸別」へ限定、
  (P3) は「現存軸では real、普遍命題としては refuted」、(P4) は real だが必要条件ではない
- **段 3 の 22 所見は全件 real で、refuted は 0 件であった。** レンズ A = BLOCKER 6 + MAJOR 4 +
  MINOR 1 で NO-GO、レンズ B = BLOCKER 4 + MAJOR 6 + MINOR 1 で受理不能。
  両レンズが独立に到達した中心欠陥 (限界効果ゼロ) を本裁定の中核根拠とした
- **親自身の実測も 2 件が訂正された。** (a) 段 1 の M8 (凍結 pin 閉包) は pin 済み insights を
  4 件と書いたが実際は 7 件で過少だった (`DW-O09` が警告する列挙漏れそのものを親が踏んだ)。
  結論 (本件の 2 dir は非 pin) は不変。(b) M5 の「実 campaign 由来の構造化 anomaly は 0 件」は
  3 campaign からの一般化だった。レンズ A が全 30 本の WAL を census して**結論は追認**したので
  維持し、根拠を census へ差し替えた
- **セッション運用の実測 2 件。** (a) 段 2 の codex `-o` 出力は完了前に部分書き込みされていた
  (00:01 に 31,141 bytes → rc=0 完了時 00:08 に 36,694 bytes)。途中版も末尾が整って見えるため、
  「出力ファイルが存在する = 完了」と判定していれば切り詰めたプランを採用していた。
  `DW-O01` の `.done` 判定が実際に効いた near-miss である。(b) 段 2 を最初 `reasoning=high` で
  起動し、log banner の照合で気づいて `max` へ再投入した (成果物への影響なし)
- **エージェント工数:** codex `gpt-5.6-sol` / `reasoning=max` / `sandbox=read-only` を 3 本
  (段 2 プラン起草 1 本、段 3 敵対レンズ 2 本並列)。いずれも rc=0、`check_codex_output.py` rc=0
- **検査 (実測値):** `tools/check_docs.py` 違反なし、`git diff --check` rc=0、
  `tools/check_ai_provenance.py` の全履歴監査 rc=0、影響テスト 5 本
  (`test_check_docs` / `test_spool_fold` / `test_frozen_artifacts` /
  `test_check_ai_provenance` / `test_s8b_repo_scan_invariant`) が
  **523 passed** (Pegasus gen_S 計算ノード request 882056.nqsv、15.81s)。
  **受入全走と変異 matrix は実装差分ゼロのため対象外**であり実施していない
- **逐語 1 ファイルに可逆最小正規化を適用した。** `s3-lensB.md` の行 3 だけが行末空白 2 個を持ち
  `git diff --check` に抵触したため、`DW-S07` に従い当該 2 byte のみ除去した。
  原文 hash・byte 数・復元法を設計本文の erratum 節に記録し、**復元法は実行で検証済み**である
  (`sed '3s/$/  /'` が原文 sha256 を再現)。可視文字は不変

## 次の一手差分

### 更新

- [T-244] **P1・P6 契約は設計完了 → 帰納段のユーザー裁定待ち**: {{D:p6-inductive-contract}} が
  択一 7 の P6 を明示的帰納契約として設計した。**中心定理 = 実測した候補だけを禁止する cut は
  受理集合への限界効果がゼロ**であり、「exact-mask と座標 cut の中間」は存在しない
  (帰納段を踏むか否かの二者択一)。実装はゼロで、`DW-G04` の発火 artifact も 0 件のため
  設計メモに留めた。**T-244 本体は未解決**。前へ進むには裁定パッケージの 5 件、とくに
  「帰納段を踏むか否か」の裁定が要る。踏まない選択も正当だが、その場合は
  「還流は実現しない」と結論して閉じるべきで未解決のまま残さない。
  設計本文 = `output/insights/2026-08-03_t244-p6-contract/README.md`
  base: e829f45189a619bf2fcaab67920c111ab7f9df12c1f5516fb4853456c77fd164

### 新規

- {{T:trigger-gating-ast-allowlist}} **P1・新規**: trigger-gating の受理集合に reward hack 経路が
  ある。EVOLVE-BLOCK の hole は `TxExecutor::abort()` 内の任意 1 行で、機械 gate は識別子 5 個の
  blacklist だけである。`pro_set_` (`cc/silo/include/transaction.hh` の `std::vector<Procedure>`) は
  blacklist に無く、`makeProcedure` は `RETRY:` の前で 1 回しか呼ばれないため、`abort()` で
  `pro_set_.pop_back()` するとトランザクションが retry ごとに縮み、**serializable のまま
  throughput だけ上がる**。`mrctid_` 経由の別経路も指摘された。auditor (LLM) だけが関所である。
  AST allowlist 化を検討する。受理集合の縮小なので D96 手続が要る (規律 2 に直接効く)
- {{T:sort-integrity-witness}} **P2・新規**: sort 軸の構造化 integrity witness を新設する。
  現行の `permutation_violations` は整数 counter と自然文 notes だけで `verdict=indeterminate` /
  `anomalies=[]` になるため、「同じ理由」の同値関係を書けない。
  {{D:p6-inductive-contract}} を sort 軸へ適用する前提条件
- {{T:placeholder-gate-recursion}} **P2・新規**: placeholder gate (D88) の対象族が非再帰である。
  `tools/check_docs.py` は `directory.glob("*.md")` で走査するため、**insights 652 ファイル /
  63 subdirectory (全体の 81%) が対象外**である (top-level は 155 ファイル)。現時点で hit は 0 件で
  実害は無いが、D88 (3) が「suffix による除外は誰でも作れる全ファイル除外スイッチだから不可」と
  却下した論理が subdirectory にそのまま当てはまる。受理集合を狭める方向の是正
