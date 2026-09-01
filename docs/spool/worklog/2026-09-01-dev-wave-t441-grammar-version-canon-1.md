---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t441-grammar-version-canon
seq: 1
title: [T-441] backoff 受理文法の版を identity/WAL/cache へ束縛し、hole の数値表記を正準化した (コード + テスト + insight、branch worktree-dev-wave-t441-grammar-version-canon、変異 12/12 KILLED)
---

## 本文

- 一次資料は `output/insights/2026-09-01_t441-grammar-version-canon/`。段 2〜6 の逐語、
  段 4 と段 6 の裁定、変異 spec と集計、事前登録の erratum を置いた。
- **依頼の前提が実測で 1 件覆った。** 依頼は「未実装なのは受理文法への initializer-literal と
  statement-count の追加」と述べていたが、着手時点の local main で両方とも実装・執行済みだった。
  親が validator を実走して確認した。実際の残件は D901 条項 2 (版束縛) と条項 3 (正準化) であり、
  依頼の他の記述 (裁定の指定、「版束縛と数値正準化を同じ変更単位に」) とは整合する。
  `0x14` と `2e1` が受理されることが条項 3 の未実装を実証した。
- **親の provisional 裁定が 2 件覆った。** P2 (正準化は台帳記録側だけ) は、段 2 のプラン子と
  段 3 の 2 レンズが独立に「source bytes が分かれたままで重複が畳まれない」と指摘したため撤回し、
  材料化時の正準化を採った ({{D:backoff-canonicalize-at-materialization}})。
  P4 (新規 test file) は、稼働中 wave の hunk 位置を実測して衝突しないと分かったため撤回した。
- **プランの中心案を 1 件差し替えた。** 版束縛を編集 path の dirty 判定で行う案に対し、
  段 3 の 2 レンズが独立に、同じ path を材料化する別 producer の実在を名指しした。
  campaign 由来の版を明示引数で渡す形へ替えた ({{D:backoff-grammar-version-explicit-campaign-arg}})。
- **段 6 で最も重かった所見は 1 レンズだけが挙げたものだった。** 共有 reject helper の既定が
  `None` でなく backoff の版になっており、版を渡さない 7 箇所の呼び出しまで巻き込んでいた。
  親が呼び出し元を独立に数えて裏を取ってから fix した。
- **scope 外の real 所見を 1 件、実装せず裁定へ残した。** 拒否候補の台帳 token が綴りで分かれる件は
  実在するが、D901 の理由が certified 選択の母集合に限定されること、拒否入力へ値抽出器を
  走らせる攻撃面を新設すること、成果物の値・受理集合・参照を変えないことから
  scope 外とした ({{D:backoff-reject-ledger-duplication-deferred}})。
- **変異の事前登録から 2 件を外し 2 件を足した。** 凍結した M7 と M12 は、実装確定後に
  注入点を実コードで探した結果どちらも該当コードが存在せず、変異が「既存文字列の置換」でなく
  「新機能の追加」になるため外した。代わりに段 6 の fix が新設した 2 つの防壁を登録した。
  理由は `mutation-erratum.md` に残した。
- **赤の帰属を 2 回、実装から切り離した。** 焦点走の初回 52 件は全件が `contract-loader-drift` で、
  HEAD blob 束縛 file を未 commit のまま走らせたことによる。変異本走の 3 回の停止は
  待ち行列の時間切れ、前回の残骸、収集段の受領証欠落であり、変異の内容は 1 件も変えていない。
- **実装子は pytest を 1 件も実走できなかった** (Pegasus dispatch の rc=16)。緑とは申告せず
  「実装済み・未実走」と報告した。テストの実測はすべて親が login node で行った。
- **受入全走の 1 回目で 9 赤が出た。9 件とも自分の差分に帰属する。** 焦点走の対象から
  B-4 系の 3 file が漏れており、`DW-O26` が警告する取り逃しの型そのものだった。
  内訳は、版付き lock を書いた直後に版を渡さず reject を記録していた配線 probe (8 件) と、
  `search_config` の key 集合を exact に固定していたテスト (1 件) である。
- **版検査は wave 中に 4 回発火し、4 回とも緩めずに呼び手側を直した。** B-4 の履歴 fixture、
  closed critic の fixture、配線 probe の 3 経路はいずれも「版付き lock を書くのに版を渡さない」
  同じ形で、production は lock 確定後に版を明示して呼ぶ。検査の省略・skip・lock の legacy 化は
  1 件も採らなかった。
- 実測値: 変異 12/12 KILLED・期待 node と完全一致・SURVIVED 0・MISMATCH 0、baseline は rc=0 失敗 0。
  焦点走は `test_p3_s4_loop.py` 単独 340 passed、main 取り込み後の 6 file で 1209 passed / 3 skipped。
- wave 中に local main が 66 commit 進み、起動時の編集面重複検査で名指しした [T-1999] が着地した。
  競合なしで自動 merge されたが、Codex role=author の合成監査を独立に走らせた。
  must-fix と should-fix はゼロだった。
- D942 の C1 (条項 2 が land するまで新しい自律 backoff campaign を走らせない) は、
  本 wave の land で解ける。C2 の「D836 の閉鎖であって D901 の完了ではない」は本項で解消し、
  D901 は 3 条項とも着地した。

## 次の一手差分

### 完了

- [T-441] D901 条項 2 (文法の版を identity・WAL・cache へ束縛) と条項 3 (hole の数値表記の
  正準化) を実装し、変異 12 件と焦点走で裏を取った。D942 の C1 が解け、D901 は 3 条項とも着地した。
  remaining: none
  base: 8ebe84f2fc93806406511f98801cd335ccea2a543be4bb047d1215aa46e9e769
