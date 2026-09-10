## 総括

**静的レビューでは、承認scope内の修正を要するreal所見なし。実測受入は未判定です。**

現在差分は指定3ファイル・5hunk、138行追加・5行削除。indexとhunk行番号を除いてsource.patchと一致しました。対象30関数・静的展開51nodeについて、既存4集合は各30登録で過不足なし。両テストファイルの既存79関数はAST一致し、正負期待の変更はありません。`git diff --check`は通過しました。

### 所見1：copy共有・別root委譲破壊

- **refuted候補／ドリフト／scope内**
- 根拠：`orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:73–97`。module templateからfunction用、返却用の二段deep copyがあり、別rootは保存した元処理へ委譲します。
- 成果物影響：nestedなsource digestやuntracked pathsの別名共有による汚染は見当たりません。個別copy削除を既存テストが検出するかは未実測です。

### 所見2：consumer漏れ・goldenの恒真化

- **refuted候補／恒真ゲート・テスト代表性／scope内**
- 根拠：`orchestrator/tests/conftest.py:267`、同`:436`、`orchestrator/tests/test_real_repo_serialization.py:56`、同`:197`。module autouseの全30関数と各集合を独立に照合し、一致しました。
- 同`:1582`は実access mapと独立goldenを比較します。M3はinventoryとparent-onlyの両方から同じ1件を落とすため、`conftest.py:606`のpartition不整合を避け、golden不一致で検出される構造です。
- 成果物影響：現在の登録漏れはありません。将来のconsumer自動追従までは証明しません。

### 所見3：変異のmasked・複数理由・期待node過不足

- **refuted候補／テスト代表性／scope内、実測保留**
- 各置換文字列は対象ファイルにちょうど1回存在しました。共通3nodeを個別変異ごとに走らせる前提では、期待失敗は各1nodeと静的に整合します。
- **M1**：`test_t1259_qsub_env_delivery_probe.py:77`の変異で正当R1が拒否され、同`:219`のevidence一致で失敗する見込みです。detached負例は元からFalseなので維持されます。
- **M2**：productionの`:261`の拒否だけを無効化すると、負例の同テスト`:643`が失敗する見込みです。manifestの`:148`とsnapshot取得側productionの`:187`が変異後の実ファイルをhashするため、source不一致によるmaskは見当たりません。負例はdetached以外を正常値に保ちます。
- **M3**：前項の独立golden比較が期待失敗点です。
- 成果物影響：静的に別理由の必然的失敗は見つかりません。ただしbaseline、実collection、失敗理由、復元完了は未実測です。

### 所見4：production変更・性能保証への拡張

- **refuted候補／権限逸脱・ドリフト／恒久差分はscope内**
- 根拠：現在差分にproduction変更なし。`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:259–285`のHEAD・detached・clean・source拒否は保持されています。M2は一時変異として区別されています。
- `orchestrator/tests/conftest.py:2055–2066`はprocess-memo以外のsuffixを除去します。module fixture承認から全worker合計1回は導けません。
- 成果物影響：timeout解消・性能改善・全体1回は未証明です。scheduler/process-memo拡張はscope外であり、要求しません。

pytest、変異、正式受入は実行していません。ファイル編集・追加成果物作成・旧worktreeへのアクセスは行っていません。