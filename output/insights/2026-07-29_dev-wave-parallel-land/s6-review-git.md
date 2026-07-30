以下の 6 件を must-fix と判定します。静的検査と read-only Git コマンドのみ使用し、テスト・編集・ネットワークアクセスは行っていません。

## Findings

1. Critical — ignored untracked が dirt 検査と worktree 登録検査を完全に迂回する

   該当箇所: [tools/dev_wave_land.py:666](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:666)、[tools/dev_wave_land.py:683](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:683)、[tools/dev_wave_land.py:686](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:686)、[s4-adjudication-plan-v2.md:42](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s4-adjudication-plan-v2.md:42)

   `git status --untracked-files=all` は ignored path を列挙しません。現 common Git admin の `info/exclude` は `**/.claude/worktrees/` を ignore しています。したがって、main がそれ以外 clean なら、未登録の `.claude/worktrees/fake/` が存在しても `records` は空になり、686–687 行で return して `_registered_worktree_prefixes()` すら呼ばれません。`build/` など他の ignored unknown dirt も常に不可視です。

   さらに T が ignored foreign-worktree path と衝突する tracked path を含む場合、998–1002 行の merge は ignored foreign artifact を上書きし得ます。これは「他 session 所有物へ非接触」という契約にも反します。

   DW-G05 影響: 受理集合が「正規 handoff と双方向登録済み worktree」から、任意の ignored unknown/unregistered dirt まで拡大します。`landed` を返しながら foreign worktree を破損する経路も残ります。既存 unknown-untracked test は非 ignored の `unknown.txt` しか覆っていません。

2. High — lock 取得前の main 検査により、協調 lander が `busy` ではなく `rejected` になる

   該当箇所: [tools/dev_wave_land.py:903](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:903)、[tools/dev_wave_land.py:918](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:918)、[tools/dev_wave_land.py:950](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:950)、[tools/dev_wave_land.py:1013](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:1013)

   Interleaving:

   1. winner が lock を保持して ff checkout 中。
   2. loser が起動するが、lock を試す前に `_verify_main_clean()` と `_verify_heads()` を実行する。
   3. winner の HEAD 更新前の working-tree/index 変更を tracked dirt、または HEAD/ref mismatch として観測する。
   4. loser は lock holder を確認せず `rejected` を返す。

   `test_nonblocking_common_lock_reports_lock_busy` は「lock を保持するだけで main を変えない」holder しか模擬していないため、この競合を検出しません。

   DW-G05 影響: 正常な same-base loser が復旧可能な `lock-busy` / `stale-main` ではなく permanent-looking `rejected` へ落ち、両 wave 成果を含む最終 main の受理集合が不当に縮小します。状態分類も契約どおり distinct ではありません。

3. High — handoff/worktree の検証結果が pathname だけで再利用され、inode replacement に弱い

   該当箇所: [tools/dev_wave_land.py:570](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:570)、[tools/dev_wave_land.py:623](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:623)、[tools/dev_wave_land.py:683](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:683)、[tools/dev_wave_land.py:700](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:700)

   Handoff は全ファイルを検証して FD を閉じた後、別の `git status` snapshot に pathname が含まれるかだけを確認します。検証直後に foreign manager が通常の上書き・atomic rename を行えば、malformed/symlink/別 inode が「検証済み pathname」として通ります。

   Worktree は逆に status snapshot を先に取り、admin/backpointer 検証後に FD を閉じます。その後 child が remove/recreate されても、古い status record と prefix だけで許可されます。普通の並行 `git worktree add` や handoff 更新を途中状態で観測すると spurious rejection にもなります。

   同じ非原子的検査は merge 後の `_postcondition()` でも繰り返されるため、main が既に T に進んだ後、foreign handoff の更新だけで `landed-postcondition-failed` になり得ます。

   DW-G05 影響: 受理集合へ schema/admin 未検証の replacement が入り、反対に正常な並行 session は拒否されます。main を変更済みの postcondition failure も foreign control-plane writerだけで発生します。

4. Critical — effective Git config の検査漏れから filter child 実行と partial main mutation が可能

   該当箇所: [tools/dev_wave_land.py:485](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:485)、[tools/dev_wave_land.py:495](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:495)、[tools/dev_wave_land.py:904](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:904)、[tools/dev_wave_land.py:998](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:998)、[tools/dev_wave_land.py:1001](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:1001)

   `_verify_local_config()` は `git config --local` のみを、`--includes` なしで検査します。Git 2.34.1 では worktree config は独立 scope です。`extensions.worktreeConfig` を有効にして primary `config.worktree` に `filter.<name>.smudge/process` を置けば検査を迂回できます。include 経由の effective config も同様に漏れます。

   T の attributes がその filter を使う場合、ff merge が任意 child process を起動します。これは「標準ライブラリと allowlist Git argv だけ」という trust boundary を破ります。filter failure は checkout を部分更新したまま HEAD を旧値に残し得ますが、[tools/dev_wave_land.py:845](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:845) は `main_after != T` なら cleanliness/postcondition を調べず `not-landed` を返します。

   また lock FD は Git merge に継承されるため、外部 filter grandchild が FD を保持すれば Git/helper 終了後も lock が残る可能性があります。既存 FD test は直接 wrapper child までしか確認していません。

   さらに history/config 検査自体が lock 前だけなので、検査後に common config、shallow、graft を変更する check-to-use raceも残ります。replace は `GIT_NO_REPLACE_OBJECTS`、hooks/fsmonitor/autostash は command config で適切に抑止されていますが、この漏れはそれらで閉じません。

   DW-G05 影響: 外部 child 実行、foreign artifact mutation、partial index/working tree を伴う `not-landed` が受理境界に入ります。`not-landed` が「main 非変更」を意味しないため、failure taxonomy も不正確です。

5. High — gitlink-changing wave は D16 同期後も evidence-preserving な成功状態へ遷移できない

   該当箇所: [tools/dev_wave_land.py:914](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:914)、[tools/dev_wave_land.py:930](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:930)、[tools/dev_wave_land.py:857](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_wave_land.py:857)、[test_dev_wave_land.py:340](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py:340)

   `gitlinks_changed` は元の A と T の tree 差だけで決まり、現在の submodule 同期状態を検査しません。

   1. 初回 land は main を T へ進めて `landed-postcondition-failed`。
   2. D16 の submodule sync を完了する。
   3. 同じ A/T/audited closure で再実行しても、930–940 行が無条件に同じ failure を返す。

   `tested_main=T, tested_tip=T, audited=()` に取り替えれば `already-landed` にできますが、それは元の A..T 監査列を消して成功させる laundering であり、exact audited-commit evidence を維持しません。現在の test は初回 failure だけを期待し、回復経路を検査していません。

   DW-G05 影響: 一般 dev-wave が従来受理していた gitlink change を永久に拒否するか、監査対象 commit 列を空にして成功させるかの二択になります。

6. High — mandatory same-base E2E が「再受入」を実行していない

   該当箇所: [s4-adjudication-plan-v2.md:20](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s4-adjudication-plan-v2.md:20)、[test_dev_wave_land.py:640](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py:640)、[test_dev_wave_land.py:657](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/orchestrator/tests/test_dev_wave_land.py:657)、[docs/dev-wave/operations.md:125](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/operations.md:125)

   Test は loser へ main を merge し、`rev-list` を再計算して直ちに `land()` を呼んでいます。merge 後 T に対する acceptance の実行・結果固定は一度もありません。docstring の「merge/reaccept」は実体と一致しません。

   Helper が acceptance receipt を検証しないこと自体は段4裁定済みですが、その場合こそ mandatory E2E が manager 側の「新 main 監査→merge→条件再評価→受入→retry」を独立に固定する必要があります。現テストは helper単発への縮退を防ぐ M13 oracle になっていません。

   DW-G05 影響: dispatcher から再受入工程が脱落してもテストが緑のままになり、winner を取り込んだ未試験 merge tip が local main の受理集合へ入ります。

## Scope notes

- Linked-worktree `.git`、admin `gitdir` backpointer、symlink final component、lock metadataの初期検査は丁寧です。full SHA、wave HEAD/ref、exact `rev-list A..T`、locked main の ancestry再検査、固定 SHAへの ff-only も静的には確認できました。
- `_verify_repository()` が inodeをFDで固定した後も全 Git commandが pathname `-C` を使うため、main/wave rootのrename/replacementで別repoへ向く余地はあります。同様にlock file unlink/recreateはflockを分裂させます。ただし、いずれも同一UIDの非協調writerまたはcleanupを必要とするため、今回は明示された scope 外として verdict根拠には含めていません。
- cross-host flock、remote/push、悪意ある common Git admin 改変も同じく scope 外です。

## 総括

NO-GO