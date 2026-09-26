---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-23
wave: dev-wave-t2865-silo-small-compare
seq: 2
---

## {{D:silo-policy-known-best-compare}}. silo-function-policy 軸の既知最良との小比較を、同 job に置いた参照 3 本 (静的 10 µs を元の適用方法で・B0-L-W0・stock) との比で 1 回とる — 既知最良は静的 10 µs で、固定 16 点のうち 3 点が 6〜7% 上回った

**決定:** D2235 項 7 (択 (b)) の小比較を、段階 D (D2234) と同じ固定 16 点・8 job・計測構成で実装・実測した。記録の正本は `output/insights/2026-09-23/t2865-silo-policy-known-best-compare/README.md`、段 4・段 6 の裁定の逐語は同 dir の `verbatim/`。

1. **参照:** 各 job に stock (`BACK_OFF=1`)・`B0-L-W0` (`BACK_OFF=0`)・fixed10 を置く。fixed10 は「元の適用方法」= CCBench の stock 木に `patches/silo-backoff-fixed.patch` を当て、`BACK_OFF=1, BACKOFF_FIXED=10` + `locks._BASE` で build する (関数方策の骨格は当てない、D2160 と同じ形)。10 µs は write-heavy の既存最良 (known_axes_freeze・A-2 正式認証・D2160・未知条件転移の R2、いずれも旧 pin) で、本走が現 pin での再評価になる。patch 未適用で flag だけ渡すと無言で適応 backoff に落ちうるので、trace1・trace0 の両 build の owner TU の compile command で `-DBACKOFF_FIXED=10` と `-DBACK_OFF=1` がちょうど 1 個ずつあることを検査し、不成立なら verify・bench へ進まない。
2. **比:** IR 点ごとに、点・同 job の abort0・参照 3 本がすべて適格 (両 verify certified・trace0 clean・5 rep 有効・前後の source evidence が非空で一致) で high-abort でないときだけ、5 rep 中央値 ÷ 参照 3 本の中央値の最大 (最良参照比) を出す。どれか欠ければ null (負けに数えない)。参照ごとの比も別掲する。3% 超は未較正の探索的な目印。
3. **順序と再測:** job 内の 6 方策は job 番号 mod 6 で巡回する。再測はしない (D2235 の「1 回」、ユーザーの計算承認も再測なし)。
4. **firewall:** 比較の出力 (点 ID・比・順位) は insight と `compare-aggregate.json` だけに置き、投影 JSON を作らない。後段へ渡すものは D2234 の `projection.json` のまま。
5. **結果:** 既知最良は全 8 job で fixed10 (同 job 中央値 3,944〜4,011 千 txn/s、`B0-L-W0` 2,374〜2,533、stock 1,343〜1,378)。IR 16 点はすべて適格で、最良参照比は 0.836〜1.069。3% 線を越えたのは 3 点 (1.062〜1.069) で、いずれも 5 rep の最小が同 job の fixed10 の最大を上回った。3 点とも lock 競合への応答を「試行 4 回まで再試行」にする水準を持つ。同じ 3 点は段階 D (別 job、abort0 比) でも上位 3 点で、throughput は 1% 以内で一致した。計算は計測 8 job の Elapse 合計 6,180 秒 (ユーザー承認の上限 4.6 node 時間の内側)。

**理由:**
- 1: D2234 の限定 (abort0 比の 3% 線は易しい問い) に答えるには、既知最良を同 job に置いた比が要る。段階 D の参照は stock と `B0-L-W0` が 1 job ずつで、静的 backoff は無かった。
- 2: 参照が欠けた job で残りの参照だけの最大を取ると比が過大になる (段 3 相談 A)。3% は段階 D と同じ暫定床で、比の大小を確証とは扱わない (相談 B)。
- 3: job 7 が基本列に戻る巡回漏れは段 6 レビューで見つけて直した。
- 4: 手順書 §3-D の firewall。

**却下した選択肢:**
- 段階 D の結果 JSON の参照値を流用する — 参照が 2 job にしか無く、fixed10 が無い。
- 超過点の別 job 再測を同じ wave で行う — D2235 の「1 回」とユーザーの計算承認の範囲外。段階 E の判断と併せてユーザーへ返す。
- 新しい投入 script・job body — 投入許可台帳に未登録 (D2234 と同じ理由)。

**限定:** 固定テンプレートの部分空間 16 点・未調整・1 回の結果で、統計的な優位 (多重選択の補正なし)・全 IR や LLM×C++ の空間・別 workload への転移・fixed10 以外の静的値 (現 pin で掃いていない) との比較については何も言わない。診断 build は NON_ADMISSIBLE で certified 候補とは称さない (D2226 項 5)。
