---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t726-pickaxe-epoch
seq: 1
title: RuleOps の pickaxe を candidate epoch 窓へ限定し、時限の失効条件を機械化した — 空窓の自明合格と receipt range の DAG 穴を敵対レビューが独立に見つけた (コード + docs、受入 8037 passed / 20 skipped / 505.41 秒 / rc=0、変異 8/8 KILLED、branch worktree-dev-wave-t726-pickaxe-epoch)
---

## 本文

- **裁定の一次資料。** rulings-inbox §58 (2026-08-10、発話「推奨通りで」)「[T-726] = (b) 履歴範囲の
  epoch 限定 (時限 5〜11 日)」。command 引数で「時限の失効条件を機械化する」が追加された。
  (a) signal token 上限の引き下げ、(c) preflight 分割、(d) 60 秒定数の引き上げ、(e) 現状維持は
  裁定で不採用。設計は {{D:ruleops-pickaxe-epoch-window}} に記録した。

- **段 1 の前提実測で裁定文の見積りを更新した。** 計算ノードで
  `RULEOPS_MAX_PACKAGE_PREFLIGHT_SECONDS=36.467` / 2,502 commit = 14.6 ms/commit。裁定時の
  見積り (46 秒 / 17.7 ms/commit) より軽く、60 秒までの残余は約 1,610 commit だった。
  commit 増加は 189/日 (直近 7 日) なら約 8.5 日、74/日 (直近 30 日) なら約 22 日で、
  **裁定文の「5〜11 日」より猶予は長い**。決定論的に赤になる事実と (b) の採否は変わらないため
  `DW-S04` の差し戻しはせず、猶予日数を land 判断の根拠に使わない方針で進めた。

- **成果物影響の主張を段 6 で訂正した。** 段 1 brief は「production preflight が赤になる」と
  書いていたが、production ledger は candidates 0 件で `check` は無風である。実際に赤くなるのは
  受入全走に含まれる `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight`
  であり、これが落ちると**全 wave の land 関門が止まる**。レンズ B が指摘し、親が訂正した。

- **段 3 の敵対レンズ 2 本 (sol/luna x max) と段 6 の敵対レビュー 2 本 (sol/luna x high) は
  すべて NO-GO を返し、fix を 3 巡した。** 設計を変えた決め手は次の 2 つで、いずれも
  親の provisional 裁定を否定している。
  - **既定 epoch を捕捉 HEAD にすると窓が空になり、証拠ゼロの package が exact 一致を
    自明に満たす** (段 3 A-01 / B-02 が独立に指摘)。窓が candidate path の最終変更 commit を
    含むことを機械検査する条件を足して塞いだ。既定 epoch も HEAD ではなく
    「最終変更 commit の第 1 親」の導出値へ変えた。
  - **receipt head の「窓 membership」検査では DAG で範囲が有界化しない** (段 6 C-03)。
    epoch より前で分岐した side branch を receipt head にすると `receipt_head..HEAD` が
    窓外の古い main 履歴まで伸びる。`merge-base(epoch, receipt_head) == epoch` へ変えて
    `receipt_head..HEAD ⊆ epoch..HEAD` を DAG でも成立させた。
  - このほか、rename 検出が checkout-local config (`diff.renames`) 依存で受理可否が分岐する
    (C-02) を防護 override の固定で閉じた。read-only probe で config を切り替えると
    pickaxe 出力が変わることをレンズ C が実測している。

- **merge 監査が実害を 1 件止めた。** wave 中に land された [T-720] の import 正準化を取り込む
  際、git の auto-merge は競合を出さなかったが、本 wave 側が足した helper import が
  `from tests import repo_tree_util` の形で禁止経路に該当し、merge 後は test file 全体が
  import 段階で落ちる状態だった。combined diff に実装面 path が残るため `DW-O17` に従って
  Codex `role=author` に merge 結果を確認させ、そこで検出した。**行が重ならない衝突は
  auto-merge が黙って通す**という一般則の実例である。

- **変異は事前登録 8 件すべて KILLED、baseline PASSED。ただし 2 段階の是正を経ている。**
  - 初回走で M1 / M7 / M8 が MISMATCH になった。原因は**親の期待 node の過小予測**で、
    実際には予測より多くの node が落ちていた (検出力は予測より強い)。実測 node を期待値へ
    写した spec で再走して KILLED を得た。初回 ledger は erratum として残す。
  - **M5 の初回 KILLED は偽緑だった** (段 6 焦点再レビューが指摘)。fixture が receipt head の側に
    candidate path の変更を含んでいたため、ancestry gate を外しても既存の `receipt-epoch-path` が
    拒否し、赤くなるのは reason の差だけだった。gate を外すと `check` が rc=0 で通る単一理由
    fixture へ作り替えて再走し、KILLED を得た。**production の検査は 1 行も変えていない。**
  - **M7 (timeout units を全履歴へ戻す変異) は受理集合を変えないので、`DW-M08` に従い
    kill でなく diagnostic sensitivity pin として数える。** 受理境界の kill は 7 件である。

- **受け入れた残余を 2 件明記する。** どちらも敵対レビューが must-fix と判定したが、親が
  `DW-G02` / 規律 5 に従い本 wave の scope 外と裁定した。
  - epoch 以前は検証されない。**候補 file を無関係に更新すれば (コメント追加・mode 変更・
    内容不変の rename でも) 最終変更 commit が前進し、監査地平もそこまで縮む** (C-01)。
    塞ぐには epoch 以前の evidence を凍結受領証として持ち回る必要があり、
    {{T:ruleops-epoch-evidence-checkpoint}} として起票した。
  - 窓へ限定したのは pickaxe だけで、commit 数え上げと control の path 限定 `log` は
    履歴長に比例したまま残る (D-01 / B-05)。内訳の常時計測は行っていない。
    実測 45 秒 guard が総和を見るので、次の律速がここへ移れば先に赤くなる。
  - 併せて、開始時と emit 前の 2 点でしか履歴境界を検査しないため、その間に grafts / shallow を
    作って消す create-use-remove が原理的に残る (段 3 A-05)。本 wave が作った穴ではないので
    {{T:ruleops-history-boundary-race}} として起票した。

- **時限の失効条件は 2 段で機械化した。** 定数側は `1,000 x 6 x 0.005 = 30.0 <= 45.0` と
  `20.0 + 1,000 x 0.035 = 55.0 < 60.0`、および外側 60 秒 literal の `ast` 固定。実測側は
  最大 package の preflight を 45 秒 (外側の 75%) で先に赤くする assertion である。
  一点測定からの線形外挿は保証にならない (A-06 / B-06) ため、**`0.005` は算術 pin 専用で
  runtime 予算には使わない**と production comment と docs に明記した。

- **セッション異常: 同じ [T-726] を受け取った背景 job が 2 本走っていた。** 双方が同じ worktree と
  job dir に入り、handoff を相互に上書きした。先方 (job ad7a196b) から cross-session message で
  説明があり撤退、以後は単独所有で進めた。詳細と恒久対応は {{F:duplicate-dev-wave-job}}。
  先方の独立実測 36.527 秒は本 session の 36.467 秒と 0.06 秒差で整合した。先方が login node で
  測った 3 token 8.7〜9.3 秒 (6 token 換算 52〜56 秒) は計算ノードの値と整合せず、機体差が
  大きいため定数導出にも律速帰属にも使っていない。

- **工数。** codex 子 8 本 (プラン起草 1 / 段 3 敵対 2 / 実装 1 / 段 6 敵対 2 / fix 3 / merge 監査 1 /
  焦点再レビュー 1 のうち sol 6・luna 2)。計算ノードへの dispatch は targeted test 4 走、
  変異 matrix 3 走 (8 件 + 3 件 + 1 件、各 baseline 付き)、前提実測 2 走、受入全走 1 走。
  受入 lease は 21 回の `claim` 後に取得し、待ち手内で local main を取り込んでから投入した。

## 次の一手差分

### 完了

- [T-726] pickaxe の履歴範囲を candidate epoch 窓へ限定し、時限の失効条件を機械化した。
  受入全走 8037 passed / 20 skipped / 505.41 秒 / rc=0、変異は事前登録 8 件すべて期待どおり
  (受理境界 kill 7 件 + diagnostic pin 1 件)。残余 2 件は
  {{T:ruleops-epoch-evidence-checkpoint}} と {{T:ruleops-history-boundary-race}} へ分離した。
  remaining: none
  base: ae403d12fac51a3aad70300d39ddb0d8bf2f8934ea5c09f936fc0d38601400a5

### 新規

- {{T:ruleops-epoch-evidence-checkpoint}} **P2・新規**: epoch 以前の pickaxe evidence を凍結
  受領証として持ち回る恒久機構。現行の窓限定は「epoch 以前を検証せず申告も受理しない」ため、
  候補 file を無関係に更新するだけで監査地平が縮む (段 3 A-01、段 6 C-01)。また現行 blob の
  最終変更が 1,000 commit より古い対象は窓の下限束縛と距離上限を同時に満たせず package 化
  できない。checkpoint 連鎖にすると両方が解ける。設計択一 (受領証の凍結先、連鎖の検証コスト、
  再 review の発火条件) を含むため裁定を要する。
- {{T:ruleops-history-boundary-race}} **P3・新規**: `tools/ruleops.py` は履歴境界 (non-shallow /
  replace refs / grafts 無し) を開始時と emit 前の 2 点でしか検査しない。その間に
  `info/grafts` を置いて全照会を偽 topology 上で走らせ、emit 前までに除去すると両端の検査を
  通る (段 3 A-05)。本 wave 以前からある性質で、窓限定とは独立。全 Git 照会を immutable な
  metadata snapshot か排他区間へ閉じる必要があり、`DW-G02` に従い 1 cycle 後へ送った。
- {{T:wave-startup-detect-duplicate-job}} **P3・新規**: `tools/check_wave_startup.py` は local main
  との乖離と handoff の実在を見るが、**同じ worktree を他 process が使用中かを見ない**。同一
  タスクの背景 job を 2 本起動すると slug が一致するため必ず同じ worktree へ入る
  ({{F:duplicate-dev-wave-job}})。「同一 worktree path を argv に持つ生存 process が自分以外に
  居ない」を fails-closed で検査する。自己マッチと並行 wave の子への誤マッチを避ける照合方法
  (pid 除外、worktree path での一意化) を含めて設計する。
