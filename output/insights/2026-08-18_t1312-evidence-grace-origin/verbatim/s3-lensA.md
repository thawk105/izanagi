### S1

- 所見 ID: S1
- 主張: 論理時計が preflight 完了から spawn 完了まで進まないため、提案テストは旧起点を殺す一方、誤った preflight 完了起点を通す。
- 根拠: `/home/SFC/tanab/.claude/jobs/a7e13b47/tmp/wave-t1312/plan.md:107-125`、`tools/codex_worker_launch.py:1765-1800`
- 具体的な失敗シナリオ: 実装が `preflight_now_ns + grace` を使っても、テスト上は preflight と spawn がともに 0.10 秒なので `supervision_drain == 0.05` が成立する。実機で `Popen` と `read_pid_identity` に 0.4 秒かかれば、子の実効猶予は 0.1 秒まで縮む。
- 重大度: must-fix — 宣言集合より狭い受理集合が残り、`evidence_forced_stop` と `stop_reason=max_attempts` の偽赤が再発する。spawn 区間にも論理的な正の時間差を注入し、`phase_duration_s["spawn"]` も assert すべきである。

### S2

- 所見 ID: S2
- 主張: 親 brief の「総所要を `max_wall_clock_s` が有界化する」という不変条件は、現行実装を物理的な launcher 総所要として読むと成立していない。
- 根拠: `tools/codex_worker_launch.py:2257-2268,2304-2344,2347-2429,2494-2498,1491-1533,2648-2701`、同 `:2226-2228`
- 具体的な失敗シナリオ: `max_wall_clock_s=3` でも、最初の wall 検査より前に各 5 秒 timeout の preflight が走る。また limit 到達後も termination grace と reap が続く。成功経路でも最終 latch 後の receipt 公開に wall 再検査がなく、3 秒を越えて accepted receipt が公開されうる。receipt 自身は scope を `launcher_start_to_receipt_fields_finalized` と宣言している。
- 重大度: must-fix — accepted receipt の `actuals.wall_clock_s` は上限内でも、実際の公開完了時刻は上限外になりうる。既存の receipt-field admission bound を意味する、と brief を狭めるか、物理的 hard cap を要求して外部 watchdog まで scope に入れるかを裁定パッケージへ返す必要がある。

### S3

- 所見 ID: S3
- 主張: 提案された判別テストは attempt 2 を必須にしておらず、F57 の実機序である retry 時だけ旧起点へ戻る欠陥を殺さない。
- 根拠: `/home/SFC/tanab/.claude/jobs/a7e13b47/tmp/wave-t1312/plan.md:75-110,144-152,154-169`、`orchestrator/tests/test_codex_worker_launch.py:1552-1553,4153-4161,4288-4296`、`/home/SFC/tanab/.claude/jobs/a7e13b47/tmp/wave-t1312/F57-excerpt.md:20-30`
- 具体的な失敗シナリオ: `attempt_index == 1` では spawn 起点、retry では `state.started_ns` を使う変異は、既定 `max_attempts=1` の sidecar テスト、既存 exact-duration テスト、attempt 1 の direct test をすべて通る。負荷時には実際の `payload_decoy,normal` や `retry_reject,retry_wait` の attempt 2 が再び即殺される。
- 重大度: must-fix — 受入全走の非帰属赤が残り、成果物への到達を証明できない。少なくとも一方を明示的な attempt 2、または second-validator だけを遅らせる二試行テストにする必要がある。

### S4

- 所見 ID: S4
- 主張: F57 の 3 件は機序の存在証明にはなるが、preflight の一般分布や再発率を示す独立 3 標本ではない。
- 根拠: `/home/SFC/tanab/.claude/jobs/a7e13b47/tmp/wave-t1312/F57-excerpt.md:12-30,34-49`
- 具体的な失敗シナリオ: 3 件は同一 request、同一 host、48-worker 全走の同じ負荷局面にあり、全件 attempt 2 である。これを「preflight は一般に grace を食い切る」または「本変更で F57 族全体が消える」と一般化すると、green 側分布や retry 膨張原因が未測定のまま閉じられる。
- 重大度: should-fix — D498 の意味是正は反証されないが、成果物の根拠は「一度実在した機序」に限定し、頻度や全再発消滅の主張を外すべきである。

### S5

- 所見 ID: S5
- 主張: 親 brief の P3 は path 検索だけを根拠にしており、`DW-O09` が明示的に禁じる証明方法になっているが、追加監査では今回影響する間接 pin は見つからなかった。
- 根拠: `/home/SFC/tanab/.claude/jobs/a7e13b47/tmp/wave-t1312/brief.md:68-71`、`docs/dev-wave/operations.md:54-65`、`orchestrator/codex_roles/review_ledger.py:15-35,75-78`、`hooks/README.md:89-96`、`orchestrator/tests/test_frozen_artifacts.py:41-88`、`docs/phase3.md:1244`
- 具体的な失敗シナリオ: role 名、schema、generator hash を key にする pin があれば launcher path の hit 0 件でも後段検査が赤になる。実際に repo には role-keyed pin 族がある。ただしそれらは Claude role sourceとmanifestを対象とし、hook 正本も launcher 自身を未 pin と明記する。launcher 二ファイルの現行 whole-file SHA-256 も tracked tree内に一致値がなかった。
- 重大度: should-fix — 現在の frozen bytes、schema、受理集合は変わらないが、P3 の根拠を追加監査結果へ差し替えない限り freeze dispatch の判定記録が不十分である。

### 必須 seam と不変 consumer の裏取り

- `FAKE_MODE=no_rollout` は `orchestrator/tests/test_codex_worker_launch.py:1403-1407` に実在し、同 mode の in-process 実行は `:4169-4178`、`LAUNCHER.main` helper は `:2420-2433` にある。
- `_hook_checker.validate_installation` の実呼出しは `tools/codex_worker_launch.py:277-305`、既存 monkeypatch は `orchestrator/tests/test_codex_worker_launch.py:3489-3504` にある。
- `_monotonic_ns` seam は `tools/codex_worker_launch.py:31-33`、論理時計への既存差し替えは `orchestrator/tests/test_codex_worker_launch.py:3483-3504,4260-4269` にある。
- `phase_duration_s` は `tools/codex_worker_launch.py:418-489` で構築され、`:2792-2796` から sidecar へ出力される。既存 assertion は `orchestrator/tests/test_codex_worker_launch.py:4221-4230`。
- `AttemptState.started_ns` は `tools/codex_worker_launch.py:1698-1705,2003-2006` で attempt wall clock に残り、receipt attempt の `wall_clock_s` は `:1631-1638`。診断 elapsed は別途保存した `attempt_started_ns` を `:391-399,461-467` で使うため意味は変わらない。
- 診断なしは `_attempt_loop(..., diagnostics=None)` が `tools/codex_worker_launch.py:1657-1666` に実在し、現行 spawn sample が診断条件内だけにあることも `:1706-1712,1793-1800` で確認できる。
- 受理集合については running poll が max wall を evidence より先に評価する `tools/codex_worker_launch.py:1841-1889`、accepted が limit 無しと complete evidence を要求する `:1608-1616`、checker が `actuals.wall_clock_s <= limit` を再検査する `:3268-3284` を確認した。予定差分だけで上限外の結果を受理する経路は見つからない。
- 全走は `pytest.ini:12-14` で `orchestrator/tests` を収集し、wrapper から launcher への転送は `tools/dev_wave_codex.py:237-240` にある。S2 の物理的 hard cap を除けば、成果物へ届く層は現 scope に入っている。
- read-only 制約に従い pytest は実走しておらず、緑とは報告しない。

## 総括

- 最も危険なのは S1 と S3で、誤った preflight 起点または retry だけ旧起点の実装が提案テストを通りうる。
- S2 は D498 の「総所要」を receipt admission scope と読むか、物理 hard cap と読むかの裁定が必要である。
- D498 の実装方向自体と、accepted receipt の既存 max-wall 関門は静的には維持されている。
- 現プランはそのまま採用不可。spawn 時間差と attempt 2 の判別を追加し、S2 と P3 の根拠を明文化した plan v2 なら採用可能。