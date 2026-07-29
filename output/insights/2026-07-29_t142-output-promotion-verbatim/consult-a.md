指定された全資料・指定 decision 節は全文読了できた。現行コード、schema、既存テスト、WAL 読み手を静的に追跡した。read-only のため編集・pytest 実走はしておらず、緑は主張しない。

### F1 — BLOCKER / real: direct-winner はユーザー裁定から導けず、選んでも O 保存は未証明

承認文は selection frontier を「new-best 等」としか定めず、親 brief 自身も比較・tie を provisional としている。[ruling-package.md:77](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-28_t142-tiering-ruling-package.md:77)、[parent-brief.md:11](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/parent-brief.md:11)、[plan.md:23](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:23)

現行にも二つの相反する意味論がある。

- `winner_tied_set()` は no-difference の推移閉包で、100–98–96 の橋渡しを既存テストが明示的に固定している。[replay.py:176](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/replay.py:176)、[test_guided.py:189](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_guided.py:189)
- `p2_2_report` は winner と各候補の直接比較である。[p2_2_report.py:149](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p2_2_report.py:149)

さらに direct-winner を選んでも、現在 incumbent に明確に遅い候補が、将来 winner と統計的 no-difference にならない証明はない。`compare()` 自身が Mann–Whitney を「弱い sanity」と位置づけており、strict weak order や推移性を与えていない。[stability.py:223](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/calibrator/stability.py:223)

`O_select = O_run のみ` は「未認証値を出さない」という soundness は示すが、「本来 selected/tie に入る候補をすべて S2 に送った」という completeness を恒真化してしまう。

成果物影響: 真の winner/tie 候補が永久 `not_promoted` になり、certified 選択、正式レポート、proof chain が all-S2 反実仮想と異なる。

最小修正・停止条件: tie、winner、unstable、incumbent 更新規則を追加ユーザー裁定で凍結する。その後も比較関係の安全性を証明できなければ、全件 S2、または最終 winner 決定後に候補を backfill する deferred 方式へ戻す。D96 の新 D は記録手続であって、未裁定の意味論を AI が選ぶ許可ではない。[decisions.md:4269](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/decisions.md:4269)

### F2 — BLOCKER / real: plan に最終 selection producer と certified stock がない

plan は `O_select` から selected/stock/tie を生成すると宣言するだけで、実装順には selector、selection schema、renderer、stock 認証経路がない。[plan.md:34](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:34)、[plan.md:70](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:70)

現行 layer3 は `runs/verifications/rejects/aborts` を並べるだけで selection を持たない。[layer3_report.py:369](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_report.py:369) 一方、phase/roadmap は operational selected/stock/tie と baseline/variant 分布を要求する。[phase3.md:427](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/phase3.md:427)、[roadmap.md:131](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/roadmap.md:131)

sort/trigger driver も変異 genome だけを評価し、同一 adaptive campaign 内に stock 候補を作らない。[p3_s4_loop_sort.py:200](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop_sort.py:200)、[p3_s4_loop_trigger_gating.py:355](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop_trigger_gating.py:355)

成果物影響: S2 済み変異の中の最速を出せても、stock/tie を正式に選べない。certified 選択と proof chain の受理条件そのものを検査できない。

最小修正・停止条件: 一つの authoritative selector を新設し、同一 config の O-certified stock を先に作る。`selection_status="unavailable"` は親の selected/stock/tie 契約の黙った縮退なので、stock を実装しないなら別途ユーザー裁定が必要。

### F3 — BLOCKER / real: `build_start` 区切りだけでは試行を一意に再構成できない

WAL の lock は一レコードの append 中だけで、試行全体の排他ではない。[wal.py:283](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/wal.py:283) `run_campaign()` も replay 後のローカル `done` しか持たず、二プロセスが同じ variant を同時評価できる。[loop.py:76](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/loop.py:76)

したがって `start(q1), start(q2), verify(q1), bench(q1), commit(q1)` と interleave すると、plan の「次の build_start まで」という境界は q1 の tail を q2 に誤帰属する。[plan.md:29](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:29)

既存 replay は commit/abort の存在を sticky にするだけで、複数 terminal、terminal 後 event、重複 COMMIT を拒否しない。[wal.py:566](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/wal.py:566)、[test_campaign.py:1111](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_campaign.py:1111) retryable abort→新 build_start→crash も既存の正規履歴である。[test_campaign.py:2702](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_campaign.py:2702)

また通常 reader は crash tail を捨てるが、layer3 は fail-closed で拒否する。共通 O helper がどちらを正本にするか未指定である。[wal.py:540](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/wal.py:540)、[test_layer3_report.py:226](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_layer3_report.py:226)

成果物影響: 別試行の S2、bench、COMMIT が結合され、certified 選択・proof chain が偽陽性になる。retry/crash/複数 terminal が全試行台帳から潰れる。

最小修正・停止条件: 新 adaptive WAL は全 stage に immutable `attempt_id` を持たせ、attempt ごとに「一 build_start、一 terminal、terminal 後 event 禁止、required verify tag 一意」を FSM 検査する。代替は campaign 全体の single-writer lock。旧 WAL は serial topology を一意に検証できる履歴だけ推論し、曖昧なら O certification unavailable とする。

### F4 — BLOCKER / real: S2 の実行証明が tag 依存で恒真化する

`extra_correctness` は任意の `(tag, workload)` を受け入れ、`verify_done` は tag、verdict、件数しか記録しない。[pipeline.py:423](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:423)、[pipeline.py:583](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:583) COMMIT 側も `verify_configs=["legacy","s2"]` という文字列だけである。[pipeline.py:729](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:729)

したがって縮小 workload を `s2` と命名すれば、plan の V/A/O helper を通せる。D36 が要求する records、threads、extime、flags、clocks、numactl の実値を proof chain から復元できない。[decisions.md:877](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/decisions.md:877)

さらに replay は COMMIT があれば O 検証より先に永久 skip するため、adaptive campaign に壊れた COMMIT が一度書かれると、その候補を再検査せず選択集合から固定的に除外・混入できる。[loop.py:76](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/loop.py:76)

成果物影響: 実 S2 未実行の候補が certified 選択・正式 `runs`・proof chain に昇格する。壊れた COMMIT は resume 後も全試行台帳上「完了」に見える。

最小修正・停止条件: `verify_done` に canonical workload/config digest と実行契約を焼き、campaign.lock、bench、COMMIT が同じ attempt/config digest/env を参照するようにする。adaptive resume の preflight で全既存 COMMIT を O_run 検査し、一件でも不正なら campaign 全体を停止する。

### F5 — BLOCKER / real: 現行実データ経路では promotion の skip 分岐が発火しない

現行 driver の bench は 100k records、4 threads、extime 1、reps 2 であり、コード自身が「性能比較用 calibration ではない」と明記している。[p3_s4_loop.py:509](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop.py:509) 一方 S2 は D36 の 1m/48/extime 3 であるため、現在のままでは bench と S2 が同一 workload/config ですらない。

planner の「現動作点に exact floor がない」は正しい。[plan.md:22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:22) ただし影響を過小評価している。floor 無しなら全件 S2 なので短縮はゼロである。さらに reps=2 の完全分離でも現行 Mann–Whitney 実装は `p≈0.245` となり、α=.05 の `slower` 自体が到達不能である。[stability.py:168](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/calibrator/stability.py:168)、[stability.py:281](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/calibrator/stability.py:281)

成果物影響: synthetic unit testだけが枝を通り、実 campaign では全件 S2、または wiring-scale TPSを正式性能として扱う。後者は certified 選択・正式レポート・proof chain を壊す。

最小修正・停止条件: adaptive opt-in を D36 と同一の正式 perf/S2 config、十分な reps、完全一致 floor へ移す。実データで `not_promoted` 正例が出るまで効果を受理しない。親 brief は新規性能測定を禁止しているため、今 wave では dormant plumbing までしか主張できず、T-142 の短縮効果完了は別の許可された ablation まで停止する。[parent-brief.md:22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/parent-brief.md:22)

### F6 — HIGH / real: critic の規律3信号と whiteboard 停止意味論を誤って変える

plan は性能 digest と verify abort signal の両方を O 適格性で gate する。[plan.md:100](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:100) しかし現行 verify abort signal は、verify に到達した各候補の最初の legacy `verify_done` を読む規律3信号である。[digest.py:387](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/critic/digest.py:387)

`not_promoted` は legacy 緑の後なので、性能値は遮断しても legacy commits/aborts は実観測として残すべきである。S2-red も性能からは除くが、verification rejection としては残す必要がある。

また whiteboard の convergence は `result != "rejected"` を評価済みとして数える。[p3_s4_loop.py:306](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop.py:306) `not-promoted` を数えるか否かで停止時点と将来候補数が変わるが、plan に裁定・テストがない。成功 bench 後に `first_bench=False` とする案も、現行 `EvalResult` に bench 完了 field がなく、内部 `_BenchResult` の変更だけでは loop に伝わらない。[pipeline.py:126](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/pipeline.py:126)、[loop.py:154](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/loop.py:154)

成果物影響: critic の次手と stop 時点が変わり、最終 certified 選択が別物になる。正式レポート上も「S2未実行」と「verifier-red」が混同・欠落する。

最小修正・停止条件: 性能 O、legacy verify signal、S2 rejection、liveness rejection、S2NotRun を別 predicate/type にする。`bench_completed` を公開結果へ持たせる。not-promoted の convergence/reverse-budget 意味論を明示して境界テストを追加する。

### F7 — BLOCKER / real: layer3 payload redaction は D12 の完全射影と両立しない

D12 は全 run 値を含む WAL+whiteboard の完全・決定論的射影を「死守」としている。[decisions.md:159](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/decisions.md:159) 現行 renderer も raw event 全体を `variants.events` に置き、その event body から source hash を再計算する。[layer3_report.py:149](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_report.py:149)、[layer3_report.py:192](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_report.py:192)

plan の source_ref/stage/time だけの射影と「JSON 全体から sentinel 不在」は、完全射影を参照カタログへ変更する。[plan.md:64](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:64)、[plan.md:124](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:124) hash が残っても payload の完全性・再生成可能性は証明できない。

加えて現行 report は COMMIT 無しを一律 `commit-event-absent` reject とするため、第三 terminal を追加するだけでは `not_promoted` が promotion outcome と reject の二重分類になる。[layer3_report.py:362](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/layer3_report.py:362)、[test_layer3_report.py:413](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/tests/test_layer3_report.py:413)

成果物影響: 正式レポートが全試行台帳でなくなり、source_ref から監査値を再構成できない。not-promoted が correctness reject に見え、proof chain の意味が変わる。

最小修正・停止条件: full forensic `variants.events` には全 payload を残し、`runs`、selection、critic、certified claims だけを O_run に制限する。attempt ごとの terminal を committed/aborted/not-promoted/incomplete に排他的分類する。JSON 全体 redactionを維持するなら D12 supersede の追加ユーザー裁定が必要。

### F8 — HIGH / real: v3 の予約転用は現行 freeze に反する

phase3 は v3 を機序仮説原料配線に予約している。[phase3.md:411](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/docs/phase3.md:411) plan はその予約を certification projection に転用し、機序仮説を次版へ送る案である。[plan.md:68](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:68)

成果物影響: `layer3-material-report/v3` の意味が既存設計と食い違い、下流 schema consumer と proof chain の版解釈が分裂する。

最小修正・停止条件: v3 に予約済み機序区画と認証区画を同時に含めるか、別版を選ぶ。予約を後送りするなら追加ユーザー裁定が必要で、新 D だけで黙って転用してはならない。

### F9 — HIGH / real: live consumer closure が不足している

取り残しは少なくとも次である。

- whiteboard `check_stop()` の not-promoted 意味論。[p3_s4_loop.py:288](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop.py:288)
- variant 単位 last-wins を使う duplicate 復元。[p3_s4_loop.py:558](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/p3_s4_loop.py:558)
- 任意 campaign dir を受け、variant 単位で bench→COMMIT を結ぶ plotting。[plot_backoff.py:110](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/tools/plotting/plot_backoff.py:110)
- authoritative final selector/selection renderer 自体。F2 のとおり未計画。

成果物影響: retry 後の別試行 bench が plotting の certified 値になり得る。whiteboard stop が候補集合を変え、最終選択も変わる。

最小修正・停止条件: consumer matrix を「adaptive policy を読める／明示拒否／campaign identity 上到達不能」に分類し、到達可能な consumer は共通 attempt/O helper を使わせる。慣例上使わないだけでは閉集合にならない。

### F10 — BACKLOG / refuted: replay・p2・s6/s8・guided・freeze の一律改修までは不要

P2 replay は固定 slug/search-tag から専用 campaign を発見する。[replay.py:87](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/replay.py:87) s6/s8 も独自 config/trial から layout を再構成する。[s6_sort_sweep.py:162](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/s6_sort_sweep.py:162)、[s8a_trigger_sweep.py:202](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/orchestrator/campaign/s8a_trigger_sweep.py:202)

adaptive key が campaign identity を確実に分離し、各 legacy consumer がその profile を拒否するなら、guided/freeze を含む歴史的 consumer の選択結果は変わらない。

成果物影響: 上記の機械的分離を置く限りなし。分離を置かず任意 layout を渡せるなら F9 に昇格する。

最小修正: blanket rewrite ではなく、profile guard と到達不能テストを追加する。

### F11 — HIGH / real: 325件と88%は受入・効果の証拠にならない

325 passed/9 skipped は親の変更前 baseline であり、現在の「未 COMMIT bench を layer3 runs へ入れる」挙動まで被覆している。[parent-brief.md:21](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/parent-brief.md:21) 新しい O 境界や third terminal の証拠ではない。

88% は30 WAL・混合 campaign/config の COMMIT 426件を raw 時系列 new-best で数えた counterfactual である。[ruling-package.md:16](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-28_t142-tiering-ruling-package.md:16) tie、near-floor、unstable、stock、正式 config を含まない。planner は外挿不能を正しく認めている。[plan.md:154](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:154) 現行 config では F5 により実際の削減はゼロ見込みである。

成果物影響: これらを wave の受入や正式効果として使うと、proof chain に存在しない短縮効果が記載される。

最小修正・停止条件: 325件は回帰開始点、88%は歴史的上限推定とだけ表示する。正式効果は同一 config の paired ablation と実 `not_promoted` 発火まで主張しない。

### F12 — HIGH / real: mutation matrix は一部しか単一理由 kill を保証しない

対象は [plan.md:129](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t142-output-promotion/output/insights/2026-07-29_t142-output-promotion-verbatim/plan.md:129)。

| plan の変異 | 敵対判定 |
|---|---|
| faster/slower 反転 | 条件付き kill 可。ただし tie/O が未凍結なので「O受理集合を変えた」とはまだ判定不能 |
| no-difference を not-promoted | 同上。direct/transitive 裁定後の tie 正例が必要 |
| near_floor 無視 | 純粋 comparator fixture なら kill 可 |
| floor 不在を skip | kill 可。`compare()` を呼ぶ前の分岐到達を正対照で示す必要あり |
| not_promoted を resumable/abort | 不十分。複数 terminal、terminal 後 event、retryable abort 後 crash が未変異 |
| 過去 COMMIT と新 bench を結合 | 不十分。attempt_id 不在では concurrent interleave を区別できない |
| verify_configs 文字列だけで認証 | 不十分。偽 `s2` tag、誤 flags/extime/numactl は生存する |
| layer3 を全 bench 射影へ戻す | `runs` に限定すれば有効 |
| critic を全 bench 読みに戻す | raw sentinel の存在と valid O 正例を先に確認すれば有効 |
| 未認証 payload を variants.events へ戻す | D12 下では逆。正しい完全台帳を殺す mutation になっている |
| opt-in key を identity から除く | 不十分。PerfConfig/floor hash/alpha の個別欠落 mutation が必要 |
| certified run まで redact | 認証 run 正対照があれば有効 |

追加で必要なのは、fake-S2-config、wrong floor coordinates/source hash、attempt/env cross-binding、二重 terminal、malformed adaptive COMMIT resume、unstable inclusion、final selector の helper bypass、not-promoted の convergence/duplicate 誤分類である。

成果物影響: mutation が先行 schema error や未到達枝に食われても kill 扱いになり、certified 選択・正式レポート・proof chain・全試行台帳の境界検査を偽装する。

最小修正・停止条件: 各 mutation fixture で「変更前は対象枝へ到達し O に入る／入らない」を先に確認し、一フィールドだけ変え、最初に落ちる assertion を固定する。F1/F3/F7 が解消するまで mutation acceptance を開始しない。

## 総括

**判定: NO-GO。** plan のまま実装段へ進めてはならない。

must-fix は以下である。

1. selected/winner/tie/unstable/incumbent 更新の意味論を凍結し、promotion が O の soundnessだけでなく completeness を保存する証明を置く。
2. authoritative selector と同一 config の certified stock を実装する。
3. attempt identity、厳密 terminal FSM、実 config digest による S2/bench/COMMIT 束縛を導入する。
4. D36 と同一の正式 perf config、exact floor、統計分岐が到達可能な reps を使う。
5. critic の性能・legacy verify・S2-red・S2NotRun を分離し、whiteboard 停止意味論を凍結する。
6. layer3 は D12 の full ledger を保持し、certified view だけを O_run に限定する。
7. consumer closure と mutation matrix を上記境界に合わせて再構成する。

**追加ユーザー裁定は少なくとも tie/winner 意味論について必須。** さらに plan 通りに `selection_status=unavailable` を許す、D12 を payload-redacted report へ変更する、予約済み v3 を転用する、のいずれかを選ぶなら、それぞれ追加裁定が要る。これらは stock 実装、D12 維持、v3 予約維持を選べば追加裁定を回避できる。