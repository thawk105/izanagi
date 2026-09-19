# 段6裁定

- review-a/bともrc0/validator0/GO、must0。review-a should1はrealで採用。
- M06にrc16だけで残置する誤読があり得たため、「既存hold条件時のみhold・変異を残す」と明確化。実装は無変更。
- collection gate緩和、caller漏れ、W override混同、local hang喪失、in-band rc16でのhold弱化、失敗node一致/resume弱化は独立2レンズでrefuted。
- mutation-spec.jsonに事前登録16変異の一意old/期待nodeを固定。t2484の33収集nodeから診断専用1nodeを外す32nodeを走らせる。診断文字列の赤をkill数へ含めない。
- M1〜M7は運用時間契約の検出、M8〜M11/M13〜M15はcaller/経路の時間契約の検出、M12は既存拒否の検出。長時間実hangの確率や全遅延でのhold消滅を証明する試験ではない。
- 全区間式の各項を落とす変異は、それぞれ単一の式欠落が複数入力で失敗するもの。診断assertを理由に重ねない。P0のmax引数交換は等価正例。
- authorが追加testを__main__節の後へ置いた点はpytest収集には影響しない。今回の実行入口はrun_tests.pyであり、現行148中33追加nodeの収集を実測した。
