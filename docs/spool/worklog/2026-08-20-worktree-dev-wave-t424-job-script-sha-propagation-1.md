---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-dev-wave-t424-job-script-sha-propagation
seq: 1
title: '[T-424] certify_calibration.sh の job-result.json へ job_script_sha256 を追加した (コード+テスト、branch worktree-dev-wave-t424-job-script-sha-propagation、変異matrix = baseline PASSED (61 passed)・2/2 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- D145 決定5 が定める floor 専用 infra 前提のうち、T-424 (job script bytes 束縛) の残余
  「hash の job-result.json までの伝播」だけを閉じた。commit `4e90b767`。
  既存 `CURRENT_SCRIPT_SHA` (certify_calibration.sh:179、submit binding 検査・reservation
  export・acquisition receipt に既に使われている値) を job-result.json の payload へ追加し、
  `tools/pegasus/collect_receipt.py` 経由で `final-receipt.json.job_result.job_script_sha256`
  として最終成果物からも読めるようにした。schema_version は `pegasus-job-result/v1` のまま維持
  (唯一の意味検証 consumer である collect_receipt.py が add-only で壊れないことを実測して確認)。
- **この記録は canonical hash (certify_calibration.sh の固定 path のハッシュ) を最終成果物へ
  記録する配線であり、`--job-script` override 実行 bytes の証明ではない。** 段3 敵対相談の
  段階で当初 brief に「override した script と実行結果の結び付きを検証できるようになる」という
  過大な表現があったが、段4 裁定でこの表現を訂正した (証拠の配線であって enforcement ではない)。
- 段3 敵対相談で新事実を発見: floor 系 (`tools/pegasus/floor_campaign.sh`) には既に同名
  `job_script_sha256` (canonical hash) と、別に実行 bytes 証明用の `executing_script_sha256`
  という2層設計が存在する。今回 certify 側に追加した値は floor 側の `job_script_sha256`
  (canonical 層) とだけ意味が一致し、`executing_script_sha256` 相当の実行 bytes 証明は
  今 wave では追加していない (scope 外、将来 wave での検討事項として記録)。
- 段6 敵対レビューが段4裁定の変異登録方針の誤りを検出: payload key 追加行の削除変異は新規
  assertion (KeyError) だけで検出されるが、argv 追加 (`$CURRENT_SCRIPT_SHA`) の削除変異は
  既存の return code assertion (`ValueError: not enough values to unpack` 由来) でも検出される
  ため、「新規 assertion だけが単一の理由で検出する」という当初裁定は argv 側には不正確だった。
  実際の変異 matrix はこの訂正を反映し、2変異 (payload key 省略・argv 省略) をそれぞれ独立に
  登録し、両方とも期待どおり同一テストノードで KILLED (完全一致) を確認した。
- T-424 の完全閉包にはまだ残余がある: override 禁止・`$0`/HEAD blob 束縛・certify/submit
  全経路の interpreter gate (T-272)・perf ノード個体差 gate・`job_script_sha256` を実際に
  検証・拒否する将来 consumer の設計 (authoritative hash が submit receipt・canonical
  path・HEAD blob・実行 `$0` のどれか、不一致時に拒否するか)。これらは D145 決定5 の
  明示的再訪裁定または専用 wave の scope とし、本 wave では実装しない。

## 次の一手差分

### 更新

- [T-424] **P2・「hash の job-result.json までの伝播」を閉じた (2026-08-20、commit
  `4e90b767`)**: `job-result.json`/`final-receipt.json.job_result` へ `job_script_sha256`
  (canonical script path の hash) を追加した。残余 (override 禁止・`$0`/HEAD blob 束縛・
  interpreter gate・perf ノード個体差 gate・将来 consumer 設計) は未着手のまま。一次資料は
  本 entry と `output/insights/2026-08-20_t425-dependency-reaudit/README.md` (b)節。
  base: 19a1801c5198b7b53ae159a9711a49de4f9b38edf123f63cb6febe97f3e6f89f
