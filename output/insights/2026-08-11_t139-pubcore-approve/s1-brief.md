# 段 1 brief — [T-139] 公表 core 段階 2 の承認 payload fold

- wave: `worktree-dev-wave-t139-pubcore-approve`、起点 main `73dad832`
- 種別: **docs-only** (実装面 0 byte 見込み)
- 裁定: 確定済み。一次控え `rulings-inbox/2026-08-04-rulings-session-5rulings.md` **§84**、
  canonical は worklog **412** (main `73dad832`)

## scope

**承認 payload の fold 1 本。**Q4 (a) / Q5 (a) の凍結承認を canonical 台帳へ機械可読 payload として
固定する。この payload を fold した commit が `F_p` になる。

- 作るもの: `docs/spool/decisions/` の decision fragment 1 件 + `docs/spool/worklog/` の worklog fragment 1 件。
- **作らないもの:** コード・テスト・script・機械設定 (実装面 0 byte)。追補 P の凍結。
  `F_p` の literal 書き戻し (先行 `F_r` も書き戻していない — §先行例)。
- **承認対象は 2 文書だけ** (新 core v2 + 追補 B v2)。追補 P 草案は承認対象では**ない**。
- **1 byte も変えないもの:** 上記 2 文書 + 追補 P 草案 + source core / 追補 A 再発行版 /
  新 core 初版 / 追補 B 初版の bytes。承認対象を編集したらそれは承認された bytes ではなくなる。

## 確定済みユーザー裁定 (適用対象)

| 問 | 裁定 | 本 wave での扱い |
|---|---|---|
| Q1 | (a) `b03` 縮小 + gate 喪失受容。**条件** = [T-793] へ「source 側の本走 gate 新設」 | **条件は履行済み** — rulings が main の [T-793] へ (iii) として追記済み (実測) |
| Q2 | (a) 新 core v2 を先に凍結承認、`F_p` 後の別 land で追補 P | 本 land は新 core v2 まで。追補 P は次 land |
| Q3 | (b) [T-793] が台帳実体を確定してから追補 P 凍結、pilot もそれまで不可 | payload に「追補 P 未凍結・pilot 不可」を明記 |
| Q4 | (a) 新 core v2 の exact bytes を凍結承認 | payload の `approved_blobs` へ三つ組 |
| Q5 | (a) 追補 B v2 の exact bytes を凍結承認 | 同上 |
| Q6 | (a) `p01` = 1 / `[1]` | **値の承認**として payload へ記録 (追補 P 自体は凍結しない) |
| Q7 | (a) `p02` = `0.05/(k(k+1))`、`α_pub` = 0.025、tail 破棄 | 同上 |

## 実測済みの前提 (段 1 前に測った)

承認対象の三つ組 (path / 内容 commit / sha256)。commit 時点の bytes を取り出して sha256 を再計算し、
作業木・HEAD と**完全一致**を確認した。両ファイルとも当該 commit 以後の変更は無い。

```text
publication_core_v2
  path   = output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md
  commit = 66934dda7f28893110a64a2011e213c2bda5e821
  sha256 = ad326dae70584d86470ff861e9bfd517b4f5b8406247f8047ae6cdb3ddabef67
addendum_b_v2
  path   = output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md
  commit = 25a66d2042a4fff1021e033c23fc2b814a735de9
  sha256 = ad12b60d29bb94ff67c3302b0779cb4765cd1c77768149d7cf6587698febb048
```

既存凍結物 4 件の bytes は worklog 411 の記録と一致 (凍結は破れていない)。
`p01` / `p02` の草案値は §84 の裁定値と逐語一致。

## 先行例 (D282 = land 1 の承認 payload)

`docs/decisions.md` の D282 が唯一の同型先行例。構成要素は
`decision_kind` / `forward_supersedes` / `preserved` / `target_core` / `approved_blobs` (path+commit+sha256) /
`erratum_application_order` / `composed_sha256` / `not_approved_*` (role 限定失効) /
`operational_boundary` / 台帳操作の canonical bytes。
**`F_r` を literal で書き戻した箇所は repo 内に存在しない** — D282 は「fold した commit を `F_r` と呼ぶ」と
定義するだけで、値は後続 manifest が持つ設計。本 wave も同じ形にする。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 承認 payload は **decision 1 件**にまとめる (新 core v2 と追補 B v2 を同一 payload)。
  *成果物影響:* 分けると `F_p` が 2 つになり、追補 P の `core_ref.commit` がどちらを指すか二義化する。
- **(P2)** 追補 B v2 は**初回承認**であり `forward_supersedes` は不要。D262/D282 の `approved_blobs` に
  `addendum_b` は無く、初版は decisions に 1 件も pin されていない (調査で hit 0)。
  *成果物影響:* 誤って失効文を書くと、存在しない承認を失効させる偽の記録が canonical に残る。
- **(P3)** 追補 B v2 の従属先は **source core**、新 core v2 は**独立 core** で追補 P の従属先。
  payload は 2 つの core を別 key で持つ。*成果物影響:* 取り違えると resolver が
  追補 B を新 core の追補として解決し、`main_admission` の閉じ方が変わる。
- **(P4)** Q6/Q7 の値承認は payload へ**値として**記録するが、追補 P の blob は承認しない。
  *成果物影響:* blob を承認すると Q2 (a) / Q3 (b) に反し、未確定 marker 入りの bytes が発効する。
- **(P5)** `operational_boundary` は D282 の逐語を継承する。*成果物影響:* 範囲を書かないと
  独立 clone や非協調 writer まで保証したことになる。

## 不変条件

1. 承認対象 2 文書・追補 P 草案・既存凍結物を 1 byte も編集しない
   (`approved_blobs` は **2 件**。追補 P 草案は編集禁止だが承認対象ではない)。
2. 実装面 0 byte。コード・テスト・script・機械設定に触れない。
3. 「凍結された」「発効した」と canonical へ書けるのは fold 後の状態についてのみ。
   fragment 本文は「本 payload の fold をもって発効する」と時制を保つ。
4. `F_p` の値を予測して書かない (fold 前には存在しない)。
5. 追補 P は凍結しない。pilot・本走は依然投入不可 (B8 (a) + Q3 (b))。

## 分割方針

docs-only だが**受理集合が変わる** (source core が受理する追補 B の blob digest が定まる) ため、
`DW-C00` により独立の敵対検証子を省かない。段 2 (プラン起草) 1 本、段 3 (敵対相談) 2 本、
段 6 (敵対レビュー) 2 本。実装面が無いため段 5 の Codex 実装子は置かない (親が docs 本文を書く)。
変異 matrix は `DW-S04` により免除 (kill を観測する実装面が無い)。

## 受入環境

Pegasus。受入全走は受入 lease を `claim` してから投入する (runbook)。
記録 commit を含む最終 tip で走らせる。
