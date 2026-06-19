# -*- coding: utf-8 -*-
"""Izanagi orchestrator (campaign engine) — 探索ループの中枢。

orchestrator を **DB のトランザクション実行エンジンの原理**で設計する
(docs/orchestrator-design.md)。Phase 1 タスク6 ではその骨格を実体化する:

STAGE1 (純ロジック・machine 非依存):
  model    — Genome / CampaignConfig / WalRecord / EvalState
  genome   — 最適化フラグ超立方体 + 制約付き列挙器 (silo を実体化)
  ident    — campaign 同一性 (内容ハッシュ, D13)
  layout   — 出力レイアウト二軸 (campaigns / env, D13)
  wal      — WAL 追記 + リプレイ/リカバリ + atomicity (D, A)
  lock     — ベンチ排他ロック (I)

STAGE2 (machine-touching, Phase 1 タスク6 後半):
  buildcache — genome → バイナリ (内容キーのビルドキャッシュ)
  pipeline   — 評価パイプライン (build→verify→[bench]→commit) の状態機械
  cli/loop   — campaign を genome 列に対して回す + リカバリ

設計対応は各モジュールの docstring と orchestrator-design.md を参照。
"""
