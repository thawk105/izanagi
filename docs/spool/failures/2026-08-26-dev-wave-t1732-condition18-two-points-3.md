---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1732-condition18-two-points
seq: 3
---

## 新規

### {{F:probe-run-serialization-parent-side}}. 親が校正用の走行を背景投入したまま次の走行を投げ、同一 worktree の並行 dispatch で orphan hold を踏んだ [手順漏れ]

- 事象: 段 6 の timeout 校正のため単一 node の走行 2 本を背景で連鎖投入し、それが計算ノードで
  実行中に焦点走 (file 全体) を投入した。後発の投入は
  `IZANAGI_DISPATCH_OUTCOME_V1 {"child_started":false,"kind":"infra","reason":"orphan-hold"}` で
  子を起動せずに終わり、焦点走の結果が 1 回失われた。
- 根本原因: `DW-O26` の「焦点走の分割投入は直列にする。同一 worktree の並行 dispatch は
  orphan hold で rc=16 になる」は**焦点走どうし**の話として読まれやすい。実際には親が校正・計測目的で
  投げる単発 node の走行も同じ dispatch 経路を使うため、種別が違っても直列化の対象である。
  親には背景投入した dispatch の在否を投入直前に確かめる習慣が無かった。
- 恒久対応: `DW-O26` が定める直列化の対象を、焦点走に限らず**同一 worktree からの dispatch 全種**と
  読む。投入直前に `qstat` と `output/pegasus-dispatch/orphan-hold.json` の不在を親が確認する。
  機械側の実体は既存の fail-closed 検査 (hold 在中は scheduler command を起動しない) であり、
  欠けていたのは親側の運用規律である。
- 再発検知: 後発投入が `reason=orphan-hold` で子を起動せずに戻る。静かに壊れることはない。
- 波及: 本件の hold は先行走行の自然終了で撤去された。手動削除も `qdel` もしていない
  (`qdel` は F47 の submission-disabled を武装させる)。

### {{F:archive-name-entry-number-collides-with-mmdd}}. 4 桁 entry 番号が MMDD と衝突し、rotation した archive が番号付きと認識されず land が塞がる [恒真ゲート]

- 事象: entry 1001 を rotation する fold が `docs/archive/worklog-phase3-0826-1001.md` を作ったが、
  生成後の canonical 検証が `carry 参照先 entry (1001) が全域番号 universe に実在しない — 宙吊り参照`
  を 22 件出して停止した (land rc=26、main は 1 bit も変わらず)。
  現行 worklog には entry 1001 を指す carry が 821 件ある。
- 根本原因: **D445 の判別鍵そのものに穴がある。** D445 は日付 token と entry 番号 token の
  判別鍵を「先頭ゼロの有無」と定め、「先頭ゼロを鍵にすると、4 桁の entry 番号 (1000 以上) を
  MMDD と取り違えない」と根拠に書いている。**この根拠は 10〜12 月について成り立たない** —
  `1001` (10 月 01 日) の月部分に先頭ゼロは無い。実装の
  `ARCHIVE_MMDD_TOKEN_RE = (?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])` は月 01〜12 を受け、
  `ARCHIVE_ENTRY_TOKEN_RE = [1-9][0-9]*` も同じ token に一致するため両義になる。
  `_archive_filename_entry_range` は日付範囲の枝を先に判定するので unnumbered が勝つ。
  実装は D445 が定めた位置文法を忠実に写しており、**実装のバグではなく裁定の穴**である。
  同関数を直接呼んで再現した:
  `...-0826-0999.md`→numbered、`...-0826-1000.md`→numbered (10/00 は無効な日)、
  `...-0826-1001.md`→**unnumbered**、`...-0826-1300.md`→numbered (13 月は無効)。
- 影響範囲 (実測): entry 1001-1031 / 1101-1131 / 1201-1231 の計 93 件。
  プロジェクトは 1001 に達したところで、この区間の入口に居る。
  **rotation を起こす wave はどれも land できない。**
- 恒久対応: 未定 (D445 の改訂を伴う設計択一のためユーザー裁定へ返す)。候補は
  (a) numbered 形に曖昧でない marker を入れる (D445 の位置文法を保ったまま鍵を明示にする)、
  (b) 両義な token を持つ名前を malformed として赤にし、生成側に曖昧な名前を作らせない、
  (c) file 名でなく内容の H2 見出しから entry 番号を採る。
  D445 は allowlist 案を「fail-open の方向に既定値がある」として却下済みなので、その線は採らない。
  いずれも受理集合を変えるため独立審査が要る。
- 再発検知: `spool_fold.py` の生成後 canonical 検証が宙吊り参照で停止し、land が rc=26 になる。
  **`--dry-run` はこの検証を回さないため手前で出ない** — 本件も dry-run は rc=0 だった。
- 波及: 本 wave は受入まで完全緑 (`verdict=child-green`、赤ゼロ) で、land だけが塞がっている。

## 再発

### F24

- **再発: 2026-08-26** — `tools/dev_wave_wait.py producer` の待ち手が rc=0 で偽完了する形を
  **同一 wave で 3 回**観測した (段 6 焦点再レビュー、変異 probe、焦点走の 2 回目)。いずれも
  `.done` は不在で子は生存しており、恒久対応 (`.done` の実在で判定し、待ち手の rc も通知も信じない)
  がそのまま効いて実害はゼロだった。**本 wave の追加事実は生存判定の側にある** —
  道具名だけの `pgrep -f "mutation_worktree.py"` は**並行 wave の子を自分の子と誤認する**。
  実際に別 wave (`dev-wave-t1858`) の変異走行を自分のものと数え、本走の投入を無用に待った。
  `DW-M05` が要求する worktree path での一意化は、変異中の生存確認だけでなく
  **待ち直しのたびの生存判定にも適用する**。
