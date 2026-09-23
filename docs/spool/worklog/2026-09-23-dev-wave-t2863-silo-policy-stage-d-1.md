---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: dev-wave-t2863-silo-policy-stage-d
seq: 1
title: [T-2863] silo-function-policy 軸の段階 D (型付き有限 IR の機械偵察) を実装・実測し、二値 = true (固定 16 点の全点が両 verify certified で同 job の abort0 比 1.34〜1.78、先頭 4 点が別 job で再現) を得た — IR・描画・列挙・偵察 driver を Codex author が書き、初走をユーザー指示で 8 job に割って同時投入 (コード + test + 計測 JSON + insight、branch dev-wave/t2863-silo-policy-stage-d)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `output/insights/2026-09-23/t2863-silo-policy-stage-d/verbatim/request.md`): 設計 §5 の型付き有限 IR の生成器・列挙・偵察 driver を Codex author で書き、段階 C の診断経路を再利用する。記録 = 同 insight の README、設計判断 = {{D:silo-policy-stage-d-recon}}。
- 起点 = local main `cadaf3805` (fresh worktree、開始 gate rc=0)。wave 中に local main を 2 回取り込んだ (`fb12a492b` 早送り、`b14d8b01c` を merge `4eab7c65c`)。設計択一が割れ受理集合 (偵察の判定) を新設するので、DW-C00 により段 2・3・6 の独立検証子を省かなかった。
- **計算投入のユーザー確認:** 段 4 で用途別の見積り (シナリオ 約 1.7〜3.1、walltime 上限で 4.0 node 時間) を示し、「上限 4.0 h で承認」を得た。作業中にユーザーから「一瞬で終わらせてね。計算ジョブを分割して投げることで」→ 初走を 2 job から 8 job に、再測を候補ごとの別 job に変えた (段 4 裁定 §6)。
- **段 3 相談は 2 本とも NO-GO** (job の偶奇分割が因子 M と完全交絡、集計の入力照合の欠如、二値の射程を固定 16 点へ限定、見積りを用途別総額に)。全件を段 4 で採用。
- **二値 = true。** 16 点すべて legacy と write-heavy 性能構成の両 verify で certified (anomaly 0)、同 job の abort0 比 1.34〜1.78、ID 順の先頭 4 点が別 job で 1.53〜1.62 を再現。限定: 基準 abort0 は abort 率 0.78 の thrashing 点で、待機を入れる方策ならほぼ何でも 3% 線を越える。既知最良 (調整済みの静的・適応 backoff) を超える地形があるかには答えていない。軸 OFF の参考値は stock 1,355・`B0-L-W0` 2,423 千 txn/s (同 job の abort0 2,407)。後段へ渡すのは投影 `output/env/pegasus/calibration/silo_function_policy_recon/projection.json` の二値と射程文だけ (手順書 §3-D の firewall)。insight を読んだ事実は段階 E / F の campaign provenance に記録する義務を残す。
- **実行上の事実:** 子が書いた新しい投入 script は投入許可台帳に未登録で実行できず、既存の `dispatch_compute.py --task generic` を計測用 worktree 8 本から使った (dispatch は checkout ごとに同時 1 本)。gen_S の同時実行は 3〜4 本で頭打ち、初走 job 7 は Pre-running のまま 20 分以上止まったので別の木から投げ直して先着を採用 (元 request も後で完了、記録のみ)。generic dispatch は環境変数を消すので結果の `pbs_jobid` は null になり、集計の job 識別を (hostname, started_at) に直した (段 6 fix 2)。
- **段 6:** レビュー 2 本 (NO-GO、must-fix = 集計の固定 workload・対照の照合、不採用 script の test)、fix 2 巡、焦点再レビュー 1 巡 (残 2 件は nit / 仮想リスクで不採用)。
- **near miss:** 前方 merge の provenance 事前検査と commit を並列 tool call で投げ、検査が赤でも commit が走った。未 land のうちに取り消し、3 版合成でやり直した (F37 の再発として記録)。
- 計算ノードの使用 (job Elapse): 計測 13 job 5,311 秒 (初走 8 本 3,661 秒、job 7 の重複 430 秒、再測 4 本 1,220 秒)、焦点走 4 回 253 秒、変異と受入は本記録の後の値を land の受領証と insight に残す。
- 工数: Codex 子 = plan 1、consult 2、author 2、review 2、fix 2、focus 1、前方 merge の合成 1 の計 11 本。

## 次の一手差分

### 完了

- [T-2863] 段階 D を実装・実測し、二値 = true を得た (記録 = `output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md`、設計判断 = {{D:silo-policy-stage-d-recon}})。
  remaining: none
  base: ed9804a6845f225a2ad4bcce4e0b046c7a18c67ed714ebe9da9b13ab59b93cd7

### 新規

- {{T:silo-policy-after-recon}} **P1・ユーザー判断待ち**: silo-function-policy 軸を段階 E (LLM ループ実装、`.claude/agents/` の coder 新設・auditor 改訂の具体差分はユーザー明示承認が要る、D2214 必須条件 11) へ進めるか、見直すか。偵察の二値は true だが、基準 abort0 に対する 3% 線は易しい問いで、既知最良を超える地形の有無は未確認 (insight §4)。
  - 推奨: 進める。ただし段階 E の前に、同じ 8 job 構成で既知最良の参照 (元の適用方法の調整済み静的 backoff と `B0-L-W0`・stock) を同 job に置いた小さな比較を 1 回だけ足すかを、ユーザーが決める (計算は投入前に確認)。
  - 後段へ渡してよいのは `projection.json` の二値と射程文だけ。
