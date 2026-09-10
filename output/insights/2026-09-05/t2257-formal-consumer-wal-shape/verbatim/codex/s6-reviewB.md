## GO/NO-GO

GO  
静的点検では M1〜M11 はすべて殺され、fixture・golden・波及にも受理判定を変える漏れはない。

## must-fix

なし。

## nit

- 変異表の帰属は実際より狭い。M4 は N-10 でも、M5 は N-4 でも、M8 は N-3 でも殺される。変異は生存しないが、最終報告では実際の重複帰属へ直すとよい。
- P-1/P-2 の commitment は同一 binding 由来なので、それ単独では比較脱落を検出しない。これは更新済み既存負例、N-9、N-10で補われている。
- 新規13 nodeid の duration 登録は受入全走後で足りる。未登録中は選択漏れではなく unknown cost 扱いになる。

## 変異 M1〜M11 の帰属

| 変異 | 実際に赤になる最小テスト | 区分 | 静的追跡 |
|---|---|---|---|
| M1 | N-1 `test_fc05c_rejects_legacy_root_trigger_binding_shape` (`orchestrator/tests/test_reflux_formal_consumer.py:687`) | 新規だけ | legacy 値は ledger と同値で、fallback があれば FC05C を通過 |
| M2 | N-2 `test_fc05c_rejects_trigger_payload_under_non_trigger_stage` (`:698`) | 新規だけ | payload は完全に valid。resolver は stage 意味を検査しないため FC05B に先取されない |
| M3 | N-8 `test_fc05c_rejects_ledger_mask_only_mismatch` (`:746`) | 新規だけ | record/provenance/member は helper が同期し、wire と commitment は据え置き。ledger mask 代入だけで通過 |
| M4 | 更新済み既存 mismatch (`:611`)、N-9 (`:753`)、N-10 (`:760`) | 既存も | nonce 差、commitment-only 差、source-only 差はいずれも最終的に commitment 差だけを FC05C へ届ける |
| M5 | N-3 (`:705`) と N-4 (`:712`) | 新規だけ | 複数時に先頭を返すなら、両ケースとも最初の valid record で通過 |
| M6 | 既存 `test_exact_fixture_contract_reaches_only_p6_unavailable` (`:422`) と P-1〜P-3 (`:618`, `:639`, `:664`) | 既存も | mask 7 の LSB-first `"11100"` は MSB-first `"00111"` と非対称。mask 18 も非対称 |
| M7 | N-5 `test_fc05c_rejects_raw_trigger_binding_extra_key` (`:723`) | 新規だけ | known field の直接読みにすると余分な raw key が無視される |
| M8 | N-4 (`:712`) と N-3 (`:705`) | 新規だけ | N-4 の2本目は attempt だけなので valid-first 走査では除外される。N-3でも最初の valid 1件を選べてしまう |
| M9 | N-7 `test_fc05c_rejects_root_attempt_shadow` (`:737`) | 新規だけ | root 優先で resolver を通り、outer 閉包脱落時だけ payload の別 attempt が隠れる |
| M10 | N-6 `test_fc05c_rejects_trigger_payload_extra_key` (`:730`) | 新規だけ | payload 閉包を落とすと binding 自体は valid なので通過 |
| M11 | P-2 `test_live_producer_trigger_with_source_reaches_only_p6_unavailable` (`:639`) | 新規だけ | source 付き mask 18・nonce b の正例が FC05C へ縮退する |

「殺せない」に該当する変異はない。

## 恒真性と FC05C への到達

P-1/P-2 は ledger と WAL を同一 binding から作るため、commitment 比較を失っても正例自体は通る。その不足は以下で補われる。

- 更新済み既存 mismatch は WAL nonce のみを変え、`_rewrite_wal()` が source、projection、result record、sealed evidence digestを追随更新する (`orchestrator/tests/test_reflux_formal_consumer.py:611-615`)。
- N-9 は ledger record と execution provenance を同じ変更値へ同期する (`:753-757`)。
- N-10 は source 付き ledger/provenance を維持し、WAL raw の source だけを `None` にする (`:760-777`)。

したがって `evaluate_formal_origin()` の FC03、FC04、resolver の FC05B、provenance FC03をすべて通り、`_validate_bijection()` の FC05Cへ到達する。呼び出し順は `orchestrator/campaign/reflux_formal_consumer.py:1022-1027`。

なお「M4 を殺すのは既存 mismatch と N-9だけ」は厳密には誤りで、N-10も第三の killer になる。source の差が commitment に含まれるためであり、検査力の不足ではなく冗長な補強である。

## golden と fixture baseline

4値を production hash helperを使わず再計算し、`orchestrator/tests/test_reflux_result_evidence.py:24-27` と一致した。

- canonical raw: 1848 bytes
- Layer 1: `sha256(raw)` = `8fac4b...672ec0`
- Layer 2: 独立な `sha256(raw)` = 同値
- Layer 3: `sha256(bytes.fromhex(_SALT) + domain-NUL + canonical({"evidence_sha256": digest, "outcome": "rejected"}))` = `df6cd7...5e6ef3`
- wrong-domain: `sha256(domain-NUL + raw)` = `5da55e...ffef53`

規則は production の docstring・実装 (`orchestrator/campaign/reflux_result_evidence.py:333-362`) および ledger の domain、salt順 (`orchestrator/campaign/reflux_origin_ledger.py:91`, `:651-656`, `:679-700`) と一致する。fix1報告の再計算手順とも一致する。

baseline は必要な3 entryだけ更新され、authority、launch admission、recovery envelope、source closureの4 entryは不変。`700 → 909` は trigger record が232 bytesから441 bytesへ増えた差分209 bytesで正確に説明でき、source record listも440 bytesから649 bytesへ同じだけ増える。golden testは独立 canonicalizerと literalを維持しており、検査は弱まっていない。

## helper と producer 実走

`_rewrite_wal()` は root に attempt があれば rootだけ、なければ payloadだけを書き換える (`orchestrator/tests/test_reflux_formal_consumer.py:303-314`)。

- N-7では追加した root が fixture attemptへ直され、payload の `"fixture-shadow-attempt"` は保持されるため、意図した食い違いを壊さない。
- 他の呼び出しは production recordの payloadかlegacy terminalの rootの片方だけで、両方を新たに作らない。
- `_live_trigger_record()` の labelは `producer-p1`、`producer-p2`、`producer-n10`で衝突せず、各testの `tmp_path` も独立する。
- `CampaignLayout.ensure()` は `exist_ok=True` (`orchestrator/campaign/layout.py:226-230`) なので既存directoryでも失敗しない。
- producer実走は3 testで各1 append。file・directory fsyncは発生するが、fixture全体に比べ過大な量ではない。
- P-3の2 literalは refs の LINE 1/2とbyte単位で一致し、fix2の timestamp復元も正しい。

## 波及と duration ledger

fixture builder利用箇所は指定どおり9 fileに `test_reflux_result_evidence.py` を加えた10 fileだけだった。旧5 hash値の残存はゼロ。旧 root literal `"kind": "TriggerGateBinding"` は意図したN-1 (`orchestrator/tests/test_reflux_formal_consumer.py:690`) だけである。

`wal.TriggerGateBinding.*` は source-closure の契約名 (`orchestrator/tests/reflux_origin_fixture_builder.py:299-301`) と production側の同一契約に残るが、旧WAL形状のpinではない。その他の root `trigger_binding` はresult evidenceやprovenanceの別schemaで、波及漏れではない。

duration ledgerについて、未登録nodeは `_acceptance_duration_for_item()` が `None`を返し、既知分布から求めたunknown costで並べられるだけで、収集・実行から除外されない (`orchestrator/tests/conftest.py:1527-1547`, `:1587-1619`)。coverage gateも90%下限 (`orchestrator/tests/test_acceptance_schedule_order.py:660-714`) なので13件の追加は事前登録を要求しない。

登録toolはJUnitの実測時間を入力にする (`tools/update_acceptance_duration_ledger.py:57-95`, `:235-282`)。したがって受入全走後に、成功nodeを `--add-only` で登録する順が正しい。

## 総括

静的レビュー結果は GO、must-fix はない。  
M1〜M11は全件殺されるが、M4/M5/M8には事前表より広い重複帰属がある。  
golden 4値とbaseline 3 entryは独立再計算および最小波及に一致した。  
pytestは実走しておらず、焦点走2回目と受入全走の緑は主張しない。