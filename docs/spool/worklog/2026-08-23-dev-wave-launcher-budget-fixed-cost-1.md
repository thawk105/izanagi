---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-launcher-budget-fixed-cost
seq: 1
title: launcher の受理締切を 3 区間へ分け、被験体でない準備と最終化を attempt 予算から外した (コード+テスト+docs、branch worktree-dev-wave-launcher-budget-fixed-cost、変異matrix = baseline PASSED・MUT-1〜7 7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー指示は「環境条件で不安定に失敗するテストを除外し、除外したものを環境非依存に
  検証できるようにして再導入する」だった。**前半は並行セッションが先行して実装を終えていた**
  ため、追加指示「似たことをしている並行セッションと通信し、被らない改善を行う」に従って
  分担を確定した。並行 2 セッションへ照会し、`flaky test exclusion and remediation` が
  後続 P2 として、`pegasus test distribution optimization` が scope 外として、
  どちらも明示的に launcher の締切を本 wave へ譲った。**両ピアの保持 file と交差しない
  唯一の残件**でもあった。設計判断は {{D:launcher-three-interval-budget}}。
- **親の因果帰属が 2 度誤り、2 度とも自分で訂正した。** (a) 当初 240 MB の codex 実行ファイルの
  hash (0.83〜0.87 秒) を主要因と帰属したが、テストは `_write_fake_codex` の偽 codex を使うので
  無関係だった。(b) 訂正後に取った実走 1281 件の分布を並行セッションが F57 の記録へ
  取り込もうとしたので止めた — その母集合は本物の 240 MB codex を使う走行であり、
  偽 codex を使うテスト regime へ絶対値を転移できない。{{F:aggregate-smuggles-regime-term}}。
- 実測: 実走 launcher の診断成果物 1281 件で、準備 (job 起点→`attempt_state_created`) は
  p50 0.678 s / p90 0.975 s / p99 1.672 s / max 3.792 s、seal は p50 0.0058 s、
  最終化 (`attempt_sealed`→`receipt_published`) は p50 0.986 s / max 4.940 s。
  **最終化が成果物 hash に支配されるという親の仮説は否定された** — stdout 10 KB 未満の帯でも
  p50 0.809 s の床がある (n=1262)。この事実が段 3 両レンズの blocker を裏づけ、
  当初の「準備だけ控除する」設計を 3 区間へ作り替える根拠になった。
- **段 3 と段 6 の敵対レンズが計 6 件の blocker を出し、うち 2 件は両レンズ独立一致した**
  (seal 区間がどの予算にも属さない、atomic 公開が最後の判定より後)。
  **焦点走はどちらも検出していない。** どちらも「実行はするが判定されない時間」で、
  緑のテストでは見えない型だった。
- **裁定の中心要求が実装で未達だった。** `codex --version` は caller 指定の codex を実行する
  ので被験体だが、process group の作成も終了確認もない素の `subprocess.run` であり、
  子を fork して detach されると計測から逃げられた。段 6 レビュー A が指摘するまで気づかなかった。
- **guard 不一致時に被験体が走る穴を、テストが構造的に見られていなかった**
  ({{F:guard-blind-to-subprocess-run}})。version を process group 起動へ変えた副作用として
  初めて可視化された。
- 実走の赤は `11 → 3 → 1 → 0` と収束した。**11 件の内訳は実装の回帰 3 件と期待値の正当なずれ
  8 件で、親が事前に静的に予想した 7 件とは件数も内訳も違った。** 予想では緑を保つとした
  node が動き、動くとした node が緑のままだった。**この種の予想は実走なしでは決まらない。**
- 期待値を更新した 8 node は、検査していた性質を移動先の gate で同じ強さで assert し直した。
  とくに後段 audit / staging の 2 件は D256 の最終可逆点の保護 (公開済み出力の削除) を
  最終化 gate 側で assert し直しており、保護は移動しただけで失われていない。
- **変異 probe が gate の二層構造を暴いた。** 単層だけ無効化した MUT-1 / MUT-2 は
  注入実在 (`anchor_counts` 1、`injection_diff_sha256` あり) にもかかわらず 212 passed で
  SURVIVED した。準備 gate も最終化 gate も 2 層あり、片方を殺しても他方が捕まえていた。
  `DW-M02` に従い両層同時変異へ再照準し、probe 2 で node を集めてから本走した。
  probe 1 は erratum として保全 (`mutation-probe-result-1.json`)。
- 新設テストの予算は実測 tail から決めた。準備 8 秒 (実測 max 3.792 秒の 2.11 倍)、
  最終化 10 秒 (実測 max 4.940 秒の 2.02 倍)、外側 watchdog 30 秒。
  **8+2+10+5=25 < 30 という不等式を、定数でなくテスト自身が検査する。**
  段 6 レビュー B が「このフレーク修理が別のフレークを生む」と指摘して是正させたもので、
  並行セッションも同じ型を踏んでいた (新設 control の `timeout=60` が負荷で先に発火)。
- 並行セッションへ「tail 余裕」の書式 5 項目を渡した (母集合 / **regime** / tail は max /
  倍率は正例 2 倍以上 / **負例は逆で確実に発火する小さい値**)。regime を独立項目に昇格させたのは、
  母集合を書かせるだけでは regime 差を見落とす実例が出たためである。

## 次の一手差分

### 完了

- [T-1549] launcher の attempt 本体時間と周辺固定費を切り分け、締切を 3 区間 (準備 / 監督実行 /
  最終化) へ分けて環境非依存にした。予算の一律引き上げは採らず、`codex --version` は
  被験体として attempt 予算へ算入したうえ process group 監督下に置いた。
  remaining: none
  base: 1bb9310fcfd688e6a8c73e7cf3ed5bdcd9e53f8d0f76df6ae249855dae4a2515

### 新規

- {{T:launcher-preparation-hard-cap}} **P2・新規**: 準備区間に物理 hard cap を与える。
  現状の準備上限は既存 wall 上限と同じ polled admission 検査であり、import や
  uninterruptible I/O が停止すると次の検査点へ到達しないため止められない。
  **これは本 wave が強度を下げたのではなく、既存 wall 上限と同じ強度に揃えた結果である。**
  launcher の import より外側に watchdog を置く必要があり、`tools/dev_wave_codex.py` の
  呼び出し形と背景 job の detach 契約に触れるため本 wave の scope 外とした。
- {{T:revert-launcher-max-wall-raises}} **P2・新規**: 並行セッションが F57 修理で
  23 node へ入れた `max_wall` の引き上げが、準備費の控除後も必要かを実測して戻す。
  引き上げは準備費が 3 秒予算を食う前提での暫定措置であり、本 wave で前提が消えた。
  **ただし「素の予算で緑になる」ことを実測で示してから戻すこと。**
  wall の発火に暗黙に依存して意図的にハングする fake を終わらせている node があり、
  一括適用は 7 failed を 60 failed へ悪化させた実績がある (並行セッション実測)。
