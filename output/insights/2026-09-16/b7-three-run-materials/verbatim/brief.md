# [T-2670] 段 1 brief — B-7 の材料を 3 走行そろえて結果節へ落とす

wave: `dev-wave-t2670-b7-three-run-materials`
worktree (投入先 repo root): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials`
基準 commit: `262c2993e`

## 研究前進

論文 §8 の見送り台帳 B-7 (全 workload の退行込み報告) の材料を、3 走行そろった 1 稿にする。
完了判定は「A-2 (rr5 / rr50)・A-6 (rr95)・[T-1998] (balanced stock-inline 対) の生標本・効果・限定・
出所 SHA-256 を持つ統制稿が results 系列にあり、入口の表から引ける」こと。新規測定は不要。

## scope (docs のみ、実装面の差分 0)

1. `docs/paper-story/results/2026-09-16-b7-three-run-materials.md` を新設する。3 走行の権威 bytes から
   作り直して併記し、次を本文へ明記する。
   - A-1 が定める横断実験の完了ではない。
   - A-2 と A-6 の 2 protocol が 3 workload を覆い、[T-1998] が balanced をもう 1 度測った計 3 走行である。
   - A-1 の本走は未投入で、認可も据え置かれている (D1986 項 5)。
   - A-1 の探索走と pilot は `formal=false` で横断結論を禁じている。
2. 入口 `docs/paper-story/README.md` の「results 系列（`results/` サブディレクトリ）」節の表へ 1 行足す。
3. 段 7 の spool fragment (worklog)。

## 確定済みユーザー裁定

逐語は同 dir の `verbatim-d1631.md` / `verbatim-d1874.md` / `verbatim-d1986-1to5.md` /
`verbatim-d1993.md` / `verbatim-b7-item.md` にある。要点だけ再掲する (逐語が正本)。

- D1993 項 6: A-2 / A-6 / balanced stock-inline 対の 3 走行を 1 つの横断実験として集計しない。
  符号が旧環境と 3 workload とも一致したのは記述的照合であって再現判定ではない。
- D1993 項 3: 「性能を測った workload そのものでの certification が無い」但し書きは 3 workload とも
  外れるが、限定 4 つは残る。
- D1986 項 5: A-1 の本走の認可は据え置き。認可はユーザー手番。
- D1631: results 系列は append-only、1 file = 1 結果、新しい日付は一次資料全体から作り直す、
  数値・日付・status の出所は一次資料だけ、status は protocol の出力として書く (D12)。
- D1874: 事前登録前の生値 (balanced の 2026-09-07 の 2 値) を主張へ転用しない。
- 絶対規律 1 (観測者効果の分離) / 2 (正しさゲートを緩めない) / 7 (旧判定を取り消さない)。

## 不変条件

- 数値は 3 走行の権威 bytes から逐語で取る。**版・既存稿・本 brief の記述を数値の出所にしない。**
- 既存の凍結物 (2026-09-14 稿・版・figures・事前登録) の bytes を 1 byte も変えない。
- 新規測定を投入しない。3 走行をプールした効果・共通 outer status を作らない。
- 性能値を根拠に variant を採用してよいと書かない。
- B-7 の充足を宣告しない ([T-2610] は未裁定)。

## (P1) 親の provisional 裁定・攻撃対象

「B-7 の材料は 3 走行を 1 稿へ併記した新しい results 稿として作る」。対抗案は次の 3 つで、
いずれも段 3 で攻撃させる。

- (a) [T-1998] 単独稿だけを足し、横断は既存稿と版に任せる。
- (b) 2026-09-14 稿 + 版 §8 で材料化済みと結論し、新稿を作らない。
- (c) D1631 規則 2 の「一項目だけを直した差分改訂を新しい日付として置かない」に抵触する。

## (P2) 親の provisional 裁定・攻撃対象

新稿の単位は「失敗条件 (e) が報告を求める『全 workload』の集合 + balanced の 2 度目の走行」。
2026-09-14 稿が §0.1 で採った単位の拡張であり、新しい一般則を作らない。

## 着手前の実測 — 依頼の前提のうち覆ったもの

- **B-7 の材料化は 2026-09-14 に実施・着地済みである** (worklog 1488、成果物
  `docs/paper-story/results/2026-09-14-b7-all-workload-regression.md`)。依頼文はこれを知らない前提で
  書かれている。
- **ただし既存稿は [T-1998] を明示的に対象外にしている** (同稿 §0.1)。3 走行として数えた要約は
  版 §8 が持ち、results 系列には [T-1998] の材料が無い。ここが純増である。

## 変更面の実アンカー表

| file | アンカー |
|---|---|
| `docs/paper-story/results/2026-09-16-b7-three-run-materials.md` | 新規 |
| `docs/paper-story/README.md` | 「results 系列（`results/` サブディレクトリ）」節の表の末尾行 |
| `docs/spool/worklog/2026-09-16-dev-wave-t2670-b7-three-run-materials-1.md` | 新規 |

## 一次資料 (3 走行)

| 走行 | 権威 bytes |
|---|---|
| A-2 `t2364-20260907b` | `output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json` |
| A-6 `a6-20260908b` | `output/insights/2026-09-08_t2411-paper-story-a6-certification/certification.json` |
| [T-1998] balanced 対 | `/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced/result.json` (repo 外)。consumer 判定は `output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md` と `output/insights/2026-09-15/t1998-landed-main-recheck/README.md` |

## 受入・実測環境

Pegasus login node。計算ノード job は使わない。新規測定 0。
