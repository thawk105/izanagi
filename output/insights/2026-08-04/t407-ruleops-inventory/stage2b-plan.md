## 現行挙動 (行を引く)

- inventory schema は [`tools/ruleops.py:25`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:25) の `ruleops-inventory/v1`。
- scope は `tools/ruleops.py:44-45,443-448` で、直下の `orchestrator/tests/test_*.py` と `output/insights/**` の二族。
- `build_inventory` は `tools/ruleops.py:649-659` で `--kind` を適用し、tracked regular blob だけを `selected` に入れる。
- その全 path に対し、item ループより先に `_batch_blobs` と `_last_changes` を実行する (`tools/ruleops.py:660-661`)。
- item ループの `raw.decode("utf-8", "strict")` は復号結果を使用せず、失敗時に `RuleOpsError("non-utf8")` を送出するだけである (`tools/ruleops.py:663-668`)。CLI はこれを rc=2 にする (`tools/ruleops.py:2218-2220`)。
- `_markers` は bytes を受け、UTF-8 だが不正な JSON は marker 無しとして扱う (`tools/ruleops.py:622-639`)。したがって skip 条件を JSON 妥当性へ広げてはいけない。
- `inspect` は独立して strict decode し、非 UTF-8 target を拒否する (`tools/ruleops.py:1006-1012`)。
- ledger は `_strict_json` の strict decode (`tools/ruleops.py:191-217,2026-2033`)、receipt は `_receipt_document` (`tools/ruleops.py:1307-1324,1676`) を通る。
- 先例は `s8b_holdout_freeze.py:318-343` の「復号不能なら text 集合へ入れず counter を増やす」で、根の `skipped_binary_count` は同 `:345-351` に出る。ただし同先例の NUL 判定は今回へ持ち込まず、strict decode 不能だけを条件にする。

## 実装プラン (file:line 粒度)

1. `tools/ruleops.py:25`

   `INVENTORY_SCHEMA` を `"ruleops-inventory/v2"` へ変更する。RuleOps workflow 自体の「v1」という `:2` の説明は変更しない。

2. `tools/ruleops.py:642-691` の `build_inventory`

   - `items` の初期化直後、item ループ直前 (`現行 :662-663`) に `skipped_non_utf8 = 0` を置く。
   - `:665-668` の decode 失敗分岐を、例外送出から `counter += 1; continue` へ置換する。
   - counter は selected path/item 単位で数える。同じ blob OID が複数 path にある場合も、読み飛ばした item 数だけ増える。
   - 根の dict (`現行 :684-689`) に `"skipped_non_utf8": skipped_non_utf8` を常時追加する。0 の場合も省略しない。
   - retained item の生成 (`:669-683`)、item key、path 順、snapshot 再検査 (`:690`) は変更しない。

変更後の擬似コードは次の形とする。

```python
blobs = _batch_blobs(snap, [entry for _, _, entry in selected])
changes = _last_changes(snap, [path for path, _, _ in selected])

items = []
skipped_non_utf8 = 0
for path, scoped, entry in selected:
    raw = blobs[entry.oid]
    try:
        raw.decode("utf-8", "strict")
    except UnicodeDecodeError:
        skipped_non_utf8 += 1
        continue

    last_commit, changed_at = changes[path]
    artifact_format = _artifact_format(path)
    authority, default_effect = _markers(raw, artifact_format=artifact_format)
    items.append({...既存 item key のみ...})

output = {
    "head": snap.head,
    "items": items,
    "object_format": snap.object_format,
    "schema_version": INVENTORY_SCHEMA,
    "skipped_non_utf8": skipped_non_utf8,
}
_assert_snapshot_current(snap)
return output
```

3. `_batch_blobs` / `_last_changes` の順序は変えない。

   - `_batch_blobs` (`tools/ruleops.py:471-520`) は decode 前に raw bytes を取得しなければならず、payload を文字列として解釈しない。ASCII decode は Git batch header (`:499`) に限られる。missing object、size drift、壊れた batch response は、将来 skip される blob でも引き続き拒否すべき repository integrity failure である。
   - `_last_changes` (`tools/ruleops.py:531-576`) は blob payload を読まず、path と commit metadata だけを扱う。非 UTF-8 payload が混ざっても固有の失敗は増えない。
   - skipped path の履歴結果は未使用になるが、Git `log` は path ごとの個別照会ではなく、固定された二つの pathspec を一回走査する (`:537-548`)。decode 後へ移しても履歴走査量はほぼ減らず、二段ループ化だけが増える。
   - history の非 UTF-8 path token や missing last-change は引き続き `bad-history` (`:555-575`) とする。これは blob payload の skip とは別の境界である。

4. `--kind` の counter は、`tools/ruleops.py:649-659` で選択された族だけを数える。

   - `--kind test`: direct test の読み飛ばしだけを数え、insight の非 UTF-8 は数えない。
   - `--kind insight`: insight だけを数える。
   - `--kind all`: 両族の合計。
   - kind 外を数えると「この出力から何件落ちたか」という根の値でなくなるため不採用とする。symlink/gitlink など、そもそも selected に入らない entry も数えない。

5. 次は変更しない。

   - `inspect`: `tools/ruleops.py:1006-1012`
   - 共通 strict JSON: `tools/ruleops.py:191-217`
   - receipt: `tools/ruleops.py:1307-1324,1666-1677`
   - ledger/check: `tools/ruleops.py:2020-2039`
   - insight candidate 本文: `tools/ruleops.py:1967-1973`
   - direct-test candidate 本文を `check` が decode しない既存の非対称も、本 wave では拡張しない。

## テストプラン (三軸 matrix、nodeid と期待値)

### fixture

[`orchestrator/tests/test_ruleops.py:87`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:87) 付近に、bytes 用 helper を追加する。

```python
def _write_bytes(repo, rel, payload):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
```

`test_ruleops.py:109-150` の `_base_repo` を利用する `inventory_encoding_matrix_repo` fixture を置き、次の全ファイルを `tmp_path` repo 内へ作って commit する。非 UTF-8 payload はすべて同じ `b"\xff\n"` とし、OID の unique 数ではなく読み飛ばした path/item 数を数えることも固定する。

| scope-kind | suffix | 非 UTF-8 | UTF-8 control / `artifact_format` |
|---|---:|---|---|
| direct test | `.py` | `orchestrator/tests/test_encoding_matrix_non_utf8.py` | `test_encoding_matrix_utf8.py` / `python` |
| insight | `.py` | `output/insights/encoding-matrix/non_utf8.py` | `utf8.py` / `python` |
| insight | `.md` | 同 `non_utf8.md` | `utf8.md` / `markdown` |
| insight | `.json` | 同 `non_utf8.json` | `utf8.json` / `json` |
| insight | `.raw` | 同 `non_utf8.raw` | `utf8.raw` / `other` |

`.json` control は strict UTF-8 decode 可能だが `_strict_json` では不正となる BOM 付き JSONなどにし、それでも item に残ることを固定する。

direct test の `.md/.json/.raw` セルは作らない。`_TEST_PATH_RE` (`tools/ruleops.py:44`) が `.py` のみを direct test と定義しており、そのセルを作るには D99 の scope 自体を変更する必要がある。suffix 独立性は insight 四種、scope-kind 独立性は共通 suffix `.py` の二族で固定する。

### 新規 nodeid

- `orchestrator/tests/test_ruleops.py::test_inventory_non_utf8_skip_matrix_and_utf8_formats`

  期待値:

  - root key 集合が更新後の `_INVENTORY_ROOT_KEYS`
  - `schema_version == "ruleops-inventory/v2"`
  - `type(skipped_non_utf8) is int`
  - `skipped_non_utf8 == 5`
  - 非 UTF-8 の5 pathがすべて `items` に無い
  - UTF-8 control の5 pathがすべて存在
  - control の `(kind, artifact_format)` が表どおり
  - control item の key 集合が `_INVENTORY_ITEM_KEYS` と完全一致

- `orchestrator/tests/test_ruleops.py::test_inventory_non_utf8_count_tracks_selected_kind_and_actual_skips`

  初回期待値を `all/test/insight == 5/1/4` とする。その後、親を `mkdir(parents=True)` して同じ非 UTF-8 bytes の insight `.raw` をもう1 path追加・commitし、`6/1/5` になることを確認する。これで定数 counter、kind 外まで数える実装、unique OID 数を数える実装を拒否する。

- `orchestrator/tests/test_ruleops.py::test_inspect_non_utf8_target_fails_closed_without_traceback`

  fixture の非 UTF-8 direct test を `_run_cli(repo, "inspect", path)` へ渡し、`returncode == 2`、stderr に `non-utf8`、stdout が空、`Traceback` 無しを期待する。`inspect` の fail-closed を inventory 変更から独立して固定する。

### 既存 assertion

`test_ruleops.py:52` は次へ更新する。

```python
_INVENTORY_ROOT_KEYS = {
    "schema_version", "head", "object_format", "items", "skipped_non_utf8",
}
```

これは弱体化ではない。更新後も次を固定し続ける。

- root key の欠落と未知 key の双方を exact equality で拒否
- `test_ruleops.py:306-312` の既存 UTF-8 item path と順序
- `:313` の item key 完全集合。`:53-57` は変更しない
- `:314-317` の kind と scope 外除外
- 新規テストによる schema literal、counter 型・値、skip path、UTF-8 control format

既存挙動への影響は次のとおり。

- `test_m1_m2_inventory_literal_scope_and_exact_keys` の `:305` は5 root keyを要求するようになるが、既存 item 期待値は変更しない。fixture は全て UTF-8 なので新 counter は0。
- `test_real_checkout_independent_maximum_package_and_runner_preflight` の `:1719-1729` は、従来の rc=2 で止まらず JSON を取得できる。`:1731` は更新後の exact root key、`:1732-1742` は retained item の非空性・既存 test path・kind を従来どおり検査する。real probe bytes の件数は新規テストの期待値に使わない。
- `test_duplicate_nonutf8_unknown_ledger_fail_closed_without_traceback` (`:382-403`) は `check` 経路であり、`validate_candidate_ledger` の `_strict_json` は不変なので、非 UTF-8 parameter は引き続き rc=2 / `non-utf8` / traceback無しとなる。

## 受理集合と出力の形の変化

kind ごとの selected regular path 集合を `S`、strict UTF-8 decode 不能な部分集合を `B` とする。

- 変更前: `B` が空の場合だけ inventory 成功。
- 変更後: Git object、履歴、snapshot 境界など他の検査が通れば `B` が非空でも成功し、`items` は `S \ B`、`skipped_non_utf8` は `|B|` となる。
- kind 外、scope 外、非 regular entry はこの受理差分に含まれない。

出力は root が4 keyから5 keyへ変わり、schema は v1 から v2へ変わる。item keyと retained item の値・順序は変わらない。skipped path や binary itemは一切出さない。

変更後も最低限、次は拒否し続ける。

- 非 UTF-8 の `inspect` target: `tools/ruleops.py:1006-1012`
- 非 UTF-8 ledger: `tools/ruleops.py:200-203,2026-2033`
- 非 UTF-8 receipt: `tools/ruleops.py:1307-1324,1676`
- invalid `kind`: `tools/ruleops.py:645-646`
- shallow repo、replace refs、grafts: `tools/ruleops.py:410-424`
- missing/corrupt blob、batch size/header drift: `tools/ruleops.py:485-520`
- 非 UTF-8 history token、last-change 欠落: `tools/ruleops.py:555-575`

## test 族の読み飛ばし危険性の評価

`--kind test` で `skipped_non_utf8 > 0` なら、一覧が correctness 防壁の全体像ではないことは検出できる。しかし件数だけでは、どの test が消えたか、実行可能な別 encoding の Python source か、単なる凍結 bytes かを判別できない。したがって件数は「不完全性の警告」には足りるが、調査・退役裁定・網羅性の根拠には足りない。

運用上は、test counter が正なら inventory を「全 direct test を確認済み」と解釈してはいけない。対象特定が必要なら、現在の path 非出力裁定を破らない別の診断経路または encoding policy が必要になる。この必要性は所見として残し、本 wave の実装へは入れない。

## docs/ruleops.md の更新箇所

- `docs/ruleops.md:19`「対象と inventory」、現行 `:36-38` の後:

  - inventory JSON schema が `ruleops-inventory/v2`
  - strict UTF-8 decode 不能な selected regular blobだけを items から除外
  - suffix、path、JSON/Python妥当性では判定しない
  - 根に常時 integer `skipped_non_utf8`
  - count は selected path/item 単位
  - `--kind` 指定時はその族だけを数える
  - skipped pathは出さない

- `docs/ruleops.md:169`「既知限界」:

  - `--kind test` の正 counter は inventory が不完全であることだけを示し、対象特定や correctness guard の網羅確認には使えないこと。

## 変異と検出

| 変異 | 赤になる nodeid / assertion |
|---|---|
| (a) `.raw` の decode failureだけ `continue` | `::test_inventory_non_utf8_skip_matrix_and_utf8_formats`。非 UTF-8 `.py/.md/.json` で例外、または binary path 不在・count 5 assertion が失敗 |
| (b) `scoped == "insight"` のときだけ skip | 同 nodeid。非 UTF-8 direct test `.py` で例外または path 不在が失敗。`::test_inventory_non_utf8_count_tracks_selected_kind_and_actual_skips` の test count 1も失敗 |
| (c) decodeせず全 itemを `continue` | `::test_inventory_non_utf8_skip_matrix_and_utf8_formats`。UTF-8 control 5 pathと format mapが欠落 |
| (d) counterを定数化、または実際の skip と無関係に上書き | `::test_inventory_non_utf8_count_tracks_selected_kind_and_actual_skips`。`5/1/4` と追加後 `6/1/5` の少なくとも一方が失敗 |
| (e) 現行どおり decode failure を raise | `::test_inventory_non_utf8_skip_matrix_and_utf8_formats` が `RuleOpsError("non-utf8")` で失敗 |
| (f) skipするが counterを増やさない／根へ出さない | `::test_inventory_non_utf8_skip_matrix_and_utf8_formats` の exact root、key access、値5が失敗。根ごと無い場合は既存 `::test_m1_m2_inventory_literal_scope_and_exact_keys` も失敗 |

## 反論 (P5・P6 と本プラン自身への)

- P5 への反論は「JSON の追加 key は loose consumer には後方互換なので v1 のままでもよい」。しかし本 repo は root exact集合を契約として検査しており、必須 root shape と意味が変わる。`ruleops-inventory/v1` の repo 内 consumerも定義箇所以外に見当たらないため、P5 の v2 を採る。
- P6 は名称だけでは kind-filter 済み件数か全 scope 件数か分からない。ただし今回の直接裁定で key 名は確定しており、改名案は出さない。曖昧さは docs と kind matrix で閉じる。
- 完全な `2 content × 4 suffix × 2 scope-kind` の16セルは作れない。direct test は `_TEST_PATH_RE` により `.py` しか scope に入らない。人工的な monkeypatch や scope 拡張で `.md/.json/.raw` を test 扱いするとD99を破るため、production-validな10セル構成を採る。
- `_last_changes` を decode 後へ移す案は、固定二族を一回走査する Git log の量を減らさず、局所修復を二段処理へ広げる。非 UTF-8 payload由来の失敗も無いため順序維持が妥当。
- counterを unique OID 数とする余地はあるが、裁定は「itemsから読み飛ばした件数」であり、inventory item は path 単位である。本プランは path/item 件数に固定する。

## 総括

変更面は `tools/ruleops.py` の schema定数と `build_inventory`、`test_ruleops.py` の root key・三軸fixture・3テスト、親が行う `docs/ruleops.md` 更新に限定する。非 UTF-8 blobは binary item化せず、selected itemから除外して根の件数だけを出す。`inspect`、ledger、receipt、その他Git/snapshot境界は緩めない。

read-only のため編集・commit・pytest実走はしておらず、テスト緑は主張しない。