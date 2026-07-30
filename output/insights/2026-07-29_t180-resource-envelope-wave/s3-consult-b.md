結論は **NO-GO**。T-179 との token 算術は一致しますが、production 結線、job/session 対応、hard cap の実効性に未解決の穴があります。

## 所見

1. [must-fix] / DW-O01 が要求する上限値を誰も決めておらず、launcher を実運用できない / [s2-plan.md:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:24)、[s2-plan.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:38)、[s2-plan.md:269](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:269)、[phase3.md:548](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/docs/phase3.md:548)

   `max_wall_clock/model_calls/billable_tokens` は必須かつ既定なしなのに、DW-O01 置換案は値も選定主体も示さない。stage policy は T-184 所有なので、T-180 が暗黙に数値を採用するのも越境である。dispatcher は subprocess 直前に O01 を読むため、`.claude/commands/dev-wave.md` と Skill の追加編集は不要で、変更点は O01 で足りる。[dev-wave.md:84](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/.claude/commands/dev-wave.md:84)、[SKILL.md:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/.agents/skills/dev-wave/SKILL.md:32)

   また、plan は operations を「実装対象」に混ぜているが、実装子は docs 編集禁止である。O01 は親所有と明記すべきである。[s2-plan.md:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:7)、[dev-wave.md:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/.claude/commands/dev-wave.md:37)

   成果物影響: 今 O01 を切り替えると全 worker が引数不足で非採用、切り替えなければ receipt・manifest・上限値は一件も生成されず、いずれも wave の受理集合を壊す。

2. [must-fix] / manifest selector を実際に使う stage-7 consumer がない / [core.md:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/docs/dev-wave/core.md:86)、[dev-wave.md:72](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/.claude/commands/dev-wave.md:72)、[s2-plan.md:247](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:247)

   launcher が manifest を書いても、DW-S07 は `codex_worker_ledger.py --manifest ... --strict` の実行、全 receipt との突合、worklog への値の転記を要求していない。さらに plan は `test_check_docs.py` へのテスト追加だけで、常用される `tools/check_docs.py` の O01 内容 invariant を追加していない。[s2-plan.md:315](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:315)、[check_docs.py:286](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/check_docs.py:286)

   `.claude/commands/dev-wave.md` は既に DW-S07 を読むので入口変更は不要。親が既存 S07 を縮約改訂し、production check に launcher・receipt・manifest selector の三点を pin する必要がある。

   成果物影響: exact manifest が存在しても公開台帳が旧 cwd selector のままなら、session 数・token 値・参照 rollout の誤混入は解消されない。

3. [must-fix] / manifest の `job_id/attempt_index` を ledger が捨て、T-179 の job・retry 定義と衝突する / [s2-plan.md:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:223)、[s2-plan.md:257](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:257)、[codex_worker_ledger.py:404](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:404)、[codex_worker_ledger.py:539](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:539)

   plan の selector は session ID allowlist としてしか manifest を使わない。現 ledger は `len(records)` を worklog の job 数と比較し、retry は `(cwd, normalized prompt hash)` で推測する。retry 後は 1 job が複数 session になるので、この前提は崩れる。T-179 自身も prompt hash は因果的 lineage ではないと明記している。[T-179 README.md:120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t179-worker-ledger-verbatim/README.md:120)

   `--manifest` 時は job/attempt を各 record に公開し、worklog の job 数は distinct `job_id`、retry lineage は manifest の対応で算出すべきである。manifest 未指定時だけ旧挙動を保存すればよい。

   成果物影響: 1 job・2 attempts が 2 jobs と報告されて strict 赤になり、別 job の同一 prompt は偽 retry に融合して、receipt と台帳が異なる lineage を主張する。

4. [must-fix] / 新 manifest に wave identity・凍結点がなく、同名の既存 `WaveManifest v1` と二義化する / [s2-plan.md:218](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:218)、[schema.py:261](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/schema.py:261)、[operations.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/docs/dev-wave/operations.md:15)

   新 schema は session 配列だけで、wave ID、worktree、artifact root、開始基準、final digest がない。既存 supervisor の `WaveManifest` は同じ `schema_version=1` だが、`supervisor_run_id/wave_index/worktree/base_main_sha` を持つ別物である。さらに receipt は manifest path だけを持ち、内容 hash に束縛されない。[s2-plan.md:133](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:133)

   `CodexWorkerSessionManifest` 等へ改名し、wave identity を create-only header に置き、全 job 終了後の manifest hash を最終 ledger 記録へ束縛すべきである。attempt artifact も job ごとの排他的 directory を必須化する必要がある。現在案の `attempt-0001.*` は、並列 job が同じ artifact-dir を渡すと衝突する。[s2-plan.md:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:107)、[s2-plan.md:304](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:304)

   成果物影響: 過去 wave の manifest path 再利用や並列 artifact 衝突により、旧 session が exact selector に混入するか、別 job の出力 hash を receipt が参照する。

5. [must-fix] / 「全非採用を再実行」は retry 分類そのものであり T-183 境界を越える / [s1-brief.md:46](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s1-brief.md:46)、[s2-plan.md:105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:105)、[phase3.md:545](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/docs/phase3.md:545)

   error text を解析しなくても、「validator reject、非ゼロ終了、evidence missing をすべて retryable と扱う」は failure 分類 `all retryable` である。既定 `max_attempts=1` は production で隠すだけで、`N>1` の実装意味論は T-183 に侵入している。

   境界を守る案は、T-180 の production O01 を必ず 1 attempt にし、T-183 まで `N>1` を拒否すること。代償は T-183 で loop/schema test を再訪すること。逆に境界を T-180 側へ動かすなら、safety-filter、validator reject、missing evidence、非ゼロ終了の retry 可否と fixture、backoff/escalation まで同 wave に入り、規模とレビュー負担が大幅に増える。

   成果物影響: 現案で `N>1` を使うと、決定的失敗にも追加 session/token が発生し、後続 attempt の偶然成功で job の非採用が採用へ変わる。

6. [must-fix] / 観測済み usage event 数を hard model-call admission cap と偽っている / [codex_worker_ledger.py:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:4)、[T-179 README.md:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t179-worker-ledger-verbatim/README.md:71)、[s2-plan.md:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:91)

   T-179 の `model_calls` は「`info` が object の `token_count` event 数」であって、call 開始前の admission event ではない。plan 自身も usage は call 完了後にしか観測できないと認めるのに、「次の model call を許さない」と主張する。[s2-plan.md:95](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:95)

   poll の間に次 request が開始されない保証はなく、kill された in-flight call は次の `token_count` を残さない可能性がある。実装可能なのは「観測済み event が閾値へ達したら停止」である。また `max_billable_tokens` は T-179 の `"CLI reported"` と同名同義でなく、値は `input-cached+output` にすぎない。[s2-plan.md:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:26)、[T-179 README.md:74](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t179-worker-ledger-verbatim/README.md:74)

   `max_cli_reported_tokens` へ改名し、`model_calls` は observable proxy と明記して最大 1 in-flight call の不可視 overshoot を receipt に表出するか、真の admission seam を別 scope で作るべきである。

   成果物影響: receipt が `model_calls=N`、token 値も上限内と主張しても、未記録の N+1 call が費消済みになり、同じ wave の資源台帳が過少値を公開する。

7. [must-fix] / T-179 の算術は一致するが、凍結 10 session を使う manifest 受入がない / [s2-plan.md:80](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:80)、[codex_worker_ledger.py:187](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/codex_worker_ledger.py:187)、[T-179 README.md:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t179-worker-ledger-verbatim/README.md:28)

   receipt の `cli_reported = input-cached+output` と attempt 累積は T-179 定義に一致する。現行 `--cwd-contains dev-wave-t153e-t15423 --json --strict` を read-only 実走した結果も、`issues={}`、`sessions=10`、`model_calls=434`、`cli_reported=2,757,982` で凍結値と一致した。

   しかし plan の ledger tests は合成 `_materialize()` のみで、10 個の凍結 ID を含む manifest と実 rollout の受入を登録していない。[s2-plan.md:306](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:306)

   実装後は README の 10 ID を manifest に列挙し、少なくとも次を親受入に固定すべきである。

   ```text
   codex_worker_ledger.py --manifest <t179-10-sessions.json> --json --strict
   expected: issues={} / sessions=10 / model_calls=434 / cli_reported=2757982
   ```

   stage 別 6 値も [T-179 README.md:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t179-worker-ledger-verbatim/README.md:37) と逐件照合すること。なお T-179 は実 job ID を凍結していないため、historical manifest の `job_id` を因果 lineage の証拠とは呼べない。

   成果物影響: selector が正しい ID を選んでも既存集計値を drift させる実装を、合成 fixture だけでは通し、凍結台帳と新台帳が別の token/model-call 値を主張する。

8. [must-fix] / probe package が brief の session・token 一致と「唯一の seam」を監査可能に保存していない / [s1-brief.md:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s1-brief.md:11)、[s1-brief.md:19](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s1-brief.md:19)、[s1-brief.md:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s1-brief.md:27)

   `events*.jsonl` は stdout だけ、`liveness.tsv` は line/event 件数だけで、対応 rollout の `session_meta`、最終 `total_token_usage`、filename、hash、probe command/script が package にない。さらに zero-count 時に単独の `0` 行が挟まり、TSV 自体が四列構造でない。[liveness.tsv:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/probe/liveness.tsv:4)、[events2.jsonl:13](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/probe/events2.jsonl:13)

   元 rollout は現在の `$CODEX_HOME` に存在し、値も一致したが、probe artifact から参照も hash もされていない。「現 CLI 0.146.0 の観測 seam」とは言えるが、「唯一」は一実走からの過剰一般化である。bounded/redacted な `session_meta`、全 token_count の時刻・usage、最終 hash、実行 script を保存すべきである。

   成果物影響: session/usage の三者束縛が追試不能なままなら、誤 rollout を receipt actuals に採用しても証拠参照から検出できず、stop_reason と token 値が変わる。

9. [must-fix] / receipt の semantic truth table が閉じていない / [s2-plan.md:154](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:154)、[s2-plan.md:204](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:204)

   schema には top-level `outcome` と Attempt の `accepted` があるのに、semantic binding の「`accepted` は…」がどちらを指すか不明である。`launcher_rc ↔ outcome ↔ stop_reason ↔ limit_trigger`、`actuals.wall_clock_s`、`max_attempts` 到達の必要十分条件も定義されていない。既存 supervisor receipt は outcome/stop_reason/Git fields を明示的に相互拘束している。[receipt.py:137](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/receipt.py:137)

   全組合せの真理値表と負例を独立 oracle にし、writer と checker の共通 helper を同時に弱化しても kill できる必要がある。

   成果物影響: `outcome=accepted` なのに `launcher_rc=1` や `stop_reason=max_attempts` といった矛盾 receipt が check を通ると、非採用 job が wave 受理集合へ入る。

10. [must-fix] / CLI executable identity と process-group 終了証拠が receipt にない / [s2-plan.md:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:33)、[s2-plan.md:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:81)、[schema.py:273](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/schema.py:273)

   probe は CLI 0.146.0 に依存するのに、receipt は CLI version、resolved executable path/hash を持たず、retry 間で同じ binary を使った証明もない。既存 worker は executable hash を検査し、PID の boot/start identity を信号前に再確認する。[worker.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/worker.py:116)、[worker.py:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/worker.py:181)

   `read_pid_identity` / `terminate_verified_group` は公開済みなので再利用可能である。receipt には binary/version と `process_group_residual` を残すべきである。

   成果物影響: CLI 更新を跨いだ attempts が同一 job の同一測定として合算されるか、子が残存したまま receipt が停止完了を主張し、台帳値が receipt 後も増え続ける。

11. [scope外候補] / stdout・stderr・artifact bytes が resource envelope から抜けている / [schema.py:158](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/schema.py:158)、[worker.py:441](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/worker.py:441)、[s2-plan.md:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/output/insights/2026-07-29_t180-resource-envelope-wave/s2-plan.md:107)

   既存 supervisor は `max_wave_output_bytes` と capped copy を持つ。新 launcher は部分出力を無制限に保存するため、一つの command execution が usage event 前に大量出力すれば、wall/token gate より先に disk を使い切れる。

   本 wave に入れるなら `max_artifact_bytes`、切詰めではなく上限停止、raw hash、receipt reason、fake spew test が必要で、schema/test 面が増える。外へ送るなら「resource envelope」ではなく「compute-usage envelope」と射程を縮め、T-185 類似の裁定パッケージへ送るべきである。実装済み扱いは不可。

12. [nit] / 既存 supervisor の exact receipt/schema を再利用するのは誤りだが、低層 primitive は再利用すべき / [SKILL.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/.agents/skills/dev-wave/SKILL.md:38)、[schema.py:297](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/schema.py:297)、[schema.py:448](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/schema.py:448)

   既存 `Receipt/WaveManifest` は Claude supervisor の whole-wave Git 結果用で、Codex job usage schema と意味が違う。exact 型の共用は supervisor 互換を偽るため不採用が正しい。一方、bounded duplicate-key 拒否の `strict_loads`、`canonical_bytes`、verified group termination は既に検査済みで、単一 850 行 launcher に再実装する合理性は薄い。[schema.py:538](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t180-resource-envelope/tools/dev_waves/schema.py:538)

## 総括

**NO-GO。**

最重要 3 件は次のとおり。

1. 必須上限値の policy・所有者と stage-7 consumer がなく、launcher/manifest が production で使えない。
2. manifest の job/attempt 対応を ledger が捨て、wave identity もないため、T-179 台帳・receipt・worklog が異なる job/session/retry を主張する。
3. post-call の `token_count` event を hard model-call cap、`CLI reported` を billable token と呼んでおり、実際に強制・測定できる範囲を越えている。