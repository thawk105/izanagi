---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1179-publish-seam
seq: 1
title: floor の publish 適格性を mode 一語から実引数の seam 集合へ束縛した — 敵対レビューが「証跡台帳は恒真に近い」と「権威 artifact が先に可視になる」を出した (コード + テスト、branch worktree-dev-wave-t1179-publish-seam)
---

## 本文

- 攻撃面は親が実測で確定させた。`eligible_for_refreeze` が `mode == "official"` 一語から
  導かれており、module docstring 自身が「receipt chain ではなく mode 由来」と既知限界を
  自認していた。下流 (`s8b_ratified_freeze` / `s8b_holdout_freeze`) はこの 1 bit しか検査しない。
  既存の seam 拒否検査は public wrapper にしか無く、private core には一切無かった。
  既存テストの 3 箇所が「official + 注入 measure」で実際に真を観測していた。
- 段 2 プランの中核だった「gateway 観測証跡の in-process 台帳」を親が段 4 で**不採用**にした。
  段 3 の 2 レンズが独立に、外部 measure の実行は seam 集合だけで必ず偽になるので純増検出力が
  ゼロであること、既定 measure では allowance が subprocess より前に消費され rep 失敗でも
  残 rep を回すため事実上つねに真になることを指摘した。恒真に近い保証だったため落とした。
  落としたことで、wrapper の戻り値変更が既存 2 テストを即壊す問題と、
  台帳値の変異が seam 判定に先取りされて殺せない問題と、
  pre-probe skip session の過剰拒否が同時に消えた。判断は {{D:floor-publish-eligibility-from-seams}}。
- 段 3 のレンズが `_validate_mode` の `isinstance` 止まりを突いた。状態を持つ `str` 派生が
  集合検査と public wrapper を通しつつ official の無条件拒否だけを外せる。
  **monkeypatch 不要**で、親 brief の「production から今日到達不能」という前提を崩す指摘だったので
  採用して exact type 検査へ硬化した。
- 段 6 の敵対レビューが land 前の must-fix を出した。publish 順が `result.json` 先だったため、
  適格性を fresh・seam ゼロへ束縛した結果として、二つの publish の間で停止すると
  真の `result.json` だけが取り残され、resume は偽を再構成して bytes 不一致で停止するので
  撤回できない。下流は `result.md` を閉包に含めないのでそのまま受理できた。
  権威 artifact を最後に publish する順序へ変えた。判断は {{D:floor-authority-artifact-published-last}}。
- 同レビューが既定 callable の identity 判定の迂回も出した。module 属性 `time.sleep` を
  差し替えてから同じ実体を `sleep_fn=` へ渡すと非既定と判定されない。親の静的 probe でも再現した。
  import 時の private sentinel で塞いだが、これは限界を縮めただけである。
- **本 wave が閉じたのは supported API 経由の publish 経路である。** 同一 interpreter 内の
  module 属性差し替えは任意コード実行と同値であり、耐性は主張しない。
  生成後の artifact を 1 bit 書き換える経路も塞いでいない (所有は [T-1178])。
  official は core / CLI / Pegasus 投入 script の三重で拒否されたままで、
  本 gate が効くのは official 解禁以後である。判断は {{D:in-process-argument-gate-scope}}。
- もう 1 本のレンズはテストの検出力を攻撃し、署名 meta-test が名前集合しか比べておらず
  「全件分類」を強制していないこと、rep 失敗許容の正例が rep 失敗を作っていないこと、
  「assembly 単体は常に偽」を pilot でしか検査していないこと、
  `_validate_mode` の変異が例外メッセージ経由で落ちるため単一理由でないことを出した。すべて採用した。
- **子は 3 回とも pytest を 1 度も起動できなかった** (段 5 実装子・段 6 fix 子・spec 子。
  `tools/run_tests.py` が dispatch preflight `qstat -Q rc=1` または bounded local の
  memory scope attest 失敗で停止)。実測はすべて親が行った。
  親側も 1 度 login ノードのメモリ逼迫 (使用量 13.7 GiB / 実効天井 15 GiB、回収不能 8.6 GiB) で
  `rc=16` になり、`--force-dispatch` で計算ノードへ回して取り直した。
- `tools/dev_wave_wait.py producer` の待ち手が本 job で複数回**空振り rc=0** を返した
  (producer 生存・`.done` 不在なのに完了)。以後は `.done` / `.rc` の実体照合に切り替えた。

## 次の一手差分

### 更新

- [T-1179] **P1・部分完了**: private core の外部 measure から publishable artifact を作る
  経路は、実引数由来の seam 集合 + fresh + canonical official へ束縛して閉じた。
  権威 artifact の publish 順も逆転させた。**残るのは 2 件のユーザー裁定**である。
  (1) official 解禁の信頼根を clean process 実行 + code identity 封印に置くか、
  下流が再検証できる durable receipt ([T-1178]) に置くか。同一 interpreter 内の
  module 属性差し替えは argument 境界では原理的に閉じられない。
  (2) resume を publish 不適格にした結果、crash した long-running official campaign は
  resume でも publish できず、一回性 claim と admission ledger のため fresh retry も拒否される。
  crash 時の freeze / admission 再生成を必須と裁定して `docs/phase3-8b-restart-runbook.md` を
  直すか、証跡の journal 永続化を別 scope で立てるか。
  base: da9ef9cd32a78998874338e526b1f7fafd3ffa33224946789dc4b1f24bfca0f9
