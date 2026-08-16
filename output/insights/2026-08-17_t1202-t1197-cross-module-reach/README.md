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

## 逐語

`verbatim/` に段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、段 5 実装 2 単位、
段 6 レビュー 2 レンズ、段 6 fix 裁定、fix 4 巡の報告を置く。

段 2 プランと段 6 の実装は、いずれも敵対レビュー 2 本が独立に NO-GO を出した。
fix 第 2 巡と第 4 巡では**子が親の裁定を否定して停止し、2 回とも子が正しかった**
(fixture の no-op 変異、述語節の恒真による等価変異)。実装子契約の
「期待値が誤りと判断したら実装を変えずに報告して止まれ」が現に効いた事例である。
