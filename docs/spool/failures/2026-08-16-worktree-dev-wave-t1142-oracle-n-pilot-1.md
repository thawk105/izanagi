---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: worktree-dev-wave-t1142-oracle-n-pilot
seq: 1
---

## 新規

### {{F:acceptance-burns-lease-on-unlandable-tip}}. 受入は land が要求する全史 provenance 監査を回していなかったため、land 不能な tip で lease を消費し 11,000 件超のテストを走らせていた [防壁の破れ] [検査の非対称]

- 事象: [T-1142] の wave で受入全走を **7 回**回した。うち少なくとも 1 回は
  land が構造的に不可能な tip で、受入は緑・受領証も発行され、**land で初めて赤**になった。
  親はその rc を並行 wave の混雑と誤分類して land を計 **42 回** (31 + 11) 空転させた。
  制御面を実測すると 80 秒間まったく動いておらず (18 サンプル、変化 0)、混雑説は反証された。
  真因は `land2.log` 最終行の
  `"reason": "provenance full-history audit rejected the wave (rc=1)"` に書いてあった。
- 根本原因: 受入経路 (`tools/dev_wave_wait.py` の `run_acceptance`) は lease 取得後に
  `git merge --no-ff --no-commit main` を行い、続けて
  `check_ai_provenance.py --message-file <msg>` を回していた。**この呼び出しは merge message の
  trailer 書式しか検査しない。** land が `DW-O25` / D254 で要求する全史監査 (引数なし) は
  受入経路に 1 度も存在しなかった。**受入の関門と land の関門が非対称**であり、
  受入を通っても land を通る保証がないという構造だった。
  違反を生んだのは受入自身が作る main 取り込み merge (`21582897ece7` / `a8c73d747621`) で、
  実装面 path の 3 方向結合結果が両親のどちらとも異なるため checker が実装面著作と判定した型。
- 波及の広さ: 受入 lease は 1 wave あたり TTL 2400 秒で、同時刻の待ち行列は 6 wave、
  待ち時間は 11〜50 分 (別セッション実測)。**land 不能な tip での 1 走行が、
  後続 5〜6 wave を待たせる。** 全史監査の実所要は 45 秒 (3,727 commit 時点) / 28 秒
  (3,752 commit 時点) であり、失われる時間との比は 2 桁違う。
- 族としての一般化 (DW-G03 が要求する独立 2 例): 別 wave t1180-pilot-approval が同日 20:50 JST に
  **lease 取得後**に rc=70 で落ちた。原因は「main が 13 commit 進んでいて
  `--merge-message-file` が必須になっていたのに渡していなかった」で、**テストは 1 件も
  走らないまま lease 窓を 1 つ捨てた**。原因は別だが「lease を取ってから落ちる」点が同型。
  共通の性質は、**判定材料が main の進み具合に依存するため投入時点の argv だけでは決まらない**こと。
- 恒久対応: 判定を 2 箇所へ入れた。位置が意味を持つ。
  - **claim 前** (`preclaim-behind-count` / `preclaim-history-provenance`): main の進み具合に
    よる `--merge-message-file` の必要性判定と、全史監査。**wave tip の履歴に既に存在する
    違反**を捕まえる。[T-1142] が実際に踏んだのはこちらで、claim 前に叩けば lease を
    取らずに落ちていた。
  - **merge 後・受入投入前** (`merge-history-provenance`): 全史監査。**その merge 自身が
    新しく作る違反**を捕まえる。claim 後にしか置けない (違反はまだ存在しないため)。
  どちらも失敗時は受入コマンドを投入せず、`_StageFailure` から既存 cleanup が
  `git merge --abort` と lease 解放を行う。想定外 rc も fail-closed。
- claim 前でなければならない理由 (実測): 待ち札は claim の試行時に作られ
  (`tools/wave_land_window.py` の `_create_ticket` / `_open_ticket`)、**稼働中の process の
  heartbeat でしか生き延びない** (`_WAITER_TTL_SECONDS = 300`)。claim 後に落ちると、親が
  直して再投入するまでに 300 秒を超えるので**札は必ず刈られ、先着順位を失う**。
  実例として t1180 は札を作り直して先着順位を 52 分ぶん失っている
  (`queued_at_ns` が 20:50:17 → 21:42:28 に書き換わったのを実測)。
  したがって「claim 後に落として札を残す」という選択肢は実在しない。
- 検出: `orchestrator/tests/test_dev_wave_wait.py` に、監査が赤のとき
  **受入コマンドが 1 度も実行されないこと・lease が解放されること・理由本文が返ること**を
  同時に主張するテストと、claim 前判定について **claim が 0 回・lease dir が空**
  (待ち札が作られない) ことを主張するテストを置いた。想定外 rc の fail-closed も固定した。
- 再発検知: 上記の 4 テスト。**「受入が緑だった」を「land できる」と区別する**ため、
  検査の緑ではなく **`submissions == 0` (受入コマンドが実行されないこと) と
  `claims == 0` / lease dir が空 (待ち札が作られないこと)** を固定する。
  受入が実際に走ってしまったかどうかは受領証の有無からは判別できないため、
  呼び出しの不在そのものを主張する形にした。
- 副次的教訓 (規律ではなく機械で縛った理由): 親は rc を自前分類して 42 回空転させ、
  受入全走 7 回のうち少なくとも 1 本を捨てた。ユーザー裁定は
  「二度とそんな無駄を繰り返すな。すべてのセッションに対して許さない」
  「すべてのセッションを調教しろ」であり、prompt 規律では 1 セッションしか直らないため
  受入経路そのものへ関門を入れた。**rc だけでなく理由本文を呼び手へ返す**のも同じ理由で、
  rc だけ返すと次の呼び手が同じ「rc を自前分類する」ループを書く。
