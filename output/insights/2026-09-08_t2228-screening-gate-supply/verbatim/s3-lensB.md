## 射程の上振れ

- **[refuted / nit] 現行 s6/s8a の挙動は 1 bit も変わらない。** 両 caller は `expected_toolchain_manifest` を渡さず、計画は `None` の場合に現行 `configure_args` をそのまま使う。`s6_sort_sweep.py:421-427`、`s8a_trigger_sweep.py:523-529`、`s2-plan.md:77-86`。

- **[real / should-fix] 将来の射程防壁という説明は成立しない。** s6/s8a が後日 manifest を渡せば、共有 helper の同じ分岐が自動発火する。一方、計画の `None` helper test は caller を通らないため、その変更後も緑になり得る。「test を更新しない限り水平展開できない」は誤りである。`s2-plan.md:86`、`screening_driver.py:473-488`。現実装では裁定違反ではないが、manifest を authority ではなく現在の経路名の代理として使っていることを明記すべきである。

- **[refuted / nit] D1733 が明示的に禁じた 2 経路には届かない。** `backoff_repro` と `s1_direct_comparison` は `screening_driver.evaluate_candidate` の caller 集合に入らず、変更対象 file も計画から除外されている。`verbatim-d1733.md:3-6`、`s2-plan.md:12`。

## (P1) の恒真性

- **[real / should-fix] D1733 の対象である canonical backoff screening 集合では恒真である。** `run_workload` は manifest を無条件生成し、baseline と残り全候補へ同じ object を渡す。全 8 genome は `BACKOFF_FIXED` request を持つ。したがって対象経路では `expected_toolchain_manifest is not None` は readiness 条件ではなく経路タグである。`backoff_sweep.py:193-202,344-347,258-264,297-303`。

- **[real / should-fix] s6/s8a は「live な反例」として弱い。** 両 canonical entry は共有 screening 関門より前に独自 preflight 関門を走らせ、その関門も FetchContent base を渡していない。masstree の `config.h` は configure ではなく `masstree_build` target が生成するため、clean な経路では先に同型の赤へ到達する。`s6_sort_sweep.py:218-230,308-310`、`s8a_trigger_sweep.py:314-326,407-409`、`external/ccbench/cmake/ThirdParty.cmake:66-78`。従って計画は「呼び出しグラフ全体では非恒真」と「実際に共有関門へ到達する集合では恒真」を混同している。

- **[refuted / nit] 現時点の拡張的挙動はない。** 上記は将来または到達性の問題であり、現在 s6/s8a の成果物、受理集合、レポート値は変わらない。新しい scope gate を足す根拠にはしない。

## 射程の下振れ (まだ赤が残る経路)

- **[refuted / nit] 指定された 3 箇所に、backoff screening を必ず赤にする別の静的障害は見つからない。** `BACKOFF_FIXED` は CMake cache route、実 build argv に同じ値が存在し、base configure args から対象 domain 引数だけが除かれる。`screening_driver.py:123-165`、`condition_meaning_gate.py:74-78`。

- **[refuted / nit] stock checkout の入れ子は妥当である。** stock worktree は外側で生存し、計画どおりその内側で prepare、requested/control configure、preprocess、admission を完結できる。`screening_driver.py:213-231`、`patchharness.py:346-379`、`s2-plan.md:92-108`。

- **[refuted / nit] meaning 腕は追加 configure 障害を作らない。** `declaration=None` は即 `unestablished` となり、admission は supply green かつ meaning non-red を受理する。`condition_meaning_gate.py:3295-3301,4058-4063`。

- **[refuted / nit] P4 の例外境界も現行 gate red と整合する。** gate は `evaluate_candidate` の candidate-abort `try` より前にあり、prepare 失敗も同じく WAL abort へ丸めず全体を停止する。`screening_driver.py:555-562,587-605`。

- **[real / must-fix] ただし、実 CCBench の screening 関門を供給後に通す生死確認が完了条件にない。** 一次資料の実測は供給前の screening 赤と、別の driver 関門の緑であり、通常 8 genome の screening admission は未測定である。fixture による合成検査だけで完了すると、baseline commit が依然 0 件でも見逃し得る。実装後、少なくとも `screening_fixed_us=2` の real production path を計算ノードで通す必要がある。`verbatim-insight-t2228.md:51-59,78-80,228-233`、`s2-plan.md:216-224`。

## 費用

- **[refuted / nit] 計画は費用を無視していない。** `SWEEP_US` は 6 点で、none/adaptive と合わせて 8 genome、既定 workload は 3 件である。新規 prepare は fresh 全走で 24 回となる。`backoff_sweep.py:60-69,193-202,451-455`、`s2-plan.md:110-116`。

- **[real / nit] 実測 20.2 秒を使う見積りは次のとおり。**

  - 8 genome: 約 161.6 秒/workload
  - 3 workload: 約 484.8 秒、約 8 分 5 秒
  - 最小 2 点: 約 40.4 秒/workload、3 workload なら約 121.2 秒

  根拠となる 20.2 秒は 1 回の観測値であり、安定した上限ではない。`output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md:130-135`。

- **[real / nit] replay 時も baseline 1 回分は必ず残る。** baseline は `force=True` で呼ばれ、`prepare_screening_campaign` は毎回 baseline callback を要求する。terminal skip が効くのは残りの候補である。`backoff_sweep.py:257-270`、`screening_driver.py:438-445,541-543`。

- **[refuted / nit] base の使い回しによる木の同一性破壊は本計画にはない。** genome ごとに新規 base を作り、関門直後に破棄する設計である。費用は高いが、別候補や可変 source 木との共有は起きない。`s2-plan.md:90-108,142-146`。

## 変異の帰属

| 変異 | 判定 | 根拠 |
|---|---|---|
| M1 | **[real / must-fix] kill 集合が不完全。** root 一致 test だけでなく、prepare-failure test も manifest 転送削除で prepare へ到達せず赤になる。 | `s2-plan.md:162-163,199` |
| M2 | **[refuted / nit] stock 腕へ独立に照準できている。** | `s2-plan.md:161,200`、`screening_driver.py:226-231` |
| M3 | **[real / must-fix] 冗長。** `without_manifest` に加え、bomb prepare を入れる既存正例も同じ反転で赤になる。実 helperなら `None` manifest は buildcache 自身にも拒否される。 | `s2-plan.md:159,164,201`、`buildcache.py:1243-1251` |
| M4 | **[real / must-fix] 冗長。** 新しい no-request test だけでなく、manifest 付き非-domain genome を使う既存 v2 forwarding test も prepare を誤発火して赤になる。 | `s2-plan.md:160,202`、`test_screening_driver.py:652-703` |
| M5 | **[real / should-fix] 複合候補。** delete と duplicate は分けるべきで、root 一致 test も prepare 欠落を検出し得る。 | `s2-plan.md:156,162,203` |
| M6 | **[real / should-fix] 複合かつ重複。** stock-root 差替えと noncanonical 差替えを分けるべきである。後者は buildcache の absolute-directory 検査が先に拒否し、exact-kwargs test も同時に赤になる。 | `s2-plan.md:156,162,204`、`buildcache.py:2020-2022` |
| M7 | **[refuted / nit] timeout の片側差替えへ直接照準できている。** | `s2-plan.md:156,205` |
| M8 | **[real / should-fix] 「site 省略」は無効な変異。** 引数既定値自体が `None` なので、明示 `site=None` の省略は意味を変えない。syntax exact test が semantic no-op を殺すだけになる。固定 `"OTHER"` とは分離すべきである。 | `s2-plan.md:206`、`buildcache.py:2009-2017,1820-1822` |
| M9 | **[refuted / nit] base 未追加/別base は実 supply argv の検査で区別できる。** | `s2-plan.md:157,207`、`condition_meaning_gate.py:1657-1670` |
| M10 | **[refuted / nit] stock checkout 内で base の存在期間を観測するなら直接帰属できる。** | `s2-plan.md:161,208` |
| M11 | **[refuted / nit] prepare 例外、evaluate 非呼出し、WAL 非追記の組で fallback を直接殺せる。** | `s2-plan.md:163,209`、`screening_driver.py:562-605` |
| M12 | **[refuted / nit] fixture は route 検査を通過して supply の bytes-identical で赤になるため、admission 無視へ帰属できる。** | `s2-plan.md:148-150,158,210`、`screening_driver.py:194-207` |

- **[real / must-fix] 変異台帳は M1、M3、M4 の全 failing node 集合を事前登録し直す必要がある。** そうしないと KILLED でも expected-node MISMATCH になり、一次資料自身が記録した過去の帰属失敗を繰り返す。`verbatim-insight-t2228.md:202-209`。

## pin 閉包の反証

- **[real / nit] nodeid key の台帳は存在する。** `acceptance_duration_ledger.json` は既存 screening test 名を直接 key にしており、新規 6 test は未登録になる。従って「nodeid pin は無い」は反証される。`acceptance_duration_ledger.json:1798-1806`、`s2-plan.md:156-165`。

- **[refuted / nit] ただし duration 台帳の再登録は受理条件ではない。** 未知 nodeid は既知 cost の policy default で並べられ、test を除外しない。成果物への影響は実行順の推定だけで、値、受理集合、参照は変わらない。`conftest.py:1534-1554,1578-1626`。

- **[refuted / nit] path/function pin の更新は不要である。** perf 閉包は `evaluate_candidate` 内の perf/evaluate call 数だけを固定し、certified-writer 閉包も `screening_driver.py -> pipeline.evaluate` の 1 callだけを固定する。計画はどちらも増減しない。`test_official_perf_closure.py:132-137,625-629`、`test_campaign.py:5346-5368`。

- **[refuted / nit] line-number pin に screening sink は無い。** define-sink 検査は line を動的採取し、line を literal 固定する deferred ledgerに `screening_driver` entryはない。`test_ccbench_spawn_sites.py:751-786,2642-2649`。

- **[refuted / nit] process/spawn pin は増えない。** 新しい call は Python helperであり、実 subprocess site は既登録の `buildcache._run` に残る。`test_ccbench_spawn_sites.py:79-110,351-375`。

- **[refuted / nit] file 全体 sha256 pin は見つからない。** 現行 `screening_driver.py` の sha256 `98127904c37bc91f5ea68fdfeed1351577889cf4f075fb8dd6301d9bec085890` を repo 全体で照合したが参照は 0 件だった。関連 closure は path/function/call 数方式である。`test_official_perf_closure.py:95-105`、`test_campaign.py:5346-5368`。

- **[real / should-fix] real CCBench を使う pytest を追加して上記 must-fix を閉じる場合だけ、別の nodeid 閉包が発火する。** `patchharness.checkout` は未登録 test nodeによる共有 submodule writeを拒否するため、その nodeid を `REAL_REPO_ACCESS_BY_NODE` 系へ登録する必要がある。`patchharness.py:315-329`、`conftest.py:514-568`。

## test の実効性

- **[real / nit] 実装前から緑になる test。**

  - `test_screening_condition_gate_accepts_real_runtime_genome_value`
  - 新規 `test_screening_condition_gate_without_manifest_preserves_unsupplied_path`
  - D1666 の backoff regression 2 件
  - perf/spawn/certified-writer closure 5 件

  これらは legacy 非発火または既存閉包の検査であり、screening 供給の正例ではない。`test_screening_driver.py:169-186`、`s2-plan.md:159,164,167-175`。

- **[real / should-fix] 実装を削除しても単独では緑のままの test。** `without_manifest`、`no_requests`、既存正例、ignored-runtime 負例、closure 群は、供給ブロック全削除を直接は検出しない。これは直交テストとしては正常だが、個別 test を実装証拠として数えてはならない。`s2-plan.md:156-165`。

- **[real / should-fix] `without_manifest` test は将来の s6/s8a manifest 転送を検出しない。** helper を直接 `None` で呼ぶ限り、caller が manifest を渡すよう変わっても緑である。P1 の scope 防壁という主張から外す必要がある。`s2-plan.md:86,159`。

- **[refuted / nit] 「本物の関門を通る正例がゼロ」ではない。** `test_screening_condition_gate_supplies_prepared_base_to_real_supply_arm` は actual `capture_define_inputs` と supply evaluator を通し、requested/control argv を検査する計画である。`s2-plan.md:133-135,157`。

- **[real / must-fix] ただし actual prepare と actual CCBench gate を同じ test/runで合成する正例はない。** prepare は stub、gate は小型 fixtureなので、`config.h` 欠落が本当に消えたことは production liveness に委ねられる。完了時には前節の計算ノード生死確認を証拠化すべきである。`s2-plan.md:148-150,216-224`。

## 親 brief への反証

- **[refuted / nit] 現行 configure 引数、driver base の早期 close、caller 4 箇所、manifest caller 2 箇所、prepare の必須 keyword、canonical source rootは repo と一致する。** `screening_driver.py:168-181,473-533`、`backoff_sweep.py:258-264,297-303,363-400`、`source_digest.py:2328-2368`、`buildcache.py:2009-2017`。

- **[real / nit] 「実測で確かめた前提」という括りは過大である。** caller 数や manifest 転送は静的確認で、20 秒は本 wave の反復測定ではなく D1666 の単一 20.2 秒観測の一般化である。`brief.md:32-47`、`output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md:130-135`。

- **[real / nit] 「関門は genome ごとに走る」は fresh 候補に限る。** terminal non-retryable candidate は gate より前に returnする。一方 baseline は forceされる。`brief.md:47`、`screening_driver.py:538-555`、`backoff_sweep.py:257-270`。

- **[real / should-fix] P3 の「driver 段と同じ解決」は byte-exact には誤りである。** driver 段は開始時に解決した `site` を明示転送するが、計画は `site=None` により関門ごとに `current_site()` を再観測する。通常の bnode では同値だが、同じ観測値を転送しているわけではない。`backoff_sweep.py:327,370-377`、`s2-plan.md:50,118`、`buildcache.py:1820-1822`。

- **[refuted / nit] P4 は成立する。** prepare 失敗は偽の gate redにも candidate WAL abortにも変換されず、現在の gate failureと同じ位置で全評価を停止する。`brief.md:63-64`、`screening_driver.py:555-562`。

- **[real / nit] 親の「編集面が 1 関数 + test」は誤りである。** 段 2 は `_run_condition_gate_for_genome`、`_require_condition_gate_before_evaluation`、`evaluate_candidate` の 3 関数を変更する。`brief.md:91`、`s2-plan.md:5-10`。

## 裁定パッケージ候補 (scope 外の real 所見)

- **[real / nit] `backoff_repro` は現行 pin 不一致で正規入口から関門へ到達しない。** D1733 に従い、本 wave では供給も pin 整合も行わない。再訪条件だけを維持する。`verbatim-insight-t2228.md:108-120`、`verbatim-d1733.md:23-30`。

- **[real / nit] `s1_direct_comparison` は freeze 検証で停止し、inert cellもない。** freeze 再生成や供給は scope 外である。`verbatim-insight-t2228.md:122-153`、`verbatim-d1733.md:16-19,25-30`。

- **[real / nit] s6/s8a の独自 preflight も同型の base 未供給である。** これは今回の backoff screening 修正へ混ぜず、それぞれ正規入口での実測と裁定を要する。`s6_sort_sweep.py:218-254,308-310`、`s8a_trigger_sweep.py:314-350,407-409`。

- **[real / nit] gate が見た `config.h` と後続 build の `config.h` の bytes は束縛されない。** D1666 が明示的に受容した限界であり、本 wave の must-fix にしない。`verbatim-d1666.md:8-10,19-21`。

## 総括

- **[real / must-fix] 計画はそのままでは NO-GO。** production 実装の配線自体には静的な致命傷を見つけなかったが、完了前に次の 2 点が必要である。

  1. 実装後の real backoff screening positive controlを計算ノードで通し、少なくとも baselineと固定 2 us が関門を越えることを証拠化する。
  2. 変異 M1/M3/M4 の全 failing nodeを登録し、M6/M8の複合または semantic no-op候補を分割・再照準する。

- **[real / should-fix] P1 は「manifest が供給権限」ではなく「現行 call graph上の経路代理」と書き直すべきである。** 現時点の s6/s8a は不変なので新しい policy gateは不要だが、`None` testが将来の水平展開を防ぐという主張は削除する。

テストは実行していない。以上は read-only の静的検査結果である。