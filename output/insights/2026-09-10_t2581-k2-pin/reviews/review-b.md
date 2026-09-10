静的レビューでは、今回の5ファイルに修正必須の欠陥は見つかりませんでした。HEADのコード・テスト差分は `author.patch` とバイト一致しています。以下の real/refuted は静的判定で、実走結果ではありません。

1. **固定goldenの追随による隠蔽：refuted／scope内**
   - 箇所：`orchestrator/tests/test_p3_s4_loop.py:590,603,5078,5081,6447`、`orchestrator/tests/test_p3_b4_closed_critic.py:3087`
   - 具体反例候補：誤った期待値へ一括更新し、pin変更以外のidentity破損を隠す。
   - 検査：本体factory・identity関数を呼ばず、静的入力から正準JSONとSHA-256を独立計算。旧通常 `8ee68c0c/95a32c3e`、新通常 `8cf3efb9/93d98106`、旧B4 `4e54b9ea/7a8e044f`、新B4 `47062c3f/6e844e5b` がすべて一致した。
   - 成果物影響：新規campaignの分離は指定pin変更と整合。期待値の動的追随化、assert削除、mask追加はない。最小修正：不要。

2. **pin依存consumer漏れ・過去値の付替え：refuted／scope内**
   - 箇所：`orchestrator/tests/acceptance_duration_ledger.json:1181`、`orchestrator/campaign/p3_b4_closed_critic.py:635`
   - 具体反例候補：旧goldenを実行consumerに残す、旧nodeの所要を新nodeへ転記する。
   - 検査：検索範囲の旧golden残存は過去所要台帳の2キー。台帳は無変更。B4の本体ソースhash依存も存在するが、そのconsumerやfixtureへ新hashを差し込む変更はない。sort/triggerは別PIN定義を使用する。
   - 成果物影響：過去所要を新nodeの実測として扱っていない。最小修正：不要。新nodeの所要は親の実測待ち。

3. **mutationの単一理由・注入消失：静的懸念はrefuted／scope内、実測未確認**
   - 箇所：`orchestrator/campaign/p3_s4_loop.py:112`、`tools/pegasus/p3_s4_loop_pegasus.sh:234`
   - 具体反例候補：先行gateによる別理由の失敗、複数置換の上書きで偽KILL/SURVIVEDになる。
   - 検査：M1/M2の置換対象は各ファイル内で一意。M1は通常goldenの不一致、M2は40桁正例の形式拒否に照準が合う。選択した2nodeでは、他方が各変異へ依存しない構造も確認した。
   - 成果物影響：F28/F33型の静的な矛盾は見つからない。ただしbaseline、実注入、復元、失敗node完全一致は未確認。最小修正：コード変更不要、登録済み検証の結果で確定する。

4. **stub正例の射程限界：real／既知・scope内の証拠限界**
   - 箇所：`orchestrator/tests/test_p3_s4_loop_job_contract.py:1203,1224,1233,1312`
   - 具体反例：本体PINを旧値へ戻しても、stubが新PINとGit HEADを返すためargv正例は通り得る。`-m`もargv記録で代替され、本体は実行されない。
   - 成果物影響：この正例やM2のKILLから、本体接続・verifier・terminal成立を導くとF649型の過大申告になる。
   - 最小修正：追加テスト不要。裁定どおり射程を限定し、親の計算ノード1本実走で最終証拠を得る。

親docsも整合しています。`docs/phase3.md:312` は実装チェックとterminal未達を区別し、runbookは完全SHAのPIN記号参照へ更新。`run-card.md:17` のK2 ID `409e13f8` も独立計算と一致しました。規律2/6/7に関わる検査・帰属処理の変更は差分にありません。

## 総括

静的検査として差分は妥当です。pytest・mutation・計算ノード実走は実施しておらず、緑やterminal取得は申告しません。最終判断には親の固定snapshot実走とWAL・verifier出力の確認が残ります。