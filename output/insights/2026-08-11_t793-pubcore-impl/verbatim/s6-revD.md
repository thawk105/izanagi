## 総括

**NO-GO。** read-only 静的レビューのみ実施し、テストは実走していない。

blocker 2 件、must-fix 2 件を確認した。

- 受入全走は plain-runner meta-test で確実に赤になる。
- `spool_fold.py` は marker を含まない既存入力まで新規拒否し、既存受理集合を縮めている。
- D291 projection API は caller が偽 payload を作れてしまう。
- 変異事前登録の複数項目で期待 node・単一理由性が成立しない。

一方、§10.4 の判定は親裁定どおり、**実成果物経路 0/11、直接 helper/parser のみ #7・#9 の 2/11**で正しい。

## 所見

### D1 — severity: blocker — 新規 test 2 本が self-runnable 契約違反

**根拠:** `orchestrator/tests/test_plain_runner_coverage.py:60-74` は、全 `test_*.py` に self-runner または allowlist 登録を要求する。ところが次の 2 file は `__main__` を持たず、allowlist にもない。

- `orchestrator/tests/test_t793_addendum_p_envelope.py:23-50`
- `orchestrator/tests/test_t793_approval_guard.py:46-123`

**落ちる具体経路:** 受入形 `python3 tools/run_tests.py` は `orchestrator/tests` 全体を対象とする（`tools/run_tests.py:505-563`）。`test_every_test_file_is_self_runnable_or_allowlisted` が上記 2 file を offenders として赤にする。

**成果物影響:** 受入 receipt を作れず land 不能となるため、certified 選択・材料レポート・公表台帳の変更はいずれも canonical main に入らない。

---

### D2 — severity: blocker — marker 無しの既存 fragment も新規拒否する

**根拠:** marker 検査前に `read_pinned_blob()` を実行し、pin 解決失敗自体を `ApprovalGuardError` にする（`orchestrator/publication/approval_guard.py:105-128`）。`spool_fold.py` はこれを `_discover()` と `apply_fold()` の双方で拒否する（`tools/spool_fold.py:1038-1069`, `tools/spool_fold.py:2354-2356`）。

**落ちる具体入力:** 次のような、exact marker を一切含まない decision fragment。40/64 hex の形は正しいが commit が存在しない。

```text
approved_blobs:
  publication_core
    path   = approved.md
    commit = 0000000000000000000000000000000000000000
    sha256 = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

従来は spool 文法として通ったが、現在は pin 解決失敗で拒否される。しかも issue code は実際の理由にかかわらず `unresolved-approval-marker` になる（`tools/spool_fold.py:1042-1049`）。

P2 はこの回帰を覆わない。P2 は `approved_blobs:` を持たない草案 bytes と noop plan しか検査していない（`orchestrator/tests/test_t793_approval_guard.py:46-50`）。

**成果物影響:** marker と無関係な既存 decision fragment の fold が止まり、canonical decisions とそれを参照する材料レポートが更新不能になる。依頼の「既存受理集合を縮めない」に直接違反する。

---

### D3 — severity: must-fix — `require_d291_projection_exact` の D291 束縛を caller が偽造できる

**根拠:** `D291ApprovalPayload` は public export された通常の dataclass（`orchestrator/publication/__init__.py:3-20`, `orchestrator/publication/approval_d291.py:170-183`）。`require_d291_projection_exact()` は型だけを確認し、固定 `F_p` を再読せず、caller が渡した `approved_values` と `value_projection` をそのまま信頼する（`orchestrator/publication/approval_d291.py:490-514`）。

**通ってしまう具体入力:** canonical payload を次のように置換した object は、D291 が承認していない値 `2` を「exact」として通せる。

```python
forged = dataclasses.replace(
    load_d291_payload(root),
    approved_values=(("p01.candidate_cap", Decimal("2")),),
    value_projection=(("p01.candidate_cap", "p01.candidate_cap"),),
)
require_d291_projection_exact(forged, {"p01.candidate_cap": 2})
```

公開 loader 自体は `F_p` 固定だが、この API では caller がその検査済み属性を偽造できる。

**成果物影響:** 将来の追補 P consumer がこの公開 API を使うと、D291 非承認値を材料レポートで「D291 exact」と扱いうる。現時点で production caller がないため certified 選択にはまだ波及しない。

---

### D4 — severity: must-fix — 変異事前登録の期待 node・単一理由性が不成立

**根拠と具体的な不成立:**

| 変異 | 判定 | 不成立理由 |
|---|---|---|
| M1 | △ | D292 固定化は P1 だけでなく、`load_d291_payload()` を使う resolver・projection・report の多数 node を同じ入口で落とす（`test_t793_approval_d291.py:69-82`, `251-286`）。「正例テストだけ」は過小。 |
| M2 | △ | `_TOP_LEVEL_KEYS` から key を消すと canonical P1 自体が `actual != expected` で先に落ちる（`approval_d291.py:265-279`）。期待 node は P1 と明記する必要がある。 |
| M3 | ○ | `document_relations` は exact section digest の対象外で、専用 normalized digest が拒否するため単一理由（`approval_d291.py:293-321`, `test_t793_approval_d291.py:156-174`）。 |
| M4 | × | bytes 負例は `approved_blobs` 節 digest が先に拒否する（`approval_d291.py:126-145`, `452-465`）。resolver の extra-role node（`test_t793_approval_d291.py:277-286`）へ明示的に再照準しない限り mask される。 |
| M5 | × | 同一 path・別 digest の bytes 負例は section digest で先取りされる（`test_t793_approval_d291.py:144-153`）。resolver 側には「同じ path/commit、sha256 だけ違う candidate」の node が存在しない。 |
| M6 | ○ | signature と TypeError を直接検査する node がある（`test_t793_publication_ledger.py:110-117`）。 |
| M7 | ○ | kind 以外を canonical に保った専用負例で、`ledger-kind` だけを観測する（`ledger.py:198-225`, `test_t793_publication_ledger.py:154-158`）。 |
| M8 | × | marker tuple を空にすると parametrize node 自体が消える（`test_t793_approval_guard.py:63-73`）。さらに後続 2 node は `[0]` / `[1]` で gate より前に `IndexError` になる（同 `81`, `98`）。 |
| M9 | △ | `apply_fold()` 結線を外すと resume node だけでなく direct-plan node も赤になる（`test_t793_approval_guard.py:76-89`, `92-123`）。期待 node 集合が不足。 |
| M10 | × | `{p01,p02}` 化すると missing-p03 負例が通る一方、P3 正例が `p03` extra として先に落ちる（`test_t793_addendum_p_envelope.py:23-32`）。期待 node は最低 2 本必要。 |
| M11 | △ | `submission_authority` は role-level と top-level の 2 箇所にあり anchor が非一意（`report.py:209-223`, `224-240`）。期待 node も report 本体と CLI の複数（`test_t793_report.py:20-32`, `98-108`）。 |
| M12 | ○ | synthetic D999 の単独 node が実在する（`test_t793_report.py:54-77`）。 |

**成果物影響:** mutation ledger の kill 理由と失敗 node 参照が実体と一致せず、試行台帳が「どの gate を証明したか」を正しく記録できない。

## §10.4 の 11 変異

記号は、○＝実成果物経路で拒否、△＝直接 helper/parser だけ、×＝拒否経路なし。

| # | 判定 | 根拠 |
|---:|:---:|---|
| 1 | × | cluster 全件性を検査する source/publication validator がない（`publication-core-v2.md:686-689`）。 |
| 2 | × | 6 行固定表の validator/renderer がない（同 `687-689`）。 |
| 3 | × | `qualification_status` 再計算・複写 validator がない（同 `686-688`）。 |
| 4 | × | 共分散から公表値を算出する validator がない。 |
| 5 | × | Holm 実装・丸め前比較 gate がない。 |
| 6 | × | 多重比較法を閉じる実行時 gate がない。 |
| 7 | △ | direct ledger parser は閉集合外 kind を拒否する（`orchestrator/publication/ledger.py:204-208`）。実 ledger は 0 entry で writer/caller がない。 |
| 8 | × | parser は同一 `(root,kind,ordinal)` の重複しか拒否せず、正の別 ordinal は受理する（`ledger.py:216-225`, `236-251`）。第2 core/candidate cap は閉じていない。 |
| 9 | △ | exact-key wrapper は extra field を拒否するが、production caller がない（`addendum_p_envelope.py:1-5`, `21-28`）。 |
| 10 | × | stress dataset の除外・再抽出を検査する validator がない。 |
| 11 | × | certified 選択 consumer への結線自体がない。report は deny-only（`report.py:1`, `237-239`）。 |

したがって、親裁定の **実成果物 0/11、直接負例 #7・#9 の 2/11** は過大でも過小でもない。

## 受入・land 経路

| 検査 | 静的判定 |
|---|---|
| `tools/run_tests.py` 受入形 | **赤。** D1 の plain-runner meta-test が失敗する。 |
| `tools/check_docs.py` | 新規 docs 自体による赤はない。ただし `validate_spool_tree()` を実行するため（`tools/check_docs.py:797-848`）、D2 の入力が spool にあれば同じ過剰拒否で赤。 |
| `test_frozen_artifacts.py` | 新 ledger は固定 23 path manifest に含まれず、独立した赤なし（`test_frozen_artifacts.py:38-85`, `125-153`）。 |
| `test_plain_runner_coverage.py` | **赤。** D1。 |
| `tools/dev_wave_land.py` | 現在は全新規 file が untracked なので、今 land すれば wave-clean gate で拒否（`tools/dev_wave_land.py:887-889`, `1315-1321`）。commit 後は通常の target blob として扱われる。 |
| ignored/untracked collision | `__pycache__` は ignored だが source target の sibling であり、個別 target との collision ではない。main に同名 untracked/ignored target があれば拒否される（`tools/dev_wave_land.py:865-870`, `1007-1019`）。 |
| AI provenance | 将来の実装 commit に Codex `role=author` trailer が無ければ赤（`tools/check_ai_provenance.py:1090-1103`, `1106-1136`）。現時点では未 commit なので監査対象 commit はまだない。 |

**0-byte file を内容だけで拒否する指定検査は見つからなかった。**むしろ ledger parser と P4 は `b""` を正規の「存在・予約 0 件」として明示受理する（`ledger.py:228-232`, `test_t793_publication_ledger.py:78-84`）。ただしレビュー時点ではまだ tracked ではなく untracked である。

## 並行 wave

`git status --short` と `git diff --name-only` で、本 wave が次を変更していないことを確認した。

- `orchestrator/preregistration/blobref.py`
- `orchestrator/preregistration/erratum.py`
- `orchestrator/tests/test_t139_preregistration_binding.py`

land 2 側ではこの 3 file が branch commit で変更されているが、path-level merge conflict はない。

本 wave が先に main へ入った場合の面は次のとおり。

- D1 を直さず入れることはできないが、仮に入れば land 2 の受入全走も同じ meta-test で赤になる。
- T-793 は共有 `BlobRef/read_pinned_blob` を import している（`approval_d291.py:18`, `approval_guard.py:14`）。land 2 の hardening 後も API/class hierarchy は互換だが、共有 trust-root 実装が変わるため、land 2 統合 snapshot で T-793 tests を再受入する必要がある。
- land 2 の現行 decision fragment には `approved_blobs:` がないため、D2 の新設 spool gateが現時点で land 2 fold を直接止める経路はない。

## 裁定パッケージ候補

本 wave 外として維持すべきものは、親裁定どおり source 本走 admission、予約原子性、cross-worktree `(root, ordinal)` 一意性である。コードもこれらを明示的には謳っていない（`approval_d291.py:1-6`, `ledger.py:1-6`, `addendum_p_envelope.py:1-5`）。

別裁定が必要なのは既存 R4、すなわち「blob authority を与える全 decision に機械可読 schema を必須化するか」。現 guard は不完全・重複 triple を黙って target 外にする（`approval_guard.py:65-80`）ため、この範囲を本 wave で「全承認 gate」へ拡張したとは扱えない。