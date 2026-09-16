---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2600-anatomy-space-recount
seq: 1
title: [T-2600] anatomy の tictoc・cicada 探索空間サイズを現物で数え直した — どちらも 5 軸・各 2 値・生 32・制約後 24、合計は ≈234 (docs + genome.py docstring、branch worktree-dev-wave-t2600-anatomy-space-recount、変異 matrix = 登録可能な変異なし)
---

## 本文

- **依頼の scope**: 数え直しと訂正だけ。軸数から要素数を推測せず、各軸の候補数と軸間の制約を現物で確かめる。
  gate・検査・台帳・一般化の追加は scope 外 (ユーザー指示)。軽量版で進め、段 2・3 と段 6 のレビュー子は
  省いた (設計択一が割れず、防壁と受理集合に触れない)。genome.py docstring の 2 行は Codex author 1 本
  (gpt-6-astra / medium、model call 6、receipt accepted)。
- **数は 2 経路で一致した**: CCBench の分岐の入れ子を読んだ積 (tictoc 2×2×2×3、cicada 2×2×2×3) と、
  `SPACES` の実列挙 (silo 16/8、mocc 8/8、tictoc 32/24、cicada 32/24)。候補数は CMake option が
  `CACHE STRING` なので自明ではなく、全フラグの使われ方が `#if` か真偽式だけであることを確かめて 2 値とした。
  cicada の `INLINE_VERSION_OPT` は CMake 変数名が別名 (`CCBENCH_INLINE_VERSION_OPT_CICADA`) で、
  `orchestrator/campaign/model.py` の写像表が渡していることも確かめた。数え方の詳細は insight
  `output/insights/2026-09-16/t2600-anatomy-space-recount/README.md`。
- **親の provisional 裁定を 1 件採用した**: 数の訂正に加え、同じ §3 で数の前提を否定していた 2 行
  (死にフラグ一覧の `NO_WAIT_OF_TICTOC`、tictoc にも XOR を当てる相互排他行) を局所修正した。
  旧 tictoc 2^4 は前者の誤認から来ており、後者のままだと tictoc は 16 になる。§8 の Phase 1 申し送りは
  歴史記録として残した。表の行番号のずれ (silo の `#elif` は現物 165 行、表は 157 行) は本件の数と無関係なので触っていない。
- **凍結物は再凍結していない**: pin 閉包を独立の調査子で引いた。anatomy の数値を逐語 pin する検査は 0 件、
  genome.py は S1 凍結検証の歴史的容認 (`_HISTORICAL_CODE_PATHS`) で、docstring だけの前例 8e06a37c8 も凍結物は無改修。
- **変異 matrix は事前登録ゼロ**: 実装面の差分はあるので DW-S04 の免除には当たらないが、docstring と docs の
  数字を守る実効 gate が repo に無く、DW-M01 の単一理由性を満たす変異を登録できない。gate の新設は scope 外。
  免除ではなく「登録可能な変異が存在しない」記録である (同日の先例 [T-1642])。
- **実 repo を読むテストの実走 (記録前)**: tip 410e21751 で consumer test 12 本 (genome.py を参照する 7 本、
  genome.py の bytes を束縛する凍結検証系 4 本、`test_check_docs.py`) を計算ノード (Pegasus request 1592.nqsv) で
  走らせ 1956 passed / 28 skipped、失敗 0。`tools/check_docs.py` rc=0、全史 provenance 監査 rc=0。
- **受入全走**は本記録 commit を含む tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない。
  本エントリの作成時点では未実施である。

## 次の一手差分

### 完了

- [T-2600] anatomy §3 の tictoc (2^5=32、制約後 24)・cicada (2^5=32、制約後 24)・単純和 (≈234) と、
  genome.py module docstring の数 (cicada 2^5、≈ 234 binaries) を現物で数え直した値へ訂正した。
  remaining: none
  base: 15558886a62f80971cba8e9bef5fba9bed4e5454d5a8acd6239f8497acfde355
