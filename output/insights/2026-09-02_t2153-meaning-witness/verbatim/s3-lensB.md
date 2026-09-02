## 所見

1. **重大度: BLOCKER**

   **問題:** `MEANING_SUPPORTED_MACROS` を14件へ広げると、既存の `MeaningWitnessDeclaration` も新13件を受け付ける一方、評価処理はその型を無条件に BACKOFF 固有 witness へ送る。CLI も新 macro に `--meaning-case` を許すため、例えば `SORT_VARIANT` を `include/backoff.hh` の観測で green にできる。

   **根拠:** `condition_meaning_gate.py:387-388,2044-2092,2351-2416,2593-2605`。プランは一般集合を広げるが、legacy declaration と proof-kind の macro 束縛を分離していない (`out/s2-plan.md:75-76`)。

   **成果物影響:** 無関係な BACKOFF 証拠で `SORT_VARIANT` 等が green となり、certified 選択・材料レポート・台帳の `unestablished_meaning_macros` から誤って消え、admission は受理されたままになる。

   **是正案:** legacy の `MeaningWitnessDeclaration`、`MEANING_PROOF_KIND`、既存 branch proof を `BACKOFF_FIXED` に限定する別集合を置く。新 proof は registry macro だけに限定し、CLI は conditional macro では factory を使い、legacy `--meaning-case` を拒否する。proof-kind と macro の不一致を schema 検査と負例で拒否する。

2. **重大度: BLOCKER**

   **問題:** driver 閉包が不足し、13件すべての実成果物は縮まらない。特に `SORT_VARIANT` の certified driver 2面、`BACKOFF_NOINLINE` の paper / probe、generic screening が未配線である。またプランは要求値1だけを扱うため、現存成果物が要求する `BACKOFF_NOINLINE=0` は green にならない。

   **根拠:** `p3_s4_loop_sort.py:119-135`、`s6_sort_sweep.py:218-235`、`screening_driver.py:153-180`、`paper_story_a2_certification.py:530-603`、`paper_story_a2_certification.v2.json:45-49`、`t1683_rr5_cost_probe.py:146-223`。対して配線予定は `out/s2-plan.md:77-79` の7 driverだけで、`out/s2-plan.md:75,83` は対応外要求値を unestablished、全件要求値1としている。

   **成果物影響:** S1 の `condition_gate` では `SORT_VARIANT` が消えても、P3 sort の certified record、A2 の `condition_gate_receipts`、T1683 台帳などでは同名が残る。`BACKOFF_NOINLINE` は現在の主要成果物では一件も縮まらない。

   **是正案:** 下記閉包の全 relevant consumer を factory へ接続する。on/off witness は実 request が0または1のどちらでも同じ閉じた二点比較を行える契約にするか、`BACKOFF_NOINLINE` を今回の達成件数から外す。

3. **重大度: MUST-FIX**

   **問題:** テストは生成 fixture に寄り、registry が実 patch の所有 file・指令へ結合していることを検査しない。また `#if 1` や `#if MACRO || 1` への置換は exact directive 抽出で先に落ちるため、非識別観測の負例にならない。

   **根拠:** `out/s2-plan.md:70,111-135`、`condition_gate_test_support.py:38-60`。production の `SORT_VARIANT` 指令は `silo-sort-variant.patch:54` だが、現 fixture には同じ指令が複数ある。既存 BACKOFF テストだけは patch target と fixture を独立照合している (`test_condition_meaning_gate.py:1048-1059`)。

   **成果物影響:** fixture は green でも実 driver が red となって admission が拒否される、または差分観測ロジックが弱体化してもテストが検出せず、未確立一覧を誤って縮める可能性がある。

   **是正案:** 各対象 patch の target-side bytes から所有 path・開始指令一意性・対応 `#endif`・companion を独立照合する。非識別負例では spec 側も変異指令へ合わせ、理由コードが必ず `conditional-meaning-not-discriminating` になることを固定する。

4. **重大度: MUST-FIX**

   **問題:** S1 に3 test nodeを足す計画なのに、node key 側の pin が編集面から落ちている。これは path/hash 検索では見えない型である。

   **根拠:** `out/s2-plan.md:129-134`、`tools/update_acceptance_duration_ledger.py:21-30`、`test_update_acceptance_duration_ledger.py:360-404`。現 pin は S1 suite 97件と exact SHA-256 (`同:377-379`)。台帳本体は `acceptance_duration_ledger.json:19523`。

   **成果物影響:** acceptance duration 台帳の参照集合が新 nodeid を欠き、正しい更新後は S1 suite pin が少なくとも97件から100件へ変わる。certified 値そのものは変えないが、受入台帳が stale になる。

   **是正案:** 親の実測後、測定済み duration を add-only で台帳へ追加し、S1 suite の件数・node集合 hashを更新する。現在 `worktree-dev-wave-t1835-t1718-tool-identity` も同台帳を変更しているため、land順を調整する。

5. **重大度: MUST-FIX**

   **問題:** 新 spec が requested/default/companion を重複保持し、`witness_kind` を4分類するが、検査アルゴリズムは全件同じ branch-selection である。特に companion の正本はすでに `DEFINE_SPECS` にあり、二重化は危険である。

   **根拠:** `out/s2-plan.md:23-43,73-74`、`condition_meaning_gate.py:150-154,590-615,629-689`。

   **成果物影響:** REPORT witness の重複 companion が供給 request とずれると、実 build と異なる条件で green を発行し、材料レポートから `IZANAGI_SILO_LADDER_RUNG1_REPORT` を誤って除ける。

   **是正案:** registry は macro、所有 path、開始指令だけに絞る。値は `DefineRequest`、companion は `_validate_define_request` が返す正本を再利用する。proof kind は一つの conditional-selection に閉じる。

6. **重大度: MUST-FIX**

   **問題:** 13件は単一の第一群ではなく、平坦な no-else 8件、入れ子2件、selector、attribute、compound companion を同時に実装するため、依頼上の「一括で扱わない」に当たる。

   **根拠:** 親 brief の逐語 `handoff.md:22-24`、プラン自身の4 witness kind (`out/s2-plan.md:43`) と13件一覧 (`同:83-99`)。

   **成果物影響:** 一括変更ではどの witness 族が admission や一覧を変えたか分離できない。最初の8件へ切れば、S3/S5/T152 の材料台帳だけが縮み、残りは明示的に unestablished のまま残る。

   **是正案:** 第一段は平坦かつ単一 `#if MACRO` の8 positive controlに限定する。次に入れ子2件、`SORT_VARIANT`、REPORT、最後に実成果物経路を確保した `BACKOFF_NOINLINE` と分ける。

## 編集面の閉包

数え方は三系統で独立に行った。

- 識別子検索: repo 全体の `evaluate_define_runtime_meaning(` を数え、production 呼出しは22面。内訳は literal `declaration=None` が14面、nullable変数経由が5面、既存の明示宣言が3面。
- path/hash検索: 対象 source の現在 SHA-256 を計算して repo 全体で検索。現在 bytes の literal hit は `s1_direct_comparison.py` の materializer hashだけだった。
- key/schema検索: `MEANING_SUPPORTED_MACROS`、`unestablished_meaning_macros`、`__all__`、green evidence schema、acceptance node prefixを検索。`__all__` の repo 内 readerは0件。

13件を維持する場合の production 編集面は次で閉じる。

- `orchestrator/campaign/condition_meaning_gate.py`。factory、legacy/new proof分離、schema、CLIを含む。
- プラン記載の `s1_direct_comparison.py`、`s2_verify_calibration.py`、`s3_lock_coverage.py`、`s5_permutation_coverage.py`、`t152_write_intent_coverage.py`、`silo_ladder_rung1.py`。
- 追加必須: `p3_s4_loop_sort.py`、`s6_sort_sweep.py`、`screening_driver.py`、`paper_story_a2_certification.py`、`tools/pegasus/probes/t1683_rr5_cost_probe.py`。
- 条件付き追加: `backoff_sweep.py:132-149`。helper が `BACKOFF_NOINLINE` を受け付け続けるなら factory 化し、編集しないならその対応を helper domain から外す。
- 削除: `s8a_trigger_coverage.py`。扱うのは `BACKOFF_TRIGGER_GATING` と `IZANAGI_BREAK_TRIGGER_MISATTR` で、今回 green にする13件を含まない (`同:137-165`)。

test/support の完全な追随面は次である。

- プラン記載の `test_condition_meaning_gate.py`、`condition_gate_test_support.py`、`test_s1_direct_comparison.py`、`test_s5_permutation_coverage.py`、`test_t152_write_intent_coverage.py`。
- 追加必須: `test_silo_ladder_rung1_driver.py`、`test_p3_s4_loop_sort.py`、`test_s6_sort_sweep.py`、`test_screening_driver.py`、`test_paper_story_a2_certification.py`、`test_pegasus_calibration_workload.py`。`backoff_sweep.py` を変える場合は `test_backoff_sweep.py` も含む。
- pin/golden: `test_s8b_oracle_manifest.py` の materializer hashと `PIN_GATE_SPEC_SHA256`、さらに `acceptance_duration_ledger.json` と `test_update_acceptance_duration_ledger.py` の S1 suite key pin。

数えたが今回編集不要な literal `None` 面は、残す8 macroだけを扱う `s1_verify_extime_calibration.py`、`p3_s4_loop_trigger_gating.py`、`s8a_trigger_coverage.py`、`s8a_trigger_sweep.py`、`run_ss2pl_lock_study.py`。`t316_sandbox_backend_probe.py` は既存 `BACKOFF_FIXED` の未配線であり、本13件とは別残件である。

## 削れる実装

- `witness_kind` の `attribute-presence`、`selector-branch`、`positive-control-branch`、`compound-report-branch` 分類。判定規則が同じなので成果物上の意味を増やさない。
- `ConditionalBranchWitnessSpec.companion_defines`。`DEFINE_SPECS` の正本を再利用できる。
- `ConditionalBranchMeaningDeclaration.requested_value/default_value`。実 request と registry から導出できる。
- `selected-body SHA-256`。conditional/source hashと exact directiveを検査するなら重複である。
- repo 内 readerがない新規 `__all__` export。外部 API として必要という別要件がない限り不要。
- `s8a_trigger_coverage.py` の factory 置換。対象13件の成果物値を変えない。
- 推奨する8件の第一段では、S1、S2、ladder、sort、paper、T1683、S1 hash golden全体を後段へ送れる。

新しい conditional declaration相当の区別と、新 proof 用の exact evidence schema自体は削れない。既存 `MeaningCase` は `BACKOFF_FIXED=-1` に明示限定され (`condition_meaning_gate.py:278-285`)、既存 branch schemaも同 macro・値へ固定されている (`同:2392-2414`)。

## 親 brief の誤り

1. **P1-c は誤り。** 11件のうち `IZANAGI_BREAK_TRIGGER_MISATTR` は `#ifdef` なので1/0で枝が変わらない (`broken-silo-trigger-misattr.patch:9-21`)。プランの否定は正しい。

2. **P1-d は誤り。** S1だけでは positive control、sort loop、paper、ladder等の admissionへ到達しない (`handoff.md:113-114`)。さらにプランが追加した専用6面でもまだ不足する。

3. **条件指令内訳が誤り。** `NOREAD_VALIDATION` と `HIGHKEY_VALIDATION` はともに `#else` を持ち、前者にも materialized source上の入れ子 `#if ADD_ANALYSIS` がある (`broken-silo-norw-validation.patch:9-23`、`broken-silo-highkey-validation.patch:8-36`)。`BACKOFF_NOINLINE` には C++ 側 `#ifndef` がなく、CMake defaultと単一 `#if` である (`silo-backoff-fixed.patch:15,24,55`)。`SS2PL_WFG_DIAG` は追加条件指令で5件ではなく63件だった。

4. **「稼働 wave との編集面重複0」は現在の完全閉包では成立しない。** 現在39 worktreeを調べると、`worktree-dev-wave-t1835-t1718-tool-identity` の tip `0e8272d3a` が追加必須の `acceptance_duration_ledger.json` を変更している。親の過去時点30 worktreeという観測自体は遡及検証できないが、実装前提としては再確認が必要である。

`condition_meaning_gate.py` の現在 bytes pinが無い点、S1 materializerの2 golden、stock submoduleで対象 macroが0件、適用済み sourceを gateへ渡す点は確認でき、誤りは見つからなかった。

## 総括

BLOCKER は2件。現プランのまま実装してはいけない。  
legacy witnessの false greenを閉じ、全 consumerと key pinを閉包する必要がある。  
段階性を守るなら、まず平坦な positive control 8件だけで成果物一覧を縮めるのが妥当である。  
pytestやcompiler witnessは実走しておらず、結論は静的検査による。