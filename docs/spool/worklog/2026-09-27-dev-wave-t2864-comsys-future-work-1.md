---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: dev-wave-t2864-comsys-future-work
seq: 1
title: [T-2864] ComSys 原稿の改訂 4 — 7 節と限界節を一次資料と照合し直し、(b) を LLM の方策 1 件の certified (比 2.80 は 1 回の観測で主張にしない)、(c) と限界節を B-5 本走の判定不能での閉鎖と v2 の見送りへ、限界節のスコープを MOCC の疎通後の状態へ直した。15 頁のまま (docs のみ、branch dev-wave-t2864-comsys-future-work)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、2026-09-27 19:16 JST): [T-2864] の (2)。依頼が挙げた食い違い 2 点 ((b) = 段階 F、D2270。(c) = B-5 v2 の見送り、D2259) に加え、段 1 の照合で
  限界節「スコープ」の「本稿の時点では非 Silo の性能比較は 0 件」「MoCC と TicToc は較正の記録各 2 件」が MOCC の疎通 (D2261) と較正 (D2248) で古くなっていたので同じ改訂で直した。
  記録 = `output/insights/2026-09-22/comsys2026-manuscript/README.md` §12。
- 依頼の 1 分前 (19:15 JST) に、ユーザーは /rulings で「comsysのことは一旦忘れてください、うざいです。」と述べている (履歴で時刻を照合)。後から出た本依頼はユーザー自身が ComSys を持ち出したものなので進めた。
  報告では発表申込・送信の催促をしていない。
- 親の裁定: 関数方策の軸の機械偵察で 3 点が静的 10 µs を超えた結果 (D2240・D2250) は、依頼が食い違いの是正で、LLM の候補でない診断 build の探索的な超過を足すと新しい性能の記述になるので本文に足さず、
  README §12.2 に残した。載せるかはユーザーの判断。MOCC の read-heavy の G2 6 件は D2261 項 6 に従い書かない。
- `EnterWorktree(name)` が「Could not read the repository git config to neutralize filter drivers」で失敗したので、`git worktree add -b … main` を手で行い `EnterWorktree(path)` で入った (既知の回避策)。
- 段 6 の read-only レビュー: (段 6 の後に書く)

## 次の一手差分

### 更新

- [T-2864] **P2・一部裁定済み (D2227 項 3〜6、D2235 項 2・3、D2262) → 発表申込・原稿送信 (人間手番)**:
  ComSys 原稿 (`output/insights/2026-09-22/comsys2026-manuscript/manuscript.tex`) の残り。頁数 15 頁のまま (D2227 項 4)、ADRS の判定 (D2227 項 5) と 4.7 節ほかの 4 巡目の反映は
  改訂 2 で、参考文献の採録版照合 (README §3.4 の 3 件) と 7 節 (a)(c) の一次資料との照合は改訂 3 で、7 節 (b)(c) と限界節の再照合 (段階 F、B-5 v2 の見送り、MOCC の疎通) は改訂 4 で済んだ
  (同 dir `README.md` §10・§11・§12)。(1) 著者・所属 (`\affiliate` / `\author` の差し込み欄、`noauthor` 指定の解除と再組版・頁数の確認を含む) はユーザーが自分で記入する。AI へは渡さず、
  AI は推定で埋めず、/rulings の索引に載せない (D2262)。(2) 関数方策の軸の機械偵察の 3 点 (D2240・D2250) を本文に載せるかはユーザーの判断で、改訂 4 では載せていない (README §12.2)。
  (3) 発表申込 10/16・原稿締切 10/30 の送信は人間手番 (収載は送信の承認ではない)。一次資料 同 dir の `README.md` §3.4・§6・§10・§11・§12。
  base: 15793350a60998950ad4cc7700ad3231073d0ffec7cee1ba1c64f549ae6a81c3
