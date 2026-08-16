---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1268-scope-cap-page-align
seq: 1
title: bounded scope の cap attest を kernel の page 境界丸めへ整合させた — 同型欠陥は 3 tool にあり、台帳 186 件中 136 件が既に恒久ラッチ済みだった (コード + テスト、branch worktree-dev-wave-t1268-scope-cap-page-align、変異 matrix = 8/8 KILLED)
---

## 本文

- 設計判断は {{D:scope-cap-exact-or-page-floor}}。手順違反と偽緑は
  {{F:mutating-the-runner-poisons-local-mutation-runs}} と
  {{F:page-size-detector-collapses-when-fixtures-share-a-floor}}。
- **親が段 1 前に実測して裁定の前提を検算した。** login node (kernel 5.15.0-186-generic,
  systemd 249, `getconf PAGESIZE` = 4096) で `systemd-run --scope -p MemoryMax=<cap>` 後の
  `memory.max` は `cap - (cap % 4096)`。cgroup へ直接 write しても同じ切り捨てで、
  丸めの主体は systemd でなく kernel である。**上方向へ倒れる経路は観測していない。**
  この実測は login / page size 4096 の 1 環境に限る (計算ノードや別 page size へは一般化しない)。
- **F362 が「確率的」と書いた現象の正体は恒久ラッチだった。** `rc=16` は走行を中断するので
  ピーク台帳が更新されない。修正前の worktree で同一 target 集合を 3 連走したところ
  3 走とも同じ予算 1467704320 で `rc=16` になった。
  ピーク台帳 186 件を全件走査すると、非整列予算を導く entry が **136 件 (73%)**、
  整列 28 件、下限 clamp 22 件。非 clamp の 164 件で見ると 83% で、
  理論値 3/4 を超えるのは**ラッチした entry が二度と更新されず蓄積する**ためである。
  全走用の `tests-full` key だけは整列していて無事だった。
- **「予算は page 倍数のピーク由来だから確率 3/4」は親の一般化しすぎだった** (段 3 レンズ A が指摘)。
  `remember_peak` は peak の page 整列を要求していない。台帳 186 件が全件 4096 倍数だったのは
  実測であって保証ではない。記録は「実測 136/186」と「page 整列を仮定した場合の 4 剰余類中 3」に分けた。
- **scope を 3 tool へ広げた** (段 3 レンズ B が第 3 の site を発見し、親が到達性を検算)。
  `tools/mutation_fanout.py` の `_bounded_scope_cgroup` も同型の厳密比較を持ち、
  `certified_peak = peak + max(ceil(peak/4), 128 MiB)` を `MemoryMax` へ渡すため、
  ピークが 512 MiB を超えると同じ残差構造で発火する。
  同 file の `_attest_measurement_cgroup` は**変更していない** — そこでの比較対象は
  既存 cgroup から読み戻した実値であって要求 cap ではなく、緩めると本物の検査が死ぬ。
- **段 6 の敵対レビュー 2 本が real 所見 3 件を出し、すべてテスト側の偽緑だった。**
  (1) detector cap が page size を区別できず 4096 固定実装を素通し、
  (2) 全角数字の拒否入力が cap と別値で正規化する誤実装を検出できず、
  (3) `os.sysconf` の stub が key 名を検証せず key 誤記の変異を素通し。
  production 側の所見はすべて refuted で、実装は 1 byte も変えていない。
- **scope 外として返す real 所見が 1 件ある** ({{T:bounded-scope-marker-authority}})。
  `_bounded_scope_membership` は環境変数由来の cap を認可上限と照合せず grant 由来性も検証しない。
  ただしこれは HEAD 時点で既に成立しており、本 wave は広げない — 偽の marker は
  page 整列値を選べば従来の厳密比較でも同じ迂回ができるため、攻撃者にできることは増えない。
- **受入条件を段 6 で修正した** (レンズ A の指摘)。「修正後 rc=0」はテストが正当に落ちれば
  成立しないので誤り。正しくは「attest 起因の `rc=16` が消え、child の rc が透過される」。
- **修正後の対の実測**: 同一 target 集合・同一台帳ピーク (1174163456) で attest が成立し、
  scope が実走してピーク 1467703296 (= 丸め後の上限ちょうど) を観測した。予算を使い切ったため
  設計どおり計算ノードへ切り替わり 499 passed。焦点走 722 passed。
- **変異 matrix = 8/8 KILLED** (anchor commit 4cd576c4、期待 node は完全集合 88 件)。
  期待集合は段 3 レンズ B の指摘に従い、事前に probe で観測してから凍結した。
  レンズ B の静的予測は `M4` を 4 node としていたが実測は 7 node だった
  (既存の marker テストも落ちる)。**静的予測を期待集合に使わなくて正解だった。**
- 焦点走 19 file の初回で赤 5 件が出たが、いずれも未編集 file だった。
  worktree のネスト submodule (`external/ccbench/third_party/shirakami` とその配下 googletest) が
  未初期化だったのが 3 件の原因で、`--init --recursive` 後に消えた。
  signal 系 1 件は再走で緑 (既知のフレーク型)。
  残る `test_dev_wave_wait.py::test_real_git_production_provenance_rejects_malformed_merge_message` は、
  合成 repo へ tool だけを複製して走らせる形で `login_headroom` が無く import 段で dispatch へ倒れるもので、
  本 wave の変更箇所には到達しない。
- 段 5・段 6 の実装子はどちらも pytest を実走できず「実装済み・未実走」と申告した
  (`qstat -Q preflight rc=1`)。**測定はすべて親が行った。**
- 段 8 の候補は 1 件で、自動是正した。`DW-M07` が local を避ける理由として挙げていた
  「同一 target set の 2 巡目以降で予算 attest が落ちる」は本 wave の修正で解消されるため、
  恒久的な理由である「runner の実行経路を変異させると runner が自壊する」へ書き換えた
  (byte 減、節名以外の逐語 pin は無いことを実測して確認)。

## 次の一手差分

### 完了

- [T-1268] `_scope_properties_are_enforced` の page 丸め不整合を 3 tool で閉じた。
  受理集合は `{str(cap), str(cap - cap % P)}` のちょうど 2 値で、要求より緩い上限は 1 つも通さない。
  修正前 3 走すべて `rc=16` → 修正後 attest 成立・焦点走 722 passed、変異 matrix 8/8 KILLED。
  remaining: none
  base: c8987016581c09c16737033c8c4f5df3092263fa528f21b95a675cf90ecadf85

### 新規

- {{T:bounded-scope-marker-authority}} **P2・新規・ユーザー裁定待ち**:
  `_bounded_scope_membership` が環境変数 `IZANAGI_BOUNDED_SCOPE_*` 由来の cap を
  認可上限 (`MAX_LOCAL_BUDGET_BYTES`) と照合せず、grant 由来性も検証しない。
  偽の marker pair と自作 scope を用意すれば予約台帳と 1 コマンド 4 GiB 上限を迂回できる。
  HEAD 時点で既に成立しており [T-1268] は広げていない。修正は marker の trust 境界の設計判断を伴う
  (`cap <= MAX_LOCAL_BUDGET_BYTES` を必要条件にするだけでよいか、grant 由来性まで束縛するか)。
  段 3 レンズ A が発見し段 6 レンズ B が親の scope 外裁定を支持した。
