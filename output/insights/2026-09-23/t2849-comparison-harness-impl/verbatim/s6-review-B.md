対象は `81745c268`・`16ee35040`。静的レビューのみで、テストは実行していません。

### 所見

1. **should — sweepの生成時間が費用から欠落する。**  
   根拠: `orchestrator/campaign/t2849_comparison_harness.py:512,534–544`。hash計算・ソートを行う `G.sweep_order()` が計時前に実行され、計上されるのは配列参照とprovenance生成だけです。初回の生成時間へ順序作成の所要も含めれば、既存fieldで修正できます。  
   **放置時の影響:** 集約の `costs.generator_wall_s` がsweepだけ生成処理を過少計上します。候補列・score・job Elapseは変わりません。

2. **nit — 台帳の `append` はB-5の実装をそのまま再利用できる。**  
   根拠: `orchestrator/campaign/t2849_comparison_harness.py:63–76` は `b5_generator_contrast.py:233–246` と同じ実装です。`B.SeriesLedger` を継承し、schemaに依存する初期化・作成・viewだけを残せば、この14行を削れます。共有moduleの変更は不要です。  
   **放置時の影響:** 現時点で成果物・受理集合・参照の差はありません。継承後もevent検査・採番・公開・view更新は同一です。

3. **nit — 未使用の設定引数を固定値へ戻せる。**  
   根拠: `orchestrator/campaign/t2849_generators.py:33,47,54,59`。`random_value(namespace=...)` と `sweep_order(initial_values=...)` は、対象production・testの全呼出しで既定値しか使っていません。名前空間と初期点は今回固定された条件なので、override引数は不要です。`weights` は独立試験で使用されており、削除対象ではありません。  
   **放置時の影響:** 現行CLIの受理集合・候補列・成果物は変わりません。未使用のPython設定面だけが残ります。

### 攻撃が不成立だった観点

- **指定関数の再実装:** 不成立。`classify_session`・`wal_timing`・`select_endpoint`・`weights_table`・`validate_backoff_value`・`default_runner` は再利用されています。参照専用分類は、既存分類が `BACKOFF_FIXED` 未指定をcandidate扱いしてTier0を要求するため、単純置換できません。
- **投入経路の不足・範囲外実装:** 不成立。5 armは共通の `_execute_slot` と単回評価CLIを通り、A・B・N・系列番号を受け取れます。launcher・schedule・MOCC・第2プロトコルは追加されていません。
- **既存経路の変更:** 不成立。静的差分上、従来のB-5・非B-5の3経路・K2へのargv変更は確認できません。archive未設定では従来のcleanupに到達します。役割本文の拡張もT-2849 K0に限定されています。
- **規模超過:** 不成立。追加行はproduction側 **1,427行**（役割文書・adapterを含む保守的集計）、test **1,159行**。上限内です。小規模な削減候補は所見2・3です。
- **禁止pathへの編集:** 不成立。2コミットの変更一覧に指定禁止pathはありません。`test_p3_s4_loop.py` はfixtureとして参照されていますが、編集されていません。

## 総括

**所見3件: must-fix 0 / should 1 / nit 2。GO。**

レンズBの静的判定です。試験実測・変異killの確認は親の検証に残ります。