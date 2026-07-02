# orchestrator — 探索ループの中枢 (Python)

Phase 進行に伴って実装してきた。現構成 (roadmap §9 参照):

- verifier/     — mini trace verifier (Phase 1)。trace → DSG → G2 cycle 検出。
                  integrity 不良は certified せず indeterminate に倒す
- calibrator/   — レコード数自動決定 + noise floor (Phase 1)。純ロジック
                  (perfparse/benchparse/analyze/report) + 実機ドライバ (runner/tsc/sweep)、
                  測定安定性 stability (P2-1/A2)
- campaign/     — Phase 2 の中枢。WAL/ACID (wal, loop, pipeline)、識別 (ident,
                  source_digest = D23)、ビルド (buildcache)、遺伝子空間 (genome, model)、
                  実験ドライバ (p2_2, backoff_*, between_run_floor, p2_5, guided)、
                  リプレイ (replay)、レポート射影器 (*_report, search_baselines)
- critic/       — critic への WAL digest 供給 (digest, online_digest)
- reports/      — 入力非依存の材料レポート (calibration_report, plot)

エントリポイント: `calibrate.py` / `verify.py` (ルート直下)。

テスト: `python3 orchestrator/tests/test_verifier.py` 等 (pytest でも素の python3 でも走る。
方針は `tests/README.md`)。
