# live-2 の親判定

job9140.nqsv、pytest 1 passed / 94.74秒、job Elapse 100秒、rc0。
probeはauthor9bd4077f1のbytesをwaveへ展開した木で実行。BACK_OFF=0であり、production controlsのphase呼出しは1を指定する点は別に確認する。
phase1 IMPL1/KIND0/DLR0/WFG1の4 supplyがrequested-default-preprocess-different、meaning4は未宣言、raw admission=true。
Sはowner-tu-unresolved3件/configure-failed1件。plain SのWFG不在検査は3TUで受理、abort増分はtransaction0/workload2。
IMPL0/1のstudy_lock_testとmake_db_testがそれぞれ成功。pristine原本config.hは前後とも不在。

## 全4TU差分の分類
生diffはlive-2配下でtransaction28行、util47行、wfg50行、ycsb75行。親が200行全文を確認した。
- transaction: rwlock.hh無条件include由来using namespace stdの追加、pragma由来空行の除去、ERRのsource pathと行150→148。
- util: 同じusing追加、ERR内source path、ShowOptParametersの旧DLR表示DLR0→DLR1。明示SS2PL_DLR表示は0のまま。
- wfg: pragma由来空行の除去、ERRのsource pathだけ。durable処理と発火条件は同一。
- ycsb: using追加、pragma由来空行の除去、gflags登録・ERRのsource pathだけ。
計器呼出し・引数・包含する制御構造、study lock本体の差分はない。これは上記条件の実前処理比較であり、runtime意味認証やcontrols成立ではない。
M5の負例はまだ実行しておらず、計器保存比較の検出力は未確認。
