---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: worktree-t2850-trace-concurrent-verify
seq: 1
---

## {{D:concurrent-local-verify-fork-receipt}}. 性能 pass の trace 5 本を直列に取得してから fork した子で同時に検査し、子は受領証を返して親が rep 順に取り込む opt-in を比較 harness の write-heavy に入れ、その初回静定待ちの上限を本番順序の実測から 120 秒にする

**決定:** 探索の独立反復の試走の費用を削る案 (b) (親の委任による codex 相談の決定、2026-09-26) を次の形で実装した
(記録 `output/insights/2026-09-26/t2850-trace-concurrent-verify/README.md`、追補 2 `docs/search-repetition-trial-preregistration-addendum-2.md`)。

1. **検査の方式:** `pipeline._run_local_concurrent_pass` が性能 pass の trace を rep 0 から直列に全部取得した後、rep ごとに `os.fork` した子で
   直列経路と同じ引数の `verify_trace_dir_with_capability` を呼ぶ。子は certified なら `serialize_remote_verification_receipt` で受領証にし、
   HMAC (fork 前に親が rep ごとに作る 32 byte の secret) 付きの結果を create-only file で返して `os._exit` する。親は既存の
   `_admit_verify_fanout_result` → `admit_remote_verification_receipt` (受理規則は変えない) で自 PID の一回限りの capability に変える。
   子は WAL・trace 保全・一時 dir に触れない。子で build admission を再導出しないので generator id を問わない (remote fan-out の
   `BACKOFF_REPRO` 限定 (D1810 項 6) は remote だけのまま)。適用は opt-in ∧ performance tag ∧ campaign WAL sink ∧ fullscale 分岐 (bench_lock と
   競合 probe の下) で、reps が 1 なら直列、remote fan-out の host 指定・qualification sink との併用は拒否する。
2. **失敗の意味論:** 最小の失敗 rep (取得失敗・不認証・子の故障) が確定したら、それより後の子を process group ごと SIGKILL して回収し、
   それより前は完了を待って、rep 0 からその rep までを `_project_repetition_outcome` で 1 回ずつ投影する。子は fork 直後に自分の process group を作り
   (verifier の pool worker も同じ group に入る)、親は leader を回収する前に /proc で group の非 zombie member が無いことを確かめる (5 秒、
   終了途中の無関係な process の ESRCH は読み飛ばす)。確かめられなければその rep を `verify-local-unavailable` (capability を発行しない) にし、
   trace の保全・削除までは進む。各 rep の結果が直列と同じなら、WAL の段の並びと abort reason は直列と一致する。
3. **opt-in の配線:** `p3_s4_loop --verify-performance-concurrent` (`--verify-performance` と `--perf-workload write-heavy` が要る) → 有効時だけ
   search_config に `verify_performance_concurrent: true` (campaign identity に入る。無指定の identity は不変) → `loop.run_campaign` → `evaluate`。
   比較 harness は write-heavy の slot argv に常に付け、台帳 header に `verify_performance_method: local-concurrent` を記録する。
   Pegasus の job body と B-5 の経路は変えていない。
4. **静定待ち:** 同時検査 mode の `_run_bench` の初回 `settle` だけ上限を 120 秒にする (`_CONCURRENT_VERIFY_SETTLE_TIMEOUT_S`)。閾値 4.0、
   `settled=true` による品質の分類、測り直し round の settle (20 秒)、`calibrator/runner.py` の bytes は変えない。

**理由:**
- `VerificationCapability` は発行した PID に束縛されるので、子の capability を親へ直接は渡せない。別 process を新しく起動する方式は子で
  build admission を generator ごとに再導出する必要があり、比較 harness の全 slot は `BACKOFF_SWEEP` (相談 A の must-fix) なので既存の remote 経路は
  使えない。fork の子は親の記憶上の認可をそのまま使え、受領証の経路で親の一回限りの capability へ変わるので、受理規則を緩めずに済む。
- 60 秒 (当初の親の裁定) は「直列検査 → 90 秒の減衰 → 同時検査」の順の実測 (3〜39 秒) から決めた値で、本番の「5 本の連続取得の直後に同時検査」とは
  状況が違った。計算ノードの smoke で stock が 60 秒を使い切って品質欠測になり、本番順序で測り直すと 67 秒 (stock)・77 秒 (候補の代理) だった。
  120 秒の上限で再 smoke の 5 session はすべて settled=true・品質 normal。
- 1 session は stock 245〜273 → 166 秒、重い候補 474〜520 → 260 秒 (smoke の実測)、試走全体の見積りは 40.8〜58.2 → 22.2〜40.5 node 時間。

**却下した選択肢:**
- remote fan-out (D1810) の worker に「取得済み trace を検査するだけ」の分岐を足す — worker が trace 取得・`/scr` 複製・`BACKOFF_REPRO` の再導出を
  所有し、分岐を重ねると回帰面が増える (相談 B)。
- trace の内容 digest を task に束縛する (相談 A2) — 直列経路も trace_dir の path と commit 数だけで束縛し、同時化で増えるのは同じ user の tmp dir での
  滞留時間だけ (新しい信頼境界が無い)。
- 検査 process の timeout を新設する — 直列経路にも検査の timeout は無く、job の walltime が上限。
- 失敗 rep より後と `finally` の経路で group の消滅確認の失敗を reject に写す (焦点再レビュー 2) — それらの rep は投影されず、group 全体へ SIGKILL を
  送った後の process は利用者コードを実行できないので、判定・記録の値が変わらない。
- 不認証の rep の `EvalResult.verify_result` を子から親へ運ぶ (レビュー A4) — 比較 harness の経路は `result_evidence_context` を渡さず、構造化診断は
  WAL の abort detail に残る (remote fan-out も同じ)。
- 静定の閾値を上げる・settled=false を許す — 正しさではないが測定の品質条件を緩めることになる。
