# [T-2502] `--run-iteration` で manifest の sources が非空なら `--coder-role` を必須にした (D1878 の実装記録)

`authority: none` / `default_effect: no-state-change` — これは dev-wave の**実装・実測記録**である。
可変状態の正本 (worklog 末尾・現行 phase doc) ではない。裁定の正本は `docs/decisions.md` の D1878。

- 実測日: 2026-09-17 (JST 00:28〜01:28)
- 基準 commit: local main `1042a1bc9` から fresh worktree、統合 commit `c79437d24` (branch `worktree-dev-wave-t2502-k2-coder-role-conditional`)
- 実測機: 焦点走・変異走は Pegasus 計算ノード (NQSV request `2274` / `2290` / `2294`、変異 `2291`〜`2302`)。codex 子は login node
- 依頼: 「`--knowledge-manifest` の `sources` が非空のときだけ `--coder-role` を必須にする (D1878)。空取得の経路は現状のまま通し、既存正例 `test_main_manifest_only_accepts_legacy_flattened_proposal` を壊さない。本題の条件変更だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 を緩めない。」

---

## 1. 結論を先に

**閉じた。** driver 直接起動で K2 manifest (sources 非空) を `--coder-role` 無しで `--run-iteration` へ渡すと、
campaign identity と knowledge receipt には K2 と焼かれるのに proposal は K2 consumer を通らず legacy flattened
loader へ流れていた穴を、`main()` の emit 分岐の `return 0` 直後・`build_run_context` と
`_prepare_knowledge_campaign` (`layout.ensure()` / `write_receipt`) の前で `ValueError` にした (production は 11 行の
挿入だけ)。変わる受理集合は「`--run-iteration` あり・`--emit-planner-context` 無し・sources 非空・`--coder-role` 無し」の
1 セルだけで、空取得 (`sources: []`)・role 付き・manifest 無し・emit 経路・fixture 経路の受理は変えていない。

| 検査 | 結果 | 実測 |
|---|---|---|
| 変異登録 6 node 焦点走 | 6 passed | request 2274、HEAD c79437d24 相当の作業ツリー |
| 変更 test file 単独走 (`test_p3_s4_loop.py`) | 414 passed in 11.89s | request 2290、HEAD c79437d24 |
| consumer 28 file 焦点走 | 3204 passed, 28 skipped in 235.28s | request 2294、HEAD c79437d24 |
| 変異 matrix (固定 commit c79437d24、`-mut` worktree) | baseline PASSED、M0 SURVIVED (対照)、M1〜M5 KILLED、期待 node 完全一致 6/6、MISMATCH 0 | request 2291〜2302、`verbatim/mutation-out-1.json` |
| 敵対レビュー 2 レンズ | GO / GO、must-fix 0、nit 3 | `verbatim/s6-a.md`、`verbatim/s6-b.md` |

## 2. 何が穴だったか (現物)

- `main()` の `--run-iteration` 分岐は `load_proposal_file(..., knowledge_input=(knowledge_input if a.coder_role is not None else None), coder_role=a.coder_role)` で loader を呼ぶ。role 無しなら `knowledge_input=None` が渡るので、loader の「両方指定か両方省略」検査は素通りし legacy flattened 経路になる。sources が非空でも同じ。
- その手前で `_prepare_knowledge_campaign` が `cfg.search_config` へ `knowledge_level` と `knowledge_manifest_sha256` を焼き、`layout.ensure()` + `write_receipt` を行う。つまり K2 として identity と receipt に記録されるのに proposal は K2 consumer (schema `CODER_CONTRACT_K2`・anomaly・参照 index) を通らない。規律 3 の「記録と検査の齟齬」。
- Pegasus job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) は env 対 (`IZANAGI_S4_KNOWLEDGE_MANIFEST` / `IZANAGI_S4_CODER_ROLE`) で既に閉じているので、残っていたのは driver 直接起動だけ (D1878 の理由と一致)。

## 3. 設計の択一と裁定 (段 3 の 2 レンズが一致)

- **検査の位置。** 親 brief の (P1)「manifest 解決直後 + `a.run_iteration` guard」は emit+run 併記を過剰拒否する (argparse は両者を排他にせず emit が先に `return 0` する)。段 2 plan は `not a.emit_planner_context` を guard に足し、それを殺す新規 test C を提案したが、**emit 分岐の `return 0` 後・`build_run_context` 前に置けば制御フローで emit 優先が保たれ、guard 拡張も test C も要らない** (段 3 A/B が一致、段 4 で採用)。副作用の順序は「`build_run_context` の nonce 生成と run 用 authority 消費より前、`_prepare_knowledge_campaign` の receipt より前」であり「全副作用より前」ではない (manifest 解決・build opt-in・site admission は先行する)。
- **拒否 message。** 規律 3 に従い、sources 件数と欠けている flag を含める: `--run-iteration: --knowledge-manifest の sources が非空 (sources_count=N) のため --coder-role coder-v4-autonomous-k2 が必要`。
- **新事実 (P5)。** 既存 `test_emit_context_and_run_iteration_share_manifest_campaign_identity` は後半で sources 非空の manifest を `--run-iteration` + role 無しで通し `main == 0` を要求していた。D1878 の「正例を 1 件も壊さずに閉じられる」は、意味上の正例 (空取得 + role 無し、`test_main_manifest_only_accepts_legacy_flattened_proposal`) には成り立つが、この identity 共有 test には成り立たない。裁定の決定 (非空 + role 無しを拒否) は動かさず、test の目的 (emit-context と run-iteration の campaign identity 一致。`_prepare_knowledge_campaign` は role を見ないので identity は不変) を保ったまま**後半 argv だけに `--coder-role coder-v4-autonomous-k2` を足した** (前半の emit と `common` は不変)。production に例外を設ける案は規律 2 / D1878 に反し不採用。
- **過剰拒否の正例 F。** DW-M01 は「受理集合を縮小する wave は承認外の過剰拒否の正例も登録する」。fixture 経路 (`--value`、`--run-iteration` 無し) を manifest 非空・role 無しで通す正例 `test_main_fixture_route_accepts_nonempty_manifest_without_coder_role` を 1 本足し、guard から `a.run_iteration` を落とす変異 M5 の検出者にした。仮想リスク向けの gate ではなく、変異契約が要求する正例である。

## 4. 変異台帳 (事前登録 = `verbatim/s4-ruling.md` と `verbatim/mutation-spec.json`、結果 = `verbatim/mutation-out-1.json`)

| id | 変異 | 期待 | 実測 status | 実測 failed node (完全一致) |
|---|---|---|---|---|
| M0 | 挿入 block 内に comment 1 行 (対照) | SURVIVED | SURVIVED | (空) |
| M1 | if/raise block 全体を削除 | KILLED {N} | KILLED | N |
| M2 | `sources` 非空判定を反転 | KILLED {N, E} | KILLED | N, E |
| M3 | `a.coder_role is None` → `is not None` | KILLED {N, P, I} | KILLED | I, N, P |
| M4 | `raise ValueError(...)` → `return 0` | KILLED {N} | KILLED | N |
| M5 | 条件から `a.run_iteration` を除去 | KILLED {F} | KILLED | F |

N = `test_main_nonempty_manifest_requires_coder_role_before_prepare`、E = `test_main_manifest_only_accepts_legacy_flattened_proposal`、
K = `test_main_manifest_and_k2_role_accept_k2_wrapper`、P = `test_main_nonempty_manifest_and_k2_role_accept_k2_wrapper`、
I = `test_emit_context_and_run_iteration_share_manifest_campaign_identity`、F = `test_main_fixture_route_accepts_nonempty_manifest_without_coder_role`。
K はどの変異でも緑 (M1/M3/M4/M5 は sources 空で短絡、M2 は反転した sources 条件が真でも role 有りで最後の条件が偽 — 段 4 の「K は sources 空で短絡する」は M2 には当てはまらないと段 6 A が訂正)。
baseline の runner は `python3 tools/run_tests.py -rf orchestrator/tests/test_p3_s4_loop.py -k "<6 node>" -n 0 --force-dispatch`、`-mut` worktree は走行後に HEAD blob と byte 一致 (復元確認済み)。

## 5. 保証しない範囲 (段 3・6 で real だが scope 外と裁定)

- parser の逆向き整合 (非空 sources + `completed_empty`) は検査しない。`_parse_value` が保証するのは「sources 空 ⇒ `declared_scope` と `completed_empty` が必須」の片方向。本 wave は sources で判定し status を見ない。
- B-4 projection closure (`p3_b4_closed_critic.py` が `p3_s4_loop.py` の生 bytes を hash) は本変更で base/sort/trigger の 3 種とも値が変わる。旧 closure を宣言した admission は live 照合で拒否される。旧 closure を受理するために gate は緩めない。既存の test golden は現行 bytes から計算し旧値を固定していない (段 6 B が `test_p3_b4_closed_critic.py` で確認)。変更前 `p3_s4_loop.py` の sha256 `f5efa58a…` は tracked 全体 (output/ 含む) で 0 件 (単体 sha の pin 検索結果に限定)。
- `--coder-role ""` は argparse `choices` が拒否、manifest 無し + role 有りは loader の相互必須検査が拒否 — いずれも本 guard とは別層で、N の入力はどれにも掛からない。

## 6. 工数

codex 子 6 本 (全て `gpt-6-astra` / effort `medium`、全て accepted): plan 9 calls・288 s、consult A 7 calls・278 s、consult B 11 calls・364 s、author 19 calls・342 s、review A 6 calls・171 s、review B 11 calls・247 s。fix 子 0 本。親 (claude opus) は brief・裁定・統合 commit・変異 spec・記録。
