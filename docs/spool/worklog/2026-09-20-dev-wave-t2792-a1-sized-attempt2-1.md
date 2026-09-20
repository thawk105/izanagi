---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2792-a1-sized-attempt2
seq: 1
title: [T-2792] A-1 balanced5 sized attempt-0002 (D2172 項 2 の認可済み独立再現) を exact な認可 record 経由で 1 回投入し、3 workload とも valid で完走 — 登録済み解析は 3 本とも resolved-above-floor (符号 +/+/−、attempt-0001 と同じ)、variance_plan_breach は write-heavy / read-heavy で true、単独稿と attempt-0001 稿の並記を書き README の results 表へ 1 行 (docs のみ、branch worktree-dev-wave-t2792-a1-sized-attempt2、実装面差分ゼロ = 変異 matrix 免除)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数の逐語は insight `verbatim/T-2792-origin.md`) の範囲で 1 wave。裁定 = D2172 項 2 (択 1、attempt-0002 の 1 attempt
  限定)、gate の実装は entry 1736 (D2178、commit `886c19259` / `ec696308a`) で main に着地済み。一次資料は
  `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md` (時系列・受領証の複製・検算・レビューの逐語) と公開 leaf
  `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` (materializer が兄弟 dir に排他作成した README / receipt / result /
  .complete.json を byte 保持で複製、sha は `.complete.json` と一致)。稿は `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md`。
  decisions fragment は無し (新しい設計判断なし)。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/HANDOFF.md`。
- 起点 local main `fec4a818741e5464fffcd11e4b094c125dfe5280`。開始 gate rc 0 (18:05 JST)。投入の形: local main の detached submit-tree を job dir 下に作り
  (submodule 再帰初期化、CCBench 511c9538 tracked-clean、lock)、hydrate 2 箇所 (5 本 pin 一致)、`authorize-rerun` で durable base に record
  (`attempt-0002.authorization.json`、`source_commit` = submit-tree HEAD、`decided_on` は定数値 2026-09-20) → 既存 `submit` 1 回 → 3 job → complete →
  materialize (兄弟 dir) を同じ submit-tree から実行した。投入後に submit-tree へ書いたのは materializer だけ。
- **全層が実機で通り、attempt-0002 は完走した。** authorize-rerun rc 0 18:10:34 → submit rc 0 18:11:16 → job `13220` (write-heavy, bnode035) / `13221`
  (balanced, bnode039) / `13222` (read-heavy, bnode040) が driver rc 0 で 18:22:12 / 18:25:34 / 18:28:57 に終端 → complete rc 0 18:30:06 → materialize
  rc 0 18:30:21 (JST)。停止条件 (落ちたら再投入せず止める) は発動していない。balanced は request 作成から開始まで記録上 5 分 31 秒 (scheduler の Pre-running、
  他 2 job は 18:11:23 開始)。bench-start barrier は 18:18:44 に 3 本同時、bench 相は bench lock で balanced → read-heavy → write-heavy の順に直列。
- 登録済み解析の descriptive 出力: 対差平均 (variant − baseline) write-heavy +1,538,451.47 tps (baseline 2,431,737.4)、balanced +548,138.23
  (3,694,424.9)、read-heavy −560,565.60 (10,168,828.7)。分類は 3 本とも `resolved-above-floor` (B = 3%)、**`variance_plan_breach` は write-heavy と
  read-heavy で true** (標本 sd / 計画 sigma = 1.207 / 0.872 / 1.081)。6 arm とも verifier `0 anomalies`。schedule receipt の root seed・group_bits・
  block の物理順は attempt-0001 と 3 workload とも一致 (登録した同一配置で測定された)。束縛 9 file のうち driver 1 本だけが 143 行追加・3 行削除
  (認可 record の生成・照合、submit / materialize への接続、CLI 分岐。AST 帰属で確認) で異なる。
  **`formal=false` / `promotion_prohibited=true` の非認証 lane のままで、A-1 の充足・formal 化・attempt 間の再現性 (L-A1S-4 の解除)・3 本目の認可は
  判定しない。** 稿 §2.7 に attempt-0001 稿の値を並記したが、プールした推定量・差・比・再現判定は作らない (D1993 項 6)。
- 稿の値の再計算・現物 digest 比較は `extract.py` (insight `verbatim/extract-attempt2.md`)、稿中の sha256 全件と値の逐語存在は `draft_check.py`
  (113 項目 ok / 0 問題、fix 後の再走 `verbatim/draft-check-2.txt`) で機械照合。raw と公開 leaf の result.json の差は `materialization_evidence` と
  `limitations` 5 項目めだけ (構造比較)。レビュー出力の逐語 (`verbatim/out-review.md`) は行末 ASCII 空白 13 箇所を可逆正規化
  (`verbatim/whitespace-normalization.json` に原文 sha256 / byte 数 / 除去 suffix)。
- 段構成: 軽量版 (段 1 → 4「実装しない」→ 親の実測 → 稿 (親) → 6 read-only review 1 本 → 7 → 8 → 9)。段 6 レビュー (codex gpt-6-astra / medium、
  2 レンズを 1 本で、424 秒) は数表 (§2.7 の 6 行 × 8 数値、再計算、digest) 全件一致、所見 10 件 = **must-fix 1 (attempt-0001 の限定 20 件を「そのまま成り立つ」と
  継承した文 → 読み替え付き参照へ) / should 7 / nit 1 / 記録 1、refuted 0、全件反映** (driver 差分の所属関数を AST 帰属で書き直し、並記値の出所を
  公開 leaf に、「stdout / stderr 空」の対象を親 command に限定、他)。裁定の逐語は insight §9。
  README の results 表へ 1 行 (受入の owned-path には入れない)。stale 注記は依頼 scope 外なので足していない (版の更新は scope 外)。
- 受入全走は記録 commit 後の tip で 1 走 (結果は land の受領証)。submit-tree と耐久 base の attempt-0002 は原本として残置 (撤去は別途)。
- 限界・言わないこと: 図は作っていない (scope 外)。`variance_plan_breach = true` の原因は帰属しない。driver 143 行の差について、測定・統計関数に変更行が無いことを
  静的に確認しただけで実行時の等価性は検証していない。認可 record は署名ではなく「性能値を見た後の選択」を防ぐ装置ではない。
- 事故 (自分起因): 三軸語走査の出力を insight の verbatim に写したところ、その file 自身が三軸語を含み holdout hit になって受入 attempt 1 が赤 25 件
  (t080 系 `IZANAGI_FREEZE_HOLD` / floor campaign の `clean scan 拒否`、全件がその file を名指し) で rc 70。fix commit で file を削除し (走査結果は
  insight §11 の要約だけ)、走査の再走で hit が既知 4 file に戻ることを確認して受入を取り直した。受入 1 走 (25 分) を無駄にした。F1013 の同型再発 (failures fragment に再発追記)。
- 工数: codex 1 本 (review、16 call)、計算ノード job = 3 (workload 別) + 受入 2 走。

## 次の一手差分

### 完了

- [T-2792] attempt-0002 を認可 record 経由で 1 回投入し完走、公開 leaf・results 単独稿 (attempt-0001 稿の並記付き)・README の results 表 1 行を着地した。
  L-A1S-4 の扱いと図の要否は insight §10 の裁定パッケージ候補 (ユーザー手番)。
  remaining: none
  base: 5aa818ca53e46a3aef50c127cc1141e3b1a506d91b3d9b1c0a53c0ffd6079ba2
