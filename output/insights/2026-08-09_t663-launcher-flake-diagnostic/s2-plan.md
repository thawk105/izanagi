結論として、実装対象は `orchestrator/tests/test_codex_worker_launch.py` 1枚で足りる。ただし (P1) の「失敗時も receipt がある」は preflight／publication failure では成り立たず、F57 再発済みの direct `Popen` test も `_run_case` を通らないため、その2点を補う。

## 1. 診断保存

対象: [test_codex_worker_launch.py:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/test_codex_worker_launch.py:332)

- `:421` の直前に `_launcher_failure_message(...)` と `_assert_launcher_returncode(...)` を追加する。
- `_launcher_failure_message` は launcher の expected/actual rc、captured stdout/stderr、receipt path/statusを先頭に置き、valid receipt の全 `attempts[*]` について次を載せる。

  - `limit_trigger`
  - `evidence_status`
  - `metering_status`
  - `process_group_residual`
  - `termination_verified`
  - `wall_clock_s`
  - `stdout_path` と全文
  - `stderr_path` と全文

- stream path は既知の `paths["artifact"]` 配下だけを読む。欠落・非文字列・配下外・読取不能は例外にせず `<missing>` / `<outside-artifact-dir>` / `<unreadable: ...>` とする。
- receipt 不在は `receipt_status=missing`、UTF-8/JSON不正・非object・`attempts` 非listは `receipt_status=invalid: ...` と raw receipt を載せる。診断生成例外で元の rc 不一致を覆わない。
- `:421-441` の `_run_case` に keyword-only `expected_returncode` を追加し、`:429-435` の `subprocess.run` 直後、既存の厳格な receipt load (`:436-440`) より前に `_assert_launcher_returncode` を呼ぶ。正常時は診断ファイルを再読しない。
- production が attempt stream をファイルへ向ける事実は [codex_worker_launch.py:1052](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/codex_worker_launch.py:1052) と `:1090-1097` に一致する。production 側の変更は不要。

現状 `_run_case` は33 syntactic call site、parametrize 展開後40 node。各呼出しへ期待rcを渡し、対応する既存 rc assert を削除する。

- rc=0、19箇所: `484→486`, `562→568`, `617→625`, `665→673`, `1155→1156`, `1170→1171`, `1212→1213`, `1252→1253`, `1281→1282`, `1302→1303`, `1317→1318`, `1385→1386`, `1520→1522`, `1602→1603`, `1675→1676`, `1698→1699`, `1713→1714`, `1740→1741`, `1758→1759`。
- rc=1、11箇所: `574→582`, `596→604`, `639→647`, `1441→1443`, `1458→1466`, `1478→1486`, `1499→1507`, `1583→1591`, `1622→1630`, `1642→1650`, `1662→1664`。
- rc=2、3箇所: `846→853`, `1567→1569`, `1827→1829`。
- `_paths` として捨てている `:562,665,1458,1478,1499,1520,1583,1602,1662` は `paths` へ改名する。

F57 再発済みの `test_manifest_is_appended_while_correlated_session_is_running` は direct `Popen` (`:1529-1561`) なので、`:1561` も同じ helper へ結線する。併せて direct launcher assertions `:542,714,808,836,876,901,921,949,1005-1006,1110,1333,1372,1375,1783` も機械的に同じ診断へ揃える。checker/help の rc assertions は launcher receipt 診断の対象外。

## 2. 予算

`_base_command` の現状は `max_wall="3"` (`:341`)、evidence `1.0` (`:403-404`)、termination `0.05` (`:405-406`)。

現行 assertion inventory は次のとおりで、期待値自体は一切変えない。

- `stop_reason`: `:489,584,606,627,649,675,715,809,837,1445,1493,1524,1632,1652,1666,1832`
- `limit_trigger`: `:586,608,632,653-655,678,717,812-813,1447,1470,1490,1512,1594-1596,1634`
- `evidence_status`: `:1526,1635,1654,1667`

据え置く集合:

- explicit `max_wall="3"`: call `:574,596,617,639,665,684,793,821,1458,1478,1499,1583,1622,1642`。
- version preflight の `max_wall="0.1"`: `:863-883`。
- external limit binding は `:1170` に `max_wall="3"` を明示追加し、`:1191` の期待 `"3"` を維持する。
- evidence deadline 自体を発火させる `:1622` と `:1642` は新設引数 `evidence_grace="1.0"` を明示する。
- `termination-grace-s=0.05` の数値そのものを検査する assert は現状ゼロ。SIGTERM/KILL、residual、PID消滅の意味的 assert は維持するが、数値は保護対象ではない。

広げてよい集合:

- `_run_case`: `:484,562,846,1155,1212,1252,1281,1302,1317,1385,1441,1520,1567,1602,1662,1675,1698,1713,1740,1758,1827`
- direct `_base_command`: `:528,891,911,931,972,978,1080,1083,1321,1346,1359,1533,1774`

提案値は通常 fixture の `max_wall="6"`、`evidence_grace="2.0"`、`termination_grace="0.2"`。brief の p90 0.671秒に対して wall は約8.9倍、薄かった evidence は2倍、termination は10ms poll相当で約5回から約20回へ増える。production の真理値表や各 protected test の trigger は変えない。

外側 harness は `timeout=10` のままにしない。通常予算を6秒へ広げる一方、termination・residual確認・receipt fsync・内部5秒 preflight timeout が後続し得るため、launcher invocation のみ `20` 秒へ上げる。順序を `evidence 2 < wall 6 < harness 20` と固定し、outer timeout が receipt rc より先に失敗形を `TimeoutExpired` へ変えるのを避ける。checker/help の `timeout=10` は据え置く。`:1542` の manifest待機3秒も通常 wall と同じ6秒へ合わせる。

## 3. 恒真でないことの固定

`:483` 前後へ meta-test を追加する。

- `_run_case(tmp_path, "no_token", expected_returncode=0, max_wall="3")` を `pytest.raises(AssertionError)` 内で実行する。
- `no_token` の実rcは1なので診断経路へ確実に入る。期待rcを既存テスト側で1へ緩める案は採用しない。
- message に `actual=1/expected=0`、指定6 fieldすべて、`evidence_status='complete'`、`metering_status='missing'`、stdout中の `"thread.started"`、空 stderr の明示があることを assert する。
- 別の小さな parametrized meta-test で receipt 不在と壊れたJSONを与え、`missing` / `invalid` が元の AssertionError 内へ出て二次例外にならないことも固定する。

## 4. 波及

- repository内の Python を静的検索した範囲では `_run_case`、`_base_command`、`_write_fake_codex` の他 test file からの import／利用はゼロ。変更は対象1枚に閉じる。
- 利用 fixture は pytest builtin の `tmp_path` と `monkeypatch` のみ。
- [conftest.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/orchestrator/tests/conftest.py:1) の TMPDIR方針は負荷機序に関係するが変更不要。
- autouse fixture `:99-119`, `:194-227` は当該 helper／envを扱わない。
- `REAL_REPO_SERIAL_NODES` (`:125-182`) に対象 node はなく、新meta-testも fake executable＋`tmp_path`のみなので追加しない。
- pytest はここでは未実走。実装後の焦点node、対象file全走、repository全走は親が `tools/run_tests.py` 経由で行う。

## 5. やらないこと・裁定候補

[tools/codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t663-flaky-truth-table/tools/codex_worker_launch.py:1) は一切編集しない。`accepted` の7条件、wall gate、receipt schemaも変更しない。

(P1) は「normal attempt がsealされたrc=1」には正しいが、preflight失敗、receipt公開失敗、direct `Popen` にはそのまま当てはまらない。上記test-side fallbackで本waveの目的は達成可能。もし「attemptが存在しない失敗にも6 fieldを必ず生成せよ」が要求されるなら、productionで早期receiptを設ける必要があり、それだけを別の裁定パッケージ候補とし、本計画には入れない。(P2) は支持する。(P3) の台帳上の統合・closeは実測後の親の記録段で裁定し、テスト変更へ混ぜない。

## 総括

- 変更は対象test file 1枚、productionはno-touch。
- `_run_case` 33 call siteへ期待rcを明示し、失敗時だけreceipt＋attempt stream全文を表示する。
- receipt不在・破損でも元のrc不一致を診断生成が覆わない。
- F57再発済みのdirect `Popen` assertionも同じhelperへ結線する。
- budget検査16 callは現行値を固定し、それ以外を wall 6 / evidence 2 / termination 0.2へ広げる。
- launcher harnessは20秒とし、内側予算より短いouter timeoutを作らない。
- `no_token` の意図的な期待違反で診断経路が恒真でないことを固定する。
- pytest結果は主張せず、全実測を親へ残す。