# -*- coding: utf-8 -*-
"""Izanagi calibrator — 実験のレコード数・noise floor を測定の妥当性を保って決める。

純ロジック (machine 非依存・モックでテスト可能):
  perfparse  — perf stat 出力 → PerfCounters
  benchparse — ccbench stdout → メトリクス辞書
  analyze    — find_saturation / scale_sensitivity / noise_floor
  report     — CalibrationResult → text / dict
  model      — データモデル

実機ドライバ (Linux 実機で perf を当てる。タスク4b):
  tsc        — TSC clocks_per_us 実測
  runner     — perf + numactl で 1 run → ScalePoint
  sweep      — 倍々スイープを回して CalibrationResult を組む

設計背景: docs/roadmap.md §4 / §3.6、calibrator.md。
"""
