---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t1027-acceptance-reds-checker
seq: 2
---

## {{D:collection-authority-is-the-dispatch-receipt}}. dispatch 経由の collection は relay ではなく receipt を権威にする

**決定:** `tools/check_acceptance_reds.py` が pytest の collection 集合を得るとき、
dispatch が親へ流した stdout を権威にしない。relay 行が告知する dispatch receipt の
`scheduler_logs.stdout` を読み、`omitted_bytes == 0` かつ `size` と tail の byte 長が
一致する場合だけ権威として採用する。加えて pytest の collection footer が申告する
selected 件数と、path に一致する unique nodeid 件数の一致を必須にする。
いずれも証明できなければ rc=2 で停止する。

**理由:**
- dispatch は child rc=0 の走行で子 stdout を末尾 4 KiB へ切り詰める。
  実測では 12,098 bytes の collect 出力が `omitted_bytes=8002` となり、
  114 件中およそ 40 件しか親へ届かず、先頭 payload 行は途中で切れた nodeid 片だった。
- 切り詰められた部分集合を完全な collection として扱うと、exact selector 解決が
  「見つからない」で止まるだけでなく、**残った部分集合の中に prefix となる別 nodeid が
  あれば誤った node を選びうる**。件数一致の gate はこの経路を構造的に閉じる。
- 完全な出力は disk 上の receipt に残っており、追加の再実行なしに回収できる。

**却下した選択肢:**
- relay の `omitted_bytes` を見て rc=2 にするだけ — 誤診は直るが、
  出力の大きい file では永久に判定できず tool が実運用に到達しない。
- exact selector だけを再 collect する — group suffix と literal の区別に推測が戻り、
  最長 exact match の契約を弱める。長い parameter 集合では再び上限を超える。
- relay 上限の引き上げ — producer 側に調整弁が存在しない。

## {{D:unverifiable-input-must-not-yield-non-attributable}}. 判定不能な入力から「非帰属」を出さない

**決定:** 受入赤の帰属判定において、collection の完全性・selector の一意性・単独 rerun の
帰結のいずれかを証明できない入力からは、`status=non-attributable-only` または rc=0 を
出してはならない。証明できない場合は rc=2 で停止する。rc=1 (帰属) 側へ倒すことは
安全側であり禁止しない。単独 rerun の rc=1 も、その selector が実際に FAILED/ERROR した
ことを rerun 自身の出力で裏取りできた場合だけ非帰属の根拠にする。

**理由:**
- この tool の rc=0 は下流で「取り込んでよい」と読まれる。危険な方向は rc=0 側であって
  rc=1 側ではない。**当初 brief はこの向きを逆に書いており、敵対レンズが blocker として
  是正した。** fail-closed 系の不変条件は、禁止する側の rc / status を明示して書く必要がある。
- rc=1 は「その走行が失敗した」ことしか意味しない。session-level error や
  collection error でも rc=1 になるため、rc だけで「main でも赤」と結論すると
  受理集合が誤って広がる。

**却下した選択肢:**
- 「match しなかったから非帰属」— 判定不能を安全側の結論に読み替える典型で、
  正しさゲートを後付けにする (規律 3) のと同じ誤り。
