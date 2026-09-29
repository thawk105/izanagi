---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-t2867-silo-contrast-impl
seq: 2
---

## {{D:silo-policy-contrast-impl}}. silo-function-policy 軸の生成器対照は、系列ごとの台帳が A・B と次の単位を持ち、全ての計測 slot を slot ごとの計測 campaign と slot ごとの authorization session で測り、auditor を省けるのは機械生成の候補と初期点だけにする

**決定:** 事前登録の草稿 (D2263) の実行経路を次の形で実装した。記録は `output/insights/2026-09-29/t2867-silo-policy-contrast-impl/README.md`。

1. **系列の identity と計測の identity を分ける。** 系列 cfg = 既定 cfg + `contrast_cohort`・`contrast_arm`・`contrast_series` と同時検査の key (D2251)。対照を指定しない cfg の bytes と campaign ID は不変。計測 cfg = 系列 cfg + `contrast_slot` (`<slot>-<index>-a<attempt>`、slot は stock・seed・eval・score・ref-stock・ref-fixed10)。機械故障の retry は attempt を変えて新しい claim を取る (D2281 の iteration ごとの計測 campaign の拡張)。系列 dir は `policy_history.jsonl` の唯一の置き場。
2. **1 job の slot は slot ごとに新しい authorization session で測る。** session は最初に認可した計測 campaign の identity に束縛される (`loop.py` の `_authorize_with_session`) ので、identity の違う slot で共有すると `binding mismatch` になる (生死確認で実測)。`loop.py`・claim・session の実装は変えない。
3. **系列台帳 (header + 連番の create-only event) が A・B・次の単位・系列の終了を持つ。** 通常 loop の `check_stop`・`loop_state.json` は使わない (通常 loop の予算の数え方は別の裁定)。job は起動時に、台帳から導いた次の単位・proposal の sha256・submit checkout と HEAD を最初の slot 開始より前に照合し、違えば rc=2。未終端の slot があれば自動で投げ直さない。台帳は作成時の checkout の HEAD を束縛し、系列は 1 つの HEAD で通す。
4. **auditor を省けるのは機械生成 (random・evo) の候補と初期点だけ。** 機械 proposal は `{generator, ir}` の別形で、arm と生成器名の閉じた対応で照合し、LLM arm の系列では拒否する。初期点は proposal file を経由させず driver が `enumerate_recon()` の `0000`・`0001` から組む。書込後の digest 再照合は全由来で行う。生成器の再計算による provenance の照合は足さない。
5. **A の計上は機会の開始と確定を分ける。** 429 と役割の異常終了は A を消費しない。schema 不合格・preview の拒否・auditor の veto と digest 不一致は A を 1 消費する却下で、driver の構造化 JSON の拒否 (`proposal-schema`・`auditor-gate`・`auditor-digest`) か round 自身の読込の失敗 (`coder-schema`・`auditor-schema`) だけを却下にし、構造化 JSON の無い driver の異常終了は却下にしない。B は評価 slot の attempt 0 の開始で 1 回だけ確定する。
6. **LLM の原提案は 1 機会ごとに新しい `claude -p` (resume しない)** で、round tool の prepare (critic) → coder → check (preview) → auditor → finalize を進め、429 は `claude -p` の JSON の構造化 field だけで判定して 900 秒後に同じ機会番号で起こし直す。coder role の `{"proposal": ...}` は round tool が展開する。
7. **静的 10 µs は D2240 と同じ適用方法** (stock 木に `patches/silo-backoff-fixed.patch`、`BACK_OFF=1, BACKOFF_FIXED=10`、骨格 patch なし) で、既存の stock 評価関数に載せる (driver の `run_campaign` の呼出し箇所は 2 のまま、閉じた inventory の期待値は変えない)。

**理由:**
- Pegasus の one-shot claim と同じ campaign の terminal skip は identity ごとに効く (D2281)。系列の全 slot (stock・初期点・評価・score の 5 session・参照の 10 session) が fresh な測定であるには、slot ごとの identity が要る。
- 草稿 §3・§5.5・§5.6 の A・B と保留と途中死の規則は、driver の反復予算でなく系列の台帳でしか表せない。
- D2214 項 8 が機械生成の IR 候補の auditor 段を省く。LLM 由来の候補が機械の口を通ると規律 2 の防壁 (auditor の veto) が外れるので、arm で閉じる。
- 生死確認で、差し替えたテストでは見えなかった session の束縛と role の出力形の食い違いが見つかった。実物の経路 (計算ノードの job body と実 LLM) で 1 評価ずつ通すことが、本走の前に要る確認だった。

**却下した選択肢:**
- 1 job の全 slot で 1 つの session を共有する — session の束縛と合わない (実測)。
- 生成器を job 内で再計算して機械 proposal の provenance を照合する — launcher も自前のコードで、仮想リスク向けの検査になる (DW-G05)。
- 通常 loop の予算 (反復 10 回・3,600 秒) を対照でも使う — 系列が複数の job にまたがり A ≤ 30 の却下を含むので噛み合わない (草稿 §3)。
- 静的 10 µs に新しい `run_campaign` の呼出しを足す — 閉じた inventory の期待値を変えることになる。
