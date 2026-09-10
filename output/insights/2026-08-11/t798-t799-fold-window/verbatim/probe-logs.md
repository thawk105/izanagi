# probe の出力 (逐語)

`authority: none` / `default_effect: no-state-change`。
log の原本は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/*.log`。

## 0. 制御群 — `probe_smoke.py` (fixture 上で land が正常完了する)

```
rc     = 0
status = landed
reason = main fast-forwarded to the tested wave tip and folded pending fragments
main_after = c836daa15409cc451d9922b070363ae489cc1c6e
--- main log ---
c836daa Fold landed documentation fragments
1122991 add fragment
b20db22 canonical ledgers
--- pending fragments ---
['README.md']
--- worklog tail ---
## 2026-08-11 (2) — fold probe

- probe 本文

### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し

- [T-001] (1)
--- FOLDED.md ---
# Fold receipts

- {"allocations":{},"authored":"2026-08-02","content_sha256":"5f2c51a614411fb46fb88483610a8e6a4fc7e5a261317bf8d3e78635d22022ca","seq":1,"wave":"wave-a"}
```

## 1. [T-798] — `probe_t798.py`

```
======== crash 前の main
HEAD        = f21f1ff871b8101587453ef39c88f56fb67bb6b1
status      = '?? .codex/'
state path  = /tmp/izanagi-land-test-bpyu871l/repo/.git/izanagi-spool-fold-state.json
state exists= False

======== land を別 process で走らせ、窓の内側で SIGKILL される
child returncode = -9 (-9 = SIGKILL)
child output     = ''
check_docs 到達  = True

======== crash 後の残骸 (= [T-798] が主張する状態)
main HEAD             = a8cd1ded50ec4b5a0943f8aaae9a25e19c78087c
main HEAD == wave tip = True
fold commit あり?     = a8cd1de add fragment
transaction state     = False (journal)
load_active_plan      = None
worklog に fold 反映?  = True
FOLDED.md に receipt?  = True
fragment GC 済み?      = ['README.md']
git status            =
M docs/spool/FOLDED.md
 D docs/spool/worklog/2026-08-02-wave-a-1.md
 M docs/worklog.md

======== 復旧経路 1: standalone spool_fold (引数なし = resume 用 CLI)
rc     = 0
output = {"gc_paths":[],"resumed_paths":[],"status":"noop","transaction_id":"","written_paths":[]}

======== 復旧経路 2: land を同じ request で再投入
child returncode = 20
child output     = LANDRESULT {"rc": 20, "status": "rejected", "reason": "main tracked/index/submodule dirt is forbidden", "main_before": null, "main_after": null, "wave_tip": "a8cd1ded50ec4b5a0943f8aaae9a25e19c78087c", "fold_commit_sha": null}

======== 復旧経路 3: 手で git restore してから land 再投入
restore 後 status = '?? .codex/'
child returncode = -9 (-9 なら再び窓へ入った)
child output     =
```

## 2. 窓の幅 — `probe_window_width.py` (実 repo、読み取りのみ)

HEAD `9abd23daa0dd885a9b1121bddd34b7c44c441428` (worklog rotation 前):

```
check_docs.py (窓の主項)                   rc=0  median=  2.694s  samples=[2.705, 2.694, 2.688]
check_ai_provenance --message-file     rc=0  median=  0.089s  samples=[0.092, 0.089, 0.088]
git add -- docs (dry-run 代替: status)   rc=0  median=  0.027s  samples=[0.027, 0.027, 0.027]
git diff --cached --name-only -z       rc=0  median=  0.012s  samples=[0.012, 0.012, 0.012]

窓の下限見積り (commit 自体を除く合計中央値) = 2.821s
```

HEAD `974207aea436776db85d83dca04bf36007dd2fcf` (worklog rotation 後):

```
check_docs.py (窓の主項)                   rc=0  median=  2.702s  samples=[2.814, 2.67, 2.702]
check_ai_provenance --message-file     rc=0  median=  0.090s  samples=[0.097, 0.089, 0.09]
git add -- docs (dry-run 代替: status)   rc=0  median=  0.027s  samples=[0.032, 0.027, 0.027]
git diff --cached --name-only -z       rc=0  median=  0.011s  samples=[0.011, 0.012, 0.011]

窓の下限見積り (commit 自体を除く合計中央値) = 2.831s
```

`git commit` 自体を含まないので、これは窓の**下限**である。

## 3. [T-799] — `probe_t799.py`

```
======== A. transaction state の所在は worktree ごとか、共有か
main worktree state = /tmp/izanagi-land-test-buo1rz4a/repo/.git/izanagi-spool-fold-state.json
wave worktree state = /tmp/izanagi-land-test-buo1rz4a/repo/.git/worktrees/one/izanagi-spool-fold-state.json
同一 path か           = False

======== B. 誤った HEAD 上での standalone resume
apply_fold の停止理由 = docs/spool/worklog/2026-08-02-wave-a-1.md: GC target content が transaction と不一致
state 残存            = True
tree 清浄             = ''
state が束縛する field  = ['fold_date', 'fragments', 'gc_paths', 'projected_worklog_bytes', 'rotation_path', 'targets', 'transaction_id', 'version']
state 中に HEAD/land 起源/base/tested tip の記述があるか = False
planned 時の HEAD     = 9fe836918395e62387f9b30a155eea6636cde473

======== B1. canonical を変えない commit で HEAD を進めてから resume
HEAD                 = bb98be2583d84955b30e9f2185a72609d0fe39b3 (planned 時と別)
docs は同一か         = base.txt
standalone rc        = 0
standalone output    = {"gc_paths":["docs/spool/worklog/2026-08-02-wave-a-1.md"],"resumed_paths":[],"status":"resumed","transaction_id":"c9e407e66fd2aad655e488ac99cfd0673cf00b84dc23fc58277a2ce3ba21ceec","written_paths":["docs/spool/FOLDED.md","docs/worklog.md"]}
worklog に fold 反映?  = True
fold commit あり?     = bb98be2 code-only commit (docs は 1 byte も変えない)
git status           = 'M docs/spool/FOLDED.md\n D docs/spool/worklog/2026-08-02-wave-a-1.md\n M docs/worklog.md'

======== B2. canonical を変える commit で HEAD を進めてから resume (対照)
standalone rc     = 2
standalone output = {"error":"docs/worklog.md: before/after 以外の第三状態","status":"transaction-error"}

======== B3. resume は _git_clean_preflight を通らない (staged 削除で対照)
state 無しの apply = 拒否: actual fold 対象に未追跡または dirty path がある
git status         = 'D  docs/worklog.md\n?? docs/worklog.md'
resume の standalone rc     = 0
resume の standalone output = {"gc_paths":["docs/spool/worklog/2026-08-02-wave-a-1.md"],"resumed_paths":[],"status":"resumed","transaction_id":"c9e407e66fd2aad655e488ac99cfd0673cf00b84dc23fc58277a2ce3ba21ceec","written_paths":["docs/spool/FOLDED.md","docs/worklog.md"]}
```

## 4. [T-799] C 節 — `probe_t799c.py` (land 経路)

```
state 作成前 status = '?? .codex/'
停止理由 = docs/spool/worklog/2026-08-02-wave-a-1.md: GC target content が transaction と不一致
state 作成後 status = '?? .codex/'
state 残存 = True
wave B status = ''

C1 land(wave B, main=main_head, tip=tip_b) → rc=27 LANDRESULT {"rc": 27, "status": "fold-recovery-failed", "reason": "active fold transaction requires main at the tested wave tip", "main_before": "b5718b170cf2496f2bd5a5c01c27140583a6654f", "main_after": "b5718b170cf2496f2bd5a5c01c27140583a6654f", "wave_tip": "81e99a063b52825d36e2277861edebee0e10709a", "fold_commit_sha": null}
C2 main==tip_b, status = '?? .codex/'
C2 land(wave B) → rc=0 LANDRESULT {"rc": 0, "status": "landed", "reason": "main fast-forwarded to the tested wave tip and folded pending fragments", "main_before": "81e99a063b52825d36e2277861edebee0e10709a", "main_after": "bb25ccd29e3b5567af8148824ec44d9b3ecb9e02", "wave_tip": "81e99a063b52825d36e2277861edebee0e10709a", "fold_commit_sha": "bb25ccd29e3b5567af8148824ec44d9b3ecb9e02"}
C2 main log = bb25ccd Fold landed documentation fragments
81e99a0 wave B commit
C2 worklog に fold 反映? = True
C2 state 残存 = False
```

**C2 の読み方:** plan は `b5718b1` (main_head) で計算され、land は `81e99a0` (wave B tip) の上で
resume して `bb25ccd` を fold commit として作った。畳まれた fragment 自体は main に pending だった
ものなので中身は正しい。**壊れているのは帰属である** — plan の計算基底は state にも
`FOLDED.md` の receipt にも残らない。

## 5. standalone resume の終端 — `probe_t799_after.py`

```
standalone resume rc = 0
standalone resume    = {"gc_paths":["docs/spool/worklog/2026-08-02-wave-a-1.md"],"resumed_paths":[],"status":"resumed",…}
git status           = 'M docs/spool/FOLDED.md\n D docs/spool/worklog/2026-08-02-wave-a-1.md\n M docs/worklog.md\n?? .codex/'
commit されたか       = 77d5901 fragment on main
その後の land rc     = 20
その後の land        = LANDRESULT {"rc": 20, "status": "rejected", "reason": "main tracked/index/submodule dirt is forbidden", …}
```

[T-798] の crash 残骸 (§1) と `git status` が 1 文字も違わない。

## 6. 選択肢 (b) の前提 — `probe_option_costs.py` / `probe_post_apply_resume.py`

```
== state 無しの validate_spool_tree (pending fragment 1 件)
issues = []

== state 有りの validate_spool_tree (= (b) で窓の間ずっと成立する状態)
issues = [('transaction-active', 'fold transaction が active — 引数なし CLI で resume が必要')]
```

```
1 回目 apply   = applied written: 2 removed: 1
state 残存      = False

== (b) の窓の形 (全 target=after / gc 削除済み / state 残存)
state 有り validate_spool_tree = [('transaction-active', 'fold transaction が active — 引数なし CLI で resume が必要')]
2 回目 apply   = resumed written: [] resumed: 2 removed: []
state 残存      = False
canonical は不変 = True
worklog 二重追記なし = True
```

**(b) の窓の形から `apply_fold` は無害に `resumed` を返す。**
一方 `validate_spool_tree` は state file の**存在だけ**で `transaction-active` を出すので、
(b) を素で入れると窓の先頭の `check_docs.py` が必ず赤になる。

**erratum:** 上の「canonical は不変」は初回、同じ `git status` を左右で 2 回呼んで比べる
**恒真な検査**だった (レンズ B の所見 3-B)。適用後の bytes を捕まえて比較する形へ直して
再走した出力が上である。結論は変わっていない。

## 7. 難しい plan での冪等性 — `probe_resume_hard_plan.py`

```
======== A. ローテーション無し + 挿入・追記あり
rotation_path = None
targets       = ['docs/failures.md', 'docs/phase3.md', 'docs/spool/FOLDED.md', 'docs/worklog.md']
1 回目 apply  = applied written: 4
2 回目 apply  = resumed written: [] resumed: 4
state 残存     = False
全 target が byte 単位で不変 = True
再発 payload の出現数        = 1
supersede 行の出現数         = 1
見送り追記の出現数           = 1
worklog エントリ見出しの数    = 2

======== B. ローテーション発火 + 挿入・追記あり
rotation_path = docs/archive/worklog-phase3-0801-1.md
targets       = ['docs/archive/README.md', 'docs/archive/worklog-phase3-0801-1.md',
                 'docs/failures.md', 'docs/phase3.md', 'docs/spool/FOLDED.md', 'docs/worklog.md']
1 回目 apply  = applied written: 6
2 回目 apply  = resumed written: [] resumed: 6
state 残存     = False
全 target が byte 単位で不変 = True
再発 payload の出現数        = 1
supersede 行の出現数         = 1
見送り追記の出現数           = 1
worklog エントリ見出しの数    = 1
archive の見出し数          = 1
```

## 8. 選択肢 (b) の残余窓 — `probe_option_b_wedge.py`

**敵対レンズ B の所見 1-B を裏取りするための追加測定。**

```
== 1 回目の land (正常)
rc=0 LANDRESULT {"rc": 0, "status": "landed", …, "fold_commit_sha": "c7bf2c80…"}
fold commit = c7bf2c80328d84c219d3fad4db2dbf28e5f41d70
その親      = 3a08cd5d741adaf93efb196e5050807a90f788b6 (== tested tip か: True )

== (b) が残す形を作る: commit 済みのまま state を残す
state 残存        = True
load_active_plan  = True
main HEAD         = c7bf2c80…
tested_tip        = 3a08cd5d…
locked_main == tested_tip か = False

== この状態から land を再投入する
rc=10 LANDRESULT {"rc": 10, "status": "stale-main",
  "reason": "main moved outside the tested audited closure while locking", …}

== 参考: standalone CLI はこの形をどう扱うか
rc     = 0
output = {"resumed_paths":["docs/spool/FOLDED.md","docs/worklog.md"],"status":"resumed","written_paths":[]}
state 残存 = False
git status = '?? .codex/'
```

## 9. 採番の入力は束縛されていない — `probe_plan_input_closure.py`

**敵対レンズ A の所見 5 を裏取りするための追加測定。[T-799] を「帰属」から「値」へ格上げする。**

```
planned allocations = [('wave-a/T:probe-new', '[T-052]')]
plan targets        = ['docs/spool/FOLDED.md', 'docs/worklog.md']
archive は target か  = False

archive へ [T-052] を追加して commit した (canonical target は 1 byte も変えていない)
archive 変更後の _max_task_number = 52 → 再計画なら [T-053]

== 残存 state から standalone resume する
rc     = 0
output = {"gc_paths":["docs/spool/worklog/2026-08-02-wave-a-1.md"],"resumed_paths":[],
          "status":"resumed","written_paths":["docs/spool/FOLDED.md","docs/worklog.md"]}

worklog へ入った番号   = ['[T-052]']
archive にある同じ番号 = True
同じ T 番号が 2 箇所に存在するか = True
```
