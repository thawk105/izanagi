## 総括

D1936項30どおり、shell の `BOUND_PATHS` へ条件関門を1件追加する計画で進められます。ただし、既存の Python 束縛テストだけでは配列entry除去を検出できません。既存テストモジュール内で shell 検査の契約を補います。今回は静的確認のみで、書込み・テスト・変異検査はすべて未実走です。

1. **実装箇所と検査順序**

   `tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54` の配列へ `orchestrator/campaign/condition_meaning_gate.py` を1行追加します。

   現在の順序は、環境条件検査（:8）→ Python 3.10 版確認（:20）→ root・host 検査（:29）→ HEAD・replace refs 検査（:47）→ dirty 検査（:60）→ 各pathの live/blob 照合（:68）→ runtime PBS 照合（:76）→ scratch・shim 準備（:82）→ probe 起動（:108）です。この順序を維持します。

   `t316_sandbox_backend_probe.py:36` の条件関門 import は、同ファイル :2331 の Python dirty 検査より前です。shell 配列追加により、その import より先に既存の dirty 検査とblob照合が効きます。

2. **既存契約テストの局所拡張**

   `orchestrator/tests/test_t316_sandbox_probe.py:1406` の Git fixture を再利用します。:1436 の独立した5pathは維持します。:1439 の PBS は現在 `exit 0` だけであり、:1526／:1545 の既存テストは Python 関数を直接呼んでいます。

   この領域に、実PBSから配列・dirty検査部分（PBS :54–63）をそのまま取り出し、fixture の実Gitに対して Bash で実行する局所テストを追加します。検査後の到達markerを観測し、期待pathは実装配列から生成せず独立literalで固定します。併せて、実PBS本文で dirty 検査→blob照合→runtime PBS照合→probe起動の順序を固定します。

   - 負例：条件関門だけを未stage／stage済みで変更し、`rc=3` かつ後続markerなし。既存4pathも独立parametrizeで拒否を維持。
   - clean正例：同じfixtureの5pathがcleanなら `rc=0` かつ後続markerあり。
   - 既存の runtime spool 正例・Python bytesとの取り違え負例（:1526／:1545）は期待値を維持。

   この局所実行が証明するのは shell dirty 検査の受理・拒否です。PBS全体や実probe importの実走証明とは区別します。

3. **単一変異の検出箇所**

   追加した配列entryだけを除去し、同じ条件関門dirty負例を再走する計画です。変異後はdirty対象が配列から外れ、`rc=0` と後続marker到達になるため、負例の `rc=3`／marker不在のassertで検出します。

   抽出部分を実行することで、変異したPBS自体のdirtyやruntime hash不一致による別理由の拒否を混入させません。clean正例も併走し、環境不備による一律拒否を除外します。

4. **consumer・参照と親briefの補正**

   Python側の5path定義（probe.py :2291）と `runtime_sha256` 生成（:2341）は既に条件関門を含み、変更不要です。既存consumer相当の確認はテスト :1536 のruntime hash参照、:1312 の完成述語、:1319 の条件関門receipt確認です。schemaや既存receiptの再ラベルは行いません。

   親brief :7–8 の現物説明は一致します。:9 は現状ではなく修正後の期待動作です。また authority :10 の「Python起動前」は、PBS :24 に版確認があるため、厳密には「probe起動・条件関門import前」と記録します。brief :12 の小規模案は妥当ですが、Pythonテストの拡張だけでは不足します。

   brief :6 の phase完了記録・専用insight・worklog fragment は親の記録対象です。指定読取範囲外のため、その挿入行、外部consumer、:16 の固定source hash不存在、:17 の所有状況は未確認です。

**実装規模上限：production追加1行、既存テストモジュール内の変更100行以内、参照更新は上記3用途の最小限。** 別テストファイル・汎用harness・新しい防護機構・汎用import閉包は追加しません。親の既存実行経路で正負例・単一変異・関連検査を実走してから受入判定します。