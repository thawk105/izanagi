# [T-2502] 段 1 brief — `--run-iteration` の `--coder-role` を manifest `sources` 非空時だけ必須にする (D1878)

親: Claude manager。worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2502-k2-coder-role-conditional` (branch `worktree-dev-wave-t2502-k2-coder-role-conditional`、HEAD 1042a1bc9 = local main、clean、submodule 3 段初期化済み)。逐語と前提実測は同 dir の `verbatim-rulings.md`。

## 研究前進
土台。K2 宣言アーム (知識付き提案の 1 巡実走、D2044 項 9 / T-2588 は別件で認可待ち) の記録の正直さを支える。driver 直接起動で K2 manifest (sources 非空) を `--coder-role` 無しで渡すと、identity と receipt には K2 と焼かれるのに proposal は K2 consumer を通らず legacy 経路で WAL の BUILD_START へ入る。この 1 経路を閉じる最小差分が本 wave。完了判定 = 負例 (sources 非空 + role 無し) が `drive_iteration` 前に拒否され、正例 2 本 (sources 空 + role 無し、sources 空 + role K2) と `_resolved_knowledge_fixture` (sources 非空) + role K2 が従来どおり通ること。

## scope (実アンカー)
- `orchestrator/campaign/p3_s4_loop.py` `main()` の `--run-iteration` 経路: `resolved_knowledge = _resolve_knowledge_manifest_argument(a.knowledge_manifest)` (:2667) 〜 `load_proposal_file(...)` 呼び出し (:2764〜2778)。ここへ「`resolved_knowledge` があり `resolved_knowledge.manifest.sources` が非空で `a.coder_role is None` なら拒否」の条件 1 つを足す。
- `orchestrator/tests/test_p3_s4_loop.py`: 負例 1 本以上 (sources 非空 + role 無しで main が拒否、`drive_iteration` 未到達)、既存正例 `test_main_manifest_only_accepts_legacy_flattened_proposal` (:7205) と `test_main_manifest_and_k2_role_accept_k2_wrapper` (:7241) は無変更で緑。fixture `_resolved_knowledge_fixture` (sources 非空) は既存。
- scope 外: `load_proposal_file` の関数レベル不変条件 (両方指定か両方省略) の変更、`--emit-planner-context` 経路、Pegasus job body、K2 2 巡目の実走認可、新規 gate・台帳・一般化、`knowledge_manifest.py` の変更。

## 確定済みユーザー裁定
D1878 (逐語は verbatim-d1878.txt)。空取得 (`completed_empty` / `sources: []`) は現状のまま通す。無条件の相互必須化は却下済み。コマンド引数: Codex author (D95) + 変異事前登録、本題の条件変更だけ、仮想リスク向けの gate・検査・台帳・一般化は scope 外、規律 2 を緩めない。

## 不変条件
- 規律 2/3: 正しさゲート (K2 consumer の schema・anomaly・参照 index) を緩めない。本 wave は受理集合を**狭める**だけで広げない。
- 受理される起動 (sources 空 + role 無し / 任意 manifest + role K2 / manifest 無し) の identity・receipt・WAL の bytes は不変。
- `load_proposal_file` の signature と既存検査は不変。
- 拒否は `drive_iteration` へ到達する前で発火する。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- (P1) 検査の位置: `--run-iteration` 経路で、`_prepare_knowledge_campaign` (:2728、`layout.ensure()` + `write_receipt` の副作用) より**前**に置く (`resolved_knowledge` 解決直後、`a.run_iteration` で guard)。副作用の前に拒否する方が記録の正直さ (規律 3) に合う。対案: `load_proposal_file` 直前 (:2764) — 受入れ側の副作用が先に走る。
- (P2) 非空の判定は typed な `resolved_knowledge.manifest.sources` (tuple) の長さで行い、planner projection の dict を見ない。
- (P3) 例外型: 既存の契約違反と同じ `ValueError` (日本語 message、`a.coder_role` の要求を明示)。`ap.error` (SystemExit 2) は parse 後の file 内容依存なので使わない。
- (P4) 変異事前登録の仮説 (段 4 で確定): M1 条件の削除 → 負例が殺す; M2 `sources` 非空判定の反転 (空のとき必須) → 既存正例 :7205 が殺す; M3 `a.coder_role is None` を `is not None` に反転 → 正例 :7241 と負例が殺す; M4 拒否を `drive_iteration` 後へ移す/`return 0` に置換 → 負例 (`drive_iteration` 未到達 assert) が殺す; M5 guard から `a.run_iteration` を外す → `--emit-planner-context` を sources 非空 + role 無しで通す既存正例 `test_emit_context_and_run_iteration_share_manifest_campaign_identity` (:6521、前半の `--emit-planner-context` 呼び出し :6546〜) が殺す。
- (P5) **新事実 (裁定文・持ち越し本文に未記録):** 既存 `test_emit_context_and_run_iteration_share_manifest_campaign_identity` (:6521〜) は後半で `_resolved_knowledge_fixture` (**sources 非空**) の manifest を `--run-iteration` + `--no-build` に **`--coder-role` 無し**で渡し (`load_proposal_file` は monkeypatch)、`main == 0` を要求する。本題の条件変更でこの test は赤になる。D1878 の「正例を 1 件も壊さずに閉じられる」は、意味上の正例 (:7205 の flattened 経路、sources 空) には成り立つが、この identity 共有 test には成り立たない。親の provisional: この test の目的は emit-context と run-iteration の campaign identity 一致であり (`--coder-role` は identity に入らない: `_prepare_knowledge_campaign` は role を見ない)、後半の argv へ `--coder-role coder-v4-autonomous-k2` を足して目的を保ったまま緑にする (production を test に合わせて緩めない)。裁定の決定 (非空 + role 無しを拒否) 自体は動かさず、段 7 の worklog fragment に新事実として記す。対案: 拒否条件を緩める — 規律 2 と D1878 の決定に反するので不採用。

## 成果物
code diff (p3_s4_loop.py 数行) + test (負例 ≥1、正例は既存流用)、変異 matrix (baseline 緑・全 KILLED)、受入全走、spool fragment (worklog / decisions は既裁定なので追加裁定なし想定 / failures 該当なし)、insight README (逐語・変異台帳)。

## 並列分割方針
実装面が小さいので author 1 本 (所有: `p3_s4_loop.py` の main 経路と `test_p3_s4_loop.py`)。段 3 と段 6 は各 2 レンズ (正しさ境界 / 整合・実効性)。
