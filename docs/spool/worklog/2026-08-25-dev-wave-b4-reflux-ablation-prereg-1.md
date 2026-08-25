---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-b4-reflux-ablation-prereg
seq: 1
title: [B-4] 還流 on/off ablation を実行できる形にした。配線は既存で、実証を阻んでいたのは off アームが遮断になっていないことだった (docs + テスト、branch worktree-dev-wave-b4-reflux-ablation-prereg)
---

## 本文

- **wave の前提が起動時の実測で 2 件覆った。** (1) scope (i)「還流 on/off の配線を合流 1 点に入れる」は
  **既に main にある** — `make_critic_digest(reflux=)` が 2026-07-06 から存在し、3 driver とも
  アームが campaign identity で物理分離される (実測: `p3-s4-loop-...-2cd75697` / `...-9f43a5b8` ほか
  6 値)。(2) wave 引数の「`--max-generations >= 2` は D106 残余 1 の裁定まで禁止」は stale で、
  `MAX_APPROVED_GENERATIONS = 2` が実測値、D443 が 8c 系列の世代数を 2 に閉じている。
  ただし段 4/5 driver に generation の概念自体が無く、設計上の結論は変わらない。

- **実証を阻んでいたのは配線不足ではなく、off アームが遮断になっていないことだった。**
  `.claude/agents/critic.md` は critic に `Bash` を与え、入力節が逐語で
  「自分で `digest.py` を走らせてもよい (`--campaign-dir` で rejection 込み)」と**明示的に許可**する。
  同 CLI は reflux 引数を持たず、`make_critic_digest` が渡さない screening 節まで描画する。
  段 3 の 2 レンズが独立にこの点を最重要所見に挙げた。詳細と裁定は {{D:b4-reflux-ablation-estimand}}。

- **親は自分の記述を 3 件撤回した。** (1) 暫定裁定 (P3)「off にも届く共通シグナルは遮断できない
  (遮断するとループが成立しない)」は二択の誤りで、内部 `LoopState` と `check_stop` を維持したまま
  role 向け射影だけを arm 別にできる。2 レンズが独立に指摘した。(2) 待機中に立てた
  「B-4 には機械化された伝達路が無いので実験が不成立」は行き過ぎ — Model Y (D39 決定 7) では
  メインセッションが伝達路そのものであり、ユーザーは 2026-08-03 に段 4 の赤射影 ablation を
  「還流チャネルの ablation として正しい」と裁定済みである。(3)「2026-08-03 裁定が本 wave を
  名指しで実装 wave として委ねた」も誤読で、委任先の所見 6 は 8c の hidden constraint の話だった。

- **段 3 レンズ A が親の実測 1 件を stale と判定し、一次資料で裏が取れた。**
  親は T-244 択一 4 を「未裁定」と記録したが、2026-08-03 に裁定済みだった
  (`docs/archive/worklog-phase3-0803-125-126.md`)。入力側は「赤は常に critic へ渡す」とし
  切替点を「機械が導いた制約の適用有無」へ移す、出力側は `prior_reverse` を停止判定から切る、
  段 4 の既存実装と事前登録 (D39 決定 4) は**当時の架構では妥当**として凍結のまま残す、という内容。
  暫定裁定 (P1)「8c は scope 外」の結論は維持し、根拠を差し替えた。

- **段 3 レンズ A が既知結果の実在を指摘し、確認した。** 2026-07-12 の F 段で実 LLM 駆動の
  還流 on アーム相当が 2 iteration 実走済み (iteration 1 = certified 275,614 tps、critic は
  ノイズ内で帰属不能・逆方向推奨、iteration 2 = certified 276,472 tps、critic は真の tie で
  探索停止推奨)。事前登録に既知結果台帳を置き、**前向き事前登録を名乗らず
  「既知結果に informed された登録追試」と自ら宣言する**形にした。

- **段 3 レンズ B が親の見立て 1 件を訂正した。** 親は既存テスト
  `test_make_critic_digest_reflux_off_drops_red_section` を「fixture 依存で恒真化しうる」と見たが、
  同 fixture は `record_diff_reject()` を明示的に呼び on の positive assert と対になっているため
  恒真ではない。**正しい限界は「出力遮断は見るが loader 非呼出は見ない」ことである。**

- **素材:** 規律 3 の還流と D39 決定 3/7 のリーク制御は、同じ経路を逆向きに引いている。
  還流は critic の帰属で次の合成を良くすることを期待し、リーク制御は毎 iteration
  「機序を planner/coder 入力へ転写しない」ことを自己監査で要求する
  (`docs/phase3-s4b-runbook.md` §1(e) と §2)。実際に通っている帯域は人間ループで
  `prior_critic_reverse` の 1 bit、8c で `uncertainty_present` と `reverse_recommended` の 2 bit だけで、
  8c の `apply_critic_feedback` は docstring 自身が「critic 自由文を捨て、source metrics から
  診断を機械射影する」と書く。**帯域が細いのは欠落ではなく設計だが、事前登録がそれを書かずに
  測れば、差が出なかったときに「還流に価値なし」という偽の negative が論文へ載る。**

- **実走の前提条件として未充足が 4 件確定した。** 閉じた critic invocation、calibrator による
  perf 設定の確定 (`default_perf()` は自ら「性能比較用 calibration ではない」と宣言)、
  対象動作点 (threads=4) の between-run floor (既存は t48 のみ、Pegasus 側は完走 0 件)、
  `prior_critic_reverse` の供給規則。事前登録は発効前 draft として発行した。

- **B-057 (差分 mutation 標準化) が再発火した** (述語 `validator_or_rejection_gate_changed` =
  検査新設)。既裁定の範囲内なので追加裁定はせず記録のみ。**変異 matrix の実施状況は本エントリ末尾の
  実測欄に書く** (実測前に実施済みと書かない)。
  加えて**登録しない既知の生存変異 2 件**を事前登録本文と worklog の両方へ明記した
  (`build_digest()` の別経路、`loop.py` / pipeline の reflux 値分岐。いずれも本 wave の編集面外)。

- **ユーザー裁定待ちを 1 件返す。** 論文 §8 の B-4 欄をどちらの架構で埋めるか。
  2026-08-03 裁定は段 4 の形を「当時の架構では妥当」と過去形で認め、新架構では
  「critic への射影を切っても測れるのは評価の劣化であって機構の効果ではない」と明言する。
  一方その新架構の hidden constraint 機構は存在しない。親の推奨は
  「段 4 の旧形で事前登録し、新架構分は別事前登録に予約する」。

## 次の一手差分

### 新規

- {{T:b4-prereg-architecture-ruling}} **P1・ユーザー裁定待ち**: 論文 §8 の B-4 をどちらの架構で
  実行するか。(a) 段 4 の旧形 (critic への赤の可視性 on/off) — 配線は既存で今すぐ事前登録できるが、
  2026-08-03 裁定が「当時の架構では」と過去形で認めた形。(b) 新架構 (機械が導いた制約の適用 on/off)
  — 現行方針だが hidden constraint 機構が存在せず、択一 7 の本丸 (構造化 anomaly から禁止範囲を
  再導出する契約) が未設計。(c) 両方を別実験・別事前登録として保持する。
  親の推奨は (a) + (c)。正本 = `docs/phase3-b4-reflux-ablation-preregistration.md` §2.3。

- {{T:b4-closed-critic-invocation}} **P2・新規**: B-4 実走の前提条件である閉じた critic invocation を
  実装する。現行 `.claude/agents/critic.md` は critic に `Bash` を与え digest 自己生成を明示許可
  するため、この role を使う実走は off アームとして数えられない。`tools=[]` の critic invocation と
  campaign path 非開示、arm ごとの fresh controller が要る。role file の変更を含むため
  ユーザー承認 gate の対象。

- {{T:b4-role-facing-result-projection}} **P3・新規**: `run_one_iteration()` の戻り値から
  role 向けに赤詳細を落とす型付き projection を設計する。現状は reject 時に `digest`、
  certified/aborted 時に `records` (WAL payload 一式) が載り、sanctioned CLI は表示しないが
  Python API 直呼びには見える。`policy_hint` も無加工で planner payload へ入る。
  広い B-4 主張を成立させるための前提。

- {{T:b4-filedrawer-mechanization}} **P3・新規**: B-4 の全件報告規則を機械強制する
  (事前 manifest・append-only trial registry・WAL との全数照合・report completeness checker)。
  現状は規範のみで file-drawer が開いている。8c 事前登録が同型の限界を記録済み。
