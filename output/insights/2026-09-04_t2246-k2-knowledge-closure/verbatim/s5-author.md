## 実装した変更

- [knowledge_manifest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/campaign/knowledge_manifest.py:75)
  - `declared_scope`、`retrieval_result`、receipt v2 を追加。
  - 空 source は両拡張欄と `completed_empty/result_count=0` がある場合だけ受理。
  - `result_count` と source 数は比較しない。legacy manifest と receipt v1 bytes は維持。
- [wal.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/campaign/wal.py:706)
  - v1/v2 receipt、拡張 BUILD_START provenance、replay、材料レポート射影を実装。
  - v1 の exact shape・非空制約を維持し、Git object 再解決は追加していない。
- [layer3_schema.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/campaign/layer3_schema.json:28)
  - legacy 4-key shape を維持し、拡張 provenance を tagged union として追加。
  - report schema version は v3 のまま。
- [layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/campaign/layer3_report.py:780)
  - アルゴリズムは変更していない。WAL helper の拡張返却値を既存経路がそのまま保持することをテスト化。
- [projection_guard.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/campaign/projection_guard.py:36)
  - K2 専用 `CODER_CONTRACT_K2` を追加。
  - wrapper と nested proposal の exact key 集合を検査。既定、sort、trigger-wire の分岐は不変。
- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/campaign/p3_s4_loop.py:1722)
  - `_consume_k2_coder_output` と明示 role routing を追加。
  - output schema → instruction-like anomaly → semantic policy の順で検査。
  - `--coder-role` を追加し、resolved knowledge projection を loader へ渡す。
- [policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/codex_roles/policy.py:497)
  - K2 semantic validator の実 consumer 配線にコメントを合わせた。述語は変更していない。
- [coder-v4-autonomous-k2.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/.claude/agents/coder-v4-autonomous-k2.md:127)
  - 自動 consumer、空 source、campaign-bound projection と実 role 入力の境界を記載。
- [manifest.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/codex_roles/manifest.json:788)
  - K2 role の `sources.minItems` だけを除去し、consumer を `_consume_k2_coder_output` に設定。
  - K2 以外の role entry hash は不変。
- [review_ledger.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/orchestrator/codex_roles/review_ledger.py:27)
  - K2 の source、description、input schema、full role manifest hash を更新。
  - output schema と `ROLE_IO_CONTRACTS` は実契約が変わらないため値を維持。
- 4 test file に新規 node と fixture 配線を追加した。

## 現行挙動との差 (受理・拒否)

- 変更前: manifest は非空 `sources` の legacy 形だけを受理。変更後: legacy は同じ受理集合を維持し、拡張形では正当に宣言された空取得も受理する。
- 変更前: receipt/WAL は v1 非空形だけを認識。変更後: v2 だけ scope/result と空 source を受理し、v1 は exact shape のまま。
- 変更前: Layer 3 の knowledge source 配列は常に非空。変更後: legacy は非空のまま、tagged extended shape のみ空を受理する。
- 変更前: base loader は flattened coder proposal だけを受理。変更後:両 marker がある場合だけ K2 wrapper を受理し、片側 marker は拒否する。
- 変更前: K2 semantic policy は production loader から未到達。変更後: K2 経路だけ `confidence`、source index、重複、論理 schema、instruction-like anomaly を検査する。
- 分類の矛盾、scope/source 包含、実取得の証明は新たな拒否条件にしていない。
- K0/K1、通常 backoff、sort、trigger-wire の既存受理・拒否挙動は変更していない。

## テスト

pytest node はすべて実装済み・未実走です。`tools/run_tests.py` は Pegasus dispatch infrastructure failure `rc=16` となり、pytest 子 process は起動していません。

- `test_completed_empty_retrieval_is_accepted_and_recorded`  
  拒否: 宣言欄のない空 legacy manifest。受理: 完全な completed-empty manifest の parse、resolve、v2 receipt。
- `test_empty_sources_require_declared_scope_and_completed_empty_result[...]`  
  拒否: 欠落・空 scope・status/count 矛盾。受理: completed-empty と source 数に依存しない取得件数。
- `test_extended_manifest_digest_binds_scope_and_retrieval_result`  
  拒否: scope/result を digest から落とす実装。受理: key/order だけ異なる同値 manifest。
- `test_receipt_version_is_v1_for_legacy_and_v2_for_extended`  
  拒否: legacy receipt の無条件 v2 化。受理: legacy v1 と拡張 v2 の分離。
- `test_nonempty_extended_manifest_fields_are_independently_optional`  
  拒否: 非空 source でも両拡張欄を必須化する実装。受理: scope-only と result-only の v2 manifest。
- `test_extended_empty_receipt_binds_lock_wal_and_material_projection`  
  拒否: scope/result が欠落した v2 receipt。受理: receipt、lock、BUILD_START、replay、report helper の全伝播。
- `test_k2_load_proposal_accepts_declared_role_output_with_empty_sources`  
  拒否: K2 wrapper の legacy 分岐への誤送。受理: empty sources、empty knowledge use、confidence 付き role output。
- `test_k2_load_proposal_rejects_out_of_range_knowledge_use`  
  拒否: source 1件に対する index 1。受理: 同じ出力の index 0。
- `test_k2_load_proposal_rejects_knowledge_use_item_without_use_field`  
  拒否: `use` 欄を欠く item。受理: `use` を持つ同一 item。
- `test_k2_load_proposal_rejects_declared_instruction_like_content`  
  拒否: instruction-like content を真と申告した出力。受理: 同じ出力の false 申告。
- `test_k2_load_proposal_requires_role_and_knowledge_marker_together[...]`  
  拒否: `coder_role` または `knowledge_input` の片側指定。受理: 両方 None の legacy flattened proposal。
- `test_main_passes_resolved_knowledge_projection_to_proposal_loader`  
  拒否: main が projection または role marker を捨てる配線。受理: resolved projection と K2 role の loader handoff。
- `test_knowledge_report_projects_completed_empty_retrieval`  
  拒否: report から scope/result を落とす経路。受理:空 source を捏造せず保持する report。
- `test_schema_accepts_completed_empty_knowledge_provenance_specimen`  
  拒否: legacy 4-key shape の空配列。受理: completed-empty の独立 extended specimen。
- `test_extended_schema_rejects_empty_sources_without_completed_empty_result[...]`  
  拒否: partial、矛盾、片側だけ空の provenance。受理: legacy 非空形と完全な extended 空形。
- `test_coder_v4_k2_input_schema_accepts_empty_sources`  
  拒否: K2 `minItems:1` の残存。受理: full K2 role input の `sources=[]`。

pytest 外の直接関数 probe では、指定8 node相当、legacy receipt、legacy Layer 3、既定/sort/trigger loader の正負例を実行し成功しました。これはpytest実走としては数えていません。

## 検査の結果

`python3 tools/check_codex_agents.py`:

```text
ERROR: /work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/.codex/role-adapters/coder-v4-autonomous-k2.json: rendered adapter byte parity drift。manifest/Claude sourceから再生成する
```

`py_compile`、両 JSON parse、`git diff --check`:

```text
STATIC_CHECKS_OK
```

焦点 pytest の実行結果:

```text
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/output/pegasus-dispatch/107aa0f954349bea9885c006e94643b9/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
```

この試行が作った dispatch 専用 directory は直後に全て除去済みで、`output/` には変更を残していません。

## 波及可能性

- `p3_s4_loop.main` 以外の `load_proposal_file` caller は両追加引数の既定が None のため legacy 経路を維持する。
- `test_p3_b4_closed_critic.py` などの共有 caller は引き続き flattened shape を使用する。
- WAL helper の consumer は `layer3_report.py` と artifact-admission 系。legacy provenance shape は維持したが、未commit closure drift による実走拒否は親 commit 前には起こり得る。
- `test_codex_agents.py::_fixture` へ新 consumer source を登録済み。
- 新 test は既存4ファイル内のため、plain-runner の test file 集合登録は不要。duration ledger には新 node の実測値がまだない。
- K2 adapter 更新後も runtime activation は blocked のまま。

## 未了・疑問

- `.codex/` が read-only mount のため [.codex/role-adapters/coder-v4-autonomous-k2.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2246-author/.codex/role-adapters/coder-v4-autonomous-k2.json) を更新できなかった。これが checker の唯一の finding。
- 期待 adapter bytes は `/tmp/coder-v4-autonomous-k2.json` に生成済み。SHA-256 は `1cfd7b75474193bff3e7bf4587bd48f1cf0e984f0b8404a1d7fb522a60fd4ccd`。
- 期待 adapter を使った一時 fixture では `check_codex_agents` の findings が空になることを確認済み。
- pytest は実装済み・未実走。親側で adapter 反映後、焦点走と全体検査が必要。

## 総括

拡張 manifest v2、空取得のWAL束縛、Layer 3 tagged union、明示K2 consumerを実装した。  
legacy v1 bytesと既定・sort・triggerの受理集合は維持した。  
指定8 nodeを含む正負テストを追加したが、pytestはdispatch失敗により未実走。  
最大の残リスクはread-only mountでK2 adapterだけ作業ツリーへ反映できず、checkerが未通過な点である。