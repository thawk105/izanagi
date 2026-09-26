指定の 6 本の patch を作成しました。**実装済み・未実走**です。commit は作成していません。

| Patch | マクロ | `#if` site 数 | 変更点・診断条件 |
|---|---|---:|---|
| [V17](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-read-lock-check.patch) | `IZANAGI_BREAK_READ_LOCK_CHECK` | 4 | `transaction.cc:466` の他者 lock による abort だけを省略。省略時に `changed` |
| [V18](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-no-write-tid-max.patch) | `IZANAGI_BREAK_NO_WRITE_TID_MAX` | 5 | `:567` を `max_rset_` に変更。最終 maxtid が元計算と異なれば `changed`。`version_not_above_write` を追加 |
| [V19](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-fixed-commit-version.patch) | `IZANAGI_BREAK_FIXED_COMMIT_VERSION` | 4 | `:579` の版を `(epoch,tid)=(1,1)` に固定。元計算と異なれば `changed` |
| [V20](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-published-version-mismatch.patch) | `IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH` | 4 | `:660` の UPDATE 公開版だけを変更。C/W 版と異なれば `changed` |
| [V21](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-tail-commit-omission.patch) | `IZANAGI_BREAK_TAIL_COMMIT_OMISSION` | 3 | `:706–709` で validation 後に `quit_` が真なら `writePhase()` を省いて true。省略を `changed`・`committed` に、write set が非空なら `omitted_with_writes` に計上 |
| [V35](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-no-read-tid-max.patch) | `IZANAGI_BREAK_NO_READ_TID_MAX` | 5 | `:567` を `max_wset_` に変更。最終 maxtid が元計算と異なれば `changed`。`version_not_above_read` を追加 |

V17–V20・V35 の `committed` は、その取引で `changed` が立ち `commit()` が true を返した回数です。V21 は省略そのものが true を返すため同時に計上します。各診断は relaxed atomic で加算し、終了時に 1 行出力します。

V19 の固定値 `(1,1)` は genesis `(1,0)` より大きく、変更するのは epoch/tid のみです。[Tidword 定義](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/external/ccbench/cc/silo/include/tuple.hh:12) では lock/latest/absent が別 bit、tid が 29 bit、epoch が 32 bit です。V20 は `(UINT32_MAX, 2^29−1)` を公開し、lock=0・latest=1・absent=0 とします。[通常の TID 計算](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/external/ccbench/cc/silo/transaction.cc:563) と [epoch の初期値](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/external/ccbench/cc/silo/include/common.hh:19)・[更新](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/external/ccbench/cc/silo/util.cc:151) から、事前登録された 1 秒の run で通常の C/W がその値に到達しない想定です。無期限の実行に対する衝突不能性は主張しません。

**確認結果:** `git -C external/ccbench apply --check` は全 6 本 rc=0。`unifdef` は無いため、各 patch を一時領域へ適用し、追加マクロを未定義側として除いた内容が pin の元ファイルと文字列単位で一致することを全 6 本で確認しました。V17 の適用後ファイルで `g++ -std=c++20 -fsyntax-only` を試しましたが、生成ヘッダー `config.h` が無く停止しました。他 5 本の構文確認と build・run は未実施です。YCSB の [main は return](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/external/ccbench/cc/silo/ycsb_silo.cc:63) し、[runner は worker を join](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/external/ccbench/common/runner.hh:299) するため、通常終了時に static destructor が走る経路です。

所有外で必要な後続作業は、6 マクロの condition gate 登録、3 test の固定表・site 数更新、`patches/README.md` の記載、計算ノードでの build と発火・verdict 実測です。

## 総括

指定 path の 6 patch は単独適用可能で、未定義時は元コードと一致します。構文と変異の発火・判定は実走での確認が残っています。