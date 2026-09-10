# Stage 4 裁定・plan v2 — [T-1526][T-1527]

## 裁定

- 件数訂正は real / 採用。T-1526 は campaign 8 node (通常 checkout で compiler dependency skip 6 + conditional-first 2)、T-1527 direct は別の 9 件目。標準 checkout の実装後期待は対象 9 node = 7 pass / 2 conditional skip。基準集合に meta 6 nodeを足すと 13 pass / 2 skip。
- 過去の g++-12 全緑を今回 direct fixture の証拠に流用できない所見は real / 採用。実装後の exact node 実走を唯一の受入証拠にする。
- missing-define が任意 RuntimeError を受ける偽緑は real / scope内 / must-fix。同じ cxx の完全 define positive を先に通し、negative の診断を `BACKOFF_FIXED` と `defined`/`undef` 系 markerへ限定する。
- conditional skip 先行順と選択 cxx の全 consumer 配線が meta test で固定されない所見は real / scope内 / must-fix。AST は存在集合でなく順序と keyword/positional binding を検査する。
- compiler 版非依存、production site compiler 同一性、旧 cache identity 維持という表現は real な過大主張。helper は available test compiler fallback と呼び、同一選択 compiler 内の関係だけを主張する。
- source token/variant ID と build-cache identity の混同は real。stock token/variant ID は維持、cache identity は明示 cxx ごとに分離、と二系列で検査・記録する。
- fixed node の `cache_key()` へ選択 cxx が届かない所見は real / scope内 / must-fix。同じ cxx を両辺へ明示し、通常 checkout で動く builtin nodeにも stock/nonstock cache-key 分離を置く。
- P1 (`submission.prepare_toolchain` 非変更) は攻撃を refute。qualification exact toolchain manifest / series acceptance は変更しない。
- T-1527 は最小 `_FAKE_MOCC_CMAKE` と条件/includeなし `int mocc_fixture;\n` を initial commit 前に供給する案を採用。canonical tupleやproduction sourceは変更しない。
- legacy cache が compiler要求名しか束縛しない所見は real / scope外。compiler portability一般化として本waveでは実装せず、insight/handoffへ記録する。
- T-1520 landed diffは dev-wave tools、spool、`test_check_docs/test_dev_wave_*/test_spool_fold`だけで対象6 pathと非重複。active T-1593が `orchestrator/tests/README.md` に1行追加を所有中なのは real。author所有からREADMEを外し、段7前にland済みならmain取込後に親が同期、未landならscope外申し送りとする。

## plan v2

1. Codex author 1本だけを起動し、所有は `orchestrator/tests/test_campaign.py`、`test_s1_direct_comparison.py`、`test_skip_classification.py` の3 fileに限定する。production、README、docs、commitは禁止。
2. `test_campaign.py` の既存 `_any_cxx()` を最初の対象consumerより前へ移し、過大な版非依存docstringを縮約する。旧 `_require_g13()` を削除する。
3. campaign 8 nodeすべてで一度選んだ cxx を preprocess、resolve、compute/baseline、trace、cache_keyの全呼出しへ明示する。fixed/missingのconditional判定は compiler選択より先に残す。
4. missing-define nodeへ同compilerのpositive controlと限定診断assertを加え、任意RuntimeError偽緑を閉じる。既存拒否集合は弱めない。
5. direct moduleに局所 `_any_cxx()` を同じ候補順で置き、direct nodeの全 resolveへ明示 cxxを渡す。module間importやshared resolverは作らない。
6. direct fake repoにmocc owner CMakeと最小transaction sourceを追加する。他のmocc bytesやOPTIONSは足さない。
7. skip-classification meta testを、候補順、g++-13不在+g++-12正例、全滅skip負例、conditional先行順、対象9 nodeのselected-cxx consumer bindingまで強化する。census 4 nodeは縮めない。
8. 親が実装後に対象9 node + skip classificationを `-rs` で実走し、選択compiler realpath/version、7 pass/2 conditional skip、cache identityとreject負例を確認する。
9. scope外の他g++-13 literal、prepare_toolchain、buildcache/source_digest、compiler portability一般化は変更しない。

## 変異事前登録 (DW-M01 / test-only 新旧差分)

| ID | 単一変異 | mask不存在 | 第一失敗期待 |
|---|---|---|---|
| M1 | `_any_cxx` から `g++-12` 候補を削除 | helper選択meta以外に同候補順の防壁なし | `test_site_compiler_helpers_choose_first_available_and_skip_only_when_empty` |
| M2 | 全候補不在でも `g++` を返す | 実compiler起動前の唯一のall-absent負例 | 同上 |
| M3 | fixedまたはmissingの `_any_cxx` をconditional判定より前へ移す | 既存call-set検査は順序を見ない | 新しいconditional-order meta node |
| M4 | 対象nodeの1つから選択 cxx bindingを外す | default g++-13が在る環境では実走だけでmaskされるためAST bindingが唯一 | 新しいselected-cxx binding meta node |
| M5 | fake mocc `transaction.cc` 作成を削除 | canonical tuple readerに代替sourceなし | `test_real_source_digest_unifies_all_outer_whitespace_tokens` |
| M6 | fake mocc `CMakeLists.txt` 作成を削除 | source owner resolverに代替CMakeなし | 同上 |
| M7 | missing-define負例へ完全defineを渡す | negativeの供給漏れが消え、他reject層なし | `test_source_digest_failsclosed_on_missing_define` |
| M8 | fixed/builtin cache-key比較から明示 cxxを外す | cache_key既定g++-13でも差比較自体は通るためbinding metaが唯一 | selected-cxx binding meta node |

- baseline は実装後commit、旧側は基準commit 402a5752。test-only waveなので新規meta nodeが旧側を拒否し、既存9 nodeの旧側skipは緑と数えない。
- 変異は対象fileの単一replacementだけにし、expected node集合は実装後のprobeで固定する。hang変異なし、1件ずつ直列実行する。

## 禁止と通る正例

- 禁止: g++-13不在を理由に規律2のnegativeをskipへ戻す、任意RuntimeErrorを成功扱いする、compiler版横断の保証を追加する、production qualification acceptanceを広げる。
- 通る正例: g++-13不在・g++-12在庫で clean/current==HEAD は STOCK、builtin挙動変更は非STOCKかつ別cache identity、コメント変更は同digest、include/TRACE/missing-defineは既存理由でrejectする。
