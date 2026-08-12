---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t921-perf-preflight
seq: 1
title: perf を測定の前提から外し preflight を pilot 限定で置いた — 検出 + 分岐 + 記録 (コード + docs、branch worktree-dev-wave-t921-perf-preflight)
---

## 本文

- **第 5 束のユーザー裁定 (2026-08-12、authority: user) を実装した。** 一次控えは
  `rulings-inbox/2026-08-12-rulings5-batch.md`。裁定 fragment の正本は未 land branch
  `worktree-rulings6-20260812` (6d4223cb) の slug `perf-optional-measurement` にあり、
  本 wave では実番号を書かず wave+slug で参照した (spool は他 wave の slug を参照できない)。
  設計判断は {{D:perf-preflight-pilot-scoped}}。
- **裁定の中核は「official を触らない」ことで満たせた。** 段 3 の敵対検証が
  「`available` は自己申告なので、偽装すれば official verifier に no-perf 形を受理させられる」
  という攻撃を具体化した。親が実コードで確かめたところ、
  `s8b_holdout_freeze._validate_floor_inputs` は `mode != "official"` と
  `eligible_for_refreeze is not True` を拒否し、`s8b_ratified_freeze` は期待 result に
  `"mode": "official"` を固定していた。**pilot 限定にすれば official の受理集合は
  広がらないのではなく変化しない**ため、段 2 プランの約 3 分の 1 (ratified freeze 改造・
  equality chain の edge 追加・3 matcher への authority 配線) を丸ごと削除できた。
- **親の実測が 1 件覆った (段 3 の成果)。** handoff 実測 8 で
  「`policy.json` の `perf_candidates` は kernel 5.15.0-135/100 を指すので stale」と書いたが、
  worklog 0804-144 に bnode005 / bnode009 で候補が動作した記録がある。
  **version 名の不一致だけでは実行不能を含意しない。** 撤回し、候補は「使わないが receipt へ
  evidence として記録する」形にした (絶対 path 採用は F89 が未裁定)。
- **敵対所見のうち 1 件を親が退けた。** 「perf が rc≠0 なら異常として abort せよ」は、
  T-920 の実測がまさに `perf stat` rc=2 である以上、裁定が開けた経路を再び閉じる。
  `rc != 0` は `unavailable` に分類し、abort は timeout・予期しない OSError・signal 終了に限った。
- **敵対所見の提案 fix も 1 件退けた。** 「accepted rep に rc=0 と counter 完備を要求せよ」は、
  実コード (`runner.py`) で `require_all_reps` が `strict_returncode` を伴い **1 rep の失敗で
  session 全体を fatal にする**こと、`require_complete_metrics` が **4 counter 完備を要求**して
  perf 無しと構造的に両立しないことを確認したため不採用。所見自体は real (wave 前から在る穴)
  として裁定パッケージへ回した。
- **「120 回失敗」の帰属を訂正した。** 12 セル × 8 round + retry 24 = **上限 120 の
  authorized session attempt** であって、perf が 120 回失敗した記録ではない。
  各 session は 5 rep を内包するため、subprocess 起動数とは別の数である。
- **親自身の運用裁定も 1 件誤りだった。** 段 4 で「direct 実行の canary は
  `smoke_probe.sh` で運用代替する」と裁定したが、同 script は perf も ccbench も起動せず
  検出力ゼロである (段 6 luna が指摘、親が確認)。撤回し、(a) wrapper の床値完備検査を
  機械強制し、(b) job 開始直後に journal を見て全滅なら早期に止める運用に置き換えた。
- **実装子が model call 上限 (100) で SIGTERM され、コードは書けたが報告を書けなかった。**
  `output_bytes=0` / `stop_reason=max_model_calls`。実装は木に残っていたため、親が差分を
  読んで検証し、焦点走を実走した (子の自己申告は 1 件も使っていない)。既知の型だが、
  **実装段で発生すると「報告なしのコード」が残る**点が新しい。fix 段は上限を 160 へ上げた。
- **fix 子は「既存テストの期待値を変更しない」規律を守って正しく止まった。** wrapper へ
  足した床値検証も `"$PY" -I -B` で硬化したため、硬化済み起動数を 14 で exact 固定していた
  `test_floor_job_hardens_interpreter` が 15 を検出して赤になった。子は手を出さず報告し、
  親が「硬化済み・承認済みの追加なので pin を追随させる (緩和ではない)」と裁定して
  別の限定 fix 子へ投げた。worklog 472 が同じテストで同型の先取りを記録している (2 例目)。
- **変異 6/6 KILLED、MISMATCH 0、baseline 緑** (固定 commit `cbb9cdab` 束縛の使い捨て
  worktree、計算ノード dispatch、runner は焦点 6 file)。本命 2 件が生きていた —
  M1 (記録 receipt を無視して perf あり形と無し形の**どちらでも通す**)、
  M2 (official mode でも receipt / perf 無し形を許す)。
  M5 は **wave 前の実コードの形** (`build_portable_run_cmd` が常に perf を前置) を復元する
  変異で、これも殺された。M6 は perf あり既定 bytes を変える正例。
- **段 6 luna が予告した先取りは fix で実際に解消していた。** 「M1 と portable builder 変異が
  `test_measure_run_cmd_rejects_shape_opposite_to_recorded_preflight` の同じ最初の assertion で
  落ちるため証拠が一意に帰属しない」という指摘に対し、fix が M1 の test を固定 stub で
  portable builder から隔離した。**本走の 6 変異の失敗 node 集合に重複は 1 件もない。**
- **erratum: 変異の初回走は probe である。** 期待 node の完全集合を事前に確定できなかったため、
  全変異を `SURVIVED` 期待 + `expected_nodes` 空で 1 度走らせ (harness は KILLED 期待に
  完全集合を要求するため空では起動しない)、MISMATCH 6/6 の実失敗 node を採取してから
  本 spec を組んだ。probe の結果は消さず `mutation-probe.json` として残す。
- **AI 工数**: codex 子 6 本 (plan 1 / consult 2 / review 2 / fix 2)。
  段 6 の review 投入で `--lane` を渡して rc=2 を 1 回 (consult 専用の引数、dry-run で検出)。
  変異 harness の投入で `-rf` 欠落による起動前 rc=2 を 1 回 (DW-M08 の要求。
  **受入全走では逆に足してはいけない flag** であり、走行の種類で要求が反転する)。

## 次の一手差分

### 完了

- [T-921] perf preflight を実装した (検出 + 分岐 + 記録、pilot 限定)。
  remaining: none
  base: e4c4142a805ffae399ae2fb1e0d09f4e053b141282f8091d2ce7e598a31f9778

### 更新

- [T-748] **P1・W-2 投入の閂は解除済み。残るのは実測値の回収 (B 系)**:
  perf 不在は `unavailable` として測定を続行するようになり、W-2 の停止理由は消えた。
  投入形は従来どおり — `tools/pegasus/floor_campaign.sh` が `--mode pilot` 固定、
  成果物は repo へ commit せず repo 外 bundle (run directory + binary store +
  submission receipt + job staging) へ退避し worklog へ path と hash、途中死は救出せず
  新規 job で再実行する。**`driver_rc` だけで成功と判定しない** — 床値が有限実数で
  あることを wrapper が機械強制する。
  base: 4c3acf87a0886e9b90aebe895faa0047bdb761e9873db0483ae96c70aed35ef1

- [T-920] **P3・閂ではなくなった。ユーザーは「今はやらない」(B 系)**:
  計算ノードへの linux-tools 導入は、床値・calibration・oracle の前提ではなくなった。
  perf があれば使い、無ければ無しで測る。導入されれば counters が戻るだけである。
  base: 7805208cf5103e049cf5909365702e23fea1c8ffe785ceec6ba9cca0ebe5d843

### 新規

- {{T:perf-condition-propagation}} **P2・ユーザー裁定待ち (B 系)**:
  測定条件 (perf の有無) を oracle manifest・oracle 実行・verdict まで伝播させるか。
  現状 no-perf は pilot 限定なので実害はないが、official で no-perf を認めるなら必須。
  伝播しないまま official 化すると `scale_state`・floor 判定・最終 verdict・certified 選択が
  異条件混在になる。
- {{T:floor-rep-rc-evidence}} **P2・ユーザー裁定待ち (B 系)**:
  床値 session の rep ごとの rc と counter 完備を記録・検査するか。probe 成功後に本番 perf が
  壊れた rep が有効 throughput として median に入りうる (**wave 前から在る穴**)。
  既存の rep 許容設計 (`exec_failures` / `excluded_reason=launch`) と衝突するため単独裁定が要る。
- {{T:floor-reservation-timeout-budget}} **P2・ユーザー裁定待ち (B 系)**:
  reservation 式が session あたり `extime_s * reps + 120` = 145 秒を仮定する一方、
  全 rep が timeout すると 1 session 最大 600 秒になる。120 attempt 全滅なら 72000 秒で
  10 時間枠を超える。
- {{T:perf-candidate-adoption}} **P3・ユーザー裁定待ち (B 系)**:
  `policy.json` の `perf_candidates` を床値経路でも採用するか。採用するなら realpath・hash・
  version を固定し、probe と本番で同一絶対 path を使う必要がある (F89 が未裁定)。
