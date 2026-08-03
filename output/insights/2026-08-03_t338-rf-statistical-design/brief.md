# 段 1 brief — [T-338] RF 統計設計の裁定パッケージ (dev-wave 2026-08-03)

`authority: none` / `default_effect: no-state-change` — 本書は wave の作業 brief であり、
可変状態の正本 (worklog 末尾) ではない。

## scope

**RF (recovery fraction) の統計設計 5 点について、ユーザー裁定パッケージを 1 本起草する。**
実装面はゼロ (コード・テスト・gate・artifact をいっさい作らない)。段 5・6 は対象外、
終端は「ユーザー裁定待ち」である。

確定済みユーザー裁定 (archive worklog (121)): **[T-338] は択 (a)** — RF 統計設計のうち
**paired session 差による floor の取り方**を正例より先に裁定する。**残る統計設計 4 点も
同じパッケージで提示する**。したがって 5 点すべてが本 wave の scope である。

対象 5 点 (出典 = `docs/decisions.md` D120 却下案 (b)):
① paired block の帰無分布 ② 多重比較 family ③ between-run floor の種類
④ 区間推定と `<0`/`>1` の帰属 ⑤ 選択的欠測。

## 不変条件

1. **規律 2 を緩めない。** floor は「差が信用できるかの下限」であり、RF を成立させるために
   下げてよい旋回ノブではない。floor を小さくする選択肢は、推定量が実際に取る誤差構造と
   一致することを根拠にしてのみ採り、一致が壊れた場合の fail-closed をセットで書く。
2. **D120 決定 (3) を維持する。** RF の compute 実装は正例 artifact が 1 本できるまで land しない。
   本 wave は設計の裁定案を書くだけで、実装しない (`DW-G04`)。
3. **D126 決定 (4) を維持する。** 受理条件は事前登録し、結果を見てから変えない。
4. **既存の `BETWEEN_RUN_CV = 0.030` と既存レポートの bytes・受理集合は本 wave では動かさない。**
   Phase 2 `compare()` Gate1 の √2 保留 (`docs/archive/audit-2026-06-30.md:309-310`) は
   既存レポートの比較可能性に触れるため、本 wave の射程外である。
5. docs-only。凍結成果物・proof chain・certified 選択・変異 matrix・受入全走はいずれも射程外。

## 親の provisional 裁定 (すべて攻撃対象)

以下は親の暫定案であり、段 3 のレンズは**この brief 自体**を攻撃してよい。

- **(P1) 点 ③ = 種類**: RF の floor は **paired session 差 `d_j` の散布**から取る。arm 別
  marginal CV の和は採らない。かつ **RF の paired floor と `compare()` の unpaired floor を
  別名の別量として持ち**、同名識別子 (`noise_cv`) へ両方を渡せる現状の二義性を塞ぐ (`DW-O13`)。
  paired が成立する前提 (全 arm が同一 allocation・同一 session 内・interleave) が崩れた
  measurement では paired floor を使わせず unpaired へ fail-closed で戻す。
- **(P2) 点 ① = 帰無分布**: 正規性を仮定せず、**session を交換単位とする permutation/randomization**
  で帰無分布を作る。session 内 arm 順序の randomize を事前登録の要件に含める。
  session 数が小さいと達成可能な最小 p が離散的に下限を持つ事実を明記する。
- **(P3) 点 ② = 多重比較 family**: **primary endpoint を事前登録で 1 つに絞り**、
  family = 「1 つの recovery 主張が跨る (workload × arm) の全セル」とする。補正は **Holm**。
  BH (FDR) は「多数発見中の偽陽性割合」の管理であって単一の受理判定の誤り率管理ではないため採らない。
- **(P4) 点 ④ = 区間と `<0`/`>1`**: 区間は **session を resample 単位とする bootstrap** で取る
  (比の区間なので Fieller は感度分析として併記)。**分母の区間が 0 を跨ぐ間は RF を報告しない**
  (定義未成立)。clamp しない。**`RF>1` を「回復」と「新規改善」のどちらにも帰属させない** —
  RF は「stock 超過」とだけ述べ、帰属は別証拠 (機序 + ablation) を要求する。
- **(P5) 点 ⑤ = 選択的欠測**: 欠測は **session 単位で落とす** (arm 単位の部分欠測を許すと
  paired 構造が壊れる)。落とした session 数と理由を成果物 field に必ず残し、**事前登録した
  欠測上限を超えたら救済せず判定不能へ倒す**。
- **(P6) 射程**: 本裁定は RF に限る。Phase 2 Gate1 の √2 問題は別 ID として立て、本 wave では動かさない。

## 親が実測した前提 (段 3 のレンズは値と一般化も攻撃せよ)

- 現行 floor の産出 = `orchestrator/campaign/between_run_floor.py`、消費 =
  `orchestrator/calibrator/stability.py` の `compare()` Gate1、wired 値 =
  `orchestrator/campaign/p2_2.py:62` の `BETWEEN_RUN_CV = 0.030`。
- 実測済み fresh same-window between-run CV (`output/env/linux-baremetal/calibration/`、8 session):
  write-heavy 0.666% (abort 82.0%)、balanced 1.067% (abort 70.5%)、read-heavy 0.110% (abort 16.0%)。
  within-run はそれぞれ 2.194% / 1.071% / 0.194%。**wired 3.0% はこれらより大きく、
  cross-campaign の genuine between (別時間窓) 側から保守的に採られている。**
- **`DW-O13` の入力実在確認**: 既存 calibration artifact が持つのは
  `between_run.session_throughputs` = **単一 arm (baseline) の session median 8 個**だけであり、
  **arm 次元も session index の arm 間対応も存在しない**。paired 差 `d_j` を作れる実 field は
  現時点でどの成果物にも無い。したがって点 ③ の裁定は producer 側の出力要件とセットになる。
- 先例: D104 決定 (4) が「同一 allocation 内の paired 比較」を既に承認済みの型として挙げている。

## 成果物影響 (`DW-G05`)

5 点が未裁定のままだと、**正例 artifact の受理条件 (`all_pass`) を書けない** — 分母の識別可能性
判定が floor の種類に依存し、同じ raw session から正例の成立/不成立が反転しうる
(段 3 レンズ B の成果物影響そのもの)。結果として [T-139] / [T-144] / [T-337] / [T-339] が
着手できず、RF を物差しに使う予定の材料レポートに RF 欄を作れない。

## 分割方針

- 段 2: read-only codex 1 本で、5 点の選択肢と file:line 根拠を起草させる。
- 段 3: read-only codex 2 本を並列 —
  レンズ A = 統計的妥当性 (推定量・帰無分布・多重性・区間・欠測の各案が本当に正しいか)、
  レンズ B = プロジェクト整合と実効性 (既裁定との衝突、規律 2/3、入力 field の実在、
  producer/consumer 不在、親の実測値と一般化)。
- 段 4: 親が real/refuted を裁定し、最終パッケージを確定する。段 5・6 は実装面ゼロのため飛ばす。
