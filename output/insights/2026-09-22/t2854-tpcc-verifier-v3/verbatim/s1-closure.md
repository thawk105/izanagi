# 段 1 pin 閉包検索の結論 (Explore 子 sonnet の最終報告の要約、2026-09-22 09:1x JST、main 8fd2a2f5c = verifier は eef04f5a7 と同一)

対象: orchestrator/verifier/{parse,dsg,model,core}.py (sha256 a588bc30… / e5989092… / 59136847… / 4d70c244…)

| 分類 | path:line | 理由 |
|---|---|---|
| exact pin (赤になる) | orchestrator/tests/test_verifier.py:2657-2663 (test_serial_parent_optimizations_match_workers_and_pin_witness_order) | `str(reason)` で EdgeReason の dataclass 自動 repr を "EdgeReason(etype='wr', key='20', u_ver=(2, 18), v_ver=None)" と exact 比較。field を足すと既定値付きでも repr が変わり赤 |
| exact pin (設計次第) | test_verifier.py:1856,1862,1867,1879,1892,1912,1924,1937,1957,1970,1990,2002 | report dict の "key": "<hex>" を golden 比較。EdgeReason.key を生 hex 以外にすると赤 |
| 出力 JSON golden | test_verifier.py:1404-1452 | g1_serial の result_to_dict を JSON bytes で比較。stats / integrity に key を足すと赤 |
| source closure (実行時 hash) | campaign_lock.py:49-62 ほか、test_t671_source_binding.py、test_artifact_admission.py、test_t126_pegasus_tools.py、test_campaign_lock_codec.py | path 一覧。中身の編集では赤にならない。path の増減・順序は赤 |
| 無関係 | critic/digest.py (Read/Write/Txn/EdgeReason を import しない)、commit_receipt.py (固定値 pin なし)、test_frozen_artifacts.py | — |

- 4 file の sha256 (先頭 16 桁) の hit は output/insights の歴史記録と b10 の historical campaign.lock fixture だけ。固定比較する test は 0 件。
- dataclasses.asdict / fields() を Read/Write/Txn/EdgeReason に使う箇所 0 件 (report.py は手動列挙)。
- EdgeReason( の出現: test_verifier.py 21 箇所 (golden は上記 4 行だけ)、test_campaign.py 2 箇所 (keyword 引数)。
- 未検査: Read / Write / Txn / Anomaly / CycleEdge の repr・eq を固定する test の有無 (段 2 plan が実測する)。
