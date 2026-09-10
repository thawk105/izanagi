所見 1: M03 の報告 node は production の phase 配線を通らず、終了時一括サンプル変異が生存する

- 分類: `恒真化`
- 深刻度: Major
- 根拠: [test_codex_worker_launch.py:3531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3531) は `AttemptDiagnosticsState` を直接生成し、[同:3548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3548) でテスト自身が `attempt.note_boundary(name, index * 1_000_000_000)` を注入している。production run を通る正例も [同:3236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3236) で key 集合しか検査せず、duration の値を検査しない。
- 根拠: production の自然終了経路では [codex_worker_launch.py:1783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1783) の `now_ns` を取得した後、[同:1788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1788) でもう一度 `observe(register_manifest=True)` を実行するが、[同:1872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1872) は古い `now_ns` を `supervision_drain_completed` として記録する。現状でも final drain の時間が process reap 側へ誤帰属する。
- 失敗シナリオ: production の全 `note_boundary` を attempt 終了時に同一時刻で一括設定する → `test_launcher_diagnostics_phase_durations_use_distinct_boundaries` はテスト自身が別時刻を注入するため緑、正例も全 key が存在すれば緑 → 実 sidecar の全 duration が 0 または誤帰属でも通る。
- 提案: production 経路を通す node を新設し、制御された clock で各 phase の exact duration を検査する。自然終了時の `supervision_drain_completed` は二度目の `observe` 完了後にサンプルする。

所見 2: 段 5 の M01〜M14 検出 node 一覧は M03 が生存し、ほかにも完全失敗集合の欠落がある

- 分類: `変異帰属`
- 深刻度: Major
- 根拠: 段 5 報告 [stage5-impl.md:68](/work/1/SFC/tanab/dev-wave-jobs/wave-t190-launcher-failure-artifact/stage5-impl.md:68) は各変異へ node を一つずつ割り当てるが、実際の assert は複数 node に分散している。DW-M08 の期待 node は完全集合でなければならない。
- 失敗シナリオ: 報告一覧をそのまま mutation spec にする → M02、M04、M05、M06、M11、M14 は報告外 node も落ち、M03 は報告 node が落ちない → exact node 照合が成立せず、検出力を正しく帰属できない。
- 提案: 以下の静的帰属を基に spec を作り直し、親が実走で完全失敗集合を確定する。

| ID | 静的判定 |
|---|---|
| M01 | 報告 node は落ちる。`AttemptState` の True が [codex_worker_launch.py:1996](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1996) で sidecar へ写り、[test:3235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3235) が False を要求する。 |
| M02 | 報告 node に加え、`test_positive_p3_exact_limit_natural_exit_is_accepted`、`test_launcher_diagnostics_records_all_conditions_and_site_values`、2 本の wall-overrun node も落ちる。 |
| M03 | 報告 nodeは落ちない。所見 1 の production 配線 node が必要。 |
| M04 | 報告 nodeに加え、[test:3466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3466) `test_unknown_residual_source_propagates_through_terminate` も落ちる。 |
| M05 | live wiring に加え、[test:1407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1407) の属性 test も落ちる。段 4 の「直接単体 node は緑」という事前登録とも不一致。 |
| M06 | `shutil.copyfile(...)` を no-op にするなら、報告 nodeのほか collision、copy-error、live-wiring node も落ちる。変異 anchor を一意に固定する必要がある。 |
| M07 | 報告された collision node で落ちる。 |
| M08 | [test:4401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:4401) が sealed/foreign の両方を要求するため落ちる。 |
| M09 | 報告 node は [test:1464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1464) で落ちる。 |
| M10 | anchor が二重 catch のどちらか不明で、単一理由性を確認できない。所見 3 参照。 |
| M11 | 報告 node以外に [test:3519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3519) と [同:5231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:5231) も落ちる。 |
| M12 | 報告 node は短い stat に対して落ちる。ただし ValueError 型 malformed は所見 6 の未被覆がある。 |
| M13 | 報告 node は [test:1470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1470) で落ちる。 |
| M14 | 報告 nodeに加え、[test:3578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3578) も落ちる。 |
| P01 | 有効。sidecar publisher の OSError 下で rc、accepted、receipt exact bytes を検査している。 |

M06/M09/M13 は一つの総合 node に縮約せず、少なくとも `test_failure_archive_copies_exact_bytes_from_new_root`、`test_failure_archive_writes_path_map`、`test_failure_archive_appends_index` に分割すべきである。

所見 3: M10 の test は実 pytest failure の保持を検査せず、hook が archive 例外を伝播する変異でも緑になりうる

- 分類: `例外安全`
- 深刻度: Major
- 根拠: [test_codex_worker_launch.py:1553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1553) は `original = AssertionError(...)` を生成するだけで raise せず、[同:1555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1555) で `_archive_launcher_failure_without_masking` を直接呼ぶ。pytest hook 経路は通らない。
- 失敗シナリオ: plugin の [同:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:342) を `_archive_launcher_failure(...)` の直接呼出しへ変える → 現 test は wrapper を直接検査するため緑のまま → 実 call-phase failure では archive の OSError が hook から逃げ、元の assertion を pytest internal error で上書きする。
- 提案: archive destination を意図的に失敗させる子 pytest を起動し、出力が元の `LauncherReturncodeMismatch` のままで `INTERNALERROR` にならないことを検査する live exception-safety node を新設する。内側の copy omission 検査と外側の原 failure 保持を分離する。

所見 4: signal 観測が共有 module の `os` を一時置換し、並行実行で制御と帰属を壊す

- 分類: `制御フロー`
- 深刻度: Major
- 根拠: [codex_worker_launch.py:1462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1462) は `original_os = _worker_module.os` の後、[同:1463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1463) で process-global な `_worker_module.os` を wrapper に置換し、finally で復元する。lock も呼出し単位の注入もない。
- 失敗シナリオ: 同一 interpreter の thread A/B が同時に forced stop → B が A の wrapper を包み、A が途中で plain `os` に戻す → B の後続 signal が未記録になり、B の finally が A の wrapper を再配置する → 後続 launcher の signal が A の sidecar へ誤帰属する。termination helper の参照先も実行途中で変わる。
- 提案: module global を置換しない observer 注入 API を `worker.py` 側へ追加する裁定を得るか、同じ制御を局所実装する。少なくとも二つの forced-stop run を同一 interpreter で並行させ、signal 帰属と `_worker_module.os` の identity 復元を検査する。

所見 5: `termination_initiated_by_launcher` は signal 送信前に True となり、「実際に送ったか」を誤記録する

- 分類: `整合`
- 深刻度: Major
- 根拠: [codex_worker_launch.py:1877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1877) と [同:1927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1927) は `_terminate` 呼出し前に `termination_initiated_by_launcher = True` とする。一方、実 signal は [同:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1450) または [同:1487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1487) 以降で、既に process/group が消えていれば送られない。
- 失敗シナリオ: limit を検出した直後に child が自然終了 → forced-stop 分岐へ入るが signal は一つも送られない → sidecar は `termination_initiated_by_launcher=true`、`termination_signals_sent=[]` → 外部終了と launcher 自身の強制停止を分離する B2 の主目的に反する。
- 提案: successful signal callback 内でのみフラグを立てるか、フラグを `bool(termination_signals_sent)` から生成する。forced-stop 分岐へ入ったが process が既に終了しており signal 0 件、という負例を追加する。

所見 6: 数値 parse failure は malformed stat なのに `proc_stat_malformed=false` のままになる

- 分類: `整合`
- 深刻度: Minor
- 根拠: 短い fields は [codex_worker_launch.py:1391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1391) で `on_malformed()` を呼ぶが、`int(fields[2])` の ValueError は [同:1409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/codex_worker_launch.py:1409) で `on_unknown("proc_stat_parse_error")` だけを呼ぶ。対応 test [test:3372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:3372) も reason だけを検査し、malformed flag を見ない。
- 失敗シナリオ: `/proc/<pid>/stat` の process-group field が非整数 → residual は従来どおり None、reason は `proc_stat_parse_error` だが `proc_stat_malformed=false` → 段 5 報告の「malformed stat を診断へ記録」が部分的に偽になる。
- 提案: ValueError 経路でも `on_malformed()` を呼び、既存の None/count 意味は変えない。同じ node で reason と malformed flag の双方を assert する。

所見 7: 4096 files 上限は directory と後続探索を数えず、退避処理全体を bounded にしていない

- 分類: `例外安全`
- 深刻度: Major
- 根拠: [test_codex_worker_launch.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:151) は directory を無条件で作成・再帰し、`files_seen += 1` は [同:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:168) の非 directory 経路だけである。さらに copy 後、[同:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:275) が `list(tmp_path.rglob(...))` で無制限に全 tree を再走査する。
- 失敗シナリオ: tmp_path に 100万個の空 directory または深い directory tree がある → `files_seen` は 0 のまま全 directory を走査・作成し、さらに rglob で再走査 → 4096 files cap を満たしたとの metadata にならず、長時間停止や RecursionError で `.complete` が残らない。
- 提案: directory を含む全 entry 数を上限へ算入し、上限到達時は subtree omission を一件記録して descent を止める。`diagnostics_present` は bounded traversal 中に集計し、後段の unbounded `rglob` を削除する。directory-heavy 負例も追加する。

不変条件 1〜7 の逐条照合結果:

1. production の limit 値・parser 既定・比較述語に差分なし。
2. `accepted` 式、`_LIMIT_REASONS`、優先順位、`_writer_truth`、receipt/attempt field 集合、checker rc に直接差分なし。
3. fixture の wall/evidence/termination/poll と既存外側 timeout 10 秒に緩和なし。
4. 既存期待値の反転、skip、削除は確認されなかった。
5. break、terminate/normal-reap の選択順、receipt 公開順は直接変更されていない。sidecar は `_run` の finally で公開後に書かれ、fsync もない。ただし所見 4 の共有 global 置換は制御上の新規危険。
6. 監視 loop 内の純増は `_record_limit_conditions` の in-memory 更新で、ファイル I/Oや追加 clock syscallはない。phase 境界の正確性は所見 1。
7. `_group_member_count` の返す数値意味は維持されている。診断 flag の不整合は所見 6。

live wiring は実 hook 経由である。[test:1710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1710) が子 pytest を起動し、probe が rc mismatch を発火させ、外側が `.complete` と sentinel bytes を検査する。archive 正例も [test:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1450) で root 不在から開始し、[同:1456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/orchestrator/tests/test_codex_worker_launch.py:1456) で実 copy bytes を読むため、単純な copy no-op では緑にならない。

pytest・mutation は実走していない。指定 3 文書の全文、2 file の全 diff、および変更 hunk 周辺だけを静的に確認した。

## 総括

所見 7 件。受理式そのものの緩和は見つからなかったが、M03 は恒真、mutation node 集合は不正確、signal 観測と終了主体の診断には誤帰属経路がある。この状態で「M01〜M14 の単一理由性確認済み」「次回再発を帰属可能」として commit するのは早い。