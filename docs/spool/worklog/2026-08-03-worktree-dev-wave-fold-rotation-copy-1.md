---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: worktree-dev-wave-fold-rotation-copy
seq: 1
title: fold 機構の裁定 3 件を 1 wave で実装 — land 不能の rename/copy 検出、`完了` の構造 field、見送り台帳への発火記録追記 (コード + docs、branch worktree-dev-wave-fold-rotation-copy)
---

## 本文

- **ユーザーが scope を 1 件から 3 件へ拡張した。** 理由は「いずれも同じ畳み込み機構を触るため、
  別 wave にすると三つ巴の衝突になる」。[T-357] 着手後に [T-352] / [T-358] を追加し、
  段 1 brief から回し直した
- **敵対検証が land を阻む blocker を見つけた。** ローテーションが起きても、取り込んだ fragment 5 件 +
  本 wave の記録では **104,462 bytes** で閾値 100,000 を超え、`rotation-capacity` で**計画段階から
  失敗する**。`_rotate_worklog` が元 worklog の最新 entry を必ず残す設計だったため。
  分割点を projected worklog に対して選ぶよう直した。**単体テストは全緑のままで、
  実 land の経路を追った静的検証だけがこれを捕まえた**
- **親の brief に誤りが 2 件あり、いずれも敵対検証が突いた。** (a) ローテーション閾値を「行数」と
  書いたが実際は bytes (`WORKLOG_ROTATE_BYTES = 100_000`)。(b) 不変条件を「他 caller の挙動を
  変えない」と書いたが、valid rotation の受理は checker と daemon でも意図して変わる
- **現行の拒否は防壁ではなく偶然だった。** 移動割合 50% では `C` が出ない (親の実測)。
  つまり閾値未満なら同じ形が今も通る。「移動検出を外すと受理集合が広がる」という所見は
  real だが、**元から防壁として機能していなかった**と裁定した
- **実装と検査を別の Codex author に書かせた。** 段 3 が「同一 worker だと、仕様が塞いだ decoy が
  実装とテストの両方から同時に漏れる」と指摘したため。段 6 はこの分割の後でも
  fence 内 decoy の別 variant (list container 相対の 4-space fence) を見つけており、指摘は有効だった
- 敵対レンズは段 3 が 3 本、段 6 が 4 本。real 21 件・refuted 2 件・scope 外へ送り 3 件。
  逐語と変異台帳は `output/insights/2026-08-03_fold-rotation-copy/`
- **[T-059] の真時 action (実装前の変異事前登録) を履行した。** 24 変異を実装前に登録し、
  段 6 の指摘で本走前に 2 件を再照准した (erratum は insights)
- **修正の証拠は dry-run と実 land そのものである。** 取り込んだ fragment 5 件 + 本 wave の記録で
  fold を計画すると、`rotation_path = docs/archive/worklog-phase3-0802-117-121.md`、
  `projected_worklog_bytes = 93277` (閾値以下)、target に `docs/phase3.md` が入り、
  fragment 順は ruling 5 件 → 本 wave になった。修正前は entry 121 を移せず 104,462 bytes で
  失敗する構成である
- 受入全走 = Pegasus gen_S 計算ノード request `878425` で **5263 passed / 19 skipped**。
  変異本走 = 事前登録 24 件が**全件 KILLED・期待 node 一致** (T-357 分 10、拡張分 14)。
  拡張分の初回は MISMATCH 5 件で、いずれも gate は壊れてテストが検出しており原因は親の
  期待 node の精度不足だった。初回台帳を残したうえで是正して再走した
- **段 8 の改善候補 3 件は docs 予算超過で保留した。** `docs/dev-wave/**` は既に hard ceiling
  近傍で、実測に基づく 3 行の追記が予算を割った。自己改善契約に従い変更を取り下げ裁定へ回す
- 素材: 「単体テストが全緑でも実経路の失敗が残る」ことを、同じ wave の中で 2 度観測した。
  1 度目は本タスクの発端 (実 land だけが落ちた)、2 度目は上記の rotation-capacity である

## 次の一手差分

### 完了

- [T-357] fold の形検査から rename/copy 検出を外し、ローテーションを伴う fold を land 可能にした。
  `--no-renames` を明示し、冗長な R/C 特判を削除。`_landed_fold_output_path` の `R` 分岐と
  `_diff_entries` の 2-path parse は予備防壁として残し、単体テストで発火を固定した。
  remaining: none
  base: a6676c6c390a91cad56232506e9badf1c6db9e931098a780ce2222b7104e2d9e
- [T-352] `完了` item に `remaining: none` を必須化した。field は item 末尾の機械 field 群の中だけで
  数え、本文・fenced code block・HTML comment 内の同形行は field と数えない。
  既存の禁制語検査は残した。
  remaining: none
  base: 62a6450ee4ee027f39ba7ad040005430eb51475a89231c43f1582787936a889a
- [T-358] fragment に `見送り追記` 節を新設し、見送り台帳の既存項目の先頭行の行末へ追記できる
  ようにした。対象探索は fence と comment を不可視化して行い、fragment 順に逐次適用する。
  慣行は変えず手段だけを補った。
  remaining: none
  base: cce7f7f2a76b950dcfb92c38d17798b75e5a37cd74bdcfdcf4c444209925ae46

### 新規

- {{T:dev-wave-reference-budget-overflow}} **P3・新規・裁定待ち**: 段 8 で実測した dev-wave の
  運用の穴 3 件を、`docs/dev-wave/**` の予算超過で reference へ統合できず保留した。
  (a) workspace-write の codex 子も、計算ノードへの dispatch が sandbox 内で認証エラーになる環境では
  テストを実走できない (`DW-O05` は read-only 子の話しか書いていない。本 wave では実装子・fix 子
  5 本すべてが該当した)。(b) 変異本走中に untracked を 1 つ作ると harness が停止し、止めた後に
  commit すると HEAD 束縛で resume できなくなる (本 wave で 1 回やり直した)。(c) session 終了で
  子 process が落ちる環境では切り離して起動する必要がある。3 行の追記で
  `docs/dev-wave/mutation.md` が 4056/3750 bytes、`operations.md` が 8629/8400 bytes、
  合計 25845/25200 bytes になったため、自己改善契約に従い変更を取り下げた。
  **[T-328] の外出し (入口 + 条件付き reference) が入れば同じ枠で解ける**ため、そこへ相乗りするか、
  予算値の独立審査を行うかの裁定が要る

### 見送り追記

- [T-058] 2026-08-02 の D125 / D127 / D128 と 2026-08-03 の fold 機構 wave で計 4 回再発火した (述語 `safety_gate_changed`)。既裁定どおり追加裁定はせず記録のみで、いずれの wave も網羅率を観測していない。記録経路が無かったため滞留していた分をまとめて書き戻した。
- [T-059] 2026-08-02 の D125 / D127 / D128 と 2026-08-03 の fold 機構 wave で計 4 回再発火した (述語 `validator_or_rejection_gate_changed`)。fold 機構 wave は真時 action を履行し、24 変異を実装前に事前登録した。記録経路が無かったため滞留していた分をまとめて書き戻した。
