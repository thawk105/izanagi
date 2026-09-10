## 変更面

行番号は現 HEAD 基準。scope 1〜3 を単一 commit・単一テスト集合として実装する。

| file | 行番号 / 関数 | 現行の挙動 | 変更後の挙動 |
|---|---:|---|---|
| [knowledge_manifest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/knowledge_manifest.py:54) | `KnowledgeManifest`、`canonical_value` | `knowledge_level` と非空 `sources` だけを持つ。 | optional な `declared_scope` と `retrieval_result` を追加する。旧 2-key 形では両方 `None` とし、canonical JSON から省略して旧 digest を byte-exact に保つ。 |
| 同上 | `_parse_value` L186-214 | top-level exact keys は `{knowledge_level,sources}`、空 `sources` は無条件 reject。 | 旧形と拡張形の tagged union にする。旧形は引き続き非空必須、拡張形だけ `sources=[]` を許す。 |
| 同上 | `_parse_value` 周辺の新 helper | 宣言範囲・取得実績の表現がない。 | `declared_scope={retrieval:[scope-entry...],injection:[scope-entry...]}` を追加する。scope entry は exact `{kind:"repo_artifact"|"web", selector:<nonempty string>}`、両配列を非空・重複なし・canonical sort とする。 |
| 同上 | 同上 | 空が正常終了か失敗かを区別できない。 | `retrieval_result={status:"completed_empty"|"completed_nonempty",result_count:N}` を追加する。`result_count == len(sources)`、`completed_empty ⇔ N==0` を強制する。 |
| 同上 | `resolve_live_sources` L301-333 | parser を通った source を解決する。空には到達しない。 | 拡張形の正当な空は subprocess を増やさず、そのまま空の `ResolvedKnowledgeManifest` にする。非空 source の Git/UTF-8/SHA 検査は不変。 |
| 同上 | `planner_projection` L344-360 | 検証済み `sources` を role input に載せる。 | wire keys は変えず、正当な空では `sources: []` を出す。宣言範囲は role 自己申告へ混ぜず、親の proof chain に保持する。 |
| 同上 | `receipt_value` L363-417 | 常に `knowledge-manifest-receipt/v1`。 | 旧 manifest は v1 の既存 bytes を再生成する。拡張 manifest は `v2` とし、`canonical_manifest.declared_scope` と `.retrieval_result` を digest 内に保持する。top-level `sources` は従来どおり検証済み実投入 source。 |
| [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/wal.py:101) | receipt schema 定数 | v1 だけを認識。 | v1/v2 を明示的に認識する。v1 exact shape と非空制約は変更しない。 |
| 同上 | `_knowledge_manifest_digest` L705-731 | 非空 `sources` だけから旧 manifest digest を再導出。 | 旧引数形では非空を維持する。拡張形では scope/result を closure 内で形状検査し、これらを含む canonical manifest を再 hash する。空は `completed_empty/result_count=0` のときだけ受理する。 |
| 同上 | `_checked_knowledge_provenance` L734-762 | WAL payload は `{knowledge_level,knowledge_manifest_sha256,sources}`。 | v1 payload は従来形のまま。v2 payload は `declared_scope` と `retrieval_result` を追加し、全体を lock の既存 manifest digest と照合する。 |
| 同上 | `_validated_knowledge_receipt` L817-920 | v1 exact receipt、canonical/verified source の非空・一致を要求。 | schema version で分岐する。v1 は無変更、v2 は拡張 canonical manifest と空の verified source 配列を許し、scope/result/source/digest の整合を検査する。Git object の再解決は追加しない。 |
| 同上 | `_append_record` L1037-1090、`validate_knowledge_provenance_bindings` L923-952 | BUILD_START へ旧 provenance を自動投入し、replay 時に検査。 | v2 では scope/result を含む provenance を receipt から BUILD_START へ写す。呼び手供給値との一致、replay 検査も同じ拡張形にする。 |
| 同上 | `knowledge_provenance_and_receipt_sha256_for_material_report` L955-995 | report 用に `declared_sources` と `injected_sources` を返す。 | v2 の場合だけ `declared_scope` と `retrieval_result` も返す。`declared_sources` は引き続き `canonical_manifest.sources`、`injected_sources` は verified sources 由来とし、scope の意味を既存配列へ転用しない。 |
| campaign lock | `_knowledge_lock_binding` L627-650 | `knowledge_level` と `knowledge_manifest_sha256` を束縛。 | 新 key は足さない。既存 digest が拡張 canonical manifest 全体を束縛するため、scope/result の重複格納や別 digest を作らない。 |
| [projection_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/projection_guard.py:28) | coder contract 定数 | 通常 implementation と trigger-wire の 2 mode。 | K2 専用 `CODER_CONTRACT_K2` を追加する。`coder` は role 出力そのもの `{proposal,knowledge_use,classification,data_boundary_report}`、その `proposal` は K2 role の exact required keys とする。 |
| 同上 | `assert_closed_proposal_schema` L283-341 | 全 backoff coder を同じ flattened schema で検査。 | K2 mode だけ wrapper と nested proposal を検査する。default mode、sort、trigger-wire の定数・分岐・受理集合は変更しない。 |
| [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/p3_s4_loop.py:1721) | `load_proposal_file` | flattened coder proposal を読み、role semantic policy は呼ばない。 | `knowledge_input=None` を default 引数に追加する。非 `None` のときだけ K2 contract を選び、`coder` の role wrapper を検査してから semantic validator を呼ぶ。 |
| 同上 | `load_proposal_file` 直前の新 `_consume_k2_coder_output` | K2 consumer がない。 | `result["proposal"]`、`["knowledge_use"]`、`["classification"]`、`["data_boundary_report"]` を明示的に読み、`validate_output_semantics("coder-v4-autonomous-k2", projected_input, result)` を実行する。manifest の consumer AST 検査点にもする。 |
| 同上 | `main` L2037-2081 | `_prepare_knowledge_campaign` が返す `_knowledge_input` を run 経路では捨てる。 | その実在変数を `load_proposal_file(..., knowledge_input=knowledge_input)` へ渡す。K2 判定を proposal の自己申告ではなく、trusted producer が解決した変数の有無で行う。 |
| [policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/codex_roles/policy.py:394) | `validate_output_semantics` | K2 index/重複検査は直接 unit test からしか到達しない。 | 述語本体は変えず、コメントを実 consumer 配線に合わせる。空 `sources` と空 `knowledge_use` は現状の述語で正当に通る。 |
| [manifest.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/codex_roles/manifest.json:733) | K2 role entry | `knowledge_input.sources.minItems=1`、`consumer:null`。 | K2 entry だけ `minItems` を外し、consumer を `p3_s4_loop.py` の新 K2 helper に設定する。他 role の schema bytes は変更しない。 |
| [coder-v4-autonomous-k2.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/.claude/agents/coder-v4-autonomous-k2.md:124) | 出力契約 | 自動 consumer は存在しないと記載。 | `load_proposal_file` の K2 経路で index/重複だけが自動検査されること、空投入なら `knowledge_use=[]` であることへ更新する。実利用・分類・data-boundary report の真偽は検査しない境界を維持する。 |
| [review_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/codex_roles/review_ledger.py:15) / [.codex adapter](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/.codex/role-adapters/coder-v4-autonomous-k2.json:1) | 旧 K2 source/schema/manifest と unwired consumer を pin。 | K2 の `SOURCE_FILE_SHA256`、input `SCHEMA_SHA256`、`ROLE_MANIFEST_SHA256` を review 更新し、renderer の期待値から K2 adapter だけを再生成する。runtime activation は blocked のまま。 |
| [layer3_schema.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/layer3_schema.json:28) | knowledge provenance の source 配列は双方 `minItems:1`。 | legacy 4-key shape は現状の `minItems:1` を維持する。拡張 6-key shape を追加し、`completed_empty` なら両配列を空固定、`completed_nonempty` なら両配列を非空とする。 |
| [layer3_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2246-k2-knowledge-closure/orchestrator/campaign/layer3_report.py:779) | WAL helper の projection をそのまま report に載せる。 | アルゴリズム変更は不要。v2 helper が返した scope/result を削らず、そのまま `knowledge_provenance` に運ぶことを回帰テストで固定する。 |

拡張 manifest の通る正例は次の形に固定する。

```json
{
  "knowledge_level": "K2",
  "declared_scope": {
    "retrieval": [
      {"kind": "repo_artifact", "selector": "output/insights/2026-09-03_*"}
    ],
    "injection": [
      {"kind": "repo_artifact", "selector": "all-successfully-retrieved-sources"}
    ]
  },
  "retrieval_result": {
    "status": "completed_empty",
    "result_count": 0
  },
  "sources": []
}
```

`selector` は digest に束縛される記録上の宣言であり、新しい allowlist や leak gate にはしない。

## 設計の択一

### 宣言範囲をどの欄で表すか

選択肢は、既存 `sources` を scope に読み替える案、新しい structured key を足す案、自由文一個だけを足す案の三つ。

推す案は新しい `declared_scope` と `retrieval_result` を足す案。

- manifest: `declared_scope`、`retrieval_result`、`sources`
- receipt v2: `canonical_manifest.declared_scope`、`.retrieval_result`、top-level verified `sources`
- campaign lock: 新 key なし。既存 `knowledge_manifest_sha256` が三者を含む canonical manifest を束縛
- BUILD_START: `knowledge_provenance.declared_scope`、`.retrieval_result`、`.sources`
- material report: `knowledge_provenance.declared_scope`、`.retrieval_result`、`.declared_sources`、`.injected_sources`

`manifest.sources`、receipt top-level `sources`、WAL `sources` の wire 上の出所は変えない。いずれも concrete な取得・投入 source であり、許可範囲の意味を新 `declared_scope` にだけ持たせる。材料レポートの歴史的な `declared_sources` も canonical manifest の concrete `sources` 射影として残し、「許可範囲」とは呼ばない。

既存 `sources` の意味を scope に変更する案は、空取得時に scope 自体まで空に見え、D1429/D1570 の差を表現できないため却下する。単一自由文案は取得範囲と投入範囲を分離できず、canonical ordering や重複検出もできないため却下する。

### 既存 K2 campaign の identity 連続性

保てる設計は、旧 `{knowledge_level,sources}` を独立した legacy variant とし、新欄を canonical JSON から省略する設計。現行 2 source の canonical bytes と digest `6d8674228d05e591a67047c4a098e077f427cb7dd6fdfa3b82d20da2000db406` が変わらず、search config も同じなので `p3-s4-loop-s4-autonomous-b6dde2ef` を維持できる。

保てない設計は、旧 manifest 読み込み時に `declared_scope` と `retrieval_result` を合成して必ず canonical JSON に入れる設計。digest が変わり、campaign suffix も変わる。

推すのは前者。新しい空取得 campaign は新 digest/new identity になる一方、既存 campaign は byte identity を保持できる。新欄を digest 対象外にして identity だけ保つ案は、scope/result が campaign lock に束縛されなくなるため却下する。

なお `wal.py` の bytes 更新により、旧 lock の recorded contract-loader closure と現 HEAD が異なる可能性はある。これは verifier epoch/conformance の問題であり、manifest digest や campaign ID の改名理由にはしない。

### 受領証の schema 版

選択肢は v1 を二形対応にする案と、旧形 v1・拡張形 v2 に分ける案。

推すのは `knowledge-manifest-receipt/v2` の追加。記録内容と canonical manifest の意味が増えるため、同じ v1 literal で二つの exact schema を表すべきではない。

互換方針は次のとおり。

- legacy manifest からは引き続き v1 の同一 bytes を生成する。
- WAL reader は v1 exact shape を従来どおり受理する。
- v2 だけ scope/result と空 verified sources を受理する。
- v1 の空 sources、v2 の partial field、status/count/source の不一致は拒否する。

版を上げない案は、既存 v1 の exact-key 契約と「schema version が内容を識別する」という性質を壊すため却下する。

### 接続点

選択肢は `load_proposal_file` 内、`main` 側、親セッションだけでの検査。

推すのは `load_proposal_file` 内。K2 coder output が CoderProposal へ縮退して自己申告欄を失う直前の、唯一の実 consumer だからである。呼び手側だけでは別 caller が検査を忘れられる。

K2 判定は role output の `classification` や `knowledge_use` では行わない。`_prepare_knowledge_campaign` が解決済み manifest から返す `knowledge_input` が `None` でないことだけで判定する。

`validate_output_semantics` へ渡す minimal `projected_input` は次の実在値から作る。

- `knowledge_input`: `knowledge_manifest.planner_projection(resolved)` の戻り値
- `planner_direction`: 同じ proposal file の検査済み `d["planner"]`

`baseline`、`leakproof_context`、`whiteboard` を空値で捏造しない。今回の semantic predicate が読むのは planner direction と knowledge source index 集合だけなので、この二欄を「semantic projection」として渡す。full coder input 全体を再証明したとは主張しない。

K2 の `coder` は `.claude/agents/coder-v4-autonomous-k2.md` の出力 wrapper をそのまま格納する。これにより parent 側の独自 flattening を増やさず、次の正例を直接 consumer に入れられる。

```json
{
  "planner": {
    "axis": "silo-backoff-magnitude",
    "direction": "increase",
    "magnitude": "small"
  },
  "coder": {
    "proposal": {
      "axis": "silo-backoff-magnitude",
      "value": 20,
      "implementation": "double now_backoff = 20;",
      "justification": "fixture",
      "confidence": "medium"
    },
    "knowledge_use": [],
    "classification": "de_novo",
    "data_boundary_report": {
      "instruction_like_content_detected": false,
      "details": "knowledge_input.sources の空配列を走査した"
    }
  }
}
```

role の `classification` は検査後に捨て、receipt を生成した caller classification を変更しない。

### K0 / K1 と他 coder role の 1-bit 不変

構造的に次の四点で保証する。

- `assert_closed_proposal_schema` の default は現行 implementation mode のまま。
- K2 mode は `knowledge_input is not None` の branch からだけ渡す。
- sort/trigger loader は K2 mode を参照せず、各既存 contract を維持する。
- role manifest/schema/adapter の変更は `coder-v4-autonomous-k2` entry だけに限定する。

明示回帰として、manifest 不在の cfg hash、通常 backoff の flattened proposal、sort、trigger-wire、各 loader の未知 key 拒否を現行期待値のまま再実行する。既存 node の assertion は変更しない。

### 材料レポート schema 版

新たな report v4 は作らず、v3 の `knowledge_provenance` 内を legacy/extended tagged union にする。既存 v3 knowledge report と既存テストの `minItems:1` 期待を保ち、新 v2 receipt 由来の shape だけ空を許せるためである。

全 knowledge object を無条件に `minItems:0` にする案は、裸の空配列まで通してしまうため却下する。

## テスト計画

| nodeid 候補 | 内容 |
|---|---|
| `orchestrator/tests/test_knowledge_manifest.py::test_completed_empty_retrieval_is_accepted_and_recorded` | 拒否: partial scope や取得失敗を正例へ混ぜない。受理: 上記 `completed_empty/result_count=0/sources=[]` を parse・resolve・v2 receipt まで通し、scope/result を確認する。 |
| `...::test_empty_sources_require_declared_scope_and_completed_empty_result[case]` | 拒否: scope 欠落、片側空、unknown status、count 非ゼロ、`completed_nonempty` と空 sources の組合せを拒否する。受理: 同じ parser が legacy 非空 manifest と拡張非空 manifest を従来どおり受理する。 |
| `...::test_extended_manifest_digest_binds_scope_and_retrieval_result` | 拒否: scope または result status だけ異なる manifest が同 digest になる実装を拒否する。受理: key/order だけ異なる同一 scope/source 集合は同 digest に canonicalize する。 |
| `...::test_legacy_k2_manifest_keeps_historical_digest` | 拒否: legacy 読み込み時に新欄を合成して digest を変える実装を拒否する。受理: 実 campaign の 2 source fixtureから exact `6d8674…406` を得る。 |
| `...::test_receipt_version_is_v1_for_legacy_and_v2_for_extended` | 拒否: 空 sources を v1 として発行すること、または legacy receipt を無条件 v2 化することを拒否する。受理: legacy は既存 v1 bytes、拡張は scope/result を持つ v2 を生成する。 |
| `orchestrator/tests/test_p3_s4_loop.py::test_extended_empty_receipt_binds_lock_wal_and_material_projection` | 拒否: scope/result の receipt・WAL 脱落、digest skew、BUILD_START 以外への provenance 配置を拒否する。受理: empty v2 receipt →既存 lock digest→BUILD_START→report helper の全段で同じ scope/result と空 source 配列を得る。 |
| `...::test_existing_k2_manifest_keeps_campaign_b6dde2ef` | 拒否: legacy canonicalization や search_config key の変更で suffix が変わる実装を拒否する。受理: digest `6d8674…406` から exact campaign ID `p3-s4-loop-s4-autonomous-b6dde2ef` を得る。 |
| `...::test_k2_load_proposal_accepts_declared_role_output_with_empty_sources` | 拒否: K2 wrapper を legacy flattened schemaへ誤送する実装を拒否する。受理: role 文書の宣言済み出力形と `knowledge_use=[]` を `load_proposal_file` で受理する。 |
| `...::test_k2_load_proposal_rejects_out_of_range_knowledge_use` | 拒否: source 1 件に対する `source_index=1` を loader 実経路で拒否する。受理: 同じ proposal の `source_index=0` と、空 sources に対する空 `knowledge_use` を受理する。 |
| `...::test_k2_role_classification_does_not_overwrite_receipt` | 拒否: role の自己申告 classification を receipt/campaign classification として採用する実装を拒否する。受理: role が別 literal を返しても caller が発行済みの receipt bytes は不変。 |
| `...::test_main_passes_resolved_knowledge_projection_to_proposal_loader` | 拒否: run 経路が `_knowledge_input` を再び捨て、legacy mode を選ぶ実装を拒否する。受理: `--knowledge-manifest` 時だけ同一 projection object を loader へ渡す。 |
| `...::test_non_k2_load_proposal_keeps_flattened_shape_and_rejects_k2_wrapper` | 拒否: manifest 不在で K2 wrapper/`knowledge_use` を受理することを拒否する。受理: 現行 flattened backoff proposal の返り値を byte/field 単位で維持する。 |
| `orchestrator/tests/test_codex_agents.py::test_coder_v4_k2_input_schema_accepts_empty_sources` | 拒否: `sources.minItems=1` の残存と、他 role schema への同緩和を拒否する。受理: K2 input schema だけが `sources=[]` を受理する。 |
| `...::test_current_sources_render_byte_exact_and_native_is_empty` | 拒否: manifest・review ledger・generated adapter・consumer status の drift を拒否する。受理: K2 adapter が `trusted-parser-wired` になっても runtime activation は blocked のまま。 |
| `orchestrator/tests/test_layer3_report.py::test_knowledge_report_projects_completed_empty_retrieval` | 拒否: report が scope/result を落とす、または空 actual sources を非空に捏造する実装を拒否する。受理: nonempty `declared_scope`、`completed_empty`、空の `declared_sources/injected_sources` を端から端まで出す。 |
| `...::test_schema_accepts_completed_empty_knowledge_provenance_specimen` | 拒否: extended branch に `minItems:1` が残る schema を拒否する。受理: producer 非依存の exact specimen が v3 schema を通る。 |
| `...::test_extended_schema_rejects_empty_sources_without_completed_empty_result` | 拒否: bare empty、`completed_nonempty`、count/source 不整合を拒否する。受理: legacy specimen は既存どおり両配列非空で通る。 |
| 既存 `...::test_schema_rejects_invalid_knowledge_source_shapes[empty-array]` | 拒否: 新 branch に便乗して legacy 4-key knowledge object の空配列を受理することを拒否する。受理: 既存非空 specimen の期待値は一行も変更しない。 |

焦点走候補は上記4 test fileに加え、既存 `test_p3_s4_loop.py` の proposal-loader、knowledge-WAL、identity node群。実行は親が `tools/run_tests.py` 経由で行い、この段では緑を主張しない。

## 変異事前登録の候補

すべて `CONTRACT_LOADER_RELATIVE_PATHS` 外へ照準する。`wal.py` 自体は変異対象にしない。

| ID候補 | 位置 / 変異 | 期待 | 期待 node | 単一理由性・遮蔽なしの根拠 |
|---|---|---|---|---|
| `t2246.m01` | `knowledge_manifest.py:_parse_value` の拡張空許可へ `or not sources` を再挿入 | KILLED | `test_completed_empty_retrieval_is_accepted_and_recorded` | 入力は valid JSON、scope/result も整合済みで、parser より前に拒否層がない。直接 parser 正例なので後段も関与しない。 |
| `t2246.m02` | `KnowledgeManifest.canonical_value` から `declared_scope` を除外 | KILLED | `test_extended_manifest_digest_binds_scope_and_retrieval_result` | 二 manifest はとも parser 受理済みで、差は scope だけ。hash assertion 以外の gate を呼ばない。 |
| `t2246.m03` | `receipt_value` の v2 `canonical_manifest` から scope/result を落とす | KILLED | `test_extended_empty_receipt_binds_lock_wal_and_material_projection` | receipt producer 自身には後付け自己検査を置かないため、最初の拒否は既存 WAL receipt consumer の exact v2/binding 検査だけ。WAL append 前に停止し、別 gateへ到達しない。 |
| `t2246.m04` | `projection_guard.py:assert_closed_proposal_schema` の K2 branch を legacy implementation branch に差し替え | KILLED | `test_k2_load_proposal_accepts_declared_role_output_with_empty_sources` | JSON、knowledge input、role output は全て正例。semantic policy も空/空を受理するので、closed-schema routing だけが失敗理由。 |
| `t2246.m05` | `p3_s4_loop.py:_consume_k2_coder_output` の `validate_output_semantics` 呼出しを除去 | KILLED | `test_k2_load_proposal_rejects_out_of_range_knowledge_use` | `source_index=1` は JSON型・closed key set・CoderProposal・ability tripwireを全て通る。source 配列長との cross-field policy だけが拒否可能。 |
| `t2246.m06` | `layer3_schema.json` の extended `injected_sources` に `minItems:1` を戻す | KILLED | `test_schema_accepts_completed_empty_knowledge_provenance_specimen` | producer/WAL を通さない standalone schema 正例であり、他層の拒否は存在しない。failure は該当 `minItems` のみ。 |
| `t2246.m07-control` | `layer3_report.py:build_report` の直後に `injected_sources = declared_sources` を挿入 | SURVIVED | — | canonical concrete sources と verified sources は v1/v2 とも receipt validator が一致を要求し、empty 時も双方空。この変異は新 `declared_scope` には触れず等価なので、gate の証拠から除外する。 |

`m07-control` は、D1559 が却下した emit payload からの独立抽出を復活させるものではない。既存二配列の出所差だけでは新しい allowed-scope/injected-source 差を証明できないことを確認する等価 control である。

## 残る不確実性

- 現行 producer には「外部取得を実行し、結果が本当にゼロだった」ことを独立に証明する retrieval receipt がない。今回の `completed_empty` は、非空 scope と count/source 整合を持つ caller/producer 宣言であり、取得行為の因果証明ではない。決めるには、実 K2 producer で制御された空 corpus/query を一度走らせ、scope/result/receipt の実物を固定して観測する必要がある。
- K2 role 新設後の実 `proposal.json` は一件もない。正例は role 文書の宣言済み output wrapper から作るが、配線発火の実証には同 role の live 出力を一件 `load_proposal_file` へ渡し、valid index と invalid index の両方を観測する必要がある。
- parent が coder に渡した full input のうち `baseline` と `leakproof_context` は harness 成果物として残っていない。今回の `projected_input` は semantic predicate が実際に読む二欄だけであり、full role input schema の E2E 証明ではない。
- `wal.py` 更新後、旧 campaign lock の recorded contract-loader closure は current closure と一致しない可能性がある。親の commit 後検査で旧 campaign の ID維持と verifier epoch 表示を別々に確認すべきである。
- read-only 段のためテストは実走していない。親が commit 後に焦点走、`check_codex_agents.py`、`check_docs.py`、provenance 監査を行う。

## 総括

旧 manifest/receipt は v1 と digest `6d8674…406` を byte-exact に残し、新しい v2 だけに structured scope と完了済み retrieval result を加える。  
新 digest を既存 campaign lockへ束縛し、scope/result を receipt→BUILD_START→材料レポートへ運ぶ。  
K2 role output は `load_proposal_file` 内の専用 contract でだけ受け、既存 semantic validator を実働化する。  
K0/K1・通常 backoff・sort・trigger の既存 schema branch は変更しない。  
最大のリスクは、`completed_empty` が現時点では取得行為の独立証明ではなく producer 宣言に留まる点である。