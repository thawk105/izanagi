## 裁定との差

比較基準は `0600887d92538b3f34d894f9674d202d0a29a578`。以下は静的レビューであり、pytest・configure・buildは実走していません。

略号：

- [P = probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py)
- [T = test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/orchestrator/tests/test_t316_sandbox_probe.py)
- [B = probe.pbs](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2607-impl/tools/pegasus/probes/t316_sandbox_backend_probe.pbs)

| 第5節 | 判定 | コード根拠 |
|---|---|---|
| 1. checkout・基底identity・単一applied | 実装済み | P:2037で既存identity群を維持。P:2052でcheckout、P:2056でpatch前identity、P:2059で結果からvalidを導出。P:2075の単一contextが両buildを包含 |
| 2. requested build・stock直渡し・3変数除去 | 実装済み。ただし全変数の独立確認は後述の限定あり | P:1851の`-S`はsource、P:1887のcontrolは引数。P:1852の共有listから指定3件だけ削除し、`BACKOFF_FIXED=-1`を維持 |
| 3. 関門への入力・拒否診断 | 実装済み | P:1885、P:1940。`_require_condition_gate`は変更前とAST一致 |
| 4. Python／PBS入力束縛 | 実装済み | P:2328、B:55にpatchとharnessを追加 |
| 5. scratch外・readonly mount | 実装済み | P:2069でscratch内を拒否、P:2073でreadonly rootsへ追加。実mount生成はP:849 |
| 6. schema・受領証 | 実装済み | P:39、P:320は変更前とAST一致。追加identityは`ccbench_requested_base` |
| 7. 配線検査 | 実装済み・実走未確認 | T:1919のroot／出所／適用順、T:1961のwrong HEAD／dirty、T:1997の3変数名の明示検査 |

**所見：裁定違反・scope超過は refuted。**

- **根拠：** 差分はP・T・Bの3ファイル。cache準備、deadline伝播、新規lock、案Aの実装はない。
- **成果物影響：** 指定された木の一致回復を超える本体変更は見つからない。
- **通る正例：** pin一致・cleanな基底へpatchを1回適用し、同じrequestedを関門と両buildへ渡す経路。

## 受理集合とテストの弱体化

**所見：受理集合の緩和は refuted。**

- **根拠：** `verdict_s6`、`_condition_gate_family_valid`は変更前とAST一致。family欠落はP:361、未発行recordはP:369の再検証、受領証不一致はP:376、非inert pairはP:381で拒否され、P:399からS6判定に効く。P:124の許可pairは従来の2組のまま。
- **成果物影響：** 同じ観測入力に対するS6のgo集合は変わっていない。
- **通る正例：** production発行record、完全一致する受領証、許可pairの一方を持ち、identity・両build・trace条件を満たす観測。

`condition_meaning_gate.py`は**バイト単位で一致**。SHA-256は  
`9fef1f9ca66f3b6db09f323dcc4d8301c77cdfffa8b73edfb9043a71afc3fa18`。

**所見：既存テストの削除・期待値緩和は refuted。**

- **根拠：** ASTで全test関数名を照合し、**62 → 68、削除名は空集合**。既存関数の変更は`test_execution_binding_shell_dirty_gate`だけで、T:1631にdirty対象2件を追加。既存assertionの反転・削除、skip追加はない。
- **成果物影響：** 既存の拒否検査は維持されている。
- **通る正例：** 従来のcleanな実行入力束縛。追加されたpatch／harnessがdirtyなら拒否対象になる。

## 恒真化と偽の緑

**所見：両側stub・control出所未検証という疑いは refuted。**

- **根拠：** T:1854は実harness・capture・build・commandのcode objectを追跡する。T:1792でstockをcommitし、patch生成後T:1799で復元する。T:1889でrequested／stockの内容差を確認し、T:1925とT:1929でcontrolがそのstock自体であること、T:1938で実configureの`-S`一致を検査する。
- **成果物影響：** requestedコピーをcontrolにする変更や、buildだけ素の木へ戻す変更を検出する構造がある。
- **通る正例：** 復元済みstockと、そこからcheckoutしてpatchしたrequestedの組。

**所見：patch後の木をcleanと偽記録する疑いは refuted。**

- **根拠：** P:2056の検査はP:2075の適用より前。P:2059の`all(...)`をP:2103で記録し、entry名も基底を明示する。T:1967はwrong HEAD／dirtyについて実検査結果のFalseを要求する。
- **成果物影響：** clean記録はpatch前基底についての記録として保たれる。
- **通る正例：** 基底identityがvalidで、適用後は差分を持つrequested。

## 未参照変数の閉包

共有configureは**20変数**。独立に引き直した参照先は次のとおりです。

| 変数 | 参照根拠 |
|---|---|
| `ENABLE_SANITIZER` | `external/ccbench/cmake/CompileOptions.cmake:21` |
| `CCBENCH_TRACE`、`CCBENCH_BACK_OFF`、`CCBENCH_ADD_ANALYSIS` | `external/ccbench/cmake/Options.cmake:62`、`:63`、`:67` |
| `CCBENCH_BACKOFF_FIXED` | `patches/silo-backoff-fixed.patch:23`の追加参照 |
| `CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION`、`CCBENCH_NO_WAIT_OF_TICTOC`、`CCBENCH_WAL` | `external/ccbench/cc/silo/CMakeLists.txt:5`、`:6`、`:10` |
| `CCBENCH_CCACHE` | `external/ccbench/CMakeLists.txt:23` |
| `FETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}` | `ThirdParty.cmake:54`、`:112`、`:136`からFetchContentへ。ローカルCMakeの`Modules/FetchContent.cmake:1149`で動的変数名を参照 |
| `CMAKE_TOOLCHAIN_FILE` | ローカルCMakeの`Modules/CMakeDetermineSystem.cmake:119` |
| `CMAKE_BUILD_TYPE`、`CMAKE_CXX_FLAGS`、`CMAKE_CXX_COMPILER`、`CMAKE_CXX_COMPILER_LAUNCHER` | CXX有効化・target生成経路。ローカルCMakeの各変数資料／compiler決定moduleと照合 |
| `CMAKE_PREFIX_PATH` | `external/ccbench/CMakeLists.txt:33`の依存探索経路 |
| `CMAKE_C_COMPILER`、`CMAKE_C_COMPILER_LAUNCHER` | **実際の依存cacheまでの確認未完了** |

**所見：全20変数の閉包を独立に確認できた、とは言えない — real／nit（検証の限定）。**

- **根拠：** 実CCBenchの`CMakeLists.txt:3`は`LANGUAGES CXX`。一方、T:1766のfixtureは`C CXX`を有効化する。C用2変数の実参照には依存側の確認が必要だが、このセッションでは実cacheの環境変数が未設定だった。
- **成果物影響：** fixtureの成功だけでは、実経路でC用2変数が未使用警告を出さないことを証明できない。
- **通る正例：** 実cacheの依存がCを有効化し、C targetを生成して両変数を消費する構成。

これは未参照変数の残存を確定した所見ではありません。**指定3件の除去と、CCBENCH系8件＋ENABLE_SANITIZERの参照は確認済み**です。

## 総括

- **must-fix：静的に確定したものはなし。**
- **nit：全configure変数の閉包確認に、C用2変数の未確認が残る。**
- 裁定7項目のコード実装、拒否条件維持、既存test削除なし、gateファイル不変を確認。
- **実経路の成功、walltime、受領証発行、テストの緑は未確認。完了承認の根拠にはできません。**