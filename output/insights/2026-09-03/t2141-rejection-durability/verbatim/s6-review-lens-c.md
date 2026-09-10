## must-fix

- [p3_b4_material_report.py:980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/campaign/p3_b4_material_report.py:980) — `producer_rejections` を持たない既存 renderer-only 入力が `KeyError` となる。放置すると certified 選択、受理集合、台帳値は変わらないが、既存互換入力から材料レポート Markdown を生成できず参照成果物が欠落する。
- [p3_b4_raw_record_producer.py:693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/campaign/p3_b4_raw_record_producer.py:693) — tail 切り捨て事実は追記成功時の戻り値にしか残らず、追記後の loader は `fragment_discarded=False` を返す。放置すると台帳 bytes は修復される一方、材料レポートの履歴状態と参照が切り捨てなしへ変わる。certified 選択と受理集合は不変。
- [p3_b4_raw_record_producer.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/campaign/p3_b4_raw_record_producer.py:696) — 完全な `write` 後の `fsync` 失敗では戻り値に `IO_ERROR` が付く一方、可視な未確認 event は後続 loader で通常 event として数えられる。放置すると台帳は crash 後に消失し得るのに、材料レポートの event 数、率、unresolved、履歴非保証が耐久 event と同じ値になり、参照が不安定になる。受理集合は rejection のまま、certified 選択は不変。

## 契約違反

- R-C/R-E は部分違反。未終端 tail 自体は最後の改行まで正しく切られるが、その事実が独立した後続 consumer へ届かない。
- `fsync` 失敗は R-D どおり `IO_ERROR` 付き rejection を返すが、可視 event を durability 未確認として運ぶ状態がなく、R-E の材料レポートが通常 event と区別できない。
- R-A、R-B、R-D の呼び出し範囲、R-F の安価な fixture 方針は遵守している。
- commit 差分上、`_publish_exact` と `B4_RAW_RECORD_NON_GUARANTEES` は変更されていない。hash-chain field と再生成検査もなく、deferred は writer を通らない。
- batch の collection 型検査は publication 検証より前のままで、返却優先順位も維持されている。

## 受理集合と記録失敗の結合

- 棄却入力から成功公開へ戻る枝は増えていない。成功時は従来どおり `_publish_exact` 直後に return する。
- 新しい拒否は ledger 固定 path、その配下、publication root との planned-path 衝突だけで、裁定どおりの縮小である。
- append、write、`fsync` の失敗はいずれも `IO_ERROR` を追加し rejection を維持する。ただし返却型が常に `B4RawRecordDurableRejection` なのは意味上紛らわしい。
- ledger 読み取り失敗は `status="invalid"` の独立値となり、assembly 本来の成功・棄却理由へ昇格していない。
- 新 subtype はいずれも `B4RawRecordRejection` を継承しており、確認対象の既存 `isinstance` 判定は壊していない。

## 段 3 所見の閉じ具合

- sol 1 の fd flags と mode、sol 2/luna 2 の tail 連結破損、sol 3/luna 1 の deferred 後の現在理由、sol 4/luna 5 の完全切断非保証、manifest 外の `not_selected`、assembly 障害隔離は実装された。
- tail の構造修復は閉じたが、修復事実の後続 consumer への伝達は閉じていない。
- sol が指摘した `fsync` 後の「可視だが耐久性不明」は閉じていない。
- publication 検証前 rejection の scope 限定、hash chain 見送り、deferred 非記録は裁定どおり。
- 並行追記の未実測は裁定どおり diagnostic 扱いであり、今回の契約違反には数えない。
- 親実測の renderer 互換性破壊は段 3 に無かった新規 regression である。

## nit

- [p3_b4_raw_record_producer.py:838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/campaign/p3_b4_raw_record_producer.py:838) — `complete` は必ず改行境界までに正規化されるため、直後の `not raw_line.endswith(b"\n")` は到達可能な byte 入力では発火しない。発火入力は名指しできず、成果物影響もない。
- [p3_b4_raw_record_producer.py:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2141-rejection-durability/orchestrator/campaign/p3_b4_raw_record_producer.py:720) — append 失敗時にも `B4RawRecordDurableRejection` を返す命名は実状態と逆だが、`IO_ERROR` と継承関係により現行判定値は保たれる。
- `fsync` 失敗後の可視 event と、修復後の材料レポートを直接検査する test がない。

## 総括

- must-fix は 3 件。親実測の赤 1 件に、tail 修復履歴の消失と `fsync` 未確認 event の誤分類が加わる。
- 成功公開の受理集合拡大、deferred 記録、hash chain、`_publish_exact` 改変は認めない。
- ledger 障害は assembly の成功可否から隔離され、既存 `isinstance` 契約も維持されている。
- tail bytes の修復そのものは正しいが、その履歴は材料レポートまで保存されない。
- 静的検査のみ実施し、pytest は実行していない。