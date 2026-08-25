# 段 1 brief — [T-1283] 受入全走の実行器を tested main の blob へ束縛する

base: main `bb7753fa` (引数の `003c0499` は 3 世代 stale。wave 開始中にも `c83b5b2c` → `bb7753fa` と進行)。
裁定: D838 (2026-08-25 ユーザー裁定)。関連: D440 (判定器の main 束縛・待ち手は tip 据置)、D95 (実装面は Codex author 必須)。

## scope

- **対象**: 受入全走の実行器 `tools/run_tests.py` の **読み元と照合基準**を tested main へ移す。
  編集面は実行主体である `tools/acceptance_launcher.py` と、受領証を独立検証する `tools/dev_wave_land.py`。
- **非対象**: 待ち手 `tools/dev_wave_wait.py` の tip 束縛 (D440 が明示的に維持)。`tools/run_tests.py` 本体。
  判定器 `tools/check_acceptance_reds.py` (D440 で既了)。D583 の残余 (i) (待ち手が launcher を迂回する経路)。

## 実測 (裁定前提の裏取り)

1. **裁定文の「tip での存在しか検査していない」は現状より弱い記述である。** 実測では tip blob の
   content sha256 まで照合している (`acceptance_launcher.py::_launch` の M3 独立再取得、
   `dev_wave_land.py::_runner_tree_entry(tested_tip)` と `runner_executed_sha256` の比較)。
   欠けているのは **main 側を基準にすること**だけであり、「tip を書き換えれば基準ごと動く」という
   脅威は裁定の記述どおり成立する。裁定の前提は覆らない。
2. **land には main 照合が既に部分実装されている。** `dev_wave_land.py:1114-1131` は
   `verdict == "non-attributable-only"` の枝でだけ `main_runner_entry[1] != tip_runner_entry[1]` を
   拒否する。常用の `child-green` では main を一切引かない。穴はこの条件付けそのものである。
3. **launcher 自身は既に tested_main 束縛で起動されている** (`dev_wave_wait.py::_default_launcher_source`、
   bootstrap 例外 `tested-tip-bootstrap` つき)。したがって本 wave が launcher を編集しても、
   本 wave の受入では **main 側の旧 launcher が走る**。新実装が効くのは次 wave からである。
4. 受領証 schema は `dev-wave-acceptance-receipt/v5`。literal は launcher / wait / land の 3 箇所。
5. 編集面の重複なし。ただし `.codex/worktrees/dev-wave-t1563-acceptance-nproc` が
   `tools/run_tests.py` を未 commit で編集中で、本変更が着地すると同 wave は受入を通せなくなる
   (D838 が明示的に受容した代償)。

## 不変条件

- **I1**: 受理集合を広げる方向の緩和を採らない (絶対規律 2)。不一致・測定不能はすべて fail-closed。
- **I2**: 待ち手 `tools/dev_wave_wait.py` の束縛を変えない (D440)。
- **I3**: 受領証 schema (`v5`)・root field 集合を変えない。
- **I4**: 実装面は Codex `role=author` が書く。親は docs 本文のみ編集する (D95)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** launcher は実行器 bytes を `tested_main` から読む。加えて `tested_main` と `tested_tip` の
  runner blob 一致を **suite 起動前に**要求し、不一致は fail-closed。bootstrap 例外は設けない
  (`tools/run_tests.py` は main に常在するため、例外は穴にしかならない)。
  根拠: D838 が代償を「当該 file を直す wave は受入を通せない」と書いており、
  main bytes を黙って実行する形 (tip の編集が無視されたまま緑が出る) では代償の記述と合わない。
- **(P2)** 受領証 schema を変えない。`runner_source_revision` 等の field を足さない。
  根拠: 本 wave の受入は main 側の旧 launcher が v5 で発行する。tip 側 land が v6 を要求すると
  自分自身を締め出す。D440 も同じ理由で schema 不変を選んでいる。
- **(P3)** land は既存の main==tip runner blob 比較を非帰属枝から出し、全 verdict で無条件にする。
  `runner_executed_sha256` の照合基準も tested_main 側の blob と書く。
- **(P4)** 本 wave 自身の受入可否は、投入直前に `main:tools/run_tests.py` と tip 側 blob の一致を
  実測して確認する (触らないので一致するはずだが、推定で通さない)。

## 成果物影響 (DW-G05)

実装しない場合、wave は `tools/run_tests.py` を書き換えるだけで実際は赤の走行を「子は緑」として
着地させられる。受理集合が「実際は赤の走行」まで広がり、certified な選択結果・材料レポート・
試行台帳の着地根拠 (受領証) が被判定側の産物になる。

## 成果物の形

`tools/acceptance_launcher.py` と `tools/dev_wave_land.py` の実装差分、両者の負例テスト
(main!=tip で fail-closed、child-green でも拒否)、変異 matrix、worklog / decisions 記録。

## 分割方針

段 2 プラン 1 本。段 3 敵対 2 レンズ (sol/luna)。段 5 実装子 1 本 (2 file は同一契約で密結合)。
段 6 レビュー 2 レンズ + fix。
