## 所見

**B-1 — must-fix：測定条件の必須項目が図・caption から欠落**

対象：[生成器 `_authority_data`／`_caption`／`make_figure`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/plot_b10_waiting_grid_forest.py:262)、figures README「キャプション正文」、brief／plan v2 の条件列挙。

[作図規約 §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/FIGURE_CONVENTIONS.md:65) は「測定条件 (スレッド数・レコード数・skew・env) は図のサブタイトルかキャプションに必ず出す」と定めています。しかし英文の `Conditions: Pegasus compute nodes, 48 threads, silo, ...`、日本語正文、PNG のいずれにも、**データベース件数 1,000,000 と Zipf skew 0.9 がありません**。provenance の `measurement_conditions` にもありません。

値は report の `calibration.records` と `preregistration.spec.workloads[].ycsb_zipf_skew` に存在します。これらを条件として転記し、caption・成果物・README の SHA を更新する局所修正で足ります。brief／plan v2 の条件列挙にも同じ漏れがあります。

**DW-G05：放置すると、論文図と caption が必須の動作点を欠いたまま着地し、どの件数・偏りで得た結果かを図から特定できません。**

**B-2 — should：等価域ちょうどの境界を fixture が踏んでいない**

対象：[生成器 `_relation`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/plot_b10_waiting_grid_forest.py:134)、test `_fixture`。

実装は両端を含む `inside`、厳密に帯の外なら `outside`、残りを `overlaps` とします。現 report の36 cellとは一致しますが、fixture に ±0.03 ちょうどの端点はなく、等号の向きは検査されません。射影資料の report にも境界上の実例がないため、**report producer の境界規則まで同じとは、この資料だけでは断定できません**。

境界上の区間と、外側から境界に接する区間を明示した小さい検査が適切です。

**DW-G05：現行の固定 report の図は変わりませんが、`>=`／`<=` の退行を受理してしまうテスト集合が残ります。**

**B-3 — should：report Markdown の照合範囲を明確にする**

対象：[生成器 `_authority_data`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/plot_b10_waiting_grid_forest.py:248)、figures README「入力」の「report .md の Holm 3 行・cell effects 36 行との照合」。

Holm 3 行は値を照合しますが、cell effects は**行数が36であることだけ**を検査しています。README は「Holm 3 行の値と cell effects の36行という構造を照合」とすると実装と正確に対応します。plan v2 自体は行数検査を指定しており、実装漏れではありません。

**DW-G05：現行 bytes は SHA pin で守られ図の値は変わりませんが、README が意味検査の範囲を実際より広く読ませます。**

指定された言い方の逸脱 (a)〜(h) は認めませんでした。英文・日本語正文・一覧表・節本文・図中の文言は、等価性成立、個別有意差、右 tail との合成、機序、一般化、性能認証・採用、研究の成否、検出力、事前登録 §8 の禁止4項を主張していません。PNG も確認しました。

## 値の写しの照合結果

読み取り専用の JSON・算術・正規表現・SHA 照合を行いました。pytest、生成器の実走、変異実走は行っていません。

| 項目 | 結果 |
|---|---|
| write-heavy | 一致：raw p `6702/2^18 = 0.02556610107421875`、Holm p 同値 |
| balanced | 一致：raw p `70/2^18 = 0.00026702880859375`、Holm p `0.0005340576171875` |
| read-heavy | 一致：raw p `2/2^18 = 7.62939453125e-06`、Holm p `2.288818359375e-05` |
| 族の状態 | 一致：3族とも `testable`／`different`、各18対 |
| 対相対効果の和 | 一致：順に `+0.11202543669460518`、`+0.13167898485090257`、`+0.087727340019642996` |
| 区間の集計 | 一致：inside 32、overlaps 4、outside 0、indeterminate 0、estimable 36 |
| 境界を跨ぐ4 cell | 一致：write-heavy μ2・μ25、balanced μ2・μ25 |
| 負の点推定 | 一致：write-heavy μ5 の1件。効果 −0.009738229292106326、区間は0を含む |
| 区間下限が正 | 一致：write-heavy μ50・μ100、balanced μ10・μ50、read-heavy μ2・μ25・μ50・μ100 の8件 |
| 条件 | 掲載値は一致：48 threads、silo、3 workload、μ6点、5 rep × 3 block、pin `511c953`。件数・skew は B-1 の欠落 |
| identity | 一致：request `978195.nqsv`、prereg commit `77b33e37d`、source commit `2a338449b` |
| caption・SHA | 英文 caption の README 逐語収録、tracked入力3件・図出力2件の SHA、README の着地 SHA 3行がすべて一致 |

和の `:+.17g` は浮動小数値の表示です。稿の小数第5位までの `+0.11203`／`+0.13168`／`+0.08773`、panel の小数第4位までの表示と丸めが整合します。これは**18対の無次元相対効果の和**であり、平均改善率でも新しい精度の主張でもありません。数値不一致とは扱いません。

「判定を作らない」について：

- 54対差は順序も含めて再計算と完全一致。18 cell の効果・区間も完全一致しました。図 provenance は report の family／cell の既存 field をそのまま保持しています。
- report に直接ない追加値は、`sum_of_differences`、`direction`、`raw_p_numerator_2pow18`、`block_effects`、summary、負の点推定数・正の区間下限数です。いずれも既存値の和・符号・分数表示・対応づけ・集計で、稿 §2.2〜§2.4 の転記の検算と同じ地位です。
- Holm・区間・等価域関係・曝露は一致を要求する検査です。raw p の全列挙をやり直したとは主張していません。

閉包と fixture について：

- `validate_repo_closure` は外部受領証を読まず、tracked入力から数値・caption・artist・summary・report を再構成して比較します。caption 1字、artist／cells 1値、summary、epoch の単独 drift はコード上拒否されます。
- ただし「全 key を独立に再導出」は厳密には違います。生成時刻・生成時の generator SHA・再現 argv の一部は、記録値を保持して形式・整合を検査します。これは README の説明と整合しています。
- 着地 test は実際に README の SHA 3行と caption を読みます。bundle 全欠落・部分欠落は失敗し、skip しません。日本語正文の意味までは自動検査しません。
- 稿の表をテストと同じ正規表現で読むと、§2.2 は3行、§2.4 は18行を取得し、値も一致しました。`**\`different\`**` と `(= … / 2^18)` の扱い、列位置は正しいです。
- test に埋め込まれた receipt／job-result bytes の SHA は外部 pin と一致します。その job-result には `prereg_commit`／`job_script_sha256` がなく、受領証で照合する実装は正当です。
- fixture は135 record、各5 throughput、36 cell、3族、参照点3種、Markdown の2節を持ち、境界跨ぎ・負の推定・正の下限を含みます。本物の Figure を layout check に渡しています。等価域の端点そのものだけが未検査です。

## 変異事前登録への所見

以下は**静的な対応確認**です。author の KILLED／SURVIVED をこちらで再実走した結果ではありません。

| 変異 | 対応 test と所見 |
|---|---|
| m0 | `test_generator_comment_change_preserves_provenance_closure` はコメント変更を許容する。ただし全 suite の SURVIVED 証拠ではない |
| m1 | `test_pinned_hashes_are_used_when_no_override` の実 repo 読込と `test_pins_match_results_document` が検出 |
| m2 | `test_receipt_sha_not_matching_submission_is_rejected` が対象検査の削除を検出 |
| m3 | `test_differences_order_mismatch_is_rejected` が逆順入力の受理を検出 |
| m4 | 定数変更では CI 式より先に spec 照合で拒否。author の留保は正しい |
| m5 | `test_equivalence_relation_mismatch_is_rejected` が分類検査の削除を検出 |
| m6 | `test_holm_p_mismatch_is_rejected` は Markdown を同期し、Holm 再計算を狙えている |
| m7 | `test_caption_contains_fixed_literals` は独立した逐語期待を持ち、文の削除を検出 |
| m8 | 重なり負例と publish 無出力検査が対応 |
| m9 | `test_constant_cell_nonzero_is_rejected` は効果・両端を個別に変え、対象検査を狙えている |
| m10 | `test_official_certification_true_is_rejected` は top-level と record を別入力で検査 |
| m11 | 重複族を追加して identity 集合を保持するため、族数検査の緩和を検出できる |
| m12 | raw p と Holm、Markdown を同期し、分母整数性の検査を狙えている |
| m13 | 下回る負例で削除を、10000ちょうどの正例で `>` 化を検出。ただし後者は通常 fixture 全般も先に拒否する |
| m14 | 不正 prefix `fig_invalid`／`fi13_invalid` を含み、緩和した正規表現による受理を検出できる |

再照準案：

- **m4：** 定数を保持して CI 計算式の係数だけを `1.96` に変え、正常 fixture の `cell interval recalculation` での拒否を観測する。
- **m13：** 検査削除と `>=`→`>` を別変異にし、前者は9999の負例、後者は10000の正例を期待 node として分ける。

m4／m13 以外に、指定した意味検査より前の別層の拒否で成立するものは、静的確認では見つかりませんでした。全変異の赤 node 完全集合と m0 の全 suite 対照は親の実走で確定する必要があります。

## 総括

must-fix **1件**：作図規約 §6 が必須とするデータベース件数1,000,000・Zipf skew 0.9 の条件表記が欠落しています。
判定・数値の転記は一致し、事前登録 §3／§8 を超える主張は認めません。
現状は **NO-GO**。条件を追記し、成果物・caption・README の束縛を更新後に再確認してください。
本レビューは静的照合であり、pytest・全変異 matrix の実走成功は判定していません。