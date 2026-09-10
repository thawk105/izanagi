5ファイル案は採用可能です。40桁限定案を支持します。ただし、既存テストの緑とterminal取得は区別が必要です。静的検査6call、編集・pytest・実測なし。

1. **real：既存K2正例の証明範囲が狭い（F27/F649）**
   `orchestrator/tests/test_p3_s4_loop_job_contract.py:1226,1234`、`plan.md:34`。helperはPINを固定出力し、`-m`実行もargv保存へ置換する。具体的反例は、本体PINを旧値へ戻しても、新SHAへ更新したhelperのK2正例は通ること。成果物への影響は「実PINからdriverへの接続を確認済み」という誤認。最小修正は、この正例を「shellの40桁通過・argv転送」の証拠と明記し、本体PINは固定golden、実接続は親の1本実走で確認すること。fixture変更自体は必要であり、禁止対象ではない。

2. **real：終了コード0はterminal取得を保証しない（F28/F33・他層mask）**
   `orchestrator/campaign/p3_s4_loop.py:2802`、`tools/pegasus/p3_s4_loop_pegasus.sh:145`。CLI成功条件は停止理由とcheckpointの存在で、verdictではない。具体的反例は、build等でabortedとなっても停止理由がcontinueでcheckpointがあればrc=0になり得ること。成果物への影響は、`compute-result.json`の成功をK2第4条件達成と誤認すること。最小修正は新gate追加ではなく、親が新campaignのWAL・verifier出力からv2 terminalを名指しして受け入れること。`brief.md:11`のP1は実走まで未確定。

3. **refuted：40桁限定では後段との互換性が壊れる**
   `tools/pegasus/p3_s4_loop_pegasus.sh:234,247`。現状は指定40桁を形式検査で拒否する。一方、後段は完全HEADと解決結果を比較し、40桁のprefix比較も実質完全一致になる。具体的な破綻反例は見つからない。成果物への影響は投入前拒否の解消。最小修正は既存述語を`^[0-9a-f]{40}$`へ変更し、拒否文言とhelper2箇所を整合すること。7桁互換は今回不要なので、`plan.md:31`の両対応案より40桁限定が適切。

4. **refuted：golden更新が追随だけで誤変更を隠す（F27/F28）**
   `orchestrator/tests/test_p3_s4_loop.py:590,603,5078,5081,6447`、`orchestrator/tests/test_p3_b4_closed_critic.py:3087`。現行cfgの`ccbench_commit`だけを指定SHAへ置換して独立再導出し、通常on/off=`8cf3efb9`/`93d98106`、B4 marked on/off=`47062c3f`/`6e844e5b`を確認した。対象旧hashのPythonテスト内参照も計画の範囲に収まる。反例となる追加consumerは未検出。成果物への影響は新campaign identityへの正当な更新。最小修正は計画どおり固定期待値を更新し、実装からの動的期待値化を避けること。

5. **refuted：既存patch・K2材料が新pinでは利用不能**
   `orchestrator/campaign/p3_s4_loop.py:1891,1903,2725,2741`、`plan.md:42-44`。現物HEADは指定40桁で、既存patchの`git apply --check`成功を独立確認した。WAL-only manifestも既存resolverで再解決でき、digest=`396cd559…`、既存proposal loaderの結果は値20・`double now_backoff = 20;`だった。利用不能の具体的反例は未検出。成果物への影響は材料を無変更で再利用できること。最小修正は不要。ただしpatch適用可能性と材料受理は、build・v2 terminal成功の代替証拠にはならない。

## 総括

40桁literal、通常golden、B4 golden、shell述語、job fixtureの5ファイルで進めてよい。追加gate・台帳・一般化は不要。残る受入条件は、親の実走で新campaignに属するv2 terminalの実体を確認することです。
