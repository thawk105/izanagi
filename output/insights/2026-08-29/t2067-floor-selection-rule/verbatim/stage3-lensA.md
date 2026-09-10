結論から言うと、段 2 プランはこのまま author 段へ渡せない。`min(run_id)` という数学的規則自体は floor 値を読まないが、現計画は「run_id と eligible 集合が値を見る前に確定した」ことを証明できず、さらに earlier result の未検証 field を書き換えて選択集合から除外できる。D1241 の上限は解除不可である。

## 値盲性

real

- production の正規経路では、fresh run の `started_at` は既定の UTC 時計から一度取得され、同じ値から `campaign_run_id`、directory、certificate が作られる。public `run_campaign` は `now_fn` 注入を拒否し、注入された private run は `eligible_for_refreeze=False` になる。[s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_floor_campaign.py:6945) [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_floor_campaign.py:7157) [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_floor_campaign.py:7267)

  成果物影響: 正規 producer だけを誠実に使う限定モデルでは、`run_id` はその run の floor 値より先に決まる。

- しかし candidate 資格検査は launch certificate を一度も検証しない。実際、既存の通る candidate fixture は `launch_certificate.json` に `{}` を書いている。[s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1348) [fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/s8b_v2_freeze_fixture.py:456)

  成果物影響: candidate と、計画どおり `_validate_floor_inputs` を使う静的批准検査は、値確認後に付けた directory timestamp を「起動前 identity」として受理できる。

- full `_launch_validate` は certificate、journal、path の時刻一致を検査するが、検証対象は相互整合だけである。certificate validator は現在時刻、署名、発行者を検査せず、`clean_scan_digest` も historical validation では形しか見ない。コード自身も C<G は Git 内の記録順だけで実時間順を保証しないと明記する。[s8b_launch_cert.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_launch_cert.py:50) [s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:3040)

  値確認後の seam は、A/B の値を見た後に、選んだ result を任意の過去 timestamp の path へ置き、整合する certificate、journal、admission identity を再構成し、certificate を C、result を G に順次 commit する経路である。live admission inspector も、削除後に同じ bytes を再構成する攻撃を検出しないと明記する。[s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_admission.py:5687)

  成果物影響: 実際には later B でも、earlier-looking `run_id` を後付けして certified source、レポート、台帳の参照先にできる。

- よって `earliest-eligible-official-run-id/v1` は、固定済み artifact 集合に対する純粋関数としては値盲だが、システム全体としての値盲性は未成立である。親 brief の P1 は条件付きでしか正しくない。

suspected

- certificate 時刻に clock rollback や複数ノード間の時計逆転を拒否する検査もない。ただし Pegasus 上で実際にその操作または十分な時計逆転が可能かは未確認である。

## 恒真化と負例の有効性

既存正例は official result が一件だけなので、selection equality はすべて恒真である。非恒真性は二件以上の負例に全面依存する。

| 負例 | 先に落とす既存 gate | 判定 | 成果物影響 |
|---|---|---|---|
| 1. candidate で fully eligible A/B から B | A の hit artifact が captured HEAD に無ければ `_measurement_closure` が先に拒否する。プランどおり A と関連 hit を HEAD に入れれば既存 rejection はない | 条件付きで有効 | 正しく構成すれば candidate 選択 predicate の受理集合差を実証できる |
| 2. 同値 A/B から B | 1 と同じ。値が同じことによる既存 rejection はない | 有効 | identity 規則が数値差を読んでいないことを実証できる |
| 3. candidate を経由しない ratified g1 | `resolve_active_generation` と現行 `_verify_generation_semantics` は selection を見ず、追加 A も拒否しない | 有効 | `load_ratified_freeze` 直行の受理集合差を実証できる |
| 4. `floor_source=A`、`generation.floor=B` | transition tableは `/floor` と `/floor_source` を独立に許し、既存 equality chain は floor 投影を持たない | 有効 | projection predicate の受理集合差を実証できる |

real

- 負例 1、3、4 が正しく実装されれば、selection と ratified projection の検査全体は恒真ではない。[段2プラン](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2067-floor-selection-rule/stage2-plan.md:158)

  成果物影響: later B と source/floor 差し替えに対する実効 rejection を確認できる。

- mutation 候補 `skip-untracked-results` は、通常の untracked fully eligible A では無効になりやすい。A の manifest は holdout 三軸を含むため、selector を H-only に変えても既存 `_measurement_closure` が untracked manifest を列挙し、`_blob_at_head` で先に拒否する。[s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1640)

  ignored A なら既存 closure から外れるので有効だが、プランは単に「untracked earlier A」としか定めていない。

  成果物影響: 現記述の mutation KILL は新規 selection gate の効力ではなく、既存 closure failure を数える可能性がある。

- `trust-reported-eligible` も、壊れた A を「eligible と信じる」変異では正規実装も変異も B を拒否する。違いは `eligibility-unverifiable` と `rule-mismatch` の reason だけで、certified 受理集合は変わらない。

  成果物影響: reason 固定テストは通っても、資格再検証が unsafe acceptance を防いだ証明にはならない。

- candidate の floor は `_validate_floor_inputs` が返した投影をそのまま代入しているため、candidate 内の projection equality は構造上恒真である。非恒真検査が必要なのは手作り generation を受ける批准側である。[s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1721)

  成果物影響: candidate 側だけの projection test を強い保証に数えると、直接批准された誤った floor が残る。

追加必須の負例は次の二件である。

- earlier A の `protocol_sha256` だけを値確認後に別 hash へ変える。プランは A を別 protocol として未検証のまま除外し、B を受理する。
- earlier A の `eligible_for_refreeze` だけを `False` に変える。プランは live admission との一致を検査せず A を除外し、B を受理する。

## 絶対規律 2 と fail-closed の向き

real

- selected result に対する official path、full protocol、binary、manifest、journal、live admission、統計、`eligible_for_refreeze=True` の既存順序を維持する点は非緩和である。[s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1392)

  成果物影響: 選ばれた B 自身の異常 result が新規則によって受理されることはない。

- 一方、earlier result の集合判定は非対称である。[段2プラン](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2067-floor-selection-rule/stage2-plan.md:76)

  - full hash 不一致: 未検証のまま除外
  - reported eligibility false: 未検証のまま除外
  - reported eligibility true だが壊れている: fail-closed
  - malformedまたは読めない: fail-closed

  これは「適格集合の中だけで選ぶ」という親 brief の不変条件を満たさない。非selected A の自己申告 field が集合 membership の権威になっている。

  成果物影響: A の一 field を後から変えるだけで required run が A から B へ変わり、certified 選択と floor provenance が変わる。

- 壊れた earlier result を常に `eligibility-unverifiable` にする向きには、次の両面がある。

  - fail-closed にする: A を壊して集合から落とす攻撃を防ぐ。しかし古い schema、失われた sibling、壊れた admission 一件で、正当な later B の candidate、再凍結、s8b report、s8c publish を停止できる。監査履歴を保つ限り長期の可用性人質になる。
  - 不適格として無視する: later B は利用できる。しかし A の値を見た後に A を壊す、削除する、false にすることで B を選べる。

  成果物影響: 前者は受理集合を過剰に狭めて公開物を停止し、後者は受理集合を広げて best-of-N を再導入する。

この二択は局所 predicate だけでは同時に閉じない。少なくとも「正当に不適格な run」と「適格だった artifact の事後破壊」を区別する authority が必要であり、署名・台帳を足さないという D1243 の境界下では親裁定事項である。

- historical 問題も未解決である。`_validate_floor_inputs` は current build admission policy を hard-codeする一方、`load_ratified_freeze` は consumer 種別を知らずに `_verify_generation_semantics` を先に実行する。したがって static loader にこの validator を入れると、`reverify_published_freeze` が `expected_policy=None` を選ぶ前に current policy で落ち得る。[s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1473) [s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:1366)

  成果物影響: 過去の published freeze、report、台帳閲覧が current policy drift のため unavailable になり、規律 7 と D1245 に反する。

## enumeration 権威

real

- 現 worktreeでは次を確認した。

  - `output/env/pegasus/calibration/s8b-floor-official/`: filesystem、HEAD とも不在
  - `output/s8b-freeze-candidates/`: 不在
  - `output/s8b-freeze-budget-approvals/`: 不在
  - floor submission attempt directory: 3件、いずれも tracked
  - worktree: clean
  - 対象三 namespace は現在の `.gitignore`、local/global ignore 判定で ignored ではない
  - `output/` は広く tracked され、`output/s8b-freeze/floor_protocol.json` 等も tracked

  成果物影響: 現時点では candidate/H の official path 集合はともに空で、A/B 攻撃は blocker のため到達不能である。ただし一致は空集合による恒真であり、将来設計の証明ではない。

- candidate の filesystem 集合と批准時の H tree 集合を結ぶ記録がない。批准時に検査するのは H とその時点の worktree の一致だけで、candidate 時の S0 は generation documentへ保存されない。[段2プラン](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2067-floor-selection-rule/stage2-plan.md:17)

  成果物影響: candidate 時に存在した nonselected A を G 前に削除または未導入にすれば、批准時の集合と required run が変わり、別の certified source を参照できる。

- untracked A が批准時まで残れば H/worktree equality は正しく拒否する。しかし削除してから批准すれば両集合から消える。committed A も current H から削除した後は現計画の selector 対象外である。

  成果物影響: enumeration dirty 検査は「現在ある未追跡 A」を止めるが、値確認後の削除を止めず、proof chain の参照集合を過去から変えられる。

suspected

- 実装予定の `os.scandir` 前後検査が、directory 自体の置換や全 intermediate component の race を本当に閉じるかはコード未実装のため確認不能である。計画上は nofollow を要求しているが、実走証拠はない。

## 投影 equality

real

- `generation.floor == project(floor_source.result.floors)` は必要である。既存 equality chain の末端は `sha256(result.raw) == generation.floor_source.sha256` であり、`generation.floor` への辺はない。[s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:147)

  成果物影響: equality を足さなければ source A を正しく名指しながら、generation floor の pairs、scale_ref、scalar_alt を B へ差し替えられる。

- したがって既存 binding chain との重複ではない。既存 chain は source bytes の真正性を閉じ、新 equality はその bytes から generation document への投影を閉じる。

  成果物影響: 両方が揃うと、g1 の凍結 floor 値が選択 source の再計算済み floor 投影へ結び付く。

- ただし十分ではない。閉じないものは、source identity の事後付替え、eligible 集合の削除、certificate の実時間性、diagnostics の投影外部分、g2以降の差し替えである。後続 transition は `/floor` と `/floor_source` を引き続き独立に変更可能としている。[s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:137)

  成果物影響: g1だけに equality を置くと、後続世代または偽装された source identityを使う公開物の参照は閉じない。

## 親 brief への所見

| 項目 | 判定 | 根拠と成果物影響 |
|---|---|---|
| P1 | real: 反証 | 正規 producer 内の時刻先行は正しいが、candidate は certificate を検証せず、批准も実時間を証明しない。成果物影響: later B に earlier-looking identity を後付けできる |
| P2 | real: 必要だが不十分 | candidate と ratified loader の両方は必要。さらに full launch、historical、gN、s8c を区別する必要がある。成果物影響: g1 loaderだけ閉じても別 consumer の受理集合が残る |
| P3 | real: 機械的には可能、事前登録証明として不足 | 現 protocol は18 key、SHA-256 `261cec1c...e74aac` で、generator source hashだけの変更なら protocol bytesは変えずに実装できる。しかし launch certificate は generator hashまたは規則版を束縛しない。成果物影響: candidate生成時のコード版は記録できても、測定開始前に同規則が有効だったという proof にはならない |
| official run 0件 | real: 確認 | directory と HEAD entry がともにない。成果物影響: 現 commitでは実データを使う certified selection 自体が存在しない |
| candidate/approval directory不在 | real: 確認 | 両方不在。成果物影響: 現在の ratified g1 経路は budget blockerでも停止する |
| A-2 は s8b floor 非消費 | real: 確認 | README の唯一の floor は A4 noise floorであり、protocolも別 family。[README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/output/insights/2026-08-28_t2022-a2-certification-run/README.md:41) 成果物影響: A-2 reject値をT-2067の s8b floor 消費実績に使えない |

nit

- brief 作成時点の事実だった可能性はあるが、現在 local `main` は `164e2c35...`、review branch は `d03855e9...` であり、header の「main と同一」は現時点では成り立たない。今回の選択規則の受理集合には影響しない。

## 層の網羅と scope 外

プランが scope に入れた層:

- candidate `build_v2_g1_candidate` の selection
- ratified `load_ratified_freeze` の g1 selection と projection
- `_launch_validate` の手作り `RatifiedFreeze` 防御
- filesystem/H enumeration と局所 TOCTOU
-関連 fixture、負例、mutation

不足または scope 外として裁定へ返すべき層:

1. pre-launch authority

   generator rule versionまたは実装 commitが certificate 発行前に存在したことの束縛。現 certificate の clean scan digest は generator bytes を束縛しない。

2. earlier result の資格分類

   `protocol_sha256` 不一致と `eligible_for_refreeze=False` を自己申告だけで除外せず、正当な別 protocolまたは正当な ineligible を検証する tri-state validator が必要である。

3. candidate 集合と ratified 集合の連続性

   candidate 時の全 result path集合が記録されない問題。台帳禁止下で削除攻撃をどこまで threat model に含めるか親裁定が必要である。

4. historical reverify

   current policy を loaderへ持ち込まない API/type 分離が必要であり、プランの `historical=False` 一点だけでは call path が成立しない。

5. g2以降

   transition は floor/source の変更を許す一方、`_launch_validate` は generation 1 以外を拒否する。g1専用規則を後続世代でどう維持するか未裁定である。

6. s8c consumer

   `verify_floor_bytes` は `load_ratified_freeze` だけを呼ぶため、プランどおり static loader に検査が入れば、単純な「later B path」の g1 は拒否される。[s8c_result_judge.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8c_result_judge.py:2103)

   ただし static検査が certificate を検証しないままなら、実際の later B を earlier pathへ付け替えた floor は受理可能である。`publish_result_table` も receipt の型と current binding を再確認するだけで、loader以上の選択証明は追加しない。[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8c_result_judge.py:2166)

   成果物影響: s8c三表の metadata に、規則準拠に見えるが実時間順では違反した floor source path/hash が掲載されうる。

7. s8c production wiring

   `verify_floor_bytes`、`judge`、`publish_result_table` の production caller は依然0で、C07 evaluator自身も構造検査後に evidence undefined を返す。[s8c_preregistration_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8c_preregistration_evidence.py:2776)

   成果物影響: library predicateが強化されても、s8c official tableが final claimへ配線済みとは主張できない。

8. claim/report policy

   D1241 の advisory labelをどの loader/report/publish が解除できるかの明示 gate。コード predicate の存在だけで文書上限を自動解除してはいけない。

## 主張上限

real

この計画がそのまま landed しても、D1241 の advisory / non-certifying 上限は解除できない。

解除できず残るもの:

- 使用 run identity が測定値より前に確定したという証明
- earlier eligible A が値確認後に削除、別 protocol化、eligibility false化されていない証明
- candidate 時と批准時の候補集合同一性
- historical reverify の非回帰
- g2以降の floor/source selection
- s8c production final claim 配線
- 実 official run と budget approvalそのもの

成果物影響: floor-backed candidate、再凍結、s8b oracle/report、s8c公開表、論文主張は certified 集合へ昇格できない。

land後に安全に追加できる主張は狭く、次までである。

- 現在列挙され、selector が同一 protocolかつ eligible と分類した path集合では、最小 `run_id` 以外を g1 candidateへ渡すと拒否する。
- g1 `generation.floor` は、記録された `floor_source` の投影と一致する。
- floor 数値は s8c `judge` の数値入力ではなく、publish metadata は path/hashだけである。[s8c_result_judge.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8c_result_judge.py:1947)

## 総括

real の must-fix は四点である。

1. earlier result の full hash不一致と eligibility falseを未検証で除外しない。
2. candidateと static ratified selectorで launch certificateを検証するか、「path run_id」は実起動時刻を証明しないと主張を下げる。
3. candidate集合と H集合の非連続、および壊れた earlier resultを巡る安全性対可用性を親裁定へ返す。
4. current loaderと historical reverify、g1とgN、s8b full validationとs8c static validationを分離した適用表を作る。

負例1から4の主要部分は有効だが、`skip-untracked-results` と `trust-reported-eligible` のmutation設計は効力を再設計する必要がある。pytest、`check_docs`、acceptance は実走しておらず、緑とは判定していない。リポジトリ変更は行っていない。