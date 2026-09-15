## 調査結果

**Q1: schema v2 は現行 builder を無改修で通る構造です。ただし、Q3 が要求する非保証の Markdown 出力はありません。** このため、現在の制約すべてを満たす「緑になる正例」は、そのままでは作れません。

以下の参照は指定 worktree 内です。略号を使います。

- `R` = `orchestrator/campaign/p3_b4_material_report.py`
- `I` = `orchestrator/campaign/p3_b4_floor_artifact_issuer.py`
- `T` = `orchestrator/tests/test_p3_b4_material_report.py`
- `IT` = `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`
- `S` = `orchestrator/tests/test_real_repo_serialization.py`
- `D` = `orchestrator/tests/test_floor_pair_driver.py`

### 親の5事実の確認

1. **手書き authority は確認できました。** `T:98` の dict に `floor_exact: [0, 1]`（101行）、source summary の `"artifact_sha256": "1" * 64`（116行）、`"spec_sha256": "2" * 64`（122行）があります。131行で直接書きます。ただし、**authority ファイル自身の hash は132行で実 bytes から計算**しています。「過去に一度も実走していない」という履歴までは、この静的調査からは断定しません。
2. `_aggregate_public_sources` は `IT:1187`、跨 test module import は `IT:19` にあります。
3. `S:362` の frozenset を AST で照合しました。**31テスト関数対31項目、欠落・余剰とも0**。厳密にはパラメータ展開前の canonical node の網羅です。
4. duration 台帳には node 別の秒数があります。`test_m9_*` の4パラメータは1931–1934行ですべて `11.0`。台帳の実項目数と `nodeid_count` はともに23109でした。
5. `R:54` の `GENERATOR_IDENTITY` は path 文字列です。issuer 側も `I:55` で同様です。

### Q1: v2 が通る経路

| 箇所 | 静的に確認できた動作 |
|---|---|
| `I:1324` | v2 を `_load_aggregate_authority` に分岐。v1 の schema 検査（1340行）へ進まない |
| `I:1270` | 全 source から再構成し、1271行で canonical bytes を比較 |
| `I:1274` | 最大床値・v2 schema・実ファイル hash・非保証を `B4AuthoritativeFloor` に格納 |
| `R:267` | 実 evaluator に `authoritative_floor.floor` を渡す |
| `_authoritative_floor_source`, `R:955` | 958行で schema をそのまま転記。v1 限定検査なし |
| `_apply_authoritative_floor_projection`, `R:973` | exact ratio を転記。990–993行で非保証をJSONの2箇所へ追加 |
| `_assert_authoritative_floor_projection`, `R:1046` | authority 由来の source・ratio と比較。v2 拒否なし |
| `_render_markdown_with_authoritative_floor`, `R:1214` | ratio・artifact path・hash を描画。schema 限定なし |
| 公開 builder, `R:1230` | 実ロードから投影・検査・JSON/Markdown生成まで接続 |

**食い違い:** `_render_markdown`（`R:1097`）にも、その wrapper（1195行）にも、`non_guarantees` の描画がありません。1214–1219行の置換内容は床値・パス・hashだけです。builder の拒否ではなく、要求された出力の欠落です。

## プラン (file:line 粒度)

**採用案は跨 file helper 再利用＋実 Git の一時 fixtureです。production は変更しません。Markdown要件の衝突は受入前に解消が必要です。**

### 1. 許可外の Git monkeypatch を避ける

`IT:1189` → `_synthetic_source`（53行）→ `D._install_git`（73行）→ `D:370` と辿ると、**`subprocess.run` が差し替わります**。既存 helper の無変更再利用はQ6違反です。

- `IT:53` に Git seam を設置するかの keyword 引数を追加し、73行の設置だけを条件化する。既存呼出しの既定動作は維持。
- `IT:1187` からその引数を渡せるようにする。新正例だけ Git seam を無効にする。
- 新正例の一時 authority root に実 Git repository を用意する。`D:405` の `_real_git` と417–437行の既存手順を参照し、入力 commit、各 spec の `provenance.source_commit` 設定、spec freeze commit を作る。
- spec変更後の hashを pins と summary に反映し、summary の `loaded_head` も実 HEAD にする。**pins は明示した3 specから確定し、受理された summaries から逆算しない。**

これは将来のテストが一時 fixture 内で行う操作です。本セッションでは実行しません。

実 Git が必要な根拠は `floor_pair_driver.py:1212` の HEAD 解決、1237行の tracked blob 比較、1285–1290行の真の祖先検査です。

### 2. 正例を1本追加する

`T:958` の直前、既存m9の後に、非パラメータ化した次のテストを置きます。

`test_aggregate_authoritative_floor_reaches_public_material_report`

- import は `T:30` 付近に module alias として追加。テスト関数自体を import しない。
- `immutable_publication`、`tmp_path`、`monkeypatch` を受け取る。
- `_aggregate_public_sources` で3入力を構成する。
- **実 `floor_issuer.issue_aggregate_authoritative_floor`** を呼ぶ。
- 実 artifact bytes を読む。
- 一時 root の `docs/...` に、発行された artifact path と実 hash の preregistration pin を書く。書式は `IT:188` を再利用できる。実 repository の preregistration は編集しない。
- **実 `resolve_preregistered_authoritative_floor`** を呼び、解決結果を確認する。
- `R._REPOSITORY_ROOT` だけを一時 rootへ向け、**実 `R.build_material_report_document(immutable_publication.publication.publication_root)`** を直接呼ぶ。

`T:248` の `_inputs`、257行の `_document` は使いません。authorityに依存しないキーの cache を避け、毎回実 builder を通します。`_fresh_publication_from_shared_evidence`（226行）も不要です。これは `secrets.token_bytes` の追加差替えを含みます。

### 3. Q3: assert の具体形

期待値は発行結果だけから導出せず、入力 summaries/specs と実ファイルから独立に組み立てます。

- 3入力の `Fraction(candidate_floor)` が相異なる。
- 入力順で **第0値 < 第2値 < 第1値**。最大が先頭・末尾でないことも固定する。
- artifact の schema が literal `"p3-b4-authoritative-floor/v2"`。
- `aggregation.operation == "exact-fraction-max/v1"`。
- `aggregation.expected_specs` が呼出し側の3 pinsと一致。
- `aggregation.sources` が3件あり、各 path・実 summary hash・spec pin・床値・`proof_limitations` が各入力と一致。
- artifact、resolver結果、reportの床値がすべて**3入力の最大の exact ratio**と一致。
- `report["floor"]` 全体を期待 dict と比較する。特に  
  `report["floor"]["source"]["artifact_sha256"] == hashlib.sha256(artifact_path.read_bytes()).hexdigest()`。
- JSONの `certification_scope.not_guaranteed` と `provenance.report_non_guarantees` に、全 source の `proof_limitations["items"]` と `AGGREGATE_NON_GUARANTEES` が順序・重複を保って追加される。`I:1202` の構成順を独立に期待値へ記述する。
- 最大でない source 0・2 固有の limitation も確認し、最大sourceだけ転記する実装を検出する。
- `analysis.status == "evaluated"`、`analysis.floor_argument == 最大ratio`、201 blocks・402 arm rows、実 raw analysis の UTF-8/hash結合を確認する。
- Markdown の床値・パス・実 hash を確認する。**非保証各項目の Markdown assertion も要求から削らない。ただし現行ではここが赤になる。**

任意の偽実装すべてをこの1本で検出する保証はありません。特に calibration の真正性、実性能測定、publish の耐久性は検証対象外です。実 issuer・resolver・builderを置換しないことと、入力からbytesまでの具体的結合を証拠にします。

### 4. Q2: 配置案の比較

| 案 | 利点 | 欠点・判断 |
|---|---|---|
| 跨 file import | 既存の3入力・最大が中央の構成・source固有非保証を再利用できる | private helperへの依存。Git seam分離が必要。**採用** |
| 共有 support module | 合成処理とseamの責任を整理できる | 移動・import変更が増える。今回の1本には不要 |
| 材料テスト内で再構成 | 許可seamを局所管理できる | 約120行の構成を重複し、両テスト間で入力が乖離しやすい |

両層の実体を通る強さを決めるのは配置ではなく、**実公開APIの呼出し、実bytesの再解決、独立した期待値**です。採用案ではさらに実 Git binding を維持します。

### 5. 台帳登録と既存期待値の維持

- `S:362` に新 canonical node を1件追加。
- `acceptance_duration_ledger.json:1935` 付近に完全 node IDを追加。
- 同ファイル `23113` 行の `nodeid_count` を項目数に合わせて1増加。
- `T:56`・59行の absent golden、77行の手書きhelper、842行以降のm9の4状態・期待値は変更しない。

**Q4:** production無変更、共有publication無変更、cache不使用、patchのfunction scope復元により、既存期待値を動かす必要はありません。path型の `GENERATOR_IDENTITY` も変わりません。

## 想定される赤と根拠

| 赤／契約 | 根拠と対応 |
|---|---|
| Markdown非保証 assertion | `R:1214` の出力に非保証がない。現在の制約では解消不能 |
| helperをそのまま再利用 | `IT:73` → `D:370` が許可外の `subprocess.run` patch |
| Git patchだけ外す | `floor_pair_driver.py:1212` 以降の実Git検査で失敗。一時実Git fixtureで対応 |
| 新nodeのgolden登録漏れ | `S:1585` の collection test →1615行→`_assert_long_lived_fixture_group_contract` →1338行の集合一致で赤 |
| xdist group変更・重複 | `T:41` のmodule markを継承する。`S:1589`→1263行のgroup契約を維持 |
| fixture consumer集約の不整合 | `S:998` が実fixture closureから集約を生成し、1295行以降で照合。新consumerは自動追加されるため手動宣言追加不要 |
| 別fixtureアクセスgolden | `S:426` の対象はrepository scan・S8C fixtures。`immutable_publication` は含まれず、新規登録不要 |
| duration count更新漏れ | `conftest.py:1538` が件数不一致で台帳を無効化する |
| duration coverage契約 | `test_acceptance_schedule_order.py:660`、712行が実collectionの90%以上を要求。新node登録で対応。1件の追加だけで必ず赤になる契約ではない |

参照検索で見つかった `p3_b4_producer_auth_experiment.py:439` は既存normal-path nodeの個別指定です。全材料テストの網羅契約ではなく、更新不要です。調べた参照関係では、**上記2台帳とcount以外の手動登録先は見つかりませんでした**。collection実走による確認はしていません。

## 未解決の論点

1. **Markdown要件とproduction変更条件が衝突しています。**  
   Q1は「受理される」ため、許可条件は発火しません。一方、非保証のMarkdown assertionは失敗します。assert削除・xfail化・renderer差替え・無断production変更は提案しません。受入可能な実装へ進むには、この衝突の解消が必要です。

2. **Q6の許可集合の射程。**  
   新正例が追加する差替えは calibration loader と `R._REPOSITORY_ROOT` の2つで足りる設計です。`os.fsync` は速度対策であり、正しさに必須ではありません。  
   ただし、指定された既存 `immutable_publication` 自体は `T:190` で admission helper、clone helper、controller invokeをpatchしています。「既存fixture内部も含め、許可3箇所以外は一切不可」という意味なら、fixture再利用要求とも衝突します。この既存内部動作を黙って許可集合内とは扱いません。

3. **Q7: 所要時間は未測定です。**  
   warm fixtureで**10–20秒、計画値15秒**を見込みます。m9の11秒からpublication再発行を省けますが、実Gitによる3 spec検査が発行・明示resolver・builder内部resolverで繰り返されます。初回fixture構築込みの単独実行は**60–90秒程度**を見込みます。台帳のnormal-path 58秒も参考値です。既存aggregate正例のdurationエントリはありませんでした。これらを実測値として台帳へ記録せず、実装段の測定で確定します。

## 総括

**v2の受理・JSON投影は無改修で接続済みです。未接続なのは非保証のMarkdown表示です。** 加えて、親案のhelper無変更再利用は許可外Git monkeypatchを伴います。

正例は実Git fixtureと実 issuer・resolver・公開builderを通す1本にできますが、現行制約のまま全assertを緑にすることはできません。ファイル変更・commit・pytest実行は行っていません。