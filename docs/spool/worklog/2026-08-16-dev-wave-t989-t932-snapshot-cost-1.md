---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t989-t932-snapshot-cost
seq: 1
title: 受入 wall の最長 node の払い手を定数化し、成長比例テスト 27 件を恒久保留した — 記録の誤りを 2 件、自分で撤回した (コード + テスト + docs、branch worktree-dev-wave-t989-t932-snapshot-cost)
---

## 本文

[T-989] と [T-932] を 1 wave で進めた。両者は同じ面を別方向から触るため、
段 4 で正面から衝突し、親が「保留しない」と裁定した (下記)。

### 親が自分の記録の誤りを 2 件撤回した

段 6 の敵対レビュー B が、親の実測記録の 2 箇所を突いた。どちらも real で、撤回した。

1. **root seal の値を「3 走中央値」と誤表示していた。** commit の本文が 4 つの bullet を
   まとめて「3 走中央値」と導入したが、root seal の 33.64 秒 → 0.38 秒だけは単発計測だった。
   3 走ずつ撮り直すと **26.30 秒 → 0.33 秒**であり、33.64 は 3 走の上振れだった。
   3 走中央値を持っていたのは fixture 全列・`_build_snapshot_base`・derive の 3 量だけである。
2. **「残る律速は copytree 約 8 秒」は誤りだった。** wrapper 会計での分離計測は成分和 12.7 秒が
   全体 8.8 秒を超える内部矛盾を起こしたので採らず、逐次計時で撮り直した。
   実体は **copytree 0.21〜0.24 秒 / case、`verify_snapshot` 3.62〜7.38 秒 / case** である。
   残る費用の 9 割以上は copytree でなく verify である。
   さらに verify の費用は BASE tree に加えて **submodule checkout にも比例する**ので、
   「`BASE_COMMIT` が固定なら固定費」という記述も狭めた。

段 3 の相談でも同型の指摘があり、親の前提実測が段 2・3 の子の稼働中に取られていて
D357 の「測定中は自分の他 job を走らせない」に反していた。静かな窓で全部撮り直した。

### [T-989] と [T-932] の衝突を裁定した

[T-932] の選別子は `benchmark_snapshots` の consumer 3 本を `output_artifacts` 軸で
保留候補に挙げた。親はこれを**不採用**にした。理由は 3 つある。

- この 3 本を保留すると consumer 17 本すべてが skip され、clean な `verify_snapshot` を呼ぶ
  唯一の既定 node が消える。`_one_git_closure_reasons` の reason 集合を守る走行がゼロになる (規律 2)。
- 提示された `output_artifacts` 軸の親実測は **0.13 秒**である。
  35 秒を占めていたのは [T-989] が同 wave で除去した `commits` 軸だった。
- 1 本でも走れば module fixture は丸ごと構築されるので、部分保留は費用を下げない。

この裁定は変異でも裏が取れた。submodule init 削除と seal 削除の 2 変異を殺しているのは、
まさにこの 3 本のうち `test_snapshot_submodule_object_store_is_recursive` である。

### 変異の期待 node を 2 度作り直した

初回登録は 6 件中 4 件が**保留 = 既定 skip の node** を期待赤に指定していた。
D335 の保留が広く効いている repo では、子が挙げた期待 node が skip されて必ず SURVIVED になる。
親が既定で走る node へ再照準した。

さらに probe 走で 2 件が外れた。1 件は node ID の空間違い (`@real-repo` 接尾辞)。
もう 1 件は、seal 呼出の削除が共有 module fixture を **error** にするため、
変異 harness の node 抽出が `FAILED ` 行しか読まず PARSE_ERROR になる問題だった。
DW-M01 の「赤理由が一つに絞れなければ実効 gate へ再照準する」に従い、
新設 node が `index-pack` 直後に sentinel を注入して seal の効果を直接検査する形へ変えた。

### 段 6 レビュー A を 1 度作り直した

初回の prompt が「検知を迂回する構成を作れ」という手順書寄りの形だったため、
codex が rc=1 / 出力 0 bytes で不受理になった (660 秒・40 model call を失った)。
「破れの成立条件を判定せよ」の判定形へ書き直すと通った。
防御目的の明記だけでは足りず、**成果物の形が手順書か判定かで決まる**。

### 背景待ち手の完了通知に偽陽性があった

review-a と fix の待ち手が、成果物も `.done` も無いまま rc=0 相当で終了し、
producer は生存していた。3 点照合 (成果物実在 + `.done` + producer 死) で検出し、張り直した。

### 段 6 レビュー A2 の BLOCKER 1 件は prompt 文言起因で refuted

「skip の追加があれば BLOCKER」と親が prompt に書いたため、
D335 の保留追加 (本 wave の成果物そのもの) が BLOCKER 判定された。
ただし同所見が指摘した `test_ratified_memo_has_a_real_resolution_payer` の**契約反転**
(「毎 session の実 direct payer を守る」→「payer が恒久保留に入っていることを assert する」) は
real であり、保留一覧でユーザーへ提示する。

### 受入が保留の 1 件を差し戻した

受入全走の 1 走目が **11,648 passed / 93 skipped / 1 failed** (pytest wall 80.72 秒) で、
帰属赤 1 件を出した。`test_s8b_floor_campaign.py::test_deterministic_artifacts_across_roots_and_subprocess_environments`
である。原因は本 wave が同 file へ足した保留の guard binding だった。

このテストは**自分自身の module をサブプロセスで
`spec_from_file_location("floor_test_helper", __file__)` として読み込む** characterization test で、
`enforce_held_functions` は pytest 経由でも解除 env でもない読み込みを必ず拒否する。
サブプロセスは別名で読むので `plain_runner` にどの値を与えても通らない。**設計上の衝突である。**

親は **この file の保留を取り消した** (57 → 56)。helper 閉包の切り出しは
`_freeze_document` / `_init_real_clean_repo` など多数への依存があり contained でない。
保留を維持したままテストを通す道が無い以上、通っていたテストを壊さない方を採った (規律 2)。
実 ROOT を `git clone --no-hardlinks` する事実は変わらないので、成長比例の負債は残る。

**この差し戻しは、保留対象を「実行コストの比例だけ」で選んではいけないことを示した。**
guard binding を持てるかどうか (= その file に standalone 読み込みの正規 consumer が無いか) が
保留可能性の前提条件である。段 2・段 4 のどちらもこの条件を見ていなかった。

### 受入 2 回目はフレーク 1 件で受領証が出なかった

2 回目は **11,662 passed / 92 skipped / 1 failed** (pytest wall 91.48 秒) で、
1 回目の赤は消えた。新しい赤は
`test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler` で、
`RESTORED=[15]` を期待するところが `RESTORED=[]` になっていた
(シグナルハンドラの復元が観測されない)。

**本 wave はこの file を触っていない。** 親が同 node を単独走させると
**1 passed / 2.60 秒 / rc=0** で再現しなかった。DW-O18 の
「差分が到達しえない赤は単独再走で実測し、再現しなければ帰属せずフレーク起票する」に従い、
フレークとして扱う。

`check_acceptance_reds.py` は `attributable-red` と判定した。checker は赤を
tested main で 1 回だけ再走して差分へ帰属させるので、**1 標本ではフレークと帰属を区別できない**。
本件は「tested main で緑・wave tip でも単独緑・差分が到達しえない」の 3 点で非帰属と判断した。

### ユーザー提示事項

正しさゲートを担う 27 件を保留した。D335 は提示を要求する。
一覧と各件の付随損失は `output/insights/2026-08-16_t989-t932-snapshot-cost/` に置いた。

### scope 外の real 所見 3 群

段 3・段 6 が出した次の 3 群は本 wave で実装せず起票した。
いずれも本 wave が作った穴ではない。

- `verify_snapshot` が submodule 未初期化を reason 0 件で受理する (既定 spec が
  `submodule_manifest_sha256` を pin しない)。親が実測で確認した。
- `remote.pushDefault` と dangling symlink が closure 検査を素通りする。
- 成長比例テストの母集合が `REAL_REPO_SERIAL_NODES` では閉じない。

## 次の一手差分

### 更新

- [T-989] **P1・実装完了 (残件は受入 wall の帰属)**: `_build_snapshot_base` の
  全 repo clone を `pack-objects` 配管による BASE 閉包限定転送へ置換した。
  静かな窓の 3 走中央値で fixture 全列 43.72 秒 → 20.83 秒、`_build_snapshot_base`
  35.02 秒 → 10.31 秒、root seal 26.30 秒 → 0.33 秒。
  closure の不変条件 (reason 0 件 / object 8,209 / commit 834) は前後で一致した。
  **残件**: (a) 受入 wall への帰属が未確定である。`--dist loadgroup` で real-repo group は
  単一 worker に集約されるが、別 worker が最長なら wall は動かない。
  (b) 残る律速は `verify_snapshot` (3.62〜7.38 秒 / case) へ移り、これは submodule pin の
  前進で増えうる。**「commit 数から完全に切り離した」とは書けない** —
  `pack-objects` は source の object 数に弱く比例する (実測 0.32 秒 対 0.065 秒)。
  base: cd8886a146ce2216cfaea138b1820529e8e30d74df01edf1245f31eed3cd493b
- [T-932] **P1・部分完了 (母集合が閉じていない)**: `REAL_REPO_SERIAL_NODES` 66 件のうち
  未登録の 47 件を選別し、成長比例と判定した 30 件から snapshot 系 3 本を除き、
  さらに受入が差し戻した `test_s8b_floor_campaign.py` の 1 件を取り消して
  **26 件を恒久保留へ登録した** (登録後の総数 56、全件 correctness_gate=True、
  解除条件は explicit-user-command-only)。併せて [T-989] で事実と食い違うようになった
  理由文 14 行の `hold_axis` を `commits` から `output_artifacts` へ訂正した (**解除はしない**)。
  **残件**: 母集合が閉じていない。`test_s8b_ratified_verify.py` /
  `test_check_docs.py::test_real_repo_clean` / `test_s8c_preregistration_invariant.py` /
  silo ladder 2 件は両 registry の外にあり、実 repo subtree を `shutil.copytree` する
  fixture (`test_dev_waves_checker.py` / `test_codex_agents.py`) も探索から漏れている。
  base: ed01fa90c47ecf13241142c1afb5ccaba409177b9dd2e4259a3674115fa0e36b

### 新規

- {{T:growth-holds-residual-sweep}} **P1・新規**: 成長比例テストの母集合を
  `REAL_REPO_SERIAL_NODES` の外へ広げて棚卸しする。先行 wave が「確認済みの追加候補」と
  名指しした `test_s8b_ratified_verify.py` / `test_check_docs.py::test_real_repo_clean` /
  `test_s8c_preregistration_invariant.py` と、段 6 レビューが見つけた
  実 repo subtree の `shutil.copytree` 系 fixture (`test_dev_waves_checker.py` /
  `test_codex_agents.py`) を含める。silo ladder 2 件は先行 wave が t816 land 後の
  再測定へ**意図的に繰り越した**ので、回収前に必ず worklog と archive を確認する。
  探索 primitive に glob / read / Git command だけでなく **`copytree` 系**を入れる。
- {{T:verify-snapshot-submodule-fail-open}} **P1・新規**: `verify_snapshot` が
  submodule 未初期化の snapshot を reason 0 件で受理する。既定 `_snapshot_spec` の key は
  branch / case / forbidden / hashes / head / modes / numstat / tracked_paths / untracked の
  9 個だけで、`submodule_manifest_sha256` を pin しない。親が repo 外 probe で実測した
  (init を飛ばすと `initialization="uninitialized"` として正規に manifest 化され、
  closure reason は 0 件のまま)。既定で走る node の `assert submodules` が現に殺しているが、
  production の verifier 自身は fail-open である。**本 wave が作った穴ではない。**
- {{T:closure-check-symlink-and-pushdefault}} **P2・新規**: closure 検査の 2 つの抜け道。
  (a) `git remote` は named remote しか列挙しないので `remote.pushDefault` は
  `remote remove` の対象にならず検査も通る。(b) `closure_paths` の loop は
  `is_dir()` / `exists()` を使うため **dangling symlink を不在扱いする**
  (packed-refs / grafts / `*_HEAD` が対象)。既存 6 種と本 wave が足した `shallow` で
  挙動は同一なので、本 wave が広げた穴ではない。lstat 基底へ変えるかを裁定する。
- {{T:mutation-harness-error-only-nodes}} **P2・新規**: 変異 harness の
  `_failed_nodes` が短縮要約の `FAILED ` 行しか読まないため、
  **module fixture を壊す変異 (= error だけの走行) から node を 1 件も取り出せず
  必ず PARSE_ERROR になる。** 本 wave はテスト側を実効 gate へ再照準して回避したが、
  同型は共有 fixture を持つ全 suite で起きる。`ERROR ` 行も読むか、
  pytest の `-rfE` と併せて別枠で記録するかを裁定する。
- {{T:hold-guard-blocks-standalone-module-load}} **P1・新規**: 恒久保留の guard binding
  (`enforce_held_functions`) は、pytest 経由でも解除 env でもない module 読み込みを
  **必ず拒否する**。そのため、**自分自身を standalone module として読み込む正規の consumer を
  内部に持つ test file は保留できない。** 本 wave は `test_s8b_floor_campaign.py` で
  受入の帰属赤を踏み、保留を取り消した (`test_deterministic_official_artifacts...` が
  `spec_from_file_location("floor_test_helper", __file__)` でサブプロセスから自 module を読む)。
  同 file の `test_real_seal_protocol_to_floor_official_core_e2e` は実 ROOT を
  `git clone --no-hardlinks` するので**成長比例の負債は残ったままである**。
  解は 2 つある。(a) guard に「module の読み込みは許すが held function の**呼出**だけ拒否する」
  モードを足す (現状の `_wrap_held_function` は既に呼出時 wrap なので、
  module 末尾の一律 raise を条件付きにできる可能性がある)。
  (b) helper 閉包を guard の掛からない module へ切り出す
  (`_freeze_document` / `_verified_freeze` / `_protocol` / `_freeze_sha` /
  `_init_real_clean_repo` / `_make_fake_build` / `_fixture_src_token` /
  `_FIXTURE_CELL_BY_TOKEN` への依存があり contained でない)。
  **併せて、保留候補の選別条件に「guard binding を持てるか」を加える。**
  実行コストの比例だけで選ぶと本件のように受入で差し戻される。
- {{T:signal-restore-node-flakes-under-xdist}} **P2・新規**:
  `test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler` が
  受入全走で非決定的に落ちる。2026-08-16 の受入 2 走目で
  `RESTORED=[15]` 期待に対し `RESTORED=[]` を観測した (シグナルハンドラの復元が見えない)。
  同 node の単独走は **1 passed / 2.60 秒 / rc=0** で再現しない。
  併せて、`check_acceptance_reds.py` が本件を `attributable-red` と判定した点も課題である。
  checker は赤を tested main で **1 回だけ**再走して差分へ帰属させるので、
  **1 標本ではフレークと帰属を区別できない。** 再走回数を上げるか、
  「差分が到達しえない path の赤」を構造的に非帰属へ寄せるかを裁定する。
  現状は親が単独再走して手で判定しており、**受入 lease を 1 本消費してから気づく**。
- {{T:ratified-memo-payer-contract-inversion}} **P2・新規**:
  `test_ratified_memo_has_a_real_resolution_payer` が本 wave で
  「毎 session の実 direct payer を守る」検査から「payer が恒久保留に入っていることを
  assert する」検査へ反転した。payer 自身を保留した以上の必然だが、
  **実 active-generation 解決を一度も実走しない状態でも受入が通る**ことを意味する。
  この受容可否をユーザー裁定へ返す。
