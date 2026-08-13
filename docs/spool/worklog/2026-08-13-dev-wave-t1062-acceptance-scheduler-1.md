---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t1062-acceptance-scheduler
seq: 1
title: 受入全走の実効 scheduler を観測して receipt へ束縛し land で照合した — argv では閉じない plugin 差し替えを観測可能にした (コード + docs、変異 14/14 KILLED、branch worktree-dev-wave-t1062-acceptance-scheduler)
---

## 本文

- ユーザー裁定は 2026-08-13 rulings 第 11 回の #3 (控え =
  `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-rulings11-12rulings.md`)。
  「採用 (縮小 scope) — 実効 scheduler を conftest で検出し acceptance receipt へ記録し
  land 側で照合する。あわせて `-p` 付き非受入走が task-run 上 `full` と記録される誤記を直す。
  scope はここまで」。設計は {{D:effective-scheduler-attestation}} と
  {{D:full-suite-plugin-option-split}}。
- **段 3 の敵対レビューが、実受入を必ず落とす欠陥を実装前に 2 件見つけた。** 詳細は
  {{F:hookwrapper-value-is-not-final}} と {{F:dispatch-relay-drops-tail-marker}}。
  どちらも「静的レビューでは出ない環境依存」ではなく、pluggy と dispatch の実装を読めば
  出る種類の欠陥で、段 2 プランは両方とも踏んでいた。
- **2 つのレンズが正面から対立し、親が実測で裁定した。** sol は「land は `loadgroup` のみ
  受理せよ。`serial` は可変 option からの推測にすぎない」、luna は「非 loadgroup の拒否は
  受理集合の縮小で scope 違反」と述べた。親は `python3 tools/run_tests.py -n0` が現行
  `_is_acceptance_run` の受理形であることを実測し、**`loadgroup` のみ受理を refuted** とした。
  同時に sol の批判は正しいので、`serial` の判定根拠を option 読みから「`dsession` plugin が
  登録されていない」という観測へ変えた。この 2 つを同時に満たす形は、どちらのレンズ単独からも
  出ていない。
- **裁定文言を超えた親の判断が 1 件ある。** 裁定は `-p` だけを名指ししていたが、`-o` と
  `--override-ini` も `_is_full_suite` の同一 predicate の同一穴であり、`_is_acceptance_run` は
  既に 3 綴りを同一に拒否している。1 つだけ直すと 2 predicate の非対称が閉集合の中に残る。
  影響半径を実測し (`output/task-runs` の全記録に該当 3 綴りは **0 件**、full 分類の記録は 6 件)、
  3 綴りすべてを直した。ユーザーが不同意なら `-p` のみへ縮められる。
- **codex 子は pytest を 1 度も走らせられない。** sandbox が socket を塞ぐため
  `run_tests.py` の dispatch が rc=16 になる。段 5・6 の子はすべて「実装済み・未実走」で、
  実走はすべて親が担った。子 prompt にこの事実を明記すると、子が正しく `partial` と申告する。
- 焦点走で出た赤 11 件のうち **10 件が本 wave 帰属のテスト側欠陥**だった (診断行の期待が
  stderr 全体の行数を数えていた 9 件 + 合成 runner の引用符崩れ 1 件)。production は初回から
  期待どおり動いており、fix 2 巡とも production を 1 行も変えていない。
- **変異検査が本物のテスト欠落を暴いた。** `type(sched) is LoadGroupScheduling` を
  `isinstance(...)` へ緩める変異が生存した。既存の live-xdist テストは派生でない別クラスを
  使うため、exact 型契約が 1 件も pin されていなかった。派生クラスを実効 scheduler にして
  `unknown` を要求するテストを足して殺した (commit 4c980d7a)。
- **変異の期待 node を巡って 5 件 MISMATCH が出たが、すべて「予測より検出力が高い」方向**
  だった。DW-M08 に従い初回を probe として記録し、実測の完全集合へ再登録して再走した。
  生 ledger は `/work/1/SFC/tanab/dev-wave-jobs/t1062-acceptance-scheduler/mutation/` に残す。
- **DW-M08 の手順が原理的に成立しない系を実測した。** 詳細は {{F:digest-truncates-expected-nodes}}。
- **signal 復元系テスト族のフレークを実測で特定した。** 詳細は {{F:signal-restore-test-family-flake}}。
- 段 6 のレビュー 2 本は計 9 件の real を出し、うち 6 件を must-fix として採用した
  (値源、marker 発行位置、単一 read の完成、`held_ids` からの独立、`getattr` 連鎖、変異の層分離)。
  scope 外として裁定パッケージへ回した real は 3 件 (発行者認証、dispatch の wire 契約化、
  待ち手 process の自己 bytes 照合)。
- 工数: codex 子は plan 1 (max、931 秒 / 52 call)、consult 2 (max、sol 1069 秒 41 call /
  luna 922 秒 37 call)、author 1 (high、895 秒 73 call)、review 2 (high、456 秒 21 call /
  381 秒 16 call)、fix 3 (high、239 秒 20 call / 510 秒 30 call / 約 180 秒)。
  すべて `outcome=accepted`。段 6 のレビューは `--lane` が相談段専用のため 2 本とも
  `gpt-5.6-sol` で、レンズだけを変えている。
- 放置した場合、plugin が scheduler を差し替えて実 repo 排他が消えた走行でも acceptance
  receipt 上は「緑の全走」として land を通り、certified 選択とレポート・台帳が排他なしの
  テスト結果の上に載ったまま残る。

**保証範囲の限定 (scope 外として明記する)。** 本 wave が閉じるのは *非共謀 plugin による
scheduler 差し替えの検出* である。scheduler を差し替える plugin は同じ process 内で marker
自体も偽造できるため、発行者認証は閉じていない。また **task-run は受入の権威ではない** —
`run_tests.py` は child rc を先に記録し、その後に待ち手が attest を検査するため、receipt が
出なくても green の task-run event は残る。受入の権威は receipt だけである。

## 次の一手差分

### 完了

- [T-1062] 実効 scheduler を conftest で観測し receipt v3 へ束縛して land で照合した。
  `-p` / `-o` / `--override-ini` の full-suite 誤分類も同面で直した。変異 14/14 KILLED。
  remaining: none
  base: 3a82c5e58b6f1095ab2a6ce9ca856765918fdaeea3d85963be55e67985fcf375

### 更新

- [T-1066] **P2・更新**: 単発フレークではなく **signal 復元系テスト族のフレーク**であることが
  実測で分かった。同一コマンド 4 走のうち 3 走が緑で、赤の 1 走は毎回この族の別テスト
  (`test_public_main_real_signal_after_success_uses_restored_handler` /
  `test_public_main_failure_restores_handler_without_release` /
  `test_signal_after_core_success_uses_restored_real_handler`) だった。
  変異検査では runner 範囲から族ごと外さないと期待 node の完全集合が安定しない。
  ignored file の撤去手順は rulings11 #10 で裁定済み。
  base: d9037d1ecdfd6c5755b8fbd222c338a7211cff23383dc29fa771c256c5573cfd

### 新規

- {{T:waiter-self-bytes-vs-tip}} **P1・新規・要裁定**: 起動済みの待ち手 process は
  ロード済みの古いコードのまま新 main を merge して走るため、新 tip に束縛した旧 schema の
  receipt を発行し land が拒否する。受入前に「走行中 waiter の bytes」と新 tip の
  `tools/dev_wave_wait.py` blob を照合し、不一致なら `restart-required` で止める契約を入れるか、
  運用手順 (land 後に稼働中の待ち手を再起動する) に留めるかを決める。
- {{T:scheduler-marker-issuer-auth}} **P2・新規・要裁定**: 実効 scheduler の marker に
  発行者認証がない。scheduler を差し替える plugin は同一 process 内で marker も偽造できる。
  閉じるには plugin autoload の隔離、明示 plugin inventory、pytest 外の観測路のいずれかが要り、
  どれも受入 env と受理集合の裁定を伴う。
- {{T:dispatch-relay-wire-contract}} **P2・新規**: Pegasus dispatch の relay framing
  (`| ` 前置、成功時 4 KiB / 失敗時 64 KiB の tail) を受入の wire 契約として固定し、
  回帰テストの scope に入れる。本 wave は「両形を受け付ける」までとし dispatch 側は触っていない。
- {{T:exploration-root-single-file-red}} **P3・新規**:
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` は
  **同 file 単独走のときだけ**決定的に赤になる (login のローカルでも計算ノードでも)。
  4 file 以上の走では緑。`IZANAGI_EXPLORATION_OUTPUT_ROOT` の process 内 pin と
  temp root の git 祖先判定の相互作用を疑う。本 wave は同 file も
  `orchestrator/campaign/` も変更していない。
