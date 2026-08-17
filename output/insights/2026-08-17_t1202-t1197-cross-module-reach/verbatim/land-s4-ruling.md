# 段 4 裁定 (再開セッション) — [T-1202] / [T-1197] cross-module 到達判定の land 相

裁定: 2026-08-17 08:50 JST / 親 (claude) / base: branch tip d61aab21, local main 66801060

## 前提の再実測 (DW-S01「brief 前に承認済み裁定の前提を実測する」)

### 保留理由は消滅した (3 点、すべて実測)
1. main の `DECIDER_VERSION` = `s8c-decider/v2`。[T-1167] の `9aee98f3` が branch と**同一 hunk**の
   v1→v2 bump を先に着地させた。
2. 凍結世代は g5 まで進み `decider_version = s8c-decider/v2` を束縛。g4 は v1。
3. `orchestrator/campaign/s8c_preregistration.py` は main と branch で blob 一致 `055666d9`。

裁定索引 1 の「注意」(t1167 が先に着地すれば衝突が消える) が現実化した。
**版 bump の取り下げも追加 bump も不要**である。

### 新事実 A — main 取り込みは意味的合成である
両側が触った file の積集合 4 件、`git merge --no-ff --no-commit main` で**競合 11 hunk**
(evidence 2 / core test 6 / predicates test 3)。実装面の合成なので Codex `role=author` が必須。

### 新事実 B — C12 の観測値は main 側で既に真になっている
本 wave が実 tree で変える判定は C12 ただ 1 つ (wave 自身の段 1 前実測と段 5 後実測が一致)。
[T-1167] の main 側 evidence.py 差分は `_evaluate_c12` と新ヘルパのみで、C01/C04/C09/C10/C11 の
評価器を触っていない。main の新第 1 gate が要求する `read_binding` / `check_reservation` は
`p3_autonomous_workload_trial.py` に **0 回**しか出現せず、module-local 到達集合に入りえない。
→ main は既に C12 = `allocation-enforcement-consumer-absent` を返す (演繹的に確実)。

### 新事実 B は裁定を覆さない (一次資料で確認)
確定裁定 (2026-08-16 /rulings 第 3 回 択 (ii)) の逐語:
「誤報の原因は判定器の射程不足であって条件側ではない。**同じ helper を 6 条件の評価器が
共有しているので C12 固有の問題ではない ([T-1197])**。」
→ 裁定の対象は共有 helper の射程であり、main はそれを直していない (今も module-local)。
実現済みなのは C12 の観測値 1 点だけ。**wave の目的は未達であり、着地させる。**

### 新事実 C — cross-module でも allocation は不到達 (独立 subagent が全件探索)
`read_binding` / `check_reservation` の repo 内呼び出し点は `s8b_oracle_driver.py:920-921`
(囲み関数 `_prepare_v2_execution`) と `s8b_floor_campaign.py:5644-5645` (囲み関数
`_run_campaign_core`) のみ。`s8b_oracle_driver` を import する production module は 0 件。
`s8b_floor_campaign` の production importer 3 件はいずれも当該関数へ届かない。
出発点 3 file に `importlib` / `__import__` / module dispatch な `getattr` は不使用。
→ **cross-module に広げても allocation gate は真の UNSATISFIED のまま。**

## 裁定

### R1 — 版は v2 のまま据え置き、追加 bump も世代発行もしない
main が既に v2、g5 が v2 を束縛。branch の 2 行差は merge で消える。
**正本 doc・証拠契約 JSON・凍結記録を一切触らない** (本 wave の不変条件であり、g5 の pin 対象)。

**裁定の逐語との突き合わせ (2026-08-17 08:40 JST、着地済み main 699c9cae の worklog 622)**:
本文は「推奨 (a) 第 5 世代を発行して完結、は却下。検証済みの改善の着地を優先する」であり、
`DECIDER_VERSION` を v1 へ戻せとは書かれていない。inbox 控え索引 1 の
「実務上の含意: 択 (b) 相当 (版上げを取り下げて着地)」は g5 が無く main が v1 だった時点の記述で、
同じ控えが「t1167 が先に着地した場合、本 wave は**版据え置きのまま**着地できる (衝突が消える)。
着地順に依存するので、着地直前に凍結記録の世代を再確認すること」と条件を付けている。
その条件は本節冒頭の 3 点実測で成立済みである。

したがって v1 への差し戻しは行わない。行えば (1)「版据え置き」に反し、
(2) 別タスク [T-1167] が着地させた変更を本 wave が取り消すことになり、
(3) g5 が v2 を束縛しているため `test_s8c_preregistration_invariant.py` が赤になる。

(peer session `cleanup-branches` から 08:38 JST に「v1 へ戻して land せよ」という派生指示が
届いたが、上記のとおり stale であるため実行せず、実測根拠を返信した。)

### R1b — 限界宣言は既存慣行で書き、新機構を作らない
裁定索引 1 は「受諾を機械可読な限界宣言として残すこと」を求めている。
調査 (独立 subagent) の結果:
- D458 決定 (1) を機械強制する検査は repo に**存在しない**。
- `docs/decisions.md` の D458 本文自身が「受理意味を変えたのに bump しなかった場合は検出しない。
  bump 忘れは裁定が受け入れた手動 provenance の範囲に残る」「bump 忘れを機械検出する
  module 変更 gate を足す — bytes 凍結の再導入であり裁定に反する」と明記している。
- 設計規範一般への受諾済み逸脱を登録する汎用 registry は存在しない
  (最も近い `tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` は provenance 限定)。

よって新機構は作らず、D458 自身が使っている既存慣行 — decisions の
「この決定が保証しないこと」節 — として wave の decisions fragment に書く。
新しい pin・署名・束縛機構を作らないことは、同じ裁定の理由 (版の厳密な前進に費用を払わない) と
2026-08-12 の既定方針にも整合する。

### R2 — allocation の**述語**は main のものを採用する
`_c12_allocation_binding_verdict` が要求する `{"read_binding","check_reservation"}` と
`allocation_consumer` の定義検査は [T-1167] の裁定 (択 (c) 実現可能な予約 binding へ縮小) の
所有面である。**述語の中身を変えない。** branch 側の `single_process_required` +
`{"single_process","allow_resume"}` attribute 検査は main が削除済みであり、**復活させない**。

### 【撤回】R3 / R4 は 2026-08-17 08:45 JST に親が撤回した

撤回理由 (親が段 5 成果物の実測で発見):
local main には [T-1167] が着地させた専用テスト 2 本が実在する。
- `test_c12_allocation_binding_gate_precedes_environment_gate`
  — 両 consumer 不在の木で reason が `allocation-enforcement-consumer-absent` になることを固定。
  すなわち「両 gate が落ちるときは allocation が勝つ」は意図的な設計でテスト済み。
- `test_c12_allocation_binding_helper_rejects_check_without_read_binding`
  — `_c12_allocation_binding_verdict(supervisor, allocation)` を直接呼び signature を固定。

R3 / R4 はこの 2 本を書き換えないと成立せず、段 5 の成果物は実際に 2 本を削除していた。
これは「既存テストの期待値を変更しない」規律の違反であり、別タスクが着地させた設計判断を
本 wave が黙って反転させる行為である。しかも R3 / R4 は**実 tree の判定を 1 つも変えない**
(新事実 C: `read_binding` / `check_reservation` は cross-module でも不到達)。費用だけで効果が無い。

さらに、本 wave が足した entrypoint 検査 (`main` 関数の存在と `main -> run_trial` 到達) を
allocation gate より前に置くと、main のテスト fixture (`def run_trial(): return None` のみで
`main` 関数を持たない木) が先に引っかかり期待 reason が変わる。

**訂正後の方針**: [T-1167] の C12 構造 (allocation を第 1 gate、helper は main の signature と
module-local 判定のまま) を完全に保持し、本 wave の cross-module 機構は**その後段**に置く。
本 wave が触るのは env/guard gate の到達判定だけとする。

これで wave の寄与は失われない。allocation gate は [T-1167] が「実現可能な予約 binding」へ
縮小した結果、将来満たされうる。満たされた瞬間に評価は env/guard gate へ進み、そこで
module-local 判定なら誤診断 `environment-contract-consumer-absent` が出る。**それを防ぐのが
本 wave の寄与**であり、順序を変える必要はない。

--- 以下は撤回前の記述 (履歴として残す) ---

### 【撤回済み】R3 — gate の順序は branch 側 (env/guard → allocation) を採る 【(P1) 攻撃対象】
main は allocation を第 1 gate に置いた。そのまま採ると実 tree では cross-module 判定に
**到達しない**ため、裁定が求めた「実在する consumer を不在と報告しない」ことを
**実 tree で示せなくなる** (合成 fixture でしか発火しない = 本 wave が潰しに来た
「謳うだけで発火しない保証」と同型)。
branch の順を保てば実 tree は env/guard gate を cross-module で通過し、allocation gate で
真の不在に当たって停止する。終状態の reason は main と同一で、単一理由性 (DW-M03) も保たれる。
- 受理集合への影響: 両順序とも実 tree の終状態は `allocation-enforcement-consumer-absent` で不変。
  順序が結果を変えるのは「両 gate が同時に失敗する木」だけで、実 tree はそれに該当しない。

### 【撤回済み】R4 — allocation gate の到達判定も cross-module にする 【(P2) 攻撃対象】
[T-1197] の裁定対象は共有 helper の射程そのものである。allocation gate だけ module-local に
残すと同じ誤診断の型が C12 に残る。新事実 C により、cross-module にしても実 tree の verdict は
変わらない (不到達のまま) ことが実測済みなので、受理集合を広げる危険がない。
- 述語 (要求する関数名の集合) は R2 のとおり main のまま。変えるのは到達判定の射程だけ。

### R5 — 版 literal の扱いは混合とする
- **report が返す版の identity assertion は main の literal `"s8c-decider/v2"` を採る。**
  branch の `recorded_version` 動的比較は、record 生成側も `DECIDER_VERSION` を使うため
  版 drift を捕まえられない (段 3 レンズ A の T-01「恒真化」)。
- **不一致 fixture の値生成は branch の `_different_decider_version()` を採る。**
  main の literal `"s8c-decider/v3"` は将来 v3 へ bump した瞬間に「不一致」でなくなり fixture が壊れる。
- `test_decider_version_binds_cross_module_semantics_to_v2` (両側にある literal pin、
  変異 m12 の kill node) は保持する。

### R6 — 共有 fixture `TOKEN_ONLY_C12` は main を土台に branch の形を足す
R3 の順序でも allocation gate は最後に来るので、実 tree 相当の positive fixture は
main が入れた `read_binding` / `check_reservation` 呼び出しを**持つ**必要がある。
main 側本文を土台に、branch 側の cross-module 構造 (`from . import env_contract,
execution_guard` と alias 経由の呼び出し) を重ねる。
- branch が `single_process_required` を前提に作った負例は R2 で述語が消えたため
  **そのままでは宙に浮く**。main の述語に対応する負例へ作り直すか削除するかを実装子に洗い出させる。
- `.replace()` ベース変異の no-op 全件検査 (段 6 第 3 巡で常設した `:936` / `:938` の assert) を
  合成後も維持し、全 param で再検査する。

### R7 — 成果物影響 (DW-G05)
本 wave を着地させなくても、実 tree の certified 選択・ActivationReport の
status / reason は **1 つも変わらない** (C12 は main が既に同じ値を出す)。
着地で変わるのは:
1. ActivationReport の `evidence` ref — 判定に効いた blob が report に載る (= reflux golden digest が変わる)。
2. 6 条件が共有する到達判定の射程 — module-local から cross-module へ。
   これが裁定 ([T-1197]) の直接の対象である。
3. 評価器の検出力 — 負例テストと変異 matrix (KILLED 4 / 等価 1)。
着地しない場合: 共有 helper は module-local のまま残り、C12 以外の条件でも
「実在する consumer を不在と報告する」型の誤診断が発生しうる状態が続く。

### R8 — scope 外として裁定へ返す所見
なし。R3 / R4 は本 wave の裁定対象 ([T-1197] の共有 helper 射程) の内側と判断した。
ただし R3 / R4 はいずれも設計択一であり、段 6 の敵対レビュー 2 レンズの必須 scope に入れる。

## 段の進め方

`4 → 5 → 6 → 7 → 8 → 9`。軽量版は採らない (正しさ防壁に触り、設計択一が割れるため
DW-C00 により敵対検証子を省かない)。

- 段 5: Codex `role=author` 1 単位。競合 11 hunk の解決 = 4 file を同時に触るので分割不能。
- 段 6: 敵対レビュー 2 レンズ (R3 / R4 の順序・射程の択一を必須 scope に含める) + fix 巡 + 変異 matrix 再走。
- golden digest: 親が実走して実測値を得てから、実装子に書かせる (親は実装面を編集しない)。
