単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s6-ruling.md — **末尾の erratum E1 が仕様。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s4-ruling.md — 事前登録 §3 (§3.1 の「builder の key ごと」)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/codex/s5-author-prompt.md — 段 5 の実装子契約 (**全文を継承する**)。
- 実データ (読むだけ、書くな): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/job-out-j1/ (job 1 の生データ)、/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/analysis/j1.json (現行 analyzer の出力)。
- 対象 (作業木 /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe、branch `author-t2273pc-probe-fix2`、基点 `2a1b83339`): `tools/t2273_replica_analyze.py` **だけ**。runner・plugin は変えるな (走行中の job が使っている)。

## 作業

erratum E1 の 2 点だけを直せ。

1. A/P の builder 比較 (`builder_keys_equal`・`one_builder_per_key`・`stat_digest_equal`・`visible_digest_equal` と、builder 別の出力・phase 集計) を **builder key だけ**で突き合わせる。その key を最初に要求した test の nodeid は出力に残すが、一致条件に使わない。key ごとに A/P 各 1 件の digest を要求する条件 (RB2) は維持。
2. 資源標本の不完全のうち、欠けている counter が `lustre: no readable llite/*/stats` だけの場合は必須観測の欠落から外し、`excluded_structural_missing` に理由付きで出す。他の欠測は従来どおり無効。

有効性の他の項目・判定式・閾値・既存 mode (`--pair-dir`・`--run-dir`) の出力は変えるな。

## 自己検査

- `python3 -m py_compile tools/t2273_replica_analyze.py`。
- 実データで `python3.10 tools/t2273_replica_analyze.py --ab-dir /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/job-out-j1 --json <作業木外の一時 path>` を走らせ、`validity.checks` と `failed` を報告 (job dir には書くな)。
- 段 5・fix1 の合成 fixture で、(a) 同 key・別 nodeid は一致、(b) 同 key で file digest が違えば無効、(c) llite 以外の資源欠測は無効、を確かめて報告。

## 出力形式

- `## 変更` (file:line)
- `## 自己検査` (実データの checks を含む)
- `## 総括` (3〜6 行)
