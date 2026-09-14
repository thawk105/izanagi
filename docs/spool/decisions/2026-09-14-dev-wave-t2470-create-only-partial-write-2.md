---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t2470-create-only-partial-write
seq: 2
---

## {{D:create-only-discard-only-own-untouched-file}}. create-only writer の失敗時撤去は「自分が作り、誰も触っていない file」に限る

**決定:** 試行台帳の起点と分類受領証を書く共有 create-only writer は、`O_EXCL` で作成に成功した後の失敗経路
でだけ file を撤去する。撤去の直前に (1) この呼び出しが書いた総 bytes 数と `os.fstat(fd).st_size` の一致、
(2) 名前が指す `(st_dev, st_ino)` と作成した fd のそれの一致、の両方を確かめ、どちらかが崩れていれば撤去せず
元の失敗をそのまま送出する。`FileExistsError` の経路は撤去処理の外に置き、既存の完成物へ到達しないことを
構造で担保する。

**理由:**
- 無条件に撤去すると、別 process が正当に追記した台帳ごと消える。台帳への追記は同じ file への `flock` を
  取るが、起点を書く側は lock を取らない。履歴 append-only 検査も、canonical path がどの commit にも
  無ければ拒否せず `None` を返す。したがって起点を書き終えてから `fsync` が失敗するまでの窓で、別 process の
  追記が正当に成立しうる。無条件撤去はその記録を消し、現行より悪い状態を作る。
- 真の部分書き込みには追記者が付かない。台帳 parser は末尾改行を要求し、起点も受領証も canonical JSON
  1 行 + 改行の単一行なので、途中で切れた bytes は必ず framing 検査で落ちる。撤去してよいのはこの状態である。
- fd と inode で条件を書くと、「撤去してよいのはこの呼び出しが作成した file だけ」という不変条件を
  そのまま検査でき、所有 flag のような別状態を持ち込まずに済む。
- 正例・負例を同じ commit へ置ける。失敗注入で撤去と再試行成功を示し、別 fd の追記と同名の別 inode を
  消さないことを示す fails-closed なテストが恒久の検出器になる。

**却下した選択肢:**
- 無条件に撤去する — 上記のとおり、追記済みの台帳を消して現行より悪化する。
- writer へ `flock` を足して窓ごと閉じる — 残る窓は照合と `unlink` の隣接 2 syscall の間だけであり、
  追記側はその手前に全 ref の履歴走査を挟む。D205 (プロトタイプであり production 級の堅牢性は目標に
  しない) に照らし、新しい lock 機構は足さない。**この残余窓は閉じていないと明記する。**
- 部分書き込みのときだけ撤去し `fsync` 失敗では残す — 撤去条件は単純になるが、`fsync` 失敗でも path が
  塞がったままになり、直すべき欠陥の半分が残る。
- staging + hard-link publish へ作り替える — 保守 tool 側の activation record 発行がこの形を採るが、
  本件の最小差分を超える。
- 同型の別 writer へ横展開する — 族一般化には独立 2 例が要る。本件は 1 例である。
