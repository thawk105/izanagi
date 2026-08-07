---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t597-budget
seq: 2
---

## 新規

### {{F:mutation-harness-self-reference}}. 変異対象が変異 harness 自身のとき、全ファイル走行の赤が単一理由でなくなる [計測汚染] [誤前提]

- 事象: [T-597] wave の変異 matrix で、`tools/mutation_harness.py` の fail-closed 分岐
  (`rc != 0 and not failed` → `PARSE_ERROR`) を消す変異 M2 が、`PARSE_ERROR` / rc=16
  (dispatcher infrastructure failure) を返して harness 全体を停止させた。M1 は正常に KILLED していた。
- 誤判定: 親は最初これを共有ログインノードの外乱と判断した (実際に別 wave 2 本が同時に
  `run_tests.py` を走らせており、artifact の「生存中の予約」も非 0 だった)。**これは誤りである。**
  生存中の予約 0 の静穏窓で再現し、harness を介さず手で変異を当てても再現した。
- 根本原因: 変異対象が変異 harness 自身であるため、fail-closed 分岐を消すと**テスト内で動く
  harness が abort しなくなり**、入れ子の pytest 実行が増えて外側 bounded scope が倒れる。
  したがって全ファイル走行の赤は「テストが検出した赤」と「暴走で実行枠が倒れた赤」の混合であり、
  `DW-M03` が要求する単一理由性を満たさない。過剰決定された fixture の一種である。
- 影響: この赤を KILLED と数えれば偽の検出力を、外乱と数えれば偽の無害を記録する。
  どちらも変異台帳の値を汚す。
- 恒久対応: `DW-M02` の「実効 gate へ再照準」を適用し、対象 nodeid だけの narrow 走行で測り直す。
  初回結果は消さず erratum として台帳に残す (本 wave は `mutation-ledger.json` に残置し、
  再照準後の実測を `mutation-narrow.json` へ分離した)。再照準走行も `DW-O19` の復元規律
  (clean 確認 → 単一変異の `git diff --stat` 確認 → 復元 bytes 照合 → clean 確認) に従う。
- 再発検知: 変異走行で `rc=16` など runner の infrastructure 系 rc が出たとき、
  静穏窓での再走と harness 非経由の手動再現の**両方**で切り分ける。片方だけで外乱と結論しない。
- 近縁: F71 (抽出 0 件を SURVIVED に倒す恒真ゲート)、F41 (測定値は測った checkout を併記する)

## 再発

### F146

- **再発: 2026-08-07** ([T-597] wave、独立 2 例)。docs-only の縮約に対する fix が、
  同じ wave 内で新しい不整合を 2 回生んだ。(1) `DW-S09` の 2 文削除を 1 文で復元したところ、
  成功 status 集合 (`landed` / `already-landed`) を `core.md` と `operations.md` で
  **二重管理する退行**を作り、焦点再レビューが検出した。`DW-O23` を参照する形へ変えて解消。
  (2) `DW-S06-C` から対応表要求の文を削除したことで、`docs/failures.md` の本 F 自身が
  担い手として指す `DW-S06-C` が **stale になった**。現在の担い手は `DW-O16` である
  (条件 16 = 焦点再レビュー直前に必読、かつ「表なしで root cause が閉じたと判定しない」まで持つ)。
  canonical の既存 bytes は通常 fold では置換できないため、本追記で現担い手を明示する。
