# [T-1283] 受入全走の実行器を tested main の blob へ束縛する

- 裁定: D838 (2026-08-25 ユーザー裁定)。関連 D440 / D583 / D387 / D95 / D867 / D871。
- wave branch: `worktree-dev-wave-t1283-runner-main-blob`、base main `bb7753fa`。
- 実装 commit: `4a974b24`。
- 逐語は `verbatim/`、変異台帳は `mutation-ledger.json.gz`、変異 spec は `mutation-spec-final.json`。

## 何を閉じたか

受入全走の実行器 `tools/run_tests.py` について、**実行する bytes の出所**と**受領証の照合基準**を
tested tip から tested main へ移した。これまでは両方とも tip 側にあったため、wave が実行器を
書き換えるだけで、実際は赤の走行を「子は緑」として着地させられた。

- `tools/acceptance_launcher.py`: 実行 bytes を `tested_main` の blob から読む。`tested_tip` の
  blob も別に読み、一致しなければ suite を一度も起動せずに rc=70 で止まる。実行後の独立再取得も
  `tested_main` を見る。実行器に bootstrap 例外は設けず、main 側の欠落も fail-closed。
- `tools/dev_wave_land.py`: 実行器の main/tip 一致検査を非帰属判定の枝から共通部へ出し、
  全 verdict へ掛ける。`runner_executed_sha256` の照合先も `tested_main` 側の blob にする。

受領証 schema は `dev-wave-acceptance-receipt/v5` のままで、root field も増やしていない。
待ち手 `tools/dev_wave_wait.py` の tip 束縛は D440 の裁定どおり変更していない。

## 着手前に実測で覆した前提

- **裁定文の「tip での存在しか検査していない」は現状より弱い記述だった。** 実測では tip blob の
  content sha256 まで照合していた (launcher の実行後再取得、land の `runner_executed_sha256` 照合)。
  欠けていたのは基準が main 側でないことだけで、脅威 (tip を書き換えれば基準ごと動く) は裁定どおり。
- **land には main 照合が既に部分実装されていた。** `verdict == "non-attributable-only"` の枝でだけ
  main/tip 一致を要求しており、常用の `child-green` では main を一切引いていなかった。
  穴はこの条件付けそのものだった。
- **`tools/run_tests.py` は main に常在しない。** 初回追加 commit は `af829260`、その親
  `b03fb9d6` に対する `git cat-file -e <parent>:tools/run_tests.py` は rc=128 だった。
  したがって「main に無く tip で初めて追加される」状態は歴史上実在する。bootstrap 例外を
  設けない根拠は常在性ではなく、例外が同じ汚染経路を再度開くことにある。
- **過去の受領証が遡って拒否される事例は無い。** tracked な JSON を全件 (1495 file) parse し、
  `schema_version` が `dev-wave-acceptance-receipt` で始まるものを数えたところ受領証は 1 件
  (`output/insights/2026-08-21_t1434-wave-d/acceptance-receipt-4.json`)、その
  `tested_main=46fbce3d` と `tested_tip=5f1c0d6c` の実行器は content SHA-256 がともに
  `b4ac7959` で一致した。legacy 用の migration reader は作らない。

## 保証の範囲 (層ごとに限定して書く)

閉じたのは「**実行器の単独差し替えでは偽の緑受領証を作れない**」という 1 点だけである。次は閉じない。

- 改変された tip 側の待ち手が launcher を起動せずに受領証を自作する経路 — D440 が意図的に
  開けたままにし、D583 が残余 (i) として記録済み。
- launcher が `tested_main` に無いときの `tested-tip-bootstrap` — 既存の例外面。
- land verifier 自身の実行権威 — D583 が [T-696] の協調境界に残すと記録済み。
- 受入後に clean な forward-main merge を足した landing tip の実行器 — 受領証の検査対象は
  `tested_main` / `tested_tip` の組であり `landing_tip` ではない。
- 実行体 (`python3`) の PATH 解決 — 段 3 のレンズが指摘したが、**D387 が
  「受入権威の防御対象は事故であって偽造ではない」と裁定し、interpreter attestation 類を
  受領証の要件から明示的に外している。** 加えて PATH は待ち手を起動する運用者の環境に属し、
  被判定側の tip が握るには待ち手の書き換えが要る (上の残余 (i) に吸収される)。
  なお修正費用は小さい — 待ち手は launcher を `sys.executable` で起動しているのに
  (`tools/dev_wave_wait.py:3047`)、launcher が実行器を起動する所だけ素の `python3` である
  (`tools/acceptance_launcher.py:216`)。事故側 (運用者の PATH に別の interpreter が居る場合に
  suite が launcher と違う interpreter で走る) は未検査のまま残る。

## 段 3・段 6 が捕まえた設計の誤り

**親の段 4 裁定が 1 点で逆だった。** 裁定は「divergence の負例には旧 launcher 相当の **tip** digest を
持たせれば、拒否理由が digest 不一致でなく equality 違反に分離される」と書いたが、実装は digest を
**main** 側 blob と照合するため、tip digest を持つ受領証は equality gate が消えても digest 不一致で
先に拒否される。つまり tip digest は equality の検出力を消していた。段 6 のレビューがこれを検出し、
負例へ main 側 digest を持たせる形へ訂正した。訂正前の設計では変異 M2 が生存していた。

**過剰拒否の正例も同型の穴を持っていた。** `locked_main == tested_main` の fixture の上に建っていたため、
land が `tested_main` の代わりに `locked_main` を引くようになっても値が変わらず、変異 M5 を殺せなかった。
`locked_main != tested_main` で locked main 側の実行器だけが異なる正例へ直した。

## 意図して受け入れた挙動変更

実行器の検査を共通部へ移した結果、非帰属判定で「実行器の不一致」と「判定器 lookup の rc=128」が
**同時に**起きた場合の分類が変わる。旧実装は一時的失敗を先に見て `retryable_same_request=True`、
新実装は不一致を先に見て `False` になる。親は新しい順序を採った。実行器の不一致は当該受領証について
恒久的に成立し再試行しても受理されないため、旧順序は受理されえない要求で lease を保持し続けていた。
受理集合はどちらでも同じなので規律 2 に反する緩和ではない。この挙動は負例テストで固定した。

## 変異 matrix

`mutation-spec-final.json` (sha256 `99f8bdfd651d238032724a32261ba190bbaaef17b6fc4c9e315a31a43ee22cec`)、
`repo_head=4a974b2486cee511c5fc2004a794ad6cf6c2e877`。

**baseline PASSED / KILLED 5 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0。**

| ID | 変異 | 殺した node |
|---|---|---|
| M1 | launcher の main/tip 一致検査を実行の後へ移す | `test_main_tip_runner_blob_mismatch_is_rejected_before_execution` |
| M2 | land の一致検査を非帰属枝の中へ戻す | `test_land_rejects_child_green_runner_blob_divergence` |
| M3 | 実行 bytes を `tested_tip` から読み直す | launcher 側 5 node |
| M4 | tip 読取失敗時に main の bytes を代用する | `test_missing_tested_tip_runner_is_rejected_before_execution` |
| M5 (過剰拒否の正例) | land が `tested_main` でなく `locked_main` を引く | land 側 2 node |

**登録しなかった変異が 1 件ある。** 「land の digest 照合先を tip へ戻す」は、main/tip の object ID
一致を先に要求するためどちらの blob へ照合しても結果が同値になる等価変異であり、登録すると
発火しない gate を数えることになる。

baseline から `test_exploration_external_root_keeps_wave_clean` を `--deselect` で外した。この node は
本 wave の差分と無関係な既知赤で、本文は campaign 層の `CertifiedWriterAuthorizationError`
「Pegasus compute では receipt state 内で一意な required authorization_contract だけを受理する」。
F57 に 2026-08-24 の再発として本文一致で記録されており、そのときの wave も campaign 層に触れていない。

## 運用で分かったこと

- **変異 harness の共有木検査は既定では共有 main checkout を観測対象に含むため、並行 wave が
  main を進めるだけで rc=125 になる。** 実際に plan-only の段階で落ちた。`--source-repo` へ
  独立 clone (`git clone --shared` + 対象 commit の checkout) を渡すと観測対象がその clone だけに
  なり、構造的に断てる。副作用として、変異走行中も自分の worktree で記録作業を進められる。
- 焦点走の途中で `/tmp/.git` の迷子 (空 directory、2026-08-25 22:05 作成) を見つけ、F457 記載の
  手順どおり `rmdir` で除去した。放置すると受入全走が別種の大量赤を出す。
