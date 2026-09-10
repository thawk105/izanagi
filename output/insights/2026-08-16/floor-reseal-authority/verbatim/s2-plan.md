## 設計

親の P1、P3〜P6 は採用する。P2 は「最新らしきファイル」ではなく、既存固定 protocol を lineage anchor とする形へ具体化する。根拠は裁定原文 `rulings-inbox/2026-08-16-floor-reseal-ai-authority.md:21-37`、18 field の正本 `orchestrator/campaign/s8b_floor_contract.py:36-42` である。

1. **格納 path**

   新 namespace を `output/s8b-freeze/floor-protocols/` とし、組 `(c, p)` から次式で一意に導出する。

   ```text
   P(c, p) =
     output/s8b-freeze/floor-protocols/
     {c}--{p}.json
   ```

   `c` は 64 桁小文字 hex、`p` は 40 桁小文字 hex に限定する。公開 API は `reseal_protocol() -> dict[str, object]` の零引数とし、path、contract、pin、先行 protocol を受け取らない。

   既存 `output/s8b-freeze/floor_protocol.json` は legacy anchor として別名のまま残す (`s8b_floor_campaign.py:161`)。新 path の例外を `write_protocol_document()` に足してはならない。同関数は引き続き凍結領域全体を拒否する (`s8b_floor_campaign.py:679-744`)。専用 issuer だけが導出済み path を `_write_protocol_document_create_only()` (`:687-723`) へ渡す。これにより任意 path writer は開かない。

   本 wave は source/test のみを追加し、実 repo に当該 directory や protocol artifact を作らない。`FROZEN_MANIFEST` と 23-key pin は不変更 (`orchestrator/tests/test_frozen_artifacts.py:41-117`)。

2. **組 index**

   `scan_floor_protocol_index(*, root=ROOT)` の走査集合を、次の閉集合とする。

   - 必須 legacy: `output/s8b-freeze/floor_protocol.json`
   - 存在する場合の `output/s8b-freeze/floor-protocols/` 直下の全 directory entry

   legacy の欠落、symlink、非 regular file は拒否する。新 directory 自体の symlink、配下の directory、symlink、非 protocol file、予期しない名前も無視せず拒否する。directory がまだ存在しないことだけは正常とする。

   各ファイルは既存の duplicate-key・非数値定数拒否 parser (`s8b_floor_campaign.py:386-415`) で strict parse し、`validate_protocol()` の歴史 resolver (`:539-544`) で検証する。新 namespace の各 entry はさらに以下を要求する。

   - 実 path が `P(contract_sha256, ccbench_pin)` と完全一致する。
   - raw bytes が、anchor の 16 fieldと当該組から再構築した canonical bytes に一致する。
   - legacy を含め、同じ組が既に index にあれば両 path を示して拒否する。

   戻り値は `(contract_sha256, ccbench_pin) -> IndexedFloorProtocol` の一意 mapping とする。legacy は path 式の唯一の例外だが、組 index からは決して除外しない。

3. **不変 16 field の継承**

   `s8b_floor_contract.py:36-42` に次を追加する。

   ```python
   _AI_RESEAL_MUTABLE_FIELDS = frozenset({
       "contract_sha256", "ccbench_pin",
   })
   _AI_RESEAL_INHERITED_FIELDS = _PROTOCOL_KEYS - _AI_RESEAL_MUTABLE_FIELDS
   ```

   import 時 assertion でそれぞれ 2 件、16 件、和集合が exact 18 field であることを固定する。`validate_ai_reseal_inheritance(predecessor, successor)` は、16 field を field ごとの canonical JSON bytes で比較する。Python の `==` だけにせず、`1` と `1.0`、nested `freeze`、list 順序も区別する。

   先行 protocol は常に legacy 固定 path とする。versioned protocol が複数あっても mtime、辞書順、Git の「最新」を authority にしない。18-field schema には predecessor pointer がなく、最新選択を導入すると追加ファイルが次回の16 fieldを選べるためである。新 namespace の全 entry は同じ anchor の子として検証する。将来、人間が16 fieldを改訂して新 lineage を始める場合は別裁定とする。

   issuer は anchor の normalized document を `deepcopy` し、2 field だけ置換する。`s8b_approved.py:46-67` から16 fieldを再導出しない。

   責務分担は次のとおり。

   - `validate_protocol()` (`s8b_floor_contract.py:106-228`): 単一 document の18-key schema、型、承認 pin、contract cross-field。
   - `validate_ai_reseal_inheritance()`: 2 document 間の16 field byte-exact 継承。
   - `scan_floor_protocol_index()`: file set、path、canonical bytes、組の大域一意性。
   - create-only writer: publish 時の同一 path 上書き拒否。

4. **可変 2 field の取得**

   `contract_sha256` は anchor の不変 `env_tag` を使って `_env_contract.lookup(anchor["env_tag"])` から得る。`REGISTRY` は activation 駆動 view であり (`env_contract.py:615-628`)、`lookup()` が active contract を返す (`:706-713`)。

   `ccbench_pin` は `_ccbench_gitlink(ROOT)` による `git ls-tree HEAD external/ccbench` の実測値とする (`s8b_floor_campaign.py:565-582`)。`s8b_approved.CCBENCH_FULL_SHA` は新経路では参照しない。

   両値は公開関数・CLI の引数にしない。build 後、publish 直前にも active contract と HEAD gitlink を再照合し、途中で変化していれば書かずに拒否する。

   target pair が既に index にある場合は no-op 成功にせず拒否する。したがって両 field が anchor と一致する場合も、legacy が index に入るため必ず拒否される。

5. **2 件目拒否の 2 層**

   - 発行時: full index を先に構築し target pair の存在を拒否する。その後も導出 path への atomic create-only hard link と、read-back、post-write full index 再走を行う。検証失敗時は既存 `freeze_protocol()` と同様、自動削除せず commit 禁止の失敗にする (`s8b_floor_campaign.py:799-819`)。
   - 常設検査: `orchestrator/tests/test_s8b_protocol_builder.py` に real-repo の `scan_floor_protocol_index(ROOT)` を必ず実行するテストを置く。legacy とその derived path に同じ bytes を置く positive control で、legacy を索引から外す変異と duplicate 判定を外す変異を殺す。

   これは `FROZEN_MANIFEST` の exact path→SHA pin (`test_frozen_artifacts.py:41-117`) と重複しない。manifest は既存23件の bytes、`validate_protocol` は単体 document、create-only は単一 destination を検査するだけであり、いずれも repo 内の組重複を検出しない。

6. **CLI**

   `s8b_floor_campaign.py:5658-5680,5783-5799` の既存 dispatch に、零引数の2 commandを追加する。

   - `reseal-protocol`: `reseal_protocol()` を呼び、成功時に path、組、byte length、SHA-256 を JSON 出力する。
   - `check-protocol-index`: read-only scan を行い、path、組、protocol SHA-256 の決定的な配列を JSON 出力する。

   `freeze-protocol` の parser、`--confirm-user-freeze`、isatty、T-080 receipt、固定 destination のコード (`s8b_floor_campaign.py:747-825`) は一行も変更しない。通常 campaign parser (`:5658-5671`) の受理集合も変えない。

7. **read-only dogfood**

   親が実 repo で一度通すコマンドは次とする。

   ```bash
   python3 -B -m orchestrator.campaign.s8b_floor_campaign check-protocol-index
   ```

   現状は count 1、legacy path、組 `(e576e9cd…e242c01, d706650c…40969)`、protocol SHA-256 `261cec1c…74aac` を返す。`-B` で bytecode 書込みも抑止する。この command は index 構築以外を行わない。

8. **正例と拒否例**

   公開署名は `reseal_protocol() -> dict[str, object]`。将来 pegasus g2 が active で HEAD gitlink が現在値の場合、次が正例となる。

   ```text
   anchor = (e576e9cd…e242c01, d706650c…40969)
   target = (1346c20b…87ad1c, 511c9538…b706ec)
   path   = output/s8b-freeze/floor-protocols/
            1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c--
            511c9538e4e8efa54b45cda62e72389ed3b706ec.json
   ```

   この document は2 fieldだけが異なり、残る16 fieldは legacy anchor と byte-exact である。本 wave ではこの正例を tmp repository のテストだけで作り、実 repo では発行しない。

## 変更計画

| ファイル | 現在の行 | 追加・変更 | 責務 |
|---|---:|---|---|
| `orchestrator/campaign/s8b_floor_contract.py` | 36-42、231-243 の後 | `_AI_RESEAL_MUTABLE_FIELDS`、`_AI_RESEAL_INHERITED_FIELDS`、canonical field bytes helper、`validate_ai_reseal_inheritance()` を追加 | exact 2/16 field 分割と cross-document byte-exact 継承 |
| `orchestrator/campaign/s8b_floor_campaign.py` | 161 付近 | `_FLOOR_PROTOCOLS_REL` と pair/path 形式定数を追加 | 新 namespace と決定的 path の単一源 |
| 同上 | 386-415 の後 | raw bytes を一度だけ読み strict parse する内部 helper を追加。既存 `load_protocol()` の受理集合は維持 | index で duplicate key、UTF-8、canonical bytes を fail-closed に扱う |
| 同上 | 556-584 の前後 | `IndexedFloorProtocol`、`_derived_reseal_protocol_relpath()`、`scan_floor_protocol_index()` を追加 | legacy を含む閉じた file set、歴史 validate、path/組/継承の大域検査 |
| 同上 | 676-746 の間 | `_build_ai_resealed_protocol()`、`_reseal_protocol_at_root()`、零引数 `reseal_protocol()` を追加 | live 2 field取得、anchor copy、事前重複拒否、create-only publish、read-back、post-index |
| 同上 | 5674-5800 | 新2 parser と dispatch を追加 | `reseal-protocol` と read-only `check-protocol-index` |
| `orchestrator/tests/test_s8b_protocol_builder.py` | 40-269 の後 | index、inheritance、AI reseal、CLI の正負テストを追加 | 2/16境界、source、path、duplicate、create-only、read-only dogfood の mutation kill |

変更しない対象は `freeze_verification_hold.py:14-62`、`s8b_approved.py:46-67`、`test_frozen_artifacts.py:41-117`、`s8b_floor_campaign.py:747-825`、既存 consumer の固定 path (`tools/pegasus/floor_campaign.sh:947`) である。

## テスト計画

read-only 段のため、ここでは実走せず nodeid と kill 対象だけを事前登録する。

### 正例

| nodeid 案 | 確認内容 | 殺す変異 |
|---|---|---|
| `test_s8b_protocol_builder.py::test_floor_protocol_pair_index_real_repo_contains_legacy_anchor` | 実 repo の index が legacy 1件を含む | legacy path を走査集合から外す |
| `...::test_ai_reseal_successor_uses_active_contract_and_head_gitlink_only` | g2 contract と別 gitlink を与えた内部 build で2 fieldだけ変わる | predecessor 値または `s8b_approved` 定数を焼く |
| `...::test_ai_reseal_successor_inherits_exactly_16_canonical_field_bytes` | 16 fieldの canonical bytes が anchor と一致 | mutable 集合を3 field以上へ広げる、再導出する |
| `...::test_reseal_protocol_writes_only_derived_create_only_path` | tmp repo で組から導出した1 pathだけ作る | caller path、固定 path、別命名を使う |
| `...::test_check_protocol_index_cli_is_read_only_and_deterministic` | 前後 tree 同一、同じ JSON 順序 | checker が directoryやcache artifactを書き込む、順序を filesystem 任せにする |

### 負例

| nodeid 案 | 拒否内容 | 殺す変異 |
|---|---|---|
| `...::test_floor_protocol_pair_index_rejects_duplicate_legacy_pair` | legacy とその derived path に同一 pair | fixed path の索引漏れ、pair重複判定削除 |
| `...::test_floor_protocol_pair_index_rejects_misderived_path` | valid document を別名で配置 | path/document 束縛削除 |
| `...::test_floor_protocol_pair_index_rejects_closed_set_violation[symlink-directory-nonjson]` | symlink、nested directory、未知 entry | 不明 entry を黙って skip |
| `...::test_floor_protocol_pair_index_rejects_malformed_member[duplicate-key-invalid-json-extra-key]` | 壊れた protocol | permissive JSON parse、validation省略 |
| `...::test_ai_reseal_inheritance_rejects_each_immutable_field_mutation[...]` | 16 fieldを個別に変異 | 対応 field を継承集合から外す。parameter id は `schema`、`formula`、`env_tag`、`freeze`、`stock_configuration`、`n_sessions`、`reps`、`master_seed`、`schedule_algorithm`、`extime_s`、`wired_min_rel_floor`、`retry_slots_per_cell`、`session_cv_max`、`cell_cv_max`、`scale_adequacy_rel_tolerance`、`allowed_excluded_reasons` |
| `...::test_reseal_protocol_rejects_unchanged_pair_without_writing` | live 2 field が既存 pair と一致 | duplicate を no-op success にする |
| `...::test_reseal_protocol_second_issue_preserves_first_bytes` | 同じ target を2回発行 | create-only を overwrite/replace にする |
| `...::test_reseal_protocol_cli_rejects_path_contract_and_pin_options` | `--path`、`--contract-sha256`、`--ccbench-pin` | caller-controlled入力面を追加 |
| 既存 `...::test_writer_rejects_real_repo_freeze_dir` | generic writer の凍結領域拒否 | 新 namespace を generic writer の例外にする |
| 既存 `...::test_freeze_protocol_confirm_flag_is_required`、`...::test_freeze_protocol_non_tty_is_refused_even_with_active_receipt` | 人間用経路の既存防壁 | 新 dispatch のため既存 freeze 分岐を緩める |

## 受理集合の差分

| 区分 | 内容 |
|---|---|
| 新規受理 | active contract と HEAD gitlink から得た未使用 pairで、legacy anchor の16 fieldを byte-exact 継承した canonical protocolを、導出 pathへ一度だけ追加する `reseal_protocol()` |
| 新規受理 | strict scanが成功した protocol index を表示する read-only `check-protocol-index` |
| 依然拒否 | 同じ pair の2件目。legacy と derived path の重複も含む |
| 依然拒否 | 16 fieldのうち1 fieldでも異なる AI reseal |
| 依然拒否 | caller指定 path、contract、pin、先行 protocol |
| 依然拒否 | malformed JSON、duplicate key、未知 key、非 canonical derived bytes、誤った派生 path、symlink |
| 依然拒否 | generic `write_protocol_document()` による `output/s8b-freeze/` 配下への書込み |
| 変化なし | `validate_protocol()` の単体受理集合、既存 builder、既存 campaign CLI |
| 変化なし | `freeze-protocol` の confirm、TTY、T-080 receipt、固定 path create-only |
| 変化なし | 固定 consumer、23-key `FROZEN_MANIFEST`、hold 状態、承認定数 |

案3を文字どおり適用するため、pair の片方だけが変わっていても、live source由来かつ未使用なら新経路自体は受理する。実 repo でそれを発行するかは次節の Q3 問題と分離する。

## リスクと未解決

1. **Q3 の事前阻止をどの層で行うか。** この最小設計の零引数 CLI は、現時点でも `(g1, HEAD pin)` を構築できる。P6 は「本 wave では実行しない」という運用境界であり、機構自体の拒否ではない。D272 (`docs/decisions.md:12507-12531`) と、D437を部分 supersede した裁定 (`:18175-18246`) を機械化するなら、上位 lockstep receipt を issuer に要求する必要がある。単に「anchor と contract が違うこと」を足す案は、未裁定の one-protocol-per-contract 規則になるため採らない。段4では、現 scope の運用境界を採るか、receipt実装まで scopeを広げるかの裁定が必要である。

2. **先行 protocol authority。** 推奨は legacy 固定 anchor。mtime、path順、Git最新を使う案は、追加者に次の16 fieldを選ばせるため却下する。将来の人間による16 field改訂を AI lineage の新 anchor にしたい場合、明示 pointerまたは lineage generation が必要で、本 wave の18-field protocolだけでは表現できない。

3. **将来 artifact と `FROZEN_MANIFEST`。** 本 plan は derived pathと固定16 fieldから versioned artifact の全 canonical bytesを再導出して検査するため、新 keyを既存 manifestへ足さない。将来も literal path→SHA台帳への収録を要求するなら、23-key lockと衝突するため別裁定が必要である。

4. **人間による非2-field改訂。** 権限は人間に残るが、新 namespace は AI lineage専用であり、異なる16 fieldを受理しない。既存 `freeze_protocol()` も固定 path create-only のため、将来の人間版 revision mechanism は本 wave の scope外である。

推奨択では実装上の blocker はない。Q3 を issuer 内で機械化する選択だけは、上位束の入力契約が無いため本 planへ暗黙追加してはならない。

## 総括

AI reseal は公開零引数 API とし、contract と pin と path を呼び手に選ばせない。  
新 path は `(contract_sha256, ccbench_pin)` から一意に導き、既存固定 pathは legacy anchorとして残す。  
16 fieldは anchorから canonical byte-exactに継承し、2 fieldだけ live sourceで置換する。  
組 indexは legacyと新 namespace全体を strict parseし、壊れた入力と同一組2件目を拒否する。  
発行時検査、atomic create-only、post-write再走、常設 real-repo testの多層で案3を固定する。  
generic writer、人間用 `freeze-protocol`、consumer、hold、承認定数、23-key manifestは変更しない。  
本 waveでは実 repoに protocol artifactを追加せず、read-only index commandだけを dogfoodする。  
残る裁定点は、Q3を将来の上位 receiptで機械化するか、P6の運用境界に留めるかである。