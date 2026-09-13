## 所見

以下、`plan` は指定の `stage2-plan.md`、`brief` は指定の親 brief、Python ファイル名は同 worktree の `orchestrator/campaign/` 配下を指す。検証は静的読解と SHA-256 再計算のみ。pytest は実行していない。

**[S-1] 新規 gate の必要性を、既存 assembler が既に保証する性質で説明している**

- **根拠:** brief:47 は precursor について「現状は on==off しか見ていない」とする。しかし `p3_b4_raw_record_producer.py:2322` は block・attempt・registry hash・manifest hash・proposal を含む期待 binding を構築し、`:2333` で完全一致を要求する。さらに `:2337` で on/off 順に source を選び、`:2366` で検証済み binding の precursor を raw へ転記、`:2370` でその source の digest を設定する。plan:214 の負例は、この処理後に戻り値を変更する。
- **失敗シナリオ:** 公開済み attempt の source block を①のように変更する → 新 gate に達する前に producer `:2289` の厳密再導出比較、または `:2333` で拒否される。③の「source=P、raw=Q」は、既存 assembler がそのまま動く限り `:2366` から生成できない。④も `:2337` の固定 arm 選択から生成できない。これらを assembly 戻り値の差し替えで作り、新規の production receipt-shopping 遮断と数えると、**試験が証明した境界を過大に帰属する**。
- **深刻度:** major。
- **提案:** 親の「現状は on==off だけ」と G05 の説明を修正する。今回示せる追加保証は「組立て後の消費境界での対応再検査」。公開 artifact からの shopping を新たに閉じたという完了判定には、既存 assembler を通過する別の具体例が必要。

**[S-2] 「5 hash の照合が無い」から「閉包を編集しても test は赤にならない」への推論は誤り**

- **根拠:** brief:27、`rulings-verbatim.md:85`。実際には `p3_b4_analysis_prereg_consumer.py:703` に AST 検査があり、`:739` は evaluator 内の呼出し順序、`:752` は `_SOURCE_CLOSURE_PATHS` の内容を固定する。`:1005` の公開検査経路から呼ばれる。
- **失敗シナリオ:** `_SOURCE_CLOSURE_PATHS` に新 consumer を追加する → 5 値の hash 字面を照合しなくても `:754` の `"analysis source closure member tuple changed"` で赤になる。呼出し順の変更も `:750` で赤になる。
- **深刻度:** minor。
- **提案:** 「§5 に記入した whole-file hash の一致を直接検査する仕組みは見つからない。ただし閉包の構造・意味論を検査する仕組みはある」と限定する。今回の private import 自体がこの赤を強制するわけではない。

## 帰属が成立しない負例

**plan が明示する「組立て後の消費境界」に限定すれば、①〜④に独立 killer としての失格は見つからない。** 静的に構成可能である。

| 負例 | 既存検査で先に落ちない理由 |
|---|---|
| ① | 変更するのは source 内の block。adapter が照合する raw block は保持されるため、`p3_b4_analysis_adapter.py:543` の未知 block 検査には掛からない。source digest を追随させれば `_source_artifacts_match` も通る。 |
| ② | 既存 evaluator は source 内の proposal を読まない。raw precursor=P を保持するので既存の precursor 検査にも掛からない。 |
| ③ | on/off をともに合法 hash Q に変更するため、adapter `:562` と contract `:426` の不一致検査を通る。reference と assignment も保持される。 |
| ④ | source bytes と raw 宣言 digest を同時交換するので、`p3_b4_analysis_path.py:183` の宣言順と `:188` の実体順が一致し、`:193` の大域一意性も維持される。既存 evaluator は source の `identity.arm` を照合しない。 |

ただし、**実 assembler が生む production 入力の独立 killer としては4件とも証拠不足**。①②は既存 producer が拒否し、③④は戻り値への介入を要する。plan:214 の限定は妥当であり、その限定を外した成果主張が [S-1] の問題になる。

## 親 brief への反証

- **P1-a:** 閉包外への配置・配線が不可能という反証はない。`_source_artifacts_match` は `p3_b4_analysis_path.py:174` に実在し、必要な引数を受け取れる。公開契約ではないが、import のために閉包編集を強いられる箇所は見つからない。
- **P1-b:** **4者を列挙して hash で束縛するデータ構造という意味では、再生成 receipt は manifest に当たる。** plan:40 の行と `:64` の canonical payload がそれを実現する。一方、独立に確定された pair manifest との照合には当たらない。既存 `assert_analysis_manifest_complete` は渡された manifest と再生成物を比較する（`p3_b4_analysis_ledgers.py:1160`）が、新 API は pair manifest を受け取らず、成功 receipt も保存・射影しない（plan:34、139）。したがって「同じ厳密再生成・照合の型」という説明は限定が必要。T-1912 の逐語だけから、新 writer や永続化の必須性までは導けない。
- **P1-c:** **「現状は on==off しか見ていない」は production 全体について誤り。** [S-1] のとおり。列挙された4性質自体の整合性は覆らない。
- **P1-d:** 覆らない。大域重複禁止は `_source_artifacts_match` の `:193`、`:194` に存在する。
- **5 module の SHA-256:** 再計算した5値は、事前登録 doc:161 および射影の値とすべて一致した。
- **機械検査の不存在:** hash 字面だけの検索では不足。path・AST・呼出し順序の検査を確認した。ただし、記入済み5値との whole-file hash 一致検査そのものは見つからなかった。[S-2] の一般化のみ覆る。
- **production 消費点が1箇所:** 覆らない。実呼出しは `p3_b4_material_report.py:267`。他に tests と `p3_b4_producer_auth_experiment.py:606` のパッチ用文字列があるが、別の現行 production 呼出しとは数えられない。
- **G04「report 生成のたびに無条件発火」:** その字義では成立しない。assembly 拒否時は material report `:244` から戻る。ただし `analysis_result=None` を保持し、既存 test `orchestrator/tests/test_p3_b4_material_report.py:300` も `not_evaluated` を要求する。**欠損 report の公開を分析成功への迂回とは認定できない。**

受理集合の拡大、floor/verdict の緩和、既存 production 正例を必然的に落とす変更は、提示プランからは確認できなかった。

## scope 外だが real な所見

**実 precursor と campaign の束縛は、再生成 receipt を加えても成立しない。**

`p3_b4_raw_record_producer.py:63` が非保証として明記し、`:2033` は registry の proposal hash を転記、`:2366` はさらに同じ値を raw に転記する。実 campaign の precursor が別物でも、この経路にはその実体から hash を導出して比較する検査がない。

これは今回追加する consumer の不備として実装させる対象ではない。実由来の束縛を完成条件に含めるか、転記の一貫性だけを完成範囲とするかの裁定パッケージ候補である。

## 総括

閉包を編集せず配線する案は成立し、①〜④も組立て後の変異として構成できる。  
ただし、その4性質は現行 assembler の正常出力ですでに成立している。  
最大の欠陥は、新 gate の効果を production の receipt-shopping 遮断へ一般化する親 brief の説明にある。  
再生成 receipt は束縛データにはなるが、独立に確定した pair 選択との照合証拠にはならない。  
欠損 report 経路から分析成功へ抜ける経路や、正しさゲートの緩和は確認できなかった。  
SHA-256 の5値は一致。pytest・変異 matrix の実行結果は未確認。