---
authority: none
default_effect: no-state-change
---

# T-2778 (改訂) — 子 worktree を manifest に束縛して段 9 で wave 自身が撤去する

ユーザー裁定 (2026-09-19)「ワークツリーが残って next-tasks / cleanup-branches のたびに費用が増え続けている。恒久対策が要る」に基づき、
D703 の例外を「wave が作成時に job dir の manifest へ exact path で登録した子木」まで広げ、`tools/dev_wave_cleanup.py` に
`remove-child` を足した。決定は同 wave の decisions fragment (D703 の例外拡張、D2148 項 9 (iii) の部分 supersede)。
本書は逐語凍結と実測の記録であり、可変状態の正本ではない。

基点は着手直前の local main `2ba4000870c63254132410b3002b5298c0c6a210`。実装統合は `2a8127c4e` (author + fix1 + fix2 + 親 docs) と `c9e4ad77a` (fix3 + fix4)。
wave は `worktree-dev-wave-t2778-child-worktree-cleanup`、専用 handoff・生ログ・manifest・証拠は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2778-child-worktree-cleanup/`。

## 1. 何を作ったか

- manifest (`<job dir>/child-worktrees.json`、schema `izanagi-dev-wave-child-worktrees/v1`): 親が Write で書く未署名の信頼済み入力。
  `wave_worktree` と entries (`path` 絶対・正規 / `purpose` 自由文字列 / `branch` `refs/heads/...` か null / `owned_paths` repo 相対 file の閉集合、
  rename は旧新両 path)。登録 CLI は作らない (段 3 所見)。
- `python3 tools/dev_wave_cleanup.py remove-child --main-worktree <M> --manifest <F> --child-worktree <P> --evidence-dir <D>`:
  manifest 束縛 → 記録・common gitdir・実 branch 一致 → 非 primary・非 wave 本体・cwd 対象外・fold state 不在 → 占有 (既存 `_assert_unoccupied`) →
  退避可能性 (assume-unchanged / skip-worktree、未解決 stage、変換属性 (`check-attr --all` で `filter` / `eol` / `working-tree-encoding` / `text=set|auto`、`core.autocrlf`)、submodule の pin 一致・clean・
  reflog 到達・primary store 実在) → 統合証明 (A: HEAD reflog 全 commit が `refs/heads/main` 到達 ∨ B: 所有 path の tree entry 一致、空集合の全称真は不可、
  reflog は main ∪ 子 branch から到達) → 証拠 dir (不在または空、receipt があれば `already-clean`) → backup (`committed.patch` (merge-base→HEAD)、
  `tracked.patch`、`index.patch`、`dirty.tar.gz` (status に現れる全 path の生 bytes)、`status.txt`、`head-sha.txt`、`branch.txt`) → unlock → detach →
  recheck (HEAD・identity・非占有・payload 再計算) → 撤去 → admin 再検査 (統合証明を再検証) → receipt `removed.json` の原子的公開。
  子 branch は残す。rc: 2 argv、20 拒否、21 占有、22 占有判定不能、30 backup 以降の部分失敗。既存 wave 本体 mode は不変。
- docs: DW-O28 (996 bytes、exact literal 追随) に子木 → 本体の順と回収 wave の旧 manifest、DW-S05-A に作成時登録と fix 巡の同木再利用。
  DW-S05-C / DW-S06-B は予算 (L1.5 9695/9696) のための空白縮約のみ。

## 2. 実測 (段 1、Pegasus login node、2026-09-19 21:3x JST)

- 稼働 19 木の編集面重複: commit 差分 (main...branch) と作業ツリー dirt の両方で 0 (`verbatim/measurements-overlap.txt`)。
- 現存子 branch 9 本の統合状態 (`verbatim/measurements-integration.txt`): author / fix 4 本は親 wave tip の祖先でなく、所有 path の blob は
  親 tip と一致、不一致は子が repo 内へ書いた報告 `.md` だけ (t2484 は probe の親 branch 名指定漏れで `anc_parent=None`、集計から外す)。
  probe 3 本は一致 0。scratch / freeze 2 本は親 tip と全一致。→ 所有契約を固定した author / fix の観測に基づく限定方式であり、
  probe・scratch・変異 container への成立は未確認。
- docs 予算: L1 10623/10625、L1.5 9660→9695/9696、DW-O28 989→996/1000。上限引き上げなし。
- 段 1 時点の check_docs baseline rc=0。親 docs 適用後は DW-O28 exact pin の 1 件だけ赤 (pin の正例)。

## 3. 段 2〜4

- 段 2 plan (`verbatim/s2-plan.md`): 子専用 mode、A ∨ B の統合証明、退避 5 file + index.patch + history.pack。
- 段 3 敵対相談 (`verbatim/s3-consult-a-correctness.md`、`verbatim/s3-consult-b-excess.md`): A = `--integration-ref` の自己証明 (must)、退避の不完全性、
  submodule の消える履歴、世代束縛、TOCTOU、partial 再開。B = 登録 CLI・時刻・purpose 列挙・履歴 pack・子 branch 削除は過剰、代案 (a)(b) 不採用・(c) 将来候補、
  DW-S05-A の縮約案。
- 段 4 裁定 (`verbatim/s4-ruling.md`): `--integration-ref` 廃止、生 bytes tar + fail-closed、履歴 pack の代わりに到達不能履歴を拒否、登録 CLI なし、
  子 branch 残置。「DW-O28 は 989 bytes 固定」は先例 `5fc1d8971` で refuted (byte assert は literal に追随)。plan の「D2148 項 9 の射影が別 D」は
  親の射影 script の誤りで段 3 前に修正。

## 4. 段 5〜6

- author (22:06→22:22、rc=0、`verbatim/s5-author.md`): 4 file / +756 行、新設 16 test 関数 (31 node)。起動器の終端 commit `4fb072418`
  (branch `codex-t2778-author`)。所有 path 限定 patch を wave 木へ適用。
- 焦点走 1 (dispatch 10793.nqsv、103 秒): 293 passed / 1 failed — `test_remove_child_rejects_live_process_cwd` の後始末 `terminate()` が dispatch 環境で
  効かず timeout (本体判定の赤ではない)。
- 敵対レビュー 2 本 (`verbatim/s6-review-a-correctness.md`、`verbatim/s6-review-b-excess.md`): 初回は wave 木で docs 未 commit のため review 段の
  authority 検査で rc=2 即死 → author 子木 + docs.patch 射影で再投入。両 NO-GO。A: clean filter の生 bytes、submodule の admin 配下 store、
  占有 test の後始末、DW-O28 の `--main-worktree` 欠落、m6/m7 の anchor、receipt 原子化、docs の field・rename、正例の `main(argv)`。
  B: DW-O28 引数、所有外 committed 差分の退避 (`committed.patch`)、占有 test、docs の契約、未使用 allowlist、submodule 走査の重複。裁定は `verbatim/s4-ruling.md` 末尾。
- fix1 (22:41→22:46、`verbatim/s6-fix1.md`、`bcebec55b`): 全採用所見を反映。A2 と段 5 新設 fixture `[clean]` (primary store なし) の衝突で停止報告 →
  親裁定「fixture 側が非現実的、実装は裁定どおり」→ fix2 (`verbatim/s6-fix2.md`、`8f430b748`、branch `codex-t2778-fix2` を同じ author 木で切り manifest を再登録
  = DW-S05-A v2 の dogfood) で fixture を実環境の形へ。
- 焦点走 2 (dispatch 10890.nqsv、104 秒): 269 passed / 1 skipped、rc=0 (cleanup 全体 + collection 契約 + check_docs の O28 / exact pin 系)。
  統合木の check_docs rc=0。全史 provenance 11,617 件、新規違反なし (既知 56)。
- 焦点再レビュー 1 巡目 (`verbatim/s6-focus-review-1.md`): NO-GO 2 件 — A1 open (`check-attr` の値文字列 `unspecified` は driver 名 `unspecified` と
  区別不能) と N1 (m4 の期待 node に detached 正例が漏れ)。他は closed、wave mode 回帰なし。
- fix3 (`verbatim/s6-fix3.md`、`aa318d9a9`): `check-attr --stdin -z --all` で属性の有無により判定 (`filter` / `eol` / `working-tree-encoding` は値によらず、
  `text` は set/auto)。焦点走 3 (login、6 秒): 186 passed / 1 failed = 新負例 `[named-unspecified]` の fixture 自己 assertion (status が ` M`)。
  親の実測 (git 2.34.1、`probe-filter.sh`): `ie_modified` は index の cached size と file size が違うと再 hash せず DATA_CHANGED を返すため、
  size を変える clean filter では「status は clean だが生 bytes は blob と異なる」状態を作れない。
- fix4 (`verbatim/s6-fix4.md`、`2804f1323`、branch `codex-t2778-fix4`): size 不変の `tr a-z A-Z` + `git add --renormalize .` で fixture を作り直し。
  焦点走 4 (dispatch 11171.nqsv): 187 passed、rc=0。統合 commit A' = `c9e4ad77a`。
- 焦点再レビュー 2 巡目 (`verbatim/s6-focus-review-2.md`): A1・N1 closed、回帰なし、anchor 8 件が HEAD に 1 箇所ずつ → GO。
  fix 巡は 4 回 (fix2・fix4 は親の実機実走でしか見えない fixture の非現実性の追従、DW-O16 の「親の実機 blocker は別枠」)。

## 5. 変異 matrix (独立 clone を source、`tools/mutation_worktree.py` + `tools/mutation_harness.py`、dispatch、runner = `run_tests.py --force-dispatch orchestrator/tests/test_dev_wave_cleanup.py -q -rf`)

事前登録 (段 4、`verbatim/s4-ruling.md`) の 7 件 + 等価 1 件。anchor は段 6 の焦点再レビュー 2 本が HEAD に逐語 1 箇所ずつと照合した。

| id | 変異 | 期待 | killer node |
|---|---|---|---|
| m0 | `owned_equal` の括弧付替え (等価) | SURVIVED | — |
| m1 | manifest の exact entry 照合を外す (任意 entry を選択) | KILLED | `test_remove_child_rejects_unregistered_path` |
| m2 | 統合証明 A∨B を恒真化 | KILLED | `..._rejects_unintegrated_author_commit`、`..._empty_owned_paths_requires_ancestry` |
| m3 | 空 owned_paths で B を成立 | KILLED | `..._empty_owned_paths_requires_ancestry` |
| m4 | `dirty.tar.gz` を空 bytes に | KILLED | `..._archives_dirty_integrated_author_and_keeps_branch`、`..._detached_ancestry_and_empty_backup` (v2 で補完) |
| m5 | preflight の占有検査を skip | KILLED | `..._rejects_live_process_cwd` |
| m6 | manifest path の正規化を外す | KILLED | `test_child_modes_reject_noncanonical_path[manifest]` |
| m7 | admin 再検査の統合証明再検証を skip | KILLED | `..._main_advance_during_removal_is_partial` |

### 5.1 probe (spec v1、commit `2a8127c4e`、`mutation/probe-v1.json`、23:10→23:53 JST、erratum として保存)

baseline 186 passed (76 秒)。m0 SURVIVED、m1/m2/m3/m5/m6/m7 KILLED (期待 node 完全一致)、**m4 MISMATCH** — 期待 1 node に対し実際は 2 node
(`detached_ancestry_and_empty_backup` も空 tar を開けず赤)。焦点再レビュー 1 巡目の N1 が事前に指摘したとおりで、spec v2 で期待 node を補完した。
queue 混雑 (izdw job 13 本) で m0 に 1150 秒、m5 に 383 秒。wrapper: `shared_snapshot_matches=true`、container 撤去済み、child_rc=1 (MISMATCH)。

### 5.2 本走 (spec v2、commit `c9e4ad77a`、`mutation/final-v2.json`、23:38→00:06 JST、rc=0)

baseline 186 passed (queue 待ち込み 715 秒)。**m0 SURVIVED (等価)、m1〜m7 KILLED、期待 node 完全一致 8/8、MISMATCH 0**。所要は m1 364 秒、
他は 27〜60 秒。wrapper: `shared_snapshot_matches=true`、container 撤去済み、child_rc=0 (`mutation/final-v2.wrapper-receipt.json`)。

## 6. 受入・land・段 9 の dogfood (wave 1 = entry 1706 / D2163)

- 受入 (門番付き chain): attempt final (02:02 開) は main 63638e179 の merge で両親が `tools/check_docs.py` を触り integrator だけの
  merge message が provenance で赤 (rc=94) → D770 の 2 commit 分割 (M1 `593a72fc9` main 版で確定、M2 `b3aed35a4` Codex author が literal を再適用、
  index tree = 一発 merge tree ab84145ab で一致、M3 `81ffc26c5` main 側の追記で溢れた L1.5 を −19 bytes で収容)。final2 (03:04) は非帰属の赤 —
  memo 発行 shard の job 11636 が QUE/PRR に 7 分滞留し他 shard の `memo publication timeout` (INTERNALERROR、差分到達不能)、driver の SIGTERM で
  orphan hold → job 終端を qstat で確認して hold 2 file を手動解除。final3 (03:17): main e6b38c5ef を merge → tip `00e571827`、
  **25410 passed / 69 skipped、child-green 03:29:38**。
- land: 調停役の GO (main = tested_main、merge 不要) → `landed`、新 main `baba46bb7` (fold: D2163、worklog 1706、03:35:22)。全史 provenance は land 内で緑。
- 段 9 dogfood: wave 本体 = removed (rc=0、branch 削除)。**子木 `remove-child` = rc=20 backup-precheck「tracked file has conversion attributes」** —
  superproject には変換属性が無く、submodule (ccbench) の `* text=auto eol=lf` を fix1 の再帰 `_assert_child_no_conversion(module)` が拒否。
  この repo の子木は全て ccbench 初期化済みなので、1706 時点の tool は実子木を 1 本も撤去できない。段 6 の tmp fixture は submodule に属性を持たず
  回帰を捕まえなかった。DW-STOP「直せる赤で終了しない」に従い同 session で wave-2 (branch `worktree-dev-wave-t2778-child-worktree-cleanup-2`、
  main baba46bb7 から) を続けた。

### 6.1 wave-2 (fix5): 変換属性の検査を superproject 限定に

裁定: submodule の内容は退避せず pin 一致・clean・reflog 到達・primary store 実在で守るので、submodule 側の属性は内容喪失の経路にならない。
Codex author (子木 branch `codex-t2778-fix5` @ main tip、同じ author 木を再利用) が再帰呼出しを外し、fixture の submodule 側に
`* text=auto eol=lf` を足して `[clean]` が回帰を検出する形にした。結果は §6.2 に記録。

### 6.2 wave-2 の結果

- fix5 (`verbatim/s9-fix5.md`、子木 commit 1ad54a50d、03:41→03:42): `_assert_child_submodules` の再帰から `_assert_child_no_conversion(module)` を外し
  (superproject への検査は不変)、fixture の submodule source に `* text=auto eol=lf` を commit。直接呼出し 6 parameter + clean-filter 2 parameter PASS、
  反実仮想 (呼出しを戻す) で `[clean]` が rc20 / backup-precheck。焦点走 5 (login): cleanup file 187 passed。実装 commit `951779aa3`。
- 変異 (spec w2 = 再帰呼出しを戻す 1 件、source clone を 951779aa3 に固定、dispatch、`mutation/final-w2.json`): baseline 186 passed (27 秒)、
  w2m1 KILLED (killer `test_remove_child_checks_initialized_submodule[clean]` に完全一致)、rc=0、container 撤去済み。
- 段 6 の敵対レビュー 2 本は wave-2 では起動していない (差分は 1 行の呼出し削除 + fixture 1 属性で、裁定は §6.1 の親判断、実効性は dogfood と変異で確認)。
- wave-2 の受入 (04:00→04:11、25410 passed / 69 skipped、child-green) → GO → land rc=0、main `c13914d44` (04:14:26)。段 9: wave-2 木 = removed。
  **子木 = rc=20 backup-precheck「submodule reflog is unreachable from gitlink pin」** (2 巡目の dogfood 赤)。

### 6.3 wave-3 (fix6): submodule reflog の判定に primary store の実在を加える

原因 (`probe-submodule-reflog.sh` + `_head_reflog_shas`): 入れ子 googletest module の HEAD reflog に clone 直後の既定 branch tip (`4267679b`、
「checkout: moving from <既定> to <pin>」の old 側) が残り pin の祖先でない。上流と primary の同 path の module store に実在 (`cat-file -e` で確認)。
裁定: reflog sha は「pin 到達 ∨ primary の同 path の module store に実在」で受理、どちらでもない sha (子の store にしか無い local commit、既存 `[reflog]`) は
拒否のまま。fix6 (`verbatim/s9-fix6.md`、子木 branch `codex-t2778-fix6` @ main c13914d44、commit f619d85a6; launcher の受理は報告文の 1 文字で
not_accepted だが内容は親が監査): 実装 4 行 + fixture parameter `[default-branch-reflog]`。焦点走 6 (login): 188 passed。実装 commit `f749b9ecf`。
変異 (spec w3 = store 実在の分岐を外す 1 件): 結果は §6.4。

### 6.4 wave-3 の結果

- 変異 (spec w3、source clone を f749b9ecf に固定、dispatch、`mutation/final-w3.json`): baseline 186 passed (27 秒)、w3m1 KILLED
  (killer `test_remove_child_checks_initialized_submodule[default-branch-reflog]` に完全一致)、rc=0、container 撤去済み。
- 敵対レビューは wave-3 でも起動していない (差分は 4 行の条件追加 + fixture 1 parameter、裁定は §6.3 の親判断、実効性は dogfood と変異で確認)。
- wave-3 の受入 (04:31→04:42、25411 passed / 69 skipped、child-green) → GO → land rc=0、main `65fe36a94` (04:46:18)。段 9: wave-3 木 = removed。
  **子木 = rc=20 phase integration「HEAD reflog history is unreachable from main and retained branch」** (3 巡目の dogfood 赤、backup-precheck は通過)。

### 6.5 wave-4 (fix7): HEAD reflog の判定に「任意の local branch が保持」を加える

原因 (`probe-child-history.sh`): DW-S05-A の手順どおり同じ author 木で fix1〜fix6 の branch を切り替えたため、HEAD reflog に各 fix branch の tip
(4fb072418 / bcebec55b / 8f430b748 / aa318d9a9 / 2804f1323 / 6baa6c973 / 1ad54a50d / f619d85a6) が残り、manifest の branch (main tip から切った
codex-t2778-fix7) からも main からも到達しない。実測で reflog 15 sha 全てが何らかの local branch に含まれる (喪失ではない、tool は子 branch を消さない)。
裁定: 「main ∨ manifest branch ∨ 任意の local branch (`git branch --contains <sha> --format=%(refname)` 非空)」で受理、どの branch にも無い sha
(reset で捨てた commit、既存 `..._rejects_unreachable_reflog_history`) は拒否のまま。fix7 (`verbatim/s9-fix7.md`、子木 branch `codex-t2778-fix7` @ main 65fe36a94、
commit 1b3d260e1): 実装 3 行 + allowlist 1 形 + 正例 `test_remove_child_reflog_retained_by_other_branch`。焦点走 7 (login): 189 passed。
実装 commit `522643410`。変異 (spec w4 = 分岐を外す 1 件): 結果は §6.6。

### 6.6 wave-4 の結果

- 変異 (spec w4、source clone を 522643410 に固定、dispatch、`mutation/final-w4.json`): baseline 186 passed、w4m1 KILLED
  (killer `test_remove_child_reflog_retained_by_other_branch` に完全一致)、rc=0、container 撤去済み。
- 敵対レビューは wave-4 でも起動していない (差分は 3 行の条件追加 + allowlist 1 形 + 正例 1 本、裁定は §6.5 の親判断、実効性は dogfood と変異で確認)。
- 受入・land・段 9 の撤去結果 (子木 `remove-child` の正例、wave-4 木) は専用 handoff と wave-4 の worklog entry に記録する。
  3 巡の dogfood 赤 (§6・6.2・6.4) はいずれも tmp fixture に無い実環境の差で、tool の受理述語は「削除範囲外 (main・local branch・primary module store)
  に在るか」に統一された。

## 7. scope 外として記録 (起票しない)

- 起動 / 撤去の排他 (lease)。撤去中に producer が再起動する TOCTOU は「producer 終端・再投入禁止」の前提で扱う (段 3 A7、段 6 A 裁定パッケージ候補)。
- 変異 tool の自己登録と外側 container の撤去、`/cleanup-branches` の改訂、起動器の改訂、代案 (c) (報告を子木外へ) の運用化。
- 既存残骸 19 本と過去 wave の manifest 無し子木 (D204 のまま個別指示)。
