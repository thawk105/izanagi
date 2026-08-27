## 前提の確認

指定された全 file を読んだ。Web 検索とテスト実走は行っていない。

正本:

- [s4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s4-ruling.md:1)
- [ref-prereg-b4.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-prereg-b4.md:1)
- [parent-measurements.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/parent-measurements.md:1)

実装:

- [p3_b4_analysis_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:1)
- [p3_b4_analysis_adapter.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_adapter.py:1)
- [p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_ledgers.py:1)
- [p3_b4_analysis_path.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py:1)
- [p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:1)

テスト:

- [test_p3_b4_analysis_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_contract.py:1)
- [test_p3_b4_analysis_adapter.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_adapter.py:1)
- [test_p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_ledgers.py:1)
- [test_p3_b4_analysis_path.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_path.py:1)
- [test_p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py:1)

逐語照合で成立している部分:

- 12 個の invalid reason と 5 個の registry reason は実装上の名前・順序とも正本どおりである。[contract:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:36)
- `missing` 同士は [contract:532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:532) で `1/2`、つまり tie である。これは正本の 3 段順位と整合する。正本の「この 2 つの間だけ」は異なる status 間で常時 tie になる組が `rejected` / `aborted` だけという意味であり、「missing は tie ではない」はその二者との比較を指す。[ref-prereg-b4.md:244](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-prereg-b4.md:244)
- tie 境界の `<=`、score `1` / `1/2` / `0`、`A_hat` の `Fraction` 集積は exact である。[contract:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:519) [contract:693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:693)
- 二項裾と `1/40` の比較は整数と `Fraction` だけで行われ、浮動小数点による判定反転経路はない。[contract:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:539)
- Clopper-Pearson は exact な二項多項式を使う 80 段の有理数包囲で、報告端点は外向きである。`W=0` の下端、`W=m` の上端、`m=0` の `[0,1]` も正しい。[contract:626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:626)
- verdict の 7 分岐順、4 分類への写像、`A_hat` と母数 `A` の区別は実装上正しい。[contract:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:686)
- adapter は `parse_float=Fraction` を使うため、現在の lexical 経路に `1.1 / 1.0 / 0.1` の超過は残っていない。[adapter:385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_adapter.py:385)
- 親実測は 5 file 合計 121 passed だが、受入全走ではない。これは親の結果としてのみ数える。[parent-measurements.md:78](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/parent-measurements.md:78)

## 所見

### F1: exact section hash が実効 gate になっていない

- 重大度: blocker
- 対象: [p3_b4_analysis_prereg_consumer.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:357)、[test_p3_b4_analysis_prereg_consumer.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py:194)
- 根拠: A8 は「§5.1.1 の exact section bytes hash」を要求する。[s4-ruling.md:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/s4-ruling.md:60) しかし consumer は `raw_sha256 != pin and semantic_sha256 != pin` の場合だけ拒否するため、raw bytes が変わっても semantic hash が同じなら受理する。テストも section hash が変わったことを確認した上で、その入力を明示的に受理している。
- 成果物影響: `preregistration_section_sha256` と closure receipt の hash が変わっても consumer 成功となり、後続レポートや §5 が参照する凍結 hash が漂流する。
- 反証されうる形: A8 より上位の裁定が semantic 等価変更を明示的に許しているか、consumer 成功前に raw pin を必ず別 gate で比較する経路を示せば反証される。レビュー対象には無い。

### F2: eligibility fixture が cutoff 後の不適格行しか使わず、受理集合の変異を殺せない

- 重大度: blocker
- 対象: [p3_b4_analysis_ledgers.py:914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_ledgers.py:914)、[test_p3_b4_analysis_ledgers.py:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_ledgers.py:396)、[test_p3_b4_analysis_path.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_path.py:201)、[p3_b4_analysis_prereg_consumer.py:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:857)
- 根拠: 3 系統とも 201 件の適格行の後ろへ不適格または汚染行を置く。`and not attempt.arm_digest_received` を削っても、その行は 202 件目なので `eligible[:201]` に入らず、manifest と verdict は同じままである。exceptional row のテストも同じく 201 件の後ろである。また `reason is SCHEDULED` が真なら `_validate_attempt()` が block id、reference 値、2 hash を既に必須化するため、[ledgers:924](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_ledgers.py:924) 以下の一部は到達可能候補上で恒真である。
- 成果物影響: 汚染 precursor や screening-only 行を cutoff 前に置いたとき、それらが manifest に入り、正しい行を押し出す受理集合変異を検出できない。
- 反証されうる形: 不適格行を 201 件目より前へ挿入し、対象 eligibility 条件だけを除いた変異で特定 node が赤になることを示せば反証される。

### F3: M12 の二層同時変異は、記載どおりでは KILLED にならない

- 重大度: blocker
- 対象: [p3_b4_analysis_ledgers.py:1132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_ledgers.py:1132)、[p3_b4_analysis_path.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py:216)
- 根拠: 行比較 1152 と canonical bytes 比較 1156 を外しても、`manifest != regenerated` が 1160 で同じ変異を拒否する。path 側にも completeness の直接呼出、`build_contract_binding()` 内の再呼出、actual binding の完全一致比較が残る。[path:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py:247) したがってテストは従来どおり「拒否された」として通り、M12 は SURVIVED になる。
- 成果物影響: manifest の行集合・順序・bytes 完全性について、事前登録した mutation kill を閉鎖証拠として使えない。
- 反証されうる形: M12 の exact patch を示し、その patch で他の一致 gate に到達せず登録 node が赤になることを実測すれば反証される。

### F4: assignment 検査の oracle が実装から自己導出され、定数割当変異が生存する

- 重大度: blocker
- 対象: [p3_b4_analysis_ledgers.py:892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_ledgers.py:892)、[test_p3_b4_analysis_ledgers.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_ledgers.py:201)、[test_p3_b4_analysis_ledgers.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_ledgers.py:222)
- 根拠: テストは `derive_assignment()` を 2 回呼び、その同じ関数で生成した manifest と、その同じ関数で再検証した結果を比較する。`derive_assignment()` を全 block で `ON_FIRST` を返す関数へ変えても、型、決定性、manifest 一致、再生成検査は全部成立する。consumer は文面から `1/2` と block ごとの独立性を抽出するが、imported implementation との比較対象に入れていない。[consumer:996](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:996)
- 成果物影響: manifest の全 schedule が on-first になっても通り、実走前無作為化と `Bin(m,1/2)` の帰無分布が成立せず、p 値と verdict が無効になる。
- 反証されうる形: 独立に計算した HMAC test vector、または定数割当変異を殺す node をレビュー対象内で示せば反証される。

### F5: `missing` 同士の tie は正しく実装されているが、挙動検査が無い

- 重大度: must-fix
- 対象: [p3_b4_analysis_contract.py:529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:529)、[test_p3_b4_analysis_contract.py:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_contract.py:356)、[p3_b4_analysis_prereg_consumer.py:969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:969)
- 根拠: 実装は missing/missing を `1/2` とするが、contract テストは missing 対 middle のみ、consumer の rank probe も rejected/aborted と missing/rejected のみである。missing/missing を `0` または `1` に変える単一変異は現行 5 test file を生存できる。
- 成果物影響: 両アーム missing の block で `A_hat`、tie 件数、`m`、p 値、theta 区間が変わり、レポート値が凍結文面と不一致になる。
- 反証されうる形: missing/missing の exact score を独立期待値で検査する既存 node を示せば反証される。

### F6: 統合された fixture は post-freeze bytes の比較 gate へ到達していない

- 重大度: must-fix
- 対象: [test_p3_b4_analysis_ledgers.py:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_ledgers.py:466)、[p3_b4_analysis_ledgers.py:1262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_ledgers.py:1262)
- 根拠: post-freeze 変異は canonical manifest に余分な改行を足している。`assert_manifest_unchanged_before_run()` は先に `load_analysis_manifest()` を呼ぶため、observed bytes が非 canonical として 1273-1279 で拒否され、目的の byte equality 比較 1280 へ達しない。また同じ changed schedule が assignment regeneration と completeness の両方を同一 node 内で赤にする。
- 成果物影響: valid な別 manifest bytes に対する post-freeze 一致 gate と、assignment gate の mutation 帰属をこの node から証明できない。
- 反証されうる形: line 1280 へ到達する valid canonical 変異で拒否されることと、各 gate の期待 node を分離して示せば反証される。

### F7: 12 理由への写像は全域だが、理由の意味を保存していない

- 重大度: must-fix
- 対象: [p3_b4_analysis_adapter.py:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_adapter.py:161)、[p3_b4_analysis_path.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py:207)
- 根拠: generic `_enum_value()` は arm、execution disposition、whiteboard、terminal stage の全不正値を `status_domain_error` にするが、凍結文面の同理由は block の `status` が値域外という意味である。[ref-prereg-b4.md:282](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2001-b4-analysis-path/ref-prereg-b4.md:282) また syntactically valid な ledger hash の bytes 不一致も `binding_domain_error` へ写すが、正本文面は欠落、型違反、expected count の domain error としている。全入力は何らかの理由へ落ちるものの、レポート理由は逐語上の意味と異なる。
- 成果物影響: protocol violation 自体は維持されるが、レポートと invalid 理由台帳が「不正 arm」や「artifact hash 不一致」を誤分類する。
- 反証されうる形: 上位裁定が raw enum 不正を `status_domain_error`、hash 不一致を `binding_domain_error` と明示的に再定義していることを示せば反証される。

## 変異の帰属

| 変異 | 単一理由性 | 実効 gate | 期待 node の確定 |
|---|---|---|---|
| M1 | 否。削る member が未特定で、collection error、enum exact、consumer の複数経路になる | enum import と `test_analysis_invalid_reason_enum_is_exact` | 不可 |
| M2 | 意味は単一だが node は複数 | `block_score()` の `<=`、contract 境界、adapter decimal、consumer rank probe | 複数確定 |
| M3 | 可 | `json.loads(parse_float=Fraction)` | `test_decimal_lexical_is_read_exactly_not_via_float` |
| M4 | 意味は単一だが node は複数 | contract 分岐、path 統合、consumer AST branch shape | 複数確定 |
| M5 | 否。変異位置と「分岐評価」の形が未確定 | `test_evaluate_analysis_does_not_call_validated_branch_for_invalid_input` が最短 gate | 一意には不可 |
| M6 | 意味は単一だが node は複数 | missing 対 rejected/aborted の直接 score と consumer rank probe | 複数確定 |
| M7 | 意味は単一だが node は複数 | `test_evaluate_analysis_establishes_below_a_min_when_p_on_is_significant` と consumer | 複数確定 |
| M8 | 否。E だけでなく ledgers 直接テストと AST gate が同時に効く | first-201 直接期待、consumer slice shape、behavior probe | 複数確定 |
| M9 | 否。現コードでは呼出を eligibility 構築後へ移すだけなら full registry を数えるため意味不変 | 実効 gate は consumer の AST 行順検査。違反数の実効 gate は path の full-registry derive | KILLED node は一意に不可 |
| M10 | 可 | permutation ごとの canonical bytes と sha256 | `test_batch_seal_is_permutation_invariant` |
| M11 | 否。source artifact hash と manifest/registry hash のどれを指すか未確定 | 前者は `test_caller_declared_hash_is_not_accepted`、後者は `test_manifest_and_registry_hashes_are_recomputed_from_bytes` | 変異 target 確定前は不可 |
| M12 | 否。登録した二層を外しても第 3、第 4 の一致 gate が拒否する | `manifest != regenerated`、completeness 再呼出、actual binding 比較 | 現記載の exact mutation なら赤 node なし、SURVIVED |
| M13 | 否。raw pin だけを外しても acceptance set は現在と同じ。raw と semantic の両方を外すなら別変異 | 実効 gate は semantic hash。raw exact hash は consumer 内では冗長 | raw-only は node なし。両方なら `test_semantic_change_with_identical_literals_is_rejected_by_section_hash` |

## 総括

blocker は 4 件である。最重は F4 の定数 assignment 変異生存で、sharp null と二項 p 値の前提そのものを失わせる。  
exact 算術、tie 境界、Clopper-Pearson の外向き包囲、verdict 順序の現実装は凍結文面と一致している。  
一方、exact section hash は consumer の実効 gate ではなく、M12 と M13 の kill 期待も成立しない。  
既存 sanctioned path には caller が無いため、既存の certified 選択・レポート受理集合は 0 bit 変更のままである。  
ただし新設 consumer の受理集合は exact freeze より広く、これは指示された変更ではない。  
親の 121 passed は確認したが、上記はそのテスト集合自体の反証力と帰属の欠陥なので、通過結果では反証されない。