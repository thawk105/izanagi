## 所見 1: 登録簿閉包に件数 pin の更新が漏れている

**判定: real／must-fix。** 放置すると新 macro の登録が正しくても既存受入テストが赤になる。

親 brief:63〜69、plan:388〜485 は主要登録を列挙しているが、次が抜けている。

| 現物 | 現在の pin | 新 macro 追加後 |
|---|---|---|
| `orchestrator/tests/test_condition_meaning_gate.py:2782` | CXX_FLAGS route 数 `16` | `17` |
| `orchestrator/tests/test_ccbench_spawn_sites.py:3466` | `proven-unreachable: 34` | `35` |
| 同:3469 | `covered: 38` | `39` |
| 同:3493 | `deferred: 14, proven-unreachable: 24` | `14, 25` |
| 同:3502 | `failure-reachable: 14, proven-unreachable: 24` | `14, 25` |

後四件は、新 macro が mocc owner の interface であり、既存 Silo probe の参照 macro 集合には加わらないことによる静的予測。pytest による確認はしていない。

また、`condition_meaning_gate.py:12〜15` の説明と `test_condition_meaning_gate.py:2901〜2904` の文字列 pin も閉包対象である。現物を AST で数えると **DefineSpec は38、compile-time witness は既に14**。説明の「12 total」は既存の不整合なので、単に12→13としてはいけない。追加後は39／15となる。

**是正案（逐語）**

> 「登録簿閉包へ route 件数、cross-product Counter、module claim とその文字列 test を追加する。新規登録後は供給39、CXX_FLAGS17、compile-time witness15とする。Counter は上表の差分を反映し、既存 node で分類を確認する。」

## 所見 2: import 再利用に伴う追加登録と行番号更新は限定される

**判定: 過剰登録の必要性は refuted／should。**

plan:451 の「旧 `_run_checked` を利用するなら新 module の同名 subprocess 登録は不要」は正しい。process inventory は各ファイルの直接呼出しを数える（`test_ccbench_spawn_sites.py:350〜368,2815〜2823`）。import 先の関数は新 module の直接 site に増えない。

- 新 `_run_trace` には `(“campaign/s3_mocc_mutation_proof.py”, “<module>._run_trace”): 1` が必要。W/U とも `ycsb_rratio=0`（plan:179〜180）なので rr0 と記す。
- `_install_dependency` は旧 module のまま。新 qualname 登録は不要（`materializer_admission.py:83〜87`）。
- 新 `_build_variant` の NON_ADMISSIBLE 登録と `MANUAL_BUILD_FILES` 追加は必要。floor test は各関数内のリテラル `"--build"` を収集する（`test_s8b_floor_campaign.py:8028〜8044`）。
- `_DEFERRED_GATE_MEMBERS` の対象は今回変更しない production file である（`test_ccbench_spawn_sites.py:913〜987`）。test ファイル自身の行移動や `screening_driver.py` の行追加を理由に lineno を更新する必要はない。

**是正案（逐語）**

> 「直接 subprocess の純増は新 `_run_trace` 一箇所とする。旧 helper の import に対する `_run_checked`／`_install_dependency` の新 module 登録、および今回非変更の deferred sink の lineno 更新は行わない。」

## 所見 3: 旧 proof test の拡張は不要で、旧証拠との境界を崩す

**判定: 『新 patch 追加で旧 exact pin が赤になる』は refuted／should。**

`test_mocc_proof_surface.py` は次を固定列挙している。

- :41〜55 の `_CHECK_KEYS` は旧14件。
- :57〜62 の `_PATCH_PATHS` は旧4本。
- :562〜568 の witness 対象は旧3負例。
- :981〜983 は旧 JSON と旧 driver を比較する。

新 patch を glob して上の集合に加える構造ではない。したがって新 patch の追加だけでは、この三面は赤にならない。plan:146 は旧 driver 無変更を明記しており、旧 driver の変更提案も確認できなかった。

D2134項5・却下事項、および設計§12の旧14 check・旧 patch sha 保持と整合する。

**是正案（逐語）**

> 「旧 `test_mocc_proof_surface.py` の14 check・4 patch・3 witness は変更しない。新 patch の一意 witness と新 JSON の検査は新 test に置き、旧 test は回帰確認として走らせる。」

## 所見 4: 過剰機構と必要な追加を区別すべき

**判定: 一部 real／should。**

DW-G05（`docs/dev-wave/core.md:80〜88`）に照らした結論は次のとおり。

| 要素 | 判定 |
|---|---|
| P7 の atomic JSON 保存 | 維持可能。plan:283 は benchmark 後・verifier 後の部分証拠保存に限定しており、job kill 時の調査に直接効く。resume 機構まで拡張しない |
| P6 の regime 分割 | 先行実装は不要。ただし brief:46、plan:528 は既に不足実測後に限定しているため、「先回り実装している」という批判は refuted |
| 新 `_verify` | 必要。旧実装は timeout=300、結果を縮約し、例外化する（旧 driver:387〜414）。900秒と raw record 保存を要求するならそのまま再利用できない |
| `all_runs_other_integrity_clean` | 必要性あり。設計:203〜204 の全走要件を表す。候補32名は上限契約ではなく、存在・完走 check に期待値を混ぜないための追加1名は説明可能 |
| 新 test 11 node | 数だけで過剰とは言えない。設計§12の4名は候補であり、終了記録・新 verifier・gate 接続・R行集計は今回追加する挙動 |
| `legacy_proof` 内の旧14 check の写し | 削除候補。旧 JSON の参照・sha と旧 consumer に加えて第三の写しを維持する必要性が弱い |
| raw record と同じ `integrity` の重複保存 | 削除候補。plan:270,274,277〜279 は raw record と integrity を二重保持する。check は raw record を直接参照できる |

matrix／check exact node は入力由来 node に統合できるが、検査内容そのものを削る理由はない。新しい framework・汎用台帳は不要である。

**是正案（逐語）**

> 「legacy_proof は旧 JSON の path と sha に限定し、旧14 check の写しを持たない。integrity の正本は verifier.record.integrity 一箇所とする。atomic 保存は小さな保存関数に限定し、regime 分割・統合・resume は初回実装へ入れない。」

## 所見 5: 新 main に実行場所・単独性の契約が書かれていない

**判定: real／must-fix。** 放置すると新 driver の benchmark 起動条件が旧 driver より弱くなる。

旧 driver は main の冒頭で以下を行う（:609〜618）。

1. `site_policy.current_site(require_evidence=True)`
2. `refuses_heavy_work(site)` なら終了
3. `_assert_single_tenant()`
4. cache の絶対 path 検査

さらに各 run 前にも `_assert_single_tenant()` を呼ぶ（:417〜419）。plan は main と `_variant_run` を新設する（:162）が、この呼出位置を指定していない。

generic dispatch は渡された argv を clean environment・repo cwd で実行する仕組みであり（`dispatch_compute.py:154〜160,1659〜1674`）、これらの driver 契約の代用ではない。

**是正案（逐語）**

> 「新 main は依存準備・build より前に current_site(require_evidence=True)、refuses_heavy_work による拒否、_assert_single_tenant を実施する。各 benchmark 直前にも _assert_single_tenant を呼ぶ。--third-party-cache は絶対 path を必須とする。」

plan:515 の cache path は絶対 path だが、その存在・内容は本レビューでは未確認。

## 所見 6: compute 予算と consumer の順序を実施手順に確定する必要がある

**判定: real／should。**

実行順の「stock12→各負例6、benchmark/verifier直列」は source checkout の寿命と整合する（plan:173）。しかし120秒／900秒は**一走の timeout**であり、job 全体の3600秒以内を保証しない。dispatch の既定 walltime は `01:00:00`（:67）、単純最大和は36,720秒（plan:523）。20〜25分は不確実という plan の訂正は妥当。

atomic 保存で残るのは最後の保存までであり、Elapse kill 中の run に `timed_out=true` が記録される保証はない。未完了 record／欠落 run と false の `all_pass` で表現すべきである（plan:283,350）。

consumer については「必ず一度赤を踏む」は refuted。plan:384 は compute 前の明示除外を許している。ただし「できます」のままでは段6手順が確定していない。

B-3 は `patches/*.patch` 全列挙（`test_p3_s4_loop.py:7933`）なので新 patch の登録が必要。plan:483〜485 は単独焦点走を既に含めており、この点の漏れはない。260秒は旧 insight:106 の記録であり、今回の実測ではない。

**是正案（逐語）**

> 「compute 前は新 JSON consumer 一 node を明示除外して焦点走し、除外を記録する。compute 後は除外なしで consumer と関連焦点走を通し、その後に受入全走を行う。途中 JSON の all_pass は false とし、36走・exact checks・観測値再計算が揃った場合だけ true にする。Elapse kill を run timeout の観測に置き換えない。」

author 1本は契約を同時に閉じる分割として妥当。ただし「足ります」（plan:587）は時間保証としては不確実。T-2294 はfix3巡後にも受入で登録漏れが発見されている（旧 insight:69〜80）。今回の閉包漏れを段4で先に潰すことが予算対策になる。

## 所見 7: 親 brief の前提と file:line に訂正が要る

**判定: real／must-fix（P3）、その他 nit。**

- **P3**（brief:43）の cycle=3,754 は別 integrity 異常の証拠ではない。要約 JSON:123〜136 は `version_dups`／`dup_txids` を載せていない。設計:203〜204 の全走要件を外す根拠にならず、plan:338〜348 の棄却案を支持する。
- **U のR行ゼロ**（brief:33）は `non_insert_writes == txns` だけから導けない。plan:281 の直接集計が必要。
- **閉包数**（brief:18）は「5箇所＋テスト3箇所」だが、表にはproduction3 file／test4 fileがある。今回判明した同一file内のpinも追記すべき。
- plan 自身にも行参照のずれがある。旧 `_verify` は:387〜414、`_variant_run` は:417〜427、`_apply_owned_patch` は:430から。plan:155,161〜162 の参照は現物とずれる。
- plan:557 の「brief:31」は、実際にはbrief:33を指す。
- 保証名の読点差は設計:160とD2134項4に実在する。意味の変更ではなく、exact test の採用文字列を一箇所で固定すれば足りる。

**是正案（逐語）**

> 「P3を撤回し、全36走の別 integrity 異常を赤とする。UはR行数を直接記録する。閉包表を件数 pin まで更新し、file:line は現物へ合わせる。保証名は設計§6の逐語に統一する。」

## 総括

**現状の plan は閉包修正と実行入口の明文化が必要。** read-onlyで検査し、ファイル変更・pytest・build・computeは実施していない。

**(a) 削除すべき構成要素**

- `legacy_proof` に複製する旧14 check。
- `verifier.record.integrity` と重複する raw integrity。
- 新 module 名での旧 `_run_checked`／`_install_dependency` 再登録。
- 初回への regime 分割・統合・resume 実装。現planどおり不足実測後に判断する。
- atomic保存、33個目のintegrity check、必要な挙動testは削除対象としない。

**(b) 登録簿閉包の追加一覧（現物の行番号）**

plan既載分も含め、以下を閉包とする。

| file:line | 追加・訂正の逐語 |
|---|---|
| `materializer_admission.py:87` 隣 | `"orchestrator.campaign.s3_mocc_mutation_proof._build_variant": MaterializerRegistration(NON_ADMISSIBLE, "trace-only mocc mutation proof controls; never source performance values")` |
| `condition_meaning_gate.py:204` 隣 | `"IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": DefineSpec(ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe", "patches/broken-mocc-hot-update-unlock.patch")` |
| 同:269 隣 | `"IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": ("cc/mocc/transaction.cc", "#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK")` |
| `screening_driver.py:80` 隣 | `"IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK": 0` |
| `test_condition_meaning_gate.py:40,2685` | `"IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK"` |
| 同:2782 | `) == 17` |
| `condition_meaning_gate.py:12〜15` と同test:2901〜2904 | `"supply domain contains the 39 patch-derived defines"`、`"compile-time witness (15 total)"`。説明・文字列pinを同期 |
| `test_ccbench_spawn_sites.py:27,62,4112` 隣 | 新module import、`("campaign/s3_mocc_mutation_proof.py", "<module>._run_trace"): 1`、W/U四FLAGSのholdout検査 |
| 同:3466,3469 | `"proven-unreachable": 35`、`Counter({"covered": 39})` |
| 同:3493,3502 | `"proven-unreachable": 25`（両箇所） |
| `test_p3_build_authority_cli.py:164,182` 隣 | `"s3_mocc_mutation_proof.py"`、`"orchestrator.campaign.s3_mocc_mutation_proof._build_variant"` |
| `test_p3_s4_loop.py:7922` 隣 | `"patches/broken-mocc-hot-update-unlock.patch": frozenset({"IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK"})` |

**(c) 焦点走の対象 test file 集合**

すべて `orchestrator/tests/` 配下。

- `test_mocc_mutation_proof.py`
- `test_mocc_proof_surface.py`
- `test_condition_meaning_gate.py`
- `test_ccbench_spawn_sites.py` — plan列挙nodeに加え所見1のCounter関連node
- `test_p3_build_authority_cli.py`
- `test_s8b_floor_campaign.py` — materializer閉包node
- `test_p3_s4_loop.py` — B-3単独nodeを一回。変異ごとの反復には含めない

**(d) 親 brief への異議**

P3の受入緩和、R行ゼロの間接推論、閉包表の不足を修正する。P6の20〜25分とauthor1本の所要は未検証の見積とする。旧driver・旧JSON・旧patch・旧14 check、および旧proof testの固定集合は保持する。