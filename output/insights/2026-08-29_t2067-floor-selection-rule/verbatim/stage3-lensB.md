結論: 段 2 プランはこのまま author へ渡せません。主な real 所見は、ratified 静的層への current-policy validator 流用、意味を証明しない版文字列検査、通常 candidate の複数 run と `{G}` introduction 契約の不整合、g2 以降の未被覆です。D1241 の non-certifying 上限は維持すべきです。pytest は実行していません。

## D1243 / D1124 / D1242 への抵触

real:

- H tree と worktree の official result 集合完全一致は、署名・nonce・予約消費・墓標を持たないため、字義上の「一回性台帳」再導入ではありません。測定開始も拒否しないので、D1124 の観測回数上限そのものでもありません。
- ただし、これは既存 provenance の再確認だけではありません。現行 closure は generation が宣言した path だけを G/H/worktree に束縛します。[`_verify_generation_semantics`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:1031) に namespace 全体の完全一致を足すと、選択済み A より後の未追跡 C を一件測っただけでも、A を使う既存 ratified consumer が拒否されます。成果物の値・参照が変わらないのに受理集合だけを狭めるため、DW-G05 上は過剰です。
- 必要なのは、H tree と worktree の和集合から `run_id <= selected_run_id` の候補を確認し、同一 path の bytes 不一致と、より早い未追跡候補だけを拒否することです。後発 C まで exact 一致させる必要はありません。
- さらに、現在の集合は削除可能です。A/B の値を見た後で A を削除し、A が H に入る前に直接 g1 を作れば、H/worktree 完全一致は B だけの集合を正当化します。plan 自身も未追跡削除を認めていますが、committed A の削除も current H tree だけでは選択集合へ戻りません。したがって、この案だけで「測定前固定を証明した」として D1241 を解除できません。
- frozen generator blob に `earliest-eligible-official-run-id/v1` が exact 1 回あることは意味検査ではありません。未使用コメントや到達不能定数でも通り、選択 equality を外しても通ります。D1242 が否定した文字列存在検査の再発です。
- 版を残すなら、g1 document に狭い `floor_selection_rule` field を追加し、その値が実際に verifier の規則 dispatch を選ぶ形にすべきです。`floor_protocol.json` を変える必要はありません。

suspected:

- namespace 全体の commit barrier は測定の前提条件ではないため、D1124/D1125 への直接違反とは断定しません。しかし各観測のたびに bytes を Git tree へ入れるまで強い consumer を止めるため、D1125 の「commit ID と環境条件で足りる」を越える運用です。この一般 barrier を残すならユーザー裁定が必要です。

## 過剰実装の摘出

| 層 | 抜いた場合に通る入力 | 判定 |
|---|---|---|
| candidate | fully eligible な A/B があり、caller が later B を指定。現行 [`_validate_floor_inputs`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1348) は B 単体を通し、candidate B を返す | 必要 |
| `_verify_generation_semantics` | A/B を G に入れ、candidate を経由せず `floor_source=B`、`floor=project(B)` の g1 を批准。`load_ratified_freeze` と load-only consumer が通る | 必要。ただし current validator は呼ばず、H-pure な選択検査に限定 |
| `_launch_validate` | `RatifiedFreeze(...)` を直接組み、loader を迂回した B を渡す | 過剰。型の契約は「任意 Python への偽造耐性を持たず、production は loader 経由のみ」と明記されています。[型契約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:747)。選択だけを重ねても approval、pointer、generation semantics の他の迂回は残ります |
| 版文字列 exact 1 回 | 意味上は同じ選択が行われるが、unused literal の有無だけが違う g1 | 削除。成果物の値・実効受理集合を正当に区別しない |
| namespace 全体 exact 一致 | selected=A のまま、未追跡の後発 C が存在 | 過剰拒否。A の値・参照は不変 |

候補、ratified static の二層と projection equality は残し、launch の重複 predicate と版文字列 scan は削るべきです。

## 既存 test への影響

real:

- [`build_production_emitter_g1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_freeze.py:940) は result を line 1015 で取得しますが、g1 更新は [`floor_source` だけ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_freeze.py:1100) で、`floor` は v1 の値を継承しています。
- 独立 fixture も同じで、[`gen_doc.update`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_verify.py:638) に `floor` がありません。
- したがって `floor = project(result["floors"])` への追随は期待値緩和ではなく、production 正規形への修正です。ただし production の `_project_floor_for_freeze()` を fixture の期待値生成にも使う案は緩和になります。helper の誤変異を fixture と verifier が同時に追随するためです。test-local な独立投影で `diagnostics` を除外し、`by_holdout` を明示構築すべきです。
- 版文字列検査を採ると、主要 fixture の generator は [`b"# deterministic generator fixture\n"`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_freeze.py:597) なので、floor 修正より先に全 load 正例が落ちます。この行は plan の編集範囲 `940-1172` 外です。
- `test_s8b_ratified_freeze.py:2286-2294` は実在し、実際に generator/floor source stub を使う [`build_valid_semantic_g1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_freeze.py:1321) を呼んでいます。
- plan が挙げた個別行番号はすべてファイル内に実在します。ただし広い範囲表記は閉包として不完全です。特に g2 builder は [`g2.update`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_freeze.py:1248) でも `floor_source` を替えながら `floor` を替えていません。g1 専用なら既存テストは閉じますが、g2 以降の再凍結は閉じません。

suspected:

- fixture 追随後の実行結果は未確認です。pytest は実行しておらず、緑とは判定しません。

## pin 閉包

real:

- `floor_protocol.json` は 18 key、SHA-256 `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac`、`holdout_freeze.json` は `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` でした。両方とも dirty ではありません。
- 両 artifact の exact pin は [`test_frozen_artifacts.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_frozen_artifacts.py:41) に実在します。
- holdout/ratified source path を走査する検査は次のとおりです。
  - protocol path assignment exact 1 回検査: [`test_s8b_protocol_builder.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_protocol_builder.py:1228)
  - perf API の reviewed-file inventory と AST predicate: [`test_official_perf_closure.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_official_perf_closure.py:44)
  - historical generator metadata hash は存在しますが、current worktree source の不変 pin ではありません。
- 新しい private 関数や無関係な定数を追加しただけで落ちる、関数一覧 exact test や current source hash pin は見つかりませんでした。
- `tools/check_docs.py` に両 production file 固有の内容契約はありません。production schema field を増やさない現 plan なら追随不要です。
- acceptance duration ledger は全 node exact 台帳ではなく、[`90% coverage gate`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_acceptance_schedule_order.py:660) です。新規 9 node をただちに登録する義務はなく、land 側 updater の対象です。静的計画段で所要値を作るべきではありません。

## historical 経路

real:

- historical と current の分離は既に `_launch_validate` 内にあります。`LaunchValidatedFreeze` のときだけ current policy を解決し、`ReverifiedFreeze` では `expected_policy=None` です。[分岐](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:3195)
- `launch_validate` と `reverify_published_freeze` は同じ core を異なる resolver/result type で呼びます。[current](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:3496)、[historical](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:3506)
- 一方 `load_ratified_freeze` から呼ばれる `_verify_generation_semantics` には current/historical の情報がありません。[loader](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:1366)
- holdout 側 `_validate_floor_inputs` は固定 `FLOOR_PROTOCOL_REL` と current build admission policy を無条件に使います。[固定 protocol](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1362)、[current policy](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1473)
- よって `_verify_generation_semantics` からこれを呼ぶと、historical reverify に入る前の loader で current policy 拒否になります。`historical=False` という bool 一点では、generation 固有 protocol path、contract resolver、recorded policy の三差分を表現できません。

修正案は、loader では H blob の path/full protocol hash/reported eligibility/選択 identity/projection だけを検査し、current または historical の full eligibility は既存 `_launch_validate` に残すことです。current policy が進んだ状態でも `load_ratified_freeze -> reverify_published_freeze` が通る回帰 test が必要です。

## 親 brief への所見

real:

- P1: `run_id` の時刻は result 値より前に確定します。campaign は [`started_at` から run_id を生成](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_floor_campaign.py:7157) し、certificate を [`測定前に発行`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_floor_campaign.py:7267) しています。同一 full protocol なら文字列最小も時刻最小です。
- ただし P1 の一般化は過大です。eligible 集合が current policy とファイル削除で変わるため、規則の結果は歴史的に安定しません。
- P2: candidate だけでは直接 g1 に迂回できるため、candidate と ratified static の二境界は必要です。三つ目の launch 重複は不要です。
- P3: `floor_protocol.json` を変えずに済む点は正しいです。ただし generator source の unused literal を事前登録証拠にする部分は不成立です。generation document の rule fieldと実 checker dispatch の結合を推奨します。
- official result は全 output 配下で 0 件でした。`output/env/pegasus/calibration/s8b-floor-official/` は不在です。
- floor submission attempt は `output/env/pegasus/floor/attempts/submissions/` に 3 ディレクトリありました。candidate/budget approval namespace は不在でした。
- 親が名指した二 worktree はともに基準 commit `d03855e9...` で、paper-story 側の dirty は `docs/paper-story/README.md` のみ、T-2049 は clean でした。plan の production/test 6 fileとの重複は 0 です。

suspected:

- 「稼働 wave 全体がその二件だけ」という過去時点の process inventory receipt は brief に無く、現在は PID が消えているため独立再現できません。名指された二 worktreeとの path 重複 0 は real、過去の全稼働集合が完全だったという一般化は未確認です。

## 層の網羅と scope 外

plan が入れた層:

- candidate builder と `generate-v2-g1-candidate` CLI
- `load_ratified_freeze` の static generation semantics
- `_launch_validate` を共有する current launch と historical reverify
- g1 の floor source identity と floor projection

実際に影響を受けるが、plan が明示していない層:

- load-only の oracle manifest producer: [`build_approved_manifest`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_oracle_manifest.py:1198)
- s8c の `verify_floor_bytes` と publish 再確認: [`s8c_result_judge.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8c_result_judge.py:2103)
- s8c budget reservation の ratified input: [`p3_autonomous_workload_trial.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/p3_autonomous_workload_trial.py:4640)
- oracle report/judge/verdict の historical reverify 経路
- g2 以降。launch は generation 1 だけを受理しますが、loader と s8c は g2 を受理します。現 plan の「g1 専用」では D1241 が列挙する再凍結・8c 公開物全体を certified に戻せません。

裁定パッケージ候補:

1. g2 以降も同じ rule fieldと選択/projectionを必須にするか、g2 以降を non-certifying のままにするか。
2. 過去に存在したが削除された result を集合へ戻す authorityを作るか、削除攻撃を残余として D1241 を維持するか。
3. C07 の provenance-only loader にどこまで eligibility を課すか。current policy を課す案は historical と両立しません。
4. 通常 candidate で複数 run を扱う際の closure/G topology。非selected artifact を先に HEAD へ入れると、後段の [`introduction set == {G}`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:3408) を満たせません。plan の「全 run を commit してから candidate」はこの契約と矛盾します。

## 変異事前登録の妥当性

全 9 件とも変異対象コード自体はまだ存在せず、現時点で実在するのは挿入先 symbolだけです。author 後に exact 置換一意性を再確認する必要があります。

| # | 判定 | 理由・再照準 |
|---:|---|---|
| 1 `min-to-max` | 採用候補 | fully valid A/B、selected B。正規版だけ mismatch、変異版だけ candidate を生成する。単一理由にできる |
| 2 `drop-candidate-check` | 採用候補 | 同じ A/B で candidate の受理集合が変わる。後段を呼ばない node に限定する |
| 3 `drop-generation-check` | 採用候補 | 直接 g1 Bを `load_ratified_freeze` だけへ渡す。launch を呼ばなければ後段 mask はない |
| 4 `drop-launch-check` | 登録から除外 | 通るのは契約外の手作り `RatifiedFreeze`。任意 Python 偽造を保証しない既存契約を一 predicateだけ部分強化する |
| 5 `skip-untracked-results` | 条件付き再照準 | 通常の未追跡 A は既存 repository scan/closure が後で拒否し得る。`.git/info/exclude` で隠した fully valid A を使い、正規版だけ filesystem enumeration で拒否、変異版は本当に candidate を生成する fixture にする |
| 6 `trust-reported-eligible` | 除外・再照準 | broken A=true では正規版も変異版も拒否し、reason が変わるだけ。`invalid earlier を fail-closed で拒否` を `continue` に変え、baseline reject / mutant accept になる operatorへ替える |
| 7 `drop-floor-projection` | 採用候補 | source A、floor B の直接 g1を loaderだけへ渡す。selection は通り、projectionだけが落とす |
| 8 `drop-rule-version-pin` | 除外 | unused文字列の診断感度しか測らず、意味・選択値を変えない |
| 9 `ignore-enumeration-shift` | 条件付き再照準 | second scanへ「selected より早い、ignore 済み fully valid A」を注入する。通常 fileでは後続 closure が maskするため不十分 |

追加すべき変異候補:

- historical reverify へ current policy を誤流用する変異
- ratified static の H tree/worktree relevant-earlier union の片腕を落とす変異
- result/manifest/journal の検査後 recapture を落とす TOCTOU 変異

## 総括

段 2 プランは差し戻しです。段 4 では最低限、次へ修正すべきです。

- candidate と ratified static の二層に限定し、`_launch_validate` 重複を削る。
- frozen source の版文字列 scan を削り、必要なら generation rule fieldを実 checker dispatchへ結合する。
- loader から current `_validate_floor_inputs` を呼ばず、H-pure な recorded-fact selectionにする。
- namespace 全体 exact 一致をやめ、selected より早い候補に必要な範囲だけを H/worktree union で検査する。
- 通常 candidate の複数 runと `{G}` introduction の矛盾、g2 以降、削除済み result authorityを裁定へ返す。
- fixture の floor は test-local 独立投影で直し、production helperを期待 oracleに使わない。
- 変異 4、6、8 を外し、5、9を maskのない入力へ再照準する。

削除履歴を閉じる authorityと g2 方針が決まるまでは、D1241 の advisory / non-certifying 上限を解除できません。