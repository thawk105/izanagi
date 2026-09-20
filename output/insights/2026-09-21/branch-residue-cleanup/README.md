# 残骸 branch/worktree が溜まらない構造にする — dev-wave の記録 (2026-09-21)

- wave: `worktree-dev-wave-branch-residue-cleanup` (ユーザーが直接起動した未採番の自己改善 wave。worklog の title に T 番号は書かず、本 wave 自身の T は起票しない)。
  起点 local main `285477c00` (fresh worktree、01:17 JST gate rc 0) → 段 4 直前に `2afb39768` (第 27 回 rulings) を ff-only 取り込み。
- 起点: ユーザーの `/dev-wave` 起動 (00:59 JST、背景 job a5f1786a)。ユーザー裁定 (00:40 頃): 「`/cleanup-branches` は branch の `-D` をしてよい /
  残骸 155 本は消す / 自己改善 wave で再発を防ぐ」。一次資料 = `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-20260921-rescue/`
  (self-improvement-brief.md、deleted-branches.tsv 140、excluded-branches.tsv 24、loss-commits.tsv 227、retire-worktrees.json 13、
  deleted-branches.bundle 5,933,267 bytes sha256 `b062caa7…`、verify rc 0・140 heads)。
- 専用 handoff: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-branch-residue-cleanup/HANDOFF.md`。逐語は `verbatim/`。

## 1. 何をしたか (成果物 1〜6)

| # | 成果物 | 所在 |
|---|---|---|
| 1 | decisions fragment (D204 の狭い例外を 2 経路へ、D703 / D2163 / D2042 の supersede と維持) | `docs/spool/decisions/2026-09-21-dev-wave-branch-residue-cleanup-1.md` |
| 2 | `/cleanup-branches` §0/§2/§3/§5 の `-D` 経路 (7,055 bytes、予算 7,058) + pin (author B)。SKILL.md は不変 | `.claude/commands/cleanup-branches.md`、`tools/check_docs.py`、`orchestrator/tests/test_check_docs.py` |
| 3 | `remove-child` が統合証明済みの子 branch を履歴 bundle 退避後に専用経路で `-D` (author A + fix 2 巡)、`DW-O28` 改訂 (994 bytes、段 6 で 3 限定を追加) | `tools/dev_wave_cleanup.py`、`orchestrator/tests/test_dev_wave_cleanup.py`、`docs/dev-wave/operations.md` |
| 4 | failures fragment (型: 掃除規約の allowlist が構造的残骸に届かず溜まった、F747 の対) | `docs/spool/failures/2026-09-21-dev-wave-branch-residue-cleanup-2.md` |
| 5 | 到達不能 object 台帳へ 248 entry (損失 227 + 監査のみ 21) を既存 schema で pending 追記 | `docs/unreachable-object-ledger.md` |
| 6 | §2 高い条件の「非施錠を再確認」(T-2814 が先に入れた) を `.git/worktrees/<name>/locked` 不在の検査として具体化 (2 と同 commit) | 同上 |

## 2. 実測 (親)

- brief 前: `.claude/commands/cleanup-branches.md` は main で 6,181 / 6,204 bytes (引数の 5,900 / 5,888 は旧値)。T-2814 wave が同 file を並走編集中 (作業中版 6,200〜6,201 bytes、land 後の余白 3 bytes)。
- `rescue2.json` (cleanup session の事前 report) は job dir `f9f84e36` の削除で消失。残る一次資料は loss-commits.tsv (227 = landed 26 / indeterminate 197 / not-landed 4) と bundle。
- 01:14 JST `check_branch_rescue.py --ledger-check` (候補なし、5.7 秒) = rc 3、未記帳 87 件。01:21 `git fsck --unreachable --no-reflogs` = 1,721 件、損失 227 は全件 fsck 到達不能、うち監査取り残し 66・監査非通知 161 (**変更 path が main / 他 branch tip に存在する等で報告対象外であって内容着地の証拠ではない** — 段 3 lens A の訂正)、監査のみ 21 (2026-08-23〜09-09 の commit、今回の削除閉包の外)。
- 台帳追記後 (02:00 頃) の `--ledger-check` = rc 3 (pending 通知 247)、parse 完全、未記帳 0、entry 278、10.4 秒。
- D2194 項 10 (候補 2 の 6 本は worktree を撤去し branch は残す、T-2821) は、裁定 (00:5x) の前 00:46 の cleanup で 6 本とも worktree 撤去 + branch を bundle 退避後 `-D` 済み (retire-worktrees.json / deleted-branches.tsv で照合)。DW-O12 に従い実行済み手順として記録し、T-2821 は完了に置く。

## 3. 段 2・3 の所見と裁定 (逐語は verbatim/)

段 2 plan (`s2-plan.md`)、段 3 lens A 11 所見 / lens B 12 所見、段 4 裁定 (`s4-adjudication.md`)。主な real:
A-2 (所有 path 一致で通った子の中間 commit は branch 削除で保全根を失う → `-D` 前に `history.bundle`)、A-7 (監査非通知 ≠ 着地証拠)、
A-10 / B-5 (cleanup 実行内で台帳へ書くと台帳契約・land・F747 と衝突 → 転記は別 wave)、B-1 (同木の旧 fix branch は manifest に無く残る → 効果を明記、
次の一手へ)、B-3 (land 済み判定 = worklog / archive の完了 entry)、B-6 (schema 拡張は不要)、B-8 (author A/B の file 所有を素集合に)、A-6 / B-9 (概算の訂正)。
refuted: A-1 (所有外 commit 済み差分は `committed.patch` に退避)、A-3 (削除順序)、A-4 (`-D` の構造限定)、A-5 (manifest は対象束縛)、B-10、B-11。

## 4. 段 5・6 (実装・レビュー・fix)

- author A (Codex、01:39 起動、`.codex/worktrees/branch-residue-author-a`、branch `codex-branch-residue-author-a`): 実装済み・未実走 (login では pytest 不可)。
  仕様衝突 1 (HEAD が main 祖先の子で bundle 範囲が空) → fix1 (同木・同 branch、bundle 省略条件 = 子 HEAD の main 祖先性) → 統合 commit `82b36fb64`。
- 焦点走 f1 (計算ノード、02:02): `test_dev_wave_cleanup.py` 10 node 赤 = 同根 (`git bundle create` は ref 名を要求し bare sha では "Refusing to create empty bundle")
  → fix2 (positive 側を `refs/heads/<branch>`、detached 子は bundle なし) → 統合 commit `c6638054b`。f1 の他の赤: `test_campaign.py` / `test_p3_exploration_namespace.py` の
  setup error (`fixture 'ratified_enforcement_source' not found`) は、test でない契約 module `orchestrator/test_selection_contract.py` を pytest に直接渡した親の誤りに帰属
  (f2 で外す)。`test_p3_b4_wiring_probe.py` の 1 件は親 docs 未 commit の作業ツリー dirty に帰属 (docs commit `3934e2921` 後の f2 で再確認)。
- 段 6 レビュー (02:32〜02:36、逐語 `verbatim/s6-reviewA.md` / `s6-reviewB.md`): A (正しさ境界) は RA-1〜RA-8、B (過剰・削除) は RB-1〜RB-10。両方 NO-GO だが実装の must-fix は無し。
  must-fix = (1) `DW-O28` 本文に「撤去前の拒否に限る」「HEAD が main 祖先なら bundle 省略」「manifest 現行 branch」の 3 限定 → v3 994 bytes (commit `cdc5ddb59`)、
  (2) 変異評価の再照準 (M7/create は後続の directory 読込みに mask、M8 は診断 pin、削除失敗の fail-open は 4 層が独立に守るので累積 4 置換 M8b)、
  (3) decisions 対応表 (D2163 の履歴 pack 却下、D2042 の引用) と母集団表現 (「残る 155 本」を書かない)。RB-2: bundle の実行順は段 4 案 (撤去後) より
  安全側の backup phase (撤去前、退避失敗時は木・admin・branch を保持) に変わった — 記録に明記。裁定は `verbatim/s4-adjudication.md` §6。
  nit (実装しない): 診断解析失敗時の実体 test、旧 receipt 正例と bundle 改変拒否 test、ref 文法検査の重複、`deleted_branch_tip` の重複、未使用変数。
- T-2814 land (03:19、main `e07c220a0`、peer の landed 通知は再読の契機) を非 ff merge `5ae40acbc` で取り込み。land 版 `cleanup-branches.md` (6,201 bytes) を base に
  親が §0/§2/§3/§5 を改訂 (7,055 bytes、sha256 `3d675f09…`、docs commit `5e3d8f3b8`)。author B (Codex、`.codex/worktrees/branch-residue-author-b`、
  03:25〜03:27) が `check_docs.py` の `CLEANUP_COMMAND_SHA256` / 予算 / `DEV_WAVE_DW_O28_SECTION_LITERAL` と `test_check_docs.py` の fixture・literal・len・padding を
  追随 (統合 commit `f0a214661`) → 焦点走 f3 (03:32) 2436 passed / 2 failed = 追随漏れ 2 件 (`o28_contract_weakened` の fixture 変異 anchor が旧文言、予算余白 0 で
  1 byte 追加負例が SHA + 予算の 2 件違反) → fix1 (anchor 追随、予算 7,058 = 余白 3、統合 commit `1972bd33f`) → f4 (03:57) = **2438 passed / 10 skipped / 0 failed**。
  親の `check_docs.py` 実走 rc 0。SKILL.md は変えない (段 4 B-10)。

## 5. 変異 matrix (DW-M01〜M08)

### 5a. tool 系 (runner = `test_dev_wave_cleanup.py`)

| 変異 | 分類 | 何を変えると | 期待 | 結果 | 落ちた node 数 (代表) | 備考 |
|---|---|---|---|---|---|---|
| m0-control-docstring-only | 対照 | docstring の 1 文に「(対照)」 | SURVIVED | SURVIVED | 0 (—) | 等価変異、harness の SURVIVED 検出の正例 |
| m1-child-delete-uses-lowercase-d | 正例 | 子専用 -D を -d へ | KILLED | KILLED | 7 (test_remove_child_already_clean_with_receipt ほか 6) | 非祖先の子は -d が拒否され rc=30 |
| m2-child-delete-call-skipped | 正例 | 子 branch 削除の呼出しを省略 | KILLED | KILLED | 9 (test_remove_child_archives_dirty_integrated_author_and_deletes_branch ほか 8) | ref 不在 assertion が落ちる |
| m3-history-bundle-skipped | 正例 | 履歴 bundle の作成を省略 | KILLED | KILLED | 3 (test_remove_child_archives_dirty_integrated_author_and_deletes_branch ほか 2) | 正例の bundle 実在検査と verify 失敗 fixture が注入点に到達しない |
| m4-integration-rejection-disabled | 負例 | integration 不一致の拒否を無効化 | KILLED | KILLED | 2 (test_remove_child_rejects_unintegrated_author_commit ほか 1) | 未統合の子が受理される |
| m5-wave-delete-uses-force | 負例 | wave 本体の削除を -D へ | KILLED | KILLED | 27 (test_forbidden_git_verbs_absent_from_source_calls_and_runtime_allowlist ほか 26) | 共通 runner が -D を拒否し wave 経路が全て失敗 = 正常受理の縮小の検出 (安全境界の突破証明ではない) |
| m6-common-runner-accepts-force | 負例 | 共通 runner の -D 拒否を除去 | KILLED | KILLED | 1 (test_common_git_runner_rejects_force_delete) | 共通 runner の実効 gate |
| m7-bundle-failure-ignored | 負例 | bundle create/verify の失敗を無視 | KILLED | KILLED | 1 (test_remove_child_bundle_verify_failure_is_partial[verify]) | [verify] が主証拠。[create] は後続の directory 読込み失敗に mask され証拠から外す |
| m8-branch-delete-phase-mislabeled | 診断 pin | branch 削除 phase 名を postcondition へ | KILLED | KILLED | 1 (test_remove_child_branch_delete_failure_is_partial) | diagnostic sensitivity pin (kill 数に入れない) |
| m9-receipt-reappearance-check-removed | 負例 | receipt 再実行時の branch 再出現検査を除去 | KILLED | KILLED | 1 (test_remove_child_receipt_rejects_recreated_branch) | 再出現 branch が already-clean に流れる |
| m8b-branch-delete-fail-open-cumulative | 負例 (累積 4 置換) | 削除 rc 無視 + 診断 malformed 無視 + sha 照合無視 + 不在確認無視 | KILLED | KILLED | 1 (test_remove_child_branch_delete_failure_is_partial) | 4 層が独立に守るため単独置換では殺されない (RB-6)。DW-M04 の累積適用 |

final: baseline PASSED (27.004 秒/run、201 passed)、KILLED 10 / SURVIVED 1 / MISMATCH 0 (期待 node 完全一致 11/11)。repo_head `cdc5ddb59`、spec sha256 `f60590a1e030…`、runner = `tools/run_tests.py orchestrator/tests/test_dev_wave_cleanup.py -q -rf --force-dispatch` (dispatch)。probe (M0〜M9、02:33〜02:45、head `c82f42da7`) と probe2 (M8b、02:46〜02:48) で観測した node を final に固定。kill に数えるのは M1〜M7・M9・M8b の 9 件、M8 は診断 pin。

### 5b. 文書 pin 系 (runner = `test_check_docs.py`、head `1972bd33f`)

| 変異 | 何を変えると | 結果 | 落ちた node 数 | 備考 |
|---|---|---|---|---|
| m0d-control-comment-line | `check_docs.py` に動作に影響しない comment 1 行 | SURVIVED | 0 | 対照 |
| m10-dw-o28-literal-one-byte | `DEV_WAVE_DW_O28_SECTION_LITERAL` の ASCII 1 byte (`-d` → `-D`) | KILLED | 337 (期待完全一致) | exact pin が崩れ、合成 fixture 依存の positive control test が連鎖して赤 (T-1458 と同型) |
| m10b-cleanup-command-sha-one-hex | `CLEANUP_COMMAND_SHA256` の先頭 1 hex | KILLED | 321 (期待完全一致) | 同上 |

probe (04:01〜04:04) で観測 → final (04:05〜04:08) KILLED 2 / SURVIVED 1 / MISMATCH 0。docs 側 (command / DW-O28) の 1 byte 変異は harness の hold で殺せない型なので、親が DW-O19 の手動 probe (§6) で check_docs の赤を確認した。

## 6. 検査・受入

- 焦点走 (計算ノード dispatch、`tools/run_tests.py … --force-dispatch`): f1 (02:02、tip `82b36fb64`) rc 1 = cleanup test 10 node 同根 + 契約 module 混入の setup error 33 + docs dirty 1 →
  f2 (02:29、tip `c6638054b`) **1011 passed / 5 skipped / 0 failed** → f3 (03:32、tip `f0a214661`、test_check_docs 等 3 file を追加) 2436 passed / 2 failed
  (author B の追随漏れ 2) → f4 (03:57、tip `1972bd33f`) **2438 passed / 10 skipped / 0 failed**。
- 親の `python3 tools/check_docs.py`: DW-O28 置換直後は exact pin 1 件だけ赤 (想定)、author B 統合後 rc 0、fix1 後 rc 0、fragment 追加後 rc 0。`spool_fold.py --dry-run` planned
  (予定採番 D2197 / F1036 / T-2828 / T-2829、確定は land)。
- 手動 probe (DW-O19、login): command 1 byte 置換 → check_docs rc 1 (SHA 不一致 1 件のみ)、DW-O28 1 byte 置換 → rc 1 (exact 契約不一致 1 件のみ)、復元後 clean・rc 0。
- 全史 provenance 監査: 各 commit 後 rc 0 (段 7 前の最終 = 12,220 件、新規違反なし)。三軸語走査 (`s8b_holdout_freeze search`) の hit は main 既存の 4 file だけ。
- 変異 JSON は job dir (`mutation-final.json` sha256 `a7b6eb59…` 485,863 bytes、`mutation-doc-final.json` sha256 `ab205711…` 1,781,965 bytes)。artifact.stdout を含み大きいので
  repo へは要約 (§5 と `verbatim/mutation-ledger.md`) だけを置く。
- 受入全走は段 7・8 の commit 後の最終 tip に land 前に 1 回投入し、受領証は job dir (`acceptance-receipt-*.json`) と land の記録が持つ (件数は本文へ書かない)。

## 7. 裁定パッケージ候補 (本 wave では実装しない)

- 同木で切り替えた旧 fix branch を manifest に記録して段 9 で消す (B-1) → 次の一手 `{{T:child-manifest-retired-branches}}`。
- 監査のみ 21 件 (2026-08-23〜09-09) の救出 / 受容の個別 triage (台帳転記は本 wave、pending のまま)。
- 台帳 248 件の pending の解決 (`accepted-loss` は人間の明示受容が要る)。

## 8. 言わないこと

- 段 9 改訂で残骸が「溜まらなくなった」とは言わない (証明不能な子、同木の旧 fix branch、中断 wave、dev-wave 外の branch は経路 2 の回収対象。被覆割合は未確定)。
- 「40 wave 分」「1 wave 2〜8 本」「39 本は内容まで同一」は名前からの概算。除外 24 本の内訳は稼働 11 / locked 7 / HEAD 1h 以内 1 / 棚卸し後の新規 5。
- 監査非通知 161 件が main に着地したとは言わない。bundle は Git object を延命しない。

## 9. 工数

codex 10 本 (plan 1・consult 2・author 2 (A / B)・fix 3 (A fix1・A fix2・B fix1)・review 2、gpt-6-astra / medium)。計算ノード job = 焦点走 4 + 変異 33 run
(tool 系 probe 11 / probe2 2 / final 12、文書系 probe 4 / final 4) + 受入。login = 台帳照合 2 (5.7 秒 / 10.4 秒)、fsck 1 (4 秒)、台帳生成 31 秒、手動 probe 2、check_docs 6 回。
wave 開始 00:59 JST、段 7 記録 04:15 JST 頃。

## verbatim の可逆最小正規化 (DW-S07)

- `verbatim/s6-reviewA.md`: 原文 (job dir `s6-reviewA.md`、sha256 `f0b7dccbb63e30180bc3c8b201b9005977643361ecd43e1018a0ef65b28d39cd`、10541 bytes) の行末 space (markdown の改行記法、7 行、各 2 byte) を除去した
  (10527 bytes)。可視文字は不変。復元は該当 7 行 (「**影響**：」で始まる行) の行末に 2 space を戻す。他の verbatim は原文のまま。
