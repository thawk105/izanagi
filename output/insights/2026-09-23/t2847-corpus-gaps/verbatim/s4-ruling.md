# 段 4 裁定 — [T-2847] 残り (1) (2026-09-23)

## 軽量版の判定 (DW-C00)
- 設計択一: 割れない (設計書 §3・§3.1 で期待と識別点が確定)。正しさ防壁: verifier・gate を変えず test を足すだけ。受理集合: 不変。
- よって段 2・3 と段 6 review 子を省く。段 5 実装子 (Codex author) と、赤が出れば fix 子は省かない。
- (P1) 内部 API で辺集合を読む: 採用。VerifyResult は辺集合を返さないので、verify_trace_dir と同じ compact 構築 (core の compact parse → DSG.from_compact) の adj を読む。あわせて公開結果 (verdict・certified・n_edges・anomalies) も assert する。

## plan v2 (実装子への指示)
- 新規 `orchestrator/tests/test_verifier_corpus_gaps.py` だけを作る。他 file は触らない。
- 合成 silo source (X・P emitter を持つ CMakeLists.txt + transaction.cc) を file 内で temp dir に作り、verify_trace_dir に protocol="silo", ccbench_root=そこ を渡す。test_verifier.py を import しない。
- test 3 本以上 (F03・F06・B06)。期待は brief の値 (手で導いた値) をそのまま literal で書く。verifier の出力を写さない。
- 各 test は temp dir を後始末する。pytest 無しの自走 runner (`_run()`、test_verifier.py と同型) を末尾に持つ。
- 期待と合わなければ期待を変えず、実装子は報告で止める (親が欠陥として記録)。

## 変異の事前登録 (DW-M01 / M08、対象 = orchestrator/verifier/dsg.py、一時変異は DW-O19)
runner の対象 = 新 test file と既存 orchestrator/tests/test_verifier.py (DW-M08 の新旧両走)。期待 node は login 自走 probe で集め、既存 file だけで赤になる変異は新規検出力に数えない。
- M0 (positive, SURVIVED): `_classify` docstring の語「G0/G1c 枝は **非 realizable」を「G0/G1c 枝は **非実現可能」に置換 (comment だけ、drift 核の測定)。
- M1 (negative, 狙い F03): compact 隣接の replay で重複を保つ — `adjacency: Dict[int, Set[int]] = defaultdict(set)` → `adjacency: Dict[int, List[int]] = defaultdict(list)`、`adjacency[source].update(outcome.run_dst[start:end])` → `adjacency[source].extend(outcome.run_dst[start:end])` (累積 2 置換)。§3.1「二重読みで辺を重複して数える」。
- M2 (negative, 狙い F06): packed 読み辺 loop で、同じ取引で次の読みが同じ key なら今の読みを飛ばす (後の読みだけ残す)。`key_id = token_to_key[...]` 行の直後に `if read_index + 1 < columns.txn_read_offsets[row + 1] and token_to_key[columns.read_key_id[read_index + 1]] == key_id: continue` を挿入。§3.1「二重読みの後の方だけを残す」。
- M3 (negative, 狙い B06): `_classify` の `return "G1c"` を `return "G2"` に (§3.1「分類器が常に G2」)。既存 test_classify_branches も落とす見込み = 既存と重なる。
- M4 (negative, 狙い B06、trace からの経路だけ): `_reasons` の wr を RW と誤ラベル — `reasons.append(_edge_reason(WR, k, u_writes[k], None))` → `reasons.append(_edge_reason(RW, k, u_writes[k], None))`。合成辺の単体 test では見えない経路。
- 各変異の単一理由性は probe 後に赤 node と赤理由で確認し、崩れたら登録を外すか再照準して erratum を残す。
