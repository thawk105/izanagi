# 裁定パッケージ — template patch 未適用で恒久 skip する 4 node をどうするか

wave: `dev-wave-known-red-exceptions`。段 6 レンズ B が must-fix として挙げ、焦点再レビューが
双方の事実を独立に検証した。親は本 wave の scope 外と裁定し、`DW-S04` に従いここへ返す。

## 事実 (すべて本 wave で確認済み)

1. 受入全走の 20 skipped のうち 4 件は「template patch 未適用」を理由に skip する。
   実測 = 診断走行 (計算ノード request `900952.nqsv`、8037 passed / 20 skipped / 514.28 秒 / rc=0)。
   - `test_campaign.py::test_source_digest_parse_options_defaults`
     (Options.cmake に BACKOFF_FIXED 既定なし)
   - `test_campaign.py::test_source_digest_fixed_variant_distinct`
     (backoff.hh に `#if BACKOFF_FIXED` 無し)
   - `test_campaign.py::test_source_digest_failsclosed_on_missing_define`
     (backoff.hh に BACKOFF_FIXED 骨格なし)
   - `test_hooks.py::test_real_submodule_payload_edit` (marker 無し)
2. **これは外部依存物の不在ではない。** patch は repo 内 (`patches/silo-backoff-fixed.patch`) に
   あり、現行 pin に対して `git apply --check` が rc=0 で当たる。適用は
   `orchestrator/campaign/patchharness.py` の `applied()` が pinned-clean assert + tree lock +
   apply + finally revert + clean assert で行う。campaign 本番経路が実際に使っている機構である。
3. **並列との衝突は無い。** 対象 4 node は `orchestrator/tests/conftest.py` の
   `REAL_REPO_SERIAL_NODES` に「writer の patch 窓にある実 source を読む reader」として
   登録済みで、xdist の `real-repo` group で直列化される。
   `tools/run_tests.py` の submodule gate は**初期化の有無しか検査せず dirty を見ない**。
   親 brief の当初の却下理由 (dirty gate / xdist 衝突) はこの 2 点で反証された。
4. **ただし窓を開けるだけでは足りない。** `test_source_digest_fixed_variant_distinct` は
   `_require_g13()` 相当のガードを持たないまま `source_digest.src_token` を呼ぶ。
   同関数の既定は `cxx="g++-13"` で、`compute()` → `_cpp_normalize()` が実際に g++-13 を
   subprocess 起動する。pinned compiler が無い環境 ([T-747] の blocker、Pegasus 全体) では
   **skip でなく未捕捉 RuntimeError = 赤**になる。
5. したがって実効回収は 4 node 中 2 node
   (`test_source_digest_parse_options_defaults` と `test_real_submodule_payload_edit`)。
   1 node は guard 追加のうえ g++-13 不在で skip のまま、1 node は同じく skip のままである。
6. 本 wave では実挙動を測れなかった。一時適用して 4 node を実走させようとしたが、
   submodule への patch 適用が権限層に拒否された。迂回はしていない。

## 成果物影響 (レンズ B の主張、親も同意)

塞がないままだと、source digest の alias 防止・未定義 macro の fail-closed・
hook 編集面の実 template 結線が**標準の受入全走では恒久的に未検査**のままになる。
誤った variant identity や certified 選択を許しうる面である。

## R1. 4 node をテスト側で patch 窓を開けて実走させるか

- **(a) 開ける (レンズ B 推奨)。** 4 node を `patchharness.applied()` で包み、
  `test_source_digest_fixed_variant_distinct` に `_require_g13()` を足す。
  回収 2 node。受入 suite が実 submodule を変異させる箇所が 4 増える。
- **(b) 開けないが分類を正す (親の既定)。** README と census の分類を
  「外部依存物の不在」から「条件付き未実走 (repo 内で満たせるが開けていない)」へ改め、
  隔離 checkout か fake repo での境界テストを別途起票する。受入 suite の挙動は変えない。
- **(c) 隔離 checkout で開ける。** `tools/mutation_worktree.py` と同型の使い捨て worktree を
  テストが作り、そこへ patch を当てる。実 submodule を触らないが、テスト 1 本あたりの
  所要が増え、submodule clone のコストを受入全走が毎回払う。
- **推奨**: **(b) を既定にしたうえで (c) を起票**。理由は、(a) の回収が 2 node に留まる一方で
  受入全走という共有の関門に実 tree 変異を 4 箇所増やすため、費用対効果が [T-747] の
  compiler blocker の解消状況に依存するからである。compiler が入るなら (a) の回収は
  4 node へ増え、判断が変わる。

## R2. `orchestrator/tests/README.md` の分類語を改めるか

現行は 4 件を「依存物不在」に含めているが、実体は repo 内で満たせる前提である。
- **(a) 改める** — 「条件付き未実走」を別分類として立て、開けない理由を各所に書く。
- **(b) 現状維持** — 分類語は変えず、個々の skip 理由文だけで判別させる。
- **推奨**: (a)。census を読む側が「外部依存だから仕方ない」と誤読するのを止めるため。

## 参考 — 本 wave が閉じた分

同族で本 wave が閉じたのは、疑似 return (PASS 化) 2 件、hook 配線欠落の skip 1 件、
広すぎる `ImportError` 1 件、死んだ広 except helper 1 件である。
positive control 2 本と変異 M2 / M3 で機械化した。
