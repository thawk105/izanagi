## 所見

以下、`plan` は指定の `stage2-plan.md`、`brief` は指定の `brief.md`。コードのパスは当該 worktree 相対です。静的検査のみで、pytest・性能測定は実行していません。

**[L-1] T-1912 の receipt shopping は閉じない。プランは正直だが、親 brief の完了主張と矛盾する**

- **根拠:** `brief:5–10` は当該項目を「閉じる」とする。一方、`plan:259–266` は別 publication root での再発行・公開前選別・直接 evaluator 呼出しを明示的に除外する。issuer は呼出しごとに新 root と予定 artifact path を受け取る（`orchestrator/campaign/p3_b4_prerun_issuer.py:709–743`）。report は caller 指定 root 一つを読む（`orchestrator/campaign/p3_b4_material_report.py:211–244`）。
- **失敗シナリオ:** 実行前に publication A/B と別々の予定 artifact path を発行 → それぞれ整合した campaign pair 群を作る → 各 publication に対応する attempt artifact を公開 → 結果を見て有利な root だけ report API／CLI に渡す。新 consumer が見るのは選ばれた一組の registry・manifest・assembly だけなので、他方の存在も不提出も検出しない。
- **深刻度:** **blocker**。
- **提案:** 「T-1912 を閉じた」は不可。プランの「残る穴」は正直である。親 brief・完了条件を同じ範囲へ訂正し、receipt shopping は未完として残す。追加の全体管理機構を、この波で無断増設しない。

**[L-2] 新しい4検査は正常な production assembly に対して既存保証と重複する**

- **根拠:** producer は source binding を registry／manifest から構築する（`orchestrator/campaign/p3_b4_raw_record_producer.py:2027–2047`）。assembler は artifact の証拠再導出と exact bytes 一致を要求し（`:2275–2294`）、binding 全体を期待値と照合する（`:2322–2334`）。raw precursor はその検証済み binding から代入する（`:2366`）。source と raw receipt は同じ arm ループから生成する（`:2337–2370`）。
- **失敗シナリオ:** plan の①〜④を公開 attempt artifact に施す → 既存 assembler が拒否するか、raw は正しく再生成される。新 consumer の独立 killer にするには、`plan:214–243` のとおり **assembler の戻り値を後から差し替える必要がある**。逆に、選別した正当な pair を渡せば旧・新検査とも通る。
- **深刻度:** **blocker**。重複実装を scope 外とする条件に抵触する。
- **提案:** 新 consumer が防ぐ追加の実経路を示すまで、4検査を新規成果として採用しない。現状示せるのは「正常 assembler 後に注入した不整合の検出」であり、receipt shopping の遮断ではない。

**[L-3] 必須配線は限定的に証明できるが、現在のキャッシュ経由では証明を取り違えうる**

- **根拠:** `plan:162–170` は assembler 境界変異、evaluator spy、consumer 除去対照を要求する。既存正例は `_inputs`／`_document` を使い、両者は root 単位でキャッシュする（`orchestrator/tests/test_p3_b4_material_report.py:248–277`）。evaluator は report module に直接 import されている（`orchestrator/campaign/p3_b4_material_report.py:32`）。
- **失敗シナリオ:** キャッシュ作成後に spy を設置 → `_inputs` を再利用 → `_load_and_evaluate` 自体が走らず、evaluator の呼出し回数が0になる。また、定義元 module だけを patch しても report module の参照には届かない。
- **深刻度:** **minor**。骨格は成立するが実装条件の固定が必要。
- **提案:** キャッシュ helper を介さず public builder／writer を直接呼ぶ。spy は `material_report.evaluate_b4_artifacts` に、保存した実関数へ委譲する `wraps` または wrapper として置く。各負例で以下を同時に確認する。
  - 所定の `pair_completeness_rejected` と個別理由。
  - evaluator 呼出し0回。
  - consumer 呼出しを除去した対照では evaluator 呼出し1回。
  - writer 試験では新しい出力先に3ファイルが存在しない。

これで証明できるのは、**注入した assembly に対する report 経路の必須配線**までである。

**[L-4] 所要台帳の未登録は conftest も `--coverage-against` も失敗させない**

- **根拠:** `orchestrator/tests/conftest.py:1513–1538` は件数不整合なら台帳全体を空扱い、不正値なら当該 entry を除外する。未登録は `None`（`:1657–1677`）、並替え時には既知所要由来の代替コストを使う（`:1722–1745`）。updater の coverage は比率を文字列化するだけ（`tools/update_acceptance_duration_ledger.py:323–326`）で、欠落による非0終了はない（`:494–537`）。
- **失敗シナリオ:** 新 nodeid の一部を登録し忘れる → テストは通常収集される → updater が `covered < total` を表示しても終了0 → 終了コードだけ見る受入では漏れを見逃す。
- **深刻度:** **major**。
- **提案:** `plan:174–176` に「対象 nodeid 集合と台帳キーの差集合が空」を受入条件として明記する。新規テストだけの JUnit を通常更新に渡すと既存台帳を置換するため、追加時の `--add-only` または既存値を保持する具体的手順も必要（updater `:485–507`）。

**[L-5] DW-G05 は実成果物への影響と、合成境界への影響を混同している**

- **根拠:** `brief:34` は実 campaign 成果物0件、`:73–74` は放置した場合の材料レポート・分析 verdict への影響を主張する。しかし production の precursor は検証済み registry binding から転記される（producer `:2322–2366`）。新 consumer は凍結 evaluator の直接呼出しには入らない（`plan:264`）。
- **失敗シナリオ:** 整合した pair 群を選別して通常 report を生成 → 新旧とも同じ経路を通る。直接 evaluator に合成した不整合 source を渡す → 新 consumer を経由しない。したがって、挙げられた脅威に対する成果物改善を新検査へ帰属できない。
- **深刻度:** **major**。
- **提案:** 0件という事実だけで将来の危険可能性は否定されない。ただし正しい記述は次である。

> 実 campaign 成果物への改善は未確認。提案は、material report の assembler 後に注入された不整合 assembly を評価前に拒否する。正常 assembler の出力に対する追加効果、receipt shopping の遮断、直接分析 API・certified 選択への効果は示していない。

## 層の被覆表

| 成果物・生成層 | 新 consumer | 根拠と未被覆層の扱い |
|---|---|---|
| 材料 document：`build_material_report_document` | 成功 assembly で入る | `material_report.py:1222–1230`。計画どおりなら必須。 |
| 材料ファイル：`write_material_report` | 成功 assembly で入る | 同 `:1551–1561`。publish は評価後の `:1585`。 |
| 材料 CLI | 上記 writer 経由で入る | 同 `:1594–1608`。独立の report 生成迂回は見つからない。 |
| assembly 拒否後の欠損 report | **入らない** | 同 `:244–254`。`analysis_result=None`。既存欠損報告として維持し、検査成功と数えない。 |
| report 内の分析 verdict | 成功 assembly で入る | 同 `:267` の直前。保証はこの呼出しに限定。 |
| `evaluate_b4_artifacts` 直接呼出し | **入らない** | `p3_b4_analysis_path.py:199`。分析 API 全体を保証するなら別裁定候補。 |
| 純契約 `evaluate_analysis` | **入らない** | `p3_b4_analysis_contract.py:755`。入力は typed blocks 等で、publication 証拠を受け取らない。上位 API の利用境界の裁定候補。 |
| issuer publication／producer attempt artifact | **入らない** | issuer `:709`、producer `:2057`。report とは別の生成層。既存保証を維持する。 |
| launcher の certified receipt・単一 arm 継続 | **入らない** | `p3_b4_launcher.py:607–635`。別の pair 検証後、選択 arm を継続する。report gate の成果に含めない。 |
| 分析結果からの certified 選択接続 | **未実装のまま** | `material_report.py:883–895` は `certifying=False` と接続非保証を明記。実装済みの迂回と混同せず、既裁定の条件を維持。 |

`brief:70` の「report 生成のたびに無条件発火」は不正確。`plan:206` の「評価へ進む全 assembly に必須」が実装可能な表現である。

## 既存機構との重複

| 計画の検査 | 既存の等価な保証 |
|---|---|
| ① manifest と source pair の対応 | producer `_manifest_row`／`_attempt_input` の各1件要求（`:945–969`）、manifest 全行走査・欠損拒否（`:2255–2274`）、期待 binding 比較（`:2322–2334`）。 |
| ② source proposal と registry | source binding の生成（`:2027–2033`）と期待 binding 比較（`:2322–2334`）。既存負例もある：`test_p3_b4_raw_record_producer.py:2063–2079`。 |
| ③ raw precursor と registry | raw precursor は照合済み binding から直接生成（producer `:2366`）。独立した観測 precursor ではない。 |
| ④ receipt と arm slot | identity で on/off を分類し両 arm を要求（`:2299–2307`）、同じ arm の source bytes と digest を raw に代入（`:2337–2370`）。 |
| receipt digest の提出内一意性 | `_source_artifacts_match`（`p3_b4_analysis_path.py:174–195`）。plan は再利用と明記しており、この点は正しい。 |

周辺機構の射程も限定される。

- `_admission_sidecar_path_for_pair` は terminal receipt が同じ pair root の `on`／`off` 下にあることを要求する（producer `:1346–1359`）。別 pair の片腕混合を制限するが、**完成した pair ごとの選別は止めない**。
- execution lock は活動中・WAL変化等の扱いに使う（`:1596–1620`、`:1983–2004`）。block の生涯実行回数を管理しない。
- create-only publish は予定 leaf の異なる bytes による置換を拒否する（`:527–550`、`:569–580`）。同じ publication 内で別 artifact を任意指定する経路は `_planned_path` が制限する（`:972–984`）。別 publication の別 leaf、公開前の候補選別には届かない。

## 受入コストの実測根拠

**今回の実測値はない。以下は既存台帳の記録とコードからの判断である。**

- 台帳は `acceptance_duration_ledger.json:23109` に **23,105 nodeid** を記録する。件数条件は conftest `:1513–1522`。未登録を拒否する機構ではない。
- conftest `:1525–1538` は有限・非負の数値を受け入れ、0も許す。**数値 placeholder が実測かどうかは判別しない**。未実測値を登録しないという plan の方針は正しいが、機械強制とは呼べない。updater は JUnit の `time` を読む（`:99–112`、`:226`）。
- `test_plain_runner_coverage.py:44–46` は `os.listdir` による動的列挙。新ファイルの自動包含という plan の記述は正しい。ただしこれは harness の文字列検査（`:35–41`、`:60–74`）であり、自走の実行成功証明ではない。末尾コードには `if __name__ == "__main__":` が必要。
- 既存 production 正例の台帳値は **58秒**（台帳 `:12521`）。共有証拠から fresh publication を作る欠損試験は **11秒**（`:12496`）。これらは node 全体の所要で、201 pair 作成だけの時間ではない。
- 既存 fixture は module scope（`test_p3_b4_material_report.py:146`）。実 invoke は on/off 各1回で、残りは writer による複製、fsync は抑止している（`:190–220`、`test_p3_b4_raw_record_producer.py:2004–2036`）。「201 pair 全てを実 invoke」する試験ではない。

したがって、各負例で全 fixture を再構築する設計は避けるべきである。plan の「純関数試験は合成 bytes、production 適合は既存共有 fixture」の分離は妥当。実 assembly を一度得て、immutable bytes のコピーに変異を入れる構成が安い。増分所要は実装後に測り、拡張した既存58秒 nodeの値も更新対象にする。

## scope 外だが real な所見

- **publication／campaign／公開前候補をまたぐ選別:** L-1 の経路。T-1912 未完を残すか、どの選別単位を権威化するかが裁定候補。`rulings-verbatim.md:34–48` の追加基盤を採らない裁定があるため、台帳や不変 writer を自動追加しない。
- **分析 API 全体の保証範囲:** 直接 evaluator と純契約 API は未被覆。閉包を変更するなら、`rulings-verbatim.md:65–87` の5ファイル pin と演算定義の扱いを含む裁定候補。
- **certified 選択との接続:** report の完全性検査から既存 certified sink へ保証は伝播しない。`rulings-verbatim.md:46` の T-2139 条件を維持し、今回の完成主張に含めない。

## 総括

T-1912 完了としては、このプランを承認できない。  
別 root・公開前候補からの receipt shopping は残り、プラン自身も認めている。  
4検査は正常 assembler の既存保証と重なり、追加効果は戻り値への変異注入でしか示されていない。  
必須配線テストは限定範囲で成立するが、キャッシュ・spy 対象・除去対照を固定する必要がある。  
台帳の未登録は自動失敗しないため、集合差分の確認が必要。  
実装前に親 brief の scope・DW-G05・完了条件を訂正すべきである。