指定された 8 本の patch を作成しました。各 patch は対象マクロの `#if` が **4 箇所**で、`changed` を含む取引が `commit()` で true を返したときだけ `committed` を加算します。追加の診断 counter はありません。

| patch（pin `transaction.cc` の変更位置） | マクロ | `changed` の条件 |
|---|---|---|
| [stale-read-payload](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ub/patches/broken-silo-stale-read-payload.patch)（269–277） | `IZANAGI_BREAK_STALE_READ_PAYLOAD` | 二度目の TID の epoch/tid が異なり、payload を取り直さず採用した |
| [corrupt-write-payload](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ub/patches/broken-silo-corrupt-write-payload.patch)（658–659） | `IZANAGI_BREAK_CORRUPT_WRITE_PAYLOAD` | 非空の公開 payload の先頭 byte を反転した |
| [skip-node-validation](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ub/patches/broken-silo-skip-node-validation.patch)（477–485） | `IZANAGI_BREAK_SKIP_NODE_VALIDATION` | node の版不一致を通した |
| [stale-read-own-write](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ub/patches/broken-silo-stale-read-own-write.patch)（216–219） | `IZANAGI_BREAK_STALE_READ_OWN_WRITE` | 返す旧 tuple の bytes が write buffer と異なった |
| [repeat-update-buffer](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ub/patches/broken-silo-repeat-update-buffer.patch)（529） | `IZANAGI_BREAK_REPEAT_UPDATE_BUFFER` | 二度目の update で、入力とも元 buffer とも異なる byte を既存 buffer に書いた |
| [double-abort-backoff](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ub/patches/control-silo-double-abort-backoff.patch)（47） | `IZANAGI_BREAK_DOUBLE_ABORT_BACKOFF` | 二度目の backoff を呼んだ |
| [reverse-write-order](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ub/patches/control-silo-reverse-write-order.patch)（408） | `IZANAGI_BREAK_REVERSE_WRITE_ORDER` | 2 要素以上の write set で元の昇順と並びが異なった |
| [conservative-abort](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ub/patches/control-silo-conservative-abort.patch)（383–388） | `IZANAGI_BREAK_CONSERVATIVE_ABORT` | **非空かつ要素数が偶数**の write set を lock 前に abort した |

V27 の元コードは二度目の update 入力を無視します。有効枝は write set の要素数を変えず、既存 buffer の 1 byte を変更します。V31 と V33 は変更を受けた取引が abort するため、通常 `committed=0` です。

**静的確認:** 8 本それぞれで `git -C external/ccbench apply --check <patch の絶対パス>` が rc=0。`unifdef` は無かったため、各マクロを未定義として枝を除いたソースを pin と byte 単位で比較し、全件一致しました。YCSB の通常終了は `main` の `return 0` で、static destructor が走る経路です。`g++ -fsyntax-only` は試しましたが、`config.h`、次いで `gflags/gflags.h` の不足で対象コードの構文確認には至っていません。**実装済み・未実走**で、build と YCSB run は行っていません。

所有外で必要な作業は、14 マクロの condition gate 登録、対応する 3 test の期待表、`patches/README.md` の更新です。所有 path 以外は編集せず、commit もしていません。

## 総括

8 本の独立 patch を残し、単独適用と未定義時の pin 一致を確認しました。動的な発火・verdict・構文の最終確認は親の計算ノード実行に委ねます。