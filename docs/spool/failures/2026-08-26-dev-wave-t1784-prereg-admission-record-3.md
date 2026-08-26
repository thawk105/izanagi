---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1784-prereg-admission-record
seq: 3
---

## 新規

### {{F:markdown-rendered-position-by-line-regex}}. 文書の描画位置を行単位の正規表現で判定し、同じ箇所が 3 巡続けて両方向に外した [恒真ゲート] [防壁の射程誤認]

- 事象: 事前登録 §5 の表が「実際に描画されるか」を判定する検査を、行単位の正規表現と
  自作の状態機械で書いた。同じ関数が 3 巡連続で欠陥を出した。
  (1) placeholder 判定 `N/?A` を `re.IGNORECASE` の部分一致で使い、`snapshot` `final`
  `internal` `signature` の中の `na` に当たって**正当な値を拒否**した (親の焦点走で赤 7 件)。
  (2) その修正で fence 判定を足したところ、CommonMark では fence opener にならない
  ``` 記号 + info 文字列に backtick を含む行 ``` を opener と誤認し、**正当な文書を拒否**した。
  (3) その修正で、先頭 BOM があると fence opener の `fullmatch` が外れ、
  **fence の内側にある §5 を受理**した (過剰受理。gate を無効化できる)。
- 根本原因: 「その表は読み手に見えるか」は Markdown の**描画結果**の性質であり、
  行の見た目の性質ではない。行単位の照合で近似すると、近似の誤差が
  過剰拒否と過剰受理の**両方向**に出る。どちらに倒れるかは入力の細部で決まるため、
  一方向だけを直すと他方向が開く。
- 恒久対応: (a) 判定対象が描画結果の性質なら、**照合対象を「行」でなく「正規化した文書」に
  そろえる** — 本件では `utf-8-sig` decode で先頭 BOM を除去してから状態機械へ入れ、
  cell は NFKC 正規化してから sentinel を見る。(b) sentinel の一致は
  **Unicode 語境界つき**にして部分一致を禁じる (F181 と同型)。
  (c) 近似で塞ぎきれない範囲は**塞げたことにせず docstring へ逐語で列挙する** —
  本件では inline code span・indented code block・backslash escape 内の `<!--` を
  comment opener と誤認する既知の過剰拒否と、HTML comment 以外の raw HTML block を
  検査しないことを `orchestrator/campaign/p3_b4_admission_record.py` の module docstring と
  関数 docstring に書き、その限界を固定するテストを置いた。
- 再発検知: 変異 matrix の M06 (sentinel 検査の無効化) と、
  `orchestrator/tests/test_p3_b4_admission_record.py` の
  `test_section5_accepts_one_leading_bom_and_rejects_bom_hidden_fence`、
  `test_section5_commonmark_fence_openers_and_marker_lengths`、
  `test_section5_known_over_rejection_for_literal_comment_openers`。
  **過剰拒否は正例テストでしか捕まらない** — 負例だけを増やしても (1)(2) は緑のままだった。
  受理集合を縮小する wave では過剰拒否検出の正例を段 4 で事前登録する ({{D:section5-syntactic-scope}})。

## 再発

### F181

- **再発: 2026-08-26** — 事前登録 §5 の placeholder 検査が `N/?A` を `re.IGNORECASE` の
  部分一致で照合し、`snapshot` `final` `internal` `signature` の中の `na` を「未記入の印」と
  みなして正当な値を拒否した。F181 と同型 (標識は「どこかに現れる文字」ではない) であり、
  Unicode 語境界つきの一致へ直した。段 4 で事前登録した過剰拒否検出の正例が捕捉している。

### F80

- **再発: 2026-08-26** — 段 6 fix 第 1 巡が
  `orchestrator/tests/test_p3_b4_closed_critic.py` の既存負例 2 件
  (terminal だけ昇格したときの start / terminal 不一致、片腕だけ昇格したときの
  evidence class 不一致) を削除し、両腕昇格の 1 検査へ置き換えた。親の fix prompt は
  F80 の定型どおり「既存テストの期待値の反転・緩和・skip・削除を禁じる」を明記していたが、
  **より強い負例へ置き換える形の削除は「緩和」と読まれずに通った。**
  焦点再レビューが実差分で検出し、第 2 巡で 3 段を並存させて復元した。
