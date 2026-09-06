## GO/NO-GO

NO-GO

canonical-list 経路では outer value の型が未検査で、production producer が生成できない trigger を受理します。

## must-fix

- `orchestrator/campaign/reflux_formal_consumer.py:734` / `orchestrator/campaign/reflux_result_evidence.py:601` - `variant`、`env_tag`、`ts` の型を検査せず、canonical-list source は `wal.parse_line()` を通らないため、`ts: "invalid"` や `ts: true`、非 string の variant/env_tag が FC05C を通過して P6 へ到達し、受理集合が production 形状より広がります。`wal.py:386-400` と同じ型契約を適用する必要があります。

## nit

- P-3 の build_start は consumer の topology 検査には使われません。`_wal_trigger()` は trigger だけを読み、build_start commitment はテスト側の独立 assertion にのみ使われます。テスト名の「sequence」は consumer が隣接順を検証するようにも読めます。
- raw non-dict、key 不足、schema/IR 不一致、mask 範囲外、predicate 不整合、nonce 不正、source 構造不正は実装上拒否されますが、今回追加された FC05C テストでは個別に pin されていません。
- plan v2 の author allowlist は5ファイルでしたが、統合差分は fix1 の golden 更新を含む6ファイルです。追加分は `test_reflux_result_evidence.py` のみで、報告された赤4件への修正と整合します。

## plan v2 と受理集合

`_wal_trigger()` は plan v2 の (a)〜(e) に逐語的に一致しています。

- (a) stage 抽出とちょうど1件: `reflux_formal_consumer.py:726-732`
- (b) outer exact keys: `reflux_formal_consumer.py:734-736`
- (c) exact dict payload と exact keys: `reflux_formal_consumer.py:737-742`
- (d) `validate_record(..., require_source=False)` と一様な None 化: `reflux_formal_consumer.py:744-750`
- (e) mask、LSB-first wire、commitment の再構成: `reflux_formal_consumer.py:752-756`

旧形状、別 stage、duplicate、outer/payload 余分 key はそれぞれ stage 件数または exact-key 検査で拒否されます。raw binding の非 dict、key 過不足、schema、IR、mask、predicate、nonce、source の不正は `trigger_gate_binding.py:205-239` が `TriggerGateBindingError` に閉じ、FC05C になります。

`set(record)` と `set(payload)` は順序非依存です。artifact の JSON 境界が key を exact string に限定するため、実際の evaluate 経路では非 string key は到達しません。`ts` は int と float の双方が production 上正当ですが、現状はそれ以外の JSON 型まで通る点が must-fix です。

## 判定順序と単一理由

呼び出し順は FC04 → FC05B → provenance FC03 → FC05A/FC05C → FC06 → FC07 です。

- N-1、N-2は resolver を通過した後、stage 件数0で FC05C。
- N-3、N-4は両 record の attempt が一致し、raw validation より先に stage 件数2で FC05C。
- N-5、N-6は resolver が nested schema を解釈せず、FC05C の exact 検査で拒否。
- N-7は `_projection_attempt_id()` の root 優先で FC05B を通り、outer extra key により FC05C。
- N-8〜N-10は helper が ledger member と execution provenance を同期するため FC04/FC03を通り、WAL 射影との exact 比較だけが FC05C で失敗。

したがって、登録済み N-1〜N-10を別 reason が先取する経路は静的にはありません。

## commitment と逐語 literal

Fixture の ledger commitment と raw WAL は同じ binding と `trigger_gate_binding.commitment()` から作られるため、P-1/P-2だけでは共通実装の誤りを独立検出できません。

P-3 は refs の2行と byte 単位で一致しました。trigger は446 bytes、build_start は242 bytesで、両 `ts` を含め一致しています。直呼び assertion は consumer の再構成 commitment を固定済み build_start commitmentへ結び、`_evaluate()` は literal の値が resolver、FC05C、後段検査を通って P6へ到達することを証明します。

M4は nonce mismatch と N-9、M7は N-5が実際の殺傷点です。

## producer 実走と terminal carry

`CampaignLayout.ensure()` は test 固有 tmp 配下に directory だけを作り、campaign.lock は生成しません。trigger_binding stage は `wal.py:1194-1198` の lock 読取り対象外です。append は test 固有 WAL を flock し、WAL file と runs directory を fsyncしますが、他の file は生成しないため隔離上の問題はありません。

Fixture は production trigger と legacy root-kind terminal の混在です。これは `_projection_attempt_id()` の payload/root 両対応と、`_wal_field()` の両対応に依存します。一方、`_validate_wal_outcomes()` は terminal の root `kind` を要求するため、production terminal は引き続き FC07です。段4裁定と author報告は原因、影響、別 carry の境界を十分具体的に記述しています。

Patch と作業ツリーの両方で、`wal.py`、`trigger_gate_binding.py`、`reflux_result_evidence.py`、`reflux_ir.py`、`model.py` に差分はありません。変更されたのは consumer、fixture関係4ファイル、golden test 1ファイルの計6ファイルです。

## 変異 M1〜M11 の帰属

| 変異 | 殺すテスト |
|---|---|
| M1 | `test_fc05c_rejects_legacy_root_trigger_binding_shape` |
| M2 | `test_fc05c_rejects_trigger_payload_under_non_trigger_stage` |
| M3 | `test_fc05c_rejects_ledger_mask_only_mismatch` |
| M4 | `test_fc05c_rejects_wal_trigger_binding_mismatch`、`test_fc05c_rejects_ledger_commitment_only_mismatch` |
| M5 | `test_fc05c_rejects_duplicate_valid_trigger_stages` |
| M6 | `test_exact_fixture_contract_reaches_only_p6_unavailable`、P-1、P-2、P-3 |
| M7 | `test_fc05c_rejects_raw_trigger_binding_extra_key` |
| M8 | `test_fc05c_rejects_duplicate_trigger_stages_with_invalid_second_payload` |
| M9 | `test_fc05c_rejects_root_attempt_shadow` |
| M10 | `test_fc05c_rejects_trigger_payload_extra_key` |
| M11 | `test_live_producer_trigger_with_source_reaches_only_p6_unavailable` |

全11変異に静的な殺傷テストがあります。pytest は実走しておらず、緑は主張しません。

## 総括

- 実装は plan v2 の (a)〜(e) と一致し、N-1〜N-10の FC05C 帰属も成立します。
- commitment の独立 pin、逐語 bytes、producer test 隔離、terminal carry は妥当です。
- ただし canonical-list 経路で outer value 型が未検査です。
- production 形状だけへの閉包が未達のため NO-GOです。