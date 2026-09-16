# [T-2502] 段 4 裁定 — plan v2 と変異事前登録

親: Claude manager、2026-09-17 01:20 JST、worktree HEAD 1042a1bc9 (= local main、段 4 直前に再確認: 差 0 commit、decisions.md に D1878 / coder-role の更新なし)。
入力: s1-brief.md、s2-plan-out.md、s3-a-out.md (レンズ A: 正しさ境界)、s3-b-out.md (レンズ B: 整合・実効性)。

## 所見の裁定 (real / refuted、採用 / 不採用、scope 内 / 外)

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A1/B1/B3 | 親 (P1) の「manifest 解決直後 + run guard だけ」は emit+run 併記を過剰拒否する。plan は `not a.emit_planner_context` と test C で補ったが、emit 分岐の `return 0` (:2713) 後・`build_context = build_run_context(...)` (:2714) 前に置けば制御フローで emit 優先が保たれ、guard 拡張も test C も要らない | real | **採用 (対案)** | 内 |
| B2 | 対案の位置は `build_run_context` の nonce 生成と run 用 authority 消費より前、`_prepare_knowledge_campaign` の `layout.ensure()` / `write_receipt` より前。「全副作用より前」とは書かない | real | 採用 (記述の限定) | 内 |
| A4 | 拒否 message に sources 件数と欠けている flag を含める (規律 3: なぜ拒否したか) | real | 採用 | 内 |
| A5/B7 | (P5) は再裁定でなく test 側の追随 (b)。identity test の後半 argv だけに `--coder-role coder-v4-autonomous-k2` を足し、前半 (`common`) は変えない。production に例外を設ける案は規律 2 / D1878 に反し不採用 | real (文言の一般化) / refuted (再裁定必須) | 採用 | 内 |
| A2/B12 | 「空 sources = completed_empty と同義」は片方向の含意 (空 ⇒ completed_empty) に訂正。parser の逆向き検査は scope 外 | real | 記述訂正のみ | 逆向き検査は外 |
| A3/B4 | K2 consumer の緩和・迂回は新設されない。job body は変えない。負例は driver 直接 `main` + 有効な非空 manifest + 有効な legacy proposal + role 省略 | refuted (懸念) | 採用 (N の入力形) | 内 |
| B6 | 負例 N は `_run_main_with_actual_proposal_loader` を流用せず直書き。`_prepare_knowledge_campaign` は `Mock(wraps=実関数)` で観測 (拒否させない)、`drive_iteration` は到達で `pytest.fail`、`load_proposal_file` は実物。receipt 未作成だけの検証は弱いので prepare 未到達 + layout root 不在を主検証にする | refuted (helper 流用) / real (検証の役割分担) | 採用 | 内 |
| A-変異/B9 | M3 は K (:7241) を殺さない (sources 空で短絡)。M3 の期待 node は N・P・I。M4 は `return 0` 版に固定 (drive 後移動版は登録しない)。plan の M5-route と test C は対案で不要 | real | 採用 | 内 |
| B8/B9 | 対案の run guard 除去 (M5) は fixture 経路 (`--value`、manifest 非空、role 無し) を過剰拒否する非等価変異だが、既存 test に検出者がいない。DW-M01「受理集合を縮小する wave は承認外の過剰拒否の正例も登録する」に当たるので、fixture 経路の正例 F を 1 本足して M5 の期待 node にする | real | **採用 (F を追加)** | 内 (変異契約が要求する正例であり、仮想リスク向けの gate ではない) |
| B5 | `docs/phase3-s4b-runbook.md` :43 直後に CLI 条件の 1 行追記。`tools/pegasus/README.md`・`agent-architecture.md` は不要 | real | 採用 (段 7 で親が docs 編集) | 内 |
| B13 | brief の「受理される起動の identity・receipt・WAL bytes は不変」は、同一外部結果を前提とした構築ロジックの不変に限定。B-4 closure (`p3_b4_closed_critic.py:635` 等) は変更対象の生 bytes を hash するので数行追加で closure hash は変わる — これは別問題として記録し、古い closure を受理するために gate を緩めない | real | 記述の限定 + worklog fragment に記録 | 内 (記録のみ) |
| A-反証/B14 | 持ち越しの最新番号は (1579)。「26 passed」は親の報告値であり子の独立検証ではない。sha256 逆引き 0 件は「単体 sha の pin 不在」に限定 | real | 記述訂正 | 内 |
| B10 | 対案採用後は plan の anchor は使えない。emit の `return 0` と次の `build_context` を含む新 anchor を登録し、最終 commit で一意性・node 実在を再検証 (DW-M07) | real | 採用 | 内 |
| B11 | 焦点走の consumer 集合は plan の 29 file。`test_pytest_collection_config.py` と `test_real_repo_serialization.py` は全 suite collection を子 pytest で起こすので焦点走から外す (受入全走では走る) | refuted (除外の不当性) | 採用 (plan の除外を維持) | 内 |

scope 外で real な所見: parser の逆向き整合検査 (非空 sources + completed_empty)、B-4 closure の互換性。いずれも実装せず、worklog fragment に「保証しない範囲」として 1 行ずつ記す。裁定パッケージへ上げる設計択一は無い。

## plan v2 (実装子への確定指示)

### production: `orchestrator/campaign/p3_s4_loop.py` `main()`

emit 分岐 (`if a.emit_planner_context:` … `return 0`、:2689〜:2713) の直後、`build_context = build_run_context(` (:2714) の直前に次を挿入する (他の行は変えない):

```python
    if (
        a.run_iteration
        and resolved_knowledge is not None
        and resolved_knowledge.manifest.sources
        and a.coder_role is None
    ):
        raise ValueError(
            "--run-iteration: --knowledge-manifest の sources が非空 "
            f"(sources_count={len(resolved_knowledge.manifest.sources)}) "
            "のため --coder-role coder-v4-autonomous-k2 が必要"
        )
```

- `load_proposal_file` (:2254〜、相互必須検査 :2309〜:2317)、`_prepare_knowledge_campaign`、`knowledge_manifest.py`、argparse 定義、`tools/pegasus/p3_s4_loop_pegasus.sh` は変更しない。
- 受理集合: 変わるのは「`--run-iteration` あり・emit 無し・manifest の sources 非空・`--coder-role` 無し」の 1 セルだけ (レンズ A の表)。

### tests: `orchestrator/tests/test_p3_s4_loop.py`

1. **N** `test_main_nonempty_manifest_requires_coder_role_before_prepare` (既存 helper 群 :7127〜:7202 の後、:7205 の正例の前後どちらでもよい): `_resolved_knowledge_fixture(tmp_path, name="missing-role")` で非空 manifest (実 parser/resolver)。proposal は `_k2_proposal_document()["coder"]["proposal"]` を `coder` に置いた flattened 形を `_write_k2_proposal` で保存 (guard 削除時に実 legacy loader を通る入力)。monkeypatch: `L._resolve_knowledge_manifest_argument` → resolved、`L.exploration_campaign_layout` → tmp 配下の `CampaignLayout`、`patchharness.assert_pinned_clean` → no-op、`L._prepare_knowledge_campaign` → `unittest.mock.Mock(wraps=L._prepare_knowledge_campaign)`、`L.drive_iteration` → 到達で `pytest.fail("drive_iteration reached")`。`load_proposal_file` は実物。`with pytest.raises(ValueError, match="--coder-role")` で `L.main(["--run-iteration", str(proposal_path), "--no-build", "--knowledge-manifest", str(tmp_path / "manifest.json")])`。事後: prepare spy `assert_not_called()`、`Path(layout.root).exists()` が偽、例外 message に `sources_count=1` を含む。
2. **P** `test_main_nonempty_manifest_and_k2_role_accept_k2_wrapper`: :7241 の構成を踏襲し fixture だけ `_resolved_knowledge_fixture(tmp_path, name="k2-role")` (非空)。`_run_main_with_actual_proposal_loader(..., coder_role="coder-v4-autonomous-k2")` で `vars(observed["coder"]) == document["coder"]["proposal"]`、`observed["prior"] is None`。
3. **F** `test_main_fixture_route_accepts_nonempty_manifest_without_coder_role`: :4434 の fixture 経路の stub 形 (`exploration_campaign_layout`、`patchharness.assert_pinned_clean`、`_run_one_iteration_resolved` → `{"outcome": "dry-pass", "variant": None}`) に `L._resolve_knowledge_manifest_argument` → `_resolved_knowledge_fixture` の resolved (非空) を足し、`L.main(["--no-build", "--knowledge-manifest", str(tmp_path / "manifest.json")]) == 0` を要求する (`--coder-role` 無し、`--run-iteration` 無し)。目的: D1878 の射程が `--run-iteration` だけであることの過剰拒否正例。
4. **I** `test_emit_context_and_run_iteration_share_manifest_campaign_identity` (:6521〜): 後半の `L.main([*common, "--run-iteration", ..., "--no-build"])` (:6585〜:6587) の argv に `"--coder-role", "coder-v4-autonomous-k2",` を足す。`common` (:6540〜:6545) は変えない。
5. 既存 E (:7205) と K (:7241) は無変更。

### docs (親が段 7 で編集、docs-only)

`docs/phase3-s4b-runbook.md` の K2 宣言アーム段落 (:41〜:43) の直後に 1 行: 「driver の `--run-iteration` 経路では `--knowledge-manifest` の `sources` が非空なら `--coder-role coder-v4-autonomous-k2` が必須で、空取得 (`sources: []` / `completed_empty`) は従来どおり role 省略を許す (D1878)。」

## 変異事前登録 (DW-M01、実装前。anchor の逐語は実装後の最終 commit で再検証 = DW-M07)

対象 file: `orchestrator/campaign/p3_s4_loop.py` の 1 本。runner 対象 node (焦点 6 node、prefix `orchestrator/tests/test_p3_s4_loop.py::`):

```text
N = test_main_nonempty_manifest_requires_coder_role_before_prepare
E = test_main_manifest_only_accepts_legacy_flattened_proposal
K = test_main_manifest_and_k2_role_accept_k2_wrapper
P = test_main_nonempty_manifest_and_k2_role_accept_k2_wrapper
I = test_emit_context_and_run_iteration_share_manifest_campaign_identity
F = test_main_fixture_route_accepts_nonempty_manifest_without_coder_role
```

| id | 変異 (位置) | 期待 status | 期待 node 完全集合 | 赤理由 (単一) |
|---|---|---|---|---|
| M0 | 挿入 block 直上に comment 1 行を足すだけ (対照) | SURVIVED | (空) | 意味変化なし |
| M1 | 挿入した if/raise block 全体を削除 | KILLED | N | 拒否が発生せず legacy loader → drive spy 到達 |
| M2 | `and resolved_knowledge.manifest.sources` → `and not resolved_knowledge.manifest.sources` | KILLED | N, E | N: 非空が拒否されない / E: 空取得が過剰拒否 |
| M3 | `and a.coder_role is None` → `and a.coder_role is not None` | KILLED | N, P, I | N: role 無しが通る / P・I: role 有りが過剰拒否 |
| M4 | `raise ValueError(...)` (3 行 + 引数) → `return 0` | KILLED | N | 例外なしで成功扱い → `pytest.raises` 不成立 |
| M5 | 条件から `a.run_iteration` の行を除去 | KILLED | F | fixture 経路 (manifest 非空・role 無し) を過剰拒否 |

- K は sources 空で短絡するためどの変異にも現れない (登録上の期待どおり、K が赤なら MISMATCH)。
- 同じ入力を拒否する別層: argparse `choices` (不正 role)、loader の相互必須検査 (manifest 無し + role 有り)、parser (不正な空 manifest)、job body (env 対) — N の入力はいずれにも掛からない (レンズ A・B が現物で確認)。
- 変異 harness: `tools/mutation_harness.py` を `--runner-mode dispatch --detached` で、最終統合 commit を `tools/mutation_worktree.py --commit <sha>` の使い捨て worktree に当てる。runner argv: `python3 tools/run_tests.py -rf orchestrator/tests/test_p3_s4_loop.py -k "<6 node の or 式>" -n 0 --force-dispatch`。`timeout_seconds` は dispatch envelope 超。baseline 緑必須。
- 焦点走 (変異とは別): 変更 file 2 本の単独走 + consumer 29 file (plan の表、`test_pytest_collection_config.py` と `test_real_repo_serialization.py` は除外) を `tools/run_tests.py` で。その後 land 対象 tip へ受入全走。

## 段 5 の所有と権限

author 1 本 (Codex `role=author`、workspace-write、専用 worktree)。編集してよい file: `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/tests/test_p3_s4_loop.py` の 2 本だけ。docs・commit・他 file は禁止。
