## 所見

- **C1｜must-fix｜brief (P2)、plan 1・2｜版 ID の忠実性。** 根拠: `external/ccbench/cc/cicada/transaction.cc:126,687-721,806-842,895-913`、`external/ccbench/cc/cicada/include/transaction.hh:173-189,229-245`、`plan.md:12-14`。plan は commit 時に `read_set_` の `ver_->ldAcqWts()` を読み直すが、読取時の wts を保存しない。GC が版を外し、`REUSE_VERSION=1` で object を再利用する経路について、対象 txn の read set が emit まで元の版を保持する保証を示していない。**放置すると:** 別版の ID を R に出し、欠けた依存によって壊れた variant が巡回 0 に見える。**推奨:** 読取時に TRACE 専用の版 ID を固定し、commit 時の pointer 値と照合する。少なくとも既定の GC・再利用条件で pointer の寿命を証明し、その条件を外れたビルドを対象外にする。

- **C2｜must-fix｜brief (P4)、plan 4・事前登録 J2/J3｜正例の帰属。** 根拠: `external/ccbench/cc/cicada/transaction.cc:253-283,463-593`、`external/ccbench/cc/cicada/include/transaction.hh:247-307`、`plan.md:15,26-29`。no-rts-update では省いた処理が reader 側、実際に通過するかを決める検査が後続 writer 側にある。reader の `changed/committed` と witness に同じ txid があるだけでは、「rts 更新があればその writer は abort した」とは確定しない。skip-read-recheck も他の検査を通ったことの照合が要る。**放置すると:** 偶然発生した別の巡回を壊し patch の赤検出として数える。**推奨:** 元 guard の判定値、対象 key・版、reader/writer の txid、両者の commit を結ぶ診断を残し、対応する witness の rw 辺と照合する。対照 cell にも同じ帰属条件を適用する。

- **C3｜must-fix｜brief の G0 完了判定・(P3)、plan 5・6｜後続 wave への接続。** 根拠: `orchestrator/campaign/pipeline.py:429-475,683-745`、`orchestrator/verifier/model.py:501-519,555-572`、`plan.md:16-18,29`。repo 外起動器と fixture は Cicada の診断を可能にするが、campaign の受理経路は `certified` を要求し、Cicada の巡回なしは `indeterminate` のまま reject する。**放置すると:** 「forwarding variant が正しさゲートを通れるようになった」という一次資料の主張が実際の受理集合と食い違う。**推奨:** この wave の達成を「指定 YCSB 履歴の巡回検出能力と stock 対照の観測」に限定する。campaign への供給経路、X/P 相当の証拠面、受理規則は後続の裁定パッケージに明記し、今回通過したとは書かない。

- **C4｜should｜brief (P2)、plan 2・5｜版順の前提を実走で照合。** 根拠: `external/ccbench/cc/cicada/include/time_stamp.hh:24-40`、`external/ccbench/cc/cicada/include/tuple.hh:74-90`、`external/ccbench/cc/cicada/transaction.cc:497-527`、`orchestrator/verifier/dsg.py:454-479,752-785`。64 bit wts の分割は大小を保存し、verifier は commit の出力順でなく各 key の版 ID 順で ww/rw を復元する。この対応は妥当だが、初期版より小さい成功書込みや、同一 key の版 ID 重複がないことまで fixture は示さない。`genesis_commits` と `version_dups` もその一般条件の完全な証明ではない。**放置すると:** 初期版を先頭に置く前提が崩れ、辺や integrity の判定が変わる。**推奨:** TRACE 実走で全成功 W の `wts > initial_wts`、同一 key の版 ID 一意性、実 chain 順との一致を検査し、失敗時は判定不能として記録する。read-only の古い snapshot は R の版で表し、C の timestamp を直列化順と呼ばない。

- **C5｜should｜brief (P5)、plan 3・未解決の論点｜対象 flag の境界。** 根拠: `external/ccbench/cmake/Options.cmake:31-34,53-54`、`external/ccbench/cc/cicada/include/transaction.hh:199-245`、`plan.md:14,35`。promotion と `REUSE_VERSION` は既定で 1。promotion は inline 最適化の内側なので提案の `#error` は有効だが、`REUSE_VERSION=1` を対象に含めるには C1 の寿命確認が必要である。**放置すると:** 未確認の構成まで同じ trace 忠実性が成立すると一次資料が読める。**推奨:** 実測した CMake 値を受理構成として固定し、inline/promotion・group commit・scan/insert/delete と同様、未検証の組合せを明示する。

- **C6｜should｜brief の規律 1、plan 6｜TRACE=0 同一性の証拠。** 根拠: `plan.md:12,17`、`external/ccbench/cc/cicada/ycsb_cicada.cc:23-43`。同一 TU の前処理比較は強いが、`transaction.cc` と初期 wts を渡す `ycsb_cicada.cc` の両方が対象である。正規化した `objdump -d` は正規化規則が広いと差を消し、`nm`/`strings` は残存の補助検査にとどまる。**放置すると:** trace 専用代入や命令の残存を見逃して規律 1 達成と報告する。**推奨:** 両 TU を同じ compile command で前処理比較し、正規化規則を保存する。対応する実行可能 section の命令 bytes も比較して根拠を残す。

- **C7｜should｜brief (P1)、plan 1・7｜配置裁定の表現。** 根拠: `ruling-D16.md` の一回限り例外、`ruling-D579.md:11-12`、`plan.md:3,18,33`。D16 の trace-hook の原則は `izanagi-trace` 枝であり、既存の out-of-tree 先例は Cicada への自動許可ではない。**放置すると:** 試作 patch の恒久配置が既決であるかのように一次資料へ残る。**推奨:** 今回の patch を試作成果物として明示し、恒久配置と pin 前進を未裁定として fragment に出す。

## brief / plan で正しいと確認した点

- `patches/ledger.json` は現行契約で entries がちょうど 1 件であり、今回の登録を README に限る修正は妥当（`orchestrator/campaign/silo_ladder_rung1_contract.py:513-519`）。`IZANAGI_` を含む新 patch が全件走査テストに掛かる点も確認できる（`orchestrator/tests/test_p3_s4_loop.py:8682-8691`）。
- read-only commit は `writePhase()` を通らないため、独立した emit が必要。書込み emit を `cpv()` 後、set clear 前に置く順序も妥当（`external/ccbench/cc/cicada/transaction.cc:895-958`）。
- verifier の ww と rw は版 ID 順で復元され、Cicada の実際の commit 完了順に依存しない（`orchestrator/verifier/dsg.py:752-785`）。read-only の古い snapshot は、それだけで偽の巡回を作る理由にならない。
- Cicada の巡回なしを `indeterminate`、巡回ありを `non-serializable` と報告する上限設定は正しい（`orchestrator/verifier/model.py:501-519,555-572`）。現時点の確認は静的点検で、stock・壊し patch・TRACE=0 の実走結果は未取得である。

## 総括

最優先は、読んだ版 ID を commit 時まで忠実に保持できることと、二つの正例の赤検出を変更した guard に帰属できることの確認である。今回の成果物は Cicada 履歴の巡回を検出する基盤になりうるが、現行 campaign で forwarding variant を `certified` として受理する門はまだ閉じない。