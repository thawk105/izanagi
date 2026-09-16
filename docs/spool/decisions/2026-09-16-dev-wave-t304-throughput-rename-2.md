---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t304-throughput-rename
seq: 2
---

## {{D:throughput-tps-rename}}. role payload の throughput field を実体名へ改め、旧名の読み替えを版で分ける

**決定 (1): 新名は `throughput_tps` とする。** 旧名 `throughput_ops_sec` の実体は
transactions/sec である。producer の源値は `outcome["fitness_tps"]`、その源は
`pipeline.py` の `bench.median_tps` であり、CCBench 側は `common/result.cc` の `throughput[tps]` で
ある。YCSB 既定 `ycsb_max_ope=10` (`include/ycsb.hh`) の下で名前どおり operations/sec と読むと
**名目 10 倍ずれる**。値は正しく名前だけが誤りであった。`throughput_tps` は
`orchestrator/calibrator/benchparse.py` と `orchestrator/calibrator/model.py` が既に同じ単位で
使っており、新しい別表記を導入しない。**値・`x100` 換算・ゲートの定義と順序と閾値は変えない。**

**決定 (2): role schema を `p3-autonomous-workload-trial/v4` へ上げる。** 理由は値の意味変更では
なく **exact-key 契約の変更**である。`s8c_generation_projection.py` の `_PERF_KEYS` と
`autonomous_trial_completeness.py` の独立 `_PERF_KEYS` は、payload の key 集合を完全一致で要求する。
改名は受理される payload の集合を変えるため、同じ版が互換でない 2 契約を表さないように版を分ける。
`REPORT_SCHEMA_VERSION` は report の形を変えないので v3 のまま据え置く。
`autonomous_trial_completeness.py` の二重定義は意図的な独立再計算であり、producer から import する
形へ置き換えない。

**決定 (3): 旧名で書かれた既存成果物は書き換えず、版で読み替える。** role schema v4 以降は
`throughput_tps` を使う。**v3 以前の role payload に現れる `throughput_ops_sec` は同じ
transactions/sec を表し、読み替えに数値の乗除は伴わない。** 既存成果物の再検証には生成時のコード版と
契約を用いる。旧名を持つのは当該 metric object であり、すべての record がその field を持つという
意味ではない。role schema の系列と、据え置く report schema の系列は別である。
**読み手側に旧名を受理する alias を足さない。** 旧版と新版の throughput field を読み分けて横断
利用する本番 consumer は、`orchestrator/**/*.py` と `tools/**/*.py` の journal reader・completeness・
trial registry・acceptance consumer を探索した範囲で不在であった。

**決定 (4): 事前登録判定器の版 `DECIDER_VERSION` は bump しない。**
`docs/phase3-8c-preregistration.md` の改訂手続きは「判定器・評価器・射影のいずれかで受理集合・
拒否理由・射影された判定入力の意味を変える変更」に bump を要求する。本改名はそのいずれにも
当たらない。`s8c_preregistration_evidence.py` に `_PERF_KEYS` / `_SOURCE_METRIC_KEYS` /
`throughput` は 0 件であり、評価器が射影 module へ要求するのは module 級代入
`_CRITIC_KEYS` / `_DIAGNOSTIC_METRICS` と関数 `apply_critic_feedback` /
`_validate_critic_projection` / `validate_planner_payload` の実在だけである。
`s8c_preregistration.py` の `_projection_module_identity()` が射影 module に対して行うのは
live bytes と登録 commit の blob の同一性照合だけで、`_PERF_KEYS` を読まない。
過去に `DECIDER_VERSION` を動かした 9 commit はすべて条件の machine_checkable 昇格または
証拠契約の変更であり、射影 module 内の key 集合変更による先例は 0 件であった。

**決定 (5): 射影 module の blob 同一性が変わることは開示し、pin は緩めない。**
`s8c_generation_projection.py` は `campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` に含まれ、
`s8c_preregistration.py` の `PROJECTION_MODULE_PATH` でもある。改名は同 file の bytes を変えるため、
**改名前 commit を指す既存の登録は改名後の live code に対して `projection-blob-mismatch` を返す。**
これは contract-loader path を触る全変更に共通の帰結であり、本決定が新設する制約ではない。
**記録済みの測定は無効にならない** (規律 7 — 当時そのコードでその測定をした事実は後から変わらない)。
新しい実走には新しい登録 commit が要る。既存実走を改名後の checkout で再受理させる必要があるか、
その手順は本決定の範囲外とし、別途の裁定に委ねる。

**理由:**

- 論文の実験節と図表、および手動射影の runbook が role へ渡した入力を旧名で記す。名前どおり
  読むと 10 倍の取り違えが起きる面であり、値が正しいぶん誤りが表に出にくい。
- 版を据え置いて 3 実装の key を揃えるだけでも新規出力の経路は動くが、旧 v3 の receipt は新しい
  key 集合と一致しなくなり、同じ v3 が互換でない 2 契約を表す。
- 旧成果物を新しいコードで通すための alias を足すと、名前の誤りを直した意味が薄れ、
  どの版の契約で検証したのかが payload から読めなくなる。

**却下した選択肢:**

- **`throughput_txn_sec`** — `latency_ns` と並びは揃うが、producer の源 field `fitness_tps` と
  CCBench の出力名 `throughput[tps]` から離れ、repo 内に既に在る `throughput_tps` と二表記になる。
- **role 定義側に単位を注記するだけで名前は残す** — 論文の図表と runbook は field 名で引かれる。
  注記は読まれない側に置かれる。
- **読み手側へ旧名 alias を足す** — 横断利用する本番 consumer の実在を確認できなかった。
  仮想の互換要求のために受理形を増やすのは、要求外の一般化である。
- **`DECIDER_VERSION` を念のため bump する** — 受理意味を変えていないのに bump すると、
  次世代の条件凍結 record の発行と、その `ruling_reference` が指す決定の先行着地が必要になり、
  変更単位が 2 wave へ割れる。判定器の版は「受理意味が変わった」という主張であり、
  変わっていない主張を記録すると版の意味が薄まる。
- **`src/coder-spec.md` の §4 も改名する** — 同節は「旧設計 (D39 以前) で superseded」「この
  throughput/abort/latency 値は現行運用で coder に一切渡らない」「本節は経緯記録として残す」と
  自ら明記する歴史記録である。記録された当時の字面を後から書き換えない。
