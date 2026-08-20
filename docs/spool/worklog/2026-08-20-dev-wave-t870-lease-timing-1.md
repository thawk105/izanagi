---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t870-lease-timing
seq: 1
title: '[T-870] 受入lease claim〜land/releaseの実時間を実測し、既定値下は安全・opt-in override使用時のTTL超過リスクを定量化して記録した (docsのみ、branch worktree-dev-wave-t870-lease-timing)'
---

## 本文

- 前wave (769、opt-in override新設) の次の一手 (a)(b)(c) を受け、claim→launcher
  start→postrun→receipt→land/release の実時間を実測した。新規の受入lease投入はせず、
  実測時点で稼働中だった13並行peer sessionとの競合を避けるため、本日中にlandした3 wave
  (T-1442/T-1445/T-1441) の成果物 (`acceptance-run.{pid,done}`・`land.{pid,done}`・
  PBS qstat summary blockの絶対時刻) を事後解析した。詳細表は
  `output/insights/2026-08-20_t870-acceptance-lease-timing/README.md`。
- 「claim試行開始→PBS submit」(32〜74分) はizanagi lease自体へのcontention待ちであり、
  TTL(2400秒)クロックの対象外と推定した (T-1442は総process寿命83分でも正常landしており、
  もし試行開始からTTLが動いていれば失効していたはず)。TTLを実際に消費する
  「submit〜land完了」区間は3サンプルで326〜1103秒、T-1442実測で552秒であり、
  いずれもTTL 2400秒に対し余裕がある。前wave段2の見積り「Q+G<=770〜1070秒」と整合する。
- 一方、前waveが新設したopt-in override (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`/
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE`) を、その override が想定する実congestion規模
  (83分・6時間) に当てはめるとlease保持想定がTTLの2.2〜9.2倍に達すると定量化した。override
  はdispatch自体の生存だけを保証し、lease TTL内に収まることは保証しないという未接続を
  裁定 {{D:t870-acceptance-lease-timing-gap}} へ記録した。
- `_LauncherSession.wait()` (`tools/dev_wave_wait.py:550`) の`--max-wait-seconds`不介入
  (起動済みlauncherを中断できない) は、実運用ログ自身が
  `"acceptance-command timeout=none (long-running acceptance is intentional)"`と記録しており、
  バグでなく意図された設計と確認した。
- 副産物: `tools/dev_wave_land.py`呼出しに`--lease-dir`を渡さないと`lease_renew`/
  `lease_release`が`reason=lease-dir-required`でunavailableになる (land-run.log実測で発覚)。
  配線すればrenew/release自動化になりうるが、D299のfencing gapと交差しうるため本waveでは
  未調査のまま次候補として記録するに留めた。
- 実装は行っていない (docsのみ)。棄却理由は{{D:t870-acceptance-lease-timing-gap}}参照。

## 次の一手差分

### 更新

- [T-870] **P2・claim〜land/release実時間を実測、既定値下は安全と確認**:
  `output/insights/2026-08-20_t870-acceptance-lease-timing/README.md`に実測3サンプル
  (326〜1103秒、TTL2400秒に対し余裕あり) を記録した。前wave(769)の次の一手のうち
  (a) 実時間実測は完了、(b) walltime(3600秒)>TTL(2400秒)は既定値下ではlatentなまま
  (実行は300秒未満、天井に到達する実例なし) と確認、(c) `_LauncherSession.wait()`の
  timeout=noneは実運用ログで意図された設計と確認 (バグではない、修正対象から除外)。
  新たに定量化した残る課題: opt-in override (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`/
  `_OVERALL_GRACE_OVERRIDE`) をその想定用途 (83分/6時間congestion) で使うとlease保持想定が
  TTLの2.2〜9.2倍に達する — override自体とTTLが未接続。次回試行が設計に含めるべき点:
  (d) mutation harness自身へcaller-budget-awareな値を渡す設計 (未着手、769から持ち越し)、
  (e) 「queue混雑時は待つのでなく並列度を下げる」別解 (`IZANAGI_TEST_NPROC=4`実例、未着手、
  769から持ち越し)、(f) D299が裁定パッケージへ送付済みのinvocation識別・fencing機構は
  引き続きT-870固有の課題として先回りしない、(g) `tools/dev_wave_land.py --lease-dir`を
  land呼出しへ配線するとrenew/release自動化になりうると判明したが安全性未検証 (本wave新規発見、
  D299のfencing gapと交差しうるため次回試行の候補として残す)。
  base: 427d55c749e3af25a62be5618ea67bb81e0e5b22e6485171d84c8162835fa1ef
