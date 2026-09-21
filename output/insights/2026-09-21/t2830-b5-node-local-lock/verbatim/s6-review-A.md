指定資料を読み、静的に照合しました。**実装の must-fix は見つかりません。変異の帰属には補正が必要です。** テスト・変異は実行していません。

以下の略記は各ファイルを指します。

- J = [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/p3_s4_loop_pegasus.sh)
- L = [b5_contrast_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b5_contrast_launch.py)
- TJ = [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_p3_s4_loop_job_contract.py)
- TL = [test_b5_contrast_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_b5_contrast_launch.py)
- R = [tools/pegasus/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/README.md)

## 1. プラン v2 との一致

**判定：refuted（逸脱なし）。**

統合差分の job body hunk は、J:661 の export **1行追加だけ**です。位置も `b5_rc=0` と driver 起動の間で、v2 A1 に一致します。

A1 の環境記録・外部 lock 除去・独立期待値は TJ:1301、1389、2031。戻り値3要素と既存 evidence 辞書比較は TJ:1397–1409 に維持されています。静的 pin の追加もありません。

A2 は L:224–226 で job ごとの tree を command に保持し、L:240 で cwd に使用。4必須引数と共通 HEAD による検証は L:248–249、263–268。禁止された validator 等の変更、互換層、path 重複検査は差分にありません。

## 2. lock path の期待値

**判定：refuted（規則不一致・観測値への依存なし）。**

- 実装：J:203 の `${PBS_JOBID//:/_}` → J:256–263 の scratch/TMPDIR。
- harness：TJ:1354 の `tmp_path/scratch-base`、TJ:1375 の固定 `0:945411.nqsv`。
- 期待値：TJ:2031 の `"0:945411.nqsv".replace(":", "_")`。

したがって期待値は `scratch-base/0_945411.nqsv/bench.lock`。観測した `TMPDIR` から lock の期待値を作っておらず、両フィールドを独立期待値と比較しています。

J:328 の `${PBS_JOBID#0:}` は qstat 用で、scratch の規則とは区別されています。

## 3. 観測の汚染

**判定：refuted（現在の caller に蓄積による誤判定なし）。**

harness の呼出し箇所は TJ:1423、1435、1465、1912、1932、1950、2041、2051、2159。各 test invocation につき1回です。同じ `tmp_path` で複数回 harness を呼んだ後に環境を読む test はありません。

TJ:2051 の fallthrough test は、**1回の harness 内で driver が2回起動**するものです。TJ:2054–2056 は起動数で失敗させ、helper も TJ:2014 の件数 assert で止まるため、環境記録2行との混同はありません。

TJ:1389 の `pop` が `**k2_environment` の更新後にあるので、親環境・明示入力のいずれからも lock を持ち込めません。未設定入力で export の実効性を検査するという裁定に一致します。継承値の挙動を試す harness ではありません。

## 4. 既存3経路の固定

**判定：refuted（指定された組合せの欠落なし）。**

| 経路 | parameter | argv 完全一致 | lock 未設定 |
|---|---|---|---|
| fixture | `stock=None,"0"` × `mode=fixture` | TJ:1924 | TJ:1926 |
| proposal 単独 | `stock=None,"0"` × `mode=proposal,k2` | TJ:1924 | TJ:1926 |
| pair | `mode=proposal,k2`、stock は `"1"` | TJ:1942 | TJ:1944 |

parametrize は TJ:1906–1907、1929。**fixture × stock=0 も含まれます。**

fixture × stock=1 は受理経路ではなく、TJ:1958 の拒否 test が担当します。K2 の空白入り manifest も TJ:1430–1459 の argv 完全一致で固定されています。ただし、この独立 K2 test 自体には lock assert はなく、K2 の lock 不在は上表で検査します。

## 5. launcher

**判定：refuted（tree の取り違え・欠落時の部分投入なし）。**

TL:231 の runner 内 assert は env の repo と実際の cwd の一致を検査します。それだけなら両方が同じ誤った tree でも通りますが、TL:235–236 の `calls` 比較が各 arm の正しい `(argv,cwd)` を要求します。`rc=0` は全4件、`rc=9` は先頭1件です。

欠落 arm は L:224 で `KeyError` になります。これは L:273 の except 対象外なので、**整形された rc=2 ではなく未捕捉例外**です。ただし全 command 構築が L:239 の mkdir／L:240 の runner より前なので、通常の mapping では投入・directory 作成の副作用はありません。

通常の CLI は必須引数と L:263–268 の全 arm 内包表記で mapping を作るため、欠落 mapping を生成しません。これは API の不正入力時に投入を止める挙動であり、今回の must-fix には当たりません。

## 6. 恒真ゲート・テスト代表性と M1〜M9

**判定：検出不能・メタ test のみという懸念は refuted。登録の帰属精度には real（nit）。**

以下は**独立した挙動 test の期待失敗 node 集合の候補**です。メタ test の巻添え失敗は含めず、実走での完全集合確定とも区別します。

nodeid の接頭辞は次のとおりです。

```text
TJ = orchestrator/tests/test_p3_s4_loop_job_contract.py::
TL = orchestrator/tests/test_b5_contrast_launch.py::
```

次の集合表記は全組合せへの展開を意味します。

```text
B =
 TJtest_b5_actual_shell_one_driver_and_trap_rc[{0,7}-{random,sweep-matched,llm,stock}]
 TJtest_b5_stock_off_preserves_single_b5_call[{None,0}]
 （計10 nodes）

D =
 TJtest_default_job_invokes_driver_once[{None,0}-{fixture,proposal,k2}]
 （計6 nodes）

P =
 TJtest_pair_job_invokes_one_driver_with_both_modes[{proposal,k2}]
 （計2 nodes）

S =
 TJtest_pair_job_propagates_driver_status[{0,7,9}-{proposal,k2}]
 （計6 nodes）
```

| 変異 | 期待する独立失敗 node | 単一の挙動上の理由 |
|---|---|---|
| M1 export 削除 | B | lock が null。TJ:2032 |
| M2 home lock | B | lock の絶対 path 不一致。TJ:2032 |
| M3 全体へ移動 | D ∪ P | 非 B-5 の lock が非 null。TJ:1926、1944。B は緑の候補 |
| M4 export 属性削除 | B | 子環境に lock がなく null。TJ:1389、2032 |
| M5 env の tree を random 固定 | 下記3 nodes | 非 random の repo root が誤る |
| M6 cwd を先頭 tree 固定 | `TLtest_submit_only_mkdir_then_argv_runner[0]` | 2件目の env/cwd 不一致。TL:231 |
| M7 pair argv 空配列 | P ∪ S | `--stock-control` 欠落。TJ:1942、1954 |
| M8 fixture 既定21 | `TJtest_default_job_invokes_driver_once[{None,0}-fixture]` | `--value 20` 不一致。TJ:1922–1924 |
| M9 proposal の isolate 削除 | 下記7 nodes | proposal argv の `--isolate-worktree` 欠落 |

M5 の3 nodes：

```text
orchestrator/tests/test_b5_contrast_launch.py::test_dry_run_prints_final_argv_without_runner_or_mkdir
orchestrator/tests/test_b5_contrast_launch.py::test_main_dry_run_validates_tree_and_prints_four_jobs
orchestrator/tests/test_b5_contrast_launch.py::test_submit_only_mkdir_then_argv_runner[0]
```

M9 の7 nodes：

```text
orchestrator/tests/test_p3_s4_loop_job_contract.py::test_default_job_invokes_driver_once[None-proposal]
orchestrator/tests/test_p3_s4_loop_job_contract.py::test_default_job_invokes_driver_once[None-k2]
orchestrator/tests/test_p3_s4_loop_job_contract.py::test_default_job_invokes_driver_once[0-proposal]
orchestrator/tests/test_p3_s4_loop_job_contract.py::test_default_job_invokes_driver_once[0-k2]
orchestrator/tests/test_p3_s4_loop_job_contract.py::test_pair_job_invokes_one_driver_with_both_modes[proposal]
orchestrator/tests/test_p3_s4_loop_job_contract.py::test_pair_job_invokes_one_driver_with_both_modes[k2]
orchestrator/tests/test_p3_s4_loop_job_contract.py::test_complete_k2_environment_reaches_actual_job_driver_argv
```

帰属上の注意は3点あります。

1. **M5 の単体 exact test への帰属は誤りです。** TL:133 は `launch()` を呼びません。変異が L:225 の env 側だけなら同 test は緑で、上記 dry-run／submit test が殺します。
2. **M7・M8 はファイル全体では単一検出層になりません。** TJ:67、74 の静的 pin にも違反し、`test_job_body_static_contract`（TJ:577）が落ちます。さらに既存変異 test の fragment 件数・期待エラーにも干渉します（TJ:844–852、1884–1889、1985–1990）。独立挙動 node の kill とメタ失敗を分離して記録する必要があります。
3. **M6 は runner 内 assert が先に落ちます。** `calls` の最終比較まで到達しませんが、失敗理由は cwd の誤り1つです。`[9]` は先頭 random だけなので検出しません。

**放置時の影響：** 現在の台帳・score・certified 判定は変わりませんが、誤った kill 帰属を完了証拠にすると、将来の lock／tree 回帰を防げるという根拠を過大評価します。

## 7. README

**判定：refuted（今回変更した B-5 記述の実装不一致なし）。**

R:433–441 の各 job の checkout、env/cwd、driver 直前の lock、同 job 内の排他と専有保証外という限定は、L:224–240、J:648–663 と一致します。4引数の実行例も R:484–487 と L:248–249 が一致します。

「別 path」は caller が用意する運用条件です。launcher が重複を拒否する保証ではありません。また「非 B-5 は設定しない」は正しく、既存の継承値を unset する意味ではありません。括弧内の home lock は既定値の説明として読めます。

## 8. 9 skipped

**判定：変更 test 自身が skip を導入した懸念は refuted。ただし全9件の帰属は資料から確定不能です。**

TJ・TL に skip 宣言／呼出しはなく、差分にもありません。

[focus-f1.log:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/focus-f1.log:44)–46 には `test_check_docs.py` の3関数が growth hold として明示されています。48行は `2074 passed, 9 skipped`、85行は `rc=0` です。

残る6件の nodeid／skip 理由はこのログにありません。外部の collection hook 等による skip も指定資料だけでは除外できないため、**「全9件とも変更2ファイル以外」とまでは断定しません。** これは実装欠陥の認定ではなく、ログの証拠範囲です。

## 総括

- **must-fix：なし（指定範囲の静的レビュー）。**
- **nit：** M5 の検出 test 帰属を補正し、M7・M8 の静的 pin／メタ失敗を独立挙動 kill と分離する。
- f1 の成功はログで裏付けられています。M1〜M9 の KILLED、期待失敗 node の完全集合、skip 全9件の帰属は未確定です。
- 新しい gate・検査・台帳の追加提案はありません。scope 外の裁定パッケージ候補も追加しません。