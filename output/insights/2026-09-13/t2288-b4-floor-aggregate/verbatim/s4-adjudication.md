# 段 4 裁定 — [T-2288] B-4 床値の集約規則

親が段 3 の全所見を real / refuted と採否で裁定し、plan v2 と変異事前登録を確定する。

## lens sol (正しさ境界と保守性)

| # | 判定 | 採否 | 裁定 |
|---|---|---|---|
| 1 | real | 採用 | spec への完全一致は「3 workload × 2 窓」への適合を保証しない。**機械検査は「各 spec がちょうど 2 窓を宣言し、全入力で窓数が一致する」までとする** (D1641 決定 3 の「2 時間窓の全部」の逐語)。n = 62 と 24 時間分離は `floor_pair_driver` も検査しておらず (同 file の window 解析は非重複と `sample_count >= 1` だけ)、**追補で人手の採用責任と明記する**。機械保証と混ぜない |
| 2 | real | 採用 (非保証の明記のみ) | v2 loader の期待 spec 列は成果物内の自己申告に戻る。「source だけ削除」と「期待列も削除して外側 pin も再計算」を区別し、後者は §5 pin の採用責任の境界として非保証欄へ書く。追加の機構は作らない |
| 3 | real | 採用 | campaign ごとの期待 strata は `closed_strata` の当該 `window_id` への射影とする。全窓集合と比較すると正規 producer の 2 窓 summary を拒否する |
| 4 | real | 採用 | 欠測の会計単位を分ける。`dropped` は record 行であり同一 sample key が複数回現れうる。retained sample 集合と dropped sample 集合の非交差・完全分割で検査し、sample 数と record 数を別に照合する |
| 5 | 一部 refuted / 一部 real | 採用 | 「Fraction だから下振れしない」は過大。有限 binary64 の `as_integer_ratio()` は順序を保つので float 比較と大小順は同じである。Fraction の意味は exact 保存と下流への受け渡しであり、**brief の該当表現を訂正する**。比較型は静的確認、丸め禁止は ratio/hex の独立期待値で確かめる |
| 6 | 条件付き real | 採用 (記述のみ) | tie 増加は最大演算ではなく対象集合の取り違えから来る。既存の値域・全件拒否を維持し、「resolver が採用対象への適合まで検証する」とは書かない |
| 7 | real | 採用 | 非保証は入力別に section と items を保存する。`I:699` は section を検査するだけで保持しないので、集約側で明示的に保存する。平坦な一覧は原文の転記であると書く |
| 8 | real | 採用 | 期待側は pin された spec から、実側は summary から抽出する。同一の検証済み spec を両側に使うと空回りする |
| 9 | real | 採用 | 負例が手前の検査で赤になる 10 件超を実装子へ表で渡す。各負例は**どの検査段階で止まったか**を記録する。**「対応 test だけを赤にする」を完了条件から外す** (brief の訂正) |
| 10 | real | 採用 | brief の過大主張 4 点を訂正する (下記「brief の訂正」) |

## lens luna (凍結境界・受理集合・波及)

| # | 判定 | 採否 | 裁定 |
|---|---|---|---|
| 1 | real | 採用 | **既存の v2 負例を v999 へ変更しない。** 既存 test は「v1 本文の schema だけを v2 へ替えると拒否される」ことだけを固定しており、error code も「未対応版」という理由も固定していない。v2 loader が `aggregation` 欠落で拒否すれば既存の入力・期待は 1 文字も変えずに成立する。v999 の負例は**新規関数として追加**する。plan の該当行 (既存 test の変更) は撤回する |
| 2 | real | 採用 | `--summaries` は `--summary` と接頭辞を共有し、`--s`〜`--summar` の既存省略形を曖昧化して受理集合を縮める。**新規オプションは `--aggregate-summary` (反復可)・`--expected-spec`・`--aggregate-output-dir` とする。** `allow_abbrev=False` の追加はさらに縮めるので採らない。旧モードへ新専用引数を混ぜた入力は明示拒否する |
| 3 | real | 採用 | brief の「受入は login node のみ・計算 job 不投入」は runner の場所判定と矛盾する。**「床値測定は実施しない。受入は `tools/run_tests.py` の場所判定に従う」へ訂正する** |
| 4 | real (一部 refuted) | 採用 | 波及に `test_p3_b4_floor_artifact_issuer.py` の private symbol 直接呼出しを加え、`test_p3_b4_material_report.py` は file 単位で確認する。**名前 pin は xdist_group 集合なので issuer test への新規関数追加は pin を壊さない** — この懸念は refuted。plan の配置案は維持 |
| 5 | real | 採用 | sol 所見 2 と同趣旨。修正 P1 (明示 spec pin 列から窓・層・標本の期待閉包を導出) を採る |
| 6 | 限定付き real | 採用 | 凍結範囲の検算は子が実コードから純粋関数を抽出して再計算し、現行の raw / semantic 両 hash と一致させた。**237 行直後で両 pin 不変**。236・238 行直後でも hash は保たれるが 238 は PerfConfig 項目の継続になるので文書構造が誤る。**237 行直後を採る。** 未閉鎖 fence・HTML コメントは H4 を隠して拒否されるので、追補本文に未閉鎖 fence とコメントを置かない |
| 7 | refuted (矛盾の疑義) | 採用 (書き方の確定) | 追補は **D1936 項 7 を根拠とする §5.1 の規範追補**として書く。§11 の「未裁定の案」表記を新しい規範の権威にしない。D1641 決定 3・D1695 の確定値を継承する |

## brief の訂正 (段 3 の反証を採る)

1. 「足りないのは集約規則だけ」→ **規則と、summary が spec の閉包を覆っていることの検査の両方**が要る。
2. 「正規経路が 1 verdict なのは floor 未記入だけ」→ **他の入力が有効で評価器へ到達する場合に限る**。
   組立拒否と pin 拒否は評価器を呼ばずに止まる別経路である。
3. 「spec を pin すれば cell 集合は閉じる」→ **spec の内容については正しいが、summary の被覆と
   §5 の対象集合への適合までは含意しない**。
4. 「Fraction 比較で下振れを防ぐ」→ **順序は float 比較と同じ**。Fraction の意味は exact 保存である。
5. 「変異は対応 test だけを赤にする」→ 共有検査の変異は複数 test を落とす。**狙った負例が狙った
   検査段階で止まったことを記録する**へ変える。
6. 「受入は login node のみ」→ **受入は `tools/run_tests.py` の場所判定に従う**。
7. 「実測は本 wave では不可能」→ **本 wave は規則と配線に限定し、較正取得・測定は scope 外**とする
   (D1936 項 7 の理由文が「取得には項 6 の停止原因解消が先に要る」と述べているとおり)。
   将来も不可能という主張はしない。
8. 「凍結 spec の実体 0 件」は親が `git grep -ln "floor-pair-spec"` で確認した結果 (hit は実装と
   insights だけ) であり、repo 全体の不存在証明としては schema 文字列検索の範囲に限る。

## plan v2 (確定)

段 2 plan を、上の裁定で次のとおり修正して採用する。

- 既存 test の期待値変更 (v2 → v999) は**撤回**。v999 は新規関数で足す。
- CLI の新規オプションは `--aggregate-summary` / `--expected-spec` / `--aggregate-output-dir`。
- campaign ごとの期待 strata は `closed_strata` の `window_id` 射影。
- 欠測は sample 集合と record 行を分けて会計する。
- 各 spec の窓数はちょうど 2、全入力で一致。n = 62 と 24 時間分離は機械検査しない (人手責任)。
- 非保証は入力別に section と items を保存する。
- 期待側は pin された spec、実側は summary から抽出する。
- それ以外 (v1 維持、集約 v2 追加、Fraction 最大、全件拒否、create-only、出所保存、
  `_publish_create_only` 再利用、命名、file:line 変更計画、波及) は plan のまま採用。

## 変異事前登録 (DW-M01 / DW-M08)

実装前に登録する。位置の逐語 anchor は実装完了後に `DW-M07` に従って再検証する。
各変異は「赤理由が一つに絞れること」を実装後に確認し、絞れないものは登録せず実効 gate へ再照準する。

| ID | 変異対象 (述語) | 期待 |
|---|---|---|
| M1 | 集約値の `max` を `min` へ替える | KILLED。保守側が反転する |
| M2 | 期待 spec 列の exact 一致検査を、実入力から導出した列との比較へ替える (循環化) | KILLED。閉包検査が恒真になる |
| M3 | 窓数 2 の要求を「1 以上」へ緩める | KILLED |
| M4 | campaign ごとの期待 strata 射影を全窓集合比較へ替える | KILLED。正規 2 窓入力を誤って拒否する向き |
| M5 | retained と dropped の非交差・完全分割の検査を件数比較だけへ弱める | KILLED |
| M6 | 入力 1 件が不正なとき、その 1 件だけ除外して続行する | KILLED |
| M7 | 非最大入力の出所・非保証の保存を落とす | KILLED |
| M8 | v2 loader の `aggregation` 必須欄検査を外す | KILLED。既存の v2 拒否 test も赤になる (共有 gate なので複数 node を期待集合に入れる) |
| M9 | `floor >= 1` の拒否を clamp へ替える | KILLED |
| M10 | create-only publish を上書き許容へ替える | KILLED |

正例 (通る例) を 1 つ登録する。**3 spec・各 2 窓・全セル被覆・許容内の欠測を持つ合成入力が、
集約成果物として発行され、既存 resolver 経由で材料レポートまで届くこと。** この正例が赤になる
変異は登録しない (過剰拒否の検出は M4 が担う)。

## scope 外 (実装しない)

床値の実測、rr5 / rr95 較正の取得、§5 値セルへの記入、本書の発効、workload 一致要求の撤去、
汎用 multi-calibration schema、別の集約基盤・台帳・manifest、n = 62 と 24 時間分離の機械検査、
仮想リスク向けの gate・検査・一般化。
