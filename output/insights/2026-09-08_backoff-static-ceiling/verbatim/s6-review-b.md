## 判定

差戻しです。現行動作に 1 件、変異被覆に 2 件の must-fix があります。新規の raw/物理値経路そのものは概ね閉じていますが、B-10 の旧 135 cell の束縛が v5 化に追随できていません。

pytest・build・実測は行っていません。

## 所見

| ID | 判定 | 重要度 | 根拠 |
|---|---|---|---|
| F1 | **real** | **must-fix** | v4 の 135 cell を旧束縛のまま残すと宣言している一方、legacy adapter は `prereg.binding` から現行 v5 の commit/spec/patch/formula を取り込み、旧 binding SHA と合成している。[preregistration.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/b10-backoff-shape-preregistration.md:13) [b10_backoff_shape_sweep.py:2805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:2805) [b10_backoff_shape_sweep.py:2943](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:2943) 実際の旧 provenance は patch `36cd…`、formula `5b3d…` である。[provenance.json:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/output/insights/2026-08-31_t1905-b10-formal-run/reports/write-heavy/b10_backoff_shape_provenance.json:8) validators はこの合成束縛との完全一致を要求する。[b10_backoff_shape_sweep.py:2887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:2887) |
| F2 | **real** | **must-fix** | M8 の node は helper の出力を検査するだけで、`load_reference_binding()` がその helperを使うことを固定していない。[test_backoff_requested_us.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_requested_us.py:637) production の 2 呼出しを現行 `genomes()` に戻しても helper を残せば、この node は緑のままである。[backoff_requested_us.py:659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_requested_us.py:659) [backoff_requested_us.py:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_requested_us.py:669) |
| F3 | **real** | **must-fix** | M11 の actual prereg hash 突合 node がない。fixture は patch 現物から期待 SHA を自己生成し、canonical 文書の test は parse だけで patch bytes と比較しない。[test_b10_backoff_shape_sweep.py:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:193) [test_b10_backoff_shape_sweep.py:796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:796) [test_b10_backoff_shape_sweep.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:1088) stale SHA は production preflight の `validate_patch_bytes` で初めて止まる。[b10_backoff_shape_sweep.py:1528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:1528) |
| F4 | **real** | **nit** | v5 発効後も「本走は本書 v4 を含む commit」と現在形で残り、parser 診断と test 名も v4 のままである。[preregistration.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/b10-backoff-shape-preregistration.md:83) [b10_backoff_shape_sweep.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:1040) [test_b10_backoff_shape_sweep.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:1088) preflight は fail-closed なので値の誤受理にはならない。 |
| F5 | **refuted** | **nit** | 新系列で raw 3000 を物理 3000 µs として出す経路は確認できなかった。generator、report、overthrottle、resume、manifest は物理 1000 と raw 3000 を分離している。[backoff_extended_sweep.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:384) [backoff_extended_sweep_report.py:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep_report.py:490) [backoff_overthrottle.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_overthrottle.py:81) [backoff_overthrottle.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_overthrottle.py:334) |
| F6 | **refuted** | **nit** | 旧 F718 図・provenance・walk model は新 codec で読み替えられていない。図は旧 repository commit/campaign ID を pin し、raw 1000 を F718 として扱う。[plot_b10_extended_backoff.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/plotting/plot_b10_extended_backoff.py:33) [plot_b10_extended_backoff.py:711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/plotting/plot_b10_extended_backoff.py:711) walk model も v1/999 に固定され、新 1000 を明示的に拒否する。[t2216_backoff_walk_model.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/tools/t2216_backoff_walk_model.py:52) [test_t2216_backoff_walk_model.py:994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_t2216_backoff_walk_model.py:994) |
| F7 | **refuted** | **nit** | scope 外の gate・台帳・一般化を追加したハンクはない。変更 17 file は codec、下流追随、歴史固定、prereg、docs、直接 test/fixture に限定される。 |

must-fix の成果物影響:

- F1: v5 report collector は旧 write-heavy/balanced を束縛不一致で拒否し、新 write-heavy/balanced は hard-code された旧 ID のため参照しない。B-10 材料レポートの受理集合が成立しない。
- F2: M8 が入ると D1106 の raw 1000 が current raw 3000 に置換され、凍結 reference set が不一致となって診断材料レポートを生成できない。
- F3: M11 が入ると stale prereg hash のテストが全緑のまま、正式走行だけが `patch-sha` で停止し、v5 formal 成果物が作られない。

## 段 3 の取り残し対応表

| 段 3 の指摘 | 判定 | 根拠 |
|---|---|---|
| 過剰抑制 producer | **閉じた** | label と `backoff_us` は codec で物理値化され、resume と manifest summary も同じ helper を使う。[backoff_overthrottle.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_overthrottle.py:81) [backoff_overthrottle.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_overthrottle.py:316) [backoff_overthrottle.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_overthrottle.py:475) |
| 旧診断モジュールの歴史固定 | **部分的** | 実装は旧 raw grid/base/seed を局所固定した。[backoff_requested_us.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_requested_us.py:68) [backoff_requested_us.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_requested_us.py:96) ただし M8 の consumer 接続被覆がない。 |
| 事前登録 parser の版 | **部分的** | 文書と parser は v5 で一致する。[preregistration.md:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/b10-backoff-shape-preregistration.md:312) [b10_backoff_shape_sweep.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:294) ただし actual prereg hash の M11 被覆がなく、legacy 135-cell collector は悪化している。 |
| coder-spec | **閉じた** | q=1/2 と q≥3 の意味が分離された。[coder-spec.md:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/src/coder-spec.md:37) |

## 生値・物理値の閉包

| 面 | 判定 |
|---|---|
| generator / WAL | raw 3000 を genome/WAL に保存し、label は `fixed-1000us`。正しい分離。 |
| T-2266 report | raw genome を保持しつつ `backoff_us=1000` を出す。[backoff_extended_sweep.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:646) [backoff_extended_sweep.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:729) |
| extended report | WAL genome を codec で復号してから比較・選択する。[backoff_extended_sweep_report.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep_report.py:462) |
| overthrottle resume/manifest | 既存行検証、rep 行、summary がすべて物理値 helper を通る。 |
| campaign identity | extended/T-2266 とも slug・scale・trial を別版へ分離済み。[backoff_extended_sweep.py:473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:473) [backoff_extended_sweep.py:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:506) |
| 旧図・旧 provenance・F718 | 旧 raw 1000 のまま pin。新解釈への遡及変更なし。 |
| B-10 旧 135 cell | 値の再解釈はないが、F1 の束縛合成により現行 reader の参照が壊れる。 |

## 変異 12 件の判定

| 変異 | 落とす node | 判定 |
|---|---|---|
| M1 `% 1000` へ戻す | `test_actual_cpp_expression_compiles_with_werror_and_matches_fraction_model` の raw 3000→1000 literal。[test_b10_backoff_shape_sweep.py:2899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:2899) | **実在する** |
| M2 `-1999` | 同 node | **実在する** |
| M3 Python 高域を旧 `mean_us` | `test_high_static_raw_values_and_exact_model_domain_are_literal_pins`。[test_b10_backoff_shape_sweep.py:2590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:2590) | **実在する** |
| M4 encoder `+1000` | `test_static_codec_is_bijective_on_its_exact_bounded_domain` の `1000→3000` pin。[test_backoff_extended_sweep.py:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:291) | **実在する** |
| M5 上限撤去 | codec の物理 10000 拒否と `exact_model(12000)` 拒否。 | **実在する** |
| M6 上限を 10000 に緩和 | 同じ 9999/10000・11999/12000 境界。 | **実在する** |
| M7 overthrottle label を raw に戻す | `test_static_1000_generator_to_diagnostic_report_uses_physical_label`。[test_backoff_overthrottle.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_overthrottle.py:76) | **実在する** |
| M8 歴史固定を外し現 `genomes()` を読む | helper 自体は検査されるが、production consumer が helper を使うことを固定する node がない。 | **実在しない — 全緑予測** |
| M9 T-2266 report schema literal | report materialization node が literal v2 を検査する。[test_backoff_extended_sweep.py:419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:419) | **実在する** |
| M10 `EXPECTED_HOLE_LINE` を patch と不一致にする | exact patch-line node。[test_b10_backoff_shape_sweep.py:2848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:2848) | **実在する** |
| M11 prereg `patch_sha256` を旧値にする | actual canonical prereg の hash を現物 patch と比較する node がない。 | **実在しない — 全緑予測** |
| M12 raw 1000 を静的 1000 と宣言 | F718 の observed 0 負例と codec の raw-gap 拒否。[test_condition_meaning_gate.py:414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_condition_meaning_gate.py:414) [test_backoff_extended_sweep.py:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:307) | **実在する** |

結論は 10/12。M8・M11 は「変異しても全部緑」の予測です。

## scope 監査

scope 外ハンクは見つかりませんでした。新規 gate、一般化、台帳は追加されていません。

一方、次の既知事項は **real / nit（本 wave では裁定パッケージのみ）** です。

- 非負 `BACKOFF_FIXED` の production meaning declaration は引き続き `None` で、`unestablished` が admission される。[backoff_sweep.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_sweep.py:133) [condition_meaning_gate.py:4058](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:4058)
- 1000 µs 超の測定格子は追加されておらず、endpoint は依然 1000 のみである。[backoff_extended_sweep.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:55)

いずれも裁定どおり scope 外であり、この review から実装要求は出しません。

## 静的確認

- staged diff と `integrated-snapshot.patch` は SHA-256 `02d4435c…f4ed32` で逐語一致。
- `git diff --cached --check` は出力なし。
- patch 現物 SHA-256 は prereg の `a5e0710c…8580a` と一致。
- pytest・build・実測 node は 1 件も起動していない。

## 総括

core codec と新系列の raw/物理値分離は成立し、段 3 の producer・coder-spec の取り残しも閉じています。旧 F718・図・walk model の遡及読み替えもありません。

ただし land 前に、B-10 v5 collector と旧 v4 135 cell の束縛混在、M8 の consumer 接続被覆、M11 の actual prereg/patch 突合被覆の 3 件を解消する必要があります。