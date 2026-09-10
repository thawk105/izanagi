## 9 本の verdict 予測

前提は段4時点の `main=a068b7f5`、ref不変、既定60秒以内の完走です。checker自体は実走せず、コードとGit objectを静的に照合しました。

| branch | 実装の予測 verdict | 主なコード経路 | 親との評価 |
|---|---|---|---|
| `t1484-backup-before-trailer-fix` | `indeterminate` / `one-or-more-states-unproven` | 全parent edgeから170 path、171 unitを生成。60 unitが候補65件を得た時点で、候補内を調べず `truncated` になる。[tool:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:478) [tool:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:485) | 親の `landed` が正しい。少なくとも59/60の打ち切りstateはmain到達可能なmerge parent上にexact stateがある。実装の探索順序が誤り。 |
| `worktree-agent-ab4539bed30390c7f` | `indeterminate` / `one-or-more-states-unproven` | receiptはexactだが、`.claude/commands/rulings.md` の履歴が64件超のため、exact stateを調べる前に打ち切る。 | 親の `landed` が正しい。必要stateは新しい方から33番目にあるが、実装は65件あることだけで打ち切る。 |
| `worktree-cleanup-branches-20260825` | `indeterminate` / `one-or-more-states-unproven` | 2 fragmentともreceipt不在。ledger hitが0でもA3により必ず `indeterminate`。[tool:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:668) | 意味上の正解は親の `not-landed`。ただしA3/A5の判定規則上は実装の `indeterminate` が正しい。 |
| `worktree-roadmap-workload-hint` | `indeterminate` / `one-or-more-states-unproven` | `docs/roadmap.md` はexact tip。re-homeされた2 fragmentは元shaのreceiptがなく、ledger hitはverdictを動かさない。[tool:734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:734) | 親の意味上の `landed` は正しいが、受理済みA3では意図的に非決定。 |
| `worktree-rulings-20260818-floor-measurement` | `indeterminate` / `one-or-more-states-unproven` | 1 fragmentはexact receipt、archiveへ着地したもう1本はreceipt miss。[tool:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:671) | 親の意味上の `landed` は正しいが、A3では実装の非決定も正しい。 |
| `worktree-rulings-20260818-second` | `landed` / `all-introduced-states-proven` | 唯一のproof unitがexact receiptで `landed`、全unit連言が成立。[tool:882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:882) | 親と一致。ただし60秒を超えると `indeterminate` へ変わる。 |
| `worktree-t1458-side-ccbench-provenance-fix` | `indeterminate` / `one-or-more-states-unproven` | 12 unitが候補上限で打ち切り。さらにmergeが削除した2 spool fragmentを、旧blobのreceiptを見ず無条件に `spool-deletion-not-proven` とする。[tool:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:748) | 親の `landed` が正しい。12 stateはmain到達可能なparent上にあり、削除された2 fragmentも旧blob shaのexact receiptが存在する。 |
| `worktree-workload-policy-hint-impl-unitB` | `indeterminate` / `one-or-more-states-unproven` | 全parent edgeで27 path、37 unit。re-home元2 fragmentが重複して6 receipt miss、さらに16 unitが履歴候補上限で打ち切り。 | A2/B3の厳密なchecker結果としては実装が正しい。親の機能着地判断は妥当でも、照合不能1 fileを含むためD720条件1の確定 `landed` とはいえない。 |
| `worktree-workload-policy-hint-impl-unitC` | `indeterminate` / `one-or-more-states-unproven` | unitBと同一commitなので同じ37 unit、同じ分岐。 | unitBと同じ。 |

したがって完走時でも、出力は **`landed` 1本、`indeterminate` 8本、`not-landed` 0本**です。タイムアウトすれば唯一の `landed` も消えます。

## 履歴候補を調べる前に打ち切っている

**深刻度**: blocker

**成立条件**: main tipでは不一致だが、対象pathの履歴commitが65件以上あり、その最初の64件内にexact stateが存在する場合。実データの `.claude/commands/rulings.md` は128件あり、必要stateは33番目にあります。

**file:line**: 候補取得は [tools/check_branch_landed.py:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:478)、件数だけでの打ち切りは [tools/check_branch_landed.py:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:485)、実際の照合ループはその後の [tools/check_branch_landed.py:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:490)。

**成果物影響**: 判定表で少なくとも `t1484` と `worktree-agent-ab4539bed30390c7f` が、正しい `landed` から `indeterminate` へ変わります。

**提案**: 取得した上限内候補を先に照合し、matchが無く65件目が存在するときだけ `truncated` にする。よりよい方法は、positive proofを `--find-object=<oid>` で狙って候補化し、`ls-tree` でmode/pathを確認することです。履歴総数が上限超過でもpositive matchは受理できます。履歴65件超かつ33件目で一致する回帰テストを追加してください。現テストは不一致時の打ち切りしか確認していません。[test:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_check_branch_landed.py:425)

## spool削除が既存receiptで証明されない

**深刻度**: blocker

**成立条件**: merge commitが `docs/spool/{worklog,decisions,failures}/` のfragmentを削除し、その旧blobのexact receiptがFOLDEDにある場合。`t1458` の旧blob sha `bfe9a104...` と `5db5feb9...` は両方receipt済みです。

**file:line**: 追加fragmentだけをhash化する [tools/check_branch_landed.py:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:727)、削除を常に非決定にする [tools/check_branch_landed.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:748)。

**成果物影響**: `worktree-t1458-side-ccbench-provenance-fix` が `landed` にならず、削除候補一覧から欠落します。

**提案**: spool deletionでは `state.old` のblobをhash化し、そのexact receiptがあれば削除stateを `landed` と証明する。receipt不在ならA3どおり `indeterminate` に保ちます。追加receiptのテストだけでなく、receipt済みfragment削除のpositive testを追加してください。

## 唯一の未着地branchはA3どおり非決定になる

**深刻度**: must-fix

**成立条件**: fragmentのreceiptがなく、ledger/archiveの構造単位hitも0である場合。cleanup branchの2本が該当します。

**file:line**: receipt missの固定判定は [tools/check_branch_landed.py:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:668)、ledger probeをverdictへ使わない箇所は [tools/check_branch_landed.py:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:736)、`not-landed` が可能なのは非spool純追加だけです。[tools/check_branch_landed.py:687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:687)

**成果物影響**: 判定表の `not-landed` は0件となり、未fold回収一覧をdecisionだけから生成できません。ただし2 fragmentのpath自体は `proof_units[].path` とledger probeに出るので、文字どおり「名指しできない」のではなく「未foldと断定できない」状態です。

**提案**: 当面はverdictを変えず、`unresolved_fragment_candidates` を追加し、path、whole-file sha、canonical body sha、receipt有無、matched unit数、unit総数、hit先を一意path単位で出す。決定的な識別力には、re-home前後のshaとidentityを残すdurable receipt/provenanceか、frontmatterを正規化した完全比較器が必要です。単なるledger hit 0だけを `not-landed` にするのはA3/A5違反です。

安全な削除判定器として `indeterminate` は許容できます。しかし「何を回収すべきかも示す」目的には、現在のJSONでは不足します。

## 既定60秒以内の完走は静的には保証できない

**深刻度**: blocker

**成立条件**: 9本はいずれもspool stateを持つため、receiptが全件一致していても750 fileのledger corpusを毎回構築します。各blobに `cat-file -s` と `cat-file blob` を別processで実行するため、少なくとも約1,500 Git child/branchです。その後、merge-heavy branchでは多数のpath履歴queryが続きます。

**file:line**: 60秒の全体deadlineと5秒のcommand上限は [tools/check_branch_landed.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:137)、blobごとの2 commandは [tools/check_branch_landed.py:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:523)、全corpus読込は [tools/check_branch_landed.py:605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:605)、無条件に近いcorpus生成条件は [tools/check_branch_landed.py:954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:954)。

**成果物影響**: 60秒超過時は9本すべて `indeterminate` になり、唯一のpositiveである `rulings-20260818-second` も削除候補一覧から消えます。

**提案**: corpusは最初のreceipt missまたはtask ID検索時にlazy構築し、`git cat-file --batch` で一括読込する。exact-state検索とtip entryをpath/state単位でcacheし、同一merge stateをdeduplicateする。total、corpus build、ledger probe、task scanの件数・bytes・elapsedをJSONへ追加してください。

また、ledger probeとtask scanのPythonループにはdeadline確認がありません。[tool:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:616) [tool:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:833) したがって `--timeout-seconds=60` は厳密なwall-clock上限でもありません。

## 20,000 commit上限がpositive proofまで一律停止する

**深刻度**: must-fix

**成立条件**: mainのcommit数が20,000を超えた場合。段4の `a068b7f5` は6,245なので現在は未発火ですが、repo成長で必ず到達します。

**file:line**: 全main履歴の列挙と上限判定は [tools/check_branch_landed.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:451)、closure内容を調べる前の必須ゲート化は [tools/check_branch_landed.py:945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:945)。

**成果物影響**: 上限到達後はclosure空branchやmain tip exact branchまで全て `indeterminate` となり、判定表全体が使用不能になります。

**提案**: 完全履歴の要求はclosed-world negative proofにだけ適用する。closure空、tip exact、exact receipt、履歴内positive matchには全履歴完走は不要です。`history_scan` を全branchの事前ゲートから外し、negative unitにscopeした完全性証明へ変更してください。

## JSONがfileとproof unitを混同し、削除判断のguardも不足する

**深刻度**: must-fix

**成立条件**: mergeが同一pathを複数parent edgeで導入する場合、または人が `decision.landed=true` を削除可と読む場合。

**file:line**: `files` にproof unitsをそのまま複製する箇所は [tools/check_branch_landed.py:973](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:973)、summaryはunit verdictを数える [tools/check_branch_landed.py:1010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:1010)、authorization guardは `land_authorized` だけです。[tools/check_branch_landed.py:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:250)

**成果物影響**: `t1484` は親の非spool 12 fileに対してJSONが170 `changed_files`、171 `files`を出し、unitB/Cは27 path、37 `files`を出します。削除候補一覧や台帳がproof edge数をfile数として過大計上し得ます。

**提案**: `files` はunique pathごとにgroup化し、edge provenanceを別配列へ置く。`changed_files` は `introduced_paths_across_parent_edges` へ改名し、tip net path数も別fieldにする。加えて `branch_delete_authorized:false`、`manual_review_required`、`unproven_paths`、`negative_paths`、`receipt_missing_paths` を出してください。`condition2:not-checked` と `land_authorized:false` は正しく実装されていますが、削除可否のguardではありません。

`ledger_probe.outcome` も、1 unitでもhitすれば `matched` になります。[tool:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:636) 親実測の「3 unit中2 hit」と全一致を区別する `matched_unit_count`、`unit_count`、`all_units_matched` が必要です。

## outcome語彙は出るが、重要なerrorがnot-matchedへ潰れる

**深刻度**: must-fix

**成立条件**: spool blobのhash計算がsize上限やcat-file errorで失敗する、archive blobが非UTF-8、またはphase途中でglobal exceptionになる場合。

**file:line**: `not-run` 初期値は [tools/check_branch_landed.py:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:218)、`not-applicable` は [tools/check_branch_landed.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:708)、局所的な `error` / `truncated` は [tools/check_branch_landed.py:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:618) で実際に出ます。一方、hash計算例外を捕捉した後もreceipt evidence outcomeをreceipt parserだけから算出するため [tools/check_branch_landed.py:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:727)、`error` / `truncated` が `not-matched` になります。[tools/check_branch_landed.py:741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:741)

非UTF-8 archiveは黙ってcorpusから除外されるため [tools/check_branch_landed.py:607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:607)、probeやtask indexが不完全なcorpusを完全探索したように `not-matched` と報告できます。global exceptionでも担当layerは初期値 `not-run` のままです。[tools/check_branch_landed.py:1021](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/check_branch_landed.py:1021)

**成果物影響**: 台帳観測で「読めなかった」「打ち切った」が「照合したが無かった」または単なる `not-run` に変わり、fragment回収判断を誤らせます。

**提案**: hash例外の `exc.outcome` をreceipt evidenceへそのまま伝播する。corpusに `files_enumerated`、`files_read`、`bytes_read`、`skipped`、`errors`、`complete` を持たせ、不完全ならprobe/task全体を `error` または `truncated` にする。global catchでは実行中phaseを対応するoutcomeへ更新してください。現在のschema testはoutcomeが許可集合内かしか見ていません。[test:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_check_branch_landed.py:646)

## 総括

blocker:

- 履歴候補を照合する前に件数だけで打ち切り、既知のexact stateを見落とす。
- receipt済みspool deletionを旧blobから証明せず、`t1458` を誤って非決定にする。
- 750-file corpusを毎branch約1,500 Git childで無条件構築し、既定60秒の実repo完走が未証明。

must-fix:

- A3を維持したまま、cleanupの2 fragmentを非決定の回収候補として明示する。
- 20,000 commit全体上限をpositive proofの事前ゲートから外す。
- file、path、parent-edge proof unitをJSONで分離し、削除非許可を明示する。
- partial ledger hit、corpus完全性、phase別error/truncated、総所要時間を正確に出す。

**結論: 現状のまま統合してはいけません。** 安全側の偽陰性だけであり誤削除は起こしにくいものの、実データでは1本しか `landed` を返せず、唯一の真の未着地も `not-landed` にできません。さらにその1本も時間予算次第で失われます。

親が実repoで必ず実測すべき点:

1. 9本を既定60秒で個別実走し、exit code、verdict、reason、branch/main tip、`refs_stable`、wall timeを保存する。
2. `rulings-20260818-second`、merge-heavyな`t1484`、ledger missのcleanupについて、cold/warm cache双方のtotal timeを測る。
3. corpus buildのfile数、総bytes、Git child数、所要時間と、ledger probe・task scanのunit数および所要時間を別々に測る。
4. `--timeout-seconds 300` でも走らせ、60秒timeoutと論理的 `indeterminate` を分離する。
5. 修正後の期待値を、`t1484`・agent・`t1458`・secondは `landed`、cleanup・roadmap・floor・unitB/Cは受理済みscope上 `indeterminate` として再確認する。cleanupを `not-landed` にするなら、先にcanonicalなclosed-world負証拠を設計する。