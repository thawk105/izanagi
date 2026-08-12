---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t316-copyout-t840
seq: 1
title: [T-316] R-1 の (b) copy-out 厳格化 + (c) 併置を実装し、[T-840] は issuer 集合の機械閉包に縮めて成果物隔離を再裁定へ返した (コード + docs、branch worktree-dev-wave-t316-copyout-t840)
---

## 本文

**ユーザー裁定 (2026-08-12、rulings-inbox `2026-08-12-coarse-provenance-45rulings.md` 34–35 行):**
[T-316] R-1 = (b) build 出力 copy-out の厳格化 + (c) 本 wave の lexical 効果 gate を
defense-in-depth として併置、(a) source の DSL/IR 化は不採用。[T-840] (機械隔離) は同 wave 同梱。

**やったこと。** (b) を {{D:build-output-copyout-contract}} の契約で実装し、(c) は docstring のみ。
[T-840] は {{D:coder-issuer-machine-closure}} に従って**分割**し、実装できる部分だけ入れた。
実装は Codex `role=author` 2 単位 + fix 3 巡、親は brief・裁定・統合 commit・全走のみ。

**[T-840] を分割した理由 (裁定の前提を覆す新事実)。** 裁定は [T-840] (機械隔離) と
[T-841] (receipt 束縛、R3-3 / R3-9 後) を別項に分離したが、**成果物のレベルでは分離できない**。
`artifact_admission` は構造的に妥当な post-policy campaign を一律 `admitted` で返し、
coder 由来かも quarantine 通過かも読まない。layer3 はその `admitted` だけを certifying input の
条件にしている。したがって「非認証成果物として隔離する」には分類を下流が消費する必要があり、
それが [T-841] の receipt 束縛そのものである。registry に書くだけでは恒真ラベルになる。
段 3 の敵対レンズ 2 本が独立に指摘し、親が `artifact_admission` / `layer3_report` の実コードで裏取りした。
この依存関係は 2026-08-11 の裁定パッケージ R-2 に書かれていないため、親は不採用にせず再裁定へ返す。

**敵対検証 5 本がすべて NO-GO を出した。** 段 3 のレンズ 2 本、段 6 のレビュー 2 本、焦点再レビュー 1 本。
blocker 2 件 (close 失敗時の fd ownership transfer 漏れ、registry が下流へ接続されない) と
must-fix 11 件を 2 巡の fix で閉じた。**焦点再レビューは指摘を書くだけでなく、audit helper へ
synthetic source を実投入して 4 経路 (tuple/dict 格納、関数引数渡し、`globals()` 経由、
変数へ束ねた動的解決) が素通りすることを実証した。** これがなければ「別名は追跡済み」で終わっていた。

**変異検査が、静的レビュー 5 本が見つけられなかった 2 件を摘出した。**
{{F:flaky-anchor-contaminates-mutation-attribution}} と {{F:equivalent-mutation-recorded-as-unkillable}}。
前者は並列走行でしか出ないため静的には原理的に見えない。後者は「殺せない検査」ではなく
「何も変えていない変異」だった。fix 3 巡目で両方を閉じ、真因 (rename が held inode の `ctime` を
更新し、`_stable_file_identity()` の `ctime_ns` 比較で拒否理由が 2 分岐する) は fix worker が特定した。
親の初期推定 (`rglob` の非決定性) は外れており、そのまま記録する。

**単独で殺せない検査は冗長 gate として証拠から外した** ({{D:redundant-gate-not-counted-as-evidence}})。
通常ファイル検査を単独無効化しても 1 件も赤にならず (FIFO は `os.lseek` の ESPIPE、directory は
`os.read` の EISDIR が先に拒否する)、実効層を含む両層同時変異でのみ FIFO 2 件が落ちた。

**実測 (すべて Pegasus 計算ノード、`--force-dispatch`)。**

- 焦点走 (最終 tip `a469863d`): **323 passed / 0 failed**。範囲 = `test_buildcache_v2.py` /
  `test_p3_build_authority_cli.py` / `test_p3_exploration_namespace.py` / `test_build_admission.py` /
  `test_artifact_admission.py` / `test_build_site_gate.py` / `test_s8b_materialization.py`。
- 変異本走: **KILLED 8 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0、9 件すべて期待と一致**。
  baseline は `PASSED` (失敗 node ゼロ)。SURVIVED 1 件は事前に `SURVIVED` 期待で登録した M2。
- フレーク切り分け: 該当 node の単独走行 3 回連続で `2 passed` / rc=0。

**codex 子は全段で pytest を実走できなかった** (`qstat -Q preflight rc=1` / runner `rc=16`)。
5 本の子はいずれも「実装済み・**未実走**」と正直に申告し、緑を騙らなかった。実測はすべて親が行った。

**段 1 実測で `DW-O09` 不成立を判定した。** `FROZEN_MANIFEST` の 23 key はすべて `output/` 配下で
orchestrator source を pin しない。`t080_freeze_migration` が `p3_s4_loop_sort.py` の source SHA を
3 箇所 pin するが、照合は固定 commit の blob に対して行われ working tree を読まない
(現行 SHA `602e44fd…` は pin 値 `9b64f34b…` と既に相違)。歴史記録であり repin 不要。

## 次の一手差分

### 更新

- [T-316] **P1・R-1 の (b) + (c) を実装済み、R-1 は終端**: build 出力 copy-out を
  allowlist した binary 1 本の inode 束縛へ厳格化し、lexical 効果 gate を defense-in-depth として
  併置した ({{D:build-output-copyout-contract}})。**主張は cache publish 時点の inode 厳格化に限定**し、
  host-security boundary / certified safety / 実行時 binary identity / staging 全体の fd anchor /
  directory publish の create-only 原子性はいずれも主張しない。
  残る blocker ([T-184] canonical stage matrix 未発行、R3-3〜R3-9、R2-b 独立 oracle 本体) は**変わらず**。
  正本 = `output/insights/2026-08-12_t316-copyout-t840/package.md`
  base: d1128a0cd4cdc7a29ed2d96d288d8117f836d0dfdb80f888d69735ce7f3ee74a
- [T-840] **P1・部分実装、成果物隔離は要再裁定**: issuer 集合の機械閉包
  (単一 registry の typed 拡張 + 未登録 site からの coder authority 発行の fail-closed 拒否 +
  tracked Python 全体を母集合とする AST 閉包) を実装した。**現存 6 entry point は 1 件も落ちない。**
  しかし**これは成果物の隔離ではない** — `artifact_admission` は依然として構造的に妥当な campaign を
  `admitted` で返す ({{D:coder-issuer-machine-closure}})。
  **ユーザー再裁定 5 件 (Q1〜Q5) を裁定パッケージで返す**: (Q1) red / kickoff を廃止するか
  実行可能だが認証されない lane として残すか、(Q2) 分類を `artifact_admission` / layer3 / WAL /
  COMMIT へ束縛して真の成果物隔離にするか ([T-841] と同時)、(Q3) calibrator の任意 binary path と
  shell materializer の扱い、(Q4) 旧実装が作った既存 cache entry を拒否・再発行するか、
  (Q5) fd-to-exec 束縛・build 子孫の終了保証・floor/oracle の store/resume 束縛。
  base: 1fbf0378025349a39512e984bed8af122395d65a106b4b8c72a66e1fbefe7270

### 新規

- {{T:mutation-waiter-early-return}} **P3・新規**: `tools/dev_wave_wait.py producer` が、生産者が
  稼働 42 秒・`.done` 不在・成果物不在の状態で rc=0 の完了通知を出した (本 wave の fix 2B)。
  pid file の内容と `ps` の生存は一致しており pid 取り違えではない。stdout は空で、rc だけでは
  完了と打ち切りを区別できない。3 点照合 (`.done` / 成果物 / 生産者の死) を毎回行っていたため
  検出できたが、照合を省くと「子が死んだ」と誤認して次段へ進む。
