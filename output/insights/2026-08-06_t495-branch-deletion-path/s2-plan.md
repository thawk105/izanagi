## 総括

指定された段 1 brief を先に読んだうえで、候補設置面を **7 件**評価した。内訳は、リポジトリ内で変更可能 **4 件**、外部層依存で実装不能 **2 件**、現行経路がなく非該当 **1 件**である。

実装可能な面のうち、事故経路を機械的に止め得る最小構成は「`guard_bash` の早期判定＋対象 ref 専用の到達性 oracle」の組合せ。ただし被覆は Claude Bash 面に限られ、全 Git 操作を保証するものではない。

親裁定への異議は **あり**。主に (P1) の「本件では発火余地がなかった」という部分で、durable ref 到達性を条件にする防壁なら本件でも発火していた。(P4) の制度化却下自体には異議なし。

また、brief の「`tools/audit_dangling_commits.py` は未 land」と異なり、現在の local `main` と HEAD はともに `cfda4abe…` で、同ツールは **main に存在する**。

## 判定対象となる性質

機械判定可能な定義としては、次が最も明確である。

> 削除対象 ref の旧 tip から到達できる commit のうち、削除後に残る durable ref から到達不能になる commit が一つでもあれば拒否する。

ここで reflog、session transcript に記録した SHA、約 2 週間残る loose object は durable ref に数えない。現行監査も `--no-reflogs` を使っている。[tools/audit_dangling_commits.py:60-75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/audit_dangling_commits.py:60)

この定義は patch-equivalent な squash／cherry-pick や「価値なしとレビュー済み」の commit も止める。反対に、内容の意味的同一性まで機械判定しようとすると、merge、conflict resolution、rename、mode/gitlink、削除を完全には扱えない。したがって、発火時は override ではなく rescue ref を作ってから元 ref を消す方が、常時警告への慣れを避けやすい。

## 実コードの確認

### `hooks/guard_bash.py`

`_GIT_READ_SUBS` は「Git 全体が読み取り専用か」を判定する集合ではなく、防護末端に触れた Git segment を `_is_read_only()` が許可するための集合である。そこには現在 `branch` が含まれる。

> `_GIT_READ_SUBS = ... "remote", "branch", "tag", "fetch" ...`

[hooks/guard_bash.py:140-146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/guard_bash.py:140)、[hooks/guard_bash.py:1328-1350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/guard_bash.py:1328)

`decide()` の順序は次のとおり。

1. Pegasus 重量操作を先に拒否。
2. 防護パス語が無ければ即許可。
3. opaque 構文、tokenize、redirect、tree destruction、leaf write を順次判定。
4. 最後まで該当しなければ許可。

> `if not _MENTION_RE.search(command): return True, ""`

[hooks/guard_bash.py:1532-1543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/guard_bash.py:1532)、[hooks/guard_bash.py:1545-1620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/guard_bash.py:1545)

したがって通常の `git branch -D foo` は `_GIT_READ_SUBS` に到達する前に fast path で許可される。`branch` を集合から外すだけでは直らない。

一方、重量操作拒否は防護パス fast path より前に置かれているため、**防護パスに依存しない拒否は構造上可能**。ref-delete 判定を置くなら同じく line 1542 より前になる。拒否は entry point で exit 2 へ変換される。[hooks/guard_bash.py:1623-1641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/guard_bash.py:1623)

ただし hook が受け取るのは command 文字列だけで、実行 cwd や承認・検査結果の構造化 field はない。`git -C`、複数 ref 同時削除、alias、対象 ref の移動を扱うには追加設計が必要である。

### `hooks/README.md`

現行責務は campaign/CCBench の直接書き込みを止める「最小の第二防壁」であり、Git ref 保護は現行責務に含まれない。[hooks/README.md:1-13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/README.md:1)、[hooks/README.md:63-82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/README.md:63)

配線は Claude の `PreToolUse:Bash` のみ。[.claude/settings.json:8-26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/.claude/settings.json:8) Codex には未配線であり、script file、変数展開、`python3 -c`、ユーザー端末も見えない。[hooks/README.md:15-24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/README.md:15)、[hooks/README.md:173-180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/hooks/README.md:173)

### `.claude/commands/cleanup-branches.md`

現行 prompt は既に次を要求する。

- ahead/cherry/status の棚卸し。[cleanup-branches.md:11-17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/.claude/commands/cleanup-branches.md:11)
- ahead=0 のみ、`git branch -d` のみ、`-D` 禁止。[cleanup-branches.md:19-25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/.claude/commands/cleanup-branches.md:19)
- ExitWorktree の強制 override 禁止。[cleanup-branches.md:39-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/.claude/commands/cleanup-branches.md:39)
- remote delete は人間へ引き渡す。[cleanup-branches.md:52-56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/.claude/commands/cleanup-branches.md:52)

現在は 3,983 bytes、上限は 4,000 bytesなので余裕は 17 bytes。上限自体は [tools/check_docs.py:168-172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/check_docs.py:168)、実効値は [worklog:292-299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/docs/archive/worklog-phase3-0805-216.md:292) に記録されている。

さらに whole-file SHA-256 が固定されており、1 byte の変更も既存負例が拒否する。[tools/check_docs.py:330-332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/check_docs.py:330)、[tools/check_docs.py:3115-3124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/check_docs.py:3115)、[test_check_docs.py:4108-4119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/orchestrator/tests/test_check_docs.py:4108)

### `tools/audit_dangling_commits.py`

現在の main に存在する。目的と rc は先頭で明記されている。[tools/audit_dangling_commits.py:1-8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/audit_dangling_commits.py:1)

ただし現在の判定は事後専用である。

- `fsck --unreachable --no-reflogs` で既に到達不能な commit を列挙。[tools/audit_dangling_commits.py:60-75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/audit_dangling_commits.py:60)
- commit の変更 path が main／他 local branch tip の tree にあるかを比較。[tools/audit_dangling_commits.py:121-152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/audit_dangling_commits.py:121)
- 既存ファイル変更、削除、同名別内容、gitlink は明示的に対象外。[tools/audit_dangling_commits.py:23-25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/audit_dangling_commits.py:23)

削除前の branch はまだ reachable なので、現行 `audit()` をそのまま前置きしても対象 branch を検査できない。また、同一 path に別内容がある場合を「報告なし」とする負例が固定されている。[test_audit_dangling_commits.py:139-162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/orchestrator/tests/test_audit_dangling_commits.py:139)

### `tools/dev_wave_land.py`

ref には触るが、削除経路はない。

- `commit` により main ref を進める。[tools/dev_wave_land.py:1479-1503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/dev_wave_land.py:1479)
- `merge --ff-only` で main を tested tip へ進める。[tools/dev_wave_land.py:1921-1933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/dev_wave_land.py:1921)
- fold 失敗時のみ、old OID 付き CAS `update-ref refs/heads/main` で巻き戻す。[tools/dev_wave_land.py:1313-1343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/dev_wave_land.py:1313)
- 成功後も wave ref が同じ tip に残ることを postcondition にしている。[tools/dev_wave_land.py:1625-1634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/dev_wave_land.py:1625)

正常 land の Git 呼び出しに `branch`、`update-ref`、`worktree` が現れないことも負例テストで固定されている。[test_dev_wave_land.py:2362-2374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/orchestrator/tests/test_dev_wave_land.py:2362)

## 候補設置点の地図

| # | 設置面 | 状態 | 被覆と限界 |
|---|---|---|---|
| 1 | `guard_bash.decide()` の fast path 前 | 実装可能 | 対話 Claude Bash の直接 `branch -d/-D` 等を止められる。Codex、script、user terminal、TOCTOU は不可。 |
| 2 | `tools/audit_dangling_commits.py` 隣接の対象-ref oracle／安全 wrapper | 実装可能 | 削除対象旧 tip と surviving refs を比較できる。単独では直接 Git 操作を interpose できない。現行 path-name audit の流用は不可。 |
| 3 | `cleanup-branches.md` から安全 wrapper のみを呼ぶ | 実装可能、prompt 補助 | 明示 `/cleanup-branches` と `$cleanup-branches` を被覆。今回の即興対話経路は被覆しない。17-byte 余裕と whole-file pin が費用。 |
| 4 | `tools/dev_waves/git_state.py` の Git allowlist | 実装可能・既存閉鎖 | supervised dev-wave は未登録 Git 操作を拒否し、branch delete API 自体がない。[git_state.py:65-100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/dev_waves/git_state.py:65)、[git_state.py:177-204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/dev_waves/git_state.py:177) 対話 session は管轄外。 |
| 5 | Git `reference-transaction` hook | プロジェクト単独では実装不能 | configured repository の標準 ref transaction に最も近く、複数削除／rename を一括判定できる。ただし tracked repo から `.git/config` 配線を強制できず、`core.hooksPath` override でも迂回される。 |
| 6 | harness の ExitWorktree gate | 実装不能 | worktree removal だけを被覆。本件経路ではなく、当プロジェクトに実装権限がない。 |
| 7 | `tools/dev_wave_land.py` | 現行経路なし・非該当 | ref は更新するが削除しない。ここへ cleanup を追加すると land 契約と既存負例を拡張し、対話 `-D` は依然被覆しない。 |

Git hook 案には追加の制約がある。dev-wave の Git helper は明示的に `core.hooksPath=/dev/null` を指定し、land helperもそれを継承する。[git_state.py:37-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/dev_waves/git_state.py:37)、[dev_wave_land.py:66-74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/dev_wave_land.py:66)

また `tools/codex_reasoning_ab.py` は、source repo 外の隔離 snapshot で不要 ref を意図的に `update-ref -d` し、その object を prune する。[codex_reasoning_ab.py:695-715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/codex_reasoning_ab.py:695)、[codex_reasoning_ab.py:1263-1276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/tools/codex_reasoning_ab.py:1263) 全 repository・全 ref の削除を一律拒否すると、この正当な snapshot sealing が偽陽性になる。保護対象は少なくとも canonical Izanagi common-dir の `refs/heads/*` に絞る必要がある。

## 費用・偽陽性上の要点

- `-D` を無条件拒否すると、完全に冗長な branch でも毎回鳴る。所望の性質には到達性 oracle が必要。
- commit 到達性を使うと squash／cherry-pick／意図的廃棄も止まる。ただし rescue ref を作れば安全に続行でき、override を常態化させずに済む。
- `git cherry`／path 名比較で意味的同一性を許可すると、merge、既存ファイル変更、削除、gitlink で見逃しが残る。
- 複数 ref の同時削除は削除集合全体で評価する必要がある。同じ unique tip を指す二つの branch を個別に検査すると、互いを「他の ref」と誤認し得る。
- ref rename は旧 ref 削除と新 ref 作成を同一 transaction で見る必要がある。削除行だけを見る gate は誤拒否する。
- 現行 hook テストには protected tree の read 許可と多数の偽陽性回帰があるため、Git gate を足すならこれらを保持しつつ、branch listing、冗長 branch 削除、unique branch 削除、複数対象を別 controls として追加する必要がある。[test_hooks.py:356-376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/orchestrator/tests/test_hooks.py:356)、[test_hooks.py:611-652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t495-branch-deletion-path/orchestrator/tests/test_hooks.py:611)

## 親の (P1)〜(P4) への異議

- **P1: 部分的に異議あり。** 「検査なしの事故」という起票前提が誤りなのは同意する。ただし、削除時点で `77db32c` が durable ref から失われるなら、到達性 gate は検査・承認後でも発火する。transcript の SHA 記録は durable ref ではない。したがって「本件では発火余地がなかった」は、意味的価値を人間が否定したことを機械入力として扱う場合にしか成立しないが、その構造化 field は現行 hook payload に存在しない。
- **P2: 異議なし。** ExitWorktree の ahead-of-base count は常時警告化しやすく、しかも harness 側で変更不能。新案は同じ count を再利用すべきでない。
- **P3: 異議なし。** 並行 session への根拠共有は別の可観測性問題。pre-delete barrier だけでは削除理由の共有までは解かない。
- **P4: 制度化却下には異議なし。** 独立二例がない以上、この一件だけで新防壁を land する根拠は弱い。ただし P4 が否定できるのは採用根拠であって、設置可能性ではない。`guard_bash`＋対象-ref oracle という部分被覆は実コード上成立する。

静的読解だけを行い、テストおよび `decide()` の実行はしていない。