## 所見

静的検査のみ実施しました。編集・pytest・実 TU 実走はしていません。HEAD は指定の `947fd160a` です。

以下、`G`＝[condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/campaign/condition_meaning_gate.py)、`T`＝[test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/tests/test_condition_meaning_gate.py)、`C`＝[s8a_trigger_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/campaign/s8a_trigger_coverage.py)、`S`＝[test_s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/tests/test_s8a_trigger_sweep.py) と略記します。他の相対 path も対象 worktree 基準です。

**1. real／must-fix：plan の driver 棚卸しは S1 extime を落としている。**

`orchestrator/campaign/s1_verify_extime_calibration.py:94` は TRIGGER_GATING を要求し、`:103` は `certified-selection`、`:468`→`:479` は admission を含む condition gate を JSON に保存します。D1492 の対象条件を満たします。「coverage だけ」の根拠に、この driver の省略は使えません。

ただし `:91` の capture は genome の configure 値も offline 供給引数も渡しません。`:225` の要求 genome は `_genome(1)`。factory の一行追加だけで実 build と同じ全12箇所観測になるとは未確認です。親は「配線＋供給整合をこの wave に含める」か「driver 名・残る未確立一覧を明記して別変更単位へ残す」を裁定すべきです。

**放置時の成果物：** coverage が green でも `s1_verify_extime.json` の TRIGGER_GATING は未確立のまま残ります。

**2. real／must-fix：未定義不在検査の適用範囲が、本題より広い。**

plan は G:2271 に `expected_value is None and not stock_identity` の検査を足します。しかし G:971 は全 domain の `default=None` を許し、G:1700 はその場合に追加 define を省くだけです。これは「登録された `#ifdef` の未定義対照」と同義ではありません。

例えば既存 SORT は `patches/silo-sort-variant.patch:18,26` に CMake 既定値0と compile define の供給があります。SORT の `1/None` にも新検査が発火し、従来その箇所では拒否しなかった CMake 既定 define を拒否します。これは静的に確認できる適用範囲の拡大であり、旧版での最終 admission は本段では実測していません。

不在検査は、今回確立する登録 `#ifdef` の未定義対照に限定するのが最小です。全 domain の None 契約変更を採るなら、I1 との調整を別途明示してください。

**放置時の成果物：** 既存 macro の supply record／判定まで変わり得て、I1 の全既存入力互換を主張できません。

**3. real／must-fix：件数と test 所有範囲は brief の訂正が必要。**

G:254–310 と T:33–52 は枝選択18件、G:314 は FIXED を含め19件です。三件追加なら **枝選択18→21、対応集合19→22**。四件なら **18→22、19→23** です。

また `orchestrator/tests/test_silo_ladder_rung1_driver.py:105` は RUNG1 宣言が None と断定します。登録後は型・macro・owner・directive を検査する assertion に変更が必要です。plan の5 file案は正しい訂正です。

**放置時の成果物：** 対応件数の報告が誤り、既存 driver test が赤のままになります。

**4. refuted／nit：N mapping 自体は過剰ではない。新 field と追加の汎用検査は削れる。**

既存2-tupleは path と directive だけで、N を持ちません。実 source から N を推定すると「欠落した一箇所を正しい件数として再宣言」してしまいます。固定 N を独立して持つことには意味があります。

一方、次は削除を推奨します。

| 削除対象 | DW-G05：削除しても変わらないもの |
|---|---|
| brief P1 の新 declaration／receipt field | G:514–515 の既存 counts と registry の N で同じ受理条件を表現でき、certified 選択・レポート・台帳・受理集合は変わらない |
| 固定 mapping に対する汎用の不正キー・型・正整数 validator／専用 test 群 | 独立期待表との完全一致検査で固定二項目を束縛すれば、同じ成果物と受理集合になる |
| driver ごとの新しい対照形 mapping | G:990 の既存 directive から判別でき、同じ request・宣言・成果物になる |
| production 用の互換再生 framework | 同一観測入力での旧新比較を test／job 内に限定しても、production の成果物と受理集合は変わらない |

新しい `site-count-mismatch` reason は**必須ではなく診断上の選択**です。ただし既存 `start-not-unique` の文章は N>1 に不正確なので、単純流用も推奨しません。新 reason を削ると赤台帳の reason は変わるため、ここを「全成果物不変の削除」と数えてはいけません。

**放置時の成果物：** 新 field は既存 canonical bytes を変え、その他の一般化は成果物を改善せず編集面だけ増やします。

**5. refuted／must-fix条件付き：既存 test の削除は不要。局所更新で pin を保てる。**

- **未登録例：** T:1690 の MISATTR を `SS2PL_LOCK_IMPL` の要求1／既定0へ差し替える。併せて registry 非所属を明示する。MISATTRを既定0のまま残すと、「未登録」ではなく「登録済みだが非対応の値対」を検査する test に変質します。
- **重複拒否：** T:1565 は `IZANAGI_BREAK_WRITE_INTENT_ERASE`。N=1 のままなので、重複は引き続き `start-not-unique` の赤です。削除・green化は不要です。
- **patch helper：** T:286 を単に `len(matches) >= 1` や `len(set(matches)) == 1` にしてはいけません。独立した期待 `(owner,directive)` に対して **`matches == [expected_pair] * expected_N`** を要求する。戻り値は従来の2-tupleで足ります。T:1006 の fixture 行数も同じ独立 N と照合します。

**放置時の成果物：** 弱い assert は箇所欠落・余分な重複を見逃し、未確立一覧から macro を消す根拠を弱めます。

**6. refuted／nit：REQUESTED_US 見送りは費用に根拠がある。ただし「(b)(c) 完了」とは書けない。**

実 patch の header 二箇所は `patches/silo-backoff-requested-us.patch:29,41`、TU 二箇所は `:60,178`。G:3182 は単一 source capture、G:2987 の shadow writer も単一 source、G:3976 は単一 source evidence です。

header 経路を二回呼ぶだけでは同じ shadow へ二 file を計装できません。三件案では複数 file 宣言・capture・shadow・schema 拡張をまとめて見送る判断が妥当です。TU二箇所だけの登録は勧めません。

**放置時の成果物：** 見送りなら REQUESTED_US は未確立のまま残るため、四件完了・残件(c)解消という報告は誤りになります。

**7. real／must-fix：gate CLI の green と、研究成果物の改善を分けて完了確認する必要がある。**

C:122 の公開経路は `raw-measurement`。C:347 の `condition_gates` が条件証拠であり、`build_admissions` は別の build receipt です。CLI の `certified-selection` admission が green になっただけでは coverage JSON の改善まで証明できません。

MISATTRの枝選択は誤帰属そのものの発火・検出も証明しません。P3 の GATING十二箇所も skeleton の枝選択までです。`patches/instr-silo-backoff-trigger-gating-tally.patch:9` の複合条件や `patches/silo_ladder_rung1.patch:56` の REPORT footer まで同時に確立したとは扱えません。

**放置時の成果物：** CLI cell の改善を、未取得の公開 driver JSONや positive-control 検出結果の改善として過大報告します。

## pin 表

path と指定 key を `git grep` し、現行 SHA-256 と index blob も照合しました。下表の「不要」は**pin 更新不要**であり、既存 pin を削除してよいという意味ではありません。

| pin／閉包 | 根拠 file:line | 判定 |
|---|---|---|
| `_COMPILE_TIME_BRANCH_MACROS`・tuple順序 | T:33、T:996 | **must更新**：追加分だけ列挙し既存順序を維持 |
| `MEANING_SUPPORTED_MACROS` 集合 | G:314、T:2814 | **must確認**：独立列挙に追随。別の件数専用 test は重複 |
| `CONDITIONAL_BRANCH_WITNESSES` の2-tuple | T:1009、`test_mocc_mutation_proof.py:177`、`test_mocc_template_proof.py:267`、`test_mocc_proof_surface.py:569` | **must維持**：consumer編集不要 |
| patch／fixture directive 行数 | T:286、T:1006 | **must更新**：新規だけ独立 N。旧 N=1 は維持 |
| observation counts・argv | T:1339–1351、G:3835–3847、G:3988–4028 | **must更新**：N と None。旧 `#if` の比較は維持 |
| RUNG1 None pin | `test_silo_ladder_rung1_driver.py:105` | **must更新**：第5所有file |
| coverage の getsource／呼出順 | S:86–94 | 更新不要。ただし順序だけでは factory／default の配線を検出しないため実 helper test が必要 |
| rung1 getsource | `test_silo_ladder_rung1_driver.py:34–47` | 更新不要：factory既配線 |
| S1 extime getsource | `test_s1_verify_extime_calibration.py:30–33` | 現状は None を要求しない。採用時は実 helper 検査を追加 |
| spawn site 数・build entry | `test_ccbench_spawn_sites.py:81,123,222–224,603,2420`、`materializer_admission.py:103` | 更新不要：subprocess／build callsiteを増やさない |
| B-4 module数 | `test_p3_b4_wiring_probe.py:327` は **47**。`p3_b4_wiring_probe.py:1083–1099` は静的import閉包 | 更新不要：N helper を既存 G 内に置き、新moduleを足さない |
| B-4 module digest | `p3_b4_wiring_probe.py:1112` | 新規実行では再算出。過去manifestを書き換えない |
| `check_docs.py` dispatch契約 | `tools/check_docs.py:3552–3553,4033–4051` | 更新不要：runbook／dispatcher契約の変更なし |
| 変更4 fileの現行SHA／blobの固定写し | 下表のhashを検索。現行hashの一致参照は検出なし | 手動repin不要。過去receiptは維持 |
| 過去 gate SHA receipt | `output/env/pegasus/t316-sandbox-backend/0:4163.nqsv/receipt.json:37`、他3 receiptの`:36` | 更新不要：過去実行の証拠 |
| S1 golden の backoff path | `orchestrator/tests/s1_expected_goldens.py:256,318,373` | **hash pinではなくpath／key構造**。driver無変更なら更新不要 |
| 凍結manifest | `output/s1-freeze/{known_axes_freeze,measurement_freeze}.json`、`output/s8b-freeze/holdout_freeze*.json` | 変更4 fileへの直接一致なし。既存backoffの歴史hashは維持 |
| 総行数pin | 検索で変更4 fileの総行数固定は検出なし | 新設不要。directive件数pinとは区別 |

現行識別子の照合用短縮表示です。

| file | SHA-256先頭 | index blob先頭 |
|---|---|---|
| G | `3a0416e2d84c` | `58fa1bfbcf42` |
| C | `66c963fa2821` | `71bbf6d1652f` |
| T | `9e4c5e455c4a` | `65a50da0ec68` |
| S | `7f107b3968a1` | `71024e3ead9f` |

**backoff の「歴史記録2件」は、現行 SHA-256全文の写しという限定なら正しいです。**

`5d55cbbb030fd8ad33701fe23da257c7f757900d7999178b481b0c39fc0bea10` の一致は次の2件でした。

- `docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md:354`
- `output/insights/2026-09-17/t2228-screening-gate-liveness/evidence/production-sha256.txt:1`

ただし「他の写しがない」は誤りです。短縮表記は `output/insights/2026-09-18/t2674-t1998-results-doc/README.md:23` にあり、**旧hash** `4e7fa96e…` は S1 freeze二件、holdout freeze二件、candidate、過去ledgerにもあります。いずれも現行driverへの追随更新対象ではありません。

## 配線表

campaign側のpathは `orchestrator/campaign/`、test側は `orchestrator/tests/` を省略しています。

| driver | 対象要求 | admissionの永続化 | 一行で済むか | None前提test／採否 |
|---|---|---|---|---|
| `s8a_trigger_coverage` | C:153 GATING、C:163 MISATTR。現状とも1/0 | C:130→347→424 | **二箇所**：defaultとfactory | S:94は順序のみ。**配線must** |
| `s8a_trigger_freq` | `:134–139` はGATINGのみ | `:148→204` | 編集0行、coverage helper共有 | **自動追随を回帰確認** |
| `s8a_trigger_sweep` | `:320–322` GATING 1/0 | `:340`で返すが`:408`で廃棄。`:614–623`にも無し | factoryだけなら一行。成果物までなら不可 | S:79–94はpreflight隔離／順序。None固定なし。**配線不要** |
| `backoff_sweep` 非FIXED | helperは汎用。公開caller`:456–459`はFIXEDのみ | `:228`で返すが`:452`で廃棄 | `:209`の一行は可能だが対象成果物を改善しない | `test_backoff_sweep.py:362`等はFIXED経路。**変更不要** |
| `backoff_requested_us` | `:137` REQUESTED_US。test`:752`も要求1を確認 | `:133`で返すが`:1107`で廃棄 | 共通helper一行だけでは永続化されない | `test_backoff_requested_us.py:732–754`は要求転送を検査。None固定なし。**配線不要** |
| `silo_ladder_rung1` | `:2174` RUNG1 **1/0**、`:2175` REPORT 1/0 | `:2245→4139／4635` | `:2232`でfactory既配線、編集0行 | test`:105`だけ更新必須。**自動追随** |
| `s1_verify_extime_calibration` | `:94` GATING、`:225`のgenomeで1/0 | `:113→405→468→479` | factoryは一行だが`:91`の供給整合も要確認 | test`:30–33`にNone固定なし。**親の採否裁定が必要** |

推奨最小集合は **coverage の二箇所変更＋frequency／rung1の追随確認**。S1 extime は省略せず、供給整合込みの追加範囲か、未解決の別変更単位として明記してください。探索loopへの編集を必要とする根拠は本検査では見つかりませんでした。

## 親 brief への反論

| 前提 | 推奨裁定 |
|---|---|
| P1 | 別N mappingを採用、新dataclass／receipt fieldは削除 |
| P2 | directiveからの判別は採用。不在検査を全 `default=None` に広げない。G:4014の再検証変更は必須 |
| P3 | 十二箇所のskeleton枝選択として採用。番兵・診断複合枝まで含む「macro全体の意味」という説明は避ける |
| P4 | REQUESTED_US見送りを推奨。四箇所同時観測が必要な残件として保持 |
| P5 | S1 extimeの省略を訂正。返り値を捨てるsweep群の配線見送りは妥当 |
| P6／I1 | 既存19件へ訂正。同一捕捉入力のcanonical比較と、独立実走の意味互換を分ける |

段6の変異matrixも縮められます。推奨する必須集合は次です。

| 種別 | 最小限残す検査 |
|---|---|
| 実装正例 | MISATTR 1/None、RUNG1二箇所、GATING十二箇所の各 green／admitted／未確立なし |
| 入力負例 | MISATTR 1/0、未定義対照へのdefine混入、一箇所逐語変更、一箇所外側非活性、既定側だけ一箇所選択 |
| 配線変異 | coverage default→0、factory→None |
| 件数変異 | GATING N=12→11。RUNG1 2→1は独立N pinと旧N=1重複拒否が残るなら追加変異走を省略可 |
| 判定変異 | 評価側default期待緩和とschema側緩和を各一件。別防壁なので統合しない |
| 不在検査変異 | supply側の検査削除。数値差を残すfixtureで意味側拒否と切り離す |
| 等価対照 | registry近傍comment一件。枝本文変更は通常testでcounts／判定不変を確認 |

MISATTR削除・RUNG1削除・任意entry削除の三系統は、独立集合pinと実factory配線testがあれば変異走として重複です。必要ならentry削除一件に集約できます。正例fixtureを壊す変異も、件数pin変異と同じ失敗を数えるため必須集合から外せます。

plan:200 の `_assert_compile_time_branch_selection` は現物に無く、変異節で突然導入されています。評価側の独立検査に必要なら**純粋なcounts検査の抽出だけ**として差分へ明記し、一般的なassertion frameworkへ広げないでください。

F29対策として、fixtureの無条件本文だけでは完了にしません。最終production registryで、採用三件を **login／計算ノードの両方、実patch・実TU・official同形供給・外側条件有効**でCLI実走し、両腕counts・supply／meaning・admissionを保存することを完了条件に残します。さらに公開成果物の未確立一覧が縮んだという主張には、coverage／frequency／rung1の実成果物が必要です。未取得なら「CLIで成立、公開成果物は未取得」と分けます。

## 総括

**planは修正後採用。** 三件登録・別N mapping・schema維持・coverage最小配線は妥当です。修正必須は、S1 extimeの採否、未定義検査の適用範囲、件数・test所有範囲・完了主張です。REQUESTED_USと探索loopは残件を明記し、凍結hashやB-4の47 module pinは動かさない方針を推奨します。