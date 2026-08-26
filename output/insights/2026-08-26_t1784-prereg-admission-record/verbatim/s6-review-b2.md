## 総括

最重要 must-fix は、`certified admission ... matching all runtime values` というテスト上の主張と、成果物に残る証拠の不一致である。9 欄はダミー文字列なのに、receipt と CLI 出力には検証した record / 事前登録 commit の参照すら残らない。  
validator の module docstring は repository-local ordering、query 後 model 検査、9 欄の意味非検査を正直に限定しており、この部分は攻撃に耐えた。  
§5 の `syntactically filled` も、実装上は「選定済み token が無い」までしか言えず、既知の過剰拒否修正後には別表記の placeholder を誤受理する。  
併走 wave の部分記入、projection hash の変化、旧 receipt はいずれも拒否側へ倒れる。一方、receipt だけを台帳へ渡して「事前登録済み」と分類する合流は誤受理になる。

## must-fix

### 1. positive test が「全 runtime 値に一致する certified admission」を名乗るが、その証拠は生成されない

- 根拠

  - `orchestrator/tests/test_p3_b4_closed_critic.py:814` の逐語は  
    `test_certified_admission_accepts_committed_record_matching_all_runtime_values`
  - 実際には同 file `:485-493` で、model / prompt / projection 以外の9欄を `closed-critic-fixture-{index}` という無意味な文字列で埋めている。
  - 同 file `:832-833` では production controller の private provider runner を fake runner へ差し替えており、production provider の実測でもない。
  - `orchestrator/campaign/p3_b4_admission_record.py:593-601` では record path/hash/HEAD commit と事前登録 content commit/hash を返すが、`orchestrator/campaign/p3_b4_closed_critic.py:191-231` の receipt はそれらを持たず、`:1546-1550` の CLI 出力にも残らない。
  - `docs/phase3-b4-reflux-ablation-preregistration.md:49` は、実走成果物に発効版 commit hash が無ければ事前登録された実験として扱わない、と要求している。

- 具体的な誤読

  このテスト名と `evidence_class="certified"` を見た後段実装者は、10 欄すべてが runtime と照合され、どの事前登録版を使ったか receipt から監査できると信じる。しかし実際に照合する runtime 値は3値だけで、exact record bytes と content commit の参照は factory 内で消える。

- 成果物影響

  併走 driver が certified receipt だけを台帳へ載せると、発効版 commit の参照を持たない標本が「事前登録済み」受理集合へ入り、レポートの事前登録参照が欠落または推測値になる。

- 修正案

  receipt `/v2` は R1 どおり変えず、provider query 前に別の canonical sidecar を作る。少なくとも `admission_record_repository_path`、record sha256、検証時 HEAD、`preregistration_content_commit`、content sha256、3期待値を持たせ、CLI 出力へ sidecar path/hash を追加する。併走 driver は receipt とこの sidecar の組を必須入力にする。  
  テスト名は例えば `test_repository_checked_record_with_nonempty_section5_and_three_matching_expectations_yields_certified_pair_fixture` とし、fake runner 使用も名前または docstring に明記する。

### 2. `syntactically filled` は実際の「登録済み token 検査」より強い

- 根拠

  - `orchestrator/campaign/p3_b4_admission_record.py:47-49` の逐語は  
    `[admission-preregistration] section 5 rows are not syntactically filled`
  - 同 file `:429` の関数名は `assert_section5_rows_are_syntactically_filled`、`:436` は  
    `Check only the fixed table shape, placeholders, and three exact values.`
  - 実際の placeholder 判定は `:72-76` の有限集合を `:474-480` で検索するだけである。既知の `N/?A` 過剰一致を直した後でも、`pending`、`未確定`、`<!-- -->`、`&nbsp;` などは値として通る。

- 具体的な誤読

  呼出側は「値セルが構文上埋まり、placeholder が無い」と信じるが、保証できるのは source cell が空文字ではなく、登録済みの数 token に一致しないことだけである。

- 成果物影響

  既知の過剰拒否を修正した後、実質未記入の10欄を持つ record が受理され、production factory が certified receipt を生成するため、certified 受理集合が不当に広がる。

- 修正案

  §0 で機械上の未記入 sentinel を exact に定義し、関数名を `assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel` 相当へ狭める。エラーにも「型・意味・render 後の非空は検査しない」と入れる。HTML comment、HTML 空白、Unicode format-only cell の拒否テストも追加する。

## nit / backlog

- `VerifiedB4AdmissionRecord` と `verified_admission` は、model がまだ query 後検査待ちでも `verified` と呼ぶ。class docstring `:85` は bytes 由来と限定しているため must-fix にはしないが、`RepositoryCheckedB4AdmissionRecord` の方が誤読しにくい。
- `orchestrator/campaign/p3_b4_closed_critic.py:655-658` の `certified controllers require one verified admission record` も、repository 検査済みと runtime 3値照合済みを分けた文言が望ましい。
- 語彙照合では、`complete` は保証語として新規使用なし、`bound` は実際の hash/commit/pair 照合に限定、`proved/proves` は module docstring の repository-local theorem と non-guarantee に限定されていた。
- 発効、driver 支配点、proposal 因果束縛、外部 ledger、query 前 model attestation、active record 単一性を実装済みと称する記述は見つからなかった。

## 併走 wave との合流で壊れる組み合わせ

|組み合わせ|実際の挙動|判定|
|---|---|---|
|§5 の一部だけ記入し、残りを `未記入` のまま commit|`:474-480` で provider 作成前に拒否|拒否、fail-closed、許容|
|10欄を埋めるが3期待値を通常の説明書式で記入|`:481-498` の exact grammar に合わず拒否|拒否、fail-closed。併走 wave に grammar の共有が必要|
|10欄と exact grammar を正しく記入|既知の `N/?A` 部分一致が残る現状では `snapshot` に反応して拒否。修正後は受理|現状は過剰拒否。修正後の受理自体は R3 の範囲内|
|併走 wave が `main` を編集し、`--admission-record` または factory forwarding を落とす|既定 factory なら argparse または必須引数 `TypeError`|拒否、fail-closed|
|merge 解決で `assert_b4_certified_arm_pair` を旧 `assert_b4_arm_pair` へ戻す|`test-only` pair が正式 CLI を通る|誤受理、must-fix|
|admission 実装前の `/v2` certified receipt を新 driver へ渡す|validator module が projection closure に追加され、reader `:1376-1377` が現在 bytes と照合するため拒否|拒否、fail-closed|
|併走 wave が `main`、reader、receipt class を変更した後、古い projection 値の record を使う|factory `:967-975` で query 前に拒否|拒否、fail-closed。合流版で hash と record を再生成する|
|新しい certified receipt だけを driver 台帳へ渡し、事前登録済みと分類|receipt に exact record/content commit の参照が無い|誤受理。must-fix 1 の sidecar が必要|

## 攻撃できなかった面

- exact record bytes が検証時 HEAD に存在し、その検証が provider query より先である repository-local ordering は、静的経路上で守られていた。
- 別経路での先見、Git timestamp の限界、query 後 model 検査と再試行攻撃は module docstring `:4-20` に明記されていた。
- `main` は `:1525` で段4 driver を配線しないと明記しており、支配点化を実装済みとは称していない。
- pytest は指示どおり実走していない。親既知の2件の赤は再発見扱いにしていない。
- 併走 wave は段1 brief のみが射影されており、実装済み branch の具体的な merge diff までは検査できていない。