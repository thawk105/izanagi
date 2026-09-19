## 総括

**NO-GO（受入検証の修正が必要）。** production差分は概ね必要最小です。新gate・台帳・一般化、f/g復元、inert target・軸従属・比較条件・abort所有権の変更は見当たりません。pytest・buildは未実走です。

- **must — 追加テスト2本が実装文字列の写し。**  
  [test_ss2pl_lock_study.py:65](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2737-noninert-codex/orchestrator/tests/test_ss2pl_lock_study.py:65)、同78行。変数名・ソース順・patch文字列を固定しており、実際の依存準備や分岐の成立を確認しません。無害な書換えで赤になり、文字列を残した挙動破壊は取り逃がします。  
  **最小修正:** 新設2本だけを削除・置換し、pristineからの実phase1 build、IMPL=0/1の既存C++テスト、実WFG不在検査へ検証を集約する。既存テストは変更しない。同じ確認を恒久テストとprobeへ重複実装する必要はありません。

- **must — TU保存だけでは計器保存・M5検出が閉じない。**  
  [test_t2737_live_probe.py:71](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2737-noninert-codex/tools/test_t2737_live_probe.py:71)。assertはTU名集合だけで、差分内容は74行で保存するのみです。`publish_wait`実呼出しを消しても、この比較部分は成功します。authorは限界を明記しており、虚偽報告ではありませんが、受入条件は未充足です。  
  **最小検証:** 実走で得た旧新4 TUの全差分をレビューし、path・空白・`__LINE__`等の各差分を個別説明する。計器呼出しの引数・制御構造、study lockとWFG本体に説明不能な差分がないことを記録する。次にphase1で有効な`publish_wait`実呼出し1箇所だけを改行保持で削除し、実前処理を再実行。同じ比較基準がその欠落を拒否することを示す。名前の存在・件数照合だけにはしない。旧binary buildや新しい比較基盤は不要です。

- **must — M6の予定検出層が実装と合わない。**  
  [ruling.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/ruling.md:28)、[probe:79](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2737-noninert-codex/tools/test_t2737_live_probe.py:79)。WFG=0では新headerが`SS2PLWfgMode`を隠す一方、[patch:2266](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2737-noninert-codex/patches/ss2pl-lock-protocol-study.patch:2266)の`wfg.cc`は同型を無条件参照します。無条件source追加の変異は、既存不在検査へ届く前にコンパイル失敗する見込みです。これを「不在検査がkill」と数えると検出力を誤報します。  
  **最小修正:** 実走の最初の失敗箇所で帰属を更新する。コンパイルで止まれば「build拒否、不在検査は未到達」と記録する。検査到達のためにproductionガードを緩めない。

- **should — 共有headerのconsumer確認がprobeにない。**  
  [patch:2773](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2737-noninert-codex/patches/ss2pl-lock-protocol-study.patch:2773)は共有`rwlock.hh`を変更しますが、probeはycsbとSS2PLテストだけです。既存configure木でd2pl consumerとSS2PL bomb/tpccの対象をbuildする程度の確認を追加するか、未確認範囲として残してください。性能測定は不要です。

**nitなし。** 親READMEはphase1 supplyとruntime meaning・controls全体を区別しており、未成立を成立済みへ一般化していません。過去revSの成功や13.7秒を今回の証拠・保証値として扱っていない点も妥当です。