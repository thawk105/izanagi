---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t213-redefine
seq: 1
title: [T-213] 再定義の設計パッケージ 8 件を起草した — 敵対 2 本が独立に NO-GO を返し、pilot は fake child のままで成立すると判明した (docs のみ、branch worktree-dev-wave-t213-redefine、実装差分なしのため変異 matrix と受入全走は対象外)
---

## 本文

- **裁定 (235) の指示どおり設計起草に徹した。** 段 4 で「実装しない」と裁定し `4→7→8→9` を通した。
  実装差分が無いため**変異 matrix と受入全走は本 wave の射程外**であり、`DW-M01` の変異事前登録も
  行っていない。コード・テスト・機械設定は 1 byte も変えていない
- **段 3 の敵対レビューは 2 本とも NO-GO** (blocker 級 13 件)。うち **4 組が独立に同型を指摘**した。
  草案そのままを実装計画として承認できないという意味であり、T-213 の断念ではない
- **pilot に real child の開放 ([T-079]) は要らない、と判明した。** supervisor は fake child 専用
  (D74) だが、pilot が試すのは child ではなく供給・信頼・dispatch・証拠・cleanup の infrastructure
  である。既存 fake child (`orchestrator/tests/test_dev_waves_fake.py`) と使い捨て driver で、
  実 izanagi の disposable clone に 1 wave を走らせるのが `DW-G01` に沿う最小の生死実験になる。
  前 wave も本 wave の草案も、ここを「real 実行が要る」と取り違えていた
- **親が一次実行・コード読解で裏取りした新事実 5 件** (逐語は insight §1):
  (A) bootstrap gate は作業木の `.gitmodules` そのものを読むため per-clone override も
  `insteadOf` も通らない、(B) submodule は入れ子 (`third_party/shirakami`、HTTPS) で最上位だけでは
  閉包が閉じない、(C) supervisor は fake child 専用、(D) `validate()` は WAL replay と status だけで
  成果物を読まない (= 述語を書くだけでは恒真になる)、(E) wave worktree の置き場はハードコードで
  `--runtime-dir` を渡しても既定 runtime 側に作られる
- **前 wave 所見 A5 の機序を訂正した (erratum)。** 「custom runtime と `discover_runs()` の namespace
  衝突」ではない。run ID 文法は先頭英数字を要求するので、ドット始まりの名前は元から run と見なされない。
  真の機序は新事実 E である。是正すべきは名前の skip でなく path のハードコード
- **親 brief 自身の欠陥も real 判定した。** 単発観測 (clone 所要、network 1 回成功、48 commit 無変更) を
  決定論的なコード事実と同じ強さで並べていた。insight では「[コード] / [観測] / [仮定]」を三分し、
  timeout 閾値を観測値から導かないことを設計要件に含めた
- **scope 外だが現行 main に実在する穴 2 件を独立に起票した** (件 8)。どちらも T-213 の前提にせず、
  T-213 を人質にしない。逐語と再現手順は insight §3 件 8
- 逐語・実測・設計パッケージ 8 件は `output/insights/2026-08-05_t213-redefinition-design.md`。
  一次成果物は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/t213-redefine/`
- **ユーザー裁定待ちは 8 件** — 件 1 完了条件 (validator と一体で設計する)、件 2 bootstrap 権威
  (推奨: tracked `.gitmodules` を変えず承認済み pin 付き local mirror registry)、件 3 再帰供給、
  件 4 trust closure と site の型分離、件 5 attestation の二相化と qsub の write-ahead、
  件 6 残骸回収と worktree path、件 7 pilot の形、件 8 trust root の穴 2 件

## 次の一手差分

### 更新

- [T-213] **P2・ユーザー裁定待ち (設計パッケージ 8 件を起草済み)**: 「計算ノードから使える検査用
  隔離 clone の供給設計」への再定義に沿って、8 件の推奨付き設計パッケージを起草した。段 3 の敵対
  2 本は独立に NO-GO (blocker 13 件)。実装は着手しない。**pilot に real child の開放は不要**で、
  既存 fake child + 使い捨て driver で実 repo の 1 wave を試すのが最小の生死実験である。
  推奨依存順序は 件 7 段階 1 → 件 2 → 件 3 → 件 4 → 件 6 → 件 5 → 件 7 段階 2 → 件 1 判定。
  逐語と 8 件の択一は `output/insights/2026-08-05_t213-redefinition-design.md`
  base: 5666032a085ec49cd66d440114b3030f5c2d7fa7434d0e20f88b953d96c825fb

### 新規

- {{T:trust-root-control-surface}} **P2・ユーザー裁定待ち ([T-213] 段 3 A3、親がコードで裏取り)**:
  `pytest.ini` のような**制御面が trust root の外**にある。trust root の pathspec は `tools` と
  `orchestrator/tests` だけで、`run_tests.py` の 4 ゲートは環境変数 `PYTEST_ADDOPTS` しか読まない
  (同 ini の冒頭が明記)。after-SHA が `addopts` を足せば、真正な compute 実行・真正 receipt のまま
  全テスト未実行の rc=0 を作れる。推奨は trust root を「ファイルの正の列挙」から
  「Python module origin と制御ファイルの閉集合」へ広げる設計。[T-213] の前提にはしない
- {{T:compute-result-channel-ownership}} **P2・ユーザー裁定待ち ([T-213] 段 3 A4、親がコードで裏取り)**:
  compute の**結果チャネルを被検査コードが先取りできる**。`dispatch_compute._job_run` は
  cwd=repo_root で子を起動した後に `O_EXCL` で `result.json` を書くため、子が先に同名ファイルを
  作れば trusted 側の書込みは失敗し、login 側は残った内容と真正 marker・会計だけを読む
  (scheduler の終了状態と突き合わせない)。推奨は被検査コードが書けない結果チャネル
  (親 wrapper 所有) の設計。[T-213] の前提にはしない
