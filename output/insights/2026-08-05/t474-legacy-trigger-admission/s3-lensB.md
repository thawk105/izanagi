# 所見

静的・read-only レビューのみを行った。テストは実行しておらず、「緑」とは判定していない。

### F-1 — 後発裁定は実在するが、プランは権威を誤認し supersession の内容を固定していない — severity: blocker 候補

- 根拠: [s2-plan.md:11](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/out/s2-plan.md:11>) の「ユーザー選択記録はない」は誤り。[rulings-session-5rulings.md:101](</work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md:101>)〜105 に、2026-08-05 の発話と **`[T-409] = 択一 A=(a) 破棄 + C 縮小版`** が明記され、[docs/worklog.md:1036](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/worklog.md:1036)〜1044、[同:1247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/worklog.md:1247)〜1252 に既に fold 済みである。一方 D160 は6件の遡及被害ゼロを決定し [docs/decisions.md:7930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/decisions.md:7930)〜7936、6件の拒否反転を明示的に却下している [同:7955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/decisions.md:7955)〜7963。

- 攻撃シナリオ: [s2-plan.md:163](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/out/s2-plan.md:163>) の一文だけで land すると、後続作業者が D160 を正本として6件を admitted と扱う一方、runtime は拒否する二重権威になる。

- 成果物影響: raw `AdmittedCampaign` の受理集合が6件縮小し、新規 Layer3 発行も6件で不能になる。それにもかかわらず canonical decision 上は「遡及被害ゼロ」が残り、材料レポート・凍結選択・trial 検証がどちらの解釈を採るかで分裂する。

- 提案: 後発裁定による限定 supersession 自体は正当であり、再裁定は不要。ただし D96 [docs/decisions.md:4271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/decisions.md:4271)〜4279 に従い、実装・境界テストと同じ変更単位に新 D の spool fragment を含めること。新 D は、D160 決定5のどの文と却下案を置換するか、6件だけを拒否すること、D160 決定1〜4・post-policy 規則・既存凍結 bytes を置換しないことを逐語的に限定すべきである。

### F-2 — 親 brief の P2 は裁定前のまま、P3 はユーザー裁定を実質的に満たさない — severity: must-fix

- 根拠: P2 は「Aならユーザー再裁定」としている [s1-brief.md:52](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/s1-brief.md:52>)〜54 が、その再裁定は既に存在する。P3 は受理集合を維持して `AdmittedCampaign` を発行し続ける [同:55](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/s1-brief.md:55>)〜58。プランの指摘どおり [s2-plan.md:7](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/out/s2-plan.md:7>)、これは「admitted view を名乗らせない」と逆である。

- 攻撃シナリオ: 段4が brief の provisional P3 を採用すると、6件は証拠 field が `legacy-unbound` になっても `require_admitted_campaign` を通過する。

- 成果物影響: 6 campaign の受理集合と Layer3 発行可能集合は現状のままになり、材料レポートが出続ける。裁定を満たしたとの表示だけが追加される。

- 提案: P2 は「2026-08-05 裁定により解消済み」に訂正する。P3 は T-474 の代替ではなく、T-473 相当の claim-boundary 改訂として分離する。

| brief 項目 | 確定済み権威との照合 |
|---|---|
| P1 | 食い違い無し。D160 自身も machine materializer を非主張として残す |
| P2 | 食い違い有り。再裁定は既に完了 |
| P3 | 食い違い有り。「admitted view」を残す |
| P4 | 食い違い無し。ledger は裁定でも費用次第 |

### F-3 — admission gate を通らない凍結 consumer が残り、grandfather 境界が未記録 — severity: blocker 候補

- 根拠: `s1_known_axes_freeze.py` は6件の provenance を直接読む [orchestrator/campaign/s1_known_axes_freeze.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s1_known_axes_freeze.py:471)〜499。検証時も `require_admitted_campaign` を通さず、source hash と再構成結果だけを照合する [同:718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s1_known_axes_freeze.py:718)〜766。実際の freeze は旧 campaign を参照している [output/s1-freeze/known_axes_freeze.json:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/output/s1-freeze/known_axes_freeze.json:36)〜43、S8B holdout も同様である [output/s8b-freeze/holdout_freeze.json:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/output/s8b-freeze/holdout_freeze.json:214)〜221。

- 攻撃シナリオ: A の land 後、同じ campaign は raw consumer には `legacy-unclassified` として拒否されるが、freeze verifier はその provenance から既知軸を再構成し続ける。

- 成果物影響: 既存 certified 選択の source reference 集合は6件を保持する。一方で admission-aware 材料では同じ6件が拒否されるため、「既存選択だけ grandfather する」のか「その proof chain も無効化する」のかが未定義になる。後者なら frozen bytes の再発行が必要になり、所有境界を破る。

- 提案: frozen files は編集せず、新 D に「既存 exact-hash 凍結 derivative は grandfather するが、新しい `AdmittedCampaign`・Layer3 は発行しない」と明記する。既存 derivative まで無効化する意図なら、この wave では実装せず再裁定へ返す。

### F-4 — 新 field 案では大半の consumer が証拠状態を読まず、表示だけの保証になる — severity: must-fix

- 根拠: P3 は「consumer に明示掲載を義務付ける」とする [s1-brief.md:55](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/s1-brief.md:55>)〜58 が、`s8a_trigger_sweep` は view の WAL だけを読み [orchestrator/campaign/s8a_trigger_sweep.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s8a_trigger_sweep.py:524)〜540、`certified` 行と性能値を出す [同:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s8a_trigger_sweep.py:570)〜631。critic も decision を解釈しない [orchestrator/critic/digest.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/critic/digest.py:456)〜464。

- 攻撃シナリオ: post-policy machine sweep に `machine-sweep-unbound` を付けても、s8a report・critic digest・replay 下流はその値を読まず、通常の admitted WAL として集計する。

- 成果物影響: 材料レポートの `certified` 行、median TPS、候補集合が証拠不足を反映せず維持される。将来非正準述語が流れた場合も、field は存在するだけで受理集合を変えない。

- 提案: B を別 task で採るなら、少なくとも s8a report、critic、Layer3、autonomous trial cell/report の各 claim issuer に、表示または拒否の閉じた規則を定義する。単に receipt へ field をコピーしただけで「consumer 結線済み」と数えない。

caller の全列挙結果は以下。production の `require_admitted_campaign` 呼び出しは `critic/digest.py:459,706`、`s6_sort_sweep.py:421`、`p3_s4_loop_sort.py:484`、`autonomous_trial_completeness.py:1085`、`p3_s4_loop.py:281,960`、`s8a_trigger_sweep.py:525`、`layer3_report.py:375`、`replay.py:107`、`p3_s4_red.py:170`。production の `classify_campaign` caller は無し。test-only caller は `test_p3_s4_loop_trigger_gating.py:118`、`test_p3_s4_loop.py:85`、`test_p3_s4_loop_sort.py:83`、`test_critic.py:69,171`、`test_artifact_admission.py:247–652`、`test_bench_first_real_wal.py:144` である。狭い A は中央 gate なので、この列挙内に raw-view の取り残しは無い。

### F-5 — 親 P3 の同一 schema version への必須 field 追加は persisted contract を in-place 変更する — severity: must-fix

- 根拠: Layer3 v3 は `admission_decision` の exact schema を持つ [orchestrator/campaign/layer3_schema.json:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/layer3_schema.json:22)〜55。完全性検査も decision の exact key 集合を固定し [orchestrator/campaign/autonomous_trial_completeness.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/autonomous_trial_completeness.py:55)〜62、byte 完全一致を要求する [同:987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/autonomous_trial_completeness.py:987)〜1011。プラン自身もこの問題を正しく認識している [s2-plan.md:99](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/out/s2-plan.md:99>)。

- 攻撃シナリオ: decision-v1 / Layer3-v3 のまま `trigger_membership_evidence` を required にすると、旧 v3 は field 欠落、新 v3 は completeness 側の未知 key として拒否される。

- 成果物影響: Layer3 材料レポートが schema failure になり、autonomous trial の cell・persisted report・trial 台帳が campaign-chain failure になる。

- 提案: B なら decision v2 / Layer3 v4 とし、v2 report、旧 v3+decision-v1、新 v4 の明示的 compatibility reader を設計する。autonomous trial report v2 を維持するなら、nested schema evolution で足りる理由も明記して exact-key consumer を更新する。

### F-6 — A でも validator SHA が全 campaign で変わり、repo 外の旧 trial receipt を失効させる — severity: must-fix

- 根拠: receipt の validator SHA は `artifact_admission.py` 自身の全-file hashである [orchestrator/campaign/artifact_admission.py:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:529)、[同:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:99)〜119。completeness は新しい expected receipt と完全一致させる [orchestrator/campaign/autonomous_trial_completeness.py:1085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/autonomous_trial_completeness.py:1085)〜1108。CLI は repo 外を含む任意 `--run-root` を正式に許す [orchestrator/campaign/p3_autonomous_workload_trial.py:1950](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/p3_autonomous_workload_trial.py:1950)〜1978。プランも危険を認識するが未解決である [s2-plan.md:79](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/out/s2-plan.md:79>)。

- 攻撃シナリオ: T-474 前に生成された非 trigger campaign の v3 trial を再検証するだけでも、campaign bytes は同じなのに validator SHA が変わり exact comparison が失敗する。

- 成果物影響: trigger と無関係な trial cell まで受理集合から落ち、試行台帳の再認証・resume が不能になる。repo 内には現時点で v3 receipt がなく、6 machine report は v2、proposal は v1だったが、custom run-root の不存在までは証明できない。

- 提案: land 前に権威ある run-root を棚卸しする。旧 receipt があれば、exact old-validator hash の限定 compatibility、または明示的な失効・再走のどちらを採るか決定に含める。

### F-7 — post-policy machine sweep と将来 generator は開いたままで、durable な後続所有が無い — severity: must-fix

- 根拠: `validate_trigger_bindings` は machine campaign なら空 dict で通す [orchestrator/campaign/wal.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/wal.py:753)〜759。現行テストも admitted を固定する [orchestrator/tests/test_artifact_admission.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:340)〜352。producer は quarantine に canonical-membership 証明を渡さない [orchestrator/campaign/s8a_trigger_sweep.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s8a_trigger_sweep.py:419)〜424、[同:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s8a_trigger_sweep.py:441)〜450。プランは穴を認めている [s2-plan.md:178](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/out/s2-plan.md:178>) が、owner/task を定めない。

- 攻撃シナリオ: 将来 `predicate_for` が quarantine を通る非正準一行述語へ drift すると、post-policy machine sweep は binding 無しで admitted になり、s8a report へ流れる。

- 成果物影響: post-policy の受理集合に32集合外候補が入り、その TPS・verification・`certified` 行が材料へ載る。将来の freeze・選択入力へ波及し得る。

- 提案: T-474 は「歴史 raw-view だけ」と明記し、この層を別の裁定パッケージへ durable に起票する。T-472 の S1 consumer membership と T-473 の claim boundary だけでは、s8a producer 自身の穴は閉じない。現 wave では所有境界上 `s8a_trigger_sweep.py` を編集しない。

## 無しと確認した項目

- **直接の所有境界違反:** 無し。プランは `s8a_trigger_sweep.py`、`output/s1-freeze/`、並行所有中の2ファイルを編集対象外としている [s2-plan.md:153](</work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/out/s2-plan.md:153>)〜161。`artifact_admission.py` は FROZEN_MANIFEST および S8B `_GENERATOR_SOURCES` に含まれないため、bytes 上の直接再発行要求も無い。ただし F-3 の意味上の grandfather 境界は必要。

- **狭い A の schema version 据え置き:** 問題無し。新 field・wire shape を追加せず、既存の負 status を利用するため、decision-v1 / Layer3-v3 の版上げ自体は不要。F-6 の validator drift は別問題。

- **grep 列挙内の raw-view consumer 取り残し:** 無し。すべて中央の `require_admitted_campaign` を通る。

## 総括

**NO-GO。**

限定 supersession の実体は、D160 より後の実在するユーザー裁定に基づくため正当である。しかし、現プランは裁定記録を「無い」と誤認し、D96 が要求する exact な supersession 範囲、凍結 derivative の grandfather、repo 外 trial receipt の扱いを固定していない。

最大の risk は、同じ6 campaign が「raw admission では拒否」「既存 certified freeze では引き続き権威」という二層状態になるにもかかわらず、その境界が新 D に記録されないことである。