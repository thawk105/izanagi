## 所見

- 成果物の値、受理集合、参照を裁定外に変える重大所見はありません。確度: 高。静的検査のみで、pytest は実走していません。

## 変異 kill 判定

- **M1 — kill される。** `stored` と `resumed` は `analysis_commit` だけが異なります（`orchestrator/tests/test_b10_backoff_shape_sweep.py:835-836`）。`core()` に同 field を戻すと、最初に `assert "analysis_commit" not in binding.core()` が赤になります（同`:840-842`）。この assert を除いても `stored.core() == resumed.core()`（同`:843`）が赤になり、さらに実体の lock 比較も `stored != binding.as_dict()` となって `resume-binding` を送出します（`orchestrator/campaign/b10_backoff_shape_sweep.py:1564-1566`）。

- **M2 — kill される。** row の `analysis_commit` は旧 `f...`、現在 binding は `c...` です（`orchestrator/tests/test_b10_backoff_shape_sweep.py:1242-1251`）。比較を現在の`:2384-2385`間へ戻すと、同`:1255-1257`の正例呼び出しが予期しない `PreflightError` で失敗し、`:1258`の exact-map assert へ到達しません。nested binding と code hash は一致済みです（同`:1253-1254`）ので、M2 単独が拒否理由です。

- **M3 — kill される。** row の `source_commit` も旧 `f...` のままです（`orchestrator/tests/test_b10_backoff_shape_sweep.py:1252`）。比較を現在の `orchestrator/campaign/b10_backoff_shape_sweep.py:2385-2386` 間へ戻すと、M2 と同じ正例呼び出しが予期しない `resume-binding` で失敗します。M2 を戻さない単独変異なら、他の validator 条件は fixture により成立しています（同`:350-387`, `:1253-1254`）。

- **M4 — kill される。** `code_drift` は `resumed` から `analysis_code_sha256` だけを変更しています（`orchestrator/tests/test_b10_backoff_shape_sweep.py:862`）。同 field を `core()` から外すと `stored.core()` と `code_drift.core()` が等しくなり、最初に `assert ... != ...` が赤になります（同`:863`）。これを除いても lock、BUILD_START、commitment の三比較（`orchestrator/campaign/b10_backoff_shape_sweep.py:1564-1584`）がすべて通り、同`:866-869`の `_expect_code` が「例外なし」で赤になります。

## 反証できたもの

- プラン v2 の production 3 行削除は裁定どおりです。`core()` からだけ `analysis_commit` が消え（`orchestrator/campaign/b10_backoff_shape_sweep.py:213-220`）、過去 row の二つの commit 比較だけが消えています（同`:2380-2398`）。field、形式検査、現在 HEAD の記録は残っています（同`:198-211`, `:1386-1394`）。

- 台帳の両表は `2515` / `2911` へ更新され（`orchestrator/tests/test_ccbench_spawn_sites.py:817-833`, `:1961-1976`）、実 sink もそれぞれ `orchestrator/campaign/b10_backoff_shape_sweep.py:2515` と `:2911` です。

- 追加された二テストは裁定どおりです（`orchestrator/tests/test_b10_backoff_shape_sweep.py:828-869`, `:1238-1279`）。binding digest の期待値を literal 化せず、等値・不等値で検査しています。受理後の旧 commit 値も確認しています（同`:1259-1260`）。

- 禁止事項の内容束縛六つはすべて `core()` に残っています（`orchestrator/campaign/b10_backoff_shape_sweep.py:215-220`）。事前登録文書と spec の整合も `Preregistration` が保持します（同`:301-307`）。

- 解析 bytes と現在 HEAD blob の照合は維持されています（同`:1377-1385`）。`prereg_commit` の祖先検査も維持されています（同`:1347-1353`）。

- submission receipt の `source_commit` と現在 HEAD の照合は維持されています（同`:465-471`）。row/report の provenance 記録も残っています（同`:2651-2652`, `:3018-3028`）。

- correctness gate と anomaly 後の不採用経路は変更されていません。未認証、unstable、missing、underexposed は usable にならず（同`:1654-1667`）、family は indeterminate になります（同`:1752-1781`）。性能 binary は certified BUILD_DONE の SHA と再照合されます（同`:2430-2459`, `:2463-2482`）。

- 受理集合の変更は裁定された commit provenance 面に限定されています。WAL 束縛は引き続き prereg commit/blob、spec、patch、式、解析内容とその digest を比較します（同`:213-228`, `:1564-1584`）。block row も nested binding、spec、解析内容、receipt hash を検査します（同`:2380-2426`）。

- ただし単純除去の厳密な帰結として、過去 row の明示的 `analysis_commit` / `source_commit` は旧値だけでなく、欠落・任意値でも validator 自体は拒否しません（同`:2380-2398`）。これは段4 B-2 の選択肢Aで明示的に受け入れた範囲であり、新たな provenance gate を追加しない裁定と一致します。

- WAL テストで模擬しているのは lock/WAL の読み取りと lock codec です（`orchestrator/tests/test_b10_backoff_shape_sweep.py:847-859`）。`PreregistrationBinding` の三表現、filesystem existence、`assert_resumable_binding` の比較本体は実体です（`orchestrator/campaign/b10_backoff_shape_sweep.py:213-228`, `:1551-1584`）。block-row テストは monkeypatch を使わず、validator と receipt 再読/hash を実体で通します。

## nit

- M1 の事前登録にある「BUILD_START 比較は通る」という説明は正確ではありません。M1 下では lock 比較（`orchestrator/campaign/b10_backoff_shape_sweep.py:1564-1566`）だけでなく、到達すれば BUILD_START dict と commitment 比較も拒否します（同`:1575-1584`）。同じ commit 差の重複表現なので成果物影響はなく、M1 は確実に kill されます。

- M1/M4 は実体 gate より前の構造 assert で kill されます（`orchestrator/tests/test_b10_backoff_shape_sweep.py:840-845`, `:863-865`）。baseline では実体 gate を通しますが、変異時の最初の赤は gate 自身ではありません。

- `indexed[...]` の旧 commit 値 assert（同`:1259-1260`）は validator が同じ row object をそのまま格納するため恒真に近い記述用 assert です（`orchestrator/campaign/b10_backoff_shape_sweep.py:2423-2426`）。また、nested binding の assert（`orchestrator/tests/test_b10_backoff_shape_sweep.py:1271`）は直前の代入`:1270`から恒真です。いずれも独立した保護とは数えられません。

## 総括

- M1〜M4 はすべて静的に kill されます。
- 裁定された5項目と個別禁止事項に対する逸脱は確認できません。
- commit provenance 以外の内容、spec、patch、式、correctness、anomaly 拒否は維持されています。
- テストは一部に恒真・冗長な assert がありますが、登録変異の kill 能力は失われていません。
- pytest は実走しておらず、本判定はコード読解によるものです。