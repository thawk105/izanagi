## 総括

親 render の手動 bytes 混入疑いは refuted です。両 adapter は現 worktree の `expected_adapters()` と byte 完全一致しました。  
各 adapter の変更は指定された 4 pointer だけで、再帰 key/container 構造、mode、runtime activation、consumer、schema、frontmatter 由来 field は不変です。  
render 自体と pin 閉包に must-fix はありません。must-fix は、親の予定した consumer test 集合から実 role bytes を読む 1 node が漏れていることです。  
pytest は実行しておらず、期待赤集合と consumer 影響は静的検査結果です。

## must-fix (成果物影響を 1 行で必ず添える)

### MF-1: consumer test 1 node の実走対象漏れ

見立て: **real**。

`orchestrator/tests/test_claude_transport.py::_DeepCopyReceiptFixtureProvider.__init__` は `A.FixtureRoleProvider(role)` を生成します。そこで `ROLE_FILES["planner"]` の `.claude/agents/planner-v4.md` を `read_bytes()` し、変更された SHA を provenance に流します。親の予定した 5 file に次の node がありません。

`orchestrator/tests/test_claude_transport.py::test_success_consumer_keeps_valid_receipt_in_journal_and_report`

この node は SHA literal 自体を pin する検査ではありませんが、変更された planner role bytes を読み、その provenance が journal/report consumer を通る経路を検査します。親の実走集合へ追加すべきです。

成果物影響: 通過時に certified 選択値、材料レポート値、試行台帳値、受理集合を変える意図はなく、受入証拠の consumer 参照集合だけが 1 node 増えます。失敗時は現成果物を受理できません。

## 親 render の独立検証 (byte 一致 / 4 pointer / key set)

### `render_adapters.py` が書込み前に行う検算

見立て: **refuted**。現在の生成物へ人手 bytes が混入した証拠はありません。

1. hard-code された正しい worktree を `sys.path` の先頭へ置き、その worktree の `orchestrator.codex_roles.spec` を import。
2. `expected_adapters(WT)` を loop 前に全体計算。source、manifest、ledger、schema pin の不整合は renderer 内で例外になります。
3. 対象を `coder-v4-autonomous` と `planner-v4` の 2 件に限定。
4. 各 target path が renderer の expected inventory に存在することを確認。
5. target が symlink ではなく通常 file であることを確認。
6. `git -C WT show HEAD:<adapter path>` を `check=True` で取得。
7. HEAD JSON と expected JSON を parse。
8. scalar leaf の pointer 集合が同じであることを確認。
9. 値が変わる pointer 集合が次の exact 4 件であることを確認。

   - `/developer_instructions`
   - `/review_ledger/source_file_sha256`
   - `/semantic_digest`
   - `/source/sha256`

10. 上記を通った target だけに、加工していない `expected[path]` を `write_text(..., encoding="utf-8")`。
11. pointer 不一致が 1 件でもあれば最終的に rc=2。

例外を握り潰す処理はありません。比較を通らずに `write_text` へ達する分岐もありません。`changed != POINTERS` は入力から計算されており恒真ではありません。また書込み値は手入力値ではなく `content = expected[path]` そのものです。

独立 byte 再計算の実測:

- coder-v4-autonomous
  - actual bytes: 9719
  - expected bytes: 9719
  - actual SHA-256: `70cb1be6d2e067a751b70618ca20d8bf44f23b6c157f0445b9af50854372b54a`
  - expected SHA-256: `70cb1be6d2e067a751b70618ca20d8bf44f23b6c157f0445b9af50854372b54a`
  - byte equality: `True`

- planner-v4
  - actual bytes: 8532
  - expected bytes: 8532
  - actual SHA-256: `963034a11ff1ec88681405a565ef117ce01e9fd0e9095b58a3cec0ed5a21adce`
  - expected SHA-256: `963034a11ff1ec88681405a565ef117ce01e9fd0e9095b58a3cec0ed5a21adce`
  - byte equality: `True`

HEAD と現在版の独立した再帰比較結果は、両方とも leaf pointer set、全 container/leaf pointer type、再帰 key/index set、top-level key order が一致しました。HEAD の duplicate key も独立 strict parse で 0 件です。

field 差分:

- coder-v4-autonomous
  - `/developer_instructions`: 埋込み例の `delta_pct: -1.2` だけが `delta_pct: null` へ変更
  - `/review_ledger/source_file_sha256`: `4073ac4223eaca9c353685f116a4dfb53db5b3412011373b717c44e3b25ec10d` から `ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806`
  - `/semantic_digest`: `564287c890c1e29bf2b0e85f118ad5021b8154121eef224d35ccf63cdc0057c7` から `4e8cd61cf2ae1ea8bc63cee16a67e1697dad2e3a93323f935a97d4e724500150`
  - `/source/sha256`: `4073ac4223eaca9c353685f116a4dfb53db5b3412011373b717c44e3b25ec10d` から `ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806`

- planner-v4
  - `/developer_instructions`: 埋込み例の `last_delta_pct: -1.2` だけが `last_delta_pct: null` へ変更
  - `/review_ledger/source_file_sha256`: `0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e` から `3a3d35fafbaaeac5b63c8f36a1cd4542fba4e7cef2793c71cc59fc40884c8374`
  - `/semantic_digest`: `ac06f0f644b3e4b0964d39bd2aaa9f116e3e116343b0a33050ddabb3d44bbe1f` から `6a995668fe9eaadf83764fb1e5467e3e1ff5901f151214a327d2305d83dbcd22`
  - `/source/sha256`: `0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e` から `3a3d35fafbaaeac5b63c8f36a1cd4542fba4e7cef2793c71cc59fc40884c8374`

したがって `mode`、`runtime_activation`、`consumer`、`consumer_contract`、input/output schema、`source.description`、`source.model`、`source.effort`、`source.tools`、adapter model/reasoning effort は動いていません。

repo 内混入の見立て: **refuted**。`git status --short --untracked-files=all` は対象 6 file だけ、`git ls-files '*render_adapters.py'` と worktree 全体の `find` は 0 件でした。script の実体は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2249-role-example-delta/artifacts/render_adapters.py` で、作業 root 外です。

揮発 payload の見立て: **refuted**。追加された期待値は `null`、role source SHA、semantic digest、baseline 移行 SHA だけです。working tree hash、時刻、絶対 path、process id は adapter/test payload に追加されていません。`2026-09-09` は review ledger の source comment だけで、renderer payload へ入りません。

成果物影響: adapter identity と将来の planner provenance SHA は新値へ更新されますが、certified 選択値、runtime 受理集合、schema、consumer 契約は不変で、既存試行台帳は書き換わりません。

## 旧 sha の残存箇所 (live / 歴史記録の分類つき)

検索 command は各値について次の形です。対象集合は worktree 配下の tracked、untracked、ignored text 全体で、`.git/**` だけを除外しました。

`rg --hidden --no-ignore -o --glob '!.git/**' "$value" . | wc -l`

実測件数:

- 新 coder SHA `ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806`: 3
- 新 planner SHA `3a3d35fafbaaeac5b63c8f36a1cd4542fba4e7cef2793c71cc59fc40884c8374`: 4
- 旧 coder SHA `4073ac4223eaca9c353685f116a4dfb53db5b3412011373b717c44e3b25ec10d`: 0
- 旧 planner SHA `0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e`: 8

旧 planner SHA の全残存箇所:

- `orchestrator/tests/test_reflux_originless_compatibility.py:372` — 7 occurrences。変更禁止の `_PRE_WAVE_ORIGINLESS_BASELINE` 内にある移行元 fixture。
- `orchestrator/tests/test_reflux_originless_compatibility.py:602` — 1 occurrence。T-2249 helper の `old` anchor。

これは stale live pin ではありません。module import 後の有効 baseline を実測すると、旧 SHA scalar は 0、新 SHA scalar は 7 でした。helper は journal 6 row と report 1 scalar run を新値へ変換し、件数を assert しています。

歴史記録分類:

- `output/insights/`: 旧 2 SHA とも 0
- `docs/archive/`: 旧 2 SHA とも 0

見立て: **refuted**。追随漏れの live copy はありません。

成果物影響: originless の有効期待 baseline は新 planner SHA を受理し、旧 baseline literal は移行元証拠として保持されます。certified 選択値と既存の歴史試行台帳は変わりません。

## 変異 anchor の一意性検算 (一意な anchor 文字列を明記)

見立て: **refuted**。anchor 不成立はありません。以下はそのまま `replacements` 要素にできる JSON で、現在差分に対する各 `old` count は全て 1 です。各 mutation が 1 replacement なので、累積適用後の一意性も同じです。

```json
{"file":".codex/role-adapters/coder-v4-autonomous.json","old":"\"path\": \".claude/agents/coder-v4-autonomous.md\",\n    \"sha256\": \"ba6c9c116fadf0d21a3e55acf1fdcaf83c412c869fcbfdf59dfad842cbfcf806\"","new":"\"path\": \".claude/agents/coder-v4-autonomous.md\",\n    \"sha256\": \"4073ac4223eaca9c353685f116a4dfb53db5b3412011373b717c44e3b25ec10d\""}
{"file":".codex/role-adapters/planner-v4.json","old":"\"path\": \".claude/agents/planner-v4.md\",\n    \"sha256\": \"3a3d35fafbaaeac5b63c8f36a1cd4542fba4e7cef2793c71cc59fc40884c8374\"","new":"\"path\": \".claude/agents/planner-v4.md\",\n    \"sha256\": \"0893644a9eae73a18fcf822c582f6007e8795f314fc1c97a3db7a6d8d439cb0e\""}
{"file":".codex/role-adapters/coder-v4-autonomous.json","old":"\"semantic_digest\": \"4e8cd61cf2ae1ea8bc63cee16a67e1697dad2e3a93323f935a97d4e724500150\"","new":"\"semantic_digest\": \"564287c890c1e29bf2b0e85f118ad5021b8154121eef224d35ccf63cdc0057c7\""}
{"file":".codex/role-adapters/planner-v4.json","old":"\"semantic_digest\": \"6a995668fe9eaadf83764fb1e5467e3e1ff5901f151214a327d2305d83dbcd22\"","new":"\"semantic_digest\": \"ac06f0f644b3e4b0964d39bd2aaa9f116e3e116343b0a33050ddabb3d44bbe1f\""}
{"file":".codex/role-adapters/coder-v4-autonomous.json","old":"{ \\\"iteration\\\": 1, \\\"result\\\": \\\"fail\\\", \\\"delta_pct\\\": null }","new":"{ \\\"iteration\\\": 1, \\\"result\\\": \\\"fail\\\", \\\"delta_pct\\\": -1.2 }"}
{"file":".codex/role-adapters/planner-v4.json","old":"\\\"last_delta_pct\\\": null","new":"\\\"last_delta_pct\\\": -1.2"}
{"file":"orchestrator/tests/test_reflux_originless_compatibility.py","old":"_extend_t2249_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)\n","new":""}
```

対応は上から M4-C、M4-P、M5-C、M5-P、M2-C、M2-P、M6 です。

特に M4 の `source/sha256` は SHA literal 単体を anchor にしていません。直前の固有 `source.path` と組にしているため、同値の `/review_ledger/source_file_sha256` を誤変異しません。

`tools/mutation_harness.py` は `new=""` を禁止していません。`new` は文字列かつ `old` と異なればよいため、M6 の helper call 除去はこの形式で実行可能です。

成果物影響: mutation spec の anchor count は全 mutation で `{"0":1}` となり、試行台帳には一意な injection evidence を記録できます。certified 選択値と通常受理集合は変わりません。

## 期待赤 node の検算

見立て: **refuted**。段 4 裁定の期待赤集合は静的読解上 complete です。

- M4-C、M4-P:

  `orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty`

  `source.sha256` 単独変異は renderer byte parity を壊します。一方、`test_all_adapters_pin_model_policy_and_blocked_runtime_activation` が見るのは `review_ledger.source_file_sha256` であり、top-level `source.sha256` ではありません。

- M5-C、M5-P:

  `orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty`

  `semantic_digest` を独立に読む別 test はなく、byte parity が拒否層です。

- M2-C、M2-P:

  `orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty`

  `orchestrator/tests/test_codex_agents.py::test_source_body_is_embedded_exactly_once_before_product_override`

  byte parity に加え、現在 source body が developer instructions 内に exact 1 回存在するという検査が 0 回になり、2 層が赤になります。

- M6:

  `orchestrator/tests/test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set`

  helper call を除くと pre-wave baseline の旧 planner SHA が残り、現生成物を投影した baseline equality が崩れます。この baseline と比較する assert は同 node 内です。

成果物影響: mutation 試行台帳の期待 status は 7 件とも `KILLED` のままで、failed node 完全集合も裁定値から変更不要です。実走していないため KILLED を観測済みとは主張しません。

## consumer の漏れ (nodeid)

見立て: **real**。漏れは次の 1 node です。

`orchestrator/tests/test_claude_transport.py::test_success_consumer_keeps_valid_receipt_in_journal_and_report`

参照関係:

`.claude/agents/planner-v4.md`  
→ `p3_autonomous_workload_trial.ROLE_FILES["planner"]`  
→ `FixtureRoleProvider.__init__().role_file_sha256`  
→ `_DeepCopyReceiptFixtureProvider`  
→ 上記 test の journal/report provenance

親の 5 file 内では、`test_p3_autonomous_workload_trial.py` が同じ `FixtureRoleProvider` 経路を多数通るため主要 coverage はありますが、transport receipt を合成した provenance consumer は上記 node 固有です。

継続子が挙げた 2 file の判定:

- `test_effort_levels.py`: **不要**。`spec` を import しますが、使うのは `ROLE_MANIFEST_CODEX_REASONING_EFFORTS` 定数だけです。`load_role_specs()`、変更した ledger 値、role bytes、adapter bytesを読みません。import/syntax health は `test_codex_agents.py` の方が強く検査します。
- `test_role_session_isolation.py`: **不要**。`A.ROLE_FILES` について検査するのは key 順だけで、fake provider は role file を読みません。`_complete_trial` も synthetic provenance を作り、実 role bytes を参照しません。

成果物影響: 漏れ node の追加は受入証拠の参照集合だけを増やします。通過時に certified 選択、材料レポート、試行台帳の値は変わりません。

## nit / backlog

### render script の構造比較は完全な key-set proof ではない

見立て: **real、nit**。現在 bytes は独立検査で正しいため must-fix ではありません。

`flat()` は scalar leaf だけを記録するため、空 dict/list の追加・削除を key-set 差分として検出できません。また key の `/` を escapeせず、array index を `[0]` 形式にするため、一般入力では pointer collision の余地があります。通常の `json.loads` なので HEAD の duplicate key も script 自身では拒否しません。

今回は独立に次を確認したため実害は refuted です。

- HEAD duplicate key 0
- recursive container/key/index set 一致
- container/leaf type 一致
- actual bytes と renderer bytes の完全一致

将来は strict JSON decoder、RFC 6901 escape、空 container を含む構造 map を用いると証明が直接的になります。

成果物影響: 現成果物の値・受理集合・参照は変わりません。将来の render evidence の強度だけを上げる backlog です。

### 2 target の事前検算が transaction ではない

見立て: **real、nit**。各 file の byte 完全性を迂回する問題ではありません。

coder を検算して書いた後に planner の pointer 検算が失敗し得るため、script は全 target preflight 後の一括 render ではありません。また書込み後の read-back と fsync はありません。今回は事後の独立 byte 比較で両 target とも一致しています。

成果物影響: 現成果物への影響はありません。将来の途中失敗時に partial working tree を残し得るだけで、正しさ gate を緩めない改善対象です。

## 未確定・要裁定

ユーザー裁定が必要な事項はありません。

動的に未確定なのは pytest 結果です。段 5 報告では親の 5 file は全て `tools/run_tests.py` rc=16、`child_started=false` で未実走でした。本レビューでも pytest は実行していません。親は既定 5 file に上記 `test_claude_transport.py` の 1 node を加えて実走する必要があります。