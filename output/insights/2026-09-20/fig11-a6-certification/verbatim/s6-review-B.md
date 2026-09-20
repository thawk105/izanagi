## 所見

**B-1 — must-fix：abort 率の代表 rep 規則が caption と README から落ちている。**
対象：`tools/plotting/plot_a2_certification.py::_caption` の A-6 枝、`docs/paper-story/figures/README.md` の fig11「何を示す図か」「キャプション正文」。

稿 §2.3・§4 限定6は、**throughput が中央値に最も近い rep から採った1点**と明記する。現状の “one aggregate abort-rate point per cell”／「1点の集計 abort 率」は、5 rep の集約値とも読める。値 `0.1547 / 0.145` は一致しているが、集計単位の説明が足りない。例えば “one abort-rate observation from the repetition whose throughput is closest to the median” とし、README と逐語検査にも反映する。

**DW-G05：放置すると、下段の値が「代表 rep の率」から「5 rep を集約した率」へ読み替えられる。**

**B-2 — should：正しさの限定を補い、性能判定との文を分ける。**
対象：同 `_caption`、fig11 README の正しさ説明。

caption は L01、D1257、元の supply／meaning record 不在を記すが、稿 §4 限定4の **(iii) artifact hash 単独では compile-out の証明にならないこと、(v) `src_token` 一致は翻訳単位全体の意味の一致を保証しないこと**を落としている。README は4者の token 一致を説明するため、対応する証明力の上限も添えたい。詳細を全部転載する必要はなく、限定を短く示して稿 §4 の (i)〜(v) を参照できる。

また “all 2 cells were certified, but … and the performance reject …” は、意味上は明確に区別しているものの、稿 §0 の「文を分けたまま使う」とは一致しない。正しさの観測、性能の非認証、reject が証拠を取り消さないことを別文にする。図中の status 行と correctness 行は分離されている。

**DW-G05：放置すると、caption 単独で読む正しさ証拠の限定が稿より狭く提示され、README の identity 説明を過大に解釈する余地が残る。**

**B-3 — should：着地 closure の保証範囲を、一次資料との再照合と区別する。**
対象：`plot_a2_certification.py::validate_repo_closure`、`test_landed_fig11_repo_closure_and_caption_when_present`、fig11 README「proof chain」。

同関数は入力・出力の hash と、provenance 自身から再構成した artist／caption を検査する。しかし certification を読み戻して `study`・status・median・correctness と突き合わせず、`external_inputs` も manifest の部分集合検査である。例えば `external_inputs=[]` はこの関数では拒否されない。`study` 欠落と A-2 用 caption の整合した組合せにも、権威 study との照合はない。

これは既存 validator 由来の限界であり、今回の通常生成経路で偽の入力を通す問題とは区別する。fig11 着地 test に対象 certification／study と外部6件の一致を直接確認するか、README の「それらが着地後もずれないこと」の射程を限定するとよい。

**DW-G05：放置すると、自己整合した provenance の変更を、権威 bytes との意味的一致まで検証済みと説明できてしまう。**

**B-4 — should：m6 の KILLED を受理集合の証拠として数えない。**
対象：`s4-adjudication.md` の m6、`test_unknown_study_is_rejected`。

author の報告どおり、生成器の study 検査を外しても producer 側が拒否する。さらに test は例外文言を固定しているので、拒否層が変わるだけで赤になり得る。未知 study が受理される変異を殺した証拠にはならない。再照準案は後述する。

**DW-G05：放置すると、受理集合の防護が退行したときに検出できる範囲を、変異結果が過大に示す。**

**B-5 — nit：study 表と hash pin 表を混同した説明。**
対象：fig11 README「入力」の拒否条件。

「study が pin 表の exact 2 件」は、正確には `STUDY_PROFILES` の2件。`CANONICAL_SHA256` は A-2 の2 attempt と A-6 の計3件である。

**DW-G05：図や受理集合は変わらないが、README が案内する検査対象の表が誤る。**

確認できた正常部分は以下のとおり。

- **着地 bytes は一致。** PNG／PDF／provenance の README hash 3行、tracked 入力3件の hash、caption の fig11 節への逐語収録、外部入力6件と manifest の完全一致を読み取り検査で確認した。
- **値は一致。** median `10,088,796 / 9,505,248`、効果 `−0.057841193339621455`、abort 率 `0.1547 / 0.145`、attempt・request・host・条件・pin・2 cell に相違はない。abort 率の出所は certification ではなく WAL／稿 §2.3。
- **生成経路は fail-closed。** hash pin、study 必須、legacy A-6 拒否、未知 study 拒否、policy 由来の `6 × N`、request／時刻の一意性、保存前の `2 × N` axes 検査を維持している。`_study_label` の互換既定は、新規入力の study 欠落を救済しない。
- **fixture は描画上の実寸を満たす。** 1 workload・2 cell・各5標本、verify 12件、receipt 4 frame、外部6 file、本物の Figure の `(2, 1)` axes と10 artist 行を検査する。producer の policy／receipt parser は stub ではない。ただし lock・claim 等は合成した最小内容であり、production 証跡全体の再現ではない。
- `_load` の現行 hash 差し込みは意味検査用 fixture の境界。pin 検査では変更前 hash を保持し、実データ test は override 無しなので、pin 検査全体が恒真にはなっていない。

## caption と稿の対応表

文頭を識別子として示す。図番号の “Figure 11.” は出力 prefix 由来。

| caption の文 | 出所 | 判定 |
|---|---|---|
| “A-6 formal certification attempt …” | 稿 §0、certification `attempt_id / status / study` | 一致 |
| “The single workload campaign …” | 稿 §1.1・§1.3、`request_ids`、manifest `campaign_claims.rr95.claim`、embedded policy `workloads` | 一致。時刻は campaign claim の時刻 |
| “The top row shows all five …” | 稿 §2.1、生標本、生成器の artist 表現 | 一致。平均CIは派生統計 |
| “The gray dashed line …” | 稿 §1.1 の効果式、§2.1 の stock median | 一致 |
| “The median effect copied … −5.7841%.” | 稿 §2.1、`effects.rr95`、adopted genome | 一致 |
| “M tps means …” | 表示単位の定義 | 一致 |
| “Mean confidence intervals describe samples …” | 稿 §2.1 末段・§4 限定1 | 一致 |
| “The displayed outer status …” | 稿 §0・§1.1・§2.1、`status / effects / cells[].performance.median_tps` | 一致。今回の reject・負効果で成立 |
| “This is one attempt …” | 稿 §0・§4 限定1・3・8 | 一致。限定2の他条件への外挿禁止は明示を補える |
| “The bottom row … one aggregate abort-rate point …” | 稿 §2.3・§4 限定6 | **欠落：代表 rep の選択規則（B-1）** |
| “Correctness comes from separate trace-enabled runs …” | 稿 §2.2・§4 限定3、`cells[].correctness` | 内容は一致。§0 の文分離とは不一致（B-2） |
| “L01 limits that evidence …” | 稿 §2.2・§4 限定4(i)(ii)、`independent_observation_limits` | 記載部分は一致。(iii)(v) の限定が欠落 |
| “The raw manifest binds …” | 稿 §1.4・§4 限定4(iv)・5、manifest の receipt 束縛 | 一致。関門の実施そのものを保証していない |
| “Conditions: 48 threads …” | 稿 §1.1・§1.3、embedded policy `performance_common`、`current_pin` | 一致 |
| “The same-sign B-10 …; the A-2 attempts …” | 稿 §3.1・§3.4・§4 限定7・9 | 一致。独立再現・pool・前後比較を主張しない |

`2026-09-07T16:29:41.491476+00:00` は **JST の `2026-09-08T01:29:41.491476+09:00`**。稿の日付と矛盾しない。ただし scheduler request の Created `01:28:55` とは別の時刻なので、caption も “campaign claim recorded at …” とすれば明瞭になる。

限定の残りでは、限定9の旧環境／実行基盤測定との非比較、限定10の測定後 policy bytes 変更が caption に無い。対象を描かず、policy bytes の測定時不変も主張していないため、直ちに過剰主張とは判定しない。限定11は README の日付付き追補で適切に扱い、限定12の perf 不使用は収録している。

## 親 brief / 裁定への所見

- **P1：妥当。** results 稿を凍結し、README に2026-09-20の追補を置く方法は append-only と整合する。稿の現 hash も一致した。凍結の根拠は運用規則であり、hash は変更を検出する束縛である。
- **P2：概ね妥当。** 1 workload／外部6 file は実物と一致し、一般化は小さい。ただし「A-2 provenance 射影を1 byteも変えない」は範囲を明確にしたい。既存 fig5／6／7 の bytes は変更対象外だが、**新規生成する A-2 current-full provenance には `study` が追加される**。
- **P3：B-1・B-2を反映すべき。** brief は「abort 率は代表 rep 1点」を要求する一方、裁定の英文骨格が既に “aggregate” に縮めている。正しさの限定も裁定段階で (i)(ii) 中心に縮約されており、実装だけの問題ではない。
- README の日付・主要数値・hash・file 数、D12／D1993／D1637／T-2430 の用途は射影資料と整合する。一覧行も fig6／fig10 と同じ構成。未追加の plotting README 1行は指摘対象にしない。

変異の静的評価：

| id | 評価・再照準案 |
|---|---|
| m0 | docstring の等価変異として妥当。生成時 source hash の変化とは区別する |
| m1 | A-6 の変更前 hash を保持した空白追加入力が適切。別の意味不整合を入れていない |
| m2 | 正常な6-file入力が12固定で落ちる正例が有効。過不足入力だけでは別の閉包検査と重複する |
| m3 | caption_source の件数・path・現 hash・scope の直接比較で検出可能 |
| m4 | 追加 axes を不可視にして副次的な文字重なりを避けており、単一理由性への配慮がある |
| m5 | 固定文削除の直接検出として有効。B-2で文を分けた後は変異位置と期待文も更新する |
| **m6** | **単一理由性なし。** 「current-full の受理集合から A-6 を誤って除外する」変異へ再登録し、正常 A-6 が拒否されることを殺す案が明確。未知 study の例は拒否維持の確認として残す |
| m7 | request 変更時は claim と certification を揃え、時刻変更と別 parametrization にしている。対象述語以外の明白な拒否理由は見当たらない |
| m8 | 全欠落の直接呼出しで skip を AssertionError に変換しており、期待に対応する |
| m9 | 凍結 fig6 caption と現在の組立てを比較するため、A-2 caption の変更を検出できる |

正式変異走は実施していないため、以上は KILLED／SURVIVED の実測報告ではない。

## 総括

must-fix は **1件：abort 率の代表 rep 選択規則を caption・README に戻すこと**。
**NO-GO（B-1修正まで）**。正しさの限定と文分離、closure の説明範囲、m6 の再照準も推奨する。
着地 hash・主要数値・UTC/JST・実寸 fixture・通常生成経路には不整合を認めなかった。
読み取り検査のみ実施。pytest・正式変異走の成功は本レビューでは主張しない。