# 段 1 brief — [T-337] 正例 artifact の適格性権威

wave = `dev-wave-t337-qualification-authority` / branch = `worktree-dev-wave-t337-qualification-authority` (背景 job)。

## scope

**確定済みユーザー裁定 (worklog (121)):** [T-337] は択 (a) — **新 D で権威境界を定義し、
`artifact_role=qualification` を [T-318] 準拠で置く**。凍結 ledger の exact-one contract は改訂しない
(択 (b) は正しさ防壁の改訂であり独立 wave)。着手条件 = [T-338] Q1〜Q5 裁定後 ((134))、
(139)(140)(142) で 11/11 裁定完了、(179) で stale 確認済み。**Q11 の consumer 経路と一体で設計する**
(command 引数)。

**本 wave の scope:** (A) 権威境界の新 D (docs)。(B) その機械化のうち **DW-G04 を満たす範囲だけ**。
scope 外 = 正例 artifact そのものの作成 ([T-139]、代替 X 未設計)、RF 統計の計算実装 ([T-339])、
[T-318] の全 producer への閉表展開 (`DW-G03` の族一般化に当たり独立 2 例が要る)。

## 段 1 前提実測 (`DW-S01`。すべて本 wave で一次資料から実測)

1. **凍結 ledger は追記不能**。`patches/ledger.json` は entry 1 件、`izanagi-patch-ledger/v1`、
   `scope=registered-entries-only`。`silo_ladder_rung1_contract.py:518` が
   `initial ledger must contain exactly one entry` を要求し、同 `:538-550` が
   `recovery_measurement_eligibility=false` / `research_goal_eligible=false` / `pipeline_eligible=false` を
   exact 値で要求する。
2. **その bytes は pin されている**。`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json`
   の `binding.ledger.sha256` と `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1193` が照合する
   (`FROZEN_MANIFEST` 収載ではなく同一 repo 内の整合鎖 — D120 の訂正どおり)。
3. **適格性 field を判断に読む consumer は 0 件**。`recovery_measurement_eligibility` /
   `research_goal_eligible` / `pipeline_eligible` の非 test hit は ledger・contract・driver の
   **定数照合だけ**であり、これらを見て受理/拒否を分ける経路は実在しない。
4. **`artifact_role` は既に別意味で実在する**。`s8b_oracle_artifacts.py:26` の
   `EXPLORATION_ARTIFACT_ROLES = {"manifest","observations","verdict"}` は「exploration oracle 内の
   文書種別」であり、[T-318] の `{official,exploration,qualification,dry}` とは軸が違う。
   同名で置くと `D75` の二義化になる。
5. **権威語の先例が既に実装済み**。`orchestrator/qualification/` (T-126) は
   `authority: "evidence-only/no-promotion"` を control / marker / series / final / failure の
   全 schema で `const` 固定し、package docstring に
   `deliberately has no promotion or formal-campaign conversion API` と書いている。
6. **正例 artifact は未存在**。D126 の probe は W2 で逆転し不成立、[T-139] は代替 X の設計待ち。
   `artifact_role=qualification` を今日付与される **committed な artifact は 0 件** (T-126 receipt は
   repo 外の persistent root、s8b exploration oracle の committed 実体も 0 件)。

## 不変条件 (破ったら停止)

- `patches/ledger.json` と `patches/silo_ladder_rung1.patch` の bytes を 1 byte も変えない。
- `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` の bytes を変えない。
- exact-one contract の受理集合を緩めない (規律 2)。
- 適格性を producer の自己申告 field にしない ([T-338] Q11、D127 の恒真 gate 型)。
- 層 3 の calibration floor 閉表を広げない (Q11)。

## 親の provisional 裁定 (攻撃対象。各行末は「これを反証しうる最も安い実測」)

- **(P1) 新しい種別 field は `artifact_role` という名前を再利用しない。** 既存の
  exploration oracle 用 `artifact_role` と軸が違うため D75 に抵触する。裁定文の語は概念名であって
  識別子名の指定ではないと読む。*反証実測: `grep -rn "artifact_role" --include=*.py orchestrator/` で
  既存 hit が exploration oracle に閉じ、同一文書へ同居しないと示せれば同名で通せる。*
- **(P2) 権威境界は「宣言」と「状態」の分離である。** producer が宣言できるのは *種別* だけで、
  *適格性* は独立 validator が raw receipt から再計算した状態としてのみ存在する。
  ledger の `*_eligible` 3 field は権威ではなく歴史的宣言に留める。
  *反証実測: 3 field を読んで分岐する consumer が 1 件でも見つかれば、既に権威として機能している。*
- **(P3) 凍結 ledger には触れず、上書きする sidecar も作らない** (D120 決定 (2) の直接適用)。
  *反証実測: contract の exact 値要求を回避せずに entry を足せる経路が示せれば P3 は不要。*
- **(P4) 本 wave は正例 artifact を作らない。** [T-139] の代替 X が未設計であり、作れば D126 決定 (4)
  が禁じた事後調整になる。*反証実測: 3 arm・`env_tag`・測定 checkout を備えた committed artifact path が
  1 本でも実在すれば P4 は覆る。*
- **(P5) 実装面の発火は `DW-G04` で決める。** 段 2 が「今日その機構を通る live producer と実 artifact
  path (または計測 ID)」を file:line で示せた範囲だけ実装し、示せなければ **docs-only** とし
  `4→7→8→9` で閉じる。D120 決定 (3) が既に「負例の存在は条件付き機能の発火を正当化しない」と裁定済み。
  *反証実測: `orchestrator/qualification/` の producer が実際に書く path を 1 本示し、そこへ種別 field を
  足しても既存 receipt を無効化しないと示せれば実装できる。*

## 成果物影響 (`DW-G05`)

- (A) 新 D を書かない場合: 正例 artifact の適格性を誰も宣言できず、**certified 選択に回復率 (RF) の
  証拠を 1 件も載せられない**状態が続く (D126 の「これが解けるまで発行できない」が未解消のまま)。
- (B) 機械化を DW-G04 の外で実装した場合: 発火しない gate が受理集合に増え、材料レポートの
  proof chain に「謳うだけで発火しない保証」が入る (規律 3 違反の型、`docs/failures.md` の既出型)。
- (P2) を採らない場合: producer 自己申告が権威になり、**劣化版 arm を自称適格にして RF を偽装できる**
  (規律 2 への直接攻撃)。

## 分割方針と受入

- 段 2 = read-only codex 1 本 (file:line プラン)。段 3 = 敵対 2 レンズ (レンズ A = 権威境界の抜け穴と
  受理集合の変化、レンズ B = DW-G04/D75/D120 との整合と consumer 経路の実在)。
- 受理集合が変わりうる wave のため軽量版にしない (`DW-C00`)。
- 受入は Pegasus 計算ノードで pytest 全走 (runbook §7) + `python3 tools/check_docs.py`。
  docs-only 裁定なら影響テストと `check_docs.py` を親が走らせる。
