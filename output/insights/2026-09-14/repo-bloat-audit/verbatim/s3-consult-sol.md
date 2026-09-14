## 総括

**参照基準の誤りは real。plan の「削除候補0件」は、静的検査では1テスト・124 bytesへ覆す。**
対象は同一モジュール・同一入力・同一述語の完全重複であり、片方を残せば検査は維持される。
ただし、全 consumer の動的検証まで済んだ「削除確定」とは区別する。実際の削除は0件。
記録については、新たに削除可能と確定したものは0件。大きな重複群には具体的な pin があった。
P1-b の「テストについては概ね真」は支持しない。実物に基づく plan の留保が妥当である。

以下の相対パスはすべて指定された repo root 配下。

## 1. 参照基準の誤り (real / refuted)

**real。文字列として参照されることと、その対象を現位置・現内容で保持する必要があることは別である。**

D1941 の逐語は「歴史的な名前の観測だけを現役pinと同一視しない」。ただし、これは歴史的証拠そのものの削除許可ではない。

置き換える基準は次のとおり。

| 分類 | 判定方法 | 削除への意味 |
|---|---|---|
| 現役の拘束的 consumer | 実行コードが対象を読む、manifest が path/hash を要求する、現行 docs が対象内容を根拠として必要とする | 削除による破損・値の変化を解消できなければ不可 |
| 非拘束の参照 | 現行コードが名前を保持するが、対象の実在を要求せず、対象を消しても残存対象の処理が変わらない | 名前の存在だけでは阻却しない |
| 歴史的言及 | 過去の commit・試験実行・分類結果を記録し、現在の対象実在を要求しない | 言及された現行テストの存続理由にはならない。記録自体は保存する |
| 未解決 | key→path、glob、hash、動的ロードなどの関係が未確認 | 「pinあり」「削除可能」のどちらにも断定しない |

plan の保留候補を再判定すると、**削除可能側へ移るのは1テスト・124 bytes**。

- 削除候補：`orchestrator/tests/test_related_work_search.py::test_postprocessing_tier_api_remains_outside_executor_scope`
- 定義：[test_related_work_search.py:1978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-repo-bloat-cleanup/orchestrator/tests/test_related_work_search.py:1978)
- 残す検査：同ファイル:1581、`test_tier_enforcement_remains_outside_registration_executor_scope`
- 両者とも引数・decorator なし。同じ:19の `search` import に対する `assert not hasattr(search, "validate_tier_analysis")` のみ。モジュール内の autouse・setup/teardown 定義も検索では見つからなかった。
- 削除する定義・本体2行は実際に124 bytes。API再導入を検出する述語は残る。

他の候補は移らない。note 2件は単なる名前の残骸ではなく、取得本文の同定・分類根拠・逐語引用を含む。内容の包含・代替性は未証明。`debug_early.sh` も撤回・完全代替を示す外部根拠がなく、hostname stdout は実測記録である。

## 2. 台帳への nodeid 掲載は削除阻却事由か

**掲載だけでは阻却事由にならない。ただし台帳の行だけを消すのは不適切。**

[conftest.py:1502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-repo-bloat-cleanup/orchestrator/tests/conftest.py:1502) の validator は、`nodeid_count == len(durations)` を要求する。

| 操作 | 静的に確認した帰結 |
|---|---|
| 台帳の行だけ削除、件数は据え置き | validator は例外ではなく `{}` を返す。一方、`test_update_acceptance_duration_ledger.py:306` の実台帳検査は件数不一致で失敗する |
| 行と件数を整合させる | 当該 validator の条件は満たせる。任意の nodeid の実在確認はしていない |
| テストだけ削除、台帳は保存 | 残存行は過去の所要記録として残る。`conftest.py:1659–1674` は収集された item から duration を引くため、その残存行から削除済みテストを呼び出すことはない |

台帳には別 suite の集合を固定する検査もあるが、確認した固定対象は今回の related-work 2 nodeid ではない。**今回、台帳の編集を削除の前提にする必要は見つからなかった。**

過去の変異台帳についても、nodeid の掲載は現行テストの保持義務ではない。

- `mutprobe-ledger.json` は過去の `repo_head=a112c736…`、collection hash、実行結果を記録する。
- `mutreal-ledger.json`／`mutreal2-ledger.json` も過去の `repo_head=ae994c8d…` に束縛される。
- repo 内の Python・shell ソースを、当該ディレクトリ名・台帳名・2テスト名で検索した範囲では、これらの台帳から当該 nodeid を現在実行する reader は見つからなかった。
- 別途現存する mutation spec の `expected_nodes` は他の検査を指定しており、この重複2件への直接参照は見つからなかった。

これは「変異台帳を消せる」という結論ではない。**過去の試験記録を保存したまま、現行の重複テストを整理できる**という区別である。

## 3. AST 一致 23 群の検分結果

独自の「`orchestrator/tests/test*.py`、docstringを除く本体AST一致」抽出では**22群**を再現した。plan の23群との1群差は未解決。以下は plan が詳査した組以外の**10群**を、定義・入力・import・呼出先まで開いた結果である。パスは `orchestrator/tests/` 配下。

| 群・file:line | 判定と理由 |
|---|---|
| `test_s1_measurement_freeze.py:286` ↔ `test_s1_verify_extime_calibration.py:243` | **非重複**。`M` はそれぞれ `s1_measurement_freeze` と `s1_verify_extime_calibration`。別ソースの禁止importを検査する |
| `test_b10_extended_figure_provenance.py:891` ↔ `test_plot_b10_extended_backoff.py:354` | **非重複**。前者の `_pinned_measurement_paths()` は `HASHES` を読み、後者は provenance JSON の `external_inputs` を読む |
| `test_paper_story_a1_headline_sizing.py:2074` ↔ `test_paper_story_a1_headline.py:1366` | **非重複**。それぞれのモジュールに属する `EXPECTED_SELF_TEST_NAMES`・`_validate_self_test_selection`・`_run` を検査する。別の実行入口 |
| `test_t1434_t1222_science_slice.py:452` ↔ `test_t189_oracle_wiring_slice.py:154` | **非重複**。欠落時のskip検査だが、前者は science artifact の review/evidence、後者は oracle slice の task provenance から必要pathを構成する |
| 同上`:468` ↔ 同上`:170` | **非重複**。完全入力時の非skip検査。同様に入力集合とローカルguardが異なる |
| `test_s8b_oracle_driver.py:617` ↔ `test_real_repo_serialization.py:882` | **非重複**。前者の `_t080_output_snapshot` は共通 helper に委譲。後者はローカルの走査実装。別実装の一時作成・削除検出を検査する |
| `test_env_contract.py:161` ↔ `:167` | **非重複**。同じ `ec`／helperでも、非正整数 `[0,-1,-1800]` と型違反 `[1800.0,"1800",True,False]` は異なる入力 |
| `test_p3_b4_analysis_prereg_consumer.py:129` ↔ `:138` | **非重複**。同じ parser に渡す変異対象が、analysis invalid reason 12種と registry violation reason 5種で異なる |
| `test_s8a_trigger_sweep.py:86` ↔ `test_s6_sort_sweep.py:79` | **非重複**。`W.run_sweep` の `W` が別モジュール。別の実行経路でpreflightの順序を検査する |
| `test_s8a_trigger_sweep.py:387` ↔ `test_s6_sort_sweep.py:297` | **非重複**。同じ動作点を要求するが、別々の `W.perf_for` の退行を検出する |

真の完全重複と確認した nodeid は§1の1組のみ。**AST本体一致は、削除数ではなく調査入口として扱うべきである。**

## 4. plan が見ていない削除候補の型

**大きな同一 blob 群**

単に `frozen` という名前を理由に除外せず、次を確認した。

| 重複群 | 同一blobの規模 | 現物の拘束 |
|---|---:|---|
| `output/s6-rounds/frozen/payloads/main-00.json`〜`main-19.json` | 20本×63,795 bytes。1本残す場合の重複分1,212,105 bytes | `hash_ledger.json` のslot別hash。`s6_proposal_rounds.py:244` が全round・全armのpathを構成して読み、hash照合 |
| 同ディレクトリの `c5-00.json`〜`c5-19.json` | 20本×61,055 bytes。重複分1,160,045 bytes | 同じreader。`:361` の実行入口はverifyを先に呼び、`:375` でslotのpayloadを読む |
| 同ディレクトリの `c4-{05,06,07,08,11,16}.json` | 6本×63,849 bytes。重複分319,245 bytes | 同じslot→path→hashの拘束 |
| axis1 retake の下記5組 | 各組はpass1/pass2の2本 | bundle manifest が両方のpathとhashを個別に記録。page側にも各passの `occurrence_ledger_path` がある |

axis1 の共通ディレクトリは  
`output/insights/2026-08-29_t2033-axis1-retake/bundle/ledgers/`。

両pathは以下の `{pass1,pass2}` をそれぞれ展開したもの。

- `AX1-20260829-E1-Q6-SM202606@arxiv.{pass1,pass2}.52dae690ca1a.json`：各297,161 bytes
- `AX1-20260829-E1-Q6-SM202603@arxiv.{pass1,pass2}.4b8e1d353281.json`：各267,620 bytes
- `AX1-20260829-E1-Q6-SM202602@arxiv.{pass1,pass2}.a63f8e12637a.json`：各257,012 bytes
- `AX1-20260829-E1-Q6-SM202604@arxiv.{pass1,pass2}.eb9f69f7e4ca.json`：各256,489 bytes
- `AX1-20260829-E1-Q6-SM202607@arxiv.{pass1,pass2}.304bb0dd0bc6.json`：各254,036 bytes

例えばmanifest:3058・3083がSM202606の両pathを固定する。**この調査から「両pathとも非pin」の組は得られなかった。**

**再生成可能な派生物**

`tools/plotting/plot_t2187_adaptive_consts.py` と対応するPNG/PDF/provenanceを開いた。生成器は現存するが、provenanceの入力はrepo外の `izanagi-job-evidence/.../results/`。指定root内で入力の現存まで閉じられず、削除候補にしない。

`plot_s1_9pair.py` も現存するが、admission済みWALと凍結reportを照合する構造である。生成器の存在だけでは、必要入力の完全性・出力の代替可能性を証明できない。今回、指定条件を満たす非凍結派生物の削除候補は確定できなかった。

**0 byte・残骸**

tracked blobの棚卸しでは0 byteが**2,838件**あった。ただし、0 byteは不要性の証拠にならない。

- `orchestrator/tests/fixtures/paper_story_a1/qstat-f-absent-900001.stderr` は `test_paper_story_a1_job_contract.py:1250` が実際に読むfixture。
- `output/registry/t139-publication-reservations.jsonl` は `orchestrator/publication/ledger.py:31` が束縛する台帳。
- 多数の空stderrは実行記録に属する。失敗した生成物の残骸と一括認定できない。
- `.tmp`・`.pyc`・`.gitkeep`・`.keep` の追加検索では、`output/insights` 内に採用可能な候補は得られなかった。Gitは空directory自体を追跡しない。

## 5. (P1-b) への判定

**P1-bは根拠不足。plan の「概ね真を支持しない」が妥当。**

8月24日以降の追加履歴で新設を確認し、実際に開いた例：

- `test_related_work_search.py`：送信間隔と状態永続化（:789）、証拠body改変の拒否（:1965付近）。過去の変異台帳にも間隔をゼロへ変更した際の失敗が記録されている。
- `test_p3_b4_analysis_prereg_consumer.py`：事前登録のliteral変更、status、tie規則、`A_min=0.60→0.61` の改変拒否（:129、:138、:146）。
- `test_paper_story_a1_headline_sizing.py`：生成器と別verifierを使う構成、およびテスト集合の空・不足・余分・重複を拒否する自己実行入口（:2074）。

これらは具体的な契約逸脱を検査している。重複124 bytesは見つかったが、**+265,519行の大半が不要だと一般化する材料にはならない。** 逆に、増分全体が必要だと証明したわけでもない。

## 6. 確かめられなかったこと

- 全ファイルのkey・hash・glob・動的consumerを含む完全なpin閉包。とくに任意pathを引数で受ける汎用readerの全呼出経路。
- 重複1テストを削除した後の実collection・受入・変異試験。**静的削除候補1件と、実測済み削除確定を区別する。**
- AST一致23群と今回再現した22群の差、残り全群の意味論的検分。
- 同一blob重複全6,761件、0 byte全2,838件の個別判定。
- 非凍結派生物の生成器・全入力・非pinを同時に満たす候補。
- note 2件の内容が他資料へ完全包含されるか。

射影4ファイルはすべて読めた。編集・commit・Git状態変更・pytest実行は行っていない。

追加棚卸しの2コマンドは `guard_bash` が不透明構文との組合せを分類不能として拒否した。拒否された追加検査は完了扱いにしていない。