# [T-106][T-107] parser-authoritative 契約の確定と射程の明記 — 材料レポート

- `authority: none`
- `default_effect: no-state-change`
- 可変状態の正本は worklog 末尾と現行 phase doc。本書は裁定・監査用の凍結スナップショットである。
- **delta-only。** 事実の大半は D89 と `2026-07-26_t098-selector-lp-reject.md` に既記載であり、
  本書はそこへ**追加された分だけ**を書く。既存材料を再掲しない。
- 検出 3 語は D88 (6) の表記規約を継承し LP-1 / LP-2 / LP-3 と記号参照する。

## 0. 既存材料へのポインタ (再掲しない)

| 内容 | 正本 |
|---|---|
| LP 拒否 gate の実装・受理集合・error code 優先順位 | `docs/decisions.md` D89 (1)〜(4) |
| schema/role が no-touch である事実と parser-authoritative という結論 | D89 (5) |
| floor と ratified で受理が分岐する事実、ratified 単独保証の限界 | D89 (6) |
| T-098 wave の材料・逐語・変異台帳 | `output/insights/2026-07-26_t098-selector-lp-reject.md` (+ `-verbatim.md` / `-mutation-ledger.json`) |

D89 (5)(6) は**いずれも「裁定パッケージへ送る」で終わっていた**。本 wave の起点はそこである。

## 1. 本 wave の delta (3 点)

1. **状態遷移。** D89 (5)(6) の推奨が 2026-07-26 のユーザー裁定 (a)/(a) として**確定**した
   ([T-106] = 現状維持 + 射程の明記、[T-107] = parser-authoritative 契約の明文化)。
2. **射程の補完。** D89 は floor しか挙げていなかった。実際の parser 感応は **2 層**である。
3. **機械的固定。** D89 は散文だけだった。受理差を assert で固定する境界テストを新設した。

## 2. 実測 (すべて実ファイル編集、模擬なし。段 1 前に取得し、直後に復元)

| # | 変異 | 結果 | 復元後 |
|---|---|---|---|
| P-A | `.claude/agents/selector-8b.md` に 1 byte 追記 | `sources.role.sha256 が実ファイルと不一致` | PASS |
| P-A' | `s8b_selector_output_schema.json` に 1 byte 追記 | `sources.output_schema.sha256 が実ファイルと不一致` | PASS |
| P-B | `parse_selector_output` 冒頭に `raise` 注入 | `rows[0].raw_response の再 parse 結果 … と不一致` | PASS |

baseline (`verify_prediction_freeze` on 封印済み `selector_predictions.json`) = PASS。
復元はいずれも `git checkout --` で行い、`git diff --stat` で単一変異だけを確認した (DW-O19 の復元規律)。

**P-A / P-A' が [T-107] の前提の実証である** — role・schema の bytes を変えると既存封印 prediction の
検証が実際に割れる。したがって受理集合の正本を schema/role 側に置くことはできない。

## 3. 親実測の訂正 (段 3 レンズ A の A-6 が指摘、real)

親は当初 measurements に「ratified は parser の blob sha を照合するだけ」と書いた。**これは過大表現。**

- ratified は `s8b_ratified_freeze.py:2461` で `s8b_selector_freeze` を import し、
  同 module は module-level で `parse_selector_output` を import する (`s8b_selector_freeze.py:34-37 / :47`)。
- したがって **ratified は parser module の import 可能性には感応する**。parser が syntax error や
  top-level raise を持てば、raw を一度も再 parse しないまま全 ratified launch が倒れる。
- 非感応なのは **raw 分類の意味論**だけである。

あわせて段 3 レンズ B の B-4 が、「ratified は blob sha だけ」という省略が
prediction の strict parse・構造・source blob・journal 対応・raw/envelope hash 検査を落としていると指摘した。
**両方とも採用し、本書と D90 の記述を正した。**

## 4. 射程 — parser 感応の 2 層 (D89 が漏らした部分)

`parse_selector_output` の直接呼び出しは repo 全体で **2 箇所だけ**である。

| 層 | 呼び出し | 意味 |
|---|---|---|
| 生成層 | `record_agent_attempt` (`s8b_selector_freeze.py:380`) | parser の判定が journal の `status`/`choice_id`/`rationale`/`parser_error_code` として**記録される** (接続 = `s8b_prediction_runner.py:884-898`) |
| 検証層 | `_reparse_agent_raw` (`s8b_selector_freeze.py:194`) | `verify_prediction_freeze` (:902) から行ごとに呼ばれ、記録値と**再照合**する |

検証層 `verify_prediction_freeze` の消費者は 4 経路。

| 消費者 | 位置 | 現況 |
|---|---|---|
| floor launch preflight | `s8b_floor_campaign.py:1365` | **dormant**。`_assert_official_permitted` が official を core で無条件拒否する (:193-203) |
| prediction runner の seal reload | `s8b_prediction_runner.py:1480` | 稼働 |
| verdict の prediction 検証 | `s8b_verdict.py:211` | 稼働 |
| selector-freeze verify CLI | `s8b_selector_freeze.py:1033` | 稼働 |

**ratified は非消費者**である (`s8b_ratified_freeze.py` に `verify_prediction_freeze` /
`parse_selector_output` / `_reparse_agent_raw` の呼び出しは grep 0 件)。

## 5. ratified が実際に検証しているもの (「何もしない」ではない)

`s8b_ratified_freeze.py:2616-2700` で、journal と prediction row の**記録値どうし**を相互照合する —
`status` / `choice_id` / `rationale` / `parser_error_code` / `receipt` / `raw_response_path` / `raw_sha256`。
加えて raw・envelope の bytes hash、parser・role・protocol の `pre_oracle_head` blob sha を照合する。

**していないのは raw テキストの再 parse だけ**である。結果として、journal と row の**両方**に
同じ嘘 (parser が拒否する raw を `status="valid"` と記録) を書き、raw の sha を合わせれば、
ratified は受理する。これが本 wave が固定した非対称である。

## 6. 境界テスト — 何を固定し、何を固定しないか

`orchestrator/tests/test_s8b_ratified_verify.py::test_selector_parser_classification_boundary_at_ratified_launch`

固定する不変条件:

1. 変異 raw が現行 parser の受理集合外である (`rationale_placeholder` で送出)。
2. 境界 commit が宣言した 4 path ちょうどを導入する (`_commit_exact`)。
3. **ratified は受理する** — `load_ratified_freeze` → `launch_validate` が成功する。
4. **`verify_prediction_freeze` は拒否する** — 同じ文書・同じ raw に対し `invalid:rationale_placeholder`。
5. **誤った error code での記録も拒否する** — `status="invalid"` だが `parser_error_code="invalid_json"`
   なら拒否する (**負例**。error code 比較の消失を撃つ)。
6. **正直な記録は受理する** — `status="invalid"` かつ正しい code なら受理する
   (**正例**。承認外の過剰拒否を撃つ)。
7. **A 後の evidence 書換えは `history-mutated` で拒否される** — 意味検証より先に H-pure 履歴検査が働く。

固定**しない**もの (正直な限界):

- certified 選択値・材料レポート・試行台帳の値。`s8b_verdict.py` に `rationale` の出現は **0 件**で、
  combined verdict は choice と `prediction_body_sha256` を使う。本テストは**受理集合テスト**であり、
  成果物値の保証ではない (段 3 レンズ B の B-6)。
- 単一セル (rr20/on)・単一 error code の 1 事例である。ratified 非再 parse の一般契約は
  **ユーザー裁定に由来**するのであって、この 1 例から一般化したものではない (段 3 レンズ A の A-4)。

## 7. 変異 matrix (親実測、fix 確定後・統合 commit 前)

control = **変更前 Git HEAD のテスト集合**。本差分は純追加 (199 insertions / 0 deletions) のため、
新 node を `--deselect` することで HEAD 集合を exact に再現した。
単一ファイル走行は import path 由来の偽赤になるため 2 ファイルを常にまとめて走らせた (DW-O18)。
baseline = 新 **192 passed** / 旧 **191 passed + 1 deselected** (両構成緑を確認してから変異を注入)。

| ID | 変異 | 新 | 旧 | 帰属 |
|---|---|---|---|---|
| S1 | ratified に `verify_prediction_freeze` 呼び出しを追加 | KILL | KILL (既存 42 node) | 非帰属 control |
| S2 | `verify_prediction_freeze` の `_reparse_agent_raw` 呼び出しを削除 | KILL | KILL (既存 3 node) | 非帰属 control |
| S3 | `_reparse_agent_raw` の **error code 比較だけ**を削除 | KILL | SURVIVE | **帰属** |
| S4 | 再 parse 失敗時に記録内容によらず送出 (過剰拒否) | KILL | SURVIVE | **帰属** |
| S6 | `history-mutated` の reason code を潰す | KILL | SURVIVE | **帰属 (診断 pin)** |

5/5 が事前登録 (erratum 訂正後) と一致。harness はアンカー一意性 assert・注入 diffstat 記録・
`git checkout --` 復元 + 内容一致検査・flock 単一走行を持ち、全走後の tree は clean。

**S1 が非帰属だったことは重要な発見である。** ratified に再 parse を足すと既存 42 node が落ちる —
つまり「ratified が再 parse しない」性質は、本 wave 以前から既存テスト群が厚く守っていた。
新テストの固有の検出力は S3 / S4 / S6 の 3 件である。

## 8. 事前登録の erratum (DW-M07 — 初回登録の誤りを台帳に残す)

初回の変異事前登録には **3 件の誤り**があり、いずれも敵対レビューまたは親の本走が検出した。

1. **S3 は等価変異だった (段 6 レビュー A の RA-1)。** `valid` 行は手前で `parser_error_code=None` を
   強制されるため、`status` 照合だけを消しても error code 不一致で拒否され続ける。
   初回登録は DW-M01 の「その位置より前に同じ入力を拒否する検査がないこと」を満たしていなかった (F28 型)。
   実装側も private 関数 `_reparse_agent_raw` の直呼びで**偽の KILL** を作っていた。
   → 公開経路の負例 (誤 code `invalid_json`) へ差し替え、S3 を実効変異へ再照準した。
2. **S5 は到達不能だった (RA-2)。** `_fixed_commit_all` へ戻すと `git add -A` が残り artifact を境界 commit に
   取り込み、**直後の base commit が空 commit で先に落ちる**。exact-path assert には到達しない。
   → S5 を本走から外した (実効 gate へ再照準できないため)。
3. **S6 の期待を誤って SURVIVE と登録した (親の誤り、本走で判明)。** reason code を潰せば
   post-A assert は落ちるので KILL が正しい。受理集合を変えず構造化シグナルだけを pin する変異なので、
   DW-M08 に従い **diagnostic sensitivity pin** 枠で記録する。

## 9. 検証プロセス

codex 子 **6 本** — プラン 1 (max)、敵対相談 2 (max)、実装 1 (high)、敵対レビュー 2 (max)、
fix 1 (high)、焦点再レビュー 1 (max)。**相談 2 本・レビュー 2 本・焦点再 1 本のすべてが NO-GO。**

- 段 3 (相談): 所見 19 件。親の provisional 裁定 (P2) が否定され、親の「delta 4 点」も水増しと判定された。
  プランは**縮小**され、テスト 2 本 → 1 本、D90 の規範文から統治機構を削除した。
- 段 4 (親裁定): scope 外として **2 件を不採用**にし裁定パッケージへ送った —
  consumer 閉集合の AST テスト (構文形状しか固定せず `if False`・alias・`getattr` を見逃す)、
  および D90 の統治機構 (「全受理集合変更に新 D 必須」「新 consumer は必ず verify 経由」)。
  後者はユーザー裁定 2 件に無い新設であり、DW-G03 の独立 2 例も無い。
- 段 6 (レビュー): 所見 8 件。**RA-1 が実在の検出漏れを発見**した (error code 比較が無防備)。
  親は RB-2 / RB-4 を **refuted** (共有 fixture の既存性質であり本差分由来でない)、RB-3 を nit と裁定した。
- 段 6 (焦点再): 7 件 closed/対象外、1 件 partial (RA-2 = 台帳の誤記)。新規所見なし。
  partial はコード欠陥でないため fix 巡 2 を行わず、本書 §8 の erratum で閉じた。

## 10. 検査

| 検査 | 結果 |
|---|---|
| 親の焦点実走 (ratified_verify + selector_freeze + selector_output) | 279 passed |
| 親の実走 (`test_s8b_ratified_verify.py` 全体、fix 後) | 160 passed |
| 変異 matrix | 5/5 一致、帰属 3 / 非帰属 control 2、復元後 tree clean |
| 受入全走 (統合 commit 直前) | **3059 passed / 18 skipped / 0 failed** (1811.26s) |
| 基線 (前 wave 実績 `ef9ef76`) | 3058 passed / 18 skipped。差 +1 = 本 wave の新テスト 1 本。node 消失 0 |
| `tools/check_docs.py` | 違反なし (rc=0) |
| 記録後検査 (F34、記録 commit 直後の再走) | `check_docs` rc=0、`check_ai_provenance` **364 件・違反なし**、焦点 (ratified_verify + selector_freeze + selector_output + check_docs + holdout_freeze) **414 passed** |
| 逐語の検出語 gate | hit 1 件 → 可逆 defang + erratum を適用し再走で rc=0 (D88 / DW-S07)。本欄は amend で埋めたため記録 commit の hash を自己参照しない (F36/F38) |
