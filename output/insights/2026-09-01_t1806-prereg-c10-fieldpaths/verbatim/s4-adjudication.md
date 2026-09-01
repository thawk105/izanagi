# 段 4 裁定 — [T-1806] / D967

親が段 2 plan、段 3 レンズ A / B、および親自身の実測から確定した。

## 0. 承認済み裁定の前提に対する訂正 (最重要)

**D967 の「既存 campaign が E1-stale になる」という前提は、後発のユーザー裁定 D1163
(2026-08-27、絶対規律 7 の新設) により現行コードでは成立しない。**

- D1163 は `artifact_admission._require_verifier_epoch_for_purpose` の
  `recorded-current-closure-mismatch` 拒否経路を**名指しで撤去**した (D422 のこの条件だけを supersede)。
- 現行実装は現在の closure が**取得可能か**だけを見る。実装内コメントが
  「D1163 keeps only the availability prerequisite here. A clean committed current closure
  may differ from the recorded closure.」と明記している
  (`orchestrator/campaign/artifact_admission.py:953-970`)。
- 親の独立実測: tracked `campaign.lock` は **32 件**、うち `contract_loader_blob_sha256s` を
  持つものは **0 件**。よって本 wave で newly stale になる campaign は **0 件**。

**裁定:** D967 の 3 つの行動 (field_paths を広げる / 凍結を再発行する / 判定器版を bump する) は
**すべてそのまま実行する**。変わるのは記録の内容だけである。
D967 の指示は「隠さず正直な migration として記録する」であり、
**起きなかったことを起きたと書くのは同指示への違反である。**
記録は次の形にする。

> D967 は既存 campaign が `E1-stale` になることを想定していたが、翌日のユーザー裁定 D1163 が
> `recorded-current-closure-mismatch` の拒否経路を撤去したため、この失効は発生しない。
> tracked campaign.lock 32 件のうち閉包 hash を持つものは 0 件で、newly stale は 0 件である。
> dirty な作業ツリーでの一時的な `E1-stale / current-closure-unavailable` は従来どおり残る。

これはユーザー裁定の**不採用ではない**。行動は全部実行し、事実だけを正しく書く。
ユーザーへは報告で明示する。

**副作用:** 親が brief (P1) の補強に使った「D967 が E1-stale を明言している以上、閉包内 .py の
変更を意図している」という推論は**取り下げる**。D1163 下ではどちらでも E1-stale は起きないため、
この推論は成立しない。(P1) は下記の一次的な根拠だけで立つ。

## 1. (P1)〜(P4) の確定

| # | 確定 | 根拠 |
|---|---|---|
| P1 `_C10_FIELDS` も広げる | **採用** | `_evaluate_c10` が読むのは `_C10_FIELDS` であって契約 JSON ではない (`s8c_preregistration_evidence.py:2240-2249`)。JSON だけでは正式 gate の検知集合が 1 件も増えない。両レンズが独立に賛成。同族の後発裁定 **D1292** (2026-08-29、判定器 C04 の到達対象を契約の要求へ揃える) が「契約が要求するのに判定器が見ていない状態は恒真に近い」として同じ方向を採っている |
| P2 drift 検査を入れる | **採用。ただし plan の形は却下し、下記の形へ差し替える** | 両レンズが本題に含めてよいと判定。ユーザーが scope 外とした「仮想リスク向けの gate」ではなく、変更対象の契約 field と評価器を直接束縛する検査である |
| P3 規範文書は変更しない | **採用** | 条件 10 の散文は field 名を列挙していない。個別 condition hash は markdown の条件文だけから算出される。両レンズが賛成し、レンズ B は g11 の各 hash を再計算して不変を確認した |
| P4 表記は `proposal.build_source_bindings` | **採用** | 既存 12 件の namespace 規約 (`proposal_path`→`proposal.path` 等) に一致。両レンズが賛成 |

## 2. 所見の裁定 (real / refuted、採否)

| # | 出所 | 判定 | 扱い |
|---|---|---|---|
| A1 | レンズ A must-fix | **real・採用** | 片方向 `all(... in ...)` は契約側の余分な field を許す。かつ `_C10_EXPECTED_FIELD_PATHS` と `_C10_FIELDS` を独立した手書き集合にすると相互に drift する。**C06 の `field_paths` idiom は実際には完全一致比較で、`all` は `reachable_from` 用**であった。plan の引用が誤っている |
| B2 | レンズ B should-fix | **real・採用 (A1 と同一)** | 独立に同じ欠陥へ到達した。採用の確信度が上がる |
| B1 | レンズ B must-fix | **real・採用** | §0 のとおり。親が D1163 と実装と件数を独立に実測して確認した |
| A2 | レンズ A should-fix | **real・採用** | `_strings` は AST 全 descendant の文字列を集めるだけで、到達性・値の由来を見ない。dead branch や `if False:` 内に literal を残せば通る。**この限界を plan・テスト名・worklog へ明記する** |
| B3 | レンズ B should-fix | **real・採用** | plan の「影響テストの完全列挙」が producer 側 (`test_autonomous_trial_completeness.py` の 13 field parameterized mutation、`proposal_build_source_bindings` 専用分岐) を落としている。焦点走へ含める |
| B4 | レンズ B should-fix | **real・採用** | dirty な閉包では `capture_contract_loader_binding()` が HEAD blob 不一致で失敗する。順序を **prepare-revision → 全変更を 1 commit → clean 木で受入全走**と固定する |
| A3 | レンズ A nit | **real・採用 (記録面)** | 一部の kill は既存 runtime / freeze テストが先に赤にする。変異台帳で「C10 評価器の単独 kill」と「既存テストによる先行 kill (冗長 gate)」を別列にする |
| B5 | レンズ B nit | **real・採用 (記録面)** | 先例 2b19d26b2 は freeze を含め 7 file。共通は 6 file で、7 番目の invariant test は今回不要 (C10 の `reachable_from`・entrypoint を変えず、`field_paths` は同 invariant の走査対象外) |
| A4 | レンズ A: brief の scope 過大主張 | **real・採用** | scope を「同 field literal を verifier AST から落とす弱体化」に限定して書き直す |
| A5 | レンズ A: 「JSON は文書のまま」が強すぎる | **real・採用** | JSON は既に freeze の `evidence_contract_sha256` / `protected_sha256` に束縛されており単なる文書ではない。正しい限定は「**freeze に対しては既に load-bearing だが、C10 の verdict に対しては非 load-bearing**」 |
| A6/B6 | DECIDER_VERSION の「exact 4 箇所」 | **real・採用 (brief の誤り)** | literal assertion は core の 3 箇所 (2404 / 2454 / 2477)。`test_s8c_gate_report.py:84` は synthetic report の自己投影で production 定数を参照せず**更新しない**。実際の 4 件目は `test_s8c_preregistration_invariant.py:449` の動的整合で、g12/v7 の発行により追随しテストコードは変えない |

**scope 外の real 所見:** 無し。全所見が本題の編集面に収まった。

## 3. P2 の確定形 (plan からの差し替え)

単一の対応表から両側を導出し、**完全一致**で比較する。

```python
# (実装 literal, 契約 field path) の単一正本。両側をここから導出する。
_C10_CROSS_BINDING_FIELD_BINDINGS = (
    ("input_payload_sha256", "role_event.input_payload_sha256"),
    ...
    ("proposal_build_source_bindings", "proposal.build_source_bindings"),
)
_C10_FIELDS = frozenset(literal for literal, _ in _C10_CROSS_BINDING_FIELD_BINDINGS)
_C10_EXPECTED_FIELD_PATHS = frozenset(path for _, path in _C10_CROSS_BINDING_FIELD_BINDINGS)
```

検査は `frozenset(probe.requirement("cross_binding_verifier").field_paths)
== _C10_EXPECTED_FIELD_PATHS` とする。`trial_registry` の evidence は
`_C10_FIELDS` の対応物ではないので**この比較へ混ぜない**。

失敗時は新しい reason code を作らず既存の
`ReasonCode.CROSS_BINDING_VERIFIER_INCOMPLETE` を返す (C06 と同型)。
呼出位置は `_evaluate_c10` の `verify is None` guard の直後、
`_C10_FIELDS <= _strings(verify)` の前。

**この形が満たす性質 (段 6 のレビューはここを検査せよ):**
- 契約 JSON に 14 件目の未実装 field を足すと**落ちる** (片方向 `all` では通っていた)。
- 対応表から 1 組を削ると、契約 JSON (13 件) と不一致になり**落ちる**。
  つまり表を縮めて gate を静かに弱める経路が塞がる。これが完全一致にする実利である。

## 4. gate の禁止と、通る正例 (DW-S04)

**禁止の署名:** `_evaluate_c10` は、
`frozenset(probe.requirement("cross_binding_verifier").field_paths) != _C10_EXPECTED_FIELD_PATHS`
または `not (_C10_FIELDS <= _strings(verify_s8c_cross_binding))` のとき
`UNSATISFIED / cross-binding-verifier-incomplete` を返し、それ以外の終端へ進んではならない。

**通る正例 (1 つ):** 現行 production の木。契約 C10 の `cross_binding_verifier.field_paths` が
13 件、`verify_s8c_cross_binding` の AST に 13 literal すべてが在る状態。
このとき C10 は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` へ進む。
親は `proposal_build_source_bindings` が同関数内に literal として実在することを AST で実測済み。

## 5. 変異の事前登録 (DW-M01)

ユーザー指示「派生値の pin は生成器の検査にならないので、**無条件版と条件版を対で登録して
射程を露出させる**」に従う。守りたい pin は `_C10_FIELDS <= _strings(verify)` であり、
これは**関数内に文字列 literal が在るか**しか見ない。

| ID | 変異 | 期待 | 単一理由性 |
|---|---|---|---|
| M01-UNCOND | `_C10_CROSS_BINDING_FIELD_BINDINGS` から `proposal_build_source_bindings` の 1 組を削除する | **KILLED** — 表が 12 件、契約 JSON が 13 件で完全一致検査が落ち、C10 が `UNSATISFIED` へ。実 repo を読む predicate snapshot が赤 | 契約 JSON は無傷なので凍結 hash pin は動かない。新 drift 検査に固有の kill である |
| M01-COND | literal は残したまま、`verify_s8c_cross_binding` 内でその field が守っている照合だけを恒真化する (値の検証を外す) | **SURVIVED (想定どおり)** — literal は AST に残り、契約も表も無傷なので C10 は緑のまま | C10 gate は検出しない。別層の producer functional test が検出する。**この非対称そのものが登録の目的である** |
| M02 | 契約 JSON の `field_paths` から `proposal.build_source_bindings` を削除する | KILLED | 凍結 contract hash pin が**先に**赤にする。**冗長 gate として明記し、drift 検査の検出力の証拠に数えない** |
| M03 | 契約 JSON へ実装に無い 14 件目の field path を足す | KILLED | 完全一致検査に固有。片方向 `all` では通っていた変異であり、A1/B2 の修正が効いていることの直接の証拠 |

**M01-COND が SURVIVED になることが目的である。** これで pin の射程が機械で露出する。
片方だけ登録すると差が見えない。SURVIVED を欠陥として隠さず、
**「この pin は literal の実在までしか証明せず、field の生成・再読・値束縛は証明しない」**と
worklog・テスト名・insight へ明記する (A2 の採用と同じ趣旨)。閉じられない残余は主張を先に狭める。

M01-COND を KILL するために producer の functional test を無効化する変異は**登録しない**
(テストを弱める方向の変異は規律 2 に触れる)。

## 6. 実装しないこと

- `docs/phase3-8c-preregistration.md` を変更しない。
- `SATISFIABLE_CONDITION_IDS` を変更せず、C10 を `SATISFIED` にする分岐を作らない。
- `CONTRACT_LOADER_RELATIVE_PATHS` の構成 (24 path) を変更せず、契約 JSON を閉包へ足さない。
- `autonomous_trial_completeness.py` を変更しない (必要な field は既に実在する)。
- 新しい reason code、汎用 drift framework、別 gate、台帳、一般化を作らない。
- `_strings()` を live-code 解析へ一般化しない。
- `test_s8c_gate_report.py:84` を更新しない (production pin ではない)。
- g10 / g11 を編集せず、g12 を手書きしない。
- skip / xfail / 期待反転 / 述語の緩和を行わない。

## 7. 実行順序 (B4 の採用)

1. 実装子がコードとテストを編集する (commit しない)。
2. 親が `prepare-revision` CLI を実行して g12 を発行する (worktree の現物を読むため commit 前)。
3. 親が全変更を 1 commit にする。
4. clean な木で焦点走 → 変異 matrix → 受入全走。commit 前は tmp-repo 型の限定 node だけを使う。
