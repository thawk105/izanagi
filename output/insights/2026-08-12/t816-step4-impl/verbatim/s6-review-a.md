静的検査のみ実施し、pytest は実走していない。必須 4 成果物と `integrated.diff` 全 1,856 行を読んだ。

## Must-fix

### 1. record tag が完全一致でなく先頭文字だけで判定され、壊れた trace を certified にできる

- [orchestrator/verifier/parse.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/parse.py:153)

  > `tag = line[0]`

- [orchestrator/verifier/parse.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/parse.py:156)

  > `if tag == "C":`

- [orchestrator/verifier/parse.py:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/parse.py:166)

  > `_, txid, thid, epoch, tid, read_count, write_count = f`

- [orchestrator/verifier/parse.py:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/parse.py:235)

  > `elif tag == "E":`

**real。** `f[0]` を検査せず `_` に捨てるため、たとえば正規の `C 0 0 1 1 0 0` に続く `End 0` が正規の `E 0` として受理される。同様に `Read`、`Write`、`Commit` なども field 数が合えば既知 record として扱われる。`C` 自体を正規にすれば前段の commit 件数確認も通るので、pipeline から到達可能な fail-open である。

テストにも「未知 tag `Z`」はあるが、既知文字で始まる不正 tag の負例はない。

**成果物影響:** malformed trace が `Integrity.clean() == True`、`certified=True` となり、偽の certified 選択と COMMIT が台帳へ入る。

### 2. 凍結 evidence の `verifier_module` hash が現行ファイルとの一致を要求したままで、静的に成立不能

- [test_silo_ladder_rung1_evidence.py:1246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1246)

  > `historical_sha256_by_key = {`  
  > `"driver": ...`  
  > `"policy": ...`  
  > `}`

- [test_silo_ladder_rung1_evidence.py:1259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1259)

  > `assert binding[key]["sha256"] == current_sha`

- [silo_ladder_rung1.json:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:119)

  > `"verifier_module": {`  
  > `"path": "orchestrator/verifier/report.py",`  
  > `"sha256": "e604cef0..."`

**real。** `report.py` は本 wave で変更済みで、静的に計算した現行 SHA-256 は `59b1e805...`。凍結 binding は `e604cef0...` のままなので、上の equality は成立しない。`driver` と `policy` は historical hash として分岐させたのに、同じく変更された `verifier_module` が漏れている。

これは unit B の申告とも食い違う。

- [unit-b-report.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4-impl/unit-b-report.md:10)

  > `記録済み verifier、trace 要約、build、compile commands、attestation、seal、manifest の検査は維持。`

**成果物影響:** 凍結 rung1 proof chain の binding 検査が成立せず、歴史 evidence の `all_pass`／台帳参照を受入済みとして扱えない。

### 3. 変異 M1 は現在の記述では単一 gate の無効化にならない

- [s4-ruling-plan-v2.md:156](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4-impl/s4-ruling-plan-v2.md:156)

  > `M1 | C の 7-field 検査を 5-field も受理へ戻す`  
  > `前後に v1 を拒否する層は無い`

- [parse.py:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/parse.py:158)

  > `if len(f) == 5:`  
  > `raise ParseError(...)`

- [parse.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/parse.py:162)

  > `if len(f) != 7:`  
  > `raise ParseError(...)`

- [parse.py:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/parse.py:166)

  > `_, txid, thid, epoch, tid, read_count, write_count = f`

**real。** 5-field 入力には専用拒否、generic exact-length 拒否、7変数 unpack の3段がある。単一条件だけの変異では次段に mask される。

operator の実体は未提示なので注入方法については推測だが、登録のままでは単一理由性を確定できない。5-field branchを実際に構築する複合 anchor/operatorとして明記し、その mutated bytes が受理集合を広げたことを確認する必要がある。

**成果物影響:** mask された変異を kill と誤認すると、v1 拒否の検出力を変異 matrix／台帳が偽って記録する。

### 4. 変異 M8 は gate を無効化しても既存テスト入力の挙動が変わらない

- [s4-ruling-plan-v2.md:163](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t816-step4-impl/s4-ruling-plan-v2.md:163)

  > `M8 | ... artifact_commit != PIN を無効化 | 再 pin した校正 artifact の gate`

- [test_s8a_trigger_sweep.py:668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/tests/test_s8a_trigger_sweep.py:668)

  > `_with_freq(monkeypatch, _freq_doc(EFF3))`  
  > `assert W.load_effective_reasons() == EFF3`

- [test_s8a_trigger_sweep.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/tests/test_s8a_trigger_sweep.py:708)

  > `doc["build_admissions"][0]["source"].update(`  
  > `ccbench_commit="wrong-pin")`

**real。** 成功 fixture の artifact commit は常に現行 PIN なので、`artifact_commit != PIN` を fail-open にしても結果は不変。既存負例が壊すのは artifact 本体でなく receipt 内の source であり、outer SHA/receipt 検証に拒否される。artifact と receipt が同じ旧 pin を持つ、内部整合した stale fixture がない。

比較を `==` に反転して正例を落とす変異なら赤になるが、それは gate 無効化による受理集合拡大の kill ではない。

**成果物影響:** M8 は SURVIVED すべき変異を kill と報告するか、校正 pin gate の検出力を証明できないまま変異台帳を閉じる。

## Nit / backlog

### R3 の保存検査には意味があるが、`raw_recomputed` という表現は過大

- [test_silo_ladder_rung1_evidence.py:1008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1008)

  > `def _correctness_passes(...)`

- [test_silo_ladder_rung1_evidence.py:1017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1017)

  > `result["verdict"] == "serializable"`  
  > `and result["certified"] is True`

- [test_silo_ladder_rung1_evidence.py:1484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1484)

  > `"raw_recomputed": True`

**real / nit。** `_correctness_passes` 単独では記録内容の意味的正しさを再証明しない。ただし記録は manifest の byte hash、raw verifier projection、build/command/provenance と結び直されるため、恒真でも無意味でもない。「当時の pass 記録が改変されていない」ことを保証する保存検査としては意味がある。

一方、trace の意味的再計算を退役した後も `raw_recomputed=True` や「all_pass を raw から再導出」と呼ぶのは過大。コメントで「historical recorded verdict preservation」と限界を明記するのが望ましい。

**成果物影響:** certified 集合は変わらないが、歴史レポートが現在の verifier による再計算済みと誤読される。

## Refuted

### 退役の巻き添え

**refuted。** 差分で削除された assert は `assert recomputed == recorded_result` の1本だけだった。ledger/pin の2 assert は historical/current 分離へ置換されている。以下は残存する。

- trace summary: [test_silo_ladder_rung1_evidence.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1060)
- symbol/build: 同 `:1062-1067`
- compile commands/replay: 同 `:1068-1090`
- command receipts/binary hashes: 同 `:1091-1147`
- compile argv/TRACE activation: 同 `:1157-1186`
- manifest/seal: 同 `:135-217`, `:1446-1449`
- commit witness: 同 `:1190-1201`

**成果物影響:** trace の現行 verifier 再検証以外の build／attestation／seal／manifest／commit witness の受理条件は維持される。

### `framing_violations` が consumer で無視される懸念

**refuted。**

- clean/certified: [model.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/model.py:160)
- JSON: [report.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/report.py:67)
- text: [report.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/report.py:112)
- rung1 acceptance: [silo_ladder_rung1.py:1137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/campaign/silo_ladder_rung1.py:1137)
- exact key-set: 同 `:1451-1456`
- critic の汎用 counter 描画: [digest.py:670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/critic/digest.py:670)

**成果物影響:** 非ゼロなら certified は false、JSON/text/WAL由来 critic report に counter と notes が残る。

### 新 gate の到達性と R5-4

**refuted。** v1、負 txid、件数、E欠落・重複はいずれも parser 状態遷移から到達可能で、`framing_violations` は core で `Integrity` に配線される。非直後の重複 E は [parse.py:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/verifier/parse.py:252) の `ParseError` となり、pipeline は [pipeline.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-step4-impl/orchestrator/campaign/pipeline.py:1028) で `trace-parse-error` として reject する。fail-closed として安全である。

**成果物影響:** 非直後 duplicate E は構造化 counterにはならないが COMMIT/certified 集合には入らない。

### テスト弱体化

**refuted。** 全差分に skip/xfail の追加、テスト削除、期待値の緩和はない。FN-2 characterization は `certified=True` から `framing_violations == 2`／`certified=False` へ強化された。`FROZEN_MANIFEST` と pin/hash literal の更新は R1/Q2 の明示的 re-pin であり、runtime から期待値を自己導出する変更ではない。

**成果物影響:** テストが受理集合を広げる変更は確認できない。

### M2〜M7 の単一理由性

**refuted。** M2 は共通 `_record_count_mismatch`、M3 は `_record_missing_end`、M4 は duplicate-end append、M5 は負 txid 構文検査、M6 は `Integrity.clean()`、M7 は `0 0 + E` 正例へそれぞれ帰属可能。M3 は count-mismatch と共存しない `0 0` fixtureを使えば単一理由になる。問題がある登録は上記 M1/M8。

**成果物影響:** M2〜M7 は anchor と期待 node 完全集合を再導出すれば、変異台帳の検出力根拠として使える。

## 総括

- must-fix: **4**
- nit/backlog: **1**
- refuted: **5**

最も危険なのは、`line[0]` による record tag の prefix 受理である。正規 `C` と不正 `End` の組合せが clean/certified まで到達でき、今回の「受理集合を縮小する」変更に実際の fail-open を残している。