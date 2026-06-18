# orchestrator — 探索ループの中枢 (Python)

Phase 進行に伴って実装する。Phase 1 では calibrate と verify の呼び出しから。

コンポーネント (roadmap §9 参照):
- verifier/     — mini trace verifier (Phase 1, 実装済)。trace → DSG → G2 cycle 検出
- calibrator/   — レコード数自動決定 + noise floor (Phase 1)。純ロジック (perfparse/
                  benchparse/analyze/report) は実装済・モックテスト済。実機ドライバ
                  (runner/tsc/sweep) はタスク4b で追加
- search.py     — パラメータ探索 (Phase 2, 予定)
- profile.py    — perf/FlameGraph 呼び出しと解析 (Phase 2, 予定)

テスト: `python orchestrator/tests/test_verifier.py` / `test_calibrator.py`
(pytest でも素の python でも走る)。

