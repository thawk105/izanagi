## 変更点

module docstring の非保証記述を、この consumer が読む回収済み成果物（result.json／reservation.json／campaign lock・WAL）に限定しました。build cache 側の全文 manifest の存在を否定しない表現です。

## 変えなかったこと

腕間の digest 一致、再計算・identity 射影との暗号学的対応は非検証、両腕を同じ別値へ置換した改竄はこの層では拒否できない、という3点を維持しました。

docstring 以外は変更せず、後続部分のバイト一致を確認しました。

## 総括

指定の文言修正のみ完了しました。テスト未実行。commit・push はしていません。