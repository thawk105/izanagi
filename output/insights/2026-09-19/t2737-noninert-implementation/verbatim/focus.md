## 総括

**GO：現状の実装と、BACK_OFF=1・phase1の計器保存。** 新たな欠陥・回帰は見つかりませんでした。M1〜M6変異と受入全走は未了であり、受入完了の判定ではありません。実装変更・pytest実行は行っていません。

旧新4 TUの**全200行・17ハンク**を読み、生TUから再生成したdiffが保存diffと完全一致することも確認しました。差分の分類は以下です。

| 差分 | 独立確認 |
|---|---|
| path | gflags登録元・ERR診断の`old/`→`new/`。計器の引数変更なし |
| `__LINE__` | transactionのERR表示150→148のみ。[transaction.cc.diff:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/live-final/t2737-pxawx_em/transaction.cc.diff:20) |
| pragma | include guard化に伴う空白行の消失。WFGの処理本体・発火条件は保存。[wfg.cc.diff:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/live-final/t2737-pxawx_em/wfg.cc.diff:3) |
| using | rwlockの無条件includeにより3 TUへ`using namespace std;`追加。空白差とは区別。study lock本体に差分なし。[ycsb_ss2pl.cc.diff:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/live-final/t2737-pxawx_em/ycsb_ss2pl.cc.diff:3) |
| DLR表示 | `DLR0`→`DLR1`。数値`SS2PL_DLR=0`と`BACK_OFF=1`は保存。[util.cc.diff:39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/live-final/t2737-pxawx_em/util.cc.diff:39) |

この全差分に、計器呼出しの削除・引数変更・包含する分岐／ループの変更はありません。study lockとWFG本体も、上記診断差を除き保存されています。

| review所見 | 状態 | 判定 |
|---|---|---|
| 新設文字列テスト2本 | **closed** | 取消し済み。既存テストのHEAD比差分なし。production変更はrunner／patchのみ |
| 現実装の計器保存 | **closed** | 最終BACK_OFF=1の全4 TU比較で確認 |
| M5の検出力 | **partial** | 未実施。自動probeは差分を保存するだけで、SURVIVED予測。親による同じ全TU比較での欠落拒否は未確認 |
| M6の検出帰属 | **partial** | 最初の実失敗へ帰属する裁定は妥当。変異未実施のためbuild拒否／不在検査到達は未確定 |
| DLR表示差の説明 | **closed** | 表示と数値選択を分離できている |
| 共有header consumer | **closed** | probeのIMPL=0/1各buildにd2pl・bomb・tpccを含む |
| fix2のBACK_OFF／sidecar | **closed** | 最終dispatchの成功とrecordで確認 |
| regressed | **該当なし** | 今回確認した範囲で検出なし |

実機数値は原記録と照合しました。job9293.nqsvは**1 passed／113.32秒、Elapse 118秒**です。[実行ログ:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/live-final-1.log:12)  
最終recordはBACK_OFF=1、IMPL=1／KIND=0／DLR=0／WFG=1。supply 4件成功、meaning 4件未宣言、raw admission=true、plain SのWFG不在確認3 TU、abort増分transaction=0／workload=2でした。[result.json:4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/live-final/t2737-pxawx_em/result.json:4)

C++原ログはstudy_lock_testがIMPL=0で8件、IMPL=1で11件、make_db_testが各1件成功。S拒否の3件／1件とpristine原本config.hの前後不在は、成功probeのassertで確認されています。[外部probe:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/test_t2737_live_probe.py:56)

親READMEに過剰主張はありません。[README:50](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2737-noninert-codex/output/insights/2026-09-19/t2737-noninert-implementation/README.md:50)の親判定は**BACK_OFF=0**、今回の独立確認は**BACK_OFF=1最終**です。runtime meaning、controls全体、M1〜M6、受入全走の成立へは拡張しません。新gateの追加要求はありません。