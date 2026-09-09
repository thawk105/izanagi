---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2419-meaning-decl
seq: 1
title: [T-2419] 非負 BACKOFF_FIXED の意味を production 経路で確立できるようにした — 判定器から符号変換を外し driver が物理 µs を宣言する (コード + テスト + insight、branch worktree-dev-wave-t2419-meaning-decl、変異 5/5 KILLED・期待 node 完全一致)
---

## 本文

- 依頼は「非負 `BACKOFF_FIXED` に production の意味宣言を渡す」で、当初の見立ては
  生値を静的 codec で逆算して期待値にする案だった。**段 3 の 2 レンズが独立に同じ blocker へ
  収束してこれを倒した** — 逆算では driver が何を要求したかを証明できず、literal-µs driver の
  格子へ「物理 3000 µs のつもりで 3000」を足すと宣言も観測も 1000.0 になって素通りする。
  段 4 は所見を採り、driver に物理 µs を渡させる設計へ変えた。設計判断は
  {{D:backoff-meaning-intent-from-driver}}。
- 設計変更で実装面は当初案より**小さくなった**。wire domain の一律拒否 (新しい拒否面) と
  codec の module 間移動が両方不要になり、循環 import の論点も消えた。
- 段 6 レビューは blocker 0・実装への must-fix 0。must-fix 1 件は**親の変異登録の不備**で、
  M1 と M5 の期待 kill 集合が重なっていた。probe 走 (全件 SURVIVED 登録) で実測 node を集め、
  M5 を別位置へ再照準してから本登録した。nit 2 件 (負例が複数 red 理由を許す、wrapper test が
  新 kwarg を pin していない) は fix 子が閉じた。
- 段 1 brief の誤りを 1 件訂正した。「凍結記録の現行 file 一致を要求する consumer は無い」は誤りで、
  `s1_known_axes_freeze.verify_document()` が live で再 hash して照合する。ただし記録値は
  本 wave の前から現行と乖離しており (generator hash の乖離が手前で先に止まる)、
  本 wave が作った赤ではない。凍結は再発行していない。
- 実測環境の infra 事象: dispatch の queue-wait-timeout で rc=16 が 2 回。D612 の
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` /
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600` で解消した。中断した走行が orphan hold を
  残したので、qstat での不在と作業木 diff の sha256 一致を確認してから解除した。
  変異 spec の `timeout_seconds` は待機契約 (3600 + 600) 以上でないと harness が fail-closed する。
- 変異走行中に親が insight を書いて作業木を汚し、harness が rc=2 で中断した (親の操作ミス)。
  `--resume` と新しい attempt 対で残り 4 変異だけを走らせて回復した。
- エージェント工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1)。すべて exit 0、
  `tools/check_codex_output.py` rc=0。

## 次の一手差分

### 完了

- [T-2419] 非負 `BACKOFF_FIXED` に production の意味宣言を渡した。判定器は符号を変換せず、
  driver が要求した物理 µs を宣言する。生値 1000 を「1000 µs のつもり」で渡すと
  宣言 1000.0 対 観測 0.0 で red になり、build と measurement の前に拒否される。
  焦点走 470 passed / 0 failed (12 file)、変異 5/5 KILLED・期待 node 完全一致。
  remaining: none
  base: 1ae91b7f8322886f01c088c8a2bcdc61978885cf4d5ee3f963c6bf1067ee1000

### 新規

- {{T:screening-meaning-declaration}} **P2・新規**: generic screening 経路にも意味宣言を入れるか
  裁定する。`orchestrator/campaign/screening_driver.py` は今も宣言を常に `None` にしており、
  生値 1000 を `unestablished` のまま admit する。ただし b10 shape driver の乱択帯
  (生値 1002〜1100) は正当な符号なので、static scalar と randomized shape を別の宣言型または
  別 helper へ分ける設計が要る。`s1_direct_comparison.py` と `paper_story_a2_certification.py` が
  正値を常に `float(raw)` と宣言する独自経路を持つことも同時に見る — 現行値は 999 以下なので
  正しいが、符号化上側へ広げると正しい生値 3000 まで誤って red にする。
- {{T:t2418-meaning-witness-status}} **P3・新規**: `orchestrator/campaign/backoff_extended_sweep.py`
  の固定文字列 `unestablished_for_positive_backoff_fixed_as_in_existing_sweep` は、
  本 wave 以後に同 driver を再走すると live の実態と食い違う。既存 artifact は不変でよいが、
  新規 run の metadata としては偽になる。直すには campaign identity と report schema の版上げが
  要り、T-2418 の事前登録に触れる。
- {{T:freeze-source-hash-role}} **P3・新規**: `output/s1-freeze/known_axes_freeze.json` の
  source sha を「歴史的出所」として保持するのか「live source 一致 gate」として使い続けるのかを
  裁定する。前者なら live verifier から当該比較を外す版上げ、後者なら明示的な再凍結と
  trust root 更新が要る。現状は generator hash の乖離が手前で止めており、
  source 側の乖離は表に出ていない。
