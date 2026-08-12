## 所見

1. **real / blocker** — AST 検査はリポジトリの Python source bytes・file 数に比例する。  
   根拠: `s2b-plan.md:61-62`、実測静的集計は `orchestrator/tests` 219 files / 8,904,169 bytes、`orchestrator/campaign` 133 / 3,849,817、`tools` 73 / 2,923,141、計425 files / 15,677,127 bytes。これは D311 (`docs/decisions.md:14275-14278`) と D335 (`:14957-14964`) の新設禁止対象である。既存の同型先例は `test_s8b_floor_campaign.py:737-741,2050-2051`、`test_login_headroom.py:1250-1251` にあるが、既存負債の先例であって新設許可ではない。  
   最小の現行3系統閉包は9 files / 約0.858 MBだが、そこへ限定すると将来の新規接触を自動検出できない。

   影響: 成功時の certified 値は不変でも、source 成長による受入時間超過で proof chain が未完了となり、certified 選択結果と受理集合が縮む。

2. **real / must-fix** — 「純増1〜3秒」は未実測で、AST parse 単体と固定点解析を分離していない。  
   根拠: `s2b-plan.md:54-62`。15.677 MBを仮に10〜50 MB/sで読む感度分析では、`ast.parse` 単体は約0.31〜1.57秒。ただし `ast.walk`、import alias、callable伝播、固定点反復、JSON化の実効値は未確認である。桁違いとは断定できないが、1〜3秒を受入値として認証できる根拠はない。

   影響: wall budget を誤って設定し、受入全走が時間切れになれば certified 選択結果が発行されず、proof chain と受理集合が未確定になる。

3. **real / must-fix** — collection report の拡張処理は「1回」ではない。  
   根拠: `_collect_xdist_group_report()` と `_run_subprocess()` は `test_real_repo_serialization.py:347-350,360-431`。呼出しは `:570`、`:641`、`:699`、`:780`、および `:794-800` のループ2回で、実際には6回の collection subprocess が起動する。新しい subprocess は増えないが、fixture closure を全 item に付ける処理は6回反復する。

   影響: proof chain の内容は同じでも collection overhead が6倍相当で加わり、受入時間超過時には certified 結果と受理集合が失われる。

4. **real / must-fix** — 150〜200行のAST解析器を同じtest fileへ置くが、解析器自身の独立 oracle がない。  
   根拠: `s2b-plan.md:8-15,30-44`、対象ファイルは既に1,431行 (`test_real_repo_serialization.py:1408-1431`)。positive controlは導出済み集合から1 nodeを削るだけで、alias、dynamic `getattr`、callable引渡し、未分類候補の検出精度を検査しない。計画自身も `s2b-plan.md:20,74-75` で限界を認めている。  
   3系統だけを対象にした小さい個別検査なら、現行検出力あたりの行数は優れるが、将来のrename・helper追加への自動追随性は落ちる。どちらを採るかを明示すべきである。

   影響: false negativeなら未直列nodeが残り、`ccbench_pin`・source digest・known-axesのproof chainとcertified選択値が変わり得る。false positiveなら受理集合が不必要に縮む。

5. **real / must-fix** — t983のfixture変更で、系統3の計画引用が既に古い。  
   根拠: `s2b-plan.md:26` は `TOOL.build_snapshot(_ROOT, ...)` を前提にするが、並行worktreeの現在差分では fixture が `TOOL._build_snapshot_base` / `TOOL._derive_snapshot_from_base` (`test_codex_reasoning_ab.py:367-376`) に変更され、実cloneは `tools/codex_reasoning_ab.py:1433-1456` に移っている。  
   `benchmark_snapshots`を正本へ加えるだけなら `conftest.py` 側のnode名追加で足り、t983 laneの編集は不要。ただしAST解析器は新helper経路を追跡する必要があり、t983側を変更して直接呼出し形へ戻す案はlane衝突で blocker となる。

   影響: 解析器が旧呼出しだけを見ると17 nodeの導出が失敗し、検査が赤になって受入・certified選択が停止する。

6. **refuted / nit** — 21 node追加で直列順序の不変条件は壊れない。  
   根拠: 実際のpriorityは `conftest.py:233-236`、並べ替えは `:403-415`、検査は `test_real_repo_serialization.py:777-800`。新nodeはpriority tupleにないため、既存2 priority nodeの後ろに安定順で置かれる。writersのbarrier後条件も変わらない。  
   なお brief の `conftest.py:223-226` はpriorityではなくserial node列の一部であり、行番号がずれている。

   影響: certified選択結果、proof chain、受理集合の値は変わらない。変わるのは直列化範囲だけである。

7. **refuted / nit** — t930の `pytest_configure` / `pytest_unconfigure` との行レベル衝突はない。  
   根拠: hookは `conftest.py:520-524,904-912`、編集対象のserial listは `:170-236`。collection pluginの追加は別subprocess内で動くため、既存hookの契約を壊さない。

   影響: certified選択結果、proof chain、受理集合に変化はない。

8. **real / must-fix** — `silo_ladder_rung1.py:963,2084` の除外は「pytest受入全走」には妥当だが、production経路まで含めると未是正である。  
   根拠: pytest側は absent stagingで停止するだけ (`test_silo_ladder_rung1_driver.py:1059-1063`)。一方production correctness/gap commandは `silo_ladder_rung1.py:3773-3774,4090` から `third_party_source_contract()` を呼び、対象statusへ到達する。`_run()` は `:331` の scrub済みenvを使う。

   影響: production時のstatus snapshotがwriter競合で不整合になり、tracked-clean/status evidenceとsource digestの値、ひいてはvariantの受理集合とcertified選択が変わり得る。

9. **real / blocker** — `os.environ.copy()` のままでは既存のGit環境衛生と矛盾する。  
   根拠: s2aの提案は `s2a-plan.md:105-128`。しかし安全な既存実装 `orchestrator/campaign/t810_validator.py:334-355` は `GIT_DIR`、`GIT_INDEX_FILE`、`GIT_WORK_TREE` 等を削除してから `GIT_OPTIONAL_LOCKS=0` を設定する。対応する攻撃入力も `test_t810_validator.py:399-401` にある。`repo_tree_util.py:20-27` と `source_digest.py:761-770` は、それぞれcwd/`git -C`で実行するため、親envのGit変数を許すと別repo/indexへ誘導できる。

   影響: `tracked_clean`、tracked paths、diff hashがdecoy repoの値になり、proof chainが汚染されてunsafe variantが受理され得る。

10. **refuted / nit** — 「新設検査全体が既存検査と二重」という攻撃は refuted。ただし純増部分は限定的である。  
    `test_real_repo_group_collection_exactly_matches_canonical_nodes` (`:567`) へ導出検査を統合するのが妥当で、純増は「正本・golden双方にない実接触node」の検出だけである。protocol builder (`:823`) の実効配線やmemo payer (`:900`) の再発見は純増ゼロまたは僅少である。

    影響: 導出検査を追加しなくても既存のcertified値は変わらないが、両リスト外の未直列nodeに対するproof chainだけが欠落する。

11. **real / must-fix** — T-991回帰テスト案は部分的に既存テストと同型である。  
    根拠: `test_campaign.py:10199-10211` は `patchharness._git()` のenv captureで、source_digestとはSUTが異なるため完全重複ではない。ただし `captured["env"]["GIT_OPTIONAL_LOCKS"] == "0"` という証明形は同じである。既存testを共通capture helperまたはparameterized形式へ拡張し、source_digest固有の呼出しも追加する方がよい。protocol builder側の `test_s8b_protocol_builder.py:431-444` にはこのenv検査はなく、そこは純粋な新規被覆である。

    影響: 値は直ちには変わらないが、重複した片方だけが緑になり、T-991のproof chainが実SUTを覆わないままunsafe variantが受理され得る。

12. **real / must-fix** — 段5 author 1本は競合回避には合理的だが、現案のままではcontext過密である。  
    根拠: s2aの実装順序は `s2a-plan.md:132-154` の6 files、そこへAST 200〜260行、t983の可変fixture、T-991のenv衛生を同時に載せる。`tools/check_docs.py` の予算はdocs/skill等 (`:174-206,4191-4238`) が対象で、Python test fileの行数超過を自動検出しない。

    影響: cross-fileの取り残しでfalse greenなら受理集合が広がり、false redならcertified選択結果が発行不能になる。

## コスト再見積り

| 対象 | 静的サイズ | parse単体の感度分析* | 固定点・report込み |
|---|---:|---:|---:|
| 現行3系統の最小閉包 | 9 files / 0.858 MB | 約0.02〜0.09秒 | 概ね0.05〜0.5秒 |
| 案Bが掲げる全対象 | 425 files / 15.677 MB | 約0.31〜1.57秒 | 約0.8〜5秒、未実測 |
| collection report拡張 | 全 collected item | なし | 6回のcollectionごとに反復、未測定 |

\* 10〜50 MB/sを仮定した感度分析であり、実効benchmarkではない。したがって段2Bの「純増1〜3秒」は桁違いとは言えないが、固定点解析と6回のreport処理を含む値としては未証明である。最小閉包へ縮めれば1〜3秒は過大、全対象を維持すれば上限側で超える可能性がある。

## 既存被覆との対応表

| 既存関数 | 新設検査との関係 | 純増 |
|---|---|---|
| `test_real_repo_group_collection_exactly_matches_canonical_nodes` `:567` | 導出集合検査をここへ統合 | 両リスト外nodeのみ |
| `test_xdist_group_audit_rejects_synthetic_negative_controls` `:618` | marker shape負例。fixture情報とは無関係 | なし |
| `test_xdist_group_name_set_audit_rejects_isolated_negative_controls` `:669` | group名集合の負例 | なし |
| `test_canonical_real_repo_nodes_have_no_handwritten_xdist_group_decorator` `:744` | marker付与元の監査 | なし |
| `test_handwritten_xdist_group_decorator_control_is_rejected` `:755` | decorator負例 | なし |
| `test_real_repo_priority_order_is_literal_and_writers_follow_barrier` `:777` | 追加nodeも同じ順序監査を受ける | 閉包検出はなし |
| `test_protocol_builder_repo_tree_guard_is_wired_to_real_root` `:823` | ROOT guardの実効配線。新AST再発見部分は重複 | ほぼなし |
| `test_ratified_memo_has_a_real_resolution_payer` `:900` | memo payer契約。resource閉包ではない | なし |
| `test_loadgroup_scheduler_keeps_same_group_on_one_worker_and_control_detects_absence` `:955` | scheduler実走 | なし |
| `test_effective_tempdir_is_not_tmpfs` `:1034` | 実mount検査 | なし |
| `test_suite_conftest_does_not_wire_tmpdir_to_tmpfs` `:1088` | conftest source検査 | なし |
| `test_tmpdir_fstype_lookup_positive_and_negative_control` `:1103` | fstype parserの負例 | なし |
| `test_tmpfs_tmpdir_wiring_scanner_positive_and_negative_control` `:1181` | 既存AST scanner自身の正負control | なし |
| `test_tmpdir_guards_are_present_and_load_bearing` `:1298` | guardのload-bearing検査 | なし |

既存関数を拡張すれば済む中心は `:567`。T-991のcampaign側は `:10199-10211` のcapture形を共通化するのが適切である。

## 並行 wave との衝突判定

- `dev-wave-t983-snapshot-fixture`: **要調整**。serial nodeの追加自体は `conftest.py` のnode名だけで足り、対象laneの編集は不要。ただし `s2b-plan.md:26` の直接 `TOOL.build_snapshot` 前提は現行差分で崩れている。AST側で `_build_snapshot_base` → `_derive_snapshot_from_base` を追跡すること。t983ファイルを変更して呼出し形を戻すなら blocker。
- `dev-wave-t930-hold-no-bypass`: **衝突なし**。`pytest_configure` / `pytest_unconfigure` は `conftest.py:520-524,904-912`、今回のserial listは `:170-236`。hookの順序契約を変更する必要はない。

## file:line 照合結果

18件以上をサンプリングした。

- 正確: `conftest.py:196-205`、`repo_tree_util.py:20-27`、`test_s8b_protocol_builder.py:431-444`、`test_ruleops.py:3276`、`source_digest.py:761-770`、`test_campaign.py:9217-9261`、`silo_ladder_rung1.py:963`、`:2084`、`:117-124`、`:306-320`、`repo_tree_util.py:78-91`、`source_digest.py:833`、`:852-861`、`test_t810_validator.py:401`、`t810_validator.py:334-354`、`test_real_repo_serialization.py:347-353,360-433,567`。
- ずれ・不正確:
  1. `s2a-plan.md:7` の `patchharness.py:193-199` は行自体は存在するが、そこは `apply_patch()`。`applied()` 本体は `:234-251` であり、計画の関数名と根拠がずれている。
  2. `s2a-plan.md:15` の `s1_direct_comparison.py:527` は `cache_root` 設定。`checkout()` 呼出しは `:528-529`。
  3. briefの `conftest.py:223-226` はpriorityではなくserial node列。priority本体は `:233-236`。
  4. `s2b-plan.md:26` の `TOOL.build_snapshot(_ROOT, ...)` は、t983差分後のfixture呼出し形として stale。

## 裁定パッケージ候補 (scope 外)

1. D335の例外を出して全425 file scanを許すか、恒久保留または変更量限定の検査へ設計変更するか。
2. T-991の対象をpytest受入経路だけに限定するか、productionの`silo_ladder_rung1` status経路も含めるか。
3. Git read-only subprocess共通のenv sanitizerを新設し、`GIT_DIR`等の除去と`GIT_OPTIONAL_LOCKS=0`を一契約にするか。
4. t983のsnapshot builder helper境界をAST検査の正式witnessとして固定するか。
5. AST解析器をtest fileへ置く案を維持するか、3系統の小検査へ縮小するか。

## 未確認のまま残した点

- pytest、受入全走、mutationは実行していない。従って緑は確認していない。
- `ast.parse`の実効速度、fixed-point反復回数、collection item数、6回のreport追加コストは未実測。
- pytest private APIのfixturedef shapeとoverride時の実際の`name2fixturedefs`は未確認。
- t983の未コミット差分は今後変わり得るため、最終land後のcall graphは未確定。
- `silo_ladder_rung1` production commandがこの受入定義に含まれるかは、静的コードだけでは運用境界を確定できない。

## 総括

案Bは、正本・golden双方にないnodeを検出する純増価値はあるが、現状のままでは **NO-GO**。D335の成長比例scan、`os.environ.copy()`によるGit環境汚染、t983後の呼出し形不一致を解消し、AST範囲とT-991のproduction適用範囲を裁定してから実装すべきである。