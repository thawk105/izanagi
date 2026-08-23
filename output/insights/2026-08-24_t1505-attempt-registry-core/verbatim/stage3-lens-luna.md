## 総括

1. **致命的 — 死んだ process を別 process が閉じる復帰経路がない（scope 内）。** PBS wall timeout・node 障害・SIGKILL は classifier 自身を殺すため、registry は `start(+seal)` または `observation-start` で止まる。次 slot は previous terminal 必須なので、plan を実装しても落ちた構成を再測定できない。[trial_registry.py:2361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2361) [s2-plan.md:355](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:355)

2. **致命的 — `session-start` と registry start の crash cut が未設計（scope 内）。** どちらを先に書いても片側だけ残る cut があり、現行 resume は journal の start を見て session を永久 skip する。plan の WAL/test 対象に run journal が含まれない。[s8b_floor_campaign.py:5210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:5210) [s8b_floor_campaign.py:5506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:5506) [s2-plan.md:499](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:499)

3. **致命的 — 提案 core API では凍結済み global retry budget を表現できない（scope 内）。** `series_key` は反復込み、policy は `max_series_attempts` しかない一方、8b の `retry_slots_per_cell` は全反復を通じた cell 単位である。素直な実装は受理可能 retry 数を `n_sessions` 倍へ拡大し、sessions・median・floor を変える。[s2-plan.md:87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:87) [s2-plan.md:120](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:120) [s8b_holdout_admission.py:1291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:1291)

4. **重大 — 出力前分類は指定編集面だけでは実装不能（scope 内だが依存面が scope 外）。** production `measure_point()` は launch・wait・parse 済み `ScalePoint` を返す一体 API であり、`s8b_floor_campaign.py` だけでは opaque output を保った二相化にならない。PBS accounting を読む authority も計画されていない。[s8b_floor_campaign.py:6797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:6797) [s2-plan.md:357](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:357)

5. **重大 — 「共有 root を master」にしても権威は一本化されない（scope 内）。** 現在は claim、journal authorization、`consumed/` marker、attempt ledger が別々の意味を持つ。新 registry の conflict truth table が無く、同じ lock は五つの成果物を直列化するだけである。[s8b_holdout_admission.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:4) [s8b_holdout_admission.py:3746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:3746) [s8b_holdout_admission.py:3821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:3821)

6. **重大 — consumer・resume checker・certification projection・docs が取り残されている（大半 scope 内）。** `assemble_result()` は完了 `session` しか出さず、start-only attempt は消える。resume verifier、floor contract/stats、Markdown、refreeze eligibility、runbook は段2の編集点に含まれず、registry を作っただけの「実装したふり」になる。[s8b_floor_campaign.py:5528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:5528) [s8b_floor_campaign.py:7094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:7094) [src-runbook-R5.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/src-runbook-R5.md:27)

7. **重大 — plan の post-observation 方針は救出ではなく永久欠測であり、所有範囲も越える。** attempt 0 を欠測に固定し後続を診断専用にすると floor 主値は戻らない。これは estimand/受理集合のユーザー裁定であり、D672 が閉じたのは reuse 形状だけである。[s2-plan.md:420](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:420) [src-D672.md:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/src-D672.md:6)

8. **重大 — 2 実装子・1 wave では完遂不能。** 安全な切断点は「8c core 抽出・facade・不変検査」の完了直後で、8b production call site は一切配線しない位置である。8b は crash protocol、trusted launcher、consumer/checker/docs を一体で別 wave にすべきである。[s2-plan.md:508](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:508)

9. **中 — 親 brief の実測表には誤アンカーと再現不能な一般化がある。** 8c attempt registry の既定 path は `output/s8c-trial-registry/...` ではなく `output/s8c-preregistration/attempt-registry.jsonl`。consumer の「15/11/60参照」は計数規則がなく再現できず、pilot の `git diff main...` 空だけでは未 commit・未追跡・semantic conflict を否定できない。[brief.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/brief.md:52) [trial_registry.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:57) [brief.md:96](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/brief.md:96)

## crash 形態別の実効性

| crash 形態 | 残る状態 | 次回起動が見るもの | 判定 |
|---|---|---|---|
| build 失敗 | manifest/genesis 前。journal は概ね `L` | 現行 resume は再 build 後 manifest を作る。[s8b_floor_campaign.py:6585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:6585) [s8b_floor_campaign.py:6642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:6642) | clean cut なら既存 resume で復帰。registry の功績ではない。 |
| genesis 前 | manifest はあるが registry/claim 無し、または claim だけ | plan は reservation lock 内で genesis を作るが、claim/genesis/binding の書順・recovery record が未定。[s2-plan.md:281](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:281) | 全く書いていなければ復帰可能。claim/genesis の片側だけ残る cut は未保証。 |
| genesis 書込み中 | O_EXCL path は存在するが bytes が途中 | direct create は file 本体へ write→fsync するため、再作成は `FileExistsError`、read は malformed になる。[s8b_holdout_admission.py:800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:800) | **復帰経路なし。** plan の `create_genesis()`/`atomic_update()` APIにも torn-create recovery がない。[s2-plan.md:136](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:136) |
| `session-start` 後、registry start 前 | journal start のみ | `_started_seqs()` が開始済みと見なし、runner は planned session を skipする。[s8b_floor_campaign.py:5128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:5128) | **復帰経路なし。** |
| registry start 後、`session-start` 前 | registry `start+seal` のみ | journal は未開始なので同じ planned session を選ぶが、registry は slot 再予約を拒否する。[trial_registry.py:3025](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:3025) | **復帰経路なし。** |
| preflight 競合 | start、分類 receipt、retryable terminal を残せる | 外部 probe だけで分類可能。現行でも output を呼ばず session を閉じる。[s8b_floor_campaign.py:5235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:5235) | crash cut が無ければ唯一明瞭に復帰可能。 |
| PBS wall timeout / node 障害 / SIGKILL | 通常 `start(+seal)`、receipt/terminal 無し | interpreter が死ぬため `launch_and_wait()` 後の classifier は動かない。`subprocess.TimeoutExpired` catch は生きている親 process が見る子 timeout で、PBS job kill ではない。[s8b_floor_campaign.py:5250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:5250) | **復帰経路なし。** scheduler accounting を次 process が受理・封印する APIが無い。 |
| process 消失 | start のみ | plan の閉集合は spawn failure までで、spawn 後 disappearance/SIGKILL 自体は理由にない。[s2-plan.md:384](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:384) | **復帰経路なし。** node failure と判定する外部証拠が別途必要。 |
| classification receipt 後、registry row 前 | create-only receipt だけ | 現行 order は receipt create が先、row append が後。同じ分類の再実行も create-only collision になる。[trial_registry.py:3170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:3170) | **復帰経路なし。** idempotent adopt/replay 規則が必要。 |
| `observation-start` 後 | observed boundary、terminal 無し | current core は observation 後の retry を拒否する。plan の `allow_recovered_abandonment` は flag だけで、event schema・recovery API・owner fencing が無い。[trial_registry.py:2377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2377) [s2-plan.md:120](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:120) | **主値の復帰経路なし。** diagnostic-only slot は床値を救出しない。 |
| job 孤児化 | campaign claim と job が生存、driver 不在 | 新 process は同じ claim を再取得し、競合なら開始前に拒否される。producer 内に release/reconcile 呼出しはない。[s8b_floor_campaign.py:6416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:6416) | **plan 内の復帰経路なし。** exact stale-claim 挙動は投影外 module のため推測だが、少なくとも本 plan は fencing/reaping を扱わない。 |

また、別 process による recovery terminal は現行 capability 所有規則にも反する。terminal は classification を実行した PID/thread の owner を要求するため、死んだ process の状態をそのまま再構成できない。[trial_registry.py:3362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:3362) [test_trial_registry.py:5969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_trial_registry.py:5969)

## retry budget と slot identity

plan は全 `(holdout, config, round, attempt=0..R)` を genesis に入れ、別途 cell-global cap `R` を封印するとした。[s2-plan.md:272](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:272) しかし提案 `SlotCodec` が core へ渡せる集約軸は反復込みの `series_key` だけで、cell-global key が無い。[s2-plan.md:92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:92)

現行の凍結予算は明確に `n_sessions + retry_slots_per_cell` であり、retry ticket 自体も round 非依存の `cell::retryN` である。[s8b_holdout_admission.py:1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:1133) [s8b_holdout_admission.py:1291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:1291)

従って、次のどちらかになる。

- `max_series_attempts` を各 round に適用し、凍結済み budget を拡大する。
- adapter が別に cell-global cap を判定し、plan の「core replay だけが認可権威」という主張を破る。[s2-plan.md:323](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:323)

必要なのは `cell_budget_key(slot)` と `max_consumptions_per_budget_key` を core replay 契約へ追加し、v1 `retryN` ticket と `(round, attempt_ordinal)` slot の一対一 transaction binding を定義することである。

## 二重・三重台帳

現行の権威分担は次の通りである。

| 成果物 | 現在の意味 |
|---|---|
| `claims/*.claim` | cell の一回性 master。[s8b_holdout_admission.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:4) |
| run `journal.jsonl` の `session-start` | attempt authorization。[s8b_holdout_admission.py:3746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:3746) |
| `consumed/*.json` | 実際の ticket consumption の durable fact。[s8b_holdout_admission.py:4363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:4363) |
| `attempt-ledger.jsonl` | marker と一致すべき evidence mirror。[s8b_holdout_admission.py:4493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:4493) |
| 新 registry/receipt/binding | plan 上は retry authorization と lifecycle master。[s2-plan.md:285](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:285) |

`shared_admission_root()` は path resolver にすぎず、どの file を正とするかは決めない。[s8b_holdout_admission.py:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:427) 同じ `ledger.lock` も crash atomicityを作らない。

さらに plan は attempt ledger v2 を追加するとするが、現在の inspector は marker を v1 schema で構築し、全 selected row に v1 exact keys を要求する。[s8b_holdout_admission.py:4434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:4434) [s8b_holdout_admission.py:4503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:4503) plan が挙げた inspector 編集アンカー `:4493-4524` だけでは v2 marker はそこへ到達する前に拒否される。[s2-plan.md:297](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:297)

一本化には、少なくとも次の conflict table が必要である。

- registry transition を attempt 認可の唯一の権威とする。
- marker/attempt-ledger は同一 transaction ID から再生成可能な projection とする。
- run journal は registry start digest への binding であり、単独では retry を認可しない。
- registry と projection が矛盾した場合の adopt/replay/quarantine 条件を crash cut ごとに固定する。
- claim/genesis/binding/journal/receipt/marker/ledger の transaction intent と commit 順を schema として記す。

現在の plan の `AttemptStore` には transaction ID、recovery scan、orphan receipt adoption のいずれも無く、この要求を実装できない。[s2-plan.md:136](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:136)

## 取り残された層

- **producer:** `_wrap_admission_aware_measure`、`_Runner`、default measure は列挙されている。ただし fresh/resume admission 配線、journal resume verifier、campaign claim/job recovery が不足。[s2-plan.md:412](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:412) [s8b_floor_campaign.py:6826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:6826)

- **consumer:** `assemble_result()` は `event=="session"` の完了行だけから `attempts` を作るため、start-only、receipt-only、observation-only attempt を全く報告しない。[s8b_floor_campaign.py:5679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:5679) [s8b_floor_campaign.py:5732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:5732)

- **集計・checker:** result verifier は別 module `s8b_floor_stats` の live-admission入口を呼ぶが、plan はその schema・primary/diagnostic rules を編集対象にも射影にも入れていない。[s8b_floor_campaign.py:5621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:5621)

- **resume checker:** `_verify_resume_journal()` は current `session-start/session` モデルを前提にし、新 classification/observation/recovery event や registry binding を検証しない。[s8b_floor_campaign.py:7094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:7094)

- **certified/refreeze 判定:** `derived_eligible_for_refreeze` は claim schema、mode、resume marker、seam だけを見て registry の complete/primary 状態を見ない。[s8b_holdout_admission.py:4355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:4355) 正式測定 gate 自体は scope 外で閉じたままでよいが、将来 gate を開く consumer に registry binding が届かない。[src-design-10.5-10.6.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/src-design-10.5-10.6.md:30)

- **docs:** R-5 は reuse/admission/classification/bias を「未解決」と記したままである。plan の成果物一覧に design/runbook 更新が無い。[src-runbook-R5.md:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/src-runbook-R5.md:27) [brief.md:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/brief.md:81)

以上から、段2のままでは gate を新設して producer の一部だけ配線する wave であり、実効的な gate ではない。

## 凍結境界

1. 親 brief の path 認識が誤っている。attempt registry 本体は `output/s8c-preregistration/attempt-registry.jsonl`、receipt は `output/s8c-trial-registry/classification-receipts` である。[trial_registry.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:57) [trial_registry.py:3172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:3172) 親 I1 だけを検査すると genesis bytes の回帰を見逃す。plan の最終 diff が `output/s8c-preregistration` を追加している点は正しい。[s2-plan.md:506](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:506)

2. 既存 v1 attempt-ledger bytes を変更しなくても、reader が v2 exact keys を正しく分岐しなければ旧成果物の再検証が壊れる。現在は単一 `_FLOOR_ATTEMPT_KEYS` だけである。[s8b_holdout_admission.py:3865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_holdout_admission.py:3865)

3. `holdout_freeze.json` の `design_source.sha256` は既知不一致である。[src-design-10.5-10.6.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/src-design-10.5-10.6.md:42) plan の `profile/schema hash` が current design bytes を含むか否かが未定義なので、誤ってこの pin を再検証すると全 existing freeze を拒否する。[s2-plan.md:295](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:295) profile hash は frozen protocol/schema のみに限定する必要がある。

4. `floor_protocol.json` の retry budget は現行 reservation 計算でも cell-global である。[s8b_floor_campaign.py:1546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_floor_campaign.py:1546) 前述の core API不足を直さず実装すると、既存 protocol bytes は不変でも意味上の budget が拡大する。

## 親 brief・段2 plan の実測再検算

- `trial_registry.py:1818-3431` は inclusive 1,614 行で、ここは正しい。`1818-3555` は 1,738 行だが、`3432-3555` の124行は8c固有 acceptance であり、全域を「attempt 状態機械」と一般化するのは不正確。[trial_registry.py:1818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:1818) [trial_registry.py:3432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:3432)

- brief の acceptance「126行」は `3432-3557` と関数後の空行まで数えた値で、実関数は124行。重大差ではないが「実測」表としてはアンカーが粗い。[brief.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/brief.md:50)

- consumer「15/11/60参照」は計数対象が未定義。ASTで「attempt を含む `trial_registry` 属性」を数える再現可能な規則では production consumer 12、evidence の対象文字列12、test側80となる。値そのものより、metric definition が無いため編集影響の見積りに使えないことが問題。[brief.md:57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/brief.md:57) [p3_autonomous_workload_trial.py:1261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/p3_autonomous_workload_trial.py:1261) [test_trial_registry.py:5047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_trial_registry.py:5047)

- pilot wave の現物は射影外なので重複状態そのものは検証不能。**推測ではなく、親が記した検査方法だけを攻撃すると**、`git diff --name-only main...` が空でも未commit・未追跡編集は見ず、計画中の新 core という semantic conflict も見ない。従って「編集面の重なりなし」はその測定から導けない。[brief.md:96](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/brief.md:96)

## 安全な分割と裁定パッケージ

安全な切断点は次の通り。

1. **この wave:** 共通 pure core、8c facade、既存8c signature/alias/exception/event/receipt golden、C01–C12 不変検査まで。8b production file から新 core を import・call しない。
2. **次 wave:** 8b adapter/store と全 crash-cut transaction modelを pure state-machine として実装するが、launcher gateはまだ閉じる。
3. **統合 wave:** trusted launcher、scheduler evidence、journal/registry fencing、result/Markdown/stats/resume/admission checker/docs を同一 commit で配線する。途中状態を production から到達不能に保つ。

残りは次の裁定パッケージへ返すべきである。

- post-observation crash を「当該 repetition 永久欠測」とするか、次 attempt を主値へ昇格して estimand を変更するか。推奨は前者だが、これは「救出できない」ことを明示する裁定になる。
- scheduler wall timeout/node failure/preemption の正本証拠源と、SIGKILL/process disappearance を retryable に含めるか。推奨は scheduler accounting receipt がある場合だけ retryable、単なる PID 消失は不可。
- orphan job/claim を再取得する fencing generation と、誰が stale を宣言できるか。
- registry、journal、marker、attempt-ledger の conflict truth tableと recovery owner。
- v1 campaign は inspection のみ許可し、既存 consumption 後の genesis backfill は全面拒否すること。
- 8b closed retry reason set。段2が提案した集合は受理集合を変えるため、author判断で確定してはならない。[s2-plan.md:384](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/s2-plan.md:384)

pytest は制約どおり実走しておらず、以上は静的検査結果である。