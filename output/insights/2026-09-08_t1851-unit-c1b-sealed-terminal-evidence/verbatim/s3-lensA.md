## 所見

以下はすべて静的読解による判定であり、テスト実測はしていない。

**A-01 — real / blocker**

- file:line: [s2-plan.md:115](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:115)、[s2-plan.md:118](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:118)、[s2-plan.md:275](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:275)、[s8b_floor_attempt_launcher.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:61)
- 破れる具体例: durable claim 上の正当な `attempt_id="C::seq0"` を使いつつ、公開 dataclass の reservation に `kind="planned", seq=999, round=99` を入れ、terminal builder の `campaign_record` に同じ値を返す。plan は record と reservation の一致しか要求せず、`attempt_id` と `kind/seq/retry_ordinal` の関係や frozen schedule との一致を要求していないため、完全な throughput を添えれば `observed` になる。
- 同じ穴は `records`・`threads`・`workload` にもある。これらの durable authority は measurement-generation claim に存在する（[s8b_holdout_admission.py:1719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_holdout_admission.py:1719)）が、plan が claim から明示的に再照合するのは `mode` だけである。誤った production caller は契約の脅威範囲内なので、「terminal builder が選べない snapshot」は十分な信頼根ではない。
- これは相互整合違反を `observed` へ救済する経路ではないが、より直接的に、権威との不一致を相互整合検査の入力へ入れないことで虚偽の `observed` を作れる経路である。

**A-02 — real / blocker**

- file:line: [s8b_floor_attempt_launcher.py:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:777)、[s8b_floor_campaign.py:6264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:6264)、[s2-plan.md:83](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:83)
- 破れる具体例: `capture_measure_point()` が `OSError(5, "I/O")` を送出する。launcher は現在これを捕捉して `failure.stage="capture"` とし、plan の E1 は `measurement_execution_unavailable` の sealed terminal を作る。一方、正本とされた campaign は `RuntimeError` と `TimeoutExpired` しか捕捉せず、`OSError` では session record 自体を作らない。
- したがって「campaign の実 semantics と同じ」という一般化は成立せず、plan は campaign より広い terminal 集合を受理する。

**A-03 — real / blocker**

- file:line: [s2-plan.md:23](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:23)、[s2-plan.md:160](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:160)、[attempt_registry_core.py:1039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1039)
- 破れる具体例: evidence file の projection が `finished_at="2026-09-08T00:00:00Z"` のまま、terminal row だけを `"2099-01-01T00:00:00Z"` に変更して event hash を再計算する。core は `finished_at` が text であることしか見ない。plan の `_require_sealed_s8b_v2_terminal()` の全件等値リストにも `finished_at` が無いため、file と row の不一致を検出できない。
- live writer は projection を使うため一致するが、契約 7 節が要求する crash 後の「内容不一致拒否」には不足する。

**A-04 — real / blocker**

- file:line: [parent-probes.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/parent-probes.md:18)、[s8b_attempt_profile.py:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:556)、[s8b_attempt_profile.py:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:683)、[attempt_registry_core.py:1436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1436)
- 破れる具体例: P-1 に列挙された「4 点だけ」の変異を適用して、5.2 の観測成功 terminal を canonical v2 profile でロードする。null matrix を通過しても、その直後に現行の `_reject_unsealed_s8b_v2_terminal` が必ず発火する。
- 実測自体を否定するものではない。読解上、5/5 を通すには validator の除去、差替え、または canonical でない profile の使用という未記載条件が必要である。したがって P-1 は記載どおりには再現できず、契約の「consumer に通した」という根拠へ一般化できない。

**A-05 — real / blocker**

- file:line: [contract-v3.md:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.md:185)、[s2-plan.md:159](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:159)、[s2-plan.md:366](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:366)、[s2-plan.md:377](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:377)
- 破れる具体例: `not-consumed` 枝を、`measurement_retry_reason` が null でも常に同じ `[attempt-null-matrix] ... not-consumed null matrix differs` で拒否するよう誤実装する。計画された負例は落ち、positive control の「競合 retryable」も通るため、テストは緑のままである。
- E1 は `not-consumed` を発行せず、sealed validator も E1 projection と row status の一致を要求する。このため canonical sealed 経路には正当な `not-consumed` positive が存在しない。競合 retryable は別枝の正例であり、`not-consumed` 拒否が恒真でないことを証明しない。観測成功側の positive は適切だが、5.3 の後半は到達不能な拒否になっている。

**A-06 — refuted / 非 blocker（v1 の台帳受理集合）**

- file:line: [s2-plan.md:185](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:185)、[s2-plan.md:198](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:198)、[s2-plan.md:216](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:216)
- 破れる具体例として検査したもの: v1 terminal に `measurement_retry_reason="measurement_sample_incomplete"` を渡す。
- plan は `_assert_null_matrix` の新引数に既定値を置かず、必ず profile から渡す。`DomainProfile` の keyword-only 既定は従来どおり `"failure_reason"`、v1 event keys は不変、v1 への非 null 新 field は拒否される。この組合せでは新しい v1 row は受理されない。
- ただし Python 呼出し集合だけを見ると、明示的に新 kwargs を `None` で渡す呼出しは従来の `TypeError` から受理へ変わる。生成 bytes は同一なので正しさ上の受理集合は広がらないが、「受理集合」を公開 API 呼出しまで含めるなら文字どおりの差分は残る。

**A-07 — refuted / 非 blocker（内部不整合の observed 救済）**

- file:line: [s2-plan.md:83](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:83)、[s2-plan.md:84](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:84)、[contract-v3.md:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.md:130)
- 破れる具体例として検査したもの: `reps_expected=5` に対し有限 throughput 4 本、`nonfinite_count=0`、`exec_failures=0` を与える。
- plan は有限列と元の reps を `assess_session()` に渡すうえ、総数不変条件を別途検査し、辞書変換や未知理由からの `observed` fallback を置かない。記載どおりならこの入力は `[s8b-terminal-evidence]` で拒否される。A-01 のような「権威を照合対象に入れていない穴」は別だが、照合対象内の破れを observed に落とす経路は見つからなかった。

**A-08 — refuted / 非 blocker（偽 registry による capability 発行）**

- file:line: [s8b_floor_attempt_launcher.py:896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:896)、[s8b_attempt_registry.py:280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:280)、[s2-plan.md:139](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:139)、[s2-plan.md:273](/work/1/SFC/tanab/dev-wave-jobs/2026-09-07_t1851-unit-c1b-v3/artifacts/s2-plan.md:273)
- 破れる具体例として検査したもの: fake registry が `ClassifiedAttempt`、`begin_attempt_observation()`、`record_sealed_attempt_terminal()` を同名で実装し、fake observation を返す。
- test seam では reserve/classify/observation は fake に到達するが、fake observation を production adapter に渡すと、厳密型、private token、weakref 同一性、state fingerprint、attempt key の最初のいずれかで拒否される。interface 模倣だけでは `ValidatedTerminalEvidence` を発行できない。
- この判定は、公開予定の `require_sealed_terminal_evidence()` が draft を validated へ昇格させる関数ではなく、既発行 capability の厳密検査として実装されることを前提とする。plan の「adapter private issuer」という記述とは整合する。

## plan の判定

**no。**

A-01 により、caller-controlled reservation と durable schedule/measurement claim の不一致を含む虚偽の `observed` が sealed proof chain に入る。A-03 により、crash replay は `finished_at` の row/file 不一致を見逃す。さらに A-02 は「campaign の実 semantics が正本」という契約より terminal 受理集合を広げている。

A-04 と A-05 は検証根拠側の blocker である。P-1 の記載だけでは 5 正例の通過を説明できず、`not-consumed` 拒否には同枝の正例がないため、恒真拒否を殺せない。

## 親の実測への反証

P-1 の「5/5 通過」は、記載された一時変異だけでは canonical v2 profile の無条件 terminal validator に阻まれる。隠れた profile 変更があったなら、その probe が証明するのは generic core の reason/null matrix までであり、plan の leaf・adapter・durable evidence 経路ではない。

仮に P-1 の core probe が実際に通っていても、形のラベルだけでは plan の正例にならない。例えば `observed` row に任意の非 null `primary_value=999` を入れれば現行 null matrix は受理できるが、plan の evidence validator は実 median との差で拒否する。したがって「5 形が core を通った」から「plan の 5 形が end-to-end で通る」への一般化はできない。

P-6 も例外集合を含めて同義ではない。campaign が捕捉しない `OSError` を launcher は terminalize するため、「実 campaign と同順」だけでは plan の受理集合を束縛できていない。

P-2〜P-5 の個別測定については、この静的読解から結果自体を否定する材料はなかった。ただし P-5 は前例となる handle 機構を測っただけであり、A-08 の安全性は plan が private issuer 境界をそのまま実装した場合に限る。

## 総括

plan は内部の E1・null matrix・v1 row schema と、interface 模倣だけの fake registry に対しては概ね fail-closed である。しかし、権威へ結ばれていない reservation field、campaign と異なる例外値域、`finished_at` の crash replay 欠落という 3 本の具体的な correctness hole が残る。

したがって、現状の plan をそのまま実装しても契約 v3 の「不一致はすべて拒否」「虚偽の terminal 事実を proof chain に入れない」は実体化できない。