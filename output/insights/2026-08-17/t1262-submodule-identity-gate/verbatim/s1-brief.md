# 段 1 brief — [T-1262] submodule の内容同一性 gate

wave: dev-wave-t1262-submodule-identity / branch: worktree-dev-wave-t1262-submodule-identity
worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1262-submodule-identity
base main: 5a19b8ab / 実測日時: 2026-08-17 00:50-01:10 JST / 環境: Pegasus login (worktree 内)

## 1. scope

`tools/codex_reasoning_ab.py` の snapshot oracle に、submodule の**内容同一性**照合を足す。
対象は `_submodule_worktree_state` (`:915-981`) と、それを消費する `_submodule_inventory`
(`:984-1037`)・`_expected_filesystem_files` (`:1240-1257`)・`_preflight_snapshot_relocation`
(`:1059-1120`)。scope 外: `collect_run` / `make_packets` の中間層再検証 ([T-1263] が別項)。

## 2. 親が実測した現行挙動 (probe は repo 外 job tmp、`probe_t1262.py` / `probe_t1262b.py`)

合成 snapshot (root + `deps/child` submodule) を `_seal_git_object_closure` で封緘したのち攻撃し、
`verify_snapshot(..., spec=...)` を呼んだ結果。`closure` は `git_object_closure: true`
(**production の既定値**。`_snapshot_spec` は同 key を持たず `expected.get(..., True)` で True)。

| # | 攻撃 | closure 有効での結果 |
|---|---|---|
| A | 空 CCBench: `read-tree --empty` + worktree 全削除 + `submodule.<n>.ignore=all` + 再 seal | **ACCEPTED** (index 0 行・worktree は `.git` のみ) |
| B | 改変: worktree の `child.txt` bytes 差し替え + `ignore=all` | **ACCEPTED** |
| C | index 追加: HEAD^{tree} に無い `extra.txt` を index+worktree へ + `ignore=all` | **ACCEPTED** |
| D | marker 差し替え: `.git` を `../../.git/modules/rogue` (admin の複製) へ | **ACCEPTED** |
| — | A から `ignore=all` を外した形 | REJECTED (`dirty set mismatch` / `numstat mismatch`) |
| — | A から再 seal を外した形 | REJECTED (`git fsck exited 2` / unreachable 1) — 内容照合ではなく偶発 |

**`ignore=all` は封緘後に設定できる。** `_seal_git_object_closure` (`:1123-1141`) は seal 時に
`submodule.*` の config section を消すが、`verify_snapshot` は不在を再検査しない。

## 3. 既存被覆 (性質で検索。機構名では引いていない)

- 「index と HEAD^{tree} の照合」: `rev-parse HEAD^{tree}` の全 hit 18 件はすべて他 module か
  test 側で、`codex_reasoning_ab.py` 本体は 0 件。`diff-index` / `diff-files` も本体 0 件。
- 「worktree bytes と index の照合」: `_expected_filesystem_files` は index から**パス集合だけ**を
  導き、`_filesystem_file_set` のパス集合と比べる。**bytes を比べる経路が無い。**
  さらに期待値を index 自身から導くので、index を改変すると期待値も一緒に動く (循環)。
- 「`.git` marker と admin dir の束縛」: `_submodule_worktree_state` は `admin_dir` を計算するが
  `admin_exists` (未初期化判定) にしか使わず、initialized 枝で marker と束縛しない。
  `_preflight_snapshot_relocation` は marker の相対性しか見ない。
- **純増検出力 = 上表 A〜D の 4 vector。** 既存の検査はいずれも 1 件も落とさない。

## 4. 不変条件 (緩めてはならない)

- 正しさ gate を緩める変異は不採用 (規律 2)。既存の拒否理由文字列・rc (`RC_SNAPSHOT=20`) を弱めない。
- 拒否は**署名で書く** — 通る正例を 1 つ添える (`DW-S04`)。
- 凍結 pin 閉包 (`DW-O09` 実測): `submodule_manifest_sha256` を pin する成果物は
  `output/` 配下に**コード外 0 件**。`output/insights/2026-07-30_t181-reasoning-ab/schedule.json` と
  `output/insights/2026-08-09_t181-certified-rerun/schedule.json` が同 field を**保持**するが、
  live consumer は `run-outputs` の rollout だけで (`test_codex_reasoning_ab.py:78-84`)、
  `verify_manifest` / `_replay_manifest` をこの 2 つへ当てる test は無い (実測 hit 0)。
- ただし `_replay_manifest` (`:3886-3890`) は `_canonical_bytes(replay_oracle)` と保存済み
  oracle bytes の**完全一致**を要求する。oracle の bytes を変えると過去 manifest の replay が壊れる。

## 5. 親の provisional 裁定 (P1〜P5。**攻撃対象**)

- **(P1) oracle の bytes を変えない (reject-only)。** `submodules` 行の schema
  (`path`/`gitlink_commit`/`initialization`) を増やさず、照合は gate 内で完結させる。
  → 正当な snapshot の `submodule_manifest_sha256` と `manifest_sha256` が不変になり、
  受理集合は**単調に縮む**。対立案「三者照合の証拠を manifest へ記録する」は proof chain の
  証拠力を上げるが §4 末の replay 一致を壊す。どちらが正しいか攻撃せよ。
- **(P2) 三者照合の実装形。** (a) index↔HEAD: `git diff-index --cached --quiet HEAD --`
  (`write-tree` は**禁止** — sealed closure へ object を書き `git fsck --unreachable` を赤にする)。
  (b) worktree↔index: **stat に依存しない** — index の各 blob id と worktree file の実 hash を
  突き合わせる。`git diff-files` は size/mtime を保つ改変を見逃しうるので単独では不可。
  (c) marker↔admin: initialized 枝で `_git_dir(candidate) == admin_dir` を要求する。
- **(P3) `submodule.*` config の再検査を足す。** 攻撃 A〜C はいずれも封緘後の `ignore=all` に
  依存する。gate 側で内容を直接見るなら不要かもしれない — 二重防壁か冗長かを裁定せよ。
- **(P4) 適用範囲は snapshot 側 (`_submodule_inventory`) と source 側
  (`_init_submodules_from_local_source` `:715-762`) の両方。** source 側の空 CCBench は
  clone 元として使われるので、そこも締める。
- **(P5) 費用は無視できる。** 実 CCBench (405 file / 3.4MB) で `HEAD^{tree}` 解決 0.010s、
  `diff-index --cached` 0.008s、`diff-files` 0.218s (cold)、index 読み 0.005s。
  実 snapshot の submodule repo は 3 件 (2026-08-16 insight 実測) なので上限でも 1 秒未満。

## 6. 成果物影響 (`DW-G05`)

実装しない場合: 空または改変済みの CCBench を読んだ試行が `initialization: "initialized"` として
`submodule_manifest_sha256` に載り、trial ledger・材料レポート・proof chain 上で「pin 済み」と
区別できなくなる (受理集合が誤って広い)。実装する場合: 上表 A〜D が `RC_SNAPSHOT` で拒否され、
正当な snapshot の oracle bytes は (P1) の下で不変。

## 7. 成果物の形

1. `tools/codex_reasoning_ab.py` の gate 実装 (Codex author、D95)。
2. `orchestrator/tests/test_codex_reasoning_ab.py` へ A〜D の拒否テスト + 通る正例。
   既存 fixture `_synthetic_verify_snapshot_with_submodules` (`:2004`) を土台にする。
3. 変異事前登録に **A (空 CCBench が通る現在の形)** を必ず含め、修正後に拒否されることを示す。
4. worklog に**受理集合の変化**と費用を実測値で記録する。

## 8. 分割方針

編集面が単一 module + 単一 test file なので、段 5 は実装子 1 本 (所有 = 上記 2 file)。
段 6 は敵対レビュー 2 本 (レンズ: 正しさ境界 / 受理集合と consumer 波及)。
