---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2294-mocc-lock-instrumentation
seq: 1
title: [T-2294] mocc に lock 被覆と permutation の #if TRACE 計装を入れ、負例 3 本と compute 実走で歯を立証した (patch 4 本 + driver + tests + docs、branch worktree-dev-wave-t2294-mocc-lock-instrumentation、変異 19/19 KILLED)
---

## 本文

- 依頼: mocc に X (lock 被覆) / P (permutation) の計装を入れ、真実源は RWLOCK と CLL、Silo の Tidword 計装は転用しない、性能 build からは
  D14 で完全除去、verifier は無編集で既存 consumer に読ませ、正例・負例を実体名指しで足す。段 1 で dynamic-backoff wave の
  `patches/README.md` 未着地差分は無し (land 済み) と確認。
- 段 2 plan + 段 3 敵対相談 2 本 (must-fix 6 + 7) → 段 4 裁定 {{D:mocc-lock-coverage-instrumentation}}: 保持検査 3 点
  (`lock-lost-before-publish` を追加)、負例 3 本 (early-unlock は balanced)、`#line` による論理行復元、`#error` は置かない、
  materializer 登録、compute JSON を成果物に。段 5 は Codex author 2 単位 (A: patch / driver / 登録簿、B: tests / fixtures)。
- 段 6 敵対レビュー 2 本はいずれも NO-GO。real の最重要 3 件: (1) early-unlock の裸 directive が 2 site に重複し、production gate の
  exactly-one で driver が停止 (test は `set()` で重複を許していた、{{F:duplicate-directive-passes-set-dedup-test}})、
  (2) 前処理 witness の生 byte 比較は `#line` が marker を増やすため構造的に成立せず、「(論理行番号, 非空本文) 列の一致」へ再裁定
  ({{D:trace0-preprocess-logical-row-witness}})、(3) 構造 test が preimage の別行や comment で恒真化可能。fix 子 3 巡
  (fix-1: R1〜R8、fix-2: configure 引数、fix-3: 条件式の逐語固定と resolver node) と焦点再レビュー 1 本 (closed 7 / partial 1 → fix-3 で閉じ、
  4 巡目は投じず変異で裏取り)。refuted: `toolchain_matches_policy` 定数は到達後条件として偽緑ではない (観測値比較へは改善として採用)、
  build dir 等長化は correctness must-fix ではない (保険として採用)。
- compute 1 回目 (job 979769) は condition gate が configure の stderr 警告 (未使用 CMake 変数 `RULE_LAUNCH_COMPILE`) を fail-closed で
  red にして 52 秒で停止 ({{F:condition-gate-red-on-unused-cmake-variable-warning}})。login で再現し引数を除去 → 2 回目 (job 979791、
  Elapse 130 秒) で 14 check all_pass。
- 素材: TRACE=0 の性能 build は `#line` で preimage と `.text` bytes まで一致した (login の同長 dir で sha e5ba3e07…、compute で差分 0 行)。
  dir 名長が違うだけで `__FILE__` 経由で lea 158 行がずれる — 「観測者効果ゼロ」の主張は path 長まで揃えて初めて bytes で言える。
- 素材: lockskip 4 thread は X に加えて本物の cycle 3,754 本を出し verifier が non-serializable と判定した。lock 被覆の破れは
  1 thread では X でしか見えず、多 thread で初めて直列性違反として現れる — 被覆検査が cycle 検出より早い段で歯を持つことの実例。
- 変異 matrix (spec v3、19 件、runner は s4_loop を除く 5 file): 19 件全て KILLED (MISMATCH 0、baseline 緑、harness 本走 08:26〜08:47 JST、compute job 980034 ほか 20 走)。login probe で期待 node を集め harness は final 1 走 (compute queue が自分の並行 job で詰まり collection 段が 2 回 timeout したため)。M7 (B-3 allowlist) は s4_loop が 260 秒/走で重いため
  matrix 外の冗長 gate (自走で閉包確認)。patch 変異は JSON の sha 束縛で consumer node も併発赤 (冗長 gate、単一理由は主 node)。
- 工数: codex 子 8 本 (plan 1、consult 2、author 2、review 3、fix 3 = 計 11 起動、うち fix 2 は receipt 上 author)、
  compute 2 job (52 秒 + 130 秒)、login build 約 20 本。親 context 1 本 (1 回圧縮)。
- 裁定パッケージ (scope 外、ユーザー判断): mocc trace pilot への計装 patch 重ね、verifier core の P 説明文の protocol 中立化、
  gitlink の e9e477ca (+patch) への前進 [T-2295]、DELETE 経路の動的立証 (YCSB に DELETE が無い)。
- 受入 1 回目 (09:02〜09:18 JST、post-claim merge で main dcf053f1c を取り込み): 20,957 緑 / 1 赤
  `test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches`。原因は本 wave の driver の
  `_install_dependency` (gflags / glog の cmake --build) が materializer 登録簿に無いこと (自分起因)。Codex fix 子 4 が登録簿と
  `EXPECTED_NON_ADMISSIBLE` へ追加し、焦点走の後に受入 2 回目を走らせた。
- dev-wave 改善候補 3 件は段 8 で routing (DW-O13 の発火条件、隔離 session の guard と submodule の object 取得、`tools/pegasus/*.py --help` 拒否)。

## 次の一手差分

### 完了

- [T-2294] mocc の lock 被覆・permutation 計装、負例 3 本、compute 実走 all_pass、verifier 読み手の正例・負例を着地した。
  remaining: none
  base: b70ad196d204d6083f3763716003d3c88704bd5302af34706acf518f9eb9fef5
