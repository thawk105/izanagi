# 段 4 裁定 — [T-1202] / [T-1197] cross-module 到達判定

親裁定 / 2026-08-17 01:36 JST / base main 5a19b8ab3280f3ba607a2856c4b6402b3c869f3f

段 2 プランは **NO-GO**。両レンズが独立に同じ結論へ達し、親も中核所見を独立に裏取りした。
プラン v2 を以下に確定する。

---

## 0. 親 brief 自身の訂正 (レビューが正しい)

| 訂正 | 誤 | 正 | 根拠 |
|---|---|---|---|
| P2 のアンカー | `run_trial` の既定引数 `drive=trigger.drive_iteration` が `:2402` | `:2402` は `_run_workload` の既定引数。`run_trial` は `_DRIVE_NOT_PROVIDED` sentinel (`:2859`) + body 代入 (`:2893-2894`) | 親が実測 |
| resume 強制の行 | `p3_s4_loop_trigger_gating.py:821` | `:816` (`:821` は provenance 書込み) | 親が実測 (P-01 が正しい) |
| 成果物影響 (DW-G05) | 「certified 選択、台帳 reason_code が変わる」 | 変わるのは **ActivationReport の C12 status / reason / evidence とその digest** だけ。certified 選択と正式 trial 台帳は変わらない (trial registry は個別 reason_code を保存せず、effective 時の digest だけを持つ)。ただし将来 `SATISFIED` 終端を開く際の潜在受理集合は広がる | S-01。親が `trial_registry.py:72` と `s8c_preregistration.py:1728,1800` で確認 |
| 既存被覆 | 「cross-module 被覆 0 件」 | **predicate suite に限れば 0 件**。repo 全体には import alias / shadow / rebind resolver の既存テスト資産がある (`test_campaign.py:4173,4234`) | P-01 |

これらは brief の実測が誤っていた点であり、レビューを採る。

---

## 1. 最重要裁定 — callable 既定値を witness にしない (A-01 = real、採用)

**実測 (親が独立に確認)**: production 経路は `drive` を常に明示的に渡す。
`run_trial:2893-2894` が sentinel を解決し、`:3172` → `_finish_trial:2121` → `_run_workload:2755`
→ `_drive_s8c_generation:1229` と keyword `drive=drive` で素通しする。
したがって `_run_workload:2402` の既定引数は **production 経路では一度も使われない死んだ束縛**である。

**裁定: 無条件 callable-default edge を却下する。** 段 2 プランの推奨案と、それを固定する
予定テスト `test_c12_callable_default_is_reachable` は採らない。

理由: 既定値を witness にすると、`:2893-2894` の実配線を削除しても述語は「到達」と報告する。
これは「実在しない強制を実在と報告する」方向の拡大であり、規律 2 が禁じる形そのものである。
本 wave は誤報を直しに来たのであって、逆向きの誤報を作りに来たのではない。

**採る案 (レンズ A の第三案)**: 限定 value-flow を実装する。

- 到達関数 F の本体で、local 名 `v` が F 内でちょうど 1 回だけ、解決可能な callable
  (import 束縛経由の `Name` / 静的 `Attribute` chain) へ代入されているとき、`v` をその callable に束縛する。
- F が G を `k=v` の keyword で呼び、`v` が上記で束縛済みなら、G の仮引数 `k` をその callable に束縛する。
- G の本体の `k(...)` は、その束縛先への call edge として数える。
- 上記のどれかが成立しないとき (複数代入、条件付き代入、`*args` / `**kwargs` 経由、
  位置引数のみ、caller override が静的に見える) は **到達と数えない**。
- 深さ上限 (下記 §3) を共有する。

この規則で `run_trial:2893-2894` → `:3172` → `:2121` → `:2755` → `:1229` が witness になり、
`:2893-2894` を削れば述語は不在へ倒れる。既定引数は一切見ない。

**追加負例 (必須)**: caller が custom `drive` を注入する形と、`:2893-2894` の sentinel 解決を
削除した形の 2 つで、C12 が第 1 gate の `environment-contract-consumer-absent` へ倒れることを示す
(B12 / A-01 の提案を採る)。

---

## 2. 探索上限 — 親の実測により上限値を改める (B05 = real へ昇格、採用)

**実測 (親、2026-08-17 01:31 JST)**: repo 内 module の transitive import 閉包は
`p3_autonomous_workload_trial.py` / `autonomous_trial_completeness.py` / `trial_registry.py` の
3 root すべてで **118 module**。段 2 プランの上限 64 module を大きく超える。

target が実在しない条件 (C04 は `mark_experiment_indeterminate` / `forbid_trial_restart` が
実 tree に無い) では早期終了できず閉包全体を探索するため、上限 64 では
`reachability-limit-exceeded` の ERROR が本来の `UNSATISFIED` を置き換える。
**これは本 wave の受理条件 (B)「実際に不在なものは依然 UNSATISFIED」を直接壊す。**

**裁定:**
- module 上限を **512** とする。上限は暴走止めであって意味論的 gate ではない。
- **実 tree の全 12 条件評価が、どの上限にも触れないことをテストで固定する。**
  触れたら赤。これが上限値の正しさの唯一の担保である。
- 実装子は実 tree 評価の実測 module 数と所要時間を完了報告に書く。
- depth 上限は value-flow と call graph で共有し 64。callable state 2048、traversal 保持 bytes 16 MiB
  は据え置き。

---

## 3. reason code と fail-closed の分類 (B06 / F-01、部分採用)

- 新 reason `reachability-limit-exceeded` を `ReasonCode` enum へ追加し、
  現行 catch (`:700-712`) が `commit-blob-read-error` へ畳まないよう分類を同時に直す。**採用。**
- 上限 4 種 (depth / module / callable / total bytes) は**種別ごとに** test を置き、
  上限ちょうどと上限+1 を固定する。**採用。**
- F-01 の `PROVEN_ABSENT` / `INDETERMINATE` の全面分離は**本 wave の scope 外**。
  現行の status 語彙 (`SATISFIED` / `UNSATISFIED` / `EVIDENCE_UNDEFINED` / `ERROR` / `NOT_EVALUATED`)
  を増やす変更であり、consumer 全層に波及する。裁定パッケージへ送る (下記 §9)。
  本 wave では「解析不能」を到達扱いにしないこと (= 不在側へ倒す) だけを守る。

---

## 4. 属性収集の所在 (A-06 / B04 = real、採用)

**実測**: C12 の第 2 gate は `{"single_process","allow_resume"} <= attributes` を要求するが、
root module (`p3_autonomous_workload_trial.py`) にはどちらも現れない。`allow_resume` の実強制は
`p3_s4_loop_trigger_gating.py:351-368` の `_assert_resume_allowed` にあり `drive_iteration:816` から到達する。

**裁定: 属性も target definition と同じ canonical 所有境界で集める。**
すなわち到達した関数が属する module を問わず、**到達関数の本体から**属性を集める。
root-only にしない。無関係 module の属性を拾わないことは、到達判定が実 import 束縛に閉じている
ことで担保される。

**帰結として、実 tree の C12 第 2 gate は `single_process_required` 不在の単一理由で落ちる**
(属性側は `allow_resume` が cross-module で拾えるようになる)。
`single_process` 属性の所在は実装子が実測し、単一理由性が崩れるなら報告して止める (DW-M03)。

---

## 5. 到達の質を上げる 4 件 (採用)

| 所見 | 裁定 | 内容 |
|---|---|---|
| A-02 | **採用** | C12 に `main -> run_trial` gate を追加する。C01 は既に持つ (`:423`)。実 tree では `main` から `run_trial` へ到達済み (親が実測) なので現 reason は変わらない。production CLI を切る負例を追加。 |
| A-04 | **採用 (fail-closed 版)** | `from . import X` の解決時、package `__init__.py` を読み、同名 export があれば**曖昧として解決しない** (到達なし)。`__init__.py` も EvidenceRef に載せる。lexical scope の parameter / local / global shadow は解決しない。 |
| A-05 | **採用** | target 解決を production tree に限る。`orchestrator/tests/` 配下および非 production tree を拒否する。test-only module 経由の負例を追加。 |
| A-03 | **部分採用** | 定数偽 branch (`if False:` / `if 0:`) 配下と、どこからも呼ばれない nested function 配下の call を到達から除く。各型の負例を追加。到達不能 except 節・`return` 後の文の除外は scope 外 (§9 へ)。 |
| B08 | **採用** | `from . import a, b, c` の複数名 ImportFrom を実コード由来 fixture として追加 (`p3_s4_loop_trigger_gating.py:55` が実際に使う形)。 |
| E-02 | **採用** | frontier と successor を canonical path/name 順に固定し、異なる `PYTHONHASHSEED` で report bytes が一致するテストを置く。 |

---

## 6. 版 bump の恒真化を防ぐ (T-01 = real、採用)

段 2 プランどおり全 mismatch fixture を「current と異なる版」へ動的化すると、
`DECIDER_VERSION` の v2 bump 自体を削除してもテストが緑のままになる。
「この行を消しても緑」の直接例であり、恒真な保証である。

**裁定:**
- `DECIDER_VERSION == "s8c-decider/v2"` の exact assert を 1 本置く。
- 変異 matrix に `v2 -> v1` を追加し、この assert で kill する。
- 意味変更 (評価器) と bump は**同一 commit**にする。

---

## 7. テストの形 (B07 / B-01 / G-01、採用)

- **B07 採用**: 現行 `TOKEN_ONLY_C12` をそのまま B2 へ転用しない。
  env と guard は正しい imported target、reservation だけを別 module の未 import decoy に分ける。
  そうしないと「bare name 誤採用で落ちた」のか「fixture が元々不正で落ちた」のか帰属不能になる。
- **B-01 採用**: (b1)/(b2) だけでは不足。負例を parameterize し、次の不在型を覆う —
  import 済みだが未 call / caller override / 定数偽 branch / 未呼出し nested scope /
  package shadow / production entrypoint 切断 / test-only module。
  対象は `_reachable*` の直接 consumer 4 条件 (C01 / C04 / C09 / C12)。C10 / C11 は direct AST gate のため対象外。
  各負例は「全 target を通る baseline が terminal `EVIDENCE_UNDEFINED`」を先に確認し、
  1 要素だけを壊して exact reason へ反転させる (単一理由性、DW-M03)。
- **G-01 採用**: snapshot helper に中継 2 path を手で足す案は一般解ではない。
  **実 HEAD 評価と snapshot 評価の result / evidence が exact 一致することを検査するテストを置く。**
  これが乖離の一般的な検出手段であり、「helper を直せば閉じる」という親の含意の訂正でもある。

---

## 8. 宣言外 module を証拠に含める解釈 (B03 = 裁定必要 → 親が裁定)

**裁定: 宣言 root からの bounded import closure を証拠範囲に含めることを許可する。**

根拠は 3 点。
1. 契約自身の C12 `reachable_from` が `"main -> run_trial -> env_contract.lookup"` と
   cross-module の hop を明示している。契約は最初から cross-module 到達を意図しており、
   評価器がそれを実装していなかった。証拠範囲の独断拡大ではなく契約の意図の実装である。
2. 宣言 path 集合に閉じると、C12 の中継 module 2 本が宣言外であるため
   ユーザー裁定 (ii) は**構成上実装不能**になる。裁定を実装不能にする解釈は採れない。
3. 読んだ blob を `EvidenceRef` に載せるので、判定に効いた bytes は report から消えない。
   隠れた判定入力を作らない。

契約 JSON の `required_evidence` は**増やさない**。JSON hash と freeze pin は動かさない。

---

## 9. scope 外 = 裁定パッケージへ送る (実装しない)

| 項目 | 理由 |
|---|---|
| F-01 の `PROVEN_ABSENT` / `INDETERMINATE` status 分離 | status 語彙の拡張は consumer 全層へ波及。別 wave。 |
| A-03 の残り (到達不能 except 節、`return` 後の文) | dominance 解析に踏み込む。本 wave の import traversal を越える。 |
| B09 の digest consumer 閉包台帳 (receipt / completeness / trial lifecycle) | 本 wave は digest を変えるが consumer を変えない。監査は独立タスク。 |
| B11 の g4 freeze record 発行 (v2 schema) | 現 g3 は legacy v1 で発効不能。v2 record 発行は別 owner。本 wave に混ぜない。 |
| C01 の records/threads 不整合 (実 100,000/4 対 要求 1,000,000/48) | 別条件の別問題。 |
| C04 / C09 / C10 の要求名と実装名の不一致 | 契約側の問題であり [T-1167] 系の所有。 |
| [T-1167] の allocation 節縮小 | 対になる別裁定 (択 (c))。本 wave では触らない。 |

**本 wave 後も C12 が `allocation-enforcement-consumer-absent` で UNSATISFIED なのが正しい終状態である。**
本 wave の仕事は診断を真にすることであって、条件を充足させることではない。

---

## 10. 変異事前登録 (DW-M01)

| # | 変異点 | 変異 | 期待 kill (完全集合は実装後に実測して確定) |
|---|---|---|---|
| M1 | `s8c_preregistration_evidence.py` 到達 helper | cross-module graph を wave 前の module-local `_reachable_functions` / `_reachable_calls` へ戻す | 実 tree golden、C12 cross-module 正例 |
| M2 | import resolver | `ImportFrom` の `asname` を無視する | `as` 形の resolver テスト |
| M3 | import resolver | 複数名 `from . import a, b, c` の 2 番目以降を落とす | 複数名 ImportFrom テスト |
| M4 | module alias resolver | `_lookup = env_contract.lookup` の alias edge を除去 | alias 到達テスト、実 tree golden |
| M5 | value-flow | keyword 引数の束縛伝播を除去 | value-flow 到達テスト、実 tree golden |
| M6 | value-flow | **既定引数も witness に数える** (段 2 プランの却下案を復活させる) | caller override 負例、sentinel 削除負例 |
| M7 | canonical 比較 | `(path, name)` を bare `name` 比較へ戻す | 未 import 同名 decoy 負例 (B2) |
| M8 | production tree 制限 | `orchestrator/tests/` 拒否を除去 | test-only module 負例 |
| M9 | package shadow | `__init__.py` 曖昧検査を除去 | package shadow 負例 |
| M10 | 定数偽 branch | `if False:` 除外を除去 | dead branch 負例 |
| M11 | 上限 | module 上限を 64 へ下げる | 実 tree が上限に触れないことの検査 |
| M12 | 版 | `DECIDER_VERSION` を `s8c-decider/v1` へ戻す | exact assert |

M6 と M11 は **wave 前 / プラン段階の実コードの形**を含む変異である
(M6 = 段 2 プランが推奨した形、M11 = 段 2 プランの上限値)。

---

## 11. 段 5 の分割

段 2 プランの 2 分割を採る (親 brief の「単一実装子」は訂正)。

- **単位 A**: `orchestrator/campaign/s8c_preregistration_evidence.py` +
  `orchestrator/tests/test_s8c_preregistration_predicates.py`
- **単位 B**: `orchestrator/campaign/s8c_preregistration.py` +
  `orchestrator/tests/test_s8c_preregistration_core.py`

4 ファイルの所有は完全に素集合。B は A の内部 API に依存しない。
契約 JSON、`docs/phase3-8c-preregistration.md`、freeze record、`reservation.py` は
どちらにも所有させない (触るのは禁止)。

単位 A は分量が大きいので `--max-model-calls` を上げる。
