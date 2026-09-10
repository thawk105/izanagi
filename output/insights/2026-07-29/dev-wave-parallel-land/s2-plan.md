結論は、P1/P3 は意図を残して条件を強化し、P2 はそのままでは棄却です。共通の stage 9 helper、短時間の共通 lock、`9→6→7→8→9` の有界な再同期を導入するのが安全です。

調査は read-only で行い、編集・pytest 実行はしていません。調査中にも local main は `fa4774c` から `180d3c1` へ前進しており、対象 race は現に発火しています。

## 現状診断

- 現行の段 9 は「main clean・開始基準不変・FF 可能・監査済み集合」を自然言語で確認するだけで、accepted-main SHA や race を機械的に束縛していません。[core.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/core.md:101)
- dispatcher は段 9 を `DW-S09` へ正しく集約していますが、終端文は他 session 差分を一律に取り込まず停止する契約です。これを監査済み再同期だけ許す形へ狭く改訂する必要があります。[dev-wave.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.claude/commands/dev-wave.md:109)
- Codex Skill は共通 dispatcher を読む薄い adapter ですが、段 9 の条件を再掲しており drift 面があります。[SKILL.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.agents/skills/dev-wave/SKILL.md:43)
- startup checker は開始時の passive gate です。fresh は全 dirt を拒否し、resume は意図的に HEAD 前進・dirty を許します。[check_wave_startup.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_wave_startup.py:226) [test_check_wave_startup.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_wave_startup.py:217)
- supervisor checker は「child が既に main を land した後」の独立検証で、active handoff を全拒否し、自動 merge/retry を持ちません。[checker.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_waves/checker.py:443) [checker.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_waves/checker.py:549) また real supervisor は未開放です。[README.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/dev-wave-supervisor/README.md:8)
- supervisor 自身も最終検査後の完全な TOCTOU 遮断を非目標にしています。したがって、その checker を interactive land の race 保証として流用してはいけません。[README.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/dev-wave-supervisor/README.md:87)

## P1〜P3 の裁定

| 前提 | 裁定 | 理由と代案 |
|---|---|---|
| P1 | 意図採用・文言は棄却 | 「形式が正しい」だけでは foreign/active を証明できず、`.gitignore` は container 内の異物も隠します。handoff の active/鮮度/own-session 除外と、container の registered-worktree identity を機械検査します。 |
| P2 | そのまま棄却 | `current == accepted` の確認後に `merge --ff-only` するだけでは TOCTOU が残ります。競合 land が wave tip の祖先なら stale acceptance のまま FF が成功し得ます。共通 git-dir 上の非 blocking 短時間 lock 内で最終比較と FF を行います。 |
| P3 | 条件付き採用 | main 前進を自動的に信用せず、旧 accepted-main の descendant であることと独立監査を要求します。upstream 監査後に immutable SHA を wave branch へ mergeし、競合解決後の統合結果も再監査・再受入します。 |

## 1. main cleanliness の exact 条件

新 helper は `git status --porcelain=v2 -z --untracked-files=all --ignore-submodules=none` を解析し、次だけを例外にします。

他 session handoff は、以下をすべて満たす場合だけ許可します。

- Git 上は untracked の direct child `docs/handoff/YYYY-MM-DD-<safe-slug>.md`。
- caller が渡す `--own-handoff-name` と異なり、own handoff 自体は main/wave 双方から消えている。
- `lstat` で symlink・directory・FIFO ではない regular file、`st_nlink == 1`、同一 FD から strict UTF-8 で読む。
- 冒頭定型が一意で、状態は `作業中` または `計測中`。`中断` は例外にしない。
- mtime が 48 時間以内。既存 stale 判定と揃える。[check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:1968)
- 基準 commit は full lowercase SHA で、同じ repository に commit object として実在する。
- helper は内容を変更・stash・commit・削除しない。

worktree container は、`/.claude/worktrees/` と `/.codex/worktrees/` だけを root-anchored ignore に追加し、helper が別途全 direct child を検査します。

- container と child に symlink component がなく、safe basename の一階層だけ。
- `git worktree list --porcelain` に一意に登録され、`prunable`・detached・main branch ではない。
- Claude は `worktree-<basename>`、Codex は `codex/<basename>` に branch 名を束縛する。
- child の top-level と common git-dir の device/inode が main と一致する。
- loose file、未登録 directory、別 repository、branch/path 不一致は拒否する。
- Git 2.34.1 は `worktree list -z` 非対応なので、安全な basename を先に制限し、line parser は未知・重複・未終端 field を fail-closed にします。

tracked/staged/unmerged、submodule dirt、unknown untracked、own handoff、上記以外の container はすべて拒否します。

## 2. accepted-main・wave tip・FF の束縛

受入結果は三つ組として扱います。

- `A`: 受入開始前後で不変だった local main SHA
- `T`: 全 commit・記録・自己改善を含む最終 wave branch tip
- `L`: `git rev-list --reverse --topo-order A..T` と完全一致する監査済み commit 列

受入中に main または wave tip が動けば結果を破棄します。helper は lock 取得後に以下を再確認します。

1. current main `C == A`
2. wave worktree HEAD `==` wave branch ref `== T`
3. main/wave の cleanliness
4. `A` が `T` の ancestor
5. 実際の commit 列が `L` と exact match
6. candidate に gitlink変更がないこと。v1 では、land 後に submodule worktree を dirty にし得る gitlink変更を fail-closed にする
7. `git merge --ff-only --no-edit --no-stat T`
8. postcondition `main HEAD == T` と cleanliness の再確認

lock は common git-dir の専用 regular fileを `O_NOFOLLOW` で開き、`flock(LOCK_EX|LOCK_NB)` します。監査やテスト中は保持せず、最終再観測と一回の local FF の間だけ保持します。

これは共通 dispatcher に従う Claude/Codex session 間の race を閉じます。同一 UID の非協調 process が helper を無視して直接 main を変更する脅威まで要求するなら、短時間 lock では不足し、`reference-transaction` hook/CAS を含む別設計が blocker になります。

## 3. main 前進後の順序

段 9 で `C != A` なら、単なる stage 9 内 retry ではなく、次の back-edge を使います。

1. `A → C` が FF ancestry でなければ即停止。reset/force/rewrite は再同期しない。
2. `A..C` を「別 session 由来の未信頼 upstream」として独立監査する。
3. mutable な `main` 名ではなく固定 SHA `C` を wave branch へ mergeする。rebase はしない。
4. conflict があれば wave worktree 内だけで解決する。実装面の解決は D95 に従い Codex author へ戻す。
5. merge結果・競合解決・consumer 取り残しを再度敵対監査する。
6. dispatcher の `9→6→7→8→9` へ戻し、変異・受入、worklog/phase/decision 保存則、自己改善終端を再実行する。
7. 新しい pair `(A=C, T=new tip, L=new list)` を作り直す。
8. distinct な main 前進は最大3回。4回目は `main-race-exhausted` で停止する。
9. helper の lock-busy は main を変更せず終了し、busy のまま長時間待たない。

これにより、記録 commit 後の main 前進で worklog 番号や task ID が衝突した場合も、段7を飛ばさず再採番できます。

## 4. helper の CLI・exit code・Git 境界

新設する CLI は次です。

`python3 tools/dev_wave_land.py --main-worktree ABS --wave-worktree ABS --accepted-main-sha SHA --accepted-wave-tip-sha SHA --own-handoff-name NAME --audited-commit SHA ...`

`--repo`、相対 path、暗黙 cwd、caller 指定の任意 Git argv は持たせません。wave branch は registered worktree から導出します。

| rc | 意味 |
|---:|---|
| 0 | `landed` または、再受入済み tip と main が同一の `already-landed` |
| 2 | argparse usage error |
| 10 | accepted-main stale。main 無変更、再同期可能 |
| 11 | land lock busy。main 無変更 |
| 20 | main dirt/submodule/unknown untracked |
| 21 | handoff/container exception 不正 |
| 22 | main/wave/common-dir/worktree identity 不正 |
| 23 | tip・ancestry・監査 commit 列・wave cleanliness 不正 |
| 24 | Git execution/postcondition failure |

Git は閉じた operation tableからのみ起動します。許可するのは `rev-parse`、`symbolic-ref`、`worktree list --porcelain`、`status --porcelain=v2 -z`、`cat-file -e`、`for-each-ref refs/replace`、`merge-base --is-ancestor`、`rev-list`、`diff-tree --raw`、最後の `merge --ff-only` です。

全呼出しで `shell=False`、stdin=`DEVNULL`、remote/network commandなし、全 inherited `GIT_*` を除去し、global/system config、hooks、fsmonitor、replace object、terminal prompt を無効化します。merge target は検証済み40桁 SHAだけです。

## 5. file:line 実装計画

1. [.gitignore](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.gitignore:22)

   `/.claude/worktrees/` と `/.codex/worktrees/` を追加します。広い `**/worktrees/` は使いません。

2. [dev-wave.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.claude/commands/dev-wave.md:31)

   - lines 31–54: 通常遷移に、`DW-S09` が許す最大3回の `9→6` back-edge を追加。
   - lines 109–113: 他 session 差分の一律拒否を、監査済み main descendant の wave-side mergeだけ許す表現へ変更。
   - 段9の詳細は書かず `DW-S09` と helper への dispatchだけにする。

3. [core.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/core.md:17)

   - lines 17–22: `DW-STOP` の「別 session 差分禁止」に、`DW-S09` の監査済み再同期だけを例外として明記。
   - lines 101–107: accepted pair、helper rc、audit→merge→6/7/8再走、3回上限を唯一の prose 正本として再定義。

4. [SKILL.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.agents/skills/dev-wave/SKILL.md:43)

   lines 43–49 の段9再掲を削り、`core.md/DW-S09` と `tools/dev_wave_land.py` を読む Codex 固有 pointerだけにします。Claude/Codex で手順文を二重管理しません。

5. [handoff/README.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/handoff/README.md:5)

   lines 5–17 と定型 lines 22–36 に、land 例外でいう active/foreign/48h/own-name 除外を定義します。

6. 新規 `tools/dev_wave_land.py`

   - planned lines 1–70: reason/exit enum、strict argparse、JSON結果
   - 71–160: sanitized exact Git operation table
   - 161–250: absolute path・symlink・common-dir・worktree identity
   - 251–360: porcelain status、handoff、container検証
   - 361–450: acceptance pair、audit列、short lock、FF、postcondition

7. 新規 `orchestrator/tests/test_dev_wave_land.py`

   temp repository と real linked worktree を使う境界/raceテストを置き、pytest と直接実行の二重 runner に対応します。

8. [check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:148)

   - lines 148–181: core budgetを9,000→11,000、aggregateを24,000→26,000へ明示 bump。現状は core 8,893/9,000、aggregate 23,962/24,000で新契約を収容できません。
   - Codex Skill の必須 literal に `docs/dev-wave/core.md` と helper pathを追加。
   - lines 282–340: 段9が引き続き `DW-S09` 一箇所へ dispatchすることを固定。

9. [test_check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py:1812)

   Skillから core/helper pointerを除く負例と、独立 surface pinを追加します。[test_check_docs.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_check_docs.py:2052)

10. 記録

   - [decisions.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/decisions.md:4298) の末尾に、D69をinteractive並行landについて上書きする新D。
   - [failures.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/failures.md:959) の末尾に、foreign handoff/Codex containerがclean gateを自己破壊した実測事象を新Fとして記録。
   - [phase3.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/phase3.md:517) と [worklog.md](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/worklog.md:968) は、main再同期後に番号・保存則を再計算して追記。
   - mutation ledgerと敵対レビューは既存 `output/insights/2026-07-29_dev-wave-parallel-land/` に置く。

## 6. テスト計画と checker の責務分離

正例:

- foreign active handoffだけ、Claude containerだけ、Codex containerだけ、三者同時でも land成功。
- containerがまだ `.gitignore` に入っていない導入wave自身も成功。
- bytes/inode/hashを比較し、foreign artifactへ非接触。
- main前進後に監査・merge・再受入した新pairで成功。

負例:

- tracked/staged/unmerged/submodule dirt、未知untracked。
- own/stale/中断/malformed/invalid UTF-8/symlink/FIFO/hardlink handoff。
- container symlink、loose file、未登録 child、別repo、branch/path不一致、prunable/detached。
- stale accepted-main、tip移動、hidden/reordered commit、non-FF、gitlink変更。
- `GIT_DIR` 等のenv poison、replace refs、shallow repo、relative/symlink path。

race:

- 同じ `A` から異なるtipを持つ二processでは一方だけ成功。
- lock保持中の相手はrc11でmain無変更。
- 先行land後のloserはrc10。
- 先行tipが後続tipの祖先で、裸の `--ff-only` なら成功する攻撃例でも、旧`A`では拒否する。

mutation:

- accepted-main比較除去
- lock除去
- ancestry/ff-only除去
- audit列比較除去
- tracked/submodule dirt判定除去
- handoff active/own/48h判定除去
- container registration/symlink判定除去
- branch-tip/HEAD束縛除去
- active handoff/containerを常時拒否する過剰拒否変異

各変異は期待test nodeを事前登録し、復元後はF52に従ってbytecode cacheも無効化します。

責務は次のように分離します。

| 面 | 既存/新規 | 責務 |
|---|---|---|
| wave開始 | `check_wave_startup.py` | passive fresh/resume gate。変更しない |
| fake supervisor事後検証 | `tools/dev_waves/checker.py` | child receipt・既land main・全handoff拒否。変更しない |
| interactive段9 | `tools/dev_wave_land.py` | ownership-aware cleanliness、accepted pair、短時間直列化、local FFのみ |

回帰として既存 startup、`test_dev_waves_git_state.py`、`test_dev_waves_checker.py`、integration の main unchanged/dirty/non-FF/commit mismatch を再走します。

最終受入は targeted pytest、mutation、`python3 tools/run_tests.py`、`tools/check_docs.py`、`tools/check_codex_agents.py`、commit前後の provenance検査です。

## 総括

推奨 plan は、共通 `DW-S09` を唯一の文章正本にし、Claude/Codex双方が同じ `tools/dev_wave_land.py` を呼ぶ構成です。main前進時は最大3回の `9→6→7→8→9` 再同期とし、最終FFだけ短時間lockで直列化します。

blocker は二点です。親briefの `T-173` は既に別のactive handoff「Codex cleanup-branches Skill」が使用中なので、記録直前に次の空きIDへ振り直す必要があります。また、非協調の直接Git writerまで防御対象に含めるなら、短時間lock案では足りず追加CAS設計が必要です。

主な変更対象は `.gitignore`、dispatcher/core、Codex Skill、handoff契約、新land helperと境界テスト、check_docsのpointer/budget gate、D/F/phase/worklog記録です。