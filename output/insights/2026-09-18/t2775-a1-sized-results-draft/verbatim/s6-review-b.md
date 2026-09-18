## レビュー範囲と結論

**NO-GO。must-fix 2 件です。** 生成器の現行 bytes による過剰拒否と、着地画像の参照先を固定しない closure を修正してください。

以下、`G` は [生成器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft/tools/plotting/plot_a1_sized_paired.py)、`T` は [対応テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft/orchestrator/tests/test_plot_a1_sized_paired.py) を指します。行番号は現在の現物です。

指定資料を読み、統合 patch の追加内容が G/T と完全一致すること、公開 leaf の SHA-256、試作 provenance の主要統計・30 対との対応を確認しました。pytest・変異実走・書き込みはしていません。親ログは **55 passed / 1 skipped** ですが、現在は README に fig9 が掲載済みで着地 3 ファイルが未存在なので、T:426 の skip 条件は成立しません。最終生成前として扱い、過去ログを現在の着地 closure の成功証拠には数えません。

## must-fix

**MF1 — `generator.sha256` を現行 source の pin にしている。**

- **根拠:** G:397–398。figures/README.md:879–880 の「生成時点の記録であり、現行 source を縛る pin ではない」と直接矛盾します。fig8 の生成器:443–444 は path のみを照合しています。
- **影響:** コメントだけの変更でも、値・画像・稿が不変の凍結図を closure が拒否します。規律 7 に反する受理集合の縮小です。
- **是正案:** 生成時 SHA-256 の記録は残し、現在のファイルとの比較だけ削除します。

```diff
-        _require(provenance["generator"] == {"path": GENERATOR_PATH, "sha256": _sha256(root / GENERATOR_PATH)},
-                 "generator closure mismatch")
+        _require(provenance["generator"]["path"] == GENERATOR_PATH,
+                 "generator path mismatch")
```

T の fixture 内の生成器をコメントだけ変更しても、既存 provenance の closure が通る正例を追加してください。親の疑い 8a は正しいです。

**MF2 — 「着地した fig9」の画像を検査する保証がない。**

- **根拠:** T:423–430 は着地 3 ファイルの存在を確認しますが、G:402–408 が hash を読む対象は provenance の任意の `outputs[].path` です。両者の同一性を照合していません。
- **影響:** 同じ basename の試作図を別ディレクトリに残し、provenance がそちらを参照していると、着地 PNG/PDF の bytes が異なっても closure が受理し得ます。「着地 PNG/PDF の SHA-256 を守る」という README の保証が成立しません。
- **是正案:** 汎用 CLI の出力先自由度は維持し、着地テストで対象を固定します。

```python
assert [row["path"] for row in prov["outputs"]] == [
    path.relative_to(REPO).as_posix() for path in paths[:2]
]
```

別ディレクトリの同名画像へ参照を差し替えた負例を、この着地対応検査に追加してください。

## should

**S1 — README の provenance SHA-256 が検査されていない。**

- **根拠:** figures/README.md:922–923 が provenance hash の正本ですが、T:425–431 は caption の包含しか検査しません。G:391–410 も README を読みません。
- **影響:** 最終生成後に古い provenance hash を README に残しても緑になります。稿が provenance hash を持たない設計で、唯一の正本にある参照値の誤りを検出できません。
- **是正案:** fig9 節から provenance hash を一意に抽出し、`_hash(paths[2])` と照合してください。既存の着地テストへの局所追加で十分です。placeholder の現状自体は所見にしていません。

**S2 — 稿 §2.1 の「区間」列が対応検査から抜けている。**

- **根拠:** T:416–419 は mean/h/B/baseline mean/sd/planned sigma/分類を検査しますが、`columns[5]` の区間を読みません。
- **影響:** 最終生成前に稿の区間だけを誤記しても、誤記した稿の SHA-256 を provenance に取り込んだ状態で全対応検査を通せます。稿 §2.6 の「両者の同一性は test に委ねる」範囲に穴があります。
- **是正案:** `json.loads(columns[5])` の両端を `c["interval"]` と既存許容誤差で照合してください。稿全体の汎用パーサーは不要です。

## nit

- **負例の未整備:** 下表の「なし」は実装欠落ではありません。現行 CLI は固定 pin でも拒否するため、これだけで現成果物の誤りとはしません。補うなら既存 fixture の局所変更と再 seal を使い、検証 framework は追加しないでください。
- **要求外の小さな検査:** G:173 の sigma の文字列型限定、G:175 の正値、G:191 の正 throughput、G:249–250 の限定文ちょうど 5 件は裁定の列挙より厳密です。ただし固定入力専用なので現行受理集合をさらに狭めません。削除必須ではありません。
- **散文の重複:** 稿 §0.3・§3・caption・README に限定句が重複しますが、独立して引用される各成果物に必要です。削除対象とは判定しません。
- **README の表現:** figures/README.md:886 の「95% CI ではない（caption にそう書く）」に対し、caption は k と分位点を明示するものの、その否定文はありません。逐語で「caption に登録済みの k と分位点を明記する」へ直せば十分です。

## 拒否条件 → 実装 → 負例 → 変異

test node はすべて `orchestrator/tests/test_plot_a1_sized_paired.py::` 配下です。「なし」は専用の意味的負例がないことを示します。

| 条件 | G の行 | 負例 test node | 変異 |
|---|---:|---|---|
| 固定 pin／注入 hash 一致 | 133–138 | `test_leaf_hash_drift_is_rejected`、`test_pinned_hashes_are_used_when_no_override` | M6 |
| `.complete.json` schema・map のキー・現物 hash | 144–147 | なし。M6 は completion の空白変更であり map 検査を踏まない | — |
| result/receipt schema・study | 148–150 | なし | — |
| formal=false | 108、151–152 | `test_formal_true_is_rejected`（result のみ） | M1 |
| promotion_prohibited=true | 109、151–152 | `test_promotion_prohibited_false_is_rejected`（result のみ） | M2 |
| policy result_authority | 153 | なし | — |
| complete／terminal／measurement_error | 154–155 | なし | — |
| pairing design／contrast | 156、164–165、202–204 | なし | — |
| workload・policy・job の順序と件数 | 159–163 | なし | — |
| workload valid/errors/terminal status | 178–179 | なし | — |
| reps=30、n=30、df=29 | 170–172、185–187、200–201 | なし | — |
| arm 名・role・flags・protocol | 176–183 | なし | — |
| rounds=1／attempt=1／unstable=false／arm valid/errors | 185–188 | なし | — |
| genome | 189 | なし | — |
| raw_tps 件数・有限正値 | 190–191 | なし | — |
| pairs 30 件・index 0..29 | 207–210 | なし | — |
| signed_difference = variant − baseline | 211–213 | `test_pair_difference_mismatch_is_rejected` | M5 |
| pairs[i] = raw_tps[i] | 214–215 | なし。M5 は両者を同時変更してここを通す | — |
| mean/variance/sd/h/baseline mean/B 再計算照合 | 217–226 | `test_statistics_mismatch_is_rejected`（mean のみ） | M3 |
| 区間の長さ・両端再計算照合 | 227–231 | なし | — |
| 分類の述語検算 | 232–234 | `test_classification_mismatch_is_rejected` | M4 |
| variance_plan_breach の述語一致 | 235 | なし | — |
| variance_plan_breach=true の拒否 | 236 | `test_variance_plan_breach_true_is_rejected` | — |
| correctness certified=[True] | 193–194 | `test_uncertified_arm_is_rejected` | M9 |
| correctness legacy／verify frame 1 件 | 195–197 | なし | — |
| result policy hash = 現 policy | 157 | `test_policy_hash_mismatch_is_rejected` | M10 |
| receipt policy hash = result policy hash | 158 | なし。M10 は両方を同じ偽値にする | — |
| policy k/sigma と statistics 一致 | 173–175、205–206 | なし。variance 負例では整合させている | — |
| caption_source 実在 | 140–141、128–129 | `test_provenance_binds_caption_source`（削除） | M12 は記録欠落を対象 |
| caption_source 現 SHA-256 | 140–141、395、399–401 | `test_provenance_binds_caption_source`（本文変更） | — |
| 保存前 layout 拒否 | 342–371、417 | `test_bbox_overlap_is_a_failure`、`test_layout_failure_publishes_nothing` | M7 |
| caption の固定 lane | 276 | `test_caption_contains_fixed_literals_and_lane` | M8 |
| artist と cells の対応 | 289–330、409 | `test_artist_series_equal_provenance_cells_and_leaf_statistics` | M11 |
| provenance の caption_source 記録 | 140–141、379 | `test_provenance_binds_caption_source` | M12 |

裁定 §2.2 に列挙された拒否条件について、**実装そのものの欠落は見つかりませんでした**。負例の充足とは分けて評価しています。

## M0〜M12 の単一理由性

以下は静的判定であり、KILLED の実測報告ではありません。author の対象 anchor は各 1 箇所であることを確認しました。

| ID | 判定 | 根拠 |
|---|---|---|
| M0 | baseline の実走が必要 | 親ログはあるが、最終着地後の状態とは異なる |
| M1 | 単一理由 | result の formal だけ変更し再 seal。receipt/policy の正常値は result を代替検査しない |
| M2 | 単一理由 | M1 と同様 |
| M3 | 単一理由 | 記録 mean だけ変更。区間・分類は pairs 由来の再計算値を見るため、照合ループ除去後の拒否層にならない |
| M4 | 単一理由 | classification だけ変更。terminal_result.classification は別途照合されない |
| M5 | 単一理由 | variant の raw と pair を同時変更。差・baseline・統計を維持するため、差の恒等式だけが不整合 |
| M6 | 単一理由 | completion の末尾空白だけ変更。JSON 内容と内側 map は正常 |
| M7 | 単一理由 | 実 Figure に重なる Text を追加。no-op 化後は拒否されない |
| M8 | 単一理由 | literal の実際の欠落を検査する。診断文だけの差ではない |
| M9 | 単一理由 | certified のみ False。legacy と frame 件数は正常 |
| M10 | 単一理由 | result/receipt を同じ偽 hash にして相互比較を通す。現 policy との比較だけが拒否 |
| M11 | 単一理由 | 非対称 fixture で mean≠median。cells と実 Line2D の比較が検出する |
| M12 | 単一理由 | append 削除で caption_source 行が実際に消え、T:355 の期待行比較が落ちる |

**期待失敗 node の完全集合には注意が必要です。** M7 は `test_layout_failure_publishes_nothing` も失敗します。最終着地後は M8/M11/M12 が着地 closure/caption の test も落とす可能性があります。author の表は「殺す代表 node」としては妥当ですが、そのまま harness の完全な期待集合にはできません。DW-M04 の注入実在・累積置換確認と最終状態での期待集合確定は、まだ実走証拠がありません。

## 入力・表示値の対応と許容誤差

**fixture 上の対応検査は実効性があります。**

- T:53–77 は fixture の raw 配列から統計を構成し、生成器の統計関数を呼びません。T:174 は別の `statistics.stdev` でも検算します。
- T:187 の `fig._a1_artist_series == prov["artist_series"]` 単独なら共通実装の自己比較ですが、T:196–206 が **実 Line2D の mean/zero/floor/pairs と、実 patch の帯の上下端**を読んでいます。
- `_provenance` の画像 bytes は合成ですが、この test で検査する Figure は本物です。CLI test では PNG/PDF も実際に生成します。両層 stub にはなっていません。
- cells の統計は leaf と比較され、pairs と raw の一致は `load_leaf` が確認します。ただし T:180 自体には cells の各 pair と leaf pair の独立した直接比較はありません。

G:102–104 の許容誤差は裁定どおりです。平均約 159 万 tps なら相対許容は約 **0.0016 tps** で、caption の丸めや分類を曖昧にする幅ではありません。

`validate_repo_closure` は画像内の artist を再読する検査ではありません。**生成時の実 artist 検査＋画像 hash 束縛**で対応を守る構造であり、その後半に MF2 の穴があります。

G:399–401 は「leaf 全体」の比較ではなく、`load_leaf` が返す **射影済みデータ全体**との比較です。固定 leaf の cells・limitations と凍結稿の hash を照合する目的は妥当です。ただし将来、同じ v1 に派生 field を追加すると旧 provenance を拒否します。v1 の射影を維持し、形式変更は別 schema にする運用が必要です。

## 図・言い方・docs・波及

**図の形と P1 は妥当です。** 3 panel、pair index、30 open marker、mean 線、帯、±B 破線、0 線、workload-local y を実装しています。試作 provenance と G:313–316 から算出した帯の高さは、各 plot 高さの約 **2.35% / 7.51% / 5.34%**。200 dpi 保存時の plot 高さ約456 pxに対して約 **11 / 34 / 24 px** で、床線との位置も離れています。尺度によって帯と床が潰れる兆候はありません。PNG/PDF の目視評価はしていません。

FIGURE_CONVENTIONS §2 の一般則である95% CIに代えて登録済み区間を使うことは、今回の裁定と推定対象に適合します。§3/5/6/9/10 も、指定された対差図として満たしています。campaign id や variant hash は図中に出ません。`rr5`・`fixed10` 等は裁定指定の表示ですが、一般読者向けの略語展開は薄く、改善するなら caption で read ratio と固定待ち時間を説明する程度で十分です。

**規律2の言い方は適合しています。** `FIXED_LANE`・`FIXED_SCOPE`・`not a performance certification`・workload-local の警告は逐語で存在します。禁止する肯定的主張や improvement/regression は caption にありません。稿 §1.1 の improvement/regression は事前登録の用語を引用して区別する箇所です。mean/h/B/job/host/分類/符号は data から組み立て、図番号も prefix 由来です。

**F36 の順序は正しいです。** 稿確定 → provenance が稿を hash 束縛 → README が provenance hash を持つ順序には循環がありません。稿を変更すると G:399–401 が拒否し、T:359–362 に変更・削除の負例があります。残る問題は S1 の README 参照値の未検査です。

**P2〜P5 を覆す根拠はありません。** results 表と stale 注記は役割が違い、分類述語の実装参照も producer と一致します。ファイル名と単独稿の単位も適切です。段2・3省略そのものを成果物の欠陥とはしません。

path・CLI・schema・入力の記述は概ね一致します。稿 §2.6 は results 系列の転記規則と F36 の例外を明記しています。明確な docs 矛盾は MF1 と nit の caption 説明です。

perf predicate は指定 test の関数・定数だけを抽出して適用し、**False** を確認しました。新 test に parametrize はなく、ASCII id の問題はありません。自走 `_run()` も存在します。ただし `test_plain_runner_coverage` や `check_docs.py` 全体は実行しておらず、その全体成功までは保証しません。指定 docs の新規部分に禁止された file:line 参照は見つかりませんでした。

## 総括

**NO-GO。** MF1 の現行 generator hash 比較を削除し、MF2 の着地画像パス対応を固定してください。S1 の README provenance hash と S2 の稿の区間列も、局所的な検査追加で閉じられます。

統計再計算・分類検算・実 artist の対応検査・限定句・F36 の生成順序は妥当です。修正後、最終着地状態で焦点 test と変異 matrix を確認する必要があります。