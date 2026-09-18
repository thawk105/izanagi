---
authority: none
default_effect: no-state-change
---

# [T-2638] 実装子 worktree の終端契約 — 起動器 / 待ち手が作業木の残差を子 branch へ commit する (D2044 項 16 の実装)

本書は wave の一次資料 (設計判断は decisions、実績は worklog へ fragment で送る)。
`verbatim/` は子の出力・親の prompt・裁定を凍結したもの (sha256 は `verbatim/SHA256SUMS.txt`)。4 file だけ行末空白を可逆に除いた
(原文 sha256・bytes・復元法は `verbatim/NORMALIZATION.md`、可視文字は不変、DW-S07)。
wave branch `worktree-dev-wave-t2638-child-worktree-commit` (base = local main `d2ebef7a4`)、
commit 列 = docs v1 `1978fe640` → impl v1 `d8e512556` → docs v2 `fe1e6662e` → fix `c5403437c` → (本 insight)。
時刻は JST、`date` / commit 日時 / job dir の mtime から採った。

## 1. 何を作ったか

D2044 項 16 (ユーザー裁定 2026-09-16) が「実装子の作業木の終端契約 = wave 終了時に内容を branch へ commit、破棄案は
採らない」と定めたものを、依頼どおり**起動器と待ち手の終端**に実装した。

| 場所 | 変更 |
|---|---|
| `tools/dev_waves/git_state.py` | `commit_worker_worktree(repo_root, *, wave, job_id, stage, launcher_rc, receipt_path=None, actor="launcher")` を追加。`GIT_COMMANDS` に `git-dir` / `git-path` / `add-all` / `staged-quiet` / `commit-file` の 5 操作だけを足す (allowlist と hardening は不変) |
| `tools/dev_wave_codex.py` | launcher 復帰後、`--sandbox workspace-write` ∧ stage ∈ {author, fix} で helper を呼ぶ。launcher rc≠0 は保持、rc=0 ∧ refused/failed → **rc=3**。read-only・dry-run は不変、workspace-write の他 stage は `worktree-commit: skipped reason=stage` |
| `tools/dev_wave_wait.py` | `producer --commit-worktree <abs>` (opt-in、相対 path は usage rc=2)。producer の死亡確定後に 1 回だけ helper を呼び、既存 outcome が成功で refused/failed なら `producer-commit` で fail-closed (receipt 非公開)。flag 無しは bytes 不変 |
| `docs/dev-wave/workers.md` DW-S05-A | patch 抽出を `git diff --cached <base>` (`<base>` = 子作成 SHA) にし、終端 commit の 1 文 (投入先全残差・待ち手は呼出側指定・記録のみ) を足す。L1.5 予算 (9,696 bytes、空き 0〜1) は同節の意味保存の縮約で相殺 |
| テスト | helper 5 本、起動器 4 本、待ち手 4 本 (+ CLI surface の option 集合更新)。実 git repo・実 dispatcher (fake launcher script)・実 producer process |

helper の状態は 5 種: `committed <sha>` / `clean` / `deferred reason=operation-in-progress` (`MERGE_HEAD`・`CHERRY_PICK_HEAD`・
`REVERT_HEAD`・`rebase-merge`・`rebase-apply` のいずれか実在。merge commit は親が作る、DW-C01) /
`refused reason=<root-mismatch|primary-worktree|detached-head|protected-branch>` / `failed reason=<Git 操作名>`。
stdout に `worktree-commit: …` を 1 行 (`flush=True`)、refused/failed は stderr に `NG: worktree-commit …` も出す。

commit message は固定件名 `[T-2638] 起動器/待ち手の終端契約 (D2044 項 16): 実装子の作業木残差を記録` + 本文 7 field
(wave / job-id / stage / actor / launcher rc / receipt outcome / scope) + `AI-Agent: product=codex; model=<m>; reasoning=<r>;
role=author`。値は launcher receipt の `recorded_*` → `requested_*` → `unknown` (`requested_*` は launcher が `codex exec -m`
/ `model_reasoning_effort` へ渡した確定値、`tools/codex_worker_launch.py` の argv 組み立てで実測)。`[a-z0-9][a-z0-9._-]*` へ
正規化し、`none` は `unknown` へ (`check_ai_provenance.py` が拒否)。message file は `<git-dir>/izanagi-worker-commit.msg`
(作業木の外) に置き、成功・失敗とも削除する。

## 2. 段ごとの経緯 (要点)

- **段 1 brief** (`verbatim/s1-brief.md`): scope 6 点、(P1)〜(P6)。docs 予算を in-memory で実測 (L1 10,622/10,625、L1.5 9,696/9,696)。
  稼働 wave との file 重なり 0 (branch tip 走査 + bytes 比較の dirt 走査)。
- **段 2 plan** (`verbatim/s2-plan.md`): (P2) に異論 — `dev_wave_codex.py` は stage と sandbox を独立に受理するので sandbox だけでは
  対象を限定できない → stage 判定を足す。DW-S05-A の縮約案 (584→583 bytes) を提示。
- **段 3 レンズ A/B** (`verbatim/s3-lensA.md`、`s3-lensB.md`): A は 10 所見 (親 worktree の巻き込み、done 非空は死亡証拠でない、
  index.lock を skip にすると rc=0 に隠れる、`none` は checker が拒否、`<base>` の定義、`add -A` は submodule 内を拾わない 等)。
  B は待ち手の done 判定・check-only・rc 再解釈・index.lock 特別扱い・rebase 等の個別分岐・重複テストを削除候補に。
- **段 4 裁定** (`verbatim/s4-adjudication.md`): 主 checkout は `refused primary-worktree`、操作進行中は `deferred`、index.lock は Git 失敗に
  集約、待ち手は DEAD 確定後 1 回だけ、rc=3 新設、provenance は recorded→requested→unknown で `none`→`unknown`、変異 M0〜M14 (M11 は a/b) を事前登録。
- **段 5 author** (`verbatim/s5-author-1.md`、job `t2638-author-1`、06:53〜07:04): 所有 6 file、545 行。sandbox では pytest 不可
  (socket 拒否) のため直接呼び出し 17 件 PASS + 反実仮想 1 件 KILLED。親の焦点走 (計算ノード 5011.nqsv、07:09):
  **461 passed / 1 failed** — 赤は `test_producer_commit_worktree_after_death` の `err == ""` が待ち手の既存診断
  (`/proc/<pid>/stat` 読取不能で pid-only へ縮退) を拒んだ fixture 側の厳しすぎ。統合 commit `d8e512556`。
- **段 6 レビュー A/B** (`verbatim/s6-reviewA-1.md`、`s6-reviewB-1.md`、07:16〜07:19): must-fix は 3 件で一致 — (1) 上の stderr 期待、
  (2) DW-S05-A に保存範囲・待ち手の対象指定・記録のみが無い、(3) `tempfile(dir=None)` は `TMPDIR` 次第で作業木内になりうる。
  B は「削除必須なし」。docs は親が `fe1e6662e` で是正 (`check_docs.py` 緑)。
- **段 6 fix** (`verbatim/s6-fix-1.md`、job `t2638-fix-1`、07:26〜07:29): (1) 当該 PID の診断 1 行だけを許し `NG:` / `producer-commit` 不在を固定、
  (3) message file を git-dir 直下へ、(nit) `<base>` patch 比較を `add -A` 後の全差分へ。統合 commit `c5403437c`。
  **fix 子は新機構を含む HEAD から起動されたため、起動器が終端で残差を子 branch へ commit した (§3)。**
- **段 6 焦点走 v2** (計算ノード 5056.nqsv、07:35): 変更 3 file + consumer 14 file (参照関係で列挙、DW-O26) =
  **2307 passed / 5 skipped** (skip は growth hold 4 = `test_check_docs.py` の実 repo 走 3 + `test_ruleops.py` 1、flaky hold 1。いずれも本 wave の test ではない)。
  `tools/check_docs.py` は親が直接実走して緑。
- **段 6 焦点再レビュー** (`verbatim/s6-focus-1.md`、07:33〜07:38): must-fix 全件 closed、新規 must-fix なし。nit 3 (下記 §5)。

## 3. 実データでの初回検証 — 起動器が fix 子の残差を commit した

fix 子 (`t2638-fix-1`) は子 worktree `.codex/worktrees/t2638-fix1` (HEAD `fe1e6662e`、新機構を含む) から
`tools/dev_wave_codex.py --stage fix --sandbox workspace-write` で起動された。launcher 復帰後に起動器が残差を commit した
(`verbatim/s6-inspect-child-commit.txt`、親が 07:29 に実測):

| 項目 | 実測 |
|---|---|
| commit | `5a99d99d0c253a5e5d0cde52ff7a1ead8e4b3a31` on `fix-dev-wave-t2638-child-worktree-commit` (07:29:14 +0900) |
| 件名・本文 | 固定件名 + `wave: dev-wave-t2638-child-worktree-commit` / `job-id: t2638-fix-1` / `stage: fix` / `actor: launcher` / `launcher rc: 0` / `receipt outcome: accepted` / `scope: worktree residue at job end` |
| trailer | `AI-Agent: product=codex; model=gpt-6-astra; reasoning=medium; role=author` (receipt の `recorded_*` 実測値) |
| 内容 | 所有 3 file、+16 / −7 (fix の差分と一致) |
| stdout | `worktree-commit: committed 5a99d99d0c253a5e5d0cde52ff7a1ead8e4b3a31` (`s6-fix-1.log` の 1 行目) |
| 作業木 | `git status --porcelain --untracked-files=all` 0 行、`<git-dir>/izanagi-worker-commit.msg` 残置 0 |

親はこの子から DW-S05-A の新手順 (`git add -A` → `git diff --cached fe1e6662e --output=<f> -- <所有パス>`) で patch を抽出し、
commit 後でも同じ 3,928 bytes の patch が取れることを確認した (`verbatim/s6-fix-1.md` の差分と wave commit `c5403437c` が一致)。
なお段 5 の author 子 (`t2638-impl`、HEAD `d2ebef7a4` = 旧機構) では終端 commit は起きず、残差は未 commit のまま残っている
(本 wave 以前の挙動そのもの。撤去は本 wave の scope 外)。

## 4. 変異 matrix (計算ノード、container `.codex/worktrees/t2638-mutcontainer` = `c5403437c`、spec / 台帳は job dir、複製は `verbatim/`)

runner = `tools/run_tests.py <3 test file> -k "<新規 13 test + producer_cli_surface + producer_waits_while_pid_alive>" -q -rf --force-dispatch`
(collect: 16 node)。probe 走 (全件 SURVIVED 期待で観測 node を集める、`verbatim/mutation-spec-probe.json` sha256
`5e2045e4…`、台帳 `verbatim/mutation-probe-ledger.json`、07:40〜08:13) → 本走 (`verbatim/mutation-spec-final.json` sha256 `72013b85…`、
台帳 `verbatim/mutation-final-ledger.json`、08:15〜08:48)。

| 変異 | 反転内容 | probe の失敗 node (完全集合) | 本走 |
|---|---|---|---|
| baseline | — | PASSED (16 passed) | PASSED |
| M0 対照 | docstring 1 語 | SURVIVED [] | SURVIVED |
| M1 | `sandbox == "workspace-write"` → `"read-only"` | 3 (codex: workspace_write_author_commits, terminal_commit_failure_rc, read_only_and_non_author) | KILLED |
| M2 | stage 判定を `True` に | 1 (read_only_and_non_author) | KILLED |
| M3 | detached の rc=1 を 99 に | 1 (refuses_detached_protected_primary_root) | KILLED |
| M4 | protected 集合を空に | 1 (同上) | KILLED |
| M5 | primary 判定を `False and` に | 2 (同上, wait: producer_commit_failure_withholds_receipt[primary]) | KILLED |
| M6 | marker 集合を空に | 1 (defers_merge_in_progress) | KILLED |
| M7 | staged rc 0/1 を入替 | 7 (git_state 3, codex 2, wait 2) | KILLED |
| M8 | `return launcher_rc` → `return 0` | 2 (terminal_commit_failure_rc, workspace_write_author_commits) | KILLED |
| M9 | rc=3 の条件集合を空に | 1 (terminal_commit_failure_rc) | KILLED |
| M10 | trailer 2 行を削除 | 3 (records_residue_then_noop, provenance_values, producer_commit_worktree_after_death) | KILLED |
| M11a | requested を recorded より優先 | 1 (provenance_values) | KILLED |
| M11b | `none`→`unknown` 写像を外す | 1 (provenance_values) | KILLED |
| M12 | flag 無しで cwd を対象に commit | 2 (producer_waits_while_pid_alive_then_completes_after_death, producer_without_commit_flag_preserves_bytes) | KILLED |
| M13 | 死亡確定前 (loop 先頭) で commit | 1 (producer_commit_worktree_after_death) | KILLED |
| M14 | dry-run でも commit | 1 (dry_run_never_commits) | KILLED |

probe: baseline PASSED、SURVIVED 1 (M0)、負例 15 件すべて赤 (probe 段の判定は SURVIVED 期待に対する MISMATCH = 観測)。
**本走: baseline PASSED、KILLED 15/15 (期待 node 完全一致)、SURVIVED 1 (M0)、MISMATCH 0、matching 16/16。** 走行後の container は clean (status 0 行、HEAD 不変)。
drift mask (HEAD blob 束縛の冗長 gate) は `-k` 選択のため 0 件で、較正走は不要だった。
M12 は既存 test (`producer_waits_while_pid_alive…`) も殺す — flag 無しの待ち手が commit を試み `refused` → `producer-commit` で
RC_FAIL_CLOSED になるため。登録した新規 test と合わせて完全集合に含めた。

## 5. 限界 (書けないこと) と scope 外

1. **配置先の回帰検出力** (レビュー A 所見 3 / focus N-1): テストは commit 後の message file 不在と untracked 0 を固定するだけで、
   使用中の配置先が作業木外であることを直接観測しない (旧 `dir=None` に戻しても赤化しない、fix 子の反実仮想で実測)。
   配置は実装 (`git_dir /`) が担う。
2. **同名 file の上書き** (focus N-3): `<git-dir>/izanagi-worker-commit.msg` が他用途で存在していれば切り詰めて削除する。
   既知の用途は無い。`clean` 経路は残置を掃除しない。同一 worktree の並行投入 (DW-C00 は全種直列) に対する排他は無い。
3. **submodule 内の編集と index flag** (レンズ A 所見 7): superproject の `add -A` の対象外。実装子は submodule を編集しない前提。
4. **別構成の展開物の混在** (レンズ A 所見 5): trailer はその job の構成を記す。段 5 は単位ごとに別 worktree、依存は着地後に展開する前提。
5. **待ち手の trailer は `unknown`**: receipt を読まない設計 (後詰め経路が常態で receipt を持たないため)。
6. **撤去との相互作用 (scope 外、D2044 項 16 の限定どおり)**: commit 済み子 branch は main 非到達 commit を持つ。稼働中 wave
   `cleanup-si-routing` (branch `worktree-dev-wave-cleanup-si-routing`) が DW-O28 を「子 worktree も `dev_wave_cleanup.py` で撤去」へ
   変えているが、同 tool は reflog / HEAD の main 到達性を要求するため、commit 済みの子は拒否される見込み (実測はしていない)。
   子 commit を祖先として保持する統合は別裁定。
7. **旧機構の子 worktree**: 本 wave の author 子 (`t2638-impl`) は旧 HEAD から起動されたため残差が未 commit のまま残る。

## 6. 工数・実走

- codex 子 6 本: plan 1、consult 2、author 1、review 2、fix 1、focus 1 (全段 `gpt-6-astra`、plan/consult は `medium`、他は docs 権威の `medium`)。
- 計算ノード: 焦点走 2 (5011.nqsv、5056.nqsv)、変異 probe 18 request、変異本走 18 request。受入全走は段 9 の受領証で記す。
- 親の実測: docs 予算 probe、branch tip / dirt 走査、receipt field、`check_docs.py` 3 回、`check_ai_provenance.py --message-file` 4 回、
  子 commit の検証 1 回。
