# [T-692] R3 — 受入全走の xdist 分配と walltime (2026-08-10)

wave: `dev-wave-t692-r3-xdist-walltime` / branch `worktree-dev-wave-t692-r3-xdist-walltime`

## 読む順序

1. `package.md` — **裁定パッケージ (R-a〜R-e)**。依頼への回答と、要裁定の 5 問。
2. `s1-measurement.md` — 段 1 の実測所見。wall の律速の分解。**段 3 の指摘による訂正を含む。**
3. `s1-brief.md` — 段 1 brief (親の provisional 裁定 (P1)〜(P5) を含む)。
4. `verbatim/s4-ruling.md` — 段 4 裁定。全 15 所見の real/refuted と採否、変異事前登録。
5. `verbatim/` — 段 2 プラン、段 3 敵対相談 2 本、段 5 実装、段 6 レビュー 2 本 + fix 4 巡 +
   焦点再レビュー、junit 解析子の報告。

## 実測の要点

| 指標 | 値 |
|---|---|
| baseline wall (bnode055、7685 passed、`--junitxml` 付き) | 1407.97 秒 |
| testcase の直列総和 | 16534.55 秒 |
| 実効並列度 | 11.74 worker 相当 = 48 の 24.5% |
| `real-repo` group の直列和 (= critical path 下界) | 1388.80 秒 / 43 node |
| うち上位 2 node | 680.23 + 653.50 = 1333.73 秒 (group の 96.0%) |
| 受入 (本 wave の変更あり、7746 passed) | 1247.95 秒 |

**wall は `real-repo` group の直列和でほぼ完全に説明でき、worker は余っている。**
律速の正体は実 repo の T-080 receipt 解決で、1 走に**構造的に 2 回**要る。
詳細と、なぜ分配側の変更が恒久策にならないかは `package.md` §2。

## 一次データ

- `mutation-spec.json` / `mutation2-ledger.json` — 変異 matrix (8 件、SURVIVED 0)。
- junit XML (`junit-baseline.xml`、1.1MB) と解析スクリプトは repo 外の job dir に置いた
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t692-r3-xdist-walltime/`)。
  集計結果の全量は `verbatim/analyze-out.md` に含まれる。

## この材料が主張しないこと

- 本 wave の変更による wall 短縮量。変更なし 2 走 = 1408.04 / 1379.26 秒、
  変更あり 2 走 = 1265.09 / 1247.95 秒で方向は一貫するが、
  **ノード差と走行間変動を分離していない**。試験数も 7685 → 7746 へ増えている。
- 段 2 が出した「約 876 秒」という期待値。段 3 の両レンズが条件値と判定した。
- 670 秒帯が共有解決の待ちであると確定したこと (開始時刻と lock owner が未記録)。
