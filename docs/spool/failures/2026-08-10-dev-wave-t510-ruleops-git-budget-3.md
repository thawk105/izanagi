---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t510-ruleops-git-budget
seq: 3
---

## 新規

### {{F:parametrize-id-breaks-node-extraction}}. parametrize の自動 id が変異 harness の failed node 抽出を壊した [手順漏れ]

- 事象: 変異 matrix の 1 走目が M09 で
  `rc=1 だが canonical stdout から failed node を確実に抽出できないため停止` となり、
  16 変異中 9 変異を消化した時点で matrix 全体が中断した。
- 根本原因: 新設した `test_git_timeout_detail_identifies_production_mode` の
  `@pytest.mark.parametrize` に明示 `ids=` が無く、pytest が 2 番目の要素
  (timeout detail の文字列全文) から node id を自動生成していた。生成された id は
  `[log-receipt-range-git log timeout (mode=log-receipt-range, budget=21.295s, units=37)]`
  のように空白・括弧・`=`・`,` を含み、F71 の failed node 抽出規則を壊す。
  parametrize の値に人間可読な文を置くと id へ漏れるという結合を、テスト作成時に見ていなかった。
- 恒久対応: `tools/mutation_harness.py` の failed node 抽出が PARSE_ERROR で fail-closed 停止する
  既存検査。宣言ではなく実際にこの走行を止めた機構である。当該 parametrize には
  短い安定 label の `ids=` を与えた。
- 再発検知: 同 harness の PARSE_ERROR。node id を値から自動生成するテストを新設した wave では、
  変異 matrix が緑にならないことで顕在化する。

## 再発

### F1

- **再発: 2026-08-10** ([T-510] wave の段 1 brief)。律速の同定で一次資料に当たらず、
  worklog の裁定要約にあった逐語「`ruleops: git-timeout: git log timeout`」だけを根拠に
  「観測された赤 3 件はすべて `git log` であり、律速は full-history pickaxe である」と結論した。
  本台帳の当該エントリを読めば、[T-639] は `git cat-file timeout`、[T-648] の
  `git log timeout` は `inventory` 経路であって `build_inventory` は `_pickaxe` を呼ばない、と
  一次資料に書かれていた。**段 3 の敵対レンズ 2 本が独立にこれを refuted し**、親が本台帳と
  実測で確認して brief の中心的主張 2 件を撤回した。誤ったまま進んでいれば、定数を実際には
  落ちていない呼び出しの費用特性から導き、落ちた 2 経路を過小予算のまま残すところだった。
  **新しい情報は、F1 が指す「一次資料」に本台帳が含まれることが明示されていなかった点である。**
  既存の恒久対応 (F31 の「裁定要約が指す decision 本文と archive worklog を開く」) は
  decision と worklog を指すが本台帳を指していない。恒久対応は memory
  `primary-source-includes-failures-ledger` を新設して閉じた。`DW-S01` への統合は
  **実測で予算超過** (L1 unique footprint 10656 bytes > 予算 10625 bytes、31 bytes 超過) となり、
  意味等価な縮約先が無いため段 8 の候補としてユーザーへ返す。

### F155

- **再発: 2026-08-10** ([T-510] wave の変異 matrix)。(b) と同一機序で 2 度続けて
  baseline `PARSE_ERROR` / rc=16 になった。直接実行して得た理由は
  `bounded scope の memory.max / memory.oom.group を走行中に attest できないため、
  scope を停止して dispatcher infrastructure failure とします`。
  runner argv に `-rf` と `-k` を足したことで `tools/run_tests.py` が受入形と判定せず、
  計算ノードへ dispatch する代わりに login ノードの bounded local 経路を選んだためである。
  **これは規則の欠落ではなく既存規則の不遵守である** — 恒久対応である memory
  `mutation-runner-dispatch-recipe` は本文に `--force-dispatch` を含む argv を明記していたが、
  親は索引行だけを読んで本文を開かなかった。`--force-dispatch` を明示すると 1 走 2.63 秒 /
  rc=0 になり、matrix は 16/16 KILLED で完走した。
  **新しい情報は、恒久対応が memory 本文にあるとき、索引行に要点が無いと参照されないことである。**
  同 memory の索引行へ `--force-dispatch` を明示する更新を行った。
