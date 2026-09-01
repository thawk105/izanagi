## file:line の食い違い

既存 file への参照は逐一確認した。主な照合結果は次のとおり。

| 資料 | 参照 | 結果 |
|---|---|---|
| brief | `layer3_report.py:691` | 一致。consumer 不在を明記。 |
| brief | `reflux_origin_binding.py:12` | 一致。`certifying` を後続昇格の権威とする。 |
| brief | `p3_b4_material_report.py:735` | 不一致。735 は `report_projection_bijection`、対象の `certified_selection_connection` は 739。 |
| brief | `p3_b4_material_report.py:46-59` | 一致。schema、固定名、non-guarantee 定数。 |
| brief | `p3_b4_material_report.py:691-795` | 一致。report wire 全体。 |
| brief | `p3_b4_material_report.py:1155-1277` | 一致。commit marker、publish、public writer。 |
| brief | `p3_b4_analysis_contract.py:42-92` | 一致。invalid reason と 4 verdict。 |
| brief | `p3_b4_analysis_contract.py:206-219` | 一致。`B4AnalysisResult`。 |
| brief | `p3_b4_analysis_prereg_consumer.py:1080-1092` | 部分一致。verify API は 1080–1089、receipt-return API は 1092 から。 |
| brief | `layer3_report.py:682-693` | 一致。 |
| brief | `reflux_origin_binding.py:1-20` | 一致。 |
| brief | `p3_b4_analysis_path.py:68-74` | 1 行ずれ。tuple 全体は 67–73。 |
| brief | `p3_b4_analysis_prereg_consumer.py:98-106` | 一致。tuple は 98–104。 |
| brief | `test_real_repo_serialization.py:247-253` | 一致。xdist group golden。 |
| brief | `test_real_repo_serialization.py:308-314` | 部分一致。対象 mapping は 310–315。 |
| brief | `conftest.py:260` | 一致。real-repo inventory。 |

plan の既存参照では、以下を個別に確認し、記載内容と一致した。

`p3_b4_analysis_path.py:11-16`、`reflux_origin_binding.py:204-257`、`:260-298`、`layer3_report.py:682-703`、`p3_b4_analysis_path.py:67-73`、`p3_b4_analysis_prereg_consumer.py:98-104`、`p3_b4_material_report.py:1171-1175`、`:717-719`、`:720-727`、`:728-744`、`:745-750`、`:699-716`、`:214-230`、`:709-716`、`:849-870`、`:150-180`、`:498-663`、`:1176-1210`、`p3_b4_analysis_path.py:349-353`、`:102-121`、`p3_b4_analysis_contract.py:85-91`、`test_p3_b4_material_report.py:560-589`、`:903-940`、`p3_b4_prerun_issuer.py:1-24`、`:52-63`、`test_p3_b4_raw_record_producer.py:1523-1547`、`test_real_repo_serialization.py:247-315`、`conftest.py:258-260`、`:1991-2000`、`p3_b4_analysis_prereg_consumer.py:1027-1089`、事前登録文書 `:154-167`。

- **severity: nit** — brief の `p3_b4_material_report.py:735`、`p3_b4_analysis_path.py:68-74`、`test_real_repo_serialization.py:308-314` は実体より数行ずれている。  
  **成果物影響:** 値・受理集合は変わらないが、レビューや台帳から辿る参照が別の行を指す。

- **severity: nit** — plan の `p3_b4_material_report.py:46` は schema 定数しか示さず、「producer wire、marker、402-row projection」の総称アンカーにはならない。また `test_p3_b4_material_report.py:1` は単なる import 行である。  
  **成果物影響:** 値は変わらないが、変更不要の根拠をその参照だけから再現できない。

- **severity: must-fix** — plan が「実 report」の根拠にした [test_p3_b4_raw_record_producer.py:881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_p3_b4_raw_record_producer.py:881) は、自ら「one real block and non-durable writer replicas」と記し、200 block を `os.fsync` patch 下で複製している。file:line は実在するが「real B-4 artifact」という一般化を支持しない。  
  **成果物影響:** synthetic fixture の受理を real publication の受理証拠として台帳・レポートから誤参照する。

- **severity: nit** — 新規 2 file の「予定 `:1-348`」「予定 `:1-325`」は現在存在せず、事実アンカーとしては検証不能である。  
  **成果物影響:** 実装後に行番号がずれるだけで、現時点の成果物値は変わらない。

## 既存被覆との重複と純増

- **severity: must-fix** — estimand「この material report が certified selection を許すか」は、既に [p3_b4_material_report.py:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:720) の `report_scope`、`:728-744` の `certification_scope.certifying=False` / `certified_selection_connection` 非保証、`:745-750` の floor 不在、`:849-870` の Markdown 非認証表示で material report 自身が機械可読に答えている。  
  **成果物影響:** 新 module を置いても certified 選択の受理集合は既に空のままで、report.json の値も変わらない。

- **severity: must-fix** — 3-file durability/binding も producer と既存 test が既に検査している。publisher は marker を最後に置いて両 digest を束縛し、[test_p3_b4_material_report.py:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/tests/test_p3_b4_material_report.py:809) が exact marker を確認する。純増は「保存後に別 reader が canonical bytes、hash、Markdown、限定的 semantic field を再検証すること」だけである。  
  **成果物影響:** 純増が変えるのは standalone API が破損コピーを decision ではなく例外へ写す受理集合だけで、certified 選択・材料レポート・台帳は変わらない。

- **severity: nit** — repository 内に同じ B-4 3-file wire を読む既存 consumer は見つからなかったため、read-side validator 自体は重複実装ではない。  
  **成果物影響:** 将来 callsite ができれば破損 report の受理集合を狭めるが、現在は参照元がない。

## 所有範囲の衝突

- **severity: must-fix** — production 新 module は所有対象 4 file を import しない設計だが、正例はそうならない。material-report CLI は [p3_b4_material_report.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:38) から raw producer を importし、raw producer は `p3_b4_closed_critic` と `p3_b4_launcher`、さらに closed critic は `p3_b4_admission_record` を importする。test helper も `test_p3_b4_closed_critic` の private fixture に依存する。4 file のうち wiring probe を除く 3 file とその test が実行依存面で重なる。  
  **成果物影響:** 別 wave の変更により正例の生成値・test 受理集合が変わり、T-2139 の「独立した緑」を確定できない。

- **severity: must-fix** — file を編集せずにこの依存を避ける方法は、着地済みの real report artifact を入力にすることだが、現 checkout には存在しない。手書き fixture に替えると所有衝突は避けられるが「実体名指し」の条件を失う。  
  **成果物影響:** 現在の二者択一では、別 wave 依存か synthetic 正例のどちらかが成果物参照に残る。

## 成果物影響と過剰実装

- **severity: blocker** — 新 API の返り値は in-memory dataclass だけで、writer、CLI、material report への追記、台帳 entry、certified sink への参照が一つも計画されていない。「誰かが report を certified 根拠として引用する経路」を何も遮断しない。  
  **成果物影響:** 実装後も certified 選択の受理集合、`report.json` / `report.md`、台帳参照は 1 bit / 1 field も変わらない。

- **severity: must-fix** — versioned connection schema、7 種の公開例外、3 digest、exact top-level schema、402 count、Markdown parser、directory-FD/inode framework は、現時点では呼出元のない約350行の互換層である。各 guard は standalone API の入力集合を狭めるとは言えるが、要求された成果物への効果は言えない。  
  **成果物影響:** 保守対象となる public API と rejection vocabulary だけが増え、選択値・材料レポート・台帳は不変である。

- **severity: must-fix** — worklog で「5語目を埋めた」とする一方、producer wire は引き続き `certified_selection_connection` を `not_guaranteed` に置く計画である。「report 単独の非保証」という説明は可能だが、wire 自体にはその限定を区別する新 field がない。  
  **成果物影響:** 同じ report が「接続済み」と「connection not guaranteed」の両方から参照され、材料レポートの状態解釈が二義化する。

## 発火 gate と命名

- **severity: blocker** — `find output -name report.complete` は 0 件で、既存 artifact path も B-4 計測 ID も書けない。plan が挙げる pytest node は tmp report を作る test IDであって、real artifact path / measurement ID ではない。  
  **成果物影響:** production artifact の受理・拒否は一度も評価されず、台帳へ結び付く decision 参照も生じない。

- **severity: blocker** — P4 は「入力生成条件」と「connection の発火条件」を取り違えている。material-report CLI は pair を書くだけで新 API を呼ばず、repository 内にも planned API の production callsite はない。test が生成後に手動で API を呼ぶことは live wiring ではない。  
  **成果物影響:** CLI 実行後も certified 選択の受理集合と downstream report は従来どおりである。

- **severity: must-fix** — `git grep` 上、module 名、schema 文字列、class/function 名は未使用で一意だが、`certified_selection_connection` は既に [p3_b4_material_report.py:739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_material_report.py:739) で「非保証」の識別子として存在する。新 module を同じ語で「完了した接続」と呼ぶと反対向きの意味が併存する。  
  **成果物影響:** worklog・report wire・将来 consumer が同じ識別子を異なる lifecycle 状態として参照する。

- **severity: must-fix** — `analysis_invalid_reasons` は既に [p3_b4_analysis_prereg_consumer.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2139-b4-certified-connection/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:118) で「許される全 reason vocabulary」を意味する。新 decision では「この結果で実際に観測した reasons」を意味し、同じ B-4 public dataclass 群で意味が異なる。  
  **成果物影響:** 将来 serializer・台帳が allowed vocabulary と observed reasons を取り違えて参照する。

## test の実効性

- **severity: must-fix** — `test_real_cli_material_reports_are_bound_non_certifying_decisions` という名称に反して、入力 publication は fake runner、temp Git repository、複数の monkeypatch、1 real pair＋200 writer replica で作られる。material-report subprocess と connection API を stub しないだけで、依存鎖全体は stub-free ではない。  
  **成果物影響:** synthetic input の False decision が real B-4 report の受理証拠として誤って台帳化される。

- **severity: must-fix** — 正例は production callsite を通さず、test が新 API を直接呼ぶだけである。したがって C01 の `False→True` killer も standalone return 値を固定するだけで、certified sink の受理集合を殺していない。  
  **成果物影響:** test が赤くなっても、実際の certified 選択や材料レポートの値が変わることを証明しない。

- **severity: nit** — 負例の「最初の fail-closed 発火」と「特定 guard まで到達」は区別されており、semantic mutation で marker/Markdown を再束縛する順序に欠陥は見つからなかった。  
  **成果物影響:** standalone API 内の rejection reason の参照精度だけが上がる。

- **severity: nit** — 新 test が本当に function-scoped `tmp_path` 完結で、`xdist_group` と real-repo fixture を使わないなら、`_XDIST_GROUP_NAMES_GOLDEN`、`_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN`、`_REAL_REPO_NODE_INVENTORY` は赤くならない。この判定は静的には妥当である。既存 `immutable_publication` を再利用する設計へ変えるなら別である。  
  **成果物影響:** 現計画どおりなら golden / inventory の受理集合は変わらない。

## 親の実測値とその一般化に対する反証

- **severity: nit** — 新事実1の狭い観測は再現した。`*1769*` branch 0、worktree 0、worklog exact entry 0、tracked insight は存在し、probe commit も履歴にある。ただし、これらは「対応する名前の Git 作業面が残っていない」証拠であり、process/job の非稼働を証明する liveness oracle ではない。  
  **成果物影響:** 現 plan は T-1769 の file を編集しないため値は変わらないが、「非稼働」を根拠に所有解除すると将来衝突しうる。

- **severity: must-fix** — 新事実2について `git worktree list` は `t1999-unit2b/2c`、`t2005-fix1/2/3` の worktree と lock を確認できるが、lock は live session を意味せず、一覧だけでは uncommitted file 集合を再現できない。また親の一般化は編集 file のみを見て、前述の test/import 依存面を落としている。  
  **成果物影響:** source edit が素集合でも、別 wave の未確定 API により正例の値と test 受理集合が変わる。

- **severity: nit** — 新事実3は確認した。B-4 material report を読む production consumer はなく、`build_accepted_report` の production callsite もない。これは plan の根拠ではなく、現 scope で接続を完成できない反証になる。  
  **成果物影響:** 新 module を追加しても downstream reference は 0 のままである。

- **severity: nit** — 新事実4は内容として正しいが、正確な行は 735 ではなく 739。  
  **成果物影響:** report の値は変わらず、参照だけがずれる。

- **severity: nit** — 新事実5は「成功した sanctioned assembly が floor check まで到達する」という限定では支持される。4 verdict 中、正規 evaluated path の verdict は `protocol_violation`、assembly rejection は verdict ではなく `not_evaluated` status である。  
  **成果物影響:** 現 material report の値域は変わらないが、synthetic fixture は real 到達性の証拠にはならない。

## scope 外だが real な指摘 (裁定パッケージ候補)

- **severity: blocker** — 検査を実効化するために必要な層は次の 8 層であり、plan の scope に入るのは 2 だけである。  
  **成果物影響:** 欠落層を埋めない限り、certified 選択・材料レポート・台帳のどれにも検査結果が到達しない。

1. material report producer/writer — code は存在、real publication/report path は不存在。
2. 3-file read-side validator — 本 plan の新規 module。
3. validator を呼ぶ sanctioned CLI または workflow callsite — 不存在。
4. decision を必須入力にする certified-selection sink — 不存在。
5. `True` を許し得る発行・再導出済み authority — T-2140 後まで不存在。
6. decision の durable artifact、材料レポート追記、または台帳参照 — 不存在。
7. `certified_selection_connection` 非保証から接続済みへの lifecycle/schema 表現 — scope 外。
8. real artifact を actual callsite→sink まで通す end-to-end test — 不存在。

裁定候補は次のいずれかである。

- 推奨: T-2139 の実装を止め、現在の plan を design memo として保持する。real `report.complete` の安定 path または measurement ID、sink owner、durable decision の参照先が着地した wave で validator と callsite を同時実装する。
- 代案: 本 wave を「material-report post-publication integrity validator」に明示的に縮退し、`certified_selection_connection` と名乗らず、5語目を埋めたとも記録しない。
- scope 拡張案: sanctioned invocation、durable decision、sink の required input、wire lifecycle 更新まで同一 wave に含める。これは「新規2 fileのみ」と別 wave 所有境界を越えるため、親判断ではなくユーザー裁定が必要である。

## 総括

- **severity: blocker** — 現 plan は整合した standalone validator の設計ではあるが、certified-selection connection の設計ではない。real gate、呼出点、sink、durable reference がなく、P4 の tmp test は発火 gate の代用にならない。現状態では実装せず design memo に留めるべきである。  
  **成果物影響:** 実装しても certified 選択の値・受理集合、材料レポート、台帳参照はすべて不変である。

pytest は実走しておらず、以上は指定資料、repository source、Git の read-only 状態に基づく静的レビューである。