## must-fix

### MF-1 — `D` は宣言ではなく、任意文字列を後から消せる恒真化装置になっている

- **(a) 何が壊れるか:** `_CRITIC_D_SELECTORS` の digest 用 5 selector は正規化処理を制御していない。実装は `理由`・`証拠`・`読み方`・`その他の abort` を無条件に消すため、`evidence` に raw variant や候補コードを流す変異でも関係テストは緑になる。裁定が許した rejection の class/count を越えた免除である。
- **(b) 根拠:** selector を参照するのは harness JSON pointer だけで、digest 行は literal prefix で無条件除去される（[test_p3_autonomous_workload_trial.py:1025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1025)、[同:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1051)）。production は候補由来の `reason/evidence` をそのまま描画する（[digest.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:725)）。その供給元には候補行の逐語値が残る（[diff_quarantine.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/diff_quarantine.py:241)、[同:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/diff_quarantine.py:448)、[同:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/diff_quarantine.py:459)）。段4は D を outcome/metrics/rejection class・件数に限定している（[s4-adjudication.md:104](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s4-adjudication.md:104>)）。
- **(c) 最小の是正案:** digest を行文字列ではなく閉じた構造へ射影し、D の selector からのみ削除を生成する。`reason/evidence` は固定 reason code・行位置・長さ等へ閉じ、候補本文や digest を出さない。各 selector を一つ削除した変異と、`evidence=raw_variant` を注入する負例を追加する。
- **成果物影響:** 放置すると raw 候補文字列で critic payload と `input_payload_sha256`、critic 応答、次世代候補集合が変わり、最終 certified 選択および report/journal/receipt hash が候補 wire に依存する。

### MF-2 — 新 fixture は ABORT 済み WAL を `certified` / `dry-pass` と偽装している

- **(a) 何が壊れるか:** helper は明示的に `BUILD_START→ABORT(diff-quarantine)` を記録する一方、二つの fixture は同じ variant を `certified` として有限 fitness 付きで返す。別 fixture は `do_build=True` なのに ABORT WAL を作って `dry-pass` を返す。関係テストも preview/auditor を pass にした後、実 driver を通さず固定 reject を直書きしており到達不能である。production supervisor に outcome と WAL terminal の照合がないため、これはテストだけの嘘で終わらない。
- **(b) 根拠:** reject helper（[test_p3_autonomous_workload_trial.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:100)）と実 ABORT 書込み（[p3_s4_loop.py:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:250)）に対し、`certified` を返す箇所は [test_p3_autonomous_workload_trial.py:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:149) と [同:1544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1544)、build 時の偽 `dry-pass` は [同:1813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1813)。実 driver は pass 後の no-build を `dry-pass, variant=None` とし（[p3_s4_loop_trigger_gating.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:546)）、no-build digest も生成しない（[同:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:748)）。また関係テストが「32 点」と数える `src_token` は test 内で計算しただけで、実 WAL は常に `src_token=""` である（[test_p3_autonomous_workload_trial.py:1169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1169)、[p3_s4_loop.py:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:260)）。
- **(c) 最小の是正案:** `_run_workload` で outcome/variant/digest flag を admitted WAL terminal と照合し、`certified` は同一 variant の COMMIT、reject は ABORT、`dry-pass` は no-build・variantなし・digestなしに限定する。関係検査は段3の是正案どおり、実 driver の固定 auditor reject と、別の admitted renderer fixture に分割する。
- **成果物影響:** 放置すると ABORT 候補が generation report では `certified`・有限 metrics となり、critic の次手と certified 選択が汚染され、材料レポートと receipt は WAL と矛盾した参照を固定する。

### MF-3 — projector が campaign admission を迂回して raw WAL を読む

- **(a) 何が壊れるか:** projector は admission validator が発行する immutable view ではなく `wal.read_records()` を直接読む。後段 renderer の admitted view と別 snapshotになり、no-digest 経路では admission 自体が一度も走らない。truncate tail を黙って落とした WALからも label を発行できる。
- **(b) 根拠:** raw 読みは [p3_s4_loop.py:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:361)。`wal.read_records()` は truncated tail を捨てる（[wal.py:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/wal.py:622)）。正本は raw consumer に `AdmittedCampaign` のみを許す（[artifact_admission.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/artifact_admission.py:123)、[同:723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/artifact_admission.py:723)）。autonomous 経路は digest の有無を調べる前に projector を作る（[p3_autonomous_workload_trial.py:1742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1742)）。
- **(c) 最小の是正案:** factory は `AdmittedCampaign` だけを受け、`view.records` から mapping を作る。digest、projector、loader は同じ view を共有する。variant がない純 dry-pass だけは WAL を読まず `None` を直接出す。
- **成果物影響:** 放置すると未 admission／別 snapshot の WAL が `candidate_label` と critic input hash を決め、trial report・journal・receipt の参照と次世代 certified 候補集合が admitted WAL から乖離する。

### MF-4 — critic CLI は直接実行で落ち、import 経路では diff-quarantine を「全緑」にする

- **(a) 何が壊れるか:** `digest.py` を直接実行すると自身は `__main__`、そこから import する `p3_s4_loop` は別インスタンスの `critic.digest.IdentityProjection` を使うため、`isinstance` が失敗する。canonical import でこの問題を避けても CLI は `load_diff_rejections()` を渡しておらず、diff-quarantine だけの campaign を「rejection なし — 全 variant 緑」と描画する。
- **(b) 根拠:** class 定義と runtime type gate は [digest.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:40)、[同:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:630)。CLI 内 import と不完全な renderer 呼出しは [同:790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:790)。liveness loader は diff reject を意図的に除外する（[同:343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:343)）。
- **(c) 最小の是正案:** projection 契約を二重 import されない中立 module へ移す。CLI に `diff_rejections=load_diff_rejections(view)` を渡し、直接 subprocess 実行で「diff reject 1件・全緑文言なし」を固定する。
- **成果物影響:** 放置すると直接 CLI は critic digest を発行せず、別入口では hard reject が全緑へ反転し、critic の次手と後続 certified 選択が変わる。

### MF-5 — critic payload の破壊的変更を同じ v2 として発行している

- **(a) 何が壊れるか:** `harness_result.variant` を `candidate_label` に改名し、`critic_digest` を常時 string から nullable に変えたのに `SCHEMA_VERSION` は v2 のままである。同じ v2 の hash が異なる key/type semantics を持ち、過去 trial と意味比較できない。
- **(b) 根拠:** version は [p3_autonomous_workload_trial.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:142)、変更後 payload は [同:1744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1744)。既存決定は role payload の意味変更時に version bump を要求する（[decisions.md:5647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/decisions.md:5647)）。
- **(c) 最小の是正案:** role payload の `SCHEMA_VERSION` を v3 に上げ、nullable digest と `candidate_label` の exact schema を固定する。段4で scope 外とされた report/declassification-account v3 とは分離して扱う。
- **成果物影響:** 放置すると同じ v2 の `input_payload_sha256` が別構造を指し、real critic の応答・次候補・certified 選択と journal/report hash を過去 trial から判別不能に変える。

## should-fix

### SF-1 — 「全 production caller」検査が autonomous caller と raw escape を検査していない

- **(a) 何が壊れるか:** AST 検査は新しい最重要 caller を列挙せず、引数名しか見ない。`identity_projection=IdentityProjection.RAW` への変更や autonomous 再描画の `tag/reflux` 既定値化を許す。
- **(b) 根拠:** hard-coded 5 path と keyword-name 検査（[test_p3_s4_loop.py:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:830)）。RAW は通常の `IdentityProjection` として runtime gate を通る（[digest.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:66)、[p3_s4_loop.py:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:442)）。
- **(c) 最小の是正案:** autonomous file を棚卸し対象へ加え、critic-facing production caller では RAW を AST で拒否し、factory 呼出し・tag・reflux の値まで固定する。

### SF-2 — `reflux_ir` の import が source file の可読性に依存する

- **(a) 何が壊れるか:** 現実装に自己 hash の固定点問題はない。複合値を同じ source に literal として埋めていないためである。その代わり import 時に `__file__` を読むので、zipimport、sourceless/pyc 配布、source 非搭載・非可読配置で import 失敗または別 bytes の ID になる。
- **(b) 根拠:** import-time read は [reflux_ir.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:23)。trigger/autonomous の起動時 import に直結している。
- **(c) 最小の是正案:** hashed preimage の外に生成済み literal module/manifest を置き、production import は literal のみ読む。test/build 側で source と golden から再導出して literal を照合する。

### SF-3 — synthetic rejection の出所を `workload` に押し込み、未知 ID 防壁を空値で迂回している

- **(a) 何が壊れるか:** synthetic fixture は `variant=?` と表示され、出所は workload 用の open dict に後置される。admitted WAL由来の未知候補と見分けにくく、空 ID を許す規則で非 WAL rejection が同じ critic digest に混入する。
- **(b) 根拠:** 空 ID と workload の流用は [p3_s4_red.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_red.py:116)。renderer は heading の後で workload dict を生描画する（[digest.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:642)）。
- **(c) 最小の是正案:** synthetic control は admitted rejection と別 section/artifact に分離するか、閉じた `origin_kind="synthetic-fixture"` を heading に必須表示する。`workload` を provenance に流用しない。

## nit

なし。

## 総括

- **NO-GO。**
- 最大理由は、関係 oracle の D が宣言と機械的に結合しておらず、raw 候補コードを `evidence` に流しても緑になること。
- ABORT WAL を `certified` / `dry-pass` とする fixture は、既知の campaign dirname 赤とは別の正しさ破壊である。
- projector は admitted immutable view を迂回し、campaign admission と同一 snapshot の保証がない。
- critic CLI は直接実行不能で、別入口では diff-quarantine を全緑へ反転しうる。
- role payload の key/type 変更を同じ v2 で発行している。
- liveness `extra` の既裁定済み scope-out と、既知の 3 赤そのものは所見数に含めていない。
- pytest は実行しておらず、緑は主張しない。