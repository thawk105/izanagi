## レンズ A

以下、`G` は生成器、`T` は test ファイルを指す。行番号は今回読んだ現物に基づく。指定資料はすべて読めた。実行・描画・外部測定 root の再検証は行っておらず、親 brief の実測報告と今回の静的確認を区別する。

**must-fix A1 — v2 caption が 4 行図の説明になっていない。**

- **根拠:** plan §1.4(2)(3)。既存文をそのまま使うと、G:275–276 の “The top row” / “The bottom row” は図全体の最上段・最下段を指し、中間 2 行の意味が曖昧になる。“the blocks share nothing but the grid” も、同じ spec・測定条件・判定規則を共有するという追記項 5 と整合しない。
- **成果物への影響:** caption が panel の対応を誤って説明し、共有条件まで異なるように読める。
- **是正:** 行の説明は “Within each block, the upper row …” / “Within each block, the lower row …” にする。“share nothing but the grid” は削除し、cohort ごとに別標本・別推定、y 軸も cohort-local であることを具体的に書く。固定表現の直前に、各 cohort に独立に適用する旨を置く。

**must-fix A2 — 「着地 fig8 を受理する」と「v1 の受理集合・凍結 bytes が不変」を同一視している。**

- **根拠:** plan §1.3、§1.7、§4 Q4。実際の着地 test は **T:414–423**。G:455–457 が artist・caption・claim boundary を照合する。一方、G:456 から呼ぶ `_caption` は G:272 で `_figure_number` を使うため、正規表現の拡張は v1 closure にも伝わる。
- **成果物への影響:** 従来拒否した英字 suffix の v1 bundle が受理可能になる。また、既存 provenance 自体を変更し、PNG/PDF の hash も追随させた場合、着地 test だけでは着手前の 3 file との byte 同一性を保証しない。
- **是正:** v1 経路では従来の prefix 制約を保持し、v2 だけ英字 suffix を許すか、「v1 の受理集合不変」という契約を親が明示的に見直す。I1 の確認は既存着地 test に加え、着手前・着地後の **3 file の完全な SHA-256** を比較する。provenance の自己 hash を同じ JSON 内へ追加する必要はない。

`_caption` の既存着地値との文字列一致は、T:422 → G:456 により間接的に守られる。ただし test が skip せず、着地 provenance が凍結されていることが前提である。`_artist_series` も同様。関数の source bytes、再描画した Figure の同一性、v1 の全受理集合まで保証する test ではない。

**should A3 — P1 の縦積みは整合するが、「重ね描き＝合成違反」とは言えない。**

- **根拠:** 追記項 2・3、cohort2 §2.6、FIGURE_CONVENTIONS §4。
- **成果物への影響:** 重ね描きでは近接した系列が一致度評価を誘い、役割の区別も弱くなる。
- **是正:** 縦 2 block を採用する。別系列を重ねるだけなら標本・区間・verdict の合成ではなく、追記項 3 に直ちに違反しない。主従を明示すれば項 2 にも直ちに違反しない。ただし作図規約 §4 の見出しは「重ね描き」も対象とし、この図には機序を示す目的がない。本文の具体例は二軸・異種指標であり、同一指標の cohort 重ね描きまで詳細に規定しているわけではないが、積極的な採用根拠にはできない。

cohort-local y 軸は許容される。ただし形や傾きを比較できないことを図中にも残す。縦積み自体が一致度評価を不可能にするわけではない。

**should A4 — 7.2 × 10.6 in は描画寸法であって、論文 1 ページへの収録実証ではない。**

- **根拠:** plan §1.5、§3.1、FIGURE_CONVENTIONS §10。現行は G:315 の 7.2 × 5.7 in、文字は G:338・346・351 の 6 pt、G:343 の 8 pt。
- **成果物への影響:** 長い caption と併置するために縮小すると、tick・直接ラベルが読めなくなる可能性がある。
- **是正:** 最終掲載寸法で PDF を確認する。原寸は約 183 × 269 mm であり、図の高さだけでも大きい。例えば高さ 8 in へ縮めると、6 pt は約 4.5 pt になる。投稿テンプレート・本文領域が射影にないため「1 ページに入る」は未確定とする。幅は既存図と同じなので、12 panel という数だけから各 panel が小さすぎるとは断定できない。

**should A5 — 再現欄の情報配置を README まで具体化する。**

- **根拠:** 追記項 2、cohort2 §2.6・§4.1、plan §1.7・§3.2。
- **成果物への影響:** provenance に情報があっても、README の再現欄から両 cohort の束縛と一次成果物を区別して辿れなくなる。
- **是正:** README に cohort 別の対応表を置き、次を明記する。

| 必須情報 | plan にある配置 | 補う点 |
|---|---|---|
| group id・役割・verdict | caption、`cohorts[]` | README でも主結果／独立再現を対応づける |
| preregistration commit | caption、`preregistration.commit` | 短縮表示と完全値の参照先を区別 |
| preregistration blob SHA-256 | `preregistration.document_blob_sha256` | README の束縛欄から参照 |
| spec SHA-256 | `report.spec_sha256` | “same spec” を両値の一致確認に基づかせる |
| 集団報告 3 file | `external_inputs` | cohort 別の root 相対 path・完全 SHA-256 と root |
| results 稿 | `results_document` | 両稿へのリンクと §2.6／§4.1 |
| 着地 PNG/PDF | `outputs` | hash による byte 確認の説明 |

全 hash を caption に詰める必要はない。`tools/plotting/README.md` 更新は **plan §3.3 に既にあり、不足とは判定しない**。

**nit A6 — P4 の指定語句そのものは主張を強めていない。**

- **根拠:** 追記項 1・7、cohort2 §2.6「この表が言うこと」、T:236–241。
- **成果物への影響:** 指定語句を変更しないことによる具体的な違反は確認できない。
- **是正:** “independent reproduction” は前向きに定めた地位、“the same aggregate verdict” は稿が明示する事実として使う。“not read as anything beyond” と `NOT_POOLED_WORDING` は主張を制限する文であり、禁止語 list にも当たらない。ただし地位説明を末尾で重複させる必要は薄い。

正しさは cohort ごとに 120 記録、anomaly 0 と書き、総数を省く方針を支持する。240 という記録数自体がプール推定になるわけではない。重要なのは G:282 相当の「trace 有効の別走行・記録された検査条件・性能認証ではない」という限定を落とさないことである。

**nit A7 — 親の実測からの一般化には、既に留保がある。**

- **根拠:** brief「親の実測」の末尾。
- **成果物への影響:** 留保を維持する限り、現時点で成果物が変わる欠陥ではない。
- **是正:** 未実測を、2 cohort の layout、block 見出し、v2 publish、v2 closure、v2 caption、README 収録、掲載寸法での可読性と列挙する。25 passed と外部 6 file の hash 確認は親の報告として扱う。今回、その実行履歴を独立に検証したとは書かない。

## レンズ B

**must-fix B1 — provenance builder の引数化だけでは v2 を保存できない。**

- **根拠:** plan §1.8。G:462–464 は保存処理の先頭で `fig._b10_tail_caption = _caption(data, prefix)` を実行する。builder 呼び出しはその後の G:475。
- **成果物への影響:** `cohorts` を持つ v2 データを渡すと、v1 `_caption` が top-level `workloads` を要求して失敗する。v1 互換データを渡して回避すると、Figure の caption 属性が v1 に上書きされる。
- **是正:** publish の caption 設定も v1/v2 に対応させる。builder だけを差し替える plan を修正し、新 test #8 が実際の publish 経路を通ることを必須にする。

**must-fix B2 — block-title は既存 layout 検査だけでは panel 侵入を検出できない。**

- **根拠:** plan §1.6。G:396–399 の panel 侵入検査は `text.axes is not None` のときだけ。`fig.text` の block-title はここを通らない。
- **成果物への影響:** 見出しが panel 内の曲線・空白領域に入っても、他の text と重ならなければ図を保存できる。
- **是正:** `gid="block-title"` に限って plot axes との交差を検査する。v2 の正常図に加え、見出しを panel 内へ移動した負例、text 重なりの負例、保存物ゼロを確認する負例を設ける。一般的な新検査基盤は不要。

さらに `len(plot_axes) in (6, 12)` は、v2 が誤って 6 axes になった図も単独では受理する。既定 6、v2 では 12 を明示するなど、生成モードごとの期待数を維持する方が契約に合う。

**must-fix B3 — 変異の kill とデータ取り違え検出を、新 test 案のままでは帰属できない。**

- **根拠:** plan §2.1・§2.2、下記変異表、T:121–128。
- **成果物への影響:** cohort 2 の不正 verdict、CI・境界点・区間注記の取り違え、検査の欠落が緑のまま残り得る。
- **是正:** test 本数ではなく、各変異に対応する独立した観測値と失敗理由を固定する。特に verdict 負例は候補 (f) の値そのものを使う。描画期待値は生成器の `_artist_series_v2` から取らず、fixture の生値から計算して実 artist と比較する。

**should B4 — fixture の値ずらしは平均の取り違えには効くが、すべての描画要素には効かない。**

- **根拠:** plan §2.1、T:75–97、FIGURE_CONVENTIONS §10。
- **成果物への影響:** throughput に一律 +12345 を足しても標準偏差・CI 幅は変わらず、cohort 1 の CI を流用した図を検出できない。区間値・job id も既存 fixture のままなら区別できない。
- **是正:** cohort 2 の反復間変動、区間値、job id も区別可能にする。JSON の reps・`tps`・statistics、DAT を整合して更新する。両 cohort の tail と境界点について、throughput・abort 率・CI、区間線と直接ラベルを確認する。

`_fixture(tmp_path, cohort=1, **overrides)` への追加自体は、現物の既存呼び出しと両立する。`_seal` も既定 1 なら既存経路を保てる。ペアは同一 root の異なる report directory に作ればよく、brief の「2 root」と plan の「同じ root」は表現を統一すべきである。

**should B5 — CLI argv の位置互換と役割固定を明文化する。**

- **根拠:** plan §1.8、T:345–349。既存 test は `argv[4]` を出力 prefix として検査する。
- **成果物への影響:** `--cohort 1` を prefix の前へ挿入すると、既存 CLI test が失敗する。
- **是正:** v1 の展開 argv を維持するか、追加 option を prefix より後ろに置く。既存期待値を変えない方針との整合を plan に書く。

役割について、固定された `[1, 2]` と `["primary", "reproduction"]`、各番号に対応する group・入力 pin を検査すれば、単純な CLI／provenance の主従交換は拒否できる。ただし `PRIMARY_COHORT = 1` を宣言するだけでは拘束にならない。期待する役割まで変更可能な表から生成すると同じ誤りに追随するため、test #2 の固定 literal に意味がある。

また、roles・group・pin を残して `workloads` と artist・caption を一緒に交換した provenance は、自己再投影だけでは原入力への帰属を証明できない。既存 fig8 README が明示する closure の限界を v2 にも引き継ぎ、実入力からの再計算と artist test に帰属検証を持たせる。新しい汎用監査機構は要らない。

**should B6 — top-level key 集合固定は、限定すれば scope 内だが「非プールの証明」ではない。**

- **根拠:** 依頼原文の scope、plan §1.7・§2.2 #3。
- **成果物への影響:** top-level だけを検査しても、`cohorts[]` 内や既存 field にプール値が入る誤実装を排除できない。
- **是正:** この図の v2 出力形状を守る局所 assertion として扱う。それなら既存 closure の必要な拡張の範囲に収まる。一般 schema validator、新 gate、台帳へ広げない。非プールは cohort ごとの生値・統計・artist の対応で確認する。

定数表・v2 schema・専用 caption・専用 figure・v2 closure は、v1 を保ちながら後継図を作る分離として妥当。不要なのは「13 本」という本数目標、既存 test の単なる重複、closure を入力履歴の完全監査へ拡張すること。新 test #10 は実質的に既存着地 test の継続であり、新規 1 本とは数えにくい。

**nit B7 — file:line は広く誤っている。関数名は概ね正しい。**

- **根拠:** plan §1 と現物。
- **成果物への影響:** 行番号の誤記だけなら成果物が変わるとは言えないため nit。ただし変更箇所の見落としにつながった部分は B1・B2 として別に指摘した。
- **是正:** 次の現物アンカーで更新する。単一の固定オフセットでは直らない。

| 対象 | plan の参照 | 現物 |
|---|---:|---:|
| pin 表末尾 | G:36 まで | G:34–38 |
| `COMPARISON_WARNING` / `FIXED_WORDING` | G:49 / 50 | G:52 / 53 |
| `_validate_dat` | G:126–141 | G:136–153 |
| `load_measurements` | loader 節内 | G:156–163 |
| `_load_measurements` | G:143–233 | G:166–255 |
| `_figure_number` | G:236–239 | G:258–261 |
| `_caption` | G:242–267 | G:264–286 |
| `_artist_series` | G:278–292 相当 | G:297–309 |
| `make_figure` | G:295–345 | G:312–367 |
| 固定 prefix の caption 設定 | G:342 | G:365 |
| `check_figure_layout` | G:356–388 | G:378–407 |
| `build_provenance` | G:395–411 | G:414–426 |
| `validate_external_sources` | G:414–421 | G:429–436 |
| `validate_repo_closure` | G:423–441 | G:439–459 |
| `_publish_outputs` | G:444 以降 | G:462–493 |
| `main` / 展開 argv | G:478–500 / 496 | G:496–517 / 508 |
| `_seal` / `_fixture` | T:33–107 など | T:39–46 / 49–105 |
| 禁止語 test | T:203–208 | T:236–241 |
| pin と稿の一致 | T:311–317 | T:326–332 |
| 実 root test | T:354–366 | T:401–411 |
| 着地 fig8 test | T:369–378 | T:414–423 |
| 自走 harness | T:381–404 | T:426–449 |

**nit B8 — CLI 名と README 追補文は改善余地がある。**

- **根拠:** P2・P5、追記項 2。
- **成果物への影響:** 正しく実装すれば図の値は変わらないが、`--cohort 2` を cohort 2 単独と誤解しやすい。
- **是正:** `--with-reproduction-cohort 2` が最も意味を表す。`--cohorts 1,2` は自由な選択・順序を許すように見える。現案を維持するなら help と plotting README に「1 + 2 の併記」と明記する。「再現欄は単独では意味を持たない」は一般論ではなく、今回の併記要件に限定する。

fig8 節へ追記しながら「本節は変えない」と書くのは不正確。「既存本文と凍結 3 成果物を保持し、後継図への案内を追記する」とする。

**nit B9 — 中間挿入は衝突を減らすが、回避保証ではない。**

- **根拠:** brief「並行 wave」、plan §3.2–3.3。
- **成果物への影響:** 別 wave と一覧・近傍文脈が重なれば競合し、解消時に一方の案内を落とし得る。
- **是正:** fig8 節直後と既存コマンド節への局所追記を維持し、統合時に fig8・fig8b・fig10 の一覧、節、コマンド例を確認する。今回の射影だけでは README 全体の絶対行番号や fig10 の実際の変更位置までは検証していない。

## 変異の帰属

以下の `#n` は plan §2.2 の test 番号。実行結果ではなく静的予測である。

| 変異 | 予想される検出先・理由 | 単一理由／stub に関する判定 |
|---|---|---|
| (a) cohort 2 DAT pin の末尾変更 | #7、凍結稿 §4.1 の digest と不一致 | 独立した稿との比較なら明確。`expected_hashes` を渡す fixture test だけでは production pin 変更を検出しない。loader／closure を stub 化しても #7 は残る。 |
| (b) `COHORTS[2]["role"]="primary"` | #2、literal `"reproduction"` と不一致 | 明確。期待値を同じ定数から作らない。closure の role 検査でも落ち得るので、帰属先は直接 assertion に固定する。 |
| (c) cohorts 順序検査の除去 | #2 の入替負例が候補 | 全 cohort を逆順にすると role 検査も失敗する。`"cohort order"` の phrase 不一致で test が赤くても、順序違反を受理した証拠ではない。重複検査を整理するか、残存防護として記録する。 |
| (d) caption から `NOT_POOLED_WORDING` を削除 | #4、文言不在 | 定数を残したまま出力だけ落とす変異なら明確。caption producer と closure が同時に欠落へ追随しても、独立した内容 assertion が検出する。 |
| (e) `FIXED_WORDING` を禁止語へ変更 | #5、および既存 T:225・239–241 | 強く検出できるが複数 test が反応する。新 test #4 が変更後の定数だけを期待するなら単独では弱い。既存の固定 literal が独立した根拠になる。 |
| (f) cohort 2 verdict に `saturated-in-all-workloads` を追加許容 | #13 の verdict 負例 | 既存 T:278 と同じ `"fixture-invalid"` では変異後も拒否し、kill できない。対象 verdict を正確に投入し、再 seal して pin 失敗を除く。loader を直接検査し、closure 側の別拒否へ帰属させない。 |
| (g) layout checker の先頭 return | 既存 T:207–220、T:368–378 | 既存負例は検出する。新 #1 の正常系だけでは検出しない。v2 にも重なり／侵入の負例と publish ゼロを置く。checker と publish 側の双方を無効化した場合も、その負例が赤になる必要がある。 |
| (h) `_figure_number` を数字のみへ戻す | #6、`fig8b_x` 拒否 | 明確。#4・#8 も巻き添えで失敗し得る。最小の帰属先は #6。 |
| (i) 下 block に cohort 1 の値を描く | #1、実 line の y と cohort 2 生値由来の期待値の不一致 | 平均の取り違えは検出可能。artist metadata と closure の自己整合だけでは通る。CI・境界点・区間まで対象にするには B4 の補強が必要。 |
| (j) `cohorts_pooled=True` | #13、claim boundary 不一致 | provenance だけの変更なら明確。定数と生成結果を共に True にする変異では自己比較が追随する。`is False` の独立 assertion が必要。#3 の `"pooled": true` という文字列検索は `"cohorts_pooled": true` を検出しない。 |

「両層 stub でも緑」を防ぐには、producer／closure 間の一致だけを oracle にしないことが要点である。生値から計算した描画期待値、凍結稿の pin、固定 literal、意図的な不正入力に対する拒否という、それぞれ独立した根拠を残す。変異行・対象 test・期待理由を固定する前に「全件単一理由で kill」とは報告できない。

## 総括

**must-fix は 5 件:** A1 caption の行・共有条件説明、A2 v1 不変契約と凍結 bytes の保証範囲、B1 v2 publish の caption 経路、B2 block-title の panel 侵入、B3 変異・取り違え検出の欠落。

| provisional 裁定 | 判定 |
|---|---|
| P1 縦 2 block | **条件付き支持**。裁定に整合。掲載寸法と v2 layout は未実測。 |
| P2 `--cohort {1,2}` | **条件付き支持**。動作は妥当。意味と argv の位置互換を明記。 |
| P3 provenance v2 | **条件付き支持**。分離は妥当。v1 の受理集合と closure の保証範囲を修正。 |
| P4 caption | **条件付き**。限定語句は支持するが、A1 の説明文は反証。 |
| P5 README 追補 | **支持**。既存本文保持と追記を区別し、束縛情報の配置を明記。 |
| P6 suffix 正規表現 | **条件付き支持**。v2 に必要。共通変更だけで v1 受理集合不変とは言えない。 |
| P7 軽量版＋敵対検証 | **条件付き支持**。本数より変異の独立性・帰属を優先する。 |

Q1〜Q6 への回答:

- **Q1:** 1 ページ収録は未確定。7.2 × 10.6 in と長い caption の組合せを、投稿寸法で確認する。重ね描きへの変更は推奨しない。
- **Q2:** 直接ラベル 6 個という密度は実寸 fixture で検査可能。ただし block 間見出しの空間確保と B2 の侵入検査が必要。text と曲線の重なりは現行 text bbox 検査だけでは保証しない。
- **Q3:** README の長さと紙面の可読性は別。約 1.6 倍という見積りは未実測。重複する役割説明を削り、固定表現・非プール・cohort 別の値・性能と正しさの限定を残す。
- **Q4:** 正しい参照は T:414–423 → G:455–457。凍結された既存 provenance に対する caption／artist 再投影一致を守る。3 file の履歴的 byte 不変や全受理集合不変は別確認。
- **Q5:** `results_document` の path 所有は自己参照 hash ではなく、問題ない。稿の凍結 bytes と生成器を相互 hash で束縛しない限り、ここで循環は生じない。
- **Q6:** **今回読めた cohort2 §2.6 の「完走 (JST)」行が両日付を明示している。これを根拠にできる。** `completion.started_epoch` は開始時刻なので、完走日の直接根拠にはしない。射影にない §1 を今回確認済みとは扱わない。