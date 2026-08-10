---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t316-sandbox-measure
seq: 1
---

## 新規

### {{F:discharge-overrejection-unguarded}}. 過剰拒否の方向が無検査で、機能を丸ごと無効化しても全テストが緑だった [恒真ゲート] [テスト代表性]

- 事象: 変異 M7 (`if by_stage.get("S7") == "go":` → `if False:`) が SURVIVED。
  probe の R3-1 coverage から perf 由来の discharge 項目を丸ごと発行しなくしても、
  115 件のテストが 1 件も落ちなかった。等価変異ではない — 実測 receipt `0:900427.nqsv` は
  当該項目を持っており、変異を入れると観測可能に消える。
- 根本原因: `test_performance_discharge_requires_s7_go` が「S7 が go **でない**ときに
  discharge しない」方向だけを検査し、「go の**ときに** discharge する」方向を検査していなかった。
  条件付き発行を「発行しない側」だけで固定すると、発行経路を殺す変異が生き残る。
- 恒久対応: 双方向を固定するテストを追加した
  (`orchestrator/tests/test_t316_sandbox_probe.py::test_performance_discharge_when_s7_go` と
  `::test_containment_discharge_when_all_containment_stages_go`)。期待値は production から
  import せず独立 literal で持つ。2 走目で M7 は KILLED。
- 再発検知: 条件付き発行を新設する wave では、発行条件を `if False:` に潰す変異を
  事前登録する (本 wave の `output/insights/2026-08-10_t316-sandbox-measurement/mutation-spec-v2.json`
  の M7 が雛形)。静的レビュー 3 本 (敵対 2 + 焦点再) はこの穴を見つけられなかった。

### {{F:renameat2-einval-on-work}}. tmpfs でしか成立しない syscall を実出力先の前提にし、単体テストが緑のまま実機だけが落ちる形になった [テスト代表性] [計測汚染]

- 事象: receipt の atomic publish に `renameat2(RENAME_NOREPLACE)` を使ったが、この機体の `/work` は
  **通常ファイルに対しても EINVAL** を返す。単体テストは `tmp_path` (= `/tmp`、tmpfs) で走るため緑になり、
  実出力先が `/work` 配下である実機の publish だけが必ず失敗する形だった。
  90 分の測定を終えてから receipt を書けない、という最悪形の手前で親の実測が捕まえた。
- 根本原因: `docs/pegasus-runbook.md` は **directory** の create-only publish について EINVAL を
  記録していたが、通常ファイルは未実測だった。子はその未実測の隙間を埋めずに採用した。
- 恒久対応: `os.link(tmp, final)` + `os.unlink(tmp)` による create-only publish へ置換
  (親が同じ `/work` 上で新規名 OK / 既存名 EEXIST を実測)。加えて probe は起動直後に
  **実出力先 directory で publish 機構の自己検査**を行い、失敗したら測定を始める前に停止する。
- 再発検知: publish 関数へ EINVAL を注入し、canonical path に部分ファイルも `COMPLETED` も
  残さないことを検査するテストを追加した。**永続化先の filesystem が単体テストの tmp と
  異なる成果物では、その filesystem で機構を実測してから採用する。**
