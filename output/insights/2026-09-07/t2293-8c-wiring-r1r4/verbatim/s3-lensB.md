## blocker

1. **R2 の「formal receipt」検査が receipt の実在・発行を証明しない。** `assert_origin_trial_completion()` は report、run root、attempt digest しか受けず、`formal_receipt_sha256 != null` を見るだけです (`out/s2-plan.md:697-714`)。これは既存 projection validator が既に強制する条件であり (`autonomous_trial_completeness.py:2182-2198`)、文字列は自己申告できます。実 receipt を issuer snapshot と照合する検査は in-process object にしかありません (`reflux_formal_consumer.py:405-416`)。

   成果物影響: formal consumer を通していない projection でも trial status、lifecycle terminal、試行台帳 acceptance を `complete` にでき、材料レポートが存在しない receipt を参照します。

2. **物理 evidence producer が結線されず、実行前に caller が渡した record を最後まで使います。** プランは `result_record_bytes` を維持すると明記し (`out/s2-plan.md:156-166`)、現 API も frozen な caller input です (`p3_autonomous_workload_trial.py:428-438`)。completion はその同じ bytes を consumer へ渡します (`p3_autonomous_workload_trial.py:1653-1665`)。プラン自身も writer / normalizer 不在を認めています (`out/s2-plan.md:331-338`)。これは trusted physical harness が terminal 後に発行するという正本と逆です (`phase3-8c-wiring-design.md:169-185`)。

   成果物影響: live 33 run から result record が生まれず、正例は事前作成 fixture か自己申告 bytes に依存するため、材料レポートと試行台帳の物理 attempt 参照が実行結果を表しません。

3. **`campaign.lock` の carrier が未決のため要件 14 は実装不能です。** 現 `result-evidence/v1` は exact 2 ref で (`reflux_result_evidence.py:112-114`)、resolved 型にも lock はありません (`reflux_result_evidence.py:166-174`)。プランは `result-evidence/v2` を追加候補にしていますが (`out/s2-plan.md:469-503`)、これは D1670 が許可した §G の 3 写像 (`phase3-8c-wiring-design.md:844-850`) とは別の受理集合変更です。

   成果物影響: carrier を足さなければ別 trial・別 attempt の WAL 流用を拒否できず、足せば未裁定の schema bytes と受理集合を変更します。これは実装前に返す裁定パッケージ候補です。

4. **「actual CampaignSummary ID」gate は現 seam のままでは恒真です。** プランは summary の actual ID と plan を比較するとします (`out/s2-plan.md:293-300,321-326`)。しかし `_run_one_iteration_resolved()` は `CampaignSummary.campaign_id` を捨て (`p3_s4_loop_trigger_gating.py:811-820`)、戻り値には入力 cfg から再計算した ID を入れます (`p3_s4_loop_trigger_gating.py:633-640`)。

   成果物影響: wrong-summary-ID 変異が planned ID と同じ値へ投影され、試行台帳と材料レポートが実際とは別の campaign identity/root を参照できます。

## must-fix

1. **物理 root を canonical layout へ束縛していません。** lock と WAL が同じ root にあることは要求しますが (`out/s2-plan.md:459-467`)、その root が `exploration_campaign_layout(rederived_identity)` そのものかは要求していません。実行時には既存 gate がこの等式を持ちます (`p3_s4_loop_trigger_gating.py:644-662`)。また `evidence_root` は caller 入力のまま残ります (`out/s2-plan.md:156-166`)。

   成果物影響: plan identity と整合する lock/WAL を任意 directory に後置して report へ載せられ、`campaign_runs[].campaign_root` の参照先が実 executor の layout から外れます。

2. **物理 `campaign_id` が論理 cell ID を上書きする経路を閉じていません。** origin entry の戻り値は物理 cfg の `campaign_id` を持つ一方、report は論理 ID を置くとだけ記述されています (`out/s2-plan.md:299,677-688`)。さらに origin 分岐で既存単数-root検査を回避します (`out/s2-plan.md:732-747`)。現在は `binding.campaign_id == cell.campaign_id` が明示的に拒否しています (`autonomous_trial_completeness.py:1205-1222`)が、代替等式が completion の検査一覧にありません。

   成果物影響: FC03 自体が正しくても cell と acceptance receipt の `campaign_id` が物理値へ変わり、論理 trial と33 runの階層が崩れます。

3. **次の変異候補は単一理由で kill されないため事前登録から外すべきです。**

   - 要件9の q 固定0 (`out/s2-plan.md:955`): 新 helper の相異検査に加え、既存 topology も identity 重複を拒否します (`reflux_origin_topology.py:368-370`)。
   - 要件10の issuer へ cfg_q (`out/s2-plan.md:956`): issuer 自身が registry campaign ID 不一致を拒否します (`reflux_origin_binding.py:559-562`)。spy はプラン自身の除外規則 (`out/s2-plan.md:980`)にも反します。
   - 要件12の q0 layout 再利用を「33 root相異」で殺す候補 (`out/s2-plan.md:959`): 先に `_assert_resume_allowed()` が既存 lock/WALを拒否します (`p3_s4_loop_trigger_gating.py:475-492`)。
   - 要件18の receipt 欠落 (`out/s2-plan.md:972`): 既存 projection validator が先に拒否します (`autonomous_trial_completeness.py:2182-2198`)。

   成果物影響: mutation 台帳だけが「新 gate が効いた」と誤記され、certified 選択等の値は変わらなくても検査根拠の参照が虚偽になります。

## 偽装入力判定

| 入力 | 判定 | 実測根拠 | 放置時の成果物影響 |
|---|---|---|---|
| (a) q10/q11 root/config交換 | **carrier 解決後は拒否**。lock 内 q と ledger/run-plan q の不一致で落ちます | `out/s2-plan.md:459-467`; `reflux_origin_topology.py:330-370` | 未解決の現プランでは q別材料レポートが交換先rootを参照します |
| (b) 別path・別object envelope | **拒否**。fixed path、lifecycle digest、in-memory canonical bytesの3照合です | `out/s2-plan.md:521-535`; `phase3-8c-wiring-design.md:796-798` | 無い場合は33 identityを事後宣言し直せます |
| (c) 別trialの33 WAL | **lock検査実装後は拒否**。lockから論理cfgを戻すと `trial` が異なり capability ID と一致しません | `out/s2-plan.md:461-466`; `ident.py:212-235` | WALを別trialの物理実行として二重利用できます |
| (d) 過去attemptのWAL | **拒否**。lock内 slot capability digest が現在値と不一致になります | `out/s2-plan.md:461-465`; `trial_registry.py:2082-2095` | 別replicate・別prereg世代の測定を現在slotへ付け替えられます |
| (e) 実行後に33 directoryを後置 | **整合したlock/WALまで後置した入力は拒否できません。** 空directoryだけならdecodeで拒否されます | `out/s2-plan.md:459-467,707-714`; `phase3-8c-wiring-design.md:221-232,867` | D1674のtrusted-writer運用前提外では、物理実行0件の偽材料を排除できません。canonical root照合欠落分は前提内でも参照を誤らせます |
| (f) build_attempt_idを1件重複 | **拒否**。FC05aが独立に相異を要求します | `reflux_formal_consumer.py:768-779`; `out/s2-plan.md:617-632` | 無ければ33 recordが32以下のattemptを水増しします |

## 3項等式と identity

FC03 の3項等式そのものは維持されています (`out/s2-plan.md:395-405`; `reflux_formal_consumer.py:702-707`)。危険な混入経路は、物理 entry の戻り値 `campaign_id` を論理 cellへmergeする経路であり、上記 must-fix 2 が必要です。

時刻・PID・乱数は physical identity に混入しません。これらは process identity にだけ入ります (`p3_autonomous_workload_trial.py:1346-1353`)。slot capability digest は slot、replicate、attempt、prereg世代から導出されます (`trial_registry.py:2074-2096`; `attempt_registry_core.py:262-273`)。

同一slot・同一qは同一preimage/identityになり、再予約または既存layoutで fail-closed です (`p3_autonomous_workload_trial.py:1398-1411`; `p3_s4_loop_trigger_gating.py:475-492`)。別attemptはpreimageが変わります。ただし公開identityはSHA-256先頭8 hexなので数学的な相異保証ではなく、衝突時は lock mismatchによる安全側停止です (`ident.py:226-235`)。

## nit

- 親briefの「v1実在成果物0件」は `git grep -- output/` の射程を「全実在成果物」へ一般化しています (`s1-brief.md:27`)。証明できるのはtracked textual corpusの範囲です。D1669の択一は戻さず、測定の射程だけ限定して記録すべきです。  
  成果物影響: repo外またはuntrackedの歴史artifactがあれば参照不能になりますが、現コードの受理値は変わりません。
- そのほか、production writer 0件、envelope write順、未使用planned identity、発行0/3・authority 0件というbriefの実測はコードと整合します (`s1-brief.md:26,28-30`; `reflux_origin_authority_v2.json:1`; `reflux_origin_binding.py:602-603`)。  
  成果物影響: 現状のcertified選択、材料レポート、試行台帳のproduction値は変わりません。

## 名乗りの上限

実装後に名乗れるのは、実際に閉じた範囲ごとの「fixture-scopedなR1/R3 wire contract」「disk envelopeと物理lock/WALのconsumer検査」「origin report projection」です。

`out/s2-plan.md:894` の「第一waveでは結線完了を名乗らない」は正しい一方、`out/s2-plan.md:900,995` の「R2 completion」は、receipt authorityとlive evidence producerがないままでは名乗れません。P6 consumerは依然として非aborted terminalを生成不能です (`reflux_formal_consumer.py:1-8`)。本番authorityは0件でproduction発行も明示拒否です (`reflux_origin_authority_v2.json:1`; `reflux_origin_binding.py:602-603`)。

したがって「8c結線完了」「発行条件を満たした」「P6が発火する」「productionで物理実行を保証する」は不可です。`certifying=False` も維持されるため、certified選択の受理集合は動かしてはいけません (`reflux_origin_binding.py:598-599`)。

## 総括

- **判定: 作り直し。**
- 最大点1: live executorからresult evidenceへ至るproducer経路がなく、caller提供bytesのままです。
- 最大点2: `campaign.lock_ref` carrierが未裁定で、追加案は§G外の受理集合変更です。
- 最大点3: actual campaign IDとformal receiptのgateが、現状は再導出文字列またはdigest自己申告です。
- (a)(b)(c)(d)(f)は必要なcarrierと照合を実装すれば拒否できますが、(e)はD1674の運用前提外では拒否不能です。
- FC03とidentityの決定性は維持可能ですが、reportへの物理ID混入経路を閉じる必要があります。
- 静的検査のみで、testは実行していません。