## 判定

NO-GO

## 所見対応表

| FIX | 判定 | 根拠と削除変異で赤くなる nodeid |
|---|---|---|
| FIX-1 | `partial` | `source_digest._sanitized_git_env()` は主要な repository/object 変数だけを除去する (`orchestrator/campaign/source_digest.py:597-607`)。呼出し側は同 helper を使う (`orchestrator/campaign/s8b_floor_campaign.py:619-665,839-845`)。`GIT_DIR` scrub の削除は `orchestrator/tests/test_s8b_protocol_builder.py::test_reseal_protocol_scrubs_ambient_git_dir_authority` が赤になる。しかし `GIT_REPLACE_REF_BASE`、replace refs、`GIT_CONFIG_*` 等の負例が無く、authority は完全には固定されていない。 |
| FIX-2 | `closed` | legacy を先に index へ入れ (`s8b_floor_campaign.py:763-766`)、同じ contract の後続 entry を拒否する (`:695-715`)。削除すると `orchestrator/tests/test_s8b_protocol_builder.py::test_floor_protocol_index_rejects_same_contract_with_different_pin` が受理へ変わって赤になる。現 HEAD は legacy だけなので既存正常 repo は赤にならない。ただし M2/M4 はこの新層に mask された。 |
| FIX-3 | `partial` | 静止した `output`／`output/s8b-freeze` symlink は拒否する (`s8b_floor_campaign.py:724-736`)。削除時は `::test_floor_protocol_index_rejects_symlink_ancestors[output]` と `[output/s8b-freeze]` が理由不一致で赤になる。ただし fixture の外部 directory は空で、削除後も legacy 欠落で拒否される。さらに検査後、writer が path を再解決するまでの TOCTOU が残る (`:920`, `:1080-1103`)。 |
| FIX-4 | `partial` | commit OID と blob OID 固定は `s8b_floor_campaign.py:619-665,839-876`。削除すると `::test_floor_protocol_index_binds_blob_read_to_one_head_commit` が赤になる。publish 後 HEAD 検査 (`:922-927`) は `::test_reseal_protocol_rejects_head_move_immediately_after_publish` で実際に発火する。一方、同じ固定 commit の gitlink を再読する恒真検査が `:928` に残り、`::test_reseal_protocol_public_entry_accepts_unoccupied_contract_and_derived_path` がその2回呼出しを逆に固定している (`test_s8b_protocol_builder.py:576-577`)。replace-object 経路も未閉鎖。 |
| FIX-5 | `regressed` | 件数固定は外れたが、代替 assertion (`test_s8b_protocol_builder.py:1117-1132`) を全部削除しても `::test_build_and_write_leave_repo_tree_unchanged[top-level]` と `[nested]` は現 repo で緑のまま。さらに index は committed anchor、比較対象は working-tree anchor なので (`:1117-1125`)、validator-admitted な dirty legacy を許す production 挙動と矛盾し、正常な dirty 作業中に偽の赤となる。 |
| FIX-6 | `closed` | read-back 3 分岐は `s8b_floor_campaign.py:930-961`、外部 artifact の継承防壁と issuer の post-condition の区別は `:812-825,906-908`。削除時に赤くなる node は `::test_reseal_protocol_readback_tamper_is_not_deleted`、`::test_reseal_protocol_readback_parse_mismatch_has_specific_reason`、`::test_reseal_protocol_post_write_index_mismatch_has_specific_reason`、`::test_floor_protocol_index_rejects_closed_namespace_violations`、`::test_floor_protocol_index_rejects_strict_and_canonical_member_violations`。ただし namespace/duplicate-key の一部は受理集合の kill ではなく diagnostic sensitivity pin である。 |

## 新規所見

### 1. replace-object 系 Git authority が残っている

- `重大度`: blocker
- `根拠`: scrub 対象は `GIT_DIR`、index/worktree/object/alternate/ceiling 系に限られる (`orchestrator/campaign/source_digest.py:597-607`)。`GIT_REPLACE_REF_BASE` を除去せず、`GIT_NO_REPLACE_OBJECTS=1` も強制しない。さらに `GIT_CONFIG`、`GIT_CONFIG_PARAMETERS`、`GIT_CONFIG_COUNT` と対応する `GIT_CONFIG_KEY_n`／`VALUE_n`、`GIT_NAMESPACE`、`GIT_GRAFT_FILE`、`GIT_SHALLOW_FILE`、global/system config も残る。テストは `GIT_DIR` 一種だけである (`test_s8b_protocol_builder.py:752-794`)。
- `再現の筋道`: HEAD commit `H` に対する replacement commit を object database へ置き、環境の `GIT_REPLACE_REF_BASE` が指す ref namespace に `H` の replacement ref を用意する。`rev-parse`、`ls-tree H`、`cat-file` は同じ汚染を一貫して受けるため、HEAD の表示上の identity を保ったまま別 anchor と gitlinkから issuer を成功させられる。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: successor の継承16 field、`ccbench_pin`、path、SHA-256 が実際の HEAD tree ではなく replacement object 由来になる。sanctioned index が「HEAD commit に存在しない lineage」を受理する。なお現 subprocess は read-only plumbing だけなので、`core.hooksPath` から hook が実行される経路自体は見つからなかった。

### 2. 祖先 symlink の check-to-write TOCTOU は未閉鎖

- `重大度`: major
- `根拠`: ancestor 検査は scan 冒頭だけ (`s8b_floor_campaign.py:724-736`)。発行はその後、path ベースの `mkdir`、一時ファイル、`link`、`open` を行う (`:920,1080-1105`)。directory fd と `O_NOFOLLOW` に束縛されていない。
- `再現の筋道`: 初回 scan 後、writer 呼出し前に `output/s8b-freeze` を外部 directory への symlink に交換する。writer は外部へ canonical artifact を作る。post-write scan は symlink を検出して失敗するが、外部 artifact は削除されない。既存 test は scan 前から空 symlink を置くだけで、この経路を踏まない。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: API は失敗を返しても repo 外の bytes を作成する。返却成功集合は広がらないが、「導出 destination なので外を書けない」という副作用境界は破れ、失敗成果物の path 参照が repo 外へ変わる。
- 正常運用への影響:通常の Git worktree と bind mount は directory として通る。相対 root と root 自身の symlink ancestor も誤拒否されないが、後者は逆に未検査である。

### 3. 失敗した publish が contract を占有または index を毒化する

- `重大度`: major
- `根拠`: artifact を作った後に HEAD を検査し (`s8b_floor_campaign.py:920-927`)、失敗時の rollback はない。テストも artifact 残置を明示要求する (`test_s8b_protocol_builder.py:614-644`)。同様に post-write scan の contract 一意性失敗でも削除しない (`s8b_floor_campaign.py:947-955`)。
- `再現の筋道`: 単独では writer 直後に empty commit で HEAD を動かす。API は拒否するが、canonical artifact は残り、次回 scan では正常 entry として contract を占有しうる。並行時は A/B が同一 contract・異なる pin を空 index から開始し、B が先に成功、A が後から書くと、A は post-scan で失敗するものの2ファイルとも残る。その後の全 scan は同一 contract 重複で拒否される。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: 失敗した issuer が sanctioned namespace の受理状態を変更する。単独 race では再発行の受理集合が空になり、並行 race では成功済み artifact を含む index 全体が参照不能になる。自動削除しない安全方針自体は理解できるが、隔離・明示的 recovery・lock のいずれも無い現状は transactional ではない。

### 4. 固定 commit に対する gitlink 再読が恒真として焼き込まれた

- `重大度`: minor
- `根拠`: `published_head == head_commit` を確認した直後 (`s8b_floor_campaign.py:922-927`)、同じ OID を `_ccbench_gitlink` へ渡す (`:928`)。テストは2回呼出しと OID 一致を要求する (`test_s8b_protocol_builder.py:576-577`)。
- `再現の筋道`: `:928` を削除して `target_pair` を post-index 照合に使っても、通常の immutable object database では受理・拒否結果は変わらない。それでも正例 test が call-count 不一致で赤になる。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: artifact 値と受理集合は変わらない。変わるのは防壁台帳上の参照であり、実効性のない subprocess を独立 gate と誤認させる。replace refs が可変なら値が変わりうるが、それは所見1の authority 漏れであり、この再読の正当化にはならない。

### 5. FIX-5 は inventory drift 検出を失い、dirty working tree を偽拒否する

- `重大度`: major
- `根拠`: 新 assertion の多くは scanner 自身が構築・保証した property の再確認である (`test_s8b_protocol_builder.py:1123-1132`)。一方、committed index document と working-tree load を同一視している (`:1117-1125`)。production は working legacy を validate するだけで、index authority は HEAD bytes に置く (`s8b_floor_campaign.py:749-765`)。
- `再現の筋道`: legacy working copy の `master_seed` を別の validator-admitted 値へ変え、未commitのまま real-repo node を走らせる。scan は設計どおり committed anchor を返すが、`:1125` が赤になる。反対に、別 contract の well-formed versioned artifact が増えても新 assertion はすべて通る。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: production artifact は変わらないが、受入集合が「clean legacy の repo」に不必要に狭まる。件数固定が持っていた「予期しない committed inventory 増加」の検出は完全に失われた。将来の異なる contract artifact を許すこと自体はD3どおりだが、inventory drift の検出は別の provenance 検査へ移されていない。

## 変異 M1〜M8 の kill 層

| 変異 | 現在の kill 層と期待 nodeid | mask |
|---|---|---|
| M1 legacy 除外 | index inclusion (`s8b_floor_campaign.py:763-766`)。`::test_floor_protocol_index_includes_legacy_and_rejects_duplicate_pair` | `部分的に有り`。public index の差は直接検出するが、issuer では exact-one anchor (`:865-867`) が先に落ち、D3への影響を mask する。 |
| M2 同一 pair 拒否削除 | exact-pair gate (`:701-705`)。同 node は「同一組」という理由不一致で赤 | `有り`。FIX-2 の同一 contract gate (`:706-715`) が同じ入力を拒否するため、受理集合は変わらない。現在は kill ではなく diagnostic pin。 |
| M3 mutable field を3件化 | module-level 2/16件 assert (`s8b_floor_contract.py:43-48`) と `::test_ai_reseal_inheritance_exact_16_field_partition_and_mutations` | `有り`。継承比較へ到達する前の構造 assert に殺される。 |
| M4 issuer の既出 contract 拒否削除 | issuer gate (`s8b_floor_campaign.py:880-889`)。`::test_reseal_protocol_public_entry_rejects_contract_already_in_index` | `有り`。書込み後の FIX-2 index gate が拒否するため、受理集合上は生存しないが issuer gate 単独の kill でもない。artifact 残置という副作用だけ増える。 |
| M4p 常時拒否 | 正例 issuer。`::test_reseal_protocol_public_entry_accepts_unoccupied_contract_and_derived_path` | `無し`。未使用 contract の正常発行が直接赤になる。 |
| M5 working-tree anchor 復活 | commit/blob OID 層 (`s8b_floor_campaign.py:619-665,759-765`)。`::test_reseal_protocol_uses_committed_anchor_not_validator_admitted_dirty_copy` と `::test_floor_protocol_index_binds_blob_read_to_one_head_commit` | `無し`。ただし replace-object 攻撃はこの変異集合外で生存する。 |
| M6 chain pattern 過剰拡大 | exact pattern (`s8b_floor_campaign.py:257-264`) と unknown-file gate (`:3626`)。`::test_clean_scan_rejects_overbroad_versioned_protocol_names` | `無し`。代表的な過剰名が新 pattern だけで受理へ変わる。 |
| M7 chain pattern 削除 | 同 pattern と unknown-file gate。`::test_clean_scan_accepts_exact_versioned_protocol_chain_record` | `無し`。正規 versioned path が直接未知 file 拒否へ変わる。 |
| M8 path/document 束縛削除 | 導出照合 (`s8b_floor_campaign.py:805-811`)。`::test_floor_protocol_index_rejects_misderived_path` | `無し`。fixture は document validation と canonical bytes を満たし、この照合だけで拒否される。 |

M2 と M4 は FIX-2 後の最終 commit では旧事前登録の単一理由性を失った。親の変異本走では「KILLED」と数えず、M2 は pair＋contract の両層変異、M4 は issuer＋post-index contract gate の両層変異へ再照準する必要がある。

## 総括

FIX-2 と FIX-6 は指定された範囲を閉じている。  
FIX-1 は `GIT_DIR` 攻撃を閉じたが、replace-object authority が残るため blocker は未閉鎖である。  
FIX-3 は静止 symlink を拒否する一方、scan-to-write TOCTOU では repo 外へ書ける。  
FIX-4 の HEAD 移動検査は実際に発火するが、artifact は残り、次回の contract を占有しうる。  
同じ固定 commit の gitlink 再読は恒真であり、テストがその冗長性を固定している。  
FIX-5 は件数依存を外した代わりに inventory drift を見なくなり、valid dirty legacy を偽拒否する。  
FIX-2 により M2 と M4 は別層に mask され、旧 matrix の単一理由 kill は成立しない。  
現 repo は clean で legacy 1件だけなので、現在状態そのものは新しい contract 一意性で赤にならない。  
worktree、bind mount、通常の相対 path に対する新しい誤拒否は見つからなかった。  
pytest は指示どおり再実走せず、親の `408 passed, 2 skipped` と静的検査を分離して扱った。  
replace refs、書込み path の原子性、失敗 artifact の recovery を閉じるまでは land 不可である。