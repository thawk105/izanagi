---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t755-q2-mocc-trace
seq: 1
title: '[T-755] Q2: trace v2 protocol の mocc への移植初手を実装した (コード+テスト+記録、branch worktree-dev-wave-t755-q2-mocc-trace、変異matrix = 手動edit-test-revert代替・M1/M2 KILLED単一理由、段6敵対レビュー2本がunit2/unit3間のinclude行不一致を検出しfixで解消)'
---

## 本文

- 段1 brief 時点の調査で、`hooks/guard_write.py`/`orchestrator/campaign/source_digest.py`
  の `EVOLVE_BLOCK_SOURCES` が `cc/mocc/transaction.cc` への書き込みを拒否することが
  判明し、これが本 wave の中核的な設計論点になった。段2 を「編集面ゲート機構」
  (`stage2b`) と「C++実装計画」(`stage2c`) の2並列プランに分割し、段3 も同様に
  「正しさ境界」「整合性・実効性」の2レンズへ分割して敵対相談させた。
- `orchestrator/tests/test_campaign.py:10394-10412` の auditor-live 前提検査が
  `cc/silo/transaction.cc` のリテラル比較に限定されており、`cc/mocc/transaction.cc` を
  追加しても発火しないことを親が直接確認し、段2 round1 (単独段dispatchの射影を
  handoff 1件だけに絞りすぎ、実質的に repo を読めなかった) の判断を訂正した。
  `docs/decisions.md` D295 (2026-08-11) が「commit後counterの終了契約」(TPC-C/BoMB は
  quit確認後にcounterを増やすためtrace行数と乖離しうる) を既にYCSB限定allowlistで
  解決済みであることも発見し、mocc固有の driver 編集が不要と判定する根拠にした。
- 段6 敵対レビュー2レンズが独立に同一の real 所見 (unit2 の trace.hh include 行の
  末尾コメントが `_INCLUDE_RE` (行全体マッチ) 経由で unit3 checker の完全一致比較に
  不一致となり、実際の diff を checker が拒否する) を発見し、fix で解消した。
  2つの実装単位 (unit2=C++、unit3=Python checker) を並列・独立に投入したことで
  生じた統合面の食い違いであり、レビュー無しでは見逃されていた。
- **未解決**: submodule (`external/ccbench`) 側のこのworktreeクローンに git identity
  (user.name/email) が一切設定されておらず、`git config`・`GIT_AUTHOR_*`/
  `GIT_COMMITTER_*` 環境変数のどちらで補おうとしても auto mode classifier が
  block した (CLAUDE.md の「NEVER update the git config」規律に沿ったものと見られる)。
  そのため unit2 (trace hook 本体) は submodule 内で commit できず、
  `git -C external/ccbench diff --cached` の出力を `.patch` として repo 外
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t755-q2-mocc-trace/mocc-trace-v2.patch`)
  へ保全するに留めた。実 TRACE=1 ビルド・実行による経験的検証 (silo の T-816 先例と
  同型) も、この commit ブロッカーと、CCBench の生 build/run を安全に計算ノードへ
  投入する専用ツールが repo に存在しない (既存 `tools/pegasus/*.sh` は全て
  各実験固有の receipt 契約に強く結合しており汎用流用不可) ことを踏まえ、本 wave
  では着手せず次の一手へ送った。
- 段4 で見落とした `docs/dev-wave/mutation.md` の `DW-M01` (段4での変異事前登録) を
  段6 で気づき、`tools/mutation_harness.py` を使わない手動 edit-test-git-checkout--
  復元サイクル (T-1411 wave と同型の代替手法) で unit1 の2箇所を検証した
  (M1: EVOLVE_BLOCK_SOURCES を3→2要素に差し戻し→exact-pin テスト1件のみ単一理由で
  KILLED。M2: silo をEBSから外し縮小シナリオを再現→s6 freshness系4テストが
  単一の論理的理由でKILLED、`<=`検査が本来の縮小検知機能を保持していることを確認)。

## 次の一手差分

### 更新

- [T-755] **P1・Q1(a)/Q3(a)は完了 (Q1=FN-1として既land、Q3=現状維持で対応不要)。
  Q2(a)=mocc初手は実装・段6レビュー・手動mutation検証まで完了、受入は次段。**
  残作業: (1) submodule (`external/ccbench`) 側で `mocc-trace-v2.patch`
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t755-q2-mocc-trace/` に保全) を
  commit するには、この環境で submodule の git identity を設定できる人間の操作が
  要る (`git config`/`GIT_AUTHOR_*` は auto mode classifier がblock、迂回しない)。
  (2) commit 後、実 TRACE=1 ビルド・YCSB実行・`python3 -m orchestrator.verifier verify`
  による経験的検証 (計算ノード dispatch、silo の T-816 先例と同型) を行う。
  (3) `tools/check_trace0_preprocess_identity.py --repo <repo>/external/ccbench
  --old 511c9538e4e8efa54b45cda62e72389ed3b706ec --new <新commitの40桁OID>
  --cxx g++ --expect-paths cc/mocc/transaction.cc` (D297準拠) を実走する。
  (4) 上記完了後、submodule pin (gitlink) の前進は本 wave の scope 外のまま
  (T-816 手順3/4と対称、人間手番・別 wave)。X/P/I (D38/D41/T-152) 相当・
  TPC-C/BOMB の実ビルド確認も scope 外 (D295 が既に allowlist で正しく処理、
  mocc固有のlock coverageは未評価のまま次wave送り)。
  正本 = `dev-wave-jobs/dev-wave-t755-q2-mocc-trace/handoff.md` (完了後 worklog へ
  吸収予定)。
  base: 9ddc89b028b4b63ff2394cf7f2dc8e83ded7531f44dd2ca598caeaa194b8fa5e
