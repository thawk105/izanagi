静的検証の結果、現プランには must-fix 候補が 6 件、scope 外の裁定候補が 1 件、nit が 1 件ある。

## 1. 現行 worklog が「閾値超過」という親実測は成立していない

**根拠 (file:line):** `measurements.md:49-54` は 1729 行を根拠に閾値超過としているが、[tools/check_docs.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/check_docs.py:99) の閾値は `WORKLOG_ROTATE_BYTES = 100_000` である。ローテーション判定も [tools/spool_fold.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1533) で fragment 反映後の `len(rendered_worklog)` を見る。静的確認時の現物は 1729 行・97,061 bytes だった。

**具体的な失敗シナリオ:** worklog への追加が 2,939 bytes 以下、または decisions/failures fragment だけなら projected 値は 100,000 bytes を超えず、rotation も `C` も発生しない。「閾値超過中は全 wave が構造的に失敗する」という一般化は、この測定からは導けない。

**成果物影響:** certified 選択値・レポート bytes は直接変わらないが、land 失敗の原因と台帳欠落の必然性を誤って記録し、受理集合と再現条件を取り違える。

**推奨:** brief を「行数閾値」から「fragment 反映後の byte 閾値」へ直し、実 candidate に対する `projected_worklog_bytes` と `rotation_path` を親が測ってから即時障害を主張する。

## 2. 高類似度正例は Git の heuristic と製品変更を分離できない

**根拠 (file:line):** `measurements.md:8-35,56-61` は単一の UTF-8 テキスト fixture、Git 2.34.1 の一点観測である。`plan.md:109-112,129` は 85〜95% fixture で `Cnnn` を対照確認する。Git の仕様上、既定閾値は 50% だが、`-l` は exhaustive 検出を `diff.renameLimit` により抑止し、`--find-copies-harder` は source 候補集合を変える。[Git 2.34 の公式 diff-tree 文書](https://git-scm.com/docs/git-diff-tree/2.34.0)でもこの区別が明記されている。

`plan.md:49` は独立した `diff.copies` が存在しないと正しく述べながら、`plan.md:70-71,111` では `diff.copies=true` を設定している。これは Git が保存するだけの未知 key で、検出力を持たない。`diff.renames` が plumbing に効かない点は 2.34 と現行文書・ソースで支持されるが、`diff.renameLimit` まで無効という一般化はできない。[Git 2.34 git-config](https://git-scm.com/docs/git-config/2.34.0)

**具体的な失敗シナリオ:** 対照の `C` assert を省けば、旧 `-M -C` 実装でも fixture が `A` になった環境で正例が緑になり、変更を何も検出しない。計画どおり `C` を必須にすれば恒真化は避けられるが、Git 版・fixture bytes・候補数の差で正しい実装まで赤くなり、製品退行ではなく環境差を検出する。

**成果物影響:** 偽緑なら `-M -C` 回帰を受理して rotation fold が再び拒否され、試行台帳と「次の一手」が欠落する。環境由来の偽赤なら正しい land が不必要に停止する。certified 選択値と既存レポート値は直接変わらない。

**推奨:** heuristic な 85〜95% を mutation oracle にせず、変更前 worklog blob を archive に完全複製し、worklog を別内容へ変更する deterministic な `C100` fixture にする。旧コマンドで `C100`、`--no-renames` で `A` を確認する。repo-local config と `diff.copies` はこの挙動テストから外し、明示 flag の所有は command 契約テストへ一本化する。

## 3. `_landed_fold_output_path` の `R` 削除は唯一の予備防壁を捨てる

**根拠 (file:line):** `plan.md:83-91` は `R` 分岐削除を推奨する。[git_state.py:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:557) の `R` 判定は、fold slot の [git_state.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:763) と違い、閉集合判定と重複していない。さらに `_diff_entries` は [git_state.py:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:565) で今後も `R/C` を正規入力として parse する。

**具体的な失敗シナリオ:** 将来 `-M` が戻り command test も誤って弱められると、wave の第一 commit が fragment を追加し、第二 commit がそれを spool 外へ `R100` で移す形を `landed-fold-owned-path` が見逃す。最終 tree に pending fragment がなければ null-fold も通り得る。計画の新 rename テストは `--no-renames` 下の `D+A` しか通らず、削除した `R` 分岐を一度も検査しない。

**成果物影響:** fragment が canonical 台帳と `FOLDED.md` に畳まれないまま wave が受理され、試行台帳・レポート参照・次タスク参照が欠落する。certified 選択値は直接変わらない。

**推奨:** fold slot の重複した明示 `R/C` 条件は削除してよいが、landed classifier の `R` は残す。到達不能保証にしないため、`R100 <fragment> <outside>` を直接、または rename detection を一時有効にした統合 fixture で検査する。

## 4. M/D/A 閉集合 gate に帰属する `T` 負例がない

**根拠 (file:line):** `plan.md:103-123` の 5 テストはいずれも M/D/A しか生成しない。一方、変更後の唯一の status gate は [git_state.py:760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:760) の `status not in {"M", "D", "A"}` になる。Git は regular file・symlink・submodule gitlink 間の typechange を `T` とする。[公式 diff-format](https://git-scm.com/docs/diff-format.html)

**具体的な失敗シナリオ:** `status` gate を削除、または `T` を許容集合へ加える変異を入れ、既存の正規 rotation path を regular file から symlink/gitlink へ変える。`T` は後段の `else` で archive 追加として扱われ、path regex、archive count、minimum shape をすべて満たして受理される。提案テストは全て緑のままである。

**成果物影響:** archive の参照先・型が壊れた fold を daemon recovery の受理集合へ入れ、試行台帳の archive 参照を不正にする。certified 選択値・既存レポート値は直接変わらない。

**推奨:** 既存の valid rotation path を index 上で regular→gitlink へ変え、`path-status` を期待する deterministic な負例を追加する。これは編集対象の閉集合 gate に直接帰属するため現 scope 内である。

## 5. archive-count 変異は README 結合 gate による偽 kill になり得る

**根拠 (file:line):** `plan.md:113-119,132-133` は `archive_adds > 1` を `> 2` にする変異を multiple-archive テストへ帰属させる。[git_state.py:781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:781) の直後には、[git_state.py:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:783) の README 結合 gate がある。

**具体的な失敗シナリオ:** 現実的な rotation helper が README も変更して archive を 2 件作る。`> 2` 変異後は `archive-count` を通過するが、続く `archive-readme` で拒否される。テストは期待 detail が変わるため赤になるものの、「archive 最大 1 件」という受理集合はこの fixture ではまだ破れておらず、別 gate の赤を mutation kill と誤認する。

**成果物影響:** mutation matrix が存在しない検出力を記録する。後に README gate も弱まると archive 2 件が受理され、台帳 archive の順序・索引参照が曖昧になる。

**推奨:** archive-count 専用 fixture では README を変更しない。変異後に「別 detail で拒否」ではなく `result.ok` まで到達することを事前登録する。README 単独負例とは fixture を分離する。

## 6. brief の I3 は caller の意図した受理集合変更と矛盾する

**根拠 (file:line):** `brief.md:48-49` は「他 caller の挙動は変えない」を不変条件にする。一方 `plan.md:140-144` は、checker の rotation receipt が fail→pass、daemon recovery が停止→受理へ変わると明記する。実際に [checker.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/checker.py:543) は結果を `fold-commit` slot に写し、[daemon.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/daemon.py:1526) は `declared.ok` を recovery 継続条件にしている。[dev_wave_land.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1513) も rollback から成功へ変わる。

**具体的な失敗シナリオ:** 同じ schema v2 receipt が変更前は checker fail／`AMBIGUOUS_RECOVERY`、変更後は checker pass／次 wave 再開となる。I3 を逐語で検査すれば正しい実装を拒否し、無視すれば不変条件を破った実装を受理する。

**成果物影響:** certified 選択・既存レポート bytes は直接変更しないが、run の受理集合と daemon の継続集合が変わり、後続 wave が生成する試行台帳・レポート材料の有無が変わる。

**推奨:** I3 を「引数・戻り値・reason schema と非 rotation ケースは不変。valid rotation の land/checker/recovery 受理だけが変わる」に修正する。caller-level テスト追加は現 scope 外なので、必要なら段 4 の裁定パッケージにする。

## 7. scope 外裁定候補: path/status だけでは fold bytes と mode を証明できない

**根拠 (file:line):** [git_state.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:708) は FoldPlan との blob 照合を明示的に行わず、[git_state.py:756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:756) は status/path/count だけを見る。対して正規 producer は [spool_fold.py:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:809) で UTF-8/LF、[spool_fold.py:1427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1427) と [spool_fold.py:1723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1723) で regular file を強制し、land は [dev_wave_land.py:1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1363) で `check_docs.py` を実行する。

**具体的な失敗シナリオ:** 正しい author/message/parent を持つ手製 fold commit が、fragment を `D` にし、`FOLDED.md` は内容を変えず executable bit だけ変更して `M` にする。minimum shape は成立し、receipt bytes を追記していなくても verifier 単体は通る。新規 rotation path を binary blob・symlink・gitlinkとして `A` にする形も同様である。正規 land producer は防ぐが、daemon recovery は verifier 単体を信頼する。

**成果物影響:** daemon の受理集合に receipt 未記録または非 regular archive を含め、試行台帳と proof-chain 参照を壊す。certified 選択値は直ちには変わらないが、レポートの台帳参照が不正になる。

**推奨:** 今回は実装しない。段 4 へ「fold commit tree の mode/after-bytes を FoldPlan に束縛する」対「daemon recovery に checker/check-docs 相当の attestation を要求する」の裁定候補として返す。binary・大サイズ・CRLF・submodule の production fixture を今 wave に追加する必要はない。

## 8. nit: command tuple 全体固定は必要以上に脆い

**根拠 (file:line):** `plan.md:39,105-107` は `commit-diff` の期待 tuple 全体を固定する案である。必要な契約は `--no-renames` の存在と `-M/-C/--find-renames/--find-copies` 等の不存在である。

**具体的な失敗シナリオ:** rename 検出と無関係な hardening flag の追加や安全な option 順序変更でもテストが赤くなり、契約違反と実装整理を区別できない。

**成果物影響:** nit。certified 選択、レポート、台帳の値・参照は変わらず、将来の dev-wave が不要に停止するだけである。

**推奨:** command 全体を意図的に凍結するなら、その理由をテスト名・コメントに明記する。そうでなければ必須 flag と禁止 flag の意味検査に絞る。

## 確認済みで追加所見なし

- [test_dev_waves_git_state.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:66) の mutating-verb meta-testは `--no-renames` と衝突しない。
- 新規・改名した `test_*` は [test_dev_waves_git_state.py:484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:484) の動的 runner に自動収集される。既存 node 名への外部参照は見つからなかった。file-level meta-testも自走 harness の有無だけを検査する。
- `spool_fold.py` には rotation producer の正例が既にあり、land の staged-path 検査も [dev_wave_land.py:1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1452) で `--no-renames` 済み。hooks と `check_docs.py` に同じ rename heuristic 依存はない。

## 総括

Must-fix 候補:

- 実 repo の projected byte 値を測り、閾値超過の一般化を修正する。
- heuristic な高類似度 fixture を deterministic `C100` に替え、無効な `diff.copies` 設定を除く。
- landed classifier の `R` 防壁を残して実入力テストを付ける。
- `T` status の帰属負例を追加する。
- archive-count fixture から README 変更を外す。
- I3 を実際の caller 受理集合変更に合わせて修正する。

Scope 外の裁定候補:

- fold commit の mode/after-bytes 束縛、または daemon recovery の追加 attestation。

Nit:

- `commit-diff` tuple 全体固定の過剰拘束。

pytest・自走テストは実行しておらず、緑は主張しない。所見は静的検査と Git 公式仕様の照合による。