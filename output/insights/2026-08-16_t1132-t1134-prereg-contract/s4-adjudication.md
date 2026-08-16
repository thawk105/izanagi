# 段 4 裁定 — [T-1132] [T-1133] [T-1134] 8c 事前登録の証拠契約

裁定者: 親 / 2026-08-16 08:45-08:55 JST / base main `10813338`
入力: 段 2 プラン v1、段 3 レンズ A (規律 2)、段 3 レンズ B (freeze 履歴・D96 手続)、親実測 M1〜M8
裁定 inbox 再走査: 69 件、wave 開始 (07:49) 以降の増分ゼロ

---

## 0. 結論 (先に書く)

**本 wave は契約改訂を行わない。** 行えないことが実測で確定したためである。
本 wave は、改訂に必要な前提 (新 D) と、改訂の設計判断・却下案・新事実の記録を land し、
契約改訂そのものを後続 wave へ渡す。あわせて (P1) の機構問題を裁定パッケージで返す。

これは scope の縮小ではない。D96 条項 1 が要求する新 D は、どの解決を採っても必要であり、
本 wave の成果は後続 wave でそのまま使われる。

---

## 1. (P1) g3 の `ruling_reference` — **blocker 確定。親 provisional (D96) を撤回する**

### 所見の裁定

| 所見 | 出所 | 裁定 |
|---|---|---|
| `ruling_reference=D96` は機械的には通る | レンズ A/B、親 | **real・採用** (`_RULING_RE` と `## D96.` 見出しに一致) |
| しかし D96 は本改訂の authorization ではない | レンズ A §1-6、レンズ B §2 | **real・採用 (blocker)** |
| 既存 D の流用は成立しない | レンズ B §2 | **real・採用** |
| P1b (spool fragment を受理形へ) は現行制度では不可 | レンズ B §2 | **real・採用・不採用案** |
| 現行 land 順序では第 4 案 (lock 内 pre-fold) も不可 | レンズ B §2 | **real・採用** |

### 親の独立確認

- D96 本文 (`docs/decisions.md:4275-4279`) を精読した。**「同じ変更単位」を要求しているのは
  条項 2 (境界テスト) だけであり、条項 1 (新しい D を起こす) には同単位要求がない。**
  したがって「D を先に land し、後続 wave で契約改訂 + 境界テスト + g3 を同一単位で行う」形は
  D96 に適合する。レンズ B の「P1c は D96 要件を満たさない」は**この点で refuted**。
- 候補として親が独立に見つけた D165 (「段 8c 事前登録は条件充足の機械確認で自動発効し、
  条件契約だけを hash 世代台帳で凍結する」) も、機構を定めた決定であって本改訂を
  authorize したものではない。**不採用。**
- D410 は逐語で「s8c C11 は `machine_checkable: false` のまま `EVIDENCE_UNDEFINED` = **未充足**」
  と書いており、本改訂はこの記述を書き換える側である。新 D は D410 との関係を明示する義務を負う。

### 裁定

1. **本 wave は g3 を作らず、凍結範囲 (§1〜§4・§6・§7 の規範本文、§5 の欄名集合、
   発効ポリシーのブロック、証拠契約 JSON の意味内容) を 1 byte も変えない。**
2. **本 wave は新 D を spool decisions fragment として起こす。** 内容は §2〜§6 の裁定を含む。
3. 後続 wave が、main に着地した実 D 番号を `ruling_reference` にして g3 を作り、
   契約改訂・doc 追随・境界テストを同一 commit で land する。
4. (P1) の機構問題 — 「`ruling_reference` は手続参照か内容 authorization か」「land が
   ff-only 後に fold する順序を変えるか」— は**裁定パッケージでユーザーへ返す**。

**成果物影響:** 本 wave 単独では certified 選択・材料レポート・試行台帳のいずれの値も変えない。
後続 wave がこの D を引けなければ、8c 本走は永久に発効しないままである。

---

## 2. (P2) 評価器終端の `SATISFIED` 化 — **親 provisional を撤回し、refuted と裁定する**

### 決定的な根拠 (3 つが独立に同じ結論)

1. **事前登録文書 §4 の逐語 (親が実測):**
   「承認上限は 3 入口 (CLI・`run_trial()`・`_run_workload()`) で機械強制する。
   **起動側の既定値は `G=2` ではないため、本系列の投入は世代数を明示的に指定する形でのみ行う**。
   `G=2` を宣言だけで満たしたと見なさない。」
   → 文書自身が、3 入口の機構は**承認上限だけ**を強制し、exact `G=2` は §7 の起動形が担うと
   規範として書いている。機構の静的存在は完了証明ではない。
2. **レンズ A の実測 (親が独立に裏取り):** `_validate_generation_budget` は
   `1 <= generations <= MAX_GENERATIONS(=10)` を受理し、`> MAX_APPROVED_GENERATIONS(=2)`
   だけを拒否する。CLI 既定は `--max-generations 1`。**G=1 は全検査を通る。**
3. **既存テスト fixture 自身の証明:** `TOKEN_ONLY_C*` は静的検査を全部通るよう設計された
   実体のないコードである。終端を `SATISFIED` にすれば、この fixture が条件充足と認定される。

### 追加の決め手

段 2 は「AST で支配関係を検査して discharge する」案を出したが、**D96 本文がこの方式を
名指しで却下している** — 「consumer 閉集合の AST 固定は構文形状しか固定できない
(`if False`・alias・`getattr`・例外握り潰しを見逃す一方、無害な refactor で偽赤になる) ため
不採用済み」。レンズ A は実際に `if False` と catch-and-continue で全 6 条件を通す最小偽装を
提示した。段 2 案自身の fallback (「証明できなければ undefined へ戻す」) を**今発動すべき**である。

### 裁定

- **6 評価器の終端は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のまま維持する。**
- **`SATISFIABLE_CONDITION_IDS` は空集合のまま維持する。**
- 段 2 の「C11 だけ SATISFIED」案は **不採用**。段 2 §1 の `generation-policy-satisfied`
  reason code 追加も不採用。
- レンズ A の must-fix 1 (P2b への退避) を**採用**。

**成果物影響:** 受理集合を 1 bit も広げない。これを採らなければ、`G=1` の試行や
実体のない実装が正式な試行台帳・材料レポート・certified 選択へ流入しうる。

---

## 3. (T-1133 / 衝突 b) 条件 11 の証拠差し替え — **後続 wave で実施。形は確定する**

裁定 #2 (a) は忠実に実装できる。ただし**終端は変えない**ので、C11 は
`UNSATISFIED / sample-plan-absent` から `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`
へ移る。これは受理集合の拡大ではない (どちらも非充足)。

確定する形 (後続 wave が実装する):

- 契約 C11 の `required_evidence` から `sample_plan` と `cap_lift` を削除する。
- `generation_supervisor.field_paths` から `_run_workload.sample_plan_sha256` と
  `_run_workload.cap_lift_sha256` を削除する。
- 段 2 が特定した**閉じた射影の実体**を新しい `required_evidence` として追加する。
  `orchestrator/campaign/s8c_generation_projection.py` (`_CRITIC_KEYS`、`_DIAGNOSTIC_METRICS`、
  `apply_critic_feedback`、`_validate_critic_projection`、`validate_planner_payload`)。
  **親の M4 は誤りだった** — 閉じた射影は `_role_metric_payloads` ではない。段 2 の訂正を採用する。
- `_evaluate_c11` から `sample_plan` / `cap_lift` 検査と `_artifact_object` を削除し、
  射影 blob の存在と閉じた key 集合の検査を足す。終端は変えない。
- `consumer_requirement.proof` と `static_only_note` を、廃止した 2 成果物に依存しない文へ改める。

### レンズ A の「下限が失われる」所見 — **real・採用。ただし本改訂の欠陥ではない**

削除する `sample-plan.v1.json` は `minimum_generations >= 2` という下限を要求していた。
既存 4 機構は上限しか持たない。したがって条件 11 の証拠から**下限が消える**。

ただし前述のとおり、文書 §4 と §7 は exact `G=2` を**起動形の責務**として既に規範化しており、
条件 11 の機構に下限強制を求めていない。よって (a) の実装は文書と整合する。
残余は「exact `G=2` を要求する正式受入 consumer が存在しない」ことであり、
これは**新規タスクとして起票する** (レンズ A must-fix 2、レンズ B must-fix 2)。

**成果物影響:** 起票しなければ、`G=1` の試行が正式系列の試行として台帳へ入り、
「ワークロード特化合成」の材料レポートと certified 選択を偽装しうる。

---

## 4. (T-1134 / 衝突 c) 条件 3 / 8 の二段束縛 — **後続 wave で実施。段 2 の修正版を採用**

裁定 #3 (a) を採る。ただし親の (P3) 原案 (`prereg_content_commit` を manifest 自身へ入れる)
は**自己参照が残るため不採用**。段 2 の修正版とレンズ B の検証を採用する。

- 内容 commit `P` が manifest bytes を導入する。**manifest は `P` の ID も自分自身の digest も持たない。**
- 発効 commit `C` は `P` の直子で、binding record だけを導入する。record は
  `prereg_content_commit = P`、manifest path、manifest bytes の SHA-256 を持ち、
  `C` 自身の ID は持たない。
- 祖先代用の禁止は、`is-ancestor` ではなく**「`C` の親集合が exact `{P}`」**で維持する。
  レンズ B が ff-only land と fold の後でも `C` の親が変わらないことを確認済み。
- `prereg_commit` を互換 alias として残さない (D75 の同名識別子二義化)。

### レンズ B の「consumer 未配線」所見 — **real・採用・scope 外**

`trial_registry.py` は manifest・registry・binding のすべてで単一 `prereg_commit` を要求しており、
契約 JSON だけ変えても launch・registry・terminal report は P/C を消費しない。
**後続 wave でも契約と doc の形だけを直し、consumer の配線は別タスクとして起票する。**
「実装したふり」にしないため、条件 3/8 は `machine_checkable: false` のまま維持する。

**成果物影響:** 配線されるまで条件 3/8 は未充足のままであり、8c 本走は発効しない。

---

## 5. 恒真な負の対照 — **real・採用。本 wave では記録のみ**

親が段 1 後に発見し、レンズ A が独立に確認した:

- `test_satisfiable_predicate_requires_negative_control` は
  `machine_checkable == SATISFIABLE_CONDITION_IDS == frozenset()` のため後続 loop が 0 回。
  negative control の実在・発火を 1 件も検査していない。
- `test_noop_and_token_only_fixtures_never_satisfy` は baseline と mutation の**両方**に
  同じ `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` を期待する。
  mutation が何も壊さなくても通る。**6 条件分すべてが恒真。**
- `nc_c02/c03/c05/c06/c07/c08` は JSON 内の文字列としてしか存在せず、mutation case が無い。

これは衝突 (a) の第 2 の害である。契約が「機械検査対象外」と記す限り、その条件の
負の対照も同時に恒真化する。**後続 wave で `machine_checkable` を反転すると、
C01/C04/C09/C10/C12 の mutation 側が具体的な `UNSATISFIED` 理由を返すようになり、
6 条件分の対照が初めて発火する。これが後続 wave の主たる実利である。**

**成果物影響:** 恒真のままなら「負例あり」という契約表示が実際の拒否能力を持たず、
台帳・材料レポート・certified 選択の信頼根拠にならない。

---

## 6. scope 外と裁定した real 所見 (裁定パッケージでユーザーへ返す)

| # | 所見 | 出所 | 重大度 |
|---|---|---|---|
| A | **evaluator / core の bytes が freeze に束縛されていない。** protected hash は文書と証拠契約 JSON だけを含み、`s8c_preregistration_evidence.py` / `s8c_preregistration.py` / `s8c_generation_projection.py` を含まない。世代を上げずに評価器の意味を変えられる | レンズ A §1-7・§5-4、レンズ B §6 | blocker |
| B | **`ruling_reference` の意味が未定義。** 手続参照か内容 authorization かが曖昧。`procedure_reference` と `authorization_reference` に分ける案がある | レンズ B §8 nit | high |
| C | **land が ff-only 後に fold するため、新 D を同一 wave の g3 から引けない。** 解くには land protocol の変更が要る | レンズ B §2、親 | blocker |
| D | **exact `G=2` を要求する正式受入 consumer が無い。** 上限 2 で代用できない | レンズ A §3-1、レンズ B must-fix 2 | blocker |
| E | **P/C binding の consumer 未配線** (`trial_registry.py` ほか) | レンズ B §5 | blocker |
| F | **衝突 (d) arm 未束縛** — brief で scope 外と明記済み | 親 | high |

---

## 7. nit 裁定 (起票のみ、本 wave では直さない)

- `PreregistrationError` は `.reason` を持つのに `s8c_preregistration_evidence.py:714` は
  `.reason_code` を見るため、全 `PreregistrationError` が `commit-blob-read-error` に潰れる
  (**親が実測で確認**)。受理には影響せず診断のみ。
- `contract-machine-evaluator` は内部例外名で、公開結果に出ない。固定 enum 値が要る。
- C03 の `static_only_note` は「registry module 不在」と書くが現 HEAD には存在する。
- `check_docs.py` の未知 D / 不存在 path 検査、runbook の旧 `prereg_commit` 記述は
  後続 wave の受入面に含める (レンズ B §3、**親の M7 pin 閉包の不足を認める**)。

---

## 8. 親の実測への訂正 (受け入れたもの)

- **M2 の一般化は誤り。** 「HEAD 1 点で全件未充足」は集合包含の証明ではない。
  正しい記述は「現 HEAD において 6 評価器は全件 UNSATISFIED であり、
  終端に到達するものは無い」に限定する。レンズ A/B 双方の指摘を採用。
- **M4 の「閉じた射影 = `_role_metric_payloads`」は誤り。** 正本は
  `s8c_generation_projection.py`。段 2 の訂正を採用。
- **M4 の「既存 4 機構」は独立 4 証拠ではない。** 上限定数と 3 入口 validator は 1 機構、
  射影と production wiring は 1 機構、negative control は開発テストで `probe.evidence()` に
  入らない。レンズ A の指摘を採用し、新 D では「4 機構」と書かない。
- **M7 の pin 閉包は不完全。** `check_docs.py` の動的検査、runbook、land/fold の採番順、
  evaluator/core bytes の freeze 非拘束を含めていなかった。採用。
- **M8 は snapshot に限定する。** 「確認時点 (07:52 JST) の path 重複ゼロ」と書く。

## 9. レンズの誤りへの訂正 (refuted としたもの)

- レンズ B「D114 は承認済み上限を 1 としている / D410 は cap 引き上げの権威に使えない」は
  **不正確**。D410 本文は「D114 の承認上限 1 を 2 へ上げる」と自ら定めており、D410 が
  cap 引き上げの権威である。D410 の当該文は「C11 の充足状態を cap 引き上げの根拠に使うな」
  という意味であって、D410 自身が権威でないという意味ではない。
- レンズ B「P1c は D96 要件を満たさない」は **refuted** (§1 の親の独立確認による)。

---

## 10. 変異事前登録 (DW-M01)

**本 wave は「実装しない」と裁定済みで実装差分ゼロ (docs と spool fragment のみ) であるため、
`DW-S04` により変異 matrix を免除する。受入全走は免除しない。**

後続 wave のために、実装時に登録すべき変異を先に書き残す (新 D に含める):

1. `machine_checkable` を 1 条件だけ `false` へ戻す → その条件の negative control mutation が
   具体理由を返さなくなり赤。**先取りされる後段検査を数えること** (gate が発火すると
   後段 loop が走らない)。
2. 評価器のない条件 (C02) を `true` にする → `ERROR / contract-machine-evaluator`。
3. 終端を `SATISFIED` へ変える → token-only fixture が充足し、対照が赤。
4. C11 の射影 blob 検査を外す → 射影不在の fixture が終端へ到達し赤。
5. **正例 (過剰拒否の検出):** 現 HEAD の実コードが、反転後も 6 条件で
   親が実測した status vector を返すこと。
6. **wave 前の実コードの形を必ず含める** — 反転前の `machine_checkable: false` を
   変異として撃ち、対照が恒真に戻ることを示す。

---

## 11. 本 wave の成果物 (確定)

1. **decisions spool fragment (新 D)** — 本裁定 §1〜§9 の設計判断、却下案、D410 / D165 / D96 との関係。
2. **worklog spool fragment** — 実測 M1〜M8 (訂正込み)、両レンズの所見、後続タスクの「次の一手」。
3. **failures spool fragment** — 「D96 手続の世代記録が引く D は、land の fold より前に
   着地していなければならない」構造的失敗型。
4. **insights** — 段 2 / 段 3 の逐語成果物、本裁定書。
5. **裁定パッケージ** — §6 の A〜F をユーザーへ返す。

**land 対象外:** 契約 JSON、`docs/phase3-8c-preregistration.md`、評価器、境界テスト、g3。

## 12. 通る正例 (gate の禁止に添える)

本 wave は gate を新設しないため署名は無い。後続 wave が反転する gate について、
通る正例を先に固定しておく:

現 HEAD の `orchestrator/campaign/p3_autonomous_workload_trial.py` は、`machine_checkable`
反転後も C11 について `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` を返す
(sample_plan / cap_lift 検査を外した場合)。これが「正しい実装が過剰拒否されない」正例である。
