# 段 1 brief — [T-2120] 層 3 の空走を受入限定で閉じる

基準 commit: 764fdf202 (local main、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2120-layer3-empty-run-acceptance`)。
以下の file:line はすべてこの worktree の現物である。

## scope (これだけ)

受入 `assert_trial_registry_acceptance` (`orchestrator/campaign/trial_registry.py:5675`〜) の
campaign-chain 区間 (`trial_registry.py:6003`〜`6093`) が、層 3 の鎖を **1 件も実体検証せずに戻る「空走」**
を層 3 に帰属する hard failure で止めるようにする。鎖の本体は
`autonomous_trial_completeness.assert_campaign_layer3_chain` (`autonomous_trial_completeness.py:4815`〜)、
実体は `_fresh_layer3_for_comparison` (`:4652`、実 `layer3_report.build_report` を呼ぶ)。
編集面は `orchestrator/campaign/trial_registry.py` (受入区間)、必要なら
`orchestrator/campaign/autonomous_trial_completeness.py` (鎖が「何を実体検証したか」を呼び手へ返す部分だけ)、
テスト `orchestrator/tests/test_trial_registry.py` (+ 鎖の戻り値を変えるなら
`orchestrator/tests/test_autonomous_trial_completeness.py`)。

## 確定済みユーザー裁定 (覆さない)

- D1460: 受入限定で閉じる。**全 verifier への拡張は採らない** (producer・診断契約・発行順序の一体改訂になり利益が示されていない)。
  → producer `p3_autonomous_workload_trial.py` (`_finalize_build_cell_admission` `:2827`〜、鎖呼出し `:3702`) と
  standalone verifier `verify_autonomous_trial_files` (`autonomous_trial_completeness.py:5036`〜`5096`、
  `fatal_without_cells` `:5054` / `failure_without_campaign` `:5059` を意図的に許す) は **no-touch**。
- D1289: 受入が鎖を迂回したら hard failure。記録だけは却下。T-2075 (worklog 1127) で campaign 無し失敗 cell の迂回を
  `trial_registry.py:6021`〜`6027` (`bypassed_cell_indices`) + `:6080`〜`6084` で閉じた。
- D536: `do_build=False` の no-build 受理は拒否しない (T-2075 変異 `reject-no-build` で境界固定)。
- D863: 8c 正式系列の着手条件。本 wave はこれを緩めない。
- D95: 実装面は Codex `role=author`。親は直接編集しない。

## 実測 (brief 前、この worktree)

- 受入で起こりうる空走 3 形と現状:
  1. **campaign 無し失敗 cell** — T-2075 が明示の hard failure で閉じた (`:6080`〜`6084`、テスト
     `test_s8c_acceptance_rejects_campaignless_failure_layer3_bypass_after_chain`、変異 5/5 KILLED)。
  2. **campaign 付き admission 失敗 cell** (materialized admission failure) — 鎖は `:4911`〜`4926` で persisted 不在・
     非 admitted を確かめて `continue` し、`_fresh_layer3_for_comparison` を呼ばずに正常 return する。受入側では
     `campaign_roots` に入り、鎖の後の `:6085`〜`6093` 「build cell has no persisted reports/layer3_report.json after
     Layer-3 chain」で止まる。**この位置は T-2075 の insight が「効いている機構として数えない・変異を登録しない」と
     明記した付随的検査**であり、拒否理由は file 実在であって層 3 空走ではない。受入のテストは 0 件
     (`test_trial_registry.py` に materialized failure の受入 fixture は無い。鎖単体のテストは
     `test_autonomous_trial_completeness.py:5038` / `:5072` にある)。producer の cell literal (`p3_autonomous_workload_trial.py:3767`)
     は descriptor / descriptor_binding を持つので、この cell は受入の腕 digest 検査を通って鎖へ到達しうる。
  3. **致命的 zero-cell** (`do_build=True`, `cells=[]`) — `:6015`〜`6018` の非空検査で止まる。テストあり
     (`test_trial_registry.py:2366` の期待文字列)。
- したがって**受理集合は現状でも 3 形すべて拒否**であり、本 wave が変えるのは (2) の拒否が「層 3 空走」に帰属する
  明示の hard failure になるか、付随的な file 実在検査に依存したままかである (DW-G05 の 1 行: 放置時の certified
  受理集合は不変。変わるのは拒否理由の構造化 (規律 3) と、空走に対する直接の防壁の有無)。
- 凍結 bytes の pin 閉包 (DW-O09): 2 production module を bytes で pin する台帳は
  `orchestrator/campaign/paper_story_a1_paired.py:172` の `NON_CERTIFYING_SOURCE_RELATIVE_PATHS` (drift 検査
  `test_paper_story_a1_job_contract.py:386`〜) だけで、T-2075 / T-524 が同 file を編集して受入緑を得ているので
  live tree 追随型と見る。**段 2 で pin 方式を file:line で確かめること。** layer3_report.py の bytes・出力 bytes は変えない。
- 編集面重複 (DW-O20 起動時要求、worktree 70 root 全走査 / unreadable 0): T-524 wave (`dev-wave-t524-slot-experiment-unit`
  と codex `t524-*`) が `trial_registry.py` を未 commit で編集中 — 区間は attempt slot 系 (行 65〜3413) と受入内の
  6193 / 6360 相当 (T-524 木の行番号) で、本 wave の 6003〜6093 とは行が重ならないが**同一関数内**。T-2246 が
  `test_layer3_report.py` を commit 済みで編集 (本 wave は同 file を触らない)。`dev-wave-t2216-*` の D+?? は checkout 中の一時状態。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 閉じ方は**実体の観測**で行う: `assert_campaign_layer3_chain` が実体検証した campaign (`_fresh_layer3_for_comparison`
  を通した cell) を呼び手へ返し、受入は「campaign identity を持つ build cell 全件が実体検証された」ことを要求する。
  満たさなければ `[campaign-chain]` の hard failure で、何 cell 中何 cell が空走だったかを message に書く。
  対案は受入側で `is_exact_cell_admission_failure_decision` の cell を `bypassed_cell_indices` と同列に扱う述語型
  (`trial_registry.py` だけの変更)。述語型は候補集合に含意されて恒真になりうるので親は実体観測型を推す。
- (P2) 鎖の戻り値追加は producer / standalone verifier の挙動を 1 bit も変えない (両者は戻り値を捨てる)。
  D1460 の「受入限定」はこれで満たされる。
- (P3) `:6085`〜`6093` の既存 post-check は残す (D1289 の fail-closed)。新しい gate・台帳・一般化は足さない。
- (P4) `do_build=False` 経路は触らない。`assert_campaign_layer3_chain` の既存の拒否・受理は 1 件も変えない。

## 不変条件

- 規律 2: 受理される正常 build report の集合を広げない。規律 3: 拒否理由を層 3 空走として構造化する。
- producer・standalone verifier・`layer3_report.py`・`s8c_acceptance_receipt.py`・凍結成果物の bytes は変えない。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない。本題の実装だけ。

## 成果物

コード差分 (production 1〜2 file) + テスト、変異 matrix (段 4 で事前登録)、spool fragment (worklog)、
insight `output/insights/2026-09-04_t2120-layer3-empty-run-acceptance/` (変異 spec / out / README)。

## 分割方針・実測環境

契約が 2 file を跨ぐので実装子は 1 本 (Codex author)。段 6 はレビュー 2 本 + fix 1 本。
テストの実測は親が worktree で行う (焦点走 → 変異 probe → 変異本走 → `tools/dev_wave_wait.py acceptance --lease-optional`)。
