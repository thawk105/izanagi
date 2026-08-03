---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: worktree-dev-wave-t357-mutation-batch
seq: 1
title: 変異本走を計算ノード 1 ジョブへ束ねる生死確認で GO を得た — 恒久実装は 4 条件が揃うまで行わず裁定へ返す (docs のみ、branch worktree-dev-wave-t357-mutation-batch、生死確認 = Pegasus gen_S request 878497-878501 / 878505 / 878510、変異 matrix = 対象外)
---

## 本文

- ユーザー依頼は「変異本走の queue 待ちを削る。harness 自体を計算ノードの 1 ジョブとして走らせ、
  ジョブ内は `--runner-mode local` にする。逐次性・flock・復元検査・全走・検出力は変えない。
  `DW-G01` に従い恒久実装の前に 2〜3 変異の小 spec で生死確認を取る」であった。
  **生死確認まで実施して GO を得た。恒久実装は行わず、設計択一を裁定へ返す**
  ({{D:mutation-transport-bundle-smoke}}、{{D:mutation-transport-ruling-package}})
- **production コードの差分はゼロ**である。したがって変異 matrix と受入全走は対象外とする。
  実施したのは使い捨て driver による 2 経路の実走比較と、その証拠の凍結だけである
- **親 brief の誤りを 3 件、子と自分の実測が訂正した**
  - 「計算ノードで走らせる task を増やすのは採用済みパターンに乗る」は**誤り**。D117 決定 (4) 本文が
    第 3 task に D105 の supersede 等 4 条件を同時に要求している。段 2 プランの指摘を親が本文で裏取りした
  - 「`--resume` で walltime 切断を回収できる」は**誤り**。変異が当たったまま落ちると
    `_assert_clean_tracked` が先に止まり resume へ到達しない
  - 「baseline も変異と同じ overhead を払う」は**誤り**。T-243 台帳の実測では 22.7 s
- **親の実測に選択バイアスがあり、敵対レンズが指摘して訂正した。** `test_output_tail` は
  MISMATCH のときしか保存されないため、そこから取った n=12 は非ランダム標本だった。
  全 41 record の `artifact.stdout` から取り直し、overhead median 228.4 s、
  42 execution run の paired 差 9161.6 s (2.545 h) へ改めた
- **段 6 レビューが blocker 3 件を突き、うち 1 件は証拠の破壊寸前だった。** 後片付け手順が
  使い捨て worktree を先に消す形で、leg 1 の receipt / job stdout の参照が全部切れるところだった。
  証拠を `output/insights/` へ固定してから削除した
- **比較器を 3 度厳格化した。** 初版は 4 field 射影しか見ておらず、除外定数が実ロジックに
  接続されていなかった。最終版は全 leaf field を再帰比較し (gate 84 件)、除外は理由つきで全列挙する。
  2 巡目は誤検出 2 種で赤になり (`tool_sha256` を file hash と誤比較、`/bin` と `/usr/bin` の
  綴り差)、親が実測で誤検出と確認してから是正した。**gate 数は 80 → 84 で減っていない**
- エージェント工数: codex 子 7 本 (段 2 プラン 1、段 3 敵対 2、段 5 実装 1、段 6 レビュー 1 + fix 3)。
  Pegasus ジョブ 7 本 (leg 1 の 5 本 + leg 2 の 2 本)
- **段 8 の自己改善は候補 3 件を記録し、いずれも入口・reference の本文編集はしなかった**
  1. 「計算ノードへの新しい実行形は sanctioned job script の環境正規化を逐語で写す」→
     {{F:bundle-launcher-env-normalization}} と {{D:mutation-transport-ruling-package}} へ送った。
     dev-wave 入口の規律ではなく機体固有の作法である
  2. 「使い捨て環境を消す前に、台帳が参照する証拠を永続領域へ固定する」→ 単発であり
     `DW-G03` の「単発事故は局所修復」に従う。加えて `docs/dev-wave/operations.md` の残予算は
     44 bytes、`mutation.md` は 68 bytes しかなく、外出しは D94 却下案 (a) で既出のため取らない
  3. 「codex 子と背景 job の完了通知が子より先行する」→ **`DW-O01` に既存規律がある**
     (「完了は `.done` の存在と exit code だけで判定する。harness の task 完了通知を完了判定に
     してはならない」)。本 wave で通知が 4 回先行したが、この規律に従って全て空振りと判定できた。
     **既存規律の有効性が実証されたので変更しない**

## 次の一手差分

### 新規

- {{T:mutation-transport-bundle}} **P1・ユーザー裁定待ち**: 変異本走を計算ノードの 1 ジョブへ
  束ねる恒久実装を、(a) `dispatch_compute.TASKS` へ `mutation` task を足す (D105 supersede +
  D117 の 4 契約) か、(b) `tools/pegasus/submit_mutation.sh` を足す (D105 に触れない) かの択一。
  **推奨は (a)** — 生死確認で「環境正規化を手で写すと内側 suite が別物になる」を実測したため。
  どちらでも共通で必要な前提 6 点は {{D:mutation-transport-ruling-package}} に列挙した
- {{T:cross-node-flock-probe}} **P1・新規**: Lustre (`/work`・`/home` は `flock` mount option 付き)
  の flock が bnode 間で効くかを最小 probe で実測する。**silent fail-open なら二重注入で
  変異台帳の verdict と復元後 bytes が非決定になる。** {{T:mutation-transport-bundle}} の前提
- {{T:nqsv-walltime-signal-probe}} **P1・新規**: NQSV が walltime 超過時に SIGTERM を送るか、
  grace が何秒かを最小 probe で実測する。SIGKILL なら harness の `finally` 復元が走らず
  F32 の再発になる。{{T:mutation-transport-bundle}} の前提
- {{T:dispatch-total-deadline-queue-wait}} **P1・新規**: `tools/pegasus/dispatch_compute.py:1182` の
  `total_deadline = submitted_at + walltime_s + overall_grace_s` が**順番待ちを実行時間から
  差し引く**欠陥を塞ぐ。超過時は `_best_effort_qdel` (:1381) が**走行中のジョブを qdel** する。
  **今日の dispatch 経路にも存在する**潜在欠陥で、束ねでは発火確率が上がる
- {{T:mutation-collection-parallelism}} **P2・新規**: `_collection_command`
  (`tools/mutation_harness.py:928-942`) が dispatch のときだけ `-n 0` を足し、local 経路は
  既定 48 になる非対称を解消する。生死確認では収集列が一致したが、`_observed_status` は
  期待 node 以外の collection 差を構造的に見ないため「安全」とは結論できない
