# 段 1 brief — T-1851 床値の測り直しを耐久台帳の中の別 ordinal 軸として置く

wave: dev-wave-t1851-floor-retry-ordinal-axis
base: 0d3d80e1 (local main, 2026-08-27 00:25 JST 時点)

## scope

床値 campaign の「統計的な測り直し」を、attempt registry (耐久台帳) の中に **`attempt_ordinal` とは
別の、事前登録された試行番号軸**として置く。その軸の ordinal を開く理由は、その ordinal の
性能量が存在しうる時点より前に耐久台帳へ確定して書かれ、後から書く・書き換える経路を残さない。
D880 が「別裁定へ回す」とした campaign 側 `retry_ordinal` と registry 側 `attempt_ordinal` の
不整合を、この形で閉じる。

## 確定済みユーザー裁定 (D1032)

- 測り直しは**同じ耐久台帳の中の別の試行番号軸**として置く。台帳の外へ出す案は不採用
  (再試行が追跡不能になるため)。
- **性能量に到達する前に理由を固定する。**
- 受理する理由の集合を広げる場合も、**外部 scheduler の証拠が付いた場合に限る**。

D880 (前提): 次 ordinal の認可は「同 cell/round の planned session が一意で `valid is False`」(旧経路) と
「attempt registry の検証済み recovery」(新経路) の排他的二択。recovery の authority 許可集合は
**今日は空**で、新経路は production では発火しない。

## 実測した前提 (引数の記述と食い違う点を含む)

1. **`floor_job_checkpoint.py` は編集面ではない。** 全 worktree で変更 0 件、かつ
   `AUTHORITY = "diagnostic-only"` の診断用 checkpoint で再試行の判断を一切持たない
   (`grep retry` が 0 件)。引数の「編集面の起点」は実測と食い違う。段 4 で再確認する。
2. **稼働 wave の重複は 2 本。** `dev-wave-flaky-holds-20260826` (00:17 に land 実行中、
   00:26 までに着地済み — 本 worktree は着地後の main へ ff 済み) と
   `rulings-20260821-calibration-registration` (08-22 起動の孤児 python process が cwd を
   握るだけで稼働 wave ではない)。他の重複 worktree は cmdline 走査・cwd 走査ともに 0。
3. **凍結 bytes の条件は不成立。** registry 成果物は `FROZEN_MANIFEST` にも golden にも
   pin されていない (`git grep` 0 件)。DW-O09/O10 は発火しない。
4. **軸は未実在。** `remeasurement_ordinal` 等の第 2 ordinal 軸は repo 内に 0 件。純増である。
5. **DW-O13 — gate 入力の実在と値域:**
   - 理由 field は実在する。campaign 側 `excluded_reason` (`s8b_floor_campaign.py:6077` の
     session record)、閉じた表は `_check_reason` (`:5810`) が protocol の
     `allowed_excluded_reasons` に対して fail-closed で照合する。
   - 値域は**コードで閉じている**: `competing_process` / `launch_failure` /
     `nonfinite_or_partial_output` / `performance_anomaly` (+ `exclusion_class` としてのみ
     `rep_integrity_failure`)。
   - **実成果物での値域実測は不能。** 8b 床値 campaign の run 成果物は repo に 1 件も
     commit されていない (`git grep -l excluded_reason -- output/` の hit は insight 文書のみ、
     `output/campaigns/*/runs/wal.jsonl` 30 件に `event=session` 行は 0)。
     registry 全体が pre-production (D880 の許可集合が空) であることと整合する。
     よって値域は閉じた表から取り、artifact 由来でないことを裁定へ明記する。
   - **`performance_anomaly` は性能量から導出される理由である** (`assess_session` の
     `required_reason`、`s8b_floor_campaign.py:6017` 付近)。したがって「性能量に到達する前に
     理由を固定する」の「理由」は、**次の ordinal を開く理由**であって、その ordinal 自身の
     除外理由ではない。この読みが実装の要になる。

## 不変条件 (緩めてはいけない)

- **絶対規律 2:** 測り直しの経路は正しさゲートを緩めない。値を見てから測り直しを正当化できる
  経路 (理由の後書き・書き換え・選び直し) を 1 本も残さない。
- `S8B_RETRYABLE_FAILURE_REASONS` の**現在値 `frozenset()` を本 wave で広げない**。広げるのは
  外部 scheduler 証拠が付く場合だけであり、それは D880 の recovery 経路であって本軸ではない。
- D880 の排他的二択と「recovery authority 許可集合は空」を維持する。本 wave はこの塞ぎを外さない。
- 事前登録: 軸の ordinal 集合は genesis (事前登録) の時点で確定し、走行中に増やせない。
- 新軸の受理集合の変更は、既存 campaign の受理集合を変えない (D880 却下理由と同じ拘束)。

## 判断が割れうる前提 (親の provisional 裁定 = 攻撃対象)

- **(P1)** D1032 の「受理する理由の集合を広げる場合も外部 scheduler の証拠が付いた場合に限る」は
  `S8B_RETRYABLE_FAILURE_REASONS` (`attempt_ordinal` 軸の retryable 集合) に掛かる制約であり、
  新設する測り直し軸が統計的理由を受理することはこれに当たらない。
  ← 逆読み (新軸の理由集合にも外部 scheduler 証拠が要る) なら、新軸は production で
  発火せず T-1851 は閉じない。段 3 で最優先に攻撃させる。
- **(P2)** 新軸は S8B slot の同一性 (`S8BAttemptSlot` の `exact_keys`) に field を足す形で置き、
  schema は `s8b-floor-attempt-registry/v1` → `/v2` へ上げる。
  ← 代案: slot 同一性を変えず event 側の field として置く (schema 据え置き)。
  slot 同一性を変えると `attempt_registry_core` の ordinal 連続 prefix 検査
  (`:1081-1090`)、`s8b_holdout_admission` の slot_identity 照合 (`:4304, :4470`)、
  `s8b_scheduler_accounting.py:349` が全て影響を受ける。
- **(P3)** 「性能量に到達する前」の機械的な支配点は、その ordinal の測定関数
  (`measure_fn`) を呼ぶ前に理由付き予約が耐久化されていること、とする。
  ← 代案: session-start の fsync 時点 (campaign 側の既存 β-5 と同じ時点)。

## 成果物の形

- 新軸を持つ registry profile / core の変更と、理由を事前確定させる支配点 1 箇所。
- 理由の後書き・書き換えを拒否する gate。禁止は署名で書き、**通る正例を 1 つ添える** (DW-S04)。
- 変異事前登録 (段 4、DW-M01) — 特に「述語が候補集合に含意されて恒真になる」型を狙う。
- 段 7 の spool fragment (worklog / decisions)。

## 成果物影響 (DW-G05)

実装しない場合: 床値 campaign は統計的に無効な session を測り直しても、その事実が耐久台帳に
別軸として残らない。台帳が持つのは campaign 側 `retry_ordinal` だけで、registry は
`attempt_ordinal` を進められない (`S8B_RETRYABLE_FAILURE_REASONS` が空)。結果、床値の
certified 選択が根拠にする試行台帳から**測り直しの試行が欠落**し、「値を見てから測り直した」
経路が台帳の上で反証できない。受理集合そのものは変わらないが、床値の proof chain が
測り直しを追跡できないまま残る。

## 変更面のアンカー

| path | anchor | 役割 |
|---|---|---|
| `orchestrator/campaign/s8b_attempt_profile.py` | `:32-48` `S8BAttemptSlot` / `:52-60` `exact_keys` | slot 同一性 |
| 同上 | `:395` `S8B_RETRYABLE_FAILURE_REASONS = frozenset()` | 空の retryable 集合 |
| 同上 | `:396-399` `S8B_RECOVERY_FAILURE_REASONS` | 外部 scheduler 証拠側の集合 |
| 同上 | `:22` `S8B_ATTEMPT_REGISTRY_SCHEMA_VERSION` | schema 版 |
| 同上 | `:419-465` `make_s8b_domain_profile` | profile 組み立て |
| `orchestrator/campaign/attempt_registry_core.py` | `:73` `attempt_ordinal` protocol、`:494`、`:1081-1090` ordinal 連続 prefix | 軸の中核 |
| `orchestrator/campaign/s8b_holdout_admission.py` | `:3817-3820`、`:4269-4289`、`:4304-4310`、`:4470-4477`、`:4485-4550` | retry 認可・slot_identity 照合 |
| `orchestrator/campaign/s8b_scheduler_accounting.py` | `:349` | slot field 読み |
| `orchestrator/campaign/s8b_floor_campaign.py` | `:5810` `_check_reason`、`:5820` `_authorized_retry_ordinals`、`:6017` 導出理由、`:6068-6100` session record | campaign 側の統計軸 |
| `orchestrator/campaign/trial_registry.py` | `:1998` | 8c 側の同型 codec (equivalence test あり) |
| tests | `test_attempt_registry_core_s8b_profile.py:302, :802`、`test_s8b_attempt_registry.py`、`test_attempt_registry_core_equivalence.py`、`test_s8b_holdout_admission.py`、`test_s8b_floor_attempt_launcher.py:520-540`、`test_s8b_floor_campaign.py:10598-10680` | consumer 閉包 |

## 分割方針

段 2 = read-only codex 1 本 (file:line 粒度のプラン)。
段 3 = 敵対 2 本 (レンズ A: (P1) の読みと絶対規律 2 の攻撃面 / レンズ B: slot 同一性変更の
consumer 取り残しと恒真化)。
段 5 = 実装 1 本 (編集面が 1 モジュール族に閉じるため分割しない)。
段 6 = レビュー 2 本 + fix + 変異 matrix + 受入全走。

## 受入・実測の環境

login node での pytest。計算ノードへの dispatch は不要 (実装面に性能計測を含まない)。
受入は `tools/dev_wave_wait.py acceptance` 経由の全走。

## 追記 (00:38 実測) — 床値 protocol の 16 field は人間手番であり、本 wave は触れない

D444 (2026-08-16 ユーザー裁定): 床値 protocol のうち **AI が更新してよいのは
`contract_sha256` と `ccbench_pin` の 2 field だけ**である。残る 16 field
(`schema` / `formula` / `env_tag` / `freeze` / `stock_configuration` / `n_sessions` /
`reps` / `master_seed` / `schedule_algorithm` / `extime_s` / `wired_min_rel_floor` /
`retry_slots_per_cell` / `session_cv_max` / `cell_cv_max` /
`scale_adequacy_rel_tolerance` / `allowed_excluded_reasons`) は不変で、
その改訂は引き続き**人間手番**である。

機械的な支配点も実在する。`orchestrator/campaign/s8b_floor_contract.py:523-528` が
`protocol.allowed_excluded_reasons` を承認凍結 4 行と**固定順で完全一致**照合し、
違えば `FloorContractError` を投げる。凍結 4 行は
`s8b_floor_contract.py:96-101` = `s8b_floor_stats.ALLOWED_EXCLUDED_REASONS` (`:53`):

```
("competing_process", "launch_failure", "nonfinite_or_partial_output", "performance_anomaly")
```

### 本 wave への拘束 (不変条件へ追加)

- **`allowed_excluded_reasons` を広げない。** 新軸のために除外理由を 1 つでも足す設計は、
  D444 の人間手番に当たるため**実装せず裁定パッケージへ返す**。
- **`retry_slots_per_cell` の意味・値・扱いを変えない。** 同じく不変 16 field である。
- したがって新軸は、凍結 protocol の外側 — attempt registry (耐久台帳) の中 — に置くほかない。
  これは D1032 の「同じ耐久台帳の中に置く」と整合する。
- 新軸が理由として使う語彙は、上記凍結 4 行を**再利用する**か、
  registry 側だけに閉じた別の語彙集合を持つかの択一になる。前者なら protocol は不変のまま
  再利用でき、後者なら registry 側に新しい閉じた表が要る。段 2 plan と段 3 はこの択一を
  明示的に扱うこと。親の provisional 裁定は **(P4) 凍結 4 行を再利用する** とする
  (protocol を触らずに済み、campaign 側の `_check_reason` と語彙が一致するため)。
