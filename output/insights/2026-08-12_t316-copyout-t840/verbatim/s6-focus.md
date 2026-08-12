| 所見 | 判定 | 根拠 file:line |
|---|---|---|
| レビュー1-1 staging fd 非保持 | `closed` | staging fd を build 後まで保持し、entry identity を再照合して held fd から copy している。[buildcache.py:1370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1370)、[buildcache.py:1411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1411)、[buildcache.py:1415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1415)、legacy は [buildcache.py:1593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1593)、[buildcache.py:1622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1622)。CMake は pathname のままで、staging 全体を anchor しないとの限定もある。[buildcache.py:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:452) |
| レビュー1-2 AST alias・dynamic import | `partial` | 単純・多段 assignment alias と直接文字列の dynamic import/getattr は追跡する。[test_p3_build_authority_cli.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:249)、[test_p3_build_authority_cli.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:284)、[test_p3_build_authority_cli.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:383)。しかし tuple/dict、関数引数、`globals()`、変数経由の module/attribute 名は全て `calls=[] / dynamic=[]` になった。 |
| レビュー1-3 file-wide 除外 | `closed` | file skip はなく、tracked Python 全体を parse し、`(path,function,helper,count)` exact allowlist と照合する。[test_p3_build_authority_cli.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:84)、[test_p3_build_authority_cli.py:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:448)、[test_p3_build_authority_cli.py:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:469) |
| レビュー1-4 capability callable identity | `closed` | import 時 original callable を保存し、現在の wrapper identity ではなく platform capability set と照合する。[buildcache.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:54)、[buildcache.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:132)。これは in-process 差替え防壁でないと限定され、規律2の緩和ではない。 |
| レビュー1-5 M5/M7 単一理由性 | `partial` | M5 は `verify_destination_entry()` 全無効化へ正しく再照準された。[test_buildcache_v2.py:1013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1013)。M7 は test parametrization 自体が production の `_SECURE_DIR_FD_FUNCTIONS` 由来なので、tuple から一 member を削る変異が test case も消して生存し得る。[buildcache.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:54)、[test_buildcache_v2.py:1242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1242) |
| レビュー1-6 site binding 未消費 | `closed` | 「保存済み・未消費」「rejection gate ではない」「receipt/WAL/cache/COMMIT/freeze に入れない」と明記した。[build_admission.py:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:326)。derive は依然 nonce だけを消費する。[build_admission.py:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:541) |
| レビュー1-7 `_mkdir_open_at()` cleanup | `partial` | post-mkdir 失敗時に close/rmdir を試すようになったが、rmdir 失敗を握り潰すため created entry が残り得る。[buildcache.py:1092](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1092)、[buildcache.py:1109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1109)、[buildcache.py:1121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1121) |
| レビュー2-1 close-error fd leak | `partial` | 共通 helper と child 登録順は改善した。[buildcache.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:62)、[buildcache.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:239)、[buildcache.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:438)。ただし返却予定 leaf fd を登録しないまま parent cleanup が例外化する経路と、v2 hit の直列 close が残る。[buildcache.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:314)、[buildcache.py:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:335)、[buildcache.py:981](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:981) |
| レビュー2-2 capability 誤判定 | `closed` | original callable snapshot と delegate wrapper 正例が入り、親実測の既知3赤も313件焦点走では解消済み。[buildcache.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:55)、[test_buildcache_v2.py:1275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1275) |
| レビュー2-3 capability 負例不足 | `closed` | set 欠如、6 dir-fd member、follow-symlinks、procfs の負例が追加された。[test_buildcache_v2.py:1233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1233)、[test_buildcache_v2.py:1242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1242)、[test_buildcache_v2.py:1254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1254)、[test_buildcache_v2.py:1267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1267) |
| レビュー2-4 M5/M13 再照準 | `closed` | M5 は entry verifier 全無効化、M13 は `CMakeCache.txt` 一 member の clean 混入で他の先取り理由を除いた。[test_buildcache_v2.py:1013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1013)、[test_buildcache_v2.py:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:968) |
| レビュー2-5 恒真・helper-only test | `closed` | 実 C++/production call-site 証拠でない範囲を docstring で明示した。[test_buildcache_v2.py:1082](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1082)、[test_buildcache_v2.py:1138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1138)、[test_buildcache_v2.py:1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1155)、[test_buildcache_v2.py:1200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1200)、[test_buildcache_v2.py:1459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1459) |
| レビュー2-6 staging anchor 過大主張 | `closed` | helper・legacy・v2 の全 docstring が CMake pathname 窓と非anchorを明記する。[buildcache.py:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:452)、[buildcache.py:1214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1214)、[buildcache.py:1500](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1500) |

## 新規・残存所見

### blocker — close-error 時の ownership transfer 漏れ

主張: `_close_fds_best_effort()` 自体は渡された fd を全て試すが、全 fd が渡される前に ownership transfer が中断する。

- `_open_regular_at()` と `_open_source_regular_at()` は leaf fd を返そうとした後、`finally` で parent fd を閉じる。parent close が「実際には閉じた後に例外」を返しても、return は破棄され、leaf fd は callerにもcleanup集合にも渡らない。[buildcache.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:314)、[buildcache.py:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:326)、[buildcache.py:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:335)、[buildcache.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:350)。
- `_validate_v2_entry()` は成功用 leaf fd を `result_fd` へ移し `binary_fd=-1` にした後、`bdir_fd` close が失敗すると leaf fd を返せず閉じない。エラー経路では binary close の例外が後続 bdir close を止める。[buildcache.py:981](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:981)、[buildcache.py:984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:984)。

成果物影響: 長時間 campaign が fd 枯渇すると後続 build/cache validation が止まり、認証済み選択・レポート・WAL/COMMIT が欠落する。

提案: auxiliary fd の close が成功してから leaf ownership を返却扱いにする。例外時は leaf を cleanup 集合へ戻す。`_validate_v2_entry()` の finalizer は `[binary_fd, bdir_fd]` を共通 helper に渡し、返却予定 fd も parent close 失敗時には閉じる。両経路へ fd-count fault injection を追加する。

### must-fix — AST 閉包に静的な回避が残る

実際に audit helperへ synthetic sourceを与えた結果:

- `from ... import ... as ...`、多段 name alias: 検出。
- `(helper,)[0]`、`{"x": helper}["x"]`: 未検出。
- `pass_helper(helper)` → 関数引数経由: 未検出。
- `globals()["add_coder_build_authority_argument"]`: 未検出。
- module名・attribute名を変数へ束縛した `import_module(name)` + `getattr(module, name)`: 未検出。

原因は simple `Name` assignment だけを固定点追跡し、call target が dotted name でない場合を捨てること、および dynamic string 解決へ常に空 binding を渡すこと。[test_p3_build_authority_cli.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:249)、[test_p3_build_authority_cli.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:339)、[test_p3_build_authority_cli.py:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:395)。

成果物影響: tracked production Python に未登録 low-level issuer を置いても closure testを通過でき、coder receiptを発行して現行 downstream admissionへ到達できる。

提案: low-level helper binding の全 `Load` を taintとして扱い、exact allowlisted `Call.func` 以外の container格納・引数渡し・subscript利用を拒否する。static string bindingも固定点へ入れる。対応できないなら [build_admission.py:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:5) の「静的に列挙できる Python issuer を閉じる」は過大なのでさらに限定する。

### must-fix — M7/M8/M11 の変異証拠がまだ単一理由でない

- M7: production tupleから memberを削ると、同じtuple由来のparametrized caseも消える。[buildcache.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:54)、[test_buildcache_v2.py:1242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1242)。
- M8: legacy は `_open_regular_at()` 前の `_relative_entry_lexists()` が同じ intermediate symlinkを先に拒否する。[buildcache.py:1555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1555)、[buildcache.py:1561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1561)。v2 anchorは成立するがlegacyは先取りされる。
- M11: decoy testはallowlist setに文字列が無いことをassertするだけで、実際のmatcherへdecoy sourceを渡さない。[test_p3_build_authority_cli.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:521)。`path == relative_path` をprefixへ緩める変異は [test_p3_build_authority_cli.py:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:448) に入るが、現行decoy testはその関数を呼ばない。

成果物影響: gate lossを変異matrixがKILLEDと誤認し、防御が無いcheckoutを認証済み系列へ進め得る。

提案: M7は独立literal 6件をtest側に固定する。M8 legacyはlexists成功後にintermediateをswapする。M11はprefix/nested pathのsynthetic callを `_low_level_allowlist_violations()` に実際に渡す。

### nit — `_mkdir_open_at()` cleanup failureの沈黙

rmdir失敗を握り潰すため、異物挿入やI/Oエラーではnonce candidateが残る。[buildcache.py:1109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1109)。

成果物影響: 完成名ではないため現行認証済み成果物へは入らない。

提案: cleanup失敗を元例外へ付加した `BuildCacheError` として返し、残骸を黙らせない。

### nit — repository-wide AST auditの費用と保守的偽陽性

tracked Python 474件、合計16,016,113 bytesを一回のtestで全read/parseする。性能測定はしていない。production runtimeへの費用はない。さらに leaf名だけでhelper扱いするため、無関係な同名local function/methodも偽陽性になり得る。[test_p3_build_authority_cli.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:349)。

成果物影響: 直接の成果物影響はなく、受入時間と将来の開発時過剰拒否だけ。

## 恒真・恒偽の再検査

レビュー2が名指ししたtest群は、少なくとも「実production gateの発火証拠ではない」ことを明記した。

- gate order: auxiliary evidence。[test_buildcache_v2.py:1157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1157)
- `test_no_trace_symbols_*`: helper contract。[test_buildcache_v2.py:1202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1202)
- secure-environment定数: helper-only。[test_buildcache_v2.py:1227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1227)
- cache-hit compatibility: fresh gate証拠でない。[test_buildcache_v2.py:1083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1083)
- stale cleanup: helper-only。[test_buildcache_v2.py:1140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1140)
- relative-path: helper-only。[test_buildcache_v2.py:1460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1460)

したがって、この名指し群に未限定の過大主張は残っていない。ただしM7のproduction-derived parametrizationとM11のset-membership decoyは、変異の実発火証拠としては恒真寄りであり修正が必要。

## 主張と T-841 境界

`host-security boundary`、`certified safety`、成果物隔離の完成、実行時binary identity、staging全体のfd anchor、directory publishのcreate-only原子性という肯定主張はない。むしろ明示的に否定・限定している。[coder_effect_gate.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/coder_effect_gate.py:3)、[buildcache.py:1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1237)、[build_admission.py:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:11)。

T-841非越境は静的比較で成立した。

- `ADMISSION_SCHEMA`、policy/generator/review schema、`_ADMISSION_KEYS`、`_new_policy()`、`derive_build_admission()`、validatorはHEADとAST同一。[build_admission.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:33)、[build_admission.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:424)、[build_admission.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:503)。
- cache `cache_key()`、`_v2_identity()`、schema定数はHEADとAST同一。[buildcache.py:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:563)、[buildcache.py:728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:728)。
- WAL producer、pipeline、layer3、freeze producerはHEADとbyte-identical。WALは同じreceipt投影を使用し、COMMIT bodyも不変。[pipeline.py:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/pipeline.py:764)、[pipeline.py:1218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/pipeline.py:1218)。
- `p3_s4_loop_sort.py` のfreeze pinはworking treeでなく固定commit blobを読む。[t080_freeze_migration.py:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/t080_freeze_migration.py:857)。

runtime serializationは本レビューでは実走していないが、producer bytesとserialized bodyを構成するASTのHEAD比較ではschema/field/bytes生成規則の差はない。T-841 blockerなし。

## 変異 M1〜M13

| 変異 | 単一理由性の最終判定 |
|---|---|
| M1 | 成立。source専用openから `O_NOFOLLOW` だけを外す。 |
| M2 | 成立。FIFOだけを証拠にする。directoryは数えない。 |
| M3 | 成立。`st_nlink == 1` の単一理由。 |
| M4 | 成立。path-based parent traversalへのcoherent mutationとして行う。 |
| M5 | 成立。`verify_destination_entry()` 全無効化でpost-hash swapが生存する。 |
| M6 | 成立。host metadata生成をstaging metadata copyへ置換するcoherent mutation。 |
| M7 | **不成立**。production tuple由来parametrizationがcase消滅を許す。独立literalへ変更が必要。 |
| M8 | **部分成立**。v2 binary-intermediateは成立。legacyは事前lexistsに先取りされる。 |
| M9 | 成立。未登録siteがtoken/build/WAL前に落ちるruntime negative。 |
| M10 | 成立。ただしstructural coverageだけでありruntime denial証拠ではない。 |
| M11 | **不成立**。prefix/nested decoyが実matcherを通っていない。 |
| M12 | 成立。通常正例を落とす全失敗node集合の記録が必要。 |
| M13 | 成立。`CMakeCache.txt` 1 member混入だけでexact published-setが赤になる。 |

## 総括

blocker:

- close-error時のleaf fd ownership transfer漏れ。

判定は **NO-GO**。親実測の焦点走313 passed / 0 failedは受理するが、未被覆のclose-error経路に具体的なfdリークが残り、AST closureにも静的な回避が複数ある。さらにM7/M8-legacy/M11は変異本走前提の単一理由性を満たさない。

親が変異本走・受入全走の前に直すべきもの:

1. `_open_regular_at()`、`_open_source_regular_at()`、`_validate_v2_entry()` のownership transferとclose-error cleanup。
2. tuple/dict・関数引数・`globals()`・変数経由dynamic importを閉じるAST追跡、または主張の明示的縮小。
3. M7を独立literal capability一覧へ、M8 legacyをprecheck後swapへ、M11を実matcherへ入るdecoyへ再照準。
4. `_mkdir_open_at()` のrmdir失敗沈黙はnitだが、cleanup契約を完全に閉じるなら同時修正する。

pytest・build・性能測定は本レビューでは実走していない。実行したのはHEADとの静的AST/byte比較と、audit helperに対するsynthetic source診断だけである。