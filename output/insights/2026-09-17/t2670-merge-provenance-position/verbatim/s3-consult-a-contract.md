## 所見 (正しさ境界)

**A1 / refuted / plan「commit 後なら取り込み分を監査できる」への反論**

根拠: `tools/check_ai_provenance.py:3557` で authoritative を選び、`:3558` → `_resolve_head` (`:1790`) で HEAD を固定、`:3564` → `_commit_range` (`:1776`) で **policy commit 自身＋`policy..HEAD`** を列挙する。HEAD が merge commit なら、取り込んだ main の新 commit と merge commit 自身が入る。`:2491`〜`:2506` が選択 commit を監査し、`:3573` で HEAD 不変を確認する。

成果物への影響: 新位置では、従来見落としていた取り込み分の違反が受入投入を拒否する。

推奨: plan の `commit-rev-parse` 直後への移設を採用する。brief P2 より、既存の waiter 側 HEAD 比較が監査呼び出しを挟む点で適切。

**A2 / refuted / preclaim の緑 receipt が取り込み分の監査を省いてしまう疑い**

根拠: `tools/check_ai_provenance.py:2363`〜`:2387` は bindings 一致、receipt tip の祖先性、prefix の digest・件数、`tip..head` と残集合の完全一致を要求する。再利用時も `:2477` で delta を選び、`:2503` で監査する。main の新 commit と merge commit は旧 wave tip の prefix に入らない。

**prefix 再利用＋delta 監査になるのは条件付き**である。checker・環境・registry・属性等が変われば bindings 不一致となり、適格な別 receipt もなければ全走になる (`:2231`〜`:2266`, `:2452`〜`:2477`)。delta に correction candidate があっても全走へ戻る (`:2479`〜`:2489`)。preclaim receipt の保存成功も必須保証ではない。

成果物への影響: どちらの経路でも取り込み分の論理的被覆は残り、変わるのは再走量。

推奨: 「必ず preclaim receipt を再利用する」とは記さない。D2045 (`docs/decisions.md:62507`) も根拠に加える。

**A3 / refuted / brief scope(out) の `--range HEAD..MERGE_HEAD` 排除**

根拠: `tools/check_ai_provenance.py:1475`〜`:1478` と `:1987`〜`:1994` は authoritative と明示 range の epoch 適用差を定義する。append-only 履歴検査も authoritative 限定 (`:970`, `:3557`〜`:3563`)。さらに commit 前の `HEAD..MERGE_HEAD` は、まだ存在しない merge commit 自身を含めない。

成果物への影響: range への置換は、既知違反台帳の履歴検査と merge 自身の監査を落とし、受理集合を広げ得る。

推奨: scope 外を維持する。ただし、これは新設する `--head` の同等性が原理的に不可能という証明ではない。`--head` は別設計が必要なため今回扱わない、と分けて説明する。

## 所見 (裁定・契約の整合)

**B1 / refuted / brief P1・plan「commit 保持」は D2044 に反する、という疑い**

根拠: D2044 項5 (`docs/decisions.md:62143`〜`:62148`) が却下するのは、**取り込み分を見ない実装を説明変更で正当化する案**であり、失敗時の rollback を明示要求してはいない。監査を commit 後へ動かすと、現行 `tools/dev_wave_wait.py:3872` の `merge_pending=False` により、監査赤の cleanup は abort から lease 解放へ実際に変わる (`:3310`, `:3353`)。

`reset --merge <premerge>` を追加すると、作成済み merge commit は reflog に残る。`tools/dev_wave_cleanup.py:575`〜`:583` と呼び出し側 `:669`〜`:674` は、その commit が main 非到達なら撤去を拒む。D1233 の喪失閉包とも整合する。**commit 保持も、直ちに撤去可能になる保証ではない。**

成果物への影響: P1 は監査の被覆を広げつつ、失敗した履歴を保存し、受入投入を止める。

推奨: P1 に賛成。ただし契約コメント・負例・F365 の追補を必須成果物にし、「cleanup 関数の変更不要」を「後始末契約の更新不要」と読み替えない。

**B2 / real / brief P1「main の違反が直るまで同じ」・plan の復旧手順不足**

根拠: `tools/dev_wave_wait.py:3775`〜`:3785` の preclaim 監査は、main 取り込み (`:3832`) より先である。監査赤の merge を保持した wave は、次回もその履歴で preclaim が赤になり得る。**main に是正が入っただけでは waiter がそれを取り込む段まで到達しない。** また F365 が示す merge 自身の違反なら、main 側だけの是正で解消するとは限らない。

成果物への影響: 単純再投入を復旧手順にすると、受入の拒否が続き、赤の原因と復旧状況の報告を誤る。

推奨: manager の次手を以下の3行で明記する。

1. 理由本文・違反 SHA・保持した merge SHA を記録し、所有 lease の解放結果を確認して同じ投入を止める。
2. main 由来／merge 自身／実行不能を切り分け、既存契約に従って是正を wave の履歴へ反映する。既知違反登録が必要ならユーザー裁定へ返す。
3. wave HEAD の authoritative 監査が緑になってから受入を再投入し、新しい受領証で land する。

**B3 / real / brief P1 の「2親だから正当な前進 merge」への一般化、brief の D518 引用**

根拠: D518 (`docs/decisions.md:21508`) は receipt memo の prewarm barrier の裁定であり、本件の前進 merge 契約ではない。対応する裁定は D689・D731・D732 (`:27205`, `:28584`, `:28624`)。

`tools/dev_wave_land.py:2160`〜`:2214` は2親だけでなく first-parent 列、初段の tested-main 祖先性、main の単調前進を要求し、`:2248` 以降で merge を再演する。したがって2親というだけでは land 適格性を証明できない。

成果物への影響: この推論を受領証再利用の根拠にすると、land が実際には拒む tip を受理可能と報告する。

推奨: 裁定番号を訂正する。本件の merge は**今回の受入より前**に作られるため、是正後に新規受入を通す通常経路では tested tip 側に含まれる。旧 receipt を持ち越す場合だけ、別途前進 merge の全条件を検査する。

**B4 / refuted / 位置移動が receipt 束縛・規律2・既知違反台帳を壊す疑い**

根拠: waiter は受入前に実行 bytes と tested tip を照合 (`tools/dev_wave_wait.py:3908`)、land は receipt の `waiter_executed_sha256` と tested-tip blob を照合する (`tools/dev_wave_land.py:1119`〜`:1141`)。schema や固定 hash の更新は不要だが、新しい実行 bytes に対応した receipt は必要である。

監査非0は `_run_capture` (`tools/dev_wave_wait.py:2160`) から `_StageFailure` となり、`:4162` で捕捉され、`:4272` の cleanup へ進む。受入 command はそれより前に実行されない。lease 解放は所有権に依存し、`HELD_SELF` は従来から対象外 (`:3359`〜`:3365`)。plan は checker・台帳の変更を対象外としている。

成果物への影響: 取得した lease の解放と受入 command 0回は維持され、台帳の受理述語も変わらない。

推奨: brief の無条件な「lease 解放」は plan 同様に所有権条件を付ける。解放失敗時まで成功を保証しない。

## 所見 (brief の実測値の検証)

**C1 / real / plan 冒頭と末尾の「D2044 逐語資料が不一致」**

根拠: 現在の [D2044-item5.md](/home/SFC/tanab/.claude/jobs/844e52e7/tmp/t2670/verbatim/D2044-item5.md:1) は位置移動と後始末契約を明記し、`docs/decisions.md:62139` の項5とも一致する。plan `:5` の「A-1 の本番測定の認可」は現物に一致しない。過去に差し替えられたかは、この静的検査では判定できない。

成果物への影響: 放置すると、本件の授権が未確認だという誤った報告が残る。

推奨: 現在の資料で再確認済みと訂正し、差し替え要求を削除する。

**C2 / real / brief「実測した現状」の選択集合表記**

根拠: brief `:7` は既定集合を `policy..HEAD` とだけ記すが、`tools/check_ai_provenance.py:1786` は policy 自身も加える。plan `:35` は正しく補正している。

成果物への影響: 実装の受理集合は変わらないが、選択集合と偽 checker の模擬差についての説明が不正確になる。

推奨: `S(H) = {policy} ∪ rev-list(policy..H)` と訂正する。HEAD 到達性だけの fake は production checker 全規則の証明ではない、という plan の限定を維持する。

**C3 / refuted / brief の現行段順序・abort 経路・reflog 拒否・live 束縛への反論**

根拠: 段順序は `tools/dev_wave_wait.py:3831`〜`:3900`、abort の事後条件は `:3118`〜`:3154`、reflog 拒否は `tools/dev_wave_cleanup.py:575` と `:669`、live 束縛は `tools/dev_wave_land.py:1119` に一致する。

成果物への影響: これらの静的事実に基づく位置移動の必要性は維持される。

推奨: 「実測」と静的読解は分ける。指定射影にない test 本文、duration ledger、凍結 manifest は今回読んでいないため、brief の test 行番号・未知 node 許容・凍結 pin 不在の主張まで検証済みとはしない。

## 裁定パッケージ候補 (scope 外だが親がユーザーへ返すべきもの)

現時点で P1 の再裁定や rollback 授権を求める必要はない。

実際に保持 merge の新規違反が出て、既存の是正契約で解消できない場合だけ、違反 SHA・理由・保持 ref・可能な是正案をまとめて返す。既知違反登録や履歴破棄を本変更の暗黙の後始末に含めない。rollback 後の reflog 消去を撤去成功の手段にしてはならない。

## 総括

**P1 と plan の移設位置に賛成。監査被覆を欠く反例は見つからない。**

修正すべき点は、失敗後の復旧手順、2親 merge から land 適格性への飛躍、D518 の誤引用、plan の古い資料不一致報告、policy 自身を落とした集合表記である。静的検査のみ実施し、書き込み・テスト実測は行っていない。