# T-755 Q2: mocc trace v2 (izanagi [T-816]) TRACE=1 正しさ検証パイロット結果

## 位置づけ

`docs/decisions.md` D579 が認可した mocc trace-hook (`cc/mocc/transaction.cc` の trace v2、
[T-816] 由来) の**初回実機実行**。段6敵対レビュー2巡+fix2段+焦点再レビューまで完了し main
着地済みの adapter (`tools/pegasus/submit_mocc_trace.sh`, `tools/pegasus/mocc_trace_pilot.sh`)
を実際に Pegasus 計算ノードで qsub し、C/R/W/E トレースを回収して
`orchestrator.verifier` で serializability を検査した。

**規律1 (観測者効果の分離) の遵守。** これは TRACE=1 の正しさ検証専用 build・run であり、
TRACE=0 の性能計測とは別 build・別 run。本 insight の数値 (transaction 数・elapsed 等) は
性能主張に使わない — `throughput_json` は生成されていない (TRACE=1 分岐、
`mocc_trace_pilot.sh:911` 以降の `else` 分岐が担う throughput 計測はこの run では通らない)。

## 実行条件

- 対象 commit (outer): `2efe6282ed22a694cdd7b38c641bedecc6d2e6d4`
- submodule (`external/ccbench`) source binding: base_oid `511c9538e4e8efa54b45cda62e72389ed3b706ec`
  → new_oid `ef9328a35d49b1b9b610f244bee22ad7f10b8b66` (mocc-trace-v2.patch 適用済み、
  D579 の限定認可範囲内。outer gitlink は未前進、D579 の方針どおり)
- workload: `records=10000, threads=48, zipf_skew=0.9, ycsb_rratio=50, ycsb_rmw=0,
  ycsb_max_ope=10, extime_s=3` — **親選定のpilot値であり、historical T-816測定の再現ではない**
  (`mocc_trace_v1_policy.json` 記載どおり)
- 実行host: bnode050 (Intel(R) Xeon(R) Platinum 8468, 48 physical cores, HT off) —
  policy期待値と一致確認済み
- PBS request 934607.nqsv、gen_S、2026-08-22

## 検証結果 (verifier構造化出力、全文)

`python3 -m orchestrator.verifier <trace_dir> --json --expected-commits 761914` を、
(a) compute-node上のjob本体、(b) login nodeからの独立再実行、の2回実行し**byte-for-byte
一致**を確認した。

**追記 (2026-08-23、land 引き継ぎ wave の敵対監査による補正)。** 上の `python3` は表記の略で
ある。(a) の job 本体は `python3` を直接呼ばず、環境 gate が `python3 python3.10 python3.11
python3.12` の順に「`orchestrator.verifier` を import でき、かつ `sys.version_info >= (3, 10)`」
を満たす最初の候補を解決し、その絶対 path (`VERIFIER_PY`) で起動する
(`tools/pegasus/mocc_trace_pilot.sh` の verifier 起動 block)。**この run で実際に選ばれた
interpreter の実体 path は記録されていない** — script は `VERIFIER_PY` を receipt にも log にも
書かない。判定値 (`verdict` / `anomaly_count` / `integrity`) はこの差の影響を受けないが、
版数 gate を通過した interpreter の実行証跡は台帳から辿れない。記録を足す改修は実装面のため
引き継ぎ wave の scope 外とし、次の一手の候補として worklog へ残した。

```json
{
  "runs": 1,
  "certified_serializable": 1,
  "non_serializable": 0,
  "indeterminate": 0,
  "results": [
    {
      "verdict": "serializable",
      "certified": true,
      "serializable": true,
      "stats": {
        "txns": 761914,
        "reads": 3687083,
        "writes": 3743284,
        "keys": 10000,
        "edges": 10749963,
        "abort_reasons": {}
      },
      "integrity": {
        "clean": true,
        "orphan_reads": 0,
        "version_dups": 0,
        "dup_txids": 0,
        "genesis_commits": 0,
        "missing_txids": 0,
        "write_version_mismatch": 0,
        "malformed_keys": 0,
        "framing_violations": 0,
        "lock_coverage_violations": 0,
        "write_intent_violations": 0,
        "permutation_violations": 0,
        "notes": []
      },
      "anomaly_count": 0,
      "total_cycles": 0,
      "anomalies": []
    }
  ]
}
```

**761,914 transaction (read 3,687,083・write 3,743,284)、依存グラフ 10,749,963 edge に対し、
G2 を含むcycleは0件、12種の整合性検査 (orphan reads・version重複・txid重複・genesis commit・
txid欠落・write-version不一致・key不正・framing違反・lock coverage違反・write-intent違反・
permutation違反) すべてclean。** mocc trace v2 hookが生成したTRACE=1トレースは、この
pilot workload条件下でserializableとverifierに認証された。

## scope・限界 (正直に)

- `official_certification: false`、`pilot: true` (receipt記載どおり)。正式な H1/H2 launch や
  T-424/T-272 の要求閉包を代行しない (D658と同型の切り分け)。
- pilot workload 1本・1 runのみ。異なるworkload形状 (rratio・skew・records・threads・実行時間)
  での再現性は未検証。将来の本格ablationは別waveのscopeとする (規律4/規律5、無造作にスケール
  拡大しない)。
- TRACE=0の性能計測はmocc-trace-v2.patchのtrace.hh include行のコメント残存
  (`tools/check_trace0_preprocess_identity.py`がreject) により本waveでは未実施 — 別途
  人間手番のcommitが要る (worklog entry 812)。**TRACE=1の本結果はこの欠陥の影響を受けない**
  (TRACE=0/TRACE=1は規律1によりビルドから分離されている)。
- `abort_reasons: {}`が空である理由は未調査 (trace formatが abort 理由を記録しない設計か、
  この pilot run でaborted transactionが実際に0件だったかは未確認)。次回このtrace形式を
  使う wave が気になれば調査するとよい。

## 実機実行で発見・修正した adapter 欠陥 (2件、正しさ検証ロジック自体ではなくtooling)

段6レビュー (コードリーディング中心) では検出できず、実機実行で初めて発現した。詳細は
`docs/decisions.md` の対応するD (fold後に採番) 参照。

1. **CPU model環境gateの厳密文字列比較バグ。** `/proc/cpuinfo`の実測値
   (`Intel(R) Xeon(R) Platinum 8468`、商標記号付き) とpolicy期待値
   (`Intel Xeon Platinum 8468`) の表記ゆれで偽陽性拒否。sibling script
   `t141_region_profile.sh`の正規化パターンを移植して解消 (commit `7e0178d8`)。
2. **verifier起動のPython版数解決バグ。** 計算ノード既定の`python3`がIntel Python 3.9系
   (module `intelpython/2022.3.1`) に解決され`orchestrator`パッケージをimportできず
   `python3 -m orchestrator.verifier`が`ModuleNotFoundError`で失敗。`floor_campaign.sh`等の
   既存版数gateパターンを移植して解消 (commit `2efe6282`)。

両修正とも段2プラン→段3敵対相談2レンズ→段4裁定→段5 Codex実装→段6敵対レビュー2レンズの
フルサイクルを経て、手動mutation kill-checkで回帰検出力を実測確認済み。

3件目の障害 (worktree-local third-party staging area
`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/masstree`に前回attemptの
build成果物が残存し`fetch_third_party.py`のhardened検証に拒否された) は adapter の
コード欠陥ではなく、同一worktree内での複数attempt間の環境状態 (job間で永続するstaging area)
に起因する運用上の事象であり、staging tree削除で解消した。実装面の変更はしていない。
