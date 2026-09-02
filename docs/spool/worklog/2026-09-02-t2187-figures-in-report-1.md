---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: t2187-figures-in-report
seq: 1
title: [T-2187 追補] 測定報告に図 3 枚を埋め込み、図を repo へ入れた — 作った図を成果物に載せていなかった (docs のみ、branch worktree-t2187-figures-in-report、実装面 0 につき変異 matrix 免除)
---

## 本文

- **ユーザー指摘:** 「レポートにグラフが載ってて欲しい」。
  worklog 1204 の wave は図 3 枚を生成し、レイアウト検査まで通し、親自身が中身を確認までしていたのに、
  **報告本文にも会話にも載せなかった。** 「図を作った」「検査に通った」とだけ書いて、
  肝心の図を成果物へ入れていない状態だった。
- **セッション異常 (自分の欠陥):** 成果物を作ったことと、それを受け手へ届けることを別に扱えていなかった。
  この wave の主張のうち 2 つは、順位表より図のほうが速く伝わる —
  段 1 は「既定の窓の行だけが崖で、窓を広げた行は平坦」という縦方向のコントラスト、
  段 2 は「no backoff が崩れ、調整済みが崩れない」という交差そのものである。
- **用語の齟齬も 1 件。** 報告で「認証されていない」を開かずに繰り返し、ユーザーから
  「私が認証していない扱いなら bug では」と指摘された。`docs/glossary.md` の
  `certify / certified` は**正しさゲート (直列化検証) を通したか**であって承認の話ではない。
  依頼文自体が「数値は認証されない」と書いていたので用語の使い方は一致していたが、
  **ユーザー向けの文章で内部語を一度も開かなかったのは規律違反**である。
  以後は「直列化検証を通していない」と書く。
- **置き場所の判断。** insight の file 名は変えず、兄弟 directory
  `output/insights/2026-09-02_cicada-adaptive-three-constants-figures/` へ PNG / PDF / provenance を置いた。
  directory 形式 (`<name>/README.md`) へ移すと、既に land 済みの D1505 / D1506 / worklog 1204 が
  参照する `.md` path が stale になるためである。
  **`docs/paper-story/figures/` へは置かない** — そこは論文図の場所で、本測定は直列化検証を
  通しておらず論文図として使える段階にない。
- 図のバイナリを追跡するのは既存規約に沿う (`docs/paper-story/figures/` は PNG/PDF/provenance を
  追跡、`output/campaigns/*/reports/*.png` も追跡されている)。
- 数値・結論は 1204 から一切変えていない。**変えたのは提示だけである。**

## 次の一手差分

### carry

- [T-2189]
