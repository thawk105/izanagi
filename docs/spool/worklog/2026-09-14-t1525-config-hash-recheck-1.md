---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: t1525-config-hash-recheck
seq: 1
title: [T-1525] masstree config.h の hash 不一致は現物で再現せず、確認だけで閉じた
---

## 本文

- `/next-tasks` が [T-1525] の修正を提案したのに対し、ユーザーが「sha256 不一致の何がまずいのか。
  VLDB/SIGMOD でそういう問題はあまり見かけない。機構が厳しすぎるのではないか」と問うた。
  提案の前提を現物で測り直し、**提案を取り下げた。**
- 実測: 共有 cache の `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree/config.h` の sha256 は
  `e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a` であり、
  `tools/pegasus/policies/floor_masstree_payload_v1.json` の `config_sha256` と**完全に一致する**。
  2026-08-23 の起票が報告した `88d75021...` は現物に無い。当時の不一致がなぜ生じ、いつ解消したかは
  特定していない (現物で再現しないため)。
- 起票が疑った「不一致のまま検証を通っている = 検査が発火していない」は、前提が成立していない。
  比較は `s8b_floor_campaign._bind_expected_floor_masstree_payload` の fail-closed な preflight であり、
  postflight 側の負例テストは `orchestrator/tests/test_s8b_floor_campaign.py` に実在して
  `floor-dependency-postflight-config-expected-mismatch` を名指しで発火させている。
  preflight 側の detail code `floor-dependency-config-expected-mismatch` を名指しで発火させる
  テストは見つけていない。赤は出ていないので本記録では扱わない。
- 設計上の論点は記録だけ残し、新規 item は起こさない。`config.h` は autoconf が生成する派生物なので、
  bytes は測定の意味と 1 対 1 ではない。ホストや検出結果が変われば測定に影響が無くても bytes は動き、
  逆に bytes が同じでもコンパイラ版や最適化フラグが変われば測定値は動く。同じ policy が持つ
  `archive_nondebug_sha256` (ビルド済み archive からデバッグ区画を落とした射影の hash) の方が
  「link される機械語が変わったか」に近い。見直すなら床値 protocol を触る wave と同じ変更単位で
  1 回だけ扱うのが安く、単独 wave を立てる価値は無いと判断した。
- 本記録は確認の結果である。実装差分はゼロで、関門の緩和も撤去もしていない。

## 次の一手差分

### 完了

- [T-1525] 共有 cache の config.h と floor payload policy の `config_sha256` が現物で一致することを
  実測し、起票時の不一致が再現しないことを確認した。実装差分ゼロ。
  remaining: none
  base: 0781aa86f311ff447d84bf1fdd249339f9b7c43f9ec14f26968a4a6788d9e836
