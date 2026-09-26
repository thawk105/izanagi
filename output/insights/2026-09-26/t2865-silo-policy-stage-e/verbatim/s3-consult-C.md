## 所見

1. **must-fix — 共有検疫への追加が段階 C/D の診断経路まで変える。** `brief.md:17,23` は既存診断経路の受理集合を不変とする一方、`s2-plan.md:43,108` は二重 compile と失敗位置の変更を許している。現行 `silo_policy_coverage.py:279–305` は共有 `quarantine()` の後に同じ本文を構文検査・単独 TU compile するため、追加後は診断経路で compile が二回走る。**影響:** 一回目だけ利用不能・timeout なら、従来の診断 receipt と受理結果が変わる。**代案:** E の新 driver に限って既存の構造・effect 検疫の後に `check_policy_body` を呼ぶ薄い方策専用経路を置き、C/D の `prepare_policy` は維持する。共有関数へ入れるなら、診断経路を二重化しない呼び分けを先に設計する。

2. **must-fix — auditor 型上限の全域拡張は「既存 3 軸の受理集合不変」に反する。** `s2-plan.md:13,49` は `_AUDITOR_VIOLATION_TYPES` を 1–21 から 1–26 へ広げる案だが、現行 `auditor_gate.py:29,54–94` の検査は軸を受け取らない。例えば sort proposal の violation type 22 は現在 schema 拒否、変更後は受理される。**影響:** 既存軸の proposal 受理集合と監査台帳の意味が変わる。**代案:** 型 22–26 の受理を policy proposal にだけ束縛する。既存呼出しの既定上限は 21 に保つ。

3. **must-fix — IR の重複 key 拒否は、計画の interface だけでは発火しない。** `s2-plan.md:27,35` の `parse_policy_ir(document: object)` は、通常の `json.loads` 済み object から `{"kind":"Const","kind":"Reason"}` の重複を復元できない。**影響:** 宣言した閉じた IR 受理契約より広い JSON を通し、IR 候補の identity と検査対象の解釈が入力側でずれる。**代案:** proposal ファイルを読む最外層で `object_pairs_hook` を適用し、全階層の重複を拒否する。IR parser は object の key・型・範囲だけを担当する。

4. **should — reverse 用フィールドと別々の履歴台帳を削る。** `s2-plan.md:31,35,44` は `prior_critic_reverse` を proposal に残しつつ「coder から信用しない」とし、履歴と justification に二つの JSONL を設ける。現行 `p3_s4_loop.py:1377–1403` では空 whiteboard なら予算停止だけで機能する。**影響:** reverse の出所を束縛しなければ停止時点が proposal の値で変わり、二つの記録のずれは次 coder の履歴を変える。**代案:** E は予算停止に絞り、reverse フィールドを proposal から外す。候補本文・結果・justification は一つの campaign 記録に保存し、次 coder へは必要 field だけを明示射影する。reverse が実 critic 結果として必要になった時に接続する。

5. **should — firewall の検査を実際の入力射影に絞る。** `s2-plan.md:33,47,68–71` の禁止ディレクトリ open 監視、他 file 改変時の bytes 同一性、履歴の他 campaign ID 検査は、driver が固定した `projection.json` と自 campaign 記録だけを開く実装なら重複する。`projection.json` の実形は `binary`・`scope`・空の `excluded` である。**影響:** テストだけが増え、実際の coder 入力に禁止値が混じる経路を検出したという過大な主張になり得る。**代案:** 入力構築関数を一つにし、許可する二 field、自系列履歴の射影、justification 不在を出力そのもので検査する。禁止 path を開く設計を追加しない。

6. **should — E 完了条件から計算ノードでの手書き二形 live 走を外す。** `brief.md:30` と `s2-plan.md:50,90–94` は C++・IR 各一回の計測と auditor 実 spawn を提案するが、手順書 `axis-onboarding.md:209–223` は実 LLM の一 iteration E2E を F として別 session に置く。手書き候補の二走は LLM role の実用性を証明しない。**影響:** E の完了と F 開始が不要な node 時間・投入承認待ちに依存する。**代案:** E は両形の preview、検疫、digest 再照合、verify 設定、checkpoint の静的・fixture テストまでとする。計算ノードでの最小 live 走は F の実 LLM×C++ 一 iteration とし、IR 形は同じ経路に不確実性が残る場合に追加する。

7. **nit — 変異候補の一部は kill と数えない。** `s2-plan.md:77–84` の M-E4 は reject subtype の変更であり、`mutation.md:13–17,38–40` の定義では受理集合でなく診断感度の変化に当たる。また M-E1～E3 は、所見 1 の二重検査が残ると後段に覆われ得る。**影響:** 台帳に実効 gate の検出力を過大記録する。**代案:** M-E4 を diagnostic sensitivity pin に分け、M-E1～E3 は実装後に前後の検査を通る単一理由 fixture で再登録する。

**規模の目安:** IR parse は数百行、方策専用 gate と proposal 契約は各数十～百数十行、driver は sort の 895 行より短い数百行を上限目安にできる。膨張要因は二重診断経路、独立した履歴台帳、firewall の path 監視、live 用 job body、既存 helper の再実装である。role 二本と auditor 改訂は D2214 決定 8 が名指ししており、既存登録簿の追随は必要な閉包に限る。runbook は手順書 §3-E が名指しする一 iteration の操作手順に絞る。

## brief と plan の前提の判定

| 前提 | 判定 | 理由 |
|---|---|---|
| P1 | **要修正** | 四段 gate は必要。共有 `quarantine()` への無条件追加と C/D の二重 compile は避ける。 |
| P2 | **要修正** | planner・whiteboard・収束判定を外す判断は妥当。reverse と二台帳は E に不要。 |
| P3 | **要修正** | IR parser と既存 `validate_ir`・renderer への接続は必要。重複 JSON key は最外層 loader で拒否する。serializer は実際の入力・保存用途が決まるまで増やさなくてよい。 |
| P4 | **要修正** | planner なしの二形 schema は必要。`prior_critic_reverse` は外す。 |
| P5 | **要修正** | 二値と射程文だけの射影は必要。禁止 path 監視や別台帳照合まで一般化しない。 |
| P6 | **real** | `loop.py:322–323` の legacy＋性能構成 verify と設計 §3.2 の全候補検証に合う。 |
| P7 | **要修正** | role 二本と auditor 改訂は必要。型 22–26 の受理を policy に限定し、登録簿は実際に変わる pin・adapter だけ追随する。 |
| P8 | **refuted** | E 完了に計算ノードでの手書き二形 live 走は不要。F の実 LLM 一 iteration が実走の出口である。 |

## 再発しうる失敗の型

`failures.md:21` の型タグでは、二重 gate による変異の隠蔽が **[恒真ゲート]**、auditor 型上限の既存 consumer への波及が **[consumer 取り残し]**、入力関数の出力ではなく禁止 file の字面だけを見る試験が **[テスト代表性]** に当たる。`mutation.md` の DW-M01・M03 に従い、診断が赤くなるだけの変異を受理 gate の kill に数えない。

## scope 外の層 (裁定パッケージ候補)

- reverse を使う停止判断と、critic 結果を proposal 外から束縛する仕組み。
- 履歴の出所を一般的に証明する台帳・禁止 path の包括監視。
- 非 LLM IR arm、比較 harness、公平性の機械観測、候補ごとの sanitizer・TRACE 計数。
- E 専用の live job body と手書き二形の性能測定。必要性が F で具体化した時に見積もる。

## 総括

**採否推奨: adopt_with_conditions。** E の核である二形の driver、IR 入力、四段 gate、auditor digest、legacy＋性能構成 verify、role、短い runbook は採用する。

**must-fix:** ① C/D を二重 compile しない経路、② auditor 型 22–26 の policy 限定、③ JSON 重複 key を最外層 loader で拒否する契約。E の live 二形走は完了条件から外す。これは read-only の静的レビューであり、build・pytest・計算実走は行っていない。