---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1283-runner-main-blob
seq: 1
title: [T-1283] 受入全走の実行器を tested main の blob へ束縛した (コード + テスト、branch worktree-dev-wave-t1283-runner-main-blob、変異 matrix = baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー依頼は `/dev-wave [T-1283] 受入全走の実行器 (tools/run_tests.py) を、判定器と同じく
  tested main 側の blob と照合する` (背景 job)。裁定は D838、base として main `003c0499` が
  引かれたが、着手時点で main は既に `bb7753fa` まで 3 世代進んでいた。実 base は `bb7753fa`。
- **裁定文の前提を 1 点、実測が弱めた。** D838 は「現状は tip での存在しか検査していない」と書くが、
  実測では tip blob の content sha256 まで照合していた。欠けていたのは基準が main 側でないことだけで、
  脅威 (tip を書き換えれば基準ごと動く) は裁定どおり成立するため、裁定の結論は覆らない。
- **land には main 照合が既に部分実装されていた。** 非帰属判定の枝でだけ実行器の main/tip 一致を
  要求しており、常用の `child-green` では main を一切引いていなかった。穴はこの条件付けそのものだった。
- **親の段 4 裁定が 1 点で逆だった。** 「divergence の負例には tip 側 digest を持たせれば拒否理由が
  equality 違反に分離される」と書いたが、実装は digest を main 側と照合するため、tip digest では
  equality gate が消えても digest 不一致で先に拒否され、検出力が消える。段 6 のレビューが検出し、
  負例へ main 側 digest を持たせる形へ訂正した。訂正前の設計では変異 M2 が生存していた。
  過剰拒否の正例も `locked_main == tested_main` の fixture の上に建っていて変異 M5 を殺せず、
  同じく段 6 で訂正した。
- **意図して受け入れた挙動変更が 1 件ある。** 非帰属判定で「実行器の不一致」と「判定器 lookup の
  rc=128」が同時に起きたときの分類が、再試行可能から恒久拒否へ変わる。段 4 裁定は「既存分類を保つ」と
  書いていたので自分の凍結指示との差だが、不一致は当該受領証について恒久的に成立し再試行しても
  受理されないため、旧順序は受理されえない要求で lease を保持し続けていた。受理集合は不変。
  負例テストで固定した。
- **棄却した所見。** 段 3 のレンズが「実行体 `python3` が PATH 解決で、blob を main に束縛しても
  解釈する側をすり替えられる」を最重として挙げたが、scope 外と裁定した。D387 が「受入権威の防御対象は
  事故であって偽造ではない」と裁定し interpreter attestation 類を受領証の要件から明示的に外している。
  加えて PATH は待ち手を起動する運用者の環境に属し、被判定側の tip が握るには待ち手の書き換えが要る
  (D440/D583 の残余 (i) に吸収される)。事故側だけを {{T:acceptance-runner-interpreter-accident}} へ残す。
- **過去の受領証が遡って拒否される事例は無い**ことを実測した。tracked な JSON を全件 (1495 file)
  parse し受領証は 1 件、その `tested_main` と `tested_tip` の実行器は content SHA-256 が一致した。
  legacy 用の migration reader は作らない。
- **変異 harness の共有木検査が並行 wave に壊される構造を回避した。** 既定では共有 main checkout が
  観測対象に入るため、他 wave が main を進めるだけで rc=125 になる (plan-only の段階で実際に落ちた)。
  `--source-repo` へ独立 clone を渡すと観測対象がその clone だけになり構造的に断てる。
- 子は 8 本 (plan 1、敵対相談 2、実装 1、レビュー 2、fix 1、焦点再レビュー 1)。すべて
  `gpt-5.6-sol` / `xhigh` / `accepted`。実装子と fix 子はいずれも計算ノードへ dispatch できず
  「実装済み・未実走」と正しく申告し、テストの実測はすべて親が行った。
- 焦点走の赤 1 件は F57 の再発で、本 wave の差分と無関係。前回の再発項が残した「引き金は file 集合」
  という読み方は今回の実測 (単独 nodeid 投入でも同じ本文で落ちる) では成立しない。
- 焦点走の途中で `/tmp/.git` の迷子 (空 directory) を見つけ、F457 記載の手順どおり `rmdir` で除去した。

## 次の一手差分

### 完了

- [T-1283] 実行器の読み元と照合基準を tested main へ移し、launcher は suite 起動前に main/tip 一致を
  要求、land は全 verdict 共通で一致と digest を照合する形にした。受領証 schema と待ち手の tip 束縛は
  変えていない。閉じたのは「実行器の単独差し替えでは偽の緑受領証を作れない」の 1 点だけで、
  待ち手の自作経路・launcher bootstrap・land 自身の権威・forward-main landing tip は閉じない
  (前 3 者は D440 / D583 / [T-696] が所有、最後は新規登録)。
  remaining: none
  base: ef3ea3d6ee196d0e78a691bb1538723c6c97f4e7b9729bf9f6599c6be9f035fb

### 新規

- {{T:acceptance-runner-interpreter-accident}} **P3・新規**: 受入 launcher が実行器を起動する
  interpreter は素の `python3` で PATH 解決である (`tools/acceptance_launcher.py`)。待ち手が
  launcher を `sys.executable` で起動している (`tools/dev_wave_wait.py`) のと不揃いで、修正は 1 行。
  偽造側は D387 が防御範囲外と裁定済みなので**事故側だけが残る** — 運用者の PATH に別の
  interpreter が居ると、受入 suite が launcher と違う interpreter で走る。現機では
  `command -v python3` が `/usr/bin/python3` を返し発火していない。発火条件を作れる機体で
  実測できたときに直すか、恒真として記録に留めるかを決める。
- {{T:landing-tip-runner-uncovered}} **P3・新規**: 受入後に clean な forward-main merge を足した
  landing tip の実行器は、受領証の検査対象外である (`tools/dev_wave_land.py` は `tested_main` /
  `tested_tip` の組を検査し `landing_tip` を渡さない)。取り込んだ main 側が実行器を変えていれば、
  最終 landing 内容はその実行器で受入されていない。実行器を変える main merge だけ受領証の再利用を
  拒否して再受入させるか、保証を original tested tip に限定して明記するかを裁定する。
