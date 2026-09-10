## 所見 1 — 非 hashable な登録外 tag が report を停止する

- 深刻度: **must-fix**
- 根拠: [`b10_backoff_shape_sweep.py:2895`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2895) で取得した `tag` を、次行で set に対して membership 検査している。`tag` が list / dict なら `TypeError: unhashable type` になる。例外捕捉は WAL 読取り部分の [`2876-2881`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2876) で既に終了している。
- 到達可能性: WAL は nested list / dict を正規の JSON-native payload として許す [`wal.py:304`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/wal.py:304)。したがって `{"workload":{"tag":[]}}` は decoder を通る。
- 裁定との差: R3 は登録外 tag を開示だけに限定しており、report 停止を禁じている。
- 成果物影響: 135 block record が正しく揃っていても report JSON、Markdown、判定台帳が一切発行されない。

## 所見 2 — M6 は adapter から digest 呼出しを外す変異を殺さない

- 深刻度: **must-fix**
- 根拠: production の実効接続は [`b10_backoff_shape_sweep.py:2689`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2689) の `_require_legacy_record_digests(content_digests)` 1 行である。
- 新テスト [`test_b10_backoff_shape_sweep.py:1373`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:1373) は helper を直接検査するだけで、adapter の正例を通さない。adapter 呼出しは誤った campaign ID と空 records で早期拒否させている [`1393-1399`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:1393)。
- 結果: production の 2689 行だけを削除しても、このテストは緑のままになる。これは M6 の「digest 照合を外し格子と binding だけで通す」そのもの。
- 成果物影響: この変異では `correctness_certified` や `median_tps` を改変して自己 hash を再計算した歴史 record が `judge()` に入り、選択結果と report 値が変わる。変異台帳も誤って M6 を防護済みと扱いうる。

## 所見 3 — M5 の欠落変異は単一理由でなく、str 型の退行も未検査

- 深刻度: **should-fix**
- 根拠: 欠落した host は型検査 [`b10_backoff_shape_sweep.py:2467`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2467) と truthiness 検査 [`2468`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2468) の両方に拒否される。
- テスト [`test_b10_backoff_shape_sweep.py:1357`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:1357) は欠落と空文字だけで、truthy な非 str を試さない。2467 行を外して `execution_host=1` を受理する変異は緑のまま。
- 裁定との差: [`s4-ruling.md:214`](/home/SFC/tanab/.claude/jobs/9dc3ec5b/tmp/wave-b10-preflight-fixes/s4-ruling.md:214) の M5 は「欠落を許す」変異であり、[`218-219`](/home/SFC/tanab/.claude/jobs/9dc3ec5b/tmp/wave-b10-preflight-fixes/s4-ruling.md:218) は同じ入力を拒否する別理由がないことを要求している。
- 成果物影響: 型検査だけが退行すると非 str host を持つ current record が受理され、provenance と Markdown の host 値が変わる。

## 所見 4 — M7 の `>=` 緩和は受理集合を動かさず、変異帰属が成立しない

- 深刻度: **should-fix**
- 根拠: exact gate は件数、重複、set equality の三条件 [`b10_backoff_shape_sweep.py:2550-2555`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2550)。
- 件数比較を「135 以上も許す」形へ変えても、余分な unique cell は set equality、重複 cell は重複条件に拒否される。新テスト [`test_b10_backoff_shape_sweep.py:1425`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:1425) の追加 record も同じ理由で件数条件へ一意に帰属しない。
- 裁定との差: M7 は KILLED を要求するが、この変異単体は意味保存であり、KILLED / SURVIVED の実効判定対象にならない。
- 成果物影響: report の現行受理集合は変わらないが、変異台帳が 135 gate の検出力を誤って件数比較へ帰属させる。

## 所見 5 — R8 の JSON producer は新テストの外にある

- 深刻度: **should-fix**
- 根拠: production 値は [`b10_backoff_shape_sweep.py:3040`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:3040) で `False` にしている。
- テストは自作 fixture に `False` を入れ [`test_b10_backoff_shape_sweep.py:1461-1470`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:1461)、直接 `_write_reports()` へ渡している。3040 行を `True` にしても緑のまま。
- 成果物影響: この退行では provenance JSON が「全 workload job の終端を証明する」と誤記し、Markdown の否定文と矛盾する。

## 所見 6 — R7 例外外でも既存テスト期待値を変更している

- 深刻度: **should-fix**
- 根拠: 段 4 は既存期待値の変更を禁止し、例外を policy current SHA、2 consumer、壁時計 meta-testに限定している [`s4-ruling.md:193-196`](/home/SFC/tanab/.claude/jobs/9dc3ec5b/tmp/wave-b10-preflight-fixes/s4-ruling.md:193)。
- 例外外の変更:

  - `FORMAL_PHASES` の既存期待値: [`test_b10_backoff_shape_sweep.py:1131-1132`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:1131)
  - job script の exact invocation/phase/dependency期待値: [`2186-2197`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:2186)
  - dry-run の receipt 数と phase 期待値: [`2334-2353`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:2334)
  - spawn-site ledger の既存行番号: [`test_ccbench_spawn_sites.py:827-841`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_ccbench_spawn_sites.py:827)

- これらは機能上自然な追従だが、段 4 の明示的例外には含まれない。
- 成果物影響: runtime の選択値は変えないが、受入テスト集合と spawn-site 台帳の参照値を裁定外で変更している。親による追加例外裁定が必要。

## R2 の有限集合検証

R2 の production 実装自体は適合している。

- 官製 45 file の envelope `record_sha256` は全件 unique。
- そのソート済み集合と実装定数のソート済み集合は、双方の集合 digest が `6cb14801e858cedd955d983267436585d75c713be48d79b50b0076fd99845b71` で一致した。
- `_load_block_record()` は envelope の exact key set と、record 全体の canonical SHA を再計算する [`2400-2408`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2400)。
- legacy digest は synthetic な `record_sha256` だけを除き、`envelope["record"]` の全 key/value を canonical JSON 化する [`2583-2592`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2583)。したがって `correctness_certified`、`median_tps`、`missing` を含む record のどの欄も digest 外にない。
- 45 digest は件数と集合の両方で exact 比較する [`2575-2580`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2575)。
- digest 外の参照は別途、campaign ID [`2618-2619`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2618)、lock binding [`2595-2608`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2595)、receipt bytes/hash [`2670-2680`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2670)、45-cell grid [`2689-2692`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2689) で閉じている。
- JSON の空白、key 順、escape 表記は digest 外だが、canonical 化後の意味内容を変えないため受理値への穴ではない。

## 絶対規律 2 への接触

正しさ防壁の弱体化は見つからなかった。

- correctness 使用条件は未変更: [`b10_backoff_shape_sweep.py:1738-1752`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:1738)。
- committed attempt / `BUILD_DONE` receipt 消費は未変更: [`2696-2726`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2696)。
- correctness binary と測定直前 binary の三者 SHA 照合は未変更: [`2729-2749`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2729)。
- `run_campaign()` の correctness 経路と abort 停止条件も維持: [`3450-3472`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:3450)。
- preregistration parser、patch/formula、`EXTIME=3`、`REPS=5`、規模・厳しさに diff hunk はない。追加された 1/5 は完全性の開示用で、実行回数を変えていない。
- correctness receipt 発行・検証を持つ exact 24-path closure に差分はない。

## 受理集合の全数

確認できた変化は次のとおりで、所見 1 を除き R1〜R8 の意図内だった。

| 面 | 変化 |
|---|---|
| CLI / receipt | workload 無しの `report` phase を新規受理 |
| current v2 block | host 欠落・空文字を新規拒否 |
| legacy block | `e3de15eb` の現物 45 件だけを report 経路で新規受理 |
| report 発行 | workload job の随時発行を廃止し、report phase + exact 135 に限定 |
| report namespace | submission trial 別から binding ごとの固定 `reports/final` へ変更し、2 通目を拒否 |
| walltime | literal 4 箇所から policy 値へ移行。不正・欠落 policy は新規拒否。値は 43200 のまま |
| report dependency | report は gflags/glog の job-local build を省略。判定入力の検査は省略していない |
| WAL 完全性 | 開示面を追加。list/dict tag だけは所見 1 の誤拒否あり |
| cache | nonce ごとの配置へ変更。record admission ではなく build artifact の参照範囲の変更 |

これ以外の validator 緩和、correctness gate、SHA 条項、事前登録規模の変化はない。

## 新規テストの変異帰属

| テスト | 赤になる 1 行 | 判定 |
|---|---|---|
| same-job SHA positive | `b10_backoff_shape_sweep.py:2743` の一致条件反転 | 既存 SHA gate の正例。負例は既存 M15 |
| nonce cache root | `b10_backoff_shape_sweep.py:3390` から nonce を除去 | M4 に一意 |
| source-root preimage | `build_admission.py:666` から source body を除去 | D1220 に一意。ただし本 commit の変更行ではない |
| report-only writer | `b10_backoff_shape_sweep.py:3404` の report 分岐を外す | 現在の直接呼出し形には有効 |
| host producer | `b10_backoff_shape_sweep.py:3514` または `3545` | 取得元と row 収載を別々に検査 |
| current host validator | `b10_backoff_shape_sweep.py:2468` を緩める | 空文字は赤。型と欠落は所見 3 |
| legacy digest | helper の `2577` を緩める | helper は赤。adapter の `2689` 削除は所見 2 |
| lock binding | `b10_backoff_shape_sweep.py:2605` の比較を緩める | 一意 |
| exact 135 | 該当なし | M7 は所見 4 |
| report disclosure | Markdown の `3132-3134` または収載の `3109` | writer は検査。producer の `3040` は所見 5 |
| verification completeness | cap の `2934`、未知 tag 分岐の `2896`、tail の `2878` | str tag、上限、tail は検査。非 hashable tag は所見 1 |

M1〜M3 は既存の壁時計 meta-testが、job receipt、scheduler comparison、driver request の各 `+1` を別々に赤にする構造になっている。M4 は適合。M5〜M7 は上記残件あり。

なお `_write_reports()` の2回目失敗テスト [`test_b10_backoff_shape_sweep.py:1518`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:1518) は、directory の `exist_ok=False` と file の `"x"` のどちらを単独で緩めても他方が拒否するため、単一行への帰属はない。現行成果物への影響はないので **nit**。

## 禁止パス

`51b3cd5bf..092f69e45` の変更は次の 7 path だけだった。

- `orchestrator/campaign/b10_backoff_shape_sweep.py`
- `orchestrator/tests/pegasus_policy_expected_goldens.py`
- `orchestrator/tests/test_b10_backoff_shape_sweep.py`
- `orchestrator/tests/test_ccbench_spawn_sites.py`
- `tools/pegasus/b10_backoff_shape_campaign.sh`
- `tools/pegasus/policy.json`
- `tools/pegasus/submit_b10_backoff_shape.sh`

exact 24-path closure [`campaign_lock.py:49-74`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/campaign_lock.py:49)、`buildcache.py`、`reservation.py`、`docs/`、`patches/`、`external/ccbench/` はすべて差分なし。

## 総括

- must-fix:

  - R3: list / dict の登録外 tag が `TypeError` で report を停止する。
  - M6: adapter の digest 照合呼出しを外す変異が新テストを通過する。

- R1: **適合** — current HEAD の driver bytes を binding に含め、base `94d2cb33...` から `e8c8478d...` へ変わるため新 campaign identity になる。
- R2: **適合** — 現物と一致する unique 45 digest、全 record 内容、campaign、lock、receipt、grid を exact 検査。ただし M6 テスト接続は must-fix。
- R3: **不適合** — string の未知 tag、tail、上限超過は開示のみだが、非 hashable tag が report を停止する。
- R4: **適合** — `(workload, variant, tag)` 件数法、上限 cap、順序非依存、重複識別不能の限界を開示。
- R5: **適合** — nonce cache root、同一 job SHA gate、source-root preimage を維持。
- R6: **適合** — current record は非空 str host 必須、欠落許容は exact 45 の legacy adapter のみ。テスト帰属に残件あり。
- R7: **適合** — policy の単一定数 43200、PBS literal 12:00:00、4 数値 consumer の値一致を実装。
- R8: **部分適合** — exact 135 と report 内の非証明表示は実装済み。設計文書側は R9 として親の未処理。

親裁定へ返すべき残件:

- 所見 1、2 の修正。
- M5、M7、R8 producer テストの再照準。
- R7 例外外で変更した既存テスト期待値を追加承認するか、裁定どおり戻すか。
- R9 の設計文書訂正。
- 次系列で歴史 campaign を再利用する場合の事前裁定。

本レビューでは pytest を実行していない。親が既に把握している `_prepare_official_output` の 1 赤は所見へ重複掲載していない。