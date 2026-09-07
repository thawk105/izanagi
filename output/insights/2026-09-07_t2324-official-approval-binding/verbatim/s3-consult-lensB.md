## 所見 (real)

- **B-1 [real] delimiter 検査は到達不能で、変異の帰属も成立しない。** plan は approval value の `,`・改行拒否と構造テストを追加するが、値は直前に 32 桁小文字 hex と検証済みの `$NONCE` そのものである。[s2-plan.md](/home/SFC/tanab/.claude/jobs/9b382fb4/tmp/t2324/artifacts/t2324-official-approval-binding/s2-plan.md:129)、[submit_floor.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/submit_floor.sh:299)。発火手順として nonce に `,` や改行を入れても `submit_floor.sh:304-307` が先に拒否するため、新 guard には到達しない。guard 削除を source 文字列検査で赤にしても、qsub delimiter 防護の動作証拠にはならない。仮想リスク向け gate に該当するため、guard と `test_submit_floor_checks_confirmation_value_for_qsub_delimiters_before_append` は plan から外すべきである。

- **B-2 [real] 未設定承認の順序について brief と plan が矛盾する。** brief は未設定も build・driver 前に拒否すると定める。[s1-brief.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/output/insights/2026-09-07_t2324-official-approval-binding/s1-brief.md:52)。しかし plan は承認 env 未設定なら `OFFICIAL_APPROVAL_BOUND=0` のまま続行し、driver argv から flag を省くだけである。[s2-plan.md](/home/SFC/tanab/.claude/jobs/9b382fb4/tmp/t2324/artifacts/t2324-official-approval-binding/s2-plan.md:147)。発火手順は `submit_floor.sh` を新 flag なしで実投入すること。job は gflags build へ進み [floor_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:985)、driver も起動する [floor_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:1200)。D926/D461 型では「未設定なら append しない」、早期 fail は空文字を含む不一致に限られるため、実装を強めるのでなく brief の「未設定も build・driver 前」を削るのが最小である。

- **B-3 [real] `test_ccbench_spawn_sites.py` の exact lineno pin が取り残されている。** 同登録簿は `s8b_floor_campaign.py` の `build_cells.invoke_build` を 4705、`main` の campaign sink を 8625 と固定し、path・scope・line の完全一致で照合する。[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:859)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:939)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:2642)。発火手順は parser flag や public/private 引数を plan どおり追加して production source の行をずらし、同登録簿を走らせること。`_deferred_member` が一致せず cross-product が未登録になる。新 process は増えないが lineno pin は変わる。実装で 4705/8625 を line-count-neutral に保つか、確定後の 2 lineno を登録簿の定義と自己 golden の双方で更新する必要がある。

- **B-4 [real] P1 の「生きた pilot consumer なし」はコード consumer に限れば正しいが、sanctioned 運用 consumer には反例がある。** [tools/pegasus/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/README.md:223) は引数なし `submit_floor.sh` を pilot 実投入コマンドとして掲げ、[phase3-8b-restart-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/phase3-8b-restart-runbook.md:193) の W-2 も現行の sanctioned 手順である。さらに plan の更新帯から次が漏れる。

  - README の旧 failure 文言は計画範囲 `217-257` 外の [260 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/README.md:260)。
  - W-2 の pilot run directory と repo 外退避手順は計画範囲 `229-241` 外の [244-252 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/phase3-8b-restart-runbook.md:244)。official result は `_validate_floor_inputs` が repo 相対 path から読むため、pilot と同じ即時退避手順を残すと downstream candidate 生成と衝突する。
  - W-3 は producer 不在と書く [262-272 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/phase3-8b-restart-runbook.md:262) が、`generate-v2-candidate` は既に実在する [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_freeze.py:2202)。
  - 「固定 pilot で走らせる」という現行形の決着文が [448 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/phase3-8b-restart-runbook.md:445) に残る。

  発火手順は実装後にこの runbook を順に実行すること。引数なし official job の投入、official result の不適切な退避、存在する candidate producer の不存在判定が順に起きうる。

- **B-5 [real] 成果物影響の記述が受理集合変更を過小評価し、保証範囲も広げすぎている。** brief は「certified 選択の値・受理集合は変わらない」としながら、直後に承認付き official の受理集合が広がると書く。[s1-brief.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/output/insights/2026-09-07_t2324-official-approval-binding/s1-brief.md:89)。また「標準投入経路でだけ起動可能」は、D926 が明示的に保証外とした raw qsub・CLI 直接・Python API 直接呼出しまで拒否する意味に読める。[verbatim-rulings.md](/home/SFC/tanab/.claude/jobs/9b382fb4/tmp/t2324/verbatim-rulings.md:80)。発火手順は実装後、CLI に flag を直接渡すか `run_campaign(..., confirm_official_floor_run=True)` を呼ぶこと。nonce 輸送の保証は無いが approval gate 自体は通る。正確には「launch/API の受理集合はこの commit で変わる。測定値と freeze/certified の選択結果は実投入まで変わらない。nonce 束縛保証は標準投入経路だけ」と書くべきである。

- **B-6 [real] brief の実アンカー表は 14 行あり、そのうち 4 行が file:line 粒度を満たさない。** A4 の `:8435` は official parser ではなく `freeze-protocol` の `--confirm-user-freeze` で、対象 `_parser` は [8393-8406 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:8393)。C1 は関数と docstring が 932-933 から始まる [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_freeze.py:932)。B1 は usage の 7-11 を落としている。D2/E1 は行番号自体が無い。発火手順は brief のアンカーだけを author に射影すること。A4 は別 parser を誤編集しうる。段2 plan はこれらの大半を補正済みだが、親 brief の検算結果としては real である。残る A1-A3、A5、B2-B4、C2、D1 の位置は現物と一致した。

- **B-7 [real] N4 の結論は維持できるが、`g1.json` を発火根拠に数える説明は誤り。** budget approval は floor job の投入器・job・driver のどこからも読まれず、official result 後の v2 candidate 生成で初めて読む。[s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_freeze.py:2014)。発火手順として `g1.json` を除いても `submit_floor.sh` の launch path は変わらず、逆に g1 だけ存在しても job は起動しない。DW-G04 の具体的根拠は既存 [floor_protocol.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/output/s8b-freeze/floor_protocol.json)、既存の `fetch_third_party.py hydrate` 経路、D1628 の reservation-bound default transport、実装後の source commit/script blob である。なお、この worktree では persistent third-party root は現時点で未作成なので、実投入前に既存 hydrate 手順が必要である。

## 所見 (refuted)

- **B-8 [refuted] D926 が不変とした 4 面への間接変更はない。**

  - 承認引数は public/private signature へ増えるが、`_nondefault_campaign_seams` の呼出しには渡さない。現行分類器は [7082-7115 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:7082) で 18 名集合との exact 一致を検査し、eligibility は [7118-7131 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:7118) の `official && fresh && seam zero` のままである。
  - 18 名集合本体は [s8b_floor_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_contract.py:40) のまま。テスト側の non-seam 除外集合へ承認引数を足すのは集合本体の変更ではない。
  - submission receipt は producer [submit_floor.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/submit_floor.sh:348)、job exact consumer [floor_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:629)、共有 leaf [floor_submit_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/floor_submit_receipt.py:13) の全てで従来 key のまま。approval は qsub env にだけ載る。
  - admission claim identity は [s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_admission.py:753) の 6 項目だけで、core が渡すのも mode/resume/nondefault seams まで [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:7872)。承認 bool は claim identity 材料へ流れない。

- **B-9 [refuted] D926/D1396/D1562/D323/D1628 の却下肢は復活していない。** append は `OFFICIAL_APPROVAL_BOUND==1` の条件付き、CLI/public/private core の三入口に gate が残る、receipt/result へ approval field を足さない、claim 前に検証する、mode は literal official 固定、Python core は raw env を読まない。default FetchContent は raw 引数 `None` のまま分類後、検証済み reservation nonce から導く既存経路である [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:3138)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:4289)。

- **B-10 [refuted] P2 の「文言だけ直し挙動不変」は支持される。** D926 の逐語は floor official submission の引数・nonce env・fixed argv・receipt/seam 不変を裁定し、v2 世代の発効経路には触れていない。[verbatim-rulings.md](/home/SFC/tanab/.claude/jobs/9b382fb4/tmp/t2324/verbatim-rulings.md:66)。v2 の record・approval・active chain は独立して [s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_ratified_freeze.py:1) と `load_ratified_freeze` [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_ratified_freeze.py:1418) が担う。さらに v1 側の上段コメント [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_freeze.py:912) が、v1 経路で世代 document を通すと未承認 floor/budget 差替えが fail-open する理由を既に説明する。plan の新 docstring も「v1 は世代承認を検証しない」「active v1 は worktree bytes 完全一致」と理由を残すため、封鎖の正当化は空洞化しない。

- **B-11 [refuted] N1/N2/N3/N5 と P4 の再検算結果は正しい。** 現行 floor submitter/job/driver に D461 nonce binding は無く、同名 flag は oracle N pilot の固定 literal 系だけである。nonce は [submit_floor.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/submit_floor.sh:299) と [floor_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:547) に既存する。N3 の明示 kwargs 分類も上記 B-8 のとおり。N5 も B-10 のとおり。P4 は現位置より先に `take_checkpoint_environment(os.environ)` が `pop` を行う [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:7256) ため、gate 前倒しが必要という plan の訂正が正しい。

- **B-12 [refuted] `_REVIEWED_PERF_FILES` / `_REVIEWED_PREDICATES` / `_REVIEWED_GUARDS` の更新は不要。** 変更対象 2 production file は既に file ledger にある [test_official_perf_closure.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_official_perf_closure.py:44)。新 approval gate は tracked perf call を増やさず、guard 条件にも perf 名を含めない。[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_official_perf_closure.py:106)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_official_perf_closure.py:266)。関数追加でもないため exact predicate/guard 閉包は不変である。

- **B-13 [refuted] conftest、admission registry、hooks の意味論登録更新は不要。** 改名・新設されるテストは real repo/shared ccbench を新たに読むものでも slow test でもない。既存 real E2E 名は不変で [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/conftest.py:377) の xdist 登録も維持できる。job body=`dispatch-required`、submitter=`local-ok` の分類も変わらない [admission_registry.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/admission_registry.json:70)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/admission_registry.json:316)。hooks はこの path 分類を読むだけで approval argv/env を pin していない。

- **B-14 [refuted] 成果物が効く production 層の取り残しはない。** 投入器、job script、CLI、public wrapper、private core は plan が全て触る。freeze は既に official result の path/mode、live admission、derived eligibility を検証してから候補へ射影する [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_freeze.py:1417)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_freeze.py:1620)。producer の `eligible_for_refreeze` 自己申告も live admission の再導出値と照合される [s8b_floor_stats.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_stats.py:1036)。freeze production 挙動を変更しないのは取り残しではない。

- **B-15 [refuted] DW-G04 を理由に設計メモへ戻す必要はない。** B-7 のとおり brief の根拠は修正が要るが、既存 protocol artifact、既存 hydration/submitter、既存 reservation-bound default transport があるため、実装後の新 source commit/script blobから official pathを発火できる。現 worktree に persistent source root が無いことは実投入前の既存運用手番であり、新しい実行機構を要求する blocker ではない。

- **B-16 [refuted] delimiter guard を除く plan の主要変異は専用テストへ帰属できる。** 無条件 append は未設定時の実 argv、二重 append は一致時の実 argv/count、public/core gate の片側削除は各専用未承認テスト、gate 後退は checkpoint env 未消費テスト、mode 受け口は token inventory が赤にする。materializer 拒否テストだけでは approval gate 削除を証明できないが、plan は別に `test_private_core_rejects_unapproved_official_before_side_effects` を設けているため mask は解消される。

## pin 閉包の全列挙

- **更新必須の production/source 面**

  - [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_floor_campaign.py:42): module 説明、`_assert_official_permitted`、launch コメント、public/private signature と call、gate 順序、parser、CLI。
  - [s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/s8b_holdout_freeze.py:932): `_reject_unratified_generation` と `_verify_source` の理由文言のみ。
  - [submit_floor.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/submit_floor.sh:7): usage/parser と qsub export。pre-submit/receipt payloadは不変。
  - [floor_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:544): nonce比較、raw env unexport、fixed official argv、job-result mode、失敗文言。

- **更新必須のテスト面**

  - [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_floor_campaign.py:775): official fixture、全 gate monkeypatch、CLI/public/private 正負例、non-seam 除外、call-order pin、旧 pilot flag 不在検査。
  - [test_pegasus_floor_tools.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_pegasus_floor_tools.py:1337): checkpoint 順序、nonce binding、actual argv/token、qsub export、job-result/failure golden。B-1 の delimiter test は除外する。
  - [test_s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_holdout_freeze.py:1285): 拒否継続と新理由。
  - [test_s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_ratified_freeze.py:940): gate monkeypatch を明示 `confirm_official_floor_run=True` へ。
  - [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_ccbench_spawn_sites.py:859): B-3。production sink line を保持できなければ 4705/8625 の 2 定義と 2 自己 golden を更新。
  - [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/acceptance_duration_ledger.json:1463): 改名 5 系統と新 test nodeid。plan どおり実 JUnit 後に正規 updater で再生成し、旧 nodeid を残さない。

- **更新必須の living docs**

  - [tools/pegasus/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/README.md:217): 計画帯を 260 まで広げる。
  - [phase3-8b-restart-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/phase3-8b-restart-runbook.md:49): 49、165-260、262-272、448-449 を対象にし、pilot 完走は dated history、現行投入と post-run は official と分ける。
  - [pegasus-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/pegasus-runbook.md:1641): sanctioned command と raw qsub 非保証範囲。
  - [phase3.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/docs/phase3.md:64): dated historyは残し、112-126 付近へ T-2324 による supersede と launch受理集合変更を追記。

- **変更不要と確認した pin**

  - 18 名 exact test [test_s8b_floor_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_floor_contract.py:187)。
  - 6 項目 effect key test [test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_s8b_holdout_admission.py:293)。
  - receipt exact-key test [test_floor_submit_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_floor_submit_receipt.py:230)。
  - official perf の 3 登録簿、conftest group、admission registry、hooks。
  - `test_frozen_artifacts.py` の全体 sha256 goldenは output artifactだけで、変更予定 fileを含まない [test_frozen_artifacts.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/tests/test_frozen_artifacts.py:29)。
  - 変更予定 12 file の現 sha256 値を値側から検索したが literal pin は 0 件だった。active v1 freeze の `generator.sha256=1910fff...` は既に現 source hashと異なる歴史 metadataで、T-080 receiptにより扱われるため更新しない。
  - [floor_submit_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/orchestrator/campaign/floor_submit_receipt.py:131) の script blob binding は dynamic hash比較である。新 commit の job script hashは submitterが新規 receiptへ記録し、job側も executing bytes・commit blob・receiptの三者一致を検査する [floor_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2324-official-approval-binding/tools/pegasus/floor_campaign.sh:697)。固定値更新は不要。
  - 既存 `output/env/pegasus/floor/attempts/submissions/*` の 3 receiptは旧 pilot submissionの歴史証拠であり変更しない。
  - `docs/decisions.md`、`docs/failures.md`、dated paper-story、archive worklog、既存 insightは書き換えない。

## 並行 wave との衝突

- `worktree-dev-wave-acceptance-speedup-20260905` の `test_s8b_floor_campaign.py` 変更帯は base の import 86-89、snapshot helper 1693-1720、1759 後の追加である。plan の 775-825、6347 以降の official 帯とは hunk が重ならない。同行競合はない。

- 同 branch は実際には `test_ccbench_spawn_sites.py` と `conftest.py` も触っている。spawn file の変更帯は base 25、55-58、182-186、2919、3485 付近で、B-3 の登録簿 859-945 / 2642-2725 とは直接重ならない。ただし同一 file 所有を避ける最小策は production sink の 4705/8625 を line-count-neutral に保つこと。保持できない場合は acceptance branch 統合後に exact 2 linenoだけを更新する。

- `worktree-dev-wave-t1851-unit-a` の `test_official_perf_closure.py` 変更帯は `_REVIEWED_PERF_FILES` 62、`_REVIEWED_PREDICATES` 181、`_REVIEWED_GUARDS` 295 付近である。本 plan は同 fileを編集不要なので衝突しない。t1851 は `s8b_floor_contract.py` も触るが、18 名集合はその diff の対象外である。

## plan へ入れるべき最小の修正

- `$NONCE` の delimiter guard とその構造テストを削除する。32 桁 hex gateを唯一の根拠にする。
- brief の未承認不変条件を D926/D461 型に合わせ、「空文字・不一致は jobで build前拒否。未設定はflagを付けずCLI/coreが拒否」に直す。
- `test_ccbench_spawn_sites.py` の 4705/8625 pinを planへ明記する。第一候補はproduction sourceのline-count維持、できなければ確定linenoの更新。
- docs帯を README 260、restart runbook 165-272 と 448-449 まで広げる。W-3 の既存 candidate producerも現況へ直す。
- 成果物影響を「launch/API受理集合は変わる、測定値とfreeze/certified結果は未投入なので変わらない、nonce保証は標準投入だけ」に訂正する。
- N4 は g1 budgetをlaunch根拠から外し、既存 protocol artifact、hydrate経路、reservation-bound default transport、新source commit/script hashをDW-G04 witnessとして明記する。
- acceptance ledgerは実測後更新のままでよい。conftest、official perf closure、admission registry、hooks、receipt/claim schemaは触らない。

## 総括

方式本体は D926 に適合し、禁止された4面や却下肢を復活させていない。P2 も挙動不変で支持でき、DW-G04を理由に実装を止める必要はない。

plan に必要な実質修正は、到達不能なdelimiter gateの削除、未設定承認の順序記述の訂正、`test_ccbench_spawn_sites.py` のlineno pin閉鎖、runbook/READMEの更新帯拡張、受理集合とDW-G04根拠の表現修正である。

pytest・実投入は行っておらず、所見は静的読解と検索のみである。repo fileは変更していない。`git status --short` に見えた未追跡 `output/insights/2026-09-07_t2324-official-approval-binding/` にも書き込んでいない。