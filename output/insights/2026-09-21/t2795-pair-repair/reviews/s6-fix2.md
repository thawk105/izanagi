# 修正内容と照合

**赤 (b)・(c) と重複検査の整理は実装済み・未実走です。M18 の挙動検査は制約の確認待ちです。** 変更は所有内のテスト2ファイルだけで、実装・job body・docs は変更していません。git add／commit、pytest は実行していません。

job contract の pin は次のように分離しました。

| pin | 変更と理由 |
|---|---|
| `proposal` | proposal 分岐内の prebuild receipt を検査。fixture 側の同名引数による見逃しを防ぎ、pair／K2 展開とは分離 |
| `pair-argv` | `"${pair_argv[@]}"` のみに限定。K2 展開との二重欠落を解消 |
| K2 展開検査 | 旧「単独行」の一致から、展開トークンが1回だけ存在し proposal 分岐内にあることへ変更 |
| proposal 変異 | 現行の展開行に合わせ、配列展開と run-iteration を残して receipt だけを削除 |
| `stock-mode` | `pair_argv=(--stock-control)` の検査を維持 |

手動照合では、検査関数の断片と shell の proposal 分岐を突き合わせ、receipt、K2／pair 展開、run-iteration と rc 捕捉の一致を確認しました。proposal 変異後も K2／pair 展開が残り、欠落は `proposal` のみになる構造です。無変異正例が通る静的根拠であり、緑の実走結果ではありません。

attestation は `effective_clock.samples_mhz` の較正中央値を算出し、同じ個数の中央値サンプルを観測として合成します。実 `attest_and_build_receipt`／`receipt_matches_contract` と、認可・reservation・claim・layout・lock・WAL・`pipeline.evaluate` の結合は維持しました。

削除した重複は、checkpoint bytes 一致後の whiteboard 再比較と、そのためだけの解析処理です。whiteboard は checkpoint 内に含まれるため、bytes 比較が同じ不変性を保証します。

# M18 の未解決事項

両 resolved 関数は、`run_campaign` より先に `ident.ensure_resumable_attempts` を呼びます。この処理が campaign lock を作り、closure を照合するため、**run_campaign の捕捉だけでは lock-free になりません**。

[段4裁定]( /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-repair/s4-adjudication.md)の「closure 照合・resumability は stub しない」と衝突するため、H 群に限った前処理の代用可否を確認しています。回答前なので挙動検査は追加せず、既存の字面 pin に「指定した代入削除の検出だけ」という限定を明記しました。

許可された場合の検査形は、両 resolved 関数を実行し、捕捉した両 `run_campaign` の `authorization_session` が同一 object であることを確認するものです。

## 総括

- pin の責務分離、中央値による合成観測、重複 whiteboard 比較の削除を実装しました。
- job body は bytes 不変で、未設定／`0` の既定 argv、B-5 単独口、fixture＋stock の prebuild／trap 前 rc=2 を維持しています。
- 本修正は production の受理集合を変更しません。
- 本修正は production の拒否集合も変更しません。
- 通る正例として維持するのは、proposal＋`IZANAGI_S4_STOCK_CONTROL=1` を1回の driver 起動へ渡すケースです。
- Python 構文、shell 構文、`git diff --check`、NFC は確認済みです。
- **実装済み・未実走。M18 の挙動検査は未実装で、上記制約の確認待ちです。**