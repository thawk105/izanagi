## 段 1 brief

### 研究前進 (土台)
受入全走・変異 harness・campaign の計算ノード job は、pytest 完了後に job の session に process が残ると walltime まで RUN に留まる
(F853: 3609 秒、T-2622/T-2675 の陽性対照で 70 秒窓を再現)。8c 無人ループの計算ノード実所要をこの型から守る土台。
完了判定 = 計算ノード実測で、陽性対照 (session 内に 75 秒生きる孤児子) の `E − J` (NQSV `Ended` − trace `job-run-returned`) が
約 70 秒 → [−1, 5] 秒になり、残存 process が job 内 trace で特定され、その終了が job 内で独立確認される。統制 (子なし) は残存 0 件・
`E − J` ∈ [−1, 5] のまま。受入全走緑。

### scope
`tools/pegasus/dispatch_compute.py` の job body (`_job_run`) に、直接の子が戻った後 result 書込み前に、
「自分の session (`os.getsid(0)`) に残る process のうち 自分と祖先鎖を除くもの」を列挙して trace に記録し、SIGTERM → 猶予 → SIGKILL で
終了させ、/proc から消えたことを確認する最小の局所処理を足す。発火は job script (`_job_script`) が export する opt-in だけ。
テストは新規 nodeid 数本 (session 隔離した fixture 子で正例・負例)。probe は repo へ commit しない (T-2675 の probe を untracked で再利用)。

### 確定済み裁定
D2124 (RUN に留めるのは現在の session 所属)、F973 (subreaper 不採用)、D95 (実装面は Codex author)、依頼文 (一般的な process 管理機構へ
広げない、仮想リスク向け gate・検査・台帳・一般化は scope 外、規律 2 を緩めない)。

### 不変条件
- correctness gate / verifier に触れない。`pegasus-dispatch-result/v1` の field を増やさない (特定結果は `IZANAGI_DISPATCH_JOB_TRACE` 行のみ)。
- `_is_bound_job_envelope` の substring 契約 (`exec "$selected" "$DISPATCHER" --job-run "$REQUEST"` 等) を壊さない。
- subreaper・PID namespace・job body 自身の setsid を入れない (reparenting を変えない → F973 の consumer 列挙義務は非該当)。
- sweep の失敗 (EPERM、消滅未確認) は child_rc / result を変えない (trace に記録するだけ)。
- opt-in が無い in-process 呼び出し (login node の pytest 内) では 1 process も列挙・signal しない。
- 別 session へ移った process には触れない (D2124: 元 session の列挙では拾えない = 本 wave の scope 外)。

### 成果物
code diff + tests、計算ノード実測 2 走 (generic、`no-child` / `keep`)、insight README (`output/insights/2026-09-18/t2676-job-session-sweep/`)、
worklog / decisions fragment。

### 攻撃対象 (親の provisional 裁定)
- (P1) 走査対象 = `/proc/<pid>/stat` の sid == 自分の sid、かつ pid ∉ {自分} ∪ 祖先鎖 (ppid を辿って 1 まで)。根拠: T-2675 request 4026 で
  job 内 dispatcher pid 3010049 ≠ sid 3010029 — dispatcher は session leader ではなく、session に NQSV 側の祖先がいる。
- (P2) 発火条件 = job script が `export` する env (名称は plan 提案、例 `IZANAGI_DISPATCH_JOB_SESSION_SWEEP=1`)。`_job_run` は child_env から
  pop する (tests task は env_mode=inherit なので pop しないと job 内 pytest が in-process `_job_run` を呼ぶ test で sweep を発火しうる)。
  根拠: `orchestrator/tests/test_pegasus_dispatch_compute.py` :1149 / :2422 / :4156 (`_job_run` 直呼び)、:6186 / :6210 (`main --job-run`)。
- (P3) 配置と順序: `_job_run` の child 段の後 (isolation 失敗経路を含む)、`_write_result_replace` (:1704) の前。
  列挙 → trace `session-residual` (pid, ppid, comm, state, uid, starttime) → SIGTERM → 猶予 → 再列挙 → SIGKILL → 消滅確認 →
  trace `session-sweep-complete` (件数)。kill 後に孫が reparent される窓があるので再列挙を 1 回入れる。
- (P4) 猶予 = 5 秒、反復 = 2 回まで。実測分布は無い (F973 の孫 6 本は即時回収)。
- (P5) 実測: T-2675 の probe (job dir 保全、sha256 f7811622…、30,373 bytes) を worktree に untracked で置き、generic task で `keep` (子 75 秒、
  陽性対照) と `no-child` (統制) を各 1 走。期待: keep は residual 1 件 (probe の子)、SIGTERM で消滅、`E − J` ∈ [−1, 5]。
  no-child は residual 0、`E − J` ∈ [−1, 5]。前 2 wave で同器具の 70 秒窓が再現済みなので反復しない。
- (P6) 変異事前登録 (段 4 で確定): sweep 呼出し削除 / 祖先除外削除 / opt-in 無視 (常時発火) / SIGKILL 段削除 / 消滅確認削除 — それぞれ新規 test が KILLED。
- (P7) uid フィルタ (自分と同じ uid だけ signal) を入れるか — 親は入れない側 (EPERM は catch して記録すれば足りる) を provisional とする。

### 変更面 (実アンカー)
| file | 位置 | 変更 |
|---|---|---|
| `tools/pegasus/dispatch_compute.py` | `_job_script` :834〜913 (`export {_REQUEST_SHA256_ENV}` の隣) | opt-in export 1 行 |
| 同 | `_job_run` :1530〜1711 (child 段 :1655〜1690、result 書込み :1704) | sweep 呼出し |
| 同 | :1620〜1627 (child_env の pop 列) | opt-in を child_env から pop |
| 同 | 新規関数 (`_job_trace` :710 の近く) | 列挙・signal・消滅確認 |
| `orchestrator/tests/test_pegasus_dispatch_compute.py` | 新規 test (既存 helper `_job_run_with_mocked_child` :4083 の近く) | 正例・負例 |

### 分割方針
DW-C00 の条件: 設計択一が割れる (回収 vs 離脱、発火条件の形、猶予値) → 段 2 plan + 段 3 敵対 2 レンズ + 段 6 レビュー 2 本を回す。
実装子 1 本 (dispatcher + tests を同一 file 群で所有)。受入・実測環境 = Pegasus (login で focus 走、計算ノードで generic 2 走と受入全走)。

