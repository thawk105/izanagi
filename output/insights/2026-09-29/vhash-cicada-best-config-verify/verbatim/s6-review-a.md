### A1 stock の分類が照合結果と食い違い得る

**重大度:** must-fix
**根拠:** [launch_cicada_run.py](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:972)、[同ファイル](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1018)、[同ファイル](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1093)
**影響:** 判定器が結果を格納した後に `proof_surfaces` の評価で例外が起きると、`verifier.error` が残って `stock_pass` は偽でも、`bcv_classification` は「その条件で巡回なし」と記録し得る。一次資料が分類欄を採用すると偽の緑になる。
**推奨対処:** stock の合格分類は `stock_pass(run)` を通った場合だけ返す。`bcv_stock_checks` にも判定器の error と許容 returncode の確認を含め、二つの合否経路を一致させる。

### A2 巡回を検出した stock に専用の分類がない

**重大度:** should
**根拠:** [launch_cicada_run.py](/work/1/SFC/tanab/tmp/vhash-cicada-best-config-verify-2026-09-29/launcher/launch_cicada_run.py:1018)
**影響:** 巡回が出た stock は単に「不合格」となり、R6 が求める主比較からの失格理由と non-serializable の結果が分類欄から失われる。
**推奨対処:** 判定器が non-serializable とし巡回を報告した場合を、診断異常・不成立と排他的な分類として明示する。保存済み witness への参照も分類に結び付ける。

## 総括

静的照合では、選択比較の wts 保存、aborted 版を飛ばした後の再読、read-only と書く txn の trts、OPT=0 の条件付き参照に明白な欠陥は見つからなかった。R5 の `b_wts` は終点 txn の raw W に結び付けられ、正例の同一 cell 対照も要求されている。build の cache 8 項目と 3 TU の define 照合も実行経路にある。

**このまま合否を記す実走には使わない。** A1 の分類と `stock_pass` を一本化し、A2 の巡回分類を直してから使うべきである。build・テスト・実走による確認は行っていない。