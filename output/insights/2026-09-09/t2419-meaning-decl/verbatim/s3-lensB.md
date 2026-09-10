## 読んだもの

一次資料として、指定された親 brief、段2プラン、および次の7ファイルを全文確認した。

- [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2419-meaning-decl/s1-brief.md:1)
- [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2419-meaning-decl/s2-plan-out.md:1)
- [backoff_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:1)
- [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:1)
- [backoff_overthrottle.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_overthrottle.py:1)
- [backoff_profile.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_profile.py:1)
- [backoff_requested_us.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_requested_us.py:1)
- [backoff_repro.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_repro.py:1)
- [b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:1)

補助資料として meaning evaluator、実 patch、screening 経路、関連テスト、import consumer、freeze 連鎖、受入時間台帳とその consumer、Pegasus 実行規約を読んだ。pytest は実走していない。

実測した `rg` 結果では `_require_backoff_condition_gate` の production 呼び出しは7式、6 module だった。うち6式が `BACKOFF_FIXED`、残り1式が `backoff_requested_us.py` の `BACKOFF_REQUESTED_US` 専用呼び出しである。B10 shape driver 内の同 helper 呼び出しは0件だった。

## driver 表

以下は現行 patch sourceを前提に、段2案をそのまま実装した場合の終端状態である。`red` は現行6 driverにはない。乱択帯の拒否は meaning の `red` recordではなく、helper内の事前例外になる。

| driver | 実際に渡す `BACKOFF_FIXED` | 変更後の終端状態 |
|---|---|---|
| `backoff_sweep.py` | `{-1, 2, 5, 10, 25, 50, 100}`。定義は [SWEEP_US:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:60)、genome化は [同:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:198)、gate入力は [同:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:378) | `-1` は既存 branch witnessでgreen、全正値もgreen。BFのunestablishedなし |
| `backoff_extended_sweep.py` | 通常系列は `-1`、raw `0..900` の疎な29点中低域、物理1000のraw `3000`。[grid:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:55)、[encode:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:64)。T2266は `{-1,150,200,300,500,750,3000}`、T2418は `{-1,4000,6000,11999}`。[各points:432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:432)、[wrapper:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:527) | BFはすべてgreen。driver停止なし。ただしT2418の成果物文字列は別途unestablishedのまま |
| `backoff_overthrottle.py` | `backoff_extended_sweep.genomes(tag)`を継承するため通常extended集合と同じ。[consumer:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_overthrottle.py:61)、[gate投入:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_overthrottle.py:72) | BFはすべてgreen。unestablishedなし |
| `backoff_profile.py` | `{-1,2,5,10,25,50,100}`。[BACKOFF_US:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_profile.py:74)、[gate:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_profile.py:344) | BFはgreen。ただし同じfamilyの `BACKOFF_NOINLINE=1` は引き続きunestablished。family admissionは通る |
| `backoff_requested_us.py` | 実測時のBF gateはadaptive基準点 `{-1}` だけ。[wrapper:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_requested_us.py:110)、[実呼出し:1087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_requested_us.py:1087)。D1106のraw `0..1000`は歴史的reference再構成で、実BF gate入力ではない。[同:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_requested_us.py:96) | BF `-1` はgreen。別呼び出しの `BACKOFF_REQUESTED_US=1` はunestablishedのまま。[同:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_requested_us.py:126) |
| `backoff_repro.py` | `{-1,5,10}`。[ORIG:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_repro.py:50)、[genomes:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_repro.py:87)、[gate:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_repro.py:72) | BFはすべてgreen。unestablishedなし |

したがって、現行6 driverの実値に限れば、段2案により停止するproduction driverは0本である。

B10の乱択帯は実在する。`shape_code=1`と `MEANS_US=(2,5,10,25,50,100)` から、`encode` は raw `1002,1005,1010,1025,1050,1100` を作る。[SHAPES:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:100)、[encode:782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:782)、[genome化:807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:807)。

- 実測: B10ファイル内の `_require_backoff_condition_gate` grep hitは0件。
- 読解: formal buildは `named_genomes()`から直接 `_build_binary` を呼び、verifyは `run_campaign`へ渡す。[build:4431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:4431)、[verify:4468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:4468)。したがって今回のstatic helper拒否はB10に届かない。
- ただしB10は無防備ではない。閉じたgrid、exact formula、applied-tree bytes、全cellのphysical residualを独自に検査する。[formula pin:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:324)、[tree検査:964](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:964)、[grid契約:1176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:1176)、[residual検査:1714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/b10_backoff_shape_sweep.py:1714)。

## 所見

**所見 1: codec由来の宣言は「driverが要求した意味」を完全には表さない**

- 根拠: helperの入力はraw整数列だけであり、物理usは渡されない。[backoff_sweep.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:88)。選択案はそのrawを `decode_static_backoff_us` に通して期待値を作る。[s2-plan-out.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2419-meaning-decl/s2-plan-out.md:16)。raw `3000` はcodec上 `1000`になる。[backoff_extended_sweep.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:71)。
- 失敗シナリオ: `backoff_sweep.SWEEP_US`へ物理3000usのつもりで整数`3000`を追加すると、genomeと表示は `fixed=3000us`になる。[backoff_sweep.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:200)、[同:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_sweep.py:425)。しかし宣言は1000、実C++観測も1000なのでmeaningはgreenになる。[patch:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/patches/silo-backoff-fixed.patch:70)、[green分岐:3434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/condition_meaning_gate.py:3434)。raw1000の一点は止まるが、「格子値を物理値と思って投入し、codec上の別条件を測る」という事故型は残る。
- 必要な修正: callerから `(raw, intended_physical_us)` を独立に渡すか、少なくともliteral-us driverとencoded driverを型または別helperで分離する。rawだけから宣言を復元しては意図を証明できない。
- 深刻度: **blocker**。親briefの狭いraw1000完了条件は満たすが、依頼されたF718同型事故の一般防止は満たさない。

**所見 2: productionのgeneric screening経路はraw1000を引き続きadmitする**

- 根拠: screeningはGenomeからBF requestを作るが、runtime meaningへ常に `declaration=None` を渡す。[screening_driver.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/screening_driver.py:93)、[同:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/screening_driver.py:219)。`None`はunestablishedになり、family admissionはunestablishedを許す。[condition_meaning_gate.py:3300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/condition_meaning_gate.py:3300)、[同:4063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/condition_meaning_gate.py:4063)。このgateは実際に `evaluate_candidate` のbuild前に呼ばれる。[screening_driver.py:589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/screening_driver.py:589)。
- 失敗シナリオ: patched sourceと `Genome(...BACKOFF_FIXED=1000)` をgeneric screeningへ渡すと、supplyはgreen、meaningはunestablished、admissionはtrueとなる。raw1000でsupply greenになること自体は既存実テストが固定している。[test_condition_meaning_gate.py:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_condition_meaning_gate.py:447)。親はこの経路を明示的にscope外としている。[s1-brief.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2419-meaning-decl/s1-brief.md:20)。
- 深刻度: **blocker**。production全体で止まるという親briefの表現とscopeが矛盾する。scopeを広げないなら、完了主張を「6 helper consumerだけ」に狭める必要がある。

**所見 3: T2418のlive成果物は、green化後もunestablishedと記録する**

- 根拠: T2418のraw `4000,6000,11999` は変更後すべてgreenになる一方、live config、JSON、dat provenanceは固定文字列 `unestablished_for_positive_backoff_fixed_as_in_existing_sweep` を使う。[定数:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:99)、[config:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:647)、[JSON:1168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:1168)、[dat:1275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:1275)。
- 失敗シナリオ: 変更後にT2418を再走すると、build前gateはgreenなのに、新規campaign identityと新規reportがunestablishedと宣言する。これは歴史的既存artifactを不変にする問題ではなく、同じdriverが新しく出すlive metadataの不整合である。
- 深刻度: **must-fix**。既存artifactを変更せず、run kindまたはschemaをversion-upしてlive状態を正しく記録する必要がある。

**所見 4: 「現行sourceとの一致を要求するconsumerはない」は実測と反する**

- 根拠: known-axes verifierはsource全件をlive bytesで再hashし、不一致を常に拒否する。[s1_known_axes_freeze.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/s1_known_axes_freeze.py:877)。hold対象になるのはその後のccbench pinであり、source hash照合ではない。[同:903](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/s1_known_axes_freeze.py:903)。productionではmeasurement freezeがこのverifierを呼び、extime calibrationも既定で直接呼ぶ。[s1_measurement_freeze.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/s1_measurement_freeze.py:160)、[s1_verify_extime_calibration.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/s1_verify_extime_calibration.py:230)。
- 実測: `sha256sum backoff_sweep.py` は `1b64f897...`、freeze記録は `4e7fa96e...`。[known_axes_freeze.json:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/output/s1-freeze/known_axes_freeze.json:152)。
- 失敗シナリオ: 上記production consumerがchecked-in known axes freezeを検証すると、今回の変更以前からsource mismatchで停止する。今回新たに作る赤ではないが、親の「consumerなし」という根拠は成立しない。
- 深刻度: **must-fix**。briefで既存赤を明示し、歴史artifactとlive verifierの契約を別裁定へ送るべきである。

**所見 5: negative test案は既存evaluator testを重複し、所見1の穴を覆わない**

- 根拠: raw1000を1000.0と宣言して実compilerでredにする検査は既に2本ある。[test_condition_meaning_gate.py:414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_condition_meaning_gate.py:414)、[同:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_condition_meaning_gate.py:447)。段2案の新負例もhelperを迂回して手製宣言をevaluatorへ渡す。[s2-plan-out.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2419-meaning-decl/s2-plan-out.md:49)。
- 失敗シナリオ: production helperがraw3000を1000と自己宣言してgreenにする所見1の変異は、新しいraw1000 evaluator testを通過する。
- 深刻度: **must-fix**。production helperの事前拒否testは必要だが、独立したdriver intentを検査する負例も必要。

循環importへの攻撃は不成立だった。`extended -> sweep` が既存方向であり、codecをsweepへ移すと同じ方向のimport名が増えるだけである。[extended:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep.py:37)。overthrottleはextended初期化後にsweepをimportし、reportもextended後にoverthrottleをimportする。[overthrottle:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_overthrottle.py:24)、[report:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/backoff_extended_sweep_report.py:21)。全import検索でもsweepからextendedへの逆importはなかった。importされたcodec名はextended module属性として残るため既存consumerも壊れない。深刻度は **nit、変更不要**。

既存テストで期待値が変わるのは、段2案のままなら次の1箇所だけである。

- [test_backoff_sweep.py:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_sweep.py:166): raw5のmeaningが `unestablished` から `green/declared-meaning-observed` へ変わる。

[extended実wrapper test:919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_extended_sweep.py:919) は挙動上greenへ変わるがmeaningをassertしていない。screeningの `("BACKOFF_FIXED","unestablished")` は別実装なので影響を受けない。[test_screening_driver.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_screening_driver.py:182)。

ただし所見3を修正する場合、T2418文字列をpinする既存3期待も更新対象になる。[test_backoff_extended_sweep.py:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_extended_sweep.py:517)、[同:578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_extended_sweep.py:578)、[同:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_extended_sweep.py:716)。

## pin 閉包

| 変更予定file | path側のpin/参照 | key側のpin | 判定 |
|---|---|---|---|
| `backoff_sweep.py` | known axes freezeで3 workload分参照。[balanced:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/output/s1-freeze/known_axes_freeze.json:152)、[write:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/output/s1-freeze/known_axes_freeze.json:378)、[read:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/output/s1-freeze/known_axes_freeze.json:604)。measurement freezeにも3複製がある。[measurement:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/output/s1-freeze/measurement_freeze.json:171)、[同:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/output/s1-freeze/measurement_freeze.json:443)、[同:715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/output/s1-freeze/measurement_freeze.json:715)。holdout freezeにも2参照。[holdout:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/output/s8b-freeze/holdout_freeze.json:157)、[同:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/output/s8b-freeze/holdout_freeze.json:424) | 全て旧SHA `4e7fa96e...` と key `_BASE and SWEEP_US` を持つ。旧SHAのkey検索でも上記freezeにhitした | 凍結bytesは変更しない方針自体は妥当。ただしlive verifier consumerがあるので「pinなし」「不発」ではない |
| `backoff_extended_sweep.py` | import consumer、test、job/closure listのpath参照あり | 現行SHA `ec0146e...` の全体検索は0件。必須freeze、golden、ledgerを読解してもwhole-file byte pinはない | codec移動によるpin更新は不要 |
| `test_backoff_sweep.py` | acceptance ledgerに既存nodeidが9件登録済み。[ledger:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/acceptance_duration_ledger.json:256)、[同:3392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/acceptance_duration_ledger.json:3392) | file SHA pinではなくnodeid別duration | 新2 nodeidの未登録はschema違反ではない。post-change coverage確認は必要 |

`test_frozen_artifacts.py` はknown axes、measurement、holdoutの外側bytesをそれぞれpinする。[同:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_frozen_artifacts.py:41)。ただし現在はこれら4件がheld集合に入り、通常照合対象から外れる。[同:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_frozen_artifacts.py:119)、[同:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_frozen_artifacts.py:162)。

`s1_expected_goldens.py` はpathとkeyの並びをpinするが、編集可能なproduction sourceのSHAは意図的にpinしない。[同:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/s1_expected_goldens.py:10)、[同:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/s1_expected_goldens.py:252)、[同:657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/s1_expected_goldens.py:657)。したがって今回これを更新する理由はない。

## 親 brief への攻撃

- 「新test fileを作らないので台帳追加不要」は理由として誤り。台帳はfileではなく完全nodeidをkeyに持つ。[ledger:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/acceptance_duration_ledger.json:2)。consumer契約は収集全体の90%以上である。[test_acceptance_schedule_order.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_acceptance_schedule_order.py:704)。結論として新2件を今すぐ推測時間で足さないのは妥当だが、post-change collectionで90%を保つことが条件である。段2プランの「未計測値を推測しない」は正しい。[s2-plan-out.md:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2419-meaning-decl/s2-plan-out.md:61)。深刻度: **nit**。

- 「実測環境はlogin nodeのPython testのみ、計算ノード投入なし」は固定できない。現在地は実測で `pegasus02` だが、テストの実行場所は `tools/run_tests.py` が空きメモリとqueueから決める契約である。[tools/README.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/tools/README.md:8)、[pegasus-runbook.md:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/docs/pegasus-runbook.md:332)、[同:368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/docs/pegasus-runbook.md:368)。また追加予定testはPythonだけで完結せず、実C++ compilerを起動する。[s2-plan-out.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2419-meaning-decl/s2-plan-out.md:49)。性能測定が不要という判断は妥当だが、login限定は不当。深刻度: **must-fix**。

- 「現行source一致を要求するconsumerはない」は所見4のとおり偽。既存のlive production consumerがあるため、「あれば受入が既に赤」という推論も成立しない。通常受入ではgrowth holdや別経路により、そのconsumerを必ずしも実行していない。

- P1はsource drift検出には有効だが、driver intentの証明ではない。Python codecとC++ compileが独立でも、期待値をrawから自動生成する限り、raw3000を物理3000と思った事故をgreenにできる。

## 裁定候補

- production全体を完了条件に残すなら、generic screeningにもmeaning declarationを導入する必要がある。ただしB10のraw1000帯は正当な乱択符号なので、static codecを一律適用してはならない。推奨はstatic scalarとrandomized shapeを別の宣言型、別helperとして分離すること。

- known axes freezeのsource SHAを「歴史的出所」として保持するのか、「live source一致gate」として使い続けるのかを裁定する必要がある。前者ならlive verifierから当該比較を外すversioned migration、後者なら明示的refreezeとtrust-root更新が必要になる。

- T2418の `meaning_witness_status` は、既存artifactの歴史文字列と新規rerunのlive状態を分けるべきである。既存run kindを上書きせず、versioned run kind/report schemaを推奨する。

- `s1_direct_comparison` と `paper_story_a2_certification` は正値を常に `float(raw)` と宣言する独自経路である。[s1_direct_comparison.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/s1_direct_comparison.py:230)、[paper_story_a2_certification.py:758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/campaign/paper_story_a2_certification.py:758)。現行値は999以下だが、encoded上側へ拡張すると正しいraw3000も誤ってredにする。今回の6 helper scope外なので別裁定とする。

## 総括

現行6 driverは段2案で停止せず、各 `BACKOFF_FIXED` はgreenになる。  
ただしrawから宣言を自動生成する設計はdriver intentを証明せず、F718同型事故を一般には止めない。  
generic screeningはraw1000をunestablishedのままadmitし、T2418成果物もunestablished表示を残す。  
したがってproduction全体を完了主張に含める現プランはblockerあり。