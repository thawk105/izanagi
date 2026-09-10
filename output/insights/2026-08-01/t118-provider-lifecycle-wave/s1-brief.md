# 段 1 brief — [T-118] production temp dir 後始末漏れ

repo root (wave worktree): `/home/SFC/tanab/github/izanagi/.claude/worktrees/worktree-dev-wave-t118-tempdir-leak`
base: local main `7b24f81`

## scope (親の裁定)

production の `tempfile.mkdtemp` のうち**後始末が存在しない 2 ファイル 4 箇所**に lifecycle を与え、
回帰 guard を新設する。

- `orchestrator/campaign/s8b_prediction_runner.py:1070` — `neutral_root` (prefix `s8b-selector-`)
- `orchestrator/campaign/s8b_prediction_runner.py:1138` — 呼び出しごとの `cwd-` (dir=neutral_root)
- `orchestrator/campaign/claude_projected_provider.py:144` — `neutral_root` (prefix `izanagi-projected-`)
- `orchestrator/campaign/claude_projected_provider.py:190` — 呼び出しごとの `cwd-` (dir=neutral_root)

## 実測済みの事実 (親が一次資料で確認、推測でない)

1. production の `mkdtemp` は 25 箇所。**23 箇所は `finally: shutil.rmtree(..., ignore_errors=True)` 済み**。
   後始末が無いのは上記 4 箇所だけである。
2. repo 全体で `neutral_root` に対する `rmtree` / `__del__` / `close` / `__exit__` /
   `TemporaryDirectory` / `weakref.finalize` は**ゼロ**である。
3. 現地観測 (`output/insights/2026-07-26_t057-test-suite-speed.md` §7): login node `/dev/shm` の
   残留 40,280 個のうち `s8b-selector-*` が **5,626 個**。これが production 由来の実測証拠である。
   残りの多数派 `izanagi_s4loop*` 10,192 / `izanagi_s8at*` 8,882 は**テスト由来**である。
4. テスト側の素の `mkdtemp` は 60 箇所 / 18 ファイル。
5. `orchestrator/tests/conftest.py` は TMPDIR を**意図的に設定しない**。撤去理由は tmpfs 使用量が
   user memory cgroup (Pegasus login 16 GiB) を課金する実測である。
6. `orchestrator/tests/real_repo_receipt_memo.py:104` は**呼び出し時**に `tempfile.gettempdir()` を
   引いて session cache path を作る。
7. 既存テスト `orchestrator/tests/test_s8b_prediction_runner.py:557,569-574` が pin する性質:
   `neutral_cwd` が空 / `neutral_root` が `gettempdir()` 配下・repo 外・`tmp_path` 外 /
   `mcp_config_path.parent == neutral_root` / `neutral_cwd.parent == neutral_root`。
8. 受入は `python3 tools/run_tests.py <args>` (login では計算ノードへ同期 dispatch)。
   login node での直接 `python3 -m pytest` は `hooks/guard_bash.py` が機械拒否する (実測)。

## 親の provisional 裁定 — **すべて攻撃対象**

- **(P1)** テスト側 60 箇所は本 wave の scope 外とし、新規タスクとして裁定パッケージへ返す。
  根拠: T-118 の記述が「production の後始末漏れ」であること、および 60 箇所の一括改変が
  テストの検出力を弱める経路を持つこと。**残留の多数派がテスト由来である以上、
  「T-118 を閉じた」と書けるかは疑わしい** — この点を攻撃せよ。
- **(P2)** 後始末機構は「明示 `close()` + `weakref.finalize` による fallback」で `neutral_root` を
  再帰削除する。呼び出しごとの `cwd-*` は**即時削除しない** (事実 7 の事後 assert と、
  失敗時の forensic を残すため)。root 削除で `cwd-*` はまとめて消える。
- **(P3)** conftest への TMPDIR 一括リダイレクトは採らない。根拠: 事実 5・6 より、
  テストごとに tempdir を変えると receipt memo の session cache が常に miss し、
  worklog (89) の 2.7 倍高速化が消える。また production の実 campaign 走行は pytest 外なので
  漏れが残る (隠蔽であって修正でない)。
- **(P4)** `__init__` が `mkdtemp` 後に例外を送出する経路 (repo 内判定・MCP config 検査・HOME 欠落)
  でも root を残さない。現状は残る。

## 不変条件 (破ってはいけない)

- `artifact_root` (payload / envelope = proof chain 材料) には**絶対に触れない**。削除対象は
  `neutral_root` 部分木だけである。
- 受理集合を変えない。拒否条件を増やしても減らしてもいけない。
- 事実 7 の既存 assert を弱めない・削除しない。
- `neutral_root` が repository 外である保証を弱めない。
- 削除は symlink を辿らない。`neutral_root` 外へ出ない。

## 成果物影響 (`DW-G05`、実装しなかった場合)

s8b selector campaign の 1 invocation ごとに空 dir が永続蓄積する。TMPDIR が tmpfs を指す環境では
user memory cgroup (16 GiB) を直接削るため、長走 campaign が途中で殺され、**certified 選択結果と
その proof chain が未完のまま失われる**。login node では他セッションの計測に外乱を与える
(実測 40,280 エントリ)。

## 成果物の形

- production 2 ファイルの差分 (最小)
- 回帰 guard test: 「provider を作って呼び、close 後に `neutral_root` が消えている」ことと
  「`artifact_root` が残っている」ことを同時に主張する positive control 付き
- 変異事前登録に基づく変異 matrix

## 並列分割方針

編集ファイル所有が素集合になる 2 単位に割れる:
- 単位 A = `orchestrator/campaign/s8b_prediction_runner.py` + その test
- 単位 B = `orchestrator/campaign/claude_projected_provider.py` + その test

ただし両者は同型の機構を持つため、共通ヘルパを導入するなら単一単位にする。どちらが良いかは
プランで判断せよ。
