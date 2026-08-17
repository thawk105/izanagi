pytest は未実走。以下は静的検査のみです。

### L1

- 主張: 判別テストの論理時計では、deadline を `preflight_now_ns` 起点にしても正実装と同じ結果になり、`spawn_completed` 起点を証明できない。
- 根拠: `plan.md:105`, `plan.md:107`, `plan.md:195`; `tools/codex_worker_launch.py:1765`, `tools/codex_worker_launch.py:1795`; `orchestrator/tests/test_codex_worker_launch.py:4260`
- 具体的な失敗シナリオ: 時計を spawn 完了まで 0.10 秒で固定するため、`preflight_now_ns + grace` や `read_pid_identity` 前のサンプルを使う変異でも `attempt_preflight=0.10`、`supervision_drain=0.05` となり、判別テストを通る。
- 重大度: must-fix。誤った起点の実装が受理集合へ入り、M1〜M4 の変異結果も誤って KILLED になる。

### L2

- 主張: この変更は preflight が猶予を消費する機序を除くだけで、F57 の非帰属赤が消えることまでは保証しない。
- 根拠: `brief.md:37`, `brief.md:42`; `F57-excerpt.md:26`, `F57-excerpt.md:32`; `tools/codex_worker_launch.py:1882`, `tools/codex_worker_launch.py:1889`
- 具体的な失敗シナリオ: `preflight=1.05`、spawn 後から rollout 出力まで `1.10` 秒、猶予 `1.0` 秒なら、新起点でも evidence が無いまま強制停止し、`limit_trigger` 無しの `max_attempts` に落ちる。F57 artifact には spawn 後遅延が無く、この可能性を排除できない。
- 重大度: must-fix。`evidence_forced_stop`、`limit_trigger`、writer の終端値、非帰属赤 3 件が残る可能性を「消える」と過大報告する。

### L3

- 主張: P2 の「既定値の意味は起点移動と独立」は誤りで、数値を変えなくても `max_wall_clock_s` との発火順が変わる。
- 根拠: `plan.md:181`, `plan.md:183`, `plan.md:189`; `tools/dev_wave_codex.py:28`, `tools/dev_wave_codex.py:150`; `tools/codex_worker_launch.py:1819`, `tools/codex_worker_launch.py:1855`
- 具体的な失敗シナリオ: `max_wall_clock_s=92` なら既定猶予は 90 秒。旧起点では時刻 90 秒で evidence 停止し、新起点で spawn が 3 秒後なら deadline は 93 秒となり、92 秒の max-wall が先に発火する。
- 重大度: should-fix。receipt の `limit_trigger`、`stop_reason`、`evidence_forced_stop`、場合によっては受理集合が変わるため、既定値を変更しない前提と発火順の変更を明記し、判別テストを追加すべきである。

### L4

- 主張: `1.0` 秒固定の既存 fixture は起点を判別せず、負荷時には evidence gate の検査自体を max-wall gate が置き換えうる。
- 根拠: `plan.md:156`, `plan.md:173`; `orchestrator/tests/test_codex_worker_launch.py:1630`, `orchestrator/tests/test_codex_worker_launch.py:2630`, `orchestrator/tests/test_codex_worker_launch.py:4173`, `orchestrator/tests/test_codex_worker_launch.py:4183`
- 具体的な失敗シナリオ: preflight が 2.2 秒、max-wall が 3 秒、no-rollout の場合、新起点の evidence deadline は 3 秒を越えるため max-wall が先に止める。missing だけを見る診断テストは通る一方、`evidence_forced_stop` を見るテストは別の理由で落ちる。
- 重大度: should-fix。既存テストの緑は evidence 起点の正しさを示さず、負荷時の受理・診断集合が不安定なまま残る。

### L5

- 主張: 意味検索で見つかった過去の説明文を、現行契約ではなく履歴として明示的に分類すべきである。
- 根拠: `docs/decisions.md:13139`, `docs/failures.md:2127`, `docs/decisions.md:20675`
- 具体的な失敗シナリオ: D286 の「既定 5 秒の evidence grace 内に起動イベントが出ない」という文だけを読むと、猶予の起点を attempt 作成時と誤解しうる。D498 は新起点を明記しているが、相互参照はない。
- 重大度: nit。コードや schema は変わらないが、将来のレビューで deadline 起点の参照が分裂する。

### 閉包・必須 seam の確認

- `state.started_ns` の deadline consumer は `tools/codex_worker_launch.py:1798` の 1 箇所。`wall_clock_s` の `tools/codex_worker_launch.py:2004`、診断の `attempt_elapsed_s_at` の `tools/codex_worker_launch.py:461` は別意味で変更不要。
- `phase_duration_s` は実際に `tools/codex_worker_launch.py:489` で出力され、sidecar の `attempts` へ `tools/codex_worker_launch.py:2796` で格納される。対象外の解析 consumer は見つからず、既存テストが主な reader。
- `FAKE_MODE=no_rollout` は `orchestrator/tests/test_codex_worker_launch.py:1403` にあり、in-process の `LAUNCHER.main` 呼出しは同 `:2420` と `:2433` にある。
- `_hook_checker.validate_installation` は実装側 `tools/codex_worker_launch.py:300`、既存 monkeypatch は `orchestrator/tests/test_codex_worker_launch.py:3318` と `:3464` にある。
- `_monotonic_ns` は `tools/codex_worker_launch.py:31` の seam で、論理時計への置換例は `orchestrator/tests/test_codex_worker_launch.py:3486` と `:4262` にある。
- P3 は妥当。`orchestrator/tests/test_frozen_artifacts.py:41` の manifest key は `output/` 配下で、`:239` でもその制約を検査している。
- `docs/dev-wave/**` への書込み提案はない。

## 総括

最も危険なのは L1 で、現在の判別テストは正しい起点を証明しない。  
L2 により F57 赤の消滅主張も過大である。  
L1 と L2 を修正し、L3 の発火順を裁定・テストへ反映するまで、プランは採用不可。