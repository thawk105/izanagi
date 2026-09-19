## 総括

**実装済み・未実走です。** phase1 の成立、計器保存、controls 全体の成立はまだ報告しません。

変更ファイル：

- [patches/ss2pl-lock-protocol-study.patch](patches/ss2pl-lock-protocol-study.patch)：a〜d を限定移植。e の条件付き `wfg.cc` を保存。既存 testing seam で宣言可視性を維持。
- [tools/pegasus/run_ss2pl_lock_study.py](tools/pegasus/run_ss2pl_lock_study.py)：関門前に helper を接続。base 作成・canonical 化、同じ依存 prefix/source、bounded manifest 観測、既存 deadline 内の timeout 配分を追加。
- [orchestrator/tests/test_ss2pl_lock_study.py](orchestrator/tests/test_ss2pl_lock_study.py)：局所契約の静的回帰テスト2本を追加。既存期待値は変更なし。
- [tools/test_t2737_live_probe.py](tools/test_t2737_live_probe.py)：96行の一回限り probe。実機構を stub せず、phase1、S拒否、S plain の WFG 不在・abort所有権、IMPL=0/1 の既存 C++ テストを検査します。

変更前の phase1 は pristine で4軸とも前処理失敗、warm でも IMPL/WFG は閉包差、DLR は command 差で拒否、KIND のみ受理でした。変更後は4軸の受理を期待しますが未検証です。S は従来どおり `owner-tu-unresolved` 3件・`configure-failed` 1件を期待します。

f/g 復元、inert target、KIND 従属、比較条件、abort所有権、登録簿、`INERT_DECLARED_DIFFERENCES` は変更していません。所有外の build caller、shell入口、receipt consumer、共有fixtureも変更なしです。共有 `rwlock.hh` の d2pl consumer と SS2PL の bomb/tpcc・C++ tests は波及確認対象です。

patch の一時木への適用、逆適用・再適用チェック、`git diff --check` は確認済みです。pytest/build・親受入・変異全走・commit/stage は未実施です。

親検証コマンド：

```bash
python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_ss2pl_lock_study.py
python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_buildcache_v2.py -k prepare_masstree_fetchcontent
python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes
```

実物 probe は `T2737_STOCK`、`T2737_THIRDPARTY`、`T2737_GFLAGS`、`T2737_GLOG` に既存絶対パス、`T2737_OUTPUT` に未作成の絶対パスを設定して実行します。THIRDPARTY は config.h 不在が必須です。

```bash
python3 tools/run_tests.py --force-dispatch tools/test_t2737_live_probe.py::test_t2737_pristine_phase1_and_rejected_stock_arm -n 0
```

**計器保存比較は独立確認へ分ける提案です。** probe が保存する旧新 phase1 全4 TU の `.ii` と `.diff` で、呼出し・引数・制御構造、および path・`__LINE__` 等の差分を確認してください。probe 成功だけではこの比較や M5 の検出成立を意味しません。