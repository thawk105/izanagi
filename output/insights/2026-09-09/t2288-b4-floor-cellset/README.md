# [T-2288] B-4 権威 floor の発行 — 凍結セル集合が 1 spec に表現できないことの確定と裁定パッケージ

`authority: none`
`default_effect: no-state-change`

2026-09-09。branch `worktree-dev-wave-t2288-b4-floor-cell-calib`。起点 main `cbcdb6c91`。
**実装面 (D95 決定 2) の差分は 0。** 本 wave の成果物は台帳 fragment とこの凍結スナップショットだけである。
可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。

## 依頼と、依頼前提の訂正

依頼は「B-4 の権威ある floor 成果物を発行して production 分析経路へ配線する。現在は `floor=None` が
渡るため、いかなる入力でも `floor_domain_error` を返す」だった。

**配線は 2026-09-08 に着地済みである** ([T-2424])。`p3_b4_material_report.py` は事前登録 §5 を読んで
`resolve_preregistered_authoritative_floor` を呼び、§5 の floor 欄が逐語 sentinel `未記入` のときだけ
`None` を渡す。それ以外は pin 文法・path・sha256・artifact schema を fail-closed で検査する。
残っているのは発行だけである。

## 発行の前提として欠けているもの (親の実測)

| 前提 | 実測 |
|---|---|
| accepted calibration | `output/env/pegasus/calibration/registered/` の 2 件のみ。**両方 balanced (rr50) / t48**。rr95・rr5 は 0 件 (tracked な `calibration/v2` 全 27 file を列挙) |
| tracked build receipt (`s8b-binary-admission/v2`) | 0 件 |
| 凍結 spec (`floor-pair-spec/v3`) の実 instance | 0 件 |
| D1641 の 2 campaign 実測 | 未実施 |
| 事前登録 §5 floor 欄 | `未記入` |

## 詰まりの正体

D1641 が凍結したセル集合「3 workload × contention セル」と、保守側最大の対象集合
「凍結したセル集合 × 2 時間窓の全部」を **1 spec・1 成果物で測ることは、現行設計では不可能**である。

原因は 2 つの組合せ。(a) D15 が calibration を (env, thread, 代表 workload) でキーすると決めている。
(b) 凍結 spec は `provenance.calibration` を 1 件しか持たず、`_bind_checkout_inputs` がその 1 件を
全 cell へ照合する (`calibration.workload` / `.threads` / `saturation.records` の一致を要求)。
したがって 1 spec の cells は同一 workload しか持てない。

issuer 側は複数 workload を前提に組まれている (`_derive_identity` の `workload_identifier` は
`_aggregate_identifier("set", ...)` による集合集約) ため、両者は食い違っている。

## 親の中心判定が段 3 で覆ったこと

親 brief と段 2 plan は「workload 一致要求は repo の先例と整合しない欠陥」と判定し、
その一致要求だけを外す案 (案 C) を選んだ。根拠は b10 formal run provenance が 3 workload すべてに
同一 calibration を束縛し束縛 field に `workload` を含まないこと、および事前登録 §5 の
校正済み `PerfConfig` 欄が単数であることだった。

**段 3 のレンズ A が D15 を引いて反証し、親が一次資料で確認した。** D15 の却下欄は逐語で
「D13 の『入力完全非依存』を維持し単一 calibration で済ませる: 飽和点が skew 依存と実測で割れた以上、
虚偽。代表 workload 署名で分けるのが honest」と書いている。**現行の一致要求は D15 準拠の正しい gate
であり、欠陥ではない。** b10 の先例は権威にならない — 同 provenance の `official_certification` は
`false` である (親が実測)。

この near miss は failures 台帳へ登録した (fragment
`docs/spool/failures/2026-09-09-dev-wave-t2288-b4-floor-cell-calib-1.md`、番号は fold が付ける)。
止めたのは `DW-C00` の「設計択一が割れる段では独立の敵対検証子を省かない」である。
軽量版で段 3 を省いていれば実装まで通っていた。

## 3 案と、それぞれを阻む既裁定

| 案 | 形 | 阻む既裁定 |
|---|---|---|
| A | cell ごとに calibration を束縛する | D1696「測定前の follow-up wave で schema と validator を拡張する案は採らない」。再訪条件は未成立。加えて DW-G04 の発火 artifact が無い (rr5・rr95 の accepted calibration が 0 件) |
| B | workload ごとに 3 spec → 3 成果物 | 現行コードのまま表現できるが、事前登録 §5 の floor 欄は pin 1 件を受ける文法であり、3 成果物の保守側最大を 1 件へ集約する規則が無い。集約規則の新設は D1383 によりユーザー裁定 |
| C | workload 一致要求だけを外す | D15 が却下済み。絶対規律 2 の向きに反する |

## D1696 に対する新事実 (裁定へ返す 1 点)

D1696 は「§5 のセル集合との一致」を凍結 spec を書く人間の責任として残した。
**それは spec がその一致を表現できることを前提にしている。実際には表現できない。**
人間が見落としたのではなく、書けない。この 1 点は再訪条件の文言 (人手の確認が実際に見落とした) には
当たらないので、条件の自動成立とは扱わずユーザー裁定へ返す。

## 裁定に依存しない前進

rr5 / rr95 (t48 / pegasus) の accepted calibration は案 A でも案 B でも必要である。
D1641 決定 2 が測定を認可済みで操作は AI 委任なので、ユーザー裁定を待たずに calibrator を走らせられる。
次の一手へ新規項として登録した。

## 段 3 の所見で親が採ったもの (抜粋)

- レンズ A: `maxrss` は workload 実行後の process peak RSS であって table サイズ定数ではない
  (read は deep copy、write は新 payload 確保、RMW は両方)。よって案 C の論拠「working set は
  workload 非依存」は成り立たない。
- レンズ A: `noise_floor.cv` は within-run であり、driver が測る between-run floor の代用ではない (D1639)。
- レンズ A: `calibration/v2` の workload は任意の `dict[str,str]` で、cell 側の exact 3-key 比較が
  唯一の拘束。案 C はその最後の拒否を消す。
- レンズ A: 案 C を採ると、偶然 `records` が一致する任意 workload の calibration を再利用できる。
- レンズ A: 事前登録 §5 の単数欄から「1 calibration でよい」は導けない。同欄は path と hash を置く
  1 セルであるだけで意味上の個数を固定していない。
- レンズ B: 案 C を入れても実 checkout の凍結 spec は作れない。`load_frozen_spec` は実在する tracked
  spec・calibration・binary・build receipt をすべて要求し、後者 2 つは 0 件である。
- レンズ B: `SPEC_SCHEMA` を v4 へ上げると canonical spec bytes と sha256 が変わり、それが HMAC 入力なので
  **literal な順序 golden 2 箇所 (session ID 8 件と measurement role 順 8 件) が確実に変わる**。
  段 2 plan の「fixture が定数を参照するので golden は変わらない」は逆である。
- レンズ B: issuer test は全て実質 1 cell workload で、`workload_identifier` の集合集約を
  複数 workload で通していない。

## 親が覆した所見

- レンズ A の (γ'') (workload key のうち records に効くものだけ一致を要求する) は不成立。
  skew・rratio・rmw のいずれも resident peak とアクセス分布に効き、records に効かないと
  証明済みの key は無い。
- 2 window 間の calibration 差替えは spec hash が塞いでいる (穴ではない)。
- binder に例外の飲み込みは無い。D1377 と floor §5.1 の直接緩和も無い。
- 段 2 plan の「受入所要台帳を更新する」は不採用。親が実測: `orchestrator/tests/conftest.py` は
  `nodeid_count != len(durations)` のときだけ台帳を破棄する fail-soft で、消した nodeid の残骸が
  残っても件数は変わらず、新 nodeid は未登録なら既定 cost になるだけである。台帳を触ると main
  取り込みで必ず衝突するので触らない方が安い。

## 親の誤りとして記録する 4 点

1. 「現行の workload 一致要求は欠陥」という中心判定そのもの。
2. 行番号 4 箇所 — `_bind_checkout_inputs` を 1122-1196 (正: 1122-1194)、cell loop を 1184-1196
   (正: 1181 開始)、`_derive_identity` を 737-812 (正: 737-814)、schema pin test を 628-634
   (正: 629-633)。いずれも段 2 が訂正した。
3. 「既存 209 node」は陳腐化。正しくは 210 (親が受入所要台帳で独立確認)。
4. 生存確認の `ps` 出力に `head -4` を掛け、他 wave の行で埋まった結果を段 2 producer の死と誤読した。
   再確認して生存を確認したので実害なし。再投入していれば job-id 衝突で 1 本無駄にしていた。

## 本 wave 以前から存在する誤り

`p3_b4_floor_artifact_issuer.py` の `_derive_identity` docstring が名指しする
`floor_pair_driver.py:759-776, 1136-1147` は artifact parser と binary/receipt 読取りであって、
「nonempty cells with calibration-consistent threads/workloads」の根拠ではない (段 2 が指摘)。
実装面差分 0 の裁定と両立させるため本 wave では直さず、次の一手へ回した。

## 一次資料

`verbatim/` に段 1 brief v2、段 2 plan とその投げ文、段 3 レンズ A・B とその投げ文、段 4 裁定の全文。

段 2 は 2 回投入した。初回 (job-id `...plan-e10ac41e...`) は投入 4 分後に親が b10 の反例を実測して
brief を v2 へ差し替えたため、親が SIGTERM で中断した (成果物なし、未完了)。
`verbatim/s2-plan.md` は再投入 (`...plan-5da9633c...`) の採用版である。
段 3 はレンズ A (lane=sol) 19 分、レンズ B (lane=luna) 19 分。いずれも
`tools/check_codex_output.py` rc=0。

`verbatim/s3-lens-a-correctness.md` だけは `git diff --check` に抵触した末尾空白を除く
可逆最小正規化を施した (可視文字不変)。原文は sha256
`5373a8925c4fe0609f80417ae482164ba4b654bc3c705ad1831c1072471b3daf`・21369 bytes、
正規化後は `df94b08ff5c499d89fd07ec96dff7bafffd56a9292f8f5f357e0f86977a9b41d`・21319 bytes。
除いたのは markdown 改行の半角空白 2 個 × 25 行 (計 50 bytes) で、対象行は正規化後の
3, 6, 9, 12, 17, 20, 25, 28, 31, 34, 39, 42, 45, 50, 53, 56, 59, 62, 65, 68, 71, 76, 81, 84, 87 行目。
復元はこの 25 行の行末へ半角空白 2 個を戻す。

**実装面の差分が 0 なので DW-S04 により変異 matrix を免除した。** 受入全走は免除していない。
