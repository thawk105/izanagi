## 総括

既存 4 API の合成順と直接 CLI 用 package shim は実装可能であり、正規コマンドの import 形も成立する。  
ただし現行 sanctioned path は `floor=None` 固定なので、全ての有効 publication が `protocol_violation` となり、4 分類のうち 3 分類と全統計値が到達不能である。  
また `anomaly_class` に予定している値は実行時 anomaly ではなく、処置割当て前 precursor の `digest_red_classes` であり、必須 field の意味を取り違えている。  
出力先 guard は必要だが、テストの fixture scope、clean subprocess 条件、例外変換、受入コマンドが未確定で、2 invoke・60 秒未満という見積りは現状では閉じていない。

## 所見

### 1. 正規コマンドの verdict が常に `protocol_violation` になる

- 深刻度: 高
- 根拠:
  - `s2-plan.md:49-52,177-182,251-260,270-272`
  - `orchestrator/campaign/p3_b4_analysis_path.py:349-353`
  - `orchestrator/campaign/p3_b4_analysis_path.py:102-120`
- 壊れ方: `None` は必ず `floor_domain_error` となり、invalid result は必ず `verdict=protocol_violation`、`a_hat/ties/m/on_wins/p_values/theta_interval=null`、`effect_below_a_min=false` になる。したがって `test_four_verdicts...` は synthetic renderer の試験でしかなく、sanctioned command から `established`、`not_established`、`indeterminate` は一度も出ない。field は存在するが実環境では常に同じ値、という設計である。
- 最小修正案: caller 注入の `--floor` は採らず、現 wave の成果物を「floor 未発効時の evidence-only material report」と明記する。正規経路のテストは protocol violation 固定を検査し、4 verdict の synthetic test は将来互換試験であると分離する。4 分類を実効的な完了条件にするなら、権威的 floor を publication から辿れるまで本 deliverable は未完了と扱う必要がある。
- 区別: 実在する制約。仮想リスクではない。

### 2. `anomaly_class` は実在 field ではなく、別概念を代入している

- 深刻度: 高
- 根拠:
  - `s2-plan.md:74-75,238`
  - `orchestrator/campaign/p3_b4_analysis_ledgers.py:90-97,123-143`
  - `orchestrator/campaign/p3_b4_raw_record_producer.py:1354-1434`
  - `prereg-s7.md:8-9`
- 壊れ方: `B4DigestRedClass` は「B-4 treatment assignment 前に記録された red class」であり、arm 実行時の anomaly class ではない。source object に `anomaly_class` はなく、あるのは `evidence_issues` と `protocol_ok` である。`source_scope:"scheduled_precursor"` を付けても、必須 field の意味を満たしたことにはならない。
- 最小修正案: 必須 `anomaly_class` は `availability:"absent"` とし、`precursor_digest_red_classes` を補助 field として全要素保存する。`evidence_issues` も別名のまま完全射影する。
- 区別: 実在欠陥。識別子の二義化である。

### 3. API の呼出し形は成立するが、例外境界が未設計

- 深刻度: 中
- 根拠:
  - `orchestrator/campaign/p3_b4_prerun_issuer.py:93-99,1007-1055`
  - `orchestrator/campaign/p3_b4_raw_record_producer.py:1894-1898,2047-2057`
  - `orchestrator/campaign/p3_b4_analysis_ledgers.py:62-67,1201-1232`
  - `orchestrator/campaign/p3_b4_analysis_path.py:199-215`
  - `s2-plan.md:38-52,140-144`
- 判定:
  - `load_b4_prerun_publication(str(path))`: 合う。ただし `B4PrerunIssuerError` を送出する。
  - `assemble_b4_raw_analysis(publication=publication)`: 合う。`B4RawRecordRejection` を返す分岐は計画が扱っている。
  - `build_contract_binding(...)`: registry、manifest、schedule receipt、seed receipt の4 keywordが必要で、失敗は `B4LedgerError` 等の例外。
  - `evaluate_b4_artifacts(...)`: 6 keywordが必要。artifact/adapter の拒否は例外ではなく invalid な `B4AnalysisResult` として返る。
- 壊れ方: plan の `main()` は `B4MaterialReportError` だけを `parser.error()` へ変換する予定だが、loader と binding の例外をどこで包むかが書かれていない。そのままなら malformed publication で traceback が出て、計画自身の CLI 契約に反する。
- 最小修正案: `_load_and_evaluate()` で既知の issuer/ledger 例外だけを理由を保存して `B4MaterialReportError` へ変換する。assembly rejection と evaluator invalid result は別経路のまま保つ。各分岐の no-write test を1本ずつ置く。
- 区別: 実在する計画欠落。

### 4. clean subprocess の条件が不足している

- 深刻度: 中
- 根拠:
  - `s2-plan.md:14-17,200-204`
  - `orchestrator/campaign/layer3_report.py:42-44`
  - `orchestrator/tests/test_layer3_report.py:2523-2533`
- 壊れ方: shim 自体は `Path(__file__).resolve().parents[2]` を入れれば正しい。しかし plan の「clean subprocess」には、`PYTHONPATH` 除去、`PYTHONNOUSERSITE=1`、repo 外の `cwd` が明記されていない。これらが無いと、package import が環境に救われ、正規コマンドの `ModuleNotFoundError` 退行を捕まえられない。
- 最小修正案: 既存 Layer3 test と同じ環境と repo 外 `cwd` をそのまま採用する。なお同じ argv の上書き拒否試験があるため subprocess 起動は1回ではなく2回である。
- 区別: 実在する試験設計の穴。

### 5. 出力先 guard は必要だが、実パス比較が必要

- 深刻度: 中
- 根拠:
  - `s2-plan.md:118-128,245-249`
  - `orchestrator/campaign/autonomous_trial_completeness.py:3317-3336,3379-3385`
  - `orchestrator/campaign/layer3_report.py:193-197`
- 壊れ方: campaign 配下へ B-4 の2 file を書くと、Layer3 の `artifact_refs` と campaign 現物の exact set が不一致になり、完全性検査が赤くなる。plan の disjoint guard はこの実在契約への直接対応であり scope 逸脱ではない。ただし `--output-root PATH` を字面のまま比較すると、symlink 親を経由して campaign 内へ書ける。
- 最小修正案: 書込みに使うものと同じ resolved output path を campaign root の resolved path と比較する。一般化した official-root admission は足さない。
- 区別: exact-set 摂動は実在欠陥。symlink 経路は到達可能だが未観測のリスク。

### 6. 2 invoke / 60 秒未満の根拠が fixture scope と再評価回数を数えていない

- 深刻度: 中
- 根拠:
  - `s2-plan.md:160-208`
  - `orchestrator/tests/test_p3_b4_raw_record_producer.py:380-381,881-917,920-937`
- 壊れ方: 引用元 fixture は既定の function scope である。full publication を必要とする test 1、4、7、8 がそれぞれ生成すれば、real `invoke()` は2回ではなく少なくとも8回になる。また test 1、4、7と CLI 2起動だけでも、201 block の load/assembly/evaluation は少なくとも5回走る。plan の「全入力評価後に出力確認」という順序なら、上書き拒否の2回目も再assemblyする。
- 最小修正案: `tmp_path_factory` を使う module-scope の immutable publication fixture を明記し、CLI の2回目は入力再評価前に既存2 fileを拒否する。焦点走と受入全走の exact argv も plan に追記する。
- 区別: 実在する見積り根拠不足。

### 7. scope と他 wave の衝突

- 深刻度: 低
- 根拠:
  - `s2-plan.md:210-221`
  - `orchestrator/campaign/p3_b4_raw_record_producer.py:655-668`
- 判定: 新規2 file は t1784、t1909、t2060 の編集 file と直接重ならない。完全射影検査、provenance byte binding、campaign disjoint 検査は現存契約への対応で、仮想リスク向けの一般化ではない。明瞭に将来専用なのは、sanctioned path から到達不能な4 verdict renderer test である。
- 注意: t1784 は raw producer が projection closure に含める `p3_b4_admission_record.py` を変更する。merge conflict は無いが、着地後の HEAD で fixture を再生成して焦点走する必要がある。t1909 と t2060 に直接編集衝突はない。
- 区別: 編集衝突はなし。t1784 は実在する意味的依存。

## 親 brief への所見

- **(P1): 条件付きで妥当。** publication loader は固定3 leafだけを読むため、通常の `<publication_root>/reports` は publication 集合を壊さない。ただし publication root が arm campaign 配下に置かれることは issuer が排除しておらず、disjoint 検査は必要である。
- **(P2): 不整合。** `s1-brief.md:58-62` は判断値を caller から受けないとしながら、`:73-75` は caller 必須 floor を provisional 採用している。D1060 とも両立しない。plan がこの案を拒否した点は正しいが、その結果、正規経路の判定は常時 protocol violation になる。
- **(P3): 妥当。** `layer3_report.py:42-44,786-808` と同じ shim を実装すれば file 直起動でき、qsub allowlist 追加は不要。
- **(P4): 一部不成立。** 初期 snapshot hash、model hash、予算消費を不在にする判断は現物と合う。anomaly class だけは precursor red class で代用できない。
- 不変条件1から4と編集面は plan で維持される。不変条件5の完全射影検査は本題そのもの。ただし不変条件6の4分類は schema 上だけで、正規経路では1分類しか実効化されない。
- 1 author 単位への並列分割は妥当。新規 module と fixture/test は密結合であり、さらに割る利益は小さい。
- `46 passed / 28.44s` は既存 producer/analysis 経路の生存を支持するが、新 generator、CLI、Markdown、反復assemblyの所要は支持しない。publication 0件は fixture 利用の根拠にはなるが、実成果物との end-to-end 適合証拠ではない。3 branch の実測は filename-level 非衝突を支持する。
- 受入環境は `tools/run_tests.py` とだけ指定され、焦点 nodeidと全走 argvが無い。pytest node 内から別 suite を起動する構成は禁止する旨も明記すべきである。

## テスト所要の見積り

- 実 `invoke()`:
  - plan の意図: on/off 各1回、計2回。
  - 現記述のまま function-scope fixture を複数 node が使う場合: 少なくとも8回。
  - 2回へ固定するには module-scope fixture の明記が必要。
- 201 block の full load/assembly/evaluation: 少なくとも5回。input provenance test の作り方次第で6回。
- clean subprocess: 上書き拒否を含め2起動。
- 耐久書込み:
  - setup 全体で `os.fsync` を確実に patch できれば、report.json/report.md の2 regular file。
  - 引用元 helper をそのまま使うだけでは、publication issuance と real seed は patch 区間外なので2 fileには閉じない。
- 現在の最遅 node は `140.0s` (`acceptance_duration_ledger.json:8185`)。新規 file の目標60秒は単独最遅 node より短いが、fixture scope未指定と5回以上の再assemblyを考えると静的には保証できない。
- 既存 B-4 46 testの28.44秒に、module fixtureを共有した新規 fileが60秒以内なら合計2分未満は plausible。ただし実走していないため達成扱いにはできない。

## 検査できなかったこと

- read-only 制約のため pytest、正規 CLI、実 fsync 回数の計測は実施していない。
- B-4 publication artifact は実在0件なので、実成果物での field 値域と end-to-end report bytesは確認できない。
- 未実装 module の Markdown escaping、hard-link rollback、symlink path処理は静的計画以上には検証できない。