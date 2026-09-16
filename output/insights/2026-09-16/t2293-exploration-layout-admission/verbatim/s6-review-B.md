## fixture の成立性

以下、`U`＝`orchestrator/tests/test_reflux_result_evidence.py`、`I`＝`orchestrator/tests/test_reflux_campaign_issuer.py`、`E`＝`orchestrator/campaign/reflux_result_evidence.py` と表記します。

- **refuted：mkdir・import 不足。** `_producer_context` は directory を作りませんが、新設 fixture・root 外負例・正例はいずれも先に `root.mkdir()` を実施しています。`dataclass`、`SimpleNamespace`、探索 layout の import も揃っています。根拠：U:7、19、272、1133、1293、1326。
- **refuted：namespace・process pin の不成立。** 非空の明示 output_root を渡すため探索 pin を経由せず、`.ensure()` が namespace marker と campaign directory を作ります。根拠：U:318、1295、`layout.py:378`、580。
- **unverified：親 runner の実効 tmp 配置。** 新設 test は `tmp_path` に依存します。worktree container 配下なら `.ensure()` が失敗します。conftest に tmp 配置の上書きは見当たらず、実際の配置は親の焦点走で確認が必要です。根拠：`layout.py:461`、578、`conftest.py:1`、`plan-v2.md:17`。
- **refuted：snapshot 対象・digest 不一致。** 通常負例は evidence root 全体、root 外負例は evidence root と outside-output の両方を比較します。terminal prefix の SHA-256 は production と同じ無加工 bytes の規則です。根拠：U:435、1185、1203、1303、E:545、1484。

静的に確定できる通常実行時の fixture 不成立は見つかりませんでした。

## 負例の単一理由性

- **refuted：subclass・duck・impostor が属性不足等で恒真になる懸念。** subclass は同じ root と継承した wal_file、duck・impostor は実 layout と同じ root/wal_file を持ちます。fixture は同一 attempt の連続5 frame を書き、context・capability・contract・receipt も共通の有効な組合せです。WAL reader に layout の型 gate はありません。根拠：U:272、336、378、407、1132、1144、1151、1174、`wal.py:1683`。
- **refuted：impostor の比較契約不足。** metaclass の `__eq__` は対象型との比較で True を返し、`__hash__` も定義済みです。identity 不一致と tuple 所属の成立を assert しています。根拠：U:1165。
- **real／nit：単一理由性の適用範囲。** 発行入口だけを緩めても内側 gate が拒否するため、発行負例は外側 gate 単独の変異を kill できません。`str`・`Path`・`None` も gate 除去後には属性不足で落ち得ます。ただし、これらを受理拡大変異の観測点から除外した現 spec は妥当です。修正不要。根拠：U:1161、E:1219、1296、`plan-v2.md:62`。

## 変異 spec との整合

全6変異について、現物の `old` anchor は**各1回**でした。全 `expected_nodes` の関数名・parametrize id も AST と一致します。これは文字列・AST 検査であり、pytest collection の実走結果ではありません。

**real／must-fix：M3 の期待集合が2件不足しています。**

[共通 projection helper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2293-exploration-layout-admission/orchestrator/tests/test_reflux_result_evidence.py:1210) は、負例呼出しの前に `layout=real` の正例を実行します。M3 では探索 real layout がここで拒否されるため、登録済み2件に加えて次の2件も赤になります。

```text
orchestrator/tests/test_reflux_result_evidence.py::test_ordered_wal_projection_refuses_layout_subclasses[exploration]
orchestrator/tests/test_reflux_result_evidence.py::test_ordered_wal_projection_refuses_type_equality_impostor[exploration]
```

根拠：U:1210、1237、1285、[mutation-spec.v1.json:66](/home/SFC/tanab/.claude/jobs/955ee86e/tmp/wave/mutation-spec.v1.json:66)。

**成果物影響：変異レポートの失敗 node 集合が登録の2件から4件になり、追加2件の赤理由も負例の拒否挙動ではなく補助正例の過剰拒否になります。**

修正案：確定仕様の集合を維持するため、共通 helper 内の正例呼出しを除き、正例は既存の parameterized 発行・resolve test に集約してください。digest の独立計算は維持できます。期待集合を4件へ変更する場合は、`plan-v2.md:51` に従う理由記録が必要です。

実装から再導出した集合は以下です。統合 node は非 skip・baseline 成立を前提とします。

| 変異 | 静的に予測する失敗集合 | 判定 |
|---|---|---|
| M1 | projection subclass ×2 | refuted：不整合なし |
| M2 | projection subclass ×2＋duck ×2＋impostor ×2 | refuted：不整合なし |
| M5 | projection impostor ×2 | refuted：不整合なし |
| M3 | unit 探索正例＋統合探索正例＋上記2件 | **real：期待集合不足** |
| M4 | unit 探索正例＋統合探索正例＋発行 root 外負例 | refuted：不整合なし |
| M6 | 空 | refuted：静的に等価 |

根拠：U:1202、1225、1249、1281、1289、1321、E:447、1219、1289。M4 の root 外負例は受理拡大ではなく、型拒否への前移動による message 不一致です。

## 統合正例の到達性

- **refuted：対象経路の stub 化。** 新設 test は `_drive_required_campaign` → `_drive_campaign` → `loop.run_campaign` に探索指定と context を渡します。trace runner と attestation 観測入力を差し替えていますが、対象コードでは producer・layout 選択・verifier を stub していません。根拠：I:338、350、416、524、570、`loop.py:449`、828。
- **refuted：root 束縛・record path の不一致。** evidence root と output_root は同じ `issued_root`。探索 physical root はその配下です。expected path は origin・batch・query から導出され、physical campaign root に依存しません。探索配下の3種 content と WAL interval も照合しています。根拠：I:312、560、592、603、617、`loop.py:296`、E:964、1393。
- **real／nit：compiler 不在なら skip します。** gcc・g++・cmake のいずれかが無ければ実経路到達前に skip します。親は当該 node の非 skip 完走を確認し、skip を成功に数えないでください。根拠：I:102、550、`plan-v2.md:18`。
- **unverified：実際の統合完走。** 本レビューでは未実走です。author も build guard による停止を明記しています。根拠：`author-1.md:27`。

## 既存 test への波及

**refuted：helper の署名変更による既存 caller 破壊。** `_producer_layout` と `_drive_campaign` は keyword-only 引数追加で既定 official を維持し、`_issue_producer_record` は注釈だけの変更です。根拠：U:314、407、I:388。

U 内の既存 caller を列挙します。名前は共通接頭辞 `test_campaign_producer_` を省略しています。各行が両 helper を呼びます。

| caller | `_producer_layout` / `_issue_producer_record` の行 |
|---|---|
| issues_real_wal_projection_and_resolves_interval | 1327 / 1340 |
| preserves_nonzero_offset_for_second_attempt | 1395 / 1411 |
| refuses_absent_execution_receipt_before_writes | 1435 / 1445 |
| refuses_required_contract_v1_receipt_before_writes | 1460 / 1478 |
| refuses_contract_not_bound_by_capability_before_writes | 1494 / 1511 |
| refuses_required_contract_without_verified_calibration | 1529 / 1543 |
| refuses_unauthenticated_receipt_before_writes | 1564 / 1582 |
| refuses_interleaved_attempt_before_writes | 1597 / 1654 |
| refuses_nonexact_verify_result_before_writes | 1669 / 1679 |
| refuses_wrong_expected_record_path_before_writes | 1694 / 1711 |
| treats_create_only_collision_as_failure | 1726 / 1734、1743 |
| snapshot_survives_append_while_live_ref_breaks | 1763 / 1771 |

新設 helper caller は U:1135、1191、root 外負例は U:1309。`_drive_campaign` の直接 caller は `_drive_required_campaign`（I:536）と `test_originless_campaign_has_legacy_literal_artifact_and_wal_shape`（I:804）です。

**real／nit：既存正例の nodeid は変更されています。** 無 suffix の1件が `[official]`・`[exploration]` の2件になりました。仕様どおりで、既存 assert は維持されています。他の既存期待値・id の変更は差分にありません。修正不要。根拠：U:1321、`plan-v2.md:44`。

## author 報告との食い違い

- **refuted：nodeid・件数の食い違い。** 一覧の単体21 node＋統合1 node、新設20・変更後2という数え方は現物と一致します。根拠：`author-1.md:14`、41、U:1225、1321、I:546。
- **unverified：直接呼出し34ケース成功などの実走主張。** 射影には実行ログがなく、独立には確認できません。pytest 全走、統合完走、完全な変異走を成功したとは報告していません。根拠：`author-1.md:18`、25、27。
- **real／must-fix〔上記M3と同一所見〕：登録集合外の赤化が報告されていません。** 「登録された単体観測点で赤化」は否定されませんが、全観測集合の整合を示しません。helper 修正後、親の全走結果に基づき報告を更新してください。根拠：`author-1.md:20`、U:1210。

## 総括

**blocker なし、must-fix 1件：M3 は共通 helper の探索正例によって、期待集合外の2 node も赤になります。**

fixture・digest・型負例・統合経路・既存 caller に、それ以外の静的な修正必須事項は見つかりませんでした。tmp 配置、統合の非 skip 完走、全変異の実測は未確認です。ファイル変更・テスト実行は行っていません。