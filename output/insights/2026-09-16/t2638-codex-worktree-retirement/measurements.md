---
authority: none
default_effect: no-state-change
---

# [T-2638] 親の実測 — `.codex/worktrees/` の実態 (2026-09-16 JST、Pegasus login node)

これは一次資料である。取得方法と限界を先に書く。**数字を使う前にこの節を読むこと。**

## 取得方法と既知の限界

| 走査 | script | 実行した command | 限界 |
|---|---|---|---|
| census | `census.sh` | `git --no-optional-locks -C <wt> status --porcelain --ignore-submodules=all` | **submodule 内の変更を数から落とす。** 削除 (`D`) された file は `[ -f ]` を通らず判定されない。`missing` 列は**追跡済み変更 (`^ *[MARC]`) だけ**を対象にしており untracked を見ていない |
| 着地照合 v1 | `reach_all.sh` | `git hash-object` → `git log refs/heads/main -1 --find-object=<blob> -- <path>` | **取り下げた。下の「照合器の欠陥」を読むこと。** |
| 着地照合 v2 | `reach2.sh` | `git hash-object` を `git rev-parse refs/heads/main:<path>` と直接比較 (O(1))。不一致なら `git log -m --find-object` で履歴探索 | `--untracked-files=all --ignore-submodules=none`。`sed 's/^...//'` は空白入り path・quote された path に弱い |
| 占有 | `occ_all.sh` | `tools/check_worktree_occupancy.py <wt>` (権威 CLI、D391) | rc0 は削除の必要条件であって十分条件でない (tool 自身が開示)。**親の census が対象を argv 参照している間は自己マッチで occupied になる** |
| 厳密版 | `strict.sh` | `git status --porcelain=v1 --untracked-files=all --ignore-submodules=none` | 権威ツール `tools/dev_wave_cleanup.py` と同じ flag。census の甘さを埋めるために後から追加した |
| 所有 | `owner_map.py` | 全 `manifest.json` の `sessions[].recorded_cwd` を突合 | `/work/1/SFC/tanab/dev-wave-jobs/` 配下しか見ていない。背景 job の artifact root は job dir 内にあり走査対象外 |

**すべて読み取りのみ。`.codex/worktrees/` の中身は 1 byte も変更していない。**
`--no-optional-locks` を付けて index の書き戻しを避けている。

## 0. 母集団は走査中に動いている — すべての件数は時点値である

| 時刻 (JST) | `.codex/worktrees/` | `.claude/worktrees/` |
|---|---|---|
| 2026-09-15 (依頼時) | 58 | — |
| 2026-09-16 04:20 | 67 | 9 |
| 2026-09-16 04:55 | 67 | 17 |
| 2026-09-16 05:18 | **71** | 18 |

**04:55 → 05:18 の 23 分で codex worktree が 4 件増えた (約 10.4 件/時)。**
依頼が記録する「100 分に 21 件」(12.6 件/時) と同じ桁である。2 時点の観測であって
誤差付きの率推定ではないが、**流入は走査中も続いている**という事実は確かである。

この結果、走査ごとに母集団が異なる。`census` / `strict` / `reach2` は 67 件を対象にし、
`xy` はより後の時点を見ている。**表どうしの件数が一致しないのは、計算誤りではなく母集団の移動である。**

## 1. 母集団

- `.codex/worktrees/` = **67 件** (2026-09-16 04:55 JST)。依頼時 (2026-09-15) は 58 件。
- `.claude/worktrees/` (wave 本体) = 04:20 JST に 9 件、04:55 JST に **17 件**。
  **時点依存が大きいので、件数比を論拠に使ってはならない。**
- branch 接頭辞: `impl-*` 37、`fix-*` 21、`codex-*` 5、`acceptance-*` 1、
  `merge-*` 1、`mut-*` 1、`mut2-*` 1。
- `git worktree lock` 済み = 8 件。
- 1 件あたり 734 MB / 26188 file (`a5f-f480` 実測)。67 件で約 49 GB / 約 175 万 file。
  **ただし filesystem は 85 TB 中 3.3 TB 使用 (4 %)、inode 17 % 使用。容量は律速ではない。**

## 2. 汚れ (census、追跡済み変更のみ)

- clean = **1 件** (`t1851-c3c-detail`)。dirty = 66 件。
- 変更 file 総数 173、untracked 総数 6。
- 追跡済み変更 173 件の内容 blob は**全件が object DB に存在する** (`git cat-file -e` 成功)。
  **この列は untracked を見ていないので「全部着地している」の根拠にしてはならない。**
- HEAD が `refs/heads/main` の祖先 = 65 件。非祖先 = 2 件
  (`prov-incr-impl` / `impl-dev-wave-prov-incremental-audit`、
  `t2293-impl` / `impl-dev-wave-t2293-origin-producer`)。
  **どちらも `.claude/worktrees/` に wave 本体が現存する稼働中 wave の子である。**
- 差分 file の mtime 範囲 = 2026-09-13 22:50 〜 2026-09-15 23:25。
  worktree 単位の最終更新: 24h 以内 8 件、1〜3 日 58 件、3 日超 0 件。
  **7 日を超えるものは無い。母集団はおよそ 3 日で入れ替わっている。**

## 2b. 照合器の欠陥 — v1 を取り下げた理由 (実証済み)

**`git log --find-object` は既定で merge commit の差分を作らないため、merge 経由で main へ入った
blob を見つけられない。** 本 repo は `merge(main): …` を多用するので隅の事例ではない。

実証 (`findobj_probe.sh`、対象 = `orchestrator/tests/s8b_v2_freeze_fixture.py`、
blob `b3d0c379455a309f5e7d86317181ee12a77da877`):

| 検査 | 結果 |
|---|---|
| `git rev-parse refs/heads/main:<path>` | `b3d0c379…` — **main の現行内容と同一** |
| `git log main -1 --find-object=<blob> -- <path>` (v1 が使った形) | **空** (rc=0) |
| `git log main -1 --find-object=<blob>` (path 指定なし) | **空** |
| `git log main -1 --diff-merges=first-parent --find-object=<blob> -- <path>` | **`9f2f8d3a3` を検出** |
| `git log main -1 -m --find-object=<blob> -- <path>` | **`9f2f8d3a3` を検出** |
| `git rev-list --count main -- <path>` | 18 |

誤りの向き: **hit は正しく、miss は正しくない。** v1 の `MAIN:` 170 件は有効、
`NOWHERE` 6 件と `OTHERREF` 1 件は無効である。

v2 (`reach2.sh`) の是正 3 点:

1. 一次判定を `git hash-object` と `git rev-parse refs/heads/main:<path>` の直接比較にする。
   **O(1) で厳密。履歴を歩かない。**
2. 履歴探索の fallback に `-m` を付け、merge の差分も見る。
3. `--untracked-files=all` にする。v1 は既定の `normal` で未追跡 dir を 1 entry に畳んでおり、
   中の file を数え落としていた (`t2566-c` と `t2566-fix3` の `.tmp/` が `NOT-A-FILE` になった)。

**この是正は提案する gate の設計も変える。** 一次判定が O(1) なら、撤去 gate の費用は
既に払っている `git status` より小さく、[T-2641] の高速化を損なわない。

## 3. 着地照合 v2 (reach2、untracked と削除を含む)

判定の意味:

- `LANDED-CURRENT` — 作業木の内容が `refs/heads/main` の**現行**内容と 1 byte 違わない。
- `LANDED-HIST:<sha>` — 現行とは違うが、main の履歴のどこかに同一 blob がある (merge を含む)。
- `OTHERREF:<sha>` — main には無いが別 ref にある。稼働中 wave の未着地分。
- `NOWHERE` — どの commit にも同一内容が無い。**一度も commit されていない。**
- `DEL-LANDED` / `DEL-UNLANDED` — 作業木で削除された path。main にも無い / main にはある。
- `CLEAN` — 変更が 1 件も無い worktree。

### 確定値 (67 件 251 entry、完走)

entry 単位: LANDED-CURRENT 70、LANDED-HIST 103、NOWHERE 62、DIR-ENTRY 14、OTHERREF 1、CLEAN 1。

worktree 単位の**最悪判定**: LANDED-CURRENT 17、CLEAN 1、LANDED-HIST 44、OTHERREF 1、NOWHERE 4。

NOWHERE 62 entry の内訳:

| 対象 | entry | 正体 |
|---|---|---|
| `t2566-fix3` / `t2566-c` | 58 | pytest の一時出力 (`.tmp/pytest-of-tanab/pytest-0/…` の `campaign.lock`・`wal.jsonl`・`*-execution.json`)。**再生成可能物** |
| `t2596-impl` | 2 | `stage5-owned.patch`・`fix-spawn-sites.patch`。**`DW-S05-A` の patch 抽出手順が作った成果物そのもの** |
| `t1643-impl` | 1 | `tools/t1643_has_include_pair_probe.py` 475 行。**唯一の実際の未着地ソース** |

`DIR-ENTRY` 14 件は pytest の `-current` **symlink** (実物で確認)。
計測器の `[ -f ]` がリンク先の directory を辿って落ちたもの。

**v1 で誤判定と判明した実例 (v2 で是正):**

- `t1994-merge` / `orchestrator/tests/s8b_v2_freeze_fixture.py` は v1 で `NOWHERE` だったが、
  blob `b3d0c379…` は **main の現行内容そのもの**だった。v1 の欠陥による偽陰性である。

**v1 でも v2 でも成立する例外 (撤去 gate が恒真でない証拠):**

1. `prov-incr-impl` / `orchestrator/tests/test_run_tests_preflight.py` → `OTHERREF:aae713e1d`。
   稼働中 wave `dev-wave-prov-incremental-audit` の子。**触ってはならない。**
2. `t1643-impl` / `tools/t1643_has_include_pair_probe.py` (475 行)。
   T-1643 は「docs のみ・実装面差分ゼロ」で着地している (worklog 1498)。
   **意図的に落とした一時 probe である。**
3. `t1994-merge` の 2 file は main と内容が本当に違う (`git rev-parse` 比較で確認):
   - `test_ccbench_spawn_sites.py` — 4 行差 (定数 8661 → 8637)。**main より古い値。**
   - `test_s8b_oracle_driver.py` — 追加 9 行 / 削除 395 行。**main が後から 386 行増えている。**
   どちらも「失われた作業」ではなく**中間状態が main より遅れている**形である。

## 3b. 厳密版の汚れ (strict、権威ツールと同じ flag、67 件完走)

`git status --porcelain=v1 --untracked-files=all --ignore-submodules=none` — `tools/dev_wave_cleanup.py`
の `_assert_clean_and_head` と同じ条件。

| 量 | census (甘い版) | strict (権威と同条件) |
|---|---|---|
| CLEAN | 1 (`t1851-c3c-detail`) | 1 (同じ) |
| 変更 file | 173 | 173 |
| 削除 | 未判定 | **0** |
| untracked | 6 | **77** |
| submodule 行 | 除外 | **0** |

**untracked は 13 倍の過少計上だった。** `git status` の既定 (`--untracked-files=normal`) が未追跡
directory を 1 entry に畳むためで、`t2566-fix3` の `.tmp/` 1 行の裏に 70 file が隠れていた。
食い違ったのは `t2566-c` (1 → 3) と `t2566-fix3` (1 → 70) の 2 件。

**削除も submodule 汚れも 1 件も無い。** したがって、削除判定と submodule に関する計測器の欠陥は
**実在するが、この母集団には該当例が無い** (欠陥の開示は下記 8 に残す)。

## 4. 占有 (権威 CLI)

**初回 (走査と同時、04:45 JST)**: 67 件中 free 64 / occupied 3
(`a5f-f480`、`t1851-c3c-detail`、`t1994-s0a`)。

**取り直し (全走査の終了後、05:25 JST)**: 71 件中 free 68 / occupied 3
(`t2545-impl`、`t2586-impl`、`t2639-impl`)。

**occupied の 3 件が完全に入れ替わった。** 初回の 3 件は親の census スクリプトが同時刻に
`git -C <path>` で参照していた**自己マッチ**であり、走査を止めたら free になった。
取り直しで occupied になった 3 件は、いずれも `.claude/worktrees/` に wave 本体が現存する
**稼働中 wave の実装子**である (`dev-wave-t2545-b4-publication-root`、
`dev-wave-t2586-itt-trace-seed-contract`、`dev-wave-t2639-branch-rescue-path-first`)。

この対比は 2 つを同時に示す。**(a) 自分の走査が占有判定を汚染する**ので、撤去判定に使う占有検査は
走査と同時に行ってはならない。**(b) 検査は本物の占有を捉える** — 初回値を「他セッションが使用中」と
読んではならなかったが、検査そのものが無力なわけではない。

なお D391 が明記するとおり **rc0 は削除の必要条件であって十分条件ではない**。走査後に始まる
process、別 PID namespace、FD 経由の参照は観測できない。TOCTOU の窓は各 PID の観測時点から
directory 撤去の終了までであり、F26 は撤去自体が分単位に達しうると記録している。

### index と作業木のずれ (xy、全件)

status の XY 2 文字の分布: `M ` 104 (staged・作業木は index と一致)、`??` 77 (未追跡)、
` M` 69 (unstaged)、`A ` 10 (staged 追加)。

**index と作業木が食い違う worktree は 0 件**だった (`MM`・`AM`・`AD` などが 1 件も無い)。
したがって作業木を hash した照合は、全件で index と同じ内容を見ている。
`A ` が 10 件あるのは、親の抽出手順が子の作業木で `git add -A` を打つためである。

## 5. 所有記録の所在と寿命

- `tools/codex_worker_launch.py` は wave ごとに `manifest.json` を書き、各 session の
  `recorded_cwd` が子 worktree の**絶対 path** を持つ。実例:
  `dev-wave-t1643-has-include-pair-author-0 | /work/1/SFC/tanab/izanagi/.codex/worktrees/t1643-impl`
- `/work/1/SFC/tanab/dev-wave-jobs/` の job dir は 1190 本、うち `manifest.json` を持つのは 183 本。
  その 183 本が名指す codex worktree は 66 件。
- **現存 67 件のうち、manifest で所有者が判るのは 2 件だけ** (`t1643-impl`、`t2519-impl`)。
  65 件は所有者不明である。
- 原因: **背景 job の wave は artifact root を job dir の中
  (`~/.claude/jobs/<id>/dev-wave-jobs/<wave>/`) に置く。** job を消すと manifest ごと消える。
  記録の寿命が worktree の寿命より短い。
- 現存する durable な符号化は **branch 名**である。**61/67 (91 %)** が
  `<種別>-dev-wave-<wave slug>` 形式。外れる 6 件は `codex-*` 5 件 (`codex-f480-scaffold`、
  `codex-dispatch-exit-hang`、`codex-t080-shared-base`、`codex-shard-weight`、`codex-t1643-impl`)
  と `acceptance-*` 1 件 (`acceptance-t1851-c3c-official-floor`)。

## 6. 既存機構が既に持っている原理

`tools/dev_wave_cleanup.py` は撤去の必要条件として次を持つ (読解、実走はしていない)。

- `_assert_clean_and_head` — `status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none`
  が空であること。**submodule も untracked も数える。**
- `_assert_reflog_commits_reachable` — worktree の HEAD reflog に現れる**全 commit**が
  `merge-base --is-ancestor <sha> refs/heads/main` を満たすこと。
- D702 の理由節はこの原理を逐語で述べている:
  「ancestry を必須にするため、削除された commit は main から到達可能なまま残る。」

**すなわち「main から到達可能なものだけ捨ててよい」は既にユーザーが批准した原理であり、
commit 粒度では実装済みである。** 子 worktree で欠けているのは、どの commit にも入っていない
**作業木の内容**に同じ条件が無いことだけである。

## 6b. 錠 — 第二の、独立した原因

- `DW-O20` は「子を走らせる worktree は `git worktree lock` (cwd 走査は launcher 型を逃す)」と
  命じている。**その lock を解く義務は `DW-O28` にも `DW-S05-*` にも `/cleanup-branches` にも無い。**
- `/cleanup-branches` §3 末尾は「cwd 固定の背景セッション や occupied/locked worktree は、
  detach・unlock・branch/directory 削除・prune を行わず、**そのまま引き渡す** (F51)」と定める。
- 実測: 67 件中 8 件が locked
  (`prov-batch`、`prov-incr-impl`、`t1706-impl`、`t1851-c3c-author`、`t2288-impl`、
  `t2515-ledger-author`、`t2515-t2534-author`、`t2591-impl`)。
  このうち `prov-batch` (worklog 1518 着地)、`t1706-impl`、`t2288-impl`、`t2591-impl` (1516 着地)
  は **wave 本体が `.claude/worktrees/` に存在しない**。
- **すなわち汚れ (未コミット差分) を解決しても、この 8 件は錠だけで残り続ける。**
  終端契約は unlock を含まなければ完結しない。

## 7. 費用

- 差分検査 1 件 = cold 6.32 秒 / warm 4.57 秒 (`git status --porcelain`、本 login node)。
  [T-2641] が記録した 12.7 秒との差は機体・cache・並行負荷による。
- `git log main -1 --find-object=<blob> -- <path>` は path 限定付きで、
  標本 (`a5f-f480` の 2 file) が数秒で返った。**全 67 件の走査は完走まで数十分かかった** —
  1 file あたりの実測平均は `reach_all.tsv` の行数と走査時間から導くこと。
- 掃除全体は 1 回 14.4 分 ([T-2641] 実測、worktree 68 件の直列 `git status`)。
