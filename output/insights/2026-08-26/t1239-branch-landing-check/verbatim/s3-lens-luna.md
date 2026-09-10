結論として、このプランはそのまま実装してはいけない。追加実測で判定規則の反例が確定しているほか、`/cleanup-branches` への配線と S5 の安全条件が欠けている。

### receipt 不在は未着地の証拠にならない

**深刻度**: blocker

**成立条件**: fragment が別 wave 名へ re-home されて whole-file SHA-256 が変わった場合、または fold 後の本文が `docs/archive/` や `docs/phase3.md` へ移った場合。

**成果物影響**: `not-in-FOLDED` 5 本を未着地と誤認し、実際の未着地 2 本ではなく 5 本を S4 対象へ載せ、D568 などを二重 fold しうる。

**提案**: receipt hit は十分条件としてよいが、receipt miss は `not-landed` ではなく本文照合へフォールバックさせる。`docs/worklog.md`、`docs/decisions.md`、`docs/failures.md`、`docs/phase3.md`、`docs/archive/` を対象に、frontmatter を除いた fragment の構造化単位と、placeholder 採番や fold 日付を反映した canonical 表現を照合する。部分一致は `indeterminate`、全構造一致は `landed`、完全な探索で有意な単位が全て不在の場合だけ `not-landed` とする。`spool_fold._receipt_records()` を複製せず、公開 read-only parser へ切り出して共用すること。D568 re-home、archive 2 例、2/3 部分一致、真に未着地の cleanup 2 本を必須テストへ加える。

### 判定器が cleanup 経路へ配線されていない

**深刻度**: blocker

**成立条件**: ahead>0 だが内容は main へ着地済みの branch を `/cleanup-branches` で処理する場合。

**成果物影響**: 判定表が `landed` でも §2 の `ahead=0 のみ`で削除候補から落ち、`git branch -d` も非祖先 branch を拒否するため、成果物が運用を一切変えない。

**提案**: **裁定パッケージ候補**として、`.claude/commands/cleanup-branches.md` §1 に ahead>0 branch ごとの checker 呼出しを追加し、§2 を「ahead=0、または固定 tip/main に対する checker=`landed`」へ拡張する。ただし非祖先 branch の削除には `-D` ではなく、ユーザーの対象別指示、直前再検査、worktree detach、`git update-ref -d refs/heads/<name> <expected-tip>` の CAS を組み合わせる案を裁定へ返す。同時に `.agents/skills/cleanup-branches/SKILL.md`、`tools/check_docs.py` の whole-file hash、対応する `test_check_docs.py` を更新対象として明記する。

### `not-landed` が D720 の land 許可に見える

**深刻度**: blocker

**成立条件**: checker が条件 1 を `not-landed` と判定し、その結果から S4 や回収 land へ進む場合。

**成果物影響**: D720 条件 2を未検査のまま古い fragment や実装を canonical 台帳または main へ入れうる。

**提案**: JSON に `assessment_scope: "D720-condition-1-only"`、`condition2.status: "not-checked"`、`land_authorized: false` を必須表示する。運用は `landed`→削除候補、`indeterminate`→保持・人手照合、`not-landed`→条件 2 の独立監査後に新しい回収 waveへ移す、と明記する。条件 2 の機械化は scope 外でよいが、手動 gate と通常の `dev_wave_land.py` へ戻す経路は本 wave の成果物に必要である。

### P4 は対象数・所有権・commit 保全の三点で成立していない

**深刻度**: blocker

**成立条件**: occupancy が `unoccupied` という理由だけで `.codex/worktrees/` の child を撤去する場合。

**成果物影響**: S5 の撤去件数が誤り、foreign/locked worktree を消すか、detached HEAD の唯一の到達根を失って commit を到達不能にする。

**提案**: P4 は現状では却下する。親の列挙は `.codex` 14 本で、その内訳は detached 11 本と branch 付き 3 本であり、「detached 15 本」と一致しない。現在の read-only 再観測でも worktree は 42 本から46 本、`.codex` は15 本へ増えた一方、detached `.codex` は11 本のままで、main も `c83b5b2c` から `a068b7f5` へ進んでいる。各 detached HEAD について永続 ref からの到達性と内容着地を検査できる SHA 入力の共通判定関数を用意し、foreign ownership、lock、直近性、occupancy、到達性のいずれかが不明なら保持する。所有権の無い worktree を撤去する例外は **裁定パッケージ候補**とする。branch と直近状態を持つ `.claude` 2 本を残す判断自体は妥当である。

### P3 は「単独非決定」なら正しいが、完全な補助化は強すぎる

**深刻度**: must-fix

**成立条件**: task が別 branch/wave から land された場合、または re-home receipt・archive 記録を task ID から発見できる場合。

**成果物影響**: task index に正しい着地経路があっても verdict が変わらず、D568 型や rebuild branch 型が `not-landed` または `indeterminate` に残る。

**提案**: task ID hit 単独で verdict を決めないという P3 の狭い原則は維持する。一方、task hit を候補 commit、別 wave 名、allocation、archive artifact の探索起点として使い、その先で blobまたは構造化本文が一致した場合は content evidence として verdict に反映する。task ID 不在は負の証拠にしない。検索対象には `docs/failures.md` と `docs/phase3.md` も含め、`branch-name task ID` と `commit-subject task ID` を混同しない field に分ける。

### P1 と branch 単位の P2 は正しいが、file 状態の合成が未定義

**深刻度**: must-fix

**成立条件**: 同じ file で内容と mode が同時に変わり、main には内容だけ、または mode だけが存在する場合。

**成果物影響**: file の一部分だけが着地した branch を `landed` とし、削除候補一覧へ偽陽性を載せる。

**提案**: P1 の3値と、P2 の branch 単位連言は採用してよい。file 内では変更次元を連言にし、regular file も content、mode、object type の全要求を証明する。別々の main commit で blob と mode が個別に現れただけでは十分とせず、同一 tree state での一致か、各次元が独立に着地したことを明示的に証明する。originless baseline は予定どおり `indeterminate` に残し、「生成物らしい」という一般除外は設けない。unitB/C を機械的に `landed` にしたいなら、対象構造を限定した semantic comparator を別の **裁定パッケージ候補**とする。

### 同 path の探索完了は closed-world にならない

**深刻度**: must-fix

**成立条件**: regular file が rename、分割、別 path への移植、または別 branch からの再実装で着地した場合。

**成果物影響**: `main` の同 path が不変というだけで純追加を `not-landed` にし、回収対象と台帳件数を過大にする。

**提案**: 同 path の exact blob miss は負の証拠ではなく、少なくとも task-linked artifact、rename先、main tree内の exact blob、追加 payload の探索へ落とす。それでも移植を排除できなければ `indeterminate` とする。D720 の「path 一致は証拠にならない」と対称に、path 不一致も単独の未着地証拠にしない。

### 個別 ref の再取得だけでは全量判定表を固定できない

**深刻度**: must-fix

**成立条件**: 20 branch を順番に検査している間に main、branch集合、worktree登録のいずれかが変化する場合。

**成果物影響**: 判定表の各行が異なる世界を参照し、新設 branch の欠落、重複 tip の見落とし、既に worktree が付いた branch の削除候補化が起きる。

**提案**: S3/S6 は開始時と終了時に local ref名とtip、main tip、`git worktree list --porcelain` を取得し、集合と SHA が一致したときだけ全量表を確定する。不一致なら表全体を stale として再実行または未確定報告にする。削除直前にも checker、occupancy、worktree attachmentを再検査し、expected tip による CAS を使う。unitB/C の同一 tip は `duplicate_tip_group` として一覧上で束ねる。

### JSON は未検査と問題なしを十分に区別できない

**深刻度**: must-fix

**成立条件**: global timeout、diff parse失敗、max-files超過、早期 positive、task ID不在、履歴打切りのいずれかが起きる場合。

**成果物影響**: `changed_files: 0`、空の evidence、`status: complete` が「検査済みで問題なし」と誤読され、判定表と削除候補一覧の信頼度が過大になる。

**提案**: 各層へ `matched`、`not-matched`、`not-applicable`、`not-run`、`error`、`truncated` を分離して必ず出す。`changed_files` 自体を確定できない場合は `null` とし、`files_enumerated:false` を出す。探索した main 範囲、path集合、調査件数、上限、打切り理由も記録する。ref移動や全体列挙失敗のような global integrity failure は、file に確定的 `not-landed` があっても branch verdict を強制的に `indeterminate` にする。

### 削除候補一覧の契約が不足している

**深刻度**: must-fix

**成立条件**: checker の JSON を人間が直接読み、branch削除を裁定する場合。

**成果物影響**: 内容判定だけが載り、worktree、所有者、lock、recent、ahead/behind、重複ref、再検査要否が欠けたまま削除判断される。

**提案**: S6 の表には最低限、branch名、固定tip、main tip、ahead/behind、条件1 verdict、条件2=`not-checked`、決定的証拠、補助観測、同一tip branch、worktree path、lock、dirty、occupancy、recent、ref安定性、推奨処置を載せる。`patch_id` と `task_index` は `auxiliary_evidence` より `observations` と呼ぶ方が verdict と誤読されにくい。

### 既存ツールの答えは用途別であり、相互保証にはならない

**深刻度**: must-fix

**成立条件**: cleanup で `audit_dangling_commits.py` の rc0を、対象 branch の削除安全性として扱う場合。

**成果物影響**: 既存 file の固有変更を持つ branchでも audit は rc0、新 checker は `not-landed` となり、どちらを信じるか不明な一覧になる。

**提案**: 対象 branch の削除判断では新 checker が正であると明記する。audit は「既に到達不能な新規 path の全体監査」であり、対象 branch がまだ ref で生きている間はその削除リスクを証明しない。`dev_wave_land.py` の `verify_declared_fold_commit()` も land/fold commit の形状検査であり、歴史的な内容着地判定には再利用しない。一方、Git hardening、branch tip解決、FOLDED schema parser は共通公開 helperへ寄せ、独自再実装による drift を避ける。

## 総括

blocker:

- receipt missを `not-landed` とする規則が追加実測に反している。

- `/cleanup-branches` の呼出しと非祖先 branch の安全な削除経路が無い。

- D720 条件2を未検査のまま回収 landへ進める形になっている。

- P4 の件数、ownership、detached HEAD保全が成立していない。

must-fix:

- P3を task-linked artifact探索へ使うこと。

- content、mode、typeをfile内で連言すること。

- path限定の負証拠を弱めること。

- 全量ref/worktree snapshotと直前再検査を設けること。

- 未検査、非該当、打切り、問題なしをJSONで分離すること。

- S6の人間向け削除判断fieldを定義すること。

- dangling audit、land helper、新checkerの責務を明記し、共通parserだけを再利用すること。

このままの実装開始には反対する。少なくとも receipt fallback、D720条件2の表示と運用gate、全量snapshot、P4の再設計をプランへ反映してから author 段へ進むべきである。

scope 外として親がユーザーへ返すべき **裁定パッケージ候補**:

- `/cleanup-branches` を内容着地済み ahead>0 branchへ拡張し、expected-tip CAS削除を許すか。

- foreign/locked `.codex` worktreeを、どのownership証拠と救出ref条件で撤去可能にするか。

- originless baseline型を今後も `indeterminate` とするか、限定semantic comparatorを新設するか。

- D720条件2の機械化を別waveで行うか。少なくとも本 waveでは手動監査必須を維持する。

pytestは依頼どおり実行しておらず、上記は指定資料、repo内正本、現在のread-only Git状態による静的所見である。