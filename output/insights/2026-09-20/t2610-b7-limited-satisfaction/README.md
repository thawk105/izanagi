# [T-2610] B-7 (全 workload の退行込み報告) の限定付き充足 (D2174 項 3) を正典へ反映する — docs wave の開発記録

これは裁定 D2174 項 3 (2026-09-20、択 (a)) の**限定文言を腐らない入口へ写す docs-only の記録**である。
新しい測定、certification の昇格、有意差判定、反復 attempt の認可は行わない。実装面の差分はゼロ。
凍結物 (稿 `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md`、fig10 の 3 成果物と caption、
ストーリー版 `docs/paper-story/2026-09-20.md`、claim-evidence `docs/paper-story/claim-evidence/2026-09-20.md`) は 1 byte も変えない。

## 1. 段 1 brief (親、2026-09-20)

- **研究前進:** ストーリー版第 3 幕の「あと何が要るか」(§8 B 群) の B-7 が「材料あり・要件充足へは昇格しない (D2044 項 3)」から
  「限定付き充足 (D2174 項 3)」へ動いた。論文の結果節は B-7 の報告 (target で勝ち他 workload で床値超の退行がある候補を退行込みで全 workload 報告する)
  を「単一 attempt・descriptive・非認証・反復間安定性は未判定」の限定で書ける。完了判定 = (i) 腐らない入口 3 か所 (paper-story README の stale 注記 +
  results 系列表の行、figures README の一覧行 + fig10 節) に限定文言と supersede が入る、(ii) worklog の T-2610 が裁定済みで閉じる、
  (iii) fig10 着地 test・`check_docs`・焦点走・受入が緑。
- **scope:** docs 4 か所 + worklog fragment + 本 README。凍結版 (ストーリー版・claim-evidence 稿) は編集せず、次版の全面再導出で拾う (系列規則、D1858)。
- **確定済みユーザー裁定:** D2174 項 3 = 択 (a) 限定付き充足。D2044 項 3 (昇格させない) を supersede。(b) 反復 attempt は認可しない。certified 昇格・有意差判定・新規測定を含まない。
  限定の文言は稿・図の説明・ストーリー版の地図に写す (AI の手番)。
- **不変条件:** (1) 稿の SHA-256 `6585d446a07d798d87c352a1b41eb5b195ee70ba453976aa5ec0f46daef4b6f9` 不変 (fig10 provenance の `caption_source` 束縛、着地 test の `validate_repo_closure`)。
  (2) figures README fig10 節の caption 逐語と着地 SHA 3 行不変、節内に第一レベル見出し (`# `) を足さない (着地 test の節切り)。
  (3) 限定の 4 語「単一 attempt・descriptive・非認証・反復間安定性は未判定」を D2174 項 3 から逐語で写し、「充足」を certified・有意・反復で安定と読める書き方にしない。
  (4) fig10 の凍結 caption "This is B-7 material, not a B-7 satisfaction decision (D2044 item 3)." は着地時点の記録として保持し、追補で読み替えを示す (fig5 erratum と同じ形)。
- **(P1) 「稿の追補」の置き場 (親の provisional 裁定・攻撃対象):** 稿は results 系列の append-only 凍結物で、かつ fig10 が SHA-256 で束縛する。
  稿本文へは書けないので、追補は paper-story README (stale 注記 1 項目 + results 系列表の当該行の末尾注記) へ置く。先例 = 「T-1998 単独稿の読解上の追補」「旧 fig5 の用途制限への追補」。
  新しい results file は作らない (1 file = 1 結果の規則に反する。裁定は結果ではない)。
- **(P2) worklog の T-2610 の扱い (親の provisional 裁定・攻撃対象):** `完了` (状態語 = 裁定済み D2174 項 3・限定文言反映済み、remaining: none)。
  `更新` で active に残すと手番の無い永久 carry (F428 型) になる。凍結版への反映は版系列の規則が拾い、T は要らない。
- **成果物の形:** paper-story README = stale 注記の件数 1 → 2 と新項目 1 つ、results 行の末尾に「D2174 項 3 で限定付き充足」注記。figures README = 一覧の fig10 行に注記、
  fig10 節末尾に `## 追補 — B-7 の限定付き充足 (2026-09-20、D2174 項 3)`。worklog fragment `docs/spool/worklog/2026-09-20-dev-wave-t2610-b7-limited-1.md` (完了 1)。
- **分割方針:** 軽量版 (DW-C00)。段 2・3 省略。段 5 は親が docs を直接編集 (実装面なし)。段 6 は一次資料 (D2174) からの再抽出を含む docs-only なので read-only レビュー 1 本を残す。
  変異 matrix は実装面ゼロで免除。受入は Pegasus dispatch (`tools/dev_wave_wait.py acceptance --lease-optional`)。
- **DW-G05 成果物影響:** 放置すると次版の再導出とストーリー版の地図が B-7 を「未充足」のまま運び、結果節の報告要件が不要な未了項として残る (D2174 項 3 の理由 (c))。
  certified 選択・受理集合・proof 参照は変わらない。
- **条件表 (段 1 直後の一括再評価):** O08 = submodule 初期化済み (511c9538e)、freeze / oracle gate / proof chain には触れない (fig10 節の proof chain 小節は不変、追補は別小節)。
  O09 = 成立 — 稿 path の pin 閉包: `tools/plotting/plot_b7_fixed5_regression.py` (`CAPTION_SOURCE`)、`orchestrator/tests/test_plot_b7_fixed5_regression.py` (着地 closure と `_document_values`)、
  `figures/fig10_…provenance.json` (`caption_source` sha256)、figures README fig10 節。稿を変えないので O10 (producer 出力 bytes) は不成立。O13 = gate 新設なし。O11 = 削除なし。
- **既存被覆 (純増の確認):** D2174 項 3 が裁定、D2162 / D2044 項 3 が旧状態、entry 1729 (fig10) が図。限定文言を入口へ写した記録は無い → 本 wave が純増。

## 2. 段 4 裁定 (親、自己裁定)

- 裁定 inbox 再走査 (13:4x JST): `rulings-inbox/2026-09-20-rulings-full25-verdicts.md` に「T-2610 の状態語は fig10 wave の land 後に照合 (未反映)」、
  `2026-09-20-t750-w4-oracle-wiring-launch-pending.md` に「[T-2610] 限定付き充足の反映 wave」の予告。項 3 を覆す更新は無い。
- (P1) 採用: 稿の追補は paper-story README 側。(P2) 採用: T-2610 は `完了`。plan v2 = §1 の scope そのまま。変異 matrix は実装面ゼロで免除 (DW-S04)。
  受入全走は免除しない。実 repo を読む test (fig10 着地 test、figures README を読む a2 / s1 の provenance test、check_docs、spool_fold) は記録前に焦点走で実走する。

## 3. 段 5・6 の経過

- 段 5 (親、docs-only): `docs/paper-story/README.md` = stale 注記の件数 1 → 2 と新項目 1 つ、results 系列表の 2026-09-19 稿の行の末尾注記。
  `docs/paper-story/figures/README.md` = 一覧の fig10 行の注記、fig10 節末尾に `## 追補 — B-7 の限定付き充足 (2026-09-20、D2174 項 3、[T-2610])` (H2、着地 test の hash 抽出範囲の外)。
  worklog fragment `docs/spool/worklog/2026-09-20-dev-wave-t2610-b7-limited-1.md` (`完了` 1、base digest は worktree 作成前に main `947fd160a` で取得)。
  `check_docs.py` rc=0、`git diff --check` 緑、`spool_fold.py --dry-run` rc=0 (status planned)。
- 段 6 (read-only レビュー 1 本、gpt-6-astra、13:46〜13:49 JST、`check_codex_output` OK、逐語は `verbatim/review-1.md`):
  - 所見 1 **real / must-fix 採用**: fig10 追補の「有意差判定・区間推定・…は含まない」は、既存の「何を示す図か」が「効果・median・床値判定の区間推定」に限定し
    標本平均の t95 CI は描くと明記しているのに対し除外範囲が広い。fix = 第 2 bullet を「図の統計的な解釈と採用根拠にしない制限は、上の『何を示す図か』のとおり変わらない」への参照に置換 (重複も解消)。
  - 所見 2 **real / nit 採用**: 一覧 2 行 (paper-story README の results 行、figures README の fig10 行) の「D2044 項 3 は supersede された」は項全体の失効と読める。
    D2044 項 3 の「記述的な報告は利用してよい」は撤回されていない。fix = 「D2044 項 3 の『要件充足へ昇格させない』はこの限定付き充足で supersede された」。
  - 所見 3 **real / nit 採用**: stale 新項目の測定説明が直前項目と重複、fig10 追補の第 4 bullet (版運用) は paper-story README が正本。
    fix = 新項目の根拠を「上項の稿 (D2162 の同時期測定と床値判定) と図 10 を根拠として」へ短縮、第 4 bullet を stale 注記への参照 1 文へ、
    「論文でこの図を…使うときに付く限定」→「B-7 の充足裁定に付く限定は上の 4 語である。稿・図の既存の限定はそのまま残る」。
  - 所見 4 **refuted (P1)**: README 側の置き場は妥当 (凍結稿への追記は append-only と SHA 束縛に反し、新 results file は「1 file = 1 結果」に合わない)。
  - 所見 5 **refuted (P2)**: `完了` は妥当 (転記 3 か所がそろい、次版の作成は今回の要求ではない)。fragment の形式も規則どおり。
- DW-O16 対応表 (fix は reviewer の対案の文面をそのまま採り派生値を含まないので焦点再レビューは省略、親が再検算):
  所見 1 closed (該当文を削除し参照へ)、所見 2 closed (2 行とも置換、`grep -c "要件充足へ昇格させない」"` = 各 file 1)、所見 3 closed (3 か所を置換)。
  partial 0 / regressed 0。fix 後の再検算: 限定 4 語は 2 file × 2 か所 = 4 (逐語)、caption 逐語 1、fig10 の SHA 行 3、`git diff --check` 緑、`check_docs` rc=0。
- 段 6 の検査 (レビュー子の静的検算、親も再現): 稿の現 SHA-256 = provenance の `caption_source.sha256` = `6585d446…`、PNG / PDF / provenance の現 SHA = README の 3 行、
  `git status --short -- docs/paper-story/results/` 空、追補の H2 書式は既存 (fig5 Erratum / 旧 fig5 追補 / fig8b 追補) と一致。

## 3.1 段 7 の検査 (記録 commit `c5fda99b3` の後)

- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) rc=1: rr80 / rr20 の hit は各 4 file で、すべて起点 main `947fd160a` に既存の
  official 床値 campaign (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/`) と凍結候補 (`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`)。
  本 wave の新規・変更 file の hit は 0 (直近 wave と同じ所見)。
- 焦点走 1 走 (計算ノード request `12603.nqsv`、job `izdw-4269d10e24`、13:57 投入 → 13:58 RUN、5 file): **904 passed / 3 skipped / 0 failed、rc=0** (19.6 秒、48 worker、907 item)。
  skip 3 件は `test_check_docs.py` の成長 hold (`hold_axis=docs_bytes`、opted_in false) で対象 test の skip ではない。fig10 の着地 test
  (`test_landed_fig10_repo_closure_and_caption_when_present`) は同 file 42 test の中で pass。正本は `output/pegasus-dispatch/4269d10e24f5d7f972eff5b159236e08/izdw-4269d10e24.o12603`。
- provenance 全史監査 rc=0 (記録 commit 後)。

## 4. 限界

- 追補は入口 (README 2 本) にだけあり、凍結版 (ストーリー版 2026-09-20、claim-evidence 2026-09-20) と凍結稿・図には無い。次版の再導出が拾うまで、版だけを読む者には B-7 が「未充足」に見える。
  stale 注記が「矛盾があればここが指す一次資料が勝つ」と定めているので、入口を経由する読者には届く。
- 「限定付き充足」の 4 語は D2174 項 3 の逐語であり、本 wave は意味を足していない。反復間安定性・認証・有意差については何も新しく言えない。
- 13:03 の裁定時刻 (D2174 の記録) と 07:04 の導出起点の前後関係は worklog entry 1730 と rulings 控えから取り、独立の時刻監査はしていない。
