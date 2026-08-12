---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t748-pilot-path
seq: 1
title: 床値 campaign の投入経路を固定 pilot にし、死経路だった W-2 投入を開いた — 裁定 (c) の実装 (コード + docs、変異 6/6 期待どおり、branch worktree-dev-wave-t748-pilot-path)
---

## 本文

- **[T-748] 裁定 (c) (2026-08-12、authority: user) を実装した。** 一次控えは
  `rulings-inbox/2026-08-12-coarse-provenance-45rulings.md`。
  投入 script が渡す mode を `official` から `pilot` へ固定し、job-result と失敗文言を追随させた。
  設計判断は {{D:floor-wrapper-fixed-pilot}} と {{D:shell-guard-token-counting}}。
- **塞いでいた 3 点のうち 2 点は「維持する側」だった。** worklog 455 が挙げた blocker
  (official 無条件拒否 / pilot は `eligible_for_refreeze=False` / 投入 script が official 固定) のうち、
  裁定が解くよう求めたのは 3 番目だけである。1 と 2 は不変条件として維持した。
- **現行の投入 script は死経路だった。** driver は official を CLI と core で二重に拒否するため、
  投入しても計算ノードで必ず倒れる。**床値の測定が構造的に不可能な状態**だった。
- **親の provisional 裁定 (P1) は敵対相談 2 本とも「反対なし」で通った。** mode の受け口
  (環境変数・argv) を作る案は、official を渡せる口を新設する点で非同値と判定された。
- **段 3 で親 brief の一般化 2 件が refuted された。** (1)「toolchain 束縛は mode による bypass なし」は
  **fresh CLI 経路に限る** — resume / finalize-pending は build を通らず、generic pilot API は
  seam 注入を許す (official だけが注入を拒否する)。本 wave が投入する W-2 は fresh CLI なので該当しない。
  (2)「W-2 の床値が certified 選択を決める」は**誤り** — pilot result は official path regex・
  holdout freeze・ratified freeze・oracle validation のいずれも通らないため、
  **certified の受理集合を直接は変えない**。変わるのは「床値の実測値が存在するか否か」である。
- **pilot 出力の自己汚染を実測で確認し、成果物を repo へ commit しない方針を採った。**
  driver は `out_root = repo_output_root()` で repo の `output/` 配下へ書き、
  `output/env/pegasus/calibration/s8b-floor-pilot/…` は gitignore されない
  (`git check-ignore` rc=1 で実測)。holdout clean-scan の除外は `output/s8b-freeze/` だけなので、
  pilot result を repo に置くと**将来の official 床値 job の起動証明 (hit 0 件要求) が止まる**。
  worklog 131-132 が同じ性質を既に記録していた。
- **段 3 の子が実在しない path を根拠に挙げた。** `experiments/phase3-benchmark/scripts/floor_campaign.sh`
  は repo に無く、実体は `tools/pegasus/floor_campaign.sh` の 1 本だけである
  (親が `find` で確認)。主張の内容自体は実体側で裏が取れたので結論は維持したが、
  **子の引用 path を親が検証しなければ捏造を採用していた**。
- **段 6 レビューは 2 本とも NO-GO**、real 所見 8 件。fix 1 巡で閉じた。
  guard の検出力不足 3 件は test 側だけで直し、production は不変のままとした。
- **レビューの must-fix 1 件を親が refuted にした。** 「offline third-party source が build 経路へ
  配線されておらず W-2 が最初の CMake configure で止まる」という所見に対し、
  **第 1 世代 calibration の `acquisition_receipt` が、同じ build 経路で計算ノード上の
  `ycsb_silo.exe` build に成功した記録** (`/scr/0_867876.nqsv/ccbench-build`) を持つことを実測した。
  子自身も停止予測を「推測」と明記していた。
- **変異 6 件は期待どおり** (KILLED 5 / SURVIVED 1)。SURVIVED は**承認外の過剰拒否を検出する正例**で、
  意味を変えない整形変更で guard が落ちないことを固定した。
- **M3 の初回は MISMATCH だった (erratum)。** marker 区間外へ第 2 起動を注入する変異は、
  登録した guard に加えて `test_floor_job_hardens_interpreter` も落とした。
  同テストが `"$PY" -I -B` の出現回数を **14 で exact 固定**しており、
  **第 2 起動を独立に検出する層が既にあった**ためである。期待 node を完全集合へ再登録して再走し、
  KILLED を確認した。初回結果は消さず erratum として残す。
- **記録執筆中に変異 harness を止めてしまった。** decisions fragment を書いた瞬間に
  untracked 検出で harness が中断した (`rc=2`、M1/M2 まで完了)。記録を先に commit してから
  投入し直した。既知の型どおりの自損である。
- **AI 工数**: codex 子 6 本 (plan 1 / consult 2 / author 1 / review 2) + fix 1 本。
  段 6 review の投入で `--lane` を渡して 1 回 `rc=2` (consult 専用の引数)。
- **待ち手が偽の完了を返した (新しい型)。** 段 6 fix の待ち手が **rc=0 で返ったのに
  `.done` も成果物も無く、producer は生存していた**。前景では正しく `rc=70` (timeout) を返すことを
  実測しており、背景実行時だけ無音で終わる。3 点照合をしていなければ成果物ゼロで先へ進んでいた。
  詳細は F24 の再発記録。
- **ユーザー手番**: 裁定 4 件 (下記「新規」)。push は行わない。

## 次の一手差分

### 更新

- [T-748] **P1・裁定 (c) を実装済み。W-2 は land 後に投入する (B 系)**:
  `tools/pegasus/floor_campaign.sh` が `--mode pilot` を固定で渡すようになり、
  pilot 経路の欠落は解消した。official の受理集合は空のまま、
  `eligible_for_refreeze` も緩めていない。**残るのは W-2 の投入と実測値の回収**で、
  成果物は repo へ commit せず repo 外の bundle (run directory + binary store +
  submission/job receipt) へ退避し、worklog には path と hash を書く。
  途中で死んだら救出せず新規 job で再実行する。
  base: ce926217ac02c9d7ffbd6809c2040c6d362483973fcbf76dad615eec25fea047

### 新規

- {{T:floor-wrapper-writer-failure-rc}} **P1・ユーザー裁定待ち (B 系)**:
  `job-result.json` の書込みに失敗しても driver が成功していれば wrapper は **rc=0 で終わる**
  (`exit "$driver_rc"`)。`failure.json` は残るが終了値は成功になる。
  README は「成功と偽らない」と書いていたので、実装に合わせて是正した。
  **非 zero で終わらせるべきかは受理集合 (「job-result が無いのに成功と記録された run」) の
  変更なので親が決めない。** 現挙動は test で pin 済み。
  なお `failure.json` は最初の失敗 1 件しか記録せず、writer 自身の失敗 rc も握られる。
- {{T:pilot-api-seam-evidence-profile}} **P2・ユーザー裁定待ち (B 系)**:
  generic な pilot API は seam 注入を許す (official だけが注入を拒否する)。
  注入で作った binary から得た値も pilot artifact として同じ形で残るため、
  **evidence profile を分けて non-evidence と明示するか**を決める。
  固定 CLI で走る W-2 自体は seam を公開しないので現行の投入は該当しない。
- {{T:cmake-realpath-binding}} **P3・ユーザー裁定待ち (B 系)**:
  toolchain 束縛は cc/cxx の realpath を照合する一方、**cmake は version body だけ**で
  realpath を束縛しない。同一 version 表示で実体が差し替わっても検出できない。
  **親推奨は見送り** — 「bytes 級 provenance 機構の新設は既定で見送り側」というユーザー基準に照らす。
  当面は W-2 の記録済み `cmake.path` を親が照合する運用で埋める。
- {{T:floor-run-resume-rescue}} **P3・ユーザー裁定待ち (B 系)**:
  床値 run が途中で死んだときの正式な救出経路が無い。wrapper は `--resume` を渡さず、
  reservation 再検査は余裕不足を terminal として数値を不適格にする。
  run_dir を使う resume は source / receipt / PBS job binding を含む別設計であり、
  mode 変更には混ぜない。当面は新規 job で最初から再実行する。
