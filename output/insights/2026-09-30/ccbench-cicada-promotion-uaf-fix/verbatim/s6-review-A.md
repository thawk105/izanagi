## 所見 — 修理 F1〜F3

- **should — F2 の目印は、promotion による要素追加を確認せず立つ。** 根拠: `fix2-promotion-update-body.patch:18–19` は `update()` 後に既存要素を検索して `from_promotion_` を設定する。一方、土台 `transaction.cc:253–283` には要素を追加せず早期 abort する経路がある。既存要素を見つけた場合も、その由来は確認できない。通常の `read()`・`scan()` は同じ key の既存 write を先に調べるため、その誤標識が実際に発火する経路は静的には確認できなかった。発火すれば後続 update が本来対象外の版の body を置換し、修理 commit の値と確認走行の結果が変わる。**直し方:** `update()` 前後の write set サイズと status を確認し、新規追加された該当要素だけを標識する。

- **nit — F3 の退避配列は追加の確保を伴う。** 根拠: `fix3-abort-insert-uaf.patch:8–17`。abort 中に `push_back` が確保失敗すれば cleanup が途中で終わり、確認結果は異常終了になる。**直し方:** 今回の成果物ではこの限界を記録する。修理の受理集合を変える根拠にはしない。

F1 の読み書き tx は wts で読み、read set を検証する。土台 `transaction.cc:95–135,545–571` を追う限り、rts で読んだ後に読み書きへ転換する P1 と同型の穴は見つからない。F2 の `new_ver_->body_` は inline・別確保・再利用の各経路で `newVersionGeneration()` が返した書込み版を指す。F3 の通常の INSERT は同じ key の再 INSERT を拒否し、tuple も INSERT ごとに生成するため、提示された二重解放経路は確認できない。3 差分は validation・install の条件式を直接変更していない。

## 所見 — 既定 genome と上流 CI

前処理差分 `default-preprocessed.diff` と `opt1_promo0-preprocessed.diff` は、F3 の abort 本文と、行移動による `__LINE__` 展開の 2 か所ずつという報告と一致する。既定 abort には `std::vector` の構築と確保が加わる。`out/s5-author-F2.md` に記された clang-format 14 の変更 file 検査は確認できるが、**上流 CI の全 protocol build と全対象 format の通過は未実走**であり、静的検査から緑とは判定できない。

## 所見 — 壊し patch

- **should — event は「壊した key」を保証しない。** 根拠: `broken-cicada-promotion-ronly-stale-recheck.patch:71–76,99–114`。`break_ronly_promoted_` は tx 全体の真偽値なので、別 key の読み取り専用 promotion が一度起きれば、その tx の別の read で見つかった再検査起点差も event になる。放置すると M1 の witness・key 照合を、壊した経路への帰属として記録し得る。**直し方:** promotion した key と read 要素の対応を保持し、その要素だけを event 対象にする。

F1 条件の除去に加え、元の読み取り専用 tx からの転換を戻している点は変異に必要な挙動である。診断コードは元の検証結果を書き換えていない。ただし最新版をたどる追加処理は実行時間に影響し得る。標準計装と診断変種への適用は `out/s5-author-X.md` に `git apply --check rc=0` と報告されており、実走による発火確認はまだない。

## 所見 — 確認 job

- **must-fix — M1・M2・M3 の期待が合否に反映されない。** 根拠: `launch_promo_confirm.py:255–285,338–366,455–457`。M1 の巡回・event・辺の一致、M2 の指定 frame の ASan UAF、M3 の `update_skip > 0` は記録するだけで、ゼロ件でも job は `observed` になれる。放置すると壊しの帰属と感度 pin が成立しない確認結果を緑として残す。**直し方:** 事前登録した M1・M2 の成立条件を job の結果判定に結び、M3 は kill とせず感度の成否を明示する。

- **must-fix — 異常終了した対照走行を `#FLAGS` 同一性エラーにする。** 根拠: `launch_promo_confirm.py:219–223`。終了前に flags が出なかった土台・M2 走行では `require` が発火し、その走行以降を観測できない。放置すると期待された異常終了や ASan 検出の記録が欠ける。**直し方:** rc が非ゼロで flags が未出力なら「未出力」と記録し、出力された flags に不一致がある場合だけ同一性エラーにする。

- **should — D297 の tip 拒否を確認していない。** 根拠: `launch_promo_confirm.py:389,417–418`。tip 検査の rc と stderr は記録されるが期待した拒否かを判定しない。放置すると D297 の二段確認が成立していない記録を完了扱いにできる。**直し方:** 裁定 R5 の拒否 rc・stderr を結果に対して確認する。probe 側の受理条件は緩めない。

受理式 `launch_promo_confirm.py:250–273` は verifier の **stdout だけ**を JSON として読み、指定された rc、巡回、integrity 数値項目、C 行数、mismatch を確認し、`integrity.clean` を使っていない。`identity():128–135` の tip byte 比較と patch SHA 束縛、`build():181–194` の compile 定義確認もある。D297 probe は `ci():391–409` で tip clone の `cc/cicada/` のみを pin C の bytes に置換して commit する。M2 は F3 逆適用、M3 は F2 逆適用後に計器を当てる構成である。

## 総括

修理の中心的な版選択・UAF 解放順には、提示資料から確定的な新しい破綻は見つからない。**確認 job は現状、変異の不成立を緑にでき、期待される土台の異常終了で観測を中断し得るため、結果の受理前に修正が必要**である。trace・計器 build の throughput を性能値として扱う箇所、および判定器自体を緩める変更は見つからなかった。