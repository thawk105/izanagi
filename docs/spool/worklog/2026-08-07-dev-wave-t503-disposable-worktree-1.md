---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t503-disposable-worktree
seq: 1
title: [T-503] 変異本走を使い捨て専有 worktree へ隔離する第一 slice を実装した — 共有木を触らないことだけを主張し §9.1 は 0/6 のまま (コード + docs、受入 7077 passed / 20 skipped、変異 14 件記録 (KILLED 9 / MISMATCH 5、全件で登録 node が赤)、branch worktree-dev-wave-t503-disposable-worktree)
---

## 本文

- **ユーザー裁定 V-1 (b) に従い第一 slice を実装した。** V-2 は V-1 に従属。**V-3 / V-4 / V-5 は
  arm・`clean`・in-place 復元が存在しないため発火面が無く未実装**であり、放棄ではなく後続 slice へ
  持ち越す。V-6 も journal を作らないため本 slice に発火面が無い。設計 §9.1 の必須 6 点の充足は
  **0/6** で、`T-503 complete`・D130 条件 3 `closed`・[T-486] `closed` とは書けない。
  L-B は `UNKNOWN` のまま。正本 = `output/insights/2026-08-07_t503-disposable-worktree/README.md`。
- **段 3 の両レンズが段 5 進行 NO-GO を返したが、親は「縮小して GO」と裁定した** ({{D:disposable-mutation-worktree}})。
  残る blocker (機械 admission、legacy drain、実行場所分類) は harness 改変か人間手番を要するため
  scope 外とし、裁定パッケージ V-7 / V-8 / V-9 として返す。
- **段 3 の A-2「64 テストからの一般化は破れる」は実測で refuted。** 使い捨て木での受入全走が
  6806 passed / 20 skipped で、同時点の共有木の値と一致した。
- **段 1 の probe に `pipefail` が無く、報告した rc が `tail` の rc だった** (レンズ A-8 / B-13 が指摘)。
  pipe を外して測り直し、worktree add / submodule init / 全走 / `--plan-only` すべて rc=0 を確認した。
- **段 6 レビューの must-fix 18 件は closed 20 / backlog 2 / regressed 0。** 主な型は
  **テストが helper を直接呼ぶだけで本番の結線を検査せず、事前登録した変異を殺せない**ことで、
  MW-05 / 09 / 11 / 12 / 14 が該当した。fix 後は `main` を通す形へ作り直した。
- **変異 matrix は 14 件記録 / KILLED 9 / MISMATCH 5 / SURVIVED 0。全 14 件で事前登録した
  test node が赤**になり帰属は成立している。MISMATCH は登録 node に加えて他 node も赤くなったもので、
  **親の事前登録が影響範囲を過小に書いていた**。`DW-M02` に従い結果は書き換えず erratum とした。
- **変異 matrix の本走が 2 度止まった。親は当初これを計算機の queue 混雑と誤診断し、
  待ち行列を見て投げ直す運用で凌いだが、一次資料を読み直して F148 / F149 の再発と判明した。**
  停止は rc=16・stdout 0 byte で、変異適用中の tree が必ず dirty なため local 試行から
  dispatch への fallback が拒否され、receipt 行が出ないまま harness が F71 どおり
  fail-closed 停止 (`PARSE_ERROR`) したものである。**混雑は相関であって原因ではない** —
  待ち 142 件のままでも完走した走行がある。初回台帳は erratum として insight へ凍結した。
- **`DW-M05` は変更しなかった。** `docs/dev-wave/**` の hard ceiling に対し残りが 13 bytes で、
  追記すると安全義務を削る圧力がかかる。wrapper は必須ではないので運用規約は設計 §9.3 に置いた。
  必須化する slice で `DW-M05` の圧縮と同時に行う。

## 次の一手差分

### 更新

- [T-503] **P2・第一 slice 実装済み (2026-08-07) → 残りは V-7 / V-8 / V-9**:
  使い捨て専有 worktree (`tools/mutation_worktree.py`) だけを実装した。設計 §9.1 の充足は 0/6、
  V-3 / V-4 / V-5 は発火面が無く未実装、L-B は `UNKNOWN`、旧 direct 経路は機械的に閉じていない。
  次は {{T:mutation-worktree-activation-package}} の裁定。正本 =
  `output/insights/2026-08-07_t503-disposable-worktree/README.md`、設計 §9.3
  base: f5cf34021fb83b8047848f050eb758d15f8cee83e6e8217429d6608179cd3ed7

### 新規

- {{T:mutation-worktree-activation-package}} **P2・ユーザー裁定待ち**: 旧 direct 経路の閉じ方 (V-7)。
  (a) harness に isolation admission を足し (U-10 解除)、legacy drain receipt と consumer 拒否まで
  含む activation package を独立 wave で作る / (b) prose-only の既定手段のままにする /
  (c) shadow prototype と位置づけ活性化を L-B 実機受入まで凍結する。親の推奨は (a)。
  **本 slice は (c) の位置づけで land した**
- {{T:mutation-worktree-run-location-class}} **P2・ユーザー手番**: `tools/mutation_worktree.py` の
  実行場所分類 (V-8)。`tools/README.md` の規約により未計測は `dispatch-required` 扱いで、
  分類の実測は AI ではなくユーザー端末の手番である。測るまでは計算ノード確保で運用する
- {{T:mutation-worktree-stale-gc}} **P3・裁定待ち**: 未完了 container の自動回収 (V-9)。
  現状は手動削除か `--resume` のみ。`DW-G04` により実残骸 path を観測してから設計する
- {{T:mutation-harness-force-dispatch}} **P2・新規**: `tools/mutation_harness.py` が
  `run_tests.py` へ D209 決定 10 の `--force-dispatch` を渡すようにする。変異適用中の tree は
  必ず dirty なので、local 試行からの fallback が拒否されて rc=16・stdout 0 byte で止まる
  (F148 / F149 の再発、{{F:stage1-rc-read-through-pipe}} とは別件)。本 wave は投げ直しで凌いだ
