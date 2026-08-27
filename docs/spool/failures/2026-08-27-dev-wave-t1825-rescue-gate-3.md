---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1825-rescue-gate
seq: 3
---

## 新規

### {{F:positive-control-never-reached-the-callee}}. 正例の述語は正しかったが走行が変異箇所を通らなかった [恒真ゲート] [検出力]

- 事象: 新しい道具の出力へ「呼び手を持たない無条件 `false` の削除許可 field」を差し戻す変異が、
  変異検査で生存した。段 3 の独立検証 2 本、段 6 の敵対レビュー 2 本、焦点再レビュー 1 本の
  いずれもこれを検出していない。
- 根本原因: 検査の述語は誤っていなかった。`_all_key_values(payload, ...)` は JSON の全階層を
  再帰的に見ており、field が現れれば必ず反応する。しかしその test 関数の走行が台帳照合だけで
  起動しており、閉包の観測 dict を作る経路を一度も通っていなかった。変異を入れた場所に
  到達しないので反応しようがなかった。
- 恒久対応: 非空の閉包と空の閉包の両方を通す走行を
  `orchestrator/tests/test_check_branch_rescue.py::test_m15_m24_retention_and_authorization_claims_are_absent_or_fixed`
  へ足した。閉包を組み立てる経路は非空側の return と空側の early return の 2 か所あり、
  どちらにも同じ field を差し込める。
- 再発検知: 同 test を期待 node とする変異 M24 を変異 spec へ登録した
  (`tools/check_branch_rescue.py` の閉包観測 dict へ `branch_delete_authorized` を差し込む変異)。
  述語だけでなく、正例がその述語を発火させうる経路を通ることを変異で確かめる。

### {{F:guard-wrapper-became-the-hole}}. 防壁として足した wrapper が任意実行の入口になった [権限] [恒真ゲート]

- 事象: partial clone で `git cat-file` が object を取得しに行き object database を変えうる
  問題への対策として、子孫の git へ `GIT_NO_LAZY_FETCH=1` を強制する wrapper を置いた。
  その wrapper の shebang が `/usr/bin/env python3` だったため、PATH 次第で任意の Python が
  実行される状態になった。read-only を守るために足した仕掛けが read-only を破る入口になった。
- 根本原因: 防壁を足すことに注意が向き、足した機構自身の攻撃面を見ていない。
  実装子はこの所見を `closed` と申告し、焦点再レビューが `regressed` と判定して見つけた。
- 恒久対応: 現に走っている interpreter の絶対 path を wrapper へ焼き込む形にした
  (`tools/check_branch_rescue.py` の子環境構築)。
- 再発検知: 変異 M25 (`GIT_NO_LAZY_FETCH` の強制を外す) を変異 spec へ登録し、
  promisor fixture の全 child env と repo control bytes の不変を検査する。

### {{F:enumerated-test-permission-leaks}}. 変更してよい期待値を個別列挙すると必ず漏れる [手順漏れ]

- 事象: 親が契約 (期限判定を 2 値から 3 値へ) を変えたとき、追随して変わるべき既存期待値を
  個別に列挙して実装子へ渡した。実装子は「期待値が誤りなら実装を変えず停止せよ」の指示に
  忠実に従い、列挙から漏れた期待値に当たって 2 回連続で成果物ゼロのまま停止した。
  2 回とも子の判断は正しい。
- 根本原因: 契約を変えたのに、許可を契約でなく列挙で与えた。列挙は漏れる。
  1 回目は 2 件を許可したが同じ契約に従う別の期待値が残り、2 回目もそこで止まった。
- 恒久対応: 契約を変える裁定では許可も一般則で書く。本 wave で採った形は
  `docs/dev-wave/core.md` の `DW-S04` が定める「gate の禁止は署名で書き、通る正例を 1 つ添える」の
  期待値版であり、(a) 新しい契約の事由を網羅列挙する、(b) 対象 file 集合を範囲で許可する、
  (c) 緩和にあたる操作を明示的に禁止する、(d)「矛盾が残ったら 1 件だけ保留して他は全部直せ」を
  入れる、の 4 点である。
- 再発検知: 実装子が「矛盾がある」と言って成果物ゼロで戻ったとき、子の規律が固いのではなく
  親が許可を列挙で与えていないかを先に疑う。2 回連続の成果物ゼロを親側の停止条件とする。

### {{F:detached-waiter-gives-no-completion-notice}}. detach した待ち手は完了を知らせない [手順漏れ]

- 事象: 子の完了を待つ待ち手を `nohup setsid` で detach して投げた。待ち手は正常に完了したが
  通知が届かず、親は成果物が出ていることに気づかないまま約 8 時間空転した
  (焦点再レビューの完了は 11:36、親が気づいたのは 19:31)。
- 根本原因: 待ち手を detach すると、その完了は親の実行環境の通知経路に乗らない。
  `docs/dev-wave/core.md` の `DW-C00` は「待ち手は 1 条件 1 本」と本数だけを定めており、
  通知が届く形で張られているかを定めていない。
- 恒久対応: 子の完了を待つ待ち手は通知が届く経路で張る。detach してよいのは、
  完了を待たない生産者側だけである。
- 再発検知: 「待ち手を張った」と報告したあとに無音が続いたら、生産者の生存ではなく
  待ち手の完了が自分に届く形かを `.done` と成果物の実在で確かめる。

### {{F:concurrent-dispatch-during-mutation-creates-orphan-hold}}. 変異走行中に別の投入を重ねて孤児 hold を作った [手順漏れ]

- 事象: 変異 matrix の走行中に、計算ノードへ投入する検査 (`tools/check_ai_provenance.py`) を
  重ねて起動した。同一 worktree からの並行投入が孤児 hold を作り、以後の scheduler command が
  rc=16 で止まった。対象 job は `child_rc=0` で正常終了しており、投入自体は成功していて
  受領の紐付けだけが切れていた。
- 根本原因: `docs/dev-wave/mutation.md` の `DW-M05` は「変異中は親の編集と worktree へ書きうる
  子の起動を止める」と定めるが、計算ノードへ投入する検査は「worktree へ書く子」ではないため
  この文言では止まらない。実際には投入の並行性が問題である。
- 恒久対応: 手順どおり `qdel` を打たず対象 job の終端を待ち、qstat 不在・source clean・
  HEAD 一致の 3 条件を確認してから hold を削除した (手動 qdel は F47 の投入停止を武装させ、
  その解除がユーザー手番になる)。
- 再発検知: 変異走行中は worktree への書き込みだけでなく、同一 worktree からの
  計算ノード投入も止める。投入を伴う検査は変異の前後に寄せる。
