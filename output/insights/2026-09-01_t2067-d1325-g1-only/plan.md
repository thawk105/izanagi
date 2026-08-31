## 現状の実測

**Q1. 「戻さない」の成立範囲**

- 選択規則本体は `orchestrator/campaign/s8b_holdout_freeze.py:1928-1963` の `_assert_floor_selection_identity`。
- earlier run の集合は、Git 履歴や台帳ではなく、現在存在する namespace を `os.listdir(namespace_fd)` で列挙して作る (`1813-1823`)。親 brief の変更面アンカー `:1792` は誤りで、実際の列挙は `:1821`。
- path が selected より早い run だけを対象にし (`1827-1837`)、`result.json` が無ければ読み飛ばす (`1842-1847`)。削除済み run の復元、削除検知、履歴からの再構成はこの call graph に無い。
- present な earlier result は適格性を再導出し (`1849-1859`)、真なら selected と同じ集合へ入れ (`1948-1954`)、最小 run-id との一致を要求する (`1957-1963`)。
- production 呼出しは g1 candidate の `build_v2_g1_candidate` (`2014-2017`, `2050-2056`) と current launch (`s8b_ratified_freeze.py:3303-3309`) の2箇所だけ。

したがって「戻さない」と主張できるのは、**この2経路が検査時点で存在する namespace だけを選択集合とし、削除済み run を自動復元しない**という範囲である。全履歴の最早 run を証明するものではない。外部の人間や別処理が run を再配置すれば、それは present run として再び列挙される。また、静的 loader と historical reverify は選択規則を課さないため、この主張の対象外である。

**Q2. 「g1 のみ」の成立箇所**

- candidate: `s8b_holdout_freeze.py:2014-2017` が g1 専用 builder を名乗り、`2053-2056` で選択 identity を検査し、`2084` で `generation_number: 1` を固定する。
- 投影 equality: `s8b_ratified_freeze.py:1054-1085` は `resolution.generation_number == 1` のときだけ `generation.floor` と `floor_source` の投影を比較する。g2 以降には投影 equality を課さない。
- full validation: `_launch_validate` は共通 core の入口 `3073-3110`、特に `3107-3110` で generation 1 以外を artifact I/O より先に拒否する。この gate は current `launch_validate` (`3548-3555`) と historical `reverify_published_freeze` (`3558-3568`) の双方を支配する。
- current selection: `3303-3309` の呼出し自体には局所 generation 条件がないが、必ず `3107-3110` の後に到達する。したがって、公開 loader から来る production 経路で g2 に g1 規則が適用されることはない。
- historical reverify は `result_type is LaunchValidatedFreeze` 条件 (`3303`) を満たさず、選択 identity を呼ばない。これは D1312 と一致する。
- `_assert_floor_selection_identity` 自身 (`s8b_holdout_freeze.py:1928-1931`) は generation 引数も検査も持たない。よって helper 単体を「g1 限定」とは呼べず、g1 性は呼出し側で成立する。
- `load_ratified_freeze` (`s8b_ratified_freeze.py:1399-1418`) は一般の active generation を静的 load できる。g2では選択も投影 equality も行わない。これは D1312 の loader 配置であり、D1325 違反ではない。
- load-only の例として `s8c_result_judge.py:2033-2060,2103-2159` は generation を確認せず path/hash を消費する。これは D1313 で残された3件のうち「load-only consumer への選択強制」であり、本 wave では変更しない。

親実測3は、**「呼出し式に局所 generation 条件がない」までは正しいが、「g2 が実在すれば g1 規則が適用される」という到達可能性の結論は誤り**である。公開経路では `s8b_ratified_freeze.py:3107-3110` が先に止める。任意 Python による `RatifiedFreeze` の直接偽造は `:747-754` が明示的に保証対象外としている。

## plan

**Q3. docs のみで閉じる。実装面変更、テスト追加、既存期待値変更は不要。**

新規ファイルだけを作る。

`docs/spool/worklog/2026-09-01-dev-wave-t2067-d1325-g1-only-1.md`

- `:1-8` — spool frontmatter。`ledger: worklog`、`wave: dev-wave-t2067-d1325-g1-only`、`seq: 1`、T-2067 を題に含める。
- `:10-24` — 本文。
  - D1325 が5残余中の設計択一2件を「復元 authority は設けない」「選択・投影の追加保証は g1 限定」と固定したこと。
  - 「戻さない」は present namespace のみを検査する現状を採用したのであり、削除済み run の不存在を証明しないこと。
  - candidate、投影 equality、launch generation gate の実測行。
  - 親実測3を訂正し、到達可能な g2 への選択規則伝播はないこと。
  - D1241/D1313 の advisory/non-certifying 上限と規律2は一切変わらないこと。
  - 実装面差分、テスト差分、受理集合変更がゼロであること。
- `:26-34` — `## 次の一手差分` の `### 更新`。
  - `[T-2067]` を「実装待ち」から「一部完了」に更新。
  - 設計択一2件は D1325 で終端したが、残る3件は load-only consumer、起動証明書の実時間性、s8c production final claim 配線と明記する。
  - `base:` は local main で再取得する。現在の静的取得値は `6b4101114ea9738f65495272d831218245be50a2f33578575faf13c014e682b6`。

受理集合、成果物、参照の3軸では次のとおり。

- **受理集合:** candidate の present-earlier 判定、g1投影、generation 1限定 full validation、load-only/historical の既存境界を一切変えない。
- **成果物の値:** `generation_number: 1`、`floor`、`floor_source` path/hash、generator hashを変えない。特に `s8b_holdout_freeze.py:2062-2064,2077` は同ファイルの hash を candidate に入れるため、無用なコード/docstring編集も避ける。
- **参照:** active chain、floor source、approval、選択 identity の参照辺を変えず、worklog から既存 D1325、D1313を参照するだけとする。

書いてよい文と言ってはいけない文は以下。

| 書いてよい | 書いてはいけない |
|---|---|
| 「現行検査は現在存在する namespace を対象とし、削除済み earlier run を復元も証明もしない。D1325 は復元 authority を追加しないと裁定した」 | 「削除攻撃を閉じ、履歴上の最早 run を証明した」 |
| 「選択強制と投影 equality の追加保証は g1 の範囲に限る」 | 「g2 は拒否する」「g2 にも g1 規則を適用する」 |
| 「D1241/D1313 の advisory/non-certifying 上限は維持され、追加主張は (a)(b)(c) に限る」 | 「選択規則が完成したので certified claim が可能になった」 |
| 「設計択一2件は閉じたが、残余3件は継続する」 | 「床値選択の残余をすべて解消した」「T-2067 完了」 |

変更後は `tools/check_docs.py` と `tools/spool_fold.py --dry-run --show-diff` の静的検査だけを行う。この段では pytest を実走せず、緑とも報告しない。4つの別 wave 所有 file、コード、テスト、decisions ledger は変更対象にしない。

## 親 brief への異議

- **(P1-1): 結論は正しいが理由が過大。** docs-only で足りる。ただし「コード変更は成果物の値を変えない」という一般化は誤りで、`s8b_holdout_freeze.py` の変更は `:2062-2064,2077` を通じて future candidate の `generator.sha256` を変えうる。正しい理由は「現行の到達可能な受理集合がすでに D1325 と一致し、追加実装が不要」である。
- **(P1-2): 誤り。** 親実測3がいう reachable な選択・投影非対称はない。`s8b_ratified_freeze.py:3107-3110` が g2 を `:3305` より先に拒否する。これを新しい次の一手へ残してはいけない。
- **(P1-3): 正しい。** D1313の (a)(b)(c) を超える主張は不可。
- **実測1:** 結論は正しいが成立範囲を production の2呼出しと present namespace に限定すべき。変更面アンカー `s8b_holdout_freeze.py:1792` は誤りで、列挙行は `:1821`。
- **実測2:** 投影 equality について正しい。ただし「g2は黙って非検査」は静的 loader の投影についてのみで、full validation は `:3107-3110` で先に拒否する。
- **実測3:** 上記のとおり、構文上の観測は正しいが到達可能性の一般化が誤り。
- **実測4:** 異議なし。本 plan の変更対象は新規 worklog fragment 1本だけで、別 wave 所有4 file と交差しない。

**Q5. 既裁定との抵触・順序**

- D1312により、選択を loader や historical reverifyへ追加してはならない。
- D1241/D1313により、「戻さない」は削除残余の解消でも上限解除でもない。
- D1325は選択・投影のg1限定を裁定したのであり、既存の一般世代 ratification machinery を撤去・変更する根拠ではない。そこを触ると既存受理集合を変え、g2を新たに定義してしまう。
- T-2067は残余3件があるため `完了` ではなく `更新` とする。
- 実装面を加える場合は D95により段5の Codex authorが必要だが、本 plan では起動不要。

## 残る不確実性

- 検査は静的のみで、pytestや acceptanceは実走していない。
- 「復元機構なし」は選択 helper とその production call graph の範囲であり、repo外のバックアップ、人手、任意 Pythonによる再配置までは統制しない。
- 実在する production g2 はない。一方、既存コードと合成 fixtureには一般世代の静的 loadがあるため、worklogではそれをD1325による将来仕様として記述しない。
- spool の `base:` digest は並行 land で変わりうるため、親が local main に対して再取得する必要がある。

## 総括

docs-only を採用し、実装子は起動しない。  
「戻さない」は present namespace のみを見る現状の選択集合として成立するが、削除済み run の不存在証明ではない。  
「g1 のみ」は candidate、投影 equality、full-validation の先行 generation gate で成立している。  
親実測3の「g2へg1選択規則が伝播する」は、先行 gate を落とした誤判定である。  
親が段4で裁定すべき択一は、docs-only の採用と、誤った非対称を次の一手へ残さないことの2点。  
worklogはT-2067を一部完了へ更新し、D1313の上限と残余3件を明記する。