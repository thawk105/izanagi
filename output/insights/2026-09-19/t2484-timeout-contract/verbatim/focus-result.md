## 総括

**GO（静的レビュー）。新規must-fixなし。** `a13570f…`からのfixture修復差分と、`7975385…`からの全体差分を確認しました。実走完了・変異検出の成功は未確認です。

| 所見 | 判定 | 状態 | 確認結果 |
|---|---|---|---|
| 1：fake dispatcherのimport時SystemExit | real | **partial** | 修復の静的閉包を確認。import guard、5定数、parserを追加。生成CLI本体・既存テスト・期待値はAST比較で不変。consumer 2 testの実走結果待ち。 |
| 2：DW-M06を「rc16だけで変異残置」と読める | real | **closed** | 「既存hold条件時のみ」に是正済み。rc16単独でholdする実装という疑いはrefuted。 |

**regressedに該当する所見なし。**

原定数から `B=P+Q+W+G+A+C` を再計算し、すべて一致しました。

| 条件 | 計算（秒） |
|---|---|
| 既定 | 180+900+3600+300+60+90 = **5130** |
| Q=3600、G=600 | 180+3600+3600+600+60+90 = **8130** |
| Q=1800、G=600 | 180+1800+3600+600+60+90 = **6330** |
| W=7200 | 180+900+7200+300+60+90 = **8730** |

静的確認では、以下の回帰疑義は**refuted**です。

- collection／baseline／mutationの全3 callerが実効timeoutを使用。長いspecは維持。
- collection gateは元specのQ+G判定を維持。2399は拒否、2400は通過して6330秒。
- collectionは既定W、実行側はW overrideを尊重。localの短いhang期限も維持。
- 内側dispatcher・run_tests・worktree wrapperはbaseと同一。期限・回収・hold・失敗node完全一致・resume処理に変更なし。
- fixtureの定数・parserは実dispatcherと一致。CLI本体と既存期待値の変更なし。

変異**17本すべての各oldは一意**で、期待nodeも静的に解決できました。P0／M1〜M15の期待失敗集合は独立した算術・callerモデルと一致。M16対象2nodeは修復fixtureを使う実harness経路です。予定の選択集合は、診断専用nodeを除く32node＋M16の2node＝**34node**で整合します。実際の選択argv・collection結果は未確認です。

**残る実測事項：** [焦点ログ](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-timeout-contract/focus-worktree-fixed.log)は確認時点でrequest `9292.nqsv`のRUNまでです。file単独走の完了、consumer 2 testの成功、M16を含む17変異の実結果は未確認として分離します。こちらではpytest実行・編集・commit・子起動を行っていません。