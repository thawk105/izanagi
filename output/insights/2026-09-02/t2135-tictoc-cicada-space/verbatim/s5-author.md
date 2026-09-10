## 読んだ資料

指定された以下の 6 資料をすべて全文確認した。読めなかった path はなし。

- `s4-ruling.md`
- `s1-brief.md`
- `s3-parent-remeasure.md`
- `s2-plan.md`
- `s3-lens-a.md`
- `s3-lens-b.md`

## 実装した内容

- [genome.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2135-author/orchestrator/campaign/genome.py:74)

  - tictoc の両 no-wait が同時に 1 の場合だけ拒否する述語を追加。
  - cicada の promotion が inline optimization を必要とする述語を追加。
  - 5 軸・生 32・有効 24 の `TICTOC_SPACE` と `CICADA_SPACE` を追加。
  - `SPACES` を silo / mocc / tictoc / cicada の 4 protocol 登録へ更新。
  - 既存 `_no_wait_xor`、`SILO_SPACE`、`MOCC_SPACE` は変更していない。

- [test_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2135-author/orchestrator/tests/test_campaign.py:248)

  - 旧未登録 test だけを削除し、指定された 7 test に差し替えた。
  - 既存 silo / mocc の 3 test は変更していない。
  - notes test の docstring に、語句確認だけで C++ 側の事実は検証しない限界を記載した。

変更前は tictoc / cicada が `space_for()` で `KeyError`、変更後は裁定された各 24 genome を受理する。silo の XOR、mocc の全 8 genome、その他の未登録 protocol の拒否は不変であり、指示外の受理集合変更はない。

## notes に入れた事実の対応表

| 対象 | 裁定事項 | notes の記述 |
|---|---|---|
| tictoc | 死にフラグ | `PARTITION_TABLE` は protocol の `.cc/.hh`、workload source、共通 header の全件検索で live site がない |
| tictoc | 計測撹乱 | `SLEEP_READ_PHASE` は `transaction.cc:68-70` の計測撹乱ノブ |
| tictoc | 冗長組 | `(1,1)` は `#if` が選ばれて `#elif` が dead code となり、`(1,0)` と同一 |
| tictoc | silo XOR との差 | 外側 write-set loop、内側 spin loop、`transaction.cc:626` の lock word 再読込を明記 |
| tictoc | 限界 | 完走性・公平性・starvation は未実測で、静的導出であり実測ではない |
| tictoc | 範囲 | 24 は YCSB workload の数。bare define と導出不能候補はなし |
| cicada | `SINGLE_EXEC` | 多版から単版へ測定対象そのものを変えるため除外 |
| cicada | default の限界 | fresh configure では default 0。ただし既存の非標準 CMakeCache を戻す主張ではない |
| cicada | 死にフラグ | `PARTITION_TABLE` は print 専用で、README と現行コードが食い違う |
| cicada | 計測撹乱 | 3 件の delay option を名前付きで除外 |
| cicada | `WRITE_LATEST_ONLY` | 読み側の可視性は不変で、保守側に余分な abort を加える最適化軸 |
| cicada | promotion | `(0,1)` と `(0,0)` は CC / data path が同一。ただし起動時 option 表示は異なる |
| cicada | 範囲 | 24 は YCSB workload の静的導出。bare define と導出不能候補はなし |
| 共通 | cache option | CLI から個別指定できることと、全組合せが異なる挙動を持つことを区別し、後者を制約述語へ委ねた |

## test の一覧

| test | 検出内容 |
|---|---|
| `test_tictoc_and_cicada_are_registered` | 両 space の登録 identity |
| `test_tictoc_space_has_twenty_four_operable_ycsb_boolean_genomes` | axes 完全集合、値域、生 32、有効 24、canonical 一意性、protocol |
| `test_tictoc_space_excludes_redundant_double_no_wait_but_keeps_wait_pair` | pair を厳密に `{(0,0),(0,1),(1,0)}` と固定。制約削除なら `(1,1)` が混入し、silo XOR 誤用なら `(0,0)` が欠落する |
| `test_tictoc_space_excludes_dead_and_measurement_axes_and_names_ycsb_scope` | 除外軸と notes の裁定語句 |
| `test_cicada_space_has_twenty_four_operable_ycsb_boolean_genomes` | axes 完全集合、値域、生 32、有効 24、canonical 一意性、protocol |
| `test_cicada_space_requires_inline_opt_for_promotion` | pair を厳密に `{(0,0),(1,0),(1,1)}` と固定。制約削除なら `(0,1)` が混入する |
| `test_cicada_space_excludes_semantic_dead_and_measurement_axes_and_names_ycsb_scope` | 意味変更・死にフラグ・計測撹乱軸の除外と notes の裁定語句 |

pair test は raw Cartesian product に拒否対象が実在するため恒真ではない。

## 実走したもの・していないもの

実施した静的確認:

- 2 file の Python 構文解析: 成功
- 7 test 名の存在と旧 test 名の消滅: 確認済み
- 両 space の生 32、有効 24、canonical 一意性 24: 確認済み
- tictoc / cicada の pair 完全集合: 期待どおり
- notes の要求語句: 確認済み
- `git diff --check`: 指摘なし
- 結合文字 U+0300〜U+036F: なし
- 変更 file: 指定の 2 file のみ

pytest は未実走であり、実装済み・未実走。build、benchmark、測定も実行していない。

## 波及可能性の静的列挙

`SPACES` / `space_for` / `GenomeSpace` を全 Python source から検索した。

- production 側に `space_for` または `SPACES` の caller はなく、`GenomeSpace` の生成も `genome.py` 内だけ。
- `test_campaign.py` の既存 consumer は silo を明示指定する決定順序 test と fixture 用 canonical 取得であり、`SILO_SPACE` 不変のため影響なし。
- `s1_known_axes_freeze.py`、`test_guided.py`、source-digest test は `SILO_SPACE` を直接参照しており、登録辞書の拡張では列挙対象が増えない。
- `screening_driver.py` と `layer3_report.py` は同じ module の `protocol_from_floor_genome` だけを importする。この helper は未変更で、module import の静的確認も成功した。
- 共有 fixture が `SPACES` 全体を暗黙列挙する箇所は見つからなかった。
- 未登録 protocol の例外文に表示される登録済み一覧は、2 protocol から4 protocolへ増える。

## 実装できなかったもの

なし。裁定された実装項目はすべて反映した。pytest の未実走だけが残り、親による全走が必要。

## 総括

tictoc と cicada を、それぞれ生 32・有効 24 の YCSB genome 空間として登録した。
tictoc は両 1 のみ拒否し、silo XOR は転用していない。cicada は promotion の含意制約を適用した。
既存 silo / mocc の定義・test・受理集合は不変。変更は指定の 2 file のみで未 add・未 commit。
静的契約確認は完了し、pytest は未実走である。