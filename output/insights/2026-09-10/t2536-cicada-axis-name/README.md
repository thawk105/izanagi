# [T-2536] genome 軸名と CMake cache 変数名の対応を CCBench 実体へ合わせる

- authority: none
- default_effect: no-state-change
- wave: dev-wave-t2536-cicada-axis-name (branch worktree-dev-wave-t2536-cicada-axis-name)
- 実装 commit: 49ef88bad4c8492f20c4d02c814dde7b8c105a92
- 可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本 dir は一次資料の凍結写しにすぎない。

## 何を直したか

genome の軸名は C++ マクロ名であり、CMake cache 変数名とは protocol ごとに食い違いうる。
cicada の `INLINE_VERSION_OPT` に対応する cache 変数は `CCBENCH_INLINE_VERSION_OPT_CICADA`
(`external/ccbench/cc/cicada/CMakeLists.txt` と `external/ccbench/cmake/Options.cmake`) だが、
`Genome.cmake_defines()` は `-DCCBENCH_<軸名>` という汎用写像を持っていた。汎用名で渡すと CMake は
未使用と報告し、値はコンパイラへ届かない。genome が build の忠実な写像でなくなる (D1864 決定 1)。

対応表を `orchestrator/campaign/model.py` に 1 本だけ静的に宣言し、送り手 (`cmake_defines`)、
受け手 (`orchestrator/calibrator/cli.py` の受領証 genome 復元)、screening の 3 箇所が同じ表を使う。

## 親が実測した事実 (probe は repo 外に置いて実行した)

- 登録済み 4 protocol で非恒等写像は **cicada の `INLINE_VERSION_OPT` の 1 件だけ**。
  silo / mocc / tictoc は全軸が恒等写像である。`oze` にも同型の `_OZE` があるが `SPACES` に無い。
- 既存 parser `source_digest._parse_supplied_macro_details` は CCBench の実 CMake テキストから
  `macro -> cache 名` を返す。**同じ左辺を別 RHS で 2 度供給する崩れ方は fails-closed で拒否するが、
  2 軸が同じ cache 変数を読む崩れ方は素通りする。** 後者を塞ぐのは本 wave の実装側の責務になった。
- 同 parser は CMake の制御フローを解釈しない。`if(FALSE)` の中に旧 mapping を残しても表に載る。
  これは既存 parser の性質であり本 wave では変えていない。限界として明記する。
- 高位 API `resolve_effective_defines_from_cmake_sources` は cicada に使えない。
  `EVOLVE_BLOCK_SOURCE_PROTOCOLS` に cicada の source が無く、`_source_protocol` が
  未知 source として fails-closed で止まる。
- 表に無い軸を恒等写像へ落とす fallback は**撤去できない**。silo の genome は patch 供給の
  `BACKOFF_FIXED` / `BACKOFF_INCR_MILLI` / `BACKOFF_MAX_US` / `BACKOFF_UPDATE_US` を持ち、
  `orchestrator/tests/test_campaign.py` と `orchestrator/tests/test_t2187_adaptive_const_probe.py` が
  現行 argv を固定している。
- `buildcache.cache_key()` の pre-image は configure argv を含まない
  (`genome.canonical()` / ccbench commit / trace / src / toolchain / admission receipt)。
  `derive_build_admission` の body にも argv は無い。

## 段 3 が実装前に潰したもの

2 レンズ (正しさ境界 / 整合と実効性) は、親 brief の (P1) 逆写像が D1864 の却下 alias に当たらないこと、
(P2) 静的表 + 実体照合、(P4) import 循環なしを refuted と判定した。そのうえで**両レンズが独立に
同じ穴へ収束した** — protocol 内の cache 名の単射性を誰も検査していない。実測でも既存 parser が
それを通すことを確認したので、実装に拒否と検査を入れた。

レンズ B はさらに「親の brief が『cicada の live build 経路は現存しない』と書いたのは過剰一般化」だと
指摘した。専用 driver が無いだけで、generic caller から cicada build へ到達できる。親はこれを採用し、
欠陥は仮想ではなく現存すると読み替えた。

## 段 6 が暴いたもの (実装を通り抜ける非等価変異)

レンズ C は追加 8 nodeid を全部通過する変異を 5 種類構成した。すべて**テスト側だけ**で閉じ、
実装は 1 byte も変えていない。

1. forward 関数が表と食い違う (mocc の 1 軸だけ別 cache 名を返す) → 表の全 entry の往復検査を追加。
2. 単射性検査が silo でしか発火しない → 4 protocol を parameterize。
3. 逆引きに `_CICADA` suffix alias を足す → 該当受領証の拒否負例を追加。
4. cli の逆変換が cicada でしか検査されていない → 3 protocol の受領証正例を追加。
5. drift 検査 helper が cicada だけ実体を読み他を捏造する → cicada 以外の CCBench 側 rename 負例を追加。

レンズ D は**検査に偽陽性の種**を見つけた。`source_digest.parse_options_defaults` は空値の cache entry を
意図的に除外するので、それを「宣言済み cache 名の一覧」として使うと、CCBench が既定値を `""` にする
正当な変更だけで赤になる。この照合を外し、空 default の正例を足した。
同レンズは、実装に混じっていた「表の件数 17」と「非恒等写像は 1 件だけ」の固定値 pin が、
段 4 が scope 外と裁定した「意図軸集合の独立 pin」の弱い実装であることも指摘した。両方外した。

## 親が採らなかった real 所見 (裁定パッケージへ)

- **build cache identity が写像を束縛しない** (レンズ B)。機構は正しいが、発火前提の cicada cache 項目は
  実測 0 件。将来の写像変更は CCBench 側なら `ccbench_commit` が key に入り、izanagi 側なら
  本 wave が新設した drift 検査が赤にする。cache identity は全 protocol 共有の同一性コードであり、
  依頼が除外した一般化に当たる。
- **表外・別 protocol・二重接頭辞の余剰 define が canonical genome に載る** (レンズ C)。
  これは現行が要求する挙動である。`orchestrator/tests/test_calibrator_certify.py` が
  `mocc|BACKOFF_FIXED=-1,...` を期待し、認定 launcher は silo へ `-DCCBENCH_BACKOFF_FIXED=-1` を渡す。
  変更前後で挙動は同一なので、閉じるなら受理集合の設計判断として別に裁定が要る。
- **意図軸集合の独立 pin** と **emitted compile command 層までの証明**。後者はレンズ A 自身が
  scope 外と書いている。

## 完了主張の限界

本 wave が主張するのは次の 2 つだけである。

- genome 軸 → CMake cache 変数名の対応を CCBench 実体と一致させ、崩れたら落ちる検査を置いた。
- cicada を認定の対象にするための**前提を 1 つ除去した**。

主張しないもの: cicada が認定できるようになったこと。コンパイラへ値が実際に届くことを証明したこと。
検査対象は CMake source 上の cache 名契約であり、emitted compile command ではない。
認定の protocol 受理集合は `{silo, mocc, tictoc}` のままである。

## 一次資料

- `verbatim/` — 段 1 brief、段 2 plan、段 3 の 2 レンズと親の実測、段 4 裁定、段 5 実装子、
  段 6 の 2 レンズと fix の逐語 10 本。
- `mutation/` — probe spec / probe ledger / 本走 spec / 本走 ledger。
  probe は全件 SURVIVED で登録して観測 node を集め、本走 spec はその実測から機械生成した。
  本走は **5/5 KILLED、期待 node 完全一致、baseline PASSED**、repo_head=49ef88bad。
