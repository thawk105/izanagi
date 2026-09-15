---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2586-itt-trace-seed-contract
seq: 2
---

## 再発

### F386

- **再発: 2026-09-16** — 閉包の上限を「依頼文の編集面ヒント」ではなく
  **「子が返した所見の列挙」**に置いた形で再発した。[T-2586] の親は、投入経路の検査を締めたとき
  赤になる既存 test の集合を、段 2 プランと段 3 の 2 レンズが挙げた 2 件に自分の実測 1 件を
  足して 3 件と裁定した。3 件は正しかったが**全数ではなかった**。4 件目
  (`test_backoff_trace_contract_accepts_only_four_exact_cell_literals`) は、実装子が
  「期待値のほうが誤りだと判断したときは実装を変えず報告して止まれ」という指示に従って
  停止報告を返したことで初めて出た。子 2 体が metadata だけを締める前提で列挙していたため、
  親が裁定で投入経路も締める方向へ変えた時点で、その列挙は閉包として無効になっていた。
  親はそこで閉包を取り直さず、無効になった列挙へ足し算した。
  是正は裁定の正誤表で、`_validate_backoff_trace_contract` と `_artifact_contract_metadata` の
  test file 内**全 20 呼び出し点**を表にして全数を出し、そこから影響 4 件を導いたこと。
  段 6 の敵対レビュー 2 本と焦点再レビューが独立に 5 件目の不在を確認した。
  **裁定で層を変えたら、前段の列挙は閉包でなくなる。** 権威 (呼び出し点の全列挙) から取り直す。

### F376

- **再発: 2026-09-16** — 今度は**検索結果の側**で再発した。F376 の根本原因は
  「切り取られた出力を不在・網羅の根拠にしない」規律を検索結果には適用していたが
  テストの失敗出力には適用していなかった、というものだった。[T-2586] の親はその逆をやった。
  段 1 の pin 閉包検査で `git grep -n "t2187_adaptive_const_probe" | grep -v <自 test> | head -40`
  を実行し、**自分で `head -40` を付けて切った出力**を閉包の全件として扱った。表示された 40 行は
  `acceptance_duration_ledger.json` の node 行が大半を占め、行番号 pin を持つ
  `orchestrator/tests/test_ccbench_spawn_sites.py` は切った側にあった。
  結果、`_DEFERRED_GATE_MEMBERS` が pin する build sink 2 件の行番号が実装の +31 行で
  ずれ、受入全走が決定的な赤 4 件 (cross-product 28 triple 分) を 2 回とも出した。
  是正は `git grep -l` で全件 (185 path) を列挙し直し、行番号を pin しているのが
  この 1 file だけであることを確かめたうえで anchor を再固定したこと。
  **出力を切る `head` は自分で付けても truncation である。** 閉包を数えるときは
  件数を先に出すか `-l` で path だけを全件出す。
