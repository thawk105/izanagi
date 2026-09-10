## 総括

独立判定は、項目 1 を着地、項目 2〜7 を破棄です。親とは実質 7/7 一致します。形式上は項目 6 だけ、私は「救出材料を破棄」、親は「着地済み」と呼んでいますが、main への追加作業不要という処置は同じです。  
重要な補正は三つあります。項目 1 は実行時間まで含む生の受入集合を広げますが、assert が固定する正しさ集合は広げず、絶対規律 2 には触れません。項目 7 は D1298 以前に、誤判定時に偽緑を出しうるため着地不可です。  
最大の異論は撤去安全性です。`root_snapshot.complete=false` のままの `commit_count=0` は十分な損失ゼロ証明ではありません。親が予定する timeout 拡大再走で `root_snapshot.complete=true` を得るまで撤去してはいけません。  
なお実走は行っておらず、以下は repo と保存差分の静的検査です。

## 独立判定 (7 件)

| # | 判定 | 一行理由 | 壊れた実例 |
|---|---|---|---|
| 1 | **着地** | assert は内側 pytest の成功、単一 skip、正規 hold marker、bypass-refused 不在を固定しており、10 秒はその性質ではない。[現行 test:2534-2550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/test_growth_test_holds_contract.py:2534) | **あり。** `aaffa71a6` の commit 本文に “that budget expired on both acceptance full runs of this branch while the same node stayed green standalone” とある。差分自身も「10.0 s budget expired twice」と記録する。[materials-diff.txt:12-24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:12) |
| 2 | **破棄** | 同じ v1 実時間 admission 経路は `42c62e4dd` で修理され、`5254ac6ed` で hold を外して受入母集団へ戻している。[worklog.md:1996-2048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/docs/worklog.md:1996) | **現行の実例なし。** 歴史上の T-1958 赤はあるが、現在必要な hold の実例ではない。 |
| 3 | **破棄** | 項目 2 の live row・digest・逐語 field を固定する鏡であり、row を捨てれば独立した検出力がない。[materials-diff.txt:101-161](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:101) | **実例なし。** |
| 4 | **破棄** | D1179 の正しい未履行部分を含む一方、「段 5 専用」を否定対象の引用へ入れており、そのままでは意味を後退させる。[materials-diff.txt:188-218](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:188) | **実例なし。** ただし D1179 の未履行自体は残る。 |
| 5 | **破棄** | docstring、help、NOTE に所定の部分文字列があることを固定する 73 行で、既存の midflight 挙動検査に新しい挙動 oracle を足していない。[materials-diff.txt:230-300](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:230) | **実例なし。** |
| 6 | **破棄・no-op** | 保存材料は main と差分ゼロで、救出対象となる byte がない。[materials-diff.txt:308-310](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:308) | **実例なし。** 親の「着地済み」と処置は同じ。 |
| 7 | **破棄** | main は exact 5 node を growth hold 済みで、D1298 は現 regime の単一 loadgroup 短縮を退ける。加えて高速判定は偽緑を出しうる。[growth_test_holds.py:205-247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/growth_test_holds.py:205) | **現行の実例なし。** T-1434 の歴史的 timeout は `ce99cc7d4` の hold で解消済み。 |

## 問い 2〜8 への回答

### 問い 2: `timeout=120.0` は受入集合を広げるか

**生の実行受入集合は広げますが、テストが固定する正しさ集合は広げません。**

この test が固定する性質は次の四つです。

- 内側 pytest が `returncode == 0`
- 出力が `"1 skipped"` を含む
- 正規の `"IZANAGI_GROWTH_HOLD_V1"` を含む
- `"IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1"` を含まない

根拠は [test_growth_test_holds_contract.py:2534-2550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/test_growth_test_holds_contract.py:2534) です。共通 helper の 10 秒は subprocess 基盤の既定値であり、assert された出力契約には含まれません。[同:1497-1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/test_growth_test_holds_contract.py:1497)

したがって、10 秒で `TimeoutExpired` になった走と、同じ rc・出力を最終的に返して 120 秒以内に終わる走は、固定対象の性質では同じです。ただし「10 秒以内に終わる実行だけを受理」と時間も集合へ含めるなら、親の「accept/reject set は不変」は厳密には誤りです。変わらないのは**機能的な正しさ集合**です。

絶対規律 2 には触れません。規律 2 は「性能や利便性のために正しさゲートを緩めない」と定めますが、この変更は四つの assert を飛ばさず、120 秒を超える hang は引き続き赤です。[CLAUDE.md:54-71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/CLAUDE.md:54)

既存機構に同等の代替はありません。

- flaky hold は exact node を丸ごと skip するため、四つの性質を受入で検査しなくなります。[conftest.py:2001-2018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/conftest.py:2001)
- growth hold は内側の高コスト node を既に skip しています。今回の外側 test は、その skip 経路が正しく働くことを実 conftest-backed pytest で検査する側です。[growth_test_holds.py:201-203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/growth_test_holds.py:201)
- 受入 runner の再試行は `retryable-no-verdict-infra` だけです。pytest の rc=1 は `child-verdict` として終端し、再試行されません。[dev_wave_wait.py:3830-3858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/tools/dev_wave_wait.py:3830)、[同:4056-4108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/tools/dev_wave_wait.py:4056)

よって timeout の局所拡大が、repo 内の既存機構では最小の性質保存修理です。

### 問い 3: flaky hold 2 件の破棄

`42c62e4dd` と hold の `cause` は、**機序として同じもの**です。

hold は次のように書きます。

> 「launcher プロセス全体の実時間が admission 上限を超えると v1 判定表が拒否する経路」

[materials-diff.txt:68-75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:68)

root fix 後の repo は v1 fixture を `max_wall="100"` で作り、上限が subprocess watchdog 10 秒を上回ることを固定しています。[test_codex_worker_launch.py:6354-6365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/test_codex_worker_launch.py:6354) 同時に、100 秒ちょうどを受理し、100.001 秒を拒否する境界 test を残しています。[同:6443-6485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/test_codex_worker_launch.py:6443)

ただし、hold の「当時の赤がこの経路だった直接証拠は無い」という自認は、**それ単独では破棄根拠として不十分**です。同じ tree で赤と緑が観測された exact node は、原因未確定でも一時 hold の対象になりえます。repo 自身も「症状を過不足なく再現するまでで、当時の赤がこの経路だったとは主張しない」と限定しています。[測定記録:66-81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/output/insights/2026-08-29_t2073-legacy-admission-wall-clock/README.md:66)

破棄を決めるのは、根本修理後の検証と hold 撤去です。最終 tip `5254ac6ed` で baseline は rc=0、m03 は `[True]` と `[False]` の両 node で KILLED と記録されています。[同:98-113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/output/insights/2026-08-29_t2073-legacy-admission-wall-clock/README.md:98) また、`git diff --exit-code 5254ac6ed..main -- orchestrator/tests/test_codex_worker_launch.py` は rc=0 でした。これは今回の実走ではなく、記録済み green tip と現行 source の byte 同一性確認です。

D1160 は未採番赤の placeholder を**許す**裁定で、修理済み node を hold し続ける義務ではありません。[rulings-verbatim.md:130-147](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/rulings-verbatim.md:130) D804 も stale 検査の委譲条件を定めるだけで、特定 row の寿命を延ばしません。[同:149-177](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/rulings-verbatim.md:149)

したがって項目 2・3 の破棄は妥当です。

### 問い 4: midflight 文面と 73 行

D1179 の履行状況は次のとおりです。

履行済み:

- `--help` は「段 5 実装子 dispatch 直前専用」
- fresh/resume の代用ではない
- HEAD/main、clean tree、handoff を検査しない
- 乖離量は関門でない

[check_wave_startup.py:598-607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/tools/check_wave_startup.py:598)

`NOTE:` も段 5 専用、開始 gate の代用でないこと、検査しない三項を出しています。[同:650-662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/tools/check_wave_startup.py:650)

未履行:

- 保証は「段 5 直前に乖離を再測し、gate 自身の実測値を提示することだけ」という肯定形
- 「古い anchor のまま実装子を投入しないこと」は保証しないという限界

これは D1179 が `--help` と `NOTE:` の両方へ明記するよう要求しています。[rulings-verbatim.md:14-16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/rulings-verbatim.md:14)

提案文の、

> 「midflight は段 5 実装子 dispatch 直前専用で、開始 gate の代用になる」という保証はしない

は意味を保っていません。「A かつ B を保証しない」は、A である「段 5 専用」を肯定しません。その後で「開始 gate の代用ではない」は B を正しますが、A の規範性は回復しません。[materials-diff.txt:195-203](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:195) D1179 の「専用の mode とする」という決定より後退しています。[rulings-verbatim.md:7-16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/rulings-verbatim.md:7)

追加 73 行が守るのは、docstring、help、NOTE に列挙文字列が存在し、help と成功時 NOTE が同じ語を含むことです。[materials-diff.txt:230-300](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:230) midflight の実際の 6 検査や除外集合は既存 test が既に固定しています。[test_check_wave_startup.py:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/test_check_wave_startup.py:987) よって追加分は、この判定基準では「ゲートを守るための文字列ゲート」に当たり、破棄でよいです。

親の P2 は条件付きで妥当です。壊れた救出差分を D1179 の名目で land しないことは D720 の「現況で妥当」条件に従います。[rulings-verbatim.md:46-61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/rulings-verbatim.md:46) ただし、破棄しても D1179 の明記義務は満たされません。T-2032 を未完了のまま維持し、正しい文面を別の一手へ送る場合だけ許容されます。既存台帳も T-2032 を「実装待ち」としています。[archive:1073-1076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/docs/archive/worklog-phase3-0828-1054.md:1073)

### 問い 5: s8c の 365 行

親の二根拠は両方成立します。

第一に、`ce99cc7d4` は candidate fixture の exact 5 node を `tracked_files` growth hold として登録しています。[growth_test_holds.py:205-247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/growth_test_holds.py:205) 対象 module は末尾で hold guard を接続済みです。[test_s8c_preregistration_invariant.py:745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/orchestrator/tests/test_s8c_preregistration_invariant.py:745) `git diff --exit-code ce99cc7d4..main` でも関連 2 file は byte 同一でした。

第二に D1298 は、hold 有効の現行 tip では 97 秒以上の unit が 10〜11 本あり、単一 loadgroup の短縮を採らないと明示しています。[decisions.md:41731-41755](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/docs/decisions.md:41731) worklog もこの `git add -A` 短縮を「実行しない方がよいこと」と記録しています。[worklog.md:457-482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/docs/worklog.md:457)

高速路が誤ると、偽緑と偽赤の両方がありえます。危険なのは偽緑です。

- `_candidate_tree_is_head` が dirty candidate を誤って `True` とすると、fresh index の `git add -A` を走らせず HEAD tree を再利用します。[materials-diff.txt:370-428](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:370)
- HEAD が正しく、未 commit candidate が不正な場合、その不正変更を候補 commit へ入れないため、不変条件 test が緑になります。
- probe の失敗を誤処理する方向は pytest failure、すなわち偽赤になります。

偽緑は、性能最適化が正しさ gate を迂回する典型なので絶対規律 2 に反します。[CLAUDE.md:67-71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/CLAUDE.md:67)

添付 test は主要な通常例を覆いますが、同値性を閉じていません。

- assume-unchanged、staged/worktree 差、untracked、submodule gitlink は覆う。[materials-diff.txt:569-710](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:569)
- fail-closed test は probe command の timeout/rc異常を覆うだけで、probe が誤って「clean」と答える意味上の誤判定は覆いません。[同:511-566](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/materials-diff.txt:511)

塞がれていない穴には、少なくとも次があります。

- real index の stat cache が clean と誤認する構成、例えば `core.trustctime=false` と同一 size・mtime の内容差
- current filter configuration が変わり、fresh index の `git add -A` なら blob が変わるが、real index の stat shortcut では再 clean されない場合
- probe 完了後から `HEAD^{tree}` 再利用までの並行変更
- 実際の skip-worktree、fsmonitor-valid state の正例。コードは tag を見るが、添付 positive test はその状態自体を構築していない

仮に D1298 が無くても、この 365 行は**そのままでは着地に値しません**。着地条件は、参照 slow path と fast predicate の同値性を偽緑方向で証明し、上記 stat/filter/race state を kill し、さらに D1299 の五条件を揃えた paired 測定で対象 loadgroup が実 wall の frontier を抜くことです。[rulings-verbatim.md:109-128](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/rulings-verbatim.md:109)

### 問い 6: 他の未着地材料

親が tracked 変更だけを見たなら、五 worktree の棚卸しとして不十分です。untracked、ignored、staged-only、stash、per-worktree reflog/index は別に確認すべきです。

各 worktree で最低限、次を行います。

```bash
git -C <WT> status --porcelain=v2 --untracked-files=all
git -C <WT> diff --binary HEAD --
git -C <WT> diff --binary --cached --
git -C <WT> ls-files --others --exclude-standard
git -C <WT> ls-files --others --ignored --exclude-standard
```

repo 全体では次を確認します。

```bash
git stash list --format='%gd %H %gs'
git stash show --stat --patch --include-untracked 'stash@{0}'
git reflog show --all --date=iso
git fsck --full --no-reflogs --unreachable --no-progress
```

今回の read-only 観測では stash は二つあり、件名はそれぞれ `"On worktree-dev-wave-t1563-acceptance-nproc"` と `"On worktree-dev-wave-t816-step4-impl"` でした。対象五 worktree名ではなく、stash ref は worktree 削除後も残りますが、payload の確認前に「無関係」と断定する必要はありません。

また、項目 1 と同じ patch は既に commit `aaffa71a6` として稼働中 branch `worktree-dev-wave-t2027-t2043-external-input` から到達可能です。これは main には未着地ですが、「t2027 child の未 commit bytes にしか存在しない」という状態ではありません。二重実装を避け、既存 commit を land する wave と調整すべきです。

### 問い 7: 撤去安全性

提示された三点だけでは、現時点の撤去証明として不十分です。

- branch tip が main の祖先でも、branch/worktree reflog の過去 commit、detached HEAD、index 内 gitlink commit、untracked bytes は覆いません。
- `deletion_loss_closure.complete=true` は、出力件数が上限内だったことを意味します。root inventory の完全性を意味しません。[check_branch_rescue.py:1250-1260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/tools/check_branch_rescue.py:1250)
- 保存 copy は既知 7 file の保険であり、未発見 untracked や `.git` 内の履歴を覆いません。

特に `root_snapshot.complete=false` は停止条件です。snapshot の complete は start/end snapshot の完全性と安定性の連言です。[check_branch_rescue.py:2014-2034](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/tools/check_branch_rescue.py:2014)

一方、`pack-index-unreadable` は `.idx` に対する `git verify-pack -v` が失敗または timeout し、pack 内 object から保存先を割り当てられなかったという意味です。[同:1343-1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/tools/check_branch_rescue.py:1343) これは retention map を不完全にし、rc=2 にします。[同:1972-1985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/tools/check_branch_rescue.py:1972)

ただし重要な点として、現行コードでは `pack-index-unreadable` 単独では `root_snapshot.complete=false` になりません。したがって親の実出力に両方があるなら、pack issue 以外の snapshot issue、または handoff 上の `root_snapshot` と `visualization_complete` の取り違えがあります。元 JSON を再確認すべきです。

撤去直前には、四 branch・四 worktreeを一操作で次のように再走し、rc=0、`root_snapshot.complete=true`、`stable=true`、closure complete/count 0 を確認します。全候補を一回で渡す義務は運用契約にも明記されています。[unreachable-object-ledger.md:63-85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2074-rescue-triage/docs/unreachable-object-ledger.md:63)

```bash
python3 tools/check_branch_rescue.py --ledger-check --timeout-seconds 900 \
  --branch impl-dev-wave-t2072-hold-author \
  --branch impl-dev-wave-t2073-rootfix-author \
  --branch impl-dev-wave-t2032-midflight-author \
  --branch worktree-dev-wave-t1434-acceptance-red-fix \
  --retire-worktree /work/1/SFC/tanab/izanagi/.codex/worktrees/t2072-hold-author \
  --retire-worktree /work/1/SFC/tanab/izanagi/.codex/worktrees/t2073-rootfix-author \
  --retire-worktree /work/1/SFC/tanab/izanagi/.codex/worktrees/t2032-midflight-author \
  --retire-worktree /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1434-acceptance-red-fix
```

D1030 は文言上「到達不能 commit」の二次保管裁定です。[rulings-verbatim.md:215-227](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/rulings-verbatim.md:215) closure が真にゼロなら直接の対象はありません。意図的に破棄すると裁いた uncommitted bytes に恒久二重保管までは不要ですが、「copy があるから安全」を根拠にする間は checksum と復元確認を済ませるべきです。

### 問い 8: 判定基準への疑義

七件への最終処遇は変わりませんが、基準だけでは取りこぼす型が一つあります。項目 4 の**基礎となる D1179 の未履行**です。

これは「まだ wave が壊れていない防御的堅牢化」ではなく、既にユーザーが `--help` と `NOTE:` への明記を命じた未完義務です。[rulings-verbatim.md:14-16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2074-rescue-triage/rulings-verbatim.md:14) 「壊れた wave の実例なし」だけで T-2032 自体を閉じるなら basis が壊れます。ただし保存差分の文面は誤っているため、**この差分を破棄しつつ、義務は別の正しい修理へ残す**のが妥当です。

「壊れたときの復旧費用が極端に高い」型として項目 7 の correctness false-green もありますが、これは保存理由ではなく破棄理由です。高速路が壊れた候補 tree を HEAD として検査すれば、研究上の不変条件を誤って緑にするからです。

撤去判断ではさらに基準を強くすべきです。未発見 untracked や root snapshot 不完全は、一度 worktree admin と reflog を消すと復旧費用が高いので、「既知 7 file の要否基準」と「撤去前の損失閉包基準」を混同してはいけません。

## 親の判定との不一致

1. **項目 1 の「受入集合」**

   - 私の判定: 実時間を含む集合は広がる。正しさ集合は広がらない。
   - 親の判定: 性質は変わらず、受入集合も変わらないという表現。
   - 決め手: timeout は 10〜120 秒の完了を新たに通す一方、assert は時間を見ていない。
   - 測るべきこと: full acceptance 下の当該 nested subprocess 所要。処遇は双方とも着地。

2. **撤去安全性の現在値**

   - 私の判定: `root_snapshot.complete=false` の時点では未証明。
   - 親の判定: 三点から損失なし。ただし handoff では再走予定。
   - 決め手: closure の `complete` と root inventory の `complete` は別契約。
   - 測るべきこと: timeout 900 の同一候補集合再走、元 JSON の snapshot issue 全件、五 worktree の untracked/ignored/staged。

3. **項目 7 の追加の破棄理由**

   - 私の判定: D1298 と既存 hold に加え、偽緑可能性だけでも着地不可。
   - 親の判定: 主に「別解済み」と単一 loadgroup 不採用。
   - 決め手: dirty candidate を HEAD tree へ潰す誤判定は正しさ gate を緩める。
   - 測るべきこと: land は不要。将来再提案するなら stat-cache、filter、race の adversarial oracle が必要。

4. **項目 6 の分類名**

   - 私は救出材料として「破棄・no-op」、親は「着地済み」。
   - main へ何も足さないという実処置は一致し、実質的な不一致ではありません。

## 未解決・親が測るべきこと

- `check_branch_rescue.py` の元 JSONで、`root_snapshot.complete=false` を作った snapshot issue を特定する。
- timeout 900 の再走が rc=0、snapshot complete/stable、closure count 0 になるまで撤去しない。
- 五 source worktree の untracked、ignored、staged-only を列挙する。
- `aaffa71a6` の既存 commit と本 wave の項目 1 実装を重複させない。
- T-2032/D1179 を閉じず、正しい肯定形の保証範囲と古い anchor 非保証を別の一手で実装する。
- 私は pytest・性能測定を実走していない。現在 tip の green 主張は、記録済み最終 baseline と byte 同一性に基づく。