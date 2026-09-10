## RA-1

有効な claim field の発行後改竄が使用時再検証を通るため、不変条件 1 は未達である。

[実測] `orchestrator/campaign/s8b_holdout_admission.py:945-1011` の claim identity は `entry_kind` を digest に含めず、`:4821-4830` は `"fresh"` と `"resume"` の両方を許可する。`:4860-4884` の主台帳再構成と `:4889-4900` の marker 再構成にも `entry_kind` は入らず、`:5008-5020` の capability identity にも保存されない。そのため `:5134-5143` の再検証後も identity は等しいままで `action()` が実行される。

具体的な破れ方: current marker から capability を発行した後、claim の `entry_kind` だけを `"fresh"` から canonical な許可値 `"resume"` へ書き換え、元の引数で `use()` する。marker と主台帳を触らなくても誤って使用が許可される。負例テストは `orchestrator/tests/test_s8b_holdout_admission.py:2361-2385` で発行後の順序を作っているが、claim を `"forged"` という不許可値へ変えるだけなので、許可値間の改竄を検出できない。

深刻度: `blocker`

成果物への影響: 改竄された claim のまま保護対象 callback が台帳を更新でき、後続 inspection の resume 判定や refreeze eligibility (`s8b_holdout_admission.py:6478-6490`) と attempt registry の参照が不整合になる。

## RA-2

current schema 検査と marker exact-shape 検査の一部は、自ら生成した候補へ適用されるため恒真である。

[実測] `orchestrator/campaign/s8b_holdout_admission.py:4960-4967` を通過すると generation の両値は非 `None` であり、`:4358-4370` の builder は必ず current schema を返すため、`:4978-4981` の拒否分岐には到達できない。また `:4982` と `:5000-5002` が exact-shape helper に渡すのは disk marker ではなく内部生成した `expected_marker` である。disk marker の extra key は最終等値比較 `:5003-5006` が拒否している。

具体的な破れ方: exact key 集合検査を `>=` へ緩める M6 相当の変異を入れても、extra-key 負例は `disk_marker != canonical_marker` で拒否され続けるため、その変異を検出できない。誤受理自体は別の等値比較が防ぐため現時点では発生しない。

深刻度: `nit`

成果物への影響: 現在の成果物値や受理集合は変わらないが、exact-key 防壁が発火したという mutation 証拠は成立しない。

## 反証材料なし

- 不変条件 2: `repetition` と `attempt_ordinal` は identity に格納される (`s8b_holdout_admission.py:267-280`)、journal から再導出される (`:4911-4950`)、使用引数と比較される (`:5100-5129`)。別軸の負例 `test_s8b_holdout_admission.py:2332-2351` も実際に `use()` まで進め、callback の実行を禁止している。反証材料なし。
- 不変条件 3: docstring は current-generation 専用と明記し (`s8b_holdout_admission.py:283-289,5027-5031`)、入口は `_cell_state()` の process-local issued token 要求 (`:4232-4237,5034`) を維持する。legacy validator や legacy 受理経路の新設・削除はない。反証材料なし。
- 不変条件 4: capability が束縛するのは admission の measurement-generation claim digest (`:4985-4994,5011`) である。cell-effect digest は current claim/marker の内部再導出にだけ使われ、registry classification claim digest は新 API に流入していない。識別子取り違えの反証材料なし。
- 受理集合: 既存 `consume_attempt_ticket`、既存 marker validator、legacy cut-6 recovery は変更されていない。新 API 以外の durable evidence 受理・拒否が変わった反証材料なし。
- テスト弱体化: test file は 404 行の追加のみで、既存期待値の反転・緩和・削除・skip はない。正例 `test_s8b_holdout_admission.py:2138-2156` は production issuance と `use()` を通り、callback の戻り値まで確認する。反証材料なし。
- 編集面: base との差分は `s8b_holdout_admission.py` と `test_s8b_holdout_admission.py` の 2 file だけで、提示 patch と worktree 差分も一致した。
- pytest は実走していない。静的検査のみであり、緑とは判定しない。

## 総括

- 不変条件 1 - 未達。許可値 `"fresh"` から `"resume"` への発行後 claim 改竄を拒否できない。
- 不変条件 2 - 達成。slot の 4 軸が identity に入り、使用時に比較される。
- 不変条件 3 - 達成。current-generation 専用で、legacy の受理を広げていない。
- 不変条件 4 - 達成。classification claim、measurement-generation claim、cell-effect の各 digest domain に取り違えはない。

結論は `blocker` 1 件による差し戻しである。