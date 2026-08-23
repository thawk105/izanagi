---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1497-conditional-unrun-premise
seq: 1
title: [T-790] 条件付き未実走と g++-13 skip の「開けない前提」を実測し、律速が pinned compiler の在庫でないことを示した (コード+テスト+docs、branch worktree-dev-wave-t1497-conditional-unrun-premise、変異matrix = baseline PASSED・MUT-1〜3 3/3 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「[T-1461] の staged FetchContent と pinned toolchain で前提が変わった可能性がある」の
  検証だった。**その仮説は反証した。** `orchestrator/qualification/submission.py` の
  `prepare_toolchain()` は `shutil.which("g++-13")` で PATH 上の実体を解決して realpath と
  sha256 を記録するだけで、compiler を導入する経路を持たない。[T-1461] の staged FetchContent は
  masstree / mimalloc / googletest の**ソース**転送で compiler は対象外。[T-747] も env contract
  への toolchain **束縛**であって在庫供給ではない (完了文が「残る非束縛量 (cxx version / ...)」と
  明記)。login node 実測で g++-13 不在 (在るのは g++-9 / g++-11 / g++-12)、`module avail` の
  compiler 系は cuda / intel / nvhpc のみ、`/opt`・`/usr/local`・spack・conda いずれにも無し。

- **しかし裁定が乗っていた前提そのものが偽だった。** README は「費用対効果が pinned compiler の
  在庫に依存する」を根拠に窓を開けない裁定を投影していたが、
  `buildcache.compilers_for_current_site()` は site が Pegasus compute のとき `("gcc", "g++")` を
  返す。**本番 campaign は計測ノードで素の `g++` を使っている。** テストだけが `"g++-13"` を
  literal で要求し、production より厳しい条件で自分を塞いでいた。この指摘は段 3 の敵対相談子が
  出し、親が `buildcache.py` の実コードで裏取りした。

- 実測 A (再現)。template patch を campaign 本番経路 `patchharness.applied()` で隔離 worktree の
  実 submodule へ適用して 4 node を実走したところ、README の記述どおり実効回収は 2/4 で、
  `test_source_digest_fixed_variant_distinct` だけが `_require_g13()` 相当のガードを持たず
  `source_digest.py:957` で未捕捉 `RuntimeError` = 赤になった。適用後 tree は
  `git status --porcelain` 空で復元。

- 実測 B (核心)。patch 適用状態で pinned でない **g++-12** を渡すと、
  `fixed_variant_distinct` の主張 5 件 (`-1` は stock へ正規化 / `t50 != STOCK` / `t10 != STOCK` /
  **`t50 != t10` = alias 防止** / `variant_id` が分かれる) がすべて成立し、
  `failsclosed_on_missing_define` の供給漏れ停止も `#error "BACKOFF_FIXED must be defined"` で
  `RuntimeError` に落ちた。さらに g++-13 ガードを持つ**依存物不在 skip 群 6 件全部**を、PATH へ
  `g++-13 → g++-12` の symlink を置いた probe process 内で直接呼んだところ**全件 PASSED**
  (合計 11.25 秒、うち `stock_roundtrip` が 9.92 秒)。D34 が digest の値を pin しない仕様と
  明記しており、これらのテストは**関係**しか主張していないため整合する。repo には同じ論理の
  先例 `_any_cxx()` (`test_campaign.py:11459`) が現に緑で走っている。

- 実測 C (ルート A の費用)。[T-790] 起票文は「受入全走が submodule clone のコストを毎回払う」と
  していたが、`patchharness.checkout()` の実体は `git worktree add --detach` である。実測 3 回
  中央値で add 0.05s + `git apply` 0.004s + remove 0.01s = 0.07 秒/サイクル。残存 worktree なし。

- **段 3 の敵対相談子 (codex read-only) が親の数値を 3 点訂正し、親は全部採用した。**
  (a) 4 node の単発実走は scheduler=serial の別 subprocess で、xdist 受入全走の代理になっていない。
  (b) 「約 2.2 秒」は追加所要ではない — 現行 skip の所要を差し引き window 開閉を込めた同配置の
  差分は約 +0.51 秒で、それも全走の予測ではない。(c) 「実 submodule 変異 0→4」は未定義 —
  suite 内の `patchharness.applied()` 4 字句は全部 `_fake_ccbench_repo()` の偽 repo 対象だが、
  うち 1 件は dirty-tree 拒否で apply へ到達しないので成功 window は 3 回であり、新規側も
  4 node を 1 window で包むか node ごとに 4 window 開くかで費用と危険面が変わる。
  `REAL_REPO_SERIAL_NODES` 所属は「追加ペナルティ 0」を意味しない。

- 子の所見のうち real として採用した caveat 3 件。(1) `_any_cxx()` を「版非依存」と断定しては
  ならない — source digest は compiler builtin を意図的に取り込むので、合成枝が
  `#if __GNUC__ < 13` のような builtin 条件を使えば関係まで版依存になりうる。上の実測 B は
  **現行 source での実測一致**であって将来の保証ではない。(2) 偽 ccbench repo は実 patch /
  実 CMake 供給 / 実 EBS 全体との統合面を代替しない。(3) hook は designated source の内容を
  検査しない契約なので、`_SKELETON` と実 patch の drift 照合には成果物検出力が無い。
  親が段 1 で出した偽 repo 案は (2)(3) により取り下げた。

- **本 wave で実装したのは 2 点だけ。** (a) `test_source_digest_fixed_variant_distinct` への
  `_require_g13()` 追加、(b) それを ast で機械固定する
  `test_skip_classification.py::test_conditional_preprocess_nodes_require_g13` の追加。
  検査集合は preprocess を駆動する 2 node だけで、compiler を要さない 2 node は入れていない
  (過剰拒否の回避)。実測で修正前 `2 passed / 1 skipped / 1 failed (rc=1)` → 修正後
  `2 passed / 2 skipped (rc=0)`。**受入 suite の受理集合は変えていない** — この 2 node は
  patch 未適用のため `skip_conditional_unrun()` で先に弾かれ、今日の挙動は不変である。

- 変異 matrix は MUT-1 (追加したガードを削除 = 変更前 HEAD の状態)、MUT-2 (もう一方の node の
  ガードを削除)、MUT-3 (compiler 不要 node を検査集合へ足す = 恒真化の否定) の 3 件で、
  baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0。期待 node は 3 件とも完全一致。
  MUT-1 が KILLED であることが `DW-M08` の求める新旧差分そのもので、本 wave の純増検出力を示す。

- **規範 compiler の裁定と [T-790] の再裁定はユーザー手番として返す** (`DW-S04`)。
  g++-13 依存 skip 群の版非依存化はその裁定に従属するので実装していない。

## 次の一手差分

### 更新

- [T-790] **P2・再裁定待ち (2026-08-23 実測で裁定前提が覆った)**: 2026-08-16 の裁定
  (ルート A = 隔離 checkout) を維持するかを再確認したい。新事実は 3 件。(1) ルート A の実効回収は
  4 node 中 1 node にとどまる — 隔離 checkout は g++-13 を生まないので
  `fixed_variant_distinct` と `failsclosed_on_missing_define` は依存物不在 skip のままで、
  `test_real_submodule_payload_edit` は `_REPO/external/ccbench` を直接読む (`test_hooks.py:1342`、
  `GW.decide` に `repo_root` を渡していない) ので submodule だけの隔離 tree には届かない。
  (2) ルート A の費用は `git worktree add --detach` の 0.07 秒/サイクルで、起票時の
  「submodule clone のコストを毎回払う」より 1 桁小さい。(3) 律速は compiler 在庫ではない —
  pinned でない g++-12 で 2 node の主張も g++-13 依存 skip 群 6 件も実測で全部通る。
  したがって択一はルート A / B ではなく、先に規範 compiler を決める問題に変わった。
  base: d4f35b3283dfe8ea03a06f44da47b4265d8f855537394f8914b095f2aceb5f54

### 新規

- {{T:norm-compiler-for-acceptance}} **P1・新規・ユーザー裁定待ち**: 受入検査の規範 compiler を
  決める。現状は qualification 系が exact `g++-13` を規範とし (`submission.py` の
  `prepare_toolchain`)、Pegasus 計算ノードの campaign 系は
  `buildcache.compilers_for_current_site()` により素の `g++` を使う。テストは前者に合わせて
  `"g++-13"` を literal で渡すため、どちらのノードでも走らない。選択肢 =
  (a) テストを site compiler へ寄せる (`_any_cxx()` 系。skip 8 件が実走に変わる。実測で全件緑、
  追加所要 11.25 秒) / (b) exact `g++-13` を規範に据えたまま在庫を用意する /
  (c) portable な unit 検査と規範 compiler 束縛の integration 検査を分離する。
  推奨 = (c) — 実測 B は現行 source での一致であって版非依存の保証ではなく、builtin 条件を
  使う合成枝が入れば関係まで版依存になりうるため。決定は cache identity と受理集合に効く。
- {{T:s1-fake-repo-missing-mocc}} **P2・新規**:
  `orchestrator/tests/test_s1_direct_comparison.py` の `_fake_ccbench_repo` が
  `cc/mocc/transaction.cc` を作らない。[T-755] (`ae958491`) が `EVOLVE_BLOCK_SOURCES` へ mocc を
  加えたのに追随しておらず、g++-13 がある環境では
  `test_real_source_digest_unifies_all_outer_whitespace_tokens` が
  `RuntimeError: ... cc/mocc/transaction.cc を読めない` で赤になる。今は g++-13 不在の skip が
  隠している。修理は数行だが、発火するのは {{T:norm-compiler-for-acceptance}} の裁定後なので
  そちらに束ねてよい。
