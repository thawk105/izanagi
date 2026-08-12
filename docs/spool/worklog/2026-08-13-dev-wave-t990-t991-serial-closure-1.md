---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t990-t991-serial-closure
seq: 1
title: 実 repo 直列正本の閉包漏れ 22 node を塞ぎ、read-only 検査の optional index lock を止めた — 検査は AST 案を捨てて閉包 + 実接触 guard の 2 本立てへ (コード + テスト、branch worktree-dev-wave-t990-t991-serial-closure)
---

## 本文

ユーザー依頼「[T-990] (P1) と [T-991] (P2) を実装で閉じてください」の wave。
実装面は Codex author、親は brief・裁定・統合 commit・全走・記録を担当した。

**閉包漏れは 20 でなく 22 node だった。** 親が独立調査で 20 node を特定し、段 3 レンズ A が
1 件を追加し、一貫性から親がさらに 1 件を追加した。系統は 4 つ。

- 系統 1 (1 node): `test_s1_measurement_freeze.py` の positive control が `freeze_env` →
  module scope `real_known_axes_doc` 経由で実共有 submodule source を読む。兄弟 10 node は
  列挙済みでこの 1 件だけ漏れていた。
- 系統 2 (3 node): `prepare_cell` が実共有 submodule を `base_dir` に `patchharness.checkout()` を
  呼び、linked worktree の管理領域を登録・破棄する。
- 系統 3 (17 node): module fixture `benchmark_snapshots` が実 repo を clone し実共有 submodule を
  local source として読む。module scope なので worker 内で最初に走った consumer が払う。
  どれが最初かは静的に決まらないため 17 件全部が対象。
- 系統 4 (1 node): helper が実親 repo と実共有 submodule を clone source として直接読む。

**worklog entry 512 が指していた canary の正体は、conftest が名指しで除外していた node だった。**
`test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` は
`prepare_fn=driver.prepare_cell` (= `s1_direct_comparison.prepare_cell` の re-export) 経由で
実共有 submodule へ到達する。除外註記は「patchharness の隔離 worktree を使い、共有 submodule
worktree を patch しない」と書いていた。**patch しないことは共有資源を変えないことを含意しない。**
同型のずれが系統 1 の除外註記にもあり、どちらも「散文で書いた境界が実装からずれる」型だった。
親は同註記の他方 (`test_campaign.py::test_patchharness_*` は tmp repo) を裏取りして refuted とし、
過剰な直列化を避けた。

**新設検査は 2 度設計をやり直した。** 段 2B が推した「fixture 閉包 + AST 固定点解析」(200〜260 行、
425 file / 15.677 MB を parse) を段 4 で不採用にした。理由は 2 つ。(i) D335 (authority: user) が
file 数比例の新設テストを禁じており、D311 も O(履歴) なら設計やり直しを要求する。
(ii) **その設計は現実の欠陥を実際に取り逃していた** — 段 2B の control は floor module の alias しか
撃たないため、上記 oracle canary (module alias 経路) を検出できない。設計判断は {{D:closure-detector-design}}。

差し替えた案は 2 本立てで、AST を持たない。

- **fixture 閉包の完全性**: 正本に載る node が使う共有 fixture の consumer は全て正本に載る、
  という閉包条件を既存 collection subprocess の report 拡張で検査する。登録簿も AST も持たず、
  正本自身が seed。コストは collected item 数に比例し repo の file 数・履歴・台帳量には比例しない。
- **実接触の runtime guard**: pytest 中に実共有 submodule が `checkout()` へ渡され、呼び出し元 node が
  正本の印を持たなければ fail-closed で停止する。**実行時の実接触を見るため、module alias・
  keyword callable・wrapper forwarding のどれを経由しても捕まる** — AST の伝播完全性問題が原理的に消える。

既知 gap は隠さず記録する。**どの node も正本に載っていない全く新しい共有 fixture は seed が無く
発見できない。** 本 wave が系統 1・3・4 を seed した。

**段 6 の敵対レビューが、親と実装子が両方見落とした穴を 2 つ出した。**
(i) guard は working-tree root の realpath 完全一致で判定していたため、`base_dir=<実 ccbench>/include`
のような **subdirectory を渡すと同じ common-dir を更新できるのに素通り**した。レビュー子が
read-only probe で両者の common-dir 同一を確認している。判定を Git repository identity
(`--git-common-dir` と `(st_dev, st_ino)`) の比較へ変えた。
(ii) **両レンズが独立に**、`source_digest` の env 衛生が `_tracked_status_paths()` だけで、
`resolve_evidence()` が組にする `_tracked_diff_sha256()` / `_git_show()` は親 env 継承のままだと
指摘した。両者の突き合わせは clean/dirty の真偽しか見ないので、decoy `GIT_DIR` を置くと
**status は実 source・diff hash は decoy から取られ、両方 dirty なら整合検査を通過して
別 repository の proof が合成される。この不整合は本 wave の段 5 が作った** (変更前は 3 箇所とも
一貫して親 env を継承していた)。`source_digest` 3 箇所と `repo_tree_util` 2 箇所を統一した。

**受入全走が、敵対レビューが refuted とした所見を real に戻した。** 段 6 レビュー A は
`user_properties` の干渉を検査項目に挙げ「growth-hold は `growth_hold_*` という別 key だけを
追加する」を根拠に refuted とした。これは「当 wave が growth-hold を壊すか」という向きだけの
検査で、**逆向き (growth-hold 契約テストが `user_properties` の完全一致を要求するか) を見ていない。**
1 回目の受入で `test_growth_test_holds_contract.py` が赤になり、実装側 (公開チャネルへ内部印を
載せた設計) を直した。既存テストの期待値は変えていない。失敗型は {{F:one-sided-interference-check}}。

**[T-991] は 2 箇所。** `repo_tree_util._repo_status()` と `source_digest._tracked_status_paths()` が
`git status` を `GIT_OPTIONAL_LOCKS=0` なしで実行していた。両レンズが独立に「排他の緩和ではなく
読取専用性の回復」と判定し、親も `source_digest` の fails-closed 消費経路を確認して支持した。
抑止されるのは status が検査中に更新した stat cache の on-disk index への書き戻しだけで、
working tree と index の比較・status 出力・mandatory lock・非 0 終了の拒否はいずれも不変である。
`silo_ladder_rung1.py` の production 2 箇所は `_ENV_FORBIDDEN_PREFIXES` に `GIT_` があるため
allowlist 追加では効かず `_run()` の scrub 後注入という別形の変更が要るので、
**「受入で到達しないから」を理由に黙って外さず起票した。**

**工数と失敗。** Codex 9 本 (plan 3・consult 2・author 1・review 2・fix 2、`gpt-5.6-sol` /
`gpt-5.6-luna`)。**段 2 の 1 本目は model call 上限 100 で SIGTERM され成果物ゼロで死んだ**
(wall 1412.8 秒)。原因は親が先行調査で確定させた 20 node を prompt へ入れず「網羅的に特定せよ」と
書いたため、子が 1 万行超の test file を読み直して予算を焼いたこと。確定事実を先渡しして
2 本へ分割し直したところ、片方は 18/40 call で完走した。**実装子・fix 子はいずれも pytest を
1 つも走らせられず** (login から dispatch し既定 grace 300 秒が queue 待ちで尽きて rc=16)、
両者とも正直に `partial` / 未実走と申告した。親が `--overall-grace 1800` を明示して全部引き取った。

## 次の一手差分

### 完了

- [T-990] 4 系統 22 node の閉包漏れを塞ぎ、fixture 閉包の完全性検査と実接触の runtime guard を
  足した。変異 8 件すべて KILLED (うち 2 件は detector 自身への変異)。
  remaining: none
  base: 5725042475042233ba631b56530c17ea3dab0ebab4175bc90564fdabe62f8954
- [T-991] `repo_tree_util._repo_status()` と `source_digest._tracked_status_paths()` の
  optional index lock を止め、危険な Git 環境変数 7 個の除去も同ファイル内の計 5 箇所へ統一した。
  段 3 が新たに見つけた production 側 2 箇所は本項の 2 箇所とは別形の変更を要するため別起票とし、
  本項は終端とする。
  remaining: none
  base: 7fd6268992fc97208c7fb397d2f8a2aa1d81929e4728c335e4ad7edb0aa3041a

### 新規

- {{T:sort-oracle-import-contact}} **P2・新規**: `test_sort_swo_oracle.py` は module 直下の
  `_ENVIRONMENT = O.resolve_oracle_environment(_CCBENCH)` で実共有 submodule を読む。
  これは **collection 時の import で全 worker が実行する**ため `REAL_REPO_SERIAL_NODES` では
  原理的に守れない。8 node を正本へ入れると偽の安心を生むので本 wave では入れなかった。
  import 時接触を扱う別機構が要る。
- {{T:silo-production-optional-lock}} **P2・新規**: `silo_ladder_rung1.py:963,2084` の
  pinned-clean gate は production 経路で `git status` を optional lock 付きで実行する。
  `_ENV_FORBIDDEN_PREFIXES` に `GIT_` があるため allowlist 追加では効かず、
  `_run()` の scrub 後へ固定値を注入する形になる。env 衛生契約に触るので独立の裁定が要る。
- {{T:runner-dist-optout}} **P1・新規・ユーザー裁定**: `tools/run_tests.py` はユーザー指定
  `--dist` を既定の `loadgroup` より後勝ちにし、非 loadgroup でも警告だけで実行する。
  さらに `--dist` は受入全走の形として許容される。**pytest 内の閉包検査が緑でも、
  runner 層で実 repo 排他を丸ごと無効化できる。** D63 の opt-out を変えるためユーザー裁定対象。
- {{T:detector-edge-mutation-matrix}} **P3・新規**: 新設 detector の edge (fixture fan-out、
  autouse、param 正規化、import alias、keyword callable、wrapper forwarding、未登録 sensitive-call)
  を 1 本ずつ撃つ完全な変異 matrix。本 wave は fan-out と空集合の 2 edge だけを撃った。
- {{T:real-but-disjoint-classification}} **P3・新規**: 実資源に触るが現 writer と path-disjoint な
  reader の第三分類。read path と writer path の交差を機械で検査する形にする。
  clone reader と sort oracle fixture の扱いがこの境界で決まる。
