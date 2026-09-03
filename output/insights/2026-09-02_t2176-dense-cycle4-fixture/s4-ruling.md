# 段 4 裁定 — [T-2176] / D1455

起点 main: `24b31d2a37353d63a4f715ed2170d13e25df3fe3`。裁定時の local main: `42116cc6568dbccf4f2dfa433907a530b128268f`
(受入前に取り込む)。

## 所見の裁定

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-1 | 新テストが realizability を固定せず、非物理な fixture も通す | real | 採用 (縮小) | 内 |
| A-2 | 「全 counter」の列挙から `abort_reasons` が漏れている | real | 採用 | 内 |
| A-3 | 無条件変異は既存 r5 テストも殺すので一意帰属が未確認 | real | 採用 | 内 |
| A-4 | D799 から「手製以外の経路がない」までは一般化できない | real | 採用 (記録の文言のみ) | 内 |
| B-1 | README 179 行の訂正は T-2177 / D1466 の所有面 | real | 採用 (方針変更) | 内 |
| B-2 | 在庫 pin の閉包は `_V2_FIXTURE_FILES` + README 表だけで足りる | real | 採用 | 内 |
| B-3 | HEAD blob 束縛の対象外、production 変更なし | real | 採用 | 内 |
| B-4 | 壊れた `certified=True` は downstream 全層を通過する | real | **不採用** | **外** |
| B-5 | 編集 path は README を除き適正 | real | 採用 | 内 |
| B-6 | `r9_dense_cycle4` は命名衝突なし | real | 採用 | 内 |

## 親 brief の訂正 (子の指摘で覆った前提)

- **(P1-3) を撤回する。** 1 file は 1 thread の逐次実行を意味し、T3 が T0 より前に genesis を読んだまま
  最後に commit する実行を表せない。`trace_0.log` (T0/T1/T2) と `trace_1.log` (T3) の 2 file にする。
- **(P1-4) を撤回する。** `fixtures/README.md` の 179 行目 (「どの fixture も担っていない」) は
  **D1466 が既に訂正を裁定済み**で、その訂正は T-2177 が所有し、「r5 はグラフ事実の検出を担うが
  certified 遷移は担わない」区別を落とさずに書くことを要求している。本 wave が同じ行を書き換えると
  その区別を落とす。**本 wave は 179 行目に触れない。** README は表へ r9 の 1 行を足すだけにする。
  親が段 1 で D1466 を引いていなかったことが原因である。

## 確定プラン (v2)

段 2 プランを次の 5 点だけ変えて確定する。それ以外は段 2 プランのとおり。

1. README の 179 行目は**変更しない**。表 (`README.md:30` の r8 行の直後) への r9 行追加だけを行う。
2. 新テストへ `assert res.abort_reasons == {}` を足す (A-2)。
3. 新テストへ realizability の pin を足す (A-1、縮小採用)。`parse_trace_dir` で得た
   `(txid, thid, commit)` の 4 組が `[(0,0,(1,1)), (1,0,(1,2)), (2,0,(1,3)), (3,1,(1,4))]` であることを
   assert する。これで「commit 順を逆転させた非物理 trace」が通らなくなる。
   **採らなかった範囲を明記する:** file 名と `thid` の対応 (T3 の frame を `trace_0.log` へ移し
   `trace_1.log` を空にする改変) はこの assert では捕まらない。`_V2_FIXTURE_FILES` が
   `trace_1.log` の実在を pin することで部分的に塞がるだけである。**専用の検査器は新設しない** —
   仮想リスクに対する gate 追加であり、ユーザー指定の scope 外だからである。
4. `assert all(anomaly.length > 3 for anomaly in res.anomalies)` を落とす。直前の
   `total_cycles == 1` と `len(res.anomalies) == 1` と `a.length == 4` に含意され、寄与が無い。
5. 編集 path は 4 つに固定する。`orchestrator/verifier/` の production 変更は禁止。

## scope 外・ユーザー裁定へ返す候補 (B-4)

verifier が誤って `certified=True` を発行した場合、campaign pipeline・commit receipt・artifact
admission・oracle driver / report・層 3 report はいずれも DSG を再計算せず、その値を整合的に運ぶ。
つまり同じ壊れ方は downstream の全層を通過する。**本 wave では実装しない。**
「downstream に verifier から独立した長周期の意味検査を要求するか」を新規 task として裁定へ返す。
子が挙げた根拠 (file:line) は `s3-lensB.md` の所見 4 にある。

## 変異事前登録 (DW-M01 / DW-M03 / DW-M08)

本 wave は production 差分 0 の**テスト強化だけの wave**である。DW-M08 に従い、各変異を
**新テストを含む木**と**変更前 HEAD の木**の双方へ走らせ、新テストだけが検出する差分を示す。

変異位置はすべて `orchestrator/verifier/dsg.py` の `DSG.anomalies` (現行 252〜275 行)。
`core.verify_trace_dir` は 142 行でこれを呼び、integrity の全 counter はその前 (43〜140 行) で
確定しているので、`anomalies` の内側で `self.integrity.clean()` を参照できる。これはコードで確認した。

| ID | 変異 | 変更前 HEAD 木の期待 | 新テスト込みの木の期待 |
|---|---|---|---|
| M1 | `anomalies` で最短巡回長 4 以上の SCC を報告と `total` の双方から**無条件に**落とす | KILLED (既存 r5 テストが赤) | KILLED (r5 テスト + 新テスト) |
| M2 | 同じ処理を `self.integrity.clean()` が真のときだけ行う | **SURVIVED** | **KILLED (新テストだけ)** |
| M3 | 等価対照: `sccs.sort(key=len)` を `sccs.sort(key=lambda c: len(c))` にする | SURVIVED | SURVIVED |

- **単一理由性 (DW-M01):** M2 を親が模擬で実測した。新 fixture だけが
  `non-serializable → serializable / certified=True` へ動き、既存 18 fixture の verdict は
  1 つも変わらない。よって M2 の赤は新テスト 1 件に絞れる。M1 は絞れないので、
  **射程を露出させるための対照**として登録する (M2 単独では「条件が候補集合に含意されて
  恒真」かどうかを見せられないため、無条件版と対で登録する)。
- **kill の意味 (DW-M03):** M1・M2 とも受理集合が期待方向へ変わる (certified 偽の緑)。
  診断文字列だけの赤は kill に数えない。
- **通る正例 (DW-S04):** M3 (等価変異) は新テストを赤にしてはならない。加えて baseline
  (無変異) は全 fixture が現行 verdict のままでなければならない。
- **既知の非帰属赤:** `dsg.py` を変異させると `CONTRACT_LOADER_RELATIVE_PATHS` の HEAD blob 束縛に
  由来する `contract-loader-drift` の赤が出る (D1422 / worklog 1176 で実測済み、等価変異でも 53 node)。
  これは挙動の赤ではないので期待 node 集合から外し、根拠を記録して `--deselect` する。

## 不変条件 (段 5・6 を通じて維持)

- 絶対規律 2 を緩めない。anomaly を検出した入力を certified にしない。
- production コード (`orchestrator/verifier/*.py`) の差分は 0。
- 新 fixture の integrity は完全に clean。巡回はちょうど 1 本、長さ 4。
- 新テストの assert はどれも恒真でない。落とした assert (上記 4) を除き、各 assert が固有の情報を持つ。
