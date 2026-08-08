# [T-530] 段 1 brief — contract hash を campaign identity と WAL COMMIT へ束縛する

## scope

実行契約の `contract_sha256` (env_contract.ExecutionEnvironmentContract の同一性 fingerprint) を

1. campaign identity (campaign.lock の正準 pre-image)
2. WAL の COMMIT record payload

の 2 点へ束縛し、3. 読み手が campaign directory だけで「この COMMIT はどの契約に認可されたか」を
fail-closed に照合できる検査を置く。

**scope 外 (隣接裁定):** [T-658] 見送り = 受領証を全書込み口へ配線すること (防御的堅牢化)。
[T-627] = generation + contract hash の同一入力束縛は別 wave。COMMIT 以外の WAL stage への
束縛拡大もしない。

## 確定済みユーザー裁定

`rulings-inbox/2026-08-04-rulings-session-5rulings.md` §44:
**「[T-530] = contract hash 束縛の実装 wave 起票 (campaign identity + WAL COMMIT、proof chain の完結)」**
起票文 (worklog 306) が「`attestation_mode="none"` の receipt 発行と resume 受理集合の変更を伴う」と
明示したうえでの裁定なので、resume 受理集合の変更はこの裁定の射程内。

## 不変条件

- 規律 2: COMMIT を書く構文位置は `pipeline.evaluate` の認証完了判定の内側のまま。AST gate を緩めない。
- 束縛の欠落・不一致は fail-closed (受理でなく拒否)。既存の受理集合を**拡大しない**。
- 恒真な gate を作らない。検査は WAL record と campaign.lock の不一致を実際に検出できる形にする。
- 既存の凍結成果物 (FROZEN_MANIFEST 23 件) の bytes を変えない。

## 段 1 実測 (実編集 + 即時復元、DW-O19)

- 既存 campaign は 32 本。WAL 3086 record は**すべて `env_tag=linux-baremetal` の単一 env**。
  D13 が許す「1 campaign を複数 env で回す」は実データに存在しない。
- identity pre-image の **top-level** に key を 1 つ足すと `ident.verify_admission_preimage` の
  exact 5-key 検査に当たり **27 件が赤** (resume/lock 経路が総崩れ)。
- **`search_config` 配下**に足した場合の赤は **4 件だけ**で、全件 campaign-id の literal pin
  (`test_campaign.py` 3 件 + `test_p3_autonomous_workload_trial.py` 1 件)。
  baseline = 808 passed / 10 skipped、変異後 = 4 failed / 804 passed / 10 skipped。
- ただし `test_campaign.py::_T343_BACKOFF_CAMPAIGN_IDS` は**現行** campaign-id を pin しており、
  これは `output/campaigns/` の実在 dir と対応する。identity を変えると driver の再計算値が
  既存 dir を指さなくなる (`s1_direct_comparison.layout_for` 等)。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 束縛点は `search_config` 配下の必須 entry (`build_admission` と同型)。**
  攻撃点: D13 の「env も date も同一性に含めない」と正面から衝突する。contract は env 固有
  (env_tag / clocks_per_us / numactl / calibration ref) なので、identity へ入れると campaign が
  env ごとに割れる。代替 = identity を保存したまま lock 隣接の別 record へ束縛する形。
- **(P2) resume 受理集合 = 束縛のない COMMIT を terminal と数えない (fail-closed)。**
  攻撃点: (P1) が入ると同一 campaign 内に無束縛 COMMIT は構造的に現れないため、素朴に書くと
  **恒真 gate** になる。非恒真にするには「COMMIT payload の contract hash と campaign.lock が
  束縛した contract hash の照合」として書く必要がある (record 移植・手編集・旧版 writer を検出する)。
- **(P3) 既存 32 campaign dir が再計算では到達不能になることを受容する。**
  根拠: T-343 (`build_admission` 束縛) の前例があり、32 dir は全て linux-baremetal の探索データで
  certified 本走ではない。攻撃点: 未完了 campaign の再開が「別 campaign」になり再測定が発生する。

## 成果物影響 (DW-G05)

- **実装しない場合:** certified COMMIT の bytes から認可主体が読めず、proof chain は
  build_admission receipt で切れる。認可済みの再起動が T-609 以前の無束縛 COMMIT を terminal と
  みなして skip でき、無認可の測定値が certified 選択の入力に残る。
- **実装した場合に変わる値:** 今後の campaign-id (cfg_hash8) が全て変わり `output/campaigns/<id>/`
  の dir 名が変わる。WAL COMMIT payload に field が 1 つ増える。既存成果物の bytes は変えない。

## 成果物の形

`orchestrator/campaign/` の {ident.py, wal.py, pipeline.py, loop.py} 近辺の変更と
`orchestrator/tests/` の新規・更新テスト。docs は親が段 7 で書く。

## 分割方針

単一 Codex 実装単位。ident / wal / pipeline / loop は同一不変条件を分担しており所有を割ると
中間状態が赤になる。

## 発火 gate (DW-G04)

発火条件を満たす既存 artifact path = `output/campaigns/*/campaign.lock` と
`output/campaigns/*/runs/wal.jsonl` の COMMIT record (32 campaign、3086 record)。
新規 campaign を作る全 driver で発火する。

## 受入・実測環境

Pegasus 計算ノードへ dispatch (`tools/run_tests.py --force-dispatch ...`)。
ログインノードでは `pytest` 直呼びが guard_bash に拒否される。
