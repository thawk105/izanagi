---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t870-lease-timing
seq: 1
---

## {{D:t870-acceptance-lease-timing-gap}}. 受入lease claim〜land/releaseの実時間を実測し、既定値は変更せず opt-in override 使用時のTTL超過リスクを記録に留める

**決定:** `output/insights/2026-08-20_t870-acceptance-lease-timing/README.md` へ、
lease claim〜dispatch submit〜queue-wait〜run〜land完了の実時間を landed 済み3 wave の
成果物 (`acceptance-run.{pid,done}`・`land.{pid,done}`・PBS qstat summary block の絶対時刻) から
実測して記録した。既定値 (queue_wait=900秒/overall_grace=300秒/walltime=3600秒/lease
TTL=2400秒) はいずれも変更しない。次の対応は**行わない**。

1. lease TTL・既定walltime・queue-wait/overall-graceの既定値変更。
2. D299 が裁定パッケージへ送付済みの invocation 識別・fencing 機構の新設。
3. `tools/dev_wave_land.py --lease-dir` を land 呼出しへ配線する変更 (renew/release
   自動化の可能性を発見したが、fencing gap と交差しうるため未調査のまま見送る)。

**理由:**

- 実測3サンプル (claim取得〜land完了、算出は submit〜done を近似に使用) は 326〜1103 秒
  ([[D612]] の段2見積り「Q+G<=770〜1070秒」と整合)、TTL 2400秒に対し十分な余裕がある。
  既定値下では latent gap は顕在化しないと確認した。
- 一方、[[D612]] が新設した opt-in override (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`/
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE`) を、その override が想定する実congestion規模
  (`docs/archive/worklog-phase3-0816-566-567.md` の83分・`docs/archive/worklog-phase3-0804-187.md`
  の6時間) に当てはめると、lease保持想定はTTLの2.2〜9.2倍に達する。override はdispatch自体を
  queue-wait-timeout/overall-timeoutで死なせないことだけを保証し、lease TTL内に収まることは
  何も保証しない — override の存在とTTLの存在が未接続のまま残っている。
- この未接続を閉じる設計 (fencing token、`--lease-dir`配線によるrenew自動化など) は、
  D299 がすでに「invocationを識別しない」ことを既知の限界として明記し、機構案を裁定パッケージへ
  送付済みの領域と重なる。[[D612]] が「識別・fencing機構はT-870固有の課題ではなく
  プロジェクトレベルで別途解決すべき前提条件として扱い、T-870側で先回りして解こうとしない」と
  裁定した理由をそのまま継承する。
- `_LauncherSession.wait()` (`tools/dev_wave_wait.py:550`) の timeout=None (起動済み launcher を
  `--max-wait-seconds` で中断できない) は、実運用ログ自身が
  `"acceptance-command timeout=none (long-running acceptance is intentional)"` と記録しており、
  意図された設計と確認した。改修対象ではなく、制約として記録するに留める。

**却下した選択肢:**
- 新規の受入lease投入による合成計測 — 実測時点で13並行peer sessionが稼働しており、
  測定専用の投入は他waveのland窓口を奪う。landed済みwaveの実artifact事後解析で代替した。
- `--lease-dir`配線の実装まで踏み込む — 効果 (renew/release自動化) を確認できたが、
  安全性 (TTL失効後の別waveによる再claimとの相互作用) の検証には D299 の裁定領域の再調査が
  要る。本waveのscope (既定値を変更しない実測) を超えるため見送った。
