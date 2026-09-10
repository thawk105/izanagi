## 判定

GO — 成果物を変える blocker はなく、第 3 巡を使う価値はない。

## 所見対応表

| 所見 | 判定 | 根拠と削除時に赤くなる nodeid |
|---|---|---|
| FIX2-1 | `closed` | Git authority 変数の除去と `GIT_NO_REPLACE_OBJECTS=1` は [s8b_floor_campaign.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:619)、全 issuer Git subprocess への正しい global-option 配置は [s8b_floor_campaign.py:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:648)〜892。削除で赤: `orchestrator/tests/test_s8b_protocol_builder.py::test_reseal_git_environment_scrubs_replace_and_config_authority`、`::test_reseal_protocol_ignores_repository_replacement_ref`、`::test_reseal_protocol_scrubs_git_config_count_injection`。 |
| FIX2-2 | `closed` | 共通祖先検査は [s8b_floor_campaign.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:753)、write 直前再検査と直後 realpath 検査は同ファイル `:966-989`。削除で赤: `::test_reseal_protocol_rechecks_ancestor_symlink_immediately_before_write`、`::test_reseal_protocol_rejects_destination_realpath_outside_repo_after_write`。通常 worktree と相対 root は read-only probe で通過。bind mount は `realpath` が mount topology を外部 path へ展開しないため誤拒否しない。 |
| FIX2-3 | `closed` | 共通診断は [s8b_floor_campaign.py:895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:895)〜903、適用先は `:968-1034`。`detail` を残すため HEAD、read-back bytes、parse mismatch、full-index mismatch は潰れない。削除で赤: `::test_reseal_protocol_rejects_head_move_immediately_after_publish`。理由分離は `::test_reseal_protocol_readback_tamper_is_not_deleted`、`::test_reseal_protocol_readback_parse_mismatch_has_specific_reason`、`::test_reseal_protocol_post_write_index_mismatch_has_specific_reason` が固定する。 |
| FIX2-4 | `closed` | gitlink は build 前の一読だけ (`s8b_floor_campaign.py:922`)。publish 後は実効性のある HEAD equality (`:991-1000`) と固定済み `target_pair` (`:1027`) を使う。削除、すなわち恒真再読の復活で赤: `::test_reseal_protocol_public_entry_accepts_unoccupied_contract_and_derived_path`。HEAD 移動の必要な検査は `::test_reseal_protocol_rejects_head_move_immediately_after_publish` が担う。 |
| FIX2-5 | `partial` | working-tree legacy との比較は廃止され、HEAD blob との pair 比較へ修正済み [test_s8b_protocol_builder.py:1327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:1327)。ただし `:1344-1347` の namespace assertion は scanner の構築規則を再確認するだけで、当該ブロックを削除しても `::test_build_and_write_leave_repo_tree_unchanged[top-level]` と `[nested]` は現 HEAD で赤にならない。production の受理集合には影響しない。 |

### D1〜D7

D1 は組から一意に導出する path (`s8b_floor_campaign.py:718-721`)、D2 は exact chain pattern (`:257-264`) を維持する。D3 は index と issuer の同一 contract 拒否 (`:730-744,926-935`)、D4 は固定 HEAD commit/blob (`:648-701,802-809`) を維持する。D5 は恒真再読を除き、実効 HEAD 検査だけを残した。D6 は CLI 以外の consumer 結線がなく dormant のまま。D7 の零引数 API、legacy anchor、strict scan、create-only、16/2 field 分割、既存 `freeze_protocol()` 非改変も保たれている。

## 新規所見

### 1. FIX2-5 の namespace assertion は独立した検出層ではない

- `重大度`: minor
- `根拠`: test は index 内の非 legacy record が prefix を持つことだけを検査する (`test_s8b_protocol_builder.py:1344-1347`)。scanner は最初から sanctioned directory だけを列挙し、その相対 path を record にする (`s8b_floor_campaign.py:811-821`)。
- `再現の筋道`: test の `:1327-1347` を削除しても、現在の clean repo では top-level／nested の両 nodeid が従来の tree-unchanged 検査だけで通る。
- `成果物のどの値・受理集合・参照がどう変わるか`: 現在の certified 選択、材料レポート、試行台帳、issuer の受理集合は変わらない。変わるのは将来回帰に対する test の検出力だけであり、第 3 巡の対象にはしない。

### 2. config-count 負例は replace-object 防壁に過剰決定されている

- `重大度`: minor
- `根拠`: [test_s8b_protocol_builder.py:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:901) は `GIT_CONFIG_COUNT` と同時に `GIT_REPLACE_REF_BASE` を設定し、注入値 `core.useReplaceRefs=true` は既定挙動と同じである。さらに argv の `--no-replace-objects` が後段で必ず遮断する。
- `再現の筋道`: config-count scrub だけを無効化し、replace-ref-base scrub と `--no-replace-objects` を残すと、この integration 負例は通る。もっとも環境集合を直接検査する `::test_reseal_git_environment_scrubs_replace_and_config_authority` は赤になる。
- `成果物のどの値・受理集合・参照がどう変わるか`: production 修正は実装済みなので変化なし。独立した動的証拠が弱いだけで、Git authority 漏れの再発ではない。

## 総括

HEAD `0ae02e4f` の fix 第 2 巡は、成果物境界に関する 4 件を閉じた。  
replace object と指定された ambient config 変数は issuer の全 Git read から除去されている。  
`--no-replace-objects` の位置は正しく、通常の Git worktree でも実行できた。  
write 直前検査と post-write realpath 検査に、相対 root・worktree・bind mount の偽拒否は見つからない。  
失敗診断は共通接尾辞を持つが、個別の失敗理由は保持されている。  
gitlink 再読の削除で必要な検査は落ちず、HEAD 移動検査が実効 gate として残る。  
FIX2-5 と config-count 負例には minor な検出力不足があるが、成果物値・受理集合・参照は変わらない。  
D1〜D7 は最終 HEAD でも維持され、land を止める理由はない。  
pytest は再実走せず、親の `413 passed, 2 skipped, rc=0` と静的監査を分離して扱った。