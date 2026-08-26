---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1848-env-coincidence
seq: 3
---

## 新規

### {{F:env-coincidence-remedy-adds-new-dependence}}. 環境の偶然への依存を消す是正が、別の環境依存を持ち込んだ [テスト代表性] [恒真ゲート]

- 事象: process 全体の fd 件数比較をやめ、clean な子 process 内で「開始前後の全 fd identity
  差分」を比べる形へ書き換えた。敵対レビューが 2 点を指摘した。(a) identity が
  `(fd, st_dev, st_ino, file type, st_rdev)` なので、**同じ fd 番号で同じ file を閉じ直して
  開くと別の open description でも同一 tuple になり**、件数を保ったままの入れ替え回帰を
  受理する。(b) 検査が `/proc/self/fd` の可視性を直接要求するため、**procfs が無い・PID
  名前空間から不可視・アクセス拒否の環境では正しい実装でも 7 node すべてが赤になる。**
- 根本原因: 「環境の偶然に依存しない形へ書き換える」という目的に対し、
  **書き換え先が新しい環境の前提を置いていないかを検査していなかった。**
  是正の正しさを「元の依存が消えたか」だけで見て、「別の依存が生えたか」を見ていない。
- 恒久対応: identity を `kcmp(KCMP_FILE)` で open description まで識別する形にし、
  同一 inode・同一 fd 番号の count-preserving swap を負例として追加した。
  procfs や `kcmp` が使えない環境では**黙って通さず明示して停止する**。
  分類台帳 `docs/test-environment-coincidence-ledger.md` に、
  是正が新しい環境依存を持ち込んでいないかを確かめる観点として記録した。
- 再発検知: count-preserving swap の負例と、能力不足時に停止することの検査。
  変異 matrix の M03 (fd の close を最初の失敗で中断する) が
  `test_close_fds_best_effort_closes_all_and_reraises_first_error` と
  `test_copied_binary_close_error_does_not_leak_later_fds` の 2 件で KILLED になることを確認した。

### {{F:exclusivity-proved-only-up-to-attempt}}. 排他の証明が「lock を試みた」までで止まり、scheduler 次第で壊れた実装が通った [恒真ゲート]

- 事象: 「N 秒待って終わらないこと」で排他を代理観測していた検査を、
  lock-attempt event で同期する形へ置き換えた。敵対レビューが、event は実 `flock` の**直前**に
  立つため、writer が排他 lock を即時取得し、そこで scheduler が writer を止め、
  main が critical section を完了した後に writer が再開しても、
  **期待する trace と期待するエラー文言の両方が成立する**ことを示した。
  共有 lock を除いた実装が scheduler 次第で受理される。
- 根本原因: 因果の証明を「呼ぼうとしたことの観測」で代用した。
  実時間の負の待ちを消したことで代理観測は無くなったが、
  **証明したい性質 (その時点で lock が保持されている) を直接観測してはいなかった。**
- 恒久対応: 別の open description からの**非 blocking lock probe** で、
  その時点で lock が保持されていることを観測する形にした。
  critical hook の前後関係まで検査し、pre-call race を閉じた。
- 再発検知: 変異 matrix の M01 (attempt registry の共有ロックを取り除く) と
  M02 (manifest ロックを排他から共有へ落とす) が、いずれも是正した検査そのもので KILLED になる。
  M02 は初回 probe で SURVIVED だったが、等価変異ではなく照準の誤り
  (テストが撃つのは manifest ロックなのに receipt ロックを変異させていた) で、
  実効 gate へ再照準して KILLED を確認した。

### {{F:boolean-literal-counted-as-numeric-bound}}. 真偽値リテラルを数値として数え、母集合と「先行記録との一致」を誤って報告した [誤前提]

- 事象: 待ち上限の候補を AST で数える走査を書き、母集合を 244 件 / 67 file と報告した。
  さらに「この 244 は失敗台帳が記録した 244 と一致する」と書いた。
  敵対レンズ 2 本が独立に 243 件 / 66 file と数え直し、食い違いを指摘した。
- 根本原因: Python では真偽値が整数型に含まれるため、`isinstance(value, (int, float))` が
  `True` / `False` を通す。走査が真偽値の引数を数値の上限として数えていた。
  **一致していると書いた「先行記録との一致」は、このバグ由来の偶然だった。**
  先行記録側の走査述語は記録されていないので、そもそも比較できない。
- 恒久対応: 走査述語に「真偽値リテラルは数値として数えない」を明記し、
  base commit の blob に対して数え直した (P1 243 件 / 66 file、P2 260 件 / 66 file)。
  分類台帳 `docs/test-environment-coincidence-ledger.md` の走査述語節に数え方の細目として
  残し、行単位の候補一覧
  `output/insights/2026-08-26_t1848-env-coincidence-inventory.json` を成果物として置いた。
- 再発検知: 台帳の数値は記載した述語でのみ再現できる、と明記した。
  走査述語を記録していない先行の数値との一致を、正しさの根拠にしない。
