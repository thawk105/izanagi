# 受入lease claim〜land/releaseの実時間実測 — 既定値下は安全、opt-in override使用時にTTLを超えうる (2026-08-20)

- wave: `dev-wave-t870-lease-timing` (branch `worktree-dev-wave-t870-lease-timing`)
- base main: `66fdf68c` (継承branchなし、T-870 main起点)
- 依頼: 受入lease claim→launcher start→postrun→receipt→land/release の実時間と、
  lease TTL(2400秒)・既定walltime(3600秒)の空白を実測する。既に landed した opt-in override
  (D612、T-870 前wave) は検証対象とするが既定値は自動変更しない。
- 結論: **実装差分ゼロ。** 既定値 (queue_wait=900s/overall_grace=300s/walltime=3600s) 下では
  実測3サンプルとも lease TTL(2400秒) に対し十分な余裕がある。構造的な空白は
  **opt-in override (D612) を意図された用途 (実congestion実例55分/2.5時間への耐性) で使った場合**
  に顕在化する — override自体は正しく動くが、それを使うとlease TTLを超過しうるという
  未接続の組み合わせが残っている。fencing機構 (D299が裁定パッケージへ送付済み) には触れない。

## 1. 実測方法

新規の受入lease投入は行わず、本日 (2026-08-20) 中に実際にlandした3 waveの成果物
(`/work/1/SFC/tanab/dev-wave-jobs/<wave>/`) を事後解析した。理由: 実測時点で13の並行peer
sessionが稼働しており、測定専用の受入投入はlease窓口を奪い他waveのlandを妨げる
([[no-concurrent-dispatch-during-acceptance]]と同種のリスク)。既に発生した実運用の受入は
無償で得られる一次資料であり、合成した単発計測より母集団として妥当である。

一次資料:
- `acceptance-run.pid` / `acceptance-run.done` / `land.pid` / `land.done` の mtime
  (`dev_wave_wait.py acceptance` / `dev_wave_land.py` 呼出しスクリプトが起動直後に自身のPIDを
  書き、終了時にrcを書く定型 — 呼出し元 `acceptance-launch.sh`/`land-launch.sh` を実見して確認)。
- `acceptance-child-*.log` 末尾の PBS `qstat -f` summary block
  (`Created Request Time` = dispatch submit、`Started Request Time` = RUN観測 (queue-wait終端)、
  `Ended Request Time` = END) — 絶対時刻を持つ唯一のログ (child logのstate遷移行自体は
  時刻なし、[[acceptance-run-takes-about-two-minutes]]の記載どおり)。

## 2. 実測結果 (2026-08-20、gen_S、13並行peer session下)

| wave | acceptance-run.pid (=claim試行開始) | PBS submit | PBS RUN観測 | PBS END | run.done | queue待ち | pytest実行 |
|---|---|---|---|---|---|---|---|
| T-1442 (c06-reachability) | 20:53:19 | 22:07:24 | 22:08:02 | 22:11:45 | 22:11:59 | 38s | 223s (13953 passed) |
| T-1445 (buildcache-toolchain) | 20:20:47 | 21:09:40 | 21:23:06 | 21:27:49 | 21:28:03 | 806s | 283s (13932 passed) |
| T-1441 (unit3-d574-audit) | 20:09:59 | 20:42:33 | 20:44:14 | 20:47:41 | 20:47:59 | 101s | 207s (13928 passed) |

T-1442のみ land 時刻も回収済み: `land.pid` 22:15:22 → `land.done` 22:16:36 (land所要 74秒)。

**区間ごとの解釈:**

- **「claim試行開始→PBS submit」(32〜74分、表の1列目→2列目):** izanagi受入lease自体への
  contention待ち (13並行peer session下)。`dev_wave_wait.py acceptance`は内部でclaimを
  `--poll-seconds`間隔(30〜120秒に強制)で再試行し、取得できてから初めて
  `python3 tools/run_tests.py`をdispatchする一体型CLIである
  ([[acceptance-lease-contract]])。**この待ちはlease TTL(2400秒)クロックの対象外と推定する** —
  T-1442は「claim試行開始」から「land完了」まで総所要83分17秒 (4997秒) だが正常にlandしており、
  もしTTLクロックが試行開始時点から動いていればとうに失効し他waveに回収されていたはずである。
  D299が定義する状態機械 (`acquired`/`held-self`/`held`/`queued`/`stale-held`/`unavailable`) と
  整合する解釈であり、TTLは実際に`acquired`した瞬間から測られる。
- **「PBS submit→END」(queue-wait+実行、表の2〜4列目):** izanagi lease保持下でのPBS
  scheduler待ち + pytest実行。3サンプルで38〜806秒 (queue) + 207〜283秒 (実行) = 261〜1089秒。
  T-1445の806秒はDEFAULT_QUEUE_WAIT_TIMEOUT_S=900秒の上限に近い実例であり、
  それでも合計1089秒はTTL 2400秒の45%に収まる。
- **T-1442の「submit→land完了」(TTL消費の実測上限に近い区間):** 22:07:24〜22:16:36 =
  552秒。lease TTL 2400秒に対し余裕1848秒 (77%)。

**結論A (既定値下):** 3サンプルとも、lease取得からland完了までの実測所要はTTL(2400秒)の
半分未満に収まっている。D612 (前wave) が段2プランで見積もった「Q+G<=770〜1070秒」と整合する。

## 3. コード実測 (file:line、2026-08-20時点)

- lease TTL: `_LEASE_TTL_SECONDS = 2400` (`tools/dev_wave_wait.py:230`)。
- dispatchの既定値: `DEFAULT_WALLTIME = "01:00:00"` (=3600秒)、
  `DEFAULT_QUEUE_WAIT_TIMEOUT_S = 900.0`、`DEFAULT_OVERALL_GRACE_S = 300.0`
  (`tools/pegasus/dispatch_compute.py:46-48`)。
- opt-in override (D612、`tools/run_tests.py:72-74`、`_default_dispatch`:1142-1183):
  `IZANAGI_DISPATCH_WALLTIME_OVERRIDE` (既存)・`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE`・
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE` (本wave直前のT-870 waveで新設、commit `dd29fd9c`)。
  いずれも未設定なら既定値を完全維持する (`_default_dispatch`は`environ.get(...)`が空/未設定なら
  `dispatch_kwargs`へ追加しない)。
- dispatchの`total_deadline`はRUN初観測時に再計算される
  (`tools/pegasus/dispatch_compute.py:1866-1874`: `run_observed_at + walltime_s + overall_grace_s`)。
  つまり`walltime`は「queue待ちを含む全体」ではなく「RUN開始からの実行時間」に対する上限であり、
  queue待ちは別途`queue_wait_timeout_s`(既定900秒)で独立に制限される。
- `_LauncherSession.wait()` (`tools/dev_wave_wait.py:550`) は `self._process.wait()` を
  timeout引数なしで呼ぶ。実運用ログ (`acceptance-run.log`) は
  `"acceptance-command timeout=none (long-running acceptance is intentional)"`
  と自己記述しており、**中断不能は意図された設計**と確認した (バグではない)。
  `--max-wait-seconds`は`_AcceptanceDeadline`(claim取得待ちループ、`dev_wave_wait.py:441-455`)
  にのみ作用し、一度`_LauncherSession`が起動した後の`python3 tools/run_tests.py`実行自体は
  この予算の対象外である — command引数が指摘した制約はこの構造を指す。
- renewは独立subcommandを持たない。D299 (`docs/decisions.md:13848`) が「専用renew subcommandを
  足す」を明示的に却下しており、claimの再呼出し (EX flock内でmtime更新、`held-self`を返す) が
  renewを兼ねる。releaseは`dev_wave_wait.py acceptance`の再呼出しでは行えず
  (`held-self lease retained; this invocation has no release authority`)、
  `tools/wave_land_window.py release --lease-dir <dir> --wave <wave>` を land成功確認後に
  単独実行する ([[acceptance-lease-contract]])。

## 4. 構造的空白の定量化

**(a) 既定walltime(3600秒) > lease TTL(2400秒)。** `DEFAULT_WALLTIME`はdispatchへ渡す
`elapstim_req`(PBSへの実行時間上限申告)であり、実測pytest実行時間 (207〜283秒、
[[acceptance-run-takes-about-two-minutes]]の183〜274秒レンジと整合) を大きく上回る
安全側の天井にすぎない。**この天井自体が実際に消費されるシナリオは観測されていない**
(3サンプルとも実行は300秒未満)。したがって既定値のままでは(a)は latent (顕在化しない) であり、
D612が「(1)は算術的に成立しない」と判定した理由 (walltime自体が既にTTLを超えている) を
実測面から裏付けるに留まる。

**(b) opt-in override使用時のTTL超過シナリオ (顕在条件).** D612は
`docs/archive/worklog-phase3-0816-566-567.md`(83分間congestion)・
`docs/archive/worklog-phase3-0804-187.md`(6時間grace実例)を一次資料として引用している。
これらの実congestion規模にopt-in overrideを当てはめると:

| シナリオ | 設定するoverride値 | lease保持想定 (submit〜land完了) | TTL(2400秒)比 |
|---|---|---|---|
| 83分congestion実例 | `QUEUE_WAIT_TIMEOUT_OVERRIDE=5000`程度 | queue最大83分(4980s)+実行300s+land100s ≈ 5380s | **2.2倍超過** |
| 6時間grace実例 | `OVERALL_GRACE_OVERRIDE=21600` | grace最大6h(21600s)+実行300s+land100s ≈ 22000s | **9.2倍超過** |

**opt-in overrideは「dispatchがrc=16/overall-timeoutで死なずに済む」ことだけを保証し、
「lease TTL内に収まる」ことは何も保証しない。** override値を大きくするほど、
lease保持中にTTLが尽きる確率は上がる。TTL失効時の挙動はD299が既に「fencing token不在」
として既知の限界に置いている (`known limitation: no fencing token is provided`、
実運用ログにも同文言が出る) — 別waveが再claimしても、失効前waveのdispatch job自体は
停止できない。land自体は`tools/dev_wave_land.py`の協調lockで直列化されるため**結果は
壊れない**が、TTL失効後は「受入直列化」というleaseの目的が効かなくなり、
失効した側のcompute投入が無駄になりうる。

## 5. 明示的にscope外としたもの

- **fencing機構の新設・改修。** D299が「invocationの識別・capability/fencing機構は裁定パッケージで
  返す」と既に裁定しており、T-870固有の判断で先回りしない ([[T-870前wave (D612) と同じ理由]])。
- **`tools/dev_wave_land.py --lease-dir`配線の採否。** land-run.log実測で、`--lease-dir`を
  渡さない現行land呼出しは`lease_renew`/`lease_release`が`reason=lease-dir-required`で
  unavailableになると判明したが (T-1442の`land-run.log`で確認)、`--lease-dir`を渡した場合の
  実際の renew/release セマンティクスは未調査。上記fencing gapと交差しうるため、
  本waveでは調査・実装のどちらも行わない。後続taskの候補として記録するに留める。
- **既定値・TTLの変更。** command引数の明示指示どおり自動変更しない。

## 関連

- [[D612]] (前wave、opt-in override新設の裁定)
- [[D299]] (lease self-holding/fencingの既知の限界)
- `docs/archive/worklog-phase3-0820-733.md` (前々wave、blocker発見)
- memory: `acceptance-lease-contract.md`、`acceptance-run-takes-about-two-minutes.md`
  (本insightの実測3〜5節が更新の一次資料になる)
