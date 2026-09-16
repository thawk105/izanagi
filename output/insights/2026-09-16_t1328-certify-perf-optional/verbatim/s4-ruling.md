# 段 4 裁定 + プラン v2 + 変異事前登録 — [T-1328]

親が段 2 プランと段 3 の 2 レンズを読み、real / refuted・採否・scope を確定した。
以下が段 5 以降の正本である。段 2 プランの本文と食い違う場合は**本書が優先する**。

---

## 1. 前提の再裁定 (brief の (P3))

**裁定: 依頼文の「この計算ノードに perf は無く、perf 不在が較正認証を止めるのは実害である」は、
計算ノードについて現在成り立たない。しかし wave は続行する。**

- 実測 (親): `output/env/pegasus/calibration/job-staging/` の 19 attempt で perf 段の失敗は 0 件。
  直近 2026-09-15 の 3 attempt は `/usr/lib/linux-tools-5.15.0-135/perf` を選び LLC 実カウンタを
  得ている。login node には候補 2 本とも不在だが、本 script は `PBS_JOBID` 必須で login では走らない。
- **相談 A の訂正を採用する。** 上記から「計算ノード全体で現在 perf が使える」とは結論できない。
  母集合は保存済み attempt、観測 regime は各実行時のノード・kernel・PATH・権限である。
  記録は「**観測範囲では perf 段の失敗を確認できない**」までに限定する。
- **続行の根拠は実害ではなく D352 違反の是正である。** 入力を「全 policy 候補不在 + literal perf
  不在 + 他の準備条件は正常」とすれば、現行 `certify_calibration.sh:907-909` は測定前に停止する。
  これは D352 の「preflight は可用性を検出して記録し、**実行を止めるためには使わない**」に反する。
  発火頻度が未確定でも是正根拠は消えない (相談 A・B とも同意)。
- **DW-G04 (条件付き機能の発火 gate) の充足:** 発火条件「policy 候補が全滅 かつ literal perf も
  unavailable」は仮想ではない。(a) D352 自身の根拠実測が「2026-08-12 に計算ノード 8/8 で
  現行 kernel 用 linux-tools 不在」、(b) 親の本日の実測で login node の候補 2 本が実行不可。
  **同じ機体種別で過去に成立した条件**である。

## 2. 所見の裁定

### 相談 A (正しさ境界)

| # | 判定 | 採否 | scope | 措置 |
|---|---|---|---|---|
| A1 受理集合の拡大 | **real** | 採用 | 内 | 不変条件を書き直す (下記 §3) |
| A2 逆向きの狭まり | **real** | 採用 | 内 | 限界として記録。fallback probe を足さない |
| A3 変異を弁別できない assertion | **real** | 採用 | 内 | テスト契約を具体化 (下記 §5) |

- **A1.** 「候補全滅 + PATH 上の literal perf が canonical probe と本測定に成功」という入力は、
  現行 `rc=2 / failure.stage=perf` から、変更後は perf 有り経路で `accepted` になりうる。
  **これは D494 が意図した拡大そのもの**であり (候補全滅だけを degrade の根拠にせず probe に
  決めさせる)、隠してはならない。親の brief 不変条件 1「現在 fail する判定を 1 つも pass に
  変えてはならない」は **D494 と両立しないので撤回する**。旧 smoke の成功を新しい gate として
  再要求する是正は目的に逆行するので採らない。
- **A2.** 旧 smoke (`stat -e … -- sleep 0.1`) は通るが canonical probe
  (`stat -x, -o … -- /bin/true`) だけ rc≠0 を返す候補では、従来 accepted になりえた走が
  rejected になる。D494 の順序を守る以上これは残る。**限界として成果物へ明記し、第二の probe や
  fallback で隠さない。**
- **A3.** no-perf 負例で「最終 rejected」だけを見ると、runner の maxrss 必須検査を削る変異でも
  同じ rejected になる。テストは §5 の形で具体化する。**新しい gate は足さない。**

### 相談 B (整合と実効性)

| # | 判定 | 採否 | scope | 措置 |
|---|---|---|---|---|
| B1 認定較正取得の停止は解消しない | **real** | 採用 | 内 | 達成範囲の明記 (下記 §3) |
| B2 shell 抽出が実呼出しへ届かない | **real** | 採用 | 内 | テスト契約を訂正 (下記 §5) |
| B3「実走不可能」の一般化しすぎ | **real** | 採用 | 内 | brief の記述を訂正 |
| B4 identity の引用が対象違い | **real** | 採用 | 内 | 記録時に訂正 |
| B5 perf なし較正を正式系列で使えるようにするか | **real** | **不採用** | **外** | 裁定パッケージへ |

- **B1.** 本案の終端は、全 sweep 成功時でも `required-metrics-missing` / `selection-invalid` /
  `within-run-cv-invalid` により `quality.status=rejected`、`calibrate_rc=1`、未登録である。
  **「認定較正取得の回復」「予約浪費の解消」を完了扱いにしない。** 本 wave の達成範囲は
  「D352 に従う測定継続と証拠保存」に限る。
- **B2.** プランが抽出しようとした `857-953` は argv JSON の保存までで、実際の起動は
  `956` の `exec_calibrate.py` → `os.execv` である。したがってこの範囲だけでは
  「calibrate 呼出し到達」「probe_error で calibrate が呼ばれない」の実行証拠にならない。
  Python 側も既存 `_invoke` の subprocess fixture は `nm` と `sha256sum` しか受けない
  (`test_calibrator_certify.py:401-406`)。§5 のとおり訂正する。
- **B3.** brief の「fixture harness が唯一の実測経路」は撤回する。候補を存在しない絶対パスにし、
  PATH の literal perf を rc=2 の fixture にすれば実 canonical probe を unavailable にできる
  (空候補配列は `certify_calibration.sh:149` の要素数検査に抵触するので非空の失敗候補が要る)。
  正しい記述は「**本 wave では計算ノードへ投入せず、fixture 検証を採用する**」。
  追加 job 投入は本 wave では行わない。
- **B4.** brief が引いた `orchestrator/qualification/identity.py:44-50` は T126 の consumer であり
  calibration の根拠ではない。calibration 自身の identity 根拠は
  `tools/pegasus/certify_calibration.sh:221-259`。記録時に訂正する。
- **B5 (scope 外・裁定パッケージ候補).** `analyze.py:48-57` が飽和点を選べず、
  `report.py:106-123` と `env_contract.py:606-631` が登録・利用への道を閉じる以上、
  perf 無し較正を正式系列で使える較正へ昇格させるには「perf に依存しない較正が何を保証するか」
  という新しい認証契約が要る。**本 wave の分岐修正に紛れ込ませない。** 段 7 で裁定パッケージとして返す。

### 段 2 プランの推奨案

**採用する。** 「no-perf でも既存 sweep を実行して throughput を保存し、飽和点に依存する noise は
実行せず、認証は rejected のまま終える」。却下した代案は「acquisition 判定後に測定せず終える」で、
理由は D352 の「動かない環境では perf なしで測定を進める」を満たさないこと (プラン §3 の比較、
相談 B も同意)。費用 (sweep 5 点 × 3 rep + build の消費) は残るので成果物へ明記する。

## 3. 不変条件 (brief から差し替え)

1. **規律 2 を緩めない。** 本変更は `report.py` の品質判定、`schema_v2.py` の accepted 制約、
   `cli.py` の登録条件を **1 文字も変えない**。no-perf 成果物が accepted になれないことは、
   新しい gate ではなく既存の `schema_v2.py:529-531` (`accepted` は `saturation is not None` と
   非空 sweep / noise_floor を要求) が保証する。**この保証を実装で代替・迂回しない。**
2. **認証 predicate は不変、実行の到達可能性は変わる。** この 2 つを分けて書く。
   受理集合の増分は「候補全滅 + literal perf が available」ちょうど (A1)、
   減分は「旧 smoke は通るが canonical probe が失敗する候補」ちょうど (A2)。
   **どちらも隠さず記録する。**
3. **判定入口は `use_perf_from_receipt` 1 本** (D494)。`command -v` / `which` / 環境変数 /
   「候補が全滅したか」を第二の判定根拠にしない。shell の `USE_PERF` は canonical 結果の
   伝達値であって判定ではない。
4. **`probe_error` を `unavailable` へ変換しない** (D348 副次決定: probe_error は abort)。
5. **perf 有り経路の argv と call shape を変えない。** `--perf-preflight-json` は
   unavailable のときだけ付ける。
6. **達成範囲を誇張しない。** 認定較正取得は回復しない (B1)。
7. 絶対規律 7: `job_script_sha256` の変化は過去成果物を無効にしない。過去判定を遡って昇格させない。
8. **依頼の scope: 本題の分岐修正だけ。** 仮想リスク向けの gate・検査・台帳・一般化を足さない。
   [T-1329] `floor_scoping.sh` は scope 外。`t141_region_profile.sh` の `fail 2 perf_select` は
   **正しいので変えない** (perf record のサンプルが目的そのもの。相談 B が検算済み)。

## 4. プラン v2 (実装対象)

段 2 プランの「変更プラン」節をそのまま採用し、次の 6 点を上書きする。

1. **wrapper `tools/pegasus/certify_calibration.sh`**
   - `907-909` の候補全滅による即時終了を削除する。
   - `911-928` の `perf-selection.json` 書き出しと symlink は**候補通過時だけ**実行する。
   - 通過時の最終 PATH は従来と同じ。全滅時は perf symlink を作らず、選択済み Python の
     directory と元 PATH を使う。
   - **その最終 PATH の下で** `probe_perf_availability` を 1 度だけ呼び、receipt を
     attempt 内 `perf-preflight.json` へ保存し、`use_perf_from_receipt` の結果**だけ**で分岐する。
   - `probe_error` は unavailable へ変換せず失敗として残す。
   - unavailable のときだけ `calibrate_argv` へ `--perf-preflight-json <receipt>` を足す。
   - rc の意味を変えない。no-perf 認証の rc=1 を成功へ変換しない。
2. **`orchestrator/calibrator/cli.py`** — optional `--perf-preflight-json` を追加。
   bool の `--no-perf` は追加しない。未指定は既存 `None → True` 契約。
   `959` / `980` の `True` を同じ導出値へ置換 (rr20/rr80 の capability 一致のため必須)。
   no-perf のときだけ `use_perf=False` を calibrate へ渡す。測定条件を既存 `host` / `notes` へ記録。
   **`report.py` の認証条件は変更しない。**
3. **`orchestrator/calibrator/sweep.py`** — `calibrate` に既定 `use_perf=True` を追加し、
   内部 `_measure` の closure で False のときだけ `use_perf=False` を渡す。
   `run_sweep` の signature は変更しない。`require_all_reps` / `require_complete_metrics` は維持。
   no-perf では noise を実行せず `saturation=None` / `noise_floor=None` で返し、sweep 測定点は保持する。
4. **`orchestrator/calibrator/runner.py`** — `1256-1260` の counter 必須検査だけを `if use_perf:`
   の内側へ置く。**throughput 検査 `1254-1255`、maxrss 検査 `1261-1262`、rep 失敗処理
   `1184-1192` は維持する。** `require_complete_metrics=False` への一括切替はしない。
5. **閉包の更新** — `orchestrator/tests/test_official_perf_closure.py` の登録集合へ CLI・sweep を
   追加し、runner guard の期待値 (`448-449`) を新条件へ更新する。**新しい一般化検査は足さない。**
6. **変更しない file** — `analyze.py`、`report.py`、`schema_v2.py`、`perf_preflight.py`、
   `submit_certify.sh`、`t126_qualification.sh`、`t141_region_profile.sh`。

## 5. テスト契約 (A3 / B2 を反映)

- **shell 側の主張範囲を訂正する。** production script から抽出した断片で検証してよいのは
  **argv 生成と分岐の到達**までである。`exec_calibrate.py` → `os.execv` の実起動と
  `job-result.json` / `failure.json` の終端は抽出範囲外なので、**「calibrate 呼出しに到達した」と
  書かない**。抽出範囲を実呼出しと終端まで広げるか、主張を「argv 生成」に限定するかを
  実装子が選び、選んだ方を成果物へ明記する。
- **Python 側は実経路を名指しする。** `cli.main → sweep.calibrate → runner.measure_point →
  runner.run_once` を通し、fixture は **subprocess 境界**に置く。
  `_fake_calibrate` だけでは伝播を検証できないので使わない。
  既存 `_invoke` の subprocess fixture が `nm` / `sha256sum` しか受けない点
  (`test_calibrator_certify.py:401-406`) を先に確認し、必要なら受理 command を広げる。
- **assertion の具体化 (A3).**
  - no-perf 正例: **全 rep が走ったこと**、throughput が保存されたこと、counter が null、
    perf prefix が argv に無いこと、noise が呼ばれないこと、`saturation=None`、
    最終 `quality.status=rejected`、未登録。
  - no-perf 負例 (maxrss 欠損等): rc と rejected だけでなく、**該当 rep の fatal 理由**と
    **後続測定が止まった位置**を確認する。
  - `probe_error` 負例: unavailable へ変換されず、calibrate へ進まないこと。
  - perf 有り対照: 最初の候補が失敗し次候補が成功する入力で、canonical probe が
    **選択後の PATH** を使い、従来 argv が 1 文字も変わらないこと。
  - 候補全滅 + literal perf available の対照 (A1 の増分): 候補全滅を直接 no-perf 判定に
    していないこと、no-perf 引数が付かないこと。
- 新規テスト file は作らず、既存 `test_pegasus_calibration_workload.py` と
  `test_calibrator_certify.py` へ追加する (自走 harness と所要台帳の赤を避ける)。

## 6. 変異事前登録 (DW-M01、実装前に確定)

harness = `tools/mutation_harness.py`。変異中は親の編集と worktree へ書きうる子の起動を止める。

| ID | 位置 | 変異内容 | 期待 node (赤にする検査) | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | wrapper 候補 loop 直後 | 候補全滅で `exit 2` を復活 | no-perf 正例 (分岐到達) | 他層に候補全滅を拒否する検査は無い |
| M2 | wrapper probe 呼出し位置 | canonical probe を候補解決の**前**へ移す | perf 有り対照 (候補成功 + base PATH に literal perf 無し) | D494 の順序だけが決める |
| M3 | wrapper 分岐 | `probe_error` を `unavailable` として扱う | `probe_error` 負例 | `perf_preflight` は raise するだけで分岐しない |
| M4 | wrapper selection 出力 | 候補全滅でも symlink / `perf-selection.json` を作る | no-perf 正例 (不在 assert) | 他層は symlink の有無を見ない |
| M5 | wrapper argv 組立 | `--perf-preflight-json` を常に付ける | perf 有り対照 (argv 不変) | 他層は argv 文字列を見ない |
| M6 | `cli.py` receipt 判定 | receipt を無視し常に `use_perf=True` | no-perf 正例 (perf prefix 不在) | CLI が唯一の導出点 |
| M7 | `sweep.py` `_measure` closure | `use_perf=False` を渡さない | no-perf 正例 (perf prefix 不在) | closure が唯一の伝播点 |
| M8 | `sweep.py` no-perf 分岐 | 飽和判定不能でも noise を実行する | no-perf 正例 (noise 未呼出し assert)。**別層 `holdout_observation.py:874-875` が `records=0` を拒否しうるので、赤の出所を実装後に確認し、帰属が割れたら実効 gate へ再照準する** | 要実装後確認 |
| M9 | `runner.py` guard | `if use_perf:` を外し counter を常に必須化 | no-perf 正例 (全 rep 走行) | 他層は rep 内の metric を見ない |
| M10 | `runner.py` guard | `if use_perf:` の中へ maxrss 検査まで入れる (過剰緩和) | no-perf 負例 (maxrss 欠損の fatal 理由 + 停止位置) | A3 の具体化 assertion が唯一の検出者 |
| M-POS | (変異なし) | 承認外の過剰拒否の正例 | 候補成功 + canonical probe 成功で従来どおり perf 有り経路・argv 不変 | DW-M01 の縮小側要求 |

- M6 の別形 (capability の `True` を残して伝播だけ壊す) は、`holdout_observation.py:945-947` が
  測定前に拒否するため **runner の metric gate へ帰属しない**。登録するなら期待 node を
  `holdout_observation` と明記すること (相談 A の注意)。本登録では M6 を CLI 導出点 1 箇所に絞る。
- 各変異は実装後に「前後にも内側にも同じ入力を拒否する層が無い」ことを確認する。
  確認できなければ登録せず実効 gate へ再照準する (DW-M01 / F28)。

## 7. 段 5 の分割

実装子 1 本 (workspace-write)。変更面は wrapper 1 file + calibrator 3 file + テスト 2 file で、
相互依存が強く分割の利得が無い。docs 編集と commit は親が行う。
