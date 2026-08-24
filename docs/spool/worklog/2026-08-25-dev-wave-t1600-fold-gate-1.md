---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1600-fold-gate
seq: 1
title: [T-1600] fold 適用後 tree の land 前関門を作った。受入全走は増やさず、隔離 tree で実コーパス依存 node だけを掛ける (コード + テスト、branch worktree-dev-wave-t1600-fold-gate)
---

## 本文

- D752 の実装。起点は F512 (受入 14832 passed の緑の受領証で land した後、fold が canonical を
  書き換えて main を赤にし、全 wave の受入を止めた)。**受入全走は 1 回のままである。**

- **引数が名指した 2 集合は、この関門の権威になれないことを実測で確定した。** 依頼は
  「実コーパス依存 node の同定は `REAL_REPO_SERIAL_NODES` と `GROWTH_TEST_HOLDS` の現行定義を
  権威として使う」と指示していたが、**F512 で main を赤にした当の node**
  (`test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`) は
  どちらの集合にも入っていない。前者 (`conftest.py:338`) は「親 repo status と共有 ccbench
  worktree の reader/writer を xdist の同じ group へ閉じる」正本で概念が**共有可変資源**、
  後者 (`growth_test_holds.py:573`) は repo 成長 5 軸のコスト保留台帳である。
  段 2 の plan 子と段 3 の 2 レンズも、親の読みを渡さずに独立判定させた結果、同じ結論に達した。
  そのまま実装すれば**関門が自分の起点事故を構造的に取り逃す**ため、2 集合は候補源にせず
  「直列実行の要否」と「hold 除外」の classification join としてだけ使い、
  対象 node の権威は新設 registry + AST call graph 導出の双方向一致に置いた。
  grep の手書き列挙は使っていない (権威は導出側にある)。

- **親の裁定に過剰拒否の欠陥があり、実装前に自分で見つけて訂正した。** 当初「fold plan の target に
  family X が現れたのに registry で family X を持つ node が 0 件なら fail-closed」と裁定したが、
  実装後の実測で family 母数は failures=3 / worklog=2 / archive=2 / folded=1 /
  **decisions=0 / phase3=0 / rotation=0** と判明した。decisions fragment を含む fold は
  大多数の wave で起きるので、そのまま実装すれば**ほぼ全 wave の land が止まる**。
  被覆の穴を可用性の停止へ変換しており正しさの利得はゼロなので、
  `covered-and-passed` / `covered-and-failed` / `uncovered` の三値へ訂正した。
  未被覆は緑と数えず receipt へ記録するが land は止めない。穴が黙って広がらない歯止めは
  land 時ではなく**受入時の contract test** (理由付き allowlist との双方向完全一致) に置いた。

- **敵対レビュー 2 本が must-fix 11 件 + nit 1 件を出し、refuted は 0 件だった。**
  最も危険だったのは `PYTHONOPTIMIZE=1` を立てて land を起動すると子 Python が `-O` 相当になり、
  実コーパス検査の bare `assert` が**コンパイル時に消える**経路である。testcase は collect も
  実行もされるので JUnit の件数検査を全部満たし、関門が緑のまま通る。環境変数 1 個で防壁が
  完全に無効化される形だった。他に `TMPDIR` 継承で関門自身が main を汚す経路、
  lock 再取得後の再列挙が `docs/spool/` 直下だけで非衝突 untracked archive が ff 後の closure 検査
  まで到達する経路、infra 失敗と意味的な赤が同じ terminal 結果になり lease まで解放される経路。

- **変異を回さなければ「所見を全部閉じた」で終わっていた穴が 4 件出た。** レビュー所見 11 件を
  閉じた後に変異 matrix を回すと 9 件中 4 件が生存した。とくに `t1600.m06` は
  **`_FOLD_GATE_ENV_REMOVE` に 5 要素を足したのにテストは `PYTHONOPTIMIZE` にしか
  付いていなかった**ことを暴いた。`DW-S06-A` の「所見ゼロは変異で裏取りするまで緑と数えない」が
  実際に効いた事例である。生存 4 件はすべて**テストを足して**閉じ、production の防壁は
  1 行も緩めていない。最終 matrix は **baseline PASSED / 9 KILLED / SURVIVED 0 / MISMATCH 0**。
  親は `t1600.m01` (`executed == 0` 検査) を「冗長 gate だろう」と見立てたが外れで、
  `nodeids` が空かつ空 JUnit なら `collected == len(nodeids) == 0` が成立して `skipped != 0` も
  発火せず、**その条件だけが唯一の拒否理由になる入力が実在した**。冗長ではなく負例が無かっただけ。
- **`DW-M08` の「期待 node は完全集合」規律が独立に 1 件を拾った。** 穴を閉じた後の走行で
  `t1600.m05` が MISMATCH になったが、中身は**期待 4 件が全部観測されたうえに新設テストが
  1 件多く落ちた**もので、検出力が増えた方向のずれだった。期待 node を probe 時点の観測から
  作っていたため反映されていなかった。kill されたかどうかだけを見ていれば見逃していた。

- **隔離 tree が fold 前の canonical を読み続ける罠を、設計段階で潰した。** 対象 node は実 checkout を
  `Path(__file__).resolve().parents[2]` で解決するので、fold が触る path だけを上書きした軽い copy
  では**テストは元 checkout を読み続ける**。landing tip の全 tracked tree export へ
  `after_bytes` を上書きする形にし、隔離 tree で 5 node が実際に緑になることを 3 回実走で確認した。

- **時間予算は母集合を訂正してから決めた。** 段 2 案の 45 秒は母集合を 5 node (ledger 19.6 秒) と
  していたが、実際は 9 node 以上 (同 40.0 秒) で 2.30 倍ではなく 1.125 倍だった。さらに
  `acceptance_duration_ledger.json` の schema は nodeid と秒と件数だけで host / argv / worker 数を
  記録しないため、受入の xdist regime から隔離 tree の serial regime へ転移できない。
  親が同一 regime で 3 回実測し (実体化 max 24.66 秒 + 5 node 実行 max 38.44 秒 = 合計 63.10 秒)、
  `inner = ceil_to_5s(2.0 * 63.10) = 130`、`outer = 145` で確定した。
  **観測 regime は login node 混雑下・dispatch 経由であり、queue 待ちを含む保守側の代理値である。**
  関門本体は同一 process 内で pytest を起動するので、これは「関門本体の実所要」ではない。

- **変異 baseline の非帰属赤 1 件を main 単独再現で確定させた。**
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` は
  `orchestrator/campaign/execution_guard.py:156` の `CertifiedWriterAuthorizationError` で落ちる。
  本 wave の差分 6 file に `orchestrator/campaign/` は 1 件も含まれず、
  **main を `git archive` で export した tree でも同じ node が非緑**だった (main は error、
  本 wave の tree では failed、どちらも file 単独走)。9 file の焦点走では 1584 passed で緑なので
  選択集合依存であり、稼働中の `t1621-suite-order-dependence` の担当領域。
  `DW-C01` に従い変異 baseline から `--deselect` で外した。

- 段 3 のレビュー B が親の実測 2 件について「測定範囲が記録されていない」と正当に指摘したため、
  `DW-O09` の pin 閉包を検索式ごと測り直した。受入 receipt が bytes で束縛するのは
  `tools/run_tests.py` / `tools/dev_wave_wait.py` / `tools/check_ai_provenance.py` の 3 本だけで、
  本 wave の編集面はいずれも対象外。一方 `tools/spool_fold.py` の whole-file bytes は
  `input_closure_sha256` へ入り `transaction_id` を導くため、**本 wave の変更前に作られた
  active fold transaction は変更後の engine では recovery できない**。gate receipt の
  「旧 schema・receipt 不在は fail-closed」という裁定はこの点でも正しい。

- 待ち手の偽完了を 40 回以上踏んだ (F24 再発、過去最多)。実害はゼロ。詳細は同 F。
- 親の作法違反を 1 件記録する。変異走行中に「待機中の独立作業」として段 7 の spool fragment を
  repo へ書き、harness の untracked 検査が走行前に止めた。変異は 1 件も実行されず影響ゼロ。
  **変異走行中に書いてよいのは job dir と handoff だけである。**

## 次の一手差分

### 完了

- [T-1600] fold 適用後 tree を隔離して実コーパス依存 node を land 前に掛ける関門を実装し、
  受入全走を増やさずに閉じた。対象 node の権威、fold 出力と実適用 bytes の同一性、
  positive control、時間予算をすべて固定した。
  remaining: none
  base: 21465f3644c2dca0c6ad982d9c9822911d5ee66fa8ceffb0b1537842ea751591
