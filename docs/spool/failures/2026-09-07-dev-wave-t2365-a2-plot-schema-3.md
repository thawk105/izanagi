---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2365-a2-plot-schema
seq: 3
---

## 新規

### {{F:background-waiter-false-completion}}. 背景待ち手が条件未成立のまま「完了」を返し、未完了を完了と誤認しうる状態が続いた [捏造/幻覚] [手順漏れ]

- 事象: 背景 job の `until [ -f <done> ]` ループと Monitor が、`.done` も台帳 file も存在しない
  状態で「完了」「rc=0」「n=7」等の通知を返す事象が、1 セッション中に 10 回以上起きた。
  producer は `ps` で生存が確認できた。通知本文だけで判定していれば、変異走の途中結果を
  完走と読み、受入と land へ進んでいた。
- 根本原因: 待ち手の通知は producer の実際の終了と束縛されていない。通知本文は待ち手 script の
  出力ではなく、別経路で組み立てられうる。**通知は「見に行け」という合図であって、状態の証拠ではない。**
- 恒久対応: 完了判定を通知本文から切り離し、**成果物の実在で行う** — producer 自身が書く `.done`
  file の存在と中身、および成果物 (台帳 JSON・図・receipt) の実在を毎回 `ls` / `cat` で確かめる。
  本 wave はこの規律で全判定を行い、10 件以上の誤通知をすべて弾いた。
- 再発検知: 「完了通知は本文ごと誤りうる」を既存 memory が持つ。待ち手の rc・grep・通知の
  いずれも判定にしない契約は `DW-C00` が既に定めており、本エントリはその契約が実測で
  必要だったことの記録である。

## 再発

### F205

- **再発: 2026-09-07** — A-2 の condition-gate 受領証の公開が、同じ `renameat2(RENAME_NOREPLACE)`
  の Lustre EINVAL で決定的に失敗した。attempt `t2364-20260907a` は 2 workload とも約 50 秒で
  `driver_rc=2` で終わり、bench に入らなかった。**F205 の恒久対応 (`os.link` + `unlink` による
  create-only publish) は directory 公開側にしか適用されておらず、T-2337 が足した file 用の
  新しい writer `_atomic_write_bytes_noreplace` が退避なしで同じ穴を再導入していた。**
  単体テストが緑だったのも F205 と同じ理由で、pytest の一時領域が同フラグを実装する FS だった。
  親が同じ Lustre 上で `ln` の成功と既存名での EEXIST を実測し、file 公開へ EINVAL 限定の
  hard link 退避を実装した。退避を消す変異と「既存を置換する rename」へ変える変異の両方が
  KILLED になることを変異試験で確かめた。
  **同日、A-1 の wave も独立に同じ型を踏んでおり、`DW-G03` の「独立 2 件」が揃った。**
  族としての一般化は別タスクへ送る。

### F581

- **再発: 2026-09-07** — 敵対レビュー 1 巡目が、足された検査 4 件について「外しても既存 test が
  1 件も赤にならない」ことを名指しした。とくに新版 profile の正例が全部 test 用の kwargs seam を
  通っており、repo 所有 pin 表を迂回する退行を検出できない形だった。fix で 4 件とも閉じ、
  それぞれを殺す最小の変異 10 件を実際に当てて赤を確認した。さらに本走の probe 段で、
  `source_binding_status` の検査が 2 層あり上位層が下位層を隠している構造が見つかった
  (片層だけの変異は SURVIVED し、両層同時変異で KILLED)。**この mask は静的レビューでは
  出ておらず、変異試験だけが明らかにした。**
