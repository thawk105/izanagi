# 段 4 裁定 — [T-627] 遷移述語 (generation + contract hash 同一入力束縛)

親が段 2 プランと段 3 の 2 レンズを real/refuted に裁定し、plan v2 と変異事前登録を確定する。

## 所見の裁定

| ID | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | 「途中 no-op」負例が実際は**末尾** no-op。`g1→g2→g3` 正例 node も無い | **real** | **採用** |
| A2 = B1 | successor 判定が「全 changed env」に量化されていない実装を殺せない | **real** | **採用** |
| A3 = B4 | production adapter の負方向 (返り値破棄・解決失敗) が未検査 | **real** | **採用** |
| A4 | 必須 capability 契約 (引数省略・非 callable) がテストで固定されていない | **real** | **採用** |
| A5 | 親 brief の `DW-G04` 説明「`is_valid_successor` と同じ結線済み・未発火」は成立しない | **real** | **採用 (記録の訂正)** |
| A6 | source binding が汎用 certified producer に閉じていない | **real** | **scope 外** |
| A7 = B7 | 段 1 probe の H が C と同一入力 | **real** | **採用 (probe 訂正済み)** |
| B2 | catalog の hash 順 (ordinal) だけを見る実装が全 node を通る | **real** | **採用** |
| B3 | `(+2,−1)` 一例では別形の集約実装 (`max(delta)==1 and sum>=0`) が生き残る。`(+1,−1)` が抜ける | **real** | **採用** |
| B5 | `g1→g2→g3` の正例 node が無く、`predecessor.generation != 1` を足す過剰拒否が生き残る | **real** | **採用** |
| B6 | serial 2 の env 集合不一致における評価順序が node で固定されていない | **real** | **採用** |
| B-307 | catalog と adapter を「検証済み `GENERATIONS` snapshot の closure」で同時生成せよ | **refuted** | **不採用** |

### A5 の裁定 (記録の訂正)

レンズ A が正しい。`is_valid_successor` は import 時の `validate_generations(GENERATIONS)`
(`env_contract.py:367`) から pegasus g1→g2 に対して**実際に呼ばれている**。一方、本 wave の遷移述語は
本番 chain が 1 record であるため呼ばれる入力が存在しない。したがって
「同じ結線済み・未発火」という親 brief の比較は成立せず、**`DW-G04` は満たしていない**。

採用する記録の言い方は次に統一する。

> `DW-G04` は満たしていない (発火 artifact が存在しない)。後発のユーザー裁定が
> 「[T-657] の活性化より前に入れる」と順序を明示したため、本件に限り狭く override された。
> consumer の存在を発火証拠とは呼ばない。

### B-307 の refuted 理由 (実測に基づく)

「検証済み snapshot を捕捉する closure」で adapter を作ると、`orchestrator/tests/conftest.py:72-76` の
`_activate_synthetic_env_authority` が `GENERATIONS` と `_REGISTERED_CONTRACT_CATALOG` を
**monkeypatch で同時に差し替える**経路と分裂する (closure は import 時の snapshot を握るため
monkeypatch が効かない)。既存 consumer である `_load_authority_snapshot` (`env_contract.py:492`) も
load 後に module-global `GENERATIONS` を読んで再照合しており、adapter が同じものを読むほうが整合する。
片方の分裂を別の分裂に置き換えるだけなので採らない。**adapter は呼出し時に module-global
`GENERATIONS` を読む**。

### A6 の scope 外理由

汎用 certified 経路が source binding を呼ばない穴は本 wave が開けたものではなく、
worklog (313) に既記録である。[T-657] の前提として扱うべき real な所見だが、実装を混ぜると
T-627 の裁定射程を超える。**裁定パッケージへ返す** (下記)。

## plan v2 (確定)

段 2 プランの設計 (必須 callable + production adapter) を採用し、段 3 の must-fix で補強する。

### 実装面 (段 2 プランの file:line をそのまま採用する部分)

- `env_contract_activation.py`: `_RegisteredSuccessorPredicate` 型 alias、
  `_validate_activation_transition` private gate、`validate_activation_records` と
  `load_activation_state` へ**既定値なし keyword-only** の `is_valid_registered_successor` を追加。
  chain loop 前に callable 検査。activation leaf は `env_contract` を import しない
  (`test_activation_leaf_is_stdlib_only_...` を保持)。
- `env_contract.py`: `_resolve_activation_entry` / `_is_valid_activation_successor` を追加し、
  `_load_authority_snapshot` から渡す。**adapter は呼出し時に module-global `GENERATIONS` を読む**。
  generation delta の判定は adapter に重複させず loader に残す。
- `tools/issue_env_contract_activation.py`: 同 adapter を loader へ渡すだけ。issuer 固有の
  delta / successor 実装は追加しない (単一 gate)。

### gate の禁止 (署名で書く)

```python
def _validate_activation_transition(
    predecessor_rows: tuple[ActiveContract, ...],
    successor_rows: tuple[ActiveContract, ...],
    *,
    activation_serial: int,
    is_valid_registered_successor: _RegisteredSuccessorPredicate,
) -> None:
```

禁止するもの (serial 2 以降の隣接 pair ごとに評価する):

1. 全 env の `(generation, contract_sha256)` が前 record と一致する遷移 (no-op)。
2. 変化した env で `successor.generation != predecessor.generation + 1` である遷移
   (skip・downgrade・相殺のすべてを含む。**env ごとに評価し、集約量で判定しない**)。
3. **変化した各 env について**、`is_valid_registered_successor(predecessor_row, successor_row)`
   が exact `True` を返さない遷移 (最初の 1 件だけでなく全件)。
4. 判定値が exact `bool` でない場合、および判定中の例外 (fail-closed で包む)。

**通る正例 (1 つ)**: `linux-baremetal` を g1 据置、`pegasus` を g1→g2 とする serial 2 record。
これは [T-657] が実際に発行する形であり、pegasus g2 は g1 から calibration path/SHA の対だけを
置換しているので現行 `is_valid_successor` の許可差分に一致する。

### 段 3 must-fix を反映したテスト node (段 2 の 14 件 + 追加 9 件)

段 2 プランの 14 node を維持したうえで、次を追加・修正する。すべて独立 node とする。

| # | node | 検出する退行 (段 3 の所見) |
|---|---|---|
| N1 | `test_transition_rejects_noop_in_middle_of_chain` を `(1,1)→(1,1)→(2,1)` へ**修正** (serial 2 で拒否) | A1: 末尾 pair しか見ない実装 |
| N2 | `test_transition_accepts_three_record_forward_chain` — `(1,1)→(2,1)→(3,1)` を受理、terminal g3、ever-active に g1/g2/g3 を exact assert | A1/B5: `predecessor.generation != 1` を足す過剰拒否 |
| N3 | `test_transition_rejects_when_second_changed_env_successor_is_false` — `(1,1)→(2,2)`、env-a は `True`、env-b は `False` | A2/B1: 1-witness 実装 |
| N4 | `test_successor_predicate_is_called_once_for_each_changed_env` — 呼出し列を ordered exact assert (changed 各 1 回、据置 0 回) | A2/B1: 量化の欠落 |
| N5 | `test_transition_rejects_compensating_plus_one_minus_one` — `(1,2)→(2,1)`、callable は `True` | B3: `max(delta)==1 and sum>=0` 型の集約実装 |
| N6 | `test_transition_matrix_matches_d228_rule` — 2 env × generation {1,2,3} の全組合せ (9×9)、callable は `True` 固定、期待値は D228 の規則 `all(d in {0,1}) and any(d == 1)` から生成 | B3: 未知の集約実装一般 |
| N7 | `test_transition_rejects_skip_when_catalog_order_is_not_generation_order` — catalog を `((1,H1),(3,H3),(2,H2))` で渡し `g1→g3` を拒否 | B2: catalog ordinal 実装 |
| N8 | `test_production_successor_adapter_returns_false_when_is_valid_successor_is_false` — `ec.is_valid_successor` を `False` へ monkeypatch し、adapter が exact `False` を返すこと + 同 adapter を渡した loader が successor 診断で拒否すること | A3/B4: 返り値破棄 |
| N9 | `test_production_successor_adapter_rejects_rows_that_do_not_resolve` — generation / hash / env_tag をそれぞれずらした row で adapter が `False`、かつ `is_valid_successor` が呼ばれないこと | A3/B4: 解決検査の欠落 |
| N10 | `test_validate_activation_records_requires_successor_predicate` — 引数省略で `TypeError`、serial 1 に非 callable を明示で `ActivationRecordError` (`load_activation_state` も同様) | A4: permissive default の追加 |
| N11 | `test_transition_rejects_env_set_change_before_calling_predicate` — serial 2 で env を 1 つ欠落／追加し、`ActivationRecordError` (env 集合の理由)、callback 0 回 | B6: 評価順序 |

N6 の期待値は**実装ではなく D228 の規則文から生成する** (循環参照にしない)。callable を `True` に
固定することで、期待値は D228 の規則へ厳密に一致する。

### 既存テストの再著述 (段 2 の 4 件を採用)

1. `test_chain_intentionally_does_not_enforce_generation_delta_predicates` → 独立 node 群へ**置換**。
   末尾の wrong-hash rejection は独立 node として保持する。
2. `test_downgrade_preserves_pegasus_g2_for_historical_resolution` →
   `test_forward_activation_preserves_pegasus_g1_for_historical_resolution` へ再構成
   (g1→g2 の forward chain で、g1 の ever-active membership と `resolve_by_contract_sha256` を検査)。
   `_actual_serial3_downgrade` は削除する。
3. `test_issue_main_success_prints_required_head_and_inactive_warning` → 引数を
   `linux-baremetal=1 / pegasus=2` へ変更し、`test_issue_main_rejects_noop_without_publishing` を新設。
4. `test_issued_valid_suffix_is_not_active_until_source_head_update_and_restart` → suffix を
   pegasus g2 への正当な forward record にし、例外 match を head 不一致まで強める (偶然緑の除去)。

**期待値の緩和・skip・削除は禁止。**受理集合が狭まった結果として期待が変わるものだけを変更する。

## 変異事前登録 (DW-M01)

実効 gate は `_validate_activation_transition` と production adapter の 2 箇所。前後に同じ入力を
拒否する層が無いことは段 1 probe で実測済み (no-op / skip / downgrade / 相殺 / 途中 no-op を
現行はすべて受理)。head serial / state hash 検査は各負例の tail に合わせるため救済しない。
`ever_active` 包含検査は current hash の包含だけを見るため mask しない。

| ID | 変異位置 (意図) | 期待 kill node | 単一理由性の確認 |
|---|---|---|---|
| M1 | no-op 拒否 (`if not changed: raise`) を無効化 | N1、`rejects_all_env_noop`、`issue_main_rejects_noop` | 他層に no-op 拒否なし (段 1 probe B) |
| M2 | `exactly +1` を `successor.generation >= predecessor.generation` へ緩和 | `rejects_skip`、`rejects_compensating_plus_two_minus_one`、N6 | downgrade は残るので理由が skip 側に絞れる |
| M3 | `exactly +1` の判定を丸ごと除去 | `rejects_downgrade`、N5、N6 | 段 1 probe F/J で他層が拒否しないことを実測済み |
| M4 | 変化 env のループを `changed[0]` だけへ縮退 (1-witness) | N3、N4 | 単一 env 前進 node は緑のまま (帰属が量化に絞れる) |
| M5 | adapter の `is_valid_successor` 返り値を捨てて `return True` | N8 | loader の数値 gate は通る fixture にする |
| M6 | `_resolve_activation_entry` の `contract_sha256` 一致検査を除去 | N9 (adapter 単体呼出し) | loader の registry pair gate を経由しない直接呼出しなので単一理由 |
| M7 | `is_valid_registered_successor` へ既定値 `None` を足し、`None` なら数値だけで判定 | N10 | 他 node は全て明示的に渡すため、この変異は N10 だけが殺す |
| M8 | 判定値の `type(...) is bool` を truthy 検査へ緩和 | `rejects_non_bool_successor_result` | 正常 +1 の fixture なので返り値型だけが理由 |
| M9 | `exactly +1` を catalog ordinal 比較へ置換 | N7 | generation 順 catalog の node は緑のまま |
| M10 | (逆方向・過剰拒否) `predecessor.generation != 1` の拒否を追加 | N2 | 受理集合を縮小する wave のため承認外の過剰拒否を検出する正例として登録 (DW-M01) |

M2 と M3 は同一行への異なる変異なので、`DW-M04` に従い置換対象の一意性を各変異で assert する。
SURVIVED が出た場合は `DW-M02` に従い他層の mask と等価変異を疑い、両層同時変異まで裏取りする。

## 実装の所有と規模

編集面は 4 ファイル (`env_contract_activation.py`、`env_contract.py`、
`tools/issue_env_contract_activation.py`、`orchestrator/tests/test_env_contract_activation.py`)。
すべて相互依存するため**段 5 は 1 単位**とし、分割しない。実装子は Codex `role=author`、
`reasoning=high`、`sandbox=workspace-write`。docs 編集と commit は禁止。

## 裁定パッケージ (ユーザーへ返す — 本 wave では実装しない)

1. **汎用 certified producer の source binding (A6)。** silo (`silo_ladder_rung1.py:254`) と
   qualification (`qualification/contract.py`) は本 wave の 2 module を code identity に含めるが、
   汎用 certified 経路はその binding を呼ばない (worklog (313) の既記録)。[T-657] の活性化後は、
   dirty / 未レビューの loader bytes で certified 選択・レポート・WAL を生成しても activation 参照
   だけでは検出できない。T-657 の前提として設計択一が要る。
2. **一般 contract rollback は本 wave の射程外 (D228 と同じ)。** 本 wave が束縛するのは
   「検証済み production generation snapshot に対する record-level edge」だけであり、
   世代列の再定義・module 属性の再束縛・逆引き index の再束縛・較正の新旧は保証しない。
   記録にこの限定を明記する (謳うだけの保証にしない)。
