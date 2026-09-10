## 総括

**real：固定契約を満たす採用案は、今回の静的検査では成立していません。refuted：7330秒を実時間の下限と扱い、短縮候補の実験まで止める判断は過剰です。** 予約式の不成立と、実時間短縮の可能性を分ける必要があります。

**1. real／refuted — 7330秒の意味**

親の式は次の部分和です。

```text
5530 = TSC 10 + cooldown 1200
     + sweep 5×3×120 + noise 10×120 + scale予約 2×3×120
     + wrapper finalize 600
7330 = CCBench configure 900 + build 900 + 5530
```

これは**旧予約項を維持して各工程の上限を加算する方式での、必要予約額の部分和**です。実行時間の下限でも、全timeoutの厳密な総上限でもありません。CCBenchのconfigure→buildは直列ですが、gflags・glog・コピー・検証等はこの部分和に入りません。[certify_calibration.sh:706](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:706)

さらにCLI自身は内部finalize **60秒**も加え、既定座標の予算は **4990秒**です。consumerは `CLI予算＋receipt.reserve_s ≤ receipt.required_s` を要求します。したがって5530を「CLIが要求する較正予算＋外側reserve」と呼ぶのも不正確です。その値は **5590秒**になります。ただし内部60秒を他のreserveへ包含するなら、その包含関係を明示する必要があります。[cli.py:228](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/cli.py:228)、[cli.py:727](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/cli.py:727)

**2. real — outer timeoutは重なっている。ただし成功完遂の予約を代替しない**

既存wrapperは、scheduler開始からの経過を引いた `remaining = deadline − now − 600` で、較正全体を囲んでいます。したがって実行制御を記述する式には、較正内の上限和とouter timeoutの **min** が現れます。[certify_calibration.sh:843](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:843)、[同:949](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:949)

概念上、`E`を残時間算出まで、`L`を算出後のperf選択等、`C`を較正所要、`F`を終了処理とすると、

```text
T ≈ E + L + min(C, 7200 − E − 600) + F
```

です。`L`は残時間算出後なので、単純な「必ず6600秒で較正終了」という読みもできません。

この式は**打切り制御の説明として成立**します。しかし、全標本・全検証を完了できる最悪時予算を保証しません。現在のconsumerもmin式を評価せず、固定予算との大小を検査します。これを理由に `required_s=7200` と書くだけでは、D1936項38の最大経路整合を満たした証明になりません。[D1936項38:58402](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/docs/decisions.md:58402)

**3. real — 実測内訳は一部復元できる**

epochの差は次のとおり一致しました。

```text
開始6387 → static6392 → pre6422 → post／job-result6685
             5秒          30秒             263秒
開始→job-result = 298秒
```

開始・完了は[reservation.json:9](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/env/pegasus/calibration/job-staging/0:989271.nqsv/reservation.json:9)、[job-result.json:10](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/env/pegasus/calibration/job-staging/0:989271.nqsv/job-result.json:10)。提示されたscheduler 302秒との差4秒を、特定工程へ割り当てる根拠はありません。保存qstatは開始直後のElapse 3秒です。

標本は**sweep 3点×3rep＝9回、noise 10回、計19回**。scaleはnot-measuredです。gflagsのログは6compile・2archiveで、同一成果物の二重buildではありません。[calibration.json:1640](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/env/pegasus/calibration/attempts/0_989271.nqsv/calibration.json:1640)、[gflags-build.stdout:1](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/env/pegasus/calibration/job-staging/0:989271.nqsv/gflags-build.stdout:1)

canary starttimeの差は以下です。

| 区間 | tick差 |
|---|---:|
| sweep 100万、3rep | 1068 |
| sweep 200万、3rep | 1196 |
| sweep 400万、3rep | 1458 |
| noise、10rep | 3547 |
| dynamic-pre→post-receipt全体 | 7480 |

出所は[window-probes.json:1](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/output/env/pegasus/calibration/attempts/0_989271.nqsv/window-probes.json:1)。コードは `/proc/PID/stat` のstarttimeを記録していますが、指定ログには当該環境の秒換算根拠がありません。**7480を74.8秒とは確定しません。** 各差もprobe処理を含む窓で、純粋なbench時間ではありません。[runner.py:420](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/runner.py:420)

cooldownの観測列は保存されず、秒単位の内訳は復元不能です。コード上は正常終了に最低2回の30秒間隔が必要ですが、「263秒のうち180秒がcooldown」等は未証明です。代表walltimeはthroughput中央付近の**1標本**から選ばれるため、3倍して全rep合計にもできません。[cli.py:251](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/cli.py:251)、[runner.py:1272](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/runner.py:1272)

**4. 未解決契約と親判断への修正**

scale実測は既にありませんが、720秒はCLI予約式に残っています。削除は標本省略には当たらなくても、予約契約の変更です。また、仮に削除しても直列構成は **7870−720＋copy／検証480＝7630秒**で、他の工程を入れる前に超過します。[sweep.py:293](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/calibrator/sweep.py:293)、[certify_calibration.sh:602](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/tools/pegasus/certify_calibration.sh:602)

従って、**全契約整合済みの最小採用案は提示できません**。未解決なのは、固定timeout・標本数・検証を維持する最終処理構成で、最大経路とconsumerの予約額を7200秒以内に整合させることです。旧文字列を確認する既存testの緑では解決しません。[test_pegasus_tools.py:212](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2563-calibration-runtime/orchestrator/tests/test_pegasus_tools.py:212)

一方、**3コピーの並列化の効果実験まで禁止する根拠にはなりません**。各120秒、全コピー成功後のpristine検証、測定前の全子孫終了を維持すれば、検証省略なしで評価できます。これは採用成立案ではなく、30秒の準備区間を短縮できるか調べる候補です。「効果未証明」は実験の理由であり、実験禁止の証明ではありません。

ファイル変更・テスト実走・計測・子agent起動は行っていません。