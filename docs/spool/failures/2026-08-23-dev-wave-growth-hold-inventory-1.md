---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-growth-hold-inventory
seq: 1
---

## 新規

### {{F:literal-expectation-table-escapes-identifier-grep}}. registry の期待表を literal 複製する consumer が識別子 grep から漏れた [手順漏れ] [テスト代表性]

- 事象: 親は保留 registry を編集する前に pin 閉包を監査し、`key_sha256` /
  `growth_test_hold_key_digest` / 件数リテラルで grep して 3 箇所を挙げ、閉包を取ったと判断した。
  段 3 の敵対 2 レンズも同じ 3 箇所しか挙げなかった。実際には
  `orchestrator/tests/test_hold_inventory.py` が `(node_id 集合, hold_axis, reason 本文)` の
  期待表を独立 golden として literal で持っており、digest も件数リテラルも使っていなかったため
  どの識別子 grep にも掛からなかった。段 5 の実装子が実際に registry を import して初めて発見し、
  親の焦点走で 2 件の赤として顕在化した。
- 根本原因: 閉包の探索を「その値を計算する識別子」で行い、「その値を**複製している**箇所」を
  探していなかった。独立 golden は定義上、元の識別子を参照しない。
- 恒久対応: {{D:growth-hold-release-by-approved-exception}} の判定手順ではなく、焦点走の
  consumer 拡張規則へ寄せる。変更した production file の consumer を参照関係で引くことに加え、
  **その file が公開する値を literal で複製している consumer** も探す。実体は
  `docs/dev-wave/operations.md` の焦点走 consumer 拡張節。
- 再発検知: 変更 file の consumer を含む焦点走を段 6 で必ず実走する。本 wave では
  この焦点走が赤 2 件として実際に検出し、受入全走まで持ち越さなかった。

### {{F:zero-diff-worktree-does-not-clear-inherited-env}}. 差分ゼロの作業ツリーで再現しても環境変数は継承されるので repo 側の性質の証明にならない [計測汚染] [テスト代表性]

- 事象: 親の焦点走で、本 wave の変更と無関係な node が赤になった。subprocess の pytest 出力を
  `(\d+) passed(?:,| in )` で照合する検査が、出力に ANSI 色が入り `103 passed` の直後が
  reset になるため一致しなかった。並行セッションは同じ赤を差分ゼロの main 作業ツリーで再現し
  「repo 側の決定的な赤」と周知した。実際の原因はセッション環境の `FORCE_COLOR=3` であり、
  同変数を外すと同じ node は緑になる。修理前 main に対する受入全走の実測は
  14,310 passed / 96 skipped / 赤 0 件で、この赤は受入では最初から発火していなかった。
- 根本原因: 「差分を消せば repo 側の性質だけが残る」と仮定した。作業ツリーの差分を消しても
  同じセッションの環境変数は継承されるため、環境起因の赤は差分ゼロでも再現する。
  再現したこと自体が repo 側の証明にはならない。
- 恒久対応: 親の焦点走を `FORCE_COLOR` / `COLORTERM` を外して走らせる。実体は
  `docs/dev-wave/operations.md` の親のテスト実行節。帰属判定では、差分ゼロ再現に加えて
  **実行環境を変えた再現**を要求する。
- 再発検知: 同じ node を環境変数を外して単独再走し、緑になれば環境起因と確定する。
  本 wave はこの手順で確定させ、無関係な修正へ時間を使わずに済んだ。

### {{F:background-completion-notice-precedes-producer-exit}}. 背景 job の完了通知が producer の完了より先に届いた [手順漏れ]

- 事象: 親が焦点走を背景投入したところ「completed (exit code 0)」の通知が届いたが、
  ログは 308 byte で終端行が無く、`pgrep` で走行スクリプトと pytest がまだ生存していた。
  通知を完了と読むと、未完了の走行を緑として次段へ進めることになる。
- 根本原因: 完了判定に外側 wrapper の終了通知を使った。既存規律は完了を `.done` と exit code
  だけで判定し通知を判定に使うなと定めているが、その記述は子プロセス起動を対象としており、
  親自身が投げる実走にも同じ規律が要ることが読み取りにくかった。
- 恒久対応: 親の実走も終端マーカーと終了 rc で判定し、背景 job の完了通知を完了判定に使わない。
  実体は `docs/dev-wave/operations.md` の親のテスト実行節。
- 再発検知: 終端マーカーの出現と producer の生存を同時に見る待ち手を張る。本 wave では
  張り直した待ち手が実際の完了を捉え、`PYTEST_RC=0` を根拠に段を進めた。
