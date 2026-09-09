---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2536-cicada-axis-name
seq: 1
title: [T-2536] genome 軸名を CCBench 実体の CMake cache 変数へ合わせ、対応の崩れを検査する — cicada を認定の対象にする前提を 1 つ除去した (コード + テスト + insight、branch worktree-dev-wave-t2536-cicada-axis-name、変異 5/5 KILLED・期待 node 完全一致)
---

## 本文

- 一次資料は `output/insights/2026-09-10_t2536-cicada-axis-name/`。逐語 10 本と変異 spec / ledger 各 2 本を置いた。
  設計判断は {{D:genome-axis-cache-name-table}}。
- **依頼が名指しした場所と欠陥の実体がずれていた。** 依頼は「認定 launcher の軸」と書いたが、
  汎用写像の実体は `orchestrator/campaign/model.py` の `Genome.cmake_defines()` で、ビルド本経路
  (`buildcache`) と screening も同じ仮定を共有していた。認定 launcher には cicada の枝が無い。
  親は brief でこの差を出し、段 4 で producer 側の修正として裁定した。
- **段 3 の 2 レンズが独立に同じ穴へ収束した。** protocol 内で 2 軸が同じ cache 変数へ潰れる形を
  誰も検査していない。親が既存 parser を probe で叩いて、同じ左辺の衝突は fails-closed だが
  この形は素通りすることを実測し、実装に拒否と検査を入れた。
- **段 3 が親 brief の過剰一般化を 1 つ訂正した。** brief は「cicada の live build 経路は現存しない」と
  書いたが、専用 driver が無いだけで generic caller から到達できる。欠陥は仮想ではなく現存する。
- **段 3 の棄却 finding:** レンズ A は 4 件 (逆写像が D1864 の alias に当たる / 既存 4 拒否の死亡 /
  現行 drift 検査の負例が空 / screening 2 置換による argv byte 差)、レンズ B は 3 件
  (import 循環 / 裸 option と universal 合成の誤用 / 射影内既存テストへの波及) を自ら refuted と判定した。
- **段 6 の敵対レビューが、追加 8 nodeid を全部通過する非等価変異を 5 種類構成した。**
  forward が表と食い違う / 単射性検査が 1 protocol でしか発火しない / 逆引きに suffix alias を足す /
  cli の逆変換が cicada でしか検査されていない / drift 検査 helper が cicada だけ実体を読む。
  **5 件ともテスト側だけで閉じ、実装は 1 byte も変えていない。**
- **段 6 が検査の偽陽性の種を 1 件見つけた。** `source_digest.parse_options_defaults` は空値の cache
  entry を意図的に除外するので、それを「宣言済み cache 名の一覧」として使うと、CCBench が既定値を
  空にする正当な変更だけで赤になる。照合を外し、空 default の正例を足した。
- **段 4 が scope 外と裁定した pin が実装に混入していたのを段 6 が見つけた。** 表の件数 17 と
  「非恒等写像は cicada 1 件だけ」の固定値である。実体表との exact equality で契約は閉じており、
  正当な軸追加で単独に赤くなるだけなので両方外した。
- **親が採らなかった real 所見 3 件は裁定パッケージへ回した** (下記 新規 3 項)。とくに
  「build cache identity が写像を束縛しない」は機構としては正しいが、発火前提の cicada cache 項目は
  実測 0 件で、将来の写像変更は `ccbench_commit` か本 wave の drift 検査が止める。
  cache identity は全 protocol 共有の同一性コードなので、依頼が除外した一般化に当たると判断した。
- **セッション異常 1:** 焦点走の 1 回目が `queue-wait-timeout` (rc=16、`child_started=false`) で
  落ちた。変更に帰属しない infra 障害である。D612 の opt-in 上書き (queue 3600 / grace 600) を
  付けて再投入し、20 file が 1744 passed / 23 skipped で緑になった (130.92s)。
- **セッション異常 2:** 親が自分で掛けた 900 秒の timeout で 1 回目の単独走が rc=124 で切れた。
  出力は 1 行も flush されていなかった。赤ではない。
- **変異走行の手順で 2 つの門に当たった** (段 8 で `docs/dev-wave/mutation.md` へ収容)。
  (a) spec / out / attempt-out は試験対象 checkout の外に置く必要がある。insight dir へ置いたら
  起動前に拒否された。(b) spec の `timeout_seconds` は dispatch 待機契約 (queue_wait + grace) 以上で
  なければならない。D612 上書きを使うと 4200 秒以上が要る。
- **変異は probe → 本走の 2 段で回した。** probe は全件 SURVIVED で登録して観測 node を集め、
  本走 spec はその実測から機械生成した。本走は 5/5 KILLED、期待 node 完全一致、baseline PASSED。
  runner argv は `orchestrator/tests/test_pegasus_calibration_workload.py` 1 本に限った —
  `model.py` は contract loader 源であり、変異中の dirty tree で他 file を走らせると
  contract-loader-drift の赤が混じって単一理由性が壊れるためである。
- **エージェント工数:** codex 子 7 本 (plan 1 / consult 2 / author 1 / review 2 / fix 1)、
  model call 合計 170 回。全子 `outcome=accepted`。receipt は job artifact 側にある。

## 次の一手差分

### 完了

- [T-2536] `SPACES` の cicada 軸 `INLINE_VERSION_OPT` を CCBench 実体の
  `CCBENCH_INLINE_VERSION_OPT_CICADA` へ合わせ、対応が崩れたら落ちる検査を同じ変更単位に置いた。
  上流の死にコードの insight 化は本 wave の依頼から外れていたので新規項へ切り出した。
  remaining: none
  base: 7ebbd0eb0231c12c293c29c63734b8ff7877183e4a889234d6f9fd9b018e3391

### 新規

- {{T:cicada-certification-acceptance-set}} **P2・新規**: cicada を認定較正の受理集合へ入れる。
  `tools/pegasus/certify_calibration.sh` に cicada の case と build target を足し、
  `tools/pegasus/submit_certify.sh` の protocol 白名を広げる。前提だった軸名の対応は本 wave で
  除去済み。`INLINE_VERSION_OPT=1` が上流の死にコードでビルド不能という別問題を含むので、
  較正 genome の値選択をこの wave で決める必要がある。
- {{T:cicada-inline-version-opt-upstream-dead-code}} **P3・新規**: 正しい cache 名で
  `INLINE_VERSION_OPT=1` を渡すと `cc/cicada/include/transaction.hh` の `write()` が POSIX
  `write(int,...)` へ解決されてビルドが落ちる上流の死にコードを、`output/README.md` の形式で
  上流 insight にする。この観測は [T-2224] の wave が得たもので、本 wave では再実測していない。
- {{T:build-cache-identity-binds-cache-name-mapping}} **P3・新規**: `buildcache.cache_key()` と
  v2 identity の pre-image に、軸名から cache 変数名への写像を束縛するかを裁定する。
  現行の pre-image は configure argv を含まないので、写像が変わると同じ key で別内容のバイナリを
  hit しうる。実測では該当する cicada cache 項目は 0 件で、CCBench 側の変更は `ccbench_commit` が、
  izanagi 側の変更は {{D:genome-axis-cache-name-table}} の drift 検査が止める。全 protocol 共有の
  同一性コードを触るため、費用と受理集合への影響を含めて裁定する。
- {{T:receipt-unmapped-cache-variable-policy}} **P3・新規**: 受領証 genome の復元が、軸に写らない
  余剰 define (別 protocol の scoped 名、表外の名前、二重接頭辞) を canonical genome へ載せることを
  許すかを裁定する。現行はこれを要求している — 認定 launcher が silo へ patch 供給の
  `-DCCBENCH_BACKOFF_FIXED=-1` を渡し、`orchestrator/tests/test_calibrator_certify.py` が
  `mocc|BACKOFF_FIXED=-1,...` を期待する。閉じるなら受理集合を狭める設計判断になる。
- {{T:compile-command-supply-proof}} **P3・新規**: cache 名の契約ではなく、emitted compile command で
  値がコンパイラへ届くことを証明する層を持つかを裁定する。先例は
  `orchestrator/campaign/condition_meaning_gate.py` が silo の 1 マクロについて行っているもので、
  その supply domain は patch 由来の define である。genome 軸全体へ広げる費用は未見積である。
