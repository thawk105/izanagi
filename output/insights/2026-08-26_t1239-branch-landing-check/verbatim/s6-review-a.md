## 不正な receipt が `landed` を作る

**深刻度**: blocker

**成立条件**: branch に spool fragment を追加し、main の `FOLDED.md` に同じ SHA-256 を持つ `- {"content_sha256":"..."}` のような不完全な JSON bullet を置く。正式な receipt でなくても `landed` になる。現テスト自身が `wave` と `content_sha256` しかない不正な receipt を作り、fragment の `wave: topic` と receipt の `wave: test` が矛盾したまま `landed` を期待している。

**file:line**: `tools/check_branch_landed.py:539-563`, `tools/check_branch_landed.py:668-674`, `tools/check_branch_landed.py:727-747`; `orchestrator/tests/test_check_branch_landed.py:132-135`, `orchestrator/tests/test_check_branch_landed.py:180-196`; 正式 schema は `tools/spool_fold.py:76-82`, `tools/spool_fold.py:1692-1735`

**成果物影響**: fold されていない fragment が判定表と削除候補一覧で `landed` になり、台帳へ未反映の内容を失う。

**提案**: legacy/v2 の完全な field 集合、型、`authored`、`wave`、`seq`、重複 key を正式 parser と同じ規則で検証する。不正な bullet が一つでもあれば `indeterminate`。正のテストも正式 receipt に置き換え、identity 不一致と不足 field を負の対照にする。

## canonical でない履歴を書き換える経路が未検出

**深刻度**: blocker

**成立条件**: main と topic を分岐させ、`.git/info/grafts` で main tip の親を topic tip に見せる。canonical tree に topic の内容がなくても closure が空になり、`branch-closure-empty` で `landed` になる。同様に `GIT_REPLACE_REF_BASE` で標準外 namespace の replace ref を使うと、標準の `refs/replace/` 検査を迂回できる。

**file:line**: `tools/check_branch_landed.py:155-160`, `tools/check_branch_landed.py:320-329`, `tools/check_branch_landed.py:339-354`, `tools/check_branch_landed.py:874-875`; テストは標準 replace ref のみ `orchestrator/tests/test_check_branch_landed.py:511-522`

**成果物影響**: canonical main に存在しない commit closure が空と記録され、branch 削除後に commit と内容が失われる。

**提案**: nonempty な `git rev-parse --git-path info/grafts` を拒否する。履歴解釈を変える環境変数を除去し、effective replace namespace も検査する。graft と標準外 replace ref の負の対照を追加する。

## 終了時 ref 検査にも削除直前の競合窓がある

**深刻度**: blocker

**成立条件**: checker が終了側の branch ref を読んだ直後、main ref を読む前または JSON 出力前に、別 process が branch を未着地 commit へ進める。開始値と取得済み終了値は一致するため `refs_stable: true` と `landed` が返るが、branch 名は既に未検査 tip を指す。いったん動いて元へ戻る ABA も検出できない。

**file:line**: `tools/check_branch_landed.py:929-935`, `tools/check_branch_landed.py:1003-1020`; 現テストは二回目の取得値が異なる場合だけ `orchestrator/tests/test_check_branch_landed.py:525-547`

**成果物影響**: 古い tip の判定を現在の branch に適用すると、削除候補一覧が新しい未着地 commit を含む branch を削除可能と示す。

**提案**: verdict を明確に `branch.tip` と `main.tip` の snapshot にだけ束縛し、削除側では expected-tip CAS を必須にする。配線が scope 外なら、配線されるまでこの出力を削除 eligibility に使えないことを schema 契約にする。`refs_stable` は連続安定を表さない名前へ改める。

## 非決定の probe が verdict を動かす

**深刻度**: must-fix

**成立条件**: exact receipt または exact tree state だけなら `landed` の branch で、ledger blob が 8 MiB 上限を超える、読取が timeout するなどして `_ledger_corpus` が失敗する。receipt が一致していても corpus を先に構築するため、外側の例外処理が branch verdict を `indeterminate` に変える。task ID observation も同様。

**file:line**: `tools/check_branch_landed.py:523-531`, `tools/check_branch_landed.py:605-613`, `tools/check_branch_landed.py:954-968`, `tools/check_branch_landed.py:1021-1028`

**成果物影響**: 本来 `landed` の行が `indeterminate` になり、判定表と削除候補件数が過少になる。

**提案**: exact receipt の判定後、必要な場合だけ probe を走らせる。ledger、task、patch-id の失敗は各 `observations.*.outcome` に閉じ込め、決定的証拠の verdict を変更しない。probe 失敗時にも landed が維持される負の対照を追加する。

## M2、M4、M8 の変異契約が実装と一致しない

**深刻度**: must-fix

**成立条件**:

- M8 の登録位置 `:444` から path 比較だけを除いても、`_tree_entry` が常に required path を返すため比較する二つの path は恒等的に同じである。さらに別 path の blob は `:692-693` が再度拒否する。現26 nodeは緑のままになり得る。
- M2 の登録位置 `:789` は observation の代入であり、verdict は既に `:735` または `:755` で決定済み。逐語を十分条件にする単一判定式が存在しない。
- M4 の merge fixture は、merge を無視しても side commit が `indeterminate` を維持する。closure 集合 assertion は変異を赤にするが、事前登録した「merge-only を落とすと landed」という単一理由にはなっていない。

**file:line**: `tools/check_branch_landed.py:442-448`, `tools/check_branch_landed.py:475-492`, `tools/check_branch_landed.py:647-665`, `tools/check_branch_landed.py:682-695`, `tools/check_branch_landed.py:735-755`, `tools/check_branch_landed.py:788-790`; `orchestrator/tests/test_check_branch_landed.py:289-309`, `orchestrator/tests/test_check_branch_landed.py:325-364`

**成果物影響**: M8 の安全式を壊しても変異結果が KILLED にならず、判定表の安全保証を誤って合格扱いできる。

**提案**: M8 は実際の決定点 `:692-693` を登録位置にするか、別 path の `TreeEntry` を直接 `:444` へ渡す変異テストを追加する。M2 は明示的な単一合成式を作る。M4 は side state を main に着地させ、merge result だけを未着地にした fixture で、merge を落とした場合に本当に `landed` になることを確認する。

**masking**: あり。M8 は exact-path lookup と any-path 非決定層に完全に隠される。M4 は verdict 上は side commit に隠されるが、closure assertion が構造差を検出する。M1、M3、M5、M6、M7、M9、M10には静的に同型の masking は見つからない。

## 打ち切り実測が `not-run` とゼロへ戻る

**深刻度**: must-fix

**成立条件**: main 履歴が `--history-scan-commits` を超える、または closure が `--max-closure-commits` を超える。関数は limit+1 件を読んだ後に例外を投げるが、payload への代入前なので `outcome: not-run`、`commits_scanned: 0` の初期値が残る。`test_history_scan_limit_is_indeterminate_and_measured` はこの値を一切検査していない。

**file:line**: `tools/check_branch_landed.py:262-267`, `tools/check_branch_landed.py:279-284`, `tools/check_branch_landed.py:339-347`, `tools/check_branch_landed.py:451-465`, `tools/check_branch_landed.py:935-945`; `orchestrator/tests/test_check_branch_landed.py:463-479`

**成果物影響**: 判定表では実際の上限超過が「未走査、0 commit」と記録され、`indeterminate` が増えた原因と走査量を台帳から説明できない。

**提案**: 打ち切り結果を例外ではなく `outcome: truncated`、観測数、limit、elapsed を持つ結果として返す。closure limit、history limit、receipt blob limit の JSON outcome を直接 assert する。

## `files` は file 集合ではなく parent-edge 単位

**深刻度**: nit

**成立条件**: 同じ path を複数 commit が変更するか、merge の複数 parent に対して差がある。`changed_files` は unique path 数だが、`files` は `proof_units` と同じ配列なので同一 path が複数回現れ、相反する verdict も持ち得る。

**file:line**: `tools/check_branch_landed.py:268-277`, `tools/check_branch_landed.py:946-952`, `tools/check_branch_landed.py:973-974`; この別名を固定するテスト `orchestrator/tests/test_check_branch_landed.py:643-645`

**成果物影響**: JSON consumer が一行一 file と解釈すると、file 件数や最終 verdict を誤って削除候補一覧へ転記する。

**提案**: `files` を削除して `proof_units` に一本化するか、path ごとに連言集約した本当の file 配列にする。

## A1〜A8 対応確認

| 裁定 | 主な実装位置 | 判定 |
|---|---|---|
| A1 | `:339-354`, `:402-412`, `:935-946` | 通常履歴では全 closure・全 parent を走査。graft等で破れる |
| A2 | `:442-500`, `:647-665`, `:788-790` | regular file は適合。無効 receipt を決定証拠にする穴あり |
| A3 | `:539-674`, `:727-737`, `:954-984` | receipt miss は適合。probe failure が verdict を動かす |
| A4 | `:72-108`, `:442-448` | tuple 同時比較は実装済み。M8 の path 比較は到達入力上恒真 |
| A5 | `:320-347`, `:451-500`, `:677-695`, `:1003-1028` | 上限、shallow、標準 replace は安全側。履歴 rewrite と ref 競合が未封鎖 |
| A6 | `:250-288`, `:793-830`, `:930-1020` | scope guard と patch-id は実装済み。打ち切り outcome と `files` が不正確 |
| A7 | `:42-45`, `:218-247`, `:590-644`, `:833-858` | 命名と検索範囲は実装済み。task/ledger failure の非決定性は未達 |
| A8 | `:111-134`, `:451-465`, `:889-904` | 平常時の候補数と時間は出る。上限超過時の実測を失うため未達 |

25 test 関数、26 nodeでは、正式 receipt schema、graft、標準外 replace、ref の ABA・終了後移動、merge-only state、全 parent edge、gitlink、deletion、closure limit、probe failure の非決定性が未検査である。

consumer の既存参照は tool と test 以外に見つからない。現行 cleanup は `ahead=0` と `git branch -d` を維持しているため、この checker と矛盾する削除 consumer はまだない。一方、既存 `audit_dangling_commits.py` は変更・削除・gitlinkを対象外と明示しており、checker の代替にはならない。

## 総括

blocker:

- 不正または identity 不一致の FOLDED bullet が `landed` を作る。
- graft と標準外 replace namespace が canonical closure を偽装できる。
- ref の終了時競合と ABA により、未検査 tip を指す branch に `landed` を適用できる。

must-fix:

- ledger/task probe の失敗が verdict を動かす。
- M2/M4/M8 の変異事前登録と実装・fixture が一致せず、M8 は masking される。
- 打ち切り走査量が `not-run`、ゼロとして出力される。

**統合してはならない。** 親の26 nodeと79 nodeの緑は確認済みテストの実走結果として有効だが、上記 blocker はその受理集合の外側にあり、偽の `landed` を構成できる。masking は **あり**。特に M8 は完全 masking、M4 は verdict-level masking である。