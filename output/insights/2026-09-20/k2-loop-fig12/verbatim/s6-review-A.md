## 所見 (must-fix)

1. **各 role の規律6の転記結果を捨て、常に「指示めいた内容なし」と描いている。**

   箇所: `tools/plotting/plot_k2_loop_flow.py:189`、`:300`、`:378`、`:502`。

   > `descriptive(cells['planner'], 'instance direction magnitude discipline6')`
   > `add('legend-r6', 'legend', 'R6: no instruction-like content (self-reported).', …)`
   > `_require(actual == _display_items(data['flow']), 'drawn_items disagree with flow')`

   `discipline6` は自由文検査だけを受け、表示文字列にも marker の条件にも使われない。`instruction-like content detected` へ反転しても数量検査を通り、表示期待集合は変更前と完全一致する。描画を伴わない関数抽出でこの点を確認した。T7 の独立照合もこの field を確認しない。

   放置時: 入力の自己申告が反転しても、図・provenance は「なし」のままで、表示一致検査も通る。現 JSON の転記は稿と一致するが、その一致を保つ仕組みになっていない。

   推奨 fix: この凍結図に必要な各 role の自己申告を小さな固定契約として検査し、反転を拒否する負例を追加する。自由文を保持するなら表示へ反映する。新しい汎用判定器は不要。

## 所見 (should)

1. **稿の限定6が caption に引き継がれず、生成日・送付・実施順序の証拠の限界が薄れている。**

   箇所: `tools/plotting/plot_k2_loop_flow.py:269`、`:593`。比較元: `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md:42`、`:155`。

   > `'proposal:', col['date_proposal'], 'evaluation:', col['date_evaluation'] or 'none'`
   > `'In each round the parent session projects typed JSON inputs …'`

   図の親 lane には `according to round records` があるため、限定が全面欠落しているわけではない。しかし、生成日と役割の実施順序までその留保に含まれること、保存 prompt が送達証拠ではないことは caption にない。

   放置時: 図や README の caption を単独で読むと、記録依存の手続きまで独立に確認された実施証拠に見える。

   推奨 fix: caption に「役割の起動・送付・生成日と細かな順序は各巡の記録による。保存入力は送達証明ではない」を短く加える。

2. **B-6 の非判定が欠け、構造遮断の範囲も広く読める。**

   箇所: `tools/plotting/plot_k2_loop_flow.py:597`、`tools/plotting/k2_loop_flow_2026-09-20.json:18`。比較元: 稿`:12`、§3 限定5。

   > `tools: [] (structural blockade)`
   > `… critic is a legacy role with Bash access, so these rounds are not material for the B-4 leak-control ablation.`

   B-4 非適格は明記されている。一方、稿が明示する「B-6 の充足を判定しない」「planner → coder の route-local 遮断も完備ではない」はない。

   放置時: tools 不在という局所的性質から、リーク制御全体の完備を読み込む余地が残る。B-6 充足を直接宣言してはいない。

   推奨 fix: 遮断を tool access に限定した表現へ変え、caption に B-6 非判定を一文追加する。

3. **提案値の二重表示は、目的に対して過剰で、数値の推移へ注意を向ける。**

   箇所: `tools/plotting/plot_k2_loop_flow.py:283`、`:285`、`:601`。

   > `parts = [cell['instance'], f"value {cell['value']}"]`
   > `parts = [cell['instance'], f"value {cell['value']}", …]`
   > `proposal values are backoff literals, not results.`

   caption の留保は適切だが、図中では coder と proposal の両方に汎用語 `value` 付きで同じ数値が並ぶ。

   放置時: データフローよりも 20／25／20／10 の推移が強調され、診断後の減少を成果として読む余地が残る。

   推奨 fix: P1 は下記の (b)。値は proposal に一度だけ `backoff literal` として示し、coder 側は instance と出力種別だけにする。

4. **provenance の arrows 照合は、実際に描いた矢印の確認になっていない。**

   箇所: `tools/plotting/plot_k2_loop_flow.py:355`、`:523`、`orchestrator/tests/test_plot_k2_loop_flow.py:262`。

   > `layout['arrows'].append(dict(id=ident, kind=kind, artist=artist))`
   > `drawn_items=_drawn_items(data,layout), arrows=data['flow']['arrows'],`
   > `assert prov['arrows']==_raw()['arrows']`

   provenance は入力をコピーし、test はそのコピーを入力と比較する。矢印 artist の可視性、件数、接続先との一致は確認していない。矢印削除などで交差が減る変更も、layout 検査だけでは検出できない。

   放置時: 図から還流が欠けても、provenance とラベルには還流が存在すると記録され得る。

   推奨 fix: 既存の production fixture で必須矢印の可視性・接続先との対応を確認する。固定 flow を provenance に含めるか、入力の還流・不在経路だけの記録とするかも明記する。汎用グラフ検証は不要。

## 所見 (nit)

1. **未使用の neutral marker 分岐が先例から残っている。**

   箇所: `tools/plotting/plot_k2_loop_flow.py:475`。

   > `for artist, owner, neutral in layout["markers"]:`

   登録箇所`:354`、`:382`はいずれも `False`。放置時の図への影響はない。推奨 fix: 第3要素と neutral 専用分岐を削除する。

2. **純粋な layout test の「file がない」は実質的に恒真。**

   箇所: `orchestrator/tests/test_plot_k2_loop_flow.py:191`、`:203`、`:220`。

   > `assert not list(tmp_path.iterdir())`

   呼び出す検査関数に出力先を渡していない。放置すると公開防止まで検証したように見える。推奨 fix: この3 assertion と不要な `tmp_path` を削除し、公開前拒否は T6 に任せる。

## P1 の判定

**(b) を推奨する。現状は性能値の掲載には当たらないが、数値推移や診断の効果として読む余地はある。**

- **(a) 値を消す:** 最も簡潔。既知値再提案や診断候補との一致を、文字の説明だけで理解する必要がある。
- **(b) 値を残し意味を明示:** 提案 literal の記録として有用。`value` を `backoff literal` に変え、proposal に一度だけ表示し、図内にも「結果ではない」を置く。
- **(c) instance 名だけで示す:** 提案の個体識別には十分。ただし proposal-1 と proposal-3 の値が同一であることは instance 名では示せず、別の説明が必要。

数列は単調減少ではなく、軸や性能単位もない。caption は非比較・非因果・literal と明記しているため、P1 自体を must-fix とはしない。job ID は `job` と明示され、評価と preflight 拒否の区別に役立つので保持が妥当。

## 恒真検査の一覧

以下は静的判定。pytest・描画・変異実走は行っていない。

| 検査 | 入力を変えて赤になるか／根拠 |
|---|---|
| schema・key 集合 | **なる。** `_keys`、T3 の未知・不足・重複 key 負例が実 `load_flow` を通る。 |
| enum | **なる。** `test_t3_invalid_enum_is_rejected`。column-kind は位置整合検査もあるため、M1 は direction 等で評価するのが明確。 |
| anchor 一意性 | **なる。** `test_t3_non_unique_anchor_is_rejected` は稿のコピーに見出しを追加して実 loader を通す。内容の意味一致は検査対象外。 |
| role frontmatter | **なる。** T2 の JSON 反転・実 file コピー変更。検査は tools 配列の空／非空であり、Bash の有無そのものを保証する検査ではない。 |
| 自由文の数量 | **なる。** T3 の loader 経由負例、T4 の関数負例。小さな字句契約であり、性能主張全般の分類器ではない。 |
| 規律6の結果と表示 | **ならない。** must-fix 1。反対の自己申告でも固定 marker・凡例・表示照合は不変。 |
| Text overlap・escape | **なる。** T5 は実 JSON から作った実 Figure の Text を追加・移動する。stub・monkeypatch・自作 bbox ではない。 |
| 矢印線分 × Text | **なる。** `test_t5_arrow_crossing_text_is_a_layout_error` は実矢印上へ実 Text を移動する。 |
| 領域・marker 検査 | **恒真ではない。** 生成器`:467`以降は実 bbox を検査。ただし各分岐の専用負例はない。neutral 分岐は現生成経路で未使用。 |
| 保存前 layout 呼出し | **なる。** T6 は衝突 Figure を本物の `_publish_outputs` に渡す。T5 と異なり公開経路の確認である。 |
| drawn_items | **なるが限定付き。** T7 は描画後に parent の文字列を変えて不一致を検出する。一方、期待文字列生成は描画側と共通で、規律6 field や矢印 artist は対象外。 |
| arrows と入力の一致 | **描画の正しさに対しては自己照合。** 入力コピー同士の比較であり、artist の欠落を検出しない。 |
| caption_source hash | **なる。** T7 は独立 hashlib で稿と比較する。 |
| no-clobber | **なる。** T7 は同 prefix の再実行を拒否し既存 bytes 不変を確認。生成器は `lexists` と `os.link` を使用。競合・部分公開失敗の専用 test はない。 |
| T5 の空 tmp | **実質恒真。** 出力先を使わない検査後の空ディレクトリ確認。T6 の同 assertion は有効。 |

稿の冒頭限定1〜6との対応は、**1〜5は主要な留保を保持、6は図中に部分的に存在し caption では不足**。性能改善・退行、知識や診断の因果効果、stock 対照達成、critic の tools 不在、性能認証を直接主張する文言は見つからなかった。

F36 は適合している。稿の実 SHA-256 は `1b0f6f568f17af4967362cb864a14c18ef9220f826e257c113da0065bb512758` で、指定 provenance と一致。稿に fig12 provenance hash の逆向き束縛はない。生成器が読む権威入力は稿・flow JSON・role 定義3件であり、role 本文を内容判断に使わず frontmatter を検査する。insight README や3巡目 materials の読込みもない。

## 削除候補

| 候補 | 削除・局所化と失われるもの |
|---|---|
| coder/proposal の値の二重表示 | coder 側を削除できる。同値を二度読む冗長性だけを失い、提案値の記録は残る。 |
| role と lane の重複 label/sublabel | role lane の表示を roles から導出し、重複入力と一致検査を削除できる。独立編集能力を失うが、現契約は独立編集を禁止している。 |
| 個別 `discipline6` 自由文 | 現状は表示されない。must-fix 1 の固定契約または実表示へ局所化できる。未使用散文の保持だけをやめられる。 |
| neutral marker 分岐 | 削除しても現図・受入能力は失われない。 |
| unused reference_ids 検査（生成器`:237`） | 削除しても数量拒否・図生成は維持される。未使用 allowlist の衛生検査だけを失う。段4の「使うものだけ」は更新が必要。 |
| T5 の空 tmp assertion | 削除可能。公開防止能力は T6 が保持する。 |
| T4 の先頭4数量例 | 同じ文字列を T3 が loader 経由で検査する。T4 は数詞・Unicode・ID 境界例を残せば M3 を検出できる。直接関数での同一例の再確認だけを失う。 |

閉じた schema、anchor、role 束縛、実寸 layout、no-clobber、独立 hash は削除非推奨。前二者や公開処理の多くは fig3b の先例であり、role 束縛と線分交差は本図で増えた主張・形状に対応している。T5 と T6、入力 hash と `caption_source` hash の照合も、それぞれ異なる欠陥を検出するため単なる重複ではない。

描画は静的に **Figure 作成2回、明示的 layout draw 6回、savefig 2回**。保存も数える8回という目安には収まる構成で、追加の削減を優先する必要はない。20秒以内は本レビューでは未確認。author 報告の8.66秒は再実測していない。

## 総括

**NO-GO — must-fix 1件。**
規律6の転記結果を反転しても図と表示照合が不変になる点を修正してから受入へ進める。
現 JSON の主要事実・非性能／非因果の留保と F36 は整合している。
統合 patch の追加内容は現物3ファイルと完全一致。テスト緑・変異 kill・最終着地は本レビューでは判定していない。