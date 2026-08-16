## 判定

NO-GO

## 所見

### 1. Git 環境変数から authority を差し替えられ、追加テストも検出しない

- 重大度: blocker
- 根拠: [s8b_floor_campaign.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:619)、[s8b_floor_campaign.py:785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:785)、[test_s8b_protocol_builder.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:311)
- 再現の筋道: `_head_blob_100644()` と `_ccbench_gitlink()` は `cwd=root` だけを指定し、`GIT_DIR`、`GIT_WORK_TREE`、`GIT_OBJECT_DIRECTORY` 等を除去しない。別 repository を指す `GIT_DIR` を設定し、その HEAD に validator が受理する改変 anchor と任意 gitlink を置けば、working legacy の検査だけは対象 root で通し、lineage anchor と pin は別 repository から取得できる。post-write scan も同じ汚染環境を使うので自己整合して通る。tmp fixture は Git 環境を汚染する負例を持たない。
- 影響: 零引数 API であっても、発行 protocol の継承 16 field、`ccbench_pin`、導出 path が ambient Git 環境に支配される。sanctioned index の受理集合へ、対象 repository の HEAD から導出されていない artifact が入る。

### 2. HEAD の mode、anchor bytes、gitlink が同じ commit に束縛されていない

- 重大度: major
- 根拠: [s8b_floor_campaign.py:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:622)、[s8b_floor_campaign.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:637)、[s8b_floor_campaign.py:714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:714)、[s8b_floor_campaign.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:820)
- 再現の筋道: `ls-tree HEAD` の後、`cat-file HEAD:path` の前に HEAD を動かすと、mode は旧 HEAD、bytes は新 HEADから読まれる。さらに anchor load と 2 回の `_ccbench_gitlink()` の間にも共通 commit OID がない。追加テストは一度 commit した静止 tmp repoしか使わず、Git subprocess 間で HEAD を動かさない。
- 影響: 100644 でない新 HEAD blobを旧 HEAD の 100644 判定で通せる。anchor bytes と pin が一度も同一 commit に共存しなかった protocol も発行可能となり、protocol bytes と path の参照元が不定になる。

### 3. real-repo テストが「versioned protocol は常にゼロ件」を焼き込んでいる

- 重大度: major
- 根拠: [test_s8b_protocol_builder.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:883)
- 再現の筋道: `test_build_and_write_leave_repo_tree_unchanged` は実 repo を scan した後、`len(index) == 1` と legacy pathだけを要求する。後続 wave が裁定どおり最初の `floor-protocols/<pair>.json` を追加すると、production index は正しく 2 件を返すが、この既存 parameterized node は 2 instanceとも赤になる。
- 影響: production artifact、受理集合は正しいままでも、受入結果が偽の赤へ変わり、予定された g2 artifact の land を阻害する。tree への書込みはないが、実 repo の時点状態に依存する。

### 4. read-back tamper テストは個別の read-back gate 削除を検出しない

- 重大度: minor
- 根拠: [s8b_floor_campaign.py:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:867)、[test_s8b_protocol_builder.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:613)
- 再現の筋道: test は末尾に改行を足す。直後の `scan_floor_protocol_index()` が canonical bytes 不一致で先に拒否するため、`read_back != built.canonical_bytes` を削除しても test は緑のまま。改行は parse 結果を変えないため、`reparsed != built.document` branch は元から発火しない。
- 影響: full-index gateが残る限り受理集合は変わらないが、「read-back 3 検査を個別に殺せる」という検出力の自己申告は成立しない。

### 5. closed namespace／strict parse の負例が単一理由でない

- 重大度: minor
- 根拠: [test_s8b_protocol_builder.py:697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:697)、[test_s8b_protocol_builder.py:713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:713)
- 再現の筋道: いずれも例外型だけを要求する。未知名の明示拒否を削除しても `{}` の protocol validation が落とす。nested-directory の非通常 file 拒否を削除しても後続 `read_bytes()` が落とす。duplicate-key 拒否を削除しても `{"x":1,"x":2}` は不完全 protocol として後段で落ちる。
- 影響: 現在の多層拒否が残る限り受理集合は変わらないが、狙った production branchを削除しても緑になる。変異を KILLED と数えるには理由を照合する期待が必要。

### `_CHAIN_RECORD_PATTERNS` が広げた正確な受理集合

[s8b_floor_campaign.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:257) の一行により、次の exact path にある任意 bytes の regular non-symlink file が未知 file 拒否から chain record 受理へ移る。

`output/s8b-freeze/floor-protocols/<64桁小文字hex>--<40桁小文字hex>.json`

- `_floor_preflight_freeze_allowlist()` の返却集合は変わらない。versioned protocolを固定 allowlistへ加えない。
- `_assert_freeze_allowlist()` は exact path の fileを内容検証せず、その bytes SHA-256 を `chain_records` に入れる。
- `clean_scan_digest()` はその path と SHA-256 を `freeze_allowlist` preimageへ併合する。bytesが変われば digestも変わる。
- `test_s8b_floor_campaign.py` の既存 clean-scan 群にはこの exact namespace の正例も負例もない。追加一行を消しても、広げても、既存群は黙って緑のまま。
- 新規 `test_clean_scan_accepts_exact_versioned_protocol_chain_record` は pattern削除で赤、`test_clean_scan_rejects_overbroad_versioned_protocol_names` は代表的な過剰拡大で赤になる。この二件は検出力がある。

### 追加テスト16件の削除変異判定

| 新規 test | 判定 |
|---|---|
| `test_ai_reseal_inheritance_exact_16_field_partition_and_mutations` | helper直呼び。helper／field分割削除では赤。production結線は単独では通らない |
| `test_public_index_rejects_validator_admitted_anchor_field_mutations` | production scanを通る。inheritance call削除は期待 message不一致で赤。ただし canonical bytes gateと過剰決定 |
| `test_reseal_protocol_public_entry_accepts_unoccupied_contract_and_derived_path` | public issuer、M4p、導出 path、Git再測回数の削除で赤。ambient Git汚染とHEAD raceは未検出 |
| `test_reseal_protocol_public_entry_rejects_contract_already_in_index` | D3削除で後段拒否になるが、message不一致で赤 |
| `test_reseal_protocol_second_issue_preserves_first_bytes` | D3削除で赤。ただし create-only単独の検査ではない |
| `test_reseal_protocol_readback_tamper_is_not_deleted` | 弱い。個別 read-back比較を削除しても緑 |
| `test_reseal_protocol_uses_committed_anchor_not_validator_admitted_dirty_copy` | working-tree anchorへ戻す変異で赤。D4の主要経路を通る |
| `test_floor_protocol_index_includes_legacy_and_rejects_duplicate_pair` | legacy scan削除、duplicate判定削除で赤 |
| `test_floor_protocol_index_rejects_misderived_path` | path/document束縛削除で赤。単一理由性あり |
| `test_floor_protocol_index_rejects_closed_namespace_violations` | 弱い。明示拒否を削除しても後段例外で緑になりうる |
| `test_floor_protocol_index_rejects_strict_and_canonical_member_violations` | canonical bytes削除は赤。duplicate／extra-key個別 gate削除は緑になりうる |
| `test_floor_protocol_index_requires_head_100644_blob` | stable executable mode負例は有効。HEAD切替 raceは未検出 |
| `test_clean_scan_accepts_exact_versioned_protocol_chain_record` | pattern削除で赤。M7に有効 |
| `test_clean_scan_rejects_overbroad_versioned_protocol_names` | `.*\.json` 相当への拡大で赤。M6に有効 |
| `test_check_protocol_index_cli_is_read_only_and_deterministic` | tmp repo限定のtree不変と同一出力を検査。時刻・working tree hashの焼込みなし |
| `test_reseal_protocol_cli_has_no_caller_selected_authority_options` | CLI option追加で赤。ただし Python API signatureの任意引数追加は直接検査しない |

## 親が走らせるべき test file

1. `orchestrator/tests/test_s8b_protocol_builder.py`  
   新規16件が正式 pytestで一度も走っていない。最優先。ただし上記 blocker用の負例は現在ない。

2. `orchestrator/tests/test_s8b_floor_campaign.py`  
   `_CHAIN_RECORD_PATTERNS` の唯一の既存 caller系列。既存群はD2を検出しないが、official preflightの既存回帰確認に必要。

3. `orchestrator/tests/test_real_repo_serialization.py`  
   既存 serial nodeのactionを変更している。marker、collection、meta guardとの整合を正式に確認する。

4. `orchestrator/tests/test_s8b_floor_contract.py`  
   `_PROTOCOL_KEYS` 分割と新しいleaf helperを追加した所有 test file。

5. `orchestrator/tests/test_frozen_artifacts.py`  
   現状では赤になる理由はなく、23-key manifest据置を確認するために走らせる。versioned artifactは検査対象外のまま。

6. `orchestrator/tests/test_s8b_holdout_admission.py`  
   consumerはlegacy固定 pathのままなので、静的には緑の見込み。

7. `orchestrator/tests/test_s8b_holdout_freeze.py`  
   同上。新 index／issuerのcallerではない。

8. `orchestrator/tests/test_s8b_ratified_freeze.py` と `orchestrator/tests/test_s8b_ratified_verify.py`  
   ratified pointerの既存legacy参照が変わっていないことを確認する。

9. `orchestrator/tests/test_s8b_prediction_runner.py`  
   protocol consumerがversioned artifactへ勝手に切り替わっていないことを確認する。

10. `orchestrator/tests/test_pegasus_floor_tools.py`  
    shell consumerの固定 `floor_protocol.json` 参照を確認する。

静的には、実装子が未実走と申告した既存 `test_s8b_floor_campaign.py`、`test_frozen_artifacts.py`、consumer群に、現在のartifact不在状態だけで赤になる変更は見つからない。D2の受理拡大は既存群を黙って通過する。

## 攻撃したが破れなかった点

- versioned path regexは fullmatchで、短いhash、大文字、alias、nested pathを受理しない。
- chain recordは任意内容を許すが、pathとbytes hashはclean-scan digestへ入る。これは裁定D2どおり。
- D3の「同一 contract_sha256 の二件目拒否」はpublic issuer経由の正例・負例があり、削除で赤になる。
- legacy anchor除外、同一pair重複、misderived path、working-tree anchor継承は追加テストで検出できる。
- `freeze_protocol()`、既存parser、既存builder本体には差分上の変更がない。
- consumer 6 件はlegacy固定 pathのままで、新 API の所有外 production callerはCLIだけ。
- tmp repositoryは実際にGit commitとgitlinkを作り、stableな条件ではproductionの`ls-tree`、`cat-file`、gitlink loaderを通る。
- tmp testの書込みはtmp repository内だけで、real-repo scan自身もread-only。
- 新しいtest fileは増えていないため、test file集合を列挙するmeta test、`check_docs.py`、`check_codex_agents.py`へのfile追加は不要。
- 実 repo scanを入れた既存node自体は既に`REAL_REPO_SERIAL_NODES`と独立goldenに登録済み。

## 総括

NO-GOの主因は、committed HEAD authorityがambient Git環境から差し替え可能な点である。  
さらにmode、anchor bytes、gitlinkが同じHEAD snapshotへ束縛されていない。  
この二点は追加テストが静止tmp repositoryしか使わないため偽の緑になる。  
D2の受理拡大はexact pathの任意bytes一件で、pathとhashはdigestへ入る。  
既存clean-scan群はこの変更を一切検出せず、新規二件だけが検出する。  
D3、D4、legacy inclusion、duplicate pair、path導出の主要変異は概ね赤になる。  
read-back、duplicate-key、closed namespaceの一部負例は過剰決定である。  
実repoの`len(index) == 1`は予定された最初のversioned artifact追加時に偽の赤になる。  
consumer群と23-key manifestは静的には変化せず、正式実走でその非回帰を確認すべきである。  
Git authorityの隔離、HEAD snapshot束縛、揮発するreal-repo件数期待の除去後に再レビューが必要である。