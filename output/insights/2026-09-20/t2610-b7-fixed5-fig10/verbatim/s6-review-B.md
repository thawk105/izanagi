## 所見

**B-1 — should｜生成器 `validate_repo_closure` / `validate_external_sources`、着地 test：着地標本と raw の内容を結ぶ照合がない**

[生成器の closure](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/tools/plotting/plot_b7_fixed5_regression.py:432) は provenance 自身の `samples_tps` から統計量を再計算します。外部検査は raw の SHA-256 を照合しますが、その raw の標本と provenance の標本は比較しません。

読み取り専用のメモリ内検証で、実装の関数定義を変更せず、次を確認しました。

- `rr5-stock` の第1標本を `2328992 → 2328993` に変更。
- 平均・標準偏差・CI・`artist_series` を変更後の標本に合わせる。
- median・effect・caption・画像・raw・各画像/raw の hash は変更しない。
- **repo closure と external sources の両検査が通る。**

既存の実データ test は「raw → 稿」を照合しますが、着地 provenance を比較対象にしていません。着地 test に、既存の `_document_values()` が抽出する30標本と provenance の一致を追加すると、durable root 不在でもこの抜けを閉じられます。

ただし、provenance ファイルだけを変更すれば、現在の README の SHA-256 検査は拒否します。本所見はその検査まで無条件に通るという指摘ではありません。現在の成果物は独立照合で正しく、親 plan が明示した closure の範囲にも沿うため、非阻害と判断します。

**DW-G05:** 再着地時に README の hash も更新されると、raw と異なる標本・平均・CI を持つ provenance を自己整合だけで受理し得ます。

**B-2 — should｜`CAPTION_SCOPE`、provenance `authority_scope`、figures README「入力」：判定の出所の記載が矛盾**

`CAPTION_SCOPE` は稿を **“not … the floor judgment”** と位置づけています。一方、実装・README・裁定は `RECORDED_JUDGMENT` を稿 §2.1 の転記としています。

fig9 は classification を result JSON から読むため、この除外が成立します。fig10 は稿が記録判定の出所なので、そのまま踏襲できません。「測定値・effect の一次権威ではないが、記録判定と限定・条件の言い方の出所」と区別するのが正確です。

**DW-G05:** 図の値は変わりませんが、provenance が判定の実際の出所を否定した状態で残ります。

**B-3 — should｜判定・correctness の negative test：重要な境界の直接検査が不足**

実装には strict `<` と、性能側 `trace_enabled is False`・正しさ側 `trace_enabled is True` の両方があります。ただし、現在の test は以下を直接区別しません。

- `effect == -floor` が退行なしになる境界。
- correctness 記録だけを `trace_enabled=False` にした拒否。

現行の judgment 不一致テストは十分離れた値を使うため、`< → <=` の変異を検出できません。hash を再封印した実寸 fixture で、それぞれ独立した負例・境界例を追加する余地があります。

**DW-G05:** 現在の固定値で成果物は変わりませんが、等号の判定変更や trace-disabled verify の誤受理を回帰検査が見逃し得ます。

その他の検査については、次の評価です。

| 対象 | 静的評価 |
|---|---|
| `_authority_data` | schema・identity・順序・条件・token・correctness・床・判定の検査に恒真な式は見当たらない。通常入力では hash が先に拒否するが、意味検査の test は再封印して到達する |
| `load_evidence` | raw hash、性能 trace-disabled、verify trace-enabled、標本数、median、effect を実際に検査。例外を成功へ変換する経路は見当たらない |
| `validate_repo_closure` | authority・派生値・画像 hash・caption は照合する。標本自体の独立した束縛は B-1 の範囲 |
| `validate_external_sources` | raw 集合と bytes の照合は実効的。標本内容との連結はしない |
| `check_figure_layout` | 本物の renderer による重なり・逸脱検査。失敗後に保存を続ける経路はない |
| fixture / test | 3 workload × 2 cell × 5標本、上段3＋下段1 axes。描画・layout・CLI は実体を通す。着地欠落 test の `REPO` 差し替えも検査関数を迂回しない |

`RECORDED_JUDGMENT` を出力し、計算結果は一致検査だけに使う構成は、提示された D2162 の解釈に収まります。定数と述語を一緒に変えても、`test_pins_floors_effects_and_judgments_match_results_document` が稿の判定列と定数を独立に照合するため、現状では自由な判定変更を通しません。

## 値の照合結果

生成器の集約結果を流用せず、標準ライブラリで raw・certification・床値 JSON・稿・provenance を照合しました。

| workload | stock median | fixed5 median | effect 全桁 | floor CV 全桁 | 判定 | 結果 |
|---|---:|---:|---:|---:|---|---|
| rr5 | 2,354,846 | 3,953,710 | 0.6789675418265144 | 0.009536033056996148 | 退行なし | 一致 |
| rr50 | 3,832,768 | 4,318,443 | 0.12671651401806727 | 0.00725042525457718 | 退行なし | 一致 |
| rr95 | 10,334,945 | 9,158,963 | -0.11378696258180376 | 0.0022283754708938273 | 退行 | 一致 |

rr95 の2 cell は durable raw を直接読みました。

| cell | raw の5標本（記録順） | 稿・provenance |
|---|---|---|
| rr95-stock | 10680928, 10171152, 10334445, 10334945, 10351729 | 一致 |
| rr95-fixed5 | 9282678, 9137295, 9158963, 9119021, 9190899 | 一致 |

| 照合項目 | 結果 |
|---|---|
| 全30標本、6 median、平均、標本標準偏差、t95 CI | 一致 |
| raw 6本の SHA-256 と manifest / `external_inputs` | 一致 |
| 床値3本の session 値から再計算した CV | 一致 |
| caption の effect % | `+67.8968% / +12.6717% / -11.3787%`、一致 |
| caption の −floor % | `-0.9536% / -0.7250% / -0.2228%`、一致 |
| request | `10807.nqsv / 10808.nqsv / 10809.nqsv`、一致 |
| pin / source commit | `511c953` / `c18a80967…`、一致 |
| 条件 | 48 threads、1,000,000 records、Zipf 0.9、rmw 0、max_ope 10、3秒、5反復、silo。一致 |
| outer / a4 status | `reject / open`、一致 |
| tracked 入力6本＋caption_source の hash | 全件一致 |
| README 一覧行・fig10 節の値と判定 | 一致 |
| README caption と provenance caption | 逐語一致 |

着地 hash も現物と一致しました。provenance の `outputs` は PNG/PDF の2件で、自身の hash は README が保持しています。

| 成果物 | SHA-256 | 結果 |
|---|---|---|
| PNG | `583e94f642a9892a66791b9e0dff5ed37bd7babedf3f4da644b1245af15d1d5d` | README・outputs・現物が一致 |
| PDF | `3fb9d1cab495c717a32fb13bb1061ea77e4c619cb56f9d6738d00908a471b764` | README・outputs・現物が一致 |
| provenance | `1a945474ad64ffed9f44f93d086966ecb19969ba75bf6945a3a96c0834b88480` | README・現物が一致 |

caption は certified を性能認証と呼ばず、anomaly 0 を主張していません。既存材料との比較・プール、同一 binary、文字どおりの同時実行も主張していません。稿への provenance hash の逆書込みもなく、F36 の方向は守られています。

## 変異事前登録への所見

**13件は positive 1件＋negative 12件です。実走結果ではなく静的評価です。**

| id | 単一理由性・期待 node の評価 |
|---|---|
| m0 | docstring 追加は意味を変えない。generator hash を現行 source の pin としない設計とも整合 |
| m1 | 末尾改行による hash drift は JSON 内容を変えない。指定3 node は hash 検査の除去だけで拒否を失う構成 |
| m2 | raw 末尾改行だけなので、raw hash 検査以外の意味検査を通る |
| m3 | 両 arm の標本を同率変更し effect 比を維持。median 検査の除去だけを狙えている |
| m4 | rr5 effect を `.4` に変更しても退行なしは維持され、先行 judgment 検査に遮られない |
| m5 | rr95 floor を `.2` に変更。床条件は有効で、median/effect は変わらない |
| m6 | certification の correctness status だけを変更。別の raw correctness 検査は変更入力を重複拒否しない |
| m7 | 性能側 trace フラグだけを変更。build 証拠は有効なまま |
| m8 | 全 adopted token と対応 raw を揃えて変更。token 相互一致・raw identity が代替拒否しない |
| m9 | Figure 上の2テキストを同位置に追加。指定 overlap 分岐を狙える。図外逸脱等を同時に導入していない |
| m10 | 本物の着地 test を呼び、Skip を明示的に失敗へ変換。期待 node は適切 |
| m11 | caption の該当文を削除すれば固定 literal の照合が失敗する |
| m12 | floor genome のみ変更し再封印。床条件・判定は維持 |

**指定された変異について、単一理由性に疑いのある id は見当たりません。** 各検査位置も関数・述語で一意に指定できます。ただし m10 は現在の全件存在 assert に「全欠落時の skip 分岐」を挿入する変異なので、実際の spec でその分岐を正確に表現する必要があります。

B-1 の着地標本の照合、B-3 の strict 等号境界・verify trace フラグは、この事前登録 matrix の検出範囲外です。

## 親 brief / 裁定への所見

- **実測値・pin の前提は一致しています。** raw 6本、各5標本、median・effect・床値・request・source commit に不一致はありません。
- **plan の `CAPTION_SCOPE` は B-2 の矛盾を含みます。** fig9 と同型なのは「記録分類と述語を照合する方式」であり、記録分類の出所まで同じではありません。
- **repo closure の前提は B-1 の限界を持ちます。** 「provenance の標本から再計算する」だけでは、標本自体を外部 raw に再束縛したことにはなりません。
- **raw に anomaly 件数がないという裁定は正しいです。** rr95 の correctness 記録にも anomaly field はありません。稿 §2.4 は raw に anomaly 0 が記録されているように読めますが、図ではその主張を引き継いでいません。凍結稿を本 wave で変更する必要はありません。
- F36、F649、F820、作図規約 §10 の適用趣旨に明らかな取り違えは見当たりません。D/F 番号の原台帳は射影対象外なので、番号自体の独立した確認まではしていません。
- author 報告の未着地1件の赤は当時の記録です。今回の着地済み状態の失敗としては扱いません。今回 pytest・変異 matrix は実行していません。

## 総括

must-fix は **0件**、should は **3件**です。
現在の標本・統計量・判定・caption・README・着地 hash は一次資料と一致しています。
**GO**：現在の固定成果物は採用可能です。
着地標本の独立照合、判定の authority_scope、境界テストは補強を推奨します。
pytest・変異 matrix の緑は本レビューでは認定していません。