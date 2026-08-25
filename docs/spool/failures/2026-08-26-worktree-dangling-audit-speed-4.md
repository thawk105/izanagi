---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: worktree-dangling-audit-speed
seq: 4
---

## 新規

### {{F:hang-mutation-orphan-limit-relearned-by-experiment}}. 既記録の tooling 限界を台帳で引かず実験で学び直し、計算ノードを 2 時間空費した [手順漏れ]

- 事象: 変異 matrix の本走で `hang_risk: true` の変異 (busy-spin 再現) が 2 回とも
  orphan-hold を立てて harness を止めた。孤児 job は毎回 PBS walltime いっぱい
  (実測 3,609 秒) 走り切ってから SIGKILL され、その間 worktree からの dispatch が
  全面停止するため親は待つしかなかった。**2 request (948690 / 948747) で合計約 2 時間**、
  ノードは 48 CPU を占有したまま最大 58.9 GB まで単調にメモリを伸ばしていた。
  親はこの 2 時間を「なぜ止まるのか」の実験に使い、`tools/pegasus/dispatch_compute.py` の
  qdel gate が `QUE`/`HLD` 以外を cancel しない実装であることを読み出して原因と結論した。
- 根本原因: **その結論は D560 が既に、より完全な形で記録していた。** D560 の未閉鎖残件は
  同型の hang 変異 (m04) を 3 回の実 dispatch で観測し、「PBS 強制終了された job は
  正常完了マーカーを残せないため、walltime 値に関わらず毎回 orphan-hold に落ちる」
  構造的非互換だと結論し、**当該変異を matrix から除外**して閉じている。さらに同じ D560 は
  この待ち時間そのものを潰すための逃げ道 `IZANAGI_DISPATCH_WALLTIME_OVERRIDE`
  (`tools/run_tests.py`) を用意した経緯まで書いていた。親は spec を組む前に
  `hang_risk` を機構名として台帳を検索しておらず、既裁定・既知の限界・既存の逃げ道の
  3 つすべてを引かないまま実験に入った。gate の実装から導いた説明は誤りではないが、
  **一次資料は動くコードでなく台帳側にあった。**
- 恒久対応: auto-memory `hang-mutation-cannot-settle-under-dispatch` に固定 —
  `hang_risk: true` の変異は dispatch 経路で清算できないので本走 spec に載せない、
  DW-M06 の「部分集合へ隔離」は spec を分けることを指す、やむを得ず走らせるなら
  `IZANAGI_DISPATCH_WALLTIME_OVERRIDE` で walltime を縮めて孤児の占有を最小化する。
  参照先の正本は D560 の未閉鎖残件。
- 再発検知: 変異 spec に `hang_risk: true` の項が含まれたまま `--runner-mode dispatch` で
  本走を起動したら同型。起動前に spec の `hang_risk` 真値を数えれば機械判定できる。

## 再発

### F185

- **再発: 2026-08-26** — hang 変異用の `hang_timeout_seconds` を 300 秒に置いたが、
  その回の dispatch は queue 待ちだけで 345 秒かかり、**job が走り始める前に timeout が切れて**
  harness が orphan-hold で停止した。同じ夜の同じ harness が直前の 11 変異を 27〜42 秒で
  回しており、往復の中央値から決めた値だった。F185 は「local 実測から決めて dispatch 下限を
  割った」型として記録されているが、**dispatch 実測から決めても混雑で割れる** —
  下限は往復時間ではなく queue 混雑で決まるため、実測の倍数ではなく混雑時の最悪値で取る。
