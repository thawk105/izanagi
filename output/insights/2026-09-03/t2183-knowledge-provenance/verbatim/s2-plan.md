## 結論

推奨は次です。

- 材料レポートの `SCHEMA_VERSION` は v3 のまま据え置く。
- `knowledge_provenance` は schema の top-level property に追加するが、既存 v3 を読めるよう top-level `required` には加えない。新 producer は常に object または `null` を出す。
- 実投入集合は、manifest の宣言集合ではなく、`planner_context_payload()` が返した実 payload の `knowledge_input.sources` から抽出する。
- 実投入集合の canonical digest `knowledge_injected_sources_sha256` を `search_config` に加え、campaign identity に直接含める。
- 受領証は新規発行だけ `knowledge-manifest-receipt/v2` とし、既存 v1 の parser・WAL shape・bytes をそのまま残す。
- WAL v2 provenance は既存 `sources` を宣言集合として維持し、`injected_sources` を1欄だけ追加する。宣言集合と投入集合の一致・包含は検査しない。
- 親の分割案は source path 自体は素集合だが、単位 A に `p3_s4_loop.py` が欠けている。ここを編集しないと「実際に emit した集合」には到達できない。

## 正確な JSON 形

新しい材料レポート欄は top-level に次の1欄です。知識非対応 campaign では `null`、新 producer の知識対応 campaign では object を出します。

```json
{
  "knowledge_provenance": {
    "knowledge_level": "K2",
    "knowledge_manifest_sha256": "64 lowercase hex",
    "declared_sources": [
      {
        "kind": "repo_artifact",
        "identity": {
          "commit": "40 lowercase hex",
          "path": "repo/relative/path"
        },
        "sha256": "64 lowercase hex"
      }
    ],
    "injected_sources": [
      {
        "kind": "repo_artifact",
        "identity": {
          "commit": "40 lowercase hex",
          "path": "repo/relative/path"
        },
        "sha256": "64 lowercase hex"
      }
    ]
  }
}
```

Web source の wire shape は次です。

```json
{
  "kind": "web",
  "identity": {
    "url": "https://example.invalid/resource",
    "retrieved_at": "2026-09-03T12:34:56Z"
  },
  "sha256": "64 lowercase hex"
}
```

両配列は集合として canonical source bytes 順に整列し、identity 重複を拒否します。本文 `content_utf8` は材料レポート・受領証の `injected_sources`・WAL のいずれにも載せません。

実投入集合の campaign identity 用 digest は次に固定します。

```text
SHA-256(
  canonical_json_bytes(
    sort(injected_sources, key=canonical_json_bytes)
  )
)
```

`knowledge_manifest_sha256` は引き続き現在の `{knowledge_level, sources}` 全体の digest であり、上記 digest と役割を混ぜません。

## 実投入集合が確定する経路

現状の呼び出し順は次です。

1. [p3_s4_loop.py:1975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:1975) で `_resolve_knowledge_manifest_argument()` を呼ぶ。
2. emit 経路では [p3_s4_loop.py:1993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:1993) から `_prepare_knowledge_campaign()` を呼ぶ。
3. `_prepare_knowledge_campaign()` は現在、[p3_s4_loop.py:1129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:1129) で受領証を先に書き、[p3_s4_loop.py:1135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:1135) で `planner_projection()` を返す。
4. その後 [p3_s4_loop.py:2005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:2005) で `planner_context_payload(..., knowledge_input=...)` を呼ぶ。
5. 実際に `knowledge_input` が payload へ入るのは [p3_s4_loop.py:810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:810)〜813、ファイルへ emit するのは [p3_s4_loop.py:2008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:2008) です。
6. run-iteration 経路は [p3_s4_loop.py:2037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:2037) で `_prepare_knowledge_campaign()` を再度呼びますが、現在は返された `_knowledge_input` を捨てています。

したがって、現状の受領証は実 payload が組み上がる前に発行されており、実投入集合を証明できません。

変更後の順序は以下にします。

1. `_prepare_knowledge_campaign()` が `planner_projection(resolved)` を作る。
2. projection の source descriptor から仮の投入集合 digest を求め、`search_config.knowledge_injected_sources_sha256` に入れて cfg/layout を確定する。この抽出は `resolved.manifest.sources` を参照しない。
3. layout に対応する state をロードする。
4. `planner_context_payload()` を一度だけ呼ぶ。
5. 返された payload の `knowledge_input.sources` からもう一度 source descriptor を抽出する。
6. その digest と campaign identity の digest を照合する。この時点、すなわち `planner_context_payload()` が返った直後が「実際に投入した集合」の確定点です。
7. 照合済み集合で v2 受領証を create-only 発行し、その後 planner context を emit する。
8. run-iteration 経路は同じ cfg/layout を導出したうえで、既存 v2 受領証が expected bytes と一致することを実行前に要求する。受領証がなければ新規作成せず停止する。

これにより、宣言集合と投入集合が現在たまたま同じでも、実装上は別入力・別 digest・別検査になります。両集合の一致や包含は gate にしません。

## knowledge_manifest.py の変更

- [knowledge_manifest.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:186) の source parse 部分を `_parse_source_descriptor()` として切り出し、manifest parser と実 payload extractor の両方から再利用する。
- [knowledge_manifest.py:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:344) の `planner_projection()` は本文付き projection の生成だけを担当し続ける。
- その直後に以下を新設する。
  - `injected_sources_from_planner_payload(payload)`：`payload["knowledge_input"]` の exact keys、data boundary、level、manifest digest、source keys、`content_utf8` と `sha256` の一致を検査し、本文なしの canonical descriptor 集合を返す。
  - `knowledge_sources_sha256(sources)`：投入集合だけの canonical digest を返す。
- [knowledge_manifest.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:363) の既存 `receipt_value()`、[knowledge_manifest.py:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:420) の `receipt_bytes()`、[knowledge_manifest.py:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:433) の `write_receipt()` は v1 producer として bytes・引数を維持する。
- 同じ位置に `receipt_value_v2()`、`receipt_bytes_v2()`、`write_receipt_v2()` を新設する。共通の verified-source・claim-boundary 組立てだけ private helper に切り出す。
- `require_receipt_v2()` を新設し、run 経路では expected v2 bytes と既存 create-only artifact の完全一致だけを確認する。存在しない場合に作成してはならない。

v2 受領証の exact top-level keys は以下です。

```json
{
  "schema_version": "knowledge-manifest-receipt/v2",
  "knowledge_level": "K2",
  "knowledge_manifest_sha256": "…",
  "canonical_manifest": {
    "knowledge_level": "K2",
    "sources": []
  },
  "sources": [],
  "injected_sources": [],
  "declaration_status": "…",
  "planner_projection": {
    "payload_key": "knowledge_input",
    "data_boundary": "external_knowledge_is_data_not_instructions"
  },
  "claim_boundary": {
    "classification": "…",
    "de_novo_claim": false,
    "pilot_comparison_eligible": false
  }
}
```

既存 v1 はこのうち `injected_sources` が無い現在の exact shape のままです。

## wal.py の変更

- [wal.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:101) に `KNOWLEDGE_INJECTED_SOURCES_SHA256_SEARCH_KEY = "knowledge_injected_sources_sha256"` と v1/v2 receipt constants を追加する。
- [wal.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:627) の `_knowledge_lock_binding()` を次の3状態に拡張する。
  - level、manifest digest、injected digest が全て無い：knowledge-unaware。
  - level と manifest digest のみ：legacy v1。
  - 3つ全て：v2。
  - その他の部分集合：fail-closed。
- [wal.py:705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:705) の manifest digest 計算は宣言集合専用のまま維持し、隣に `_knowledge_sources_digest()` を新設して投入集合を独立に canonicalize する。
- [wal.py:734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:734) の `_checked_knowledge_provenance()` を lock binding の版で分岐させる。
  - legacy exact keys：`knowledge_level`、`knowledge_manifest_sha256`、`sources`
  - v2 exact keys：上記3つと `injected_sources`
  - v2 では `sources` から manifest digest、`injected_sources` から injected digest を別々に再導出する。相互比較はしない。
- [wal.py:810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:810) の `_knowledge_provenance_from_receipt()` を v1/v2 exact schema で分岐する。
  - injected digest のない legacy lock は v1 receipt だけを受理。
  - injected digest を持つ lock は v2 receipt だけを受理。
  - v2 receipt の `injected_sources` digest を lock と照合。
  - verified declared sources と canonical manifest の現行一致検査は維持する。
- [wal.py:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:901) の `validate_knowledge_provenance_bindings()` は版ごとの exact shape を全 BUILD_START に要求する。非 BUILD_START 禁止、knowledge-aware 欠落拒否、knowledge-unaware 混入拒否はそのまま残す。
- 直後に `knowledge_provenance_for_material_report()` を新設する。上記 validator を先に呼び、全 BUILD_START の normalized provenance が一意であることを確認して、材料レポート用の `declared_sources` / `injected_sources` 形へ変換する。
- [wal.py:978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:978) の BUILD_START writer は lock が legacy なら現在の v1 shape、injected digest を持つなら v2 shape を受領証から生成する。

これにより `_checked_knowledge_provenance`、`_knowledge_provenance_from_receipt`、`validate_knowledge_provenance_bindings` の既存検査を残したまま、その外側に新しい独立 digest 検査を追加できます。

## p3_s4_loop.py の変更

この file は親の単位 A に追加が必要です。

- [p3_s4_loop.py:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:794) の `planner_context_payload()` は引き続き実 payload の唯一の組立て口とする。`knowledge_input` はコピーせずに無検査で受けるのではなく、producer helper が検査済みの exact dict であることを確認する。
- [p3_s4_loop.py:1104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:1104) の `_prepare_knowledge_campaign()` から受領証書込みを外す。
- 同関数内で projection 由来の投入集合 digest を `search_config.knowledge_injected_sources_sha256` に加える。既存の level・manifest digest も維持する。
- [p3_s4_loop.py:1993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:1993) の emit 経路は `planner_context_payload()` を一度だけ呼び、その返値から実投入集合を抽出・identity digest と照合してから `write_receipt_v2()` を呼ぶ。
- [p3_s4_loop.py:2037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:2037) の run 経路では `_knowledge_input` を捨てず、`require_receipt_v2()` に渡す。emit 済み証拠がない direct run は WAL/build 効果の前に停止する。

## layer3_report.py の変更

- [layer3_report.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:46) の `SCHEMA_VERSION` は v3 のままにする。
- [layer3_report.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:255) の legacy v2 schema 派生では、新しい `knowledge_provenance` property も削除する。これにより v2 の旧 acceptance set を広げない。
- [layer3_report.py:711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:711) で読んだ decoded lock と、[layer3_report.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:749) の WAL snapshot を `wal.knowledge_provenance_for_material_report()` に渡す。
- [layer3_report.py:750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:750) の admission hash 再確認後に provenance projection を確定する。knowledge-aware legacy v1 は receipt/WAL 自体は読めても、投入集合を証明できないため新しい材料レポート生成は fail-closed とする。
- [layer3_report.py:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:788) の report dict に `"knowledge_provenance": knowledge_projection` を追加する。
- 既存 `_artifact_refs()` は campaign 内の受領証も hash するため再利用する。`admission_decision` の lock/WAL digest、WAL `source_refs`、artifact ref の receipt digest が proof chain を構成する。
- 読出し時に git object や Web を再取得しない。D1493 の既知限界は残る。

## layer3_schema.json の変更

- [layer3_schema.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:5) の top-level `additionalProperties:false` は維持する。
- [layer3_schema.json:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:22) の top-level `required` には `knowledge_provenance` を追加しない。既存 v3 artifact の可読性を守るためです。
- [layer3_schema.json:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:27) の後に `knowledge_provenance` の `oneOf: [null, object]` を追加する。
- object 側は `additionalProperties:false` とし、`knowledge_level`、`knowledge_manifest_sha256`、`declared_sources`、`injected_sources` の4欄すべてを nested `required` に入れる。
- [layer3_schema.json:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:252) の `definitions` に `knowledge_source` を追加し、repo/Web を `oneOf` で exact 定義する。各 source と identity の双方を `additionalProperties:false` にする。
- 両 source array は `type:array`、`minItems:1`、`uniqueItems:true` とする。順序の canonicality は JSON Schema ではなく producer/WAL validator が検査する。

## SCHEMA_VERSION の評価

**据え置き案 — 推奨**

- v3 に optional property を足し、新 producer は必ず `null` または object を出す。
- 既存 v3 report の欠落を引き続き受理できる。
- [test_layer3_report.py:1367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1367) などの既存 v3 期待値を変更しない。
- repo 内 consumer は必要欄だけを参照しており、exact v3 literal の実 consumer は見つからなかった。テスト fixture の v3 constants も変更不要。
- 欠点は、旧 schema file を持つ repo 外 consumer が同じ v3 literal の新欄を `additionalProperties:false` で拒否することです。

**v4 版上げ案**

- `SCHEMA_VERSION=v4`、`PREVIOUS_SCHEMA_VERSION=v3`、`LEGACY_SCHEMA_VERSION=v2` とする。
- v4 top-level `required` に `knowledge_provenance` を加え、v3 reader は property と required を除去して派生、v2 reader はさらに `admission_decision` を除去する。
- wire contract と版の対応は最も明確です。
- 一方、現在の非 knowledge report も v4 + `null` にすると既存の v3 期待値変更が不可避です。今回の「既存テストの期待値を変更しない」条件とは両立しません。

したがって今回は据え置きを推奨します。将来 repo 外 consumer の version negotiation が必要になった時点で v4 に上げるのが妥当です。

## 既存 v1 受領証の扱い

`knowledge-manifest-receipt/v1` の schema や bytes は変更しません。

- v1 producer API はそのまま残す。
- WAL は injected digest のない legacy lock に対してのみ v1 receipt と旧3-key provenance を受理する。
- v2 lock に v1 receipt または旧 WAL shape を与えた場合は downgrade として拒否する。
- 既発行 v1 receipt と既存 WAL は replay/read 可能なままです。
- ただし v1 には実投入集合がないため、それを宣言集合から推定して新材料レポートへ載せません。v1 knowledge campaign から新しい proof-complete report を作ろうとした場合は停止します。
- 新 CLI は injected digest を campaign identity に加えるため、既存 v1 campaign と別 campaign ID になります。既存 create-only receipt を上書きしません。

## campaign_lock.py の扱い

[campaign_lock.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/campaign_lock.py:19) の identity exact keys は `search_config` を1 object として束縛し、[campaign_lock.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/campaign_lock.py:199) はその型だけを確認しています。

したがって `search_config.knowledge_injected_sources_sha256` は既存 canonical identity preimage に自然に入り、`campaign_lock.py` 自体の編集は不要です。

## Web digest に関する P4

P4 には賛成です。ただし「schema 上の記録要件が既に満たされている」という限定付きです。

- [knowledge_manifest.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:198) は全 kind に exact `{"kind","identity","sha256"}` を要求しています。
- Web branch は [knowledge_manifest.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:202) を通った後、[knowledge_manifest.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:208) で同じ `_require_sha256()` が必ず発火します。
- URL と取得時点は [knowledge_manifest.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:160) で exact 検査されています。

一方、[knowledge_manifest.py:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:309) は Web の live 解決を明示的に拒否しています。したがって取得・snapshot 作成・digest 照合まで満たしたとは書かず、その配線も追加しません。

## テスト計画

既存 assertion は変更せず、以下を追加します。各テストの赤理由は1つに限定します。

| file:line 付近 | 新規テスト | 単一の赤理由 |
|---|---|---|
| [test_knowledge_manifest.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_knowledge_manifest.py:163) | `test_injected_sources_are_extracted_from_emitted_payload_not_manifest` | extractor が payload でなく宣言集合を参照した |
| [test_knowledge_manifest.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_knowledge_manifest.py:244) | `test_v2_receipt_has_exact_injected_sources_field` | v2 receipt の exact key/値が不正 |
| 同上 | `test_v2_receipt_rejects_injected_content_digest_mismatch` | 実投入本文と source SHA が不一致 |
| 同上 | `test_v2_receipt_create_only_rejects_changed_injected_set` | 同じ path の投入集合を上書きできた |
| [test_p3_s4_loop.py:1833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_p3_s4_loop.py:1833) | `test_v2_knowledge_writer_records_declared_and_injected_independently` | WAL が2集合を独立保存しなかった |
| 同上 | `test_v2_knowledge_writer_rejects_missing_injected_sources` | v2 exact key 欠落を受理した |
| 同上 | `test_v2_knowledge_writer_rejects_injected_digest_tamper` | 投入集合 digest と lock の不一致を受理した |
| 同上 | `test_v2_lock_rejects_legacy_wal_shape_as_downgrade` | v2 identity が旧3-key WAL を受理した |
| 同上 | `test_legacy_v1_receipt_and_wal_shape_remain_readable` | 既発行 v1 compatibility が壊れた |
| [test_p3_s4_loop.py:5473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_p3_s4_loop.py:5473) | `test_emit_context_binds_actual_injected_digest_into_campaign_identity` | emit payload の source digest が identity に入らなかった |
| [test_p3_s4_loop.py:5549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_p3_s4_loop.py:5549) | `test_run_iteration_requires_prior_v2_receipt` | emit 証拠なしで run 経路が進んだ |
| [test_layer3_report.py:1408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1408) | `test_nonknowledge_report_emits_null_knowledge_provenance` | 新 producer が非 knowledge campaign で欄を省略した |
| [test_layer3_report.py:1524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1524) | `test_report_projects_distinct_declared_and_injected_source_sets` | report が2集合を同一視した |
| 同上 | `test_report_rejects_injected_sources_not_bound_to_campaign_identity` | WAL 投入集合 digest と lock の不一致を受理した |
| 同上 | `test_report_rejects_multiple_build_start_injected_sets` | campaign 内で投入集合が一意でなかった |
| [test_layer3_report.py:1601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1601) | `test_saved_v3_without_knowledge_provenance_remains_readable` | 既存 v3 の欄欠落互換性が壊れた |
| 同上 | `test_v2_schema_rejects_forward_knowledge_provenance_field` | legacy v2 acceptance set を誤って広げた |
| [test_layer3_report.py:1655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_layer3_report.py:1655) | `test_schema_rejects_unknown_nested_knowledge_key` | nested `additionalProperties:false` が効かなかった |
| 同上 | `test_schema_rejects_missing_injected_sources_in_object` | nested required が効かなかった |

変異 matrix は「宣言 source SHA」「投入 source SHA」「v2 `injected_sources` 欠落」「未知 key」「v1 shape への downgrade」を別々のテストにし、一つのテストが複数の拒否理由へ依存しないようにします。

## P1〜P5 の評価

- **P1 — 採用。** `knowledge_provenance` 1欄、4つの nested fields、本文なし source descriptor は適切です。補強として投入集合 digest を report ではなく campaign `search_config` に加えます。
- **P2 — 修正して採用。** top-level property と `object|null` は採用しますが、v3 据え置き・top-level optional とします。nested 4欄は required、新 producer は top-level を必ず出します。v4 + top-level required は契約として明快ですが、既存期待値を変更しない条件に反します。
- **P3 — 採用。ただし取得点を修正。** `planner_projection(resolved)` から直接記録せず、`planner_context_payload()` が返した実 payload から抽出・再照合します。宣言集合との一致を仮定しません。
- **P4 — 採用。** Web も `sha256` 必須であり、記録 schema の digest 要件は既に満たします。ただし live fetch/照合は未配線のままで、満たしたとは主張しません。
- **P5 — 採用。** WAL exact keys を v2 lock のときだけ `injected_sources` 分広げます。legacy lock では旧 exact keys を維持し、v2 identity から旧 shape への downgrade は拒否します。

## A/B 分割

親の列挙どおりの集合は形式上は素集合です。しかし単位 A は機能的に不完全です。

修正後の分割は次です。

- 単位 A：
  - `orchestrator/campaign/knowledge_manifest.py`
  - `orchestrator/campaign/wal.py`
  - `orchestrator/campaign/p3_s4_loop.py`
  - `orchestrator/tests/test_knowledge_manifest.py`
  - `orchestrator/tests/test_p3_s4_loop.py`

- 単位 B：
  - `orchestrator/campaign/layer3_report.py`
  - `orchestrator/campaign/layer3_schema.json`
  - `orchestrator/tests/test_layer3_report.py`

この修正版でも編集 path は素集合です。両方で編集が必要な file はありません。B は A が新設する `wal.knowledge_provenance_for_material_report()` の出力契約に依存するため、実装順は A → B です。

`campaign_lock.py` は両単位とも編集不要です。

## 総括

- 推奨は v3 据え置き、top-level property は optional、nested object は exact-required、新 producer は常に object/null を出す案です。
- 実投入集合は `planner_context_payload()` の返値から確定し、宣言集合とは別 digest で campaign identity・v2 receipt・WAL・材料レポートへ結びます。
- 既存 v1 receipt/WAL は完全に読み続けますが、投入集合を推定して新しい proof-complete report を作ることはしません。
- A/B は `p3_s4_loop.py` を A に補えば素集合を維持できます。
- 未解決の設計択一は schema version だけです。repo 外の旧 v3 validator まで強く保護するなら v4 が正しい一方、既存テスト期待値を変更しない今回の条件では v3 据え置きを推奨します。
- pytest は実走しておらず、上記は指定ファイルと参照 consumer の静的読解に基づくプランです。