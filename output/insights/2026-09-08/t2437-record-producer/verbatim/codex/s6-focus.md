## 所見×対応表

| 所見 | 判定 | 現物根拠 |
|---|---|---|
| A-1 | closed | terminal 外枠を production の exact 5 key に限定。[reflux_result_evidence.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:527) |
| A-2 / B-1 | closed | canonical projection bytes から digest を導出し、assembler で ref digest と照合。[reflux_result_evidence.py:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:493)、[同:738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:738) |
| A-3 | closed | drift assertion と切詰め・単一 class 防護の comment が分離され、typed/wire 二重検査も維持。[reflux_result_evidence.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:479) |
| A-4 | closed | verify order 4 境界値を追加し、統合経路は33件すべて実 issuer を通る。[test_reflux_result_evidence.py:741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:741)、[test_reflux_formal_consumer.py:927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:927) |
| A-5 | closed | shared validator は旧 consumer 本体と body AST 同値。digest wrapper の `ArtifactError -> FC07` も維持。[reflux_formal_consumer.py:1102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1102) |
| B-2 | closed | synthetic Silo 限定、production 到達性非証明、salts 未行使、ledger replay 不要を明記。[test_reflux_formal_consumer.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:813) |
| B-3 | pending-parent | 現在36 nodeid。collection/JUnit 実測と受入所要台帳への追加は親担当。 |
| B-4 | closed | fixture builder、baseline、`wal.py`、`pipeline.py`、verifier の `git diff --exit-code` は rc=0。golden 定数も変更なし。 |
| B-5 | closed | producer/consumer は同じ canonical anomaly digest を使用。[reflux_result_evidence.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:406) |
| B-6 | closed | 差分は所有4ファイルだけ。新規・未追跡ファイル、S3、pipeline 配線、追加 production file はなし。 |
| B-7 | closed | 静的AST計数は result-evidence 35件、consumer 1件。段5の24 nodeidは改名0・削除0。skip/xfail追加なし。 |

### 正当入力の静的経路

production writer は外枠を `{variant, stage, env_tag, ts, payload}` の5 keyだけで生成します。[wal.py:407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/wal.py:407)

- JSONL 経路は各 frame を同じ5 fieldへ再投影します。[reflux_result_evidence.py:1076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:1076)
- canonical-list 経路も strict parse 後に canonical bytesへ戻ります。[同:1068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:1068)
- projection 自体は canonical exact object、schema、attempt、非空 records を検査し、terminal の5 key検査へ到達します。[同:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:506)
- raw projection digest は consumer の content-addressed ref と同じ SHA-256 定義で、assembler が一致を要求します。[同:545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:545)、[同:972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:972)

したがって、production JSONL由来と canonical-list由来の双方で正当入力が新たに拒否される経路は認めません。

### 不正入力の追跡

| 入力 | 具体値 | 拒否位置 |
|---|---|---|
| 同 attempt・別 projection | typed は `r9_dense_cycle4`、ref は `r3_cycle3` | digest 不一致。[test_reflux_result_evidence.py:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:849) |
| root shadow | `reason`、`verify_configs`、`verify`、`build_attempt_id` | terminal 5-key exact 検査。[同:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:596) |
| verifier order | policy `["legacy","s2"]` に対し `[]`、`["legacy"]`、逆順、`["legacy","legacy"]` | tuple exact 不一致。[reflux_result_evidence.py:549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:549) |
| 別 run snapshot | typed `r9`、terminal snapshot `r3` | canonical bytes 不一致。[同:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:600) |
| reason 不一致 | verdict `non-serializable`、payload reason `indeterminate` | [同:598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:598) |
| dirty | `r4_mixed_cycle`、`integrity.clean() is False` | typed clean と wire clean/counter。[同:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:573) |
| 空 witness | `total_cycles=1`, `anomalies=[]` | typed cardinalityとwire singleton/total。[同:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:584) |
| 切詰め | `total_cycles=4`, `len(anomalies)=1` | typed/wire total equality。 |
| 複数 class | `total_cycles=len(anomalies)=4` | typed/wire singleton。 |

列挙対象で通過する不正入力はありません。

既存テストの期待値については、HEAD既存 test の変更は `test_fc07_converts_witness_canonicalization_artifact_error` の monkeypatch owner 移動だけで、期待する FC07 は不変です。段5の24 nodeidにも反転・緩和・改名・削除はありません。

## 新規所見

production defect、受理集合 regression としての新規所見はありません。

ただし M15 の提示された正方向 literal は現物に存在しません。これは実装欠陥ではなく、変異 anchor の再照準事項です。

## 変異×位置×nodeid

`R` = `orchestrator/tests/test_reflux_result_evidence.py`。すべて静的判定であり、pytest実測ではありません。

| 変異 | fix後の old 逐語と一意性 | 殺す nodeid | mask |
|---|---|---|---|
| M2-typed | `and verify_result.integrity.clean() is True`、[578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:578)、1件 | `R::test_synthetic_silo_source_refuses_dirty_nonserializable_result` | 3置換を同時適用すれば既知maskなし。単独ではmaskあり |
| M2-wire | `if integrity.get("clean") is not True:`、同448、1件 | 同上 | 同上 |
| M2-counter | `type(integrity[key]) is int and integrity[key] == 0`、同451、1件 | 同上 | 同上 |
| M3-typed | `or len(verify_result.anomalies) != 1`、同588、1件 | `R::test_synthetic_silo_source_refuses_multiple_witness_classes` | typed/wire同時なら既知maskなし |
| M3-wire | `if type(anomalies) is not list or len(anomalies) != 1:`、同480、1件 | 同上 | 同上 |
| M4-typed | `or verify_result.total_cycles != len(verify_result.anomalies)`、同587、1件 | `R::test_synthetic_silo_source_refuses_truncated_multiple_witness_classes` | typed/wire同時なら既知maskなし |
| M4-wire | `if anomaly_count != len(anomalies) or total_cycles != anomaly_count:`、同488、1件 | 同上 | 同上 |
| M5 | 親案どおり変異から削除。old anchor不要 | 空 witness testは現存 | 該当なし。M3/M4との重複を避ける削除は妥当 |
| M15 | 提示 literal `ordered_wal_ref["sha256"] == derived.ordered_wal_sha256` は0件。実在 anchor は `if ordered_ref["sha256"] != derived.ordered_wal_sha256:`、[738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:738)、1件 | `R::test_formal_consumer_contract_assembler_rejects_different_projection_same_attempt` | 実在 blockへ再照準すればmaskなし |
| M16 | `if set(terminal) != _PRODUCTION_WAL_RECORD_KEYS:`、[527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:527)、1件 | `R::test_formal_consumer_contract_refuses_terminal_root_shadow[reason\|verify-configs\|verify\|build-attempt-id]` | 4件とも既知maskなし |

## 総括

closed 10、partial 0、regressed 0、pending-parent 1。  
正当な production/canonical-list 入力の regression と、列挙された不正入力の通過は認めない。  
段5 nodeidは改名0・削除0。pytestは未実行で、緑とは判定していない。  
M15 anchorを実在する負方向guardへ再照準する条件で、実装を支持する。