---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t1281-qsub-waiter
seq: 3
---

## 新規

### {{F:hang-mutation-orphan-hold}}. hang 変異を dispatch へ投げると job が walltime まで居座り orphan-hold で wave が止まる [手順漏れ] [資源競合]

- 事象: 変異本走 (`--runner-mode dispatch`) の 11 件目で、待ち手の引数検査を外す変異が
  計算ノード job の中でハングした。harness の `hang_timeout_seconds` (300 秒) は job を止められず、
  job は自身の walltime (3,600 秒) まで実行し続けた。harness は終端証拠を取れずに orphan-hold
  (request 982386.nqsv) を立てて中止し、**変異を当てたまま作業ツリーを残した**。
  手動 `qdel` はユーザー手番の掛け金を武装させるため使えず、job の walltime 満了まで
  約 45 分、ツリーの復元も受入も land も進められなかった。
- 根本原因: 変異対象が「待ち手の deadline を守る引数検査」だったため、外した結果が赤ではなく
  **既定 6 時間の待機**になった。local runner なら probe の per-mutation timeout で観測できるが、
  dispatch では harness が子 job を kill できないので、DW-M06 が言う「超過は orphan hold 中止 +
  変異残留」がそのまま起きる。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M06` (hang 変異は `hang_risk` と timeout へ隔離し、
  timeout を fail-open の証拠とする。dispatch は `hang_timeout_seconds` < job walltime) が既に
  正本である。本 wave はこれに従い、**待ち手自身の待機時間を伸ばす型の変異を dispatch 本走から
  外し**、login 自走 probe の hang 観測を erratum として台帳へ残す運用を採った。
  復旧手順は `output/pegasus-dispatch/orphan-hold.json` の `recovery` field が正本で、
  対象の不在または終端を `qstat` の本文で確認 → `git checkout --` で dirty path を復元 →
  clean と HEAD を確認 → hold と sidecar を削除、の順に行う。
- 再発検知: 変異 spec を書く時点で「外すと待ち手の待機時間が伸びる述語か」を確かめる。
  該当するものは login 自走 probe で hang を観測して `expected_status: TIMEOUT` として記録し、
  dispatch の本走 spec には入れない。probe は per-mutation timeout と `try/finally` の復元を持ち、
  各回の前後で `git status --porcelain` が空であることを確かめる
  (`output/insights/2026-09-08_t1281-compute-waiter/evidence/probe-nodes.json` が実測)。

### {{F:new-test-file-hits-duration-ledger-gate}}. 新規 test file を足す wave は受入所要時間台帳の被覆 gate で必ず赤になり、main 取り込みのたびに同台帳で競合する [手順漏れ] [ドリフト]

- 事象: 受入全走 attempt 1 が 1 件だけ赤になった。
  `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
  が `coverage too low: 89.849780%` (覆い 19439 / 収集 21635)。本 wave が足した
  `orchestrator/tests/test_dev_wave_wait_compute.py` の 37 node は
  `orchestrator/tests/acceptance_duration_ledger.json` に 1 件も登録されていなかった。
- 帰属の実測: 同 file の 37 node を除いた反実仮想の覆いは 19439 / 21598 = 90.0037% で閾値を満たす。
  **main 側の余裕は 1 node 未満**であり、node を足す wave はどれでも閾値を割らせる。
- 根本原因: 台帳は受入 shard の割付に使う実測所要の登録簿であり、**新規 node は誰かが登録するまで
  未登録のまま**である。被覆 gate の閾値 90% に対して main の余裕が 1 node 未満まで詰まっていたため、
  node を足す側の wave がその不足を必ず顕在化させる。さらに登録簿が単一 file の追記構造なので、
  同時期に node を足した wave どうしが同じ領域で必ず衝突する。
- 是正後に二次の罠が出た。台帳へ登録すると、同じ台帳へ追記した main 側 wave
  (`a2cf07766` の 9 node、`9db6eb9b6` の 65 node) と **content conflict** になる。受入の
  post-claim merge は競合を解けず `stage=merge rc=70 reason=terminal-merge` で止まり、
  テストは 1 件も走らない。本 wave は 2 回連続で踏み、その都度 main を固定 SHA で取り込み直した。
- 恒久対応: 台帳は正本 producer
  `python3 tools/update_acceptance_duration_ledger.py --add-only <実走 JUnit>` だけで作る。
  同 flag は既存 entry を byte exact に保ち未登録 nodeid だけを足す。競合の解決も同じ経路で行う —
  main 側の現物を base に置いて producer を回し、和集合になったことを **両親の全 entry について
  欠落 0・値不一致 0・和集合外 0** で照合する。手で JSON を編集しない。閾値・凍結 prefix・
  除外集合を触るのは正しさゲートを緩める変更であり絶対規律 2 に反する。
  台帳は実装面 path なので生成は Codex `role=author` の子が行い、両親が共に触った merge の
  message には `role=author; scope=merge-composition-audit` が要る。
- 再発検知: test file を新設する wave は、段 6 の焦点走に
  `orchestrator/tests/test_acceptance_schedule_order.py` を必ず含める (`DW-O26` の
  「file 集合列挙のメタテスト」がこれに当たる)。台帳は HEAD blob 束縛なので、
  焦点走の前に登録を commit する — 未 commit のままだと
  `test_paper_story_a1_headline.py::test_existing_a1_non_touch_manifest_is_empty_from_base` が
  `git status` の非空で落ちる (本 wave で実測)。
