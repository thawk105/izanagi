## 所見

静的検査のみ。ファイル変更・pytest・性能測定は行っていません。以下の略号はすべて指定 repo root 内です。

- F＝`orchestrator/tests/test_s8b_ratified_freeze.py`
- V＝`orchestrator/tests/test_s8b_ratified_verify.py`
- C＝`orchestrator/tests/test_s8b_floor_campaign.py`
- O＝`orchestrator/tests/output_snapshot_ignores.py`
- R＝`orchestrator/tests/test_run_tests_preflight.py`
- A＝`orchestrator/tests/test_codex_reasoning_ab.py`
- P＝`orchestrator/tests/test_p3_b4_producer_auth_experiment.py`

1. **severity: must-fix — コピー元の絶対パス漏洩を既存 assertion が検出できなくなる。**

   **位置:** [plan-out.md:64](/home/SFC/tanab/.claude/jobs/28fa456a/plan-out.md:64)、F:1277–1281。

   **失敗の形:** production `s8b_floor_campaign.py:4819` の root→placeholder 置換を無効化すると、manifest/result の `configure_argv` に構築元の絶対パスが残る。現行 builder は自身の root を探すため assertion failure になる。提案の切断点で保存し、別 root にコピーした場合、既存 assertion が探すのは**コピー先**の `tmp_path/root/out_root` だけなので、構築元パスを見逃す。

   具体的には V:1433 `test_design_source_worktree_drift_still_loads` が、旧版では builder 内で失敗し、新版では load まで通り得る。`load_ratified_freeze` は source/closure/floor 投影を検査するが、argv の絶対パス不在は検査しない。

   **根拠行:** production `s8b_floor_campaign.py:4817–4826, 4861–4865`、`s8b_ratified_freeze.py:1422–1440`、V:1443–1453。argv の後段検査も非空 `list[str]` の確認に留まる（production `s8b_ratified_freeze.py:1782–1788`）。

   **修正条件:** consumer ごとに構築元・コピー先の双方を needle に含める。無変異時の全木比較だけでは、この変異に対する検出を維持できない。これは **fresh memo でも起きる mask**。

2. **severity: must-fix — module fixture と環境清浄化 fixture の scope が矛盾する。**

   **位置:** [plan-out.md:155](/home/SFC/tanab/.claude/jobs/28fa456a/plan-out.md:155)、R:58–69。

   **失敗の形:** 記述どおり module base 構築 fixture を `_clean_runner_env` に依存させると、後者は function scope で、さらに function scope の `monkeypatch` に依存するため `ScopeMismatch`。R:1837 など対象 node が test body に入る前に setup error になる。

   function scope のコピー fixture だけを依存させても、module base の eager Git 構築を清浄化後にする保証にはならない。

   **修正条件:** module fixture は lazy な保管先／factory のみ用意し、初回 Git 構築を `_clean_runner_env` 完了後の function fixture から要求するなど、scope と実行順を明記する。

3. **severity: should — preflight 対象リストに fingerprint を呼ばない full-run dispatch node が混ざっている。**

   **位置:** plan-out.md:159、R:2314–2333。

   **失敗の形:** `test_previous_full_cap_estimate_dispatches_without_local_scope` は admission が DISPATCH なので、production `run_tests.py:2540` の fingerprint に到達しない。それでも `_tracked_repo` のコピーへ `_REPO` を差し替えると、空引数の acceptance 経路で `tools/ruleops.py` を実行しようとし、ファイル不在により期待値9ではなく `_RULEOPS_GATE_RC` を返す。

   **根拠行:** R:81–90 の repo は `tracked.txt` だけ。production `run_tests.py:2531–2535, 2588–2596, 822–859`。RuleOps を満たしても、その後には submodule 初期化検査がある（:891–935）。

   plan の「最小の正常 repo」はこの入力閉包をまだ定義していない。この node は高速化対象から外すのが自然。通すために RuleOps/submodule 検査を新たに stub 化するのは、DW-O14 適合の根拠にならない。

4. **severity: should — U2 の cache は「blob SHA→SHA256 の純関数」という説明になっていない。**

   **位置:** plan-out.md:119–125、O:604–619、profile 要約:21。

   **失敗の形:** worker A が clean entry の digest を共有済みの状態で、worker B の初回 `_real_output_snapshot()` における同ファイルの digest 読取りだけが `OSError` になる入力を考える。現行の B は process cache が空なので例外で停止する。共有後は digest を呼ばず、C:13795 の before/after が通り得る。

   **根拠行:** cache miss は blob を読み出して計算するのではなく、渡された `digester(absolute)` を実行する（O:618）。C は `_digest` を注入し、その実体は worktree の `open/read`（C:1773–1775, 1788–1792）。

   安定した正常 tree で値を共有できることと、読取り失敗まで含む fail-closed 同一性は別。C:2205 の既存例外検査は tmp の非cache経路なので、共有 hit のこの差を検査しない。共有値の発行条件・破損時処理と、保証する同一性の範囲を明示する必要がある。

## plan の等価主張の裏取り表

| 主張 | 現物の行 | 裏取り結果 |
|---|---|---|
| campaign 後・mutation 前で分割できる | F:1085–1127 | 分割位置と後段 mutation は確認。ただし後段 assertion の観測対象が変わる。所見1 |
| `selector_extra_files` は後段だけに効く | F:641–692, 1102–1105 | 確認。`_prepare_emitter_base` 内では使われない |
| 固定 Git identity/date により決定的 | F:278–314 | commit の決定性の材料は確認。全 artifact・全 key の同一性は未証明 |
| cert は root を含まない | production `s8b_floor_campaign.py:5565–5580` | 確認 |
| binary/argv を相対化する | 同:4746–4758, 4789–4826, 4933–4955 | 正常実装では確認。相対化退行の検出維持は未達 |
| PID 束縛 capability を運ばず後続を実行できる | `s8b_v2_freeze_fixture.py:92–129`、production `s8b_ratified_freeze.py:1831–1846`、`s8b_binary_admission.py:324` | portable receipt 検証に issuer capability 引数はない。別PIDでの全 load/launch 成功までは未実測 |
| admission 状態はコピー後に作り直す | F:1143–1165、`s8b_v2_freeze_fixture.py:586–588` | legacy/v5 とも削除・再構築を確認 |
| `durable_root_policy` は移設可能 | F:1097–1099 | `approved_roots` は構築元に束縛された実行時値。コピー後の新規処理がコピー先 policy を作ることは実装待ち |
| `_fixed_prepare.cache_root` を設定し直す | F:1060–1061, 1303–1304 | 必須。`ccbench_dir` も同時に設定し直す必要がある |
| index refresh で元と同じ観測になる | production `s8b_ratified_freeze.py:367–378, 1049–1055` | status／直接bytes比較は確認。全木・全Git呼出しの等価証明にはならない。inode/ctime/stat欄の一致は期待できない |
| ratified module に `diff-index` がない | 同 module の検索、:340–378 | 確認。brief の説明は過大 |
| before/after を維持する | C:13796, 13823 ほか | 正しい。P2 を退けた理由も成立 |
| clean digest の共有だけなら観測不変 | O:594–619 | 正常・安定 tree の値について条件付き。失敗伝播は所見4 |
| ignore 規則解析だけを bytes-key memo にできる | O:115–180 | 解析部分の純粋性は確認。返却する mutable dict の共有汚染を避ける必要はある |
| `_REPO` は fingerprint の外側 seam | production `run_tests.py:2540, 2567` | local routing 対象では妥当。ただし `_REPO` は preflight 全体にも効く。所見3 |
| RecordingSession は旧 root を保持する | production `run_tests.py:1029, 1092–1097, 1118, 2155–2157` | plan の注意は正しい。正規 runner の auto-record=0 が前提 |
| oracle/prompt をコピー先で再生成する | production `codex_reasoning_ab.py:3600, 3617, 3727–3732, 3766–3774` | 必須。完成 oracle の単純コピー不採用は正しい |
| base metadata/index の検査を維持できる | A:921–942, 3795–3818、production `codex_reasoning_ab.py:1634–1671` | 元の構築前後観測を保存すれば検査可能。metadata は相対path・mode・内容digestで、inode/mtimeは含まない |
| p3_b4 は3×3 tree | P:759–828 | 誤り。3+3+1＝7。plan の訂正が正しい |
| nodeid・group・登録簿・hold は不変 | plan-out.md:27、conftest.py:614–664 | 変更しない方針は確認。実装・collection 前なので結果の保証は未了 |

real-repo lock は **function fixture より前の `pytest_runtest_protocol` で setup/call/teardown 全体を囲む**（conftest.py:2285–2303）。したがって既存の登録 consumer が lazy に shared base を構築するなら、module fixture であること自体は lock 外読取りを意味しない。

一方、`benchmark_snapshots` を session scope に変更すると、serialization test が要求する `benchmark_snapshots[module]` literal が消え、`test_real_repo_group_collection_exactly_matches_canonical_nodes` 系の閉包検査が赤になる（`test_real_repo_serialization.py:1454–1494`）。**fixture の module scope は維持し、その内部の保管先だけを session 共有にする必要がある。** 未登録 node にまで依存を広げる変更も同じ閉包検査に抵触する。

## 変異が mask される経路

| 経路 | 誤って通る／帰属が変わる形 | 必要な確認 |
|---|---|---|
| **構築元パスが needle から消える** | 所見1。fresh memo でも V:1433 が旧版だけ失敗し得る | `_portable_argv` の相対化退行を matrix に追加 |
| **U1 campaign 構築済み木を変異後に再利用** | `_run_campaign_core`、certificate、portable binary、selector 材料生成にだけ効く変異が consumer に届かない | production 変異適用後に import・初回構築。各変異で新 interpreter／新memo |
| **U3/A 完成 POS/NEG 木を変異前から再利用** | `_build_snapshot_base`／`_derive_snapshot_from_base` の誤りをコピー先 `verify_snapshot` が観測できない。正常完成木だから通る | 構築側の変異も入れ、新memoで生成。HEAD/branch検証の2変異だけでは不足 |
| **保存した base metadata が変異前の観測** | A:3801–3802 が旧構築時の「不変」を比較し、変異した derive の base 破壊を見ない | 初期・POS後・NEG後の記録を毎変異の実構築から取る |
| **U4 prepared tree の再利用** | guard挿入bytes／`prepare_candidate_tree` の変異後も、以前の AST が guard 1回を示す | process内 lazy cache も毎変異で破棄。pristine と prepared を混同しない |
| **U2 process/disk digest の残留** | 変異前の digest、別workerで取得した値が cold read の失敗・異常値を隠す | diskだけでなく process cache もfresh。共有hit・miss両方を比較 |
| **失敗した共有構築の再利用** | 最初の失敗を完成品扱いすると後続が別理由で落ちる／通る。pytest module fixture の setup failure を共有すると失敗nodeが拡大する | failed construction を記録しない。lazy factory内部で構築し、全consumerの結果を比較 |
| **fork 前に import 済みの production** | diskの変異後も fork 子が旧関数・旧定数を継承する | 新interpreter開始後に変異済みproductionをimport。新tmpだけでは不足 |

plan:255–257 の fresh run／pyc 対策は正しい。ただし matrix の U1 はコピー後の loader 変異、U3/A は再実行する verifier 変異が中心で、**省略する構築処理そのものの検出維持を十分に攻撃していない**。

共有管理についても、次の具体的経路を親の実測に含めるべきです。

- `_T080SharedBases.get` は marker 確認後に tree の完全性を検証しない（:933–951）。完成markerだけ残してbaseのfileを欠落させた場合、元の独立構築なら成功するconsumerがcopy失敗になる。
- fork 子が継承した lifetime fd に `LOCK_UN` すると、親の参加lockまで外れ得る。plan:88 の所有PID区別は必須。
- T080 の既存実装は `PYTEST_XDIST_TESTRUNUID` 不在時に disk共有へ参加しない（:957–959）。U1 は親で作った一意の所在をfork子へ継承する別経路が必要。同じ固定fallback名では独立走同士が混ざる。
- 全workerがcollection中に参加する条件なら通常終了の早期削除を防げる。遅れて参加するreplacement workerまで無条件に保証するものではない。最後の退出者がlock fileごと削除する間に参加すると、旧inodeと新inodeのlockが分離し得る。
- shared-base のkey lockは実repo lockの代替にならない。collectionでは参加だけを行い、実repo構築は登録consumerのprotocol内に置く。

## 親 brief への所見

| 前提 | 所見 |
|---|---|
| **P1** | 固定Git日時とindex refreshだけでは不足。特に所見1でassertionの検出集合が変わる。portable receipt とPID束縛capabilityは区別できるが、別PIDで全後続成功という結論は未実測 |
| **P1′** | 代表nodeでledger回復が支配的という観測はある。ただし約90node全部が同じ内訳という証拠ではない。残る律速の説明には使えても、一律の秒数算定には不足 |
| **P2** | **誤り。** 先行testがB→X、後続testがX→Bと変更すると、共有beforeでは後続の変更を見逃す。planの不採用が正しい |
| **P3** | local routingについて条件付きで妥当。19node全部に一括適用できる証明ではなく、対象リストにはfingerprint非到達nodeもある |
| **P4** | **誤り。** oracleのsnapshot絶対pathとそのdigest、rendered prompt／receiptはコピー先に依存する。planの再生成方針が必要 |
| **P5** | blanketな「局所候補なし」は言い過ぎ。p3_b4の対象は7treeで共有候補がある。T1259も既存module memo以上の利得があるかは別問題 |
| **P6** | **12workerの比が48workerへ転移する根拠なし。** 共有構築待ち、copy競合、配置worker数、real-repo lock待ちの割合が変わる。planの外挿禁止が正しい |

台帳を読み出して再集計した値は次のとおりで、親の約32%という算術は合っています。

| file | 台帳node数 | worker秒 |
|---|---:|---:|
| floor_campaign | 528 | 2,368.125 |
| ratified_verify | 189 | 944.843 |
| producer_auth_experiment | 50 | 832.179 |
| t1259 | 51 | 550.045 |
| run_tests_preflight | 216 | 544.325 |
| codex_reasoning_ab | 643 | 482.524 |
| **6 file合計** | | **5,722.041** |

全体は **17,958.848秒**。ただし台帳自体には、この値を「48workerの同一走」と立証するrun情報がありません。floorの実測532nodeと台帳528nodeの差も突合が必要です。

profile要約の `-n 12` に対する「13worker×10〜11秒」は、setup合計からの逆算でworker数を確定しており不適切です。worker再起動等の記録なしに13workerとは言えません。また fork 親のwaitpid時間は、builder内のGit・campaign・後続assertionの費用分離には使えません。

## 総括

plan は P2・P4・P6 の過大な前提を適切に修正している。
ただし U1 のコピー元path検査抜けと U3 のfixture scopeは実装前に修正が必要。
mutation matrixには、コピー後のvalidatorだけでなく省略する構築処理への変異が必要。
nodeid・hold・登録簿の変更要求は見つからないが、fixture scope／consumer閉包の維持を確認すること。
性能値・別PID消費・失敗node集合の同一性は未実測。