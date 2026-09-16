---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2590-a1-sized-source-contract
seq: 1
title: [T-2590] A-1 balanced5 sized 本走の pilot 専用分岐 4 点を対称化し、T-2081 (D1323) を同じ変更単位で閉じた — 本走は投入せず認可も出していない (コード + docs、branch worktree-dev-wave-t2590-a1-sized-source-contract、変異 matrix = baseline PASSED・負例 10/10 KILLED 期待 node 完全一致・等価 1 SURVIVED)
---

## 本文

- ユーザー依頼は「A-1 (balanced5) の本走を実行できるように、計測経路に残る pilot 専用の分岐を一式で揃える。
  裁定は D1986 項 5。同じ変更単位で T-2081 (D1323) も入れる。対象は `orchestrator/campaign/paper_story_a1_*.py` と
  契約 JSON。正式測定の認可は T-1505 のまま据え置き、本 wave は認可を出さず本走も投入しない。Codex author + 変異
  事前登録。本題の分岐整理だけ」。
- 一次資料は `output/insights/2026-09-17/t2590-a1-sized-source-contract/README.md` (段 1〜6 の逐語、変異 spec と台帳)。
  sized の source 追補 README は `output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md`
  (sha `6093de244e6fc90607094608617032f427db4951ebffc847c7bcaa795309789b`、v2 契約が `amendment` として束縛)。
- **設計判断は {{D:a1-sized-source-contract}}。** v1 契約の sha は pilot 公開受領証の live pin (`binding_matches`)
  なので v1 は 1 byte も変えず、sized は `paper_story_a1_source.v2.json` (sha `b50a4edf86250033aa0e2b18efa2d7842d7c90025fdb901011fdad7adf052fe1`、
  11 key、`attempt` なし) で束縛する。module は固定 2 要素表。
- **job script (`tools/pegasus/paper_story_a1_paired.sh`) も変更面に入れた。** 引数の列挙は `.py と契約 JSON` だが、
  数え上げの「hydrate 入力と staging の分岐」の実体 (staging 1 箇所、source 閉包 3 箇所) は job script にあり、
  ここを揃えないと sized の measure は起動できない。変更は分岐条件の 2 値化だけで、共通の module / patch の
  文字列は各箇所 1 出現に保ち、既存 test の出現数 pin (`count == 3`) を pilot / sized の両方で満たす。
- **段 3 の敵対相談 2 本は production への反例を出さなかった。** A (凍結・受理集合): pilot 履歴 binding の互換・両契約
  混入・hydrate の無検査経路はいずれも構成不能。real は「受理集合には拡大と縮小がある (記録した)」「T-2081 の閉じは
  実測前」「追補 README に保証範囲の限定 2 文が要る (`.git` を除く tree 比較、元 checkout の untracked は登録どおり
  無視)」「pilot attempt 1〜3 の失敗分類 (0001/0002 = bench 前停止、0003 = 条件関門の拒否)」。B (実効性): 追加の
  pilot 限定分岐なし。real は「sized fixture に `sizing_inputs` の 2 file が要る」「root 不一致の期待 error は 2 分
  (非 canonical → `amended-source-admission-mismatch`、canonical だが configure `-S` と別 → `trace0-source-route-incomplete`)」
  「M8 は pilot 条件の削除だと v2 に `attempt` が無く `KeyError` で帰属が崩れる → literal 照合の追加に確定」
  「現行 sized は 7133 行でなく 7127 行で先に落ちる」。
- **親の逐語射影に誤りがあった (near miss、実害なし)。** D1986 項 5 の位置に項 4 (B-4) の本文を入れたまま段 2 の
  plan 子へ渡した。plan 子が現物と突き合わせて訂正して進み、段 3 前に親が直した。逐語は行範囲でなく見出しで切り、
  切った直後に先頭見出しを確認する。
- **段 5 の実装子は親の仕様誤りで 1 度止まった。** test 8 (pilot 公開 binding の不変) の呼出先を
  `_validate_non_certifying_source_binding` (14 path) と書いたが、公開 receipt の binding は terminal 用 9 path で
  `_validate_source_binding` が正。実装子は期待値を弱めずに停止して報告し、2 巡目 (継続) で訂正した。
  最終: 新規 14 test、sandbox 内 pytest 129 passed、反実仮想 20 変異 KILLED / 等価 1 SURVIVED。
- **段 6 レビュー 2 本は production の must-fix ゼロ。** real は「報告と実体の時点不一致」(親が 1 巡目報告だけを
  射影した所為、2 巡目報告で閉じた) と「変異 anchor の再照準 (M4 は 2 行、M6 は `THIRD_PARTY_ARGS=()` 込み)」。
  nit: sized の hydrate 欠落時の文言が `attempt-0004 requires …` のまま (受理判定に影響なし、据え置き)。
- **焦点走 (計算ノード) で 2 赤 → 両方閉じた。** (1) `test_existing_a1_non_touch_manifest_is_empty_from_base` は
  manifest file の未 commit 差分検査で、統合 commit 後に緑。(2) `test_deferred_gate_ledger_…` は paired.py の
  `run_measurement` 内 `run_campaign(` sink の行番号 pin 7423 が差分 +5 行で 7428 へずれたもの。Codex fix 子が
  2 箇所を実値へ更新 (pytest 47 passed、反実仮想で 7429 なら赤)。統合 commit 後の再走は spawn_sites + headline
  82 passed、test_campaign 選択 node 6 passed。login の bounded local 走は memory 予算 cap で 1 度 OOM 停止 (非帰属)。
- **変異 matrix (container worktree `.codex/worktrees/t2590-mutcontainer`、統合 commit ad83b108b、
  runner = 3 A-1 test file、dispatch):** probe (全件 SURVIVED 期待) で観測 node を集めた — 全件が本 wave の新規 test で既存 test の巻き添え 0 (冗長 gate なし)。本走は baseline PASSED、負例 10 件 (M1〜M10) すべて KILLED で期待 node 完全一致 (11/11)、等価変異 M0 は SURVIVED、MISMATCH 0、TIMEOUT 0。走行後の container は HEAD ad83b108b で clean。probe / 本走とも 12 走 × 約 1 分。
- **T-2081 (D1323) は既存機構の sized 適用を test で確認して閉じた。** `_assert_ccbench_acceptance` の 3 境界
  (sized policy、`_run_git` だけ stub、正例 1 + 負例 3)、`_parent_porcelain` が空でも submodule dirty で拒否、
  sized の `SourceContext` が `pipeline._require_canonical_build_source_state` の trace / perf 双方で `validate` に
  届く。新規 gate も bytes 級検査も足していない。限界: Git 応答と期待 materialization の生成 / 比較は stub で、
  実 tree 検査の実証ではない。
- **言わないこと:** sized 本走が実機で全層を通ったとは言わない (materializer / 依存準備 / condition gate /
  campaign は stub)。変更後 checkout で過去の pilot 束を再 materialize できるとは言わない。認可は T-1505 のまま。
- 工数: codex 子 8 本 (plan 1、consult 2、author 2 (継続 1)、review 2、fix 1、全段 `gpt-6-astra` / `medium`)。
  計算ノード job: 焦点走 3 (うち 1 は no tests ran)、変異 probe 12 走 + 本走 12 走、受入は記録 commit 後の tip で 1 走投げる (結果は land の受領証が持つ)。

## 次の一手差分

### 完了

- [T-2590] pilot 専用の分岐 4 点 (source 契約 / hydrate と staging / source binding の生成 / amended build の
  受理形の発火条件) を sized へ対称化した。v1 契約・pilot の閉包・pilot 公開受領証の判定は不変。本走は未投入。
  remaining: none
  base: dc6d9c4e122963acdbf4f3a64d6b158c2131d841f2d9c071c696348f62a8b7ea

- [T-2081] D1323 の閉じ: 既存 5 境界 (canonical pin + tracked-clean、期待 materialization、consumer) が sized を
  study 非依存に覆うことを test で確認した。bytes 級検査は新設していない。
  remaining: none
  base: fcb28203835816a1f1cae8ada315840513cbd1e025d3dbb8344141e300ffcbf4

### 更新

- [T-1505] **P1・ユーザー裁定待ち (再提示)**: D1986 項 5 / D2044 項 8 が「改めて諮る」条件とした
  「試験運転専用の分岐を外す実装」が本 wave で閉じた (実装 commit ad83b108b、変異 matrix と受入で検証)。
  A-1 balanced5 sized 本走の認可は人間手番のまま。認可が出た場合の投入は既存 submit 経路
  (`paper_story_a1_paired.py submit --study-id paper-story-a1-20260901-balanced5-sized-v1`、hydrate 済み
  third-party source root が必須) で、sized の attempt 名は契約で pin されない。実機で sized の全層が通った実績は
  まだ無い (test は materializer / campaign を stub)。
  base: d5b5dbf8f8c190bf17f6b7e97ed7a36b2df0072ab76b51910b1d5abf0e4a3ce2
