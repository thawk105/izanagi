---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1416-backoff-screening-compiler-binding
seq: 1
title: [T-1416] backoff_sweep/p2_2 へ D293 同型の site 依存 compiler 解決 + toolchain 束縛検査を実装した (実装、branch worktree-dev-wave-t1416-backoff-screening-compiler-binding)
---

## 本文

- entry701 (`docs/archive/worklog-phase3-0819-701.md`) が記録した D58 ablation 起動失敗
  (Pegasus 計算ノードで g++-13 不在により `source_digest.resolve()` が fails-closed) の
  条件(b) — {{D:site-toolchain-binding-scope}} 同型の実装 — を4 commit で実施した。
  既存 screening 無し3 campaign データ (backoff-sweep-silo-{write-heavy-sweep-493813a7,
  balanced-sweep-484c663e,read-heavy-sweep-610004b9}) は無傷のまま保持。
- 段2 codex plan が段1 brief の想定を訂正: source_digest の cxx 解決 (P1-1) と実際の
  build compiler 解決は別物で、P1-1 単独では D293 を満たさないと判明。
- 段3 敵対相談2レンズ (正しさ境界/スコープ実効性) が「compiler だけ site 依存化して
  ENV_TAG は Linux のまま」という折衷案は `execution_guard.py` の build 前認可検査に
  より現行構造では通らないと確認。ENV_TAG/Pegasus 公式実行有効化は次wave送りと裁定
  ({{D:site-toolchain-binding-scope}})。
- 段6 敵対レビュー2本: real 所見2件 (cache hit 時の full-version toolchain 束縛欠落
  {{F:cache-hit-toolchain-drift}}、新設テストの screening/loop forwarding 検証不足) を
  fix (計3件) で解消。焦点再レビューが所見1を「対応しないなら明示的な scope waiver を
  decisions.md へ記録せよ」と要求し、{{D:cache-hit-toolchain-drift-waiver}} で対応。
- 変異matrix 11件 (DW-M01): F358 (`docs/failures.md:9270`) と同型の
  contract-loader-drift 偽陽性 (pipeline.py/loop.py が enforcement source closure
  member のため、変異注入時の disk-bytes-vs-HEAD-blob 不一致で無関係なテスト群が
  機械的に ERROR/FAILED になる) が4件で発生。共通核を機械的に差し引き、うち2件
  (M5, M10) は codex 提案の expected_nodes が過大だったと判明 (単一理由性違反:
  対象コードに到達しない/loop.py へのどんな変異でも contract-loader-drift ERROR に
  なる) — expected_nodes を訂正した縮小 spec で再検証し、全11件 KILLED 相当を確定
  (SURVIVED 0件)。F358 へ再発追記 ({{F:cache-hit-toolchain-drift}} とは別件、
  `run_campaign` 内部の `ident.verify_against_lock` 経由でも同型 ERROR が起きるという
  詳細)。
- codex 工数: 段2 plan 1・段3 consult 2・段5 author 1・段6 review 2・fix 3・focus 1・
  変異design consult 1 = 計11回。全て rc=0、check_codex_output.py 通過。

## 次の一手差分

### 完了

- [T-1416] backoff_sweep.py/p2_2.py の site 依存 compiler 解決 + toolchain 束縛検査を
  実装した (段1-6 完了、詳細は上記本文と {{D:site-toolchain-binding-scope}}・
  {{D:cache-hit-toolchain-drift-waiver}} 参照)。ENV_TAG/Pegasus 公式実行有効化は
  次wave の scope として明示的に持ち越す (次の一手へ新規登録)。
  remaining: none
  base: cb0698f33b9d66602456baef6e13e454d079879cad4872ca8f11134cfa654b92

### 新規

- {{T:pegasus-official-run-env-tag-activation}} **P1・新規**: ENV_TAG を Pegasus 用
  runtime tag へ切り替え、`execution_guard.py` の Pegasus 公式実行認可・追加
  calibration 実測・S8b machine pin からの分離を行い、D58 ablation を実際に
  Pegasus 計算ノードで実行可能にする。前提: {{D:site-toolchain-binding-scope}} の
  実装 (本エントリ) が land 済みであること。
- {{T:buildcache-cache-hit-toolchain-binding}} **P2・新規**: `buildcache.py` の v2
  build cache (completion.json) に full-version toolchain manifest を保存し、
  cache hit 時にも expected_toolchain_manifest との完全一致を照合する
  ({{D:cache-hit-toolchain-drift-waiver}} が明示した既知の限界の恒久対応)。
