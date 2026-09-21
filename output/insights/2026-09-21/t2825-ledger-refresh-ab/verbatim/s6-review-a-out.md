1. **主張:** 無効対の直後に、取り直しではなく次の slot を投入でき、系列を回復不能な `series-invalid` にする。

   **根拠:** [run-series.sh:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/run-series.sh:48) の preflight は既存系列だけを検査し、`:62–66` は指定済みの次の spec を投入する。[run-measure.sh:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/run-measure.sh:64) も今回投入する condition／slot を検証しない。例えば `01 A 1`／`02 B 1` がともに rc=0 でも skipped 集合が違えば対は無効になる。しかし既存系列には `series_invalid` が立たず、既定の `03 B 2` が投入される。次回解析で初めて「slot 1 の A が必要」と判定され、以後の投入を拒否する。

   **重大度:** **must-fix**

   **修正案:** 集計結果から次に許される condition／slot を求め、flock 内で今回の要求と照合する。対の無効化時は同順序の対全体へ戻し、有効対が成立したときだけ slot を進める。

2. **主張:** M3 は単一理由を守るために変更されているが、その変更が判定規則の正本に反映されていない。

   **根拠:** [s4-ruling.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/s4-ruling.md:108) は「凍結 prefix と `@real-repo` 以外を sorted 順の先頭から」削除すると登録している。一方、[make_mutation_spec.py:103](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/make_mutation_spec.py:103) は **87% 以下**を目標に最短連続区間を選び、g6 自身の key も保護する。実 spec は 3,265 件削除、被覆 86.996419%。g6 が自身の台帳値を順序比較に使うことは [test_acceptance_schedule_order.py:839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2825-ledger-refresh-ab/orchestrator/tests/test_acceptance_schedule_order.py:839) で確認できるため、保護には根拠があるが、登録どおりの変異ではない。

   **重大度:** **must-fix**

   **修正案:** g6 key の保護・区間選択・87% の根拠を裁定へ明記し、元の登録との差を残す。元の登録に従った結果として扱わず、変更後の spec に対する単一理由を検証する。

3. **主張:** 台帳予測負荷が consumer の suffix fallback を再現せず、登録済み node を未登録として数える。

   **根拠:** [t2825_ab_analyze.py:180](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/t2825_ab_analyze.py:180) は `ledger.get(nodeid, 1.0)` のみ。一方、[acceptance_shards.py:399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2825-ledger-refresh-ab/tools/acceptance_shards.py:399) は `nodeid@group` も検索する。実物 shard-0 の `test_real_patchharness_checkout_and_resolver_use_explicit_binding` は suffix key に **0.19 秒**があるため、probe は負荷を **0.81 秒過大**に、未登録件数を **1 件過大**に報告する。

   **重大度:** **should**

   **修正案:** `observed_universe` の group を使い、割付器と同じ順序で base key／suffix key を解決する。未登録件数も同じ解決結果から数える。

4. **主張:** 必須出力の「条件ごと」の集計が不足している。

   **根拠:** 事前登録 §8 は走ごと・条件ごとの出力を要求するが、[t2825_ab_analyze.py:456](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/t2825_ab_analyze.py:456) の `condition_summaries` は有効走数と台帳 hash だけ。W₀／W_max の条件別中央値**差**はあるが、各条件の W_j／O_j／L_j／F_j／pre／post の集計値はない。

   **重大度:** **should**

   **修正案:** 採用した有効対の走を母集団として、条件別・shard 別の中央値と対象走番号を JSON／Markdown に出す。無効対の片側を集計へ混ぜない。

## 見つからなかったこと

- `aggregate`、`pair_metrics`、`growth`、`reference_only` を追跡した範囲では、ΔW／ΔO／ΔL の符号、10% 境界、判定の副分類、L の規則、W_max の補助扱い、参考値の判定への混入に誤りは見つからなかった。
- 実物 JSON／XML を部分解析し、26,808 件すべての classname/name 対応が一意に成立した。主要 field は存在し、W₀=382.090 秒、T-2724 は8件、旧 L 候補は4件を取得できた。主要計時 field の欠落を黙って0にする経路は見つからない。コピー hash 検査はこの field 検算では対象外とした。
- `grep -vc ... || true`、`source gate.conf`、最後の `gate_open`、flock、番号重複検査、投入後の HEAD／dirty 検査を確認した。通常の leader 0 件処理、毎回再読込、RUN 作成直前の再判定、投入前の12走上限・有効3対停止は実装されている。
- warm は両条件で同じ経路・空の `PYTHONDONTWRITEBYTECODE` を使う。shard env の除去は collect-only の不適格判定を避けるためで、片側だけ条件を変える処理は見つからない。
- 台帳を独立に照合し、凍結426行の bytes 一致、入力 hash 一致、被覆26,587／26,808、removed140件の一覧一致・main 内0件を確認した。決定性検査は実際に `--refresh --check` の rc を使い、単なる「書かなかったから一致」ではない。
- M1／M2 の凍結検査、M3 の g6 保護・count 整合は source と整合する。追加の赤を生む根拠は見つからなかった。全件 `SURVIVED` は probe 用の生成として一貫しているが、harness 契約との独立照合は指定資料内の author-M 報告を超えて行っていない。pytest・変異実走は未実施。

## 総括

**must-fix は2件、判定は修正後 GO。**
最優先は、無効対の直後に誤った slot を投入できる系列制御の修正。
M3 は単一理由を守る変更に根拠があるが、登録との不一致を解消する必要がある。
台帳の凍結保持と実物 field の対応は確認できた。現状のまま測定系列へ進めることは勧めない。