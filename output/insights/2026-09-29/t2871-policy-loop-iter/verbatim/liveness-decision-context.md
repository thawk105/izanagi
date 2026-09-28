# [T-2871] 生死確認の形の判断材料 (親、2026-09-29 05:20 JST)

## 事実 (実測)
- 実装 tip d7161a2a1: pair 経路の候補と stock を `policy_iteration` 付きの計測 campaign で測る。焦点走 (計算ノード 33701.nqsv) 393 passed。結合検査 T1〜T3 は driver `main` を別 process で直列に 2 回、実 `_authorize_measurement`・実 `acquire_claim`・実 `check_reservation` で通す (build・bench・trace は模擬)。
- 段 4 裁定 §6 の生死確認: 新しい submit checkout で t2865 の auditor 通過済み proposal prop-2 → prop-3 を pair job として**直列に 2 本** (本番入口 = job body `tools/pegasus/p3_s4_loop_pegasus.sh`)。
- 投入済み: 1 本目 33730.nqsv (04:03 投入、prop-2)、2 本目 33800.nqsv (05:15 投入、prop-3、`qsub --after 33730.nqsv`、要求 walltime 1800 s に変更済み)。
- 待ち行列: gen_S 実行中 23・待ち 67 (他の並走 wave の job も多い)。sstat の予定開始は 1 本目 07:13、2 本目 14:42。
- 系列の walltime 予算 `MAX_WALLTIME_S = 3600` は系列の `loop_state.json` の作成時刻 (= 1 本目の job の driver 起動) から数え、待ち行列の時間も含む (runbook §1(f))。2 本目は `drive_iteration` の冒頭で予算を見て、超えていれば `stopped-before` を返し claim も計測もしない。予算の値の変更は依頼の scope 外 (D2256 項 3)。
- pair 1 本の Elapse 実測 786 s (t2865 31855)。
- 計算量: ここまで焦点走 4 回で約 3 分、変異と受入が残る。見積り合計 ≈ 1.03 node 時間 (< 2)。

## 選択肢
- A: 今の 2 job のまま待つ。2 本目が予算で `stopped-before` になったら、その事実を記録し、待ち行列が空いた時点で新しい submit checkout で同じ 2 本をもう一度流す (再試行は 1 回まで)。
- B: 本番入口の 2 job (A) は残しつつ、加えて 1 本の計算ノード job の中で driver を別 process で 2 回 (prop-2 → prop-3) 直列に起動する小さな script を使う。実 reservation・実 claim root・実 build/verify/bench を計算ノードで通すが、job body の 2 回目ではなく、2 本目は同じ job id。
- C: A だけにし、予算で止まったら生死確認は「未完」と記録して wave を閉じ、系列の予算の扱いは別 task として起票する。
- D: (codex が見つけた別案)

## 制約
- 絶対規律 2 (正しさゲートを緩めない)、claim leaf と one-shot 性は不変、claim の手動退避はしない、予算の値を変えない、仮想リスク向けの検査を足さない。
- ユーザーは就寝中。マネージャー指示: 判断待ちで止まらず codex と決める。
