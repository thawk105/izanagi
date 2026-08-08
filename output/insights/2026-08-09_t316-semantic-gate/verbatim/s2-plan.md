推奨は案 (iii) の非対称構成です。すなわち、全軸の build/run を credentialless・network 無し sandbox に置き、AST/DSL は backoff と trigger-gating に限定します。sort-strategy は raw comparator 合成を維持し、sandbox で被害半径を絞ります。これは実装裁定ではなく、3 前提が揃うまでの設計裁定です。

本番コードは編集しておらず、確認は静的な file:line 読解と文書 byte 数の確認だけです。

## R1. 現状認識と静的補正

### α が通る理由

`DiffQuarantine` の load-bearing な保証は物理行の封じ込めだけで、C++ の意味 admission ではありません。[diff_quarantine.py:9–22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/diff_quarantine.py:9) はこの限界を明記し、実装も hole 内では前処理指令・コメント delimiter・行末 backslash しか検査しません。[diff_quarantine.py:394–497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/diff_quarantine.py:394)

`source_digest` も意味 gate ではありません。`EVOLVE_BLOCK_SOURCES` は二つのファイルを列挙するだけで、hole の文法を定義していません。[source_digest.py:73–82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/source_digest.py:73) `resolve_evidence()` が束縛するのは source bytes、diff、identity です。[source_digest.py:836–876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/source_digest.py:836)

generic coder 契約は「#if 枝の中の既存 API を使う straight-line C++」であり、複数行を型で拒否しません。[coder.md:13–21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/.claude/agents/coder.md:13) 無限ループは契約違反ですが機械 enforcement がなく、`std::system` 等の straight-line 呼出しは文法上通ります。

### β が通る理由

`assert_digest_matches()` は実 diff の SHA-256 と auditor 提示値の一致しか見ません。[auditor_gate.py:148–164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/auditor_gate.py:148) `parse_auditor_dict()` は `pass` かつ空 violations を正当として受理します。[auditor_gate.py:203–243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/auditor_gate.py:203) sort driver はその二条件後、`pass` なら build へ進みます。[p3_s4_loop_sort.py:137–164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop_sort.py:137)

したがって β は「同じ diff を見た」という attribution 証明であって、安全性証明ではありません。D127 決定 (6) も auditor を security credit 上 advisory としています。[decisions.md:6263–6267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/decisions.md:6263)

### D127 決定 (5) の現在地

D127 当時の cache class 未束縛は歴史的事実ですが、現在の直接経路では後続 D136 により閉じています。

- legacy cache key は admission receipt digest を含みます。[buildcache.py:130–148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:130)
- v2 preimage と completion manifest も admission を束縛します。[buildcache.py:250–266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:250)
- D136 が cache/replay/campaign identity への束縛を決定済みです。[decisions.md:6610–6630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/decisions.md:6610)

残るのは旧・推移的 artifact、shell materializer、任意 binary path、同一 process issuer、ABA/mixed snapshot です。[decisions.md:6650–6654](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/decisions.md:6650) 新 sandbox profile を cache/WAL identity に束縛しなければ、D127 (5) と同型の穴を再導入することになります。

## R2. 案 (i) — 全軸を AST/DSL にする

### 設置点

1. proposal 入口

   [projection_guard.py:28–41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/projection_guard.py:28) に次の closed contract を追加します。

   - `scalar-ir`: `{axis,value}`
   - `comparator-ir`: enum tag と型付き node のみ
   - `trigger-wire`: 既存のまま

   `assert_closed_proposal_schema()` の分岐点は [projection_guard.py:283–334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/projection_guard.py:283) です。raw `implementation` と IR の併記は禁止します。

2. compiler

   新規 `orchestrator/campaign/semantic_gate.py` に以下を置きます。

   - `parse_scalar_ir()` / `emit_backoff_cpp()`
   - `parse_comparator_ir()` / `emit_sort_cpp()`
   - `CompiledHole` と `SemanticReceipt`
   - marker/source/full tracked-diff への束縛

   trigger は既存 `reflux_ir.py` を移動せず再利用します。既に exact 5-bit parser と固定 token emitter が存在します。[reflux_ir.py:113–141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/reflux_ir.py:113)

3. coder→diff

   - backoff: [p3_s4_loop.py:115–121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop.py:115) から `implementation` を除き、値だけを compiler に渡します。現行の regex 帰属検査 [p3_s4_loop.py:762–798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop.py:762) は不要になります。
   - sort: [p3_s4_loop_sort.py:110–118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop_sort.py:110) と loader [p3_s4_loop_sort.py:270–301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop_sort.py:270) を raw string から `ComparatorIR` に変更します。
   - trigger: 現状でも wire→predicate→quarantine です。[p3_s4_loop_trigger_gating.py:390–405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:390)

4. 最終 build admission

   proposal loader だけでは direct `buildcache.build()` が迂回路になります。compiler が発行した `SemanticReceipt` を source evidence に束縛し、[build_admission.py:424–483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/build_admission.py:424) で新しい `DSL_GENERATED` class として導出します。`build()` / `build_v2()` の既存 `require_build_admission()` が最終 materializer gate になります。

   現行 `DiffQuarantine` は単一 marker しか検査せず、marker-set completeness を持ちません。[diff_quarantine.py:24–26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/diff_quarantine.py:24) 従って receipt 発行時には full tracked diff を全 marker/template 差分へ割り当て、未帰属 hunk を拒否する必要があります。

### 脅威被覆

- α: **消す**。raw coder bytes が C++ emitter に届かず、compiler が固定 token だけを生成することが条件です。
- β: **塞がない**。ただし source 安全性が auditor pass に依存しなくなるため、α に関しては非 load-bearing になります。
- 残余: compiler bug、IR receipt issuer、sort の SWO/fairness、許可された式による reward hack。

### 三軸適合

- backoff: 適合。coder は値を自力選択し、trusted compiler が固定一行へ落とすため D39 の「値の自力合成」は維持できます。
- trigger-gating: 適合。既に 5-bit wire と固定 emitter で同じ形です。
- sort-strategy: 不適合。現行契約は comparator ラムダを含む複数行 `sort(...)` 文そのものの合成です。[coder-v4-autonomous-sort.md:58–89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/.claude/agents/coder-v4-autonomous-sort.md:58) 出力も明示的に「複数行コード」です。[coder-v4-autonomous-sort.md:105–130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/.claude/agents/coder-v4-autonomous-sort.md:105)

D127 の「allowlist 選択に化ける」は、述べられた狭い boolean DSL に限れば実質的に真です。SWO を構成的に保証するには、許可 field と昇順/降順の辞書式 key 列など、host が先に決めた有限の意味族へ狭めざるを得ません。ただし「有限なら synthesis ではない」は一般には真ではありません。backoff 値も trigger の 32 wire も有限です。決定的なのは、sort の事前登録済み評価対象が raw C++ code synthesis であり、それを別の typed-program synthesis へ変更する点です。

### コスト

共通 parser を作っても、symbol table、型、意味不変条件、emitter、golden、positive control は軸固有です。新軸ごとに文法追加が必要です。段 8a は構文契約・列挙空間・positive control を軸ごとに要求し、第三の変異型はテンプレ改訂と D41 水準レビューを要求します。[axis-onboarding.md:223–240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/axis-onboarding.md:223) 通常固定費は約 5 セッション/軸です。[axis-onboarding.md:263–280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/axis-onboarding.md:263)

## R3. 案 (ii) — build/run sandbox

### 正しい seam

`run_campaign()` 全体を sandbox 内へ入れてはいけません。WAL、cache、repo、認証情報への書込み mount が必要になり、境界が広がるためです。親 orchestrator は外側に残し、untrusted source/binary を消費する子 process だけを包みます。

```text
loop.run_campaign             policy/profile を campaign identity へ束縛
        ↓
pipeline.evaluate             admission 後に同 profile を build/run へ配る
        ├─ buildcache.build / build_v2
        │        └─ buildcache._run → sandbox
        ├─ pipeline._run_trace → sandbox
        └─ calibrator.run_once → sandbox
```

具体的には次です。

- 新規 `orchestrator/campaign/execution_sandbox.py`

  `SandboxProfile`、`SandboxRunner.run()`、backend attestation、stage 別 mount/env/seccomp/resource policy、receipt を置きます。loose bool や環境変数 opt-in は持たせません。

- profile の authority

  `BuildRunContext` [build_admission.py:147–179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/build_admission.py:147) に登録済み profile を必須で持たせ、policy preimage [build_admission.py:281–313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/build_admission.py:281) に profile digest を入れます。これにより既存の admission→cache/campaign identity 束縛を再利用できます。

- build

  `build()` と `build_v2()` は既に context/admission を必須にしています。[buildcache.py:575–608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:575) [buildcache.py:802–821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:802) 実 subprocess の集約点 [buildcache.py:1052–1068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:1052) を `SandboxRunner` に置換します。configure/build の呼出し箇所は legacy が [buildcache.py:887–893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:887)、v2 が [buildcache.py:721–737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:721) です。

- trace/run

  `_run_trace()` の直接 `subprocess.run` を包みます。[pipeline.py:260–281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:260)

- perf bench

  `run_once()` の `subprocess_runner=subprocess.run` 既定を廃止し、必須 backend にします。[runner.py:346–373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/calibrator/runner.py:346) 現状 `measure_point()` は injected runner を一部 mode でしか下流へ渡しません。[runner.py:396–450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/calibrator/runner.py:396) ここを残すと通常 campaign が unsandboxed のままなので must-fix です。

- loop/pipeline

  `run_campaign()` は profile を policyへ束縛する propagation seam です。[loop.py:92–123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/loop.py:92) `evaluate()` は build と実 run の合流点です。[pipeline.py:476–520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:476)

- 追加対象

  untrusted source を読む preprocess と post-build `nm` も同じ境界へ入れるべきです。[source_digest.py:320–352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/source_digest.py:320) [buildcache.py:1026–1049](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:1026)

### stage profile

最低でも profile を分けます。

- preprocess/build: source は read-only、build staging のみ writable
- trace: binary/read-only libs + private trace dir のみ writable
- perf: binary/read-only libs + private perf/log dir のみ writable
- 共通: private PID/proc/tmp、network namespace 無し、host home・agent socket・credential file 非 mount、環境変数 allowlist、no-new-privs、process-tree 単位 timeout/pid/memory cap

run profile に repo、cache、campaign output を writable mount してはいけません。`std::ofstream` は private scratch には書けても、host artifact は変更できない構成にします。

### 脅威被覆

- α: **絞る**。任意 C++ は残るため消えません。network/credential/host filesystem への影響と無限実行時間を絞ります。
- β: **塞がない**。ただし host security は auditor verdict に依存しなくなるため、その範囲では非 load-bearing です。
- certification integrity: 塞がない。悪意ある binary は許可された stdout/trace dir を偽造できます。これは sandbox ではなく規律2の reward-hack 問題です。

### 三軸適合

候補言語を一切変えないため、backoff の値合成、sort の raw comparator 合成、trigger の wire 合成をすべて維持します。stock と全 variant を同一 profile で走らせ、profile digest を campaign identity に入れなければ性能比較が汚染されます。

## R4. 案 (iii) — 両方

「全軸一律に AST/DSL + sandbox」ではなく、次の非対称構成を採ります。

- 全軸: 案 (ii) を host-security boundary とする。
- backoff: value-only IR + trusted compiler。
- trigger-gating: 現行 5-bit wire + emitter を materializer-bound receipt に格上げ。
- sort-strategy: raw comparator を維持し、構造検疫 + sandbox。auditor pass は安全 capability にしない。

この解釈は sort role の「複数行 comparator コードを独立合成する」実験目的 [coder-v4-autonomous-sort.md:128–134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/.claude/agents/coder-v4-autonomous-sort.md:128) と、trigger role の「wire だけを合成する」契約 [coder-v4-autonomous-trigger-gating.md:62–77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/.claude/agents/coder-v4-autonomous-trigger-gating.md:62) の両方に整合します。

ただし DSL/raw の軸別分類を caller 自己申告に戻してはいけません。`transaction.cc` は sort と trigger の両 marker を含むため、compiler receipt または raw-sort quarantine receiptを exact `SourceEvidence` と full tracked diff に束縛し、未分類・複数 marker・未帰属 hunk は build admission で拒否します。

## R5. 3軸 × 3案の被覆表

| 軸 | (i) 全軸 AST/DSL | (ii) sandbox | (iii) 非対称併用 |
|---|---|---|---|
| backoff | α **消す**、β **塞がないが非 load-bearing**。value 合成は維持 | α **絞る**、β **塞がない**。現行 raw implementation を維持 | α **消す** + sandbox。value 合成を維持 |
| sort-strategy | α **消す**、β **塞がないが非 load-bearing**。ただし raw-code synthesis を host 定義の式族合成へ変更するため不採用 | α **絞る**、β **塞がない**。raw comparator 合成を完全維持 | α **絞る**、β **塞がない**。raw comparator 合成を維持する推奨セル |
| trigger-gating | α **消す**。既存 wire/emitter を最終 admission まで延長。β **塞がないが非 load-bearing** | 現行 wireを残すため αは実質 **消す** + sandbox、βは **塞がない** | α **消す** + sandbox。現行 5-bit synthesis を維持 |

β はどの案でも auditor 自体を修理しません。「非 load-bearing」は「pass が security capability を発行しない」という意味であり、auditor の判断精度が上がるという意味ではありません。

## R6. auditor advisory 化

採るべき規則は deny-only です。

- `auditor.pass` は build/sandbox/semantic admission capability を一切発行しない。
- `reject` / `uncertain` は保守的な品質 veto として候補を狭めてよい。
- `diff_digest` は attribution/provenance にだけ使う。
- 安全性の根拠は、DSL receipt または sandbox receipt と verifier に置く。
- raw sort に対しては「auditor pass = 安全」と記録しない。

これにより echo された `pass` は独立 gate を迂回できません。ただし raw sort の意味安全性や fairness を証明するものは残らないため、その穴は規律2の残余として明示します。

静的 anomaly として、[auditor_gate.py:4–7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/auditor_gate.py:4) の “fails-closed” は digest attribution にだけ正しく、verdict の意味には適用できません。D127 と `diff_quarantine.py` の記述が正しい限定です。gate を飛ばせ等の指示様文字列は必読入力中に確認していません。

## R7. 残余の開いた境界

- 同一 process issuer: seal/private factory は真正性境界ではありません。[build_admission.py:4–13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/build_admission.py:4) DSL receipt と sandbox token にも同じ限界を明記します。
- cache/replay: 現行 class 束縛は閉じていますが、sandbox profile/compiler identity を admission・cache・campaign・WALへ束縛しなければ再発します。
- transitive/旧 artifact: 全歴史 artifact の遡及再分類は依然別問題です。
- raw sort: sandbox 内での stdout/trace 偽造、private scratch 破壊、CPU消費は残ります。
- reward hack: backoff 0、fairness を犠牲にする comparator、trigger wire による starvation は sandbox/DSLとは別です。verifier・liveness/fairness 観測点・規律2が所有します。
- sandbox escape/kernel/compiler bug: containmentの前提外として backend version、seccomp profile、node kernel を receipt に残します。

## R8. 実装 wave の事前条件

1. 計算ノード backend の決定的計測

   login node の bwrap/unshare 実測を転用してはいけません。親 brief 自身が compute node 未計測としています。[s1-brief.md:24–29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate/s1-brief.md:24) 実 `qsub` 計測 ID を作り、少なくとも以下を確認します。

   - user/net/pid namespace が起動可能
   - network connect と credential/home/agent socket access が失敗
   - source RO・scratch限定 write
   - process-tree timeout が子孫を残さない
   - CMake build、trace、`perf stat`、numactl、48-thread run が成功
   - stock/variant双方で性能差と floor 再較正要否を測る

   `DW-G04` は既存 artifact path または計測 ID が書けるまで実装せず設計メモに留める規則です。[core.md:60–63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/dev-wave/core.md:60)

2. docs 予算 [T-664]

   `tools/check_docs.py` の dev-wave aggregate ceiling は 25,200 bytesです。[check_docs.py:247–258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/tools/check_docs.py:247) 静的実測では現在 4 reference が 25,199 bytes、dispatcher が 9,457/9,500 bytesでした。backend契約・stage別 profile・失敗時規則を恒久文書へ置く余地がないため、[T-664] の陳腐化 prose 削除または機械検査化を先行させます。[worklog.md:549–552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/worklog.md:549)

3. stage matrix 所有 [T-184]

   T-316 内で並行する独自 matrix を新設せず、[T-184] が所有する model/resource/retry の stage policy に sandbox profile を追加してから消費します。[worklog.md:635–637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/worklog.md:635) 対象 inventory は build、preprocess、post-build inspect、trace、perf、および pipeline 外の直接 binary materializer 全件です。

4. 事前登録する受入条件

   - `system`/network/file-write/infinite-loop の4種について、DSL reject または sandbox containment を区別して期待値化
   - 正しい digest + `pass` + 空 violations が capability を発行しない β control
   - sandbox profile違いの cache/replay拒否
   - backoff value、trigger wire、raw sort comparator の synthesisability をそれぞれ維持
   - stock/variant、trace/perf の同一 profile 適用と環境タグ記録

## 総括

推奨は、全軸 sandbox + backoff/trigger限定DSLの非対称な案 (iii) です。  
全軸一律DSLは sort の raw comparator 合成実証を別実験へ変えるため不採用です。  
auditor pass は security capability から外し、digest は attribution、reject は deny-only veto に限定します。  
実装開始条件は計算ノード実測ID、[T-664] のdocs余白、[T-184] のstage matrix確定です。  
最大の未解決点は、raw sort がsandbox内の評価出力を意味的に攻撃できる規律2の境界です。