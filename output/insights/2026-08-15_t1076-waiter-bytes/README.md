# [T-1076] 稼働中の待ち手の実行 bytes 契約 — 変異台帳

対象 commit = `70ae5bf22d1fd04d8ab5656a66ec04e2abd11536` (実装 + テストの統合 commit)。
runner = `python3 tools/run_tests.py orchestrator/tests/test_dev_wave_wait.py -q -rf --force-dispatch`
(計算ノードへ dispatch)。期待 node の名前空間は runner の範囲と対であり、
`orchestrator/tests/test_dev_wave_wait.py` の 221 node に閉じている。

## 結果

| 台帳 | spec sha256 | 結果 |
|---|---|---|
| `mutation-ledger.json` (本走) | `ac40cae132ccf92d430eea86c891aaf3504b9e67f0542a25be015222362354da` | **7/7 KILLED、SURVIVED 0、MISMATCH 0、baseline rc=0** |
| `mutation-ledger-probe.json` (初回 probe・erratum) | `bad2a4cd68929617bf578f51966a3f3908077a4cee63a838673860d953e05eab` | 7 完了、SURVIVED 0、KILLED 3・MISMATCH 4 |

**probe の MISMATCH 4 件は検出漏れではない。** 親が段 4 で登録した期待 node が実際より狭く、
完全集合になっていなかったことによる (DW-M08 は完全集合との完全一致だけを KILLED とする)。
probe の観測 `failed_nodes` を権威 node 一覧 (junitxml 由来 221 件) へ写し戻して再登録し、
本走で 7/7 一致を得た。probe 台帳は erratum としてそのまま残す。

node id には 2 つの名前空間がある。pytest は param 内の制御文字を ASCII エスケープし、
harness は backslash を `/` へ潰す。両者を正規化して一意対応するものだけを採った
(未解決があれば spec を作らず停止する導出にした)。

## 変異の内訳

| ID | 位置 | 変異 | 期待 node 数 | 結果 |
|---|---|---|---|---|
| M01 | gate の比較 | 比較を削除して常に通す | 3 | KILLED |
| M02 | gate の比較 | `!=` を `==` へ反転 (過剰拒否の検出 = 正例側) | 78 | KILLED |
| M03 | gate の位置 | `run_logged` の後へ移動 | 24 | KILLED |
| M04 | 照合不能処理 | 束縛不能 sentinel を検査省略へ落とす | 1 | KILLED |
| M05 | 束縛時点 | import 時束縛を pathname 再読へ退行 | 1 | KILLED |
| M06 | 既定配線 | `_default_effects` の実行 bytes callable を pathname hash へ退行 | 1 | KILLED |
| M07 | gate の位置 | merge があったときだけ検査する | 23 | KILLED |

## この台帳が示す一番重要な事実

**M05 と M06 を殺しているのは、いずれも
`test_real_waiter_process_rejects_merged_tip_with_different_waiter_bytes` の 1 nodeid だけである。**
fake effects を注入する検査は 1 件も反応していない。

この 2 つは「束縛した FD ではなく、そのときの pathname を読み直す」という退行であり、
production の既定配線でしか現れない。注入テストは常に seam 側の値を使うため、
既定配線が壊れても緑のままになる。**実際の待ち手 process を起動する検査だけが検出力を持つ。**

対の正例 `test_real_waiter_process_accepts_merged_tip_with_same_waiter_bytes` は、
比較を反転させる M02 で赤になる (78 node のうちの 1 つ)。受理集合を狭める wave の
過剰拒否検出はこの正例が担う。

## 検出力の外にあるもの (正直な限界)

- **loader が source を読んでから module-level で束縛するまでの窓は、どの変異でも検出できない。**
  Python は source 全体を compile してから最初の top-level 文を実行するため、
  同じ file の中では消せない。外部 bootstrap を入れない限り KILLED にできる形にならない。
- **gate 導入より前に起動した待ち手は契約の被覆外**であり、変異でも受入でも観測できない。
  閉じ方の設計裁定はユーザーへ返した。
- gate 通過後から `run_logged` までの一時差し替えは、同一 Unix user の敵対 race として残る。
  D254 が provenance checker について明記している残余窓と同型で、範囲を広げていない。
