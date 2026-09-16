## 変更 hunk

行番号は変更前のもの。`L` = `orchestrator/campaign/layer3_report.py`、`T` = `orchestrator/tests/test_layer3_report.py`。

| # | file:line | before → after |
|---|---|---|
| 1 | L:112–120 | `_read_campaign_lock(path)` → `_read_campaign_lock(path, *, purpose: CampaignReadPurpose)`。返却型を `DecodedCampaignLock \| DecodedHistoricalCampaignLock` にする。読取り前に exact enum を検査し、HISTORICAL_RAW のみ歴史 decoder、それ以外の有効値は通常 decoder。既存の例外変換を維持。 |
| 2 | L:191–195 | `_resolve_generated_from_head` の `decoded_lock` 注釈を同じ union にする。処理は変更しない。 |
| 3 | L:375–378 | `_contract_calibration_pin` の `decoded_lock` 注釈を同じ union にする。処理は変更しない。 |
| 4 | L:755 | `_read_campaign_lock(...)` → `purpose=CampaignReadPurpose.HISTORICAL_RAW` を付ける。 |
| 5 | L:815 | `campaign_lock=decoded_lock` → `campaign_lock=decoded_lock.identity`。 |
| 6 | L:937 | `_read_campaign_lock(...)` → `purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE` を付け、従来どおり `.identity` を取り出す。 |
| 7 | T:568 の前 | 合成歴史 campaign の fixture helper を追加。既存 `_campaign` と admission view の seam を使う。 |
| 8 | T:1854 の前 | 後述の新規テスト 7 関数をまとめて追加。 |
| 9 | T:2258–2260 | 既存の直接呼出しに `purpose=CERTIFIED_ACCEPTANCE` を追記。返却型と WAL への受渡しを従来どおり維持。 |
| 10 | T:2279 | 同じく `purpose=CERTIFIED_ACCEPTANCE` を追記。 |

hunk #1 の中心部分は次とする。

```python
if type(purpose) is not CampaignReadPurpose:
    raise TypeError(
        "purpose は exact CampaignReadPurpose.CERTIFIED_ACCEPTANCE "
        "または HISTORICAL_RAW が必要"
    )
try:
    text = path.read_text(encoding="utf-8")
    if purpose is CampaignReadPurpose.HISTORICAL_RAW:
        return campaign_lock.decode_historical_campaign_lock(text)
    return campaign_lock.decode_campaign_lock(text)
```

brief の scope #1〜#6 はすべて必要で、実装範囲に過剰はない。補足が必要なのは scope #6 に含まれる**既存直接呼出し 2 箇所の追随修正**。既に module import と enum import があるため、実装側の import 追加や共通型 alias は不要。`wal.py`、decoder、admission、公開 builder の signature は変更しない。

## P1〜P4 の評価

**P1：採用。** `CampaignReadPurpose` は exact 2 値の `str, Enum`（`artifact_admission.py:180–184`）。同 module の purpose dispatch（1016–1025）と型検査（1138–1143）に合わせ、検査を読取り・decode より前に置く。文字列との等価比較では exact 型を保証できないため、`type(...) is ...` と分岐の `is` を使う。私有 helper は import しない。

**P2：採用。ただし「WAL 全処理の等価性まで確認済み」という断定は親の最終確認に残す。** 最小変更は L:815 の `.identity` 追加。

- 旧入力 `DecodedCampaignLock` は `wal.py:1748–1749` でそのまま返り、1765–1768 で `.identity` になる。
- 新入力の identity dict は `wal.py:1752–1753` で decoded なしとなり、1769 でその dict 自体が返る。
- L:789–791 が受理する identity の exact key 集合に `schema_version` はない。したがってこの経路で dict が v2 envelope と再解釈されることはない。
- 現行 63 は `campaign_lock.py:705–707` で通常 decoder を経由し、663–677 の変換で identity を保持する。v1 も688–689で同じ変換を通る。両者とも上記正規化の結果は同じ identity。
- 歴史 decoded object を直接渡すと `wal.py:1754–1755` で拒否される。`.identity` なら既存の identity 入力契約を使える。

指定範囲から確認できる material-report 入口は `wal.py:1135–1138` の binding 取得と検証呼出しであり、検証側も1102で binding を取得する。ただし、その `_knowledge_lock_binding` 本文と1140行以降は今回の読取り射程に含まれない。**正規化結果の等価性は上記行番号で示せるが、関数全体で authority を別途参照しないことまで、この射影だけで証明したとは報告しない。** 親は段4でこの点を確認し、後述の knowledge 正例・拒否テストと変更前後比較で I5 を検証する。WAL 側への歴史型追加は不要で、closure を変更するため採らない。

**P3：採用。** L:733–736 と755の purpose を一致させる。certified は937の通常 decoder、966–969の certified admission、975以降の decision／epoch 検査を維持する。`build_report` に purpose 引数を増やす必要はない。

**P4：採用。ただし到達確認と完全生成を区別する。** L:835–838 は `records/threads` の整数性を要求する。親の実測では exact-62／24 は755で停止し、63対照は838まで到達している。修正後の実 corpus 受入条件は「exact-62 の3本が63対照と同じ838のエラーに到達し、lock/WAL bytes が不変」。完全生成の証拠は合成 fixture で取る。実 corpus の完全生成済みとは報告しない。

## 歴史型の消費地点

| 消費地点 | 使用内容 | 歴史型との適合 |
|---|---|---|
| L:756、784–791 | `.identity`、object／キー／lineage 検査 | `campaign_lock.py:298` は `dict[str, Any]`。そのまま動く。 |
| L:835–838、856、864、870–871 | identity 内の `search_config`、`ccbench_commit` | 通常型と同じ identity。records/threads 等の既存条件は残る。 |
| L:803–815 | WAL provenance 検証への入力 | decoded object のままでは不適合。`.identity` にする。 |
| L:852–854 → 375–402 | `.authority.environment_contract_sha256` | 歴史 authority の270に同名 `str`。authority は299で optional。既存の `None` 分岐も動く。 |
| L:865–867 → 191–205 | `.authority.contract_loader_commit` | 歴史 authority の273に同名 `str`。外部 campaign の HEAD fallback を維持できる。 |

`DecodedHistoricalCampaignLock` の `schema_version`、`identity_preimage`、`original_text`、`is_v1/is_v2` はこの builder では直接消費しない。歴史 authority 固有の `recorded_contract_loader_relative_paths` も直接使わない。

L:794–800 の bytes 照合、884–893 の admission／epoch／conformance 投影は admitted view と実ファイルを使うため、decoded 型の変更対象ではない。`_epoch_projection` の注釈変更も本件には含めない。

## テスト設計

追加先は T:1854 前。reader と decoder は一切 monkeypatch しない。

**fixture の作り方**

最短の構成は、`test_artifact_admission.py:760–780` の `_committed_closure_repo` を作り、`contract_loader_binding._REPO_ROOT` をそこへ向け、T:210–295 の `_campaign` を使う方法。これにより、既存の records/threads、calibration、`trial="trial"` をそのまま使える。

exact-62 は `test_artifact_admission.py:3194–3203` の `_rewrite_as_t733_exact62_lock(campaign)` を再利用する。既存の63 path mapから、テスト側の独立した期待 tuple を使って62 pathを選び、canonical JSONで保存する。exact-24 も同 module の812行の既存 rewrite helperを使える。

`_new_schema_campaign`（同841–932）も使用可能で、records/threads は887–889に存在する。ただし trial は894で `"test"` のため、T:568 の receipt seam と合わせる追加調整が要る。本件では `_campaign` を選ぶ。

rewrite 後に T:555 の `_historical_admitted_campaign` で実 admission を通した歴史 view を取得する。その view を返す `historical_only(_path, *, purpose)` をT:1946–1952の形で設置する。**view は rewrite 後の bytes で取得する**ため、L:794–800 の digest 照合を迂回しない。

| 新規 test 関数 | ケースと検証 |
|---|---|
| `test_historical_exact_grammar_build_report` | exact-62／24で parameterize。実 `build_report` が report を返す。workload は records=100000、threads=4、非認証、receipt=None、conformance=`"unknown"`、歴史 epoch の固定期待値を検証。呼出し前後の lock/WAL bytes も比較。 |
| `test_accepted_report_rejects_historical_exact_grammar_at_lock` | 上と同じ fixture 構成を62／24で使用。T:568の receipt と2649–2653の検証済み receipt seam を使い、`generated_from_head="fixed"` を明示。例外全文を `^campaign\.lock schema が不正$` に限定し、cause が `CampaignLockCodecError` であることも確認。 |
| `test_read_campaign_lock_requires_purpose` | 正常な63 lockへ purposeなしで呼び、`TypeError`。 |
| `test_read_campaign_lock_rejects_non_exact_purpose` | 両目的の文字列、同じ値を持つ別の `str, Enum` を渡して `TypeError`。正常な63 lockと存在しないpathの両方で試し、型検査がI/Oより前にあることも確認。 |
| `test_read_campaign_lock_current_and_v1_by_purpose` | 63／v1 × 両purpose。成功だけでなく、歴史側は exact `DecodedHistoricalCampaignLock`、certified側は exact `DecodedCampaignLock` を検証。identity は入力用の固定辞書に一致することを確認。 |
| `test_historical_exact_grammar_uses_authority_head_fallback` | 62／24の外部 campaign。T:4641–4689の既存手順に合わせ、fixture の記録 commit を40桁の固定値にし、digestを更新した歴史viewをseamへ渡す。`generated_from_head` 省略時に固定値を返すことを確認。 |
| `test_material_knowledge_identity_argument_preserves_current_and_v1` | T:364の `_knowledge_campaign` を使い、63／v1について通常 decoded object とその identity を実WAL helperへ渡す。非Noneの結果とreceipt digestが一致することを確認し、既存の固定期待projectionも維持する。decoder／WAL helperの差替えはしない。 |

epoch の期待値はテスト内の固定文字列とする。

- exact-62：`E1:78920efc47f4eb280b956a8fb92abed16b888495db544b62b1a15bf1f61004e9`（既存固定値：`test_artifact_admission.py:591`）。
- exact-24：`E1:e1e397737e509b550482d3e815bcb69b87c0b5c42f6ac7feb6fccb657856cfc7`。今回、テスト側の独立literal tupleとfixture bytesから静的に算出した値。追加テストではこの文字列を直接置き、実装や `_expected_pre_t733_fixture_epoch()` から再計算しない。
- state=`"E1"`、reason=`"recorded-closure"`、assessment basis=`"recorded-at-original-verifier-epoch"` を固定期待値にする。

親は63／v1の同一fixtureに対して変更前後のreportも比較する。同一入力・同一HEAD指定で比較し、除外するfieldは I5 が許す `meta.generator.sha256` だけとする。

## 変異事前登録の候補

対象はすべて L。挿入行は変更前アンカーで示す。以下9件から段4で確定する。

| # | 対象 file:line | 変異 | 殺すはずの test |
|---|---|---|---|
| M1 | L:112–120 | purpose分岐を除去し、常に通常decoder | `test_historical_exact_grammar_build_report` |
| M2 | L:112–120 | purpose条件を反転 | `test_historical_exact_grammar_build_report`、`test_read_campaign_lock_current_and_v1_by_purpose` |
| M3 | L:112–120 | 常に歴史decoder | `test_accepted_report_rejects_historical_exact_grammar_at_lock`、返却型を検査するcurrent/v1 test |
| M4 | L:937 | purposeをHISTORICAL_RAWへ変更 | `test_accepted_report_rejects_historical_exact_grammar_at_lock` |
| M5 | L:755 | purposeをCERTIFIED_ACCEPTANCEへ変更 | `test_historical_exact_grammar_build_report` |
| M6 | L:112直後 | exact型検査を除去 | `test_read_campaign_lock_rejects_non_exact_purpose` |
| M7 | L:815 | `.identity` を除去してdecoded objectへ戻す | `test_historical_exact_grammar_build_report` |
| M8 | L:112 | purposeにHISTORICAL_RAWの既定値を付ける | `test_read_campaign_lock_requires_purpose` |
| M9 | L:112–120 | exact型検査を `read_text` の後へ移動 | `test_read_campaign_lock_rejects_non_exact_purpose` の存在しないpathケース |

brief の「反転（常に歴史decoder）」は異なる変異なので、M2とM3に分ける。

M4では、937を通過した後に historical statusやcertified admissionで拒否されても、期待する**正確なschemaエラー**と異なるため殺せる。単なる `raises(Layer3ReportError)` にはしない。

候補から外すものは、旧grammarだけを入力にした L:966 のcertified admission削除や980のE1 gate削除。正常実装では937で停止するため、これらの変異箇所へ到達しない。新規負例がそのまま緑でも防壁の有効性を測れない。また、scope外のdecoder内部grammar変更も今回の変異対象にしない。

## 既存テストへの波及

`rg` による `orchestrator/tests` 内の検索で、layer3の `_read_campaign_lock` 直接呼出しは次の2件。両方ともpurpose必須化だけで赤になる。

| file:line | 関数 | 対応 |
|---|---|---|
| T:2258 | `test_artifact_refs_accept_validated_knowledge_receipt_digest`（2251） | CERTIFIED_ACCEPTANCEを追記。通常decoded型をWALへ渡す既存検証を維持。 |
| T:2279 | `test_artifact_refs_reject_receipt_changed_after_provenance_read`（2274） | 同上。2282・2295のWAL入力は変更不要。 |

builder自体を差し替える既存箇所は次の2件で、公開signatureは変えないため追随修正不要。

- T:2655：`test_accepted_report_rejects_historical_before_certifying_fields_are_set`。`build_report` を `lambda *_args, **_kwargs` に差替え。
- T:4553：`test_render_accepted_existing_output_fails_before_builder`。`build_accepted_report` を可変引数の `fail_builder` に差替え。

admission／receiptのseamを使って実builderを呼ぶ箇所も、signature変更による赤は見込まない。検索とAST確認による一覧は次のとおり。

- historical admission差替え：T:1861、1950、2020、2545、2641、2872、4673。いずれも既存のpurpose付きadmission呼出しを受ける。
- receipt検証差替え：T:2569、2649、2678、2713、2736、2786、2822、2861、4573。readerの新keywordはこれらのstubへ伝播しない。
- T:2977は `autonomous_trial_completeness.require_admitted_campaign` の差替えであり、本readerのsignature変更対象ではない。

ただし型変更の影響確認として、既存knowledgeのreceipt置換拒否（T:2232）、authority投影（1991）、外部HEAD fallback（4641）、certified成功・拒否群（2673以降）は親の焦点走に含める。静的確認のみで、実走済みとはしていない。

## 受理集合 before / after

`build_report` が受理する lock は、変更前のv1／現行exact-63から、変更後は既存のHISTORICAL_RAW admissionと後段検査を満たすv1／exact-63／exact-62／exact-24へ広がり、旧grammarでもrecords/threads等が不適合ならreport生成は拒否される。

`build_accepted_report` が受理する lock は変更前後で不変であり、exact-62／exact-24は937の通常decoderで拒否され、v1／現行exact-63も従来のreceipt・certified admission・E1等の全条件に従う。

## 総括

変更file数：2（実装1、テスト1）。
変更hunk数：10（論理単位）。
追加test数：7関数、既存2関数の呼出しを追随修正。
変異候補数：9。実装・pytest実走は未実施。
段4争点：P2のWAL全経路の等価性確認、固定epoch fixtureの採用、実corpusの完了線を838到達に限定すること。