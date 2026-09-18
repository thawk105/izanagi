---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2772-mocc-mutation-proof-wave1
seq: 2
---

## {{D:mocc-proof-wave1-integrity-scope}}. mocc 実証 wave 1 の proof JSON は、別 integrity 異常の clean を受入必須走のうち certified 型 16 走と 1 thread 負例 7 走にだけ要求し、4 thread 負例と観測のみの走は完走だけを要求する

**決定:** `orchestrator/campaign/s3_mocc_mutation_proof.py` の 32 check は D2134 項 5 のとおり受入必須 25 走だけに対応させ、
verifier の別 integrity 異常 10 項目 (orphan_reads / version_dups / dup_txids / genesis_commits / missing_txids / write_version_mismatch /
malformed_keys / framing_violations / framing_violation_details / write_intent_violations) の clean を要求するのは、stock-W / stock-U の 12 走と
hot-update-unlock の cold / default 4 走 (いずれも certified を要求するので含意) と、1 thread の受入必須負例 7 走 (lockskip cold / default t1、
perm-erase hot / cold t1、early-unlock hot / cold t1、hot-update-unlock hot t1) だけとする。lockskip cold / default の 4 thread 2 走 (受入必須) は
X>0・P=0・certified=false・txns / write>0 (cycle>0 なら non-serializable、0 なら indeterminate) だけを要求し、観測のみ 11 走は
`matrix_runs_complete_and_terminated` (存在・予定 cell との一致・実 argv・benchmark の終了・rc=0・timeout なし・verifier の終了・rc∈{0,1,3}・raw record 実在)
だけを要求する。各走の `certified` は verifier の値をそのまま JSON に残し、実証の `all_pass` で上書きしない。T-2757 の設計 insight §7 の
「別 integrity 異常は区分を問わず赤」は上の形に限定する (hang・欠落は区分を問わず赤のまま)。

**理由:**
- 設計 wave の親 brief (T-2772 の段 1) は「T-2294 の lockskip 4 thread が cycle 3,754 を出したので integrity clean を全走に要求すると恒偽」と
  書いたが、段 3 の 2 レンズがこれを反証した (cycle と integrity は別軸。旧 JSON に version_dups の値は無い)。撤回した。
- しかし lock を故意に欠いた 4 thread の負例では、2 worker が同じ版を読んで同じ maxtid を選び、balanced のまま同じ版を順に publish しうる
  (段 3 レンズ A の具体順序: `cc/mocc/transaction.cc` の 1000・1118〜1132・1195 行)。発生頻度は不確実だが、これは負例の許容挙動であって
  実証の欠陥ではない。全走に clean を要求すると、壊した variant の当然の帰結で実証全体が赤になりうる。
- compute の実測がこれを裏づけた: lockskip cold / default の 4 thread は version_dups 21,954 / 20,668、hot-update-unlock hot 4 thread は 67,777、
  early-unlock hot 4 thread は 17,866 で、1 thread の負例 7 走・stock 12 走・hot-update cold / default 4 走は 0。全走 clean を要求していれば実証全体が赤だった。
- 逆に 1 thread では重複版が構造的に起きないので、負例 7 走に clean を要求することは「負例が X / P 以外の不変条件を壊していない」ことの実質検査になる。
- 規律 2 は異常 variant の認証・採用を禁じる。実証 JSON の `all_pass` は検出器の実証の合格であって variant の certified ではなく、両者を分けて記録する。

**却下した選択肢:**
- 全 36 走に共通 check `all_runs_other_integrity_clean` を置く (段 2 plan) — 上記の許容挙動で恒偽になりうる。D2134 項 5 (必須走だけを check に対応) とも食い違う。
- 観測のみの 4 thread 負例の integrity を一括免除する (親 brief の P3) — 根拠が誤り (cycle から重複版を推論できない) で、免除範囲も広すぎた。
- version_dups だけを許容し他の integrity 項目は観測走にも要求する (段 3 レンズ A の案) — 観測のみの走に check を置くことになり D2134 項 5 と衝突する。
  raw record は全走で保存するので、必要になれば後続 wave が別 check として足せる。
