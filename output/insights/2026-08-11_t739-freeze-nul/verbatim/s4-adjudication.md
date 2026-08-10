# 段 4 裁定 — [T-739] 凍結発行・検証層への NUL 検査拡張

親 = manager。両レンズとも NO-GO。所見を real/refuted、採否、scope 内/外に裁定し、プラン v2 を確定する。

## 1. 所見の裁定

| # | 出典 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A2 | lensA | 起草案の「v1 schema の 2 位置だけ列挙」では、malformed shape (`conditions` が dict、要素が非 dict、入れ子 wrapper) の exact `"path"` NUL が凍結を通る。裁定 (b) が不採用にした「凍結可能・発効不能」の境界を再導入する | **real / 高** | **採用**。親 P2 (再帰 exact `"path"` key + `str` 値) へ戻す |
| O1 | lensA | 親 P1 の「`_canonical_bytes` の前」は既存 `evidence-contract-json` を横取りする (NUL + unpaired surrogate で reason が変わる) | **real / 中** | **採用**。**親 P1 を撤回**し、検査は canonicalization 成功後・`_sha256` の前に置く |
| T2 | lensA | activation report の freeze 層差分 (`freeze_reason_code` 等) を固定していない。`effective is False` だけでは旧実装でも通る恒真 | **real / 中** | **採用** |
| D1 | lensA | v1 に path 位置が増えたときの更新漏れ検査がない | **real / 高** | **採用 (形を変えて)**。A2 で再帰走査へ戻すため列挙 helper 自体が消え、drift の主因は構造的に解消する。残る担保として「現行契約の全 path 位置を 1 つずつ NUL 化して全件拒否」を parametrized test で固定する |
| B1,B2 | lensB | fixture が**最後の** path しか変えないため「最後だけ検査する」実装を通す | **real / 高** | **採用**。D1 の 38 位置 parametrize が同時に閉じる |
| B3,B4,B5 | lensB | CR/LF・非 path NUL の受理テストが required path のみ・`len == 64` のみで弱い | **real / 中** | **採用**。consumer 側も含め、**hash 値の完全一致**で固定する |
| B9 | lensB | 履歴検証 E2E が期待 hash を `M._sha256(M._DOMAIN_EVIDENCE + M._canonical_bytes(...))` で再構成しており自己参照 | **real / 高** | **採用**。親が**実装前に実測した literal** を使う (下記 §3) |
| B10 | lensB | 既存 freeze がある分岐の `prepare_revision` を検査していない | **real / 中** | **採用** |
| B(5節) | lensB | core module を編集すると `activation_report_at` の `core_module_blob_sha256` と report digest が変わる。親 brief の「影響しない」は protected_sha256 と C 述語静的解析に限られる | **real / 中** | **採用 (記録事項)**。段 7 の worklog へ明記する。テスト化は**却下** — commit ごとに変わる揮発値を期待値へ焼き込むことになり `DW-S05-C` に抵触する |
| S1 | lensA | CR/LF は同層に残る同型の穴 | **real / 高** | **scope 外**。裁定 (c) 不採用の射程。実装せず**裁定パッケージ**でユーザーへ返す |
| lensA nit | lensA | s2 が `core:84` を `__all__` と誤記 (実際は `_FREEZE_KEYS` の field 名) | real / nit | 結論に影響なし。記録のみ |
| lensB 3節 | lensB | 例外 message 形式の懸念 | **refuted** | 親も実測済み (`[{reason}] {detail}`) |
| lensB 4節 | lensB | E2E が手前の別 reason で倒れる懸念 | **refuted** | 両レンズが独立に到達性を確認 |
| lensA P1,P2 | lensA | 親 brief の「raw bytes 走査では検出できない」「現行 hash と g1 bytes は不変」 | **refuted (主張は成立)** | ただし正確には「UTF-8 decode が拒否」ではなく「JSON parser が strict mode で制御文字を拒否」。brief の表現を段 7 で訂正する |
| lensB `test_core_module_rebinds_report_digest...` | lensB | core blob hash の下流影響をテスト化 | real だが**却下** | 揮発値の焼き込み。上記のとおり記録で閉じる |

**A2 と s2 の対立の裁定理由**: s2 は「再帰走査は `metadata.path` を過剰拒否する」と反対したが、裁定 (a) の
制約は **NUL-only** (= NUL 以外の不正を拒否しないこと) であって、走査範囲の広さではない。再帰走査でも
拒否するのは「`path` という名の field に NUL がある」場合だけで、CR/LF も schema 違反も通す。一方
s2 案は NUL 付き path を凍結記録へ束縛できる形を意図的に残し、これは裁定 (b) の再導入である。
よって A2 を採り、親 P2 を維持する。

## 2. プラン v2 (実装仕様)

### 2.1 production

`orchestrator/campaign/s8c_preregistration.py`、`evidence_contract_sha256` (現 l.344) の直前へ private
helper を追加し、`evidence_contract_sha256` を差し替える。

```python
def _assert_no_nul_in_contract_paths(value: Any) -> None:
    """契約の ``path`` field に NUL があれば fail-closed で拒否する。

    走査対象は key が exact ``path`` かつ値が ``str`` のものだけである。NUL 以外の文字も、
    ``path`` 以外の field の NUL も拒否しない。文書順で最初に見つけた 1 件で停止する。
    """
    pending: list[tuple[str, bool, Any]] = [("", False, value)]
    while pending:
        pointer, is_path, node = pending.pop()
        if is_path and isinstance(node, str) and "\x00" in node:
            raise PreregistrationError("evidence-contract-path-nul", repr(pointer))
        if isinstance(node, dict):
            for key, child in reversed(list(node.items())):
                pending.append((f"{pointer}/{key}", key == "path", child))
        elif isinstance(node, list):
            for index, child in reversed(list(enumerate(node))):
                pending.append((f"{pointer}/{index}", False, child))


def evidence_contract_sha256(raw: bytes) -> str:
    """evidence contract の JSON 意味内容を canonical 化して hash する。"""
    value = _strict_json(raw, what=EVIDENCE_CONTRACT_PATH)
    try:
        canonical = _canonical_bytes(value)
    except (TypeError, ValueError) as exc:
        raise PreregistrationError("evidence-contract-json", str(exc)) from exc
    _assert_no_nul_in_contract_paths(value)
    return _sha256(_DOMAIN_EVIDENCE + canonical)
```

- 再帰でなく明示 stack にするのは、深い入れ子で `RecursionError` (既存の `except` が捕まえない例外) を
  出さないためである。
- `reversed(...)` は pop 順を文書順に揃えるためであり、複数違反時に報告される pointer を決定的にする。
- reason は `evidence-contract-path-nul`、detail は `repr(JSON pointer)` のみ。**path 値を連結しない**。
  pointer 自体は key 名を含むので、key に制御文字があっても `repr` が escape する。

### 2.2 受理集合の差分 (確定)

「変更前は受理・変更後は拒否」になるのは、`_strict_json` と `_canonical_bytes` の両方に成功する入力の
うち、**parsed value のどこかに key `path` があり、その値が `str` で U+0000 を 1 個以上含むもの**だけ。
次は従来どおり通る: path の CR/LF、`path` 以外の field の NUL、schema 違反 (unknown key、
condition 数、schema_version)、`{"predicates":[]}` のような非 v1 形。

### 2.3 テスト (`orchestrator/tests/test_s8c_preregistration_core.py`)

先頭付近へ `EVIDENCE_CONTRACT_FILE = _ROOT / M.EVIDENCE_CONTRACT_PATH` を追加する。

1. `test_evidence_contract_hash_rejects_nul_at_every_consumed_path` — **実契約の全 `path` 位置**
   (現在 38 箇所) を**テスト側の独立走査**で列挙して parametrize し、1 箇所ずつ NUL を挿入して
   `evidence-contract-path-nul` を要求する。message が `[evidence-contract-path-nul] '<pointer>'` と
   exact 一致し、`\x00` を含まないことも assert する。**production の helper を呼んで期待値を作らない。**
2. `test_evidence_contract_hash_accepts_non_nul_path_controls` — `required` / `consumer` × `\r` / `\n`
   の 4 param。`len == 64` では足りない。**変更前後で同一である hash 値**を assert する
   (期待値は §3 の実測 literal、または「NUL なし corpus の hash が挿入前後で決定的に一致する」形)。
3. `test_evidence_contract_hash_accepts_non_path_nul` — `static_only_note` の NUL は通る。
   **過剰拒否を検出する正例**であり `DW-M01` の要求を満たす。hash 値を literal で固定する。
4. `test_evidence_contract_hash_rejects_nul_in_malformed_shape_path` — A2 の反転。少なくとも
   (i) `conditions` が dict でその直下に `path`、(ii) `required_evidence` の要素が非 dict の wrapper 内の
   `path`、(iii) 未知 key `metadata.path`、の 3 param で**拒否**を要求する。
   起草案の `test_..._accepts_unconsumed_schema_path_nul` は**作らない**。
5. `test_evidence_contract_hash_preserves_canonicalization_reason_before_nul` — NUL + lone surrogate で
   `evidence-contract-json` のままであること (検査順を前へ移す変異を殺す)。
6. `test_current_evidence_contract_hash_is_frozen` — 現行契約の hash literal 固定。
7. `test_existing_g1_record_pins_are_unchanged` — 実 repo の g1 record の
   `evidence_contract_sha256` / `protected_sha256` を literal で固定する (§3)。
8. `test_prepare_revision_rejects_nul_path_contract_before_create` — freeze なしの発行 E2E。
   destination が作られないことも assert する。
9. `test_prepare_revision_rejects_nul_path_contract_with_existing_freeze` — g1 がある分岐の発行 E2E。
10. `test_validate_condition_freeze_at_rejects_legacy_frozen_nul_path_contract` — 履歴検証 E2E。
    期待 hash は §3 の**実装前に実測した literal**を使い、テスト内で再計算しない。
11. `test_activation_report_marks_legacy_nul_bound_freeze_invalid` — 同じ legacy fixture に対し
    `activation_report_at` 相当を呼び、`condition_freeze_valid` が偽、`freeze_reason_code` が
    `evidence-contract-path-nul`、generation / protected hash が None であることを固定する
    (field 名は実装を読んで合わせる)。

## 3. 親が実装前に実測した独立オラクル (実装後は再計算不能)

`job dir/oracle_probe.py` の出力。テストへ literal として焼き込むこと。

```text
LEGACY_NUL_CONTRACT (bytes literal):
  {"conditions":[{"consumer_requirement":{"path":"orchestrator/campaign/trial_registry.py«NUL»alias"}}]}
  ※ raw に 0x00 は含まれない (JSON escape で表現される)
LEGACY_NUL_CONTRACT の pre-T-739 sha256 = 5203daa58be7cc33303ded109851d9ab9feabc34177a5aa0afef8488ccb6ba7b

現行契約 evidence_contract_sha256 = c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471
現行 g1 protected_sha256          = 853e6c44442780f180997b86819efaa8cbf245ae15d1a37a83e5b9a4ee99286e
現行 g1 generation_number         = 1
実契約の path pointer 数           = 38 (先頭 /conditions/0/required_evidence/0/path、
                                        末尾 /conditions/11/consumer_requirement/path)
malformed 例 {"conditions":{"path":"x«NUL»alias"}} の pre-T-739 sha256
                                   = 4dfcc3159b453a0be03f9bfee6486e8f8711ede15dee1ce1af9915085daa7b1b
```

## 4. 変異事前登録 (DW-M01)

対象 production file = `orchestrator/campaign/s8c_preregistration.py`。
各変異は置換対象が一意であることを harness が検査する。同じ入力を拒否する層が前後に無いことは
`job dir/premise_probe.py` の実測で確認済み (`load_contract_bytes` は別経路で、
`evidence_contract_sha256` の呼出し経路には介在しない)。

| id | 変異 | category | 期待 | 単一理由性 |
|---|---|---|---|---|
| `M1-remove-gate` | `    _assert_no_nul_in_contract_paths(value)\n` → `` (削除) | negative | **KILLED** | **wave 前の実コードの形そのもの**。赤は「NUL path が受理される」1 理由 |
| `M2-first-only` | helper の list 枝を先頭要素だけに切り詰める: `for index, child in reversed(list(enumerate(node))):` → `for index, child in reversed(list(enumerate(node))[:1]):` (`conditions[0]` しか走査されなくなる) | negative | **KILLED** | 38 位置 parametrize だけが殺す。「先頭だけ / 最後だけ検査する」実装の検出力を測る |
| `M3-over-reject` | `if is_path and isinstance(node, str)` → `if isinstance(node, str)` | positive | **KILLED** | **承認外の過剰拒否を検出する正例** (`static_only_note` 受理テストが殺す) |
| `M4-order` | 検査呼出しを `canonical = _canonical_bytes(value)` の**前**へ移す | negative | **KILLED** | reason 順序テストだけが殺す |
| `M5-nul-to-cr` | `"\x00" in node` → `"\r" in node` | negative | **KILLED** | NUL 拒否テストと CR 受理テストの両方が殺す |

- `M2` の anchor 逐語は実装確定後 (段 6 の fix 後 commit) に取り、`DW-M07` に従って再検証してから本走する。
- `hang_risk` は全件 False。`estimated_run_seconds` は 1 run あたりの実測で決める。
- テスト強化だけの wave ではない (production 挙動が変わる) ため `DW-M08` の新旧両走は登録しない。

## 5. scope 外 → 裁定パッケージ (段 7 で spool fragment 化)

- **CR/LF の同型穴 (S1)**: valid v1 の path に CR/LF があると、凍結発行・検証は通り、発効時だけ
  `contract-path-control-char` で倒れる。T-739 と**同じ性質**の穴が残る。裁定 (c) 不採用の射程に
  入るため本 wave では実装しない。選択肢 = (a) NUL と同じ扱いで CR/LF も凍結層で拒否する /
  (b) 現状維持。成果物影響 = (b) のままなら凍結台帳・proof chain の受理集合に CR/LF path 契約が残る。
- **一般 schema 違反契約の凍結可能性**: 裁定 (c) が不採用である以上、再提案しない。
