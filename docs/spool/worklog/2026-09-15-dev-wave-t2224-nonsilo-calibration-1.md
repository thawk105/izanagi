---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2224-nonsilo-calibration
seq: 1
title: [T-2224] 非 silo の認定較正 record を 3 件取り、受理集合 3 protocol すべてが実測で生産できることを示した (実測 + docs、branch worktree-dev-wave-t2224-nonsilo-calibration、変異 matrix = 免除 (実装面差分ゼロ))
---

## 本文

- ユーザー依頼は「非 silo (mocc / tictoc) の認定較正 record を取る。引数化は着地済みで受理集合は
  {silo, mocc, tictoc} に閉じたが、認定較正 record は 0 件のままで非 silo の within-run floor は
  embargo 継続中。within-run floor の本走は embargo 中なので含めない。較正取得だけに絞る。
  規律 2 を緩めない。Codex author = D95。本題の実測だけ。仮想リスク向けの gate・検査・台帳・
  一般化の追加は scope 外」。
- **依頼の前提「認定較正 record は 0 件」は brief 前の実測で覆った。** 着手時点で registered は
  4 件あり、うち 1 件は **mocc** (`calibration-449d0ad22f13e366.json`、rr50、2026-09-10、[T-2535])
  だった。残り 3 件は silo (rr95 が 1 件、protocol 無記録の legacy が 2 件)。
  **0 件だったのは tictoc だけ**である。この差で scope を「非 silo を 0 から立ち上げる」から
  「silo が既に持つ workload 点 (rr50 / rr95) に非 silo を追いつかせる」へ変えた。
- 依頼が挙げた blocker 2 件はどちらも着地済みだった ([T-2535]、[T-2534])。活動そのものを止める
  裁定も無い — D1936 項39 の後置は cicada 限定で、mocc / tictoc は射程外である。
- **3 条件を別ノードへ同時投入し、3 件とも `accepted` で registered へ昇格した。**
  tictoc/rr50 = `998860.nqsv` / bnode093、tictoc/rr95 = `998863.nqsv` / bnode103、
  mocc/rr95 = `998864.nqsv` / bnode016。所要 184 / 177 / 238 秒 (要求枠 7200 秒)。
  **tictoc の測定は 0 件から 2 件になり、受理集合 {silo, mocc, tictoc} の 3 protocol すべてで
  認定較正 record を実測で生産できることが示された。**
- **コードもテストも 1 行も変えていない。** 既存 launcher を `--protocol` / `--rratio` で呼んだだけで、
  実装面の差分はゼロである。したがって変異 matrix は DW-S04 の免除に当たる。受入全走は免除していない。
- **投入前に見つけた罠を scope 決定に使った。** `layer3_report.py` の floor 照合は一致キー
  `(protocol, records, threads, workload)` で 2 件以上が一致すると `Layer3ReportError` を投げる。
  **mocc/rr50 を再取得すると既存 record と衝突して layer3 が hard error になる**ため、
  mocc は rr95 だけにした。取得した 3 件は既存 4 件のいずれともキーが重ならない。
  legacy 2 件 (753f / 94a4) が `(silo, 1000000, 48, rr50)` で既に完全一致している件は本 wave が
  作ったものではなく、直してもいない。
- **genome が build の忠実な写像であることを受領証で数えた (D1864)。** tictoc の
  `-DCCBENCH_*` はちょうど 6 件、mocc はちょうど 4 件で、撤回済みの `BACKOFF_FIXED` は
  argv にも genome にも無い。投入前に静的にも確かめており、tictoc の 5 軸は
  `cc/tictoc/CMakeLists.txt` の OPTIONS と `cmake/Options.cmake:63` の universal definitions 経由で
  全件コンパイラへ届き、`TICTOC_SPACE.axes` と完全一致する。
- **主張しないこと:** 性能を比較していない (取ったのは物差しであって throughput の優劣ではない)。
  非 silo の within-run floor の embargo を解いていない。rr5 と cicada は取っていない。
  所要 3 値はそれぞれ 1 回の観測であって分布ではない。
- **運用で 2 件詰まった。** (i) third-party staging は gitignore 対象で主 checkout にも全 worktree にも
  不在であり、`submit_certify.sh` は hydrate を起動しない (構造検査だけ) ので、親が投入前に
  `fetch_third_party.py hydrate --staging-root <worktree>/output/.../thirdparty-src` を明示的に走らせる
  必要がある。(ii) login node 負荷 173 (48 コア) で `tools/dev_wave_submodule_init.py` が rc=1 に
  なったが、中身は `_GIT_TIMEOUT_S = 30` の deadline 超過であって submodule の欠陥ではない。
  同じ argv を打ち切らずに走らせて rc=0。`git worktree add` も同じ負荷下で 13 分かかった。
- 一次資料は `output/insights/2026-09-15/t2224-nonsilo-calibration/README.md`。
- codex 子は 1 本も使っていない。設計択一が割れず、正しさ防壁に触れず、受理集合も変えないため
  DW-C00 の既定軽量版に当たり、実装面の差分もゼロだった。

## 次の一手差分

### 完了

- [T-2224] 認定 launcher の protocol / 軸の引数化に続けて、受理集合 {silo, mocc, tictoc} の
  3 protocol すべてで認定較正 record を実測で生産できることを示した。tictoc は 0 件から 2 件
  (rr50 / rr95)、mocc は rr50 に rr95 を足して 2 件になった。
  remaining: none
  base: f28d31deca2c47ede5fbbfc37b6d1f1e0a9f15da8debbd420969294417389388

### 新規

- {{T:nonsilo-within-run-floor-embargo-lift}} **P2・新規**: 非 silo の within-run floor を
  公式成果物へ入れてよいかを裁定する。[T-2224] が置いていた前提条件
  「生産できる protocol の集合を実測で示す」は満たされたが、embargo の解除自体は行っていない。
