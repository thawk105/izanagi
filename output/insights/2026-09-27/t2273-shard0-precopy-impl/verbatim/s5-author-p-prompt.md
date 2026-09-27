単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

作業木 (あなたが書いてよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-probe
所有 path (これ以外を編集しない): 作業木内の新規 dir `probe-t2273pi/` の下だけ (repo の tracked file は 1 byte も変えない。親が完成後に repo 外の job dir へ退避する使い捨ての計測 probe)。
docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s4-ruling.md — 親の段 4 裁定。**「計測の事前登録」1〜8 が仕様の正本。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/ — 移植元 (前回 wave の Codex author 製): `t2273lc_run_series.sh`、`t2273lc_run_measure.sh`、`t2273lc_run_warm.sh`、`t2273lc_gate.conf`、`t2273lc_ab_analyze.py`。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-probe/output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md §5 と verbatim/s4-ruling.md の「計測の事前登録」、verbatim/s6-ruling.md の erratum E1 — 移植元が実装している登録。

## 作ること

移植元 5 file を `probe-t2273pi/` に `t2273pi_` 接頭辞でコピーし、次だけを変える (他の挙動・検査・門番・台帳・hash 照合・有効性判定は移植元のまま):

1. job dir を `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl`、slug を `dev-wave-t2273-shard0-precopy-impl` に替える (全 file の直書きと import 名 `t2273lc_ab_analyze` → `t2273pi_ab_analyze`)。
2. E1 の B 追加 node: 定数 `E1_ADDED_NODE` をやめ、job dir の `expected-added-nodes.json` (`{"added_nodes": ["<nodeid>", ...]}`、親が投入前に A/B の login collection 差から書く) を読む。file が無い・空・形式不正は preflight で拒否 (系列を投入しない)。A/B の collection 差がこの集合ちょうど (B only = 集合、A only = 空)、共通 node の 3 shard 割付は完全一致、という E1 の判定式は移植元のまま、集合版にする。
3. 出力 (`markdown` と JSON) に事前登録 8 の 4 通りの記録区分を 1 行で出す: land 条件 (met / not-met / undetermined) と 5 分判定 (B の W_max 3 走の中央値 ≤ 300 秒、met / not-met / undetermined) の組から、`land-and-5min` / `land-5min-not-met-next-b` / `no-land-next-b` / `undetermined` のいずれか。5 分判定は各走の W_max の超過も一覧に出す。
4. 赤走の分類は移植元どおり親が書く `classification.json` だけを使い、自動で infra にしない (B の早期 memo 超過も同じ)。この点が移植元のままであることを確認して報告する。

## 検査

- `python3 -m py_compile` を全 .py に、`bash -n` を全 .sh に通す。
- 集計器の単体確認: 移植元の前回系列 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/runs/` を読み取り専用の入力として、`expected-added-nodes.json` 相当 (前回の追加 node 1 件) を作業木内の一時 dir に置いて集計器を走らせ、前回 insight の対差 (+19.111 / +19.679 / −4.341 秒、対率中央値 5.2 %、land not-met、B の W_max 中央値 348.387 秒 → 5 分 not-met) と一致することを確かめる。新しい 4 通り区分は `no-land-next-b` になるはず。**移植元の job dir へは書かない。**
- 走らせられないものは「実装済み・未実走」と書く。

## 出力形式

- `## 変更` (file ごとの差分要旨)
- `## 実走` (コマンドと結果)
- `## 移植元のまま残したもの` (門番・台帳・分類・有効性判定)
- `## 総括` (3〜6 行)
