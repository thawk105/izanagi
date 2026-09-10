# 段 1 brief — [T-419] U-2 chain / [T-478] 案 A′ 第 1 層

起点 main = `a1265453`。branch = `worktree-dev-wave-t419-u2-contract-generation`。

## 実測した新事実 (段 4 で再裁定にかけるもの)

- **U-2 (較正再取得) の entry condition 1 が未成立。** `env_attestation.probe()`
  (`orchestrator/campaign/env_attestation.py:404-455`) は `/proc/cpuinfo` を 1 回読み、
  `method="proc-cpuinfo"` を出す。裁定 R-1 の方式 α (走行 CPU を移して K 回読み、
  論理 CPU ごとに最小値) は**未実装**。T-478 §6.1 は「R-1 の probe 実装完了」を再取得開始の
  必要条件にしているので、本 wave で再取得は行えない。
- 裁定「[T-478] の実装は U-2 wave の所有」は生きている。よって本 wave の主眼は
  **契約世代機構の実装**であり、再取得・pin closure ではない。
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は現在 1 件 (`calibration-753f535a8d024727.json`)。
  本 wave では**空にしない** (空にできるのは新較正の登録時のみ)。

## scope (この wave で実装する)

T-478 案 A′ の構成要素のうち、**受理集合を 1 bit も動かさずに置ける層**だけ:

1. **A′-1 immutable 世代列 + hash 逆引き** — `GENERATIONS[env_tag] = (g1, ...)` と
   `resolve_by_contract_sha256()`。現状は全 env が 1 世代。
2. **A′-2 transition predicate** — successor は `/calibration_ref/path` と
   `/calibration_ref/sha256` 以外を前世代と厳密一致。可変 pointer 列挙は他に無い。
3. **A′-3 型による権限分離** — `HistoricalContract` / `CurrentContract` を別型にし、
   production 入口 (receipt / build / launch / certified 選択) は後者だけを受ける。
   `allow_historical=True` 相当の真偽フラグを設けない。命名規約に頼らない。
4. **消費者移行** — `lookup()` の production 呼び出し (約 20 箇所 / 10 module:
   `t126_driver` `pipeline` `s8b_ratified_freeze` `s8b_oracle_driver` `s8b_oracle_report`
   `s8b_floor_campaign` `silo_ladder_rung1` `p3_s4_loop_trigger_gating`
   `pegasus_floor_scoping` `env_attestation`) を `require_current()` へ移す。
5. **A′-9 の第 1 層** — 世代列に対する独立 exact key-set・非空 cardinality 検査
   (先例 `test_frozen_artifacts.py:87-114`)。自己申告集合だけを正本にしない。

## scope 外 (実装しない。段 4 で射程として明記する)

- A′-4 単一権威 (activation record からの REGISTRY 導出) と A′-5 activation receipt の
  全入口検査 — **この 2 つは対で入れる** ((P1) 参照)。
- A′-6 campaign identity への `environment_contract_sha256` 必須化 (D13 改訂)。
- A′-7 versioned predicate dispatch。A′-8 `floor_campaign.sh` wrapper 結線。
- 方式 α probe 実装 (R-1)、実際の再取得、pin closure、[T-443] / [T-444] / [T-506]、
  [T-452] U-8 の supersede を書く新 D。

## 不変条件 (破ったら赤)

- **g1 の `contract_sha256` が 1 bit も変わらない。** これは floor protocol の 18 key、
  oracle manifest の `run_contract`、build cache namespace、execution receipt に束縛されている
  (DW-O09 閉包)。`ExecutionEnvironmentContract` の field 追加・削除・型変更・`asdict` 表現の
  変化はすべてこれを壊す。世代機構は**契約 dataclass の外側**に置く。
- 凍結 bytes・`env_contract.py` の calibration pin・`env_attestation.py` の述語・
  Pegasus campaign の開閉は不変。受理集合は変えない。
- `V2_ENV_NEUTRAL_MODULES` の env-literal AST 検査 (`env_contract.py` の免除 region =
  `_build_registry`) を恒真化しない。世代列を別関数へ出すなら免除 region も追随させ、
  免除の穴を広げない。
- 既存 test の期待 (`checked_entries == 2`, `required_entries == 1`,
  `len(KNOWN_SELF_INCONSISTENT_CALIBRATIONS) == 1`) は本 wave では維持する。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** A′-4 / A′-5 を本 wave に入れない。理由: REGISTRY の trust root を source literal から
  activation record ファイルへ移すと、A′-5 の全入口検査と A′-9 の独立検査が揃うまでの間、
  γ-13 (静的定義以外から env を注入する経路が無い) が**弱くなる**。半分だけ入れるのは
  純減になりうる。→ 段 3 はここを攻撃してよい。
- **(P2)** `HistoricalContract` / `CurrentContract` は `ExecutionEnvironmentContract` を
  継承せず、**同じ contract 値を包む別型の wrapper** とする。継承にすると
  `isinstance` が通ってしまい権限分離が名ばかりになる。`contract_sha256` は wrapper 越しでも
  g1 と同値。
- **(P3)** 世代列の宣言は `env_contract.py` 内に静的に置く (新ファイルにしない)。
  registry と世代列が別ファイルだと単一権威が割れる。

## 成果物影響 (DW-G05)

実装しない場合: 新較正 (g2) を登録した瞬間、g1 を参照する既存の certified 選択・floor
protocol・oracle manifest・T-126 適格性 artifact の contract hash が `lookup()` から
解決できなくなり、**過去試行の proof chain が「解決不能」になる** (T-478 §1)。
その状態で再取得へ進むと、旧 evidence の binding を新 SHA へ貼り替える誘惑が生じる
(§4.2 が明示的に禁じた虚偽履歴)。本 wave はその貼り替えを型で不可能にする。
実装した場合の受理集合の変化: **なし** (g1 のみの世代列は現行 `lookup()` と同値)。

## 分割方針 (段 5 の並列)

- 子 A: `env_contract.py` の世代列・transition predicate・型分離 (新規面、所有独占)。
- 子 B: consumer 20 箇所の `require_current()` 移行 (既存面、A の API 確定後)。
  → A と B は同一ファイルを触らないが API 依存があるため**直列**。並列は段 6 の review 2 本のみ。

## 環境

受入全走・pytest は Pegasus 計算ノードへ dispatch (runbook §7)。login node では走らせない。
