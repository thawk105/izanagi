---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t419-seam-checknet
seq: 1
title: 世代を有効にする根拠を較正 artifact の 4 面へ広げ、床値 protocol の path を authority へ寄せた — 再生される判定に現在値を混ぜる誤りを 2 度捕まえた (コード + テスト + docs、branch worktree-dev-wave-t419-seam-checknet、変異 matrix = 13/13 KILLED、焦点走 1087 passed)
---

## 本文

- **ユーザー裁定 (2026-08-16 /rulings 全件 第 2 回 #3、authority=ユーザー) の実施 wave。**
  択 (c) = 上位の較正・凍結権限束を待たず seam と検査網の補強だけを先に land する。
  環境契約の active 世代は変えていない (activation serial は 1 のまま)。
  設計判断は {{D:activation-admission-artifact-faces}} と {{D:floor-protocol-current-resolver}}。
- **択 (c) が活性化を禁じている以上、受理集合を狭める production gate を置ける位置は
  「次の世代を active にしてよいか」の 1 箇所しかない。** 段 3 の敵対 2 レンズが独立に、
  それ以外の位置は (a) 今日動いている経路を止める、(b) 他層に覆われて帰属が成立しない、
  (c) 今日の受理集合を変える、のいずれかになることを示した。裁定でそこへ集約し、
  走査の拡張は検査網 (テスト層) へ置いた。択一の原文も「seam と test-net の hardening」である。
- **従属問 (i) の扱いを、親が wave の途中で 1 度取り下げて書き直した。** 当初は
  「(i) は D329 (2026-08-12 のユーザー裁定) の反転で、裁定時の未見事実だから丸ごと差し戻す」と
  判断した。段 3 のレンズ A がこれを部分反証した — F339 が実害の中身 (方式改訂で全 attestation が
  落ちる) を既に記録しており、「ユーザーが実質を見ていない」という一般化は成立しない。
  同レンズが第 3 の形 (実行時ではなく活性化の後継判定へ置く) を出し、親はこれを採用した。
  **伏せられていたのは D329 という裁定の存在だけである**という形へ主張を縮小した。
- **親が段 1 で 1 件、実測を誤った。** 「編集面に source bytes を pin する live な trust root は
  0 件」と書いたが、`campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` が編集対象 3 file を含む
  exact 12 path の enforcement source closure として実在する。段 3 のレンズ A が反証し、
  親が独立に確認して訂正した。該当形式の campaign.lock は 32 件中 0 件なので既存再開は壊れない。
- **段 6 のレビューが land 阻止の本物の欠陥を 1 件出した。** 方式名の判定を可変な現行 probe 定数と
  比較していたが、activation chain は読み込みのたびに過去の全遷移へ後継判定を再適用する。
  probe を改良すると既に有効な過去の遷移が落ち、authority 全体が読めなくなる。
  fix で「再生される 3 面」と「発行時だけの方式名 1 面」に分けた。
  **親が fix 1 巡目の差分を読んで、同じ欠陥が発行経路に残っていることを追加で見つけた** —
  発行 tool は既存記録を含む chain 全体を検証するため、記録が 2 本以上になると同じ形で詰まる。
  2 巡目で「後継がまだ ever-active でない遷移だけ」に限定した。教訓は
  {{F:replayed-gate-against-mutable-constant}}。
- **焦点走の赤 30 件のうち 26 件は未 commit の編集そのものが原因だった。**
  enforcement source closure の 12 path は disk bytes が HEAD blob と一致することを要求するため、
  編集中は campaign lock を作る系のテストが機械的に赤くなる。統合 commit の後に同じ範囲を
  再走して 26 件が消えることを実測し、真の赤 4 件と切り分けた。
  {{F:uncommitted-edit-red-in-enforcement-closure}}。
- **真の赤 4 件は fixture の適応漏れで production の欠陥ではなかった。** 2 件は実在の登録を使いながら
  repo root を空の一時 directory へ差し替える型、2 件は較正が存在しない架空 65 環境の規模テストである。
  前者は一時 root へ実在の較正を配置して判定を実際に通す形で、後者は artifact 判定の部分だけを
  名前のある seam で隔離し production の既定が composite であることを同じテストで確かめる形で閉じた。
  **判定を迂回して緑にしたものは無い。**
- **変異 matrix は 2 回走らせて 13/13 KILLED、SURVIVED 0。** 1 回目 (13 件) は KILLED 3 /
  MISMATCH 10 で、**MISMATCH はすべて「期待より多く落ちた」側**である。原因は、closure の 12 path を
  変異させると注入自体が `contract-loader-drift` を起こして `test_campaign.py` の約 25 件を
  巻き込むことで、狙った検出が過剰決定になる。2 回目は対象集合からその file を外し、
  1 回目の実測 node 集合をそのまま期待値に再登録して 10/10 KILLED / MISMATCH 0 を得た。
  `test_campaign.py` を要する 3 件は 1 回目が期待値と完全一致の KILLED であり、そちらが権威である。
  台帳は `output/insights/2026-08-16_t419-seam-checknet/` に 2 本とも残した。
- **main の取り込みを 2 回行い、両方で Codex role=author が合成を監査した。** 競合はどちらもゼロ
  だったが 3 方向結合の結果は両親と異なる。1 回目は merge-base から各親への差分と反対側の親から
  合成結果への差分の stable patch-id が両 file・両方向で一致すること、2 回目は合成が
  「main 版 + 本 wave の +81 行 (削除ゼロ)」であることを確かめ、いずれも編集ゼロで「正しい」と判定した。
- **背景待ちの異常が 3 度あった。** `dev_wave_wait.py producer` が 2 回、出力に自分の echo 行を
  残さずに即死し、Monitor が 1 回**偽の完了イベント**を出した (完了印が存在せず子は生存していた)。
  いずれも 3 点照合 (成果物実在・完了印・producer の生死) で検出して張り直した。
- **この wave が保証しないこと。** 床値 protocol の seam は preflight admission までである。
  shell wrapper と 5 module は literal path を持ったままで、配線そのものは裁定へ返した
  (literal が resolver の結果と一致することを固定する検査だけを置いた)。
  acquisition receipt の検査は artifact 内部の自己整合であり外部の取得証明ではない。
  活性化の後継判定は今日 production で一度も呼ばれず、発火するのは次の世代交代からである。
- **エージェント工数**: codex 子 9 本 (plan 1 / consult 2 / author 2 / review 2 / fix 2) に加え、
  main 取り込みの合成監査 2 本。

## 次の一手差分

### 更新

- [T-419] **P1・択 (c) を実装して land 済み。残る 3 件がユーザー裁定待ち**: 世代を有効にする根拠を
  較正 artifact の 4 面 (自己整合・方式名の実体一致・content-addressed path・取得記録の内部束縛) へ
  広げ、方式名だけを発行経路かつ「後継がまだ ever-active でない」場合に限定した。
  床値 protocol の path は authority resolver 経由にし、再読 bytes を SHA で再照合するようにした。
  検査網の走査は active view の 2 件から登録済み 3 件へ広げた。活性化はしていない。
  **返した 3 件** — (1) 実行時 attestation の `effective_clock.method` を実体一致にするか
  (D329 の可否。実装すると pegasus の全 attestation が即座に落ちる)、
  (2) 既に ever-active な第 1 世代の自己不整合の扱い (実測で、歴史 resolver は歴史成果物専用ではなく
  live campaign の COMMIT 監査を含む 6 consumer に載っており、gate を置くと今日の経路が止まる)、
  (3) 床値 path の shell 層・driver 層の配線。
  一次資料 = `output/insights/2026-08-16_t419-seam-checknet/ruling-package.md`。
  base: 4ff137bae9046590e871d5328f578a8c082aa528ca3ea081e1ebc7619176214e

### 新規

- {{T:waiter-spurious-return-mechanism}} **P2・新規 (F355 の再発検知条件が成立)**:
  `tools/dev_wave_wait.py producer` が producer 生存・完了印不在のまま出力ゼロで rc=0 終了する
  事象の 2 例目が出た。F355 の再発検知は「2 例目が出た時点で機序を特定し、待ち手側の
  fails-closed 検査として実装する」と定めている。機序を特定し、
  **完了印の実在と producer の死亡を待ち手自身が検査して、満たさない終了を非 0 にする**
  形を入れる。本 wave では scope 外として実装していない。
