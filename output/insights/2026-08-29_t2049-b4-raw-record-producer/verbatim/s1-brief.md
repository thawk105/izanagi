# [T-2049] 段 1 brief — B-4 raw 試行記録の権威 producer

## scope (純増点)

B-4 (規律 3 の還流 on/off ablation) 専用の**権威ある raw 試行記録 producer** を新規実装する。
現在 repo 全体に、`orchestrator/campaign/p3_b4_analysis_adapter.py` が必須にした field を書く
producer が存在しない。`p3_b4_analysis_path.py` の docstring が自ら
「authoritative artifact producer, sanctioned command, durable writer, report generator,
certified-selection connection は本 module の scope 外」と明記しており、
`p3_b4_analysis_ledgers.py` の docstring も「authoritative producer を作らない・同定しない」と書く。
本 wave はこの 5 語のうち **producer と durable writer だけ**を埋める。

sanctioned command (T-2051)、report generator、certified-selection connection、
schedule/seed issuer (T-2050)、primary outcome cell の充填 (T-2052) は scope 外。
汎用の試行記録 framework へ広げない。

## 確定裁定 (ユーザー指示・既裁定)

- scope は B-4 専用に閉じる。汎用 framework 化しない。
- 既存 WAL・campaign lock・receipt 機構の再利用を優先する。**新しい署名・nonce・一回性台帳を作らない。**
- D824: estimand は「粗い結果と緑 leading-indicators を両アーム共通にしたうえでの詳細 anomaly の
  増分効果」。screening rejection は treatment から明示除外 (決定 4)。primary は paired 1-step (決定 3)。
  この範囲を広げない。
- D1240: B-4 分類と receipt は同一 lock snapshot へ束縛し、不在は明示 (固定) absence digest で表す。
  producer も同じ束縛に載せる。
- 実装面は D95 の Codex `role=author` が書く。親は直接編集しない。

## 不変条件

1. **分析 source closure の exact pin を動かさない。** `p3_b4_analysis_path.py` の
   `_SOURCE_CLOSURE_PATHS` (5 file) は `p3_b4_analysis_prereg_consumer.py` が AST で literal 一致を
   要求する。新 module を closure へ足さない。5 file の当該構造も変えない。
2. **規律 2:** 証拠が欠けたら値を捏造せず fail-closed。正しさゲートを緩める分岐を作らない。
3. **規律 3:** 拒否は pass/fail でなく「どの証拠のどの field が欠けたか」を構造化して返す。
4. **規律 1:** trace/perf 分離に触れない。producer は既存 artifact を読むだけで測定を起こさない。
5. **数値の厳密性:** JSON の十進 token を保ったまま出力する。binary float を経由させない
   (adapter は decoded mapping を「binary float を使わなかったことを証明できない」として拒否する)。
6. **同一 lock snapshot:** 分類と hash 検証に同じ raw bytes snapshot を使い、不在は
   `CAMPAIGN_LOCK_ABSENT_SHA256` へ束縛する (D1240、実体は `wal.py` `_append_record`)。
7. **全件を落とさない:** duplicate / dry-pass / 実行前停止 / crash / 終端記録不在は `missing` へ写し、
   **行そのものを落とさない** (事前登録 §5.1.1、adapter の `execution_disposition`)。

## 成果物の形

- 新 module (仮) `orchestrator/campaign/p3_b4_raw_record_producer.py`。
  - 入力: 1 campaign root の実 artifact + 封印済み registry / manifest。
  - 出力 1: **arm ごとの canonical source artifact** (排他 create + fsync の durable write)。
    事前登録 §7.1 の全件報告 row field を持つ。その sha256 が `source_artifact_sha256` になる。
  - 出力 2: block ごとの raw 記録。全 block 揃った時点で `p3-b4-raw-analysis/v1` 文書へ組み上げる。
  - `evaluate_b4_artifacts` が要求する **block/arm の exact 順**で source artifact bytes 列を返す。
- 対応する test file。

## 実アンカー表 (実測済み)

| 出力 field | 実データ上の出所 (実測) |
|---|---|
| `schema_version` | `p3_b4_analysis_adapter.RAW_ANALYSIS_SCHEMA_VERSION` = `p3-b4-raw-analysis/v1` |
| `block_id` | 封印済み `scheduled_attempt_registry` / `analysis_manifest` の canonical id |
| `reference_tps` / `reference_snapshot_hash` / `reference_receipt_hash` | 同 registry 行 (`B4ScheduledAttemptInput`)。adapter が contract binding と exact 一致を要求 |
| `assignment_observation` | 2 arm の実行 slot 順。manifest の `assignment_schedule` と一致した時だけ `assignment_followed` |
| `terminal_stage` | WAL 終端 record の `stage`。**実 WAL は小文字 `commit` / `abort`** (`model.py:28-29`) だが raw schema は大文字 `COMMIT` / `ABORT`。producer が写像する |
| `terminal_reason` | abort payload の `reason`。`diff-quarantine` は `p3_s4_loop.py:391` が実際に書く |
| `throughput` | commit payload の `fitness_tps` (実測例 `491796.5`)。`certified` のときだけ持つ |
| `whiteboard_result` | `loop_state.json` の whiteboard 末尾 `result` (実測例 `success`) |
| `precursor_hash` | registry 行の `initial_proposal_sha256`。block 内 2 arm で一致必須 |
| `treatment_fired` | 閉じた critic receipt (`p3-b4-closed-critic-receipt/v3`) の arm/campaign/iteration/digest 束縛 |
| `contaminated` / `protocol_ok` | `B4ArmPairComparison` (`admitted_view_sha256_equal` / `loop_state_sha256_equal` / `iteration_equal`) と launch sidecar |
| `source_artifact_sha256` | producer 自身が書いた canonical source artifact の sha256 |
| lock 束縛 | `campaign.lock` raw bytes snapshot の sha256、不在は `CAMPAIGN_LOCK_ABSENT_SHA256` |

補助入力の実在も実測した: `b4_launch_context.json` (`p3-b4-launch-context/v1`) は campaign_id / arm /
driver_kind / admission_record_sha256 / launch_context_sha256 を持つ (`p3_b4_launcher.py:386-398`)。

## 値域の実測 (DW-O13)

- 実 campaign `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387` を読み、
  lock の `search_config.reflux` が `"on"`、WAL 15 record が `build_start`/`build_done`/`verify_done`/
  `bench_done`/`commit` の 3 巡、commit payload に `fitness_tps` が実在、
  whiteboard の `result` が `success` であることを確認した。要求する値は到達可能である。
- 同 campaign は whiteboard 4 行に対し WAL commit 3 件で、**loop state が WAL より先行**していた。
  事前登録 §7.2 が非保証に挙げる「進んだ WAL と一世代古い loop state の組合せ」の実物であり、
  producer は 2 者の突き合わせを fail-closed にしなければならない。
- 正式 B-4 campaign はまだ 1 本も存在しない (producer 不在が実走の blocker であるため)。
  したがって述語は**既存 production writer が書く実形式**に対して検証し、手書き mock で代用しない。

## (P1) 割れうる前提 — 親の provisional 裁定・攻撃対象

- **(P1-a)** `treatment_fired` は「そのアームの割当条件が実際に届いたか」であり、
  **off でも真になりうる** (事前登録 383-387 行: 「on では赤詳細が digest へ載ったこと、
  off では載らなかったことが確認できたこと」)。contract は
  `on.treatment_fired and off.treatment_fired` が 201 block 全部で真でなければ判定不能にする
  (`p3_b4_analysis_contract.py:728`)。**off を一律 False にする実装は全 block を判定不能にする。**
- **(P1-b)** `precursor_hash` は contract binding に pin されておらず、adapter は
  「block 内 2 arm で一致」しか見ない。定数を書けば通る。よって producer 側が実証拠へ束縛する
  唯一の権威であり、ここが最大の reward hack 面である。
- **(P1-c)** 201 block × 2 arm = 402 campaign root なので、producer は**逐次追記**で 1 arm ずつ
  durable に書き、全件揃った時点で組み上げる形が要る。一括生成だけの API は実走に耐えない。
- **(P1-d)** source artifact は producer 自身が書く。「producer が書いた物の hash を producer が
  宣言する」構造は自己参照であり、外部証拠 (WAL bytes・lock snapshot・receipt) への束縛を
  source artifact 内に持たせないと恒真になる。

## 分割方針

Codex `role=author` を実装面へ 1 本 (producer 本体 + test)。scope が 1 module に閉じ、
所有が割れないため並列分割はしない。親は brief・裁定・統合 commit・変異 matrix・受入・記録を担う。
設計択一 (逐次追記の粒度、source artifact の schema、treatment_fired の証拠源) が割れうるため、
段 2 プラン起草と段 3 敵対相談 2 本、段 6 敵対レビュー 2 本を省かない (軽量版にしない)。

## DW-G05 — 成果物影響

放置すると B-4 の実走で作れる生データが 1 件も無く、`evaluate_b4_artifacts` は全入力を
`field_missing_or_ill_typed` で拒否し続ける。論文 §8 の B-4 verdict セルは永久に空欄のままで、
「規律 3 の還流に効果があるか」という主張は成立も不成立も書けない。

## DW-G01 — 生死確認

新規コードなしで実施済み。`orchestrator/tests/test_p3_b4_analysis_path.py` と
`test_p3_b4_analysis_adapter.py` を実走し **49 passed**。消費側は適合 raw record を受理する。
欠けているのは producer だけである、という前提を実測で確認した。

## 実測環境

- 本 wave の検査は Pegasus login node 上の `tools/run_tests.py` (自動判定) で行う。
- 正式 B-4 実走・qsub・性能測定は行わない。
