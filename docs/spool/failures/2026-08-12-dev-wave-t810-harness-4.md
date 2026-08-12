---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t810-harness
seq: 4
---

## 新規

### {{F:child-cannot-run-tests-defect-survives-review}}. 実装子が全員テストを実走できない wave では、静的レビュー 4 本を通った欠陥が初回実測で出る [テスト代表性]

- 事象: [T-866] / [T-867] の実装 wave で、実装子 5 本とレビュー子 4 本のすべてが計算ノードへ
  dispatch できず (`qstat -Q` preflight が rc=1)、全員が正直に「実装済み・未実走」と報告した。
  親が変異 matrix を投入したところ**基準走が赤**で、これが本 wave のテストの初回実走となった。
  coordinator の 4 node が落ちた。段 3 の敵対相談 2 本、段 6 の敵対レビュー 2 本、
  焦点再レビュー 1 本のいずれもこの欠陥を検出していない。
- 根本原因: 欠陥は「`presence_valid` という同じ名前の値を、coordinator は slot 行列と
  group-root の両方で決め、schema は document 内の行列だけから再計算して不一致なら例外にする」
  という 2 モジュール間の意味の食い違いだった。**どちらのファイルも単独では正しく読める**ため、
  静的レビューの読み方 (所見ごとに file:line を挙げる) では表に出にくい。
  実行して初めて「root だけが不一致のとき必ず例外」が観測できる。
- 恒久対応: `DW-S05-C` の「子の実走は親の全走を代替せず、実走できない子は所見や要件を closed と
  申告しない」に加え、**親が段 6 の変異 matrix より前に焦点走を 1 回実走する**ことを既定にする。
  本 wave では変異 matrix の基準走がその役を果たしたが、基準走が赤だと変異が 1 件も走らず
  (17 件登録・0 件実行)、走行枠を丸ごと失う。
  再照準先は `docs/dev-wave/workers.md` の `DW-S06-C` (統合後の再検証)。
- 再発検知: 変異 harness は基準走が赤なら production write を開始しない
  (`baseline が緑でないため production write を開始しない: status=FAILED`)。
  この fail-closed 自体は正しく働いた。検知の問題ではなく、検知が遅い位置にあることが問題である。

### {{F:m7-frozen-table-shared-coverage}}. 凍結表を共有する変異は超過検出になり単独帰属しない [テスト代表性]

- 事象: [T-866] の変異本走で M7 (retry 表の変異) が MISMATCH。変異は KILLED されたが、
  事前登録した期待 node 1 件に対し実測は 7 件で、期待は実測の真部分集合だった。
  余分な 6 件は `test_post_release_reason_codes_are_post_release_only` の parametrize であり、
  同じ凍結表 (境界と reason code の対応) を schema 側のテストも参照しているため同時に落ちる。
- 根本原因: 凍結表を 1 つの正本として複数モジュールが読む設計では、表を変異させると
  読み手すべてが落ちる。単独の gate を狙った変異が、表の共有によって複数 gate の同時変異になる。
- 恒久対応: `DW-M03` の「過剰決定なら単一理由へ差し替えるか、冗長 gate と明記して単独変異の
  証拠から外す」に従い、M7 を冗長 gate として単独変異の証拠から外した。
  **事後に期待 node を実測へ合わせて書き換えていない** (事前登録を結果へ合わせる事後調整になる)。
  再照準は worklog の新規項へ送った。
- 再発検知: 変異 harness の期待 node 完全一致検査 (`DW-M08`) が MISMATCH として顕在化させた。
