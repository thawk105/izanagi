# [T-2813] DW-O26 に「production file を変えた wave は inventory test 4 群を参照関係に依らず焦点走に含める」の 1 句を足し、exact pin を 998/1000 bytes の新本文へ追随させた (T-2292 の契約側更新を同じ変更単位で閉じた)

`authority: none` / `default_effect: no-state-change`

**種別:** docs (`docs/dev-wave/operations.md` DW-O26 節、親 author) + 実装面 (`tools/check_docs.py` の literal と `orchestrator/tests/test_check_docs.py` の
合成 fixture、Codex author 1 本) + 記録 (本 insight、worklog fragment)。**新規測定はゼロ。** 正しさゲート (verifier) には触れない。

- 日付: 2026-09-20 (JST)
- wave: `dev-wave-t2813-o26-inventory`、branch `worktree-dev-wave-t2813-o26-inventory`、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/` (repo 外)
- 起点 local main: `f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad` (fresh worktree、開始 gate rc=0 = `verbatim/startup-gate.log`)
- 依頼: `verbatim/T-2813-origin.md` (ユーザー、dev-wave 引数の逐語)。裁定 = D2186 項 5 (採用、`verbatim/D2186-item5.md`)。予算処理の委任 = D782 / D961。
  実装面 = D95 (Codex author)。T-2292 (`verbatim/T-2292-origin.md`、entry 1238 起点) の「契約側更新はセットで行う」を同じ変更単位で閉じる。
- 実害の一次資料: `output/insights/2026-09-20/t2795-pair-launcher/README.md` §6〜§7 (焦点走 15 file 緑 → 受入で inventory 2 件赤、往復 1 + fix 3 巡)。

## 0. この wave が主張すること・しないこと

**主張する。**

1. **DW-O26 に D2186 項 5 の 1 句が入り、節は 998 bytes (単節予算 1000 以内)。上限は上げていない。** 旧 979 bytes + 新句 331 bytes を D782 / D961 の
   手順 1 段目 (既存記述の削減) で収容した。2 段目 (独立 3 例) と 3 段目 (最小増分) には進んでいない。§2。
2. **削減で落としたのは根拠説明 4 件だけで、6 義務 (参照関係で引く / private symbol を symbol 名で production を grep / 同一 worktree の dispatch 全種直列 /
   変更 test file の受入前単独走 / 新規 test file のメタテスト収載 / 並行 wave の相乗り・受入後に足さない) と F242 参照は保持。** 義務文の短縮 5 件は条件・対象を
   変えない (段 6 レビューが独立に文単位で対応づけ、GO)。§2・§4。
3. **exact pin の 3 者 (docs 本文 / `DEV_WAVE_DW_O26_SECTION_LITERAL` / `_SYNTHETIC_DW_O26_SECTION`) は byte 一致 (998、NFC、末尾 LF 1)。bytes assert は 979 → 998。
   旧本文の 1 文を削る M8 変異 case の削除対象を新文へ追随。`o26_contract_weakened` の attack 文字列は 1 行内に 1 回のまま不変。** §3。
4. **変異 matrix: baseline PASSED、負例 3/3 KILLED (期待 node 完全一致 336 / 1 / 336)、等価 1 SURVIVED、MISMATCH 0。docs 側の変異 (M4') は親の手動 probe で
   check_docs が exact 不一致 1 件で赤。** §5。
5. **焦点走 19 file (変更 test 1 + `tools/check_docs.py` の consumer 14 + inventory 4 群 = 新 DW-O26 を本 wave 自身に適用) は 3832 passed / 16 skipped / 0 failed。** §6。

**主張しない。**

- **T-2292 の起点 entry 1238 が挙げた「process 起動一覧」と「subprocess guard」の型が 4 群で被覆された、とは言わない。** `test_ccbench_spawn_sites.py` と
  `test_check_subprocess_bytecode_guard.py` は D2186 項 5 の 4 群に含まれない (段 6 レビュー nit 1、§4)。裁定「この 1 句だけ、他の gate・検査を足さない」に従い
  実装せず、§7 に裁定パッケージ候補として置く。T-2292 の「DW-O26 の契約側更新はセットで行う」という義務そのものは本 wave で果たした。
- 裁定 D2186 項 5 の「fixture placeholder (DW-O25)」は本 wave では**不要だった** (新本文に新しい D / F 番号が無く、`orchestrator/tests/` prefix を落としたので
  合成 fixture の path 実在検査 (`PATH_REF`) にも掛からない)。手順として想定されたが発火しなかった (DW-O12: 実際に実行した手順を書く)。
- 焦点走の緑・変異の KILLED は受入全走を代替しない。受入の結果は本 README に書かず、受領証 (job dir `acceptance-receipt-*.json`) と land の記録が持つ。
- 新句は焦点走の**集合の規則**であり、受入全走が inventory 赤を捕まえる現状の機構を変えない (規律 2 は不変)。

## 1. 置いたもの

- `0bb4365a2` — 親 docs commit: DW-O26 節を新本文 (998 bytes) へ置換。この時点で `check_docs` は「節全体が exact 契約と不一致」1 件だけの赤 (期待どおり、`verbatim/`
  には写していない。job dir `check_docs-after-docs-edit.log`)。
- `c805a53a7` — 統合 commit (Codex author + 親 integrator): `tools/check_docs.py` (+8/−8)、`orchestrator/tests/test_check_docs.py` (+10/−11)。unit worktree
  `.codex/worktrees/t2813-unit-impl` (branch `dev-wave-t2813-unit-impl`、base `0bb4365a2`、終端 commit `93604a077`) の所有 path 限定 patch を親が適用。
  `check_docs` 違反なし、`git diff --check` rc=0、provenance 全史 rc=0 (12062 件)。
- `15781341b` — 記録前に local main `eb6aa98de` を固定 SHA で取り込む merge (変更面 3 file は main 側で不変、gitlink `e9e477ca` は main と一致)。
- 本 insight (README + `verbatim/`) と worklog fragment `docs/spool/worklog/2026-09-20-dev-wave-t2813-o26-inventory-1.md` は記録 commit。
- 軽量版: 段 2・3 省略 (設計択一なし、正しさ防壁に触れない、受理集合は exact 述語の置換で 1 → 1)、段 6 = read-only レビュー 1 本 + 変異 + 焦点走 + 受入。

## 2. 裁定と収容 (段 1 brief = `verbatim/brief.md`、段 4 裁定 = `verbatim/s4-adjudication.md`)

- 実測 (段 1 前): DW-O26 は L2 (条件 18 のみ)、単節予算 1000、現 979 bytes。新句 (裁定文言そのまま) は 331 bytes → 1310 bytes で超過。
- 条件 dispatch: DW-O08 / O09 / O10 / O13 とも非成立 (freeze 族に触れない、写しは 3 箇所のみで launch authority は DW-O26 非対象、file 全体 bytes の pin なし、
  gate 新設なし・受理形は 1 → 1)。
- 新本文 = `verbatim/dw-o26-new-section.md` (998 bytes)。削減の内訳 (段 6 裁定 `verbatim/s6-adjudication.md` で訂正済みの分類):
  - (i) 根拠説明の削除 4 件: 「名前の推測でなく」/「この拡張を欠く焦点走は…初回実測でも取り逃す」→「欠くと…取り逃す」/「（全走緑は file 単独緑を含意しない）」/
    「並行投入は orphan hold で rc=16 になる」(DW-C00 が同文「並行はorphan holdでrc=16、`DW-O26`」を保持、全文複製の解消)。
  - (ii) 義務文の短縮 5 件: 「変更した」→「変更」×3 / 「受入全走前」→「受入前」/ 「production 全体を」→「production を」/ 「焦点走に含める」→「含める」
    (メタテスト文) / 「焦点走対象 file 集合」→「焦点走 file 集合」。いずれも義務の条件・対象を変えない。
  - 新句と裁定文言の差: `orchestrator/tests/` prefix を落とす (4 群は全て同 dir 直下、file 名は `git ls-files` で一意)、「wave は、」の読点、全角括弧。4 群の名指し
    (2 つの説明句を含む) と「参照関係に依らず焦点走に含める」は逐語。名指しの 2 test は実在 (`test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`、
    `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact`)。
- 前提の実測: 4 群の受入所要 (台帳 `acceptance_duration_ledger.json`) = 152 / 37 / 39 / 110 秒 (直列 338 秒) — 裁定の「軽い」は成立。独立 3 例の根拠
  (2 段目に進む場合用、未使用) = F42 再発 2026-09-07 / entry 1238 (4 件中 3 件) / T-2795 §6。
- 裁定 inbox (`rulings-inbox/2026-09-20-rulings-full26-verdicts.md`、mtime 19:50) の項 5 は D2186 と同文。wave 開始後の更新なし。

## 3. 段 5 実装 (Codex author、`verbatim/s5-author-prompt.md` → `verbatim/s5-author.md`)

- 所有 path: `tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`。docs は親が先に commit (`0bb4365a2`) し、unit worktree は docs が HEAD と一致した状態で起動
  (launch authority の HEAD 照合を満たす)。
- 変更: literal 本文の置換、独立 literal の fixture 置換、bytes assert 979 → 998、`test_non_attributable_landing_contract_mutations_have_one_finding[M8]` の削除対象を
  新文「変更 test file は受入前に単独走で確認する。」へ (削除後 939 bytes、exact 不一致だけが立つ)。旧本文断片への他の依存は無し (author・レビューが独立に探索)。
- author の実走 (login sandbox): 焦点集合 36 passed / 1 skipped、`test_check_docs.py` 全 583 件 580 passed / 3 skipped (実 repo 正例 3 件は growth hold `docs_bytes`)、
  meta-test 4 passed、`python3 tools/check_docs.py` 違反なし、`git diff --check` 問題なし。`check_codex_output.py` rc=0。

## 4. 段 6 レビュー (`verbatim/s6-review-prompt.md` → `verbatim/s6-review.md`、裁定 `verbatim/s6-adjudication.md`)

- read-only 1 本 (3 レンズ: A 義務の欠落と意味の変化 / B pin 整合 / C 過剰・削除)。**GO、must-fix 0 / nit 1。** `check_codex_output.py` rc=0。
- nit 1 (real、scope 外): 4 群は T-2292 起点の「process 起動一覧 / subprocess guard」型を含まない → §7 の裁定パッケージ候補へ。実装しない。
- 反証 (real、採用): 段 4 §2 の削減表「すべて根拠説明」は粗い — 3 件は義務文の短縮。義務が保持されている点は一致。§2 の分類 (i)/(ii) で訂正。
- レビューが独立に検算した事実: 3 者 998 bytes 一致、attack 文字列 1 行内 1 回、M8 削除後 939 bytes、DW-C00 の rc=16 参照は成立、旧断片への実行可能な依存なし、
  上限 1000 / exact 登録集合 / 他 pin 節 / L1・L1.5 不変、候補 1 件目 (provenance 監査 dispatch の直列化) の混入なし。
- fix 子: 不要。焦点再レビュー: 不要。

## 5. 変異 matrix (事前登録 = 段 4 §4 → probe → final、`verbatim/mutation-spec-{probe,final}.json`、`verbatim/mutation-{probe,final}-out.json`)

- harness: `tools/mutation_worktree.py` (独立 clone `mutation-source` = D1009、main = `c805a53a7`)、runner `python3 tools/run_tests.py --force-dispatch
  orchestrator/tests/test_check_docs.py -q -rf`、`--runner-mode dispatch --detached`。probe = 全件 SURVIVED 期待で観測 node を収集 (rc=1 は MISMATCH の設計どおり)、
  final = 観測 node を期待集合に登録 (`--wrapper-attempt 2`、新 out path)。出力 JSON は 1.7 MB のため sha256 束縛の要約 (`mutation-*-out.json`) を写した。
- final (`spec 30d3395e…`、`repo_head c805a53a7`): **baseline PASSED (37.8 s)、KILLED 3 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0、期待 node 完全一致 4/4。**

  | ID | 位置 | 変異 | 判定 | 赤 node (1 理由) |
  |---|---|---|---|---|
  | M0 | `check_docs.py` comment 1 行 | 等価 (comment 追記) | SURVIVED (期待どおり) | 0 |
  | M1 | `check_docs.py` literal | 「4 群」→「5 群」 | KILLED | 336 = literal ≠ docs 本文 / fixture (合成 repo で check_docs が赤になる全 test + literal 比較) |
  | M2 | `test_check_docs.py` bytes assert | `== 998` → `== 979` | KILLED | 1 = `test_normative_exact_section_contract_is_handwritten_and_complete` |
  | M3 | `test_check_docs.py` fixture | 末尾 1 文を削除 | KILLED | 336 (M1 と同一集合、変異位置は fixture 側) |
  | M4' | `docs/dev-wave/operations.md` DW-O26 | 「4 群」→「5 群」(bytes 不変) | KILLED (手動、`verbatim/mutation-m4-docs-manual.log`) | 実 repo `check_docs` rc=1、exact 不一致 1 件のみ (予算は 998 のまま) |

- M4' を harness に載せなかった理由: 実 repo 正例 test 3 件 (`test_real_repo_clean` 等) は growth hold `docs_bytes` 軸で受入から除外されており pytest では殺せない。
  DW-O19 (porcelain 空 → 注入 → 赤確認 → `git checkout --` 復元 → HEAD blob と sha256 照合) で親が 1 回実測した。
- 29 node は runner 中継のエスケープ表記 (`/uXXXX`) を含む既存 parametrize id で、観測形をそのまま登録して完全一致した (final で MISMATCH 0)。

## 6. 焦点走・検査 (受入は本 README に書かない)

- 焦点走 focus-1 (`verbatim/focus-1.log`、request 13595.nqsv、runner 報告 78.61 秒): 19 file = `test_check_docs.py` (変更 test) + `tools/check_docs.py` を参照する
  consumer 14 file (`git grep -l check_docs orchestrator/tests/`) + inventory 4 群 (新 DW-O26 の規則を本 wave に適用) → **3832 passed / 16 skipped / 0 failed**、rc=0。
- `python3 tools/check_docs.py` 違反なし (統合 commit 後・記録 commit 前)、`git diff --check` rc=0、provenance 全史監査 rc=0 (docs commit 後 12061 件、統合後 12062 件)。
- 三軸語走査・placeholder 走査・spool dry-run は記録 commit 前に実施し、結果は worklog fragment に書く。
- 受入全走は DW-O12 に従い記録 commit + 段 8 の後に `tools/dev_wave_wait.py acceptance` で投入する。child-green でなければ land しない。

## 7. 言ってよいこと・言ってはいけないこと・次の一手

- 言ってよい: §0 の「主張する」。言ってはいけない: §0 の「主張しない」。
- 裁定パッケージ候補 (実装せず、次回 /rulings が拾う): **T-2292 の残る型 = 「subprocess を起動する module を足すと process 起動一覧 (`test_ccbench_spawn_sites.py`) と
  subprocess guard (`test_check_subprocess_bytecode_guard.py`) も落ちる」(entry 1238 で 4 件中 3 件の実害)。** 択: (a) DW-O26 の inventory 4 群にこの 2 file を足す
  (D2186 項 5 の集合を広げる再裁定。節は 998/1000 でさらなる削減か上限増が要る) / (b) 据え置き (受入で捕まえる現状のまま、往復の費用を払う)。推奨は書かない
  (集合の拡張は D2186 項 5 の再裁定で、AI が決めない)。
- 設計メモ (scope 外、実装しない): DW-O26 は 998/1000 bytes で追記余地が 2 bytes。次に同節へ足す wave は D782 手順を最初からやり直す。
- 一次資料 §7 の候補 1 件目 (provenance 監査 dispatch の直列化 1 句) は本 wave で触っていない (裁定「この 1 句だけ」)。

## 8. 一次資料

- 依頼・brief・裁定: `verbatim/T-2813-origin.md`、`verbatim/brief.md`、`verbatim/s4-adjudication.md`、`verbatim/s6-adjudication.md`、`verbatim/D2186-item5.md`、
  `verbatim/T-2292-origin.md`、新本文 `verbatim/dw-o26-new-section.md`
- codex 入出力: `verbatim/s5-author{-prompt,}.md`、`verbatim/s6-review{-prompt,}.md`
- 走: `verbatim/startup-gate.log`、`verbatim/focus-1.log`、`verbatim/mutation-spec-{probe,final}.json`、`verbatim/mutation-{probe,final}-out.json`、
  `verbatim/mutation-m4-docs-manual.log`。行末空白・末尾空行の可逆正規化は `verbatim/NORMALIZATION.md`
- job dir (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/` (HANDOFF.md、launcher、patch、check_docs / provenance log、受入 log・受領証)
