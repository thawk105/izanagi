# [T-2814] /cleanup-branches §2・§3 に F1034 の 2 命令 (未追跡 output/ の原本確認、退避 tar の -C 順と非 dir entry 数の検算) と同日 cleanup session の罠 (削除直前の非施錠再確認) を足し、Codex overlay と whole-file SHA pin を追随させた — 予算 6,204 は上げず 6,201 bytes に収容、[T-2601] は対象 2 本の不在を実測して閉鎖

`authority: none` / `default_effect: no-state-change`

**種別:** docs (`.claude/commands/cleanup-branches.md`、`.agents/skills/cleanup-branches/SKILL.md`、親 author) + 実装面 (`tools/check_docs.py` の whole-file SHA 定数 2 個と
`orchestrator/tests/test_check_docs.py` の byte literal fixture・sha・bytes assert、Codex author 1 + fix 子 4 巡 (本文修正 3 回、受理 2、最終巡は監査)) + 記録 (本 insight、worklog fragment、failures fragment)。
**新規測定はゼロ。** 正しさゲート (verifier) には触れない。

- 日付: 2026-09-21 (JST)
- wave: `dev-wave-t2814-cleanup-command`、branch `worktree-dev-wave-t2814-cleanup-command`、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/` (repo 外)
- 起点 local main: `285477c0052819e272e390d798f6442658075866` (fresh worktree、開始 gate rc=0 00:45:42 JST = `verbatim/startup-gate.log`)
- 依頼: `verbatim/T-2814-origin.md` (ユーザー、dev-wave 引数の逐語 + T-2814 / T-2601 の carry 原文 + D2044 項 17)。裁定 = D2044 項 17 (T-2601)、D782 (予算収容の手順の委任)、
  F1034 恒久対応 (command 反映は T-2814 で別 wave)。実装面 = D95 (Codex author)。
- 一次資料 (事故): `output/insights/2026-09-20/cleanup-backup-loss-record/README.md` (entry 1759、F1034)。

## 0. この wave が主張すること・しないこと

**主張する。**

1. **`/cleanup-branches` §2 に (a) 未追跡 `output/` (`exploration/`・`env/`) の原本確認 (該当 wave の insight「証拠の所在」節で repo 外原本なら候補にせず残置・報告)、§3 に (b) §5 で引き渡す
   dirty 撤去 script の退避検算 (tar の `-C <worktree>` を `-T` の前、`ls-files -o` の list 数を tar の非 dir entry 数が下回れば撤去しない) を足し、§2 高い条件に同日 cleanup session
   の罠 (削除直前に status 空と非施錠を再確認) を足した。本文は 6,201/6,204 bytes (最長行 105/110 文字)。上限は上げていない。** §2。
2. **Codex overlay `SKILL.md` に同じ 2 点 (command §2 の原本確認を経るまで foreign/unknown と同じく保持、command §3 の退避検算 (非 dir entry 数照合) を欠く撤去手順を人間へ渡さない) を
   足した (3,060/3,100 bytes)。** overlay は command 本文を不可分に適用するので、command の命令は Codex にも効く。§2。
3. **exact pin の 3 者 (本文 / `tools/check_docs.py` の sha 定数 / `test_check_docs.py` の fixture literal + sha + bytes assert) は一致 (command 6,201 bytes、sha `c8db749b…`、
   SKILL 3,060 bytes、sha `3cf0344d…`)。check_docs 違反なし、全史 provenance 12188 件違反なし。** §3。
4. **予算ちょうど (余白 0) は既存 test と衝突する: `test_cleanup_command_leading_space_h2_is_rejected` が byte-neutral helper を使わず先頭に空白 1 byte を足すため、予算超過が
   2 件目の違反になり期待件数 1 が崩れる (Codex fix 子 2 巡目が実測して停止)。余白 3 bytes (6,201) は段 5 author の 580 passed で実績がある。** §3・§4。
5. **段 6 レビュー (read-only 1 本) は NO-GO (must-fix 1: §3 の検算文が一次資料と受理集合が異なる) → fix 1 で一次資料の条件へ訂正。焦点再レビュー (fix 1〜3) は GO (所見 1・2 closed、記録面 nit 2 → 訂正済み)。** §4。
6. **変異 matrix (anchor = fix 統合 6dae18be1): baseline PASSED (37.3 s)、KILLED 4/4 (期待 node 完全一致 321 / 335 / 1 / 1)、等価 1 SURVIVED、MISMATCH 0、TIMEOUT 0。** §5。
7. **焦点走 19 file: f1 (統合 C、untracked fragment あり) 3869 passed / 16 skipped / 1 failed (赤は untracked の spool fragment を検出する inventory test = 親の手順起因)、
   f2 (記録 commit 後、同 19 file) は記録 commit の後に走らせ、結果は追記 commit で本 README §6 と worklog fragment に書く (この時点では未実施)。** §6。
8. **[T-2601] は対象 2 本 (`dev-wave-t1875-delta-min-gate` / `dev-wave-t2267-exec-site-class`) が `git worktree list` (38 本)・`git branch --list`・`.git/worktrees/` admin・
   `.claude/worktrees/` と `dev-wave-jobs/` の directory・`docs/unreachable-object-ledger.md` のいずれにも無い (00:4x JST 実測) ので閉鎖 (`完了`)。** §7。

**主張しない。**

- 引き渡し script の退避検算を機械強制する gate・tool は足していない (scope 外、command 本文の命令のみ)。「非施錠」の判定手段 (`git worktree list` の locked 表示 / admin dir の
  `locked` file) は本文に書いていない (余白なし、§2 安い条件「locked … は inventory/report のみ」と同じ流儀)。
- T-2601 対象の撤去者・日時は不明のまま (worklog 現行 + archive・`cleanup-20260920/inventory/`・git 履歴に記録なし。推測しない)。過去の撤去が D2044 項 17 に従ったことの証明ではない。
- 削減 11 件が「すべて意味不変」とは言わない: R6 (§3 ExitWorktree 文の「`git log` で確認」→「確認」) は確認義務を保持しつつ手段指定を落とした (別手段の確認も許す。段 6 nit)。
- 焦点走の緑・変異の KILLED は受入全走を代替しない。受入の結果は本 README に書かず、受領証 (job dir `acceptance-receipt-*.json`) と land の記録が持つ。
- 依頼の「docs のみ」「SKILL.md は codex 側の写し」は段 1 の実測で更新した (§1)。依頼の (a)(b) と「稼働中 session の final の罠」は全部入った。

## 1. 段 1 で更新した依頼の前提 (`verbatim/brief.md`)

- **「docs のみ」は成立しない:** `tools/check_docs.py` が両 file を whole-file SHA-256 で pin (`CLEANUP_COMMAND_SHA256` / `CODEX_CLEANUP_BRANCHES_SKILL_SHA256`)、
  `orchestrator/tests/test_check_docs.py` が本文の byte literal 全文 (`_SYNTHETIC_CLEANUP_COMMAND` / `_SYNTHETIC_CLEANUP_SKILL`)・sha・`len == 6_181` を pin。追随は Codex author
  (先例 T-2813 と同型)。gate・検査の新設なし (DW-O13 不成立)。
- **SKILL.md は「写し」でなく overlay:** command を全文読み不可分に適用し Codex 固有の縮退を重ねる。overlay には Codex 固有の縮退 2 項だけ足した。
- **command 本文に「退避」の概念は無かった:** command 自身は §2 で status 空の worktree だけ撤去し、dirty は §5 で引き渡す。F1034 は引き渡し script (repo 外) で起きたので、(b) は
  §3 に「§5 で引き渡す dirty 撤去 script も本節に従い、退避を撤去の前提にする」の形で書いた。`tools/cleanup_remove_dirs.py` は退避を作らない (docstring 実測)。
- 既存被覆: decisions / failures / dev-wave docs / commands に「退避 tar の検算」「証拠の所在で原本判定」の命令は無い (F1034 の恒久対応が本 wave を名指すのみ)。純増。
- 段構成 (DW-C00): 軽量版 — 一次資料から事実を抽出する docs + 機械的な pin 追随 → 段 2・3 省略、段 5 Codex author 1、段 6 read-only review 1 + fix + 焦点再レビュー 1 + 変異 + 焦点走。

## 2. 本文の変更 (`verbatim/reduction-table.md` = 追加 A1〜A3・削減 R1〜R11 の逐語対応表、`verbatim/cleanup-branches.old.md` / `SKILL.old.md` = 旧本文)

- 追加: A1 (§2、未追跡 `output/` の原本確認、F1034)、A2 (§3、退避検算、F1034。fix 1 で「list と entry 数が一致」→「list 数を tar の非 dir entry 数が下回れば撤去しない」)、
  A3 (§2 高い条件、fix 2、「削除直前に status 空と非施錠を再確認」— 同日 00:20〜00:36 JST の `/cleanup-branches` 実行中に /rulings session が submit-tree-pair を lock した罠。
  memory `cleanup-discipline` 2026-09-21 節。待ってはいない: 依頼の「final が返す罠があれば反映」)。
- 削減 (D782 手順 1 段目のみ、2 段目・3 段目に進まず): 意味不変の縮約 10 件 (R1 argument-hint、R2 §0「commit」「後から」、R3 §0 末尾段落 = §2 見出しと高い条件が同義、
  R4 §1「rebase/cherry-pick 後も ahead>0」、R5 §3「(取り込み済み確認の上)」= §2 ahead=0、R7 §3 背景セッションの括弧書き、R8 §4 submodule 行、R9 §5 push command 例、
  R10 §4「cleanup 前の status を保存し」→「§1 の status と比べ」(fix 1)、R11 §5 助詞 1 語 (fix 3)) + 手段指定の削除 1 件 (R6)。
- 保持した check_docs の構造 literal: §3 冒頭 2 行 (exact)、「正本は `docs/failures.md` F26。」の共起行、`docs/skill-self-improvement.md` 到達行、`$ARGUMENTS` 1 件、
  frontmatter key 集合、`discard_changes: true` 1 回 (test の byte-neutral slack)。
- bytes の推移: 6,181 → 6,201 (docs f6a530523) → 6,200 (fix 1 82c53b98d) → 6,204 (fix 2 b36da2b09、余白 0 で test 衝突) → 6,201 (fix 3 8901d6b62、最終)。SKILL 2,646 → 3,052 → 3,060。

## 3. pin 追随 (Codex author + fix 子、`verbatim/s5-author*.md`、`verbatim/s6-fix*.md`)

- 順序は先例 T-2813 と同じ: 親 docs commit → Codex author (unit worktree `.codex/worktrees/t2814-unit-impl`、所有 path = `tools/check_docs.py` + `orchestrator/tests/test_check_docs.py`)
  → 所有 path 限定 patch を親が適用 → 統合 commit。
- commit 列: docs `f6a530523` → 統合 `92263e53e` (author、+25/−20) → docs fix 1 `82c53b98d` → 統合 A `47e1730b7` (fix 1 巡目、+10/−10) → docs fix 2 `b36da2b09` → docs fix 3
  `8901d6b62` → 統合 C `6dae18be1` (fix 3 巡目の差分、4 巡目が監査、+7/−7)。
- fix 子の経過: 1 巡目 受理 (580 passed / 3 skipped)。2 巡目 (本文 6,204) は余白 0 の test 衝突で指示どおり停止 (終端 7907abd8b は不採用、報告は launcher 未受理 =
  `verbatim/s6-fix2.unaccepted.md`)。3 巡目 (本文 6,201) は差分を作り 580 passed だったが `test_check_docs.py` の非 NFC fixture 行 (5749・5772、**F728 の再発**) を cat したため
  launcher が未受理 (`verbatim/s6-fix3.unaccepted.md`、終端 d258b0597)。4 巡目 (行番号回避を明記) が同差分を監査して一致・変更 0・580 passed / 3 skipped・check_docs 違反なし
  (`verbatim/s6-fix4.md`、受理) → 親が d258b0597 の差分を統合 C に適用。
- 合成 fixture の F / path placeholder は不要だった (新本文の F1034 参照は command file が腐敗検査対象外、prefix 付き path なし)。

## 4. 段 6 レビュー (`verbatim/s6-review-prompt.md` / `s6-review.md`、裁定 `verbatim/s6-adjudication.md`、再レビュー `verbatim/s6-rereview-prompt.md` / `s6-rereview.md`)

- 初回 (read-only 1 本、4 レンズ): **NO-GO**。所見 1 (must-fix、real): §3「list と entry 数が一致」は一次資料 §4「tar の非 dir entry 数が list 数を下回れば撤去せず」と受理集合が
  異なる (dir entry を数えると総数一致で不足を見逃し、逆に正常な退避を誤停止)。親の対応表 A2 の判定誤り (反証を採用)。所見 2 (nit、real): R6 は手段指定の削除で「意味不変」は過大
  → 記録で対応。pin 整合ゼロ、scope 逸脱ゼロ、T-2601 閉鎖に反証なし。
- 焦点再レビュー (fix 1〜3、所見 closed/partial/regressed 表): **GO**。所見 1 closed (非 dir entry 数 N < list 数 L で停止、N=L・N>L は拒否せず一次資料 §4 と一致)、所見 2 closed。
  fix 2 妥当 (棚卸し後の lock を見落とす経路を塞ぐ、安い条件の locked 除外と時点が違い矛盾なし)、fix 3・R10 意味不変、退行なし、余白 0 の新事実は整合。新規 nit 2 (記録面のみ):
  (1) 巡数の混在 → 「本文修正 3 回、Codex fix 子 4 巡 (最終巡は監査)」に訂正、(2) byte 算術 (fix 1 = §3 +9 / §4 −10 / overlay +8・余白 40) と削減件数 (11 件) を訂正。

## 5. 変異 matrix (事前登録 = 段 4 → probe → final、`verbatim/mutation-spec-{probe,final}.json`、`verbatim/mutation-{probe,final}-summary.json`)

- harness: `tools/mutation_worktree.py` (独立 clone `mutation-source` = D1009)、runner `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_check_docs.py -q -rf`、
  `--runner-mode dispatch --detached`。probe (anchor = 初回統合 92263e53e) は全件 SURVIVED 期待で観測 node を収集、final (anchor = fix 統合 6dae18be1、DW-M07) は観測 node を
  KILLED 期待に登録。出力 JSON は 1.6 MB のため sha256 束縛の要約を写した。
- probe: baseline PASSED 37.4 s、m0 SURVIVED、m1 321 node、m2 335 node、m3 1 node、m4 1 node (設計どおり MISMATCH)。
- final (`spec d3acd1bc…`、`repo_head 6dae18be1`、rc 0): **baseline PASSED (37.3 s)、KILLED 4 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0、期待 node 完全一致 5/5。**

  | ID | 位置 | 変異 | 期待 | 赤 node (1 理由) |
  |---|---|---|---|---|
  | m0 | `check_docs.py` comment 1 行 | 等価 (comment 追記) | SURVIVED | 0 |
  | m1 | `check_docs.py` `CLEANUP_COMMAND_SHA256` | 旧 sha へ | KILLED | 321 = 定数 ≠ fixture / 現物 (合成 repo で check_docs が赤になる test 群 + pin test) |
  | m2 | `check_docs.py` `CODEX_CLEANUP_BRANCHES_SKILL_SHA256` | 旧 sha へ | KILLED | 335 (m1 と 14 差: command 側 mutation test は helper で digest を再束縛するため m1 では救われる) |
  | m3 | `test_check_docs.py` `_EXPECTED_CLEANUP_COMMAND_SHA256` | 旧 sha へ | KILLED | 1 = `test_codex_cleanup_branches_skill_contract_pins_exact_surface` |
  | m4 | `test_check_docs.py` bytes assert | `6_201` → `6_181` | KILLED | 1 = `test_cleanup_command_budget_is_pinned_and_enforced` |

- docs 側の変異 (本文 +1 byte) は harness に載せない: 実 repo 正例 test 3 件は growth hold で skip のため pytest では殺せない (先例 T-2813 と同じ)。本 wave では fix 2 巡目の
  「本文 6,204 で合成 repo の check_docs が予算超過 + SHA 不一致」が同型の実測になっている (§0 主張 4)。

## 6. 焦点走・検査 (受入は本 README に書かない)

- 焦点走 f1 (`verbatim/focus-1.log`、request 14114.nqsv、runner 76.52 秒、tip 6dae18be1 + untracked fragment): 19 file = `test_check_docs.py` (変更 test) + `tools/check_docs.py` を参照する
  consumer 14 file (`git grep -l check_docs orchestrator/tests/`) + inventory 4 群 (DW-O26) → 3869 passed / 16 skipped / **1 failed**
  (`test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` = 作業ツリーの untracked `docs/spool/failures/…-2.md` を検出。本 wave の実装差分でなく
  記録 fragment を untracked のまま投入した親の手順起因。DW-O18 の「自分起因は直す」)。
- 焦点走 f2 (`verbatim/focus-2.log`、記録 commit 後、同 19 file): 未実施 (記録 commit の後に投入し、結果は追記 commit で書く)。
- `python3 tools/check_docs.py` 違反なし (統合 C 後、記録 commit 前)、`git diff --check` rc=0、provenance 全史 rc=0 (docs 12182 → 統合 12183 → fix 統合 12188 件)。
- 三軸語走査・placeholder 走査・spool dry-run は記録 commit 前に実施し、結果は worklog fragment に書く。
- 受入全走は DW-O12 に従い記録 commit + 段 8 の後に `tools/dev_wave_wait.py acceptance` で投入する。child-green でなければ land しない。

## 7. T-2601 の閉鎖 (`verbatim/T-2814-origin.md` の carry 原文と D2044 項 17)

- 裁定 (D2044 項 17): `dev-wave-t1875-delta-min-gate` を撤去、`dev-wave-t2267-exec-site-class` は施錠を尊重して残す。
- 実測 (2026-09-21 00:4x JST): 両方とも `git worktree list` (38 本)・`git branch --list`・`.git/worktrees/` admin dir・`.claude/worktrees/`・`dev-wave-jobs/` の directory・
  `docs/unreachable-object-ledger.md` に無い。撤去の実行記録 (実行者・日時) は worklog 現行 + archive (`grep -rn t1875-delta-min-gate`)・`cleanup-20260920/inventory/`・
  `git log --all --grep` に無い。→ 実行対象が無いので `完了` (remaining: none)。

## 8. 言ってよいこと・言ってはいけないこと・次の一手

- 言ってよい: §0 の「主張する」。言ってはいけない: §0 の「主張しない」。
- 裁定パッケージ候補: なし (上限を動かさず収容できた。scope 外 real 所見なし)。
- 設計メモ (scope 外、実装しない): command 本文は 6,201/6,204 で追記余地 3 bytes。次に同 file へ足す wave は D782 手順を最初からやり直し、余白 0 にはできない (§0 主張 4)。
- F728 の再発 2 回 (fix 子 2・3 巡目) は failures fragment で `再発` 追記、恒久対処 [T-2041] は見送り台帳のまま (回避で通り研究実走の blocker ではない → 見送り追記のみ)。

## 9. 一次資料 (`verbatim/`)

`T-2814-origin.md`、`brief.md`、`startup-gate.log`、`s4-adjudication.md`、`reduction-table.md`、`cleanup-branches.old.md`、`SKILL.old.md`、`s5-author-prompt.md`、`s5-author.md`、
`s6-review-prompt.md`、`s6-review.md`、`s6-adjudication.md`、`s6-fix1-prompt.md`、`s6-fix1.md`、`s6-fix2-prompt.md`、`s6-fix2.unaccepted.md`、`s6-fix3-prompt.md`、`s6-fix3.unaccepted.md`、
`s6-fix4-prompt.md`、`s6-fix4.md`、`s6-rereview-prompt.md`、`s6-rereview.md`、`mutation-spec-probe.json`、`mutation-spec-final.json`、`mutation-probe-summary.json`、
`mutation-final-summary.json`、`focus-1.log` (末尾空白の可逆正規化 = `NORMALIZATION.md`。`focus-2.log` は f2 の追記 commit で置く)。
