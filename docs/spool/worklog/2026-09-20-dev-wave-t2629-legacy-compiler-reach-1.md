---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2629-legacy-compiler-reach
seq: 1
title: [T-2629] 旧 build 分岐の compiler 非対称の到達条件と既存の拒否を計算ノードで実測し、修正せず限界として閉じた (docs のみ、branch worktree-dev-wave-t2629-legacy-compiler-reach、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- 裁定 D2044 項 24 の範囲で 1 wave。一次資料は `output/insights/2026-09-20/t2629-legacy-compiler-reach/README.md`
  (非対称の条件、呼び手の閉包、実測、裁定、限界、一次資料の所在)、設計判断は {{D:legacy-build-compiler-asymmetry-closed-as-limit}}。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2629-legacy-compiler-reach/HANDOFF.md`。
- 段 1 brief 前の静的読取で、非対称は「`env_contract` 無し (旧分岐) × 実 site が Pegasus 計算ノード」の積でだけ成立すると
  特定した (それ以外の site では `compilers_for_current_site()` が既定を返し対称)。AST 走査で certified 入口 3 API の
  呼び出し 28 箇所 (中継 3 + 外側 25) を分類: pegasus 契約で `env_contract` を省く呼び手は 0、省く 12 件は全て
  `linux-baremetal`。
- 段 3 相談 1 本 (2 レンズ) は must-fix 5 を出し全採用: 直接 `buildcache.build()` 呼び手 (7 file・8 箇所) の閉包を追加 (全て対称)、
  `g++-13` 不在を全 node へ一般化しない、「対称化は abort reason が変わるだけ」は `identity-error` (retryable) /
  `build-error` (非 retryable) の差で反証、evidence 一致検査の保証範囲を限定、probe の stock admission 条件
  (`ccbench_commit == pin.CURRENT_PIN`) を明記。加えて repo 内 campaign WAL 30 本 (全部 `linux-baremetal`) を JSON として集計し、
  `build-error` abort 12 件の error 本文に compiler 不在型の診断は無し (本文なし 2 件は判定不能)。
- 段 5 は Codex author 1 本 (probe 147 行、production 関数の直呼び・stub 無し・共有 cache 回避)。probe は repo に残さず
  job dir へ退避 (unit branch `dev-wave-t2629-unit-probe` 終端 commit `39585d2fc` にも同一内容)。
- 実測 (2026-09-20 07:41〜07:42 JST): login `pegasus02` は site compiler = 既定で対称、`g++-13` 不在。計算ノード `bnode020`
  (NQSV `11860.nqsv`) では `linux-baremetal` の認可が `CertifiedWriterAuthorizationError` で拒否、`pegasus` は通過、
  site compiler `g++` (11.4.0) で stock evidence を確定、既定 `g++-13` の evidence は起動不能の `RuntimeError`、
  旧分岐 `buildcache.build()` (cc/cxx 無し) は admission 3 段を通過した後 cmake configure が
  `CMAKE_CXX_COMPILER: g++-13 … was not found in the PATH` (rc=1) で `RuntimeError` → 静的読取どおり fails-closed。
- 段 6 は独立 read-only レビュー 1 本 (README・fragment・probe JSON の対応): must-fix 2 (裁定 fragment が静的確認を実測へ
  拡張、WAL 集計の event 混同)、should 2、nit 2 を全部反映した。レビューの「`build-error` 27 + `s1-session` 3」は親の JSON 集計
  (12 + 18) と食い違い、現物の値で書いた。`base:` は現行本文と一致 (レビューが独立に検算)。逐語は README §7。
- 受入全走は、記録 commit で HEAD を最終形にした後に land 前に 1 回 (land はその受領証を要求する)。結果は job dir の受領証
  `acceptance-receipt-*.json` と `acceptance-child-*.log` (受理は `child-green` だけ)。
- 棄却・限界: 閉包は静的。`g++-13` 不在は 3 node・2 日付の観測で一般化しない。evidence 一致検査は「compiler の一致」を
  保証しない。v1 経路の toolchain 非束縛 (D293 の領域) は本 wave の主張外。Pegasus の durable output root 配下の WAL は未検索。
- 工数: codex 3 本 (consult 1、author 1、review 1)、計算ノード job 1 (probe、walltime 15 分枠で数十秒)、login probe 1 走。

## 次の一手差分

### 完了

- [T-2629] 到達条件と既存の拒否を計算ノードで実測し、修正せず限界として閉じた。確認した呼び手の範囲
  (certified 入口 3 API の 28 箇所 + 直接 `buildcache.build()` 7 file・8 箇所) と保証境界は insight と
  {{D:legacy-build-compiler-asymmetry-closed-as-limit}} に明記した。
  remaining: none
  base: 5d7fc53b9ce2a7f5ee68384890be07c1e9dd0add863e80cb52ee0146a03f4866
