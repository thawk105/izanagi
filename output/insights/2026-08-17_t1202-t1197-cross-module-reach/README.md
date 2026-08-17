# 8c 事前登録の到達判定を cross-module へ広げる ([T-1202] / [T-1197])

wave: `dev-wave-t1202-t1197-cross-module-reach` / 2026-08-17 / base main `5a19b8ab`

ユーザー裁定 2026-08-16 /rulings 全件 第 3 回 択 (ii)。逐語正本は
`dev-wave-jobs/rulings-inbox/2026-08-16-rulings-full3-28rulings.md` §4。

## 何が壊れていて、何を直したか

条件 12 の評価器は実 tree に対して `UNSATISFIED` / `environment-contract-consumer-absent` を
返していた。この診断は**誤り**である。reason が指す 2 つの consumer は実在し、pegasus 経路で
実際に走る。原因は条件側ではなく判定器の射程で、到達判定が同一 module 内の top-level 定義しか
辿らなかった。同じ helper を 6 条件の評価器が共有していた ([T-1197])。

到達判定を、契約が宣言する root module を起点に**実際の import 束縛だけ**を辿る canonical
`(path, 関数名)` graph へ置き換えた。結果、条件 12 は真の不足である allocation 強制の不在を
指すようになった。

| | 改修前 | 改修後 |
|---|---|---|
| C12 | `UNSATISFIED` / `environment-contract-consumer-absent` (誤報) | `UNSATISFIED` / `allocation-enforcement-consumer-absent` (真) |
| C01 / C04 / C09 / C10 / C11 | — | 変化なし |

**条件 12 は改修後も充足しない。それが正しい終状態である。** 本 wave の仕事は診断を真に
することであって条件を充足させることではない。allocation 節の縮小は対になる [T-1167] 択 (c) の
所有であり、本 wave では触っていない。

## 実測 (main `5a19b8ab` / tip `b361e277`)

- 実 tree 12 条件の走査 module 数と秒: C04=55/10.7s、C09=55/7.9s、C12=56/7.8s、他は 0〜2 module。
  `reachability-limit-exceeded` の発火は 0 件。
- repo 内 module の transitive import 閉包は 3 root いずれも 118 module。需要駆動 traversal の
  実走査は 56 以下に収まる。上限 512 はこの差を吸収する暴走止めであり、意味論的 gate ではない。
- 焦点走 489 passed in 11.43s (計算ノード dispatch)。

## 規律 2 のための証拠 — 受理集合を広げていないこと

ユーザー指示は「実在する強制が『不在』と報告されないこと」と「実際に不在なものは依然
`UNSATISFIED` になること」の**両方**を要求した。後者が抜けると受理集合が黙って広がる。

到達を広げる方向の受理規則には、次の fail-closed をすべて対にして入れた。

- callable の既定引数は witness にしない (production 経路は常に明示的に渡すため死んだ束縛)
- 代入は call を支配し、かつ関数内でちょうど 1 回でなければならない
- 位置引数と `*args` が見えた仮引数は hard-block
- import 名も local 名も binding が 1 回でなければ解決しない
- 終端 target の定義 path は契約宣言 evidence path の中に限る
- 定数偽 branch と未呼出し nested function 配下は到達から除く
- 解決不能・上限超過は到達扱いにせず fail-closed

## 変異検査

`mutation-spec.json` / `mutation-ledger-v2.json` が正本 (tip `b361e277`、全件一致)。

| 変異 | 期待 | 実測 | kill node |
|---|---|---|---|
| 判定器の版を v1 へ戻す | KILLED | KILLED | `test_decider_version_binds_cross_module_semantics_to_v2` |
| module 上限を 64 へ下げる | KILLED | KILLED | `test_production_default_module_limit_accepts_sixty_five_modules` |
| 「ちょうど 1 回代入」を外す | KILLED | KILLED | `test_callable_value_flow_failures_stay_environment_absent[multiple-assignment]` |
| 条件 9 の宣言 path 限定を外す | KILLED | KILLED | `test_c09_same_name_target_in_undeclared_production_path_is_not_witness` |
| `_declared_call` の宣言 path 節を外す | SURVIVED | SURVIVED | (等価変異) |

後段 2 件は wave 途中に実在した形である (module 上限 64 は段 2 プランの値、
「ちょうど 1 回」の緩みは fix 第 1 巡が一時的に持っていた形)。

**等価変異の根拠**: `_declared_call` には常に `probe.requirement(<kind>).path` 由来の target が
渡され、`declared_paths` は同じ契約の `evidence_paths` である。したがって
`target[0] in probe.declared_paths` は全呼び出し点で恒真であり、外しても挙動が変わらない。
条件 1 / 4 / 12 の宣言 path 限定は target の構成 (exact `(宣言 path, 名前)` の一致要求) が
担保しており、条件 9 は生きた検査が担保している (変異は kill 済み)。
probe 走 (`mutation-ledger-probe.json`) の初回結果も消さずに残す。

## 残件 (裁定パッケージ候補)

1. `_declared_call` の宣言 path 節が恒真である。挙動は変わらないので成果物への影響はゼロだが、
   読み手には効いている guard に見える。削除するか防御的冗長として明記するかは未裁定。
2. 属性名の存在を enforcement の証明として使っている (`single_process` / `allow_resume`)。
   拒否方向や契約との対応までは見ない。条件の再定式化であり [T-1167] 系の所有。
3. 判定器の版が v2 になったが、凍結記録の tip は legacy schema で `decider_version` を持たず
   引き続き発効しない。新 schema での記録発行は別 owner。
4. `PROVEN_ABSENT` と `INDETERMINATE` の status 分離。解析不能と実 consumer 不在が同じ
   `UNSATISFIED` に畳まれている。status 語彙の拡張は consumer 全層へ波及する。
5. 条件 1 の要求値 (records 1,000,000 / threads 48) と実装値 (100,000 / 4) の不一致、
   条件 4 / 9 / 10 の要求名と実装名の不一致。いずれも契約側の問題。

## land 相 (2026-08-17 08:12〜、別セッションで再開)

以上は land 保留までの記録である。保留理由は main の進行で消え、以下の経過で着地した。
この節が着地時点の正本であり、上の節と食い違う場合は**この節を優先する**。

### 保留理由の消滅 (段 1 再実測、3 点)

1. main の `DECIDER_VERSION` = `s8c-decider/v2`。[T-1167] の `9aee98f3` が本 branch と
   **同一 hunk** の v1→v2 bump を先に着地させた。
2. 凍結世代は g5 まで進み `decider_version = s8c-decider/v2` を束縛する (g4 は v1)。
3. `orchestrator/campaign/s8c_preregistration.py` は main と本 branch で blob 一致 `055666d9`。

よって本 wave は**版を据え置き、新しい凍結世代を発行しない**。
2026-08-17 のユーザー裁定 (worklog 622) が「第 5 世代を発行して完結する推奨 (a) は却下、
検証済みの改善の着地を優先」と定めており、裁定控え索引 1 が付けた条件
「t1167 が先に着地した場合は版据え置きのまま着地できる。着地直前に凍結記録の世代を再確認する」
が成立している。

### main 取り込みは意味的合成だった

両側が触った実装 file の積集合は 4 件で、`git merge` の競合は **11 hunk**
(評価器 2 / core テスト 6 / predicates テスト 3)。[T-1167] は条件 12 の allocation 節を
「実現可能な予約 binding」へ縮小し、`_c12_allocation_binding_verdict` を新設して
gate 順序を allocation 優先へ変えていた。共有 fixture `TOKEN_ONLY_C12` も両側が別目的で
作り替えていた。合成は Codex `role=author` が行い、merge commit は `47146d74`。

**親の裁定 2 件 (R3 / R4) は撤回した。** 親は当初「gate 順序は本 wave 側 (env/guard 優先) を採る」
「allocation gate の射程も cross-module にする」と裁定したが、local main には
`test_c12_allocation_binding_gate_precedes_environment_gate` (両 consumer 不在なら reason は
allocation) と `test_c12_allocation_binding_helper_rejects_check_without_read_binding`
(helper の signature を固定) という [T-1167] の専用テストが実在し、
R3 / R4 はこの 2 本を書き換えないと成立しなかった。しかも R3 / R4 は
**実 tree の判定を 1 つも変えない**。別タスクが着地させた設計判断を、効果ゼロで反転させる
裁定だったので撤回した。撤回後は [T-1167] の C12 構造をそのまま保持し、本 wave の
cross-module 機構をその後段に置いた。

### 着地時点の実 tree の姿

- 条件 12 は `UNSATISFIED` / `allocation-enforcement-consumer-absent`。**これは main が
  [T-1167] の着地時点で既に返していた値と同じ**である。main の第 1 gate が要求する
  `read_binding` / `check_reservation` は `p3_autonomous_workload_trial.py` に 0 回しか
  出現せず、module-local 到達集合に入りえないためである。
- **cross-module でも到達しない**ことを独立に全件探索で確認した。この 2 関数の repo 内呼び出し点は
  `s8b_oracle_driver.py:920-921` (囲み `_prepare_v2_execution`) と
  `s8b_floor_campaign.py:5644-5645` (囲み `_run_campaign_core`) だけで、前者を import する
  production module は 0 件、後者の production importer 3 件はいずれも当該関数へ届かない。
  よって main の allocation 診断は真であり、誤診断ではない。
- 12 条件の status / reason は着地前後で 1 つも変わらない。

**訂正**: 親は当初「cross-module 機構は C01 / C04 / C09 で実 tree に走る」と書いたが誤り。
`s8c_preregistration_evidence.py` の C01 は `workload-projection-mismatch` を返して early return し、
その次行の `_ReachabilityExplorer` に到達しない。**実 tree で cross-module 走査が現に走るのは
C04 と C09 の 2 条件だけ**である。条件 12 では allocation gate が先に確定するため走らない。

### では本 wave は何を着地させたのか

観測値は変わらない。着地させたのは、**6 条件が共有する到達判定 helper の射程**である
(ユーザー裁定の逐語が名指しした対象、[T-1197])。[T-1167] は条件 12 の allocation 節を
**実現可能な**形へ縮小した。それが満たされた瞬間に評価は env/guard gate へ進み、
そこが module-local のままなら `environment-contract-consumer-absent` の誤診断が再び出る。
**それを防ぐのが本 wave の寄与**である。効果は今日の観測値にではなく、
allocation が満たされた将来の木に現れる。

### 段 6 敵対レビュー 2 レンズと裁定

レンズ A (受理集合と正しさ防壁) は NO-GO で must-fix 4 件、
レンズ B (合成の取り残しと consumer 波及) は GO で must-fix 0 件。

| 所見 | 裁定 | 根拠 |
|---|---|---|
| A-01 裸名照合で未束縛・dead・nested の同名 call を誤認 | scope 外 | 該当は local main の `_c12_allocation_binding_verdict` / `_called_names`。本 wave は未変更 |
| A-04 decorator 置換を無視 | scope 外 | `_functions` の扱いは local main と同一 |
| A-02 dead 枝の除外が不完全 | 採用・修正 | 本 wave の新設規則の穴。狭める方向 |
| A-03 終端 target の所有が固定されていない | **処方を反証・別タスクへ** | 下記 |
| B-1 snapshot 補助が campaign 規模に比例し 5 回重複 | 採用・修正 | 本 wave が持ち込んだ成長比例コスト |
| B-2 親の検証範囲の記述が誤り | 記録側で訂正 | 上記「訂正」節 |
| B-3 `_attributes` が無参照 | 採用・削除 | local main では参照あり、本 wave の cross-module 化で dead に |

**A-03 の処方は実測で反証された。** 「終端 target の定義 path を条件自身の宣言 path へ限定する」
案を適用すると、条件 9 の正規 target `assert_campaign_layer3_chain` は
`autonomous_trial_completeness.py` すなわち**条件 10 の宣言 path** にあるため target が 0 件になり、
条件 9 の reason が `formal-acceptance-layer3-consumer-absent` から
`layer3-producer-unreachable` へ変わる。契約は正当に別条件の宣言 path にある consumer を
参照している。所見自体 (別条件の宣言 path に置いた同名 decoy で cross-wire できる) は real なので、
「終端 target を契約が名指しする所有 path へ束縛する」別設計として新規タスクへ送る。
fix 子は停止条件に従って実装せず報告し、親が裁定した。**この巡も子が正しかった。**

### 成長比例コストの除去 (B-1)

`_snapshot_current_commit` は `orchestrator/campaign/` 配下の tracked な `.py` を**全件** archive して
展開し、それを 5 箇所が別々に呼んでいた (139 file x 5 = 695 file 展開)。改修前は契約宣言 path
だけを写していたので、この成長比例コストは**本 wave が持ち込んだ**ものである。
module scope fixture で 1 回だけ生成して共有し、archive 対象を
「契約 + 宣言 evidence + 評価器が実際に読んだ中継 module」の閉包 **57 file** へ限定した。
共有 tree を使う 5 テストはいずれも読み取り専用で変異漏れはない。
焦点走は 540 passed / 47.01s から **544 passed / 45.35s** になった (テストが 4 本増えて時間は減)。
実時間の短縮自体は小さいが、campaign module が増えても展開量が増えない形になった点が本質である。

### 変異検査 (着地版)

`mutation-spec-v3.json` / `mutation-ledger-v3.json` が正本 (tip `44213350`、rc=0、全件一致)。
**KILLED 7 / SURVIVED 1 / MISMATCH 0**、期待 node 完全集合 36 件が実測と完全一致。
`DW-M07` に従い、probe 走 (`mutation-ledger-probe-v3.json`) を全件 SURVIVED 期待で先に回して
観測 node を集め、その完全集合を期待値に据えてから本走した。

| 変異 | 結果 | kill node 数 |
|---|---|---|
| 判定器の版を v1 へ戻す | KILLED | 3 |
| module 上限を 64 へ下げる | KILLED | 1 |
| 「ちょうど 1 回代入」を外す | KILLED | 1 |
| 条件 9 の宣言 path 限定を外す | KILLED | 1 |
| `_declared_call` の宣言 path 節を外す | SURVIVED | 0 (等価変異) |
| **条件 12 の env/guard gate を module-local へ戻す** | **KILLED** | **23** |
| 終端文後の dead code 除外を外す | KILLED | 1 |
| literal 真偽判定を常に不明にする | KILLED | 6 |

後半 3 件は本 wave が新設した規則を **local main に現に実在する形**へ戻す変異であり、
`DW-M01` の「変異は wave 前の実コードの形を必ず含める」を満たす。
中でも env/guard gate の module-local 化は **23 node** で殺され、本 wave の中核が
厚く検査されていることを示す。版 bump 変異の kill node が 1 から 3 へ増えたのは、
合成で版 identity assertion を literal 固定側に寄せたためである。

### 上の「残件」節の更新

- 項目 2 (属性名を enforcement の証明に使う) は**消滅**した。[T-1167] が allocation 節を
  予約 binding へ縮小した際に attribute 検査ごと削除している。
- 項目 3 (凍結記録の tip が legacy schema で発効しない) は**更新**。tip は g5 で
  `decider_version = s8c-decider/v2` を束縛する。ただし `effective` は引き続き False。
- 新規: 終端 target を契約が名指しする所有 path へ束縛する設計 (A-03)。
- 新規: `_called_names` の裸名照合と decorator 置換の無視 (A-01 / A-04)。local main の性質。

## 逐語

`verbatim/` に段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、段 5 実装 2 単位、
段 6 レビュー 2 レンズ、段 6 fix 裁定、fix 4 巡の報告を置く。
land 相の逐語は `land-` 接頭辞で置く (段 4 裁定、合成、fix 3 巡、レビュー 2 レンズ)。

段 2 プランと段 6 の実装は、いずれも敵対レビュー 2 本が独立に NO-GO を出した。
fix 第 2 巡と第 4 巡では**子が親の裁定を否定して停止し、2 回とも子が正しかった**
(fixture の no-op 変異、述語節の恒真による等価変異)。実装子契約の
「期待値が誤りと判断したら実装を変えずに報告して止まれ」が現に効いた事例である。
