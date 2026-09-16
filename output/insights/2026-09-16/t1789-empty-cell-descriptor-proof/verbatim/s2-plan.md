## brief と現物の食い違い

必読6ファイルは全文確認済み。以下は静的読解であり、テスト・probe の再実行はしていない。

- **P3 の「実行を名乗らない」は限定が必要。** 正確には「完了・観測成功を名乗らない」。`_install_attempt_registry_binding` は terminal-failure でも observation-start を記録する（test file:403–409）。partial は「一切実行していない」の証明ではない。
- **既存 node の名前と入力 status は異なる。** `test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof`（test file:906）は cells だけを空にし、report・receipt とも `status="complete"` のまま。brief の再現表とは整合する。
- **producer 正例が証明する範囲に注意。** `test_trial_registry.py:3005` の P6 node は production の受入処理で receipt を発行し、最後は **parse** する。`verify_acceptance_receipt` と capability gate の通過までは検査していない。今回の正例で補う必要がある。
- P1 の status 式には、長さ一致・fatal_error 不在に加えて stop_reason と build admission の条件もある（driver:3816）。空の selected なら式だけでは complete を排除できないが、launch workload の非空制約と登録 trial の単一 workload 束縛がある（`trial_registry.py:3963,3764`）。登録済み production 経路についての結論は維持できる。
- P4 は現物との食い違いではなく、互換性方針の選択。以下で比較する。

以下、production file は `orchestrator/campaign/s8c_acceptance_receipt.py`、test file は `orchestrator/tests/test_s8c_acceptance_receipt_v2.py` を指す。

## production 変更案

変更 symbol は **`verify_acceptance_receipt` のみ**。

[production file:2053](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1789-empty-cell-descriptor-proof/orchestrator/campaign/s8c_acceptance_receipt.py:2053) の直前、既存 mandatory-reasons 判定（2039–2052）の**後**、cross-binding aggregate 判定の**前**へ挿入する。

```python
    if rederive_arm_execution and any(
        trial.status == "complete" and not descriptor_proven
        for trial, descriptor_proven in zip(receipt.trials, descriptor_proofs)
    ):
        _fail(
            "receipt-arm-binding",
            "complete trial lacks descriptor proof",
        )
```

- failure code は既存の `receipt-arm-binding`。
- 完全文言は `[receipt-arm-binding] complete trial lacks descriptor proof`。
- `rederive_arm_execution` は1999–2004で v2〜v5 を表す。
- trials の順に2025で必ず proof を追加するため、この地点では両列とも6件。長さ検査や新しい helper は不要。
- report と receipt の status 一致は1421で検査済み。report を再読する必要はない。
- この地点へ到達した `descriptor_proven=False` は cells=[] に対応する。非空で descriptor 不在・不一致なら1468–1480で既に拒否される。

既存 node の評価順は次のとおり。

1. 書き直した report hash と tracked receipt は整合している。
2. cells=[] により proof=False。status、arm_execution、run-start、expected digest は整合する。
3. C02 が無いため、2039–2052の既存判定が発火する。
4. 新判定には到達せず、既存文言  
   `[receipt-mandatory-reasons] c02-arm-binding-unproven was dropped without descriptor proof`  
   を維持する。

**D949 に抵触する冗長照合ではない。** 親の実測 C2/C3 は、新条件を満たしながら現在の全 verifier gate を通過している。C2 では expected digest 一致も実測済み。C3 では矛盾 descriptor を消すと verified になる。したがって「既存 gate の成立 ⇒ complete trial の descriptor 証明」は偽で、新判定は実際に受理集合を狭める。

## 適用世代の比較と推奨

| 観点 | v2〜v5 共通 | v5 限定 |
|---|---|---|
| 条件式 | 上記の `rederive_arm_execution` | 先頭を `receipt.schema_version == SCHEMA_VERSION` に置換 |
| 差分量 | 1判定ブロック | ほぼ同量。共通案の行数上の優位は小さい |
| legacy の受理集合 | complete＋cells=[]＋C02 を新たに拒否 | 変化なし |
| 実測との対応 | A2/A3/B2 と C2/C3 を拒否 | C2/C3 のみ拒否 |
| D1757 | 到達不能な legacy も狭める点は緊張がある | legacy capability 到達不能という先例に沿う |
| 必要な追加資料 | 既に読んだ status と proof のみ | 同左 |

**推奨は v2〜v5 共通。** 理由は、今回の対象が下流 capability だけでなく「descriptor 不在の実行主張が verified になる構造」であり、legacy v2 にも A2/A3/B2 の実在反例があるため。D519 の descriptor 不在の例外は「部分 report」であり、complete の例外ではない。

ただし「版分岐が不要だから」だけでは正当化しない。D1757 は、到達不能性に加えて **legacy の失われた campaign 現物を新たに要求する過剰拒否**を理由としている。今回その追加要求は無い。この違いを根拠に、既に再現された legacy の complete 主張も修正対象とする。

D947/D948 の authority root、固定 V1 authority、schema・保存形式は変更しない。ただし legacy の受理集合が狭まる事実は明記する。

## テスト案

test file:906 の既存 node 付近に、**3関数・4 collected nodes**を追加する。C2 の v2/v5 パラメータ化だけを追加し、共通適用の境界も直接検査する。

| 略号 | 追加 node | 種別 |
|---|---|---|
| N2v2 / N2v5 | `test_partial_receipt_cannot_claim_complete_without_descriptor_proof_even_with_c02[v2]` / `[v5]` | 負例、A2/C2 |
| N3 | `test_partial_receipt_cannot_hide_conflicting_descriptor_by_dropping_cells` | 負例、C3 |
| P | `test_partial_receipt_with_c02_and_no_cells_passes_current_capability` | 正例、v5 |

負例の新判定に対する完全一致 regex は共通で次とする。

```python
r"^\[receipt-arm-binding\] complete trial lacks descriptor proof$"
```

**N2v2 / N2v5**

- `_fixture`、`_trial(value, "H2", "off")`、`_canonical`、`_rewrite_receipt` を利用。
- report の cells を空にし、`_write` の返す hash で row の report hash を更新。
- C02 を sorted unique な reason 集合へ追加する。
- status は report・row とも complete、do_build=False を確認する。
- v5 の場合だけ、変更後に `_upgrade_to_current(repo, value)`。
- receipt を書き直して公開 verifier の拒否を検査する。

**N3**

- H1/on の read_ratio が整数80であることを確認して79へ変更する。receipt/run-start の digest は変更しない。
- report hash と receipt を更新し、まず v2 公開 verifier で以下を検査する。

```python
r"^\[receipt-arm-binding\] cell descriptor content digest differs from receipt$"
```

- 続いて同じ report の cells を空にし、hash を更新、C02 を追加、`_upgrade_to_current`、`_rewrite_receipt`。
- 新判定の完全一致 regex で拒否を検査する。
- `_synchronize_arm_execution(..., descriptor=...)` は使わない。矛盾 descriptor に合わせて主張 digest を変更すると、C3 と異なる入力になる。

**P**

- H2/off だけを cells=[] にして hash を更新し、C02 を保持。
- 次を一度だけ呼ぶ。

```python
_upgrade_to_current(
    repo,
    value,
    terminal_failure_trials=frozenset({row["trial_id"]}),
)
```

- `_rewrite_receipt` 後、verified、対象 trial の partial、C02 保持、certifying=False を確認。
- `require_current_verified_receipt(verified)` が成功し、同じ receipt hash を返すことを確認。例外期待はない。

**helper は使用可能。** [test file:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1789-empty-cell-descriptor-proof/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:425) 以降が row/report の status と report hash を更新し、その hash で terminal-failure を作り、prefix hash と projection も設定する。

`_upgrade_to_current` は先に cross-binding leaf を作るが、no-build leaf は status を含まない（`autonomous_trial_completeness.py:4165–4188`）。したがって **cells の変更を helper 呼出し前に済ませれば**、その後の status 更新で leaf は古くならない。

## 変異候補

変異用の固定実行集合を次の6 node に限定する。

- N2v2、N2v5、N3、P
- E：既存 `test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof`
- B：既存 `test_v5_attempt_binding_accepts_all_predeclared_observed_units`

以下の赤集合は、**この6 node 内の完全集合の静的予測**。repo 全体の実測済み failure 集合ではない。

| 変異 | 赤になる全 node | 赤になる理由 |
|---|---|---|
| 新判定を削除 | N2v2、N2v5、N3 | 最後の verifier 呼出しが例外を出さない |
| `== "complete"` → `!= "complete"` | N2v2、N2v5、N3、P | complete 負例を取り逃がし、partial 正例を拒否 |
| `== "complete"` → `== "partial"` | N2v2、N2v5、N3、P | 上と同じ |
| `== "complete"` → `== "completed"` | N2v2、N2v5、N3 | 該当 status が無く負例を取り逃がす |
| 新ブロックを2039の直前へ移動 | E | mandatory-reasons より先に新文言を返し、既存 regex と不一致 |
| 適用条件を v5 限定へ変更 | N2v2 | 共通適用の v2 負例だけ取り逃がす |

拒否層の競合を避ける根拠：

- N2/N3 の最終入力は C02 保持なので mandatory-reasons を通る。
- hash を更新し、v5 の leaf・aggregate・attempt terminal を変更後の report から作る。status は complete、terminal は observed で整合する。
- expected digest は fixture のまま。N3 の矛盾 descriptor は最終入力には存在しないため、descriptor mismatch と freeze mismatch のどちらも発火しない。
- do_build=False なので、C4 の「build report must contain at least one cell」には入らない。
- 削除変異で最後まで通ることは親の C2/C3 実測とも対応する。
- P は partial／terminal-failure と hash が整合し、残り5 trial は descriptor 証明済み。反転変異による新判定だけが拒否原因になる。
- **順序変異は例外**で、E には意図的に2つの成立条件がある。これは受理集合の変化ではなく、最初に返す診断の契約を検査する。独立した欠陥検出力として二重計上しない。

## 波及の静的列挙

`orchestrator/tests/` の Python files に対して、変更 symbol、関連 helper 名、failure code を `rg` で検索した結果：

| 参照 | 該当 test file |
|---|---|
| `verify_acceptance_receipt` | `test_s8c_acceptance_receipt.py`、`test_s8c_acceptance_receipt_v2.py`、`test_trial_registry.py`、`test_layer3_report.py` |
| `require_current_verified_receipt` | `test_s8c_acceptance_receipt.py`、`test_s8c_acceptance_receipt_v2.py`、`test_layer3_report.py` |
| `receipt-arm-binding` | `test_s8c_acceptance_receipt_v2.py` |
| `receipt-mandatory-reasons` | `test_s8c_acceptance_receipt.py`、`test_s8c_acceptance_receipt_v2.py` |
| `_verify_v2_trial_arm_execution` / `descriptor_proofs` | test Python files に直接参照なし |

consumer の具体的な入口は `test_trial_registry.py:1777,1906`、`test_layer3_report.py:671`。後者の helper は v1 receipt を作るため、新条件の対象外。production consumer は `layer3_report.py:918` の capability 呼出し。

**subprocess pin：影響なし（読解）。** `test_ccbench_spawn_sites.py:264` は `("campaign/s8c_acceptance_receipt.py", "<module>._git"): 1` を固定し、2664の node が静的呼出し箇所一覧を比較する。提案は subprocess 呼出し箇所を増減しない。これは動的な Git 呼出し総数の pin ではない。

**duration 台帳：新 node の登録は必須ではない（読解）。**

- `conftest.py:1675–1695` は未登録 node の duration を `None` とする。
- 1740–1763では未知コストとして並べ替える。collection から除外せず、未登録をエラーにしない。
- `tools/acceptance_shards.py:392–404` は未登録 node に **1.0秒**の割付けコストを与える。
- ledger の `nodeid_count` は ledger 内の辞書件数との整合検査であり、現在の全 collection 件数との一致要求ではない。

従って `acceptance_duration_ledger.json` は今回編集しない。親の実測対象は新旧焦点 node、上記 consumer files、spawn inventory、通常の受入全走とする。

## 修正後も残る形と scope 判断

| 残る形 | 判断 |
|---|---|
| v2〜v4：report・receipt とも partial、cells=[]、C02 保持 | 引き続き verified になり得る。D519 の部分 report として許容。current capability は通らない |
| v2〜v4：complete 以外の任意の非空 status、cells=[]、C02 保持 | parser は非空文字列しか要求しないため残る。再現済み complete 欠陥とは区別し、status 値域の一般化は今回行わない |
| v5：partial、cells=[]、C02 保持、terminal-failure と report hash が整合 | verified と current capability を通す正例。完了・観測成功の主張ではないため、P1 の意味での T-1789 には当たらない |
| v5：partial への変更だけで registry は observed のまま | 通らない。1715–1723の既存 status 対応検査で拒否 |
| partial でも非空の矛盾 descriptor が残る | 通らない。既存 descriptor digest 検査で拒否 |
| complete、descriptor 証明あり、C02 保持 | 通り得る。今回の descriptor 不在の欠陥ではない |

v5 の terminal-failure への変更は、既に committed な observed terminal を単に上書きすればよいわけではない。registry の append-only history も満たす必要がある。

**scope の重要な境界：** 「arm_execution という宣言値があり、descriptor が無い receipt は、partial も含めてすべて T-1789」と定義するなら、上記 partial 正例は欠陥として残る。しかしそれは D519 の部分 report 許容と今回指定された正例に衝突する。本案は「complete／observed を名乗る trial に証明が無い」という範囲を閉じる。partial が実際に一切実行されなかったことや、証拠削除の過去が無いことまでは証明しない。

## scope 外候補

実装へは含めない。

- legacy status の値域制約。
- partial に対する fatal_error、run-finish、実行履歴の追加検査。
- capability gate での C02 一律拒否。
- producer、attempt registry、schema、保存形式の変更。
- 「実行開始」と「観測成功」の区別を越えて、partial の証拠削除まで禁止する別仕様。

## 総括

既存 mandatory-reasons 判定の直後に、**complete かつ descriptor 未証明の trial を拒否する1ブロック**を追加する。v2〜v5 共通を推奨し、3関数・4 node で legacy/current の拒否と v5 partial 正例を検査する。

ファイル変更・テスト実行はしていない。変異の赤集合と正例の成功は静的予測であり、親の実測で確定する。