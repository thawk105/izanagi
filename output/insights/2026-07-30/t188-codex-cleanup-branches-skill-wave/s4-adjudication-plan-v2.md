# T-173 段 4 裁定・plan v2

## 裁定

段 2 plan v1 は NO-GO。段 3 の安全・実効性レビューは rc=0 / 形式 gate green で、次を real として採用する。

1. command に存在しない `/cleanup-branches`→`$cleanup-branches` 読み替えは恒真なので削除する。
   Codex 固有差分は `$ARGUMENTS`、Claude 固有 `ExitWorktree` の非互換、hook 未配線である。
2. destructive Skill は明示起動専用にする。exact description を固定し、
   `policy.allow_implicit_invocation: false` を生成済み interface に追加する。
3. 共通手順を Skill へ再掲しない。ただし共通 dispatcher に存在しない Codex 固有の安全縮退は
   adapter overlay として Skill に置く。
4. local `main` と primary worktree は無条件保持する。locked worktree、および現在の Codex session が
   作成・所有したと証明できない foreign worktree は inventory / report のみに縮退し、unlock、directory
   削除、prune を行わない。Codex からの `/proc` miss は非使用の証拠に数えない。
5. Claude 固有 `ExitWorktree` が Codex にあると仮定しない。cwd を target 外へ固定できない場合は F51
   縮退とし、自 worktree の directory 削除・prune を行わない。
6. `git worktree prune` 前に `git worktree prune --dry-run --verbose` を行い、scope 外 record が1件でも
   出る、または作用域を一意に証明できない場合は prune せず人間へ引き渡す。破壊操作直前に dirty /
   HEAD / branch / lock / cwd を再確認する。
7. 権限不足時に sandbox や shared Git metadata への権限を拡大せず、対象と未実行操作を人間へ返す。
8. Skill substring だけでなく、共通 command の既存安全 literal、exact trigger description、limits、
   placeholder 不在、negative-case registry を checker / 独立 pin で固定する。
9. T-172 の checker 拡張が T-058/T-059 発火記録から漏れている所見は real。T-173 と同時に phase へ
   補正し、coverage / mutation の未観測を実績以上に書かない。

次は refuted / scope 外とする。

- initializer の利用方法、UI interface 3 fields、generic `_check_codex_skill_guard` 再利用は成立している。
- `.claude/commands/cleanup-branches.md` の直接編集は行わない。今回の静的レビュー所見だけで
  cleanup-branches 自己改善 gate を満たしたと扱わず、共通正本の改訂権限を広げない。
- primary / main、foreign worktree、prune の未見危険は Codex adapter overlay で fail-closed に塞ぐ。
  共通 command 側の改訂は、cleanup-branches の実行で gate が成立した将来 task の候補として本 artifact
  に残す。
- implicit invocation の択一は安全側の false を採用する。明示 `$cleanup-branches` の利用可能性は保持され、
  ユーザー意図を狭めるだけなので追加裁定待ちにしない。

成果物影響: この是正なしでは Codex Skill が primary checkout / foreign active worktree を削除候補に
含め、共有 Git metadata や並行セッション成果を失わせ得る。checker 強化なしでは安全 overlay または
dispatcher の削除が green のまま通る。

## plan v2

段 5 author の所有は次の4実装ファイルだけとする。docs、wave artifact、commit は親が所有する。

- `.agents/skills/cleanup-branches/SKILL.md`
- `.agents/skills/cleanup-branches/agents/openai.yaml`
- `tools/check_docs.py`
- `orchestrator/tests/test_check_docs.py`

実装順:

1. `skill-creator` の `init_skill.py` を resources / examples なしで実行し、2 file skeleton と
   interface 3 fields を生成する。
2. Skill を共通 dispatcher への薄い adapter として書き換える。質問・レビューはクラス 1 read-only、
   明示的な掃除依頼だけクラス 2、`$ARGUMENTS` の読み替え、Codex 固有 safety overlay、hook / permission /
   push 境界、自己改善正本への pointer を置く。
3. generated `openai.yaml` の interface bytes を再生成し、explicit-only policy を決定的に追加する。
4. checker に cleanup Skill の limits / exact files / exact description / required adapter literals /
   forbidden `[TODO` / exact metadata を登録する。helper は optional expected description /
   forbidden literals を検査できるよう拡張する。
5. command の既存 safety literals (`git branch -d` / `-D` 禁止、`/proc/*/cwd`、F26、F51、
   remote delete / main push、非発火時自己改善禁止) を command 本文へ直接照合する。
6. synthetic fixture に第三 Skill と command safety literals を追加し、最低8負例
   (file欠落、extra、name、description、adapter、metadata、placeholder、command safety) と独立 pin
   (files、limits、description、adapter literals、metadata、case ID集合、command safety literals) を追加する。
7. quick_validate と focused `test_check_docs.py` を実走し、docs / commit を触らず親へ返す。

段 6 では2 review、必要なら同じ4 file ownershipの単一 fix、下記 mutation、fresh read-only discovery
smoke、統合検査を行う。

## mutation 事前登録

各変異は統合後 anchor を固定して1件ずつ行い、復元を byte 比較で確認する。V8 は正例であり mutation
件数に数えない。

| ID | 位置と変異 | 事前確認した単一赤理由 |
|---|---|---|
| V1 | cleanup `_check_codex_skill_guard` call だけ削除 | cleanup permanent negative cases が期待 finding を返さず positive-control test 赤 |
| V2 | synthetic command から command safety literal 1件だけ削除 | command safety drift finding |
| V3 | real Skill から foreign worktree fail-closed literal 1件だけ削除 | adapter literal finding |
| V4 | real Skill frontmatter description を別の非空文へ変更 | exact description finding |
| V5 | metadata の `allow_implicit_invocation: false` を true に変更 | exact metadata finding |
| V6 | real Skill 本文末尾へ `[TODO placeholder]` を追加 | forbidden placeholder finding |
| V7 | limits / fixture の同時縮小はせず、test 側の独立 pin が保持する exact limits / case集合を直接照合 | 独立 surface pin の恒久回帰 test |
| V8 | 正しい2 files、全 literals、exact metadata、placeholderなし | baseline green。explicit Skill を過剰拒否しない正例 |

metadata budget +1 は exact interface mismatch と二重発火するため、単一理由 mutation から除外する。
M9 の「正しい構成」は survivor / 正例へ移し、変異数を水増ししない。
