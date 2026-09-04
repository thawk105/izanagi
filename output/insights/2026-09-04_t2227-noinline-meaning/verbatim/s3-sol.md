## 所見

1. **対象:** `orchestrator/campaign/condition_meaning_gate.py:553-571,3058-3071`、`s2-plan.md:236-238`  
   **何が問題か:** D1491 の「factory 以外から宣言を作れない」は成立していない。registry と同じ `macro/source_rel/start_directive` を指定すれば、呼び手が `ConditionalBranchMeaningDeclaration(...)` を直接構築できる。dataclass の等値比較なので、evaluation 時に factory が返す宣言との比較も通る。異なる `source_rel/directive` は `:564-569` で拒否されるが、生成元は識別されない。  
   **裁定にどう効くか:** plan のままでは D1491 と D1569 の factory-only 条件を満たさない。予定された registry 削除・変更試験でも、factory 外の直接構築は検出できない。  
   **性質:** real  
   **推奨する扱い:** 宣言にも evaluator 発行を示す非 canonical capability を持たせるなど、直接構築した同値宣言が `:3058-3066` で unestablished になる形を本題内で実装する。

2. **対象:** `orchestrator/campaign/condition_meaning_gate.py:86-89,1758-1766`、`s2-plan.md:70-76,175`  
   **何が問題か:** registry に `BACKOFF_NOINLINE` を加えると、要求 1・既定 0 は `shared_branch_build=True` になる。しかし同 macro は `cmake-cache-option` route なので、`:1762-1766` が `compile-command-unavailable` を発火する。現状は registry 外なのでこの分岐に入らない。  
   **裁定にどう効くか:** plan が約束する「要求 1 の診断 build も green」は meaning 単体では可能でも、supply arm を含む family admission では必ず red になる。A-2 の要求 0には直接影響しないが、fail-closed 発火条件を未記載のまま変える。  
   **性質:** real  
   **推奨する扱い:** shared-build 条件を既存 CMAKE_CXX_FLAGS witness に閉じるか、cache route を別 build root で扱い、要求 1 の supply・meaning・admission 全体を確認する。

3. **対象:** `verbatim-decisions.md:137-150`、`s2-plan.md:38-42,256-274`、`tools/pegasus/probes/t1683_rr5_cost_probe.py:150-165,219-223,243`、`orchestrator/campaign/backoff_sweep.py:363-371`  
   **何が問題か:** D1492 は「promotion 成果物」に限定しておらず、対象 macro を要求し、その admission が成果物へ載る driver を対象としている。t1683 probe は `BACKOFF_NOINLINE` を実際に要求し、meaning record と admission を `condition_gates` として payload に載せるため、raw-only を理由に除外できない。一方、brief が対象とした `backoff_sweep` の実呼び出しは `BACKOFF_FIXED` しか渡しておらず、`BACKOFF_NOINLINE` を要求していない。  
   **裁定にどう効くか:** plan の「promotion artifact だけ」という解釈は固定済み D1492 を狭める新裁定である。現状では t1683 に green/unestablished の driver 間分裂が残り、逆に backoff_sweep は不要な候補である。  
   **性質:** real  
   **推奨する扱い:** raw という class 名ではなく、実 request と serialized admission の有無で再分類し、少なくとも t1683 は配線対象に戻す。backoff_sweep は対象外とする。

4. **対象:** `orchestrator/campaign/condition_meaning_gate.py:2681-2713,2779-2783,2828-2850`、`s2-plan.md:92-98,177-186`  
   **何が問題か:** 現行の count だけなら、owner または別 header に marker 呼び出しを置き、別の同名 header、`-I` の原本、`#include_next`、旧 shadow directory symlink 経由で登録 header を避けても、値 0 で `(0,1)`、値 1 で `(1,1)` を作れる。しかし plan の P1 が各観測の dependency file を解決し、正確な `instrumented_root/include/backoff.hh` の存在を要求するなら、これらの「計装 header が読まれない」構成は red になる。symlink 経由の原本は resolve 後に原本 path となり一致しない。`-ffile-prefix-map` は marker を生成せず、dependency path まで変換する処理系なら偽 green ではなく false red になる。  
   **裁定にどう効くか:** 質問された absent-header 型について P1 は十分で、P2 の観測を恒真にはしない。ただし basename、suffix、source-root 側 path との一致ではなく、各 preprocess 後の shadow header exact path 比較であることが条件になる。  
   **性質:** refuted  
   **推奨する扱い:** plan の exact dependency membership と planned negative test をそのまま必須とし、path 比較を緩めない。

5. **対象:** `orchestrator/campaign/condition_meaning_gate.py:877-883,2996-3018`、`orchestrator/tests/test_condition_meaning_gate.py:1096-1109`、`s2-plan.md:100-120`  
   **何が問題か:** 既存 8 macro の受理が広がる疑いは、plan の macro 別分岐を守る限り成立しない。既存 factory は引き続き要求 1・既定 0だけを発行し、同一 count は先に `not-discriminating` で red、期待値不一致も red のままである。要求 0・対照 1は `BACKOFF_NOINLINE` だけに閉じる。  
   **裁定にどう効くか:** 既存 8 macro で「以前 red、変更後 green」になる入力はない。新 macro は成功時に unestablished から greenとなるが、どちらも admission は通るため受理集合は広がらない。失敗時の unestablished から red への変化だけが受理集合を狭める。  
   **性質:** refuted  
   **推奨する扱い:** equality 判定の優先順、既存 8 macro の factory 条件、validator の 1/0 固定分岐を逐語的に維持する。

6. **対象:** `orchestrator/campaign/condition_meaning_gate.py:405-436,680-705`、`orchestrator/tests/test_condition_meaning_gate.py:786-823,1135-1180`、`s2-plan.md:32-36,111-120`  
   **何が問題か:** plan 上、既存 evidence の byte 変更はない。`CompileTimeBranchSelectionEvidence` の field は順に `proof_kind`、`source_rel`、`start_directive`、`source_sha256`、`source_file`、`requested`、`default`、`compiler_path`、`compiler_version`、`compiler_identities`、`cmake_path`、`requested_configure_argv`、`default_configure_argv`、`requested_cmake_identities`、`default_cmake_identities` の15個で、追加・削除・既定値変更はない。`CompileTimeBranchSelectionObservation` の4 field も不変である。さらに canonical JSON は `sort_keys=True` なので dataclass field の宣言順だけでは key 順は変わらない。  
   **裁定にどう効くか:** 既存 8 macro の旧 shadow 分岐と 1/0 の slot 値を本当に維持すれば canonical evidence の値は不変である。ただし既存 test は count、argv 同値性、schema integrity を検査するだけで、完全な canonical JSON literal は pin していない。所要時間台帳は byte pin ではない。  
   **性質:** refuted  
   **推奨する扱い:** evidence dataclass と既存 8 macro の evidence 組み立てを変更せず、noinline の対照値だけを既存 slot に格納する plan を維持する。

7. **対象:** `s2-plan.md:78-84`、`orchestrator/campaign/condition_meaning_gate.py:1473-1501,2716-2748,3067-3084`  
   **何が問題か:** 深い鏡像は、従来は触らなかった無関係 subtree まで列挙するため、読めない directory で `compile-time-branch-instrumentation-failed` が増える。巨大 tree の列挙は subprocess 前なので120秒 timeout の対象外である。directory symlink を follow する実装なら循環・root 外走査で hang しうる。`RuntimeError` などが `ConditionMeaningGateError` へ変換されなければ、`:3067-3084` の structured red にもならない。dangling symlink や権限不足それ自体から偽 green は作れないが、hang または非 terminal exception は作れる。  
   **裁定にどう効くか:** `owner-tu-unresolved` と compile operand の一意性は shadow 作成前に評価されるため不変だが、instrumentation failure の入力集合と終了性は変わる。  
   **性質:** real  
   **推奨する扱い:** deep mirror は既存 directory symlink を追わず、全 traversal failure を `compile-time-branch-instrumentation-failed` に畳むことを実装条件にする。親は巨大 tree で traversal が timeout 外になる点を受容可能か確認する。

8. **対象:** `brief.md:42-49`、`s2-plan.md:276-278`、`external/ccbench/.gitmodules:1-3`、`external/ccbench/cc/silo/transaction.cc:5-9`、`external/ccbench/cc/silo/include/transaction.hh:7-16`、`external/ccbench/cc/silo/include/common.hh:10-15`、`external/ccbench/include/masstree_wrapper.hh:17-25`  
   **何が問題か:** brief の「404 file / 49 dir」は、この worktree の物理 tree には一般化できない。`.git` をすべて除外した静的 count は1438 file / 267 dirで、populated な `third_party/shirakami` submodule が含まれる。404は実質的に superproject 側だけの規模である。また fixture は `transaction.cc` から直接 header を読むが、実 TU は `transaction.cc` → `transaction.hh` → `backoff.hh` の二段 symlink includeで、さらに Masstree `config.h` と複数 `-I` を依存閉包に持つ。  
   **裁定にどう効くか:** toy の成功は実 TU の成功を含意せず、「深い鏡像のコストは小さい」という根拠も source root の submodule 状態に依存する。plan 自身は dogfood 必須と認めているため、未実測の一般化だけを acceptance 根拠にできない。  
   **性質:** real  
   **推奨する扱い:** 親 dogfood で実際の A-2 と s1 の `variant_root` を使い、二段 include、Masstree `config.h`、全 `-I`、追加された `-ffile-prefix-map`、dependency file の instrumented-header tokenを実測する。

## brief と plan が正しかった点

- `BACKOFF_NOINLINE` は現行 registry に無く、factory は要求 1・既定 0・source_rel が owner TU の場合だけ発行する。`condition_meaning_gate.py:180-210,873-888` と一致する。
- `silo-backoff-fixed.patch:52-58` の対象 directive は `include/backoff.hh` に一意で、実 owner の include 連鎖は `transaction.cc:7` → `transaction.hh:9` である。
- A-2 の要求値は `paper_story_a2_certification.v2.json:45-50` の 0、default も `paper_story_a2_certification.py:583` の 0であり、現行は `:630-654` で noinline declaration を作らない。
- production driver の現行 factory 呼び手は `s3_lock_coverage.py:101`、`s5_permutation_coverage.py:98`、`t152_write_intent_coverage.py:198` の3面である。
- 旧 `MeaningWitnessDeclaration` は `condition_meaning_gate.py:540-549`、legacy evaluation は `:3116-3124`、CLI meaning-case は `:3833-3842` で `BACKOFF_FIXED` に閉じている。`MEANING_SUPPORTED_MACROS` の拡張だけでは旧宣言型の green 経路は開かない。
- green validator も pointwise と selected-branch proof を `BACKOFF_FIXED` に固定し、compile-time proof は registry tuple に束縛している。`condition_meaning_gate.py:3521-3565,3609-3612` と一致する。
- fixture header に noinline directive が無いこと、追加3行が EVOLVE block 外なので既存 block 比較を変えないことは、fixture `backoff.hh:1-7`、patch `:55-57`、test `:1924-1935` から確認できる。
- repo 内 `output/` には `unestablished_meaning_macros` を持つ実 JSON がなく、A-2 実走2回が `driver_rc=2` だったことは `output/insights/2026-09-02_a2-condition-gate-patched-root/README.md:49-52` と整合する。repo 外保存先は未確認という plan の限定も正しい。
- toy と実 TU の差を隠さず、実 patch 木 dogfood を未完条件として残した `brief.md:48-49` と `s2-plan.md:276-278` は正しい。

## 総括

最も重い欠陥は、D1491 の factory-only が構造等値だけで実装され、直接構築した宣言を拒否できない点である。  
次に、registry 追加だけで要求 1の supply が `compile-command-unavailable` へ変わる未計画の分岐がある。  
P1 の exact dependency membership は、計装 header が読まれない count 偽装を塞ぐため、恒真性の疑いはその範囲では退けられる。  
親は実 A-2/s1 tree で二段 include、依存 path、`-I`、Masstree、prefix-map、物理 tree 規模を実測する必要がある。  
静的検査のみで、pytest や compiler の実走は行っていない。