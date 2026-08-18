---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: dev-wave-t1132-stage2-luna
seq: 2
---

## {{D:dev-wave-all-luna-max}}. dev-wave の codex を全段 `gpt-5.6-luna` @ `reasoning=max` にする — 根拠は費用の運用選好であって品質同等性の証拠ではない

**決定:** dev-wave が起動する codex の model を、全段・全 lane 単一の `gpt-5.6-luna` にする。
`reasoning` は段 2 / 段 3 が従来どおり `max`、段 5 (author) と段 6 (review / fix / focus) を
`high` から `max` へ上げ、**luna を使う段はすべて `max`** に揃える。
lane 名 `sol` / `luna` は残すが、model を指さないレンズ識別子になる。

**この採用の根拠はユーザー裁定であり、品質同等性の証拠ではない。**
[T-1146] の現行裁定 (c) が「体感や速度を理由に切り替えたくなった場合は、証拠に基づく判断ではなく
**運用上の選好**として (b) を明示指示し、その旨を記録する道を残す」と定めており、本決定はその道を
通ったものである。D423 が「supersede はユーザー裁定にだけ属する」とした権限を、ユーザー自身が行使した。

**理由 (費用):**
- `gpt-5.6-luna` のレートは `gpt-5.6-sol` の 4% である
  (sol 入力 $5 / 出力 $30 per M、luna 入力 $0.20 / 出力 $1.20 per M。2026-07-30 に luna が 80% 値下げ、
  sol は据え置き)。
- dev-wave の codex 消費のうち sol を使う段が 76.4% を占める
  (receipt 170 本 / 26 wave / CLI reported 35.8M の集計)。
- token 比 luna/sol は同一 wave 内 paired 15 wave で中央値 1.05 倍であり、
  **token の数は減らない。減るのは単価である。**
- `high`→`max` の段は token が約 2.02 倍になる (D207 が観測した比) が、レート差がそれを上回る。
  費用換算の削減は約 70% と見積もる。**wave の所要時間は伸びる。**

**この決定が失うもの (受容した代償):**
- 段 3 の敵対相談 2 レンズと段 6 の敵対レビュー 2 本が同一 model になる。
  レンズは prompt だけで分かれ、model 由来の系統的盲点は共通化する。
  D241 が「sol にしか出せない所見を落とす」として不採用にした「全 luna」の形そのものである。
- D266 の認証済み A/B が段 6 focused review について選んだ `high` を `max` へ上書きする。
  effort を上げる向きなので検出力は下がらないが、認証済みの値を証拠なしで動かしている。

**機械化した内容:**
- model 権威行の文法を v1 (旧) / v2 (新) の 2 本にし、**live snapshot は v2 だけを受理する**。
  過去 commit 指定では v1 も受理する — 過去 receipt の再構成監査を壊さないため。
  v1 を live 起動へ使える抜け道は作っていない。
- `AuthoritySnapshot.as_dict()` と集約 digest は 1 bit も変えていない。既存 receipt の照合は不変。
- 段 6 の `reasoning` pin は削除せず `high` から `max` へ張り替えた。
  値ちょうど一致の要求と decoy 4 種 (HTML comment / fence / blockquote / 併記) の拒否は減らしていない。

**却下した選択肢:**
- **段 2 だけ luna にする** — 段 2 は codex 消費の 16.0% しかなく、レート差を最大に見積もっても
  削減は 15.3% で目標に届かない。
- **model だけ替えて effort は据え置く** — ユーザーが「luna は愚かだから luna を使う段は max
  でなければ受け入れない」と裁定した。
- **権威行の sol / luna 位置を入れ替える flip trick** — D423 が挙げた 145 箇所の
  `--lane` 呼び出しの意味が反転する footgun があり、費用も減らない。
- **`reasoning` pin を削除して自由化する** — pin の finding 文が「変更には採用裁定と pin の同時更新が
  必要」と手順を定めており、削除は手順ではない。張り替えが正しい対処である。

**rollback:** 権威行 1 行と `workers.md` の 3 語を戻し、`check_docs.py` の pin literal を戻せば
旧挙動へ戻る。v1 文法は残っているため過去 receipt の監査経路は影響を受けない。
