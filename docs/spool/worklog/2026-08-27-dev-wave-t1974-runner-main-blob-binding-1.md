---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1974-runner-main-blob-binding
seq: 1
title: [T-1974] 段階 P — 計算ノードの受入子を tested main の blob へ束縛した。実行器の差分は 0 byte (コード + docs、branch worktree-dev-wave-t1974-runner-main-blob-binding、変異 matrix = baseline PASSED・KILLED 13・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー依頼は `/dev-wave [T-1974] 段階 P を実装してください` (背景 job)。確定済み裁定は D1151。
  設計 6 点の正本は `docs/archive/worklog-phase3-0827-1028.md` の [T-1974] 項。
- **引数の前提を 3 点、親が起動時に訂正した。** (i) 引数が挙げた `tools/dispatch_compute.py` は
  実在せず、実体は `tools/pegasus/dispatch_compute.py`。(ii) 「裁定は未 land」は誤りで、
  D1151 は既に main の `docs/decisions.md` に着地していた。(iii) 「4 file を触る稼働 wave は 0 本」は、
  編集面を確定した後の再走査では `docs/pegasus-runbook.md` に 1 本 (`dev-wave-t1647-a2-cert-fanout`)
  が居た。`.codex/worktrees/` の 2 本は 08-24 / 08-26 の子の残骸だった。
- **land が launcher へ課すのは tested main の blob 束縛だけで、tip 等値は要求しない**
  ことを親が実測した (`tools/dev_wave_land.py` の launcher entry 検査)。
  したがって launcher の編集は本 wave の着地を塞がない。これが設計 (i) が成立する前提である。
- **段 2 のプランを段 4・段 6 で 6 点覆した。** 最重は申告 channel で、
  段 3 の 2 レンズが独立に「manifest を環境変数で渡すと被検査テストコードが申告を偽造できる」へ
  到達した。継承 write-fd へ変更した ({{D:runner-binding-report-channel}})。
  ほかに source bytes を運ばない、shard 数を注入しない
  ({{D:acceptance-shard-count-authority}})、申告検査を outcome の後へ、
  `result.json` の `O_EXCL` を変えない、恒真述語 2 つを gate から外す。
- **段 6 レビュー A が正常経路を壊す実バグを捕まえた。** dispatcher の申告 writer が
  `indent=2` の複数行 JSON を書き、launcher の parser は 1 行 JSON を読む実装だった。
  そのままなら段階 P 着地後の正常な dispatch が全部 land 不能になる。
  片側の serializer だけを使うテストでは検出できないので、writer の bytes を parser へ
  直結する seam テストを置き、変異 M13 で殺せることを実測した。
- **静的レビュー 2 本を通り抜けた赤が実走で 2 種類出た。** (i) `parametrize` した引数に既定値を
  付けたため pytest が file 全体の収集を拒否し、48 worker が同一エラーを返した。
  親が 4 file を AST 全走査して同型 1 件だけと確定した。(ii) 消費者の取り残しが 2 段あり、
  1 段目は実装子が自分で見つけて止まり、**2 段目は親の初回閉包判定が粗くて取り逃した** —
  `test_dev_wave_land.py` の `acceptance_launcher` 参照 29 件を「path 文字列の fixture」と
  一括判定したが、実際には実 launcher を端から端まで駆動する node が 2 本あった。
  2 回目は全 test file を走査し直し、候補 5 file を実走 (886 passed / 2 skipped) して閉じた。
- **設計 (iv) の blast radius を親が実測し、不採用にせず記録した。**
  待ち手は Pegasus LOGIN かつ queue が `ENA=ENA` / `STS=ACT` のときだけ shard 数を注入する。
  注入されない走行は login admission へ入り、memory headroom があれば suite を
  ログインノードで local 実行して受領証を出している。段階 P 着地後、
  **「queue 停止 + login に余裕あり」の受入は受領証を作れない**
  ({{D:nondispatch-acceptance-fail-closed}})。復旧は段階 R が担う。
- **束縛が及ぶのは dispatch された `tests` 子 1 層だけである。** shard worker は
  `multiprocessing.get_context("fork")` で起動され、fork は `close_fds` と無関係に fd を複製する。
  dispatcher はその fork worker から呼ばれるので、実行器と `tools/acceptance_shards.py` を
  編集できない段階 P では継承を閉じられない。残余の正確な形は
  「dispatcher または `tools/acceptance_shards.py` を編集した wave は捕まらない」である。
  台帳では「受入全層を main へ束縛した」と書かない。
- **「実行器を触った 24 commit のうち 6 件が dispatcher も触っている」は観測事実としてだけ残す。**
  申告の必要性や将来の確率の根拠には使わない。段 3 の両レンズが独立にこの一般化を攻撃した。
- **変異の事前登録を本走前に 4 件訂正した。** M4 は同値変異、M9 は構成不能、M7 と M11 は
  診断だけの赤だった。DW-M03 / DW-M04 に従い実効 gate へ再照準し、初回登録は insight に残した。
  さらに実バグ用の M13 を新設した。
- **DW-M07 の probe を挟んだ効果が実測で出た。** 13 変異のうち 5 件が、意図した node に加えて
  もう 1 本を落としていた。期待 node は完全集合なので、勘で書いていれば本走を 1 回捨てていた。
- 変異 matrix は `b93861570` 固定・dispatch・使い捨て worktree で
  **baseline PASSED / KILLED 13 / SURVIVED 0 / MISMATCH 0**。
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` は F57 系の
  既知非帰属赤 (所有 [T-1079]、計算ノードで決定的) なので DW-C01 / D690 の既定手順で `--deselect` した。
- 子は 9 本 (plan 1、敵対相談 2、実装 1、レビュー 2、fix 3)。すべて `gpt-5.6-sol` / `xhigh` /
  `check_codex_output.py` rc=0。実測はすべて親が行った。
- 逐語・実測表・変異台帳は `output/insights/2026-08-27_t1974-runner-main-blob-binding/`。

## 次の一手差分

### 完了

- [T-1974] 段階 P を実装した。計算ノードで dispatch された `tests` 子の実行 bytes を
  tested main の blob へ束縛し、launcher が全 shard の申告を無条件に要求する。
  `tools/run_tests.py` の差分は 0 byte で、受領証 schema も env allowlist も変えていない。
  残余と blast radius は insight と runbook に明記した。
  remaining: none
  base: 34df0eda9a60637ad52af401cd72b9f0e204464c7613dd77d7357173ccc8fe42

### 更新

- [T-1975] **P1・実装待ち (段階 Q)**: 段階 P が main へ入ったので着手できる。
  launcher と land の実行器 main/tip 等値要求だけを外す。Q 自身の受入は P の main launcher が
  判定するので、申告検査が実際に発火した証拠が受領証として残る。
  **Q の設計時に、段階 P が残した非 dispatch 受入の fail-closed を併せて確認すること** —
  queue 停止時にログインノードで走る受入は段階 R まで受領証を作れない。
  base: 0ee47677b9b9f92ddeffebc524530f9563452189014f17cd20168946e1042256
