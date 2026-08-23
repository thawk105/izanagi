---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1510-sort-swo-sigabrt
seq: 1
title: [T-1510] sort SWO oracle の SIGABRT は oracle 自身の事前条件違反で masstree 由来ではなかった (コード+テスト、branch worktree-dev-wave-t1510-sort-swo-sigabrt、変異matrix = 事前登録2件ともKILLED)
---

## 本文

- **真因は環境ではなく oracle 自身の C++ コードだった。** `_TU_PREFIX` の
  `snapshot_corpus()` が `element.body_.get_val()` を無条件に呼び、既定構築の
  `TupleBody` に対して `HeapObject::view()` の `assert(data_ != nullptr)` が発火して
  abort していた。`_COMPILE_FLAGS` に `-DNDEBUG` は無く assert は生きている。
  **masstree と CMake に欠陥は無かった** — `libjson.a` / `*.o` は `_compile_command` から
  link されておらず、test 側 skip gate の代理でしかない。
- **タスク本文の前提「masstree のビルド設定の整合から始めよ」は実測で外れた。**
  切り分けは pytest も `preexec_fn` も `RLIMIT_AS` も通さない素の subprocess で TU を
  compile して実行するだけで足りた。oracle 本体が候補実行の stderr を DEVNULL へ捨てるため
  signal 番号しか残らず、これが真因到達を遅らせていた (T-1524 が別途所有)。
- **並行セッションが配っていた `RLIMIT_AS=512MiB` + hugepage 仮説を棄却した。**
  resource limit を一切かけない実行で同じ abort が出る。仮説の中継元へ棄却根拠を返し、
  中継側は撤回のうえ worklog へ記録した。
- **段 3 敵対レンズが oracle の別の穴を 2 件出し、親が実測で確定させた。**
  どちらも正しさ防壁の設計変更にあたるため実装せず裁定パッケージへ回した ({{D:sort-swo-oracle-baseline-visibility}})。
  (1) 候補 comparator が corpus を壊した後に `trusted_snapshot = snapshot_corpus();` と
  書くと変異が完全に見逃される (実測: 変異のみ = witness 検出、変異 + baseline 再計算 = witness なし)。
  `coder_effect_gate.DENY_TABLE` は host 副作用しか塞がずこの識別子は素通りする。
  (2) 合法な SWO を作る候補が `a.body_.get_val()` を読むだけで SIGABRT し、
  `UNAVAILABLE` として不当に棄却される (修理後も再現)。
- **本 wave の着地で (1) の穴は到達可能になる。** 着地前は全評価が SIGABRT で
  `UNAVAILABLE` だったため穴は死んでいた。緩和事実として、sort 合成エージェント
  `coder-v4-autonomous-sort` は `tools: []` で filesystem 経路を構造的に持たず
  `trusted_snapshot` という識別子を知り得ないが、これは隠蔽への依存であり解決ではない。
- **除外表の entry 削除は解禁条件の成立を実測してから scope へ入れた。**
  wave 開始時は `dev-wave-sort-swo-oracle-exclusion` (tip 367d41e9) が未 land だったが、
  wave 中に land したため段 4 で scope を広げた。機構は残し entry だけを外し、
  合成 `Exclusion` を契約表と runtime 表の双方へ注入して検査が恒真にならないようにした。
- **親の実験設計に欠陥があった。** 焦点走で出た
  `test_growth_test_holds_contract.py::test_plain_pytest_delegating_runner_is_not_over_rejected`
  の赤を、差分ゼロの main worktree で再現したことを根拠に「repo 側の決定的な赤」と判断して
  並行セッションへ配ったが、実際は `FORCE_COLOR=3` / `COLORTERM=truecolor` に依存していた
  (対照実験: ambient で rc=1、`env -u FORCE_COLOR -u COLORTERM` で rc=0)。
  **差分を消しても環境は同じセッションから継承されるので切り分けにならない** ({{F:zero-diff-worktree-does-not-isolate-environment}})。
  この赤は別 wave が既に修理済みで、こちらの fix 子は起動後に停止・撤去して衝突を避けた。
- 親の計数も誤っていた。`test_sort_swo_oracle.py` は 53 関数・62 node で、
  落ちていたのは 7 関数・10 node である。「7 node」「全 53 node」はどちらも関数数と node 数の混同。
- 親は段 2・段 3 の codex prompt 先頭を `単独段 dispatch:` 形式にせず `DW-O02` に違反した。
  子は例外を使えず通常のクラス 3 導線で走ったので緩む方向ではなく厳しい方向に外れており、
  再 dispatch はせず実際に実行した手順として記録した。
- 変異 matrix: baseline PASSED、事前登録 2 件とも KILLED。
  M1 (null 安全 accessor を `view()` へ戻す) の kill は**過剰決定**である —
  E2E 10 node の実行時 abort と、TU hash 変化による golden literal 不一致の両方で落ちる。
  単一理由の証拠は E2E 側で、identity 系は冗長 gate として扱う。

- 段 8 の自己改善候補 1 件が **byte 予算で入らず、ユーザー裁定へ返す**。
  `DW-S05-A` の所有パス限定 patch 手順 (`git add -A` → `git diff --cached --output` → `git apply`) は
  **隔離 session では実行できない** — 隔離 guard が子 worktree への git 操作を拒否するためである。
  親は代替として `diff -rq` による全 tree 比較を実測で使い、所有面の確認と所有外編集の検出を
  同時に行えた (実装子 3 本すべてで所有外変更ゼロを確認)。この手順を `DW-S05-A` へ統合しようとしたが、
  L1.5 の unique footprint が 9922 bytes となり予算 9566 bytes を 356 bytes 超えた。
  自己改善契約は「予算に収まらなければ止めてユーザー裁定へ返す」「予算値を上げる変更は
  独立審査」と定めるため、追記は撤回した。**現状の `DW-S05-A` は隔離 session で実行不能な手順を
  唯一の正本として書いている。**

## 次の一手差分

### 完了

- [T-1510] sort SWO oracle の SIGABRT を真因 (oracle TU の事前条件違反) まで特定して修理し、
  受入全走の file 単位除外 entry を外した。焦点走で対象 10 node が skip でなく実走して緑
  (185 passed / 0 failed)、除外側も 375 passed / 0 failed。
  remaining: none
  base: 6c4b11abab304079a19101a86b0831da3df7428011cef7bf9944392c6f137681
