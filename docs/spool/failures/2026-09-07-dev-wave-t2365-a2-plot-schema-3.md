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

### {{F:consumer-validates-historical-artifact-with-current-grammar}}. 成果物に保存した当時の policy を、consumer が版選択なしで現行 validator へ渡していた [テスト代表性] [ドリフト]

- 事象: A-2 図生成器が、成果物の埋め込み policy bytes を現行 producer の `load_policy` へ
  版選択なしで渡す設計だった。別 wave が producer の policy 文法へ必須 key を 1 つ足した結果、
  その変更より前に作られた正当な認証成果物が拒否され、焦点走が 35 件赤になった。
  **測定は当時の policy で正しく走り、当時の検証を通っている。** 壊れたのは読み手だけである。
- 根本原因: producer は成果物へ当時の policy bytes を意図的に保存しているのに、
  **consumer がその時点の文法を選ぶ情報を使っていない。** profile 選択は certification /
  manifest の schema 名の組だけで行われ、policy の版は選択に関与しない。
  したがって producer の必須 key・値制約が過去 bytes を満たさなくなる変更ごとに再発する。
- 恒久対応: `(certification bytes の SHA-256, 埋め込み policy bytes の SHA-256)` の組を主 key にした
  repo 所有の列挙を引き、完全一致した entry だけ当時の文法で読む
  ({{D:a2-figure-historical-policy-hash-bound-adapter}})。未知 hash への fallback は設けない。
  version 欄と key 集合は entry 選択後の二次 assertion に留める
  (旧も現行も policy version は同じ `v2` なので識別子にならない)。
- 再発検知: 主 key を「policy hash だけ」に弱める変異が
  `test_historical_rejects_changed_certification_bytes` を赤にすることを実測で確かめた。
  **ただしこの対応は 1 件限定の adapter であり、構造そのものは残る。**
  producer 共通 loader の版管理は本 wave の scope を超えるため裁定パッケージへ返す。

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
