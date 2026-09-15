## 所見対応表 (closed / partial / regressed)

**全体は partial。受理集合の退行はありませんが、fix 2 の環境変数操作には同一プロセス内の並行呼び出しで退行があります。** 以下の closed は静的なコード確認についての判定です。pytest・build・変異は実走していません。

コード略号：

- [P：probe](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py)
- [T：テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/orchestrator/tests/test_t316_sandbox_probe.py)
- [H：patchharness](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/orchestrator/campaign/patchharness.py)
- [G：condition_meaning_gate](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/orchestrator/campaign/condition_meaning_gate.py)
- [B：PBS](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/tools/pegasus/probes/t316_sandbox_backend_probe.pbs)

| 所見 | 判定 | コード根拠 |
|---|---|---|
| C：裁定との一致――checkout・patch 前 identity・単一 applied | closed | P:2082、2086、2089、2104。基底検査の後、単一 context が両 build を包む。 |
| C：requested／stock／共有 configure の一致 | closed | P:1851、1885、1944、2109、2114。同じ requested を関門と両 build に渡し、stock は P:2055 の素の submodule。指定3変数は P:1850 の共有 list から除去。 |
| C：受理集合の緩和 | closed | P:361、369、376、381、399。従来の4拒否条件を維持。未発行 record の拒否は G:4058、4089。 |
| C：既存テストの削除・弱体化 | closed | AST 比較で既存62関数の削除なし。変更された既存 test は T:1643 のみで、T:1632、1633 の dirty 対象追加。 |
| C：両側 stub・control コピーによる恒真化 | closed | T:1873 が実関数を追跡し、T:1927、1928 が両木の実内容差、T:1967 が stock の実 path、T:1976 が実 configure の `-S` を照合。 |
| C：patch 後の木を clean と偽記録 | closed | P:2086 の検査は P:2104 の適用前。P:2089 の検査結果を P:2132 に記録する。 |
| C：未参照変数の閉包 | closed | P:1850 の20変数を再確認。実 cache の mimalloc `CMakeLists.txt:2` が C を有効化し、`:665` が C ソースの static target を生成。詳細は後述。 |
| D：実行順序・短絡・例外時 cleanup | closed | P:2104、2116、H:262、373。outside 短絡と関門例外の検査は T:2032、2039、1949。Git 自体の失敗まで成功保証する判定ではない。 |
| D：scratch の writable bind による被覆 | closed（直列経路） | P:2098 が実 requested の scratch 配下を拒否し、P:2102 が readonly 登録。mount 順は P:847、849、851。 |
| D：時間予算内の完了 | partial | P:1872、1898 は build コマンドの残時間制限。H:90 の Git、H:130 の flock、P:1954 の関門には同じ deadline が伝播しない。実経路の時間内完了は未確認。 |
| D：Python／PBS の入力束縛 | closed | P:2356 と B:54 は同じ7入力。patch／harness を双方に追加。 |
| D：新規 node の `_run()` 収集 | closed | T:2134 が当該ファイル全体を `pytest.main` に渡す。 |
| D：外部メタテスト・波及 | partial | `test_hooks.py:4392` は実行ファイル集合、`test_official_perf_closure.py:827` は predicate 集合、`test_real_repo_serialization.py:1591` は登録集合・fixture 閉包を検査する。これらの実走結果は未確認。 |
| D：M4 の検出力 | closed（静的） | T:1973、1975、1976 が実 configure 2本の `-S` を requested と照合。 |
| D：M5 の検出力 | closed（静的） | T:1927、1928 の内容差と T:1967 の実 stock path 照合で、patched control を検出する。 |
| D：M6 wrong-head の別層による mask | closed（静的） | T:1891 が実 wrong-head 観測を確認後、T:1893 で pin を復元し、T:1894 で実 harness の受理を確認。それでも T:2023 が probe の拒否を要求。拒否を外せば T:1917 で apply 前に失敗する。 |
| D：M7 の検出力 | closed（静的） | T:2051、2052 が除去した3名称を個別に拒否し、T:2053 が `BACKOFF_FIXED=-1` の維持を要求。 |
| D：報告の裏取り・件数 | partial | T:2076、2109 に2関数・4 parametrized cases が存在する。実パス検査も T:2089 に存在する。runner／checker／変異の実走成否はコードから裏取りできない。 |
| 親：inside build が requested 木を読めない赤 | partial | T:1736 が fixture 全体を workspace 側へ配置。P:1998、2102 が requested 配置と readonly 登録を修正。inside 成功 assertion は T:1960、2120 に残るが、fix 2 後の計算ノード成功は未確認。 |
| 親：`TMPDIR` 未設定から `/tmp` に生成される本番欠陥 | partial | P:1993、1998 と H:362 により、直列・scratch が `/tmp` 外なら回避する。ただし本番 `TMPDIR=/tmp` 明示時は B:85、P:2563 により scratch も `/tmp` 配下となり、P:2000 で停止する。 |
| fix 2：並行呼び出しでの環境復元・配置 | **regressed（同一プロセス内の並行時）** | P:1993、2003、2007 が共有 `os.environ` を保存・変更・復元する。H:362 はその共有値を後から読む。並行時の復元順・生成先を保証しない。 |

## regressed の検査

比較基準は `0600887d92538b3f34d894f9674d202d0a29a578`。

**受理・拒否契約は維持されています。** 次は AST 一致でした。

- `verdict_s6`
- `_condition_gate_family_valid`
- `_INERT_CONDITION_GATE_PAIRS`
- `_require_condition_gate`
- `_condition_gate_receipt_summary`
- `SCHEMA_VERSION`

G は基準 commit と**バイト一致**。SHA-256：

```text
9fef1f9ca66f3b6db09f323dcc4d8301c77cdfffa8b73edfb9043a71afc3fa18
```

AST を全走査した関数集計：

| 集計対象 | 基準 | 現在 | 削除 |
|---|---:|---:|---|
| 全関数定義ノード（入れ子を含む） | 89 | 104 | — |
| 全関数名の集合 | 85 | 100 | 空集合 |
| `test_*` 関数名の集合 | 62 | 71 | 空集合 |

既存 test の変更は dirty parametrization の追加だけです。新規9関数の parametrization は計13ケース、既存 dirty 対象追加は4ケースです。fix 1 時点の独立したソーススナップショットは確認できていないため、「69関数すべてが fix 2 前後で AST 一致」という報告までは独立に追認しません。

**並行時の退行は、受理集合とは別です。** コード上、次の交差が成立します。

1. A が元の `/tmp` を保存し、`TMPDIR` を安全な親へ変更する。
2. B が A の一時値を「元の値」として保存する。
3. A が `/tmp` へ復元する。
4. B が H:362 で `/tmp` を読めば、検査した親と異なる場所へ生成する。
5. B の finally は A の一時値を復元し、元の環境を残せない。

これは静的な実行順序の反例です。実走した競合ではありません。本番呼出しは P:2632 の直列経路なので、この競合が本番で発生したとは判定しません。

## 配置機構の検査

### 例外と復元

直列呼び出しでは P:2007 の `finally` が checkout 入口の例外でも元の値／未設定状態を戻します。`yield` は復元後の P:2012 にあり、その後の identity・apply・build は元の環境で動きます。終了処理は `ExitStack` と H:373 が担当します。

並行呼び出しには前節の問題が残ります。

### path 判定と二つの配置条件

P:1994 の `resolve()` と P:1995 の `is_relative_to()` により、通常の静的な filesystem では次の区別ができます。

| 入力 | 判定 |
|---|---|
| `/tmp` を指す symlink | 解決後に `/tmp` 配下として扱う |
| 相対 path | cwd 基準の絶対 path に解決して判定 |
| `/tmpfoo` | `/tmp` 配下とは扱わない |

直列経路では二条件を別々に扱っています。

- **`/tmp` 外：** P:1995、1999 が生成親を制限し、H:362 がその親に生成する。
- **scratch 外：** P:2085 で生成された実 path を解決し、P:2098 で独立に拒否する。

ただし、生成後の実 requested に対する `/tmp` 外の再確認はありません。前述の環境競合が起きると、生成親に対する保証が崩れます。

新 helper に `/scr` literal はありません。B:85 の既存 fallback には残っています。

また、**新テストの `TMPDIR=/tmp` ケースは PBS 全経路の再現ではありません。** T:1845 の scratch は workspace 側に固定され、その後 T:2084 で環境だけを `/tmp` に変更します。本番 PBS は B:85 で scratch root 自体を `/tmp` にするため、同じ入力名でも配置条件が異なります。

### 負例は実体を観測しているか

**実体を観測しています。**

T:2089 は build に渡された `source` を `resolve(strict=True)` し、T:2094 は実ファイルを読んで patch 適用を確認します。T:2091〜2095 は生成先・scratch 外・readonly 登録、T:2104 は親 directory の撤去を検査します。

T:2096 の環境変数再読は復元検査です。配置検査の代用品ではありません。ただし、この負例は T:2099 で build を置換するため、実 mount や inside build 成功の証拠にはなりません。

## scope 超過の検査

基準 commit との差分は P・T・B の3ファイルです。H と G はバイト一致でした。

次の scope 外変更は認めませんでした。

- cache 準備の導入：なし。P:1859 の既存 cache 直指定を維持。
- 関門への deadline 伝播：なし。P:1954、1957。
- 新規 lock：なし。H:130 の既存 lock を使用。
- 一般化した timeout 改修：なし。
- 案 A：なし。P:1853 の define と P:399 の条件関門を維持。

時間内完了と外部メタテストは未解決ですが、そこから scope 外の改修は提案しません。

## 未参照変数の閉包の検算

**親の「除去した3件で閉じる」という判断を、参照経路の静的検算として支持します。** fixture の `C CXX` 宣言だけを根拠にはしていません。

共有 configure は P:1850 の**20変数**です。

| 変数群 | 再確認した参照先 |
|---|---|
| `ENABLE_SANITIZER` | `external/ccbench/cmake/CompileOptions.cmake:21` |
| `CCBENCH_TRACE`、`BACK_OFF`、`ADD_ANALYSIS` | `external/ccbench/cmake/Options.cmake:62`、`:63`、`:67` |
| `CCBENCH_BACKOFF_FIXED` | `patches/silo-backoff-fixed.patch:23` |
| `CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION`、`NO_WAIT_OF_TICTOC`、`WAL` | `external/ccbench/cc/silo/CMakeLists.txt:5`、`:6`、`:10` |
| `CCBENCH_CCACHE` | `external/ccbench/CMakeLists.txt:23` |
| `FETCHCONTENT_SOURCE_DIR_*` 3件 | `ThirdParty.cmake:54`、`:112`、`:136` → `/usr/share/cmake-3.22/Modules/FetchContent.cmake:1149` |
| `CMAKE_TOOLCHAIN_FILE`、`CMAKE_PREFIX_PATH` | `CMakeDetermineSystem.cmake:119`、CCBench `CMakeLists.txt:33` の依存探索 |
| `CMAKE_BUILD_TYPE`、`CMAKE_CXX_FLAGS`、C/CXX compiler・launcher | C/CXX 有効化・target 生成経路。特に C 側は下記で確認 |

C 側の閉包は次の通りです。

1. P:1860 が実 cache の mimalloc を指定する。
2. `external/ccbench/CMakeLists.txt:43` → `ThirdParty.cmake:112` → `FetchContent.cmake:1281` が依存を build graph に加える。
3. [実 cache の mimalloc CMakeLists.txt:2](/work/1/SFC/tanab/izanagi-thirdparty-cache/mimalloc/CMakeLists.txt:2) は `project(libmimalloc C CXX)`。
4. 同ファイル `:63` の `.c` ソースを `:665` の `mimalloc-static` が使用する。`MI_USE_CXX` の既定値は `:14` で OFF。
5. `CMAKE_C_COMPILER` は `CMakeDetermineCCompiler.cmake:39` と mimalloc `:600` で参照される。
6. `CMAKE_C_COMPILER_LAUNCHER` は `CMakeCInformation.cmake:121` で参照され、生成 target の launcher 初期値になる。空文字は launcher 抑止の指定として残る。

したがって、C 用2変数を未参照とする根拠はありません。ただし、これは**参照先の閉包確認**であり、本番 configure の stderr が空だったという実測ではありません。

## 総括

- **条件関門・schema・既存テストの受理／拒否契約に退行なし。**
- **M6 の別層による mask は静的に解消。新配置検査は実 path と実ファイルを観測している。**
- **fix 2 の `TMPDIR` 操作は同一プロセス内の並行時に regressed。**
- 未設定 `TMPDIR` の直列配置は修正されているが、PBS での `/tmp` 明示経路、fix 2 後の計算ノード inside 成功、本番 S6・時間内完了は closed としない。

親提示の **161 passed** と **162 passed／3 failed** は判断材料として区別しました。本レビューで緑を実走確認した検査はありません。