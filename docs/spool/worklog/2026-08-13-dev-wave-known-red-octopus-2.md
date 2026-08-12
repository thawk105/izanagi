---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-known-red-octopus
seq: 2
title: 非帰属 checker を実環境で 3 回踏み抜き、DW-O18 を実態へ是正した (コード + docs、branch worktree-dev-wave-known-red-octopus-v2)
---

## 本文

同 wave の追補。**`tools/check_acceptance_reds.py` を実 repo の受入 log へ当てたところ、
静的レビューが見つけられなかった実環境の欠陥を 3 つ連続で踏んだ。** 順に直したが 3 つ目が残った。

1. **probe worktree の submodule 初期化が必ず失敗する。** 新しい worktree には submodule の
   作業コピーが無く、`.gitmodules` の https URL から clone しようとして
   `GIT_ALLOW_PROTOCOL=file` に弾かれる。修正は「参照側の初期化状態を写す」— index の
   mode 160000 を列挙し、`<git-common-dir>/modules/<path>` が存在する submodule だけを
   その絶対 path を URL にして個別初期化する。**入れ子の `third_party/shirakami` は main 側でも
   未初期化**であることを実測し、`--recursive` を外した。
2. **receipt の `submodules` が空になる。** 参照側未初期化の記録が実際には載っていなかった。
   子自身が書いたテストが検出した (production を直し、テストは 1 文字も変えていない)。
3. **login ノードで probe が必ず rc=16 になる。** `tools/run_tests.py` を素で起動すると
   dispatch infrastructure failure になる。`--force-dispatch` を collect-only と再走の両方へ入れた。
4. **未解決**: collect 出力と log の nodeid が exact 一致せず
   `logged pytest nodeid has no exact collected selector` で rc=2 になる。

**この経験から `DW-O18` を是正した。** 当初は「受入赤は checker で判定し rc=0 だけを非帰属とする」
と書いたが、**実運用で成立しない tool を必須にすると全 wave が止まる**。従来の
「差分が到達しえない赤は単独再走で実測する」を正本へ戻し、checker は「その機械化で rc=1 なら停止、
rc=2 は判定不能で非帰属の根拠にしない」と位置づけた。規律 5 (段階導入・盛らない) と
`DW-G04` (発火条件を満たす実 artifact を書けるときだけ実装する) に従う。

**静的な敵対レビューは実環境の欠陥を 1 件も出さなかった。** 段 6 レンズ B は blocker 6 件を
出したが、いずれも「入力の作り方」「rc 経路」の論理欠陥であり、submodule・dispatch・collect の
実環境依存はすべて**親が実際に走らせて初めて出た**。gate を新設する wave では、静的レビューの
所見ゼロ/多寡にかかわらず**親が実データで 1 回通す**まで完成と数えない。

受入全走は 2 回とも**赤 1 件だけ**で、いずれも `test_codex_worker_launch.py` の負荷フレーク
(F57 系、単独再走で緑を実測)。1 回目 10,391 passed / 0 failed、2 回目 10,411 passed / 1 failed。

工数は Codex 追加 3 本 (fix-c/d/e、`gpt-5.6-sol`・reasoning=high)。

## 次の一手差分

### 新規

- {{T:acceptance-red-checker-selector-match}} **P1・新規**: `check_acceptance_reds.py` が
  collect 出力と log の nodeid を exact 一致させられず rc=2 で止まる
  (`logged pytest nodeid has no exact collected selector`)。dispatch 経由の collect 出力の
  行前置・xdist group suffix の扱いが疑わしい。**この 1 点で tool は実運用に到達していない。**
- {{T:gate-waves-need-live-dogfood}} **P2・新規**: gate を新設する wave の完了条件に
  「親が実データで 1 回通す」を入れるかを裁定する。本 wave では静的レビュー 2 本が
  実環境欠陥を 1 件も出さず、親の実走で 3 件出た。
