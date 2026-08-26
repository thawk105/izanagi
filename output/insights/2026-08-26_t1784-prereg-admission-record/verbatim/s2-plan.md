## 総括

採るべき形は、canonical JSON の admission record を production factory の必須入力とし、その record 自身と事前登録文書の双方が Git commit に束縛されていることを role query 前に検証する形である。  
§5 は controller 本体ではなく新設 validator で限定的に構文解析し、10 欄の非空・非 `未記入` と、3 期待値の記載一致を fail-closed で確認する。  
projection は pair 作成時、prompt は provider 構築時、model は応答受理直後に照合し、成功 receipt に admission の commit と hash を残す。  
最も危険な残存穴は、別経路の先行実走で結果を知った後に record を commit し、新しい実走を始める攻撃をローカル Git だけでは識別できないことである。

## 変更面 (file:line)

| file:line | 計画する変更 |
|---|---|
| `orchestrator/campaign/p3_b4_admission_record.py` 新設 | exact schema、canonical bytes、§5 parser、Git commit・blob・ancestry 検証、`B4AdmissionRecordError`、不変な verified dataclass を実装する。production の repository root は呼び手が固定する。 |
| `orchestrator/tests/test_p3_b4_admission_record.py` 新設 | canonical schema、duplicate key、§5 完全性、record 自身の commit 束縛、文書 commit/blob/ancestry を一時 Git repo で検査する。 |
| `orchestrator/campaign/p3_b4_closed_critic.py:39-82` | validator を import し、その Python module の path 定数を追加する。 |
| `p3_b4_closed_critic.py:182-223` | receipt に admission record と事前登録文書の path・commit・SHA-256 を追加する。test-only は全 admission field を `None` に固定する。成功 receipt schema は `/v3` に上げる。 |
| `p3_b4_closed_critic.py:501-537` | validator の Python code を projection closure に加える。入力 JSON record 自身は絶対に加えない。`test_m15_m20...` の期待 entry も追随させる。 |
| `p3_b4_closed_critic.py:619-660` | controller に verified admission を渡す。`certified` と admission 有り、`test-only` と admission 無しを双方向の型不変条件にし、provider 作成直後に prompt hash を照合する。 |
| `p3_b4_closed_critic.py:668-814` | invoke 前に record・HEAD 束縛を再確認し、start receipt に admission 情報を記録する。provider 応答後、decision の parse と成功 receipt 構築より先に model を照合する。 |
| `p3_b4_closed_critic.py:904-926` | `_prepare_b4_closed_critic_pair` に verified admission を渡し、925 行相当で得る closure hash と期待値を比較する。production では closure の全 repository entry が record を含む commit の tree と一致することも確認する。 |
| `p3_b4_closed_critic.py:944-1002` | `create_b4_closed_critic_pair(*, admission_record_path: Path, ...)` を既定値なしの必須 keyword にする。record 検証は executable 探索、artifact directory 作成、provider 作成より先に行う。 |
| `p3_b4_closed_critic.py:1005-1056` | test-only factory は公開引数を増やさず admission を `None` に固定する。production と共通の private controller invariant は弱めない。 |
| `p3_b4_closed_critic.py:1059-1420` | start/success receipt の `/v3` exact schema、admission field の型、Git blob の再読、record 期待値と receipt 実測値の一致、両 arm の同一 record 使用を再検証する。 |
| `p3_b4_closed_critic.py:1443-1476` | 最小変更だけ行う。必須 `--admission-record` を1個追加し、factory に渡し、`B4AdmissionRecordError` を既存失敗処理へ加える。CLI 出力 schema と driver 非配線は変えない。 |
| `orchestrator/tests/test_p3_b4_closed_critic.py:298-326,466-490,841-892,1092-1115,1397-1478` | production factory helper、negative seam、projection entry、CLI argv を追随させ、新 admission gate の正負例を追加する。 |
| `orchestrator/campaign/claude_projected_provider.py:162-169,317-353` | 変更しない。169 行の実際の effective prompt hash と、353 行の実測 model slug を比較元として使う。 |

入力 JSON record は projection closure に入れない。validator の Python code は gate の意味を決める実装なので closure に入れる。この区別により自己参照を避けつつ、validator の後付け改変も projection mismatch に落とせる。

指定された事前登録文書、`p3_s4_loop*`、`test_p3_s4_loop.py`、runbook、critic role、main experiment 文書は変更しない。

## record schema

schema version は `p3-b4-prerun-admission/v1` とする。`p3-b4-closed-critic-receipt/v2` とも、一般名の `projection_sha256` とも衝突しない。

```json
{
  "schema_version": "p3-b4-prerun-admission/v1",
  "preregistration_binding": {
    "repository_path": "docs/phase3-b4-reflux-ablation-preregistration.md",
    "content_commit": "40-digit-lowercase-git-sha1",
    "content_sha256": "64-digit-lowercase-sha256"
  },
  "closed_critic_expectations": {
    "expected_claude_model_snapshot": "claude-opus-...",
    "expected_effective_critic_prompt_sha256": "64-digit-lowercase-sha256",
    "expected_closed_critic_projection_closure_sha256": "64-digit-lowercase-sha256"
  }
}
```

canonical bytes は次の一意な形にする。

- UTF-8、BOM なし、末尾改行なし。
- `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)` の bytes。
- duplicate key、未知 key、欠落 key、`bool` を `int` として扱う入力を拒否する。
- hash は小文字 hexadecimal 64 桁、commit はこの repository の object format に合わせて小文字 40 桁に固定する。
- model は `claude-opus-` で始まる閉じた ASCII slug とする。
- 入力 bytes を parse 後に再 canonicalize し、元 bytes と完全一致しなければ拒否する。

record JSON 自身には、それを含む commit を書かない。これは自己参照になるためである。代わりに loader が実行時の `HEAD` を一度解決し、次を verified dataclass に追加する。

- `admission_record_repository_path`
- `admission_record_sha256`
- `admission_record_commit`: exact record bytes を tree に持つ、検証時の `HEAD`
- record 内の全宣言値

Git 検査は次を行う。

1. record path が repository 内の regular file で、symlink や `.git` 経由でない。
2. `HEAD^{commit}` の tree に同じ repository-relative path と exact bytes がある。untracked、staged-only、working-tree 改変はいずれも拒否する。
3. `content_commit` が exact commit object で、record を含む commit の祖先である。shallow history、graft、replace ref は拒否する。
4. `content_commit` の固定文書 path にある blob bytes の SHA-256 が `content_sha256` と一致する。
5. その blob の `## 5.` から `### 5.1` の間に、現在の10行ラベルが重複なく全て存在し、値が空でも `未記入` を含む値でもない。
6. `model snapshot / prompt hash / projection hash` 行から、model slug 1個と SHA-256 2個を抽出し、record の3期待値と一致させる。曖昧な複数候補や未知の表構造は拒否する。

書式依存は意図的に fail-closed とする。併走 wave が行ラベルや表構造まで変えた場合は validator を同期してから record を作り、推測による fallback は設けない。

## 照合の設計

| 値 | 位置と比較対象 | 失敗 |
|---|---|---|
| closed critic projection closure | `_prepare_b4_closed_critic_pair` の現 925 行で `projection_closure_manifest()` を一度 canonicalizeし、その SHA-256 と `expected_closed_critic_projection_closure_sha256` を比較する。さらに manifest 中の repository file 全てが `admission_record_commit` の tree bytes と一致することを確認する。`invoke` の現 695-697 行でも再計算し、pair 作成後の drift を拒否する。 | 期待値不一致は `B4AdmissionRecordError`、固定署名 `[admission-mismatch] expected_closed_critic_projection_closure_sha256`。pair 作成後 drift は既存の `B4ReceiptError("projection closure changed after pair creation")` を維持する。 |
| effective critic prompt | `B4ClosedCriticController.__init__` の現 643-653 行で provider を作成した直後、`provider.effective_prompt_sha256`、つまり provider 169 行の read-once 実測値と record を比較する。on/off の各 provider で照合し、role query 前に停止する。 | `B4AdmissionRecordError`、固定署名 `[admission-mismatch] expected_effective_critic_prompt_sha256`。不一致時は provider を close してから再送出する。 |
| Claude model snapshot | `invoke` の現 744-759 行で provider が envelope と `modelUsage` を検証して返した直後、`response.provenance["model"]` と record を比較する。現 748 行の decision parse と、779-786 行の成功 receipt 構築より前に置く。両 arm で個別に照合する。 | `B4AdmissionRecordError`、固定署名 `[admission-mismatch] expected_claude_model_snapshot`。query は既に1回消費されるが、decision は返さず、成功 receipt も作らず、既存の failure terminal receipt に遷移する。 |

record 不在・束縛不能の署名は以下に固定する。

- path 不在または非 regular: `[admission-record] record is unavailable`
- HEAD tree と不一致: `[admission-record] record is not committed at execution HEAD`
- 文書 commit/blob/ancestry 不成立: `[admission-preregistration] document binding is not verifiable`
- §5 不完全または曖昧: `[admission-preregistration] section 5 is incomplete or ambiguous`

成功 receipt `/v3` と start receipt `/v3` には、record path/hash/commit と文書 path/hash/commit を含める。`_read_verified_terminal_receipt` は commit tree から record を再読し、record の期待値と receipt の実測3値も再比較する。両 arm の common field に admission binding を加え、異なる record の混在を拒否する。

## 既存呼び手の追随

repository 全体で production factory の直接 call expression は3箇所だけである。

| 現行行 | 現状と追随 |
|---|---|
| `test_p3_b4_closed_critic.py:317` | 正常な certified construction。必須引数欠落で実際に壊れる。committed record fixture または verified loader fixture を渡す。 |
| `test_p3_b4_closed_critic.py:476` | `runner=` 注入を拒否する負例。現状でも TypeError を期待するため結果だけなら落ち続けるが、新 gate の欠落と混同しないよう有効な `admission_record_path` も渡す。 |
| `test_p3_b4_closed_critic.py:1101` | `executable=` 注入を拒否する負例。476 行と同様に record 引数を追随させ、拒否軸を executable だけに保つ。 |

CLI 必須化により壊れる `main` の既存呼び手は2箇所である。

- `test_p3_b4_closed_critic.py:1438`: 成功 argv に `--admission-record` を追加し、fake factory が受け取った path も assert する。
- `test_p3_b4_closed_critic.py:1466`: factory failure の argv にも同 option を追加する。

実装内の caller は `p3_b4_closed_critic.py:1456` の1箇所で、`admission_record_path=args.admission_record` を追加する。

さらに、validator code を projection closure に含めるため、`test_p3_b4_closed_critic.py:841-892` の exact manifest 期待集合が壊れる。新 module の entry を1個追加する。`inspect.signature` の現 468、1094 行はそれ自体は壊れないが、必須 keyword に既定値が無いことを明示的に assert する。

`create_b4_closed_critic_pair_for_test` の既存呼び手は変更しない。

## 塞げない穴

この gate が証明できるのは、「この certified invocation の provider query より前に、検証した exact record bytes が Git commit の tree に存在した」という順序である。必須 factory 引数、query 前の Git 検証、start receipt の record commitment により、同じ invocation の終了後に record を差し替えて成功扱いにすることは拒否できる。

一方、次は検出できない。

- 別 CLI、test-only 経路、手動 API、過去の類似実験などから結果を先に知り、その後 record を作って commit してから新しい certified invocation を始める。
- Git の author/committer timestamp を根拠に、外部実走との絶対的な時系列を証明する。
- §5 の非 placeholder 値が、意味的にも正しい floor、予算、母集合であることを証明する。
- same-process Python が module global や test seam を改変する攻撃。これは既存の trust non-guarantee の範囲である。

最初の穴を塞ぐには、実走開始を発行する外部 append-only ledger、信頼できる timestamp、または一度だけ消費できる署名済み admission token が必要であり、本 wave の repository-local controller だけでは達成できない。

## テスト設計

必須の正例1件と、異なる拒否方向の負例2件は次の組にする。

| 種別 | test 名 | 固定する性質 |
|---|---|---|
| 正例 | `test_certified_admission_accepts_committed_record_matching_all_runtime_values` | §5 の10欄が埋まった文書と canonical record を commit し、projection、prompt、fake envelope の `claude-opus-5` を一致させる。両 arm が成功し、start/success receipt に同じ record commit/hash が入り、再検証も通る。 |
| 負例: 期待値不一致 | `test_certified_admission_rejects_each_projection_prompt_and_model_expectation_mismatch` | fresh fixture ごとに3 subcase を走らせる。projection mismatch は provider 作成前で query 0回、prompt mismatch は provider 作成後だが query 0回、model mismatch は query 1回後に failure terminal receipt となり success receipt と decision return が無いことを固定する。 |
| 負例: record 不在または束縛不能 | `test_certified_admission_rejects_missing_untracked_or_prereg_unbound_record_before_query` | Python の必須 keyword 欠落、CLI option 欠落、untracked record、HEAD と異なる record bytes、非祖先の文書 commit、blob hash 不一致を subcase 化し、全て query 0回で拒否する。 |

補助テストも追加する。

- `test_admission_record_requires_canonical_exact_schema_and_complete_section5`
- `test_admission_record_section5_expectation_row_binds_all_three_values`
- `test_test_only_factory_has_no_admission_input_and_cannot_emit_certified_binding`
- `test_projection_manifest_includes_admission_validator_but_excludes_record_json`
- `test_receipt_revalidation_rejects_admission_record_or_commit_tamper`

P4 の固定として、test-only receipt の admission field は全て `None`、certified receipt は全て非 `None` とし、一部だけの状態も evidence class の書換えも拒否する。

## 親の provisional 裁定への評価

| 裁定 | 評価 | 根拠 |
|---|---|---|
| P1 | 支持 | projection と prompt は repository bytes と固定 contract から事前計算できる。model は provider の `modelUsage` まで観測不能なので、事前宣言と応答直後の照合が正しい。ただし model mismatch は query 自体を未実行にはできず、成功標本化を止める gate である。 |
| P2 | 修正 | path、blob SHA-256、commit、ancestry の束縛だけでは、§5 が全て `未記入` の文書も通る。10行ラベルの限定 parser を validator に置き、非 placeholder と3期待値の一致を必須にする。書式変更は fail-closed とし、文書を推測して受理しない。 |
| P3 | 支持 | production factory の既定値なし必須 keyword と、CLI の必須 option が必要である。record の検証は artifact 作成や executable 探索より先に置く。`main` は option、引渡し、例外 catch 以外を変えない。 |
| P4 | 修正 | test-only factory に record は要求しない。ただし controller 内で `certified` と verified admission の存在を双方向に固定し、test-only receipt の admission field を全て `None` にする。既存の promotion 拒否を維持し、official consumer が evidence class を無視する危険は別途残す。 |
| P5 | 支持 | 不一致は全て例外で停止し、warning、environment variable、CLI flag、既定値による bypass は設けない。shell CLI からは `pair_factory` を選べず、Python 内の差替えは既存の same-process trust non-guarantee として扱う。 |