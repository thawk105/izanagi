単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

作業木 (あなたが書いてよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-probe (branch `fix-t2273pi-probe-1`)
所有 path (これ以外を編集しない): 作業木内の `probe-t2273pi/` の下だけ (repo の tracked file は変えない、repo 外へ出す使い捨ての計測 probe)。
docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s6-ruling.md — 段 6 裁定。**fix P の対象は A4 だけ。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s6-review-a-out.md の A4。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s5-author-p-prompt.md — 段 5 の契約 (全文を継承)。
- 作業木の probe-t2273pi/ 全 file。

## 直すこと

A4: 系列投入前 (series の preflight と measure の投入前検査) に、job dir の `input/login-collection-A.log`・`input/login-collection-B.log`・`expected-added-nodes.json` の 3 つを必須にし、欠落・空・形式不正なら投入しない。A/B の login collection の差 (B only = `expected-added-nodes.json` の集合ちょうど、A only = 空) を preflight で検査する。集計 (analyze) も各条件の基準 collection にこの 2 file を使い、走自身の collection へ fallback しない。他の挙動は変えない。

## 検査

- `python3 -m py_compile`、`bash -n`。
- 前回系列 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/runs/` 等、読み取り専用) を作業木内の一時 dir に置いた入力 3 file で集計し、段 5 と同じ値 (+19.111 / +19.679 / −4.341 秒、`no-land-next-b`) が出ることを確かめる。入力を 1 つ欠いた場合・差が合わない場合に拒否されることも確かめる。**移植元の job dir へは書かない。**

## 出力形式

- `## 変更`、`## 実走`、`## 総括` (3〜6 行)
