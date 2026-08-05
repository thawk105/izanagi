# 段 4 裁定 — [T-419] U-2 較正の再取得

基準 HEAD = `18149bcf` (段 1 の `cfda4abe` から local main を ff-only 取り込み)。
merge 差分は docs・`tools/run_tests.py`・`check_docs.py`・t139 probe・test 2 本のみで、
本 wave の実装面 (`orchestrator/calibrator/cli.py`、`orchestrator/campaign/execution_guard.py`、
`env_attestation.py`、`env_contract.py`、`tools/pegasus/certify_*`) は 1 行も変わっていない。
よって段 2 プランの file:line は有効 (SRC-01 に対する親の実測)。
dev-wave 契約側の変更 (DW-O15 削除、DW-O11 改訂) は取り込み済みで、本 wave の段構成に影響しない。

## 親 brief の誤りを 2 件認める

- **B-1 (F-00 / lens A・段 2 が独立に指摘): 「取得経路に自己整合検査が無い」は誤り。**
  `_effective_clock_self_comparison_passes` (`cli.py:380`) が canonical 述語を呼び、
  `cli.py:611-613` で benchmark 後に適用されている。既存テストが全 outlier 位置の拒否と
  非 publish を固定している (`test_calibrator_certify.py:533,564`)。
  現 HEAD は自己不整合な較正を accepted で publish **しない**。
  よって本 wave の純増は「新しい防壁の追加」ではなく「既存 late gate の早期化・構造化診断・
  policy 再束縛経路の閉鎖」である。変異台帳と記録もこの表現へ統一する。
- **B-2 (SCOPE-01 / lens B): 「D176 の fuse により accepted publish receipt も取れない」は誤り。**
  publish 経路 (`cli.py:633-659`) は `registered/calibration-<sha>.json` を作るだけで
  `env_contract` を一切呼ばない (親が grep で確認: `cli.py` に `env_contract` の出現なし)。
  D176 が阻むのは **current への活性化・pin 切替**であって取得と publish ではない。
  したがって着手条件 (ii) accepted publish receipt と (iii) 独立 self-comparison は
  **本 wave で到達可能**であり、親が縮小したのは誤りだった。scope を戻す。

## 所見の裁定

| ID | 判定 | 採否 | scope | 理由 |
|---|---|---|---|---|
| F-00 | real | 採用 | 内 | 上記 B-1。記録表現を是正する |
| F-01 (policy 再束縛で accepted 集合が変わる) | real | 採用 | 内 | late gate を**残し** early gate を**追加**する。加えて publish 直前に「attempt 開始時 policy と publish 時 policy の同一性」を独立検査して反例を閉じる |
| F-02 (rejection 成果物と reason 集合が変わる) | real | 採用 | 内 | early 拒否時の `rejection.json` に `not_evaluated` を明示し、artifact 種別が変わる事実を仕様化して記録する |
| F-03 (benchmark 後 clock が未検査、外側 post probe は publish より後) | real | 不採用 | 外 | 既存の穴であり本 wave が作ったものではない。publish transaction の位置を動かす設計択一 → 裁定パッケージ |
| F-04 (evaluator は band math と canonical policy を一軸にできない) | real | 採用 | 内 | 評価を `input_valid` / `policy_matches` / `band_pass` の 3 分解にし、canonical は 3 者の連言。診断の帯外 0 件を受理判断に使わない |
| F-05 (変異帰属の不成立) | real | 採用 | 内 | 下記の事前登録で矛盾 oracle と「1 項だけ不正」fixture を採る |
| F-06 (loader/schema/registry/直接 reader に self-pass が無い) | real | 不採用 | 外 | [T-506] 本体。新較正の登録と同時に課す裁定済み方針のまま → 裁定パッケージ |
| F-07 (D176 は source fuse であり runtime 再束縛を防がない) | real | 採用(記述のみ) | 外 | 親の「迂回不能」を「source bootstrap では不能」へ是正。runtime authority は [T-529] → 裁定パッケージ |
| F-08 / PIN-01 (pin 閉包の不足と 3 分類) | real | 採用(記述のみ) | 外 | `current 更新` / `歴史保持` / `新世代で再発行` の 3 分類を裁定パッケージへ載せる。**本 wave では 1 件も更新しない** |
| F-09 (login 1 回測定は計算ノードの根拠にならない) | real | 採用 | 内 | 親も同意。login 値は sampler identity の smoke に限定して記録する |
| SCOPE-01 | real | 採用 | 内 | 上記 B-2 |
| SCOPE-02 (certify script の編集禁止は親が作った自己矛盾) | real | 一部採用 | 内/外 | 禁止が親由来である事実を認める。ただし T-443/T-444 の完全結線は本 wave で実装せず、「同梱済み」とも書かない → 裁定パッケージ |
| CERT-01 (過去 build の transport は確定不能) | real | 採用 | 内 | 「compute node の transport が働いた」と断定しない。実測で言えるのは「job-local warm `_deps` は否定できる」までと記録する |
| LIVE-01 (別 job の 1/1 は後続 certify を許可しない) | real | 採用 | 内 | **別 PBS の生死 driver を取り下げる**。生死判定は certify と同一 allocation 内の early gate が担う |
| OPS-01 (新出力先は guard inventory・snapshot・dirty gate と衝突) | real | 採用 | 内 | LIVE-01 の帰結として新出力先を作らないので消滅する |
| API-01 (`run_probe.py` の改造は旧 evidence 束縛に触れる) | real | 採用 | 内 | 同上。`run_probe.py` を編集しない |
| SRC-01 (source snapshot の drift) | real | 採用 | 内 | 冒頭の実測で対応済み |
| CLAIM-01 (U-2 完了を主張してはならない) | real | 採用 | 内 | 到達表を記録へそのまま載せ、未達を task ID と依存付きで残す |

## プラン v2 (実装する範囲)

**単位 1 (唯一の実装単位。分割しない)**

1. `orchestrator/campaign/execution_guard.py`
   - 帯評価を 1 箇所へ集約する private evaluator を抽出し、`input_valid` / `policy_matches` /
     `band_pass` と違反位置の詳細を返す。
   - 既存 public `effective_clock_comparison_passes()` は
     `input_valid and policy_matches and band_pass` の連言として**現行と 1 bit も変わらない**ことを、
     境界 unit vector (tolerance 0 / 2.0 の上下等号と `nextafter` / 100、NaN、空列、
     numeric string、bool、非 float) で固定する。
   - 診断 projection `effective_clock_comparison_diagnostics()` を追加する。**診断値は
     受理判断に使わない。**
2. `orchestrator/calibrator/cli.py`
   - `_acquisition_reasons` に early self-comparison を **追加**する (benchmark 前)。
     既存の `cli.py:611-613` の late gate は**残す**。
   - early 拒否時の `rejection.json` に構造化診断と `not_evaluated` を書く。
   - publish 直前に「attempt 開始時に profile へ書いた `tolerance_pct` が、publish 時点の
     policy 定数と一致する」ことを独立検査し、不一致なら fail-closed で拒否する。
3. 独立 self-comparison (着手条件 iii)
   - publish 済み artifact の **bytes を読み直し**、CLI 内部状態を使わずに canonical 述語を
     適用して合否を返す検査を追加する。CLI の内部 gate の再掲にしない。

**禁止の署名 (DW-S04)**

- 禁止: `publish(artifact)` where `not canonical_effective_clock_passes(artifact.effective_clock)`.
- 禁止: `publish(artifact)` where `artifact.effective_clock.tolerance_pct != EFFECTIVE_CLOCK_TOLERANCE_PCT`
  評価時点 (= attempt 開始時と publish 時のいずれか一方でも不一致)。
- 禁止: 受理判断が `diagnostics["out_of_band_count"] == 0` に依存すること。
- **通る正例:** `samples_mhz = [2101.0] * 48`, `tolerance_pct = 2.0`, `method = α`,
  policy = 2.0 のまま attempt 終了 → early gate 通過、late gate 通過、publish される。

**実装しないもの (現状維持)**

`env_contract.py`、世代登録、pin、`EXPECTED_GENERATION_HASHES`、`contract_sha256`、
`FROZEN_MANIFEST`、`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の空化、loader/registry/consumer の
self-pass、`_assemble_v2` / `window_probe` への gate、campaign 群の CMake argv、
`tools/pegasus/*.sh` と `run_probe.py`、新しい PBS と新しい出力先。

## producer の書き出し面 (DW-O10)

certify producer が repo 配下へ書くファイル種を棚卸しした (実測 = 既存 job `0:867876.nqsv`)。

- `output/env/pegasus/calibration/registered/calibration-<digest16>.json` — publish 成功時だけ。
  content-addressed、create-only、`.publish-*.tmp` 経由の `renameat2(NOREPLACE)`。
- `output/env/pegasus/calibration/attempts/<job-id>/` — `calibration.json`、`calibration.md`、
  `window-probes.json`、`publish.json`、`final-receipt.json`。
  **本 wave の early gate が発火した場合はここに `rejection.json` だけが残り、
  `calibration.json` / `calibration.md` / `window-probes.json` は生成されない** (F-02)。
- `output/env/pegasus/calibration/job-staging/<PBS_JOBID>/` — 約 45 種。
  attestation static/pre/post の json・stdout・stderr、acquisition candidate/receipt、
  binary sha/symbols、build/configure の stdout・stderr、gflags/glog の build ログ、
  toolchain version 群、`calibrate-argv.json`、`calibrate.stdout/stderr`、
  qstat 系、job-result、PBS の `.o`/`.e`。

本 wave の実装は**このどれの bytes 生成規則も変えない**。変わるのは
「early 拒否時に attempts 配下へ何が出るか」だけで、それを F-02 の仕様として固定する。

## 変異事前登録 (DW-M01)

単一理由性は「同じ入力を拒否する層が前後に無いこと」をコードで確認したうえで登録する。
schema preflight (`cli.py:556`, `schema_v2.py:227`) が先に拒否する入力は登録しない (F-05)。

| ID | 変異 | 期待赤 node (方針) | 単一理由性の根拠 |
|---|---|---|---|
| M1 | early gate の呼出しを削除 | early 拒否 integration test (`calibrate_fn` 未呼出し assert 付き) | late gate は残るので publish 集合は変わらない。**受理集合を変えない診断/時点 pin** として `DW-M08` の diagnostic sensitivity pin 枠へ記録する |
| M2 | late gate の呼出しを削除 | 既存 `test_calibrator_certify.py:533,564` | early を通す入力 (policy 再束縛) でのみ差が出るため M3 と分ける |
| M3 | publish 直前の policy 同一性検査を削除 | 新規 policy 再束縛 negative test | 他層に policy 同一性を見る検査が無いことを確認して登録 |
| M4 | canonical を 3 分解の連言でなく `band_pass` だけにする | tolerance=0 / tolerance=100 / 非 policy 等号の unit vector | schema を経由しない unit 呼出しなので preflight に mask されない |
| M5 | `all` を `any` へ退化 | 全 outlier 位置の parameterized unit test | 位置ごとに独立 |
| M6 | 先頭 / 末尾 index を走査対象から外す | index 0 と index n-1 の unit test | 同上 |
| M7 | 受理判断を `diagnostics["out_of_band_count"] == 0` へ差し替える | 矛盾 oracle test (`band_pass=True` かつ帯外 0 だが `policy_matches=False` の入力) | 通常の outlier では両者が一致するため、**矛盾入力でしか kill できない**ことを事前に明記 |
| M8 | 独立 self-comparison が artifact bytes でなく CLI 内部の profile を読む | bytes 改竄 fixture (publish 後に 1 sample を帯外へ書き換え) | CLI 内部状態には改竄が伝わらないので単一理由 |
| M9 (正例) | early gate を「帯内でも拒否」へ倒す | 正常 profile の publish test | 承認外の過剰拒否の検出 |

harness は `tools/mutation_harness.py` を使う (DW-M05)。所要見積りは 9 変異 × 対象 file 選択式で、
外側の実行時間上限に掛からない経路で起動する。

## 運用順序 (親)

1. 実装 → 段 6 レビュー 2 本 → fix → 変異 matrix → 受入全走 → commit。
2. **commit 後・tree clean の状態で** `tools/pegasus/submit_certify.sh` を投入する
   (CERT-01: dirty tree では submit が確定的に失敗する)。
3. certify の結果で分岐する。
   - early gate で帯外拒否 → **α は計算ノードで帯内にならない**という決定的事実を得る。
     benchmark 前に落ちるので約 1/3 の費用。U-1c の再裁定へ返す。
   - accepted publish → 着手条件 (ii)(iii) 到達。artifact は activation 権限が無い限り
     inert (registry へ入らない) なので誤 certification は流れない。

**certify を投入するという裁定の根拠 (両レンズの NO-GO に対する親の判断)。**
両レンズは「T-443/T-444 の source projection 前に certify すべきでない」とした。親は投入する。
(a) 生成物は activation 権限が無い限り inert であり、certified 受理集合へ到達しない。
(b) source proof の欠落は g1 と同一で、本 wave が新たに悪化させない。記録に明示する。
(c) 「計算ノードで α が帯内か」は環境束縛の事実であり、機会があるときにしか取れない。
(d) early gate により帯外なら benchmark 前に落ちる。
この判断自体を裁定パッケージへ載せ、ユーザーが覆せるようにする。

## 追記 (段 5 実測後、DW-O12: 実際に実行した手順)

実装子は権限どおりコードとテストだけを編集し、既存テストの期待値を 1 つも変えずに
「赤くなる node を予告」して止まった。親が計算ノードで実測した結果は
**4 failed / 307 passed** で、赤は予告と完全一致した。

- `test_calibrator_certify.py::test_cli_effective_clock_self_failure_is_quality_rejected_before_publish[0|24|47]`
- `test_calibrator_certify.py::test_effective_clock_policy_metamorphic_wiring_producer_loader_issuer_consumer_self`

**親の裁定: これらの期待値更新を明示的に許可する。** 理由は、赤の原因が実装の誤りではなく、
段 4 で採用した F-02 (early 拒否では benchmark を開始しないので `calibration.json` /
`calibration.md` / `window-probes.json` が出ず `rejection.json` だけが残り、probe 呼出しも
3 回から 2 回になる) そのものだからである。旧期待値は **late 拒否の成果物構成**を逐語で
固定しており、早期化と論理的に両立しない。

許可の条件 (これを満たさない更新は差し戻す):

- 更新後の期待値は**厳密に強く**すること。旧テストが固定していた性質
  (rc≠0 / publish しない / `registered` が存在しない / reason 文字列 / 帯外 sample の値 /
  `tolerance_pct == 2.0`) を 1 つも落とさず、`rejection.json` 側で同じ性質を固定する。
- 加えて新しい性質を固定する: benchmark 未開始 (probe 呼出しが 2 回)、
  `not_evaluated` に late gate と publish が含まれること、診断に帯外位置が含まれること。
- 反転・緩和・skip・削除は禁止のまま。上記 4 node 以外の期待値には触れない。

## 追記 2 (段 6 レビュー後) — 裁定記録の是正 (REC-01)

段 6 の 2 レンズが本裁定文の記述の行き過ぎを 6 件指摘した。すべて認めて是正する。

1. **「public 述語は 1 bit も変わらない」は不成立。** malformed / 非 policy 入力で
   旧 `False` が `OverflowError` へ変わる (レビュー A の C-02、B の REG-01)。
   これは本 wave の refactor が入れた**回帰**であり、fix 巡で直す (F-1)。
   同値性の主張は「schema-valid・有限・plain-dict 入力について」へ限定する。
2. **「early 拒否では `rejection.json` だけが残る」は job 終了時点の話。**
   所定の collection 後は `final-receipt.json` も加わる。
3. **「どの bytes 生成規則も変えない」は誤り。** `rejection.json` に
   `diagnostics` と `not_evaluated` を足すので、同ファイルの生成規則は変わる。
4. **「1 job の拒否 = α は計算ノードで帯内にならない決定的事実」は一般化のしすぎ。**
   同裁定が採用した LIVE-01 と矛盾する。証明できるのは
   **その job・その host・その boot・その cpuset・その時刻の profile が帯外だった**ことだけ。
   記録もこの語で書く。
5. **「accepted publish → (ii)(iii) 到達」は誤り。** (iii) 独立 self-comparison は
   test helper にしかなく、実 job は実行しない (レビュー B の PC-02)。
   fix 巡で「同一 process 内で内部状態を使わない publish 済み bytes 再読検査」を production へ入れ、
   到達範囲を**そこまで**と書く。別 process の完全独立検証は scope 外。
6. **「registry へ入らない」は曖昧。** 正確には
   「filesystem の `registered/` へは入るが、`env_contract` の current 契約へは活性化されない」。
7. **「費用は約 1/3」は未立証。** `certify_calibration.sh` の逐次 timeout 合計は
   gflags 60×3 + glog 120×3 + CCBench 900×2 = 2340 秒で、header の `build_cap=1080` と一致しない
   (レビュー B の OPS-03)。費用の表現は「benchmark 部分を省く」に限定し、比率を書かない。
   reservation 式の誤りは編集禁止面なので裁定パッケージへ回す。

## 追記 3 — 変異事前登録の再照準 (C-04、DW-M01/DW-M08)

レビュー A が M1・M2・M5・M8 の単一理由性不成立を指摘した。認めて再登録する。

- **M1 (early gate 削除)**: late gate が残るため受理集合は変わらない。
  `DW-M08` の **diagnostic sensitivity pin** 枠へ移す。期待赤は
  「probe 呼出しが 2 回」「`calibrate_fn` 未呼出し」「`rejection.json` の存在」。
- **M2 (late gate 削除)**: publish policy gate が同じ入力を拒否するため、
  期待赤は accepted 集合ではなく **reason が self-failure から policy-changed へ変わる** assertion。
  これも sensitivity pin 枠。
- **M5 (`all` → `any`)**: 現実装に `all` が無く loop と `band_pass = not violations` なので、
  anchor を `if lower <= sample_mhz <= upper: continue` の条件反転へ再照準する。
- **M8 (独立 self-comparison)**: fix 巡 (F-8) で production 側へ移すので、
  anchor を「publish 済み target の再読を CLI 内部 profile の参照へ差し替える」1 置換に再登録する。
- M3・M4・M6・M7・M9 は静的 mask が見つからなかったので登録どおり。
- 追加登録 **M10**: public 述語の shape/policy 短絡を外す (F-1 の回帰を再発させる) →
  期待赤は F-1 で追加する OverflowError negative vector。

## 追記 4 (焦点再レビュー後) — producer inventory の是正 (NR-04) と変異の再々登録 (NR-05)

**producer 書き出し面の追加 (追記 1 の DW-O10 棚卸しを更新)。**
fix で publish 後の独立再読検査を production へ入れたため、**成功 attempt** の staging に
`published-self-comparison.json` が 1 種増える。追記 1 の列挙はこれを含んでいなかったので是正する。
collector は attempt/staging の全 file を opaque に manifest 化して final receipt へ hash 束縛するため、
この sidecar も自動的に proof chain へ入る。

**変異事前登録の再々照準 (焦点再レビューの表を採用)。**

- M1・M2・M6・M7・M9 — 成立。登録どおり (M1/M2 は `DW-M08` の diagnostic sensitivity pin 枠)。
- **M3** — 不成立。publish policy gate を消しても F-8 の published-bytes 検査が
  policy mismatch を拒否する。受理集合変異から「reason と target 非生成時点の sensitivity pin」へ再分類。
- **M4** — 不成立。3 分解の conjunction anchor は F-1 の短絡復元で消えた。
  anchor を「policy mismatch の early return を band math へ流す」1 置換へ再照準。
- **M5** — 不成立。`lower <= sample <= upper` の反転は `all→any` ではなく帯内外の意味反転になる。
  anchor を band math body の明示的 `any(...)` 置換へ再照準。
- **M8** — 不成立。helper は target しか受けないので in-memory profile 置換は複数変更になる。
  anchor を「published-bytes 検査の引数を `target` から `staging_artifact` へ変える」1 置換へ再照準。
- **M10** — 不成立。shape・policy・band eagerness は別 anchor。policy 面は M4 へ寄せ、
  M10 は「診断側の全件収集フラグを既定へ倒す」1 置換に限定する。

**この再々登録を確定してから変異 matrix を回す。** 登録どおりに単一置換が取れない変異は
走らせず、走らせた結果だけを台帳に残す。

## 裁定パッケージへ返す項目 (実装しない)

1. **[T-529] 活性化権限** — registration・pin 切替・例外集合空化の唯一の前提。F-07 の
   runtime 再束縛も同 wave で閉じる。
2. **[T-506] loader/schema/registry/直接 reader の self-pass** — F-06 の全層。
3. **pin 閉包の 3 分類と versioned resolver** — F-08 / PIN-01。旧 evidence
   (`silo_ladder_rung1.json`、causality manifest、`floor_protocol.json` 経由の凍結 contract hash)
   は保持し、新 current だけを再発行する設計。
4. **[T-443]/[T-444] の certify script 結線** — SCOPE-02。certify script の限定編集を
   許可するかの択一。
5. **F-03 publish transaction の位置** — benchmark 後 clock の検査を課すか。
6. **wave 名と U-2 完了の扱い** — CLAIM-01 の到達表。
7. **別 process による完全独立 self-comparison と receipt 束縛** — PC-02 の完全形。
   job wrapper から verifier を起動し、判定を final receipt へ束縛する設計。
8. **reservation 式の誤り** — OPS-03。`certify_calibration.sh` の逐次 timeout 合計 2340 秒に対し
   header と receipt は `build_cap=1080` を記録する。CLI 起動前に
   `remaining >= calibrator_required_s` を検査する改修も含む。
9. **runbook の attempt path 不一致** — OPS-01。attempts は `0_...`、job-staging は `0:...` だが
   `tools/pegasus/README.md` は raw `<PBS_JOBID>` を両方に使うと書いている。
   rejection-only の collector test も無い。
10. **job 実行中の source drift** — OPS-02。job 冒頭で commit と clean を照合した後も、
    後段 helper は live worktree の `run_probe.py` / `runner.py` / `calibrate.py` bytes を読む。
    CCBench だけが immutable snapshot を取る。
