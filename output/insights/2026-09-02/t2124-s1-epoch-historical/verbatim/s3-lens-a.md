## 所見

所見 1: 30 campaign の census から S-1 出力の byte 不変は導けない

重大度: must-fix

壊れる入力: repository 外の正規 `--output-root` に、記録 commit と blob map が正しい v2 lock を持つ4 campaign があり、現行閉包だけが取得不能な場合。変更前は `E1-stale / current-closure-unavailable` で拒否され、変更後は受理されるため report 内容が変わる。repo 内 `output/campaigns/` の30件はこの入力集合を覆わない。

実物の根拠 (file:line):

- 親の推論は `brief.md:54-58`、プランも `plan.md:153` で追認している。
- S-1 が読むのは30 directory 全件ではなく、`ROLES` の4件だけである。`orchestrator/campaign/s1_report.py:59`、同`:940-943`。
- 各 campaign ID は freeze と role から `layout_for` が再計算する。`orchestrator/campaign/s1_direct_comparison.py:457-490`。
- `output_root` は `generate_report` からそのまま渡される。`orchestrator/campaign/s1_report.py:1126-1138`。
- official root は明示された repository 外の root を受理する。`orchestrator/campaign/layout.py:323-367`、同`:412-458`。
- producer を再実行した場合は `generated_at_head` も現在の HEAD から再生成されるため、E0判定が同じでも byte 同一性は証明できない。`orchestrator/campaign/s1_report.py:905-915`、同`:1018-1021`。
- 現在の凍結 report 自身が gate 導入前の生成物であることは親も認めている。`brief.md:65-70`。

親 brief / プランのどちらの誤りか: 両方。30件が v1 という実測値自体ではなく、それを S-1 の入力母集合および byte 不変へ一般化した部分が誤り。

## 親 brief の実測への異論

read-only で再集計した範囲では、`output/campaigns/` は30 directory、30 lock、`authority` key は0件だった。凍結された4つの canonical S-1 campaign IDも全件存在した。したがって census の数値自体への異論はない。

異論は母集合と結論である。S-1 report は30件を列挙せず、freeze、`ROLES`、`layout_for` から決まる4件だけを、指定された `output_root` で読む。さらに出力は campaign ごとの30成果物ではなく、既定では1組の `report.json` と `report.md` である。`orchestrator/campaign/s1_report.py:1134-1144`。

`s1_direct_comparison.py` の `epoch` 文字列0件という観測だけには証明力がないが、実経路も確認した。同 module は計測 driverで、report側がそこから `layout_for`、schedule、budget、session解析関数を importする一方向の依存である。`orchestrator/campaign/s1_report.py:41-52`。driver側の import集合に `artifact_admission` や `s1_report` はなく、report生成時に使う `layout_for` は campaign pathを返すだけである。`orchestrator/campaign/s1_direct_comparison.py:35-44`、同`:487-490`。別名または別 admission APIによる epoch gateはこの経路に見つからなかった。

byte pinについては親の別の根拠、すなわち「producerを走らせない」は静的に支持された。正規 producer は `s1_report.generate_report/main` のみである。`orchestrator/campaign/s1_report.py:1126-1168`。受入 runnerは pytestを起動するだけで、`orchestrator/tests/test_s1_report.py` の生成テストは `tmp_path/output` へ書く。`tools/run_tests.py:550-572`、同`:2682-2699`、`orchestrator/tests/test_s1_report.py:216-225`、同`:642-650`。provenance testは凍結 reportを読み、digestを照合する。`orchestrator/tests/test_s1_9pair_figure_provenance.py:648-705`。受入全走から tracked reportを再生成する経路は見つからなかった。

## 破れが見つからなかった項目 (確かめた上で異論なしと言えるもの)

1. `CERTIFIED_ACCEPTANCE` の拒否集合

   `_require_verifier_epoch_for_purpose` の全分岐は次のとおり。

   - purposeが exact `CampaignReadPurpose` でなければ `TypeError`。`orchestrator/campaign/artifact_admission.py:939-944`。
   - `HISTORICAL_RAW` は記録診断を返す。異常な型検査を迂回してはいない。同`:957-964`。
   - `CERTIFIED_ACCEPTANCE` で記録 state が E0なら、`CampaignVerifierEpochRejected`。同`:965-966`。
   - 非E0では現行閉包を取得し、任意の `ContractLoaderBindingError` を `E1-stale / current-closure-unavailable` にして拒否する。同`:967-974`。
   - 現行閉包を取得できれば記録診断を返す。同`:975`。

   `recorded-current-closure-mismatch` は診断型が受け入れる旧理由だが、現行中央 gateが生成する経路はない。`orchestrator/campaign/artifact_admission.py:186-201`、`orchestrator/tests/test_artifact_admission.py:1630-1639`。

   したがって局所 `state == "E0"` は従来の拒否集合全部ではない。落ちるもう一群は E1 の現行閉包取得不能である。ただしD1387は「可用性 gateを外し、E0だけを残す」と明記しているため、この差分は裁定内であり絶対規律2違反ではない。`D1387.md:9-13`、`D1366.md:10-15`。

2. `_recorded_campaign_verifier_epoch` 内の拒否

   v1はE0を返し、v2だけが purpose 判定前に `_verify_committed_loader_binding` を必ず通る。`orchestrator/campaign/artifact_admission.py:898-935`。拒否条件は次の全群である。

   - authority不在。ただし `_recorded_campaign_verifier_epoch` 経由ではv1分岐済みなので到達しない。`orchestrator/campaign/artifact_admission.py:880-885`、同`:909-919`。
   - commitまたは24 path blob mapの型、exact key集合、lowercase hexが不正。実 lock bytesではcodecが先に拒否する。`orchestrator/campaign/campaign_lock.py:215-250`。
   - repository root、Git top-level、Git executable、ambient Git override、timeoutまたはGit commandが不正。`orchestrator/campaign/contract_loader_binding.py:97-130`、同`:251-315`。
   - 記録 commitが存在しない、exactに解決できない、対象 pathがblobとして読めない。同`:329-345`。
   - 24 pathの記録 digestと記録 commit blobが不一致。同`:386-401`。

   これらは `ArtifactAdmissionError` に変換される。`orchestrator/campaign/artifact_admission.py:886-895`。S-1は `campaign_verifier_epoch_validation_failed` として構造化し、WAL読取前に返る。`orchestrator/campaign/s1_report.py:447-463`。purpose変更より前で起きるため挙動は変わらない。

3. exact型

   プランの `CampaignReadPurpose.HISTORICAL_RAW` は同じ moduleからimportされたenum実体であり、中央 gateの `_validate_read_purpose` を通る。局所E0以外で中央 gate自体を省いていないため、exact型検査の迂回はない。`orchestrator/campaign/s1_report.py:33-39`、`orchestrator/campaign/artifact_admission.py:957-964`。

4. 負例の実 callee

   提案どおりmodule import時に実関数を保存すれば、autouse fixtureが動くのは後のtest setupなので保存値はproduction関数である。現 fixtureはsetup時にreport属性をlambdaへ差し替える。`orchestrator/tests/test_s1_report.py:15-16`、同`:31-38`。test本文の後勝ちmonkeypatchでdispatcherを置き、保存済み関数を直接呼べば局所E0判定を通る。fixture lockはroleを含むため、block1 bytesだけを選別できる。同`:162-166`。

   実経路を失う具体的な転び方は、保存をautouse fixtureの差し替え後に行ってlambdaを保存する、dispatcherから `report._campaign_verifier_epoch_from_lock_bytes` を再参照して再帰する、またはE0診断をdispatcher自身が合成する書き方である。planのmodule-level保存と `_REAL_...` 直接呼出しはこれらを避けている。`plan.md:45-62`。

5. 正例の記録済み束縛

   共有helperはHEAD commitの24 blobを読み、production v2 encoderへ渡す。`orchestrator/tests/campaign_lock_test_support.py:10-48`。現行閉包取得だけを失敗stubにしても、記録commit/blob検証は別経路で実行される。

6. 他の2消費者

   `replay.load_landscape` は `require_admitted_campaign` と exact `CERTIFIED_ACCEPTANCE` を直接使う。`orchestrator/campaign/replay.py:33-40`、同`:179-187`。oracleも独自のlock-only関数から中央 gateへ `CERTIFIED_ACCEPTANCE` を直接渡す。`orchestrator/campaign/s8b_oracle_report.py:46-62`、同`:556-563`。どちらも `s1_report` をimportしていないため間接影響はない。

## 未確認事項

- 指示どおりpytest、build、producer、checkerは実走していない。緑とは報告しない。
- 親briefの32 worktree競合調査は再実測していない。
- repository外の `--output-root` 入力は静的に経路を確認しただけで、実際のreport生成は行っていない。
- fileは1 byteも編集していない。

## 総括

最も重い破れは、repo内30 campaignのcensusをS-1の入力母集合とみなし、byte不変まで一般化した点である。  
実際のS-1はfreezeから決まる4 campaignを任意の正規外部 `output_root` から読み、その入力では変更前後の受理結果が変わる。  
一方、E1の `current-closure-unavailable` を落とすことはD1387が明示的に許した緩和であり、E0と記録commit/blob検証は残る。  
実装プラン本体、exact型、実callee負例、replay/oracle分離、受入中のbyte-pin非再生成には追加の破れを確認できなかった。