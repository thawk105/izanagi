# 変異本走 — [T-243] spool + fold の land blocker 解消 wave

anchor commit: `c829d071ee20345e87d8652d94f74e87be0dc964`
spec sha256: `25d6ea69d7243e3d65a3b4580e5ee861ca58e0e06173dd43b2103e36e09d69c7`
runner: `tools/mutation_harness.py --runner-mode dispatch --detached`
(Pegasus gen_S 計算ノードへ 1 変異 = 1 job で dispatch、42 run)

## 結果 (親の裁定込み)

| 区分 | 件数 | 結果 |
|---|---:|---|
| 負例 (`expected_status=KILLED`) | 34 | **全件 KILLED** |
| 正例 (`expected_status=SURVIVED`) | 7 | **全件 SURVIVED** |

harness の生の分類は `KILLED 24 / SURVIVED 5 / MISMATCH 12` である。
MISMATCH 12 件の内訳と裁定は次のとおり。

### 正例 2 件 (P01 / P05) — フレークにより MISMATCH。**裁定 = SURVIVED**

赤くなった node は `orchestrator/tests/test_codex_worker_launch.py` の 2 件だけで、
**変異差分が到達しえないファイル**である。`DW-O18` に従い単独再走したところ
**6 passed in 5.25s** で全緑。同 anchor の受入全走も 5185 passed / 0 failed。
並行負荷下の自己干渉フレークと帰属した (先例: main の [T-244] が同型を実測)。

### 負例 10 件 — 事前登録 node は赤。**裁定 = KILLED、ただし帰属は単一理由でない**

| # | 追加で赤くなった node 数 (フレーク除外後) |
|---|---:|
| N14, N18 | 0 (フレークのみ。**実質は事前登録どおりの単一理由 kill**) |
| N02, N06, N07, N21, N37 | 1 |
| N19, N23 | 4 |
| N27 | 35 |

いずれも**事前登録した node が実際に赤くなっている**ため、gate の検出力は示せている。
MISMATCH は「予期しない node も赤くなった」ことによるもので、
`DW-M08` の意味では**帰属が単一理由に絞れていない**という所見である。
N27 (境界定数のずらし) が 35 件と突出するのは、世代分離が corpus 解析の広い経路に効くためで、
設計上の想定内である。

したがって単一理由の kill は 26 件 (24 + N14/N18)、帰属が広い kill が 8 件である。

## 事前登録から除外した 3 件

変異 spec 作成時に、**単独理由で赤くなる anchor が実装に存在しない**ため除外した。
gate 自体は存在するが、変異で検出力を示せない状態である。

| # | 除外理由 |
|---|---|
| N12 (冪等性) | receipt 検査だけを外しても、GC 後の 2 回目は fragment 0 件の no-op のままで「二重追記」を作れない |
| N24 (fold rc 無視) | 現行 fold API は rc でなく例外を返すため、事前登録の「rc 無視」に対応する anchor がない |
| N25 (pending 0 件 postcondition) | 最初の pending 検査を外しても staged-path closure と commit 後検査が同じ入力を先に拒否する |

これは worklog fragment の `{{T:spool-mutation-attribution}}` へ起票した。

## 一次資料

- `mutation-spec.json` — 事前登録した 41 変異 (負例 34 + 正例 7)
- `mutation-ledger.json` — harness の raw 台帳 (各変異の failed_nodes・artifact path を含む)
