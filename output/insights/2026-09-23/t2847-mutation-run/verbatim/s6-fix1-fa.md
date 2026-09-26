3 つの patch を修正しました。V18/V35 は Tidword を使う helper を `transaction.hh` の後へ移しました。同 header は `tuple.hh` を取り込むため、宣言順が正しくなります。V20 は UPDATE の公開版だけを `epoch=UINT32_MAX, tid=2^28` に変更し、29 bit の巻き戻り余地と 1 秒の通常 C/W 版がその値に届かない根拠を patch 内の 1 行コメントに記しました。診断条件と既存テストの期待値は変更していません。

| patch | macro | site 数 | 確認 |
|---|---|---:|---|
| [V18](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-no-write-tid-max.patch) | `IZANAGI_BREAK_NO_WRITE_TID_MAX` | 5（不変） | `apply --check` rc=0、未定義側は pin と完全一致 |
| [V35](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-no-read-tid-max.patch) | `IZANAGI_BREAK_NO_READ_TID_MAX` | 5（不変） | 同上 |
| [V20](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-ua/patches/broken-silo-published-version-mismatch.patch) | `IZANAGI_BREAK_PUBLISHED_VERSION_MISMATCH` | 4（不変） | 同上 |

未定義側は各 patch を一時領域に適用し、対象 macro の有効枝を除いた全文を pin と比較しました。`unifdef` は利用できませんでした。`g++ -fsyntax-only` も試しましたが、外部依存の `config.h` がなく完了していません。**有効ビルドと実走は未確認**です。site 数が変わらないため、登録表への波及はありません。

## 総括

A01・A02 の修正と静的確認は完了しました。commit は段 5 の共通契約に従い作成していません。