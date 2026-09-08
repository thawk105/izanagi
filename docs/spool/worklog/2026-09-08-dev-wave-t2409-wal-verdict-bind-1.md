---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2409-wal-verdict-bind
seq: 1
title: [T-2409] B-10 集約の受理経路へ WAL の正しさ判定を束縛した — 既存 135 literal の再発行は不要と実測で確定し、親 brief の枠組み 2 点を敵対相談が倒した (コード + テスト + insight、branch worktree-dev-wave-t2409-wal-verdict-bind、変異 12/12 KILLED)
---

## 本文

- ユーザー指示 (dev-wave 引数): WAL の `anomalies` / `certified` / `verdict` を既存の内容 digest へ
  含めて閉じる (D1772)。起草時の「gate を作らず明記」は D1744 の誤引用に基づき撤回済みなので採らない。
  **着手前に既存 2 系列の literal を再発行せずに重ねられるかを実測する。** 本題の実装だけ。
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- **着手前の実測の答えは「再発行不要 (0 個)」。** 内容 digest は block record 本体の hash で、
  同じ値が現物 file 内に `record_sha256` として書かれている。3 系列 135 file を production 関数で
  読み直して literal 集合と完全一致を確認し、**block record 側に 3 field が 1 件も無い**ことも
  確認した (各 0/45)。よって digest の対象を字義どおり広げると凍結 file の書き換えになる。
  D1772 が指示した「追加 exact 条件として重ねる」形なら 135 literal は 1 個も変わらない。
- **段 3 の敵対相談が親 brief の枠組みを 2 点で倒し、段 4 で撤回した。** (a) 「D1772 の字義は
  実装不能なので代替を採る」は誤りで、**D1772 自身が「literal を再発行せずに追加 exact 条件として
  重ねられるかを実測せよ」と書いている**以上、値述語は裁定が名指しした第一候補そのものである。
  (b) 「凍結 135 file の書き換え or 系列別 whole-WAL digest」の二択も偽で、`variant` + tag + 3 field に
  限った projection digest という第三形がある。第三形は存在を認めたうえで不採用とした —
  新しい digest producer・期待値・対応規則を要し「新しい gate 機構は作らない」から遠い ({{D:wal-verdict-realization}})。
- **段 2 プランの述語 code が `payload` 未定義だった** (このループの変数は `record.payload`)。
  そのまま貼ると現物 3 系列まで `NameError` で拒否される。段 4 で訂正して実装子へ渡した。
- **親の段 1 pin 閉包に穴があった。** whole-file sha256 pin は path で探したが、**行番号 pin を
  探していなかった。** production へ 10 行足したことで `run_formal` の build sink が 4051 行から
  4061 行へ動き、deferred-gate 登録簿の pin が stale になって既存 3 node が赤になった。
  consumer 拡張の焦点走 (`DW-O26`) と段 6 レビューが独立に検出し、着地前に閉じた。
- **段 5 実装子の prompt が `DW-S05-C` の必須項目を 5 つ落とした** (実走 nodeid の併記、
  meta-test の自己洗い出し、hash 差し込み禁止、揮発 payload 禁止、波及の静的列挙)。
  投入後に気づいたので子は撒き直さず、親が全走・波及列挙・diff 確認で補償し、
  段 6 の fix 子 prompt には全項目を入れた。
- **段 6 レビュー 2 本と再レビューはいずれも NO-GO を出した。** 行番号 pin (両者が独立に検出) と、
  collector 正例が 3 validator と lock を stub していた点。lock は実物を通す形へ直した。
  **validator 側は親が実測して裁定 (A10) を訂正した** — validator は各 record の
  `submission_receipt` を実 path として開き bytes を照合するので repo 内では通せず、
  receipt を書き換えると `record_sha256` が凍結 literal と一致しなくなる。逃げ道が無い。
  先行 wave が同じことを実測して記録済みの構造的限界である。要求を lock 部分だけへ狭め、
  限界を test の docstring と insight に明記した。**「統合を通した」とは書かない。**
- **親が must-fix を 1 件足した** — 攻撃の再現 test (拒否側) が無く、受理側しか無かった。
  これが無いと wave の主張を挙動で示せないので fix で追加した。件数 90・tag 15/75・variant・
  block record 45 件・lock bytes をすべて保ったまま 1 record の `anomalies` だけを崩し、
  `_collect_report_inputs` が `legacy-wal-verdict` で止まることを固定した。
- **既知の型を踏んだ (親起因)。** `check_ai_provenance.py` の全史監査を `timeout 300` で打ち切り、
  dispatch 親が SIGTERM されて orphan hold が立ち、以後の dispatch が全部 rc=16 になった。
  **F333 に何度も記録され auto-memory にも「削除対象は 2 つある」まで書かれている型で、新事実は無い。**
  記録があったのに読まずに踏んだこと自体が事象である。復旧は既載の契約どおり (手動 qdel をせず、
  request が稼働中だったので終端まで待ち、clean/HEAD を確認して 2 file を削除)。被害ゼロ。
- **主張の限界を明記した。** 束縛するのは WAL に記録された 3 値であって生成主体・verifier の実行では
  ない。WAL に hash chain は無く真正性は束縛しない。検査の母集合は「終端済みで parse 可能な
  `stage == "verify_done"`」に限る。この 2 つは {{T:wal-authenticity-binding}} と
  {{T:wal-absence-fail-closed}} としてユーザー裁定へ返す。

## 次の一手差分

### 完了

- [T-2409] WAL の `anomalies` / `certified` / `verdict` を B-10 legacy 受理経路の exact 条件として
  束縛し、閉じた。既存 135 literal の再発行は不要と実測で確定した。
  remaining: none
  base: 767bf773dbc6d5d64dbb482fd13bd52f4bd840981669da5347f4b69bbd7ba932

### 新規

- {{T:wal-authenticity-binding}} **P2・ユーザー裁定待ち**: 3 field を正常値で自己申告した偽 WAL は
  述語を通る。WAL に hash chain が無く真正性の仕組みを持たないのは既存の性質で、閉じるには
  暗号学的束縛 = 新しい gate 機構が要る。D1772 が却下し、ユーザーも「仮想リスク向けの gate 追加は
  scope 外」と指示しているため実装せず返す。再訪条件 = 偽 WAL による誤った report 発行が
  実際に起きたと示せたとき、または論文の主張が WAL の真正性まで要求するようになったとき。
- {{T:wal-absence-fail-closed}} **P2・ユーザー裁定待ち**: WAL 欠落・読取例外・未終端 tail は
  述語へ到達しない。ただしこれらの経路では `incomplete_slots > 0` か `wal_read_error` が立った
  見て分かる別物の report になるので、T-2409 が名指しした「同じ判定の report が出る」穴には
  当たらない (`_verification_completeness` は一度も raise せず開示するだけであることを実測)。
  fail-closed 化は受理集合をさらに狭める別の裁定事項なので返す。
