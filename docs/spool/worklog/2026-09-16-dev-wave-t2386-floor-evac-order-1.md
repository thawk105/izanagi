---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2386-floor-evac-order
seq: 1
title: [T-2386] official 床値成果物の退避と再配置の順序を一方向に裁定し、退避先を固定導出にした転送機構を新設した (コード + docs、branch worktree-dev-wave-t2386-floor-evac-order、変異 matrix = baseline PASSED・11/11 KILLED・SURVIVED 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「official 床値 result の repo 相対読取りと、走行直後の repo 外退避の順序を決めて
  実装する。既存 file で順序と読取りを確認できる範囲に限定し、[T-2650] の Masstree config.h 修理後の
  本走を待つ仕事にはしない。実装面は Codex author (D95)。規律 2 を緩めない。本題の順序決定と実装だけ。
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **順序を決めて実装した。** 決定は {{D:floor-evacuation-order-one-way}} と
  {{D:floor-evacuation-bundle-root-fixed}}。一次資料は
  `output/insights/2026-09-16/t2386-floor-evac-order/README.md`。
- **依頼の前提を 1 つ訂正した。** 起票時の本文は「clean-scan の除外が freeze namespace だけなので
  起動証明が止まる」までを問題としていたが、実測すると衝突はもう一段深い。candidate 生成は
  `_measurement_closure` で専用 6 path 以外の走査 hit に captured HEAD の blob 一致を要求し、
  批准側の `_verify_generation_semantics` は世代 commit の tree に blob が実在し worktree が
  HEAD blob と一致することを要求する。**再配置しただけでは通らず、commit が必要条件である。**
  その帰結として、commit を持つ branch では以後 official 床値を起動できない。順序が一方向で
  なければならない理由はここにある。
- **段 3 の敵対相談 2 本がそろって NO-GO を返し、親の案の中心を壊した。** 親は「部分復元の口を
  作らなければ cherry-pick は起きない」と置いたが、レンズ sol が「退避先が呼出し引数である限り、
  別 bundle を作って一部だけ戻せば同じことができる」を具体的な操作列で示した。候補の
  `floor_source` と床値が変わる。親は退避先を git common dir 配下の固定導出へ変え、選択の口を
  API から構造的に消した (D475 と同形)。
- **親 brief の主張 3 つが過剰で、レンズがそれを反証した。** 「v1 freeze の generator pin が
  乖離済みだから同 file の編集は無関門」は推論として不成立 (v2 candidate は captured HEAD の
  bytes を記録する)。「untracked なら走査対象」は `--exclude-standard` を無視している。
  「再配置した earlier run は HEAD 一致が要る」は、実際に出た hit だけが対象である。3 つとも
  裁定文で縮めた。
- **段 6 のレビューが must-fix 2 件を出した。** `git rev-parse --git-common-dir` が呼出し元の
  環境を継承するので `GIT_DIR` 等で退避先が分岐する件と、旧 bundle を `TemporaryDirectory` 配下へ
  退避していたため公開 rename と巻戻し rename が連続で失敗すると唯一の累積 bytes が cleanup で
  消える件。どちらも closed。
- **レンズ luna の nit を親が実測して実欠陥に格上げした。** 新設 test file が検索パス補正の前に
  `orchestrator` を import しており、`PYTHONPATH` 無しの直接起動が `ModuleNotFoundError` で
  rc=1 になる。自走 harness の meta-test は形式上満たしていたが、実際には走らなかった。
- **変異 probe が gate の検出力不足を 1 件暴いた。** 全件 SURVIVED 登録の probe を計算ノードで
  実走したところ、baseline 緑・11 変異中 10 件が赤を出し、`bundle_root` へ環境変数の上書き口を
  足す変異だけが生存した。同じ性質を pin するはずの node は推測した環境変数名 3 つと CLI flag 名
  5 つしか見ておらず、新しい名前の追加を検出できなかった。等価変異でも他層の mask でもないので、
  `inspect.getsource` + AST で「環境値を読む形が 1 つでもあれば赤」にする構造検査へ再照準した
  (`DW-M02`)。既存の名前検査は残した。
- **変異 matrix 本走は baseline PASSED・11/11 KILLED・SURVIVED 0・期待 node 完全一致**
  (対象 commit `99af814c3`)。M5・M8 は 6 node、M9 は 5 node を殺す過剰決定なので、単独の
  検出力証拠には数えない (`DW-M03`)。
- **受入全走 1 回目は 24098 passed / 2 failed / 1 error で、赤 2 件は自分の変更に帰属した。**
  新設 module の `bundle_root` が呼ぶ `git rev-parse --git-common-dir` が、
  `test_ccbench_spawn_sites.py` の process 起動台帳 (exact 比較) に未登録の起動箇所として出ていた。
  実装子の制約 meta-test 洗い出しも親の焦点走も、この横断台帳を集合に入れていなかった。
  台帳へ件数 1 で登録して閉じた (比較は緩めていない)。残る 1 件
  (`test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module`
  の setup error) は変更から到達しない module で、wave tip の単独再走で緑だったので受入再走で扱った。
- 工数: codex 子 10 本 (plan 186 秒 / 6 call、consult 2 = 137 / 6 と 124 / 5、author 874 / 27、
  review 2 = 85 / 5 と 114 / 5、fix 341 / 30、focus 92 / 3、fix2 375 / 25、fix3 272 / 24)。
  計算ノード job は変異 probe 12 走と本走 12 走、runner argv の所要実測 1 走 (72 秒)。
- **real だが scope 外**の 3 件は実装せず、発火条件付きの次の一手として残した。外部依存物
  (binary store / submission receipt / job staging) の完全 bundle 化は {{T:floor-evacuation-external-deps}}、
  痕跡を消した後の official 再起動の扱いと、批准後に同一 repo で official 床値を再開する道が構造的に
  無いことの是非は {{T:floor-relaunch-after-evacuation}} へまとめた。どちらも official 本走
  ([T-2650] の後) が実際に成果物を出すまで発火しない。

## 次の一手差分

### 完了

- [T-2386] 退避と再配置の順序を一方向に裁定し、退避先を固定導出にした転送機構と 15 node を入れた。
  runbook W-2 の「順序は未決」も裁定済みへ直した。
  remaining: none
  base: ca62b35eae08b6d26b40916495634cc4cf67fa68e358b00dd73f4bca5f9f74e9

### 新規

- {{T:floor-evacuation-external-deps}} **P3・新規**: official 床値の退避 bundle は run directory の
  payload だけを実体保存し、binary store・submission receipt・job staging は path と hash の参照に
  留めている。使い捨ての測定木を捨てると参照先が消え、再配置しても proof chain が dangling になる。
  **発火条件は official 本走が成果物を 1 件出したとき**。そのとき参照先の保持場所を実測で決め、
  必要なら bundle へ実体を含める。仮想のうちに機構を足さない。
- {{T:floor-relaunch-after-evacuation}} **P3・新規**: 退避は全 proto8・不適格・未完成 run を
  含むので、退避後に clean scan が緑になることは痕跡を消してよかったことの証明ではない。また
  再配置後の commit を持つ branch では以後 official 床値を起動できない。**発火条件は同じ holdout
  集合で official を打ち切った後に再測定が必要になったとき**。そのとき codex 2 レンズで扱いを決める。
