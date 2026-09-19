## 所見

以下、`J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a1-sized-attempt2`、`driver` は `orchestrator/campaign/paper_story_a1_paired.py`、`事前登録` は `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md` を指す。静的検査のみ実施した。

1. **成立 — 択2は「固定表への1行追加」では実現しない。**  
   新 study は `_policy_identity` と v3 semantics の固定 ID 集合で拒否され、新しい事前登録も既存 sized の path・sha 固定照合に落ちる。さらに job shell の study 分岐、source 契約選択、hydrate 分岐、非認証 identity 登録も変更が必要。**二つの gate 本体を維持できることと、既存の受理集合に触れないことは別である。**  
   根拠：`driver:1026`、`:1438`、`:1690`、`tools/pegasus/paper_story_a1_paired.sh:39`、`:74`、`:1380`、`orchestrator/campaign/ident.py:37`。親の過少記述は `J/adjudication.md:69`。

2. **成立せず — 新 study でも先行 attempt のため二つの gate が必ず拒否する、という攻撃。**  
   `_assert_no_prior_v3_bench_start` は指定 base 内を走査する。新しい空の canonical base なら旧 attempt は走査されない。公開先検査も policy の指定先と一致し、宛先が未存在、親 directory が存在すれば通る。したがって、**新 study を正しく登録した後なら、両関数の変更は不要**。ただし base・公開先が「別」というだけで submit 全体の成立は保証しない。  
   根拠：`driver:2454`、`:2672`、`:2901`、`:8264`。

3. **成立 — D2096項5の扱いには明示的な裁定変更が必要。**  
   D2096は「登録 API」と「3 study目の枠組み」を別々に禁じ、固定表も2要素と指定する。「APIではない1行追加」は、第三 study を受理する変更への免責にならない。親は衝突を認識しているが、返答例の「固定表1行を許す」では実際の変更範囲を表せない。  
   一方、**D1323自体が第三 study を禁じる、という攻撃は成立せず**。同裁定は source の commit 同定と、新たな bytes 級同一性検査の禁止を定める。policy field の比較テストを直ちに禁止する根拠ではない。D1986前文は、名指しの実装以外の gate・台帳・汎用化を足さないという scope 制約である。  
   根拠：`J/materials/d2096.md:3`、`:17`、`docs/decisions.md:60018`、`:42450`、`J/adjudication.md:79`。

4. **成立 — 別 study 化にも、結果を見た再投入を繰り返せる危険が残る。**  
   新 study・新 base ごとに登録すれば、旧 study の bench 到達を検査しない。これは独立再現を可能にする構造そのものであり、study 名の変更だけでは結果依存の選択を排除できない。択1だけにこの危険を帰属させ、択2は gate 本体不変だから安全とする比較は非対称である。新規登録を誰が何回認めるか、既存結果と失敗を残すかが両案で重要になる。  
   根拠：`driver:2677`、`:2732`、`:2901`、`J/adjudication.md:66`、`:77`。

5. **成立／成立せず — 択1は規律2に関わるが、「認可があれば何度でも」は必然ではない。**  
   gate は自ら「MF2 rear gate」と記す防壁であり、解除は保護範囲を変える。本 wave の「規律2を緩めない」認可では実装できない。一方、規律2本文は anomaly 即 reject と検証を甘くする変異の禁止を定めており、認可済み別観測の設計が必ず verifier 緩和になるとまでは読めない。  
   現行 gate に認可入力がないことは事実。しかし提案どおり exact study・attempt・source に限定すれば、他 attempt の拒否は機械的に維持できる。**認可対象の識別は可能、認可者が性能値に影響されたかの識別は不可能**、と分けるべきである。後者は択2にも残る。  
   根拠：`CLAUDE.md:67`、`driver:2673`、`:2675`、`:3225`、`J/brief.md:17`、`J/adjudication.md:62`。

6. **成立 — §6.4への追加は誤記訂正ではなく、将来の実験規則の変更である。**  
   §6.4は理由を閉じて列挙し、全て bench 前の失敗に限定する。「認可済み独立再現」を追加すると明確に範囲が広がる。erratum と呼ぶだけでは正当化できない。採るなら、既存凍結物・既存結果の判定を保持し、将来の観測に適用する別版または追補として明示的に裁定する必要がある。  
   根拠：`事前登録:373`、`:380`、`J/adjudication.md:65`。

7. **成立 — 新 seed は今回の「同じ policy・配置」の自明な実現ではない。**  
   今回の要求をそのまま満たすのは、同じ seed・同じ物理順の再実行である。別 study で順序の共有を避ける研究設計なら、新 seed は§2.1の動機に沿うが、要求を「同じ配置規則」に変更したと明示すべき。§2.1は study 名から自動導出する一般規則ではなく、特定の原像を凍結している。  
   また、**新 seed でも物理順が変わる保証はない**。各 workload は3 bitで、全同一列を除く少数の順序しかなく、別 seed でも同じ列になり得る。「seed が変わるので物理順は同一にならない」は訂正が必要。順序を見て study 名や接頭辞を選び直してはならない。  
   同 seed は順序割付を共有するが、測定誤差の統計的依存をそれだけで証明しない。新 seed も測定値の独立性を保証しない。  
   根拠：`J/brief.md:15`、`事前登録:113`、`:128`、`:132`、`:139`、`J/adjudication.md:69`、`:72`。

8. **成立 — submit拒否を「落ちた」と数え、停止した判断は妥当。認可未消費との断定は根拠不足。**  
   stderr は実際の拒否を示し、コード上も gate は intent 書込・attempt root 作成より前にある。1回の既存 submit はユーザーの認可範囲内であり、実行自体を違反とは判断しない。ただし静的停止でも足り、相談Bもそれを推奨していた。  
   **計測 attempt は開始されていない。しかし認可された実行手続は submit 層の失敗で停止条件に達した。** qsub 未到達から「今回の認可で再度 submit してよい」は導けない。次の実行は再認可が必要である。  
   根拠：`J/submit.stderr:1`、`driver:3234`、`:3244`、`:3247`、`J/brief.md:13`、`J/materials/d2120-item3.md:5`。親の断定は `J/adjudication.md:12`。

## 択 2 の変更面

新規ファイル名は未裁定。以下は既存 pin を置換せず、新 study 専用に追加する前提。

| 区分 | file | 必要な変更 |
|---|---|---|
| code | `orchestrator/campaign/paper_story_a1_paired.py` | 新 policy の path・ID・sha、`_policy_identity`、v3 ID集合、事前登録 path・sha 選択を追加。二つの gate 本体は維持。根拠：94、202、1026、1438、1690行。 |
| code | `orchestrator/campaign/paper_story_a1_source.py` | 新契約 path・sha・source paths と `CONTRACTS` 行を追加。既存v2の流用では新 policy を束縛できない。根拠：24、32、44行。 |
| code | `orchestrator/campaign/ident.py` | 新 study の exact 非認証 identity を追加。根拠：37行。 |
| code | `tools/pegasus/paper_story_a1_paired.sh` | study dispatch、source契約・追補選択、source binding の各列挙、hydrate対象を更新。根拠：39、74、458、997、1380行。 |
| JSON | 新 policy JSON | study ID、base、公開先、事前登録束縛を設定。新 seed 案なら3 workloadの `schedule_root_seed` も変更。「4 fieldだけ」ではない。既存：`paper_story_a1_paired.v3-sized.json:29`、`:197`、`:237`。 |
| JSON | 新 source契約 JSON | 既存v2 schemaを使うとしても別ファイル。新 policy・事前登録・追補の path・sha を束縛。既存v2は単一 study の11 key objectで、追記用のstudy表ではない。根拠：`paper_story_a1_source.v2.json:2`。 |
| docs | 新事前登録・新source追補 | 原登録の引用と変更点、seed選択、1観測の範囲、公開先、失敗時停止を明記。旧凍結READMEと旧契約は維持。 |
| docs | 裁定記録・親パッケージ | D2096の第三study制約をどこまで変更するか、実際の実装面と受理集合の拡大を明記。成功後のresults接続は別途必要。 |
| tests | `orchestrator/tests/test_paper_story_a1_paired.py` | 新 policy・事前登録pin、条件比較、旧pin維持、新study内の再走拒否・公開先排他を検査。既存pin例：1275、1292行。 |
| tests | `orchestrator/tests/test_paper_story_a1_job_contract.py` | 新dispatch・契約・hydrate・source bindingを検査。`V3_STUDY=1` が2箇所という既存pinは更新対象。根拠：1623、1637、3256行。 |
| tests | `orchestrator/tests/test_a1_non_certifying_marker.py` | 登録identityと誤った組合せの拒否例を追加。根拠：26、31行。 |

指定の `tests/test_paper_story_a1_source.py` はこの checkout では見つからなかった。変更済み・検査済みとは扱えない。source契約の追加検査の置き場所は実装時に確定する。

計画用数値実験の `V3_SIZED_CERTIFICATE_REGISTERED_PARAMETERS` 内の root seed は、物理順用 `schedule_root_seed` と別物である。後者を変えるだけなら前者を変更する理由はない（`driver:223`、`:1416`、`:1808`）。

## 推奨の評価

**反対 — 現在の説明のまま択2を推奨することに反対する。別study案そのものは候補として成立する。**

択2には凍結済み成果物と公開先を保持できる利点がある。しかし、第三studyの明示的な許可、複数の固定分岐の更新、非認証identity追加を必要とし、結果依存の再投入問題も消えない。「既存gateに一切触れない」「固定表1行」「新seedなら物理順が変わる」を根拠に優位とするパッケージは修正すべきである。

第4案を置くなら、**今回は停止し、同一配置の反復と順序を変えた再現のどちらを研究目的とするかを確定してから、有限回の将来計画を別途裁定する**。これは新たな実行経路の提案ではなく、未確定の研究設計を先に解く案である。

択3では L-A1S-4 が残り、反復間の再現性を観察する機会を失う。この損失は重要だが、attempt-0001 の記述的価値は失われない。「研究前進を止める」は広すぎる。2本目が得られても、一般的な安定性の証明まで進むわけではない。根拠：`docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md:315`。

## 総括

本 wave の submit拒否後の停止は妥当。計測未開始と、再投入の認可が残ることは同義ではない。  
択2は二つのgate本体を維持できるが、第三studyを受理する複数の実装変更と明示的裁定を要する。  
択1だけを結果依存再走の危険で退ける比較は成立せず、その危険は別study登録にも残る。  
親パッケージは変更範囲・seedの説明・認可消費の断定を修正してから提示すべきである。