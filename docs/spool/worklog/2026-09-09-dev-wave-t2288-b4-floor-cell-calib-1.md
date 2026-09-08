---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2288-b4-floor-cell-calib
seq: 1
title: [T-2288] B-4 権威 floor の発行は 3 案すべてが既裁定に阻まれると確定した — 現行 driver の workload 一致要求は D15 準拠であり欠陥ではない (docs、branch worktree-dev-wave-t2288-b4-floor-cell-calib、実装面差分 0・変異免除)
---

## 本文

**依頼前提の訂正。** 依頼文と起票文 (entry 1237 の [T-2288]) は「production 分析経路は `floor=None` を
渡すため、いかなる入力でも `floor_domain_error` を返す」を前提に「発行と配線」を求めた。**配線は
2026-09-08 に着地済みである** ([T-2424])。`p3_b4_material_report.py` は事前登録 §5 を読んで
`resolve_preregistered_authoritative_floor` を呼び、§5 の floor 欄が逐語 sentinel `未記入` のときだけ
`None` を渡す。それ以外は pin 文法・path・sha256・artifact schema を fail-closed で検査する。
**残っているのは発行だけである。**

**発行の前提が本 wave の外に 3 件欠けていることを実測した。** (a) accepted calibration は
`output/env/pegasus/calibration/registered/` の 2 件だけで、両方とも balanced (rr50) / t48。
read-heavy (rr95) と write-heavy (rr5) は 0 件 (tracked な `calibration/v2` 全 27 file を列挙して確認)。
(b) tracked な `s8b-binary-admission/v2` build receipt は 0 件。(c) D1641 が認可した 2 campaign の
実測は未実施。凍結 spec の実 instance も 0 件である。**よって本 wave で発行そのものは行えない。**

**親 brief の中心判定が段 3 で覆った。** 親は b10 の formal run provenance が 3 workload すべてに
同一 calibration を束縛し束縛 field に `workload` を含まないこと、および事前登録 §5 の
「校正済み `PerfConfig` … の artifact パスと hash」欄が単数であることを根拠に、
`floor_pair_driver` の workload 一致要求が repo の先例と整合しないと判定し、
段 2 plan もその線で「workload 一致要求だけを外す」案を選んだ。
**段 3 のレンズ A が D15 を引いて反証し、親が一次資料で確認した。** D15 の却下欄は逐語で
「D13 の『入力完全非依存』を維持し単一 calibration で済ませる: 飽和点が skew 依存と実測で割れた以上、
虚偽。代表 workload 署名で分けるのが honest」と書いている。D15 は calibration を
(env, thread, 代表 workload) でキーすると決めており、出力を workload 署名付きファイル名へ分ける
実装まで採用している。**現行の workload 一致要求は D15 準拠の正しい gate であり、欠陥ではない。**
b10 の先例は権威にならない — 親が実測: 同 provenance の `official_certification` は `false` である。

**3 案すべてを不採用にした裁定は {{D:b4-floor-workload-keying-is-d15-conformant}} と
{{D:b4-floor-cellset-not-expressible-in-one-spec}}。** near miss は
{{F:noncertified-precedent-used-to-widen-a-ruled-out-receiving-set}}。

**段 3 が独立に挙げ、親が採った所見。** レンズ A: `maxrss` は workload 実行後の peak RSS であって
table サイズ定数ではない / `noise_floor.cv` は within-run であり between-run floor の代用でない
(D1639) / 規律 4 の充足 (rr5・rr95 で L3 下限を満たす) は未証明 / 偶然 records が一致する任意 workload の
calibration を再利用できてしまう / `calibration/v2` の workload は任意の `dict[str,str]` で、cell 側の
exact 3-key 比較が唯一の拘束 / §5 の単数欄から「1 calibration でよい」は導けない / D1060 の向きと逆 /
D1759 の producer 版境界を潜脱する。レンズ B: この変更だけでは実 checkout の凍結 spec を作れず
DW-G04 の発火 artifact が無い / `SPEC_SCHEMA` を v4 へ上げると HMAC 順序 golden 2 箇所が確実に変わり、
段 2 plan の「golden は変わらない」は逆である / issuer test は全て実質 1 cell workload で
複数 workload の集約を通していない。

**覆した所見。** レンズ A の (γ'') (workload key のうち records に効くものだけ一致を要求する) は
不成立 — skew・rratio・rmw のいずれも実行時の resident peak とアクセス分布に効く。
2 window 間の calibration 差替えは spec hash が塞いでおり穴ではない。binder に例外の飲み込みは無い。
D1377 と floor §5.1 の直接緩和も無い。段 2 plan の「受入所要台帳を更新する」は不採用 —
親が実測: `conftest.py` は `nodeid_count != len(durations)` のときだけ台帳を破棄する fail-soft で、
消した nodeid の残骸が残っても件数は変わらず、新 nodeid は未登録なら既定 cost になるだけで gate は
赤にならない。台帳を触ると main 取り込みで必ず衝突するので触らない方が安い。

**親の誤りとして記録する 4 点。** (1) 「現行の workload 一致要求は欠陥」という判定そのもの。
(2) `_bind_checkout_inputs` を 1122-1196、cell loop を 1184-1196、`_derive_identity` を 737-812、
schema pin test を 628-634 と書いたが、正しくは 1122-1194 / 1181 開始 / 737-814 / 629-633 (段 2 が訂正)。
(3) 「既存 209 node」は陳腐化で、正しくは 210 (親が受入所要台帳で独立確認)。
(4) 生存確認の `ps` 出力に `head -4` を掛け、他 wave の行で埋まった結果を段 2 producer の死と
誤読した (再確認して生存を確認したので実害なし。再投入していれば job-id 衝突で 1 本無駄にしていた)。

**issuer docstring の行番号 pin は本 wave 以前から誤っている** (段 2 が指摘)。
`p3_b4_floor_artifact_issuer.py` の `_derive_identity` docstring が名指しする
`floor_pair_driver.py:759-776, 1136-1147` は artifact parser と binary/receipt 読取りであって、
「nonempty cells with calibration-consistent threads/workloads」の根拠ではない。
実装面差分 0 の裁定と両立させるため本 wave では直さず、次の一手へ回す。

**エージェント工数。** 段 2 は 2 回投入した。初回 (job-id `...plan-e10ac41e...`) は投入 4 分後に
親が b10 の反例を実測して brief を v2 へ差し替えたため、親が SIGTERM で中断した (成果物なし、未完了)。
再投入 (`...plan-5da9633c...`) が採用版。段 3 はレンズ A (lane=sol) 19 分、レンズ B (lane=luna) 19 分。
いずれも `tools/check_codex_output.py` rc=0。

**実装面 (D95 決定 2) の差分が 0 なので DW-S04 により変異 matrix を免除した。** 受入全走は免除していない。

## 次の一手差分

### 更新

- [T-2288] **P2・裁定パッケージ返却済み**: B-4 の権威 floor 成果物の発行。配線は着地済み
  ([T-2424])。残る発行は 3 案すべてが既裁定に阻まれると確定した
  (D15 / D1696 / 事前登録 §5 の単数 pin)。詳細と裁定パッケージは worklog の本エントリと
  {{D:b4-floor-cellset-not-expressible-in-one-spec}}。ユーザー裁定が下りるまで着手しない。
  base: b8f3ac06e41bb6e2073efb1917e830e0027d5393074c80f12ac7d7fe64941558

### 新規

- {{T:b4-floor-calibration-rr5-rr95}} **P2・新規**: read-heavy (rr95) と write-heavy (rr5) の
  t48 / pegasus 向け accepted calibration を calibrator で取得する。現在 accepted は balanced の
  2 件だけで、D15 が calibration を (env, thread, 代表 workload) でキーすると決めているため、
  B-4 の 3 workload セル集合はどの案を採っても 2 件不足している。D1641 決定 2 が測定を認可済みで
  操作は AI 委任なので、ユーザー裁定を待たずに走らせられる。
- {{T:b4-issuer-derive-identity-stale-lineno-pin}} **P3・新規**: `p3_b4_floor_artifact_issuer.py` の
  `_derive_identity` docstring が名指しする `floor_pair_driver.py` の 2 つの行範囲は、指す先が
  実際の根拠でない。行番号 pin を識別子参照へ替えるか正しい範囲へ直す。
- {{T:b4-issuer-multiworkload-identity-coverage}} **P3・新規**: issuer test は全て実質 1 cell
  workload であり、`workload_identifier` の集合集約を複数 workload で通していない。
  複数 workload の spec を受理する形が採られたときに、identity が workload を落とす退行を
  検出できない。
