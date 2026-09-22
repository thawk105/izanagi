---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-22
wave: dev-wave-t2851-transfer-prereg
seq: 3
---

## 新規

### {{F:stock-names-different-builds}}. 事前登録の比較対象で「stock」を CCBench の上流既定と定義しつつ、A-2・A-6 の「stock」(無 backoff) と同じ build だと書いた [誤前提]

- 事象: [T-2851] の事前登録 v1 の初稿は、R0 (stock) を「CCBench pin の上流既定」と定義したうえで、read-heavy の強い静的設定 (無 backoff) を
  「R0 と同じ build なので重複除去」と書いた。上流既定は CCBench の `cmake/Options.cmake` で BACK_OFF=1 (abort 時の指数 backoff 有効) で、
  A-2・A-6 の certification JSON が role `stock` と呼ぶ arm は BACK_OFF=0・固定値なし・他は既定である。後者の flag の組は balanced・write-heavy の
  `p2_2_flag_opt` (B0-L-W0) と同じだった。段 6 レビューの走行中に親が T-2849 の設計書の「stock 経路は BACK_OFF=1」という記述から疑い、現物で確かめて
  land 前に直した。放置していれば、read-heavy で比較対象が 1 つ消え (重複除去)、主要族の大きさと費用の試算が変わっていた。
- 根本原因: repo の中で「stock」が指す build が記録ごとに違う (A-2・A-6 の記録 = 無 backoff、CCBench の既定 build と p3_s4_loop の stock 経路 =
  BACK_OFF=1)。論文ストーリーと差分分析の「無 backoff 比」という言い方を、名前だけで上流既定と同一視した。
- 恒久対応: 比較対象を書くときは名前でなく flag の組 (BACK_OFF・NO_WAIT_LOCKING_IN_VALIDATION・NO_WAIT_OF_TICTOC・WAL・固定値) で書き、
  記録の「stock」を引くときは当該記録の genome を開いて確かめる。memory `stock-names-different-builds` と、事前登録
  `docs/unseen-condition-transfer-preregistration.md` §4 の R0 の注。
- 再発検知: 「stock と同じ」「stock 比」を書く箇所で、比の分母の genome の BACK_OFF が書かれていなければこの型を疑う。

### {{F:non-idempotent-normalization-record}}. 逐語の可逆正規化を記録する script を冪等でない形で書き、別の command に紛れた再実行が記録を除去 0 件で上書きした [手順漏れ]

- 事象: [T-2851] の段 7 前、insight へ写した Codex 出力 2 本の行末空白を除く script を job tmp に書き、原文の sha256・byte 数・除去した行を
  `verbatim/NORMALIZATION.json` に記録した。後で handoff を更新する command の先頭に、その script の起動を誤って混ぜて実行した。script は引数を無視して
  既に正規化済みの file を「原本」として読み直し、除去 0 件の記録で JSON を上書きした。段 6 の修正 commit の差分統計 (JSON の rewrite 76%) で気づき、
  直後の commit で元の内容へ戻した (差分 0 を確認)。本文 file は変わっていない。land 前に閉じた near miss。
- 根本原因: (1) 記録を書く script が「入力が既に正規化済みなら何もしない」形になっておらず、2 回目の実行が 1 回目の記録を黙って壊す。
  (2) 無関係な処理を 1 つの Bash 呼び出しへ継ぎ足した。
- 恒久対応: 可逆正規化の script は、出力先の記録が既にあれば上書きせず停止する (冪等) 形で書き、実行は単独の呼び出しにする。commit 前に
  `git diff --cached --stat` で意図しない file が含まれないかを見る。memory `git-and-guard-discipline` の「記録を書く使い捨て script は冪等に」節。
- 再発検知: commit の差分統計に、その commit で触る予定の無い記録 file (NORMALIZATION・manifest・receipt) が出たらこの型である。
