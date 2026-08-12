---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t922-measure-happypath
seq: 1
title: 測定装置の staged file identity を実体へ束縛し統合経路を 1 本通す — 変異が静的レビュー 4 本の見逃しを捕まえた (コード + docs、branch worktree-dev-wave-t922-measure-happypath)
---

## 本文

- **焦点再レビューは古い前提だった。** [T-922] の正本 (`docs/archive/worklog-phase3-0812-481.md`)
  は [T-866] 段 6 の焦点再レビューを写したものだが、その後 main が 5 commit 進んでおり、
  must-fix 7 件のうち #1 (coordinator→wrapper CLI 結線) と #2 (repo_absence と ready barrier の
  非互換) は**既に閉じていた**。段 1 で現行 main を測り直さなければ、閉じた 2 件を作り直す
  重複実装になっていた。なお台帳の [T-922] 項は焦点レビューの must-fix 7 件のうち
  **#2 を転記していない** (6 件しか写していない)。#2 は残り 1 件目の達成条件だった。
- **本 wave 最大の発見: T-810 測定装置には production producer が存在しない。**
  `launch_intent` / `validator_kwargs` / `admission_policy_path` を**書く**非 test コードは
  repo に 1 件も無く、`.sh` / `.pbs` / `.json` からの coordinator 呼び出しも 0 件。
  これは事故ではなく設計で、D331 が「本 wave は witness の
  発行経路を実装しない、実体は §9.1 item 6 の人間による第 1 段承認 ID」と定めており、
  policy の ratify も [T-923] としてユーザー裁定 deny 中である。
  → 「production 正例経路を 1 本通す」は**実際に走らせる意味では原理的に達成不能**であり、
  達成できるのは「coordinator の production 関数を通って staged wrapper CLI へ到達する統合経路が
  成立し、テストで実行される」ことに限られる。§9.1 item 1 はこれでは充足しない。
- **敵対相談 2 本 (BLOCKER 2 + 7) が親の設計案を 2 度倒した。** 一次資料で全件検算し real と判定。
  (a) 「実 bytes を読んで照合する」だけでは**申告が食い違う入力しか捕まえられない** —
  攻撃者が偽 wrapper とその正しい hash を揃えて申告すれば通る。
  (b) 親の対案「import 済み `pbs_wrapper.__file__` を authority にする」は、
  `tools/pegasus` が `__init__.py` を持たない namespace package のため
  `PYTHONPATH` shadowing で差し替え可能。→ **import 解決ではなく coordinator 自身の
  設置場所からパスで導く**形へ変更した ({{D:t810-shipped-anchor}})。
  (c) 検査を `coordinate()` や `_scheduler_effect()` にだけ置くと、内側の
  `_coordinate_authorized()` / `_subprocess_scheduler()` から迂回できる。
  → 最内の effect adapter と `prepare_group()` 内へ移した。
- **親の裁定が自ら赤を生み、それも敵対レビューが正した。** roots を live git から導く際、
  `repository_roots_from_git_identity()` が並行 wave の worktree 増減で一時的に解決不能な
  登録に当たり、`prepare_group()` を呼ぶ**全テスト 33 件が一斉に落ちた** (同一コードの再走で
  1 件まで減り、親が独立に解決処理を再現して異常 0 件を実測して確定)。
  最初の fix (「解決不能な登録は skip」) は**受理を広げる方向の穴**を作り、
  段 6 レビュー A が「main tree の**外**の linked worktree は主 root で守れない」と指摘。
  → skip をやめ**解決不能でも主張 root を非 strict 解決で保持**する形にした。
  roots に対する操作は `add` のみで `remove` / `discard` / skip が 1 つも無く、単調増加である。
- **変異が静的レビュー 4 本の見逃しを捕まえた。** 段 3 の敵対相談 2 本と段 6 の敵対レビュー
  2 本を通過した後で、変異 M3 (roots の authority を live 導出から caller 申告値へ戻す) が
  **SURVIVED**。機序は等価変異で、fixture が `validator_kwargs.approved_git_identity` に
  live repo の identity をそのまま入れていたため、caller 申告値と live 導出値が全テストで
  一致していた。既存の偽装テストは caller roots 側しか偽装していない。
  → **本 wave の中心的な主張「roots の authority を caller から奪った」を検証するテストが
  1 件も無かった。** 別の実 git repository を自己整合させて申告する負例を足して閉じた。
  再走で 6/6 KILLED / SURVIVED 0 / MISMATCH 0。
- **敵対レビューの提案を 1 件棄却した。** レビュー B は「既存の exact-argv assert を外せば
  変異 M5 が単独帰属する」と提案したが、**検査の弱体化と引き換えなので採らない**。
  `DW-M01` に従い M5 を登録から外し、「既存の強い検査に先取りされている = 二重に守られている」
  と記録した。M4 は M3 と同一 code region で独立適用できないため分離し直した。
- **`guard_bash` が敵対レンズ 1 本を丸ごと殺した。** 子が read-only の hash 計算のために
  `tools/pegasus/` を含む shell command を組み立てた瞬間に「login node で重い処理」として
  機械拒否され、codex が rc=1 / output 0 bytes で終了。model_calls 45、約 1,080 秒を空費した。
  **hook は正しく動作している。** prompt 側に「そのパスを shell で触るな・読取ツールを使え・
  hash の実値計算は不要」を入れて再投入し回収した。同じ機序は稼働中の
  t921-perf-preflight wave でも独立に記録されており、これで独立 2 例目である。
- **編集面の重複はゼロだった。** 起動時にユーザー指定で稼働 worktree 20 本を全数走査し、
  `tools/pegasus/t810_*.py` を触る wave が 1 本も無いことを実測してから実装に入った。
- D328 (凍結チェーン検証の保留) との衝突判定: **保留対象外**。保留 check_id 21 件は
  すべて s8b / known-axes / t080 の測定 provenance 系で t810 の実行認可を含まず、
  D328 本文が admission と信頼境界を対象外と明記している。対象 module は
  `FROZEN_MANIFEST` に hit 0 で凍結 bytes は動かない。新規の凍結 pin 台帳・署名連鎖は
  作っていない。敵対レンズ A も独立に「維持可能」と判定した。

## 次の一手差分

### 更新

- [T-922] **P2・部分実施**: caller 外 authority を要さない範囲を実装した。
  (1) coordinator artifact → staged wrapper CLI: `prepare_group()` が生成した PBS script file
  自体を subprocess 実行し、`--request` parse・静的 request decode・PBS runtime identity 補完
  までを統合テストで確認した。staged package は `PYTHONPATH` に repo を含めずに起動する。
  `coordinate()` / coordinator CLI / qsub / production producer を通る正例は**未確認・未達**。
  (2) staged file identity: **部分実施**。request publication 時と qsub effect 直前に
  宣言 digest と live bytes の一致を要求し、wrapper file は coordinator 同梱
  `t810_pbs_wrapper.py` の bytes へも束縛した。自己整合した任意 binary、staged package の
  依存閉包、qsub 後から node 読取までの TOCTOU は**拒否できない**。
  (3) guard / budget: **未実施**。authority と 2 相結線を裁定へ返した。
  (4) repository roots: **実施**。coordinator の live git identity から main と現存
  linked-worktree roots を導き、caller roots とは和集合にしたため caller は roots を
  増やせるが減らせない。付随して、登録先が既に消滅した linked-worktree entry はその主張 root を
  保持し、symlink / 不正 registration の拒否は維持した。
  残件は {{T:t810-executable-authority}} 〜 {{T:t810-production-producer}} へ分離した。
  base: 211e4f86a6ffb5cbc679c6121308c7ee1fa35fc384121110a834586e1f5569c7

### 新規

- {{T:t810-executable-authority}} **P2・新規・ユーザー裁定待ち ([T-922] 残余 R1)**:
  自己整合した任意 binary を拒否するには caller 外の authority が要る。prereg に binary hash の
  値は無く (`node_hash_checkpoints` は実測 checkpoint であって authority ではない)、
  producer も無い。選択肢は (a) prereg へ binary hash を追加、(b) staging producer を実装して
  そこを authority にする、(c) §9.1 item 6 の承認 ID に hash を含める。着手点は
  `orchestrator/campaign/t810_preregistration.py` の schema 検証と
  `tools/pegasus/t810_coordinator.py` の `_assert_staged_file_identities()`。
  wrapper file の bytes は本 wave で閉じたので、binary だけが残っている。
- {{T:t810-staged-dependency-closure}} **P3・新規 ([T-922] 残余 R2)**:
  staged package 内の `t810_harness_schema.py` / `t810_runner_policy.py` が同梱版と異なる
  実装でも、wrapper file 自身の bytes 一致は通る。選択肢は (a) 依存全 file の manifest 化、
  (b) staged package を使わず承認済み設置物を実行する。着手点は
  `publish_wrapper_request()` と `build_wrapper_request()`。
- {{T:t810-node-read-toctou}} **P3・新規 ([T-922] 残余 R3)**:
  qsub 直前の bytes 一致は node が実際に読む bytes を束縛しない。選択肢は
  (a) node-local copy と hash の後に実行、(b) immutable staging の運用保証。
  着手点は `_canonical_job_script()` と wrapper の `main()`。
- {{T:t810-guard-two-phase}} **P2・新規・ユーザー裁定待ち ([T-922] 残余 R4)**:
  guard producer の production 結線は現 API では**不能ではなく未裁定**。coordinator config の
  7 field に qstat transcript / owner / phase が無く、pre-release の B job identity は
  `submit_group()` 後にしか存在しないため receipt 読取順と矛盾する。snapshot provider、
  submit 後の identity 取得、pre-release 再評価、deny 時 withdraw、receipt schema の 2 相化が
  要る。着手点は `_coordinate_authorized()`、`evaluate_parallel_guard()`、`withdraw_b_group()`、
  coordinator の `_validate_guard_receipt()`。**形だけの結線は偽 allow receipt を通すため禁じる。**
- {{T:t810-budget-canonical-ledger}} **P2・新規・ユーザー裁定待ち ([T-922] 残余 R5)**:
  budget receipt の `ledger_sha256_after` を receipt が指す ledger と照合しても、
  policy が canonical path を持たないため「唯一の予算台帳」との一致にはならない。
  caller は別 ledger に予算を複製できる。加えて「現 ledger 末尾 = receipt after」条件は
  正当な並行 reservation を殺すため chain 内 event 検証が要る。canonical path を policy に
  置くか authority-signed receipt に置くかの択一で、前者は
  [T-923] (deny 中) の admission policy に触れる。
- {{T:t810-production-producer}} **P2・新規・ユーザー裁定待ち ([T-922] 残余 R6)**:
  launch intent / coordinator config / guard receipt / budget receipt / validator kwargs /
  authorization witness を**書く producer が repo に 1 件も無い**。これが [T-922] の
  真の上流 blocker であり、§9.1 item 1 はこれが閉じるまで充足しない。
  択一は (a) producer を新設する、(b) 意図的 dormant のまま §9.1 item 1 を未達に固定する。
  (a) を選ぶ場合の実装範囲は上記 6 種の生成責務と `coordinate()` の呼び出し。
