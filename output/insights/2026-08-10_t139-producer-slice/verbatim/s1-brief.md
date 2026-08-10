# 段 1 brief — [T-139] producer 実装 (vertical slice 1 本)

wave: `worktree-dev-wave-t139-producer-slice` / base main `58d1878d`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer-slice`

## 1. scope

裁定 §44 Q4 (a) が定める vertical slice 1 本を実装する。すなわち
(1) pilot 用 PBS 測定本体、(2) qsub 前の durable submission intent と台帳、
(3) job 側 preflight reject の collector、(4) binding を必須化した受領証 writer、
(5) schema-valid な受領証が end-to-end で 1 本出る正例。
これに §47 R6 (a)「受領証 schema は本 wave が発行し digest 固定」と、
追補 A §0 が本 wave の責務と明記する **envelope parser の発行**、
erratum §5 が本 wave の責務と明記する **erratum resolver** を加える。

**pilot は投入しない。** 本 wave の終端は「pilot 投入可否の判定材料」を返すところまでである。

## 2. 確定済みユーザー裁定 (一次資料で確認済み)

| 出典 | 内容 |
|---|---|
| §44 (2026-08-08) | Q1 (a) 閉集合は `a01`〜`a13`、§15 は erratum で明示 supersede / **Q2 (a) D234 の列挙は T-139 全段の完了範囲であり同一 wave の実装範囲ではない。段順序は D162・事前登録 §11 に従う** / Q3 (c) 記録項目は追補 A と同時裁定 / Q4 (a) 追補 A 先行 + 1 本の vertical slice |
| §47 (2026-08-08) | R1 (a) approval manifest + 承認済み erratum の exact set / R3 (a) `a13` 移管 + 原子予約台帳 / **R6 (a) schema は producer wave が発行し digest 固定** / R7 (a) 予備置換なし |
| §51 (2026-08-09) | 追補 A 一式 (再発行版・判定写像・erratum・record-items) を**一括承認、段階 2 発効**。producer 実装 wave 起票可 |
| [T-643] (2026-08-08) | (i) 認可の第一境界は **producer 側 sink**。投入 script の静的 admission は前置の補助 / (ii) trust root は**最小形** — 受領証に測定 checkout の HEAD hash を記録し validator が一致検査する。完全な偽造検出は見送り (D205) |

## 3. 実測した前提 (DW-S01 / DW-O09 / DW-O13)

| 事実 | 実測値 |
|---|---|
| `F` (D234 の fold commit) | `88d68f9127b31df5aafc3d59607896626a1652e8`。HEAD の祖先である |
| core blob digest | `F` 時点・HEAD 時点とも `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9`。**凍結は破れていない** |
| T-139 固有 public API | `resolve_effective_preregistration` / `PreregBinding` / `submit_pilot` / `verify_receipt` の実装は **0 件** (`verify_receipt` の同名関数は `campaign/t080_freeze_migration.py` にあるが別機構) |
| 既存被覆 (性質で検索) | closed schema + `additionalProperties:false` = `qualification/t126_*_schema.json` 6 枚 / create-only publish = `qualification/artifacts.py` / qsub 束縛 = `qualification/qsub_binding.py`・`submission.py` / job 側回収 = `qualification/collector.py` |
| `DW-O09` pin 閉包 | 対象 4 blob の path pin: `orchestrator/ tools/ hooks/` に **0 件**。core digest の literal: **insight 文書内のみ**。`FROZEN_MANIFEST` (23 件) に **未収載**。よって bytes の trust root は approval manifest + git blob identity だけである |

## 4. 新事実 (承認済み裁定の前提を覆しうる。段 4 で再裁定する)

- **N1. approval manifest が存在しない。** §51 の承認は `rulings-inbox` にあるだけで canonical 台帳へ未記録である。
  erratum §5 は「resolver は manifest から `approval_fold_commit` と blob identity を取得する。caller 引数・受領証からは取らない」を要求し、
  「manifest が存在しない状態で本 erratum を適用してはならない」と明記する。
  さらに `approval_fold_commit` は本 wave の land fold commit になるため、**実 repo の正例は land 前には原理的に成立しない**(循環)。
- **N2. 追補 A を名乗る blob が 2 つある。** 旧版 `output/insights/2026-08-08_t139-addendum-a/addendum-a.md` と
  承認済み再発行版 `output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md` は、**同一の `core_ref` 三つ組**を記す。
  manifest が blob digest で pin しなければ、旧版が §15 要件 4 を通ってしまう。

## 5. 親の provisional 裁定 (P) — 攻撃対象である

- **(P1)** 依頼文の「validator」= 受領証の **schema validator + 三つ組 / `measurement_head` 照合** (`verify_receipt`) に限る。
  D162 段 C の**適格性 validator** (pairing・順序均衡・cluster 適格性の再計算) と consumer の受理判定は
  §44 Q2 (a) により pilot の**後**であり scope 外。→ 依頼文と裁定の差はこの読み分けで解消する。
- **(P2)** 依頼文の「投入 script」= `submit_pilot` の静的 admission + qsub 前 durable intent + collector 配線まで。**実 qsub は行わない。**
- **(P3)** e2e 正例は hermetic fixture (合成 git repo + stub driver) で 1 本出す。実 repo 正例は N1 により land 後の判定材料として返す。
- **(P4)** PBS 測定本体は「1 pilot 割当て = 1 cluster = 2 workload × 6 順列 × 3 arm = 36 run」の
  schedule 生成 (`a09`)・driver argv 組み立て (`a07`)・run loop・`performance_started` marker (`a04`)・環境観測 (`a03`) を実装し、実投入はしない。
- **(P5)** approval manifest は docs 成果物として本 wave が起草し、canonical 台帳へ fold されることで発効する。
  resolver は manifest の path を定数で持ち、毎回 blob を読む (wave 310 §0 の裁定と同型)。

## 6. 不変条件 (緩めない)

1. **絶対規律 1** — 性能 arm は `trace_enabled:false` / `analysis_enabled:false` 必須、correctness は独立 build object・別割当て。
   `correctness_evidence[].build.binary.sha256` と `arms.*.binary.sha256` の**非同一性を schema 制約**にする。
2. 受領証に適格性状態・pairing の成否・受理状態・validator identity / 結果の field を作らない。top-level key は **18 のまま**。
3. 認可 sink = **受領証を永続化する関数自体**が `PreregBinding` を keyword-only 必須で受け、三つ組と `measurement_head` を照合してから publish する (T-643 (i)、B6)。
4. exact-key は欠落も余剰も解決失敗。検査に失敗したら期待集合を §14 基準へ**緩和せず** fail-closed (erratum §5 の 7)。
5. 凍結 blob の bytes を 1 byte も変えない。`DW-O10` の対象は本 wave が新設する producer の出力のみ。
6. `attempts[]` は intent の全 attempt を exact に被覆する。失敗投入の row を省略しない (§13 否定検査 1)。

## 7. 成果物影響 (DW-G05)

- **実装しない場合:** pilot は投入不可のまま。certified 選択の入力に本 study の cluster が 1 本も入らず、
  roadmap §「限定例外」の受理集合は空のままである。
- **半実装で land した場合 (wave 310 が blocker とした形):** 台帳だけが「producer 実装済み」へ進み、
  受理集合が空のまま pilot が走りうる。→ 本 wave は (5) の e2e 正例が出るまでを 1 単位とし、途中で land しない。
- **N1 を無視した場合:** manifest なしの resolver は「未承認の追補 A′ を `measurement_head` の祖先に置くだけで通る」経路を残す
  (erratum §5 が名指しする欠陥)。適格 cluster 集合が実装で分岐する。

## 8. 純増検出力

本 wave が新たに機械 kill できるようになるのは、事前登録 §13 の否定検査のうち
**1 (失敗投入を双方から落とす)・4 (適格性 field の追加)・6 (順序 / 待機の不一致)・7 (core と異なる blob の申告・閉集合外 field)・8 (環境判定の恒真化 / 失敗の写像先すり替え)** である。
2・3・5・9 は段 C validator と consumer の担当であり本 wave では閉じない (そう書く)。

## 9. 分割方針 (所有は素集合)

- **単位 A — 参照束縛層:** 追補 A envelope parser、erratum resolver、approval manifest 読取、`PreregBinding`、`resolve_effective_preregistration`。
- **単位 B — 受領証層:** 受領証 JSON Schema blob の発行 (1 枚・digest 固定)、schema validator、binding 必須 writer、`verify_receipt`。
- **単位 C — 投入・測定層:** durable submission intent 台帳、job 側 preflight reject collector、`submit_pilot` の静的 admission、schedule 生成 / driver argv / run loop。

A は B・C の入力 (`PreregBinding`) を定義するので**先行**させ、所有パス限定 patch を展開してから B・C を並列投入する。

## 10. 環境

- 実測・軽い pytest は login node (実効上限 16GiB、目標 12GiB)。受入全走は計算ノードへ dispatch し、直前に受入 lease を claim する。
- `DW-G01` の生死確認は R4 環境 probe (request `0:896504.nqsv`、判定 `feasible`) が既に済ませている。本 wave で新規 driver は作らない。
