---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1275-lease-ticket-retry
seq: 1
title: 受入待ち手へ同一 process 内の attempt 再試行を入れ、再試行の引き金を raw rc から肯定的証拠の合議へ変えた (コード + テスト + docs、branch worktree-dev-wave-t1275-lease-ticket-retry)
---

## 本文

- ユーザー裁定 [T-1275] 択 (a) の実装。待ち札の意味論 (D253) には触れていない。
- **段 3 と段 6 の敵対検証が計 21 件の所見を出し、親は全件を real と裁定した。refuted はゼロ。**
  そのうち 2 件は独立 2 例 (段 3 の A-3 と B-3) で同じ欠陥を突いた。
- **併走を許可されていた [T-1172] を本 wave から外した。** 裁定文は「[T-1275] と同じ作業で
  扱ってよい」であって義務ではない。段 3 の 2 レンズが独立に、land 側で `wave_land_window.claim`
  を renew として流用すると **lease と待ち札を新規生成する** (land が retryable 終端なら
  最大 2400 秒 / 300 秒残る) ことを実コードから成立させた。安全な形には `wave_land_window.py` へ
  非取得型 renew primitive を新設する必要があり、それは D253 の実装面そのものである。
  絶対規律 5 (段階導入) に従い別 wave へ送る。
- **親の provisional 裁定 P1 は、段 3 で 2 レンズが独立に反証した。** 親は「rc が 0/1 以外なら
  判定なし」と置いたが、`tools/pegasus/dispatch_compute.py` は受領証の永続化に失敗すると
  **child rc を得ているのに `INFRA_RC` (=16) を返す**。pytest が実走して rc=1 の赤を出しても
  待ち手には 16 に見えるため、raw rc を発火条件にすると実走赤を再試行できた。規律 2 の直接違反。
  親が一次資料で再現手順を確認して採用し、肯定的証拠の合議へ設計を変えた。
- **段 6 レンズ C は、肯定的証拠そのものが弱いことをさらに突いた。** `child_started` は
  qstat が RUN を観測したかに依存しており、短い job が `QUE -> END` と遷移すると
  実走していても false になる。log が切り詰められて赤痕跡が落ちれば裏取りも素通りする。
  producer 側で「まだ待ち行列にいる」肯定証拠を要求し、consumer 側で切り詰め framing を
  不在確定不能へ倒す形で閉じた。
- **偽造耐性の新 channel は作らないと裁定した。** attestation は受入 command と同じ
  stdout/stderr にあり、repo 内 runner を書き換えれば偽造できる (段 6 レンズ C)。
  ただし (i) [T-1299] で source root repository は信頼済み中核と裁定済み、
  (ii) 偽造で得られるのは attempt 上限 2 のもとでの**再試行 1 回**だけで赤を緑に変えられない、
  (iii) 新 channel は D239/D253 と同格の設計判断で独立の敵対検証を要する。
  **残る限界として明記し、{{T:acceptance-attestation-forgery-channel}} へ起票する。**
- **本 wave が閉じない残余を明示する。** 実測された t1180 の 52 分喪失 (F365) は
  「lease 取得後・受入 command 投入前に落ちる型」であり、本 wave が対象にする
  「受入 command が判定を産まずに戻った型」ではない。同じ argv の即時再試行では直らず、
  親が修正済み message path を供給する協調点の設計が要る。
  {{T:acceptance-postclaim-precommand-recovery}} へ起票する。
  rc=16 型の発火率と節約時間は**未計測**である。本 wave が入れる retry journal で以後測れる。
- 段 3 レンズ B・段 6 レンズ D が独立に「40〜70 分」は queue 長 4〜6 の**観測範囲**であって
  確定値ではないと指摘した。成果物影響の記述からその一般化を落とした。
- **段 6 レンズ C は変異 kill の帰属も攻撃した。** 事前登録のうち 6 件が
  「名目上の assertion はあるが受理集合も fail-closed 挙動も検査していない」型だった。
  M3/M4/M5 を実 lease directory・競合待ち札・inode/mtime・実 release の観測へ強化し、
  M12 は `DW-M08` に従い kill でなく diagnostic sensitivity pin へ別枠記録した。
- 設計判断は {{D:acceptance-retry-positive-evidence}}。
- 実測: 段 5 後の焦点走 15 file = 2314 passed / 1 failed。赤は実装子が新設したテストの
  期待値の誤りで production の欠陥ではなかった (red-check 失敗経路は受領証発行前に止まるので
  receipt-reclaim の 2 回目 claim へ到達しない)。段 6 fix 後の焦点走 17 file =
  **2438 passed / 0 failed (rc=0)**。全史 provenance 監査 = 3856 件・新規違反なし。
  `check_docs` = 違反なし。
- 工数: 段 2 プラン 15 分、段 3 敵対 2 本 (sol 18 分 / luna 15 分)、段 5 実装 2 単位
  (U2 9 分 / U1 23 分)、段 6 レビュー 2 本 (11 分 / 15 分)、段 6 fix 19 分。
  codex 子は 8 本すべて `stop_reason=completed`。

## 次の一手差分

### 完了

- [T-1275] 受入 lease の待ち札を同一 process 内で再試行させる形を実装した。lease を保持したまま
  attempt 境界で自 holder の claim により mtime を更新し、`ownership` を `ACQUIRED` のまま保つ。
  再試行は「受入 command が pytest の判定を 1 つも産まなかった」ことの肯定的証拠が
  6 条件すべて揃ったときだけ許す。D253 の待ち札意味論・受領証 schema・rc 意味論・
  受入の受理 2 経路はいずれも不変。
  remaining: none
  base: a91115093abc90e8ad8e983279981e2eb7ef21cfbed06413e938443c59dd77f7

### 更新

- [T-1172] **P2・裁定済み (2026-08-17 /rulings 全件 第 5 回、lease renew)**: land 直前の
  lease renew を入れる。660 秒 > 300 秒が確定値なので実測を待たない。外側 deadline は着地失敗の
  事実を変えないため不採用。**[T-1275] と同じ作業で扱う案は 2026-08-17 に取り下げた** —
  段 3 の 2 レンズが独立に、`wave_land_window.claim` の renew 流用は lease と待ち札を
  新規生成すると実コードから示した。安全な形は同 file への非取得型 renew primitive の新設を要し、
  D253 の実装面に当たるため独立の敵対検証を要する。単独 wave で扱う。
  base: 910891de405834d4e22275de00ec14cdb871caf8742b97df0a9235f9e31fdc15

### 新規

- {{T:acceptance-postclaim-precommand-recovery}} **P1・新規**: lease 取得後・受入 command
  投入前に落ちる型 (実測 t1180、F365) からの回復経路が無い。同じ argv の即時再試行では直らず、
  親が修正済み `--merge-message-file` path を供給する協調点の設計が要る。
  [T-1275] は「受入 command が判定を産まずに戻った型」だけを閉じており、
  実測された 52 分喪失はこの型ではない。設計択一を裁定パッケージで返す必要がある。
  成果物影響 = 直さない場合、この型を踏むたびに certified 選択・材料レポート・台帳の確定が
  観測範囲で 40〜70 分遅れ続ける。
- {{T:acceptance-attestation-forgery-channel}} **P3・新規**: dispatch の
  `IZANAGI_DISPATCH_OUTCOME_V1` attestation は受入 command と同じ stdout/stderr channel に
  あるため、repo 内 runner を書き換えれば偽造できる。[T-1299] の信頼済み中核の内側であり、
  偽造で得られるのは attempt 上限 2 のもとでの再試行 1 回だけ (赤を緑に変えられない) なので
  本 wave では受容した。dispatcher が受入 command から書けない場所へ nonce 付き sidecar を
  `O_EXCL` で置き、待ち手が inode・schema・nonce・完全終端を検証する案がある。
  再訪 = 外部公開時、または attempt 上限を 2 より増やすとき。
  成果物影響 = 直さない場合、内部作業者が再試行 1 回を余分に引ける残余が残る。
