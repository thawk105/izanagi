---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t650-lease-release
seq: 1
title: land 到達後の受入 lease 残留を機械で塞いだ — 敵対 2 レンズが親の測定 3 件と provisional 裁定 1 件を覆した (コード + テスト、branch worktree-dev-wave-t650-lease-release、変異 13/13 期待一致)
---

## 本文

- **ユーザー指示 (2026-08-16)**: 受入全走のボトルネックを根治する。**リワードハック禁止**。
  ログを見ること。並行セッションと通信してよい。
  「終わった dev-wave が lease を解放していないケースがあるだろう」
  「タイムアウト頼みで他にめっちゃ迷惑かけてるやついる気がする」— **両方とも実測で確認した**。
- **並行セッション経由で伝達されたユーザー裁定**: 決定的な赤の再試行ループについて
  「二度とそんな無駄を繰り返すな、全セッションに対して許さない」「すべてのセッションを調教しろ」
  (= 記憶でなく機械で縛る)。本 wave の段 4 裁定の拘束条件として扱った。
- **本 wave が閉じたのは「land 到達後の lease 残留」だけである。** 受入全走のボトルネック全体では
  ない。閉じていない面は下記の新規項目に分けた。
- **観測した 2 事故 (2026-08-16)**。(i) 21:01 に land 成功した wave が release せず、
  lease は mtime 21:00 + TTL 2400 秒の満了 (21:41) まで残り、6 wave が 11〜50 分待った。
  holder digest は `sha256(<wave slug>)[:12]` の一致で同定した。
  (ii) 別 wave が決定的な provenance 赤 (rc=29) を 45 秒ごとに再試行し lease を占有した。
  真因は保存ログの最終行にあり `tail -3` で読めた。
- **段 3 の敵対 2 レンズが親の実測 3 件を過大一般化として潰した。**
  (a)「lease 内実作業の中央値 308 秒」は再現しなかった。レンズ A の再集計は
  時系列対 30 対・中央値 397.5 秒、fold の第一 parent が当該 merge である厳密対
  **20 対・中央値 276.5 秒・最大 2037 秒**。**厳密対を採用し、親の初回値は誤りとして残す。**
  (b)「最大 4827 秒」は親子関係のない commit 間の時刻差で、**TTL 超過 holder の実在証明にならない**。
  (c)「6 wave が 11〜50 分待ち」は一時点の観測で、40 分後には 1 本へ減った。定常値ではない。
  **これらは lease lifetime ではなく commit 時刻差であり、改善率の基準値に使えない。**
- **段 3 レンズ A が親の provisional 裁定 (P1) を却下した。** 親は「未知の rc は terminal 側
  (手放す側) に倒すのが安全側」としたが、これは可用性側であって正しさ側ではない。
  terminal を retryable と誤る最悪値は「TTL または誤 loop が続く間の停止」(時間損失) だが、
  逆向きの誤りは「元 lander が再開可能な間に排他を解き、別 wave の受入を重ねる」(正しさに隣接)。
  **既定を保持側へ反転し、明示宣言した到達点だけが解放を許す形へ変えた。** 詳細は {{D:land-terminal-lease-release}}。
- **段 6 の敵対 2 レンズが must-fix 8 件を出した。** うち 1 件は運用中の実事象と直結していた —
  provenance の `returncode != 0` を全部「決定的拒否」としており、**dispatch の
  infrastructure failure rc=16 も signal 由来の負値 (-9 / -15) も解放する**。
  レンズは I/O seam 実行で `1, 16, -9, -15` のすべてが解放側になることを実測した。
  **この罠は並行セッションからの情報提供 (bounded local で rc=16 を実際に踏んだ) を
  handoff へ記録し、レビュー prompt の攻撃面に入れた結果として出た。** 単独セッションなら
  見落とした可能性が高い。
- **fix 1 巡目が回帰を作り、親の実走だけが検出した。** F5 の修正が再取得後に
  `_locked_preflight()` を丸ごと完了させたため、その中の heads 検査 (rc=23) が
  provenance 拒否 (rc=29) を先取りした。子は pytest を起動できないため気づけない。
  2 巡目で head・collision fingerprint を全 preflight より先に再計算する順序へ戻した。
- **親の疑いが受理集合の変更を 1 件止めた。** fix 1 巡目が `_open_dir` の rc を引数から
  `RC_IDENTITY` へ固定していた。main 取り込みの競合合成で全呼び出し元 8 箇所を列挙させたところ
  **2 箇所が `RC_CONTROL_PLANE` を渡しており**、固定は受理集合を変える。引数 `rc` を使う形へ戻した。
- **codex 子は pytest を 1 度も実走できなかった** (`dispatch infrastructure failure:
  qstat -Q preflight rc=1` / `Unknown user-id`)。**実走はすべて親が行い、子の非実走を緑と記録していない。**
  親の bounded local 実行も 3 回 rc=16 で止まった ([T-604] の既知事象)。
  **rc=16 は赤ではなく「測れなかった」であり、赤として数えていない。**
- **変異は 13 件を事前登録し 13/13 が期待と一致した** (12 KILLED + 1 SURVIVED、MISMATCH 0、
  baseline PASSED)。**release 呼び出しを丸ごと削除する変異 (= wave 前の実コードそのもの) は
  6 node が KILL した。** 生存 1 件 (receipt 権限未検証でも解放する変異) は注入実在を
  anchor 一致と injection diff hash で確認したうえで**下層に mask された等価変異**と判定し、
  両層同時変異を別途登録して KILLED を確認した。**生存を隠して KILLED を水増ししていない。**
- **焦点走で 1 件の赤が残った。** `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean`。
  機械化された非帰属 checker が `status=non-attributable-only` / `classification=non-attributable` /
  `rerun_rc=1` を返し、**tested main でも再現する main 側の赤**と確定した。
  受入形の走行では出ず焦点走 (非受入形) でだけ出る。詳細は新規項目へ。
- **並行セッションとの協調が実際に成果へ効いた。** 相手側の land を先行させて衝突を減らし、
  相手から受け取った「merge が provenance 違反を生むかは commit 前に測れる」実測
  (merge-base からの変更 file の積集合が空なら違反は生まれない) を本 wave の取り込み前に適用した。
  予測どおり積集合に実装面 2 file があり、**merge を実行する前に Codex `role=author` の
  合成監査が要ると分かった**。逆に本 wave からは、相手の preflight が同じ rc 畳み込み欠陥を
  持つこと、および待ち札の順位喪失の機序を渡した。
- **erratum**: 相手 wave が同日 land した F365 の「計 42 回」は誤りで、保存ログ実測では
  **43 回** (`land-loop.log` 31 行 + `land2-loop.log` 12 行)。相手は受入走行中で tracked file を
  触れず訂正できなかった。本エントリは 43 を正とする。
- **merge 進行中は codex 子を起動できない**ことが分かった。`tools/pegasus/admission_registry.json` の
  working bytes が HEAD blob から drift するため Codex hook 配線の exact 検証が落ちる。
  index の sha256 を控えて working tree だけ HEAD へ戻し、子の完了後に index から復元して
  sha256 一致を確認した。

## 次の一手差分

### 更新

- [T-650] **P2・一部着地**: land が到達点ごとに release_safe / retryable_same_request を宣言し、
  両方成立するときだけ受入 lease を自分で解放する形が着地した ({{D:land-terminal-lease-release}})。
  **起票文が求めた「claim〜release を 1 つの wrapper の finally へ束ねる」形は採っていない** —
  束ねると land を駆動する呼び手の形を全部変えることになるため、land の終端へ置いた。
  **残るのは land へ到達しないまま終わる経路** (argparse 失敗・context 死亡・SIGKILL・
  受入緑後に land 前でセッションが死ぬ) で、ここは依然 TTL 2400 秒まで他 wave を止める。
  発生率の分母は測れていない。
  base: fb0fef6bca04cc6e7fd1e063ab7749b25c2b6f4994f58c292097893a47877cc3

### 新規

- {{T:lease-ticket-seniority}} **P1・新規**: 受入 lease の待ち札は稼働中 process の
  heartbeat でしか生き延びず、最後の claim から 300 秒で失効して新しい到着時刻で作り直される。
  受入が赤・argv エラーで終わった wave の親は解析・修正・再投入で 300 秒を超えるのが普通なので、
  **赤を 1 回踏むと行列の最後尾へ落ちる**。2026-08-16 に 1 wave が 52 分の先着順位を失い、
  後着 3 本に追い越された (待ち札の到着時刻が書き換わったのを実測)。行列長 4〜6 本のとき
  フレーク 1 件の実コストが「受入 1 走 2.5 分の再走」から「40〜70 分の待ち直し」へ増幅される。
  択一は (a) 同一 process 内で再試行させる (D253 の待ち札意味論に触れないので親推奨)、
  (b) heartbeat を claim 以外の経路でも出す (順序キーと生存の分離が崩れるため非推奨)、
  (c) 待ち札 TTL を延ばす (放棄札が先頭を塞ぐ時間が延びるため非推奨)。
  成果物影響 = 直さない場合、フレークのたびに certified 選択・レポート・台帳の確定が
  40〜70 分ずつ遅れる。
- {{T:lease-event-log}} **P2・新規**: 受入 lease の claim / release / TTL 失効に監査証跡が無く、
  「release が機械化されたか」「待ち時間がどれだけ減ったか」を事後に測れない。
  段 3 と段 6 の敵対レビューが独立に要求した。release 側だけでは
  「claim されたのに release されなかった」を検出できないので claim 側も要る。
  lease directory へ bounded な append-only JSONL (時刻・wave digest・main SHA・state・
  reason・source) を置き、判定には使わず後処理でのみ読む案。
  成果物影響 = 直さない場合、再発率・平均待ち時間・改善率を台帳へ書けない。
- {{T:land-retry-protocol}} **P2・新規**: 既知の land 再試行 script は rc を自前分類し、
  終端的な赤でも lease を再取得せずに land を再実行する。自動解放が入ると 2 回目以降は
  lease 無しで全史 provenance (38〜61 秒) を走らせ、次の holder の receipt と main snapshot を
  古くしやすい。呼出し protocol (terminal 結果を受けた caller は停止し、再試行には新 claim と
  新 receipt が要る) の明文化と、正本 wrapper 側での強制が要る。
  成果物影響 = 直さない場合、受入レポートの試行回数と有効 receipt 集合が競合順序で変わる。
- {{T:red-depends-on-run-shape}} **P2・新規**: `test_exploration_external_root_keeps_wave_clean` が
  受入形の走行では緑、焦点走 (非受入形) では計算ノード単独でも赤になる。非帰属 checker は
  tested main で再現することを確認済み (`rerun_rc=1`)。**赤の有無が走行形に依存する**ため、
  焦点走を根拠に差分へ帰属させる判断が誤りうる。原因の分離と、走行形を跨いで一貫させるかの裁定が要る。
  成果物影響 = 直さない場合、焦点走の赤を差分の回帰と誤認して不要な fix 巡回が起きる。
