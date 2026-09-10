## 所見

### 所見 1 — 条件 (i) の計測 ID は存在するが、D162 の三条件を同時に満たす計測は存在しない。

- 根拠: `output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration-witness.tsv:1-10`、`order.tsv:1-12`、`verdict.tsv:1-5` は、事前登録済みの stock/mode1/modeX 3 arm と `892042.nqsv` を示す。一方、同 artifact の `env_tag` と `attestation` が 0 hit であることは `s2-plan.md:7-11` に記録されている。`calibration-94a4b79fa31bba3c.json:72,1569,1637` の環境情報や、`silo_ladder_rung1.json:124-137,550-570` の attestation は別計測であり、後から合成できない。D162 は同一計測での保持を要求する (`refs/D162.md:42-55`)。
- 放置時の影響: `892042` を監査参照から落とすと条件 (i) の証拠が不正確になる。逆に calibration/T-126 artifact を合成すると、正例の受理集合を不正に拡大する。
- 自己判定: **real**。ただし NO-GO を倒す証拠ではない。

### 所見 2 — D229 は producer・attempt ledger・schedule の先行整備を禁じておらず、親の「実装可能 slice 0 件」は広すぎる。

- 根拠: D229 は着手順序を明記し、pilot 自身を D162 の (i)(ii) を満たす計測にできるとしている (`refs/D229.md:43-51`)。さらに既存の試行台帳・系列 FSM・投入束縛・原子公開・identity の再利用を future producer の設計択一として認める (`refs/D229.md:53-58`)。対象候補は `orchestrator/qualification/contract.py:38-58,150-159` に列挙される。
- 放置時の影響: raw receipt を作る前段まで不要に凍結すると、D162 (ii) を満たす pilot 自体が作れず、T-338 の待ち状態が無期限になる。これは現時点の certified 選択や受理集合を変えないが、次段へ進む参照と実装順序を誤る。
- 自己判定: **real**。先行可能なのは権威を持たない producer/台帳基盤であり、validator/consumer 本体ではない。

### 所見 3 — D163/D229 自身は docs-only だが、隣接 T-139 と qualification には再利用可能な非 gate 実装面が既にある。

- 根拠: D163 は拒否専用 adapter・fixture leaf を含めて実装しないと定める (`docs/decisions.md:8084-8104`)、D229 も code/test/gate/schema/artifact を変更しないと定める (`refs/D229.md:9-11`)。しかし `orchestrator/preregistration/__init__.py:1-28`、`orchestrator/qualification/__init__.py:2-32`、`orchestrator/tests/test_t139_preregistration_binding.py:904-916` には parser、契約、非 admission API の実装と検査が存在する。
- 放置時の影響: 「repo に実装面がない」と一般化すると、producer 段で再利用できる台帳・契約を見落とし、不要な再実装を招く。これらを RF gate と誤って流用しても、明示的な no-promotion 境界を越えない限り受理集合は変わらない。
- 自己判定: **real**。

### 所見 4 — J 禁止は文書とシミュレーションにはあるが、投入履歴を読む実効 gate にはなっていない。

- 根拠: simulation は admission gate ではないと明記され (`orchestrator/preregistration/stress_check_simulation.py:1-6`)、`J_VALUES` も再計算補助に限定される (`:35-60`)。`pilot_ready=False` は `:730-740` にある。approval payload の top-level key に J/attempt はなく (`orchestrator/preregistration/approval_payload.py:38-50`)、alpha descriptor 自身も台帳の存在や履歴を証明しない (`:129-141`)。予約 commit も「pin しない。全履歴から再導出」と検査されるだけである (`orchestrator/tests/test_t139_approval_payload.py:62-66`)。
- 放置時の影響: 文書 digest や固定 `J_VALUES` のテストが緑でも、結果後の追加 submission・slot・attempt を止められず、将来の正例受理集合に自己根付き J が入り得る。
- 自己判定: **real**。

### 所見 5 — 既存 floor verifier は実際に import・consumer 接続されるが、Q11 の raw receipt validator にはならない。

- 根拠: `orchestrator/campaign/s8b_floor_stats.py:593-624,798-883` は cells/floors の再計算を行う一方、attempt registry・schedule・raw 真正性を保証しないと明記する (`:598-602`)。既存 consumer は floor freeze 専用 (`s8b_holdout_freeze.py:1391-1395`、`s8b_ratified_freeze.py:2235-2246`)。test import も floor API のみ (`orchestrator/tests/test_s8b_floor_stats.py:32-51`)。pytest の収集先は `pytest.ini:12-14`、受入形の実行経路は `tools/run_tests.py:391-399,519-579,1698-1721,1898-1907` である。`tools/check_docs.py:2-10` 自身も意味的ずれを検出できないと明記する。
- 放置時の影響: floor schema の緑と RF の raw receipt 検証を混同し、RF の accepted set・材料レポート・consumer 参照は一つも増えない。test collection や `check_docs.py` の成功だけでは未結線 leaf が成果物にならない。
- 自己判定: **real**。

### 所見 6 — 親実測の #4 は状態表示を gate と呼び、#5 は参照元が repo 外で独立再検証できない。

- 根拠: 親の記載は `s1-brief.md:23-27`、計画の訂正版は `s2-plan.md:17-22`。`pilot_ready=False` は `stress_check_simulation.py:737`、未充足列は `:738` だが、実際の禁止状態は `docs/decisions.md:13470-13482`、解除権限は `:13581-13588` である。33 件の裁定控えは `parent-handoff.md:31-32` が repo 外 inbox として参照しており、現在確認できる `docs/worklog.md:620-623` は T-338 の持越し一覧に過ぎない。
- 放置時の影響: simulation の値を qsub gate と誤参照し、また未確認の「新裁定なし」を根拠にすれば、pilot の禁止状態や T-339 境界の参照を誤る。ただし現行の受理集合自体は変わらない。
- 自己判定: **real**。

## NO-GO を倒せたか

倒せなかった。`892042.nqsv` により D162 (i) は実在するが、同一計測の (ii) と RF consumer hook の (iii) がないため、D162 (10) と `DW-G04` (`refs/D162.md:49-55`、`refs/dev-wave-core.md:60-63`) は validator/consumer の production code・schema・test をまだ許可しない。

ただし親の「何も先行できない」は訂正が必要である。別 wave なら `orchestrator/qualification/attempt_ledger.py`、`series.py`、`submission.py`、`atomic_publish.py`、`identity.py`、`collector.py` などを producer/receipt 前段として再利用・整備できる。これは T-339 側の前段であり、正例適格性を発行する validator ではない。`892042` 固定拒否 test、純粋 RF calculator、floor verifier 流用は未結線 leaf のため、現 wave の実装 slice にはならない。

## 依頼と [T-339] scope の境界

依頼側は「raw receipt から独立 validator が再計算し、J の後付けを拒否する経路」までを T-338 の残件としている (`s1-brief.md:5-12`)。

一方、Q11 が後続 scope として列挙するのは、計測 producer、attempt registry、schedule validator、RF calculator、[T-337] authority、層 3 次版、selector/material report consumer、双射・変異検査である (`refs/t338-package.md:302-312`)。raw receipt の供給元と受理 consumer を除外したまま validator だけを実装する境界は、実効性を持たない。

返すべき択一は次の通り。

- **A（推奨）**: T-339 境界と D162/D229 を維持し、今回は NO-GO。次の一手は producer/attempt ledger/pilot の前段 wave を起票し、pilot が (i)(ii) を満たした後に validator/consumer を起票する。
- **B**: T-339 を T-338 に戻し、producer → pilot → validator/consumer の全順序を scope に入れる。D229 はこの順序なら D162 の supersede を要求していない。validator を pilot より先に置くなら、その時点で D162/D229 の明示 supersede が別途必要になる。

## 親実測の検証

| # | 判定 | 根拠 |
|---|---|---|
| 1 | 概ね正しい | `s2-plan.md:17`。全 19 worktree の対象 2 ファイルについて branch diff と未コミット差分を再走査し、該当なし。稼働 wave の編集面も `parent-handoff.md:12-17` と一致。 |
| 2 | 正しい | `s1-brief.md:17-18` の六語を `orchestrator/` と `tools/` で再検索し 0 hit。 |
| 3 | 正しいが限定付き | D162 の三連言は `refs/D162.md:49-55`、D229 の順序は `refs/D229.md:43-51`。D229 は producer/pilot 前段までを禁止していない。 |
| 4 | 根拠を訂正 | `pilot_ready` は `stress_check_simulation.py:737-738` の状態表示で gate ではない。禁止の正本は `docs/decisions.md:13470-13482,13581-13588`。 |
| 5 | 独立確認不能 | `s2-plan.md:21` と `parent-handoff.md:31-32` が参照する 33 件ファイルは repo 外で、現 sandbox から内容を取得できない。0 hit を緑とは扱わない。 |
| 6 | 正しい | Q11 の T-339 列挙は `refs/t338-package.md:302-312` と一致する。ただし T-339 の producer/pilot 前段まで含めて「実装不可」と一般化してはならない。 |

pytest、`check_docs.py`、受入全走は本段では実行していない。 read-only 静的検査として、実行済み結果を緑とは報告しない。

## 総括

**NO-GO。** `892042.nqsv` は条件 (i) の既存証拠だが、同一計測の env tag/attestation と RF consumer hook がなく、現 T-338 scope の validator/consumer は land できない。一方、D229 は producer・台帳・pilot の前段を禁じておらず、親の「実装面 0」は過大である。ユーザーへは、T-339 境界を維持して前段 wave を起票するか、全順序を T-338 に戻すかを返すべきである。