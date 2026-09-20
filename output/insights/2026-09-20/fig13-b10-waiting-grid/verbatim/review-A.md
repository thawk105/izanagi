## 所見

指定資料・差分・着地 PNG を確認した。静的レビューに加え、入力 5 file と画像 2 file の SHA-256、36 cell の効果・区間を読み取り専用で照合した。SHA は記録と一致し、効果・区間の再計算差はすべて 0。pytest・変異走は実施していない。

以下、生成器は [`plot_b10_waiting_grid_forest.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/tools/plotting/plot_b10_waiting_grid_forest.py)、test は [`test_plot_b10_waiting_grid_forest.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig13-b10-waiting-grid/orchestrator/tests/test_plot_b10_waiting_grid_forest.py) を指す。

**A-1 — should｜生成器 `_authority_data`、figures/README「入力」：Markdown 照合は削減でき、説明も実装より広い。**
report JSON と report .md は双方が固定 SHA で束縛されているため、同じ固定資料同士の Holm 照合を毎回行うことは、本番入力の選別には重複している。さらに cell 36 行について実装が検査するのは**行数だけ**で、効果・区間・identity の値照合ではない。README の「Holm 3 行・cell effects 36 行との照合」は、この差を明示した方がよい。追加パーサは不要で、削減するか「Holm 値の照合と cell 行数の確認」に局所修正する。

DW-G05：放置しても現図の値は変わらないが、README が cell 値まで照合済みと読める状態が残る。パーサ削除は hash override 下の受理集合を広げる。

**A-2 — should｜plan v2 `RELATIONS`、生成器 `_relation`：未観測の分類名を受理する理由は弱い。**
`outside-equivalence-range` は現 report に存在せず、通常 CLI では固定 SHA によりその分岐へ到達しない。一方、hash override 下では、区間とその文字列が一致すれば受理する。したがって裁定の「実例が無い名前を受理集合に足すのではない」は、本番 pin の範囲に限れば正しいが、関数全体については正しくない。この report 専用なら、外側になった時点で対象外として拒否する方が狭い。将来 report 対応へ一般化する必要はない。

DW-G05：現図・caption は変わらないが、現状は override 下で未観測の分類名を受理する。

**A-3 — nit｜生成器 `REPORT_*_EPOCH`、`load_evidence`、`validate_repo_closure`：過剰の起点は「全 field の再構築」である。**
時刻の実値は外部 bytes と一致している。図や caption に時刻は不要だが、plan が要求する「外部を読まず report field まで再構築する閉包」の下では、この 2 定数には役割がある。新たな判定経路ではなく、固定受領証の値の複製である。外部 SHA 照合後の時刻一致検査は重複だが、**定数だけの削除では同じ閉包契約を保てない**。今回これを blocker にする根拠はない。

DW-G05：放置しても値・受理集合に誤りは生じない。定数と閉包照合を除けば、provenance の時刻改変に対する受理集合が変わる。

**A-4 — should｜生成器 `make_figure`、P1：主な過剰は panel 題の情報量。**
PNG では重なりによる読取不能はない。灰色 tick は 3 block のばらつき、空丸 18 個は構成上の参照 cell、5 項目の凡例は実際の符号化に対応している。削減するなら、panel 題の raw p の「分数＋小数」の二重表示と、18 対の和の数値を caption に移すのが先。本文幅へ縮小すると、この 3 行と長い条件脚注が細かくなる。空丸は balanced μ5 などで小さい効果点と近接するが、36 cell を見せる P1 の目的もあるため、一律削除は勧めない。

DW-G05：放置しても数値は変わらないが縮小時の可読性が下がる。題の短縮は表示・画像 bytes を変えるため、無影響の削除ではない。

**A-5 — should｜両 README の fig13 節：説明の重複を減らせる。**
figures/README は一覧・「何を示す図か」・「入力」・適合節・日英 caption・proof chain で、同じ限定と検査一覧を繰り返している。tools/plotting/README まで拒否条件と固定 caption 文の説明を持つ必要は薄い。後者は用途・コマンド・入力 root・出力と fig13 節への参照で足りる。作図規約の逐語転載というより、**適用説明と限定文の多重記載**であり、別の規律を新設したものではない。

DW-G05：caption 正文・必要な限定・参照・SHA 行を残した整理なら、図の値・受理集合・参照先は変わらない。

**A-6 — should｜変異表 m4・m13、対応 test：検出理由の確定が必要。**
m4 の定数変更は CI 式へ進む前に `spec confidence interval` で拒否される。CI 計算の検出証拠として扱えない。m13 は境界正例と下回る負例を同じ test に置くため、`>` 化と検査削除で同じ node が赤でも、観測した性質が異なる。後述の再照準で足り、新しい検査機構は不要。

DW-G05：図は変わらないが、そのまま変異結果を確定すると、CI 式と曝露境界について検出できた範囲を台帳が過大に表す。

なお、`_relation` の再分類・Holm 再計算・raw p の整数性検査は、いずれも report の値を上書きせず不一致を拒否する。**「判定を作らない」と両立する照合**である。raw p の整数性は図中の分数表示を支えるが、符号反転検定自体の再実施を意味しない。

## 削除候補

「不変」は現成果物の意味・受理集合・参照について述べ、単なる source hash の変化とは区別する。

| 候補 | DW-G05 上の判定 |
|---|---|
| 未使用の `_string`、`POINTS_PER_BLOCK` | **不変**：提示された生成器・test に使用箇所がなく、値・受理集合・参照を変えない。 |
| `_authority_data` の末尾の grid 完全性検査 | **不変**：135 件、期待集合内、一意、point と shape/mean の一致を既に要求しており、`set(indexed) == expected` と登録 108 件は導かれる。 |
| 外部 SHA 照合後の epoch 一致検査 | **本番では不変／全体では変わる**：固定 bytes では冗長だが、外部 pin を差し替えた test 条件では受理集合が変わる。 |
| report .md の Holm パーサ・cell 行数検査と専用負例 | **本番では不変／override 下では変わる**：固定 SHA を残せば本番入力・描画値は同じ。 |
| `outside` 分岐を拒否へ置換 | **現成果物では不変／override 下では変わる**：未観測の外側 cell を受理しなくなる。 |
| `crosschecks` の `differences/intervals/holm/report_markdown=True` | **変わる**：成功時に恒真だが、削除すると provenance の field と閉包受理集合、README の参照が変わる。無影響な掃除ではない。 |
| `direct-label` 用の owner-axis 検査 | **現図では不変／検査関数の受理集合は変わる**：本図は該当 gid を生成しない。任意の追加注釈まで対象にすれば差がある。 |
| README の重複した拒否条件・固定文の日本語要約 | **不変に整理可能**：正文・限定・正本への参照を残す。 |
| 灰色 tick、空丸、凡例項目、脚注の削除 | **変わる**：示す情報または限定が減る。単なる冗長コード削除とは扱えない。 |

着地全欠落・部分欠落 test は、着地 test の skip 化を検出する役割があり、「通常は既に file がある」という理由だけでは削除候補にしない。

## 親 brief / 裁定への所見

**実測前提。** tracked 2 file・稿・外部 2 file の SHA、epoch、`driver_rc=0` は一致した。135 records、36 cells、3 families、各 18 differences、raw p の分子 6702／70／2、inside 32／overlaps 4／outside 0、CI 式も確認できた。job 結果に `prereg_commit` と `job_script_sha256` が無い点は author の説明どおりであり、裁定 §1.7 は「受領証の 6 field、job 結果の 4 field」と書き分ければよい。

brief の「3 workload × 3 block × 15 点 × 5 rep = 135 record」は単位が混ざっている。**135 records、各 5 samples＝675 samples**が正しい。実装 fixture の寸法にはこの誤記は伝播していない。

**軽量版。** DW-C00 は受理集合が変わる作業に独立検証を求めるが、必ず段 2・3 を実施するとは書いていない。一次資料と P1 を明示し、段 6 の独立 review を残した判断は妥当。fig11 と完全同型とは言いにくいものの、今から段を追加し直す根拠にはならない。

**単一理由性を再照準すべき変異。**

- **m4：** 定数変更による spec 照合と、定数を保った CI 式だけの `1.96` 化を分離し、後者は正常 fixture が `cell interval recalculation` で落ちる観測を取る。
- **m13：** `>= → >` はちょうど 10000 の正例、検査削除は 9999 の負例へ分け、同一 node の赤を同じ理由として記録しない。
- **m10：** top-level と record の 2 箇所を区別し、削除箇所と対応入力を固定する。双方一括削除を一つの性質の証拠にしない。
- **m8：** 重なり検査の「どの block」を無効化するか固定し、通常 Figure は通る、重なり注入後だけ落ちなくなる、という差に絞る。

m2／m3／m5／m6／m9／m11／m12 は、静的には単一理由を保つ工夫がある。特に m6・m12 は Markdown を同期し、m11 は identity 集合を保った重複を入れている。m0 の全 suite 生存は author 自身が未確認と明記しており、焦点 test の生存から拡張して記録しない。以上は静的判断で、最終赤 node 集合の観測を代替しない。

**文書の置き場と時点。** 「限定 11 は起草時点の事実」「その後 fig13 を作成」「稿 bytes と results 表は保持」の書き分けは、当時の事実と現在を分離しており整合する。results 表の変更を追加要求する必要はない。稿・decisions への参照もあり、独自の研究判定を README に作ってはいない。

## 総括

must-fix **0 件**。現図の値・入力束縛・限定に、このレンズから着地を止める誤りは見つからない。
判定は **GO**：plan v2 の作図本体を採ってよい。
Markdown 照合の説明、未観測 relation の扱い、重複文書は削減・局所修正を推奨する。
変異表は m4・m13 を中心に検出理由を再照準してから確定し、静的確認を変異走の成功として記録しない。