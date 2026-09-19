## 総括

**NO-GO（現planのままの実装着手）。局所修正の方針は妥当ですが、次の2点を補ってください。** 静的検査のみ実施し、編集・build・pytestは行っていません。

1. **study headerの宣言ガード追加が、IMPL=0の既存テストを壊します。**  
   [plan.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/artifacts/dev-wave-t2737-noninert-codex/plan.md:42)は宣言・定義全体を`IMPL==1`内へ移します。一方、[patch:830](patches/ss2pl-lock-protocol-study.patch:830)は`study_lock_test.cpp`を常にテスト対象へ追加し、[patch:986](patches/ss2pl-lock-protocol-study.patch:986)のfixtureは`SS2PLTxControl`等を無条件参照しています。既存のIMPLガードは一部のproductionテストだけです。  
   **最小修正:** IMPL=0ではstudy専用テストを対象から外し、`make_db_test`は維持する。production headerのガードを緩める必要はありません。

2. **helper本体だけのtimeout配分では、新規接続全体をdeadlineへ接続できません。**  
   planが指定する`observed_toolchain_manifest()`は、内部でtimeoutなしの`subprocess.run(... --version)`を呼びます（[buildcache.py:1195](orchestrator/campaign/buildcache.py:1195)、[buildcache.py:1235](orchestrator/campaign/buildcache.py:1235)）。終了後のdeadline確認だけでは、この呼出しを中断できません。  
   **最小修正:** runner側のmanifest取得も既存deadlineで制限する。取得後に残時間を再計算し、helperのconfigure／targetへ**合計が残予算内**となる正整数を渡す。2秒未満など配分不能なら呼出し前に拒否する。共有helper本体の変更は不要です。

その他の判断は以下です。

- **P1は予測として適切です。** 親briefも成立済みとは書いていません。planの参照は`HANDOFF:26`ではなく[29行](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/HANDOFF.md:29)です。revSの実測はf/g込みなので、a〜d限定版の証明には流用できません。
- **phase1の実経路:** `run()`はSからbuildします。限定版の受入は、計画どおりproductionの`build_target(arm="phase1")`直接呼出しで確認します。controls全体の成立とは区別してください。
- **計器保存:** a〜dはphase1のstudy経路・計器呼出しを保存する構造ですが、未実証です。全target TUで呼出し・引数・制御構造を比較する計画は妥当です。WFG=0の不在検査は別途必要です。
- **所有・変異の帰属:** helperは専用baseだけでなく、渡したmasstree sourceにも生成物を書きます。親実走では所有するstaging複製を使い、helper削除／後置の各変異も毎回pristineから開始してください。暖機済みstagingでは変異が隠れます。`publish_wait`削除の検出は計器保存比較に帰属し、条件関門の検出力とは数えません。

**検証候補:** pristineからのphase1実build、旧／限定patchの全TU計器保存比較、S plain buildのWFG不在・abort所有権確認に加え、IMPL=0のテストbuildとdeadline境界の検証を追加してください。13.7秒は過去1環境の観測値であり、timeout設定の保証値にはできません。