---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2676-job-session-sweep
seq: 2
---

## {{D:job-session-sweep}}. 計算ノード job の終了遅延は job body が session の残存 process を回収して塞ぐ — 帰属は入れ子 user ns、発火は request SHA-256 束縛、signal と終了観測は pidfd

**決定 (D2124 の対処。D2048 / D2124 は置換しない):** job 内 dispatcher (`tools/pegasus/dispatch_compute.py` の `_job_run`) は、直接の子が戻った後・result 書込み前に
自分の session に残る process を回収する。

1. **対象** = `/proc/<pid>/stat` の session が `os.getsid(0)` と一致し、自分と祖先鎖 (ppid を 1 まで) を除き、かつ
   `readlink(/proc/<pid>/ns/user)` が自分 (init ns) と**異なる** process。bootstrap は全 task の子を入れ子 user ns に置くので、この述語が workload への帰属証明になる。
   同 ns・ns 不読・stat 不読は trace に記録するだけで signal しない。
2. **発火** = job script が export する `IZANAGI_DISPATCH_JOB_SESSION_SWEEP="$REQUEST_SHA256"` が `_job_run` の検証済み request SHA-256 と一致するときだけ。
   値は child_env から pop する。ambient な `1` や別 sha では getsid にも `/proc` にも触れない (login node の in-process テストを守る)。
3. **signal と観測** = `os.pidfd_open` → starttime 再照合 → `signal.pidfd_send_signal(SIGTERM)` → pidfd の `select.poll` (POLLIN = 終了) で 5 秒 →
   生存へ SIGKILL → 1 秒 → 再列挙。最大 2 巡、新規候補 0 で終了、候補 0 の巡は待たない。`os.kill(pid)`・非子 `waitpid`・subreaper・PID ns・setsid は使わない。
4. **記録** = `IZANAGI_DISPATCH_JOB_TRACE` の新事象 (`session-sweep-start` に祖先鎖、`session-residual`、`session-signal`、`session-process-exited`、`session-sweep-complete` の
   status ∈ {clean, remaining, unknown} と件数、`session-sweep-error`)。result schema の field は増やさない。sweep の失敗は `child_rc` / result / return を変えない。
5. 定数 5 秒 / 1 秒 / 2 巡は設計値 (未実測) であり、CLI・request・env から変えられない。

**理由:**
- D2124 の設計入力 (session 離脱・session を基準とする回収を検証候補とし、会計終了と残存子の終了を別々に評価) のうち、「job 終了時に残さない」は回収でしか満たせない。
  session 離脱 (`start_new_session`) は残存を別 session へ移すだけで、離脱後の記録途絶は回収成功の証拠にならない (D2124)。
- 計算ノードの実 trace で session leader は NQSV の `nqs_shpd` (ユーザー uid) であり、dispatcher は leader ではない。「同 session を全部 kill」は leader を殺す。
  祖先鎖の除外だけでは同 session の非祖先 NQSV process を守れない (段 3 A-1) ので、bootstrap の構造 (入れ子 user ns) から導ける帰属述語を置いた。login で述語の可読性を実測した。
- 既存の in-process テストは `patch.dict(os.environ, clear=True)` でないものがあり、`=1` の opt-in は ambient 継承で login の pytest session を走査しうる (段 3 A-2)。
- pid 再利用の窓 (段 3 A-3) と終了観測の独立性 (D2124 の「別々に評価」) は pidfd で同時に満たせる。計算ノード kernel 5.15 で利用可能 (login 実測、計算ノード実走)。
- 計算ノード 2 走 (generic 単一子 probe): 統制 no-child `E − J` = −0.468 秒 / 残存 0、陽性対照 keep (子 75 秒) `E − J` = −0.381 秒 / 残存 1 を KILL で回収
  (`after=kill`、pidfd で終了観測、G − t0 = 10.0 秒)。前 2 wave の同条件は 69.5 / 69.7 秒。
- **環境事実:** 計算ノード job 内の全 process は SIGTERM を SIG_IGN で継承する (nqs_shpd → bash → dispatcher → 子、F1012 と同じ)。handler を持たない残存子は TERM で死なず、
  猶予 5 秒後の KILL で死ぬ。keep の期待は投入前にこの形へ改訂して固定した。

**却下した選択肢:**
- 隔離 child を `start_new_session=True` で別 session に置く (session 離脱) — 会計は早く終わるが残存 process が node に残る。「残さない」を満たさない。
- subreaper で孫を回収する — F973 (zombie の窓が残存計数を汚す)。
- uid フィルタ — 同 uid の非 workload (`nqs_shpd` は uid 31609) を守れない。ns 帰属述語に包含。
- opt-in を固定値 `1` にする — ambient 継承で in-process テストが発火する。
- dispatcher で SIGTERM を SIG_DFL に戻して子孫に継承させる — TERM 猶予が効くようになるが job body 全体の signal 環境を変え、受入 suite の既存挙動へ波及しうる。本 wave の scope 外、次の一手候補。
- 計算ノードで SIGTERM を無視する子の追加 1 走 — probe の改変 (Codex author) と別事前登録が要る。結論を generic 単一子に限定し、SIGKILL 経路は login のテストで検証。
  結果的に keep 自体が SIG_IGN 継承で KILL 経路を通った。
- watchdog・一般的な process 管理機構・result schema への field 追加 — 依頼の scope 外。
