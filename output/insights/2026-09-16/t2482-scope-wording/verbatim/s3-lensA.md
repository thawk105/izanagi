## 経路分類表

**計画は文言の修正が必要です。また、親の「受理への影響経路は scope の直接照合だけ」という一般化は成立しません。** ファイル全体の hash を介する receipt 照合もあります。ただし、今回の変更で受理から拒否へ変わる記録実物は確認していません。

以下、`C/` は `orchestrator/campaign/`、`P/` は `tools/plotting/`。分類は **(a) 説明として投影、(b) 一致照合、(c) hash preimage**。複数に該当する経路は併記します。

| 経路・根拠 file:line | 分類 | 判定への関係 |
|---|---|---|
| `C/artifact_admission.py:183`、`:187`、`:189` | a・b | 現行 scope を既定値に設定し、明示値も現行定数と完全一致させる。保存済み report の decoder ではない。 |
| 同 `:220`、`:227`、`:233` | a・b | 歴史 exact-24 は `PRE_T733_*` と照合。現行定数変更の影響なし。 |
| 同 `:248`、`:254` | a | 拒否例外の属性・message に投影。 |
| `C/s8b_oracle_report.py:582`、`:596`、`:616` | a | 拒否・取得不能・取得成功の各 epoch を observations へ投影。 |
| `C/layer3_report.py:332` | a → b | JSON に投影。後述の completeness が再検証する。 |
| `C/s1_report.py:122`、`:132` | a | 成功・拒否の epoch を投影。 |
| `C/p2_2_report.py:107` | a | scope を report に投影。 |
| `C/backoff_sweep_report.py:103`、`:169` | a | JSON・Markdown に投影。 |
| `C/s6_sort_sweep.py:613`、`C/s8a_trigger_sweep.py:718` | a | Markdown に投影。 |
| `orchestrator/critic/digest.py:1261` | a | critic 材料へ投影。 |
| `P/plot_backoff.py:358`、`:615` | a | provenance に保持。現行定数との照合なし。 |
| `P/plot_s1_9pair.py:537`、`:1511` | a | provenance に保持。現行定数との照合なし。 |
| `C/autonomous_trial_completeness.py:4732`、`:4756` | a・b | validator の epoch と保存済み epoch を canonical bytes で比較。 |
| 同 `:4696`、`:5019` | b | epoch を保持した report 全体の比較にも scope が入る。専用 epoch 検査とは別の照合箇所。 |
| `C/layer3_schema.json:330`、`C/s8b_oracle_artifacts.py:181` | a相当※ | 非空文字列という形の検査。現行 scope との一致検査ではない。 |
| `C/s8b_oracle_judge.py:480`、`:489` | a相当※ | 上記検査後、state・eligible・campaign 集合を使う。scope の文面で選択しない。 |
| `C/artifact_admission.py:1249` → `:329` | **c** | **当該ファイル全 bytes** の SHA-256 が admission receipt の `validator.sha256` になる。 |
| `C/autonomous_trial_completeness.py:4443`、`:4783`、`:4974` | **b（上記 c の下流）** | receipt 全体を現行 validator の再生成値と比較。scope 欄がなくてもファイル変更の影響を受ける。 |
| `C/layer3_report.py:975` | b（同上） | 同一生成処理内の historical／certified decision を比較。通常は双方とも新 hash となる。 |
| `C/campaign_lock.py:57` → `C/contract_loader_binding.py:531` → `C/artifact_admission.py:1061` | **c** | source blob hash を介して新規 lock の E1 に入る。既存 map からの E1 再導出値は変わらない。 |
| `C/p3_b4_closed_critic.py:636`、`:668`、`:681`、`:1679` | **c・b** | source bytes を projection hash に含め、保存 receipt の hash と現行値を照合。 |
| `C/p3_b4_raw_record_producer.py:992`、`:1019`、`:1043` | **c** | 同じ closure を snapshot から hash 化し、receipt 検証に使用。 |
| `C/p3_autonomous_workload_trial.py:3131` → `C/trial_registry.py:5056` | c（間接） | admission receipt を含む trial report の bytes が report hash に入る。再生成時の参照値は変わりうる。 |

※非空検査は厳密には三分類の「出力だけ」に収まりません。文面の意味・現行定数との一致を判定しない経路として区別しました。

親の producer 11 箇所の列挙は一致しました。しかし、その列挙だけでは、receipt・projection hash・report 全体比較への間接流入を覆えません。

## 所見

1. **must-fix — 非 import 委譲の一括除外が現物と矛盾する。**
   計画は「subprocess … を含む非 import 委譲は本 map の外」を維持しています。しかし `C/campaign_lock.py:112` は `verify_fanout_worker.py` を収載し、`C/pipeline.py:836` はこれを subprocess 経由で起動します。親 brief の追加実測は正しく、段2計画に未反映です。除外文を「明示収載した委譲先を除く」等に限定し、非 import 委譲全体の網羅を主張しない形に直す必要があります。24／36／2 の内訳を残すこと自体は必須ではありません。
   **成果物影響:** 放置すると全 producer の材料レポートが、実際には束縛する worker の source bytes まで対象外と説明し続ける。

2. **should-fix — 「受理に関わる経路は `_require_compatible_layer3_epoch` だけ」という説明を修正する。**
   `C/artifact_admission.py:1249` の source hash は `:329` の receipt に入り、`C/autonomous_trial_completeness.py:4783` と `:4443` が現行再生成値との一致を要求します。専用 scope 検査より先に receipt 比較で拒否される経路もあります（`:4974` → `:4999`）。計画の差分を拡大する必要はありませんが、「述語を編集しない」と「述語への入力値が変わらない」を分けて記録すべきです。
   **成果物影響:** 旧 validator hash を保持する記録は、scope 欄の有無にかかわらず completeness の再検証結果が変わりうる。今回該当する受理済み実物は未確認。

3. **should-fix — 「bytes pin なし」は事前登録欄の確認だけでは支えられない。**
   `C/p3_b4_closed_critic.py:636`、`:668` が当該 source bytes を束縛し、`:1679` は保存 receipt の projection hash と現行値を比較します。事前登録の hash 欄が未記入でも、この動的 receipt 検証経路は存在します。親の結論は「確認した事前登録欄に有効な固定値なし」と限定すべきです。
   **成果物影響:** 旧 bytes で発行された B-4 receipt が存在すれば、変更後の現行 bytes による検証で拒否される。該当実物の存在は確認していない。

4. **should-fix — E1 不変の条件を親 brief にも反映する。**
   `C/campaign_lock.py:57`、`C/artifact_admission.py:1061` により、新規 lock に変更後 blob を収録すれば E1 は変わります。段2計画が指摘した「同じ記録済み map に対する再導出値は不変」が正確です。
   **成果物影響:** 新規 lock・材料レポートの E1 参照値が変わる。既存 lock の E1 は変わらない。

5. **nit — 同じ scope 文面を、歴史／現行 grammar の判定上の曖昧さと扱わない。**
   現行 `C/artifact_admission.py:276`、`:1067` は型と path tuple を使用します。並行 worktree の同ファイル `:292`、`:299` は歴史型の内部で exact-24／exact-62 の固定 scope を区別し、`:1099` は exact-62 tuple から診断を生成します。現行型との文面重複だけで grammar が混同される経路は見つかりませんでした。
   **成果物影響:** 文面上の誤説明はあるが、同文面だけを原因とする受理集合・参照の変化は確認できないため nit。

## 親 brief・実測の点検結果

- **63／162／99 は射影 JSON と整合します。** 配列長、`discovered − enrolled = unenrolled`、収載集合の包含、現行 tuple との順序込み一致を独立に確認しました。探索 probe 自体は再実行していません。
- verifier の3 path は発見集合外です。worker は収載され、JSON の `edges` に worker への流入はありません。親の subprocess 委譲に関する追加実測と整合します。
- **P1 は妥当です。** 数値を日付・commit 付き測定事実に限定します。ただし `curated exact 63 path` は現行 tuple の説明なので、将来の変更まで保証するものではありません。
- **P2 は保証を狭める説明です。** 段2案の「発行器全体を網羅する集合ではない」は妥当です。JSON では `s8b_oracle_report.py` が集合外、`autonomous_trial_completeness.py` は集合内なので、「発行器すべてが集合外」としてはいけません。
- **repo 1 本という数は検索範囲付きです。** `output/` の insight 外では親の1本を確認しました。一方、`docs/paper-story/figures/` の provenance JSON 3本にも scope が残っています。これらの production 読取経路に現行 scope との一致照合は見つからず、件数の追加だけで回帰とは判定しません。
- **外部 root 23 directory の0件は独立再確認していません。** 射影 evidence には root 一覧・個別結果がなく、本レビューでは親の報告として扱います。scope 検索0件から、scope を保持しない receipt の hash 影響0件は導けません。
- **歴史 exact-24 の判定は維持されます。** `PRE_T733_*`、記録 tuple、歴史型の検査は変更対象外です。並行 exact-62 の固定定数も現行定数から独立しており、両変更後の文字列同一性による判定の曖昧さは確認しませんでした。
- **規律2を緩める変更は計画にありません。** 規律7についても、歴史 raw 読取は `C/artifact_admission.py:1109` で current closure 検査を回避します。ただし receipt／completeness の現行値照合は別経路なので、「記録を上書きしない」だけで全記録の再検証互換性まで証明したことにはなりません。

## scope 外候補

- **should-fix・scope 外候補:** completeness の保存済み admission receipt と現行 validator hash の照合、および B-4 receipt の現行 projection hash 照合に関する歴史互換性。根拠は `C/autonomous_trial_completeness.py:4783`、`C/p3_b4_closed_critic.py:1679`。
  **成果物影響:** 該当する既存記録があれば、説明文だけの source 変更でも再検証時の受理が変わりうる。

これは既存契約の問題であり、本 wave で照合を削除・緩和したり、新しい gate・台帳・互換機構を実装したりする提案ではありません。

## 総括

**非 import 委譲の除外文は実装前に修正が必要です。** P1・P2 と数値更新は妥当で、被覆拡大や歴史 grammar の変更は不要です。

親の安全性説明は、直接 scope 照合に加えて **validator receipt hash・B-4 projection hash・report 全体比較**を含め、確認した実物の範囲に限定してください。静的点検のみを実施し、書込み・pytest 実行は行っていません。