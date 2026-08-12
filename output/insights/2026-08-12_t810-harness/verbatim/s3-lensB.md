結論は **NO-GO**。N=13・R=10 は前提として受け入れるが、同じ digest のまま推定式・gate・状態判定の実装を変更できる穴が残っている。

対象: [plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md)、[brief.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/output/insights/2026-08-12_t810-harness/brief.md)、[protocol](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/docs/pegasus-node-variance-protocol.md)、[floor_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/floor_v1.json)、[calibration_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/calibration_v1.json)。

## 1. 8 群の schema 対応表

`○` は literal の網羅、`△` は値はあるが手続き・証拠の拘束が不足、`×` は必須の機械的表現がない、の意味。

| protocol の群 | plan の対応 field | 判定 | 漏れと開く事後選択 |
|---|---|---:|---|
| §2 測定 literal | `measurement.*`、`design.selected.*`、`measurement.recording.*` | ○ | literal 自体はほぼ網羅。実 binary の hash・同一性は §3.1 側で閉じる必要がある |
| §3.1 build preimage | `build_preimage.*`、`runtime_identity.*`、`builder_retry.*` | △ | dedicated cache root、completion manifest の厳密 schema、release token、`scr_references` が空である条件が未固定。別 build path・別 runtime でも field の存在だけで通せる |
| §3.3 / §3.4 閾値・preflight | `coordination.*`、`preflight.*` | △ | ready receipt の field、request ID と投入順、release/start response の timestamp と差分式、cancel/release event、per-round の終了コードがない。遅延・失敗を別状態として扱う自由が残る |
| §4 N・R、設計目標、assurance | `design.*`、`assurance_reproduction.*` | △ | F quantile の実装版、independent check の seed/order、`τ=τ*` の再現条件、candidate grid の検証証拠がない。`unique_minimum=true` が自己申告になる |
| §5.1 区間式・報告量 | `estimator.*` | △（手続きは×） | 式は文字列で、secondary output の exact field も未列挙。式を別実装へ置換・丸めてから比較する自由がある |
| §5.3 対応表・slope gate | `decision.*`、`decision.slope_gate.*` | △（手続きは×） | OLS の `se_i`、欠損/NaN/丸め、effective N、評価 AST がない。`<` を `<=` にする、gate を省略する、行順を変える自由がある |
| §5.4 終端状態・retry | `terminal.*`、`retry.*`、`terminal-state.json` の集合 | △ | typed event と状態遷移の schema、attempt order の tie-break、状態別の effective N がない。claimed state を使って軽い状態へ倒せる |
| §6.2 期待集合・presence matrix | `artifacts.*`、状態別 table、slot 集合 | △ | exact path 展開と receipt/event の content schema がない。file の存在だけ検査し、release event や不正な conditional file を見逃せる |

## 2. Blocker

### B1 — digest が手続きを凍結していない

`point_variance`、`S_beta`、`predicate`、`ordered-first-match` は文字列として保存されるだけである。plan は後続コードを hard-coded dispatch するとしているが、その dispatch 実装自体は digest に束縛されない。

これを直さない場合、同じ prereg digest のまま `τ_U`、slope gate、終端状態を別実装にでき、`valid` / `terminal_reduced` の受理集合と §7 の downstream fan-out が変わる。

必要なのは、式の versioned AST/op graph、型・単位・丸め・NaN 処理を含む evaluator、`N=13` と reduced `N=12` の golden vector、境界値（等号・切捨て）のテスト、そして evaluator 実装の version/hash である。

### B2 — assurance の再現条件が不完全

NumPy 2.2.6、`Generator(PCG64(810))`、40 万 draw、順序、当選数は固定されている。しかし protocol 自身が版をまたぐ乱数列の同一性を保証していない。

さらに plan には次がない。

- `F_quantile` の実装・SciPy 版または固定 critical value
- Python 版、wheel hash、dtype、配列 shape
- independent check の seed と生成順
- `τ=τ*` の非反証確率 0.9536 の再現手順
- 400,000 / 10,000,000 draw の出力 mask または raw-array hash

これを直さない場合、同じ N/R に対する assurance `0.8462` / `0.8080` と「唯一最小」の参照値を別環境で再現できず、設計根拠の参照が変わる。

具体策は、NumPy/SciPy の wheel hash を含む reference runtime、API 呼出しと dtype の固定、生成配列または pass-mask の hash、independent check の seed/order を artifact に追加すること。別版で不一致なら値を更新せず `reference_not_reproduced` として fail-closed にする。

### B3 — `terminal_reduced` の effective N が estimator に束縛されていない

plan の estimator は `node_df = "N-1"`、`residual_df = "(N-1)*(R-1)"` と固定され、design の N は 13 である。一方、`terminal_reduced` は 12 ノードで推定する。

これを直さない場合、reduced attempt に N=13 の自由度を誤適用でき、`τ_hat`、`τ_L`、`τ_U` と結論が変わる。

状態ごとに `effective_node_count_ref`、`ν1`、`ν2`、F quantile、出力の使用 N を明示的に束縛すべきである。

### B4 — release / measurement_start / ready の手続きが schema になっていない

`start_spread <= 5` や timeout `1200` はあるが、次が機械的に定義されていない。

- ready receipt の必須 field
- request ID と投入順の schema
- coordinator の release timestamp
- job の measurement-start response timestamp
- その二つを引く exact な式と時計の単位
- release/cancel の event type と sequence
- per-round の終了コード

これを直さない場合、同じ path/hash でも開始遅延、cancel 後開始、非 0 終了を `valid` 側へ分類でき、occasion と実行結果の参照が変わる。

### B5 — `.claude` を除外しても、含めても実行可能性が閉じない

親 P1 の blanket exclusion は protocol の「gitignore された未追跡も filesystem walk」の要求を破る。逆に plan の full scan は、並行 worktree が `.claude` を書き換える限り pre/post race で恒常的に失敗する。

これを直さない場合、`.claude` を除外すれば隠れた未追跡書込みが validator の `rc=0` を通り、含めれば同時 writer がいる occasion の受理集合が空になる。

必要なのは、測定専用の immutable checkout/snapshot、scan 中の writer 停止、または protocol と整合した明示的な scan boundary である。単なる除外では足りない。

### B6 — slice 1 の成功が実行許可と誤読される

`run_authorized=false` は artifact の field に過ぎず、loader 成功や validator `rc=0` を run API が拒否する契約がない。

(a) barrier/release/cancel/exact completion、(b) PBS wrapper、(f) 並走ガード、(g) budget admission が未実装のままでも、runner policy を直接呼べば単独 job を実行できる。

これを直さない場合、N-job の同時性・予算・並走条件を満たさない attempt が「凍結 artifact と validator がある」だけで後続成果物へ参照される。

### B7 — execution receipt は未記録の exec を証明できない

plan 自身が認める通り、receipt に記録されなかった executable/argv の不存在は、receipt の照合だけでは証明できない。PBS wrapper と単一 mediation point が scope 外である。

これを直さない場合、別 executable、shell redirect、追加 flag を実行しても receipt だけを正規形にでき、測定値・binary hash・argv の proof chain 参照が虚偽になる。

## 3. 機械可読性の判定

| 対象 | 現在の表現 | 攻撃 | 必要な修正 |
|---|---|---|---|
| §5.1 区間式 | 式文字列＋ hard-coded dispatch | `F_{0.05}` と `F_{0.95}` の交換、`max(0, …)` の省略、R の除算位置変更 | typed AST または固定 evaluator と golden vector |
| §5.3 slope gate | `S_beta` 等の式文字列 | `>` を `>=` に変更、OLS の `se_i` を別定義、gate を skip | OLS・SE・比較・丸めを含む executable contract |
| §5.4 状態順 | `ordered-first-match` と状態配列 | runtime で `valid` を先に評価、caller の claimed state を優先 | typed receipt、有限状態機械、証拠 event の順序検証 |
| §3.3 / §3.4 | 閾値 literal | timestamp の差分定義や ready 判定を実装側で変更 | event schema と state transition evaluator |
| §6.2 presence | file 名と状態 table | file の存在だけ確認し、event 内容や slot 集合を確認しない | state 別の完全な path/content schema |

## 4. digest の再現性

plan の次の部分は良い。

- UTF-8、BOM なし、LF
- duplicate key 拒否
- float/NaN/Infinity/negative zero 拒否
- raw bytes と canonical bytes の完全一致
- SHA-256
- loader 側と test 側の pin

ただし、`json.dumps` の default に依存せず、`separators`、`allow_nan`、整数範囲、Unicode normalization（または artifact を ASCII 限定）まで明示すべきである。digest は JSON bytes には効くが、evaluator、runner、receipt parser の動作を拘束しない。

また、loader の literal と test の literal が同じ commit で同時更新されれば、独立性は失われる。これは provenance/review で補う必要がある。

## 5. scan コストと一般化

観測値から単純に線形近似すると次の通り。

| scan 面 | file 数 | 1 scan | 概算 rate | pre+post |
|---|---:|---:|---:|---:|
| `.git` / `.claude` 除外 | 12,627 | 7.8 秒 | 0.62 ms/file | 15.6 秒 |
| 全面 | 158,011 | 185 秒 | 1.17 ms/file | 370 秒 |
| 非動的面が 50,000 file | — | 約31秒 | 同率仮定 | 約62秒 |
| 非動的面が 100,000 file | — | 約62秒 | 同率仮定 | 約124秒 |
| 非動的面が 1,000,000 file | — | 約618秒 | 同率仮定 | 約20.6分 |

「1 validator invocation を 60 秒以内」と仮置きすると、非動的面でも約 50,000 file、pre/post 合計では約 25,000〜50,000 file が実用性の境目になる。これは file 数だけの推定で、実際は総 byte 数、hash 回数、`output/` の protected inventory 重複でさらに増える。

現在の全面走査は既に 1 回 185 秒、pre/post で 6 分強であり、親の 7.8 秒は本走時の保証ではない。`output/` の生成ログ・WAL・receipt が増えれば、entries と bytes の双方で線形増加する。加えて、scan 中の追加・削除が fail-closed になるため、コストだけでなく race による恒常失敗も問題になる。

## 6. scope 外で裁定パッケージに返すもの

| 層 | slice 1 の状態 | 未実装時の危険 |
|---|---|---|
| (a) barrier/release/cancel/exact completion | 未実装 | 13 job の同時性・完了集合を証明できない |
| (b) T-810 PBS wrapper | 未実装 | repo 外 root、qsub argv、binary copy、receipt を強制できない |
| (c) runner allowlist | planned | 単独 mediation がない限り receipt-only |
| (d) repo 外 root | planned/部分的 | policy は協調的 allowlist で、測定ノードの repo 不在を証明しない |
| (e) validator | planned | scan boundary と event schema が未解決 |
| (f) 並走ガード | 未実装 | T-139 等との競合を防げない |
| (g) budget admission | 未実装 | 残枠を超えた投入を防げない |

(a)(b)(f)(g) に加え、実行 mediation、測定ノード上の repo 不在、stage 1/2 approval ID を run API に束縛する契約も、裁定パッケージ候補として明示的に返すべきである。

## 7. 親 brief の P1〜P3

| 裁定 | 判定 | 理由 |
|---|---|---|
| P1 `.git` と `.claude` を除外 | **反対** | plan の反対判断に賛成。`.claude` 除外は protocol の ignored-untracked 検査を弱める。ただし全面走査には quiescent snapshot が必要 |
| P2 DurableRootPolicy は root 注入だけに使い、検出は独立 scan | **賛成** | policy は能力遮断ではなく協調的 allowlist。検出は独立 filesystem/inventory が必要。ただし TOCTOU と node 上 repo 不在は別途閉じる |
| P3 policy JSON に置き digest を test pin | **条件付き賛成** | 配置は既存 policy JSON と整合するが、test pin だけでは runtime 保証にならない。loader pin、evaluator pin、generic policy loader からの誤使用防止、run authorization の拒否が必要 |

## 8. test ごとの破壊変異

以下は、テスト名から静的に保証されない mutation である。実装時には各 mutation を実際に注入して、期待通り落ちることを確認すべきである。

| # | test | 通したまま壊せる変異 |
|---:|---|---|
| 1 | `test_prereg_digest_is_independently_pinned` | `load(path=...)` が引数を無視して常に default path を読む。default の digest assertion は通る |
| 2 | `test_prereg_rejects_one_byte_tamper` | raw bytes ではなく再直列化後を hash する。JSON escape の一 byte 変更が通る |
| 3 | `test_prereg_rejects_duplicate_json_key` | top-level だけ duplicate 拒否し、nested object の duplicate key を後勝ちにする |
| 4 | `test_prereg_rejects_noncanonical_bytes` | CRLF/BOM は検査するが、Unicode escape や exponent 表記を正規化して受理する |
| 5 | `test_prereg_rejects_unknown_missing_or_wrong_typed_fields` | nested field の unknown/type check を省略する |
| 6 | `test_prereg_contains_n13_r10_only` | selected は 13/10 のまま、hidden candidate に 12/12 を残し runtime が参照する |
| 7 | `test_prereg_cross_field_design_invariants` | `terminal_reduced` でも selected N=13 の df を使う |
| 8 | `test_prereg_assurance_reproduction_literals` | artifact literal は 810 のまま、実行コードだけ seed 811 を使う |
| 9 | `test_prereg_decision_order_and_strict_inequalities` | artifact は `<` のまま、evaluator が `<=` を使う |
| 10 | `test_prereg_terminal_states_are_exact_ordered_closed_set` | artifact の順序は維持し、runtime だけ `valid` を先に評価する |
| 11 | `test_prereg_projection_is_deeply_immutable` | `runtime_identity.required_fields` など一つの nested list だけ mutable のまま残す |
| 12 | `test_presence_projection_for_all_five_states` | aggregate root だけ確認し、slot ごとの conditional path 展開を誤る |
| 13 | `test_policy_registry_contains_t810_in_sorted_closed_set` | registry の path は正しいまま、artifact 内容を別 policy に置換する |
| 14 | `test_runner_accepts_only_the_frozen_invocation` | canonical argv は受理するが、渡された prereg digest を loaded digest で上書きする |
| 15 | `test_runner_rejects_certify_calibration_forms` | exact token だけ deny し、`-m orchestrator.calibrate` 等の別表現を許す |
| 16 | `test_runner_rejects_extra_or_reordered_benchmark_flags` | 同一 flag の重複を deduplicate してから比較する |
| 17 | `test_runner_rejects_ycsb_max_ope_and_shell_passthrough` | parser は拒否するが、実行層が `shell=True` で別 command を起動する |
| 18 | `test_runner_rejects_binary_symlink_or_hash_mismatch` | hash 一致の hard link、または非 executable mode の regular file を許す |
| 19 | `test_root_accepts_disjoint_external_directory` | `/tmp` や共有祖先の広い directory も「repo 外」として受理する |
| 20 | `test_root_rejects_repo_child_equal_and_ancestor` | lexical prefix 判定にして `/repo2` 等を誤受理する |
| 21 | `test_root_rejects_symlink_and_mount_crossing` | approval 後の symlink/mount swap を検査しない |
| 22 | `test_repo_snapshot_detects_tracked_byte_change` | regular file は見るが、gitlink の submodule dirty state を見ない |
| 23 | `test_repo_snapshot_detects_gitignored_untracked_file` | ignored regular file は検出するが、ignored directory と nested file を skip する |
| 24 | `test_repo_snapshot_detects_gitignored_file_under_dot_claude` | `.claude` 直下は見るが `.claude/worktrees` 以下を除外する |
| 25 | `test_repo_snapshot_detects_add_remove_type_and_symlink_target` | mode change を比較しない |
| 26 | `test_repo_snapshot_fails_on_scan_race_or_unreadable_entry` | path set の race だけ検出し、hash 後の bytes 差し替えを検出しない |
| 27 | `test_protected_inventory_detects_output_mtime_or_hash_delta` | `output/` は見るが `env_contract_activations` を inventory から落とす |
| 28 | `test_protected_inventory_detects_new_absent_root` | canonical root の一種類だけ absent→created を比較する |
| 29 | `test_frozen_manifest_rejects_missing_changed_duplicate_and_escape_member` | member hash は確認するが manifest 自身の prereg digest を確認しない |
| 30 | `test_frozen_manifest_rejects_unlisted_new_file` | unlisted regular file は検出するが nested symlink/socket を skip する |
| 31 | `test_calibration_wildcard_namespace_is_explicitly_denied` | canonical `calibration` path だけ deny し、symlink alias や別名 namespace を許す |
| 32 | `test_execution_receipt_rejects_unknown_executable_and_missing_record` | supplied receipt 内だけ検査し、未記録 exec を検出する mediation がない |
| 33 | `test_each_completed_slot_has_exactly_ten_commands` | command 数だけ 10 とし、同じ round ID の重複を許す |
| 34 | `test_expected_layout_rejects_extra_file_directory_symlink_socket` | root 直下だけ検査し、slot 下の extra を見逃す |
| 35 | `test_presence_matrix_release_and_estimate_rules` | file の存在だけ確認し、pre-release の coordinator log 内の release event を許す |
| 36 | `test_failure_state_is_derived_from_receipt_boundary` |複数 event のうち最後の boundary を使い、最初の measurement_start を無視する |
| 37 | `test_failed_valid_or_reduced_claim_becomes_incomplete_after_start` | inventory 以外の failure code、または reduced claim の override を漏らす |
| 38 | `test_same_cli_runs_pre_and_post_checks` |同じ関数名を呼ぶが、`mode=post` の内部 branch で検査を skip する |
| 39 | `test_every_error_class_returns_nonzero_without_pass_receipt` | `Exception` だけ捕捉し、`BaseException` や receipt finalize failure で rc=0 にする |
| 40 | `test_post_requires_approved_baseline_digest` | digest 確認後に baseline path を差し替える TOCTOU を許す |

pytest は要求通り実行していない。

## 総括

**NO-GO。**

最も危険な穴は、**canonical JSON の digest が、区間式・slope gate・状態遷移・実行 mediation を拘束していないこと**である。これを直さない限り、同じ事前登録を参照したまま、成果物の値・受理集合・proof chain の実行参照を変更できる。