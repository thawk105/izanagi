# 変異 matrix の記録 (下書き、final の結果で確定する)

## 事前登録 (段 4 裁定 §5、実装前)

14 件 (M0 対照 + 正例 4 + 負例 9)。runner は焦点 5 file
(`test_campaign_lock_codec.py` / `test_artifact_admission.py` / `test_t671_source_binding.py` /
`test_s1_9pair_figure_provenance.py` / `test_s8b_oracle_report.py`)。
`test_layer3_report.py` は前段で M0 が 5 node を落とした drift 核なので runner に入れない
(layer3 の追随は焦点走 f1 の緑が担保)。

## probe 走

| 走 | spec sha256 | attempt | 結果 |
|---|---|---|---|
| probe 1 (`mutation-probe.json`) | `cdd0c849…` | 1 | **rc=2 で中止** — 走行中に親が repo へ insight 下書きを作り、harness が untracked file を検出 (`DW-M05` の「変異中は親の編集を止める」違反)。baseline PASSED、M0 SURVIVED まで観測。実害は再投入のみ |
| probe 2 (`mutation-probe2.json`) | `cdd0c849…` | 2 | 完走。baseline PASSED、M0 SURVIVED、他 13 件で観測 node を取得 (09:33〜10:09) |
| probe 3 (`mutation-probe3.json`) | `0ff8298e…` | 3 | M12b だけの追加 probe。baseline PASSED、1 node を観測 (10:11〜10:14) |

## erratum: M12 の不発と M12b への再照準 (DW-M02)

**M12** (`_RecordedCampaignVerifierEpoch` が現行 96 の scope 対と 85 map の組を許す) は probe 2 で **SURVIVED (0 node)**。
原因は他層の mask — 現行 96 の scope 対は `HistoricalCampaignVerifierEpoch.__post_init__` の歴史 scope 白名単に無く、
歴史 epoch としてそもそも構築できない (`artifact_admission.py:270-288`)。したがって変異箇所へ到達する入力が存在しない。
初回結果は消さず本節に残し、実効 gate (歴史 scope 対と map の対応) へ再照準した **M12b**
(exact-85 の scope 対の下で exact-63 の map を許す) を登録した。probe 3 で 1 node
(`test_t2344_exact85_epoch_requires_matching_scope_and_paths`) を観測している。

## 観測 node 数 (probe 2 / 3)

| # | 変異 | 群 | 観測 node |
|---|---|---|---:|
| M0 | comment だけ (対照) | 対照 | 0 (SURVIVED) |
| M1 | 現行 tuple から `s8b_oracle_report.py` を除去 | 収載追加 | 304 |
| M2 | 現行 tuple の末尾 2 path の宣言順を交換 | 収載追加 | 204 |
| M3 | capture の disk-vs-HEAD 比較を新収載 1 本だけ素通り | 収載追加 | 1 |
| M4 | 歴史 decoder の exact-85 分岐を pre-T733 validator へ | 歴史可読性 | 87 |
| M5 | exact-85 の committed blob 検証を省略 | 歴史可読性 | 85 |
| M6 | 兄弟 validator の wire 比較を superset 許容へ | 未知 grammar | 3 |
| M7 | 歴史 authority 白名単を superset 許容へ | 未知 grammar | 3 |
| M8 | 通常 decoder が exact-85 も一貫して受理 | certified 隔離 | 2 |
| M9 | exact-85 歴史 scope の数値を変更 | 歴史 scope 凍結 | 1 |
| M10 | exact-85 epoch が現行 96 の scope 対を運ぶ | 歴史 scope 凍結 | 1 |
| M11 | 歴史 epoch の計算順を sorted に | 歴史 scope 凍結 | 12 |
| M12b | exact-85 scope の下で exact-63 map を許す | certified 隔離 | 1 |
| M13 | 兄弟 validator が wire 順の map を返す | 未知 grammar | 88 |

**帰属の確認 (DW-M03):** M3 は狙った 1 node (`…rejects_each_emitter_stage_source_drift[…s8b_oracle_report.py]`) だけを落とし、
起動 test (`test_loader_drift_rejected_before_campaign_lock_or_wal_bytes`) は落ちていない — 段 6 レビュー A-1 のとおり、
capture の後段にある `ident.py:283` の live 検証が拒否を維持するためで、起動 test は対照として扱う。
M8 は certified 拒否の 2 node、M9 / M10 / M12b は凍結 scope と scope↔path 対応の各 1 node に正確に当たっている。
`KeyError`・import error・fixture 破壊・live drift だけで落ちる赤は登録していない。

## final 走

(記入済み。spec sha256 `4009f3158222beccc39026b7d1ab99442f02bc3523fd2390d8afee418dd19a76`、
repo HEAD `f605a7ba2`、期待は M0 = SURVIVED / 他 13 件 = KILLED で期待 node 完全一致)

### final 走の結果 (10:15〜10:51 JST、`mutation-final.json`)

spec sha256 `4009f3158222beccc39026b7d1ab99442f02bc3523fd2390d8afee418dd19a76`、repo HEAD `f605a7ba2`、
runner-mode = dispatch (計算ノード)、attempt 1、rc=0。baseline PASSED。

**13 / 13 KILLED (期待 node と完全一致)、M0 対照は SURVIVED。**
M1 304 / M2 204 / M3 1 / M4 87 / M5 85 / M6 3 / M7 3 / M8 2 / M9 1 / M10 1 / M11 12 / M12b 1 / M13 88。

M0 が SURVIVED であることは、runner 内に drift 核 (閉包 member への変異が狙った関門より先に
`contract-loader-drift` を発火させる経路、F923 / F741) が無いことの実測である。
