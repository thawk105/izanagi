---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2396-a1-receipt-oslink
seq: 1
title: [T-2396] A-1 受領証の公開を os.link() へ改めた — 機構の差し替えが撤去処理へ受領証削除の経路を開きかけ、段 3 が着地前に捕らえた (コード + テスト + 記録、branch worktree-dev-wave-t2396-a1-receipt-oslink、変異 10/10 KILLED)
---

## 本文

- D1732 (2026-09-07 ユーザー裁定、推奨どおり) の実装。F870 のとおり A-1 pilot の attempt-0002 は
  3 job の qsub がすべて受理された直後に group receipt の公開だけが Lustre で決定的に失敗し、
  **測定値が 1 点も出なかった。**
- 着手前に durable base 直下の scratch directory で裁定の前提を測り直した (2026-09-08 00:35 JST、
  fstype=lustre)。`renameat2(RENAME_NOREPLACE)` は空き先に errno 22 EINVAL、`os.link()` は
  空き先に成功し nlink=2 で staging が残り、既存先に errno 17 EEXIST を返して宛先 bytes は不変。
  **この probe が証明したのはその directory・その時点の 3 操作の結果だけ**であり、
  Lustre 一般の性質としては主張しない。
- 段 3 の敵対相談が着地前に致命的所見を出した。hard link 公開では staging と宛先が同じ inode に
  なるため、rename 時代のままの identity 照合では、公開後に第三者が
  `unlink(staging)` と `rename(destination, staging)` を行うと撤去が受領証の最後の link を消す。
  {{F:hardlink-publish-aliases-staging-and-destination}} と
  {{D:a1-published-receipt-cleanup-contract}} で閉じた。
- 親が refuted と裁定した所見 (実装しない):
  - 宛先確認と unlink の間に残る競走 — 非協調な同 uid writer を前提とし、その writer は受領証を
    直接消せるので file 操作では閉じられない。threat model 自体の裁定へ返す。
  - link 後の最初の fsync 失敗が生の `OSError` で抜ける — `_fsync_directory` は変更前から生の
    `OSError` を投げ、v3 submit の `except PaperStoryError` は捕まえない。偽の failure receipt は
    書かれず、成果物の状態は変更前後で同一。
  - `FileExistsError` 専用 catch が冗長 — create-only 契約を明示し、変異の単一行 target になる。
    防御コードの追加ではない。
  - `_fsync_directory` 内部の実 fsync 消失、波及列挙の精度、duration 台帳の旧名 entry — 本 wave の
    変更面ではない、または実装に影響しない。
- 段 6 の敵対レビューが、実装の弱い点を 3 件出して直させた。同一 inode 移動の負例が
  「どちらかが残っていれば通る」恒真形だったこと、**v3 の completion 公開点を実行するテストが
  repo 全体に 1 本も無かった**こと (`run_complete` を呼ぶ既存 2 本はいずれも v2 policy を通る)、
  公開済み撤去の 2 つの guard を単独で殺せなかったこと。
- 実装の行数増で 2 つの機械検査が赤になった。deferred gate 台帳が pin する行番号 (7146 → 7209) と、
  受入 duration 台帳の被覆 (89.993511% で 90% 下限をわずかに割った)。どちらも実測して追随させた。
  行番号 pin は他 wave も同じ台帳を更新するため、先に local main を取り込んでから実測した。
- 子は 8 本 (plan 1、consult 2、author 1、review 2、fix 2)。model call は合計 296、
  reasoning 出力 token は合計 136,730。全子が `completed` で終了。
- 実装子と fix 子は sandbox から計算ノードへ dispatch できず pytest を 1 度も実走できなかった
  (`qstat -Q` の認証エラーで rc=16)。緑の主張は 1 件も受け取らず、実測はすべて親が行った。
- 受入全走は本記録 commit を基準に投入する。**本エントリに受入結果は含まれない。**

## 次の一手差分

### 完了

- [T-2396] group submission receipt と `complete` の completion receipt の公開を、完成した staging への
  `os.link` へ改めた。materialize の directory 公開は棚卸しの結果そのまま残した。
  正例・負例を同じ commit へ入れ、変異 10/10 KILLED (期待 node 完全一致、baseline PASSED)。
  remaining: none
  base: 9283f673750d0f6ad2d7b60936bdf14ca6164ee25b566abad04521538766a969

### 新規

- {{T:a1-receipt-dir-writer-threat-model}} **P2・新規・ユーザー裁定待ち**: A-1 の durable base 配下で、
  非協調な同 uid writer を正しさ境界に含めるかを裁定する。含めるなら受領証公開・撤去は
  parent descriptor の固定か排他契約が要り、含めないなら現行の「決定的順序だけ閉じる」で足りる。
  現状は後者として実装し、宛先確認と unlink の間の競走は開いたまま明記している。
- {{T:a1-submission-failure-receipt-publish}} **P3・新規**: `receipts/submission-failure.json` も
  staging + no-replace 公開へ揃えるか。D1732 の射程外として本 wave では変えていない。
  千切れた failure receipt が create-only 名を占有すると、失敗した attempt の理由と job status を
  復元できず試行台帳の参照が壊れる。失敗処理中の二次失敗と retry policy の裁定を伴う。
- {{T:a1-exclusive-write-bytes-partial-staging}} **P3・新規**: `_exclusive_write_bytes` は staging を
  作成した後の `write` / `fsync` 失敗で partial staging を残す。本 wave が作った破れではなく
  変更前から同一で、共有 helper なので intent・barrier・qsub stdout 等の全利用者を巻き込む。
- {{T:dev-wave-worker-reasoning-pin-contradiction}} **P3・新規・ユーザー裁定待ち**: dev-wave の
  worker 契約は段 5 実装子と段 6 レビュー・焦点再レビューに `reasoning=xhigh` と書くが、
  `tools/dev_wave_codex.py` は author / review / fix / focus 段で `--reasoning` を rc=2 で拒否する
  (本 wave の段 5 投入が実際に落ちた)。effort は docs 権威から導出されるので実効値は変わらないが、
  記述どおりに投げると必ず失敗する。**この `reasoning=xhigh` は adoption pin であり、
  変更には採用裁定と pin の同時更新が要る** (`tools/check_docs.py` が実測で拒否した)。
  加えて `docs/dev-wave/**` の L1.5 予算は 9696 bytes に対し現行 9660 bytes で、
  是正文を足すと 9732 bytes となり超過する。段 8 契約に従い実装せず裁定へ返す。
- {{T:a1-v3-complete-staging-precheck}} **P3・新規**: v3 `complete` は completion staging の
  freshness を不可逆な成果物 (result root、`result.json`、`receipt.json`、group terminal) の
  作成より後にしか見ない。同一 PID の先行 crash が残した staging があると completion だけが
  生まれず、その attempt の proof chain を閉じられない。引き金は極めて狭く、`complete` は
  現行でも result root 作成後の失敗から再開できないため、1 cycle 後へ送った。
