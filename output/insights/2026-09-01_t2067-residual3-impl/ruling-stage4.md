# 段 4 裁定 — [T-2067] 残件 3 点

裁定時刻 JST 2026-09-01。wave base = `2bf9cf387`。裁定時の local main = `1d2706f9e`。
裁定 inbox 再走査済み。最新の `2026-09-01-dw-s04-superseding-ruling-boundary.md` は
DW-S04 の裁定境界に関する別主題で、本 wave の scope を動かさない。

## 結論

**実装するのは残件 1 のうち s8c 床値 verifier / publish の 1 群だけ。** 残り 4 項目は実装せず、
理由を添えて記録・裁定へ返す。段 5・6 は実施する (実装面の差分が非ゼロ)。

## real / 採用

### A1 (real・採用・設計差し替え) — plan の wholesale `launch_validate` は D1325 に抵触する

レンズ A 所見 1。親が独立に裏取りした:
`load_ratified_freeze` は otherwise-valid な g2 を**受理**する
(`test_s8b_ratified_verify.py:1264-1272`)。一方 `launch_validate` は
`s8b_ratified_freeze.py:3107-3110` で g2 を artifact I/O より前に拒否する
(`test_s8b_ratified_verify.py:1400-1410` が `generation-scope` を固定)。
したがって plan の設計を採ると **3 群に新しい g2 拒否挙動が生じる**。これは D1325 の
「g2 は実在してから設計する」と、段 1 brief の不変条件 (iv) の両方に抵触する。

**差し替える設計:** `s8b_ratified_freeze` に**選択規則だけを g1 限定で**課す狭い公開 API を新設する。

- `generation_number != 1` のとき**何もしない** (現在の挙動をそのまま保存する。g2 について
  受理も拒否も新たに定義しない)。
- `generation_number == 1` のとき、`_launch_validate:3303-3321` と**同じ** 3 つの拒否理由
  (`floor-selection-eligibility-underivable` / `floor-selection-rule-mismatch` /
  `floor-selection-unverifiable`) だけを課す。
- `validate_selected_certificate` は launch 側と同じ既定 (False) にする。candidate 側だけが
  True を渡す現状を変えない。
- **`launch_validate` は呼ばない。** activation HEAD、current contract/build admission、
  closure、binding graph、live scan は 1 つも持ち込まない。

### A2 (real・採用) — 「current admission を通った」は D1313 の 4 番目の主張になる

レンズ A 所見 2。D1313 の逐語は「追加で主張してよいのは (a)(b)(c) の 3 点だけ」。
A1 の差し替えにより full current admission は入らないので抵触は解消する。
その上で**記録側の不変条件**を置く: worklog・拒否理由・docstring のいずれにも
「current launch validation を通った」「current admission に束縛された」と書かない。
本 wave が記録してよいのは「選択規則の強制点が s8c の床値 verifier / publish にも増えた」
という実装事実だけであり、**主張の水準は D1241 / D1313 のまま動かさない。**

### A3 (real・採用) — `assert validated.ratified is ratified` は恒真

`LaunchValidatedFreeze` は入力をそのまま格納するため、この assert が単独で落ちる入力は
構成できず `python -O` で消える。**採用しない。** 保証・gate・変異の数に入れない。

### A4 / B5 (real・採用・親の実測 5 を訂正) — C06 経路は「全体が到達不能」ではない

`load_ratified_freeze(ROOT)` は `p3_autonomous_workload_trial.py:4640`。C05 の常時例外
`_load_s8c_schedule_authority` は `:1837` で `_prepare_s8c_budget_inputs` の内側から呼ばれ、
その `_prepare_s8c_budget_inputs` は `:4641` (= `:4640` の**後**) で呼ばれる (親が実行行を確認)。
gate 自体は C05 より先に評価できる。親の段 1 実測 5 の一般化は過大だった。

### B2 (real・採用・限定) — s8c judge に production caller は無い

`s8c_result_judge` の production importer / caller は 0 件 (親・レンズ A・レンズ B の 3 者が独立確認)。
C07 は source の AST 静的検査であり、現に**通っている** (親実測: C07 =
`EVIDENCE_UNDEFINED` / `completion-proof-not-machine-checkable` = `_evaluate_c07:3313-3317` の
全検査通過の終端)。さらに `SATISFIABLE_CONDITION_IDS = frozenset({"C10"})` により C07 は
設計上 SATISFIED に到達しない。**したがって「production final claim を配線した」「C07 が
改善した」とは一切書かない。** この事実は worklog に明記する。

### B1 (real・採用・親の (P1-2) の理由を訂正) — 残件 2 の不能理由

親は「凍結時に再計算できない」と書いたが、正確には `clean_scan_digest()` は現在の repository に対して
再実行できる。不能なのは **launch 時点の独立した expected が保存されていない**ことである。
scan は run directory 作成前 (`s8b_floor_campaign.py:7278-7306`) に行われ、その後 certificate /
result が tracked 集合へ加わる。preimage は certificate・journal・manifest・Git tree のいずれにも
残らない。certificate 自身の値を expected にする形は **D80 が明示的に禁じている恒真**である。
現在 scan を expected にすれば正当な drift を過剰拒否する。

### B3 (real・採用) — C06 群は実装しない

- **`DW-G05`:** 実装前後とも budget ledger を生成できる入力集合は空 (C05 が `:1837` で必ず拒否)。
  変わるのは「選択 error と C05 error のどちらが先に出るか」だけで、成果物の値・受理集合・参照は
  1 つも変わらない。影響行を書けない。
- **`DW-M01` / `DW-M03`:** gate を戻しても baseline は選択 error、mutant は C05 error で、
  どちらも `reserve_all_cells` 前に fail-closed する。受理集合も fail-closed 挙動も期待方向へ
  変わらないため、診断文字列だけの赤であり kill にならない。単一理由の変異を登録できない。

両方が独立に refuse するので実装しない。C05 が着地した時点で再評価する項目として記録する。

### B4 / B5' (real・採用) — 残件 3 を止める理由は C05 単独ではない

production の aggregate 点は `trial_registry.assert_trial_registry_acceptance:5675-6267`
(receipt は `:6233-6255`、`:6251` が常に `certifying: False`、CLI は `:6348-6354`)。
止まる理由は次の**連言**であり、C05 単独ではない。

1. exact 6 cell・`n>=2`・`6×n` observation の反復 schedule が無い
   (producer / acceptance は replicate 0 に固定: `p3_autonomous_workload_trial.py:1330-1338`、
   `trial_registry.py:3496-3509`)。
2. throughput と correctness/trace に独立束縛された attestation authority が無い。
3. judge の `_ContrastParams` へ渡す H1/H2 params authority が無い。
4. `publish_result_table` は repository 外の絶対 path だけを許す
   (`s8c_result_judge.py:2255-2284`) 一方、acceptance receipt schema は 3 表の path/hash を
   持たない (`s8c_acceptance_receipt.py:45-67`)。**失敗原子的に束ねられない。**

したがって `trial_registry.py:6104-6256` は「正しい配線位置」ではなく **coordination boundary の
候補**である。`DW-G04` の発火 artifact path も書けない。**実装しない。設計メモに留める。**

### A4' (real・採用・親の実測 1 を訂正) — t1999 は commit 済み、ただし未 land

t1999 の作業ツリーは clean になり、`s8b_oracle_driver.py` / `test_s8b_oracle_driver.py` /
`test_s8b_oracle_manifest.py` は branch へ commit 済み (親が `main...branch` で確認)。
「未 commit 37 file」は現時点で成立しない。**しかし t1999 は未 land** (裁定時 main = `1d2706f9e`)
なので所有は継続しており、同 file を本 wave が編集すれば land 時に衝突する。

### 採用 — oracle manifest 群は本 wave で実装しない (保留)

blocker を親が直接確認した: `test_s8b_oracle_manifest.py:272-292` の
`_synthetic_ratified_freeze` は **`generation_number=1`** を返す。したがって
A1 の g1 限定 gate は当該 fixture でも発火し、`:1346-1371` と `:1374-1406` の 2 正例
(いずれも candidate manifest の生成成功を期待する) が必ず赤になる。
直すには同 file への fixture 追随が要るが、t1999 が所有している。
**production 側へ test 専用の抜け道を入れることはしない** (規律 2・偽緑の禁止)。

段 5 投入直前に t1999 の land 状態を再取得する。land 済みなら main を取り込んで unit B として
実装する。未 land なら本 wave では実装せず、次の一手へ繰り上げる。

## refuted / 訂正

- **plan の残件 1 設計 (wholesale `launch_validate`) — refuted。** A1 のとおり差し替える。
- **plan の `assert validated.ratified is ratified` — refuted (恒真)。** A3。
- **plan の C06 helper・対応 2 test・変異 3 / 4 — refuted。** B3。
- **plan の「`trial_registry.py:6104-6256` が正しい配線位置」— 訂正。** B5。候補境界に留める。
- **親の段 1 実測 5 (「C06 経路は無条件に塞がれている」) — 訂正。** A4。
- **親の段 1 実測 1 (「t1999 が未 commit で保有」) — 訂正。** A4'。commit 済み・未 land。
- **親の (P1-2) の理由 — 訂正。** B1。
- **レンズ B の「残件 1 は 3 群とも裁定へ返すべき」— 一部不採用。** s8c 群は
  `publish_result_table` が s8c 3 表の**唯一の producer** であり、gate を戻すと
  「より早い導出適格 run があるのに選ばれた床値の receipt でも 3 表が作られる」という
  受理集合の変化が実在する (`DW-M03` の kill 条件を満たす)。production caller が 0 件である事実は
  worklog に明記した上で実装する。C06 群と異なり、受理集合が実際に変わる。

## 不採用 / scope 外

- 新しい署名・nonce・一回性台帳・汎用の選択規則 framework (D1241 が却下済み)。
- g2 の受理・拒否・選択・投影の新規定義 (D1325)。
- 上限の解除・緩和、および D1313 の (a)(b)(c) を超える主張。
- s8c 事前登録 CLI が全述語を `evaluator-exception` で返す既存問題の修理 (別主題・本 wave 非接触)。
- 仮想リスク向けの gate・検査・台帳・一般化 (ユーザー明示で scope 外)。

## 変異事前登録 (`DW-M01`)

実装は s8c 群のみ。登録する変異は 3 件。

| # | 変異する位置 | 変異内容 | 殺すはずの test |
|---|---|---|---|
| M1 | `s8c_result_judge.py` の `verify_floor_bytes` 内 | 新 helper 呼出しを bare `load_ratified_freeze()` へ戻す | `test_s8c_result_judge.py::test_floor_verification_rejects_selection_mismatch` |
| M2 | 同 `_validate_verified_floor` の current binding | 同上 | `test_s8c_result_judge.py::test_publish_rejects_when_selection_mismatch` |
| M3 | `s8b_ratified_freeze` の新 helper 内 | `generation_number == 1` の枝を無条件実行へ変える | `test_s8b_ratified_verify.py::test_g1_only_selection_helper_is_noop_for_g2` |

M3 は **g2 不変性の負例**である。無条件化すると g2 入力で新たな拒否が生じ、A1 の抵触が再現する。

**承認外の過剰拒否の正例 (`DW-M01` 必須):**

- P1: selection が valid な g1 は、実装後も `verify_floor_bytes` / `publish_result_table` を通り、
  3 表が作られる。
- P2: `generation_number == 2` の入力は、実装前後で**挙動が完全に同じ**である
  (新 helper は何もしない)。
- P3: historical `reverify_published_freeze` の受理集合は実装前後で不変
  (`test_s8b_ratified_verify.py:890-895` の既存固定が緑のまま)。

各変異は、同じ入力を拒否する層が前後に無いことをコードで確認してから登録する
(M1/M2 は selection gate が唯一、M3 は g2 gate が新 helper 内の唯一の分岐)。

## 成果物

- 実装面 (段 5、Codex `role=author`、D95): `orchestrator/campaign/s8b_ratified_freeze.py`、
  `orchestrator/campaign/s8c_result_judge.py`、`orchestrator/tests/test_s8c_result_judge.py`、
  `orchestrator/tests/test_s8b_ratified_verify.py`。**単一 unit** (helper と consumer の
  producer/consumer 契約が単位を跨ぐため分割しない)。
- docs: `docs/spool/worklog/` fragment 1 本。decisions fragment 1 本
  (残件 2 / 3 / C06 群を実装しないという設計判断は新しい裁定にあたる)。
- insight: `output/insights/2026-09-01_t2067-residual3-impl/`。

## `DW-G05` 成果物影響 (実装する 1 群)

放置すると、同一 namespace により早い導出適格 official run があるのに選ばれた床値の receipt でも、
s8c の 3 表 (`descriptive_only` / `official_status` / `selection_evaluation`) が作られる。
実装後は 1 表も作られない。**ただし現 HEAD に `s8c_result_judge` の production caller は 0 件で、
この差は直接 API を呼んだときにだけ現れる。** この限定を worklog に明記する。

## 受入

`python3 tools/dev_wave_wait.py acceptance --wave t2067-residual3-impl
--lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease -- python3 tools/run_tests.py`
(実行場所は Pegasus runbook §7.0.0 の既定自動判定に従う)。段 7 の記録前に実走する。
