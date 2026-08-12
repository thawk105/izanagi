## 総括

- **BLOCKER: 6**
- **MUST-FIX: 2**
- **NIT: 0**
- **land 判定: 不可**

plan の `hold` 4 node 自体は [T-793] R2 の見送り範囲に収まる。しかし、親 brief が保留対象とした production 検査点には、測定公正・admission・防壁が同居している。さらに現行 caller は verifier の戻り値を見ないため、単に typed hold を返す実装は静かな成功になる。

## BLOCKER

### 1. typed hold は現行 caller では fail-open になる

`brief.md:70-75` は verifier が例外の代わりに hold 判定を返す案だが、現行 caller は戻り値を捨てている。

- `orchestrator/campaign/s1_direct_comparison.py:141-142`
- `orchestrator/campaign/s1_verify_extime_calibration.py:205-209`
- `orchestrator/campaign/s8b_holdout_freeze.py:1002-1003`
- `orchestrator/campaign/s8b_oracle_driver.py:393-397,429-433`

`verify_document()` が hold object を返しても wrapper は元 document を返し、oracle driver は refusal を追加しない。

**成果物影響:** 未検証 freeze が検証済みとして operating point、oracle gate、manifest、report へ進み、certified 選択の受理集合が静かに広がる。

hold を例外とは別の return にするなら、全 caller を列挙し、exhaustive な状態分岐と report/台帳への伝播を同じ変更で入れる必要がある。

### 2. known-axes の関数単位保留は S-1b 比較公正を巻き込む

`orchestrator/campaign/s1_known_axes_freeze.py:831-879` では、保留対象の head/pin/再構成検査 `:863-879` より前に次が同居する。

- trigger name/mask の schema 検査: `:802-825`
- `system_gate` と `ident_all` の flags 同一性・predicate 差分: `:859`、実体 `:677-707`

後者は gate on/off を同条件で比較する S-1b の測定公正であり、bytes provenance ではない。

**成果物影響:** gate on/off の flags が異なる freeze を calibration/oracle が利用でき、レポートの性能差が gate 効果ではなく構成差を含む。

`verify_document` 全体ではなく `:863-879` の検査だけを分離しなければならない。

### 3. holdout verifier には対象外検査が少なくとも 3 種同居する

`orchestrator/campaign/s8b_holdout_freeze.py:848-988` で、保留対象 `_verify_source` / `_verify_head` (`:874-877`) と次が同居する。

- 未承認世代の admission 拒否: `:865`
- holdout 漏洩検出と rr50 positive control: `:879-880`
- holdout と実構成の `variant_binding` 再導出: `:974-978`

漏洩検出は親指摘どおり実験妥当性である。`variant_binding` も測定対象構成の取り違えを防ぐ測定公正側である。

**成果物影響:** repo に既知化した holdout、未承認世代、または誤った構成 binding が oracle manifest/selector 対応へ入り、report の holdout 別構成参照が変わる。

### 4. frozen-artifacts の 1 node に blind selector 証拠が混在する

`orchestrator/tests/test_frozen_artifacts.py:125-136` は 23 件を一つの loop で検査する。その集合には凍結 JSON だけでなく、次の blind seal が含まれる。

- selector prediction: `:57-58`
- journal、payload、envelope、raw response: `:59-84`
- exact key-set: `:100-113,139-153`

ファイル自身が `:31-32` でこれらを「盲検封印」と定義している。oracle 結果を見た後の coherent な prediction/journal 書換えを防ぐ実験妥当性であり、単なる実装 provenance ではない。

**成果物影響:** selector 選択と根拠を oracle 後に整合的に差し替えても exact original-bytes の番人が消え、verdict/report の予測一致値を後付けできる。

23 件一括 node の保留は禁止し、少なくとも selector 証拠 14 件は keep 側へ分離する必要がある。

### 5. protocol の入口とされた node は pin seal ではなく防壁検査である

`brief.md:44` が入口に挙げた `test_protocol_builder_repo_tree_guard_is_wired_to_real_root` の実体は、`orchestrator/tests/test_real_repo_serialization.py:823-897` にある。

この node が検査するのは次である。

- guard が実 `ROOT` を受けること: `:878-885`
- builder/writer が同一 guard action 内でだけ動くこと: `:852-864,887-897`

これは protocol pin seal ではなく、防壁の自己完全性そのもの。保留対象外である。

**成果物影響:** guard を tmp root へ誤配線しても受入が緑になり、builder/writer が実 repo や凍結領域を変更できる。

この node は `keep` に固定し、実際の protocol pin node を別途特定すべきである。

### 6. T-080 の public gate は receipt provenance と正しさ検査を一緒に実行する

`orchestrator/campaign/t080_freeze_migration.py:2169-2268` の `verify_receipt` は receipt bytes/history と同時に次を実行する。

- positive control: `:2219-2221`
- holdout live leak scan: `:2222-2226`
- live ccbench identity: `:2227-2230`
- known schemaと S-1b pairing: `:2231-2237`

同じ検査は official adapter の `:2321-2332` にも重複している。`verify_receipt` または `static_gate_adapter` 全体を保留できない。

**成果物影響:** `ReceiptResolution.active-valid` と T-080 observation が、holdout 漏洩・比較条件不一致・live ccbench 不一致を含んだまま oracle driver と report に渡る。

receipt の raw bytes、履歴、repin closure だけを独立した hold 単位へ切り出す必要がある。

## MUST-FIX

### 1. 4 hold node の解除 positive control が計画上まだ存在しない

`plan.md:50-59` は未 land の growth-tests wave に依存するが、現 tree には `growth_test_holds.py` も opt-in 分岐もない。`conftest.py:239-252` は real-repo group の付与だけである。

必要な positive control は最低限次の 3 点である。

1. env 無指定では 4 function が理由付き skip になる。
2. exact env 値では同じ 4 function が収集・実行される。
3. 各元検査の負例が実際に赤になる。無効な env 値では解除されない。

**成果物影響:** hook の条件分岐が壊れても全 node が永久 skip のままになり、ユーザー解除後も R2 番人が復活しない。

### 2. [T-499] A/B を plan v2 の明示的 keep 集合へ入れる必要がある

plan には次の正しさ境界が node/function 単位で書かれていない。

- reviewed spec approval: `orchestrator/campaign/s8b_oracle_spec.py:182-200,258-274`
- freeze v2 approval/active pointer: `orchestrator/campaign/s8b_ratified_freeze.py:1214-1334`
- published freeze 再検証: `orchestrator/campaign/s8b_ratified_freeze.py:3244-3254`

これは T-499 確定リスト `:19-30` が明示した「使う機構」である。特に `s8b_ratified_freeze` は growth wave との重複候補なので、一般的な「freeze 族」記述だけでは粗すぎる。

**成果物影響:** A を巻き込むと official manifest/report の `spec_sha256` が未承認 spec と区別不能になり、B を巻き込むと approval/active pointer を経ない freeze が report/judge の参照対象になり得る。

## plan の `hold` 4 件を 1 件ずつ確認

| node | 判定 | 唯一検出者 | 保留時の変化 |
|---|---|---|---|
| `test_t793_publication_ledger.py::test_duplicate_root_kind_ordinal_identity_is_rejected` (`:180-185`) | hold 妥当 | この tuple 重複拒否の専用 node は他にない | 未使用 publication reader の重複拒否回帰が通常受入から消える。現行 certified/report/実台帳値は不変 |
| `...::test_unchanged_ledger_bytes_across_merge_history_are_accepted` (`:259-302`) | hold 妥当 | merge 正例の唯一 node | append-only gate の過剰拒否検出が通常受入から消える |
| `...::test_committed_non_prefix_ledger_history_is_rejected` (`:310-328`) | hold 妥当 | truncate/rewrite の唯一 node | committed ledger rewrite の拒否回帰が通常受入から消える |
| `...::test_committed_delete_and_recreate_is_rejected` (`:331-350`) | hold 妥当 | delete/recreate の唯一 node | ledger path 再作成の拒否回帰が通常受入から消える |

4 件はいずれも非 test caller がなく、T-499 が見送った R2 に一致する。消える検出力は実在するが、今回は裁定された縮小である。ただし上記 positive control が完成するまでは land できない。

## `keep` / `unsure` 側の逆方向監査

過剰な `keep` は確認できなかった。

- F2 の land/spool 関数にはすべて production caller があり、live transaction/admission である。
- T-810 の `test_preregistration_contains_adjudicated_upper_closure` は trust-root 不在だけでなく authorization、artifact presence、測定手順を同じ node で検査するため、一括 hold 不可。
- F3 の identity literals、canonical entry 正例、primary disjoint は R3 を reject-all の恒真保証にしないため残す必要がある。
- F4 の 2 `unsure` は D282 の既承認 7 blob/alpha descriptor と、見送った追補 P が分離されていない。現状どおり保留しないのが安全。
- `test_alpha_reservation_commit_must_remain_unpinned` は pin の再導入を拒否する D320 整合検査なので `keep` が正しい。
- trace-enabled/trace-disabled 分離を検査する node が今回の `hold` 4 件へ混入した形跡は、静的検索では見つからなかった。

pytest は実行していないため、緑は主張しない。編集・commit も行っていない。