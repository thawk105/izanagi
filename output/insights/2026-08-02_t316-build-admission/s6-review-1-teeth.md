# 静的敵対レビュー

結論から言えば、新 gate は `pipeline.evaluate()` の呼出規約には歯を持つが、build 境界そのものには歯を持たない。未分類・誤分類された source bytes と既存 cache/WAL を通す経路が残っている。

これは read-only の静的検査である。書き込み、pytest、build、mutation 実走はいずれも 0 件であり、緑は主張しない。

## 重大所見

### Critical — F1: `buildcache` が admission を完全に迂回する

- **claim:** admission は実際の materializer に置かれていない。構文クラス「`buildcache.build()` / `build_v2()` の直接呼出し」は、provenance も opt-in も提示せず binary を生成・取得できる。
- **evidence:** 両 API の引数に admission がない（[buildcache.py:423–428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py:423)、[buildcache.py:594–610](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py:594)）。`backoff_profile` は直接 build 後に binary を実行し TPS/IPC を成果物へ書く（[backoff_profile.py:130–170](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/backoff_profile.py:130)、[backoff_profile.py:183–220](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/backoff_profile.py:183)）。同型経路は [backoff_overthrottle.py:60–86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/backoff_overthrottle.py:60)、[between_run_floor.py:150–166](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/between_run_floor.py:150) にもある。別 API の S8b も `build_v2` を既定 materializer にする（[s8b_floor_campaign.py:962–981](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8b_floor_campaign.py:962)、[s8b_floor_campaign.py:2682–2708](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8b_floor_campaign.py:2682)）。
- **impact:** allowlist 内に CODER_DERIVED の tracked 差分がある共有 tree から、admission 0 回で binary と TPS/IPC/floor 系成果物を生成でき、受理集合は実質的に縮小していない。
- **suggested_fix:** admission を `build()` / `build_v2()` の必須引数にし、raw materializer を非公開化する。直接 caller 全件を分類し、少なくとも profile・coverage・calibration・S8b を同じ gate に通す。

### Critical — F2: provenance は source bytes ではなく caller の自己申告

- **claim:** gate が検証するのは enum/bool の整合だけであり、実 source と class の対応ではない。構文クラス「非 `CODER_DERIVED` enum + false を渡し、非-stock `src_token` を build する」は無条件に受理される。
- **evidence:** `_validate()` は型と二値の組だけを見る（[build_admission.py:22–35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/build_admission.py:22)）。`evaluate()` は admission 検証後に source token を解決するが、両者を比較しない（[pipeline.py:472–473](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:472)、[pipeline.py:524–553](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:524)）。source 側は三ファイル内の tracked 改変を明示的に許す（[source_digest.py:78–81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/source_digest.py:78)、[source_digest.py:662–698](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/source_digest.py:662)）。一方、`demo` や P2 は clean/pinned を確認せず固定 `STOCK_OR_PINNED` を渡す（[demo.py:41–60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/demo.py:41)、[p2_2.py:129–139](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p2_2.py:129)）。
- **impact:** 同じ CODER_DERIVED bytes を `STOCK_OR_PINNED`、`MACHINE_SWEEP`、`HUMAN_REVIEWED` のどれかとして自己申告すれば、certified/median_tps の受理集合へ入れられる。
- **suggested_fix:** class を caller が自由に選ぶ値にせず、materialization 時の source digest、clean/pin 検査、generator identity、review receipt から発行する capability にする。`STOCK_OR_PINNED` なら `src_token == stock` または署名済み pin を必須化する。

### Critical — F3: cache と WAL replay が class を跨いで再利用される

- **claim:** admission は legacy/v2 cache identity、completion manifest、campaign identity のすべてから欠落している。現在の有効な別 class admissionだけで、過去の未分類または CODER_DERIVED artifact を再利用できる。
- **evidence:** legacy key は genome/commit/trace/src/compilerだけ（[buildcache.py:121–135](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py:121)）、v2 preimage も同様（[buildcache.py:219–234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py:219)）、completion manifest にも admission がない（[buildcache.py:557–568](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py:557)）。cache hit は source identity を再照合するだけで class を見ない（[buildcache.py:487–503](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py:487)、[buildcache.py:628–641](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/buildcache.py:628)）。campaign preimageにも admission がなく（[ident.py:76–103](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/ident.py:76)）、`run_campaign()` は terminal を admission receipt と照合せず `evaluate()` 前に skip する（[loop.py:88–108](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/loop.py:88)、[loop.py:143–156](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/loop.py:143)）。実装自身も stock seed binary を CODER_DERIVED no-op run から cache-hit させる設計である（[p3_kickoff.py:13–18](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_kickoff.py:13)、[p3_kickoff.py:101–118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_kickoff.py:101)）。
- **impact:** binary hash、`median_tps`、certified terminal を作成時とは別の provenance class へ付け替えられ、旧未分類 artifact も grandfather される。
- **suggested_fix:** provenance class と admission-policy version を cache preimage・manifest・campaign preimageへ入れ、cache hit/replay 時に完全一致を要求する。receipt 欠落の旧 entry は拒否または明示 migration とする。

### High — F4: sort/trigger sweep の正経路は `admission` 未定義で全点停止する

- **claim:** `run_sweep()` が受け取った admission は `_eval_one()` に渡されず、`_eval_one()` は未定義名を参照する。
- **evidence:** sort は `_eval_one()` 呼出しに admission がなく（[s6_sort_sweep.py:246–268](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py:246)）、仮引数にもないのに [s6_sort_sweep.py:305–337](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py:305) で参照する。trigger も同型（[s8a_trigger_sweep.py:292–315](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py:292)、[s8a_trigger_sweep.py:352–384](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py:352)）。広い `except Exception` がこれを `driver-error` に変換する（[s6_sort_sweep.py:267–280](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py:267)、[s8a_trigger_sweep.py:313–326](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py:313)）。
- **impact:** opt-in 正例でも build/`median_tps`/commit に到達せず、全候補が `driver-error` となるため「従来能力を保つ」という裁定条件を満たさない。
- **suggested_fix:** `_eval_one()` に keyword-only admission を追加し、通常・screening baseline・candidate の全呼出しから明示伝播する。少なくとも一つの検疫通過候補を実 build-entry spy まで通すテストを追加する。

### High — F5: 15 caller のうち少なくとも8箇所は分類の証明になっていない

- **claim:** author の「判断不能 caller なし」は成立しない。6箇所は source tree と class が未束縛で緩すぎ、s6/s8a の2箇所はコード自身の「機械生成」説明と矛盾する。
- **evidence:** 独立 census は次のとおり。

| call 数 | callsite | 指定 class | 静的判定 |
|---:|---|---|---|
| 2 | [demo.py:51,59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/demo.py:51) | STOCK | clean 未確認。allowlist 内 coder bytes を受理可能 |
| 2 | [backoff_sweep.py:149](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/backoff_sweep.py:149)、[backoff_repro.py:98](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/backoff_repro.py:98) | MACHINE | genome の生成法だけを分類し、source bytes は未束縛 |
| 2 | [p2_2.py:138](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p2_2.py:138)、[sanity_silo.py:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/sanity_silo.py:51) | STOCK | clean/pin 証明なし |
| 7 | kickoff 2、P3 loop 3、red 2 | CODER/STOCK | 適用 patch と stock 復帰の区別はコードから追跡可能 |
| 1 | [s6_sort_sweep.py:330](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py:330) | CODER | 候補は「信頼中核が機械生成」と明記（[同:31–34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py:31)）。stock点も同じ admission |
| 1 | [s8a_trigger_sweep.py:377](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py:377) | CODER | 部分集合を決定論的列挙（[同:155–195](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py:155)）。stock点も同じ admission |

- **impact:** 前者6箇所は CODER bytes を別 class で受理して受理集合を拡大し、後者2箇所は MACHINE/stock を不必要に拒否して正例集合を縮小する。
- **suggested_fix:** source単位で class を決定する。s6/s8a は stock点を `STOCK_OR_PINNED`、決定論的候補を `MACHINE_SWEEP` と分け、もし過去の coder 由来 skeleton が全体を汚染するという判断なら、その由来を manifest へ明示して検証可能にする。

### Medium — F6: 「CLI 由来のみ」「immutable」は強制されていない

- **claim:** 変更された production driver から環境変数・設定値が opt-in へ流れる箇所は静的には見つからなかったが、型自体は CLI authority を表現していない。
- **evidence:** public constructor は通常の bool `True` を受理し、正例テスト自身が CLI を介さず生成している（[test_campaign.py:1438–1447](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1438)）。`frozen=True, slots=True`（[build_admission.py:38–46](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/build_admission.py:38)）は通常代入だけを止め、テスト自身が低水準 object 操作で instance を構成・変更できることを示す（[test_campaign.py:1397–1402](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1397)）。
- **impact:** 任意の in-process Python caller が CLI 操作なしに有効な CODER receipt を製造でき、opt-in は operator authority ではなく規約上の bool に留まる。
- **suggested_fix:** constructor を公開 authority にせず、CLI parser が発行する run-scoped capability と source digest を結合する。Python 内の絶対不可変性を保証できないなら、信頼境界を文書上も「trusted orchestrator code」に限定する。

## admission 分岐の発火性

実装上の死枝は見つからない。ただし、発火対象は source ではなく自己申告値である。

| 分岐 | 発火する構文クラス | テスト状況 |
|---|---|---|
| CODER + opt-in false（[build_admission.py:27–31](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/build_admission.py:27)） | CODER class と省略時 false、または CLI flag なし | あり |
| 非CODER + opt-in true（[build_admission.py:32–35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/build_admission.py:32)） | STOCK/MACHINE/HUMAN class と true | 直接テストなし |
| provenance/bool の非exact型（[build_admission.py:23–26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/build_admission.py:23)） | 文字列 class、整数の opt-in、subclass | 一部あり |
| admission の非exact object（[build_admission.py:55–60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/build_admission.py:55)） | `None`、別型、subclass | あり |

従って「既定拒否分岐が恒真で発火しない」のではない。問題は、非CODER class を名乗れば source に関係なくその分岐を選ばせない点にある。

## テストと M1〜M5

### High — F7: 五つの変異は独立した五つの証拠にならない

- **claim:** M1/M2 は実質同一、M3 は二重防御の片側しか変えられず、M4 は誤った class oracle、M5 は変異対象の分岐自体が存在しない。
- **evidence:** 裁定の変異定義は [s4-ruling.md:75–81](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s4-ruling.md:75)、実装の policy 分岐は [build_admission.py:22–35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/build_admission.py:22)、追加テストは [test_campaign.py:1405–1612](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1405)。
- **impact:** mutation ledger が赤でも、acceptance boundary や build 到達回数を一意に証明せず、cache/direct-build/replay の穴は無傷のまま残る。
- **suggested_fix:** 各 mutant の exact hunk を一つに固定し、一つの入口・一つの buildcache spy・一つの期待理由へテストを分割する。

静的な赤予測は次のとおり。

| 変異 | 赤くなると予想するテスト | 赤理由の単一性 |
|---|---|---|
| M1: CODER reject を除去 | pipeline負例、loop/screening複合、sweep CLI、sweep seam、qualification負例 | pipeline/qualification は build spy まで到達するため比較的有効。loop/screening は二入口同時、sweep seam は `names=[]` なので build spy は常に0で、例外が消えたことしか示さない |
| M2: opt-in値を `True` 固定 | 通常の `coder_derived_opt_in → True` 変異なら M1 と同じ一式 | M1 と真理値表が同一で独立証拠にならない。「if条件全体をTrue」の意味なら逆に常時拒否となり、事前登録が曖昧 |
| M3: evaluate の未指定許可 | signatureだけ既定 `None` にすると、[missing-argument test:1422–1435](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1422) は `BuildAdmissionError` の未捕捉で赤 | runtime `require` が拒否を維持するため、受理集合を広げていない偽 kill。runtime検査だけ緩める変異は必須signatureで手前拒否され、生存すると予想 |
| M4: sweepを MACHINE へ | [CLI既定負例:1531–1549](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1531) に加え、s6正例は MACHINE + opt-in true が別分岐で拒否され赤 | default bypass、非CODER opt-in拒否、class期待不一致が同時発火する。しかも実 source は機械生成なので、mutation が policy 修正側 |
| M5: STOCKを拒否 | `_validate()` に STOCK 固有分岐がない。constructor拒否を足すと module-level `_STOCK_ADMISSION`（[test_campaign.py:53](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:53)）で collection が停止 | stock正例だけでなく多数のtestが実行前に崩れる。既存CODER分岐のenumを書き換えるなら CODER許可も同時発生し、二理由になる |

追加の生存候補として、非CODER + opt-in true の拒否分岐を削除する変異は、現在のT-316直接テストでは検出されないと予想する。[非exact値テスト:1476–1482](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1476) はこの組を入力していない。

また sweep/preview の「build spy」主張は弱い。sweep seam は候補ゼロ（[test_campaign.py:1552–1571](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1552)）、opt-in正例は `run_sweep` 全体を lambda に差し替える（[同:1574–1589](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1574)）。preview試験は `_preview_diff` 自体まで差し替えるため（[同:1592–1612](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1592)）、その内部に direct build が追加されても検出できない。

## preview / `--no-build` / dry-run

現行コードを静的に追った限り、通常の preview は `quarantine(write=False)` を `applied()` の一時 context 内で実行して復帰し（[p3_s4_loop_sort.py:338–353](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_sort.py:338)、[p3_s4_loop_trigger_gating.py:532–544](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:532)）、preview branch は admission構築前に return する。

`--no-build` も base loop では `write=False` の検疫後に `dry-pass` を返す（[p3_s4_loop.py:654–663](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop.py:654)）。campaign lock、checkpoint、reject WAL 等のメタデータは残り得るが、現在の標準経路から binary/cache entry や永続 source mutation が作られる箇所は見つからなかった。後日の標準 build には改めて admission が必要である。ただし F1 の direct materializer はこの結論の外側から常に迂回できる。

## 総括

must-fix: admission を `buildcache` 境界へ移し、source digest・class・cache manifest・campaign replayを同じ証明に束縛する。加えて s6/s8a の未伝播 `admission` と候補単位のclass誤りを直す必要がある。

変異で死なないと予想する箇所: M3のruntime側だけの緩和、非CODER+true拒否分岐、cache/replay/direct-build の admission欠落。M1/M2は重複し、M4/M5の赤は単一理由にならない。

最大の迂回経路: allowlist 内に coder-derived 差分がある共有 CCBench tree で `backoff_profile` 等の既存 direct callerから `buildcache.build()` を呼ぶ構文クラス。admission 0 回で build・cache・実測成果物まで到達する。