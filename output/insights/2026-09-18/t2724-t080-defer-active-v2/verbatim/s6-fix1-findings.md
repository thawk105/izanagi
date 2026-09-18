# 段 6 fix-1 の所見裁定と指示 (親、2026-09-18 12:30 JST)

レビュー A / B はともに NO-GO。所見は全件 real。裁定と指示を所見 ID ごとに書く。**本巡で親が段 4 裁定を 1 点改める**: A-1 (鮮度) の実装形。

## F1. campaign-start 前の鮮度検査 (RA-1 / RB-2 / RA-3) — 段 4 の A-1 実装形を改める

事実: campaign-start 前に `launch_validate` を再実行すると floor artifact を disk から再読し、既存 tracked test `test_v2_floor_disk_swap_after_launch_uses_same_validated_object` (E3b / A3-6: launch 済みの同一 object だけを使い disk を再読しない) が `refused` になる。親が代案にした「走査だけの再検査」も、走査が floor result の bytes を読む (result は exact 免除の対象外) ため、同 test の poisoned bytes で `closure-hit-mismatch` となり救えない (RA-1)。**campaign-start での内容鮮度の再検査は、tracked test が固定する E3b と両立しない。**

裁定: **campaign-start 前は再 launch も再走査もしない。** `campaign_start_resolution = _resolve_t080_receipt(root=root, launch_validated=validated)` (gate 時 token) → `_t080_epoch_identity` の 4 要素比較、の形に戻す (基点 `24ede1d11` の構造 + token)。委譲 predicate は campaign-start 時点でも HEAD・active 世代の再解決・列挙集合 digest・凍結 doc 束縛を live で再照合する (この部分が「同じ条件を適用」)。同名 file の内容交換 (走査 hit の増減) は predicate では捉えず、E3b と同じ single-tenant の残余として D に明記する (親が docs に書く。fix 子は docs を触らない)。`fresh_validated` とその一致検査、`v2-execution: launch-validate:` の campaign-start refusal 経路は削除する。解決回数は成功経路で 2 回 (gate 後 + campaign-start 前) を維持。15 refusal-return pin を維持。

帰結の test 変更 (未 land の wave test なので編集対象):
- `test_t080_delegated_campaign_start_rejects_late_hit`: 「同名 path の内容交換」は上の裁定により検出対象外。**namespace 外・非 ignored の新規 file を gate 後に追加する形**へ変える (列挙集合 digest が変わり predicate が None → 通常 scan → zero-hit 失敗 → resolution が `invalid` → epoch identity が変わり `migration-receipt-verify: receipt epoch が campaign-start 前に変化した` で refuse、WAL / evaluate 不到達)。名前を `test_t080_delegated_campaign_start_rejects_late_hit_file` に改める。
- `test_t080_delegated_campaign_start_rechecks_receipt[missing]`: receipt を unlink すると `inspect_receipt_history` が `issued-but-missing` になり epoch identity が変わる。期待は epoch refusal のまま (再 launch を消せば走査失敗が先行しない)。predicate は列挙集合 (git ls-files 由来) が不変なら token の report を返すので走査は起きないはずだが、**現物で確かめ**、走査が起きて別理由になるなら報告 (期待値は緩めない)。
- 変異 m11 は登録から外す (再走査が無い)。m5 の kill 証拠は `[changed]` と既存 `test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4`。`[missing]` は単独証拠から外す (RA の帰属表)。

## F2. 接続 fixture の build seam (RA-2 / RB-1)

`test_s8b_ratified_freeze.py:_make_emitter_build` の `compiler_input_rel = "fixture.txt"` を引数化する (既定は `fixture.txt` で固定 fixture の挙動不変)。接続 fixture (`_build_t080_active_v2_repo` → `build_production_emitter_g1(..., receipt_root=...)`) は、fixture が checkout した実 ccbench pin に**実在する tracked regular file** (例: `CMakeLists.txt`。存在を `git ls-tree` で確認して選ぶ) を渡し、manifest hash は実際に渡した source root の bytes から作る。実 submodule へ `fixture.txt` を追加しない、pin を変えない、検証 API を stub しない。修正後、接続 8 node が fixture 構築のどの段まで進むかを直接呼出しで追い (socket 拒否で止まる段があればその段名と例外を報告)、次に出る拒否を「緑予測」に織り込まない。

## F3. `[missing]` と受理順序 (RA-3 / RB-2) — F1 で解消。F1 の裁定どおり実装したうえで現物確認。

## F4. 変異の帰属 (RA-4)

- m8b (`_draft_reconstruct_holdout` の `search_assertion` 除去) は後段 `verify_document` の `_assert_search_pass` と非空 hit 拒否に mask される → **単独変異の証拠から外す** (親が台帳に「冗長 gate」と記録)。draft 負例 test は残す (実機構の負例として価値あり)。
- m2b (`_campaign_t080_value` の invalid 受理) を観測する負例を追加: `test_s8b_oracle_driver.py::test_run_block_refuses_invalid_receipt_after_gate_seam` — 既存 seam (`_gate_check_validated` を allowed=True に、`_resolve_t080_receipt` を `state="invalid"`・refusals 非空の合成 resolution に) で `run_block` を呼び、`status == "refused"`、refusals が `migration-receipt-verify: T-080 campaign epoch を active-valid/never-issued のどちらにも固定できない` を含む exact 集合、budget / marker / WAL / evaluate に到達しないことを要求。既存 `_run_with_real_manifest_gate` と同型の seam 利用 (機構本体は stub しない)。

## F5. floor e2e の期待 digest (RA-5 / RB-3)

`test_real_seal_protocol_to_floor_official_core_e2e` の `expected_clean_digest` の allowlist 項に、clone に**残存する chain record** (`_CHAIN_RECORD_PATTERNS` に一致する path。production の返値を使わず、clone の tracked file を独立に列挙して正規表現で選び sha256 を取る。既存 unit test `test_clean_scan_digest_binds_recognized_chain_record_path_and_bytes` と同じ規則) を加える。preflight 用 `expected_allowlist` (`allowlist == expected_allowlist` の比較対象) は `frozen_paths` のまま分ける。`clean_calls` の回数 2・両 digest の完全一致・production の `clean_scan_digest` / `_assert_freeze_allowlist` は不変。chain 無し木では chain record が無いので期待値は bit 同一。G を S に足さない。

## F6. sink 行番号 pin (RA-6 / RB-4)

`test_ccbench_spawn_sites.py:3460` 付近の `_BuildSink("orchestrator/campaign/s8b_oracle_driver.py", "<module>.run_block", 1775, "campaign")` を同じ `pipeline.evaluate(` 呼出しの**最終差分後の行番号**へ追随 (1803 側の `evaluate_fn` sink も最終行番号で再確認)。`Counter({"covered": 38})`・kind・scope・`failures == []` は不変。F1 で driver の行が減るので、driver の編集を終えてから両 pin を確定する。

## F7. 非層 2 負例の単一理由 (RB-5)

`test_t080_active_v2_preserves_nonlayer2_receipt_refusal` は、R trailer 不正の単一理由 (`receipt.user_commit_trailer`、既存 f28 と同型) を exact に固定し、公開 `gate_check` にも同じ完全な拒否集合を要求する。fixture の別拒否を期待集合へ足して通さない。同様に `test_t080_failed_launch_preserves_receipt_refusal` と `test_v1_gate_does_not_delegate_with_active_v2` の `any(...)` は、可能なら完全集合の一致へ強める (fixture が別理由を出すなら fixture を直す)。

## F8. 実 root reader の登録簿 (RB-6)

新接続 8 node + draft 負例 + `test_run_block_refuses_invalid_receipt_after_gate_seam` (実 root を読まないなら不要) について、実親 repo (P) / 共有 ccbench (S) を読む test を conftest の resource 登録簿 (`_REAL_REPO_NODE_INVENTORY` 等、既存 `test_t080_stub_free_*` と同じ分類) と `test_real_repo_serialization.py` の独立 golden に追随させる。新しい台帳・lock 機構は作らない。

## F9. serialization 負例の件数 (RB-7)

`test_receipt_memo_consumer_inventory_and_optouts_are_complete` の合成負例で `node_count=35` を正しい値に直し、集合だけを壊す形にする。lazy test の非 consumer 対照に「今回外した元 consumer (例: `test_success_wal_order_budget_and_evaluate_contract`) だけを選ぶ」ケースを足し、prewarm 不発火を要求する。残存 consumer の起動条件・worker 禁止は弱めない。

## F10. 所有外の callers 再確認

`_holdout_layer2_delegation` / `_verify_holdout_live_scan` / `verify_receipt` / `static_gate_adapter` / `_resolve_t080_receipt` の signature 変更に対する caller (driver、`s8b_holdout_freeze.py:1210` 付近、memo、driftguards、serialization の生成 script、test の lambda) を再列挙し、keyword 省略時の挙動が基点と同じことを確認。

## 対応表の書き方

所見 ID (RA-1 … RB-7、F1 … F10) ごとに closed / partial / regressed と変更箇所 (file:関数) を書く。実走できない項目は「実装済み・未実走」。
