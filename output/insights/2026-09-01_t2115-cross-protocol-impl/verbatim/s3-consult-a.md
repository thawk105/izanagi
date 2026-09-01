## 所見

### 1. `legacy implicit silo` が stock mocc の within-run 値を公式 report に混入させうる

**主張:** 計画の legacy 互換規則は「歴史的 silo file」と「新しく stock mocc で生成した protocol 不明 file」を区別しません。したがって trace-hook のない mocc の測定値が silo の値として層 3 公式 report に到達可能です。

**根拠 (file:line):**

- calibrator は任意の `ycsb_*.exe` を受け取り（[cli.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/cli.py:132)）、入口では trace symbol 不在だけを検査し、transaction verifier は通しません（[cli.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/cli.py:187)）。
- 非 certify 経路は protocol/genome を持たない JSON を固定 stem に書きます（[report.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/report.py:72)、[cli.py:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/cli.py:1064)、[cli.py:1077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/cli.py:1077)）。
- 計画は、`noise_floor` があり `genome` がない全 record を、hash・既知 path・生成時点の限定なしで implicit silo とします（[plan.md:91](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:91)）。
- 層 3 は calibration directory 直下の全 JSON を走査し、shape 一致だけで値を採用します（[layer3_report.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:337)、[layer3_report.py:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:348)、[layer3_report.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:378)、[layer3_report.py:402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:402)）。
- `build_accepted_report()` も同じ `build_report()` の floor を保持し、floor producer の correctness verification を追加要求しません（[layer3_report.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:674)、[layer3_report.py:707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:707)）。
- 提案正例も「genome 無しなら silo」を実体識別なしで受理させます（[plan.md:189](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:189)）。

これは新設された calibrator path ではありませんが、protocol 対応後も残る防壁の穴であり、計画する例外がその入力を明示的に受理します。

**成り立つ場合の成果物影響:** `noise_floor.within_run.value/source/protocol` が stock mocc の値なのに silo provenance で確定し、公式 material report とそれを使う採否閾値が変わります。

**確信度:** 高。

### 2. 凍結 pin は path manifest 以外にもあり、計画の編集面が source binding を壊す

**主張:** 「編集 file が `FROZEN_MANIFEST` の key でない」ことから「凍結影響なし」は導けません。`genome.py` と screening caller 3 file は、凍結済み known-axes 内で file 全体の SHA として pin されています。

**根拠 (file:line):**

- `known_axes_freeze.json` は `genome.py` の SHA を明示的に保持します（[known_axes_freeze.json:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/output/s1-freeze/known_axes_freeze.json:107)）。同様に `backoff_sweep.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py` も同 artifact の source record です（[known_axes_freeze.json:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/output/s1-freeze/known_axes_freeze.json:152)、[known_axes_freeze.json:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/output/s1-freeze/known_axes_freeze.json:200)、[known_axes_freeze.json:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/output/s1-freeze/known_axes_freeze.json:51)）。
- verifier は各 source の現在 bytes を再 hash し、不一致を拒否します（[s1_known_axes_freeze.py:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/s1_known_axes_freeze.py:856)、[s1_known_axes_freeze.py:869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/s1_known_axes_freeze.py:869)）。
- S8b oracle driver はこの verifier を起動 gate で呼びます（[s8b_oracle_driver.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/s8b_oracle_driver.py:501)）。
- 計画は `genome.py` に加え caller 3 file も編集対象にしています（[plan.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:3)、[plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:67)）。

現時点では `genome.py` の実 SHA は凍結 record と一致します。caller 3 file には既存 drift もあるため oracle 全体が現在受理されるとは主張しませんが、計画は少なくとも `genome.py` の成立中の source predicate を新たに偽にします。

**成り立つ場合の成果物影響:** 凍結 bytes 自体は不変でも、known-axes の参照受理が追加で壊れ、S8b oracle gate が `known-axes-freeze-verify` 拒否になります。

**確信度:** 高。

### 3. 「trace-hook を持つ protocol だけ admit」は固定 allowlist に退化し、提案負例も恒真

**主張:** 計画が実装するのは hook/pin の検査ではなく `{"silo"}` 固定集合です。したがって mocc 負例は source の hook 有無に関係なく常に緑になります。

**根拠 (file:line):**

- 計画は admission を `{"silo"}` に固定します（[plan.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:45)）。
- 負例は build/measure/write が呼ばれないことだけを確認し、現在 pin と hook の対応を検査しません（[plan.md:181](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:181)）。
- 現在 pin は `511c953` 固定です（[pin.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/pin.py:28)）が、repository 内には mocc trace source の別 pin が既にあります（[mocc_trace_v1_policy.json:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/tools/pegasus/mocc_trace_v1_policy.json:15)）。
- よって hook 有り pin へ移っても allowlist と負例の結果は変わらず、「hook が無いから拒否」を証明しません。

現在 pin で mocc を止める向き自体は安全です。問題は、述語が主張する source 事実に束縛されず、移植完了後も必要な mocc floor を拒否し続ける点です。

**成り立つ場合の成果物影響:** 現在の公式値は増えませんが、trace 移植後も mocc floor の受理集合が空のままで、mocc report は `no-matching-env-record` から前進できません。

**確信度:** 高。

### 4. mocc 正例は提案 system 内で生成不能な synthetic input に依存する

**主張:** consumer の mocc 正例は緑になりますが、変更後 system にその入力を作る production 経路がありません。これは cross-protocol の正例ではなく parser の正例です。

**根拠 (file:line):**

- 計画自身が `space_for()` の production caller はないと認めています（[plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:24)）。
- 実 production search は `SILO_SPACE` を直接 import・列挙します（[p2_2.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/p2_2.py:35)、[p2_2.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/p2_2.py:365)、[guided.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/guided.py:40)）。
- between-run producer は mocc を固定拒否し（[plan.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:45)）、within-run producer の protocol 対応も後続へ送ります（[plan.md:95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:95)）。
- それにもかかわらず層 3 正例は mocc campaign と mocc floor を fixture で直接与えます（[plan.md:186](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/artifacts/dev-wave-t2115-cross-protocol-impl/plan.md:186)）。

**成り立つ場合の成果物影響:** `space_for("mocc")` の API 受理だけが増え、certified mocc campaign・floor・公式 report の実受理集合は増えません。

**確信度:** 中。今回を純粋な先行 scaffolding wave と定義し直すなら許容できますが、親 brief の「残余を公式成果物へ接続する」という完了主張とは一致しません。

## プランのどこが正しいか

- 現 pin の mocc subtree 全体を検索し直した範囲では、mocc source から `trace.hh` や `#if TRACE` への参照はありません。共通 header と CMake の `TRACE` 定義は存在しますが、mocc から未使用です。別 pin の hook と現 pin を分けた親の限定主張は正しいです。
- `space_for()` の直接・別名・`getattr`・文字列参照を再検索しましたが、production caller は見つからず、現 consumer は test だけという主張を反証できませんでした。
- mocc の live 軸を `BACK_OFF`、`TEMPERATURE_RESET_OPT`、`KEY_SORT` の 3 ブールとする判断は実分岐に一致します。`RWLOCK` は bare define、delay は実処理がコメントアウトまたは表示だけです。
- campaign protocol を WAL `build_start.payload.genome` から取る方向は正しいです。post-policy admission は canonical genome、source evidence、variant ID を既に相互束縛しています（[artifact_admission.py:744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/artifact_admission.py:744)、[artifact_admission.py:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/artifact_admission.py:1189)）。
- protocol 不一致・複数・不明・floor 不在を wrong floor の採用ではなく `value=null` / `no-matching-env-record` に倒す向きは安全です。report 自体は通りますが欠落は明示され、現 checkout に certified-selection consumer はありません（[layer3_report.py:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:634)）。
- 既存 silo WAL は調査した tracked campaign すべてで `build_start.payload.genome` が `silo|...` でした。legacy within-run を限定的に救済する意図により、懸念された既存 silo の一律 `no-matching-env-record` 回帰は避けられます。ただし救済集合が広すぎる点は所見 1 のとおりです。
- screening を protocol 対応させ、同 workload・異 protocol の 2 file を一意選択へ変える必要性は正しいです。既存 between-run JSON 4 file はいずれも `genome` を持っています。
- `floor_result.search` は `{"type":"object"}` だけで `additionalProperties:false` がなく、criteria 追加に schema 変更は不要です（[layer3_schema.json:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_schema.json:255)）。
- create-only 出力、actual loader、actual `build_report()`、actual schema validator を通すテスト方針は妥当です。

pytest、build、測定、qsub は実走していません。read-only の静的検査だけです。

## 親 brief の誤り

- [brief.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2115-cross-protocol-impl/brief.md:25) の「凍結 bytes への影響なし」は結論が誤りです。`FROZEN_MANIFEST` と `_GENERATOR_SOURCES` の key 集合に編集 file がないという狭い事実は正しいものの、凍結 artifact 内の source SHA pin を探索していません。特に現在一致している `genome.py` の SHA binding は計画変更で新たに不一致になります。
- mocc TRACE、`space_for()` caller、`layer3_schema.json.search` に関する限定された実測主張には、再検索で誤りを確認できませんでした。

## 総括

最重要所見は、`legacy implicit silo` が protocol 不明の stock mocc calibration を silo として公式 report に入れうることです。  
凍結 pin は manifest の path key だけでなく artifact 内の source SHA にもあり、親 brief はこれを見落としています。  
固定 `{"silo"}` guard とその負例は hook の有無に束縛されず、移植後も緑のまま mocc を拒否する恒真検査です。  
実走は行わず、read-only 静的検査のみです。