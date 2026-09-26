単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s6-ruling.md — **段 6 裁定 (直す所見 8 件と fix の形)。これが仕様。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/codex/s6-review-a-out.md、s6-review-b-out.md — 所見の原文 (file:line)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/s4-ruling.md — 段 4 裁定 (plan v2・事前登録 §3)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/codex/s5-author-prompt.md — 段 5 の実装子契約 (**全文を継承する**: 所有 path、守ること、自己検査、出力形式)。
- 対象 (作業木 /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe、branch `author-t2273pc-probe-fix1`、基点 `2ebf25e24`): `tools/t2273_replica_runner.py`、`tools/t2273_replica_plugin.py`、`tools/t2273_replica_analyze.py`。計測される側 (編集禁止): 同作業木の `orchestrator/tests/test_s8b_oracle_driver.py`、`orchestrator/tests/conftest.py` (早期 memo 待ち超過の実際の例外文・rc は conftest の該当関数から引け)。

## 作業

s6-ruling.md の表の 8 件 (RA1=RB1、RA2、RA3、RB2、RA5=RB3、RA4、RA6=RB4、RB5) をすべて直せ。所有 path はこの 3 file だけ。commit はするな (起動器が終端で記録する)。

- 既存の判定・出力の期待を緩めて通すな。有効性の条件を削るな (RA4 の P 固有の構造的欠測の除外だけは、どの欠測を除外したかを出力に明記して行う)。
- 既存 mode (`run`・`pair`) と既存 `--pair-dir`・`--run-dir` の出力を変えるな (RA1 の `T2273_LOCAL_OUTPUT_SOURCE` を None に戻すのはこの回復)。
- 仮想リスク向けの gate・検査・一般化を足すな。

## 自己検査

- 3 file の `python3 -m py_compile`。
- 段 5 の合成 fixture を拡張し、所見ごとに「直す前なら誤判定、直した後は正しい」入力を 1 つずつ作って `--ab-dir` / `--ab-series` を走らせ、結果を所見 ID ごとに報告 (RA1: 正しく記録された P env で有効、RB2: P 側 digest 欠落で無効、RA3: dir size だけ違う入力で有効・file mtime 違いで無効、RA5: 有効 2 対で判定保留、RA4: 必須欠測で無効、RA6: 実際の memo 超過文を含む log で除外・件数計上、RB5: key 別中央値が出る)。
- RA2: controller の hook 内に import が残っていないことを静的に示せ。
- login で pytest の実走は hook で拒否されうるので、suite は走らせなくてよい。実走できなかった検査は「実装済み・未実走」と書け。

## 出力形式

- `## 所見ごとの対応` (ID ごとに closed / partial と、変更箇所 file:line、自己検査の結果)
- `## 自己検査`
- `## 限界・未解決`
- `## 総括` (3〜6 行)
