## must-fix

- `s2-plan.md:37-41` / `orchestrator/campaign/wal.py:84-86,1941-1943`: 提案コードは payload に `trigger_gate_binding` が存在することしか確認しないため、余分な key を持つ非 production payload を受理する。payload の key 集合を `{build_attempt_id, trigger_gate_binding}` に閉じ、その負例を追加すべき。
- `orchestrator/campaign/reflux_result_evidence.py:594-598,601-607,657-662` / `s2-plan.md:28-56`: 通常の payload attempt 不一致は FC05B で拒否されるが、canonical-list 経路では root に正しい `build_attempt_id` を足すと payload 内の不一致が隠れ、提案 `_wal_trigger()` が受理する。選択した trigger record の outer key 集合を production の `{variant, stage, env_tag, ts, payload}` に閉じるか、root/payload の曖昧性を明示的に拒否する必要がある。
- `s2-plan.md:123-145,212-224` / `orchestrator/campaign/trigger_gate_binding.py:172-202`: fixture の raw WAL と ledger commitment は同じ binding と同じ `commitment()` から生成されるため、正例の identity assertion は恒真で、source を commitment から落とす共通変異を殺せない。source 付き正例と、source だけを変えた commitment 不一致負例、または既知 commitment 値の独立 pin が必要。

## nit

- 受理経路の追跡結果は、旧 root 形状と別 stage が stage record 0 件で FC05C、raw binding の非 dict が `validate_record()` から FC05C、stage record 2 件以上が payload の正否にかかわらず FC05Cとなる。これらは提案どおり fail-closed。
- `orchestrator/campaign/wal.py:1947-1948,1954-1973` は同じ attempt の binding 重複を orphan/tombstone の有無より前に拒否する。合法な orphan 後の再 binding は別 attempt であり、`reflux_result_evidence.py:657-658` が同一 projection への混在を拒否するため、FC05C が projection 内の binding 2 件を拒否しても正しい production 履歴は失われない。
- `s2-plan.md:134-154,212-224` の正例は trigger の直後が legacy abort で、`wal.py:1975-1981` が認める trigger直後の `build_start` 系列ではない。「production record 形状を通す FC05C 正例」であって「production WAL interval の full 正例」ではないと明記すべき。可能なら逐語 record の第2行 `build_start` も含めると証拠が強くなる。
- pytest は実走しておらず、静的検査だけである。

## 親 brief への所見

- (P1): 部分反証。WAL 側の mask、`encode_wire()`、`commitment()` は ledger record とは別入力から導かれ、`reflux_formal_consumer.py:738-742` の exact dict 比較も維持されるため、判定本体は非恒真である。一方、payload exact-key と outer-envelope/attempt の閉包が不足し、受理集合は production 形状1つに閉じていない。`candidate_wire` は fixture の独立 `_wire()` により共通変異を避けている。
- (P2): 支持。旧形状の値を ledger と一致させた負例は、両受け互換層だけを確実に露出させる。
- (P3): 支持。ただし必須 carry である。production terminal は `orchestrator/campaign/model.py:24-36` の `stage == "commit"` または `"abort"` で、outer record は `wal.py:378-404` により root `kind` を持てない。したがって trigger 修理後も production projection は `reflux_formal_consumer.py:825,831` で必ず FC07 になる。T-2257 は `_wal_trigger()` を名指ししているため同 wave への拡張は DW-G05 上不要だが、今回の成果を production end-to-end 修理とは呼べない。
- (P4): 支持。`TriggerGateBindingError` を `None` に閉じれば既存 FC05C が正しく拒否し、未捕捉例外にもならない。別 reason code は正しさを強めず、要求外の外部判定面を増やす。
- (P5): 条件付き支持。動的 producer 呼び出しと逐語 literal の併用は現行形と履歴形の双方を pin する。ただし payload-extra、attempt-shadow、source-only mismatch を追加しなければ受理集合と commitment の独立性を十分に証明しない。
- (b): 1件の実測事実として支持するが一般化は不可。固定 nonce は別の valid nonce による負例で足りる。source 付きは必ず正例と source-only mismatch が必要。既定 producer の float `ts` と fixture の int `ts` で許可された2型は覆える。`env_tag` と `variant` は FC05C の派生値ではないため、代表的な非空値で十分だが、outer production 形状を閉じるなら不正型の拒否も確認すべき。
- (c): 支持。ledger は `reflux_result_evidence.py:106-108,273-289` の exact 3 key に閉じるが、mask・wire・commitment 間の関係自体は検査しないため、その関係を FC05C が独立に再構成する意味がある。production の projection/provenance producer が未実装という限界も検索結果と整合する。
- (d): 支持。ただし `_projection_attempt_id()` の root 優先は、root と payload が併存する非 production recordでは不一致を隠す。terminal の root `kind` 問題も記載どおり残存する。
- `require_source=False`: 支持。`trigger_gate_binding.py:221-232` は null と構造正しい source の双方を受理し、`172-202` は source を commitment に含める。admission は `wal.py:1982-1992` で receipt 付きなら source 必須、receipt 無しなら non-null source を拒否するため、親の責務分離と整合する。

## 総括

- 提案の FC05C 射影と重複拒否は基本的に正しい。
- payload exact-key、outer/attempt shadow、source-only 検査の3点は修正必須。
- terminal 修理は別 carry を支持するが、完了までは production projection は FC07 を通らない。
- 静的検査のみで、テストの緑は主張しない。