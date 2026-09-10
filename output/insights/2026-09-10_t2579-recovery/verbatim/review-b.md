## 総括

**静的レビューでは、承認scope内の修正を要するreal不具合は見つかりませんでした。親の実測へ進める状態です。** pytest・変異・正式受入は未実測であり、合格判定はしていません。

現在のHEADはbrief指定の`c68d08d9e452138c383e9b92076bf91451912700`。`git diff`は`source.patch`とバイト単位で一致し、指定3ファイル・5hunk、138行追加・5行削除です。既存79テスト関数のASTは変更なし、`git diff --check`は通過しました。

以下、パスは親worktree基準です。

1. **refuted候補：consumer登録漏れ／後続main巻戻し**【ドリフト】
   module内の全30テスト関数、parametrize静的展開51nodeに対し、4集合それぞれ30登録で過不足なし。autouse fixtureの外部参照も検索範囲ではありません。
   根拠：`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:83`、`orchestrator/tests/conftest.py:267`・`:434`・`:764`、`orchestrator/tests/test_real_repo_serialization.py:56`・`:194`。
   成果物影響：全consumerが既存parent reader分類へ入る差分で、基準HEADの後続内容を削除していません。**scope内。実collectionは未実測。**

2. **refuted候補：copy共有／fixture取得時のlock漏れ**【恒真ゲート】
   template取得後、function用と返却用のdeep copyを保持。別rootは元処理へ委譲します。parent reader lockはsetupを含むruntest protocol全体を覆います。
   根拠：`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:73`・`:90`・`:94`・`:95`、`orchestrator/tests/conftest.py:590`・`:2180`。
   成果物影響：独立copy境界の欠落は認めません。ただしM1〜M3はcopy削除への検出力を証明しません。**実装確認はscope内、検出力追加はscope外。未実測。**

3. **real候補：module単位1回を全worker合計1回へ広げる説明**【ドリフト】
   対象はprocess-memo集合に含まれず、現行処理が`@real-repo`を除去します。同一worker集約やreader間の直列化は保証されません。
   根拠：`orchestrator/tests/conftest.py:632`・`:2055`。
   成果物影響：主張できるのはfixture実体ごとの取得共有まで。裁定・author説明は既にこの限界を明記しており、現成果物の修正事項ではありません。**説明範囲はscope内、scheduler拡張はscope外。取得総数・timeout解消・性能改善は未実測。**

4. **refuted候補：変異が別理由に隠れる／期待node過不足**【テスト代表性】
   全置換文字列は現物で各1箇所です。共通3node選択を前提に、静的な期待は整合します。

   | 変異 | 静的に予想される失敗と根拠 |
   |---|---|
   | M1 | R1がdetached拒否され、`_observe`のevidence確認で失敗。detached負例は拒否のまま。testファイル`:219`・`:234`、productionファイル`:261`。 |
   | M2 | detached負例だけが受理され、testファイル`:645`で失敗。manifestとsnapshotは実ファイルからhashを取得するため、一時production変更によるhash不一致が必然的に先行する構造ではありません。testファイル`:150`・`:631`、productionファイル`:186`・`:279`。 |
   | M3 | 二集合同時削除は既存partition整合を保ち、独立goldenとの差がserializationファイル`:1581`で失敗する見込み。conftest`:607`。 |

   成果物影響：期待失敗は各1nodeで静的矛盾なし。ただし**失敗node一致だけでは単一理由の実証になりません**。baseline・失敗本文・復元は親の既定実測で確認する事項です。**scope内。KILLEDは未実測。**

5. **refuted候補：production拒否の恒久変更／回収範囲逸脱**【権限逸脱】
   恒久差分はfixtureと既存4集合のみ。productionのdetached・clean・HEAD・source拒否、timeout、走査範囲は変更されていません。
   根拠：`source.patch:1`、`mutation-spec.json:28`、`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:142`・`:163`・`:259`。
   成果物影響：M2は承認された一時変異として区別されています。**恒久回収はscope内。一時変異後の復元は未実測。**

ファイル編集・成果物作成・旧worktreeへの接触は行っていません。