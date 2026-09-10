### `stage` への置換だけで、production 外の root-flat terminal が新たに通る

種別: real

根拠: `reflux_result_evidence.py:594-598` は attempt を root 優先で読み、同 file:601-608 は source が canonical list なら `wal.parse_line()` を通さず、そのまま受理する。file:653-658 の record 検査も「dict で attempt が一致」のみである。`reflux_formal_consumer.py:726-778` の exact-shape gate は trigger にしか適用されず、file:821-825 の `_wal_field()` は root を優先する。したがってプランどおり file:861/867 を `terminal.get("stage")` に替えると、旧 fixture と同じ flat recordを `kind` から `stage` へ名前変更しただけの、例えば `{stage:"abort", build_attempt_id:..., candidate_attributable:true, truncated:false, witness_class_sha256s:[...]}` が FC07 を通る。`variant`、`env_tag`、`ts`、`payload` は不要である。

影響: production 形状でない terminal evidence が FC07 rejection ではなく P6Unavailable receipt と projection を得て、レポート上の受理集合と proof-chain 参照が変わる。

分類: scope 外・裁定パッケージ候補。これを閉じる terminal outer-shape gate または terminal 専用 payload 読みは、brief:60-61 の P4 と「2 行だけ」の確定 scope を広げる。

### payload-only `stage` は拒否される一方、root/payload の矛盾は root 側が勝つ

種別: real

根拠: プランの新判定は `s2-plan.md:18-40` の `terminal.get("stage")` なので、payload にだけ `stage` がある record は FC07 で落ちる。反対に root `stage` が正しければ payload 内の相反する `stage` は参照されない。attempt は `reflux_result_evidence.py:594-598` と `reflux_formal_consumer.py:821-825,858-859` の双方で root 優先であり、verify/witness fields も file:864,870-877 から `_wal_field()` 経由で root 優先になる。このため root attempt/witness が正しければ、payload 側の同名値が誤っていても通る。

影響: root shadow を含む非 production terminal が正式な terminal と同値に扱われ、FC07 の受理集合が production producer の出力集合より広くなる。

分類: scope 外・裁定パッケージ候補。D1665 の trigger root-shadow 拒否と同等の処置は P4 の再裁定を要する。

### 旧 root `kind` 負例は FC05B/FC05C を越え、実際に FC07 で落ちる

種別: refuted

根拠: `test_reflux_formal_consumer.py:303-327` の `_rewrite_wal()` は root `build_attempt_id` を選択 attempt に書き換え、source bytes、projection range/hash、physical result digest も同期する。したがって `reflux_result_evidence.py:651-662,687-688` の attempt と content-addressed 検査を通る。trigger は既存の production-shaped recordを再利用し、`reflux_formal_consumer.py:726-778` の FC05C は terminal の旧 `kind` を検査しない。評価順も file:1032-1041 で FC05B、FC05C、FC06 の後に FC07 である。プランの legacy terminal は `s2-plan.md:124-139` のとおり root attempt を持つため、最初の terminal 検査で `stage` 不在として FC07 になる。

影響: この負例は恒真な前段落ちではなく、旧 `kind` rejection を正しく固定する。ただし `kind` を `stage` に改名した flat shape は所見1のとおり未検査である。

分類: nit。提示テスト自体の修正は不要。

### production commit 正例は commit 枝を通過した後にだけ P6Unavailable へ到達する

種別: refuted

根拠: `s2-plan.md:144-170` は physical result を acceptedかつ constraint `None` にし、これは `reflux_result_evidence.py:291-303` の exact schemaを満たす。terminal payload attempt は `_rewrite_wal()` により同期され、resolver を通る。`reflux_formal_consumer.py:855-865` では physical outcome が accepted なので commit stage と verifier order の枝を必ず実行する。file:1039-1047 で `_validate_wal_outcomes()` 後にも FC09/FC10 を通り、P6Unavailable を作る唯一の経路は file:1056-1082 である。

影響: 旧 `kind` reader では FC07、新 `stage` readerでは P6Unavailableとなるため、正例は今回の commit 修理を実際に識別する。

分類: nit。追加 instrumentation は不要。

### 4 個の hash と `byte_length: 975` は read-only の in-memory 再計算で一致した

種別: refuted

根拠: `reflux_origin_fixture_builder.py:63-80` の独立 canonical JSON、file:362-400 の変更予定 WAL、file:417-473 の result record 合成を、ファイルを書かず関数だけメモリ上で差し替えて再計算した。結果は次のとおり完全一致した。

- ordered WAL: length `975`, SHA-256 `271323c60ad2af8b4034872096d5c1c5066f26c6c85689252dd5ce762ddd3bc6`
- result record: length `1848`, SHA-256 `631a5fa04f9cc1a5442c5660410bb27b1ad03ef76f5da3fe3d4603ac5577c82c`
- outer salted commitment: `5aaf3851fe1c8b55ee009a35b9f319cc1feee93d45df7a99c68a56da8bba6cf7`
- wrong-domain digest: `515e7f7ca39461903b9d3291dd010b9576732ff2674f1b29e677aba6032399c3`

`reflux_result_evidence.py:65-71,333-350` は record raw hash と ledger evidence digest が、別 helperながら同じ raw bytes の SHA-256 になる契約を明記している。したがって更新後の baseline line 25、`_RECORD_RAW_GOLDEN`、`_LEDGER_EVIDENCE_DIGEST_GOLDEN` が同じ `631a...` になるのは正しい。

影響: 提示値を採用しても hash 層や台帳 digest の意味は変わらず、fixture変更後の bytes を正しく参照する。

分類: nit。値の取り直しは不要。pytest は実走しておらず、緑とは判定していない。

### 親 brief の事実6は downstream fixture pin を閉包に含めていない

種別: real

根拠: `reflux_origin_fixture_baseline.json:15-25` は ordered WAL と result record の length/hash を固定する。`test_reflux_origin_fixture_builder.py:107-119` は全 builder 出力をその baseline と独立再計算で exact 比較する。`test_reflux_result_evidence.py:24-27,145-181` も result bytes と派生 hash を literalで固定している。

影響: 2 pin fileを更新しない場合、baseline と literal evidence参照が実物から外れ、関連テストも既知の不一致になる。

分類: scope 外・裁定パッケージ候補。

親の閉包に構造的に欠けていた点: 3 source file 自身への path/hex 参照だけを検索し、`_wal_records()` から `build_ordered_wal_projection()`、`build_result_evidence_record()`、baseline/literal goldenへ至る生成物依存グラフを辿っていなかった。

### 親 brief の事実2と事実4も範囲を広く言い過ぎている

種別: real

根拠: 事実2の `error` は prebuild abort の `pipeline.py:1071-1075` にはあるが、一般 abort の file:1206-1215 は `{reason, build_attempt_id, build_admission_receipt_sha256, **extra}` で、`error` は必須でない。事実4の「落ちているのは kind 2 行だけ」は accepted commit には当てはまるが、production abort payloadには `reflux_formal_consumer.py:870-877` が要求する `candidate_attributable`、`truncated`、`witness_class_sha256s` がない。pipeline.py:1071-1075,1206-1215 にもそれらは書かれていない。事実1、3、5、7は主要結論としては妥当だが、事実3の `WalRecord` 形状は producer契約であって canonical-list consumer の shape gateではない。

影響: 放置すると「修理後は production accepted/rejected の双方が通る」と誤読されるが、実際に新たに通るのは accepted側で、rejected側は引き続き FC07となる。

分類: nit。brief:50-57 と brief:78-80 は既に P1 の限界を正しく記しているため、最終報告で表現を揃えればよい。

## 総括

must-fix:

- 確定済みの狭い scope 内ではなし。提示された負例、正例、golden値には前段落ちや計算誤りはない。

親が段4で裁定すべき択一:

- terminal shape: P4を広げ、production outer shapeとpayload-only field参照を要求して root-flat/shadow形状を拒否するか。推奨は拡張する。現行2行案を維持する場合は、非 production terminal の新規受理を規律2上の既知例外として明示的に再裁定する必要がある。
- fixture pins: `reflux_origin_fixture_baseline.json` と `test_reflux_result_evidence.py` を機械的同期の scope に含めるか。推奨は含める。含めない場合は stale pinと関連テスト不一致を意図的に残す選択になる。
- rejected production: P1どおり producer新設を scope 外に保ち、修理後も rejected側が FC07で止まる限界を最終報告へ明記するか。現在の確定 scopeに従うなら「保つ」が整合的である。