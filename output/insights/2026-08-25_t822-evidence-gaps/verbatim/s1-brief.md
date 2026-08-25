# [T-822] 段 1 brief — 8c 正式受入の証拠欠落

## scope

裁定 D863 (2026-08-25 ユーザー裁定、択 (a)) が挙げる 3 件のうち、段 0 実測で
**(1) 層 3 鎖の必須呼び出し・(2) 宣言 arm と実走 arm の同一性・(3) レポート間の
計測対象一致は、いずれも 2026-08-17〜18 に実装済みである** ことが分かった。
判定器 (activation_report_at @bb7753fa) でも C02 / C09 / C10 は合格終端に達している。
D863 の典拠は 2026-08-11 の insight であり、その後の実装を照合していない。

同じ変更単位と指定された **[T-1211] だけが実際に開いている**。
本 wave の実装 scope はこれ 1 件に絞る。

- **実装対象:** 受入 (`assert_trial_registry_acceptance`) の世代数検査を、
  report と journal の自己整合に加えて、**受入自身が再読する campaign WAL / 層 3 鎖の
  射影から独立に再導出**して照合する。
- **実装しない:** (1)(2)(3) への追加コード。既に成立している条件へ重複実装を書くと
  受理集合を動かさずに複雑さだけ増える (C11 の同型事故)。
- **scope 外 (裁定パッケージへ):** C03 (manifest-registry-proof-undefined)、
  C05 (schedule-schema-absent)、C08 (prereg-binding-proof-undefined)。
  これらが正式系列 ([T-1135]) の実際の残 blocker である。

## 確定済みユーザー裁定

- D863: 3 件が閉じるまで正式系列へ入らない。**本 wave はこの裁定を覆さない。**
  3 件が既に閉じているという実測は、裁定の禁止を解く根拠として親が使ってはならない。
  ユーザー再裁定へ返す。
- D95: 実装面は Codex role=author が書く。親は直接編集しない。
- 絶対規律 2: 検査を通すために受理集合を広げない、恒真な保証を置かない。

## 不変条件

- `orchestrator/campaign/autonomous_trial_completeness.py` を**触らない**。
  稼働中の t1176-t1230 wave が同 file を編集中 (段 0 で実測)。
- receipt schema version・exact key 集合・canonical preimage を変えない。
- 新しい非 certifying 理由コードを足す場合、既存 receipt の bytes を変えない形にする。
- 世代数の不一致は「受理集合を広げる」向きへ倒さない。不一致は非 certifying。

## 成果物影響 (DW-G05)

実装しない場合: 正式受入が「2 世代走った」という主張を、走行側が書いた宣言 field と
その journal 射影からしか得ない。走行側が両方に同じ誤った値を書けば certified 受入が通る。
実装した場合: certified 受領証の受理集合が狭まる (WAL / 層 3 射影と世代数が食い違う
run が非 certifying になる)。既に certifying な run の値は変わらない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 世代数は cross-binding 射影の `build_records` / `bench_records` から
  cell × generation の対応として再導出できる。→ 導出不能なら DW-O13 に従い採用せず、
  測った値域を裁定へ書く。
- **(P2)** 実装面は `trial_registry.py` 側に置ける (autonomous_trial_completeness.py を
  触らずに済む)。→ 触らざるを得ないなら t1176-t1230 の着地待ちへ切り替える。
- **(P3)** (1)(2)(3) は本当に閉じている。→ 段 3 の 1 レンズはこの主張の反証だけを任務とする。

## 成果物の形

- 実装 1 単位 (trial_registry.py + テスト)。
- 裁定パッケージ: D863 の前提が古いこと、C03/C05/C08 が実残 blocker であること。

## 分割方針

段 2 plan 1 本、段 3 敵対 2 レンズ (1 本は (P3) 反証専任)、段 5 実装 1 本、
段 6 レビュー 2 本 + fix。
