# [T-1336] / [T-1337] / [T-1347] 2026-08-18 裁定の事前登録改訂を 1 回の再凍結で発効させた

`authority: none` / `default_effect: no-state-change` — 本書は記録であり裁定ではない。
可変状態の正本は `docs/worklog.md` 末尾。一次資料 = 同 dir の `verbatim/`。

## 1. 何を変えたか

2026-08-18 のユーザー裁定 3 件が要求する事前登録の改訂を、**1 回の再凍結**として発効させた。
scope は改訂文書と凍結 record までで、実装 (judge・registry・role payload・証拠契約) は後続 wave。

| 裁定 | 改訂 |
|---|---|
| [T-1336] | 最終判定から対象別 between-run floor との比較を撤去し、**反復単位の対比とその分散**を判定の基礎に置いた。性能主張は順位事実層と公式性能層の**二層**とし、選択評価は独立した**第三の表**とした |
| [T-1337] | 実走後の再走全拒否 (8b §9 項 8 の択 (a)) を **freeze-wide の事前割当 attempt registry** へ改訂した。測り直しの単位は落ちた構成だけ |
| [T-1347] | role payload の契約を、真の作業種別名を含まない**非干渉性**へ変えた |

成果物は 3 つ。`docs/phase3-8b-descriptor-design.md` の新規 §10 (旧本文は 1 byte も改変せず追記)、
`docs/phase3-8c-preregistration.md` の §3 / §4 / §5 欄名 / §6 / §7、および凍結 record
`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json`。

## 2. 判定の中身 (8b §10)

対は**同一 holdout・同一反復添字**の 2 構成で作る。schedule 上で隣接する行を対と見なさない。
反復添字は manifest の schedule row が持つ replicate 添字であり、observations 側の schedule 添字で
行の同一性と順序を照合する。完全 block を要求し、欠測・重複・不連続は判定不能へ倒す。
unpaired 推定への退避を禁じる。

**判定が消費するのは対差の有限な平均と有限な標本 SD だけ**である。共分散・相関・相対差・散布比は
併記するが主量へ昇格させない。走行内変動係数をそのまま閾値化する形は採らない — 対で測った
2 構成の差の分散は `Var(a) + Var(b) - 2 Cov(a,b)` であり、共分散を無視すると正の相関の下で
過大評価する。既存実装 (`s8b_oracle_n_pilot` の `_difference_summary` / `_sample_covariance`) が
直接の対差を出すため、この点は既に正しい。

数値 (`n` / 下限 / 上限) は**本 wave では凍結しない**。凍結したのは規則である — `n` は 2 以上の
整数で**観測反復数と exact に一致**しなければならず、下限は有限の正、上限は有限の非負、単位と
向きを同時に固定する。

## 3. 消える保証を名指しした

旧条件 3 とその周辺が要求していた 4 つが、新しい生値側の主張からは消える。
(i) 対象別 floor の超過、(ii) scale adequacy gate、(iii) oracle の一意最大の確定、
(iv) 両構成の eligibility。消えた分は、対差の分散が「この差は測定のばらつきより大きい」を
担う形へ置き換わる。

## 4. 段 3 / 段 6 の敵対所見

段 3 は 2 レンズとも NO-GO、段 6 も 2 レンズとも NO-GO、焦点再レビューも NO-GO を返した。
**親 brief の前提 3 件が反証された。**

- 「受理集合を広げない」— 床値比較の置換は定義上どこかで受理側を動かす。規律 2 が守るのは
  正しさの gate であって性能主張の閾値ではない。不変条件の方を訂正した
- 「テスト編集不要」— `test_s8c_preregistration_core.py` が §5 の欄名集合と欄名 hash を逐語で
  pin していた。実装面の差分 2 literal が生じ、Codex `role=author` を立てた (D95)
- 「8b 文書の編集は凍結鎖を壊さない」— 編集**前から** bytes pin は不一致であり、当該検査が
  2026-08-12 のユーザー裁定で保留中のため新たに発火しないだけである。保留は健全性の証明ではない

採用した主な所見 (いずれも「書いたが拒否力が足りない」型):

- 数値欄に型・範囲・単位・向きの制約が無く、恒真にも永久判定不能にもできた
- 登録 `n` と観測反復数の一致要求が無く、`n=8` を登録して 2 反復で判定を成立させられた
- 失敗分類が性能値の閲覧後に確定でき、良い attempt だけを採る経路が残っていた
- registry の唯一性が宣言だけで、複数 registry を走らせて良い方を公開できた
- role payload から作業種別名を落としても、`descriptor_binding` の
  `arm_binding_digest_sha256` が真の holdout と arm から導出されるため識別は残る
- 8b §7 項 3 と §9 前提段落に、床値と resume 全拒否を要求する生きた規範が残っていた

**refuted と裁定した勧告 1 件。** 段 3 レンズ B の「8b を編集する前に v2 再凍結・pin 更新・
保留解除後の再検証を完了せよ、できないなら 8b を編集するな」。不一致は編集前から存在し、
保留解除は `freeze_verification_hold.REASON.release` のとおりユーザーの明示命令のみである。
子の勧告で再武装しない。

## 5. 実測

- 焦点走: **371 passed / 0 failed** (事前登録 core + invariant、fix 2 巡後の tip)
- 8b 凍結テスト: **261 passed / 17 skipped** (oracle driver + ratified verify)。
  8b 文書の編集でこれらが赤にならないことを実測した — golden が持つ現行 bytes hash は
  受領証 `output/t080-migration/legacy-freeze-repin.receipt.json` の歴史値であり、
  照合先は basis commit の git blob である
- 変異 matrix: **baseline PASSED、KILLED 3 / 3、SURVIVED 0、MISMATCH 0、TIMEOUT 0**
  (`mutation-out.json`、dispatch runner、4 走行)。3 変異はいずれも事前登録 §5 の欄名集合の凍結が
  実際に発火するかを撃つ。`t1336.m3-doc-field-name-prewave-form` は **wave 前の実文書の形**
  そのものである
- **erratum (初回結果を消さない)。** 変異 matrix は 3 巡した。1 巡目 (`mutation-probe-out.json`) は
  全件 SURVIVED 期待の probe で観測 node を集めた (3 件とも MISMATCH = 検出力あり)。
  2 巡目 (`mutation-run2-out.json`) は m1 / m2 が KILLED、m3 が MISMATCH。原因は変異 node ID の
  2 空間で、harness の collection 検査は接尾辞なし形を要求する一方、失敗 node 抽出は
  pytest-xdist の `@<group>` 接尾辞付きで返していた。3 巡目で runner argv へ `-n0` を足し
  xdist を無効化して両者を同じ空間へ揃え、3 / 3 KILLED を得た。**期待 node 自体は 1 度も
  緩めていない**
- `python3 tools/check_docs.py`: rc=0
- g6 の `protected_sha256` は段 6 焦点子が独立に再計算して一致した

## 6. 残る限界 (後続 wave)

1. **証拠契約と評価器が旧意味のまま。** 条件 4 は `restart_forbidden`、条件 7 は `floor_refs` を
   要求し続ける。両条件は引き続き非充足で受理集合は広がらないが、追随 wave は
   `DECIDER_VERSION` を v3 へ bump し g7 を発行しなければならない。
2. **世代 record は承認した決定を指せない。** 番号は台帳統合時に採番されるため、record を
   導入する commit の時点には存在しない。`ruling_reference = D496` は**改訂の対象**を指す。
3. **世代 record は 8b bytes を束縛しない。** 両文書を確定してから record を 1 度だけ生成する
   運用で補うが、機械閉包ではない。
4. **数値欄の型検査は判定器に無い。** 担保は「欄が空であること」だけである。2 巡目の fix で
   条件 7 の充足要件へ validator の production 到達性を加えたため、validator 無しでは条件 7 が
   充足しない形にはなっている。
5. **文書は新規則・実装は旧規則の期間がある。** 最終判定層 `s8b_verdict` は依然として旧条件 3
   (床値超) と scale gate を使う。8b §10.6 が epoch 境界として、この期間の run を legacy・
   exploratory と定め、後から formal へ昇格・再解釈・混合しないことを規範化した。
