# 段 4 裁定 — [T-2778 改訂] 子 worktree の manifest 束縛撤去

作成: 2026-09-19 22:1x JST (親)。入力: `brief.md`、`artifacts/<wave>/plan.md`、`consult-a.md` (正しさ境界)、`consult-b.md` (過剰・削除)。
裁定 inbox 再走査: 本件への更新なし (最新は別 wave の A-1 認可)。本 wave の裁定控えを `rulings-inbox/2026-09-19-t2778-child-worktree-manifest-cleanup.md` に置いた。

## 所見の裁定 (real / refuted、採否)

| # | 所見 | 判定 | 採否・理由 |
|---|---|---|---|
| A1 | `--integration-ref` に子 HEAD (またはその子孫) を渡すと統合証明 B が自己比較で恒真 | real (must) | **採用: `--integration-ref` を廃止**。参照は `refs/heads/main` のみ。段 9 は land 後なので wave tip ⊂ main。 |
| A2 | patch + `ls-files -o --exclude-standard` では bytes を網羅しない (assume-unchanged / skip-worktree、clean filter、ignored、空 dir) | real (must) | **採用 (fail-closed + 生 bytes)**: index に assume-unchanged / skip-worktree flag (`ls-files -v` の小文字) があれば rc20。退避は `status --porcelain=v1 -z --ignored --untracked-files=all` に現れる全 path の**生 bytes を tar** (`dirty.tar.gz`) + `tracked.patch` (HEAD→worktree、`--binary --full-index`) + `index.patch` (HEAD→index) + `status.txt` + `head-sha.txt` + `branch.txt`。空 directory は保存しない (明記)。未解決 stage は rc20。 |
| A3 | clean な submodule にも消える履歴がある (linked worktree の module store は admin gitdir 配下)、submodule 内 ignored | real (must) | **採用 (拒否のみ、救出は作らない)**: 初期化済み submodule ごとに、(i) `submodule status --recursive` の prefix が ' ' (pin 一致)、(ii) submodule 内 `status --porcelain --ignored` が空、(iii) submodule の HEAD reflog 全 commit が gitlink pin から到達可能、のいずれか不成立で rc20。 |
| A4 | exact path は作成世代を識別しない (同 path 再作成 + 旧 manifest) | real (should) | **部分採用**: entry に `branch` を必須化 (detached container は `null`) し、remove 時に実 branch と exact 一致を要求。証拠 dir の `removed.json` receipt (成功時に書く) を世代の記録にし、同 evidence dir で再実行したら `already-clean` (path・record・admin 不在) か rc20 (残骸あり)。admin inode 等の追加束縛は不採用 (再利用で偽陰性、費用対効果)。残余 risk を決定に明記。 |
| A5 | owned_paths の完全性 (rename の両端、再登録での縮小) | real (should) | **採用**: rename は旧新両 path を所有集合に書く (docs)。tool 側は「HEAD 側で `base..HEAD` の diff に現れる path のうち所有集合外のものは統合判定に含めず退避」— 縮小検知は manifest を親だけが書く前提で tool には持ち込まない (B2 と整合)。`base_sha` は不採用 (B1)、比較起点は `merge-base(main, HEAD)`。 |
| A6 | manifest の整合性と所有権限の混同、別 wave manifest の受理 | real (should) | **採用 (明文化)**: manifest は同一 principal (親) が書く信頼済み入力で、署名なし。remove は header `wave_worktree` ≠ child path、manifest file の親 dir が repo 外・登録 worktree 外であること、entry の exact path 一致を検査する。「旧 wave 回収」は caller が旧 manifest を明示して渡す行為そのものが授権 (DW-O28)。 |
| A7 | 占有再検査は再起動を排他しない (TOCTOU) | real (should) | **限界として明記**: 前提 = 当該 wave の子 producer が終端し再投入しない (DW-O28 の「計算ノード job 終端後」+ 決定文)。unlock → 再走査 → rmtree の既存順序は維持。lease 新設は scope 外 (裁定パッケージ候補として insight に記録、起票しない)。 |
| A8 | node の入力条件不足、正例の参照が未明示 | real (should) | **採用**: 正例は「tmp main に author の所有 path patch を取り込み commit 済み (= main 到達)、子は非祖先・所有 blob 一致・所有外 file あり・dirty あり」。負例ごとに唯一の拒否理由・phase・非変更 assertion を要求 (author prompt へ)。 |
| A9 | 回収時の欠落 entry と partial の扱い | real (should) | **採用**: A4 の receipt 規則。partial (rc30) は証拠を上書きせず、次回は rc20 で残骸を報告。退避不能 (A3) は backup 開始前に検査して rc20。 |
| A10/B12 | plan の「materials の D2148 項 9 が T-2051」は誤り | real | **採用**: 原因は親の射影 script の正規表現 (全文で最初の `### 項9` に一致)。段 3 投入前に修正済み。plan §9 のこの finding は撤回。 |
| A11/B9/plan P5 | DW-O28 は 989 bytes 固定が必要 | **refuted** | 先例 `5fc1d8971` (T-2777、Codex author) が `_SYNTHETIC_DW_O28_SECTION` の byte assert を 998→989 へ追随させている。byte assert は literal の派生 pin であり、literal 改訂と同じ commit で author が追随する。制約は L2 単節 ≤1000 bytes と、変異 test `o28_contract_weakened` の置換文字列「次 wave・ユーザー・`/cleanup-branches` へ引き渡さない」の exact 1 出現。 |
| B1 | `registered_at`・`purpose` 列挙・`base_sha`・header `job_dir`/`common_gitdir` は過剰 | real | **採用 (一部)**: `registered_at`・`base_sha`・`job_dir`・`common_gitdir` を削る。`purpose` はユーザー裁定が「用途」を名指すので**自由文字列の必須 field として残す**が、用途別の判定は作らない (所有集合空 ⇒ 祖先性 A のみ、が唯一の規則)。 |
| B2 | 登録 CLI は不要、親が JSON を Write | real | **採用**: `register-child` を作らない。manifest は親が Write で書く (DW-S05-A)。remove 側で全検証。flock なし。 |
| B3 | 履歴 pack は過剰、到達不能履歴は拒否 | real | **採用 (A2/A3 と両立)**: HEAD reflog の全 commit が `refs/heads/main` ∪ 残す子 branch から到達可能でなければ rc20。pack writer・allowlist の `pack-objects` は作らない。 |
| B4 | 子 branch の `-d` は不要 | real | **採用**: 子 branch は常に残し、ref と SHA を報告。branch-recheck/delete phase は子 mode に無い。 |
| B5/B6 | 代案 (a) `-s ours` merge、(b) path 一覧 + 祖先性のみ | real (不採用の裏付け) | 不採用を確定。(a) は内容採用を証明せず不採用履歴を main に残す。(b) は確定裁定の「統合済み」条件を緩める。 |
| B7 | 代案 (c) 報告を子木外へ | real (将来候補) | **本 wave では採らない**が、author prompt に「報告は最終メッセージだけに書き、repo 内へ report file を作らない」を入れ、本 wave の author 子木で (c) 型が成立するかを段 9 の dogfood で観測する (owned_paths 方式のまま)。 |
| B8 | scope 侵食なし | — | 確認。mutation tool 自己登録・外側 container・occupancy 判定変更・`/cleanup-branches`・起動器は別件と決定に明記。 |
| B10 | DW-S05-A 縮約案 (L1.5 残 36 bytes) | real | **採用 (親が文面を確定)**: pin 文「codex は `reasoning=medium`、`sandbox=workspace-write` とする。」は exact 維持 (B 案はこれを崩しているので採らない)。DW-O20 は不変。fix 巡の再利用も DW-S05-A に載せ、DW-S06-B は不変。 |
| B11 | tests 規模、変異 7 件 | real | **採用**: 登録側 node なし。変異は下記 7 件。実 scanner の成功は正例に統合。 |
| B13 | 決定 fragment に実装詳細を混ぜない | real | **採用**: schema 名・rc 表・phase 名・退避 file 名は決定に書かず、対象・条件・置換範囲・維持・却下案だけ。 |
| B14 | 親 brief の一般化 (author 4 本 → 全 producer) | real | **採用**: 決定と worklog に「所有契約を固定した author/fix の観測に基づく限定方式。probe・scratch・mutation container への成立は未確認」と書く。t2484 の `anc_parent=None` は probe script の親 branch 名指定漏れで、集計から外す。 |

## plan v2 (確定)

### manifest (親が Write で書く、repo 外の job dir)

`<job dir>/child-worktrees.json`:
```json
{
  "schema": "izanagi-dev-wave-child-worktrees/v1",
  "wave_worktree": "<絶対 path>",
  "entries": [
    {"path": "<絶対 path>", "purpose": "author", "branch": "refs/heads/<name>" | null, "owned_paths": ["<repo 相対 file>", ...]}
  ]
}
```
検証 (remove 側): 未知 key・重複 key・型不一致・重複 path は rc20。`path` は絶対・正規 (`_validate_path_spelling` 相当、realpath 一致)。
`branch` は `refs/heads/` 始まりか null。`owned_paths` は正規化済み repo 相対 file の閉集合 (絶対・`..`・`.git`・glob magic・directory は rc20)。
manifest file は repo 外・登録 worktree 外。header `wave_worktree` は entry path と一致してはならない。

### CLI

`python3 tools/dev_wave_cleanup.py remove-child --main-worktree <M> --manifest <F> --child-worktree <P> --evidence-dir <D>`
- argv 先頭が `remove-child` のときだけ新経路。既存 4/5 option 形と `_parse_argv` は不変。
- rc: 2 (argv・表記)、20 (manifest・実体・統合・退避可能性・残骸)、21 (占有)、22 (占有判定不能)、30 (backup 開始以降の失敗)。0 で `removed` または `already-clean`。

### preflight 順序 (固定)

1. manifest 束縛 (schema・exact entry・配置)。
2. 記録実在・common gitdir 一致・admin backpointer・実 branch = entry.branch (detached は null)。
3. 対象制限: 非 primary、≠ header wave_worktree、cwd 対象外、fold state 不在、進行中 git 操作なし。
4. 占有: `_assert_unoccupied` をそのまま (D705 継承)。
5. 退避可能性: assume-unchanged/skip-worktree なし、未解決 stage なし、submodule 条件 (A3)。
6. 統合証明: A = HEAD reflog 全 commit が `refs/heads/main` から到達可能; B = owned_paths 非空 ∧ 全所有 path の tree entry (存在/mode/type/OID) が HEAD と main で一致 (単一参照)。A ∨ B。両方不成立なら不一致 path を列挙して rc20。
   さらに (B3) HEAD reflog 全 commit が main ∪ entry.branch から到達可能でなければ rc20。
7. 証拠 dir: 不在または空。receipt があれば手順 0 の already-clean 判定へ。
8. backup: A2 の file 群を書き fsync、内容再照合。
9. mutation: unlock → detach (attached のみ) → recheck (clean は要求しない、HEAD・binding・非占有再走査) → remove-directory → admin-recheck → admin-remove → registry → postcondition → receipt `removed.json` (path・branch・HEAD・証拠 file 一覧)。

### 所有 (Codex author 1 単位)

`tools/dev_wave_cleanup.py`、`orchestrator/tests/test_dev_wave_cleanup.py`、`tools/check_docs.py` (DW-O28 literal のみ)、`orchestrator/tests/test_check_docs.py` (`_SYNTHETIC_DW_O28_SECTION` と byte assert 2 箇所のみ)。
親: `docs/dev-wave/workers.md` DW-S05-A、`docs/dev-wave/operations.md` DW-O28、spool fragment (decisions・worklog)、insight。
親 docs の DW-O28 本文は親が確定して author へ逐語で渡す (literal 一致)。

### 正負例 (実体を名指し、stub 禁止)

正例 `test_remove_child_archives_dirty_integrated_author_and_keeps_branch`: tmp main/wave/child。child は base から所有 `tracked.txt` を commit + 所有外 `author-result.md` を commit (起動器の終端 commit と同型)。main へは `tracked.txt` の同 blob を別 commit で取り込む (child は非祖先)。child に staged 編集・unstaged 編集・`scratch.txt`・ignored file を残す。実 CLI を通し rc0、証拠 file 群の存在と内容 (別 tmp checkout へ patch/tar を当てて一致)、child dir・admin・record の消失、branch 残存 (同 SHA)、main/wave 不変、`removed.json`。占有は実 scanner。
負例 (各 1 理由、phase と rc、非変更 assertion、unlock/detach/rmtree 呼出しゼロ):
- `test_remove_child_rejects_unregistered_path` (manifest / 20)
- `test_remove_child_rejects_live_process_cwd` (occupancy / 21、実 process)
- `test_remove_child_rejects_unintegrated_author_commit` (integration / 20: 非祖先 ∧ 所有 blob 不一致)
- `test_remove_child_empty_owned_paths_requires_ancestry` (integration / 20: 空集合の全称真を通さない)
- `test_remove_child_rejects_nonempty_evidence_dir` (evidence / 20)
- `test_remove_child_rejects_wave_root_and_primary` (preflight / 20、parametrize)
- `test_remove_child_rejects_branch_mismatch` (preflight / 20: entry.branch ≠ 実 branch)
- `test_remove_child_rejects_unreachable_reflog_history` (integration / 20: reset 前 commit)
- `test_remove_child_rejects_skip_worktree_flag` (backup-precheck / 20)
- `test_remove_child_admin_binding_change_is_partial` (rc30)
- `test_remove_child_already_clean_with_receipt` (rc0 already-clean)

### 変異事前登録 (7 件、単一理由、実装後に anchor を逐語で固定)

| id | 変異 | 期待 |
|---|---|---|
| m1 | manifest の exact entry 照合を除去 (任意 path を受理) | KILLED by `test_remove_child_rejects_unregistered_path` |
| m2 | 統合証明を恒真化 (A∨B → True) | KILLED by `..._rejects_unintegrated_author_commit` |
| m3 | 空 owned_paths で B を成立させる | KILLED by `..._empty_owned_paths_requires_ancestry` |
| m4 | backup を skip して成功扱い | KILLED by 正例 (証拠 file 不在) |
| m5 | 占有検査を skip | KILLED by `..._rejects_live_process_cwd` |
| m6 | realpath 検査を文字列一致に落とす | KILLED by `test_child_modes_reject_noncanonical_path` |
| m7 | admin recheck の binding 比較を除去 | KILLED by `..._admin_binding_change_is_partial` |
| m0 | 等価変異 (括弧付替え等) | SURVIVED |

harness: `tools/mutation_harness.py` + `tools/mutation_worktree.py` (DW-M05/M07)。source は独立 clone、dispatch 経路、spec/out は checkout 外。

## docs 本文 (親)

- DW-O28: ≤1000 bytes、置換文字列を exact 維持。確定文面は `dw-o28-final.md`。
- DW-S05-A: L1.5 残 36 bytes に収める縮約 + 「作成時に job dir の manifest へ path・用途・branch・所有 path を書き、保存後に起動。fix は同じ木で branch を切り manifest を更新」。pin 文 exact 維持。確定文面は `dw-s05a-final.md`。
- DW-O20 不変。DW-S06-B 不変。

## scope 外 (insight に記録、起票しない)

- lease による起動/撤去の排他 (A7)。mutation tool の自己登録と外側 container の撤去 (B8)。代案 (c) の運用化 (B7)。
- 既存残骸 19 本と過去 wave の manifest 無し子木 (手動、D204)。

## 段 6 レビュー所見の裁定 (2026-09-19 22:4x JST)

焦点走 1 (`focus-1.log`、dispatch 10793.nqsv、103 秒): 293 passed / 1 failed (`test_remove_child_rejects_live_process_cwd` の後始末 `terminate()` が
dispatch 環境で効かず `wait(timeout=10)` が TimeoutExpired)。review A / B とも NO-GO。所見の裁定:

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | clean filter / eol 変換で status に出ない生 bytes が失われる | real (must) | **採用 (fail-closed)**: backup-precheck で `git check-attr --stdin -z filter text eol -- <全 tracked path>` を取り、`filter` が unspecified 以外、`text` が set/auto、`eol` が設定、または `core.autocrlf` が true/input なら rc20 (変換なし ⇒ clean な tracked file の生 bytes = blob)。負例: `.gitattributes` `* filter=x` + `filter.x.clean` を設定した子 → rc20 (backup-precheck)。全 tracked file の bytes 読取りは採らない (26k file)。 |
| A2 | 子 admin 配下の submodule object store だけにある commit が消える | real (must) | **採用 (fail-closed)**: 初期化済み submodule の gitdir が子 admin dir 配下なら、gitlink pin が primary の module store (`<common>/modules/<path>`、`cat-file -e <pin>^{commit}`) に実在しなければ rc20。負例: 子内 submodule で commit → gitlink 更新 → superproject commit、primary store に無い → rc20 (backup-precheck)。 |
| A3/B3 | 占有テストの後始末が dispatch 環境で赤 | real (must) | **採用**: 既存 `test_real_occupancy_scan_rejects_live_process_cwd` と同じ stdin 待ち + 書込み終了 (`stdin.write(b"x")`, `close`, `wait(timeout=10)==0`) に変更。timeout 増量は不可。 |
| A4/B1 | DW-O28 の実行例に `--main-worktree` が無い | real (must) | **採用**: DW-O28 v4 (`dw-o28-final.md`、996 bytes) で「`--main-worktree <MAIN>` は両方に付ける」と明記。literal・fixture・byte assert (996 のまま、本文は変わる) を fix 子が追随。 |
| A5/B8 | m6・m7 の anchor が単独変異を殺せない | real (must) | **採用 (再照準)**: m6 = `_manifest_path` の `_validate_path_spelling` 呼出しを `Path(raw)` に落とす (killer: `test_child_modes_reject_noncanonical_path[manifest]`)。m7 = `_recheck_admin` の child_proof 分岐 (`_assert_child_integration` 再検証) を `pass` に落とす。killer に新 node `test_remove_child_main_advance_during_removal_is_partial` (rmtree hook で main を 1 commit 進める → rc30 / admin-recheck、証拠は残り receipt 無し) を追加。 |
| A6 | receipt が原子的に公開されない | real (should) | **採用**: 一時 file (`removed.json.tmp`) に書いて fsync → `os.link`/`rename` で `removed.json` を公開 (既存 receipt があれば失敗)、directory fsync。 |
| A7/B4 | docs に登録 field・rename 規則・unlock 主体・「tree entry」が無い | real (should) | **採用 (親)**: DW-S05-A v2 (`dw-s05a-final.md`) に「形式は tool 冒頭、所有 path は rename 両端込み」、DW-O28 v4 に「tree entry 一致」「退避可能性」「親が unlock」。fix 子は `tools/dev_wave_cleanup.py` の module docstring に manifest 形式 (schema・field・rename 規則・信頼境界) を書く。決定 fragment に世代識別の残余 risk と対象外範囲を追記 (親)。 |
| A8 | 正例が `main(argv)` を通らない | real (should) | **採用**: 正例を `cleanup.main(argv)` 経由にし rc0 と stdout `removed` を assert (`run()` の結果検査も残す)。 |
| B2 | 所有外の committed 差分が退避されない (裁定 A5・決定文と不一致) | real (must) | **採用**: `committed.patch` = `git diff --binary --full-index --no-ext-diff --no-textconv --no-renames <merge-base(main,HEAD)> HEAD --` を証拠 file に追加 (receipt の file 集合にも)。正例に `author-result.md` の差分が含まれる assertion。allowlist に `merge-base <a> <b>` と `diff ... <sha> <sha> --` の exact 形を追加。 |
| B5 | 未使用 allowlist 項目 | real | **採用**: `("ls-files", "--others", "-z", "--exclude-standard")` を削除。 |
| B6 | submodule 走査と統合証明の重複 | real (nit) | **部分採用**: `submodule status --recursive` は再帰の各階層で 1 回だけ取得。祖先性成立時の履歴再判定省略と recheck の tree 比較省略は採らない (再検証は意図的)。 |
| B7 | test 数削減は不要 | — | 確認。削減しない。重複分は新規検出力に数えない。 |
| B9 | fragment の「4 本すべて」と ruling の 3 本、S06-B 不変からの逸脱 | real (nit) | **採用 (親)**: fragment を「祖先性を確認できた 3 本」に直す。S06-B の空白縮約は docs 予算 (L1.5 9695/9696) の原資であり、意味不変 — ruling の「S06-B 不変」を「意味不変・空白縮約のみ」に訂正。 |

fix 単位: 1 (所有 4 file、同じ author 木で branch `codex-t2778-fix1` を切る = DW-S05-A v2 の dogfood)。既存テストの期待値変更は不可。
