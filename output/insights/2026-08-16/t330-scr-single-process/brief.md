# 段 1 brief — [T-330] `/scr` fresh namespace と `single_process` 強制

## 確定済みユーザー裁定

archive worklog (122) `docs/archive/worklog-phase3-0803-122.md` の [T-330] 項 = **択 (a)**:
「`/scr` fresh namespace と `single_process` 強制は、使用権を供給する wrapper の新設と**セットで**
独立タスクとして実装する。発火 caller を持たない強制だけの部分実装は採らない」。

今回のユーザー追加指示: 裁定は 2026-08-03 と古いので、**まず現行 main で前提が生きているかを実測する**。
失効していたら**実装差分ゼロで裁定へ返してよい**。実装する場合は wrapper と強制を同一 wave で入れ、
**caller が実在することをテストで固定**する。実装は Codex author (D95)。規律 2 を緩めない。

## 正本 (逐語でなく本文を開くこと)

- `docs/decisions.md` の **D125 決定 (5)** (「`/scr` の fresh namespace と claim/reservation による
  `single_process` 強制は実装しない」)。同 D の決定 (1)(3)(4)(6)(7) も本 wave の境界を決める。
- `output/insights/2026-08-02_t277-pegasus-measure-path/` の `brief.md` (S4/S5)、`s4-adjudication.md`。

## 段 1 前の前提実測 (親が実施済み。**これ自体が攻撃対象**)

D125 決定 (5) が挙げた見送り理由 3 点:

- **R1「発火条件を満たす caller が存在しない」= 生存**。attestation を入れた sink は
  `orchestrator/campaign/loop.py:92 run_campaign`。その caller は p2_2 / sanity_silo /
  backoff_sweep / s6_sort_sweep / backoff_repro / p3_s4_loop_sort / p3_s4_loop_trigger_gating /
  demo だけで、PBS job script から起動されるものは 1 本もない。`tools/pegasus/*.sh` が計算ノードで
  起動する python は silo_ladder_rung1 / env_attestation / profiler_directive /
  `s8b_floor_campaign.py` (`tools/pegasus/floor_campaign.sh:962`) / t126_driver。
- **R2「`campaign_claim.AcquiredClaim` が public frozen dataclass ゆえ偽造可能」= 生存**
  (`orchestrator/campaign/campaign_claim.py:62`)。
- **R3「`reservation` が binding の `host` を現在 hostname と照合しない」= 生存**
  (`orchestrator/campaign/reservation.py:218-270` は PBS_JOBID・boot_id・時刻だけを照合)。

**失効した前提 (床値経路)**: 「使用権を供給する wrapper が存在しない」は床値経路では失効している。
- `tools/pegasus/submit_floor.sh:403 provision_claim_root` が claims/ を create-only 0700 で事前作成。
- `tools/pegasus/floor_campaign.sh:733-` が `IZANAGI_RESERVATION_*` 8 値を export、`:97` が
  `TMPDIR=/scr/${PBS_JOBID}`。
- 強制も発火済み: `s8b_floor_campaign.py:4236-4273`、`s8b_oracle_driver.py:1026-1037` が
  `acquire_claim`、`orchestrator/qualification/t126_driver.py:886` が `single_process is not True` を拒否。
- ただし `s8b_floor_campaign` は `loop.run_campaign` を使わず自前の測定ループを持つ。

**新事実**:
- dispatch は計測経路ではない。`tools/pegasus/dispatch_compute.py` の `TASKS` は `tests` と
  `provenance` の 2 種のみで、冒頭 docstring が「certification submitter は置き換えない」と明記。
- 8c 事前登録 C12 は `single_process_required` の consumer 到達性を要求するが
  (`orchestrator/campaign/s8c_preregistration_evidence.py:588-605`、
  `s8c_preregistration_evidence_contract.v1.json:471-479`)、C12 の `machine_checkable` は false で
  機械評価器 `_evaluate_c12` は休眠。実走で現況値 = EVIDENCE_UNDEFINED /
  completion-proof-not-machine-checkable を確認 (`test_s8c_preregistration_predicates.py` の
  `zero_satisfied` / `gap_reason_snapshot` 2 node 緑)。**`reservation.py` に
  `single_process_required` という名前の関数は存在しない** (`is_reservation_required`)。
- S4 の「未実装なら build 起源と単独性が台帳から読めない」という害は、その後 D125 決定 (3) の v2
  build identity (site + dependency prefix 束縛) と D136 (build provenance を admission / cache /
  replay / 選択の identity へ束縛) が別経路から塞いだ**可能性がある** (親は未検証)。

## scope 候補と成果物影響 (DW-G05)

本 wave が決めるのは次の 3 択のいずれかである。

- **(X) 実装差分ゼロで裁定へ返す** — 前提が実質失効しており、残る literal 作業は
  「certified 数値を 1 件も生まない探索経路のための wrapper 二重化」に過ぎない、と結論する場合。
  *成果物影響*: certified 選択・レポート・proof chain・凍結 bytes は不変 (D125 決定 7 のとおり
  `loop.run_campaign` 経路の数値は exploratory であり floor 認証されない)。
- **(Y) 最小の発火実装** — `loop.run_campaign` 側に claim/reservation 強制と `/scr` fresh
  namespace を入れ、**同一 wave で** それを起動する PBS wrapper (使用権供給側) を新設し、
  caller 実在をテストで固定する。
  *成果物影響*: 未実装なら Pegasus 計算ノードで探索計測を回す経路が構造的に開かないまま
  (Pegasus 由来の exploratory 値が台帳に入らない)。
- **(Z) 部分実装** — 裁定が明示的に禁じている (発火 caller なしの強制だけ)。**採らない**。

## 不変条件 (緩めない)

- 規律 2: 正しさゲートを緩める変異を採らない。既存の受理集合・拒否を弱めない。
- `env_contract.py` の registry と `contract_sha256`、凍結 bytes を変えない。
- OTHER (linux-baremetal) の既存経路 (cache key・build namespace・campaign identity) を 1 bit も変えない。
- D125 決定 (6): 8c を計算ノードで運転する経路は開かない (D108 決定 (1) と [T-276] の所有)。
- D125 決定 (4): attestation の実装を driver 側へ二重化しない (「二つの真実」を作らない)。
- 床値経路 (`s8b_floor_campaign` / `floor_campaign.sh` / `submit_floor.sh`) の既存強制を回帰させない。
- push しない。land は共通段 9 operation のみ。

## 親の provisional 裁定 (= 攻撃対象)

- **(P1)** T-330 の対象経路は `loop.run_campaign` 側であり、床値経路ではない。床値側は他タスクで
  実装済みなので、本 wave が床値側へ触る必要はない。
- **(P2)** R2 (claim 偽造可能) と R3 (host 未照合) は今も生存しており、(Y) を採るなら同一 wave で
  塞がなければ「謳うだけの gate」になる。
- **(P3)** (Y) の wrapper は `floor_campaign.sh` (41KB) 級の完全な job script ではなく、
  既存 wrapper 群の供給部分 (reservation export + claim root provisioning) を再利用する最小形で
  足りる。
- **(P4)** `/scr` fresh namespace の対象は `cache_root` であり、TMPDIR だけでは S4 を満たさない。
  ただし durable build cache の再利用は D136 の identity 束縛で正当化されている可能性があり、
  その場合 S4 は「実装すべきでない」に転ぶ。

## 並列分割方針

段 2 で file:line 粒度のプラン、段 3 で 2 レンズの敵対相談。段 4 で (X)/(Y) を裁定する。
