総合判定は **NO-GO** です。累積差分の棄却自体は正しい一方、段2案には仕様上の blocker が残っています。実装・pytest は行わず、静的検査と Git object の読取りだけを行いました。

## 1. 痕跡集合の十分性

**判定: real / blocker。2 path は lock 外 fold の十分条件ではありません。**

現行述語は実際に次の二つだけです。

- `[git_state.py:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:559)` — 「`status == "M"` かつ `docs/spool/FOLDED.md`」
- `[git_state.py:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:561)` — fragment の `D` または rename source

しかし fold は「canonical 3 台帳への追記」「必要なら archive と索引の更新」「fragment GC」「FOLDED receipt」を行います。[docs/spool/README.md:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/spool/README.md:81) の逐語は「`fold が行うこと`」、[同:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/spool/README.md:84) は「`canonical 3 台帳へ追記`」、[同:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/spool/README.md:90) は「`fragment を削除 (GC) し、FOLDED.md へ receipt を追記`」です。実装も canonical・phase・receipt・archive を独立 target にしています。[spool_fold.py:1858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/spool_fold.py:1858)

通常の「fold commit → 後続 commit で復元」は最初の commit で拒否されます。反例は、commit snapshot に署名を残さない次のクラスです。

| commit | `FOLDED.md` | fragment `f` | canonical / archive | 判定 |
|---|---|---|---|---|
| B | regular `R0` | regular・存在 | `L0` | 基準 |
| C1 | B と同じ | B と同じ | `L0→L1`、任意で archive A/M | 2署名なし、受理 |
| F | `M` | `D` | 正しい declared fold shape | declared fold として受理 |

C1 の作業中に lock 外 fold を実行し、その二 path だけ B へ戻してから commit すれば、Git history に残るのは台帳・archive 出力だけです。検証関数は操作の実行有無を tree から復元できません。

さらに commit-visible な多段反例もあります。

| commit | `FOLDED.md` | fragment `f` | 台帳 |
|---|---|---|---|
| C1 | regular→gitlink (`T`) | regular→gitlink (`T`) | `L0→L1` |
| C2 | gitlink→元 regular (`T`) | gitlink→元 regular (`T`) | `L1` のまま |
| F | 正規の `M` | 正規の `D` | declared fold |

`T` は `_landed_fold_output_path` のどちらにも該当しないため C1/C2 は通ります。最終状態では二 path が元に戻り、台帳だけが残ります。

初回/root も同型です。`--root` は A を列挙しますが、`A docs/spool/FOLDED.md` は明示的に許可されています。[test_dev_waves_git_state.py:484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:484) transient fragment を同じ commit 内で A→D にすれば fragment の履歴差分もありません。

したがって二条件は高い specificity を持つ heuristic ですが、fold の完全な署名ではありません。

## 2. 3 tree 免除の健全性

**判定: path bytes については限定的に refuted、fold provenance 全体については real。**

プランの逐語は次です。

- `[plan.md:190](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:190)` — 「`次をすべて満たす direct parent P`」
- `[plan.md:194](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:194)` — 「`key を出した各別 parent Q`」
- `[plan.md:203](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:203)` — `merge-base(Q,P) の path == Q の path`
- `[plan.md:204](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:204)` — `P の path == merge result C の path`

正しい trusted cutoff と通常の regular/absent path 状態を前提にすれば、対象 path の最終 bytes が P と異なる反例はありません。第二等式がその可能性を定義上排除します。

ただし証明できるのは bytes の一致であって、次は証明できません。

- merge actor が P の bytes を手動で再現したのか、実際に未変更継承したのか。
- canonical 台帳・phase・archive が同じ P の fold transaction に由来するか。
- FOLDED receipt と fragment GC が一つの coherent な main snapshot に由来するか。

具体的には、共通祖先 O から P が正規 main fold、Q が protected 2 path を O のまま保って canonical 台帳だけを変更した履歴を作れます。C が protected path を P、台帳を Q から採れば、

- `P == base_main_sha`
- `C[path] == P[path]`
- `merge-base(Q,P) == O`
- `Q[path] == O[path]`

をすべて満たします。しかし C の台帳は main fold 由来ではありません。現行テストは canonical・archive 変更を明示的に許しています。[test_dev_waves_git_state.py:457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:457)

octopus について、`各別 parent Q` は「その key を出した親」への全称には読めますが、**全 direct parent への全称ではありません**。A/T status の親、canonical/archive だけを持ち込む親、別 key の親は固定されません。また key ごとに別 P を選べるため、fold transaction 全体を一つの P に束縛していません。3 parent 以上を免除する仕様として不十分です。

## 3. 4 呼び出し経路の `base_main_sha`

**判定: 2 経路は条件付きで実在、checker / daemon の 2 経路は意味が誤っています。**

| 経路 | 値 | 判定 |
|---|---|---|
| land・declared fold | 提案どおりなら `tested_main` | 通常の再監査後 land では正しい |
| land・no-fold | 同じく `tested_main` | 通常経路では正しい |
| checker | receipt の初期 `base_main_sha` | 誤った cutoff |
| daemon recovery | manifest に固定した初期 `base_main_sha` | 誤った cutoff |

land は `tested_main..tested_tip` の exact closure を検査しています。[dev_wave_land.py:953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:953) の逐語は「`tested main is not an ancestor`」、[同:956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:956) で `rev-list --reverse tested_main..tested_tip` を作ります。通常試行では、この `tested_main` が必要な trusted cutoff です。

ただし active-fold recovery / already-landed では、main が tip に達していれば別の祖先を `tested_main` として再提出できます。`_main_is_allowed` は `[dev_wave_land.py:1117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1117)` の「`current == tested_main`」または current が audited closure 内なら通すため、stored fold transaction と元の cutoff の durable binding はありません。

checker は receipt を `spec.before_main_sha` に束縛します。[checker.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:408) の逐語は `ReceiptBinding(... spec.before_main_sha ...)` です。その値は wave 作成時の snapshot です。[daemon.py:1147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1147)

wave 中に main が B0→P と進み、P を wave へ merge した場合、

1. P は B0 の子なので、`P is ancestor of B0` を満たしません。
2. checker は receipt closure を B0..tip と照合します。[checker.py:489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:489)
3. その closure には P 側の正規 non-merge fold commit 自体も含まれます。merge 免除は適用不能なので、そこで `landed-fold-owned-path` になります。

したがって checker 経路では提案後も正規 main merge が拒否されます。

daemon recovery も receipt を `wave_manifest.base_main_sha` に束縛しています。[daemon.py:1500](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1500) 同じ不一致により `accepted_matches=False` となり、`AMBIGUOUS_RECOVERY` で停止します。[daemon.py:1539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1539)

プランの「schema/receipt format は変えない」は refuted です。[plan.md:290](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:290) 少なくとも初期 base と、最終受入に使った trusted/tested main cutoff を別 field として永続化・binding する必要があります。

## 4. `test_n31` の意図保存

**現行テストが逐語的に証明している内容:**

[test_dev_waves_git_state.py:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:374) は、

1. pending fragment を2件作る。
2. `tip` の後、`first_fold` が1件を削除し FOLDED を M。
3. `second_fold` が残りを削除し FOLDED を M。
4. HEAD / `landed_main_sha` / declared fold は `second_fold`。
5. `landed_commits=(tip, first_fold)`、`wave_tip=first_fold`。
6. `second_fold` の parent・message・shape が正しくても、先行 `first_fold` が landed 区間にあるため拒否する。

逐語は `[同:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:381)` の `fold_commit_sha=second_fold` と `[同:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:383)` の `landed_commits=(tip, first_fold)` です。

**提案された置換は同じ強さではありません。**

新案は first_fold の後に restore commit を追加します。[plan.md:306](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:306) しかし restore 自身も `M docs/spool/FOLDED.md` を出すため、拒否理由が first_fold なのか restore なのか分離できません。したがって `[plan.md:342](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:342)` の逐語「`hidden first_fold の per-commit 検出を消した場合だけ受理される`」は false です。

提案アルゴリズム自体は non-merge scan を残すので元の入力も拒否する予定ですが、テスト置換は次の回帰を許します。

- plain `first_fold(M+D) → declared_fold` は受理する。
- M-only、D-only、restore の M+A は拒否する。

既存 N31 を残し、net-zero restore は別テストとして純増させる必要があります。

## 5. fail-closed 性

| 入力 | 判定 |
|---|---|
| `landed_commits=()` | fail-closed。`landed-commits-empty`。[git_state.py:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:716) |
| base と tip が無関係 | helper 自身は exact closure / `base ancestor tip` を検査しない。caller 依存であり、active recovery では binding も弱い |
| root commit | `--root` は残るが FOLDED `A` は許可されるため、初回 fold-like output は捕捉不能 |
| 非 UTF-8 path | fail-closed。strict decode 後 `path-encoding`。[git_state.py:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:584) |
| gitlink / symlink typechange | fail-open。`T` は landed 署名述語に含まれない |
| merge-base 複数 | プランは `--all` + 複数なら免除なしとしており妥当。[plan.md:230](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:230) |
| merge-base 0 件 | Git の rc=1 を例外にすれば fail-closed だが、プランに明示 parser 契約・テストがない |
| 想定外 status | `_diff_entries` は任意の ASCII status を受理し、署名述語が無視する。[git_state.py:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:573) |
| `commit-parents` が空・壊れた出力 | プランは exact parse を規定していない。merge を root/single-parent と誤分類し、`-m` を外した `diff-tree` が空なら受理へ倒れ得る |

特に `commit-parents` は「1行、先頭 SHA が要求 commit と一致、残りがすべて full SHA、親数を正確に保存」を要求し、違反時は例外にする必要があります。tree equality も「diff が空」より `ls-tree` の mode/type/object/path を exact 比較する方が fail-closed です。

## 6. 検査順の相互作用

**well-formed input では概ね保存、malformed input と detail 到達性は変わります。**

プランは `[plan.md:259](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:259)` で「`landed_commits[-1] == tip までの detail 順序は維持`」、[同:263](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:263) で「`null-head 以降には手を入れない`」としています。

- `wave-tip`: scan より前のまま。
- `null-head` / `declared-head`: scan より後のまま。免除成功時に初めて到達するケースは増える。
- `parent`: declared fold の shape 後で不変。
- `added-path` / `path-status`: declared fold commit は1 parent 必須なので、`-m` 除去の論理影響はない。
- `null-pending-fragment`: scan 後のまま。正規 merge の false positive が消えれば、pending がある no-fold は本来の理由へ到達する。

ただし新しい `base_main_sha` validation を先頭に置けば、invalid base と empty/list mismatch が併存する入力では従来 detail より `ValueError` が先行します。また新設する parents/tree/merge-base Git 呼出しは `null-head` 等より前なので、malformed Git 出力では既存 detail が `git-error` に置き換わります。「受理集合不変」と「理由・到達性不変」は分けて記録すべきです。

## 7. 複雑さと代替

**判定: real。現プランは F82 型の再発面を増やしています。**

F82 の現行逐語は「`正規経路を 2 度禁止した`」です。[failures.md:1739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/failures.md:1739) また「`署名で書けば禁止集合は 2 条件で済み`」とあります。[同:1751](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/failures.md:1751)

ただし今回の merge false positive 自体が、「FOLDED M は fold actor 以外では起きない」という F82 の一般化を反証しています。さらに `T` と canonical-only history は感度不足を示します。3 tree 免除は worst-case で commit × parent × key × candidate の Git subprocess を増やし、共有30秒 deadline `[git_state.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:53)` の下で正規履歴を timeout 拒否しやすくします。

より単純で厳しい案は次です。

1. receipt に初期 base と別の `tested_main_sha` を追加し、land/checker/recovery で同じ値へ binding する。
2. merge 免除は2-parent mergeだけに限定する。octopus に署名があれば拒否する。
3. 二親 C について、trusted parent P は最終 `tested_main_sha` の祖先、Q はもう一方と一意化する。
4. 各対象 path を `ls-tree` の exact entry で `C==P`、`Q==merge-base(Q,P)` と比較する。T/gitlink/不正 mode は拒否する。
5. これとは別に `tested_main..wave_tip` の endpoint で canonical 3 台帳・phase・archive に残る fold output を検査する。二署名を戻して台帳だけ残す履歴をここで拒否する。

通常の O23 merge は2-parentなので正例を失わず、octopus・status parser・候補 P の組合せを削減できます。

完全な「lock 内で実行された」という因果まで必要なら、tree equality では証明不能です。land lock 内で作った transaction ID と全 target の before/after hash を receipt に永続化し、それを declared fold commit と照合する必要があります。

## 親 brief の独立検証

### 累積差分の棄却

**判定: 棄却理由は real。親 P1 は refuted。**

brief は `[brief.md:47](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/brief.md:47)` で `<landed_main>..<wave_tip>` を提案しています。しかし fold 経路の実値は `landed_main_sha=fold_commit`、`wave_tip=tested_tip` です。[dev_wave_land.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1513) これは landed 区間でなく「post-fold child とその parent」の endpoint 比較です。

正しく `base_main..wave_tip` にしても、fold→restore で endpoint 差分は消えます。brief の `[brief.md:50](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/brief.md:50)` の逐語「`範囲内で現れて消える変更は land しない点で無意味`」は誤りです。ff-only は commit 列自体を main history に残し、本仕様はその履歴中の lock 外 fold を禁じています。

### 履歴実測

4主張はすべて再現しました。

```text
git diff-tree --root -r -m --no-commit-id --name-status --no-renames 6af21d7 -- docs/spool/FOLDED.md
A  docs/spool/FOLDED.md

git diff-tree --root -r -m --no-commit-id --name-status --no-renames ee28642 -- docs/spool/FOLDED.md
M  docs/spool/FOLDED.md
```

`ee28642` は wave parent `914c317...` との差分が M、main parent `ea6ca43...` との差分は空、`--cc` も空でした。

`git log -S '"diff-tree", "--root", "-r", "-m"' -- tools/dev_waves/git_state.py` は導入 commit `2743e0de...` だけを返しました。`27f693f4...` の patch は逐語で

```python
-    if "docs/spool/FOLDED.md" in paths:
+    if status == "M" and paths[0] == "docs/spool/FOLDED.md":
```

でした。brief の履歴観測は real です。

### 「正規手段が他にない」

**結論は real、根拠文の一部は refuted。**

`DW-S09` は `dev_wave_land.py` を「`local main を変更する唯一の通常 land 経路`」としています。[core.md:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/dev-wave/core.md:106) stale/busy 後の唯一の指定回復も「`固定SHAのwave-side merge`」です。[operations.md:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/dev-wave/operations.md:134) したがって現在の sanctioned workflow に代替はありません。

ただし brief `[brief.md:19](/work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/brief.md:19)` の「`rebase / cherry-pick は DW-STOP が禁じる`」は逐語的には誤りです。DW-STOP が列挙するのは rebase / force / 未監査差分で、cherry-pick は書かれていません。[core.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/dev-wave/core.md:22) cherry-pick は通常経路として承認されていない、という結論に留めるべきです。

## 裁定パッケージ候補

- receipt schema に最終 `tested_main_sha` を追加し、active fold transaction にも binding する変更。
- canonical/archive を persistent fold trace に含めるか、過渡期の legacy direct-ledger wave をいつまで許すか。
- lock 所有を tree から推定せず、transaction ID・target hashes の durable receipt で証明する変更。
- F82 の回数記録の整合。現行本文は「2度」、`27f693f` の commit body は「4度目」と記録しており、ユーザー前提の「3度」とも一致しません。

## 総括

- **NO-GO:** M-FOLDED / D-fragment の2署名は十分でなく、canonical-only・T/gitlink・同一commit内復元を受理する。
- **NO-GO:** checker / daemon の `base_main_sha` は wave 初期 main であり、正規 merge 後の tested main cutoff ではない。schema 変更なしでは直らない。
- **NO-GO:** 3 tree は個別 path の bytes 一致しか証明せず、fold transaction 全体の main/lock provenance を証明しない。
- 累積差分案の棄却と4件の履歴実測は正しい。
- `test_n31` は置換せず、現行例を残して net-zero 例を純増すべきである。