# 段 1 brief — [T-139] producer 実装 (dev-wave 2026-08-08)

**正本:** 事前登録 core `output/insights/2026-08-07_t139-mainrun-design/preregistration.md` (凍結)、
D234 / D235 / D162、worklog (305)(306)(307) の T-139 / T-643 項。
**起点 main HEAD:** `6cc3e59a`。**wave branch:** `worktree-dev-wave-t139-producer`。

## 1. scope (事前登録 §11 の段 A = producer だけ)

1. **admission resolver** `resolve_effective_preregistration(repository_root, *, core_ref, addendum_a, addendum_b=None) -> PreregBinding`。
   D234 決定 (7) の (i)〜(vii) を全条件実装する。`measurement_head` は引数にせず `repository_root` の実 checkout から導出する。
2. **sink 側の認可** — `submit_pilot(*, binding, ...)` / `submit_main(*, binding, ...)` を、投入を実際に行う実体の
   **必須 keyword-only 引数**として強制する (T-643 (i)、D235 と同型)。呼び手の列挙で塞がない。
3. **受領証 producer** — §12 の必須項目を closed schema で書く。三つ組 (core / 追補 A [/ B]) + 発効 fold commit `F` +
   **測定 checkout の HEAD hash** を必須記録にする (T-643 (ii) の最小形)。適格性 field は未知 field として拒否する (D162 決定 2)。
4. **`declared_use_class`** — 閉集合 `{official, exploration, qualification, dry}` を宣言必須にし、新 D で名前を確定する ([T-479] 択 (b))。
5. **投入 script の静的 admission 前置** — T-609 の PBS wrapper 前置と同型の補助。第一境界ではない。
6. **`verify_receipt(*, binding, receipt)`** — 投入**後**に三つ組と `measurement_head` の一致だけを見る最小形。admission の前提に置かない。

## 2. scope 外 (実装しない。理由を worklog に書く)

- **適格性 validator の独立再計算と consumer の受理判定** — 事前登録 §11 の段 C。D162 決定 (10) の発火条件 (ii)(iii) が未成立
  (実測: 唯一の 3 arm 計測 `892042` は env_tag も attestation も持たない。`grep -rn "env_tag\|attestation"` = hit 0)。
- **追補 A / B の中身** (時間予算・待機・`q`・有意水準ほか) — 別 wave。本 wave は追補を**読む**側だけを作る。
- **pilot の実投入** — 追補 A 不在のため resolver は正しく拒否する。

## 3. 不変条件 (破ったら停止)

- 事前登録 core の bytes を変更しない。実測: 承認済み digest `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9` が
  fold commit `F=88d68f91` / HEAD / 作業木で一致。**core path への機械 pin は 0 件** (`FROZEN_MANIFEST`・generator hash pin・role key pin いずれも不在、`DW-O09`)。
- **作業木 bytes を固定する検査を新設しない** (D234 決定 (6))。main の前進を妨げる freeze を作らない。
- **`artifact_role` を再利用しない** — `orchestrator/campaign/s8b_oracle_artifacts.py` が探索 oracle 軸で使用中。同名採用は D75 の二義化 (`DW-O13`)。
- gate を恒真 deny にしない。**通る正例をテストで 1 本示す** (合成 fixture repo で追補 A を作る)。
- 絶対規律 1 (観測者効果) / 2 (正しさゲート) / 3 (シグナル後付け禁止) は不変。producer は適格性を宣言できない。

## 4. 成果物影響 (`DW-G05` — 実装しない場合に何が変わるか)

| 項目 | 実装しない場合 |
|---|---|
| 1 resolver | pilot が事前登録に束縛されず投入でき、`RF` の受理集合が事後選択で動く |
| 2 sink 認可 | 列挙漏れの経路から無認可投入ができ、認可の閉包がレビュー規律頼みになる (T-609 の実測型) |
| 3 受領証 | 段 C の validator が再計算する入力が存在せず、certified 選択が proof chain を持てない |
| 4 種別 field | 族の外延がファイル名列挙に戻り、新 producer が宣言なしで通る |
| 5 静的 admission | 投入前に落ちるべき不整合が job 内まで進み、割当てポイントを空費する |
| 6 verify_receipt | 受領証の三つ組と測定 checkout の不一致が検出されず、別 checkout 測定が混入する |

## 5. 親の provisional 裁定 (攻撃対象。段 3 で反証してよい)

- **(P1)** scope を段 A に限る (validator/consumer は段 C) — 根拠は事前登録 §11 と D162 決定 (10)。
  ただし D234「実装境界」は validator と consumer も producer 実装 wave の責務と書いており、**食い違っている**。
- **(P2)** `verify_receipt` は「三つ組と HEAD の一致」だけを見る形にする。適格性の再計算は含めない。
- **(P3)** 種別 field 名は `declared_use_class` を採る (T-479 の第一候補のまま)。
- **(P4)** 受領証の物理形式は既存 probe の TSV witness 群ではなく **単一 JSON** とし、`orchestrator/qualification/` の
  atomic publish と closed schema の既存機構を再利用する。
- **(P5)** 投入 script は既存 `tools/pegasus/probes/t139_positive_control_probe.{sh,pbs}` を**改造せず新設**する
  (probe は J=1 screening の凍結記録であり、本走 producer と役割が違う)。

## 6. 純増検出力 (既存被覆との差)

既存: blob@commit 読取 (`trial_registry._blob_at_commit`)、祖先検査 (`assert_prereg_ancestor`)、
capability 必須引数 (`s8c_preregistration.require_effective_preregistration`)、
単一 fd / 重複 key / symlink 拒否 (`certified_writer_preflight`)。
**純増**: 承認済み core digest (`F` 時点 blob) との一致検査、追補の従属三つ組一致、閉集合の exact-key 検査 (欠落も余剰も失敗)、
受領証の三つ組 + measurement HEAD 必須記録、`declared_use_class` 閉集合、投入 sink の必須 binding。

## 7. 環境

実測・受入は Pegasus (受入全走は計算ノードへ dispatch)。本 wave は**計測を行わない** — pilot 投入は scope 外。
