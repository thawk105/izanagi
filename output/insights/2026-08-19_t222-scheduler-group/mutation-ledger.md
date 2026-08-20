# [T-222] 変異台帳

対象 commit: `f67245cf2fe2e425e8fa935a190885e981c04004`
実行方式: 手動直列 (`DW-O19` 手順、`Edit` で単一置換 → `python3 tools/run_tests.py` 実走 →
`git checkout -- tools/pegasus/dispatch_compute.py` で復元、を4件直列実行)。
`tools/mutation_harness.py --runner-mode dispatch` は未使用 — 対象ファイルが
`campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` に含まれないことを確認したうえで、
同日の T-1303 wave (`output/insights/2026-08-19_t1303-spool-fold-digest/mutation-ledger.md`) の
precedent (親自身の直接実行が安定・高速) に倣った。

## baseline

変異前 (commit `f67245cf` 単独、`orchestrator/tests/test_pegasus_dispatch_compute.py` 全体):
188 passed, 0 failed (12.73s)。DW-O26 consumer sweep 13 file も全緑
(`test_mutation_harness.py` の5件赤はバッチ負荷起因のフレークと単独再走90/90緑で切り分け済み)。

## 落とし穴: full-file 実走のハング

M3 (`!= [DEFAULT_PROJECT]` → `!= ["WRONG"]`) はいずれの入力でも `_accounting_present` が
ほぼ常に `False` を返すようになり、`_Scheduler(accounting=True)` に依存する全188テスト中
半数近くが波及的に失敗する。この状態でファイル全体を4回実走したところ、いずれも
90〜300秒で無応答 (CPU時間はほぼ0のまま) になった。host load average は 5〜10
(18ユーザー在席、他 wave の `landed` advisory が実行中に複数回届いた) で、`free -h` は
199GiB available と潤沢で、単純なメモリ枯渇ではなかった。SIGTERM で終了させた際に
`pytest_sessionfinish` の hookwrapper teardown で `OSError: cannot send (already closed?)`
(`PluggyTeardownRaisedWarning`) が発生し、それまでに蓄積されていた進捗ドット (76%超) が
まとめて flush された — pytest-xdist (`-n 32`/`-n 4` いずれでも再現) の worker 集約・終了処理が、
大量の同時失敗 + host 混雑の組み合わせで極端に遅延する現象と見られる (根本原因は未特定)。
**対応:** 変異の検証に本当に必要な2テスト関数
(`test_accounting_requires_matching_request_id_and_all_nqsv_fields`,
`test_accounting_accepts_measured_nqsv_shape_only_when_id_matches`) だけへ nodeid で絞り込み、
M3・M4 を実走した。絞り込み後はいずれも2秒未満で完了し、再発しなかった。
この落とし穴自体は本 wave の実装差分とは無関係な既知でない infra 事象であり、
次にこのファイルへ広範囲な mutation を仕掛ける wave は同じ絞り込みを最初から使うとよい。

## 結果

| id | 概要 | 対象範囲 | 期待/実測 KILLED node 数 | 判定 |
|---|---|---|---|---|
| M1 | Group Name 検査分岐を丸ごと削除 (常に通す) | file 全体 | 4 / 4 (混在・重複・不一致・欠落の4parametrizeケースのみ。正例は影響なし — bypass は既に受理される入力を変えないため) | KILLED、完全一致 |
| M2 | `!=` を `not in` 相当 (部分一致) へ弱める | file 全体 | 2 / 2 (混在・重複の2ケース。段6敵対レビューで「重複ケースも検出される」と訂正済み — 当初の登録は混在のみと誤って記述していた) | KILLED、完全一致 |
| M3 | 期待値を `DEFAULT_PROJECT` から `"WRONG"` へ差し替え | 2 test 関数へ絞り込み (理由は上記落とし穴節) | 1 / 1 (正例テストのみ。7つの負例ケースは「False を期待」なので誤った理由でも False が返れば通ってしまい検出しない) | KILLED、完全一致 |
| M4 | 比較演算子 `!=` を `==` へ反転 | 2 test 関数へ絞り込み (同上) | 5 / 5 (混在・重複・不一致・欠落の4負例ケース + 正例テスト。過剰拒否と過小拒否を同時に検出する設計どおり) | KILLED、完全一致 |

**4/4 KILLED、SURVIVED 0、MISMATCH 0。** 全件で観測 node 集合を実走で確定した
(DW-M08、手動予測との食い違いは M3/M4 で判明 — 詳細は下記)。各変異後は `git checkout --` 後
`git diff --stat` が空であることで bytes 復元を確認した。

## 単一理由性・マスク層の確認 (DW-M01)

- M1・M2: Group Name 検査は `_accounting_present` 内のこの1分岐のみ。呼び出し側 (`:1935`,
  `:1944-1946`) は bool をそのまま使うだけで独自の Group Name 検査を持たない
  (段3 lens B #2/#3、段6 レビュー b#1/#2 で確認済み)。他4フィールドの検査条件も無傷。
- M3・M4: 同じ1分岐だが、この2件は `_accounting_present` を「ほぼ常に False」または
  「SFCのときだけFalse」という極端な方向へ倒すため、file 全体で実走すると
  `_Scheduler(accounting=True)` に依存する無関係な多数のテストへ波及する
  (「落とし穴」節参照)。この波及は「マスク層がある」ことを意味せず、単に
  `_accounting_present` の戻り値に依存する consumer が多数存在するという既知の事実の表れ。
  DW-M01 が求める「同じ入力を拒否する層が前後に無い」の確認は2 test 関数への絞り込みで
  引き続き成立する。

## 事前登録との差分 (DW-M08)

段4裁定時点の手動予測 (`s4-adjudication.md`) は M3 について「正例テストで KILLED」とだけ書き
負例側への影響を書いていなかった (実測と一致、問題なし)。M2 は当初「混在行だけ」と書いたが
段6敵対レビュー b#5 の指摘で「重複行も検出する」と実装前に訂正済み — 実測 (2/2、混在+重複) は
訂正後の記述と完全に一致した。M4 は「正例テストが真っ先にKILLEDする」という記述に対し、
実測は負例4件も同時にKILLEDすることを明らかにした — 記述の意図 (過剰拒否と過小拒否を同時に
検出する) とは整合するが、影響範囲の記述が不足していた。T-1411 wave の F323 型
under-registration と同型の教訓 (静的な手動予測だけに頼らず実走で確認する) が、
今回は commit 前の絞り込み実走で早期に露見し、記録の補正で済んだ。
