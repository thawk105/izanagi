---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1825-rescue-gate
seq: 1
title: [T-1825] 掃除で失われる commit を掃除の前に可視化する道具を作った (コード + docs、Codex resume 監査済み、変異 matrix = baseline PASSED・14/14 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー起票。あわせて [T-1826] (到達不能 object の期限付き台帳と通知) を同じ wave で扱った。
  [T-1828] と [T-1823] はユーザー裁定待ちのため触っていない。
- **段 3 の独立検証 2 本が揃って NO-GO を返し、プラン v1 を捨てた。** 3 点が決定的だった。
  (a) プランの中心 command が git 2.34.1 で動かない
  (`git rev-list --stdin` の stdin に `--not` は置けず `fatal: options not supported in --stdin mode`。
  `^<oid>` なら通る)。(b) 削除候補はほぼ全部 checkout 中で、
  「checkout 中なら判定不能」は道具を恒常的な停止点にする
  (実測: non-main branch 31 本中 27 本、`ahead=0` は 20 本中 18 本)。
  (c) **現行 §2 の `ahead=0` のみ削除という条件の下では、喪失閉包は構造的に必ず空になる。**
  そこへ閉包検査を置くと一度も発火しない。配線先を §1/§5 (棚卸しと報告) へ移した。詳細は {{D:rescue-gate-visualizes-not-authorizes}}。
- **依頼の文言より広くモデルにする判断が、実データで裏付けられた。** 依頼は
  「branch 削除前の rescue gate」だったが、実装は branch 削除と worktree 撤去を
  ひとつの操作として受ける形にした。実測すると
  `worktree-dev-wave-t1629-ratification-broker` は branch だけ消す前提で喪失 0 件、
  その worktree も畳む前提で **12 commit** 失われる。文言どおりに作っていたら
  「失われるものは無い」と報告した直後に `/cleanup-branches` §3 が 12 commit を失っていた。
- **親 brief の数値が 1 件誤っていた。** 自動 gc の余裕を
  「loose 総数 6268 / `gc.auto` 6700 で残り 432」と書いたが、git 2.34.1 の判定は
  fanout 1 ディレクトリの標本であり、実測は `objects/17` が 22 個・閾値
  `(6700+255)/256` = 27 で**残り 5** だった。総数由来の余裕を台帳 schema からも削った。
- **期限契約を実測で作り直した。** 当初実装は packed object を判定不能として rc=2 にしていたが、
  喪失閉包に入る commit 39 件のうち **23 件 (59%) が packed** で、実 repo の過半数で
  「絵を描けない」と返る形だった。3 値化して `conservative-floor` (下界 = 現在時刻、rc=0) を
  新設した。fail-closed の向きは「何も言えない」ではなく「今すぐ失われうる」である。詳細は {{D:conservative-floor-is-a-complete-answer}}。
- **fix 子が 2 回連続で成果物ゼロで停止し、2 回とも子の判断が正しかった。**
  原因は親が「変更してよい既存期待値」を個別列挙したこと。列挙は漏れる。
  契約を一般則で書き直し (期限 3 値の網羅列挙 + 「本 wave が新設した 2 test file の期待値は
  契約へ追随してよい」+ 緩和の明示禁止 + 「矛盾が残ったら 1 件だけ保留して他は全部直せ」)、
  3 回目で全所見が閉じた。恒久対応は {{F:enumerated-test-permission-leaks}}。
- **焦点再レビューが fix 子の申告と 6 件食い違った。** fix 子は全 19 所見を closed と
  申告したが、判定は closed 14 / partial 3 / regressed 3 だった。うち 2 件は防ごうとした
  欠陥の型そのもので、1 件は防壁自身が新しい穴だった (lazy fetch を抑止する wrapper の
  shebang が `/usr/bin/env python3` で PATH 次第の任意実行)。詳細は {{F:guard-wrapper-became-the-hole}}。
- **変異検査が、レビュー 4 本が見逃した穴を 1 件出した。** 新 schema へ無条件 `false` の
  削除許可 field を差し戻す変異が生存した。これはこの wave の出発点そのもの
  (`tools/check_branch_landed.py` の `branch_delete_authorized` が呼び手ゼロの定数のまま
  残っている) であり、同じ形をもう 1 つ作っても誰も気づかない状態だった。
  述語は JSON 全階層を再帰的に見ており正しかったが、**その走行が閉包を作る経路を
  一度も通っていなかった**。詳細は {{F:positive-control-never-reached-the-callee}}。
- 親の実 repo 試走が、レビューでも子の自己診断でも出なかった欠陥を 2 件出した。
  (a) `git worktree list --porcelain` の `locked` field を parser が拒否し、実 repo で
  常に rc=2 になっていた (53 worktree のうち **37 本が locked**)。
  (b) 存在しない候補・`indeterminate` を含む閉包で正しく fail-closed することの確認。
- 採用しなかった所見が 1 件ある。期限付き root が保持する**祖先** commit へ retention source が
  伝播しない件は real だが、向きが「実際より早い期限を表示する」であり閉包からの脱落を
  起こさない。次の一手へ送った。
- 親の運用失敗が 2 件。(a) 待ち手を detach して投げたため完了通知が来ず、
  焦点再レビューの完了 (11:36) に気づかず**約 8 時間空転した** ({{F:detached-waiter-gives-no-completion-notice}})。
  (b) 変異走行中に計算ノードへ投入する検査を重ねて孤児 hold を作った
  ({{F:concurrent-dispatch-during-mutation-creates-orphan-hold}})。対象 job は `child_rc=0` で
  正常終了しており、手順どおり `qdel` を打たず終端を待って解消した。
- **段 8 の自己改善は予算で止めて裁定へ返した。** 実測 2 件 (待ち手の通知経路、変異中の並行投入) を
  `DW-C01` と `DW-M05` へ 1 行ずつ統合しようとしたが、`DW-C01` は現況 996 bytes に対し
  単節予算 1000 bytes で空き 4 bytes、かつ節全体が exact 契約で pin されている。
  `DW-M05` への 80 bytes は L1.5 の unique footprint を 9566 → 9644 にして予算を超える。
  `docs/skill-self-improvement.md` は「予算に収まらなければ reference へ統合し、それでも
  意味等価にできなければ変更を止めてユーザー裁定へ返す。予算値を上げる変更は独立審査対象」と
  定めているので、変更を戻した。両件の恒久対応と再発検知は failures 台帳に入っている。
- 子の工数: codex 子 11 本 (plan 1 / consult 2 / author 2 / review 2 / fix 3 / focus 1)。
  いずれも `gpt-5.6-sol` / `reasoning=xhigh`。うち fix 2 本は成果物ゼロで正しく停止した。
  子は sandbox の制約 (`qstat -Q` rc=1 → dispatch rc=16) で pytest を一度も実走できず、
  全 test は親が実走した。
- **Codex resume 監査で 3 件を追加修正した。** scoped ordinary reflog expiry の欠落、landed report の
  対象 OID 未束縛、ledger 解決 status/field と audit 再報告通知の不整合を Codex author が直した。
  最終焦点 review は先行 3 所見も含め closed / blocker 0 / GO。関連 3 file は 677 passed / 3 skipped。
  final merged tip `d269408cb` の変異は既存 9/9 と新規 5/5 がすべて KILLED、SURVIVED 0、最終
  MISMATCH 0。新規 M34 の初回だけ期待 node 1 件漏れで MISMATCH となり、初回を残して期待完全集合を
  2 node へ訂正し再走した。実 repo dogfood は非空閉包 (10 commit、および別入力 1 commit / landed 1)
  を得たが、共有 repo の root が走行中に動いたため `root-snapshot-moved` / rc=2 で正しく停止した。

## 次の一手差分

### 完了

- [T-1825] `tools/check_branch_rescue.py` として実装し、`/cleanup-branches` の §1/§5 へ配線した。
  掃除で最後の恒久的な根を失う commit を列挙し、着地判定と自動 gc の窓の下界を添える。
  remaining: none
  base: 6bd49377d65aeb60292ac684c15b24fe50a20a3fc7b90c87800149524ad3d204
- [T-1826] `docs/unreachable-object-ledger.md` を新設し、`--ledger-check` で
  `tools/audit_dangling_commits.py` の報告と突き合わせて未記帳を通知する形にした。
  台帳が永久に空でも検出できる。ただし通知が gc の窓に間に合う保証は作れておらず、
  高頻度な発火点の選定を新規項目として起票する。
  remaining: none
  base: dcd02863e441a12576ff6ad71c4b1de3a2204598a75c9bed3243398800c6baa2

### 新規

- {{T:rescue-gate-ancestor-retention}} **P3・新規**: 期限付き root が保持する祖先 commit へ
  retention source と失効下界を伝播させる。現行は完全一致だけを見るため、祖先の期限が
  実際より早く表示される。向きは安全側なので本 wave では実装しなかった。
- {{T:dw-o28-real-cas}} **P2・新規**: `DW-O28` の branch 削除に真の CAS を入れるか裁定する。
  現行の `tools/dev_wave_cleanup.py` は `git branch -d` の診断行を**削除後に**照合しており、
  検査と削除の間に branch が動けば別 tip を消してから気づく。また削除前に
  `git worktree prune --expire=now` を行うため、preview 時の worktree root が
  削除時まで残る保証もない。是正には `docs/dev-wave/operations.md` の DW-O28 本文
  (「branch は `git branch -d` だけで消す」) の変更が要り、D978 の CAS 裁定は
  `/cleanup-branches` を対象として DW-O28 を対象としていない。
- {{T:dev-wave-contract-budget-for-measured-corrections}} **P2・新規**: 実測で得た作法 2 件を
  dev-wave の契約本文へ入れる余地を作るか裁定する。(a) 子の完了を待つ待ち手は通知が届く経路で
  張ること (detach は完了を待たない生産者だけ)、(b) 変異走行中は同一 worktree からの
  計算ノード投入も止めること。前者の宛先 `DW-C01` は空き 4 bytes で節全体が exact 契約、
  後者の宛先 `DW-M05` は L1.5 予算を 78 bytes 超える。無損失圧縮で余地を作るか、
  予算値を上げるか、契約本文へは入れず failures 台帳だけに留めるかの選択である。
- {{T:rescue-notification-firing-point}} **P2・新規**: 到達不能 object の期限通知に、
  gc の窓 (既定 2 週間) に間に合う頻度の発火点を選ぶ。現行は `/cleanup-branches` §1 の
  手動起動だけで、実行間隔を記録から引けない。`tools/check_wave_startup.py` は全 wave 起動時に
  走るが、古い未裁定 entry 1 件で全 wave の起動が止まる形は採れないため、
  非阻止の通知にするか別経路にするかの裁定が要る。
