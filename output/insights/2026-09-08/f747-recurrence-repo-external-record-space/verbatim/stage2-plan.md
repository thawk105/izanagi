## 判定 3 経路

### (a) 一般的な自己改善許可を「別 dev-wave の明示起動」と読む

**判定: 拒否できる。command 単体でも拒否でき、SKILL.md を重ねるとさらに明確になる。**

command 単体の根拠:

- `.claude/commands/cleanup-branches.md:8-10`

  > この command の受領から final response 完了までを cleanup 実行とする。成功・削除 0 件・罠発見・
  > 検査赤・途中停止を含め、**本節は `CLAUDE.md` の一般クラス 2 規律より優先する**。クラス 2 は
  > repo 内容や履歴の変更権限を与えない。対象限定の引数: $ARGUMENTS

- `.claude/commands/cleanup-branches.md:17-22`

  > **未列挙の state mutation は目的・修復・一般クラス 2 規律を理由にしても禁止する。** とくに
  > branch/worktree の新規作成、surviving worktree の tracked/untracked file・index・設定の作成/編集、
  > handoff/worklog/spool/insight/failure/decision の作成、`git add/commit/amend/merge/rebase/cherry-pick/reset`、
  > 同一実行内の自己改善、local main/commit graph/remote の変更、push を禁止する。repo file を変更しない
  > cleanup では project tests・build・provenance 監査も行わない。未確定事項・新しい罠・prompt 不備は
  > final で裁定候補として返し、実装・記録・commit は後から明示起動された別 dev-wave だけが行う。

- `.claude/commands/cleanup-branches.md:80-81`

  > 記載と実挙動の食い違い・新しい罠・手順不足は `docs/skill-self-improvement.md` の routing 候補として
  > final で報告するだけにする。同一 cleanup 実行・継続・自己 spawn では編集や記録へ移行しない。

command + SKILL.md の根拠:

- `.agents/skills/cleanup-branches/SKILL.md:14-15`

  > `.claude/commands/cleanup-branches.md` を全文読み、冒頭の最優先 mutation boundary から末尾の
  > 自己改善終端までを全工程へ不可分に適用する。クラス 2 や外側の作業種別は許可集合を拡張しない。

- `.agents/skills/cleanup-branches/SKILL.md:38`

  > 自己改善候補も共有 command の終端に従い final で報告するだけとし、別 dev-wave へ自動移行しない。

反論として、「したらええんちゃう？」をユーザーによる明示許可とみなす余地はある。しかし、それは「dev-wave の明示起動」でも「別 dev-wave」でもない。さらに final 前なら `.claude/commands/cleanup-branches.md:8` により同一 cleanup 実行中であり、継続・自己 spawn を名指しする `:80-81` がその読解を破る。

### (b) repo 外の memory / job dir へ書く

**判定: 拒否できる。repo 外であることは allowlist 外 mutation を再許可しない。**

command 単体の根拠:

- `.claude/commands/cleanup-branches.md:12-15`

  > 状態変更の allowlist は、(1) §2 を満たす既存 local branch の `git branch -d`、(2) §2 を満たし
  > 所有確認済みの既存 worktree について §3 が定める detach・branch 解放・directory と対応 metadata の
  > 撤去だけである。Codex はさらに real prune を許さない。§1〜§4 の読み取り検査と final での報告は
  > state mutation ではなく許可する。overlay は許可集合を狭めるだけで、本 command は再許可しない。

- `.claude/commands/cleanup-branches.md:17`

  > **未列挙の state mutation は目的・修復・一般クラス 2 規律を理由にしても禁止する。**

- `.claude/commands/cleanup-branches.md:20-22`

  > 同一実行内の自己改善、local main/commit graph/remote の変更、push を禁止する。repo file を変更しない
  > cleanup では project tests・build・provenance 監査も行わない。未確定事項・新しい罠・prompt 不備は
  > final で裁定候補として返し、実装・記録・commit は後から明示起動された別 dev-wave だけが行う。

- `.claude/commands/cleanup-branches.md:81`

  > final で報告するだけにする。同一 cleanup 実行・継続・自己 spawn では編集や記録へ移行しない。

`state mutation`、`実装・記録`、`編集や記録` のいずれにも repo 限定はない。memory と job dir への書込みは列挙された branch/worktree cleanup mutation ではないため default-deny に入る。

command + SKILL.md でも `.agents/skills/cleanup-branches/SKILL.md:14-15` が §0〜§6 の不可分適用と「許可集合を拡張しない」を命じるため、repo 外という理由で再許可できない。

反論になり得るのは `docs/skill-self-improvement.md:65-66` の狭い表現である。

> cleanup 本走は共有 command §0/§6 に従い final の候補報告だけで終え、同一実行・継続・自己 spawn では
> repo file/history を変更しない。後からユーザーが明示起動した別 dev-wave だけが再照合・routing・実装する。

ただし同じ文が先に「共有 command §0/§6 に従い」と明記しており、§0 の無限定 default-deny と§6の無限定な「編集や記録」を解除する例外ではない。`repo file/history` は禁止対象の強調であって、repo 外 mutation の許可文にはならない。

### (c) 継続セッション・自己 spawn で実装・記録する

**判定: 拒否できる。3経路中もっとも逐語的に閉じられている。**

- `.claude/commands/cleanup-branches.md:8`

  > この command の受領から final response 完了までを cleanup 実行とする。

- `.claude/commands/cleanup-branches.md:80-81`

  > 記載と実挙動の食い違い・新しい罠・手順不足は `docs/skill-self-improvement.md` の routing 候補として
  > final で報告するだけにする。同一 cleanup 実行・継続・自己 spawn では編集や記録へ移行しない。

- `.agents/skills/cleanup-branches/SKILL.md:38`

  > 自己改善候補も共有 command の終端に従い final で報告するだけとし、別 dev-wave へ自動移行しない。

反論として、spawn された別 agent を「別 dev-wave」と呼ぶ読解が考えられるが、command は `自己 spawn` を明記して禁止している。許されるのは cleanup final の後にユーザーが明示起動した別 dev-wave であり、cleanup の継続や自己 spawn ではない。

## 機械検査の被覆

**判定: `tools/check_docs.py` は今回の実行経路を捕まえない。文書の改変は捕まえるが、固定された正しい条文の誤読・不遵守は観測しない。**

根拠:

- `docs/skill-self-improvement.md:82-83`

  > `check_docs.py` の担保は予算と dispatch・節・孤児・逃がし・住所 (address edge) の構造 lint に限る。
  > whole-file SHA-256 pin も bytes 差だけを検知し、意味は敵対監査と人間レビューが担う。

- byte・行長は `tools/check_docs.py:275-289` の `TextLimit` と、`:5953-5967` のサイズ・行長比較で検査する。
- 見出し集合は `tools/check_docs.py:828-839` の `REQUIRED_SELF_HEADINGS` と、`:6352-6372` の個数・孤児検査で守る。
- SKILL.md は `tools/check_docs.py:743-745` の SHA と、`:6535-6544` から呼ばれる `:5193-5200` の比較で固定する。
- command は `tools/check_docs.py:751-753` の SHA と、`:6546-6555` の比較で固定する。
- 独立 fixture は `orchestrator/tests/test_check_docs.py:577-708` に全文を複製し、`:9742-9772` で双方の digest を固定する。1-byte 変異の負例は `:9854-9865` と `:9870-9883`。
- 現在の実ファイル SHA は checker の定数と一致している。したがって今回の事象は、これらの検査が緑になり得る状態のまま発生する。

追加案を層ごとに整理すると次のとおり。

| 層 | 実現可能性 | 追加すべきか・副作用 |
|---|---|---|
| `check_docs.py` | **live 経路の検出は不能。** 必須語や§0/§6の逐語検査は追加できるが、whole-file pin より弱く、同じ文書を誤読した実行には恒真になる。 | 追加すべきでない。二重の literal 正本と「意味も検査済み」という誤った安心だけを増やす。 |
| hooks | 固定 subtree の直接 Write/Edit 拒否なら部分的に可能。先例は `hooks/README.md:155-163`。ただし現行 hook は cleanup 実行中という信頼可能な文脈を持たない。 | memory/job dir の無条件拒否は通常の memory・job 記録を壊すため追加すべきでない。さらに script・変数展開は `hooks/README.md:316-321`、persistent process・MCP・apps・子の別書込面は `:402-414` のとおり開く。完全被覆は不能。 |
| 別 tool／外側 runner | **可能。** cleanup 開始をモデルの自己申告でなく外側 runner が管理し、許可された Git/worktree mutation 以外を OS sandbox で拒否するか、対象 root の before/after snapshot を監査する。 | 本 waveではなく別裁定・別 waveにすべき。Git metadata、worktree directory、job runtime の必要書込みを精密に分離する必要がある。snapshot 方式は並行 session の正当な書込みを誤検出し、事後検知にしかならない。 |
| モデル行動 eval | 一般許可、repo 外、自己 spawn の敵対 prompt を流す回帰 eval は追加可能。 | 非阻害の観測用途なら有用だが、確率的で live enforcement にはならない。モデル/API費用と揺らぎがあるため防壁には数えない。 |

hook 本体へ手を入れる場合は、通常編集経路自体に特別な保守制約がある (`hooks/README.md:421-437`)。したがって、軽い追記として本 waveへ混ぜる案は採らない。

## 変更プラン

1. `docs/spool/failures/2026-09-08-dev-wave-f747-recur-20260908-1.md:1-13` を新規作成する。

   - 命名は `docs/spool/README.md:28-33`、frontmatter は `:35-49` に従う。
   - `docs/spool/failures/README.md:43-45` に従い、`## 再発`、既存 `### F747`、日付付き bullet を使う。新 F は採らない。
   - 逐語草案:

```markdown
---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-f747-recur-20260908
seq: 1
---

## 再発

### F747

- **再発: 2026-09-08** — branch 削除 19 本の完了後、一般的な自己改善許可を別 dev-wave の明示起動と誤読し、cleanup の同一継続内で allowlist 外の repo 外 memory 2 件と `MEMORY.md` を更新した。
```

2. `docs/spool/worklog/2026-09-08-dev-wave-f747-recur-20260908-1.md:1` を親 brief の S4 として作成する。

   - failures fragment と3経路の判定が確定した後に書く。
   - 内容は「F747再発 fragment」「3経路はいずれも現行条文で拒否可能」「静的 checker は実行時誤読を捕捉不能」「runtime enforcement は別裁定」とする。
   - worklog 固有形式の README は本 dispatch の射影外なので、親の実装段で正本を読んでから具体化し、推測した schema を使わない。

3. 以下は**変更なし**とする。

   - `.claude/commands/cleanup-branches.md:6-22,78-81`: 3経路を既に拒否している。whole-file pin の更新を伴う本文変更は不要。
   - `.agents/skills/cleanup-branches/SKILL.md:10-18,33-38`: command の不可分適用と自動移行禁止が既にある。
   - `docs/skill-self-improvement.md:63-66`: `repo file/history` は狭い強調だが、同じ文が command §0/§6を先に取り込んでおり許可にはならない。現況5993/6000 bytesのため、明確な意味欠落なしに変更しない。
   - `tools/check_docs.py`, `orchestrator/tests/test_check_docs.py`, `hooks/`: runtime 誤読を静的 literal 検査へ見せかける追加はしない。
   - `docs/failures.md`: 直接編集しない。fold は wave側で行わない (`docs/spool/README.md:91-93`)。
   - F538、repo 外 memory 2件、`MEMORY.md`、job dir: 変更しない。

依存順は「3経路の判定確定 → failures fragment → worklog fragment → docs検査 → fold dry-run → commit」である。

## 検査プラン

親は以下を実行する。テストは直接 pytest を起動せず、`tools/run_tests.py` に次の nodeid を渡す。

- `orchestrator/tests/test_check_docs.py::test_codex_cleanup_branches_skill_contract_pins_exact_surface`
- `orchestrator/tests/test_check_docs.py::test_cleanup_command_budget_is_pinned_and_enforced`
- `orchestrator/tests/test_check_docs.py::test_cleanup_skill_one_byte_change_is_rejected`
- `orchestrator/tests/test_check_docs.py::test_cleanup_command_one_byte_change_is_rejected`

文書・fold 検査:

- `python3 tools/check_docs.py`
- `python3 tools/spool_fold.py --dry-run --show-diff`
- dry-run diffで、F747エントリ末尾への再発1件の挿入だけであり、新規F見出しが増えないことを目視する。
- `python3 tools/check_codex_agents.py`
- commit後に `python3 tools/check_ai_provenance.py`
- 最終 diff で canonical `docs/failures.md`、F538、command、SKILL.md、self-improvement文書、hooks、repo外 memory が変更されていないことを確認する。

この read-only plan 段ではテストを実行しておらず、緑は主張しない。

## 総括

3経路はいずれも command 単体で拒否でき、SKILL.md はその境界を不可分適用している。
今回の再発は条文欠落ではなく、正しい固定条文の読解・遵守失敗である。
本 wave の最小変更は F747 再発 fragment と通常の worklog fragmentだけでよい。
親の択一は「docs-onlyで閉じる」か「信頼された外側 runnerによるruntime enforcementを別 waveへ送る」かであり、command／SKILL.md変更は既定にしない。