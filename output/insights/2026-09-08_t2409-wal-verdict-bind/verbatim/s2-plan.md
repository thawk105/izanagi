## 採否と理由

**(P1-採用案) を採るべきである。** WAL 全体または系列別 WAL digest literal は新設せず、legacy report 経路が読む全 `verify_done` に次の exact 値述語を追加する。

```python
type(payload.get("anomalies")) is int
and payload.get("anomalies") == 0
and payload.get("certified") is True
and payload.get("verdict") == "serializable"
```

`anomalies` は `False == 0` による迂回を防ぐため、整数型の完全一致も必要である。

現物の構造は次の通りだった。

- 3 系列とも WAL は 135 record、そのうち `verify_done` は 90 record。
- 15 variant ごとに `legacy` 1 件、`performance` 5 件。
- 全 270 件で `anomalies=0`、`certified=true`、`verdict="serializable"`。3 field の欠落は 0 件。
- write-heavy と balanced の `verify_done.payload` は同じ key 集合。
- read-heavy だけ `proof_surfaces` が追加されている。
- `wal.py:14-15` 自身が、WAL に hash chain はなく真正性を保証しないと明記している。

対抗案の系列別 WAL digest は改変検出能力では強いが、3 個以上の新しい authority literal と第 2 の digest 族を作る。また、判定対象でない timestamp、commit 数、`proof_surfaces` まで固定する。read-heavy の key 差により系列別管理も避けられない。これは D1772 の「新しい gate 機構は作らない」から遠い。

採用案も「既存 digest の preimage を広げる」という字義どおりではない。この点の距離は明記すべきである。ただし、凍結 block record と既存 135 literal を変更せず、既存の legacy report 受理ループへ局所的に条件を追加するため、D1772 の「局所修正」「新機構を作らない」側には最も近い実現である。

## プラン (file:line 粒度)

1. `orchestrator/campaign/b10_backoff_shape_sweep.py:3359-3438`

   `_verification_source_disclosure` の単一 WAL read と既存 disclosure 集計を維持する。新しい digest、定数、一般化 helper は作らない。

2. `orchestrator/campaign/b10_backoff_shape_sweep.py:3390-3395`

   現在の `wal.read_records_checked(layout)` の `try/except` は変更しない。特に、新述語をこの `try` の内側へ入れない。内側へ入れると、新しい `PreflightError` まで `except Exception` に握り潰されて `wal_read_error` と空 counts に変換される。

3. `orchestrator/campaign/b10_backoff_shape_sweep.py:3405-3426`

   `record.stage != STAGE_VERIFY_DONE` の `continue` 直後、`workload.tag` と variant mapping を調べる前に上記 exact 述語を置く。不一致または field 欠落なら、例えば code `legacy-wal-verdict` の `PreflightError` を送出する。message には `campaign_id` と `record.variant` を含める。

   これにより検査対象は全 `verify_done` になる。unknown tag と unmapped variant も、集計から `continue` される前に判定される。

4. `orchestrator/campaign/b10_backoff_shape_sweep.py:3411-3426`

   既存の unknown tag、unmapped variant、tag count、point count の処理は変更しない。3 field が正しい unknown/unmapped record は、従来どおり disclosure へ記録され、counts には寄与しない。

5. `orchestrator/campaign/b10_backoff_shape_sweep.py:3518-3608`

   `_collect_report_inputs` 自体の分岐、3 個の `_legacy_*_binding()` 呼出し、3 個の `_validate_legacy_*_records` 呼出しは変更しない。

   legacy 限定は現在の call graph で担保する。production で `_verification_source_disclosure` を呼ぶのは `:3590-3595` の 1 箇所だけで、その呼出しへ到達する campaign は `:3532-3555` の固定 3 ID だけである。

6. `orchestrator/campaign/b10_backoff_shape_sweep.py:2876-3200`

   `LEGACY_*_RECORD_SHA256S`、`_require_legacy_record_digests`、`_legacy_record_content_digest`、3 系列の既存 validator 受理述語には触れない。

7. `orchestrator/campaign/wal.py:1645-1662`

   変更しない。既存の production reader と duplicate-aware JSON parser をそのまま使う。

8. `orchestrator/tests/test_b10_backoff_shape_sweep.py:2530-2651`

   `_verification_source_disclosure` の production caller が `_collect_report_inputs` だけであることを AST で固定する test を追加する。既存の `test_report_collector_reads_only_three_formal_series_and_discloses_sources` と合わせ、formal live campaign ID と trial campaign ID が対象にならないことを維持する。

9. `orchestrator/tests/test_b10_backoff_shape_sweep.py:2752-2853`

   WAL fixture、exact 正例、field 別負例、unknown/unmapped の順序 test をこの近傍へ追加する。

10. `orchestrator/tests/test_b10_backoff_shape_sweep.py:2766-2769`

    既存 `test_verification_completeness_counts_records_and_discloses_wal_anomalies` の WAL fixture に正しい 3 field を追加する。既存 assertion と期待値は一切変えない。unknown tag や list tag の disclosure 期待も維持する。

11. `orchestrator/tests/test_b10_backoff_shape_sweep.py:1898-2201`

    既存 literal、balanced/read-heavy `meta_digest` golden、production record digest の各 assertion は編集しない。新 test は block record を書き換えず、temp WAL だけを生成する。

12. `orchestrator/campaign/b10_backoff_shape_sweep.py:3970-3998`

    report phase の配線は変更しない。新述語の失敗は `_collect_report_inputs` から伝播し、`_write_reports` と report directory 作成へ到達しない。

## 穴が塞がることの論証

指定された攻撃は次の経路で止まる。

1. `run_phase(..., phase="report")` が `b10_backoff_shape_sweep.py:3970-3983` で `_collect_report_inputs` を呼ぶ。
2. `:3532-3578` で固定 3 系列の 45 block record が既存 digest literal と既存 semantic gate を通る。攻撃者が block record を変えていないため、ここは通る。
3. `:3581` の campaign lock binding も、攻撃条件どおり変更されていないため通る。
4. `:3590-3595` から `_verification_source_disclosure` に入り、`wal.py:1645-1662` が差し替え後の WAL を parse する。
5. 各 `verify_done` は tag count や variant mapping より先に exact 3 field を検査される。90 件という件数、15/75 の tag 内訳、variant が正しくても、1 record でも次のいずれかなら `PreflightError` になる。

   - `anomalies` が欠落、非整数、または 0 以外
   - `certified` が singleton `True` 以外
   - `verdict` が exact `"serializable"` 以外

6. 例外は WAL read の `try/except` より後で発生するので握り潰されない。
7. `_collect_report_inputs` が return せず、`:3599-3608` の後続処理および `:3988` の `_write_reports` へ進まない。

全 `verify_done` を対象にするため、悪い record の tag を unknown 値へ変える、または variant を block record に存在しない値へ変えることで既存 `continue` に逃がすこともできない。

現物 3 系列では全 270 `verify_done` が通る。read-heavy の `proof_surfaces` は参照も key 集合比較もされないため、正例を壊さない。

ただし、次は残余として残る。

- WAL が存在しない場合、`read_records_checked` は空 list を返し、述語は一度も評価されない。
- 終端済み不正 frame の例外は現行どおり `wal_read_error` に変換され、report 発行自体は止まらない。
- 未終端 tail は捨てられるため、その tail 内の悪い `verify_done` は検査されない。
- 全 3 field を攻撃者が正常値へ偽装した WAL、または正常 record の複製には真正性防護がない。既存の「repetition identity がなく duplicate と別 repetition を区別できない」という制約も残る。

したがって採用案は、課題で指定された「同じ件数と tag を持つが 3 field が悪い WAL」への穴を塞ぐ。一方、「任意差し替えに対する暗号学的束縛」までは実現しない。

## テスト正例・負例

正例は最低でも次の 2 層にする。

- `test_legacy_verify_done_verdict_accepts_exact_values_and_extra_payload`

  temp `CampaignLayout` に、3 field が exact な `verify_done` と、3 field を持たない非 `verify_done` frame を書く。read-heavy を模した `proof_surfaces` も payload に追加する。production の `wal.read_records_checked` と `_verification_source_disclosure` を通し、期待 counts が返ることを確認する。

- `test_report_collector_accepts_exact_legacy_verdict_fixture`

  3 campaign layout に各 90 record、各 15 variant に `legacy` 1、`performance` 5 を生成する。既存 collector test と同じ形で block validator と lock だけを固定し、実際の `_verification_source_disclosure` は mock しない。`_collect_report_inputs` が返ることを確認する。

負例は parameterized node `test_legacy_verify_done_verdict_rejects_field_mutation` とし、少なくとも次を独立 ID にする。

- `anomalies-nonzero`: `anomalies=1`
- `anomalies-bool-false`: `anomalies=False`
- `anomalies-missing`: key を削除
- `certified-false`: `certified=False`
- `certified-int-one`: `certified=1`
- `certified-missing`: key を削除
- `verdict-other`: `"serializable"` 以外
- `verdict-missing`: key を削除

各 case は WAL の record 数、variant、`workload.tag` を不変にし、`legacy-wal-verdict` の `PreflightError` を期待する。

さらに `test_legacy_verify_done_verdict_is_checked_before_disclosure_filter` を次の 2 case で追加する。

- `unknown-tag`: bad verdict と unknown tag を同じ `verify_done` に置く。
- `unmapped-variant`: bad verdict と unmapped variant を同じ `verify_done` に置く。

どちらも従来の `continue` より先に赤になることを確認する。

本物の現物 WAL は repository 外なので、通常 suite の唯一の正例にはできない。決定的 fixture test が必要である。そのうえで補助的な production-evidence node を同じ test file に置ける。

- 既存の `IZANAGI_OFFICIAL_OUTPUT_ROOT` が設定され、3 campaign が存在する場合だけ実行する。
- `B.campaign_layout(campaign_id, root)` と `_collect_report_inputs` を使い、実際の campaign lock、135 block record、既存 literal、3 WAL をすべて通す。
- 親の実測環境では root を `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output` に設定する。
- 外部証拠がない環境では skip するが、これは fixture 正例の代替にはしない。

既存の次の期待値は無変更で残す。

- `test_e3de15eb_legacy_adapter_enforces_injected_exact_digest_set`
- `test_143a3f74_balanced_adapter_accepts_only_pinned_series`
- balanced `meta_digest == 8e5f0b48...`
- `test_acf840c8_read_heavy_adapter_accepts_only_pinned_series`
- read-heavy `meta_digest == 27195442...`
- `test_acf840c8_frozen_read_heavy_records_match_production_contract`

## 変異事前登録候補

1. `b10_backoff_shape_sweep.py:3408` 付近  
   exact predicate 全体を削除する。  
   赤になる node: `test_legacy_verify_done_verdict_rejects_field_mutation` の全 case。直接 disclosure を呼ぶため他 gate の先行失敗はない。

2. `b10_backoff_shape_sweep.py:3408` 付近  
   `type(anomalies) is int` を `isinstance(anomalies, int)` に変える。  
   赤になる node: `[anomalies-bool-false]`。Python の `bool` が `int` の subclass である点への帰属が明確。

3. `b10_backoff_shape_sweep.py:3408` 付近  
   `anomalies == 0` を、正数も許す条件へ緩める。  
   赤になる node: `[anomalies-nonzero]`。

4. `b10_backoff_shape_sweep.py:3408` 付近  
   `certified is True` を `certified == True` に変える。  
   赤になる node: `[certified-int-one]`。

5. `b10_backoff_shape_sweep.py:3408` 付近  
   `certified` 条件を削除する。  
   赤になる node: `[certified-false]` と `[certified-missing]`。

6. `b10_backoff_shape_sweep.py:3408` 付近  
   verdict の exact equality を truthy 判定または部分一致へ変える。  
   赤になる node: `[verdict-other]` と `[verdict-missing]`。

7. `b10_backoff_shape_sweep.py:3408` 付近  
   3 条件の成功側 conjunction を `or` に変える。  
   赤になる node: 各単独 field mutation case。1 field だけ悪い fixture のため帰属が明確。

8. `b10_backoff_shape_sweep.py:3411-3419` 付近  
   verdict 判定を unknown tag の `continue` より後へ移す。  
   赤になる node: `test_legacy_verify_done_verdict_is_checked_before_disclosure_filter[unknown-tag]`。

9. `b10_backoff_shape_sweep.py:3420-3423` 付近  
   verdict 判定を unmapped variant の `continue` より後へ移す。  
   赤になる node: `test_legacy_verify_done_verdict_is_checked_before_disclosure_filter[unmapped-variant]`。

10. `b10_backoff_shape_sweep.py:3390-3408` 付近  
    validation loop を broad `try/except Exception` の内側へ移し、`PreflightError` を `wal_read_error` に変換させる。  
    赤になる node: field mutation の全 case。負例が例外を期待するため、他 gate による先行失敗はない。

11. `b10_backoff_shape_sweep.py:3405-3407` 付近  
    stage filter を反転または削除し、`build_start` などにも 3 field を要求する。  
    赤になる node: `test_legacy_verify_done_verdict_accepts_exact_values_and_extra_payload`。正例 fixture に 3 field のない非 `verify_done` を含めて帰属を固定する。

12. `b10_backoff_shape_sweep.py:3590-3597`  
    collector から disclosure 呼出しを迂回し、空 counts を直接設定する。  
    赤になる node: `test_report_collector_rejects_same_counts_and_tags_when_legacy_wal_verdict_changes`。この node は block validator と lock を通る fixture に固定しないと、別 gate が先に赤になる恐れがある。

## 未解決・親へ返す点

- 採用案は D1772 の「既存 digest の対象へ加える」を字義どおりには実現しない。凍結証拠を変更できないための限定的代替であることを insight と decision fragment に明記すべきである。
- missing WAL、`wal_read_error`、truncated tail を fail-closed にするかは別の裁定が必要である。今回同時に止めると、親の P1 より受理集合をさらに狭め、単なる 3 field 値述語を越える。
- 正常値を偽装した WAL や duplicate replay は防げない。これまで含めて「WAL の真正性へ束縛した」と主張するなら、採用案では不足し、系列別 digest など別裁定が必要になる。
- repository 外の現物証拠 test は補助 test にしかできない。親環境で production-evidence node を必ず実行するか、標準 suite に外部証拠依存の skip node を置くかを親が選ぶ必要がある。
- read-only のため pytest は実行していない。確認したのは指定ファイルと現物 WAL の静的読取だけである。

## 総括

採るべき実装は、`_verification_source_disclosure` の `verify_done` ループ先頭へ exact 3 field 述語を直接追加し、その例外を既存 broad catch の外から伝播させる局所修正である。全 `verify_done` を tag/variant filtering より先に検査し、legacy 3 系列だけに到達する現行 call graph を test で固定する。

これにより、45 block record、campaign lock、90 件の件数、15/75 の tag 内訳を保ったまま 3 field を崩す攻撃は report 書込み前に停止する。135 digest literal、2 個の `meta_digest` golden、凍結 block record、既存 legacy validator は無変更で維持できる。