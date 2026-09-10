静的検査の結果、must-fix は 4 件、裁定へ返すものは 1 件です。pytest・collection を含めテストは実走しておらず、緑の主張はしません。

## 所見 1 — campaign output root が二重化し、実 producer は必ず raw 生成前に失敗する

- file:line: [paper_story_a2_certification.py:2482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2482)、[layout.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/layout.py:248)、[paper_story_a2_certification.py:2115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2115)
- 具体的な経路: `run_workload()` は `output_root=jobs/rr5/campaigns` を渡す一方、`campaign_layout()` はさらに `campaigns/<cid>` を付加するため、実 layout は `jobs/rr5/campaigns/campaigns/<cid>` になる。その後 `_campaign_observation()` は親が `jobs/rr5/campaigns` であることを要求して拒否する。テスト helper は実 producer を使わず、期待側の `jobs/rr5/campaigns/<cid>` を手作りしている。
- **成果物影響: 実機 campaign は測定後の raw cell 作成へ到達できず、A-2 certification 成果物を一件も生成できない。**
- 推奨: **must-fix**。`run_campaign()` へは `job_root` を output base として渡し、claim path も同じ base から導出する。

## 所見 2 — campaign claim の `protocol_digest` が値として束縛されていない

- file:line: [loop.py:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/loop.py:209)、[paper_story_a2_certification.py:2541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2541)、[test_paper_story_a2_certification.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_paper_story_a2_certification.py:242)
- 具体的な経路: 正規 producer は bound config の canonical preimage から digest を算出するが、consumer は「64 桁 hex」だけを確認し、request ID・host・boot ID・campaign IDとのみ交差照合する。テストも実 digest ではなく `"a" * 64` を canonical positive としている。
- **成果物影響: campaign lock/config と無関係な protocol digest を宣言する claim が certification manifest に受理され得る。**
- 推奨: **must-fix**。再構成済み `CampaignConfig` から full digest を再計算して一致を要求し、digest 単独変異の負例を追加する。

## 所見 3 — `finish-group` が submit 専用 gate を継承し、正当な完了 group を過剰拒否する

- file:line: [submit_paper_story_a2_certification.sh:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/submit_paper_story_a2_certification.sh:65)、[submit_paper_story_a2_certification.sh:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/submit_paper_story_a2_certification.sh:71)、[submit_paper_story_a2_certification.sh:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/submit_paper_story_a2_certification.sh:91)
- 具体的な経路: mode 分岐より先に `qsub` の存在、`check_quota`、`qstat -Q` の ENA/ACT、repo clean を要求する。すでに終端した group の取得には qsub admission や active queue は不要だが、いずれかが落ちると `finish-group` に到達しない。
- **成果物影響: queue 停止・quota 検査障害などの時点で、完了済み 2 job の completion/acquisition を作れず成果物が取り残される。**
- 推奨: **must-fix**。批准・login・必要な `qstat` と receipt identity 検査だけを共通化し、qsub/queue/quota/submit用 clean-tree gate は submit branch へ移す。

## 所見 4 — 合成 qstat fixture は実機 block ではない 7 行抜粋を正例・負例の基礎にしている

- file:line: [qstat-visibility-fanout-945411.stdout:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/fixtures/paper_story_a2/qstat-visibility-fanout-945411.stdout:1)、[test_paper_story_a2_certification.py:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_paper_story_a2_certification.py:345)、[test_paper_story_a2_certification.py:864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_paper_story_a2_certification.py:864)
- 具体的な経路: 個々の field spelling は歴史 fixture と整合するが、実機 fixture は 94 行なのに新 fixture は 7 行しかない。receipt helper の全正例と多数の負例がこの抜粋を使用し、full-real test でも rr5 だけを歴史 fixtureへ差し替え、rr50 は抜粋のままである。
- **成果物影響: 実環境に出ない短縮 block の受理だけで group 契約を証明し、2 本の実形式 qstat block に対する互換性退行を見逃し得る。**
- 推奨: **must-fix**。歴史 fixture 全体を基に request ID と canonical log path だけを変えた 2 本を作り、負例もその full block から一字段だけ変異させる。

## 所見 5 — raw directory の余分な regular file が新たに受理される

- file:line: [paper_story_a2_certification.py:2568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2568)、[implementation.diff:1039](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s6/implementation.diff:1039)、[implementation.diff:1186](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s6/implementation.diff:1186)
- 具体的な経路: 旧版は `raw/` の regular-file 集合が正確に 4 cell であることを二層で検査した。新版は policy-derived path だけを直接開くため、例えば `jobs/rr5/raw/decoy.json` があっても manifest と acquisition が成立する。
- **成果物影響: 以前は拒否された汚染済み raw namespace から certification 成果物を作成できる。**
- 推奨: **裁定へ返す**。これは「受理集合を論理積以外に広げない」と「親 directory を列挙しない」の衝突である。共有親は走査せず、job-local `raw/` の closure だけ検査する案を裁定する。

## 受理集合の全差分

- 許可された拡大: scalar 1-job receipt では表現できなかった、順序固定の rr5/rr50 独立 campaign 2 本の論理積。
- 許可外の拡大: 所見 5 の job-local raw 余分 file。加えて所見 2 は新 claim consumer の値束縛漏れ。
- 意図した縮小: 旧 7 schema、flat layout、workload 無指定、単一 request receipt、順序違反、request/log path 重複、claim 不在、request/host/boot 不一致、片側 nonzero なのに manifest を主張する形は拒否される。
- 事故縮小: 所見 1 により実 producer の全 layout、所見 3 により submit admission が閉じた時点の有効な finish 操作が拒否される。
- 上記以外に、旧 validator の qsub/qstat、reservation、cell、performance、5反復、6時間の受理条件が緩和された箇所は見つからなかった。

## 反証 — policy rename と 7 契約 consumer

- 現物の版上げは [paper_story_a2_certification.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:41) で policy 1→2、submission 3→4、completion/acquisition/result 2→3、compute 1→2、raw manifest 2→3。
- operational source に旧 path・旧 7 schema literal は残っていない。明示 path consumer の T-1683 も [t1683_rr5_cost_probe.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/probes/t1683_rr5_cost_probe.py:20) で v2。
- 旧 filename は [s2-plan.md:218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/output/insights/2026-08-26_t1156-post-oracle-refetch-ban/verbatim/s2-plan.md:218) の歴史引用だけ、submission v3 は過去記録の一箇所だけで、consumer ではない。
- `git ls-files`/filesystem inventory、generated `pyc` の strings、`glob/rglob/iterdir` consumer、module import経路も確認した。A-2 policy JSON を暗黙に列挙する別 consumer はない。
- **成果物影響: rename による runtime consumer の v1 読み残しは反証された。**
- 推奨: **nit**。歴史記録は編集禁止どおり維持する。

## 反証 — 新 production file の inventory closure

- [test_hooks.py:3849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_hooks.py:3849) の再帰 `os.walk` は suffix・実行 bit・shebang の内容で新 `.sh` を拾う。
- registry class map、entry 全 field、local evidence、registry-derived sanctioned projection、明示 executable 検査にも追加済み。
- official-perf inventory は `tools/` まで内容走査し、新 file に perf predicate がないため正しく非対象。CCBench subprocess inventory は shell ではなく変更された Python module の新 subprocess site を追随済み。
- **成果物影響: 新実行体が inventory 外で無審査実行される経路は反証された。**
- 推奨: **nit**。実走されていないため inventory test の緑とは扱わない。

## 反証 — ledger、禁止事項、B-10 同形性

- 変更された4 test fileは旧版と現版で test function 名・parametrize decorator が同一で、ledger に全 base node が存在する。新規 nodeid 欠落 0 という報告は静的には正しい。duration の再計測は未実走。
- 投影された `s6/implementation.diff` に docs、Pegasus README、`output/insights/`、信頼根4 file、hooks、歴史 fixture の編集はない。skip/xfail・test削除・parametrize縮小もない。現在の HEAD にある親所有の verbatim output 2本はこの実装 diff には含まれないため、実装子違反には数えていない。
- registry は [admission_registry.json:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/admission_registry.json:268) の B-10 2本と同じ4 field構成で、`class="local-ok"` と `evidence="static login-side submitter classification"` が完全一致する。
- **成果物影響: node集合・禁止対象編集・registry形状に起因する追加の成果物欠落は反証された。**
- 推奨: **nit**。テスト実走 0 件という状態は別途解消が必要。

## 総括

- must-fix: **4 件**。裁定へ返す受理集合変更: **1 件**。テスト実走: **0 件**。
- 最重: campaign root 二重化により実 producer が raw を一件も作れない。
- 次点: claim の protocol digest が未束縛で、非正規 claim を受理できる。
- 3番目: finish-group が queue/quota/qsub gate を継承し、完了済み groupを取り残す。