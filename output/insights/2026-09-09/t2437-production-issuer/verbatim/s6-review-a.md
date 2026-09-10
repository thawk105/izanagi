## 所見

### 1. 認証されていない receipt を発行根拠として受理し、中心正例もその穴を利用している

- 重大度: **blocker**
- 根拠:
  - `orchestrator/campaign/loop.py:184-187` — 実経路は `attestation_mode == "required"` の場合だけ receipt を生成する。
  - `orchestrator/tests/test_campaign.py:114-118`、`orchestrator/campaign/env_contract.py:292-300` — 中心正例が使う `linux-baremetal` は `attestation_mode="none"`。
  - `orchestrator/tests/test_reflux_campaign_issuer.py:311-324,433-439` — fixture が `_authorize_measurement()` の返した `None` を `build_receipt()` 製の receipt へ差し替える。
  - `orchestrator/campaign/execution_guard.py:204-222` — `build_receipt()` は実関数だが、required attestation の比較を行わない v1 receipt の単純生成器。
  - `orchestrator/campaign/reflux_result_evidence.py:1210-1211,1298-1317` — issuer は非 `None`、dict、`contract_sha256` 一致しか検査せず、schema、attestation mode、`receipt_matches_contract()` を検査しない。
  - `orchestrator/tests/test_reflux_result_evidence.py:354-359,1096-1104` —任意の fixture schema と自己申告 attestation を持つ dict でも発行成功としている。
- 成果物影響: 自作した receipt の digest を execution provenance に載せた record が発行受理集合へ入り、対応する台帳束縛があれば certified 選択やレポートが未認証実行を参照できる。
- 反証可能な主張: 他の入力が妥当なら、`{"contract_sha256": contract_sha256}` を含む任意の dict は `reflux_result_evidence.py:1298-1317` を通り、record 発行を妨げる receipt 検査は後段にも存在しない。
- 提案する最小の直し方: required-mode の hash-bound calibration と照合済みの receipt だけを受理し、mode-none/v1 receipt を拒否する。中心正例から `_install_fixture_receipt_authorization()` を除き、mode-none は file 0 件で拒否する負例にする。発行正例は実 required-attestation 経路か、偽造不能な issued receipt capability を使う。

A4 への回答: 合成 receipt は実 `build_receipt()` を通るが、本物と同じ意味ではない。実 `_authorize_measurement()` が mode-none で返す値は `None` であり、fixture は裁定された拒否 gate を無効化している。

### 2. originless の WAL 不変検査が変更後実装どうしの自己比較になっている

- 重大度: **must-fix**
- 根拠: `orchestrator/tests/test_reflux_campaign_issuer.py:424-429,525-545`
- 成果物影響: context の有無にかかわらず追加される WAL frame、stage、payload key が入っても緑のままとなり、originless WAL digest、consumer の受理集合、レポート参照が変わる回帰を受理できる。
- 反証可能な主張: context 分岐より前で両 campaign に同じ WAL frameまたは payload key を追加しても、`:535` の集合等値と `:537-545` の result-evidence 不在検査は成立する。
- 提案する最小の直し方: originless の file集合、stage集合、payload key集合を、変更前経路から固定した非揮発 baselineまたは具体的な期待集合と比較する。context付き runを比較対象にしない。

### 3. eval-exception の issuer 判断は実装されたが、非回帰テストがその経路を通っていない

- 重大度: **must-fix**
- 根拠:
  - 実装上の発行点は `orchestrator/campaign/loop.py:816-847`。
  - `orchestrator/tests/test_reflux_campaign_issuer.py:723-793` の eval-exception test は `result_evidence_context=None` を渡すため、`loop.py:342-343` で issuer が即時 no-op になる。
  - identity-error testも `test_reflux_campaign_issuer.py:695-719` では例外と WALだけを検査し、result-evidence fileが 0 件であることを検査しない。
  - terminal-skip 再走も `test_reflux_campaign_issuer.py:509-518` で例外だけを検査し、発行失敗前後の file集合を比較しない。
- 成果物影響: eval-exceptionだけ issuer を迂回する変異が入ると、campaign は aborted summary を返す一方で record が欠け、台帳 memberとレポート参照が欠測する。
- 反証可能な主張: `loop.py:839` の呼び出しを「`build_attempt_id` が非空のときだけ」に変えても、現在の中心正例と originless eval-exception testは通る。
- 提案する最小の直し方: context付き eval-exceptionを、attempt IDあり・なしの両形で駆動し、`ResultEvidenceIssuanceRefused` の伝播と result-evidence file 0 件を検査する。identity-errorとterminal-skipも拒否前後の evidence file集合を比較する。

## 恒真な保証 (発火しない検査)

- `derive_physical_result()` の mixed-attempt拒否 `orchestrator/campaign/reflux_result_evidence.py:660-661` は、今回の production producer経路では `wal.ordered_attempt_frames()` が同じ IDだけを選ぶ `orchestrator/campaign/wal.py:1701-1708` ため発火しない。公開 derive APIには意味があるが、issuer配線の追加防護には数えられない。
- `anomaly_count == len(anomalies)` など `result_to_dict()` が生成する値の検査は、コードコメントどおり drift assertionであり、実防護は `total_cycles` と単一 anomaly の検査 `reflux_result_evidence.py:615-626`。ここに新たな反例はない。

A5 の4発行点:

- identity確定不能かつ既存terminal: `loop.py:664-674`。helperは空文字を返しうる。
- 新規identity-error: `loop.py:677,692-705`。現実装では `secrets.token_hex(16)` が渡るため空文字経路はない。
- 通常terminal skip: `loop.py:713-721`。helperは空文字を返しうる。
- 通常結果/eval-exception: `loop.py:816-847`。eval-exceptionでは空文字が実際に渡りうる。

有効な非 `None` receiptがあれば、空文字は `reflux_result_evidence.py:1252-1254` から `_ordered_attempt_materials()` の `:444-445` に入り、確かに `ResultEvidenceIssuanceRefused` になる。ただし実 mode-none 経路では `:1210-1211` の receipt不在が先に拒否するため、「空 attempt ID gateが拒否した」という帰属は過剰決定である。いずれの場合も発行呼び出しは `try` の外にあり、例外は握り潰されない。

## テストを甘くした箇所

- A4の中心正例: `test_reflux_campaign_issuer.py:311-324,433-439`。mode-none拒否をreceipt合成で迂回している。
- producer正例: `test_reflux_result_evidence.py:354-359,1096-1104`。任意schemaの自己申告receiptを正例にしている。
- originless不変検査: `test_reflux_campaign_issuer.py:535-545`。変更後実装どうしの比較である。
- identity-errorとterminal-skipの拒否検査: `test_reflux_campaign_issuer.py:509-518,695-719`。例外だけで、発行 artifactが増えていないことを検査しない。
- eval-exception: `test_reflux_campaign_issuer.py:723-793`。context未指定なのでissuer判断自体を検査していない。

現行hashのfixtureへの差し込み、時刻・乱数・working-tree hash・campaign lock digestを期待値へ焼き込んだ新規テストは見つからなかった。

## 段 4 裁定との食い違い

- blocker所見1が明確な食い違い。裁定の「mode-noneではreceipt不在として拒否」「唯一のstubはtrace生成」に対し、中心正例がmode-none receiptを追加合成して発行している。
- identity-error、identity-skipped、通常terminal skip、eval-exceptionの4箇所にはissuer呼び出しが存在し、例外も伝播するため、実装コード上の素通りはない。ただしeval-exceptionの裁定命題はテストされていない。
- remote fan-outは `orchestrator/campaign/pipeline.py:850-875,1000-1006,1031-1047` で一貫して `verify_result=None`。wire payloadからtyped値を再構成する経路は見つからなかった。
- 複数witness classから1件を選ぶ分岐、3方向導出の緩和、live WAL参照、originlessでのresult-evidence発行は見つからなかった。

## 裁定パッケージ候補 (scope 外の real な所見)

新規候補なし。正本に既出のS4 production呼び手、completeness origin分岐、材料レポートrenderer、terminal後のtombstone、mode-none receipt契約は再指摘していない。

## 総括

静的レビュー結果は **blocker 1件、must-fix 2件**。最大の問題は、認証済みreceiptではなく任意dictの存在だけで発行でき、中心正例もmode-none拒否を迂回している点である。

create-onlyの `O_EXCL|O_NOFOLLOW`、file/parent fsync、read-back、`FileExistsError`失敗扱い、immutable prefix snapshot、元WAL offset保持、issuer失敗の伝播には反例なし。pytestその他のテストは実行していない。