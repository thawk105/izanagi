# レンズ B：実効性と層の網羅

指定資料をすべて静的に読了しました。テスト実走・変異実走は行っていません。brief の 4 秒観測は「親実測」としてのみ引用します。

## 所見 B-1：現行 dev-wave の成果物採用経路は gate を通らない

**主張:** `tools/codex_worker_launch.py` を修正しても、現行 dev-wave の子成果物採用は保護されない。

**根拠:**

| 経路 | gate | 状態 |
|---|---|---|
| `tools/codex_worker_launch.py` | 通る | `codex exec` は `tools/codex_worker_launch.py:1098-1113,1161-1168` |
| 現行 `DW-O01` | 通らない | raw `codex exec`、`.done`、exit code、`check_codex_output` で採用 (`docs/dev-wave/operations.md:6-13`) |
| `tools/run_codex_role.py` → `orchestrator/codex_roles/launcher.py` | 通らない | direct `codex exec` (`orchestrator/codex_roles/launcher.py:622-638,699-711`)。ただし現在は `run_role` が必ず BLOCKED (`:1086-1112`) |
| `tools/codex_reasoning_ab.py` | 通らない | 独自の Codex 起動・成果物記録 (`tools/codex_reasoning_ab.py:1800-1821,1991-2003,2031-2038`) |
| `tools/dev_waves/worker.py` | 対象外 | fake-only child (`tools/dev_waves/worker.py:1,231-251`) |
| `dispatch_compute` | 直接 caller ではない | task enum は tests/provenance のみ (`tools/pegasus/dispatch_compute.py:56-72,546-590`) |

親 brief 自身も production caller 不在を認めています (`s1-brief.md:67-74`)。

**影響:** 現時点で gate が守るのは dogfood receipt と、将来 `DW-O01` を launcher 経由へ集約した場合だけです。「全 dev-wave 子成果の採用条件」とは主張できません。`check-receipt` も既存 receipt の再監査に過ぎず、raw 経路を結線しません (`tools/codex_worker_launch.py:2420-2452`)。

**提案:** 次を独立した裁定パッケージ候補に分けるべきです。

- `DW-O01` を launcher 経由へ集約し、`.done`・output checker・receipt を E2E で結ぶ。
- `codex_reasoning_ab.py` と role launcher を「全 Codex 起動層」に含めるか明示裁定する。
- 外部 shell/CI caller は repo 内静的検査の scope 外として明記する。

## 所見 B-2：親の 4 秒観測は、10〜20 秒級や F57 原因への一般化を支えない

**主張:** 親の観測は「現行 gate が `_stage_receipt_write` の入口より前にある」という局所的な positive control であり、10〜20 秒級の実障害や F57 の原因同一性は示さない。

**根拠:** 親の注入・結果は `s1-brief.md:13-20` の 4 秒 sleep、`max_wall="3"`、外側 timeout 10 秒です。現行の gate は `tools/codex_worker_launch.py:1739`、stage と final publication は `:1751-1761` にあります。一方、F57 は 32/48 worker の全走で発生し、単独再走では再現しない (`docs/failures.md:1349-1369,1414-1424,1448-1462`)。F57 には launcher、git、PBS、共有 checkout 競合など複数 producer が混在します (`docs/failures.md:1397-1437`)。

**影響:** `[構成例・未実測]` 12 秒の stage/publication は現行 test helper の timeout 10 秒 (`orchestrator/tests/test_codex_worker_launch.py:528-543,555-575`) に先に捕捉され、4 秒観測からは推論できません。また sleep は Python thread を止めるだけで、`write`、file fsync、`os.link`、parent fsync、lock contention と同じ障害機序ではありません。

**提案:** 親が次を別々に測るまで、「10〜20 秒級を塞いだ」「F57 を説明した」とは書かないでください。

- stage の serialize/write/fsync。
- final `link/replace` と parent directory fsync。
- lock close/unlock。
- 4、9、12 秒相当と outer timeout 10 秒の境界。
- 32/48 worker・共有 node の実 receipt と stop reason。

## 所見 B-3：P1/P1′ は「publication 完了後」の字義を満たさない

**主張:** P1′ は「最終 receipt path 公開直前の gate」であって、brief の publication 完了後 gate ではない。

**根拠:** brief の依頼は publication 後再評価です (`s1-brief.md:3-6`)。P1 自身が atomic create 後の取消不能を認めています (`s1-brief.md:40-46`)。P1′も gate 後に `os.link`/`os.replace`、parent fsync、temp cleanup、lock release、return が残ると明記しています (`s2-plan.md:27-41`)。実装上もこれらは `tools/codex_worker_launch.py:452-472,319-325,438-442` にあります。

**影響:** `[構成例・未実測]` final `os.link`、`os.replace`、directory fsync が 10〜20 秒停止すると、receipt はすでに consumer から読める状態になり、`accepted` のまま残ります。P1′の gate はその停止を見ません。これは単なる微小な残余ではなく、依頼の中心経路です。

**提案:** いずれかを明示的に裁定してください。

- create-only 制約を維持し、scope を「prepublication admission」に格下げする。
- final publication を含む commit/admission protocol を別途設計する。
- P1′を T-678 の実装案とするなら、brief の「publication 完了後」という表現と成果物影響の主張を撤回する。

## 所見 B-4：`wall_clock_scope` と実際の記録値・gate 時点がずれる

**主張:** P2 の「literal は真のまま」という主張は不十分です。プランの順序では、gate が観測する時刻と receipt の `actuals.wall_clock_s` が別の時刻になります。

**根拠:** `actuals.wall_clock_s` は `_receipt` 構築時に計算されます (`tools/codex_worker_launch.py:1396-1399`)。P1′の順序は receipt staging の後に latch し、accepted の場合は同じ staged bytes を公開します (`s2-plan.md:79-102`)。つまり accepted のままなら、stage 時間を含まない古い `actuals.wall_clock_s` が保存されます。checker は保存済み値だけを検査し、実経過時間を再測定しません (`tools/codex_worker_launch.py:2105-2121`)。

**影響:** `[構成例・未実測]` stage が 2 秒掛かっても max wall 3 秒以内なら、receipt の `actuals.wall_clock_s` は stage 前の値のままになり得ます。final publication 停滞ならさらに過少記録です。人間には `accepted / completed / rc=0` と低い wall 値しか見えず、gate が別の時計で発火した事実は残りません。非 accepted candidate は wall 再評価しない設計 (`s2-plan.md:104-112`) のため、後段停滞が既存の `max_attempts` 等に埋もれる経路も残ります。

**提案:** `actuals.wall_clock_s` を「receipt object 構築時」と定義するのか、「staged bytes fsync 完了時」と定義するのかを固定し、必要なら admission 時刻を別 field にするべきです。module doc、help、receipt、validator、D100 (`docs/decisions.md:4422-4457`) も「final path publication は含まない」と明記してください。

## 所見 B-5：flip 以外の停止では、人間向け診断が消える

**主張:** staging 遅延が gate を通過して flip する場合は診断できるが、publication exception、outer timeout、非 accepted 経路では原因が失われる。

**根拠:** P1′の想定 flip は `limit_trigger=max_wall_clock_s`、`accepted=false`、`outcome=not_accepted`、`stop_reason=max_wall_clock_s`、`launcher_rc=1`、output 不在です (`s2-plan.md:116-136`)。一方、例外時の receipt は `launcher_error/rc=2` に再構築されるだけで、例外原因を receipt field に保存しません (`tools/codex_worker_launch.py:1765-1829`)。production の stderr は単に `NG: ...` です (`tools/codex_worker_launch.py:2582-2587`)。test 側の詳細な `failed_predicates` は `orchestrator/tests/test_codex_worker_launch.py:169-219,291-336` にしかありません。

**影響:** `[構成例・未実測]` fsync が例外になれば、receipt は generic `launcher_error` になり、最初の「どの publication 操作が失敗したか」は receipt から分かりません。10 秒超の hang なら receipt 自体が無くなり、test diagnostic は `receipt_status=missing` になります (`orchestrator/tests/test_codex_worker_launch.py:222-258`)。raw `DW-O01` ではこれらの診断 receipt も採用判定に使われません。

**提案:** finalization phase、wall observation point、publication operation を少なくとも bounded な診断 artifact に残してください。preflight/publication 失敗で receipt が無い経路は、S4 の S5 (`s4-adjudication.md:69-79`) として別裁定にするべきです。

## 所見 B-6：P3 の durable cleanup は exception 経路を覆わない

**主張:** P3 が親 directory fsync を加えるのは通常の accepted→not_accepted flip だけで、例外 fallback の output 削除は durable ではない。

**根拠:** P1′は flip 時に output directory fsync を要求します (`s2-plan.md:90-100`)。しかし既存の `_publish_launcher_error_receipt` は output を unlink するだけです (`tools/codex_worker_launch.py:1777-1782`)。新 staged temp の所有は呼出側へ移るため、stage 後 latch 前の例外を含む `finally` 契約も明示的に実装する必要があります (`s2-plan.md:47-62`)。

**影響:** `[構成例・未実測]` output unlink と fsync の間に process crash が起きると、同一 process 中は output 不在でも、再起動後の filesystem 状態は保証されません。race loser や publication failure で temp が残れば、receipt slot や後続診断も汚染されます。既存テストは `exists()` と receipt outcome だけを見ています (`orchestrator/tests/test_codex_worker_launch.py:2077-2104,2235-2309`)。

**提案:** staged temp を所有する scope object または明示的 `try/finally` を置き、flip・exception・race の全 output unlink で parent fsync を行ってください。temp 残骸、lock、output directory の状態を検査する test を追加し、crash durability は未検証として記録してください。

## 所見 B-7：テストの clock monkeypatch は正規 seam ではなく、実障害を注入していない

**主張:** 新 node 1 は gate の論理分岐を検査できますが、実際の停滞・outer timeout・xdist 影響を検査できません。

**根拠:** プランは production clock seam を追加せず、`LAUNCHER.time.monotonic_ns` を wrapper で変更するとしています (`s2-plan.md:168-181`)。対象 production は複数箇所で直接 `time.monotonic_ns()` を呼びます (`tools/codex_worker_launch.py:1397-1399,1603-1617,1641-1643,1691-1694`)。既存 in-process helper は `LAUNCHER.main` を同一 pytest process で実行します (`orchestrator/tests/test_codex_worker_launch.py:1073-1094`)。outer timeout は 10 秒のままです (`s2-plan.md:216-220`)。

**影響:** `LAUNCHER.time` は共有された Python の `time` module なので、monkeypatch の有効期間中は同一 pytest worker 内の他コードにも影響し得ます。[構成例・未実測] pytest plugin や補助 thread が `monotonic_ns` を使う場合、診断・timeout の時刻が変わります。fake offset は fsync、lock、I/O blocking を再現せず、12 秒 stall は in-process test では外側 timeout を通りません。

**提案:** launcher に限定した clock callable を注入し、論理時計テストと実 I/O seam テストを分けてください。`-n 2`、direct `Popen`、`TimeoutExpired`、publication exception を別々に検査し、timeout を 20 秒へ広げない現行裁定は維持すべきです。

## 所見 B-8：親の段 4 変異は、publication gate の検出力を測れない可能性が高い

**主張:** 提案された 2 node は staging latch と temp write 再利用しか測らず、最重要の final publication と receipt scope の変異を検出できません。

**根拠:** node 1 の期待値は stage 後 flip (`s2-plan.md:168-193`)、node 2 は `_write_json_temp` 呼出回数 1 回 (`s2-plan.md:195-203`) です。既存テストは output 不在や race を確認しますが、receipt wall の測定時点や durable deletion は確認しません (`orchestrator/tests/test_codex_worker_launch.py:1630-1655,2077-2104,2235-2309`)。T-663 の M1/M2/M3 (`s4-adjudication.md:81-94`) は診断用の別 wave の変異で、M3 は既存テスト自体が赤になる想定です。

**影響:** `[構成例・未実測]` 次の変異は生き残り得ます。

- latch 後に `_receipt` を再構築しない。
- `actuals.wall_clock_s` を stage 前の値のままにする。
- final `link/replace`・parent fsync の遅延を gate 対象外にする。
- flip 後の output directory fsync を削る。
- `output_published_by_run=False` の復元だけを削る。
- P4 の再 staging 後に wall reason を更新しない。

逆に helper signature の破壊や「常に not_accepted」は既存テストだけで赤になり、新テストの純増検出力を示しません。

**提案:** 段 4 では T-678 専用に、HEAD が通り新テストだけが落ちることを期待する変異を登録してください。最低限、stale wall field、cleanup flag、parent fsync、stage後 latch、publication後遅延を別 ID に分ける必要があります。実際の kill 結果は未実測です。

## 所見 B-9：偽陽性の発生率は、現資料からは見積もれない

**主張:** 新 gate が既存 job を何件落とすかを、現在の根拠から数値化することはできません。

**根拠:** production CLI は `--max-wall-clock-s` を必須とし、production の既定値はありません (`tools/codex_worker_launch.py:2475-2486`)。`max_wall="3"` は test fixture の値です (`orchestrator/tests/test_codex_worker_launch.py:934-946`)。成功 receipt 84 件の median 0.428 秒、p90 0.671 秒は login node の単独寄り母集団であり、F57 は高並列全走で発生しています (`docs/failures.md:1477-1492`)。F57 の失敗 receipt は保存されず、3 秒超過も原因確定していません (`docs/failures.md:1351-1359`)。

**影響:** 現行 dev-wave の raw 経路にはこの gate が無いため、現在の dev-wave 子の追加 rejection は repo 内では 0 件です。一方、将来 launcher 経由へ切り替えた場合、`[構成例・未実測]` worker 自体は 2.8 秒で完了しても共有 filesystem の stage が 0.4 秒掛かれば rc=1 になります。これは契約上の正当な拒否とも、運用上の偽陽性ともなり得るため、予算意味の裁定なしには率を出せません。

**提案:** 予算値を変えず、attempt seal、output publish、audit、stage、final publication の各時点を同じ 32/48 worker 負荷で記録してください。F57 を「改善した」「悪化させた」と判断するには、失敗 receipt と stop reason の保存が先です。 s4 の R6 (`s4-adjudication.md:5-23`) に反する fixture 拡大は行うべきではありません。

## 総括

1. 最重：現行 `DW-O01` は raw 経路で、production gate は dev-wave の採用集合に効かない。  
2. 最重：P1′は final publication 後 gate ではなく、10〜20 秒級の final link/fsync は残る。  
3. 最重：P2 は gate 時刻と receipt の `actuals.wall_clock_s` を一致させていない。  
4. 親の 4 秒観測は局所的 positive control であり、F57 原因や 10〜20 秒への一般化は不可。  
5. 判定：**NO-GO**。caller 結線、scope/receipt semantics、finalization cleanup、専用変異を裁定・補強してから実装すべきです。