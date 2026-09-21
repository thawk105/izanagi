## 1. 図 (1) 生成器

以下の行番号は変更前の現物。repo 相対 path の基準は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures`。略記は次のとおり。

- `A` = `tools/plotting/plot_a1_sized_paired.py`
- `AT` = `orchestrator/tests/test_plot_a1_sized_paired.py`
- `B` = `tools/plotting/plot_b10_waiting_grid_forest.py`
- `BT` = `orchestrator/tests/test_plot_b10_waiting_grid_forest.py`
- `M` = 新規 `tools/plotting/plot_mocc_witlight_four_arm.py`
- `MT` = 新規 `orchestrator/tests/test_plot_mocc_witlight_four_arm.py`
- `R2` = `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md`
- `RM` = `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md`
- `J` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures`
- `E` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W`

新規 file の現物行番号はまだ存在しないため、以下では `M:新規 / 関数名` の形で位置を指定する。実装後の行番号を推測して記載しない。

| 現行位置 | 変更後の形 |
|---|---|
| `A:2` | 説明を attempt-0001 / attempt-0002 の単独記述図へ更新。 |
| `A:36–59` | 既存定数をそのまま残し、attempt-0002 の定数と `ATTEMPTS` 表を追加。既存 `LEAF_DIR`、`RESULT_JSON`、`RECEIPT_JSON`、`COMPLETE_JSON`、`PINNED_SHA256`、`CAPTION_SOURCE` の名前・値・挿入順を維持。 |
| `A:122–143` | `load_leaf(repo_root, *, attempt="attempt-0001", expected_hashes=None)`、`_load_leaf(root, expected_hashes, attempt)`。先に `attempt in ATTEMPTS` を要求し、未知値を既定へ落とさない。選択した表の `pins` に対し `set(hashes) == set(pins)` を検査。読込順は常に表の順序とし、注入 dict の順序には依存しない。 |
| `A:140–147` | caption_source と completion の leaf path を選択表から取る。`.complete.json.files` の README / receipt / result の追加照合は維持。 |
| `A:148–234` | schema、lane、policy、arm、対、生値、統計、分類の検査は維持。policy path は両 attempt 共通。 |
| `A:235–236` | 235 行の述語一致を両 attempt に適用。236 行だけ `if attempt == "attempt-0001":` 配下に置き、既存の `is False` と例外文を維持。 |
| `A:237–255` | cell の形は両 attempt とも現行のまま。返却用 `data` を現行 dict で組み立て、attempt-0002 の場合だけ `data["attempt"] = attempt` を追加。 |
| `A:264–286` | `_caption` 冒頭で attempt-0002 を `_caption_attempt2(data, prefix)` へ dispatch。attempt-0001 の既存本文・固定定数・書式化・文順は変更しない。 |
| `A:289–331` | 数値系列は同じ式。attempt-0002 の系列だけ表示用 breach / sd / sigma を追加し、その系列から panel 題を描く。attempt-0001 の系列の key と描画文を維持。 |
| `A:342–371` | renderer-backed 検査を弱めない。attempt-0002 の題のために許容重なりを広げない。 |
| `A:374–388` | signature と schema は維持。現在の `data.items()` 展開によって fig14 にだけ `attempt` が入る。公開時は引き続き `fig._a1_artist_series` を渡す。 |
| `A:391–411` | provenance の `attempt` 欠落を旧 attempt-0001 と扱い、存在時は exact 選択表で検査して `load_leaf(..., attempt=attempt)`。それ以降の全 data key、出力 hash、artist、caption の照合を維持。 |
| `A:414–445` | publish の保存前検査・一時 file・置換失敗時復元を維持。 |
| `A:448–460` | `--repo-root` の次に `--attempt` を追加。`choices=("attempt-0001", "attempt-0002")`、既定 attempt-0001。loader に渡す。 |

**exact pin 表**

- `A:36–46` の既存表は次の順序・値を保持する。

| 順序 | key | SHA-256 |
|---|---|---|
| 1 | `RESULT_JSON` | `372f199e674cce28d46e2aeeed90b0f5b6c06e894bca63bcb779b580a8bb75a0` |
| 2 | `RECEIPT_JSON` | `a2039dc1457cf34828714a98955faf3df68d335c0442d144122686f4e177e930` |
| 3 | `COMPLETE_JSON` | `0b1f177944f6cab5c5eed5aa94a34beda11a06fcd8e94c1018d35c4e5e212a1e` |
| 4 | `POLICY_PATH` | `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a` |

- `A:55` 後へ `ATTEMPT2_LEAF_DIR = "output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002"`、`ATTEMPT2_CAPTION_SOURCE = R2`、以下の `ATTEMPT2_PINNED_SHA256` を追加する。出所は `R2:427–438`、`J/verbatim/attempt2-doc-s5.1.md:10–14`。

| 順序 | key | SHA-256 |
|---|---|---|
| 1 | `ATTEMPT2_LEAF_DIR + "/result.json"` | `b7e0518e197500f2daf875e841acabf63f5eddb82bc14e072dd28e3431fe5f74` |
| 2 | `ATTEMPT2_LEAF_DIR + "/receipt.json"` | `98c35cca4fe0e9f12559b8f9dc3acb4c6c5c4c597e5f5cc01a6449533918ecbf` |
| 3 | `ATTEMPT2_LEAF_DIR + "/.complete.json"` | `7ad34232eaf920babd783140c47018b5c9d2f7665635872d4c2ee3be6f464fb3` |
| 4 | `POLICY_PATH` | `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a` |

- `ATTEMPTS` は二つの明示 entry に `leaf_dir / pinned_sha256 / caption_source` を持つだけとする。CLI から path・hash を注入する入口、任意 attempt の探索、fallback は追加しない。
- README の hash は従来どおり、pin 済み completion の `files` から検査する。attempt-0002 の README hash は `034cd1fd2f5004b1faac27d7e5e629a88c29f1e89dfd5fd1af9e6eadc50b53a1`（公開 leaf `.complete.json:4`）。

**返り値と旧図の互換性**

- `A:251–255` の attempt-0001 返却 key は、順に `repo_root, tracked_inputs, study_id, measurement_source_commit, ccbench_pin, measurement_conditions, workloads, limitations, authority_note`。追加 key はゼロ、値も従来と同一にする。
- attempt-0002 だけ上記に `attempt` を足す。`variance_plan_breach` と `planned_sigma` は既に cell にあるため、共通 cell の構造変更は不要（`A:241`）。
- `validate_repo_closure` の旧 provenance 解釈は「`attempt` 欠落の場合だけ attempt-0001」。未知文字列を旧図と扱わない。fig14 の attempt field 除去・改変は、選択した leaf と `tracked_inputs` の不一致で拒否する。

**caption と panel**

- `A:264–286` の attempt-0001 caption は一文字も変えない。共通化のための文章再構成や既存 `FIXED_SCOPE` の変更もしない。
- 新規 `_caption_attempt2` は既存 caption の構成を踏襲し、attempt 名、3 workload の値・job・host・breach 記述だけをこの attempt から作る。固定文には既存 `FIXED_LANE`、`FIXED_SCOPE`、`COMPARISON_WARNING` と、次を追加する。

  `Attempt-0001 is neither pooled nor compared with this attempt; no between-attempt difference, ratio, or reproducibility judgment is made.`

  `No cause is attributed to variance_plan_breach.`

- workload 別の文は `write-heavy: variance_plan_breach=true, sample sd=80,148.44 tps, planned sigma=66,403.45 tps` の形で3件。balanced は false、read-heavy は true。sd / sigma の比を作らない。出所は `R2:198–200`。
- `A:320` の panel 題は attempt-0002 の場合だけ3行にする。1行目は現行題、2行目 `variance_plan_breach=true/false`、3行目 `sd …; planned sigma … tps`。図高・上余白の変更は attempt-0002 分岐内だけ。開始候補は `(12, 4.4)`、`top=.72`。**layout 通過は未確認**で、実寸 Figure の検査を通して確定する。
- `_artist_series` に入れた表示値を `make_figure` が実際に使い、test は Text と数値 artist を照合する。provenance にだけ開示する形にしない（`J/s1-brief.md:44–47`）。
- 図番号は既存 `A:258–261` の prefix 正規表現から導く。

**展開済み argv**

- attempt-0001 は明示選択時も旧形へ正規化し、`AT:431` をそのまま通す。
- attempt-0002 は次の形。caption の図番号を attempt から決めない。

```text
python3 tools/plotting/plot_a1_sized_paired.py --repo-root <absolute-root> --attempt attempt-0002 docs/paper-story/figures/fig14_a1_balanced5_sized_attempt2
```

## 2. 図 (1) test

既存 `AT:164–524` の test 本文・期待値は弱めない。新規 test は `AT:527` の plain runner より前に置く。

| 追加 test 名 | 検査内容・fixture |
|---|---|
| `test_attempt1_default_and_explicit_data_are_identical` | 既定と明示 attempt-0001 の dict 全体一致、上記9 key と順序、旧 pin の順序・値、caption 一致。`AT:80–130` の fixture。 |
| `test_attempt2_fixture_has_production_shape` | 3 workload × 30 対 × 2 arm。write-heavy / read-heavy が true、balanced が false。 |
| `test_attempt_hash_key_sets_are_exact` | attempt1 の hash map を attempt2 に渡す、逆方向、key 欠落・追加を拒否。注入 dict の逆順でも入力種別の順序は不変。 |
| `test_attempt2_pinned_input_hashes_match_results_document` | `AT:415–420` と同型。`R2:427–447` の各 path の行が一意で、4 hash と一致。 |
| `test_attempt2_real_leaf_loads_and_matches_results_document` | `AT:455–468` と同型。`R2:198–200` の mean / h / interval / B / baseline / sd / sigma / classification / breach を照合。breach は `[True, False, True]`。 |
| `test_attempt2_variance_plan_breach_true_is_accepted` | 他条件を満たす true を受理。既存 `test_variance_plan_breach_true_is_rejected`（`AT:332–347`）は変更せず attempt1 の拒否を保持。 |
| `test_attempt2_variance_plan_predicate_mismatch_is_rejected` | 再計算 sd と sigma は正しいまま boolean だけ反転し、述語不一致で拒否。`1` / `"true"` も拒否。 |
| `test_attempt2_caption_contains_fixed_literals_and_breach_values` | 固定文を test 側の独立した literal として検査。各 workload の true/false・sd・sigma、Figure 14 を検査。 |
| `test_attempt2_caption_avoids_forbidden_claims` | `AT:262–270` の禁止句に加え、`reproducibility confirmed`、`pooled estimate`、`breach caused by` 等の肯定主張を拒否。禁止語 `ratio` 等の単語丸ごとの排除は、否定の固定文まで壊すので行わない。 |
| `test_attempt2_rendered_breach_and_statistics_match_provenance` | `AT:180–209` を踏襲。実際の90点、平均、帯、床、0線と provenance を照合。さらに `fig.findobj(Text)` で3 workload の breach / sd / sigma が可視 text に存在することを要求。 |
| `test_attempt2_real_figure_passes_layout_check` | 実寸 fixture、本物の Figure、axes `(1,3)`。検査関数を差し替えない。 |
| `test_attempt2_cli_and_provenance_closure` | 3成果物、attempt field、caption_source、展開 argv。attempt / caption / artist / workload / output の改変を個別に拒否。 |
| `test_cli_rejects_unknown_attempt_and_hash_options` | choices 外の attempt、hash・leaf を渡す未定義 CLI 引数を拒否し、成果物ゼロ。 |
| `test_landed_fig14_repo_closure_and_caption_when_present` | `AT:471–486` と同型。fig14 の exact repo 相対出力 path、3 file の存在、閉包、README 自節の hash 3行と caption 収録を検査。欠落を skip しない。 |
| `test_landed_fig14_rejects_missing_or_partial_bundle` | `AT:489–524` と同型。全欠落と非空の不完全な6組を拒否。 |

- fixture helper は `AT:44–138` を基に、選択表を引く keyword-only `attempt` を追加する。既定出力は旧 fixture と同一にする。
- attempt2 の true は boolean を置くだけではなく、対差の分散を上げて raw arm と pairs、統計を整合させる。実寸の対数・arm 数を減らさない。
- semantic 負例は変更後に completion と test 専用 hash を再封印し、hash mismatch ではなく狙った述語で落ちることを例外文まで確認する。
- fig9 の着地閉包 `AT:471–486` は残す。旧 caption の小変更を検出する最終 oracle とする。

## 3. 図 (2) 生成器

**定数と入力**

`M:新規 / 定数部` は `B:27–50` を雛形とする。schema は `izanagi-mocc-witlight-four-arm-figure-provenance/v1`、`CAPTION_SOURCE = RM`、`EVIDENCE_ROOT = E`。

`EXTERNAL_SHA256` は root 相対 path を key にした次の5件だけとする。現物 SHA-256 は全件、`RM:307–312` と一致した。

| key | SHA-256 |
|---|---|
| `summary.json` | `b1be3ebde10c20ea26de3956495f927d2baa8c06ecc1b7e2d7222f2795310698` |
| `W1/result.json` | `ca8ab3ff579e3fb55b97447ebb7b647d34806a6fd452ad410051aca9e5bd4b50` |
| `W2/result.json` | `473063aa741cc4c349931d987c902facbc5dcf6499b3692ea2cad3a27ac1e584` |
| `W3/result.json` | `f68876600f1cd5b7300b030fb3cfa75509cc7a687858d6f12985051ce46e3642` |
| `W4/result.json` | `197a2798de5ef53a7f6a32460f7ecfa5adbba8e853778b315d3b6e1839c36a6c` |

| 定数 | 値・根拠 |
|---|---|
| `ARMS` | `("e9-witlight-wit", "e9-witlight-nowit", "e9-witlight-wit-bo1", "e9-witlight-nowit-bo1")`。`RM:132–135`。 |
| arm 対応 | 順に `(BACK_OFF,witness) = (0,True),(0,False),(1,True),(1,False)`。 |
| `BLOCKS` | `("W1","W2","W3","W4")`。 |
| `ROUNDS` | 15。`E/W1/result.json:6`。 |
| `RUNS_PER_BLOCK` / `PLANNED_PER_ARM` | 60 / 60。総数240。`RM:163–165`。 |
| schema | block=`t2774-probe/v1`、summary=`t2774-summary/v1`。 |
| 条件 | mocc、TRACE=1、3秒、48 thread、10,000 records、rr50、rmw0、max_ope10、Zipf0.9。`E/W1/result.json:6078`、`RM:125–127`。 |

- `M:新規 / _load_external`：`load_evidence(repo_root, evidence_root, *, expected_hashes=None)` の seam は上記5 key を要求する。CLI には露出しない。入力は列挙した5 file のみを開き、glob で block を集めない。
- `summary.json.inputs` は `E/summary.json:151` の4要素 list と exact に一致させる。期待値は **原保存先 `E` と W1〜W4 の path**、選択 pin の digest から組み立てる。余剰・重複・欠落・順序・path・hash をすべて照合する。
- `--evidence-root` は bytes の読出し場所であり、原本内部の path を書換える指定ではない。同じ bytes を別 root に移した場合も読めるが、summary 内の原保存先 path は引き続き exact 検査する。
- fixture も summary 内には原保存先 path を記録し、digest だけ test seam の値とする。smoke を追加した semantic 負例では summary の hash を再封印する。
- bindings の patch / runner / binary の path は記録として扱い、そこから追加 file を開かない。5 JSON 以外を権威入力に拡張しない。

**関数構成**

| 新規関数 | 実装内容と雛形 |
|---|---|
| `_load_external(evidence_root, expected_hashes)` | 5 file の exact key・hash・JSON schema を確認し、block と summary を返す。`B:287–304,501–508`。 |
| `_validate_blocks(blocks)` | block ID、completed、rounds15、planned60、not_started0、runs60、ordinal1〜60、round1〜15、各 round の4 arm 一意性、回転、run の block / arm / witness / pin と bindings の整合。 |
| `_project_runs(blocks)` | 再導出に必要な240件だけを縮約。block、ordinal、round、order、arm、rc、commit_count、verifier の status/rc/verdict/cycles、discriminator の記録を保持。 |
| `_derive_statistics(records)` | arm 別 N / m / k / failure / indeterminate / decisive_m、位置 Counter、commit 平均、CP、Fisher、on/off 曝露比を計算。 |
| `_crosscheck_summary(derived, summary)` | summary に実在する集計値・率・CP・discriminator / identification を照合。Fisher / commit 平均は summary に無いので照合対象に捏造しない。 |
| `load_evidence(...)` | 上記と caption_source の hash 記録を束ね、data を返す。例外を `FigureDataError` に統一。 |
| `_format_arm` / `_format_comparison` | 描画・caption・test が使う書式化。ただし test の期待値は生成器定数から作らず稿または独立 literal とする。 |
| `make_figure(data)` | 下記2 panel。実際に渡した系列と表示文字列を `fig._mocc_artist_series` に保持。 |
| `check_figure_layout(fig, axes)` | `B:416–445` を自己完結で移植し、axes 数を2に変更。 |
| `build_provenance(...)` | `B:448–462` 型。生値の縮約、統計、書式文字列、入力、条件、caption、実 artist 系列、argv を束縛。 |
| `validate_repo_closure(provenance, repo_root, *, expected_hashes=None)` | repo 内だけで caption_source・出力 hash・入力目録・schema・argv・内部再導出・artist/caption の整合を検査。 |
| `validate_external_sources(provenance, evidence_root, *, expected_hashes=None)` | 5 hash と原本の再導出を検査し、provenance の縮約 records・条件・集計と比較。hash 確認だけでは終えない。 |
| `_publish_outputs(...)` | `B:511–542` 型。検査成功前は出力先作成・保存をしない。 |
| `main(...)` | `B:545–564` 型。`--repo-root`、`--evidence-root`、prefix。失敗 rc2、Figure を finally で閉じる。 |

**集計の意味と実値**

- `E/W1/result.json:30,1747` と `E/W3/result.json:434` に、verifier status `no-g2` / `g2` がある。G2 signal は `verifier.status == "g2"` から数える。`total_cycles > 0` だけで一般の cycle を G2 と呼ばない。
- N は保存走数、m は failure を除いた有効 verdict 数で indeterminate を含む。decisive_m は zero-cycle indeterminate を除く。failure と indeterminate を no-g2 に加算しない（`RM:76–80`）。
- この専用入力の受理条件は全 arm で `N=m=decisive_m=60`、failure=indeterminate=0、未収載0。これらを再計算してから現 scope を要求する。未知 status は拒否する。
- `k=[0,1,0,1]`。G2 signal の2走は W1 ordinal18 と W3 ordinal5、いずれも off。discriminator は各 arm `not-run:60`、比較ゼロ、identifiedゼロ（`RM:196–211`）。
- commit 平均の分母は **その arm の保存走数60**。整数 commit 数の総和 / N とし、3秒で割らない。on/off 比は丸め前の平均どうしから計算する。

| arm | k/m | 率 | CP 両側95% | 平均 commit 数 |
|---|---|---|---|---|
| on, BACK_OFF=0 | `0/60` | `0%` | `[0%, 5.963%]` | `613,741.5` |
| off, BACK_OFF=0 | `1/60` | `1.667%` | `[0.042%, 8.940%]` | `710,659.4` |
| on, BACK_OFF=1 | `0/60` | `0%` | `[0%, 5.963%]` | `788,885.6` |
| off, BACK_OFF=1 | `1/60` | `1.667%` | `[0.042%, 8.940%]` | `933,621.8` |

- 上表は `RM:173–176`。平均の再計算値は順に `613741.4666666667`、`710659.4166666666`、`788885.6166666667`、`933621.8` で、一桁小数の丸めが一致した。
- `RM:185–186` の両 Fisher 表は `[[0,60],[1,59]]`、表示 `0.500`。`RM:217–218` の曝露比は `0.8636` / `0.8450`。これらも独立の短い算術確認で一致した。

**scipy を使わない CP / Fisher**

- `M:新規 / _beta_quantile`：整数 shape の Beta CDF を有限二項和で計算する。

```text
I_x(a,b) = Σ[j=a..a+b−1] C(a+b−1,j) x^j (1−x)^(a+b−1−j)
```

- `math.comb`、`math.fsum`、区間 `[0,1]` の二分法70回を使用。CP は lower=`Beta(.025;k,m-k+1)`、upper=`Beta(.975;k+1,m-k)`。k=0 の lower は0、k=m の upper は1。
- 算術確認結果：0/60 upper=`0.059629492286166874`、1/60 lower=`0.0004218744523420083`、upper=`0.08939905005748705`。summary との差は約 `7e-16` 以下。率の照合は `abs_tol=1e-12` とし、稿の百分率小数3桁に一致する。
- 0の書式だけ `"0%"`、それ以外は `f"{100*p:.3f}%"`。commit は `f"{mean:,.1f}"`、p は `.3f`、比は `.4f`。
- `M:新規 / _fisher_less`：行 on/off、G2総数 K、on 標本数 n、総標本数 T とし、超幾何確率を `x <= observed_on_k` の範囲で合計する。両側の「観測確率以下を合計」は使わない。`[[0,60],[1,59]]` は正確に0.5。
- 依存は標準ライブラリと matplotlib / numpy のみ（`FIGURE_CONVENTIONS.md:79–83`）。

**2 panel と caption**

- `M:新規 / make_figure`：横並び2 panel、両方に同順序の4 arm。短い行ラベルを `on / BACK_OFF=0` 等とし、exact arm ID の対応を caption に出す。
- panel(a)：横軸 `G2 signal detection rate (%)`。点と非対称 CP 横線、右側の予約領域に k/m・率・CP の上表文字列。0率の点は境界で切れない余白を設ける。
- panel(b)：横軸 `commits per run`。60走の commit 生値を淡い点、平均を明瞭な印、平均値を直接表示。`TRACE=1 exposure, not performance` を可視の副題へ置く。on/off 比は脚注の2行。
- 曝露平均へ新たな検定や登録外の推論区間は足さない。反復の散らばりは60点で示す。§2適合の説明では panel(a) の CP と panel(b) の記述的生値表示を区別する（`FIGURE_CONVENTIONS.md:30–37`）。
- 2 panel とも on/off を同じ軸へ置き、対照を caption だけに隠さない。区間の重なりから判定しない。
- caption の固定文は次を採用する（根拠 `RM:18–27,73–85,250–268`）。

  `Non-significance does not establish equivalence, and zero detections do not establish absence.`

  `Power 0.105 is a calculation under the design assumptions, not a measured quantity: independent Bernoulli trials, 60 runs per arm, off probability 0.0417, on probability 0, and a one-sided Fisher test at alpha 0.05.`

  `TRACE=1 commit counts are exposure, not performance.`

  `G2 signals do not identify a root cause or distinguish a real anomaly from a torn read.`

  `This is a non-certifying observation; individual verifier certified flags and observational_only=false do not certify this wave, MOCC, or the witness.`

  `The denominator includes only 4 blocks x 15 rounds x 4 arms; smoke runs are excluded.`

  `CP intervals and Fisher p values assume independent Bernoulli trials and do not model within-node dependence, rotation order, or temporal variation.`

- その他、主比較 BACK_OFF=0 / 副比較 BACK_OFF=1、on が低い方向・未調整 p、discriminator未到達、固定時間の走あたり率で同 commit 数への曝露比較ではないこと、旧 wave と合算しないことを記す。
- 禁止句は肯定形の `equivalence established`、`no witness effect`、`G2 cannot occur with witness on`、`performance improvement`、`root cause identified`、`MOCC certified` 等。否定の固定文を誤検出する単語単位の禁止はしない。

**provenance の二層**

- `M:新規 / build_provenance`：`tracked_inputs` は caption_source の1件、`external_inputs` は5件の root 相対 path / kind / hash。別 field に原保存先 root と summary inputs を記録する。
- 主要 field は `schema, generated_utc, generator, tracked_inputs, external_inputs, source_inputs, measurement_conditions, blocks, records, arms, comparisons, exposure_ratios, analysis, authority_note, crosschecks, artist_series, caption, outputs, reproduction`。
- `records` は240走の再導出用縮約。repo 内閉包はこれから統計と表示を再構成する。**外部原本との一致を repo 内閉包が独立に証明したとは書かない**。
- `validate_external_sources` が原本から同じ縮約を作り直して比較し、この差を閉じる。fig13 は一次数値が tracked にあるが、fig15 は外部なので、`B:469` の `_authority_data(root)` をそのまま移植できない。
- generator hash は生成時点の記録。現在の生成器 bytes との一致は要求しない（`B:481–483`）。

## 4. 図 (2) test

新規 `MT` は `BT:23–78,167–253,480–638` の構成を雛形にし、実寸 fixture と独立した数値 oracle を持つ。

| test 名 | 内容 |
|---|---|
| `test_fixture_has_production_shape_and_rotation` | 4 block ×60走、各 block 15 round ×4 arm、総240。開始 arm は block index と round index の和を4で割った余りで回転。各 arm は全体で各位置15回。 |
| `test_statistics_recomputed_from_runs` | N/m/k/failure/indeterminate/decisive_m、位置、commit 総和・平均、比を独立に確認。fixture の commit 数は block / round / arm で非一様にする。 |
| `test_cp95_matches_reference_values_and_boundaries` | 上記0/60・1/60の独立 literal、k=m境界、区間順序。summary を期待値の唯一の出所にしない。 |
| `test_fisher_is_one_sided_on_lower` | `[[0,60],[1,59]] -> .5`、行反転方向の別表、両側なら1になる識別例。 |
| `test_commit_mean_uses_all_runs_of_each_arm` | 分母60、G2走を含むこと、m・全240・15・3秒で誤除算しないこと。 |
| `test_external_hash_drift_is_rejected` | 5 file を一件ずつ改変し、旧 seam hash のまま hash mismatch。 |
| `test_production_pins_match_results_document` | `RM:303–327` から `arm-W/<relative>` の行を一意抽出し5定数と照合。外部 root が無くても実行。 |
| `test_summary_disagreement_is_rejected` | N/m/k/CP/decisive_m/discriminator/identification の各不一致。summary を再封印して狙った照合で落とす。 |
| `test_summary_inputs_are_exact` | 欠落・重複・順序・path・digest の誤り。summary hash を再封印。 |
| `test_summary_inputs_reject_smoke_extra_entry` | 元の4件と集計は正しいまま smoke の第5 entry だけ追加。exact inputs 検査だけで拒否させる。 |
| `test_smoke_or_duplicate_run_in_main_block_is_rejected` | block ID smoke、余剰走、重複 ordinal、欠落 round を個別に拒否。 |
| `test_arm_bindings_and_rotation_are_checked` | witness / BACK_OFF / order の不一致。hash gate は通して意味検査を確認。 |
| `test_failure_and_indeterminate_are_not_no_g2` | failure・indeterminate を独立に集計できることと、この専用図の完全収載条件では拒否すること。 |
| `test_rendered_artists_equal_provenance` | CP の端点、4点、曝露240点・4平均、直接 label を実 artist から照合。 |
| `test_real_figure_passes_layout_check` | 本物の Figure、axes `(1,2)`、実寸の注記密度で検査。 |
| `test_required_disclosures_are_rendered` | `fig.findobj(Text)` で exposure 文、4 arm、率・区間・平均の文字列が可視で存在。削除で重なりだけ解消しても緑にしない。 |
| `test_layout_rejects_overlap_wrong_axes_and_escape` | 本物の Figure に重なり、axes追加、逸脱を個別注入。 |
| `test_layout_failure_publishes_nothing` | `_publish_outputs` を通し3成果物ゼロを要求。 |
| `test_caption_fixed_literals_and_forbidden_claims` | §3の固定文を独立 literal で照合。肯定の禁止句を検査。 |
| `test_caption_number_comes_from_prefix` | fig15 / 任意の数値prefix、非 `fig<N>_` 拒否。 |
| `test_cli_outputs_and_provenance_closure` | 実 Figure のCLI実行、3成果物、argv、repo / external 双方の閉包、各 field のdrift拒否。 |
| `test_external_sources_and_repo_closure_have_separate_roots` | `BT:506–516` 型。外部 file を消して repo 閉包は通り、external 検査は失敗。入力目録欠落は repo 検査でも失敗。 |
| `test_relocated_evidence_keeps_original_input_paths` | bytes を別 root に置いてもロード可能。内部原保存先の書換えを要求しない。 |
| `test_landed_fig15_repo_closure_and_caption_when_present` | `BT:623–638` 型。着地3 file、exact出力path、README自節のhash3行・caption、caption_source現hash。外部の有無でskipしない。 |
| `test_landed_fig15_rejects_missing_or_partial_bundle` | 着地物欠落を skip せず失敗。 |
| `test_real_evidence_loads_when_root_present` | 外部 root 不在時だけskipする唯一のtest。原本ロード、稿§2.2/2.3/2.6のセルとの逐語一致、実Figure layout、着地provenanceへのexternal閉包をまとめて実行。 |

- fixture は `W1/18` と `W3/5` に G2 signal を置き、他238走を no-g2 とする。smoke file を通常 fixture に含めない。負例の smoke は通常入力から独立した追加 entry として作る（`E/W1/result.json:1747`、`E/W3/result.json:434`）。
- 全 fixture は5 JSONを生成し、W1〜W4をhash化した後に summary inputs を作って最後に summary をhash化する。
- semantic 負例でも描画・検査関数をmockしない。変更対象と必要なhashだけを再封印する（`BT:300–312`）。
- `test_real_evidence_loads_when_root_present` は root が存在するのに1 file が欠ける場合や読めない場合を skip しない。
- 稿比較はMarkdownの backtick / bold の装飾だけを外し、`0%` と `0.000%`、`0.8450` と `0.845` を同一視しない。

## 5. 新規 test の登録

- **専用の test 登録設定は要らない。** `test_*.py` と `test_*` の通常収集を使う。根拠は `J/s1-pin-closure.md:29–38`。新規汎用台帳・gateは追加しない。
- 唯一の条件付き対象は `orchestrator/tests/acceptance_duration_ledger.json:2,26609`。消費者は `orchestrator/tests/conftest.py:1007,1627` と `tools/acceptance_shards.py:63`。
- `orchestrator/tests/test_acceptance_schedule_order.py:660–712` の90%被覆に十分な余裕があれば、今回のnodeを台帳へ登録しない。
- 余裕は本段では**未確認**。P9と `J/s1-pin-closure.md:35–38` に従い親が段4で確定する。
- 不足時だけ Codex author が実走JUnitを入力に `tools/update_acceptance_duration_ledger.py --add-only <JUnit>` を実行する。`duration_seconds_by_nodeid` への nodeid→実測秒と `nodeid_count` 更新はproducerに任せ、手書きの推定秒を登録しない。収集・実走は `tools/run_tests.py` 経由とする。

## 6. docs の骨子

- `docs/paper-story/figures/README.md:31` の一覧末尾へ次の2行を追加する。

| filename | 生成器 | 状態の骨子 |
|---|---|---|
| `fig14_a1_balanced5_sized_attempt2.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_a1_sized_paired.py`（`--attempt attempt-0002`） | attempt-0002単独記述図。fig9と同形の兄弟、非認証lane、breach開示、attempt間のプール・比較・再現判定なし。 |
| `fig15_mocc_witlight_four_arm.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_mocc_witlight_four_arm.py` | W1〜W4の非certifying観測。G2検出率・CPとTRACE=1曝露量の2panel。smoke除外。 |

- fig14 / fig15 節は現末尾 `docs/paper-story/figures/README.md:1839` の後へ追加。H1 はそれぞれ ``# `<basename>` — …``。小見出し順は fig9 (`:948–1049`) / fig13 (`:1721–1829`) と同じにする。

| 見出し | fig14 | fig15 |
|---|---|---|
| `## 何を示す図か` | 3workload・30対、登録区間と床、breach true/false。 | 4arm・検出率/CP・曝露量、計画/収載分母。 |
| `## 既存図との関係` | fig9のbytes維持、比較なし、稿の「図は無い」は起草時点の事実。 | 旧mocc観測と合算なし、既存図の後継ではない。 |
| `## 入力` | 選択表4pin、completion、caption_source。 | 外部5pin、exact inputs、runsからの再導出、照合先の区別。 |
| `## 再現` | `--attempt attempt-0002` とfig14 prefix。 | `--evidence-root E` とfig15 prefix。 |
| `### 再現できるのは「値」であって「バイト列」ではない` | 旧図を上書きしない、hashによる着地閉包。 | repo / external の二層と外部不在時の射程。 |
| `## 作図規約への適合` | 登録区間は95% CIと呼ばない、breachを実描画。 | CP・60生値の曝露表示、2panel、依存、実寸fixture。 |
| `## キャプション正文` | 生成器のcaption全文。 | 生成器のcaption全文。 |
| `## proof chain` | pair→統計→artist→caption→leaf/稿。 | run→集計→artist→caption、外部原本再検査。 |
| `## 着地 bytes の SHA-256` | png/pdf/provenanceの正確な3行。 | 同左。 |

- hash 行は `AT:483–486` / `BT:635–638` の正規表現に合わせる。`(記録)` を見出しに付けない。
- `tools/plotting/README.md:196–224` の既存 attempt1 節は残し、その直後へ attempt2 節を追加する。CLI、exact選択表、attempt別breach受理、表示、caption_source、fig14節への導線を置く。
- `tools/plotting/README.md:465–481` の後へ mocc 節を追加する。CLI、外部5入力、再計算・照合、2panel、出力/schema、fig15節への導線だけを置く。
- 両図ともD1637の「2本目の論文と共用しない」を記載。results稿・版は編集しない（`J/s1-brief.md:41–50`）。

## 7. 変異候補

新規関数の正確な行番号は実装後、段4の登録時に確定する。以下の新規位置は関数・文のアンカーであり、架空の現物行番号ではない。

| # | 対象位置・変更 | killするはずのtest | 単一理由 |
|---|---|---|---|
| 1 | `A:236` 由来の attempt1 `is False` 拒否を削除 | 既存 `test_variance_plan_breach_true_is_rejected` | 述語・統計・hashが整合したtrueなので、scope拒否だけを除く。 |
| 2 | `A:55` 後の attempt2 result pinを1文字変更 | `test_attempt2_pinned_input_hashes_match_results_document` | 入力や稿を変えず定数だけを変える。 |
| 3 | `A:276` の旧caption `sized run` の1語を変更 | 既存 `test_landed_fig9_repo_closure_and_caption_when_present` | 数値・入力・出力bytesは不変、caption完全一致だけを破る。 |
| 4 | `A:264` 後の `_caption_attempt2` からプール・比較禁止文を削除 | `test_attempt2_caption_contains_fixed_literals_and_breach_values` | 他caption値を変えず開示文だけを欠落させる。 |
| 5 | `M:新規 / EXTERNAL_SHA256["summary.json"]` を1文字変更 | `test_production_pins_match_results_document` | 外部rootの有無によらず定数と稿の一致だけでkill。 |
| 6 | `M:新規 / _load_external` のsummary inputs exact照合を削除 | `test_summary_inputs_reject_smoke_extra_entry` | 再封印済みsummaryへ第5entryだけ追加。4blockと集計は正常。 |
| 7 | `M:新規 / _cp95` のupper分位 `.975` を `.95` に変更 | `test_cp95_matches_reference_values_and_boundaries` | CPの片端だけを破壊。fixture summary生成に同関数を使わない。 |
| 8 | `M:新規 / _fisher_less` を両側確率和へ変更 | `test_fisher_is_one_sided_on_lower` | 同じ2×2表で0.5→1.0となり方向だけを識別。 |
| 9 | `M:新規 / _derive_statistics` のcommit平均分母Nを総240に変更 | `test_commit_mean_uses_all_runs_of_each_arm` | commit生値と率を保ち、曝露平均だけを誤らせる。 |
| 10 | `M:新規 / _publish_outputs` のlayout呼出しを削除 | `test_layout_failure_publishes_nothing` | loader・Figureは正常、重なりだけが保存拒否理由。 |
| 11 | `M:新規 / make_figure` の可視 exposure 文を削除 | `test_required_disclosures_are_rendered` | caption・数値は維持。実artistの開示欠落をkill。 |
| 12 | `A:69` の空行付近へコメントだけ追加 | 全関連test、特に既存 `test_generator_comment_change_preserves_provenance_closure` | 等価対照。`SURVIVED`予測。生成時source hashは現sourceのpinではない。 |

## 8. 落とし穴

- **新規行番号**：`M / MT` の現物行は未存在。段4登録では実装位置へ置換する。既存fileについては上記の変更前行をアンカーにする。
- **実寸fixtureの費用**：`AT:80–125` の180値、`MT` の240走はいずれも小さい。CPは最大60項×70回×8端点程度で、JSON処理より描画・PDF保存の費用が支配的と見込む。追加test群は通常30〜120秒程度を初期見積りとするが、**実測未確認**。数値testで毎回Figureを作らず、render / publish testへ描画を限定する。
- **長いpanel題**：`A:320` の既存題にbreachとsd/sigmaを足すため、fig14だけ高さ・余白を調整する。文字を消す、bbox検査を緩める、fig9の全体rcParamsを変える方法は採らない。layout通過は親の実走待ち。
- **fig15のlabel密度**：`B:424–442` 型は可視Text同士を全件照合する。率・区間の表記と曝露比には専用余白を取り、凡例と二重表示しない。存在検査も併用する。
- **prefix**：`A:258–261` は `fig14_` / `fig15_` を受理する。`fig9b_` は受理しないまま。生成器は番号を一般的に導き、着地testがexact basenameを縛る。
- **原保存先と読出しroot**：`E/summary.json:151` の絶対pathを読出しrootへ置換すると、bytes移設時の再現が壊れる。原path照合とfile読出しを分ける。
- **G2のfield**：statusはrun最上位でなく `runs[].verifier.status`（`E/W1/result.json:30,1747`）。verifier rc1を無条件でG2と数えない。
- **小数丸め**：`R2:214` はread-heavy sdの再計算最終桁差を明記している。A-1の数値照合は現許容差を維持し、moccの稿表との逐語一致は書式化後に行う。
- **font解決**：`A:299–300` と同じ Agg / DejaVu Sans を使い、図中文字は英語中心とする。親のlogin実走では書込可能なfont cacheを用意し、font解決と実layoutを確認する。本段はread-only・tmpなしなのでmatplotlib実走はしていない。
- **凍結物**：fig9やresults稿を再生成・更新しない。再現確認が必要な旧図は別の一時prefixで行い、着地fig9は既存testで検査する（`docs/paper-story/figures/README.md:5–8`）。

## P の反証

- **P1〜P8を覆す根拠は見つからなかった。** P1は `J/verbatim/D2194-item6.md:9` の「必要になれば単独図」と、`J/verbatim/fig9b-wave-RESOLVED.md:5` の並記図中止を両立させる。
- **P6の適用範囲を確認した。** `E/summary.json:3–149` にFisher・commit平均は存在しない。`J/s1-brief.md:30–33` の補足どおり、これらはrunsから計算し稿との一致をtestする。P6を変更する理由ではない。
- **P8は二層のまま採用する。** fig13のtracked数値再導出（`B:465–496`）を外部一次数値のfig15へそのまま移すことはできない。repo側は保存された縮約値の自己整合、external側は5原本との再導出一致、と射程を明記する。
- **P9は条件付き採用。** 被覆余裕の実測は本段では未確認であり、登録不要を無条件には確定しない（`J/s1-brief.md:39–40`）。

## 総括

- P1〜P8を採用し、fig14はattempt-0002単独、fig15はmoccの2panelとして計画した。
- `A:36–59,251–286` の旧定数・返却値・captionを保ち、fig9の着地閉包を維持する。
- attempt2のbreachは述語一致で受理し、3workloadのboolean・sd・sigmaを実際の図とcaptionに出す。
- moccの5pinは原本と稿に一致し、CP・Fisher・commit平均・曝露比の丸め一致を算術確認した。
- fig15のrepo閉包と外部原本検査を分け、外部不在によるskipは1testに限定する。
- 既存testを弱めず、実寸fixture、実artist、caption、着地README閉包の検査を追加する。
- P9の被覆余裕、実layout、loginのfont解決、test所要時間は未確認で親の実走に残す。
- 本段ではfile書込み・実装・pytest・作図を行っていない。