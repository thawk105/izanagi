# T-2074 救出材料の要否判定 — 止まった 5 wave の残骸 7 file

止まった 5 つの wave worktree に残っていた未着地差分 7 file を、1 件ずつ
「main へ着地させる」か「破棄して worktree ごと撤去する」かに裁いた記録。

判定基準はユーザーが確定した。破棄が既定であり、要否は「これが無いとどの wave が実際に壊れたか」
で決める。実例を挙げられないものは破棄する。過剰実装、ゲートを守るためのゲートは完成度に関わらず
破棄してよい。着地させるなら「これが無いと何の測定・主張が立たないか」を一行で書けなければならない。

## 依頼の前提を覆した実測

依頼は「main が触っていない (= 純粋な未着地) 5 file」という前提を持っていた。**成り立たない。**

1. **7 file はすべて main に実在する。** 未着地の実体は file の不在ではなく、
   worktree の未 commit 差分である。
2. **撤去候補 4 branch は未着地 commit ゼロ。** `git rev-list --count main..<branch>` が
   `impl-dev-wave-t2072-hold-author` / `impl-dev-wave-t2073-rootfix-author` /
   `impl-dev-wave-t2032-midflight-author` / `worktree-dev-wave-t1434-acceptance-red-fix` の
   4 本すべてで 0 である。tip はいずれも main の祖先であり、未着地分は worktree の
   未 commit 差分だけだった。
3. **`fix-dev-wave-t2027-timeout` は撤去対象外。** 未着地 commit を 2 本 (`2e35a2596`、
   `104954a30`) 持ち、内容は S8B compiler input と buildcache で、本件の 7 file とは無関係である。
   同 commit は稼働中の `worktree-dev-wave-t2027-t2043-external-input` (未着地 10 commit) からも
   到達可能である。

## 7 件の処遇と根拠

| # | file | 出所 | 処遇 | 根拠 |
|---|---|---|---|---|
| 1 | `orchestrator/tests/test_growth_test_holds_contract.py` | t2027-timeout-fix | **着地** | 別 session root の受入全走 2 走が、18382 件中この 1 node だけの赤だった |
| 2 | `orchestrator/tests/flaky_test_holds.py` | t2072-hold-author | 破棄 | root fix 後に hold を外して受入母集団へ戻し済み |
| 3 | `orchestrator/tests/test_flaky_test_holds_contract.py` | t2072-hold-author | 破棄 | 項目 2 の逐語鏡。row を捨てれば独立した検出力がない |
| 4 | `tools/check_wave_startup.py` | t2032-midflight-author | 破棄 | D1179 の決定より意味が後退する文面 |
| 5 | `orchestrator/tests/test_check_wave_startup.py` | t2032-midflight-author | 破棄 | 文字列の存在だけを固定する 73 行 |
| 6 | `orchestrator/tests/test_codex_worker_launch.py` | t2073-rootfix-author | 着地済み | worktree の blob が main と同一 |
| 7 | `orchestrator/tests/test_s8c_preregistration_invariant.py` | t1434-acceptance-red-fix | 破棄 | 別解が着地済みで、かつ偽緑を出しうる |

**着地させた 1 件の一行:** これが無いと、受入全走が偽の timeout 赤を出し続け、
その走が唯一の根拠として与えるはずの tested_tip の緑 — land の前提そのもの — が捨てられる。

### 項目 1 — 一次資料

受入全走 log 2 本の逐語。出典は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2027-t2043-external-input/acceptance-child-{1,2}.log`。

```
IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1 {"session_root":"/work/1/SFC/tanab/.izanagi-acceptance-shards/88c30977d31376c428ad3969694430d0","shard_count":3}
collected 18382 items
FAILED orchestrator/tests/test_growth_test_holds_contract.py::test_regular_pytest_path_keeps_single_hold_skip
1 failed, 18319 passed, 62 skipped
```

```
IZANAGI_ACCEPTANCE_SHARD_ARTIFACTS_V1 {"session_root":"/work/1/SFC/tanab/.izanagi-acceptance-shards/b25599b1c1fedce1e2caa6efae019d34","shard_count":3}
collected 18382 items
FAILED orchestrator/tests/test_growth_test_holds_contract.py::test_regular_pytest_path_keeps_single_hold_skip
1 failed, 18319 passed, 62 skipped
```

session_root が別の 2 走で、18382 件の収集に対し赤はこの 1 node だけだった。

この差分は**再実装していない**。同じ内容が既に commit `aaffa71a6` として存在し、
`worktree-dev-wave-t2027-t2043-external-input` から到達可能で main には未着地だったので、
cherry-pick で逐語回収した。D720 の 2 条件を両方満たす。

- **未着地:** `git cherry` で main に無いことを確認。`merge-base --is-ancestor` は偽。
- **現況で妥当:** 「12 caller のうちこの 1 本だけが実 conftest を読む」を main で caller 数 12 と
  実測して一致を確認。「両方の受入全走で予算が切れた」を上の一次 log で検証。
  「assert は経過時間を見ていない」を現物で確認。AI-Agent trailer は 1 block に 2 行あり完全。

合成の余地はゼロだった。cherry-pick 後の blob `5fdd36cac` は `aaffa71a6` の blob と byte 同一で、
main の blob は commit の親 blob `d60083028` と同一である。

### 項目 1 の erratum — 受入集合の言い方

回収した commit message は「its accept and reject sets are unchanged」と書く。
**厳密には正しくない。** 変わらないのは 4 つの assert が固定する機能的な正しさ集合であり、
実時間を含む生の実行受入集合は 10 秒から 120 秒へ広がる。

message は原著者の記録なので書き換えず逐語で回収し、訂正をここへ置く (D720 の (a) 群)。
絶対規律 2 には触れない。4 つの assert は 1 つも飛ばず、120 秒を超える hang は引き続き赤である。
固定されている性質は次の 4 つで、いずれも経過時間を見ていない。

- 内側 pytest の `returncode == 0`
- 出力が `"1 skipped"` を含む
- 出力が `"IZANAGI_GROWTH_HOLD_V1"` を含む
- 出力が `"IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1"` を含まない

repo 内に同等の代替機構は無い。flaky hold は exact node を丸ごと skip するのでこの 4 性質を
受入で検査しなくなる。growth hold は内側の高コスト node を既に skip しており、今回の外側 test は
その skip 経路が正しく働くことを実 conftest 込みで検査する側である。受入 runner の再試行は
`retryable-no-verdict-infra` だけで、pytest の rc=1 は `child-verdict` として終端し再試行されない。

### 項目 2・3 — 破棄根拠の差し替え

当初の破棄根拠は「root fix `42c62e4dd` が着地済みだから hold は不要」だった。
独立レビューが、hold の `cause` 欄自身の「当時の赤がこの経路だった直接証拠は無い」という自認は
**それ単独では破棄根拠として不十分**だと指摘した。同一 tree で赤と緑が観測された exact node は、
原因未確定でも一時 hold の対象になりうるからである。

破棄を決めるのは根本修理後の検証と hold 撤去の実績である。最終 tip `5254ac6ed` で baseline は
rc=0、変異 m03 は `[True]` と `[False]` の両 node で KILLED と記録されている
(`output/insights/2026-08-29_t2073-legacy-admission-wall-clock/README.md`)。
その後 hold は外され、対象 node は受入母集団へ戻っている。main の `flaky_test_holds.py` に
この row は無く、その状態で受入全走が緑を出し続けている。

D1160 は未採番赤の placeholder 登録を**許す**裁定であって、修理済み node を hold し続ける義務ではない。
D804 は stale 検査の委譲条件を定めるだけで、特定 row の寿命を延ばさない。

### 項目 4・5 — D1179 の履行状況

D1179 は「midflight が保証するのは段 5 直前の再測と提示だけであり、古い anchor のまま実装子を
投入しないことは保証しない。この限界は `--help` と `NOTE:` 行に明記する」と課している。

main の履行済み部分は、段 5 専用であること、fresh/resume の代用でないこと、
HEAD/main・clean tree・handoff を検査しないこと、乖離量が関門でないことの 4 つである。
**未履行は肯定形の保証範囲と、古い anchor 非保証の 2 つ**である。

破棄する救出差分はこの未履行部分を埋めようとしているが、文面が壊れている。

> 「midflight は段 5 実装子 dispatch 直前専用で、開始 gate (fresh / resume) の代用になる」
> という保証はしない。

「A かつ B を保証しない」は A である「段 5 専用」を肯定しない。直後の
「midflight が開始 gate の代用ではない」は B を正すが、A の規範性を回復しない。
D1179 の「専用の mode とする」という決定より後退している。

添付の 73 行が守るのは、docstring・help・NOTE に列挙文字列が存在し、help と成功時 NOTE が
同じ語を含むことだけである。midflight の実際の 6 検査と除外集合は既存 test が既に固定している。

**破棄しても D1179 の明記義務は残る。** T-2032 は完了にせず、正しい肯定形の文面を別の一手へ送る。

### 項目 7 — 偽緑の経路

main は `ce99cc7d4` で s8c candidate fixture の exact 5 node を `tracked_files` growth hold として
登録済みで、対象 module は末尾で hold guard を接続している。D1298 は hold 有効の現行 tip では
97 秒以上の unit が 10〜11 本あり、単一 loadgroup の短縮を採らないと明示している。

これに加えて、提案されている高速路 `_candidate_tree_is_head` は git 自身の clean 判定を
5 本の probe で再実装しており、**偽緑の経路を持つ**。dirty candidate を誤って `True` と判定すると
fresh index の `git add -A` を走らせず HEAD tree を再利用するため、HEAD が正しく未 commit candidate が
不正な場合に、その不正変更を候補 commit へ入れないまま不変条件 test が緑になる。
性能最適化が正しさ gate を迂回する典型であり、絶対規律 2 に反する。

添付の 5 本の正例は主要な通常例 (assume-unchanged / staged と worktree の差 / untracked /
submodule gitlink) を覆うが、同値性を閉じていない。fail-closed test は probe command の
timeout と rc 異常を覆うだけで、probe が誤って「clean」と答える意味上の誤判定を覆わない。
少なくとも次の穴が残る。

- real index の stat cache が clean と誤認する構成 (`core.trustctime=false` と同一 size・mtime の内容差)
- filter 設定が変わり、fresh index の `git add -A` なら blob が変わるが real index の
  stat shortcut では再 clean されない場合
- probe 完了から `HEAD^{tree}` 再利用までの並行変更
- 実際の skip-worktree、fsmonitor-valid state の正例 (コードは tag を見るが正例が状態を構築していない)

D1298 が無かったとしても、そのままでは着地に値しない。

## 撤去の損失ゼロ検査

### 独立した完全証明

**撤去候補 4 branch の tip はすべて main の祖先である。** したがって tip から到達可能な commit は
すべて main からも到達可能であり、ref を消しても到達不能にならない。
これは snapshot に依存しない完全な証明である。

- `impl-dev-wave-t2072-hold-author` -> `d03855e92`
- `impl-dev-wave-t2073-rootfix-author` -> `d03855e92`
- `impl-dev-wave-t2032-midflight-author` -> `7b4c992de`
- `worktree-dev-wave-t1434-acceptance-red-fix` -> `968fd25a6`

4 本とも `git rev-list --count main..<branch>` が 0 である。
`git branch -d` 自体もこの条件を機械的に強制する (`-D` は使わない)。

### 未 commit bytes の棚卸し

5 worktree すべてで `git ls-files --others --exclude-standard` が空だった。
ignored は `__pycache__` と `output/pegasus-dispatch/` だけである。
stash は repo 全体で 2 本あり、どちらも対象外 branch
(`worktree-dev-wave-t1563-acceptance-nproc`、`worktree-dev-wave-t816-step4-impl`) のもので、
本件の撤去では失われない。

### 救出写しの byte 一致

7 file すべてで worktree の現物と `/work/1/SFC/tanab/dev-wave-jobs/rescue-20260829/` の写しが
sha256 で一致した。

| file | sha256 |
|---|---|
| `t2027-timeout-fix/orchestrator/tests/test_growth_test_holds_contract.py` | `d66217dc8fc1c9fac9831d6f3904bbcb74a68c7320a4e4c85f39484f7e7e211f` |
| `t2072-hold-author/orchestrator/tests/flaky_test_holds.py` | `e4831531d5afddd6388dc376308ceb0a804751fce4267d3bd6728b04dec2d34e` |
| `t2072-hold-author/orchestrator/tests/test_flaky_test_holds_contract.py` | `a0d11de7cad8f58faa205ae7fc8b2938186a3ca948dfccfddf574f87bcf029f8` |
| `t2073-rootfix-author/orchestrator/tests/test_codex_worker_launch.py` | `97f1eb8fb6d0656f422abfbfbc11a955aecc78985a18f8148dc26c368dab8f4e` |
| `t2032-midflight-author/tools/check_wave_startup.py` | `90d64564e8328dce5e8007de05509b1db224561278b94adcf69c4d63fea32974` |
| `t2032-midflight-author/orchestrator/tests/test_check_wave_startup.py` | `573c96ddbd813f9ac39c7636414529de258829f7d9bf2bac658813819fe58921` |
| `dev-wave-t1434-acceptance-red-fix/orchestrator/tests/test_s8c_preregistration_invariant.py` | `20ba865fadbe7e87a8348a70b5280affcc955d25e988f18b48426b101d33da9e` |

### `check_branch_rescue.py` の結果と限界

4 branch と 4 worktree を 1 操作としてモデル化し、`--timeout-seconds 900 --ledger-check` で走らせた。

- `deletion_loss_closure`: `complete=true`、`commit_count=0`、`observed_commit_count=0`。
- `root_snapshot`: `complete=false`、`stable=false`。issue は 1 件だけで
  `root-snapshot-moved` (root inventory changed between the start and end snapshots)。
- rc=2。

**`root-snapshot-moved` の原因は本件と無関係である。** 走査中 61 秒の間に、稼働中の別 wave
(`dev-wave-t2033-axis1-retake`、`dev-wave-t2061-wal-admission`、
`dev-wave-acceptance-speedup-20260829`) が ref を進めたためである。
初回走にあった `pack-index-unreadable` は timeout を 900 秒へ上げて解消した。

root inventory が走査中に**増える**方向の変化は、撤去が何かを孤児にする可能性を作らない。
それでも snapshot が安定しない以上、この道具単独では損失ゼロを主張しない。
主張の根拠は上の**独立した完全証明** (4 tip がすべて main の祖先) である。

`ledger_notification_due=true` は、別セッション由来の到達不能 commit に台帳 entry が無いという
既存の通知であり、本件の撤去が作ったものではない。

### 変異 harness の観測対象

撤去時点で稼働していた変異 harness 2 本の `--repo` を `/proc/<pid>/cwd` で確認した。
`dev-wave-t2033-axis1-retake` と `dev-wave-t2061-wal-admission` の各 worktree であり、
**主 checkout ではない。** 主 checkout の untracked 集合 (`?? .codex/worktrees/` の 1 行) は、
配下の worktree を 4 本消しても directory 自体が残るため変化しない。

## 変異事前登録

| id | 変異 | 期待 |
|---|---|---|
| `M1-ANTI-HANG-BUDGET-NOT-WIRED` | `], timeout=120.0)` -> `], timeout=0.001)` | KILLED = {`orchestrator/tests/test_growth_test_holds_contract.py::test_regular_pytest_path_keeps_single_hold_skip`} |

単一理由性: 前後に同じ入力を拒否する層が無い。`_run_subprocess` は `TimeoutExpired` を捕捉せず
伝播させる。repo に pytest 全体へ掛かる timeout plugin の設定は無い。anchor は対象 file 内で 1 箇所。

DW-M08 の「新旧両走」は適用外である。本 wave はテストを新設も改名もせず、既存 test の基盤上界を
変えるだけで、検出力を示すべき新テストが存在しない。

## 逐語

- `s3-consult-sol.md` — 段 3 相当の独立レビュー全文 (read-only codex、gpt-5.6-sol、xhigh)。
  7 件を親の処遇表を見る前に独立導出し 7/7 一致。補正 7 件はすべて real と裁定し採用した。
- `s4-adjudication.md` — 段 4 裁定全文。
