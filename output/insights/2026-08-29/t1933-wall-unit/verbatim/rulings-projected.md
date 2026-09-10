# 必読の既裁定（逐語）

以下は `docs/decisions.md` / `docs/worklog.md` から逐語で取り出したものである。
省略記号で切っていない。子はこの逐語だけを根拠にしてよく、記憶で代用してはならない。

---

## D1260. full K=3 wallを動かさないT-080 process-memo groupingは採らない (2026-08-28)

**決定:** 同じimmutable baseを使うT-080の6 nodeを同一workerへ寄せる配線は、paired full K=3中央値が10%未満の差なら採用しない。正しく配線され変異が全件KILLEDでも、速くなった証拠の代用にしない。

**理由:**
- fixed tip 3走ずつでpre 244.810秒、post 245.707秒、差+0.37%。D357により変化なしである。
- 焦点6 nodeではcache共有が成立したが、その費用はfull wallのcritical pathの下へ隠れた。
- worker duration総和は下がっても、同じ48-core nodeを同じwall占有し、node秒は仕事量代理にできない。

**却下した選択肢:**
- 焦点走のcache hitだけで採用する — full wallへの因果が無い。
- worker duration総和の低下をmachine cost削減と読む — node-hourは変わらない。
- no-effect配線を残したままKやallocatorを追加する — D1019の不採用を再実装し、原因を覆う過剰機構になる。

---

## D357. 受入 wall の主張は反復走の中央値で行う (2026-08-13)

**決定:** 受入全走の所要を根拠にして律速を同定したり改善を主張したりするときは、
**同一 tip・同一条件で 3 走以上を逐次に取り、中央値で述べる。** 1 走同士の差が
10% 未満なら「変化なし」と扱い、改善としても退行としても記録しない。
測定中は自分の他 job を同時に走らせない (dispatch receipt と共有ファイルシステムの双方で干渉する)。

**理由:**
- 同一 tip・逐次・条件交互の sweep で、同一条件の 2 走が 99.30 秒と 117.80 秒 (19% 差) まで開いた。
  受入 wall の観測域は 99.3〜117.8 秒 (±9%) である。
- この幅は、これまで 1 走の値で行ってきた律速同定・改善主張の解像度を上回る。
- 48 worker で観測される node 所要は競合で膨らむ。同一 suite の node 秒合計は
  worker 12 / 24 / 32 / 48 本で 1,542 / 2,261 / 2,828 / 3,344 秒と単調に増える。
  **node 秒は仕事量の代理にならない。**

**却下した選択肢:**
- 1 走のまま報告して「参考値」と注記する — 実際には設計択一の根拠に使われてきたので不十分。
- job Elapse で代用する — job 側の設定・収集時間を含み、pytest wall と別量である。

---

## worklog の「次の一手」 T-1933（逐語、docs/worklog.md）

- [T-1933] **P1**: 現行固定argvでは安全かつ実効的な短縮案を証明できず、T-080 process-memo groupingもpaired K=3で+0.37%の変化なしとして撤去済み。次に再開するなら、fixed-tip full artifactのcritical workerでwallを実際に決める単体処理を先に同定し、その処理自体の安全な短縮だけを検討する。

---

## ユーザーが本 wave に付けた指示（逐語）

受入の壁時間を実際に決めている単体処理を同定する。台帳の現在地は「現行の固定 argv
では安全かつ実効的な短縮案を証明できず、T-080 process-memo grouping も paired K=3 で +0.37%
の変化なしとして撤去済み」であり、D1260
がその不採用を確定している。次の一手は台帳が明示している — fixed-tip の full artifact の
critical worker で wall
を実際に決める単体処理を先に同定し、その処理自体の安全な短縮だけを検討する。この wave
では同定までを成果物とし、短縮案の実装は同定結果が具体的な処理を 1
つ指し示した場合にだけ、その処理に閉じて行う。焦点走の速さを full wall
への因果の代用にしないこと (D1260 の却下理由がそのまま当てはまる)。worker duration
の総和低下を machine cost 削減と読まない。受入 receipt の argv は完全一致で pin
されているので、テストを絞る形の短縮案は land できない。既着地の branch
worktree-dev-wave-t1933-reconciliation / -acceptance-longest-node /
worktree-dev-wave-acceptance-fastest は残骸なので取り込まない。
