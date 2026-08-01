authority: none
default_effect: no-state-change

# T-126 FR3-2 closure — 段 1 brief

## scope

- 前 wave (`DW-O16` 有界終端) が real / must-fix と裁定した F3-2 だけを閉じる fresh wave とする。
- F3-2 の根本は「正規の after-publish staging hardlink が reconcile されず、放棄された証拠として
  扱われる」ことである。段 1 の前提実測により、この根本は **2 つの経路**で発火すると確定した。
- **S1 (series-result あり):** `collector.collect()` は series 有り経路で `_reconcile_job_results`
  より前に `verify_attempt()` を呼ぶ。`t126_driver.py` の unreferenced in-job evidence 判定は
  attempt 直下の `.job-result.json.create-*` を許容集合に持たないため、publish 直後 crash した
  **正常な** attempt が拒否される。B (semantic-invalid early namespace) は不要で、単独で発火する。
- **S2 (pre-series failure):** `collector.py` の semantic-conflict return が同関数内の
  `_apply_result_reconciliation` より前にあるため、A の stage が残り、closure manifest
  (`collector.py` の `_manifest`) が abandoned staging bytes として拒否する。
- 前 wave の裁定は S2 だけを射程に書いていた。S1 は同じ FR3-2 の宣言
  (「collector 単独で exact job-result staging を回収または破棄し、final / failure の
  どちらかへ閉じる」) の内側であり、scope 拡大ではなく同一 must-fix の未検出経路として扱う。

## 段 1 前提実測 (承認済み裁定の前提の再測)

- 計算 node job `874703.nqsv`、`result.rc=0`、probe `2 passed`。
  artifact: `.codex/dev-wave-t126-f32-closure-jobs/s1-premise/`。
- control (stage 無し / series あり) は final receipt へ閉じる。
  subject (stage あり / series あり / **B 無し**) は
  `series result failed read-only verification: ... unreferenced in-job evidence:
  ['.job-result.json.create-123-0123456789abcdef']` で拒否され、receipt は未発行、
  ledger は `initial_submitted` のまま。probe 前後で production source の SHA-256 は一致 (rc=0)。
- production 側の到達性: `tools/pegasus/t126_qualification.sh` は attempt dir が安全なら
  `JOB_RESULT="$ATTEMPT_DIR/job-result.json"` を使う。したがって S1 は fixture 限定でなく live。
- `collector.py` の SHA-256 は前 wave 固定値
  `9c2d3fa5ea8d556cb319f674ca287faea53f33d74fbfa5adab4cb9336be06d91` と一致し、
  `:894` / `:902` の行番号も review 記載と一致する。

## 成果物影響 (`DW-G05`)

- S1 を放置すると、**成功した qualification series** が publish と unlink の間で落ちた場合、
  final receipt も failure receipt も永久に発行されず、attempt ledger は `initial_submitted` の
  ままになる。certified 選択の材料となる series が完了も失敗確定もできない。
- S2 を放置すると、pre-series failure で rejected evidence と post-job copy を作った後も
  receipt / outcome event が出ず、正規 submitted attempt が恒久的に `initial_submitted` に残る。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** S1 の是正方向は「`verify_attempt` の許容集合へ after-publish stage を足す」より
  「`collect()` が検証前に attempt namespace の after-publish cleanup を済ませる」を優先する。
  前者は公開 verifier の受理集合を広げる方向で、正しさ防壁を緩めうる。ただし後者は
  `_apply_result_reconciliation` の「global preflight 後にだけ適用する」不変条件に触る。
  情報保存性 (after-publish stage は canonical と同一 inode / 同一 bytes) が根拠になるかを攻撃せよ。
- **(P2)** semantic-conflict return と `invalid` return の**両方**で A の stage を cleanup してよく、
  B (early job-staging) の stage は rejected evidence として保存する、と仮に裁定する。
- **(P3)** 本 wave は受理集合を「閉じられなかった正規 attempt が閉じる」方向にだけ変え、
  不正な attempt を受理する方向へは広げない。targetless staging の非昇格、別 inode /
  extra hardlink / bytes 不一致の拒否、M9a〜M9d の kill は不変とする。

## 不変条件

- evidence-only / no-promotion、`hold_enforced=false`、`statistical_claim=none`、
  qualification lineage の formal Layer3 拒否、既存 formal caller の受理集合を変えない。
- 既存の凍結成果物 bytes を変更しない (`DW-O09` / `DW-O10` は不発火)。
- 既登録 M1〜M7 と M8a〜M11b を削除・弱化せず、anchor だけ再照準する。
- Pegasus `allow_resume=false`。live run は単一 allocation / process 内で完遂する。

## 成果物

- S1 / S2 の production 修正、各経路の独立 exact fixture (series あり / pre-series の双方)、
  更新済み変異 matrix、計算 node での関連受入と全受入、統合 commit、local main 取り込み。

## 環境と分割

- build / test / check / mutation / live control はすべて Pegasus 計算ノードへ qsub する。
  login node (pegasus02) では静的読取と子の実行だけを行う。
- **ユーザー裁定 (本 wave 固有):** Codex はレートリミット近接のため使用せず、plan / 敵対相談 /
  実装 / レビューの子は Claude で代替する。親が実装面を直接編集しない凍結境界は維持する。
- 段 2 = read-only planner 1 本。段 3 = 敵対レンズ 2 本 (正しさ防壁 / 到達性・実効性) 並列。
  段 5 = 単一 author (S1 と S2 は同一関数群を触るため所有を分割しない)。段 6 = 敵対レビュー 2 本。
