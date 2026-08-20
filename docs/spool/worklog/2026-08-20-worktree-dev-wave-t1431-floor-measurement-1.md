---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-dev-wave-t1431-floor-measurement
seq: 1
title: '[T-1431] 床値pilotの実測を試みたが、source_digest.pyがmocc protocolの実供給マクロを認識せずbuild段階でfail-closed停止した — [T-1256]は解消済みと実証、新blockerは記録のみで実装せず (docsのみ、branch worktree-dev-wave-t1431-floor-measurement)'
---

## 本文

- D581 (2026-08-20、decisions.md:23453、「床値measurementは事前登録なしの粗いprovenanceで
  十分」) に従い、`orchestrator/campaign/s8b_floor_campaign.py` pilot mode で床値の実測実行を
  試みた ([T-1431]、entry 727 起票)。
- **[T-1256] (worklog archive 601、床値pilotが標準投入経路から1回も走れない問題) は既に
  解消済みと実証した。** `tools/pegasus/submit_floor.sh --dry-run --confirm-irreversible-pilot-holdout`
  を実行 (main checkout・wave worktree の双方) したところ、`qsub -v` へ
  `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=<nonce>` が正しく渡ることを確認した
  (`submit_floor.sh:44,489` は対応済み)。追加のコード修正は不要と判断した。
- 投入前 preflight (本日実測、全て green): `git ls-tree HEAD external/ccbench` = `511c9538e4e8…`、
  `resolve-current-protocol` rc=0 (現行 ccbench pin と整合する世代別 protocol へ解決)、
  `test_frozen_artifacts.py` = 5 passed/0 failed、oracle gate-check rc=2 (refusals = 厳密に
  floor-null/budget-null の2件のみ)、`qstat -u tanab` 投入直前空。設計択一は既存裁定
  ([T-748] 裁定(c) 等、`docs/phase3-8b-restart-runbook.md`) で既に決着済みで正しさ防壁・
  受理集合に触れないため、段2/3 の codex 起草・敵対相談は省略 (根拠は専用 handoff に明記)、
  Codex子は0本。
- `tools/pegasus/submit_floor.sh --confirm-irreversible-pilot-holdout` で実投入
  (request ID `926261.nqsv`、nonce `70b9b8a087bb1e6d9af4ac248ff3c040`、投入元 commit
  `9fb521662…`、queue gen_S、10h割当)。投入から45秒 (13:15:06〜13:15:51) で driver が
  rc=1 を返し `floor_campaign.sh` は正しく fail-closed 停止した (floor_campaign.sh 自体の
  挙動は正常)。admission・attestation・toolchain束縛 (R-4)・protocol解決・gflags/glog依存
  ビルドは全て通過しており、停止点は mocc protocol の実ソースビルド準備段階
  (`source_digest.resolve`) だった。
- **新規 blocker: `source_digest.py` の `_SUPPLY_RE` 正規表現 (`(\w+)=\$\{CCBENCH_(\w+)\}`)
  が `external/ccbench/cc/mocc/CMakeLists.txt` の裸オプション `RWLOCK` を構造的に
  拾えない。** `TEMPERATURE_RESET_OPT=${CCBENCH_TEMPERATURE_RESET_OPT}` は形式上マッチする
  はずだが同様に「未知」と判定されており、`parse_supplied_macros` へ渡る `protocol_cmake_text`
  自体が mocc の CMakeLists.txt を指していない疑いがある (呼出し元の特定は未実施)。
  `MQLOCK` は現行ビルド設定に存在せず死コードの可能性が高い。stock_configuration
  (LLM変異を含まない基準構成) で発生しており、floor 実測固有ではなく mocc protocol を使う
  限り pilot/official 問わず再現する構造的 gap と判断した。file:line 裏取り・調査の詳細・
  admission チケット消費ゼロの確認 (claims/consumed 両ディレクトリとも本 job 実行時刻以降の
  新規ファイル 0 件) は正本 `output/insights/2026-08-20_t1431-floor-pilot-measurement/README.md`
  を参照。
- この blocker の修正は `source_digest.py` の identity 計算基盤 (CLAUDE.md 絶対規律1・2・6、
  D23・T-148 の設計意図) に直接触れる実装面変更であり、独立した wave として brief・plan・
  段3敵対相談を経るべき規模と判断し、本 wave では実装しなかった (段階導入の原則、規律5)。
  新task ({{T:fix-source-digest-mocc-supplied-macros}}) として切り出した。
- **エージェント工数**: 0 (Codex子を起動していない。段2/3/5/6 を全て省略した軽量版)。

## 次の一手差分

### 完了

- [T-1256] `tools/pegasus/submit_floor.sh --dry-run --confirm-irreversible-pilot-holdout` の
  実地検証により、標準投入経路が pilot 承認フラグを正しく driver へ渡すことを確認した。
  追加のコード修正は不要。
  remaining: none
  base: a5350656dad31c3c662ad35fa972d98a7bb75004cba668275e354143b77445c3

### 更新

- [T-1431] **P1・実行を試みたが新blocker (source_digest/mocc) で床値の実測値は未取得
  (2026-08-20)**: D581 に従い床値pilotを実投入したが、mocc protocol の実ソースビルド準備段階
  (`source_digest.resolve`) で fail-closed 停止し、実測値は0件のまま。[T-1256] は解消済みと
  実証済み (上記「完了」参照)。admission チケットは1枚も消費していない
  (`retry_slots_per_cell=2` を12セル分フル保持のまま)。新task
  {{T:fix-source-digest-mocc-supplied-macros}} の解消後、本insightの投入パラメータ
  (`output/insights/2026-08-20_t1431-floor-pilot-measurement/README.md`) をそのまま
  再利用して再投入できる (admission・toolchain・protocol は健全と確認済み)。
  base: 16d665b87b236f2ece6453c861767a4eb6a9b363d0e1e83d67565ee0c4cd6c3b

### 新規

- {{T:fix-source-digest-mocc-supplied-macros}} **P1・新規**: `source_digest.py` の
  `parse_supplied_macros`/`_SUPPLY_RE` が mocc protocol (`external/ccbench/cc/mocc/
  CMakeLists.txt`) の実供給マクロ (`RWLOCK` 裸オプション、`TEMPERATURE_RESET_OPT=${...}`)
  を認識せず、stock ソースの build 準備段階で fail-closed 停止する ([T-1431] 2026-08-20
  実測で発見)。段1 brief の出発点は
  `output/insights/2026-08-20_t1431-floor-pilot-measurement/README.md` の「推奨する次の一手」
  節 (呼出し元での `protocol_cmake_text` 実体確認・裸オプションの扱い設計・MQLOCK死コード
  判定・再発防止テスト追加の4点)。correctness/observer-effect境界 (規律1・2・6) に触れるため
  Codex `role=author` 必須、段2/3の敵対相談を省略しない。
