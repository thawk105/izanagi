# [T-2421] A-2 consumer の policy 版選択 — dev-wave 2026-09-08

wave branch: `worktree-dev-wave-t2421-a2-policy-version`
実装 commit: `93f85297a`
起点 main: `cc9bba523ac7804aadb7891d686bf4c925789a3f`

## 何を直したか

A-2 の consumer は、成果物へ保存された当時の policy を**版選択なしで**現行 `load_policy` へ渡していた。
producer の文法が締まるたびに過去成果物が読めなくなり、先行 wave は
`(認証 bytes sha256, 埋め込み policy bytes sha256)` の組で 1 件だけを名指しする hash 束縛 adapter で
閉じていた (D1754、F884)。D1754 自身が「producer 共通 loader への一般的な版管理は本 wave の scope を
超える」と裁定パッケージへ返していた分が、この wave の本題である。

## 絶対規律 7 について — この成果物が主張しないこと

**過去成果物を読めるようにすることは、当時の測定を現行の正しさ主張へ昇格させることではない。**

歴史世代で読んだ Policy は、plot consumer の 1 経路からしか得られない。producer の認証・実行・
生成経路へは流れない。status、correctness、`source_binding_status` を再分類しない。
当時の測定は当時の policy で走り当時の検証を通っており、その事実は後から変わらない。
この wave が変えたのは**読み手だけ**である。

## 覆う次元と覆わない次元 (限界の明記)

版選択が覆うのは `trace0_cmake_argv.configure` の exact key 集合だけである。

| 次元 | 世代選択の対象か |
|---|---|
| `trace0_cmake_argv.configure` の exact key 集合 | **対象** |
| 同 key の値検査 (FetchContent prefix 4 本) | **対象** (key 存在時のみ適用) |
| `schema_version` (`POLICY_SCHEMA`) | 対象外 (全世代共有) |
| top-level key 集合 (`_TOP_LEVEL_KEYS`) | 対象外 (全世代共有) |
| `performance_common` などの各値制約 | 対象外 (全世代共有) |
| `_protocol_preimage` の構成 | 対象外 (全世代共有) |

**したがって「再発を無くした」わけではない。** 次の締め付けが対象外の次元に及べば、
世代を正しく選べても過去成果物は読めなくなる。世代ごとの完全な文法契約を作る案は、
発火条件を満たす既存成果物がまだ無いため DW-G04 に従って実装せず、裁定パッケージへ返している。

## 受理集合はどう動いたか

**広がっていない。狭まっている。**

先行 wave の手書き `_historical_policy_view` は schema・configure key 集合・protocol hash の
3 assert だけを当て、その後 `Policy` と `CellSpec` を手書きで再構成していた。つまり
`load_policy` 本体の約 150 行の検査 (top-level exact key、scheduler、durable base、
`tracked_destination`、`performance_common` の値制約、legacy correctness、workload/cell の
cardinality と exact shape、role pair、genome の型と値) を**歴史側では走らせていなかった**。

これを producer の完全な loader へ一本化したので、`_protocol_preimage` に含まれない
`tracked_destination` などの検査が歴史側にも効くようになった。
負例 `test_historical_rejects_unknown_content_with_the_same_six_keys` は、変更前は現行文法の
FetchContent key 欠落で赤くなっていたが、変更後は
`"tracked destination must be a bounded relative path"` で赤くなる。これが直接の証拠である。

先行 adapter が受理集合を緩めていたわけではない (entry の主 key が policy bytes を完全に固定する)。
欠陥は「緩い」ではなく**「再利用できない」**だった。

## 親が実測した検査

| 対象 | 結果 |
|---|---|
| `test_plot_a2_certification.py` (fix 後) | 79 passed |
| `test_paper_story_a2_certification.py` + `test_paper_story_a2_job_contract.py` | 247 passed |
| `test_campaign.py` + `test_official_perf_closure.py` + `test_ccbench_spawn_sites.py` + `test_hooks.py` | 938 passed / 4 skipped |
| `check_ai_provenance.py` 全史 | rc=0 |

焦点走の対象 file 集合は、変更した production module 名で `orchestrator/tests/` を grep して
参照関係から引いた (DW-O26)。

実装子と fix 子はいずれも sandbox から pytest を起動できず (`run_tests.py` は rc=16、
直接 pytest は hook 拒否)、「実装済み・未実走」と正直に申告した。実測はすべて親が行った。

## 段 1 brief の完了条件

「t2364 成果物を当時の文法の**全体**で読んで figure data を構成できること」。
測定 root `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b`
がこの機体に実在することを確かめ、`expected_hashes` override なしで `load_measurements` を
最後まで通す統合テストを入れた。期待値は凍結成果物から読む (cell 順・median_tps・効果値・
manifest の file 集合)。数値を test へ literal で焼き込んでいない。

## 子の逐語

`verbatim/` に全文を収める。段 2 plan 1 本、段 3 敵対相談 2 本、段 5 実装子 1 本、
段 6 レビュー 2 本、段 6 fix 1 本の計 7 本。すべて `check_codex_output.py` rc=0。

## 段 4 裁定の erratum

親は段 4 で「差分定義へ戻す変異は現時点では等価変異であり kill できない」と裁定した。
**これは誤りである。** 実装子は producer source の AST を検査して literal であることを構文レベルで
要求する形を採り、この変異は実際に KILLED になる。変異 M9 として登録し実測した。
初回の裁定は消さず `s4-erratum.md` に残している (DW-M02)。
