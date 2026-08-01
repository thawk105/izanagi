現状のままの land は不可です。規律 2・3・6 に直結する scope 内の land stopper が 3 件あります。特に「既存 pipeline の受理集合は変わらない」という親 brief / 段 2 の結論は成立しません。

本監査は静的読取りと既存 receipt の再照合だけです。pytest、build、実計測は実行しておらず、緑を主張しません。

表記は `real / refuted`、`scope 内 / scope 外` です。

## Land を止める所見

### LB-1 — 規律 3 の構造化失敗理由が次の生成へ届かない

**real / scope 内 / land stopper**

既存 pipeline は verifier の anomaly、依存種別、workload 等を構造化して WAL に保存します。[pipeline.py:589](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/pipeline.py:589)

supervisor はその digest を critic には渡しますが、[p3_autonomous_workload_trial.py:806](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:806)、critic の `attribution/recommend/avoid/uncertainty` を全て捨て、次世代へ残すのは `reverse_recommended` の boolean だけです。[p3_autonomous_workload_trial.py:831](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:831)

次の planner/coder が受ける whiteboard も、`direction/magnitude/result/delta_pct` だけに落とされます。[p3_s4_loop.py:258](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_s4_loop.py:258) [p3_autonomous_workload_trial.py:667](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:667)

したがって以下が消えます。

- verifier がなぜ壊れたかという依存・anomaly 情報
- auditor の `violations`、`nits`、`proposed_tests`
- critic が構造化した修正指針と不確実性

これは「pass/fail に潰さず、なぜ壊れたかを次の LLM 生成入力へ渡す」という規律 3 の直接違反です。次世代が同型の誤りを繰り返し得るため、記録だけ残ることでは代替できません。

### LB-2 — 独立 auditor を無効化できる二つの実行経路

**real / scope 内 / land stopper**

1. `fixture + build` が CLI で禁止されていません。

`--provider fixture` と `--no-build` は独立 flag です。[p3_autonomous_workload_trial.py:1012](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:1012) `--no-build` を付けなければ実 build へ進みます。[p3_autonomous_workload_trial.py:1048](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:1048)

fixture auditor は入力を監査せず、渡された digest をコピーして無条件 `pass` を返します。[p3_autonomous_workload_trial.py:335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:335)

現 fixture coder の固定候補自体は安全側ですが、「実計測は独立 auditor 必須」という防壁は機械的に失われています。将来 fixture 値が変わっても止まりません。

2. `--claude-executable` は任意バイナリを受理します。

CLI flag は任意 path を許し、[p3_autonomous_workload_trial.py:1020](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:1020)、provider は解決したバイナリを hash しますが承認済み hash との照合をしません。[claude_projected_provider.py:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/claude_projected_provider.py:110)

任意バイナリは、Opus/token/session/tool-use の形だけ整えた envelope と、coder/auditor の任意応答を返せます。auditor payload 自身に `diff_digest` が入るため、偽 auditor は正しい digest をそのまま反射できます。

例えば `izanagi_gate_pass = false;` は、静的には一行 parser、DiffQuarantine、5 個だけの禁止識別子検査に掛かりません。[p3_autonomous_workload_trial.py:235](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:235) [p3_s4_loop_trigger_gating.py:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_s4_loop_trigger_gating.py:102) しかし `kUnset must always evaluate true` には明白に違反します。これを止める load-bearing な層は semantic auditor だけであり、その auditor が交換可能です。legacy/S2 が backoff 方針違反を必ず観測する保証もありません。

さらに public `run_trial()` は `providers/drive/preview` を注入でき、report の `provider` 表示との整合検査もありません。[p3_autonomous_workload_trial.py:841](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:841) これは CLI より狭い programmatic 経路ですが、同じ「正式 supervisor」APIとして露出しています。

### LB-3 — 探索 run を公式 proof-chain namespace へ書く

**real / scope 内 / land stopper**

supervisor は自分を `exploratory-ycsb-abc`、`scientific_claim=false` と記録します。[p3_autonomous_workload_trial.py:400](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:400) [p3_autonomous_workload_trial.py:575](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:575)

ところが build 有効時は通常の `campaign_layout()`、すなわち `output/campaigns/` を使います。[p3_autonomous_workload_trial.py:631](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:631) [layout.py:214](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/layout.py:214)

現 main の D65 は探索を `output/exploration/campaigns/` へ分離すると明記し、[decisions.md:2474](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/decisions.md:2474)、非継承の専用 `ExplorationCampaignLayout` まで実装済みです。[layout.py:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/layout.py:223) `output/campaigns/*/runs` は COMMIT/fitness の公式 proof chain です。[output/README.md:46](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/output/README.md:46)

外側 report の `scientific_claim=false` は pipeline に読まれません。legacy+S2 を通れば通常の certified/COMMIT が記録されます。[pipeline.py:700](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/pipeline.py:700)

したがって親 brief の「certified 選択・proof chain は不変」と、段 2 の「official selector 登録がないから不変」は過小評価です。自動登録がなくても、path/type 境界そのものを破っています。

## 規律 2 の gate 経路

| 仮判定 | 範囲 | 経路 |
|---|---|---|
| **real** | scope 内 | `fixture + build` で独立 auditor が無条件 pass へ置換される |
| **real** | scope 内 | 任意 `--claude-executable` が coder/auditor/envelope を同時に偽装できる |
| **real** | scope 内・programmatic | `providers/drive/preview` 注入で authoritative path と report 表示を分離できる |
| **refuted** | scope 内 | 通常の `drive_iteration` は DiffQuarantine、禁止識別子、digest、auditor verdict を再検査する。[p3_s4_loop_trigger_gating.py:276](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_s4_loop_trigger_gating.py:276) |
| **refuted** | scope 内 | supervisor の pre-audit reject は gate を飛ばさない。後段 drive でも uncertain verdict が reject される |
| **refuted** | scope 内 | `--no-build` は build/legacy/S2/bench を省くが `dry-pass` に限定され、docs も correctness 証拠でないと明記している |
| **refuted** | scope 内 | 例外 handler は成功へ変換せず partial report に落とす |
| **real** | scope 内 | formal oracle gate は通らない。探索だから oracle 受理集合へ入らない、という説明なら正しいが、親 brief の「oracle を含む唯一経路」は誤り |

`_preview()` が既存 preview を再実装する点も real です。[p3_autonomous_workload_trial.py:453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:453) authoritative drive が再検査するため受理集合は広げませんが、branch D99 の「supervisor は再実装しない」 (`codex/p3-autonomous-trial:docs/decisions.md:4393`) には反します。

## 主張された保証の裏取り

| 主張 | 仮判定 | 裏取り |
|---|---|---|
| runtime `tools=[]`、空 MCP、slash/settings 無効 | **real：設定は存在 / real：runtime 保証は未証明 / scope 内** | inline agent、argv、空 MCP は実装済み。[claude_projected_provider.py:134](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/claude_projected_provider.py:134) ただし実 CLI を起動するテストはなく、`observed_tool_events=[]` は観測でなく定数です。[claude_projected_provider.py:280](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/claude_projected_provider.py:280) |
| session id 再利用拒否 | **real：保証不足 / scope 内** | set は provider instance ごと。[claude_projected_provider.py:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/claude_projected_provider.py:153) 4 role は別 provider なので role 横断重複を拒否しない。検査途中で失敗した session id も set へ入らない |
| 主 model = Opus 一意、正 token | **real：過大主張 / scope 内** | Opus prefix が一個あり、その record の token が正であることだけを検査。[claude_projected_provider.py:239](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/claude_projected_provider.py:239) 他 model は禁止しない。v3 の実 envelope 12 件中11件は `claude-haiku-4-5-20251001` と `claude-opus-5` の併記だった。どちらが結果を生成したかは attest されない |
| server tool use=0、permission denial=[] | **refuted（狭義）/ scope 内** | envelope 検査は実在。[claude_projected_provider.py:221](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/claude_projected_provider.py:221) v3 receipt も12件全て zero/empty。ただし server counter は local/client tool 全体の証明ではない |
| env allowlist が5変数だけ | **refuted / scope 内** | import 元は正確に `PATH/HOME/LANG/LC_ALL/TERM`。[s8b_prediction_runner.py:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/s8b_prediction_runner.py:70) provider もその集合だけを射影する |
| planner→coder は3 fieldだけ | **refuted / scope 内** | current code の `planner_direction` は3 fieldだけ。[p3_autonomous_workload_trial.py:694](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:694) v3の3 payloadにも justification/uncertainty は無かった。ただし coder は別経路の whiteboard/common payloadも受ける |
| role attempt 1回、retryなし | **refuted（production provider）/ scope 内** | `_invoke()` は provider を一度だけ呼び、retry loopなし。[p3_autonomous_workload_trial.py:523](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:523) 注入 provider 内部の再試行までは検査しない |
| performance target 早期停止なし | **refuted（狭義）/ scope 内** | 数値 threshold はない。ただし既存 `converged/reverse-exhausted` stop はあり、critic は performance metrics を見て reverse を返せる。[p3_s4_loop.py:291](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_s4_loop.py:291) よって report の `fixed_generations=True` / `performance_early_stop=False` は意味が広すぎる |
| 競合検査・pinned disposable worktree | **refuted（CLI）/ scope 内** | CLI build path は事前競合検査後、pinned checkout を使う。[p3_autonomous_workload_trial.py:1039](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:1039) direct `run_trial(do_build=True)` にはこの外側 preflight/worktree 保証がない |
| numactl のない host で実計測停止 | **refuted：最終的には停止 / real：起動前検査なし / scope 内** | driver は `["numactl","--interleave=all"]` を固定使用。[p3_s4_loop_trigger_gating.py:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_s4_loop_trigger_gating.py:78) 空 command へ差し替える CLI はなく、不在なら subprocess 起動失敗で partial になる。ただし supervisor 自身に `which numactl` 等の起動前 gate はない。insight の停止は operator 判断であってコードの preflight 発火ではない |

別の real な説明違反として、`max-wall-seconds` は supervisor 全体の hard 上限ではありません。時間確認は workload/generation 境界だけです。[p3_autonomous_workload_trial.py:655](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:655) 一回の Claude 呼び出しだけで最大1200秒、その後の残り role/build/verify/bench も期限後に続行できます。runbook の「supervisor 全体の上限」[runbook:131](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/phase3-8c-autonomous-trial-runbook.md:131) と D99 の「全体 wall safety budget」は偽です。

## 恒真・自己申告になっている保証

**real / scope 内**

- `fresh_context=True`
- `observed_tool_events=[]`
- fixture の `declared_tools=[]` / `observed_tool_events=[]`
- `generation_budget_is_fixed=True`
- `fixed_generations=True`
- `performance_early_stop=False`
- `scientific_claim=False`

これらは実挙動から導出した判定でなく、定数を書いて後で同じ値を検査するものです。[p3_autonomous_workload_trial.py:575](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:575) [p3_autonomous_workload_trial.py:957](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:957)

auditor contract も「配列要素は exact string fields」と要求しますが、consumer は `list[dict]` であることしか検査しません。[p3_autonomous_workload_trial.py:132](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:132) [auditor_gate.py:125](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/auditor_gate.py:125) `{}`、未知キー、非文字列 field を含む要素が通ります。v1 failure 後に「schemaを閉じた」という説明は未完了です。

## 信頼境界と prompt injection

### 直接の verifier/WAL 偽装

**refuted / scope 内**

通常の LLM 生出力に「serializable と記録せよ」と書いても、model response が verifier verdict を直接設定する経路はありません。authoritative drive は diff、digest、auditor verdictを再検査し、legacy/S2 の結果を pipeline が書きます。

### semantic auditor の誘導

**real / scope 内**

auditor は untrusted な `working_diff` を命令文と同じ JSON payloadで読みます。[p3_autonomous_workload_trial.py:748](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:748)

DiffQuarantine がコメント、block delimiter、line splice 等を拒否するため、単純な `// ignore previous instructions` は refuted です。しかし machine syntax gate は5識別子だけで、次を構文的には執行しません。

- allowed reads の閉表
- `kUnset=true`
- side-effect-free
- predicate が一式だけ
- string literal や追加演算子を使った auditor 向け命令文の混入

digest 照合も、同じ payload に digest が含まれる以上、prompt-injected auditorや偽 executableに対する独立性を与えません。

role 本文そのものは repository 内の既知ファイルを read-once し SHA を取るので、「外部由来 role 本文をそのまま命令化している」という恐れは **refuted / scope 内** です。[claude_projected_provider.py:115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/claude_projected_provider.py:115) ただし source body と mediated contract は同じ prompt 内で連結され、「takes precedence」という自然言語だけで優先順位を決めています。[claude_projected_provider.py:126](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/claude_projected_provider.py:126)

さらに、別 `--run-root` なら同じ trial id の公式 campaign state を再利用できます。run root の fresh 検査はありますが、build campaign root の fresh 検査はありません。[p3_autonomous_workload_trial.py:869](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:869) 既存 loop state の `direction/magnitude/result` は enum/value 閉表を検査されず whiteboard として再び LLM に渡ります。[p3_s4_loop.py:371](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_s4_loop.py:371) これは stale/tampered campaign からの prompt injection 面です。

## 説明と実装の不一致

| 仮判定 | 不一致 |
|---|---|
| **real / scope 内** | Runbook 21行「diff と designated context だけを auditor」だが、実際は workload、descriptor、generation、policy等の `common` 全体も渡す。[runbook:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/phase3-8c-autonomous-trial-runbook.md:21) |
| **real / scope 内** | D99「supervisor は previewを再実装しない」対 `_preview()` 再実装 |
| **real / scope 内** | Runbook/D99 の runtime tool、fresh context、主 model保証は envelope自己申告と定数を越えていない |
| **real / scope 内** | Runbook 115行は exploratory build を公式 `output/campaigns` へ置くが、現 main D65 と衝突 |
| **real / scope 内** | Runbook 131行の hard wall 上限は境界時刻検査にすぎない |
| **real / scope 内** | D99「schemaを object 配列へ明確化」は promptのみで、nested parserは閉じていない |
| **refuted / scope 内** | insight の6 SHAは全て現存 artifactと byte-for-byte一致 |
| **refuted / scope 内** | v1は6 valid + 3 auditor invalid、v2/v3は各12/12 valid・3/3 dry-passで整合 |
| **refuted / scope 内** | v3 planner→coder の3-field境界は実 payloadでも成立 |
| **real / scope 内・軽微** | v1/v2 reportには current schemaの `attempt_journal_sha256` fieldがなく、v3だけにある。insight は外部計算SHAを正しく記録しているため数値捏造ではないが、古い receipt は current report contractの replay証拠ではない |
| **real / scope 内** | insight の `kUnset=true` は3候補の観察として正しいが、今後の候補に対する machine gate ではない |

## Consumer 取り残し

API signature、role名、descriptor schemaについては **refuted / scope 内** です。現 main と branch base の間に対象 orchestrator/role API の変更はなく、次は実在し signature も一致しています。

- `trigger.drive_iteration`
- `checkout` / `assert_pinned_clean`
- descriptor projection/validation
- planner/coder/auditor/critic role files
- `CampaignConfig` / `PerfConfig`

一方、consumer 契約の取り残しは real です。

- **real / scope 内:** mediated auditor schema と `parse_auditor_dict()` の nested schema が不一致。
- **real / scope 内:** 現 main の `ExplorationCampaignLayout` / D65を採用していない。
- **real / scope 内:** build path の campaign fresh/namespace 検査がなく、custom run rootから旧 WAL/loop stateを再利用可能。
- **real / scope 内:** actual `claude-headless` subprocess、実 role本文、現在の CLI versionを通す regression testがない。
- **refuted / scope 外:** 新 moduleは既存 schedulerから自動 import/実行されない。landしただけで直ちに既存 campaignが変わるわけではない。しかしCLI実行時の危険は残る。

## 5テストの検出力

1. [`test_fixture_trial_runs_ycsb_abc_and_binds_descriptor`:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/tests/test_p3_autonomous_workload_trial.py:64)

   **検出できる:** A/B/C descriptor値、12 journal event、report書込み、planner_directionの3キー。

   **検出できない:** 実 preview、DiffQuarantine、digest gate、legacy/S2、bench、headless CLI。全provider/preview/driveがfakeです。`performance_early_stop`、`scientific_claim`、attempt/retryは実挙動でなく定数の自己申告を検査しています。

2. [`test_invalid_role_is_single_attempt_and_stops_cell`:125](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/tests/test_p3_autonomous_workload_trial.py:125)

   **検出できる:** top-level schema違反をinvalidにしcellを止めること。

   **検出できない:** provider実呼出し回数。providerにcounterがなく、`attempt=1/retry=false`という記録値だけを確認しています。内部retryを入れてもこのassertは緑になり得ます。

3. [`test_supervisor_error_still_writes_partial_terminal_report`:152](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/tests/test_p3_autonomous_workload_trial.py:152)

   **検出できる:** 捕捉可能なPython例外後のpartial reportとjournal。

   **検出できない:** kill、電源断、subprocess hang、プロセス突然死。したがって「常にterminal report」の証明ではありません。

4. [`test_projected_provider_lowers_source_tools_and_binds_effective_prompt`:239](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/tests/test_p3_autonomous_workload_trial.py:239)

   **検出できる:** inline JSONの`tools=[]`、prompt連結、env/cwd引数、provenance field。

   **検出できない:** 実 `claude` がflagを尊重するか、MCP/settings/slash/local toolが本当に無効か、served model、実session freshness。実行バイナリはexit 99のfakeで、runnerがfabricated envelopeを返します。

5. [`test_projected_provider_rejects_server_tool_use`:264](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/tests/test_p3_autonomous_workload_trial.py:264)

   **検出できる:** fabricated `web_search_requests=1` を拒否する分岐。

   **検出できない:** 実server/local tool、permission denial、empty MCP、設定source、aux model、role横断session再利用。

テスト全体が恒真というわけではありません。しかし「実際に能力が無い」「実際にretryしない」「実際に固定停止」という保証を、同じコードが書いた自己申告 fieldで検査する箇所は恒真ゲート型です。

## failures.md 型タグ監査

- **[捏造/幻覚] — refuted / scope 内:** F8型の定量捏造は再発していません。6 SHA、12/12、3/3は再計算結果と一致。
- **[恒真ゲート] — real / scope 内:** F9/F14/F16/F17型。tool events、fresh context、fixed stop等の自己申告、fixture auditor、hardでないwall gate。
- **[セッション死・救出] — real / scope 外:** crash resumeは未実装で、突然死時のterminal reportも保証されない。ただしD99/runbookが残余として明記しており、今回のMVPから明示除外。
- **[権限逸脱] — real / scope 内:** `tools=[]`設定をprocess/runtime隔離の証明として扱い、任意実行バイナリも許す。F16/F17再発面。
- **[ドリフト] — real / scope 内:** D65 namespace、duplicated preview、auditor schema、runbookとの分裂。
- **[コンテキスト浪費] — real / scope 内・低:** `critic_digest`をサイズ上限なしで毎世代全文投入する。[p3_autonomous_workload_trial.py:806](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:806) 再利用campaignでは膨張可能。
- **[計測汚染] — real / scope 内:** exploratory runの公式namespace混入とcustom run rootによる旧campaign再利用。CLIの競合process検査自体はF3再発を防いでいる。
- **[手順漏れ] — real / scope 内:** headless/build/namespace/numactl負例がテストされず、D65 consumerを段2が見落とした。
- **[テスト代表性] — real / scope 内:** F15/F21/F60型。5テストの主要経路はfakeで、live CLI/build gateを一度も通らない。

追加タグでは、F56の「requested/recorded modelをserved identityと誤認」が、Opus単独記録とaux Haiku消失で再発しています。F59の「装置自身が上限を守れない」は、最大1200秒×roleに対する境界確認だけのwall budgetで再発しています。F61についてはv1/v2/v3を区別し、正式証拠でないと明記しているため、過去artifactの改竄・正式昇格は refuted です。

## 親 brief・段2が過大に恐れていた点

- 通常の authoritative driveは全gateを再実行するため、preview重複は受理集合を広げない。
- `--no-build` はcorrectness/性能認証へ昇格しない。
- planner justification/uncertaintyのv3 leakはコード・実payloadとも塞がっている。
- env allowlistは正確に5変数。
- production providerのsupervisor-level retry loopはない。
- CLIの競合検査とpinned disposable worktreeは実装済み。
- `numactl`を空commandへ置換する入口はなく、不在hostでbenchまで成功する経路は見つからない。
- 現mainとのAPI rename/signature driftは見つからない。
- insightの定量値とSHAは捏造でない。
- source role本文自体は外部入力ではなく、repository内byteをread-once/hashしている。

逆に段2が見落とした主要点は、規律3のfeedback消失、fixture+build、任意Claude executable、D65 namespace、nested auditor schema、role横断session重複、aux model、hardでないwall budgetです。

## 総括

**現状の5ファイルを「既存防壁を変えない bounded supervisor」として取り込むべきではありません。**

Landを止めるに十分な具体的影響は次の3点です。

1. verifier/auditorの失敗理由が次の候補生成へ届かず、規律3を破る。
2. fixtureまたは任意executableで独立semantic auditorを置換でき、`kUnset=true`等のmachine未執行条件を外した候補がlegacy/S2/benchへ到達できる。
3. exploratory runを公式`output/campaigns`へ書き、`scientific_claim=false`を読まないproof chainへcertified/COMMITを混入できる。

最低限、fixture+build禁止、production provider/driveの封印と実行バイナリtrust root、構造化failure feedback、allowed-read/kUnsetの機械gate、D65準拠の探索namespace、hard wall semantics、実headless/build負例テストが必要です。歴史的insightのSHA receiptは正しいため、コード採用とは切り離して「非正式・揮発artifactの記録」として保存する余地はあります。