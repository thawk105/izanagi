## 現行の受理・拒否挙動

- `tools/acceptance_receipt_signature.py:46-48,127-129,168-199`
  - `project_v5_receipt()` は `lease_generation` に `[0-9a-f]{64}` と完全一致する文字列だけを受理する。
  - 大文字、63/65桁、非16進文字、空文字、`None`、`"not-acquired"` 等は `ReceiptSignatureError("invalid lease_generation")` で拒否する。
  - 64桁小文字16進であれば、実際の lease 取得との対応を検査せず、そのまま payload に格納する。

- `tools/acceptance_receipt_signature.py:202-217,220-230,304-311`
  - canonicalization、署名付与、signed receipt からの payload 復元でも、`lease_generation` を同じ SHA-256 形式に再検証する。
  - root field は完全一致で検査され、`lease_generation` の欠落や余分な field は拒否される。

- `tools/acceptance_receipt_signature.py:326-375`
  - `expected_lease_generation` も `[0-9a-f]{64}` のみ受理する（`:349-351`）。
  - receipt の `lease_generation` と expected 値の完全一致は `:357-364` で行われ、不一致は `signed receipt context mismatch` になる。
  - その後、固定された key record と key id を照合し、Ed25519 署名を検証する（`:365-374`）。

- `tools/acceptance_receipt_signature.py:378-396`
  - 固定公開鍵を使う上位 verifier も、同じ expected 値を下位 verifier へ転送する。

- `tools/acceptance_issuer_reference.py:436-464,513-528`
  - issuer API も64桁小文字16進だけを受理する。
  - caller の値を projection と自己検証の expected の両方へ渡すため、現状は「caller が渡した値」と「同じ caller 値」の照合であり、取得との対応は検査しない。

- `tools/acceptance_issuer_reference.py:550-579`
  - CLI の `--lease-generation` は必須。argparse 自体は任意文字列を読むが、形式不正は issuer 内で拒否され、`main()` は rc=70 を返す。option 欠落は argparse の rc=2 となる。

## 変更案

| file:line | 変更内容 | なぜそれが D1527 を満たすか | 変更後に新しく受理される値 / 新しく拒否される値 |
|---|---|---|---|
| `tools/acceptance_receipt_signature.py:9-14,168-180` | module と projection の docstring に、SHA-256 形式値は「排他権の1回の取得」に対応し、別取得では再利用してはならないという契約を記す。同時に、この module は値を導出せず、取得や live lease の検査を証明しないと明記する。 | 粒度を取得ごとに固定しつつ、D1528 に従って導出方式を選ばない。D1443/D1499 に従い関門主張も縮退する。 | 文書変更のみ。 |
| `tools/acceptance_receipt_signature.py:43-49,122-129` | 予約値 `LEASE_NOT_ACQUIRED = "not-acquired"`、serialized 値を検査する `_require_lease_generation_value()`、明示的な `(lease_acquired, lease_generation)` を serialized 値へ変換する小さな helper を追加する。`lease_acquired` は真の `bool` を必須とし、`True` なら64桁値、`False` なら `lease_generation is None` だけを許す。既定値は設けない。 | 取得ありと取得なしを caller が必ず明示し、取得なしを通常世代と構文的に分離する。 | 新規受理: serialized `"not-acquired"`。新規拒否: `True + "not-acquired"`、`False + SHA-256値`、非boolの状態指定。 |
| `tools/acceptance_receipt_signature.py:168-199` | `project_v5_receipt()` に必須 keyword `lease_acquired: bool` を追加し、`lease_generation` を `str \| None` にする。helper で SHA-256 値または marker に正規化してから、既存の `lease_generation` field に格納する。`SIGNED_V6_PAYLOAD_FIELDS` は変更しない。 | 署名 schema を増やさず、取得1回または取得なしという二つの意味だけを既存 slot に載せられる。 | 新規受理: `lease_acquired=False, lease_generation=None`。従来の64桁値は `lease_acquired=True` の明示付きで引き続き受理。状態引数を省略した programmatic call は新たに拒否される。 |
| `tools/acceptance_receipt_signature.py:202-217` | canonical payload の検査を「64桁小文字16進または予約 marker」に変更する。ほかの hash field、field 集合、canonical bytes の規則は変更しない。 | 非保持 marker も `lease_generation` として署名対象に含めつつ、任意文字列への拡張を防ぐ。 | 新規受理: `"not-acquired"`。新規拒否なし。marker 以外の非SHA文字列は従来どおり拒否。 |
| `tools/acceptance_receipt_signature.py:326-396` | verifier に必須の `expected_lease_acquired: bool` を追加し、`expected_lease_generation` を `str \| None` にする。expected 側を同じ helper で serialized 値へ変換し、`:357-364` 相当の完全一致を維持する。docstring に、marker 一致は caller が期待した自己申告との一致にすぎず、lease 検査通過の証拠ではないと書く。 | 取得あり・なしを混同した再利用を拒否する一方、非保持を新しい lease gate と読み替えない。署名、固定鍵、fail-closed 経路は維持される。 | 新規受理: 署名済み marker と `False/None` expected の組。新規拒否: marker receipt と acquired expected、通常世代 receipt と nonholding expected。 |
| `tools/acceptance_issuer_reference.py:2-41` | claims 表を、取得ありでは caller 提供の「1取得に対応する識別子」、取得なしでは明示申告から `"not-acquired"` を記録する、という二分に更新する。どちらも live lease から独立導出・検査されないと明記する。 | 粒度の契約と非保持値を issuer 境界にも固定し、D1499 の恒真な関門主張を避ける。 | 文書変更のみ。 |
| `tools/acceptance_issuer_reference.py:436-464` | `issue_signed_receipt()` に必須 `lease_acquired: bool` を追加し、`lease_generation: str \| None` と組で早期検証する。取得ありの値は64桁形式のみ、取得なしは `None` のみ許す。値の生成・lease 読取りは追加しない。 | issuer の programmatic API でも取得状態を暗黙に補完せず、D1527 の二つの状態を明示する。 | 新規受理: `False/None`。新規拒否: 状態と値が矛盾する組、および状態指定のない旧呼出し。 |
| `tools/acceptance_issuer_reference.py:513-528` | projection と自己検証へ、同じ明示状態と値を渡す。自己検証は従来どおり完全一致と実署名検証を行うが、live lease 検査とは記述しない。 | signed bytes に状態を反映しつつ、既存の署名・固定鍵・context binding を弱めない。 | 新規受理: 正しく署名された nonholding marker。状態の交差は context mismatch で拒否。 |
| `tools/acceptance_issuer_reference.py:550-579` | `--lease-generation HEX` と `--lease-not-acquired` を required な mutually-exclusive group にする。後者では API に `False/None`、前者では `True/value` を渡す。`--lease-generation not-acquired` は許さない。 | CLI caller に取得状態を必ず選ばせ、予約値を通常世代として注入する経路や暗黙の既定値を作らない。 | 新規受理: `--lease-not-acquired`。新規拒否: 両option指定、両方欠落。従来の有効な `--lease-generation HEX` は維持。 |
| `orchestrator/tests/test_external_acceptance_signing.py:51-63,115-159,214-340` | marker の独立 literal、取得状態を受け取る test helper、正負の署名・context・CLI controls を追加する。既存 acquired control には `lease_acquired=True` を明示するだけとする。 | 取得あり、取得なし、交差拒否、署名対象への包含、明示CLI選択を直接固定する。 | テストのみ。既存 SHA-256 の受理値・期待 canonical bytes・root field 集合は変更しない。 |

## 非保持走行の値の設計

| 候補 | (a) SHA-256 値空間との衝突 | (b) 署名対象 | (c) 保持受領証との構文的区別 | (d) D1499 との関係 |
|---|---|---|---|---|
| 予約文字列 `"not-acquired"` | ハイフンを含み64桁16進でもないため衝突しない。 | 既存 `lease_generation` field の値なので canonical signed payload に含まれる。 | 通常世代は `[0-9a-f]{64}`、非保持は固定 literal と一意に判別できる。 | 暗黙の既定値にせず、`--lease-not-acquired` または必須 `lease_acquired=False` で明示させ、docstring で「lease 検査の証拠ではない」と縮退すれば該当しない。 |
| JSON `null` | 文字列値空間とは衝突しない。 | field を残す限り `null` も署名対象になる。 | JSON type が異なるため区別可能。 | 明示入力なら直ちには該当しないが、Python の `None` や `mapping.get()` が欠落・不明・非保持を混同しやすく、既定値への縮退を誘発しやすい。 |
| 64桁の全ゼロ値 | SHA-256 形式値空間そのものに含まれ、将来の正規取得値と衝突しうる。 | 署名対象になる。 | 保持世代と構文的に区別できない。 | 「既定の世代値を入れる」形そのものであり、D1499 の却下理由に当たる。採用不可。 |

推奨は `"not-acquired"`。既存 field を保ったまま値域を disjoint union にでき、JSON type を増やさず、canonicalization も単純に保てる。ただし marker 自体は「取得しなかった」という署名済み自己申告でしかない。CLI/API に既定値を置かず、保持検査通過を意味しないことを verifier と issuer の両方に明記する。

## テスト案

**正例**

| nodeid 案 | assert の中身 |
|---|---|
| `orchestrator/tests/test_external_acceptance_signing.py::test_recorded_production_v5_receipt_passes_canonical_projection` | 既存 test を保持し、呼出しに `lease_acquired=True` を追加する。`len(canonical) == 1919` と既存 SHA-256 literal を変更せず、取得ありの serialized bytes が不変であることを確認する。 |
| `orchestrator/tests/test_external_acceptance_signing.py::test_valid_test_signature_and_exact_context_pass` | 実体である production-v5 fixture、`Ed25519PrivateKey.generate()`、`canonical_signed_payload_bytes()`、`attach_signature()`、`verify_signed_receipt_signature()` をそのまま使う。stub は置かず、取得あり expected で `_LEASE_GENERATION` が返ることを既存どおり assert する。 |
| `orchestrator/tests/test_external_acceptance_signing.py::test_nonholding_marker_is_signed_and_exact_context_passes` | 実 fixture から `False/None` で projection し、実 Ed25519 key で署名・検証する。`payload["lease_generation"] == "not-acquired"`、canonical bytes に `"lease_generation":"not-acquired"` が含まれること、`False/None` expected で同じ payload が返ることを assert する。 |
| `orchestrator/tests/test_external_acceptance_signing.py::test_reference_issuer_parser_accepts_explicit_lease_state_choices` | 実 `issuer._parser()` に全必須引数を渡し、取得ありでは `lease_generation == _LEASE_GENERATION`、非保持では `lease_not_acquired is True` かつ `lease_generation is None` を assert する。 |

**負例**

| nodeid 案 | assert の中身 | 何が起きたら赤になるか |
|---|---|---|
| `orchestrator/tests/test_external_acceptance_signing.py::test_acquired_claim_rejects_nonholding_marker` | `lease_acquired=True, lease_generation="not-acquired"` の projection が `ReceiptSignatureError("invalid lease_generation")` になることを assert する。 | marker が取得ありの通常世代として受理されたら赤。 |
| `orchestrator/tests/test_external_acceptance_signing.py::test_nonholding_claim_rejects_generation_value` | `lease_acquired=False, lease_generation=_LEASE_GENERATION` が `ReceiptSignatureError("lease_generation must be absent when lease was not acquired")` になることを assert する。 | 非保持宣言と通常世代を同時に署名できたら赤。 |
| `orchestrator/tests/test_external_acceptance_signing.py::test_nonholding_receipt_is_rejected_for_acquired_expected_context` | 実鍵で作った marker receipt を acquired expected で検証し、`signed receipt context mismatch` を assert する。 | 非保持 receipt が取得あり context に再利用できたら赤。 |
| `orchestrator/tests/test_external_acceptance_signing.py::test_acquired_receipt_is_rejected_for_nonholding_expected_context` | 既存 acquired receipt を `False/None` expected で検証し、`signed receipt context mismatch` を assert する。 | 取得あり receipt が非保持 context として受理されたら赤。 |
| `orchestrator/tests/test_external_acceptance_signing.py::test_unreserved_non_sha_lease_generation_is_rejected` | payload の値を `"none"` 等へ置換し、`canonical_signed_payload_bytes()` が `invalid lease_generation` を返すことを assert する。 | 予約 marker 以外の任意文字列へ受理集合が広がったら赤。 |
| `orchestrator/tests/test_external_acceptance_signing.py::test_reference_issuer_parser_rejects_missing_or_conflicting_lease_state` | lease option が両方欠落した argv と両方指定した argv の各々で、実 parser が `SystemExit(2)` になることを assert する。 | caller が取得状態を明示しなくても、または矛盾して指定しても parse できたら赤。 |

既存の `_PRODUCTION_PROJECTED_BYTES`、`_PRODUCTION_PROJECTED_SHA256`、`_EXPECTED_SIGNED_ROOT_FIELDS`、`_LEASE_GENERATION`、既存 replay control の期待値は変更不要である。必要なのは新しい必須状態引数を既存 helper 呼出しへ明示する機械的変更だけである。

## 親 brief の誤り

無し。

## 総括

- 取得ありの値は64桁小文字16進のまま、「排他権の1回の取得」に対応する契約とする。
- 非保持値は、SHA-256 値空間と交わらない `"not-acquired"` を推奨する。
- 状態は必須 API 引数または mutually-exclusive CLI option で明示し、暗黙の既定値を作らない。
- marker の署名・expected 一致は自己申告の固定であり、live lease 検査の証拠とは主張しない。
- 世代の導出・一意性強制は D1528 後に残る不確実性であり、本変更では実装しない。
- 親は上記 nodeid、既存 canonical hash/length の不変、全既存 control を実測すべきである。本段では pytest を実行していない。