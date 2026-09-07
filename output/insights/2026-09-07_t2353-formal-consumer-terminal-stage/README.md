# 8c formal consumer の terminal 検査を production の `stage` 形状へ直した — accepted 側は FC07 を通るようになり、rejected 側は producer 不在のまま止まる

**種別:** 読み手 (consumer) の修理。dev-wave `dev-wave-t2353-terminal-stage` (2026-09-07)、[T-2353]。
設計判断は {{D:formal-consumer-terminal-stage-shape}} (fold 後は実番号)。起点は D1665 が別 carry として起票した
terminal 側の食い違いである。

**この wave が直したのは terminal record の読み方だけである。** rejected 側 (abort) の
`candidate_attributable` / `truncated` / `witness_class_sha256s` には production producer が存在せず、
本修理の後も rejected の本番 projection は FC07 で止まる。本番 projection が端から端まで通るようになったとは書かない。
certified 選択集合も変わらない — consumer は全検査通過後も `P6Unavailable` を返す。

## 1. 食い違いと修理

| | 変更前 | 変更後 |
| --- | --- | --- |
| terminal の識別 | root `kind == "commit"` / `"abort"` | `stage == STAGE_COMMIT` / `STAGE_ABORT` (`orchestrator/campaign/model.py` の定数) |
| production の commit terminal | FC07 (読めない) | 受理し、commit 枝の verify 順序検査へ進む |
| 旧形状 (root `kind`) | 受理 | FC07 |
| fixture の terminal | root flat | production 外枠 `{variant, stage, env_tag, ts, payload}` |

producer 側 (`orchestrator/campaign/pipeline.py`、`orchestrator/campaign/wal.py`) は 1 byte も変えていない。
`_wal_field()` の root→payload fallback、FC07 以外の判定式、reason code も変えていない。

## 2. production 形状の出所

- commit: `pipeline.py` が `verify_configs` と `build_attempt_id` を payload へ入れ、`STAGE_COMMIT` で `wal.log()` する。
- abort: `pipeline.py` の 2 経路がいずれも `STAGE_ABORT` + payload `{reason, build_attempt_id, ...}` を書く。
  prebuild abort だけが `error` を持ち、一般 abort は持たない。
- 外枠は `model.py` の `WalRecord` = `{variant, stage, env_tag, ts, payload}`。`STAGE_COMMIT = "commit"`、
  `STAGE_ABORT = "abort"`。outer に `kind` は無い。

rejected 側 witness 系 field の production producer は `orchestrator/campaign/` 全走査で 0 件だった。
`reflux_source_closure.py` の token 表は `wal.abort.payload.witnesses` という**別名**を挙げており、
consumer が読む `witness_class_sha256s` とも一致しない。この限界は {{D:formal-consumer-terminal-stage-shape}} に書いた。

## 3. pin 閉包 — 親の初回閉包は漏れていた

親 brief は「3 対象 file の bytes を pin する `FROZEN_MANIFEST`・golden sha256 は不在」と実測して書いたが、
これは**誤り**だった。段 2 のプランと段 3 の 2 レンズが、fixture 生成器の**出力**を固定する pin を独立に見つけた。

- `orchestrator/tests/reflux_origin_fixture_baseline.json`: ordered WAL projection の byte 長と hash、
  result evidence record の hash を固定する凍結 snapshot。
- `orchestrator/tests/test_reflux_result_evidence.py`: raw record hash、ledger evidence digest、
  outer salted commitment、wrong-domain digest の 4 golden literal。

親の閉包に構造的に欠けていたのは、**生成物の依存グラフ**を辿る一手だった。対象 file 自身への path 参照と
hex literal 検索は行ったが、「この生成関数の戻り値を hash して pin している箇所」は path でも値でも引けない。
この near miss は {{F:generator-output-pin-closure}} に記録した。

段 3 レンズ B は (a) 64 桁 hex literal 走査、(b) 長さ literal 走査、(c) 生成関数の全 caller 追跡、
(d) `orchestrator/tests/` 外の走査、の 4 通りで独立に引き直し、第三の pin は無いと結論した。

pin の新しい値は段 5 の実装子が**変更後の実物から再計算**した。段 2 / 段 3 が提示した値をコピーさせては
いない。親は焦点走で検算した — `test_reflux_origin_fixture_builder.py` は baseline の全 entry を
builder の実物から独立再計算して exact 比較するので、この走行の緑が pin 値の byte 一致を含意する。

## 4. 段 3 / 段 6 の所見と裁定

段 3 (相談 2 レンズ) の must-fix は 2 件で、いずれも採用した。

- pin 2 file の同期を scope に入れる (上記 3 節)。
- 焦点走の閉包に `orchestrator/tests/test_reflux_originless_compatibility.py` を足して 11 file にする。
  これは P3 trial の helper 経由で fixture builder を間接利用する唯一の追加 file だった。

段 6 (敵対レビュー 2 レンズ) の must-fix は 0 件。両レンズとも、新しい負例が手前の判定 (FC05B / FC05C / FC06 /
evidence 解決) で落ちていないこと、新しい正例が commit 枝を通過してから `P6Unavailable` へ至ること、
witness 検査の payload 移動で既存テストが緩んでいないことを、判定順を辿って個別に否定した。

**両段が real と認めた scope 外の所見が 1 件ある。** terminal record の外枠 key 集合・型・重複・root shadow は
依然閉じておらず、production 形状でない flat record も FC07 を通る。ただしこれは**本 wave が新たに広げた
受理集合ではない** — 同じ緩さは修理前の `kind` 版にも同じだけ存在した。D1665 が trigger 側に置いた exact gate と
同等の処置を terminal へ入れるかは、依頼の名指し外なので裁定パッケージへ送った。

## 5. 変異 matrix

事前登録 B-057。probe 走 (全件 SURVIVED 登録で観測 node を集める) → 本走の 2 段で行った。
runner は 11 file の焦点走、`--runner-mode dispatch`。baseline は両走とも PASSED (rc=0)。

| id | 変異 | 期待 | 結果 | kill node 数 |
| --- | --- | --- | --- | --- |
| B-057-M1 | commit 枝の `STAGE_COMMIT` を `STAGE_ABORT` へ | KILLED | KILLED | 1 |
| B-057-M2 | abort 枝の `STAGE_ABORT` を `STAGE_COMMIT` へ | KILLED | KILLED | 15 |
| B-057-M3 | commit 枝を `terminal.get("kind")` へ差し戻し | KILLED | KILLED | 1 |
| B-057-M4 | baseline json の projection hash を 1 文字変更 | KILLED | KILLED | 1 |
| B-057-M5 | abort 枝の `terminal.get("stage")` を `_wal_field(terminal, "stage")` へ | SURVIVED | SURVIVED | 0 |

**probe 段が静的予測の漏れを暴いた。** 段 6 レンズ B は M2 の kill 集合を 14 node と予測したが、実測は 15 node で、
`test_fc07_accepts_production_commit_terminal_shape` が追加で落ちた。`_validate_wal_outcomes()` は paired 全件を
走査するため、accepted の 1 件を検査する test でも他の rejected record が abort 枝を通る。予測だけで
期待 node を登録していたら、本走が完全一致に届かず登録し直しになっていた。

**M5 の生存は設計どおりで、4 節の scope 外所見の実証である。** root だけを読む `terminal.get("stage")` を
root→payload fallback へ緩めても、11 file の焦点走はそれを検出しない。terminal の外枠が pin されていないことを、
静的な指摘でなく実測で示している。

## 6. 実走した検査

- 焦点走 11 file: rc=0、687 passed (160.41 秒、計算ノード dispatch)。
- 新規 2 node の名指し走: rc=0、2 passed。
- 変異 probe 走・本走: いずれも rc=0、baseline PASSED。
- AI provenance 全史監査: rc=0、8396 件、新規違反なし。

段 5 の実装子は sandbox から pytest を起動できず (dispatch rc=16、child 未起動)、
自分の実装を「実装済み・未実走」と正しく申告した。上記の実走はすべて親が行った。
