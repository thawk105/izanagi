---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-04
wave: dev-wave-f241-perf-attribution
seq: 2
---

## 再発

### F1

- **再発: 2026-09-04** — F241 (2026-08-12) が、観測 (`perf stat` の rc=2) から**推論した**
  「計算ノードに perf が無い」を根本原因として記録し、「環境側 (管理者手番) に linux-tools を
  入れてもらう以外に道はない」まで一般化した。一次資料を 2 つ確認していない —
  `/usr/bin/perf` の実物 (完全一致する版が無ければ他版へ fallback せず exit 2 する**振り分け役**)
  と、**同じ台帳の F89** (9 日前の 2026-08-03 に bnode005 / bnode009 で候補実体が rc=0 で動くことを
  実測済み) である。`docs/pegasus-runbook.md` の環境事実も同じ機構を既に書いていた。
  転写対象が日付・機構の実在状態・推測の確度から、**観測した非 0 rc の帰属先**へ広がった顕在化で
  ある。振り分け役の rc は「その kernel 版の実体が無い」ことしか言わず、その先に動く実体が
  あるかどうかについては何も言わない。相反する根本原因が同じ台帳に併存したまま、
  F501 と `output/insights/2026-08-26_b10-balanced-profile/README.md` が独立に正しい機構を
  書いた後も F241 は訂正されなかった。検出はユーザーの指摘と、同日の同一 node・同一 run 対測定
  23 run。恒久対応は memory `nonzero-rc-of-a-dispatcher-is-not-absence` —
  非 0 rc を「対象の不在」と読む前に、rc を返した実体が振り分け役でないかを確かめ、
  推論の否定側を同じ台帳の中でも検索する (worklog 2026-09-04、
  `output/insights/2026-09-04_f241-perf-attribution/`)。

## supersede 追記

- F241 **supersede: 2026-09-04** — 恒久対応の 3 点を訂正する。(1)「計算ノードに現行 kernel 用 perf が無い」は kernel 一致の linux-tools が無いという意味では真だが、既設の `/usr/lib/linux-tools/5.15.0-100-generic/perf` と `/usr/lib/linux-tools/5.15.0-135-generic/perf` は実在して動く。(2)「環境側 (管理者手番) に linux-tools を入れてもらう以外に道はない」は成り立たない。rc=2 を返すのは `/usr/bin/perf` という振り分け役で、完全一致する版が無ければ他版へ fallback せず exit 2 するだけである。(3)「perf を外す回避を採ってはならない」は D352 と矛盾する — 正式系列は perf 不在で進み `use_perf=false` の測定は eligible である。2026-09-04 の実測: gen_S へ 24 job 投入し 23 job が返却 (request 975613 のみ scheduler 出力・probe 出力とも戻らず除外)、6 distinct bnode (049 / 074 / 075 / 076 / 092 / 101、うち 092 と 101 で 17 run)、全 node が kernel 5.15.0-173-generic・`perf_event_paranoid=0`。同一 node・同一 run の対比で literal `perf` は 23/23 が `stat` rc=2 で 4 event 0/4、絶対 path 2 本は 46/46 が rc=0 で 4/4、両側 control は全 run で成立した。示したのは候補実体の直接 smoke までであり、production argv (`-x,` と `-o <csv>`) の完走は示していない。受理集合は経路ごとに違う — shell の `certify_calibration.sh` は `[[ -x ]]` で候補を受理して既に選定しており、Python の `submission._executable` は symlink を拒み (F89、未裁定)、床値 preflight は literal だけを probe する (D348)。したがって本追記は絶対 path の採用を認可せず、[T-970] の見送りと D352 を動かさない。distinct node は 6 であり本項の 8 node と同等の標本ではない。全数記録は `output/insights/2026-09-04_f241-perf-attribution/`。
