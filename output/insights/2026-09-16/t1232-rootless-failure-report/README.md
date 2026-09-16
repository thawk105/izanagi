# [T-1232] failure-only の診断 report を root 引数なしで独立検証できるようにした

wave: `dev-wave-t1232-rootless-failure-report` (branch `worktree-dev-wave-t1232-rootless-failure-report`)
base commit: `d97c423bdd14e0b416cb4f585d350e6c2b251287`
実装 commit: `7bf2a8c9be9ca8bab584cbe6aaaaf3232c4142f7`

## 1. 何が壊れていたか

producer (`orchestrator/campaign/p3_autonomous_workload_trial.py`) は report を publish する前に
completeness、execution digest chain、`assert_campaign_layer3_chain` を呼ぶが、
**`verify_s8c_cross_binding` は呼ばない** (producer 内の呼び出し 0 件。受入
`orchestrator/campaign/trial_registry.py` だけが 2 箇所で呼ぶ)。standalone verifier
`verify_autonomous_trial_files` は呼ぶ。

この非対称のため、**producer が publish できて独立検証器が原理的に受理できない failure-only の
build report が存在していた。** campaign identity を宣言している admission 失敗 cell は、

- campaign directory が無ければ `autonomous_trial_completeness.py:4255` で、
- directory はあるが `reports/layer3_report.json` が無ければ `:4374`〜`:4379` の
  `cross-binding-build-population` で、

**campaign output root を与えても無条件に落ちる。** 診断が要る失敗走ほど独立検証できなかった。

## 2. 起票文との差 (段 1〜4 で訂正した)

起票文 (`docs/archive/worklog-phase3-0816-593.md:578`) は「非空 build report に
`campaign_output_root` を要求する」としていたが、**root 要求には既に免除が 2 つあった。**

- `fatal_without_cells` (`:5054`): `do_build=True` かつ `fatal_error` かつ `cells == []`。
- `failure_without_campaign` (`:5059`): 全 cell が `is_exact_campaignless_failure_fallback_cell` に一致。

後者は 2026-08-18 の `79194aebf9` (T-1348 の C09/C10 consumer 配線) が副次的に入れたもので、
T-1232 を閉じる意図では入っていない。producer が campaign 生成前に落ちたときの 6 key の fallback cell は
**この免除に厳密一致するので、着手時点で既に root なしで通っていた。**

本 wave が実際に直したのは、**campaign identity を宣言した失敗 cell** である。これは root の有無と
無関係に受理できなかった。

### 親の段 1 brief が誤っていた点

段 2 plan と段 3 レンズ 2 本が次を指摘し、親が現物で裏取りして段 4 で訂正した
(逐語は `verbatim/s4-ruling.md` §2)。

| brief の記述 | 実際 |
|---|---|
| root を省くと失われるのは path identity 束縛だけ | identity を持つ失敗 cell は root 有りでも cross-binding が先に落とす |
| producer の失敗 report の実例として `test_p3_autonomous_workload_trial.py:8800` を挙げた | 同テストは completeness・digest chain・`layer3_report.render` (admitted を返す fake)・`assert_campaign_layer3_chain` を monkeypatch で無効化しており、実出力の証人にならない |
| 残る穴は partial cell 経路だけ | 正常 return 後の admission 失敗 (role-invalid、cell 内 wall-budget) も failure-only report を作る |

## 3. 何をしたか

明示 opt-in の**非 certifying な診断検証経路**を足した。

- `verify_autonomous_trial_files(..., failure_only_diagnostic=True)` と CLI `--failure-only-diagnostic`。
- 新分岐の発火条件は 4 つの積 — flag が真、root 未指定、`fatal_without_cells` でない、
  `failure_without_campaign` でない。**root を渡した呼出しは従来検証をそのまま実行し、flag で検査を
  省略できない。既定経路の受理・拒否は 1 つも変えていない。**
- 受理形は閉じた厳密一致の述語 `_is_exact_failure_only_diagnostic` だけ。
- **欠けている束縛は素通りさせず、不在を report 側の事実と突き合わせて証明する。**
  - journal の role-attempt 件数を `honest_accounting.role_query_count` と照合する (0 件も)。
  - 探索走が arm 束縛の provider 成果物を主張したら矛盾として拒否する (producer は
    `arm_binding_digest` が `None` の探索走では書かない)。
  - valid role には raw 参照と bytes を必須にする。
  - 提案参照の宣言は拒否する (producer は探索走で提案参照を記録しない)。
  - 提案の不在は「preview 前の早期停止」であることを generation の形から証明させる。
- Layer-3 側は既存 `assert_campaign_layer3_chain` をそのまま呼ぶ。
- 戻り値の receipt は検証範囲の申告であり署名ではない。`certifying=false`、
  `campaign_output_root_binding="not-verified"`、`s8c_cross_binding="not-established"`。

### 狭めた 3 点 (導出できない形は受理しない)

| 除外した形 | 理由 |
|---|---|
| 診断情報 (`layer3_admission_diagnosis`) 付きの cell | 生成器 (`layer3_report.render` の失敗) を mock せずに正例を作れなかった |
| invalid / skipped role、`error_artifacts` を持つ role | producer は error 成果物を取得できたときだけ書く。不在を report 側の事実から証明できない |
| `arm_execution` を持つ report | 正式 registered 系列。publish 前に digest 検査で拒否されるので対象になりえない |

## 4. 成功集合が増えることを明示する

**これは standalone verifier の成功集合を増やす変更である。** 段 3 レンズ A の指摘を受け、
opt-in であることと `certifying=false` であることを「受理集合不変」の証拠に使っていない。
増えるのは上記の閉じた形についてだけで、certifying 受入 `assert_trial_registry_acceptance` は不変である。

段 6 レビュー B が現物から数えた結果、**この経路が救う producer の実出力は外側 2 形・3 経路**ある
(role 開始前の例外、cell 内 wall-budget による正常 return、valid role の raw 保存後の preview 例外)。
空振りではない。

## 5. 変異 matrix

`mutation/` に spec と結果を置く。harness は `tools/mutation_harness.py`、runner は
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_autonomous_trial_completeness.py -q -rf -p no:cacheprovider`、
`--runner-mode dispatch --detached`。

- **probe** (`spec-probe.json` / `result-probe.json`): 全件を SURVIVED 期待で登録し観測 node を集めた。
  baseline PASSED、8 変異すべて MISMATCH (= 実際は全件赤)。
- **final** (`spec-final.json` / `result-final.json`): 観測 node を完全集合として KILLED 期待で登録。
  **baseline PASSED・8/8 KILLED・MISMATCH 0・SURVIVED 0・8 変異すべてで期待 node と完全一致。**
  repo head `7bf2a8c9be9ca8bab584cbe6aaaaf3232c4142f7`。

| # | 殺す機構 | 赤 node 数 |
|---|---|---|
| M1 | opt-in 条件を恒真化 | 4 (**既存 `test_build_file_verification_with_cells_still_requires_campaign_root` を含む** — 既定経路が無改変であることの裏取り) |
| M2 | cell key の厳密一致を部分集合判定へ | 2 |
| M3 | 診断 helper の `assert_campaign_layer3_chain` 呼出し削除 | 3 |
| M4 | valid role の raw bytes 検証を無効化 | 1 |
| M5 | CLI から新引数を転送しない | 1 |
| M6 | 診断 dispatch を無効化 | 16 (新規テストすべて) |
| M8 | 提案宣言の拒否を `continue` へ戻す | 1 |
| M9 | 探索走の provider 主張の拒否を無効化 | 1 |

### 事前登録からの訂正

- **M4 を再照準した。** 当初の「role 件数照合の削除」は、先行する accounting 検査 (`:2924`、`:3069`、
  `:3207`) に覆われて単一理由性が立たないと段 6 レビュー B が示した。raw bytes 検証へ差し替えた。
- **M7 を登録から外した。** 「admitted cell を弾く条件の削除」は、`status != partial` と件数検査に
  遮られて生存する。段 6 fix 子が単一理由の入力を構成しようとしたが、先行 gate
  (`:3146`、`:3150`〜`:3154`、`:3165`〜`:3168`) により**構成不能**と確定した。
- **M8・M9 を追加した。** 段 6 fix で足した機構 (M8) と、実装子が足した provider 主張の拒否 (M9)。

## 6. 直さなかったこと (real だが scope 外)

1. **正式 registered 系列の failure report は回復しない。** identity を持つ admission 失敗は publish 前に
   `autonomous_trial_completeness.py:1137`〜`:1141` の digest 検査で拒否される。
2. **admitted prefix + identity failure の混在 report** は root を与えても `:4374` と `:4911` の条件が
   両立せず受理できない。
3. **producer が publish 前に `verify_s8c_cross_binding` を呼ばない非対称そのもの。**
   producer 側で呼ぶか、verifier 側で受けられるようにするかは設計択一である。
4. **`campaign_id` が絶対 path でも `expected_root` の突合せが通り、`campaigns/<単一 ID>` 配下という
   包含保証は既存 chain にも無い。** そのような `campaign_id` を出す producer 経路は確認していない。
   依頼の scope 外 (仮想リスク向けの gate 追加) なので gate は足さず、receipt が包含を主張しないことだけを確かめた。

## 7. 工数

codex 子 7 本 (model `gpt-6-astra`、effort すべて medium)。

| 段 | 本数 | 所要 / call |
|---|---|---|
| 段 2 plan | 1 | 379 秒 / 9 |
| 段 3 consult | 2 (sol / luna) | 175 秒 / 6、203 秒 / 9 |
| 段 5 author | 1 | 1243 秒 / 55 |
| 段 6 review | 2 | 226 秒 / 8、148 秒 / 7 |
| 段 6 fix | 1 | 646 秒 / 38 |

変異走 2 回 (job 所要の和: probe 787 秒、final 340 秒)。

## 8. 逐語

`verbatim/` に親 brief、段 2 plan、段 3 レンズ A・B、段 4 裁定 (erratum 1〜3 を含む)、段 5 実装子報告、
段 6 レビュー A・B、段 6 fix 報告を置く。

**逐語 5 file (`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`、`s6-revA.md`、`s6-revB.md`) は行末空白だけを除去してある。**
codex の出力が Markdown の強制改行 (行末の空白 2 個) を含み、`git diff --check` が拒否するためである。
可視文字は変えていない。原本の sha256・byte 数と、除去した行番号・空白数を
`verbatim-whitespace-normalization.json` に記録した。記録どおり空白を戻すと、5 file すべてが原本と
byte 一致することを親が検算した。
