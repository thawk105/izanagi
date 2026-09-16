# 段 2・3・4 の逐語保存と正規化

authority: none
default_effect: no-state-change

本 dir は [T-2588] wave (`dev-wave-t2588-k2-loop-roundtrip`) の段 2 plan、段 3 敵対相談 2 本、
親の段 1 brief と段 4 裁定を逐語で保存したものである。可変状態の正本ではない。

| file | 中身 | 受理検査 |
|---|---|---|
| `brief.md` | 親の段 1 brief | — (親が書いた) |
| `plan.md` | 段 2 plan (codex `stage=plan`, `sandbox=read-only`, `reasoning=medium`) | `check_codex_output.py` rc=0 |
| `consult-a.md` | 段 3 相談 A (lane `sol`、整合と実効性のレンズ) | `check_codex_output.py` rc=0 |
| `consult-b.md` | 段 3 相談 B (lane `luna`、正しさ境界と主張範囲のレンズ) | `check_codex_output.py` rc=0 |
| `ruling.md` | 親の段 4 裁定 | — (親が書いた) |

## 可逆最小正規化 (DW-S07)

`git diff --check` の行末空白に抵触したのは **`plan.md` の 1 file だけ**で、各行末の空白 / tab を
除去した (可視文字不変)。他の 4 file は無変更である。

- `plan.md`: 原文 sha256
  `2b86bd3b68bb98ec4478e76ff1fe726cb6ef511a8983602ccc953c714094eefb` / 19951 bytes。
  正規化後 sha256 `cd38a6e2eeffd8cfd5d7141c309aa8e197256178cd90cbcb4352a55dc959c461` / 19941 bytes。
  抵触行は 7, 9, 11, 93, 95 の 5 行。`diff -w -B` で原文と一致する (実測 rc=0、2026-09-16)。

原文は repo 外の job root
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/` にも保持している。

## 裁定の要約 (詳細は `ruling.md`)

段 3 の 2 レンズは**独立に同じ real 所見へ収束した** — critic の診断は次生成の型付き入力へ届かない。
親はこれを採用し、完了条件を「本走の実測結果を入力にした proposal-2」へ改めた。
新しい機構は 1 つも足していない (D2044 項 9 逐語「新しい機構は足さず、既存経路だけで行う」)。

refuted は 7 件 — 正しさの受理集合を広げる経路の不在、知識源への指示混入の不在、
repo 内の新規実装 file の不要性、[T-304] の owned-path 侵犯の不在、実測から型付き入力への
写像と単位の一致、同一 campaign ID でも skip が起きないこと、pin・verifier の修正の不要性。
