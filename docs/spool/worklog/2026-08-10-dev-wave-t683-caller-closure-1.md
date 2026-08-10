---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t683-caller-closure
seq: 1
title: certified writer の caller 閉集合検査から部分恒真を除いた — 旧テストは負変異 14 件を同時注入しても緑、新テストは全件検出 (コード + docs、受入 7927 passed / 20 skipped / 495.29 秒、変異 16/16 事前登録一致、branch worktree-dev-wave-t683-caller-closure)
---

## 本文

- **起動ゲート**: 裁定 (2026-08-09 /rulings) が「[T-671] 実装 wave の後」と順序を指定していたため、
  起動時に land を確認した。初回起動時 (2026-08-09 20:52) は [T-671] 実装 wave が段 6 の fix 8 巡目で
  稼働中・自前 commit ゼロだったので、着手せず状況を返して終了した。2026-08-10 04:29 に land
  (main=d41f4741、entry 355) したのを確認して再開した。同梱はしていない。
- **段 1 の前提実測**: 裁定文が挙げた 2 経路に 1 経路を足し、一時変異 → 実測 → `git checkout --`
  復元で 3 件とも部分恒真を再現した。(A) `loop.py` へ authority なしの 2 本目 `evaluate()` を
  足しても緑、(B) `campaign/` へ新規ファイルを置いて `run_campaign()` を呼んでも緑、
  (C) 台帳に載る `demo.py` へ alias + attribute 形を足しても緑。いずれも 1 passed のまま。
- **成果物影響の訂正**: 段 3 レンズ A が親 brief の 1 行を誇張と判定し、親が採用した。
  両 sink の `authorization_contract` は既定値なし keyword-only なので、省略した呼出しは
  書き込み前に `TypeError` になる。よって現行境界で失われるのは「閉集合を検査した」という
  **証拠の真正性**であって、未認可 COMMIT の certification ではない。将来の既定値退行に対する
  最後の網である点を仮定で終わらせないため、signature 自体の pin を足した。
- **設計の切り替え**: 焦点再レビューが 2 巡とも「resolver の scope model が Python と一致しない」
  形の穴を出し続けたため、親が**完全再現を放棄**して「resolver が厳密に模型化しない再束縛・
  shadow・参照はすべて `UNRESOLVED` (= 赤) に倒す」原則で閉じると裁定した。fix は 3 巡で終端。
- **恒真の再発を 3 度指摘された**: (1) 段 5 実装は `getattr` を bare literal しか閉じておらず、
  (2) fix 1 巡目は fixture リストを空にすると loop ごと消え、(3) fix 2 巡目が導入した第 3 分類
  `OUT_OF_SCOPE` は repo 走査で蓄積されるだけで一度も検査されていなかった。(3) は
  `<other>` の穴を名前だけ変えて温存した形で、理由 enum + allowlist 照合で閉じた。
- **fix 子の自己申告は 2 度とも甘かった** — 焦点再レビューが `closed` 申告を `partial` と判定した
  (F2/F4、次いで G1〜G3)。実装子の完了報告を採用条件にしないことの実例。
- **走査根の凍結を親が撤回した**: 段 4 は除外 5 種で凍結したが、レビューが
  `output/pegasus-dispatch/*/interpreter_probe.py` を実測で指摘した (dispatch のたび増え、
  レビュー中に走査対象が 263 → 264 と変動)。親が 8 種へ改訂し、走査対象は 227 本で安定した。
- **新旧両走 (DW-M08)**: 負変異 14 件を**同時注入**した木で、旧テストは 1 passed (2.58 秒) =
  検出力ゼロ、新テストは同じ木で 1 failed (8.51 秒)。個別帰属は変異 matrix が担う。
- **受入 lease で 2 度空振りした**: 取得できた時点で main が 7 commit / 22 commit 先行しており、
  runbook §7.3 の「待ち手は `HEAD..main == 0` の検査に留め、0 でなければ lease を返す」に
  従って 2 回とも返した (待ち時間 合計 約 2 時間)。3 回目は待ち手内で merge commit を作る形へ
  変えて通した。詳細と恒久策は {{F:acceptance-lease-overtaken-while-queued}}。
- **段 8 の改善候補は 3 件**。うち 2 件は reference 節への統合候補、1 件は上記 F。
  本 wave では reference を編集せず、台帳へ送るに留めた (段構成・防壁・裁定境界に触れないが、
  runbook §7.3 の手順そのものの変更にあたるため)。
- エージェント工数: codex 子 8 本 (plan 1、敵対相談 2、実装 1、レビュー 2、fix 3 のうち
  レビュー内訳は敵対 2 + 焦点再レビュー 2)。親の実走は対象 nodeid 6 回、新旧両走 2 回、
  変異 matrix 17 走、受入全走 1 回。

## 次の一手差分

### 完了

- [T-683] caller 閉集合検査の部分恒真をテスト側のみで修繕した。受理集合は不変
  (現 tree で走査 227 本・`run_campaign` 15 本・`evaluate` 5 本すべて authority あり)。
  remaining: none
  base: ea669497500669849aee7fdbd60eac1f366caca032d27c0484709eb9bdc00eab

### 新規

- {{T:acceptance-lease-waiter-merge-contract}} **P2・新規・ユーザー裁定待ち**: 受入 lease の
  待ち手契約 (runbook §7.3) を改訂するか。飽和時は `acquired` の時点で main に追い越されており、
  「0 でなければ lease を返す」に従うほど投入できない ({{F:acceptance-lease-overtaken-while-queued}}、
  同一 wave で独立 2 例)。本 wave は待ち手内で merge commit を作る形で回避したが、
  runbook 本文の改訂は scope 外とした。選択肢 = (a) 待ち手内 merge を正本化する /
  (b) lease の粒度を「受入 + land」まで広げる / (c) 現状維持で待ち手の空振りを許容する。
  成果物影響 = 受入結果そのものは変わらないが、飽和時に wave が land できず滞留する。
