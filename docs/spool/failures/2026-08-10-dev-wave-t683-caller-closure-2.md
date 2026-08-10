---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t683-caller-closure
seq: 2
---

## 新規

### {{F:acceptance-lease-overtaken-while-queued}}. 受入 lease の待ち行列で main に追い越され続け、取得しても投入できない [手順漏れ]

- 事象: `tools/wave_land_window.py claim` が `acquired` を返した時点で local main が既に
  7 commit (1 例目)、22 commit (2 例目) 先行しており、runbook §7.3 の待ち手契約
  「`git rev-list --count HEAD..main` が 0 でなければ lease を返して親へ戻す」に従って
  2 回とも lease を返した。受入全走を 1 度も投入できないまま約 2 時間を消費した。
  同一 wave (dev-wave-t683-caller-closure) の連続する 2 回で、待ち中の holder は別 wave。
- 根本原因: §7.3 は「取り込みは投入前に**親が** merge commit として済ませ、待ち手側は検査に
  留める」ことを前提にするが、この前提は**待ち時間が 0 に近いときしか成立しない**。
  holder の受入が 500〜1300 秒かかり待ち行列が飽和した状態では、待ち始めてから取得するまでに
  他 wave が land するため、取得時点で必ず追い越されている。親は待ち中に取り込めない
  (待ち手が走っている間に tree を触ると受入対象が変わる) ので、契約どおりに動くほど空振りする。
  待ち周期を 120 → 30 → 10 秒へ詰めても、追い越しの原因は周期ではなく待ち行列長なので消えない。
- 恒久対応: 待ち手スクリプトが `acquired` の直後に**自分で merge commit を作る**
  (`--ff-only` は使わない。wave branch が自前 commit を持つと fast-forward できないため)。
  競合したら `git merge --abort` して lease を返し、親へ戻す。merge 後に
  `HEAD..main == 0` を再検査してから投入する。3 回目はこの形で通り、受入全走は
  7927 passed / 20 skipped / 495.29 秒で完了した。実体 =
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t683-caller-closure/run_acceptance.sh` の
  fail-closed 分岐 (rc=90 未取得 / 92 競合 / 93 merge 後も先行)。
  runbook §7.3 の待ち手契約自体の改訂は本 wave の scope 外であり、裁定へ返す。
- 再発検知: 待ち手 log (`lease.log`) に `acquired` があるのに `acceptance-status.txt` が
  `behind-main:*` になる組み合わせ。この組が出たら待ち手が取り込みを行っていない。
