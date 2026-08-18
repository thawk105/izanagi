# 8c 事前登録 §5 判定パラメータ欄の値 validator (2026-08-18)

wave: `worktree-dev-wave-s8c-section5-value-check` / 背景 job / [T-1352] の部分実装。

## この wave が入れたもの

`orchestrator/campaign/s8c_preregistration.py` に、§5 の
`反復単位対比の判定パラメータ (H1 / H2: n・平均差の下限・差の標本 SD の上限)` 欄へ記入された
canonical JSON を 8b §10.2 の制約で検証する validator を置いた。違反は
`Section5ValueViolation` (欄名・違反位置・違反軸ごとの理由コード) として `MarkdownContract` に載り、
production の parse 経路 (`parse_preregistration_markdown` / `parse_preregistration_at` /
`parse_preregistration_worktree`) から到達できる。

**記入済み判定と発効の連言式は変えていない。** 実効的な閂は repo の不変検査であり、生きた
`docs/phase3-8c-preregistration.md` の §5 に制約違反値が入ると受入が赤になる。設計理由は
decisions の当該エントリ (fold 後に採番) を参照。

## 検証した制約 (8b §10.2)

| 対象 | 制約 | 実装 |
|---|---|---|
| `n` | 整数かつ 2 以上 | `type(n) is int` で bool を弾き、`>= 2` |
| `delta_min` | 有限の正 | 数値型 exact + `math.isfinite` + `> 0` (負のゼロは落ちる) |
| `sd_max` | 有限の非負 | 数値型 exact + `math.isfinite` + `>= 0` (**負のゼロは受理**) |
| `unit` / `direction` | 単位と向きの同時固定 | 両方必須、非空白の文字列 |

`H1` / `H2` の exact key 集合は 8b が凍結した制約ではなく 8c 側の表現裁定である
(validator の docstring に明記)。`n` と観測反復数の exact 一致は manifest 側の責務であり、
値セル validator へは入れていない。

## 実測

- 焦点走 (bounded local、cwd=repo root): core 386 → 392 passed、invariant 18 → 19 passed、
  trial_registry + reflux_origin_binding 157 passed。既存テストの期待値・fixture は不変。
- 全史 provenance: 4051 件・新規違反なし。
- 変異 matrix (`mutation-ledger.json`): baseline PASSED・**10/10 KILLED**・SURVIVED 1
  (M11 = 有限性検査の冗長 gate、事前登録どおり)・MISMATCH 0。
  spec は `mutation-spec-final.json` (sha256=794393690d2d9eb77f6e9c4c31cc48cf3a8b34fa93352e9ef92896ea787f36c8)。
- **attempt 1 の erratum** (`mutation-ledger-attempt1-erratum.json`): 7 KILLED / 1 SURVIVED /
  3 MISMATCH。3 件はいずれも親が申告した期待 node 集合の不完全であり、変異は殺されていた。
  過剰拒否の正の対照 (M07) は 22 件を赤にし、想定より広い検出力を示した。

## verbatim

`verbatim/` に段 1 brief・段 2 プラン・段 3 レンズ B・段 4 裁定・段 5 実装子・段 6 レビュー B・
段 6 fix を置く。`s6-revA-UNACCEPTED.md` は `## 総括` を fence 内に書いたため機械受理されなかった
段 6 レビュー A の生出力である (**未完了扱い**。内容は real 所見 1 件を含み fix の入力に使った)。
段 3 のレンズ A は 2 回とも出力ゼロで落ちたため verbatim が無い (failures の当該エントリを参照)。
