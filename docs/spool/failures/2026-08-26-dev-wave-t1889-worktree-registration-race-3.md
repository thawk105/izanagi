---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1889-worktree-registration-race
seq: 3
---

## 新規

### {{F:worktree-registration-scan-has-two-failure-modes}}. 生きた worktree 登録の scan は 2 種の失敗を出すが、台帳は 1 種しか記録していなかった [誤前提] [テスト代表性]

- 事象: F633 は churn 下の失敗を
  `cannot read worktree registration: file is absent` の 1 種として記録していた。
  親が実測すると失敗は 2 種あり、`worktree registration changed while reading` も出る。
  hermetic な churn では 1032 scan 中 798 失敗のうち 57 件 (7%)、実 git の
  `worktree add` / `worktree remove` を反復させた条件では 634 失敗のうち 1 件 (0.16%) だった。
  稀だが到達可能である。
- 根本原因: 消滅は `os.open` の `FileNotFoundError` 経路、読み中変化は読み取り前後の
  dev/ino/size/mtime_ns 比較の経路で、発火点が別である。**`git worktree add` は登録 dir が
  列挙可能になってから `gitdir` が完成する窓を持つ**ため、撤去だけでなく**追加**でも失敗する。
  F633 は撤去の事例しか観測しておらず、消滅だけを吸収する修理案を書いていた。
  その案は 7% (実 git では 0.16%) を取り残す。
- 恒久対応: production は未変更のまま、テスト側を hermetic にして観測される赤を閉じた
  ({{D:worktree-registration-race-is-fixed-in-tests-not-production}})。
  2 種の拒否はそれぞれ専用の負例テストが固定し、変異
  `M5-registration-read-tolerates-absence` と
  `M10-registration-read-accepts-non-regular`、および読み中変化の負例で KILLED を実測した。
  production 側の競合そのものは受理集合を変えるため裁定へ送った。
- 再発検知: 修理案が「消滅」だけを名指しして種別で閉じた条件を持つなら本件である。
  親の実測値 (所要中央値 17.391 ms、最大 808.553 ms、44 登録) と、
  取り直し 3 回でも連続 churn 下で 1.5% 残る点を前提に読む。

### {{F:registered-mutations-had-no-killing-node}}. 事前登録した変異を確実に赤にする node が 1 つも存在しなかった [恒真ゲート] [手順漏れ]

- 事象: 親は段 4 で「登録読み取りの `missing_ok` 化」と「symlink 拒否の除去」を KILLED 期待で
  変異登録した。段 6 のレビューが、その 2 つを決定的に赤にする node が**変更前から存在しない**
  ことを見つけた。hermetic 骨格も実 repository も正常な regular file しか置かないため、
  欠落・symlink・非 regular・登録経路の読み中変化を踏む経路が 1 つも無かった。
  既存の `test_git_common_dir_preserves_missing_registered_worktree_claim` は
  「登録ファイルの欠落」ではなく「登録先 worktree の欠落」を検査する別物である。
- 根本原因: 親が変異位置を「production の拒否がある場所」から選び、
  **その拒否を踏むテスト入力が実在するかを確認しなかった**。DW-M01 が要求する
  「無効化時の赤理由が一つに絞れることをコードで確認する」を、拒否の実在確認で代用していた。
- 恒久対応: 負例 4 件 (欠落・symlink・非 regular・読み中変化) を新設してから変異を登録し直し、
  本走で 4 件すべて KILLED を実測した。さらに DW-M08 の反実仮想走で、この 4 負例を取り除くと
  3 件が SURVIVED に戻ることを実測して寄与を分離した。
- 再発検知: 変異の期待 node 欄を書くとき、その node が**変異前に緑で、変異後に赤になる**ことを
  probe で観測していない場合は本件を疑う。probe を全件 SURVIVED 期待で回すと観測 node が出る。

### {{F:mutation-harness-cannot-classify-setup-errors}}. 変異 harness は fixture で落ちる変異を rc=1 でも分類できず停止する [手順漏れ]

- 事象: 空骨格の変異を投入すると harness が
  `rc=1 だが canonical stdout から failed node を確実に抽出できないため停止` で中止した。
  job stdout を読むと **42 errors / 0 failures** で、全 hermetic node が `when=setup` で
  落ちていた。変異は検出されているのに分類できていない。
- 根本原因: 抽出器は `FAILED ` で始まる行だけを読む。fixture / setup で落ちる node は
  pytest が `ERROR` として報告するため、`-rf` の出力に `FAILED ` 行が現れない。
  rc≠0 かつ 0 件は fail-closed 停止の条件なので、正しく止まっている。
- 恒久対応: 未実施。本 wave では該当 2 変異を登録から外し、親が単発で実測して
  worklog へ書いた (空骨格 = 42 errors / 0 failures、authority 常時失敗 = live 3 node が FAILED)。
  抽出契約を `ERROR` 行まで広げるかは受理集合の変更なので裁定へ送った。
- 再発検知: 変異の効果が fixture・conftest・collection に落ちる位置なら本件である。
  `IZANAGI_FAILURE_DIGEST_ACCOUNT` の `failed=0 errors=N` が証拠になる。
