## 所見

**A-1 — must-fix：変異の検出根拠を再照準する。**
対象：[s4-adjudication.md「変異事前登録」](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/s4-adjudication.md)、[test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/orchestrator/tests/test_plot_a2_certification.py) の unknown-study／pin test。

m6 は生成器の study 検査を除去しても producer が未知 study を拒否する。現 test は例外文言の違いで赤になり得るが、受理集合の変化を検出した証拠にはならない。m1 の既存 `test_m11_whitespace_changed_certification_fails_cli_with_zero_outputs` も、一時ディレクトリの certification が pin 表にないため、変異対象の SHA 比較より前で拒否される。A-6 専用 pin test はこの問題を避けている。生成器の防壁追加ではなく、変異の対象・検出 node・主張の局所修正でよい。

**DW-G05：放置すると変異結果レポートが、別層の拒否を「対象検査が受理集合を守った証拠」として参照してしまう。図の値は変わらない。**

**A-2 — should：A-2 不変の対象を明記する。**
対象：[plot_a2_certification.py `build_provenance`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/tools/plotting/plot_a2_certification.py:845)、plan v2 の不変条件。

fig5／6／7 の着地ファイルは差分に含まれず、旧版・新版から再構成した caption は着地文字列と UTF-8 bytes 一致、artist 射影も一致した。A-2 の描画変更箇所も、既存の４ cell では同じ寸法・文字列になる。一方、新しく生成する A-2 current-full provenance には `study` が追加される。着地 closure test は、新規生成時の全キー集合の不変を証明していない。「着地 bytes と既存キーの射影は不変、再生成 current-full は study を追加」と書き分けるべきである。

**DW-G05：放置すると、再生成した A-2 provenance のキー集合まで不変だったという過大な互換性報告になる。既存図は変わらない。**

**A-3 — should：closure の説明を実装の射程に限定する。**
対象：同生成器 `_study_label`／`validate_repo_closure`、figures README「再現」「proof chain」。

fig11 の `study` だけを削除すると、A-2 caption の再構成結果が保存済み A-6 caption と異なり、実際に拒否された。ただし `validate_repo_closure` は caption_source 行の記録済み path／hash を照合するだけで、study との意味的対応は検査しない。メモリ上で study を削除し caption も A-2 版へ再構成すると、caption_source を残したまま同関数は通った。着地 test には別途 README caption・provenance 自身の hash・caption_source の照合があるため、これを単純な着地改変の通過経路とは扱わない。

**DW-G05：図の値・現行の着地受入結果は変わらない。説明を広げると、closure が保証する参照関係を過大に述べることになる。追加 gate は不要。**

**A-4 — nit：README の重複と二つの不正確な表現を削る。**
対象：[figures README の fig11 節](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/figures/README.md:1309)。

「study が pin 表の exact 2 件」は、３ leaf の `CANONICAL_SHA256` と２ study の `STUDY_PROFILES` を混同している。また「内部識別子は出さない」は、図の脚注に `rr95` を出す実装と一致しない。作図規約への適合節は規約の逐語転載ではなく本図への適用説明だが、「何を示す図か」「入力」「proof chain」と重複が多い。caption 正文・再現コマンド・hash 行・正本への参照を残して短縮できる。

**DW-G05：放置しても図・受理集合は変わらず、README に二つの不正確な説明と重複が残る。**

## 削除候補

| 候補 | 削除時の DW-G05 上の影響 |
|---|---|
| `check_figure_layout` の `len(plot_axes) != 2 * ncols` と、それだけに使う平坦化変数 | **変わらない。** 直前の「２行・各行同じ列数」で同じ条件が成立する。`len(fig.axes)` の検査は残す。 |
| README「作図規約への適合」の重複説明、caption 正文直前の固定文の再列挙 | **変わらない。** 本図の説明・caption・規約参照を残せば値・受理集合・参照先は維持できる。 |
| current-full 一覧 test と A-6 専用 real-root test の重複 load | **整理なら変わらない。** 一覧の exact 検査と両 study の実入力正例、A-6 固有の値照合は残す。test 丸ごとの削除は被覆を変える。 |
| `'four' if len(cells) == 4 else 'two'` | **単純削除は変わる。** A-2 と A-6 で両枝とも到達する。到達不能分岐ではない。 |
| `_study_label` の study 欠落時 A-2 既定 | **変わる。** study を持たない fig5／6／7 の着地 caption 再構成が壊れる。残す。 |
| `STUDY_PROFILES`／study 受理検査 | **変わる。** producer 自身は B7 の３ workload study も扱うため、生成器の exact ２ study 契約とは同一でない。残す。 |
| A-6 caption_source 追加 | **変わる。** 限定文の出所への束縛が消える。残す。 |
| m6 を通すための producer 迂回・追加 fixture 一般化 | **追加不要。** 変異の再照準で済み、本図の生成経路を広げる理由がない。 |

fig10 固有の床値判定・３ workload 集計が本図へ持ち込まれた形跡はない。

## 親 brief / 裁定への所見

**P1：README 追補による現況更新は妥当。ただし稿本文を更新したとは言わない。**
稿冒頭は明確に凍結を宣言しており、日付付き追補と results 表の更新は append-only 運用と矛盾しない。依頼の趣旨が「図なしという現況を更新する」なら、現在の実装で満たす。文字どおり「単独稿 §4 限定11 の本文を変える」要求とは異なり、その場合は凍結規則の例外を明示する必要がある。

また「provenance が束縛するから、生成前から稿を変更できない」は根拠として循環している。生成前なら変更後の bytes を束縛できる。P1 の根拠は凍結規則で十分であり、hash 束縛は着地後の変更制約として説明すればよい。

**P2：exact ２ study と `6 × N` は必要最小の共有化と判断する。**
既存 producer が A-2 を `(2 workloads, 4 cells)`、A-6 を `(1, 2)` に限定している。生成器の study 検査と合わせて N=0／N≥3 は入力経路で拒否され、legacy は A-2 のみ。CLI の hash override は追加されておらず、未登録 certification leaf も拒否される。既存の Python caller 向け `expected_hashes` を、新設の CLI 流用口とは数えない。layout helper 単体の `2 × N` 受理と、生成器全体の入力受理集合は区別すべきである。

**P3：着地 caption の値と限定は稿に整合する。**
median 比・性能 reject／正しさ certified の区別・単一 attempt・CI の記述的性質・B-10 と A-2 の非集計は稿に対応する。A-6 固有でない A-2 の末文も混入していない。figsize の計画値 `6.4` から実装値 `8.0` への変更は、同じ２段１列を描く局所的な配置調整である。

一次資料の読み取りで、次を確認した。

- certification SHA-256：`3a9505b009f4d0aa2161bcac8e50dada6712fc214d03d7d68d705060e6d92cab`
- raw manifest SHA-256：`8d17953575afc4594df052d5b5b778291c4d41a1564bb1fbc2d29e8d1df94ef9`
- 稿 SHA-256：`34a968428f867ce26479abe37320946b6eb8149007244dfe1d18a18446633850`
- 指定 durable root の外部６ file は実在し、記録 hash と全件一致。２ cell の５標本と median `10088796`／`9505248` も一致。
- embedded policy は１ workload・２ cell、request は `982234.nqsv` の１件。６ file は raw-manifest の閉包数であり、attempt 全体の file 数ではない。

**段２・３の省略：段６の独立レビューを残す判断は妥当。**
DW-C00 は受理集合変更に独立敵対検証を要求する。本レビューを含む段６を実施するなら、その要件を満たせる。「軽量版だから独立検証も不要」という一般化はできないが、省略段を今から形式的に増やす必要は見いださない。

**変異の再照準：**

- **m1：疑義あり。** 既存 m11 を検出根拠から外し、変更前 hash を保持して空白追加する `test_a6_pin_drift_is_rejected` を主検出 node にする。
- **m6：単一理由性なし。** current-full の許可集合から A-6 だけを落とす変異へ替え、既存の有効な A-6 fixture／real-root 正例で検出する。未知 study の別層拒否を迂回する機構は足さない。
- **m0・m2〜m5・m7〜m9：静的には追加の再照準理由なし。** m4 は余分な axes を不可視にして重なり理由を避け、m7 は request と claim を揃えている。正式 harness の単一理由性を実走確認したとの主張は、本レビューではしない。

## 総括

must-fix は **１件**：m1／m6 の変異検出根拠を局所的に修正する。
**NO-GO：plan v2 を記載どおり採用するには、上記の再照準が必要。**
生成器の共有化・fig11 の値・A-2 着地互換性には、作り直しを要する欠陥を認めない。
新しい gate・台帳・一般化は不要。静的照合と読み取り検証を実施し、pytest／正式変異走は実施していない。