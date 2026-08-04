---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t422-campaign-external-root
seq: 1
title: [T-422] campaign の実行先を worktree 外へ出す seam を実装した — F98 択 (iii)・防壁不変、変異 16/16 KILLED、受入 5574 passed / 19 skipped (コード + docs、branch worktree-dev-wave-t422-campaign-external-root)
---

## 本文

- **依頼はユーザー command 引数 `/dev-wave [T-422]` (背景 job)。** 2026-08-04 裁定
  (rulings-inbox 2026-08-03 §5 = F98 択 (iii)) の実装。設計は {{D:exploration-external-output-root}}。
  interface 変更 + gate 新設のため軽量版にせず、段 2 起草 + 段 3 敵対 2 レンズ + 段 6 敵対
  レビュー 2 本・fix 2 巡・焦点再レビュー 2 回 (実装面は全て Codex role=author)。
- **段 1 前提実測**: guard_bash の防護は repo 相対判定で、/work 配下の同形 path の rm は現行でも
  ALLOW (5 case 実測) — 外部化は guard に触れず成立。durable-root admission の利用者は official
  floor 経路のみで exploration は非接触。F98 の実測 dirt は全て layout root 配下。
- **敵対相談・レビューの主な real 所見と裁定**: 8c run_root の取り残し (採用・同 seam へ接続)、
  env 受理集合の過大 (採用・絶対 path / `..` 拒否 / 祖先 .git 拒否 / suffix symlink walk /
  euid 所有)、pin の module 二重 identity 分裂と thread 競合 (採用・sys singleton + lock)、
  WAL 直呼びの gate 迂回 (採用・materialization policy method 化。第 1 巡 fix の官民無差別 gate は
  official 過剰拒否の回帰と再判定し、official no-op / exploration gate へ是正)、テスト代表性
  (採用・fake evaluator の最小 run_campaign 完走 + replay 契約整合 + `_cwd` 内 `_verify_wave_clean`)。
  scope 差し戻し提案 (防護の実質縮小) は、裁定時点で既知の事実に基づくため停止条件を満たさず
  blocker 不採用 — 「外部 root は repo hook 防護外の使い捨て領域」を docs に明記して閉じた。
- **変異**: killer-node 単位の 9 グループ 16 変異 (runner を期待 kill node に絞り単一理由で
  検出力を証明する構成)。結果 16/16 KILLED (全て期待 node と一致)。
  post-resolve suffix 再検査の単独除去は等価変異
  (到達可能な区別入力は `..` 拒否と pre-walk が先に塞ぐ) のため登録せず、実効 gate へ再照準
  (F28 の型)。同 walk は walk-resolve 間の変化に対する冗長防壁として残置。
- **受入**: 焦点 13 node 緑 (job 887770.nqsv、計算ノード)、統合直後の全走 5548 passed /
  19 skipped / 0 failed。local main (T-244 P5 U-1 等) を 2 度目に取り込んだ land 直前の全走 =
  **5574 passed / 19 skipped / 0 failed** (job 888332.nqsv、bnode131、rc=0。増分は incoming の
  テスト追加)。既知赤 W1 (ruleops) は失効済みで deselect なしの全走、非発火。
- Pegasus スケジューラー全停止 (gen_S INA・231 件滞留) に段 6 で遭遇し、ユーザー指示で一時停止 →
  回復後に再開した。停止中は静的段 (fix2・変異 spec 再構成) を先行させた。
- F98 の恒久対応 (択 (iii)) と再発検知検査はこの wave で実装済み。canonical F98 本文の恒久対応欄は
  fold 不変条件により追記せず、本エントリを closure の正本とする。
- **段 8 自己改善: 候補 1 件を見送り。** 「段 1 前提実測に受入実行環境 (計算ノード queue) の
  生存確認を足す」は、本 wave でスケジューラー全停止に段 6 終盤で遭遇した実測に基づくが、
  停止中も静的段 (fix・変異 spec 再構成) を先行でき実害が限定的で、無人継続は DW-CTX の
  fail-closed 条項が既に覆い、DW-S01 の肥大化に見合わないため見送る。入口・reference の変更なし。

## 次の一手差分

### 完了

- [T-422] campaign 実行先の worktree 外部化 (F98 択 (iii)) を実装した。env seam
  `IZANAGI_EXPLORATION_OUTPUT_ROOT` + 検証 + process pin + container gate + 8c run_root 接続 +
  F98 再発検知検査 + docs 4 点。防壁 (guard_bash / dev_wave_land / durable_root) は不変。
  remaining: none
  base: 470aa46511031f91cc7471884e674a3a077ded62fe77328d13c65a3afd2f7b8a

### 更新

- [T-410] **P2・裁定済み → 着手不能の再開条件が 1 つ進んだ**: 再開条件 4 点のうち
  「T-422 実装」が完了。残りは T-419 U 系裁定 → 較正再取得 → campaign 再走 (witness 実装と
  同一 wave で evidence 再発行)。campaign 再走の wave は job script で
  `IZANAGI_EXPLORATION_OUTPUT_ROOT` を export すれば段 9 で止まらなくなった
  base: 4486b079c616d77d93fabd026ee9c0e4f969cea66c30c04fdfaa2ea3174abee1

### 新規

- {{T:official-campaign-root-externalization}} **P3・新規**: official / sweep 系 launcher
  (s6_sort_sweep / s8a_trigger_sweep、official campaign_layout) の実行先は [T-422] の
  exploration seam の対象外 (D123 が sweep producer を対象外とし、[T-422] 裁定の射程も
  exploration family のみ)。これらを wave worktree で実走すると F98 と同型で land 不能の
  まま。外部化するか、wave 実行を禁止と明文化するかの設計択一を検討する
- {{T:exploration-resume-root-manifest}} **P3・新規**: exploration campaign のプロセス跨ぎ
  resume は env 変化で root drift しうる ([T-422] 段 3 所見、process 内 pin は実装済み)。
  job/supervisor の永続 manifest に解決済み root を束縛し再入前に一致を要求する設計を検討する。
  発火 artifact が無い間は設計メモ (DW-G04)
