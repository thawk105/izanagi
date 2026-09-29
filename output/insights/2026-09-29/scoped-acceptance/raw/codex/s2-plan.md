## 分類器

新規 `tools/scoped_acceptance.py` に `changed_entries(repo, tested_main, tested_tip)`、`classify(entries)`、`select_tests(...)` を置く。判定範囲は **`tested_main..tested_tip` の tree 差分**とし、merge-base を暗黙に使わない。受入時に固定した二つの SHA を land が再使用する。差分は `git diff-tree --no-commit-id -r -z --raw --no-renames --no-ext-diff --no-textconv <tested_main> <tested_tip>` の raw record とし、旧新 mode・object type・path を検査する。rename は削除と追加として扱う。非 UTF-8 path、空差分、parser が解釈できない record、gitlink、symlink、mode 変更、type 変更、削除は全受入へ倒す。これなら rename、属性変更、実行権変更で allowlist 判定をすり抜けない。

初版の縮小許可は、通常の regular blob の**追加・内容変更**に限り、次の閉集合にする。

| 許可 path | 条件と根拠 |
|---|---|
| `docs/**/*.md` | 知識文書。ただし下記の除外と production reader 検査を通ったものだけ |
| `output/insights/**/*.md`, `*.txt`, `*.csv`, `*.tsv`, `*.json`, `*.jsonl` | 研究記録のテキスト成果物。形式を追加するときは別裁定 |
| `docs/spool/{worklog,decisions,failures}/**/*.md` | land が fold する fragment のみ。`docs/spool/README.md` の正本・`FOLDED.md`・その他の制御 file は含めない |

`svg/png/pdf` は初版から外す。SVG の active content、画像・PDF を解析する test、バイナリ内容の検査範囲が未確定だからである。`output/insights/**` も拡張子だけでは十分でなく、後述の reader 検査で gate 入力なら除外する。

除外は閉じた prefix／exact 集合として、新 module に定義する。`docs/dev-wave/**`、`docs/spool/README.md`、`docs/spool/FOLDED.md`、`docs/{worklog,decisions,failures}.md`、`docs/archive/**`、`docs/skill-self-improvement.md`、事前登録・erratum・freeze の登録済み docs、production が読む doc、`output/insights/**` 内の gate 入力を除く。さらに `.gitattributes`、`.gitmodules`、`AGENTS.md`、`CLAUDE.md`、`.claude/**`、`.agents/**`、`.github/**`、`.codex/**`、`orchestrator/**`、`tools/**`、`hooks/**`、`patches/**`、`external/**`、`output/**` の insights 以外は許可集合の外である。検査器、trace、受領証、事前登録、凍結、proof chain、開発手順の正本を全受入に固定するためである。

D95 決定 2 の実装面判定は [check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/check_ai_provenance.py:1593) の `_is_implementation_path` に既存実装がある。ただしこれは `patches/` を実装面から外すなど、**縮小受入の安全な許可判定そのものではない**。まずこの関数で実装面なら拒否し、さらに上記の狭い許可集合を適用する。長期的な規則共有は scope 外候補とする。

(P2) は `orchestrator/`・`tools/`・`hooks/` の非 test source を全走査し、Python は AST の文字列定数、その他は字句上の引用文字列から、repo 相対 path の完全一致、既知の `Path(...) / ...` 定数連結、basename 参照を拾う。変更 path と一致する literal、またはその親 directory を列挙する reader があれば全受入へ倒す。動的連結、glob、設定値経由、subprocess 内の reader は静的走査の偽陰性になる。**到達範囲を決められない reader が許可 prefix を読む場合、その prefix 全体を除外する**。初回 inventory と例外の確認は半日～1日、以後の分類は source 数に比例する秒単位を見込む。P2 の「literal を数えれば完全」は成立しないため、この保守的な境界が必須である。

## 縮小集合

`select_tests` は [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/conftest.py:262) の `_REAL_REPO_NODE_INVENTORY` を基底にする。約148 node／22 file の inventory は file 全体ではなく、収集後の exact nodeid に展開する。parametrize suffix と loadgroup suffix の正規化を collection 側の既存規則に合わせ、未解決・重複・収集差は受領証を作らず全受入へ戻す。[growth_test_holds.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/growth_test_holds.py:580) の `docs_bytes` 3 node は現行の hold を維持し、新しい hold は加えない。

変更 path を参照する test は、test source の文字列定数に対して **full path と basename** を照合し、該当したら test **file 全体**を選ぶ。親 directory 名だけの一致は過大選択が大きいので、directory の literal が `glob/rglob/iterdir` 等の引数なら、その配下の変更を選ぶ。変数連結・fixture・import 先の reader は偽陰性、同名 basename と説明文の引用は過大選択となる。検出不能な glob reader が許可 prefix を扱う場合は、分類側でその prefix を除外する。

固定 file 集合は `test_check_docs.py`、`test_spool_fold.py`、`test_check_ai_provenance.py`、`test_real_repo_serialization.py`、`test_acceptance_schedule_order.py`、`test_campaign.py`、`test_official_perf_closure.py`、`test_p3_exploration_namespace.py`、`test_p3_b4_wiring_probe.py` とする。後四者は [DW-O26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/docs/dev-wave/operations.md:193) の inventory 4 群である。file 全体を選ぶと重くなる `test_campaign.py` 等は、固定 nodeid を明示して収集時に展開する。この集合は docs checker・spool fold・provenance・実 repo 排他と inventory の既知の門を覆う。ただし未知の動的 reader まで証明しないので、分類の保守的除外が対になる。

直接実行は exact argv の `python3 tools/check_docs.py`、`python3 tools/spool_fold.py --dry-run`、`python3 tools/check_ai_provenance.py`。各 command の argv、実行 source blob、正規化した rc=0、stdout/stderr log の SHA-256 を launcher が受領証に束縛する。`spool_fold --dry-run` は canonical bytes を変更せず plan を出すが、base digest 不一致を検出する必要がある（[docs/spool/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/docs/spool/README.md:73)）。provenance は全履歴監査であり、login 完結を保証しない。

## 実行経路

`tools/dev_wave_wait.py acceptance --scoped ... -- python3 tools/run_tests.py <選択 target...>` を追加し、既存の flag 無し経路をそのまま残す。`--scoped` では専用の `tools/scoped_acceptance_launcher.py` を起動する。[acceptance_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/acceptance_launcher.py:21) の `_EXACT_RUNNER_ARGV` と v5 生成関数は変更しない。待ち手の claim 後 merge、clean fingerprint、log 捕獲、atomic publish は共通にし、mode 分岐は受入 command の検査と launcher 選択に限定する（[dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_wave_wait.py:3739)、同:1660）。

選択を `run_tests.py` に渡すのは positional nodeid／file path の列とする。`-k` 等の選択 option は使わない。現行 `_is_acceptance_run` は `::` と標準 test directory 以外を拒否する（[run_tests.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/run_tests.py:692)）。したがって縮小走行を v5 の「受入形」と偽装しない。新たな閉じた scoped 形を認識させ、恒久除外表の検査、非 loadgroup 拒否、事前 gate、binding report を同等に適用する。選択 node が恒久除外に当たれば黙って消さず、既存の裁定済み除外と一致することを確認して記録する。`_positional_tokens` と `_test_operation` は選択列を digest 化できる（同:616、:672）。明示 shard は現行の空 argv 制約を保ち、scoped には初版で使わない。

login admission は現行 [run_tests.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/run_tests.py:2495) を利用する。headroom が足りれば bounded local、足りず queue が動けば dispatch、双方不可なら拒否する。縮小集合が login で完結することは目標であって受理条件ではない。

## 受領証と land

新 schema は `dev-wave-scoped-acceptance-receipt/v1` とし、v5 と異なる exact field 集合を持つ。共通 field は `acceptance_wave`、`lease_holder`、`tested_main`、`tested_tip`、`pre_fingerprint`、`post_fingerprint`、`env_projection`、`child_rc`、`verdict=child-green`、`effective_scheduler`、`log_sha256`、待ち手・launcher・runner の blob ID と実行 bytes digest。固有 field は `classification=knowledge-only`、分類規則版、変更 entry の canonical 列 digest、選択規則版、選択 nodeid／file の canonical 列 digest、分類器・選択器の Git blob ID と実行 bytes digest、三つの直接実行の exact argv・source blob・rc・log digest とする。配列そのものも受領証に入れ、digest と長さを再計算する。wave、tip、main の SHA が違う受領証は再利用できない。

[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_wave_land.py:811) の `_receipt_object` は schema を先に識別し、**既存 v5 の exact field 検査と `_verify_acceptance_static` を一行も緩めず**、別関数 `_verify_scoped_static` へ分岐する。lock 前の登録検査（同:5637）と lock 内の再検査（同:5800、:6140）の両方に同じ分岐を通す。lock 内では固定 SHA の diff を読み直して分類・選択を再導出し、受領証の列と digest、blob と rc を照合する。実装面1 file、分類器差、選択集合差、v5／scoped の field 混用は拒否する。再導出時に使う module は **tested main の固定 Git blob** とし、実行時に使った bytes と照合する。tip 側の module が勝手に選択を狭めても通さない。

forward-main merge 時、v5 は [同:887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_wave_land.py:887) の D987 runner blob 比較を維持する。scoped では最後に取り込んだ main と tested main の **runner、分類器、選択器、scoped launcher、直接実行三本の blob** を比較し、いずれか違えば再受入を要求する。選択対象 test・conftest・pytest 設定の main 差も集合または意味を変え得るため、初版はその変更を検知したら再受入へ倒す。これを除くと「選択器の blob は同じだが収集集合が違う」抜け道が残る。

## test と正例・負例

新規 `orchestrator/tests/test_scoped_acceptance.py` に、少なくとも次の node を置く。純粋分類・選択 10～14 件、合成 repo の launcher／land 8～12 件で、実装と fixture 作成を含め約2～3日を見込む。

- `test_docs_tip_scoped_receipt_lands`：合成 repo の許可 doc 追加、緑の縮小受領証、land 成功。
- `test_one_implementation_file_rejects_scoped_receipt`：同 tip に `tools/*.py` を1 file 混ぜ、lock 内で拒否。
- `test_gate_doc_is_full_acceptance_only`：事前登録・freeze・production reader doc を除外。
- `test_pin_change_makes_scoped_run_red`：**合成 repo 内で許可 doc に pin を設けた場合**、選択 test の赤を確認。
- `test_raw_diff_rejects_rename_symlink_gitlink_mode_delete_non_utf8`：各 metadata の fail-closed。
- `test_selection_covers_inventory_literal_and_fixed_nodes`、`test_selection_rejects_unresolved_collected_node`。
- `test_receipt_rejects_other_wave_tip_main_and_v5_fields`、`test_receipt_rejects_selector_blob_or_set_drift`。
- `test_forward_main_rejects_scoped_runner_selector_or_test_collection_drift`。
- `test_direct_gate_nonzero_or_log_swap_never_publishes`。

変異は「除外1件削除」→ gate doc test、「land の再導出削除」→ 実装1 file test、「固定 test 集合削除」→ selection test、「直接実行の rc 検査削除」→ direct gate test、「forward-main 比較削除」→ drift test が殺す。

親の実物確認では、(a) 許可された docs／insight／fragment だけの独立 wave を縮小受入・land、(b) 別の合成 tip に `tools/*.py` を加えた受領証を land へ渡して rc 拒否、(c) 許可 doc を読む実 repo test の既知の期待値を壊して縮小受入を赤にする。**現行の exact pin された節は原則として許可集合から除外するので、(c) の「allowlist 内の pin 節改変」はそのままでは両立しない。** 実物の (c) は許可 doc に対する実 repo reader の期待値破壊で行い、pin 節の例は合成 repo に限定するか、親に完了判定の修正裁定を求める。本 wave 自身は従来の全受入で land する。

## 手順書

[DW-S04](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/docs/dev-wave/core.md:90) の文案：

> 免除は「実装しない」裁定済みかつ実装差分ゼロの wave の変異 matrix だけ。受入については、機械分類で知識面の許可集合に閉じ、縮小受入の受領証が land の協調 lock 内で再検証された wave に限り、受入全走の免除を認める。それ以外の wave に受入全走の免除はない。実 repo を読む test と文書・台帳・履歴の検査結果は、選択した受入の記録とともに worklog へ残す。

D237/D301 に従い、変異 matrix の免除条件は連言で明記し、受入免除も限定された**免除の否定**として書く。`DW-O23` の D987 文は scoped の追加比較を追記し、`DW-O27` には scoped の起動例と別 schema を短く参照する。[runbook §7.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/docs/pegasus-runbook.md:889) には `--scoped` の exact command、適格性、三つの直接 gate、login／dispatch、赤時は receipt 無し、v5 との分離、forward-main 時の再受入条件を追記する。

[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/check_docs.py:558) の `SECTION_LITERAL`／[EXACT 定義](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/check_docs.py:654) には `DW-S04`、`DW-O23`、`DW-O27`、runbook §7.3 の exact section は載っていない。ただし `DW-O23` は参照位置・順序 pin がある（同:6145、:6367）。見出しと配置を維持する。L1 上限は **10,625 bytes**（同:361）。現行残量を静的資料だけから確定できていないため、改訂前後の L1 実 byte を checker の分類規則で算出し、超過するなら同じ L1 内の重複説明を圧縮する。義務文を削って収容しない。詳細は L2 の runbook へ置く。

## 分割

A が `tools/scoped_acceptance.py` と `orchestrator/tests/test_scoped_acceptance_classifier.py` を所有する。分類、production reader inventory、選択集合、差分 metadata の test を先に固定する。

B が `tools/scoped_acceptance_launcher.py`、`tools/dev_wave_wait.py`、`tools/run_tests.py`、`tools/dev_wave_land.py`、`orchestrator/tests/test_scoped_acceptance_integration.py` を所有する。A の公開 API と canonical serialization を受けて実行・受領証・lock 内照合を実装する。親が `docs/dev-wave/core.md`、`docs/dev-wave/operations.md`、`docs/pegasus-runbook.md` と insight／fragment を所有する。所有 path は互いに素で、依存順は **A の契約固定 → B の実装 → 親の統合・手順書 → 全受入**とする。

## brief への攻撃

- **P1：`docs/**/*.md` と `output/insights/**` は広すぎる。** 事前登録・凍結・proof chain の入力、運用契約、production が読む insight が混入する。`.gitattributes` の変更、rename、symlink、gitlink、mode、削除、非 UTF-8 path は内容拡張子だけの判定を破る。tree metadata で拒否し、動的 reader の到達 prefix を除外する。
- **P2：literal 検索は完全性の証明にならない。** `glob`、path 連結、basename、設定値、subprocess、別 module を経由する reader が残る。検出不能な reader の到達 prefix は全受入にする。reader inventory の更新漏れを test と review の対象にする。
- **P3：固定 node だけでは不足し得る。** `conftest.py` の inventory 外の実 repo reader、glob reader、inventory 系 test、D237 の `check_docs`／spool 実 repo test を確認する。三つの `docs_bytes` hold は直接 gate で一部を補えるが、test 固有の検出力と同値とは主張しない。固定集合と直接 gate を双方要求する。
- **P4：digest だけでは偽造・再利用を防げない。** wave／main／tip、実行 source bytes、選択列、rc、log、fingerprint、lock 内再導出が一緒に必要。v5 の parser を緩めると種類の取り違えが起きる。別 schema の exact parser に隔離する。
- **P5：login 完結は保証できない。** 固定 file の大きさ、provenance 履歴監査、headroom により dispatch へ落ちる。queue 停止かつ headroom 不足なら「受入不能」で止める。
- **fold と main 前進：** fragment の dry-run が緑でも、他 wave の land 後に canonical 台帳・base digest が変わり得る。land の lock 内 fold gate は維持する。取り込んだ main が runner 以外の分類・選択・検査・収集面を変えた場合も、scoped receipt の再利用を拒否する。
- **完了判定の矛盾：** 「allowlist 内の exact pin 節を壊す」は、正しさの門を読む doc を全受入にする不変条件と衝突する。前節のとおり実物の負例を reader 期待値破壊へ修正する必要がある。

scope 外候補は、D95 判定器の共通 module 化、動的 reader の完全な依存解析、v5 受領証の改版、既存 hold の解除、テスト削除、画像・PDF の許可拡大である。

## 総括

実装可能な核は、**狭い path 許可、保守的 reader 除外、選択集合と三つの直接 gate、別 schema の受領証、land の lock 内再導出**である。現行 v5 は独立のまま維持する。未解決なのは、allowlist 内 pin 改変という負例の矛盾と、動的 reader の初回 inventory で許可集合がどこまで残るかである。今回は指定どおり静的調査のみで、テスト・実走・所要比較は行っていない。