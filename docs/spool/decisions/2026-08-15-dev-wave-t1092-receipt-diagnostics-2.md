---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-15
wave: dev-wave-t1092-receipt-diagnostics
seq: 2
---

## {{D:acceptance-receipt-failure-diagnostics}}. acceptance-receipt 段の失敗は reason と判定観測値を必ず出す

**決定:** `tools/dev_wave_wait.py` の `acceptance-receipt` 段の各失敗地点は、
互いに一意な `receipt-*` の reason と、**その判定に実際に使った観測値**を
`_attestation_detail` の `{"reason": ..., "observed": ...}` 形式で出す。
出力は stderr の既存 `error:` 行へ `detail=` を足し、**加えて** stdout へ別接頭辞の 1 行を出す。
判定条件・分岐・rc・stage 名・受理集合は変えない。失敗時の `raise` へ引数を足すだけとする。

載せてよいのは判定に使った値だけとする。短絡で未評価だった条件は `null` を明示し、
再評価して観測値を作らない。例外は**型名と整数 errno のみ**とし、例外メッセージ・`repr`・
絶対 path・環境変数値・stdout 原像の hash は載せない。自由文字列は 256 bytes、
serialized detail 全体は 2048 bytes で切り詰める。診断生成は例外を出さない構造にし、
rc と stage を置換しない。

cleanup の失敗が一次 outcome を置換するときは、**返す outcome の選択を変えずに**
一次側の stage と detail を入れ子で保存する。

テスト側の期待 reason / failure_kind は **production の定数を参照せず literal 文字列**で書く。
両側が同じ定数を共有すると、reason の取り違えが同時に動いて緑のまま通るためである。

**理由:**
- 受入全走が完全に緑でも `stage=acceptance-receipt rc=70` だけが出て land できない事故で、
  git 履歴・全 log・source を持つ親が約 14 の失敗地点のどれかを特定できなかった。
  1 走 300 秒と受入 lease 1 枠が理由不明で捨てられ、影響は全 wave に及ぶ。
- 診断の仕組み (`_Outcome.detail` / `_attestation_detail` / `_print_outcome`) は既存で、
  隣の段は使っていた。欠けていたのはこの段が値を渡していないことだけだった。
- 判定に使っていない値まで載せると、短絡で未評価だった式を評価することになり、
  追加評価の例外が stage を変えうる。観測値は判定の写像に限る。
- 診断を足す変更は「緩める」方向だけでなく「過剰に拒否する」方向にも壊れる。
  受入証を書き終えた後の失敗は成功を覆してはならない。

**却下した選択肢:**
- stderr だけに出す — 確定裁定の文言は stdout であり、`2>&1` は特定 launcher の
  リダイレクトであって stderr を stdout 契約に変えない。親が読み替えてはならない。
- 失敗時に receipt を書いて診断を載せる — publish は成功経路にしかなく、新機構になる。
- 失敗後に全条件を再評価して観測値を揃える — 短絡で未評価だった値を「判定に使った値」と
  偽ることになり、追加評価の例外が rc と stage を置換する。
- 入れ子保存で一次 detail の `observed` を落として stage と reason だけ残す —
  出力は減るが、この決定が残そうとしている原因値そのものを失う。
