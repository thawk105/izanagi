## must-fix

**0 件。所有 2 file の実装は GO。** 静的読解で、裁定 §2 に反する実装欠陥は確認できませんでした。fig8b の着地・README・変異実測・受入完了を認定するものではありません。

以下、生成器を [G](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2793-fig8b-cohort2/tools/plotting/plot_b10_static_tail_formal.py)、test を [T](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2793-fig8b-cohort2/orchestrator/tests/test_plot_b10_static_tail_formal.py) と表記します。pytest・test harness は実行していません。

## should

**S1 — 親の統合時に、README の単 cohort 説明へ v2 の再現方法と限界を追記する。author への差し戻し事項ではありません。**

根拠：`tools/plotting/README.md:137–164` は現在も「3 列 × 2 段」「実寸 6 axis」「schema …/v1」のみ。`docs/paper-story/figures/README.md:817–819` は fig8 から fig9 へ続き、fig8b 節はありません。現物にも fig8b の 3 成果物は未着地です。

放置時の影響：再現欄の束縛情報と生成方法が論文図の入口に載らず、依頼された成果物が未完成になります。

是正案：既存 command の逐語

```text
    [--measurement-root PATH] OUT_PREFIX
```

を保持し、その後に次を追記してください。

```text
`--reproduction-cohort 2` を指定すると、主結果 cohort 1 と独立再現 cohort 2 を
縦 2 block（4 行 × 3 列）で併記する。省略時は従来の単 cohort 経路。
描画寸法は 7.2 × 10.6 in、provenance schema は v2。
```

figures README の fig8b 節には次の command を収録します。

```bash
python3 tools/plotting/plot_b10_static_tail_formal.py \
  --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2500-formal \
  docs/paper-story/figures/fig8b_b10_static_tail_cohort2 \
  --reproduction-cohort 2
```

再現欄は次の列構成で、**両 cohort を別行**にしてください。値は入力・provenance・各 results 稿から転記します。

```text
| cohort / 役割 | group id | 集団 verdict | 事前登録 commit / blob SHA-256 | spec SHA-256 | 集団報告 3 file の root 相対 path / SHA-256 | results 稿 | job id |
```

closure の説明は、既存 `figures/README.md:811–812` の逐語を引き継ぎます。

```text
着地後の closure 検査 (`validate_repo_closure`) が見るのは、着地 PNG / PDF の
SHA-256・pin 表・provenance に保存した cells からの artist / caption の再投影であって、
reps からの再計算ではない。
```

さらに、生成された caption 正文、fig8 節末尾の後継図案内、一覧行を追加してください。並行 fig10 wave との統合では、land 直前に main の両 README を再読して一覧・節・command を照合する必要があります。「1 ページに入る」とは記載せず、掲載寸法での PDF 可読性は親の確認事項です。

## nit

**N1 — 未使用の `PRIMARY_COHORT` は削除可能。**

根拠：G:52。生成器内に参照がなく、既定値・分岐は literal `1` を使用しています。

放置時の影響：生成される図・provenance・caption は変わりません。

既存行：

```python
PRIMARY_COHORT = 1
```

修正案：この 1 行を削除。参照側を一般化する変更は不要です。

## 過剰・規模・既存互換

追加された `_draw_block`、caption/builder の切替、v2 closure は裁定 §2 のための局所実装です。新 gate・台帳・汎用 validator・不要な互換層は見つかりません。top-level key 集合の assertion も v2 closure 内に限定されています（G:541–567）。

提示 diff は、**base `b7f970dfa` から現物への diff と完全一致**しました。

| 対象 | 追加／削除 | 純増 | 上限との差 |
|---|---:|---:|---:|
| 生成器 | +193 / −30 | +163 | 約 250 行まで 87 行 |
| test | +257 / −15 | +242 | 約 300 行まで 58 行 |

base と現物の関数ソースを比較し、既存 **25 test の名前・本文・assert はすべて一致**、`_run()` も一致しました。`_caption`・`_artist_series`・`build_provenance` の本文も一致しています。

既定 fixture は `shift=0` となり、従来の値・path・job id・commit・書出し順序を保持します。`_seal` も cohort 1 の同じ 3 path を同じ順序で処理します（T:39–113）。fixture bytes の再生成比較は本レビューでは実行していません。

着地 fig8 の 3 file は読み取りで SHA-256 を確認し、author 報告の値と全件一致しました。

## fixture の実寸と test の独立性

**B4 は充足しています。** 同一 root の別 report dir に、各 cohort 3 workload × 8 点 × 5 反復、DAT 120 行、区間 6 × 3 を構成します（T:50–120）。

| 区別する量 | cohort 2 の差分 | 根拠 |
|---|---|---|
| throughput 平均 | +12,345 tps | T:82–85 |
| throughput CI 幅 | 反復刻みが 1,000 → 3,300、CI 幅も 3.3 倍 | T:82–85 |
| abort 平均・反復変動 | abort・commit の定数項と反復係数を双方変更 | T:80–86 |
| 区間値 | `qhat/qL/qU` を −0.1、対応する `L/U` も変更 | T:102–104 |
| job id | `fixture-0..2` → `fixture-10..12` | T:74 |
| 事前登録 commit | `c` ×40 → `e` ×40 | T:109 |

変更後の同じ reps から JSON の `tps`・`statistics` と DAT を作るため、loader の相互照合と矛盾しません（T:86–98、G:123–172、247–273）。区間判定を fixture の reps から推定し直さないことも、判定は報告からコピーする契約に沿っています。

要求された独立観測は揃っています。

| 検査 | 確認結果・根拠 |
|---|---|
| 描画平均・CI | 生 JSON reps を読み、test 側の `statistics` と固定 t 値で計算。実 line・bar・cap と比較（T:519–548） |
| verdict 負例 | `saturated-in-all-workloads` そのものを投入し、再 seal（T:460–474） |
| `(cohort, role)` 入替 | bundle を反転し、他の射影を整合させて位置検査だけで拒否（T:620–625） |
| `cohorts_pooled=True` | provenance の拒否負例に加え、定数への独立した `is False` assertion（T:454–457、610–619） |
| `fig8b_` | v1 caption 拒否・v2 caption 受理（T:477–485） |
| 見出し侵入・publish ゼロ | 本物の Figure の見出しを panel 内へ移動し、理由と出力ゼロを確認（T:553–582） |
| CLI 実経路 | `main` → `_publish_outputs` を差し替えず、3 成果物・closure・argv を確認（T:589–625） |

入替負例で `_artist_series_v2` を呼ぶのは、無関係な不一致を除いて位置検査を独立させるためです。**描画値の oracle としては使っていません。** loader・artist の双方に同じ誤値を埋めても、生 reps からの描画比較が残ります。

## 例外・公開・consumer

`load_measurements` は既存の `FigureDataError` をそのまま再 raise し、その他の入力例外を包みます（G:176–183）。CLI は生成・公開の例外で rc=2、argparse の不正 choice も終了コード 2 です（G:649–678）。

v2 も同じ公開処理を通ります。layout 検査後に同一 directory の一時 file を作成し、全 bytes を保存してから `os.replace`、一時 file は `finally` で削除します（G:615–646）。**atomic なのは個々の file の置換**であり、3 file 一括の transaction ではありません。通常の rename 失敗時の復元は既存実装を保持しており、v2 固有の退行は見つかりません。

`--reproduction-cohort` は `type=int, choices=(2,), default=None`。省略時の v1 展開 argv は従来の 5 要素、v2 は prefix の後ろに option を追加します（G:653–672）。

静的検索では、所有外 Python caller・consumer test は見つかりませんでした。`tools` / `orchestrator` 内の所有外参照は plotting README でした。

## author 報告と証拠範囲

行数、追加 12 test、既存 25 test 不変、fig8 の hash、親所有の未着地事項は現物と整合しています。

[焦点走ログ](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2793-fig8b-cohort2/focus/focus-post-s5.log:10) は child rc=0、`39 passed, 1 skipped in 8.74s` を記録しています。一方、author の自走 harness 報告は `36 passed, 1 skipped` です。異なる走行なので矛盾とは断定できませんが、提示ログには node 一覧がなく、差分 3 件の内訳や各 node の PASS は独立確認できません。

author 報告の実 root 両 mode 実走・PNG 目視についても、この焦点走ログは直接の裏付けではありません。変異 probe/final、着地 test、掲載寸法での可読性は未了のまま扱うべきです。ログ自身も「受入全走として扱わない」と明記しています。

## 総括

**must-fix 0 件、GO（所有 2 file の実装レビュー）。** should 1 件は親の予定済み統合作業、nit 1 件は未使用定数の削除です。T-2793 全体の完了には、成果物・README の着地と残る実測が必要です。

| 裁定 §2 | 実装状況 | 根拠・残件 |
|---|---|---|
| 1 定数 | 実装済み | G:25–73。v1 固定表現・境界を保持 |
| 2 loader | 実装済み | G:176–280。cohort 別束縛と追加 metadata |
| 3 図番号 | 実装済み | G:283–287。suffix は v2 のみ |
| 4 caption v2 | 実装済み | G:315–346。cohort 別記述・固定表現・非プール・限定 |
| 5 図 v2 | 実装済み | G:440–462。4×3、見出し 2、凡例 1、7.2×10.6 in |
| 6 layout | 実装済み | G:473–504。axes 数と見出し侵入を検査 |
| 7 publish | 実装済み | G:615–646。caption/builder 切替、既存公開処理を共有 |
| 8 provenance / closure v2 | 実装済み | G:526–567。順序・pin・verdict・非プール・射影 |
| 9 CLI | 実装済み | G:649–680。choices・既定経路・argv 位置を保持 |
| 10 test | 実装済み、着地検証は未了 | 実寸・独立 oracle・指定負例あり。既存 25 test 不変。変異実測と親統合後の着地確認は残る |