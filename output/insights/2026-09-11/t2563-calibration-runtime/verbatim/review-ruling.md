# 段6 親裁定

- 両review rc0/check_output rc0。通常の3copy成功barrier・失敗回収・pristine検証・build・測定前descendant検査の維持は一致。
- Aのsignal所見は制御フローの差としてreal。ただし比較実験のmust-fix指定は不採用 (scope外)。TERM/HUP handlerは非0でwrapper全体を終了し、verifier/build/較正/accepted出力へ到達しない。job-privateコピーの最大120秒の残存を、測定区間の非単独性や誤った較正受理へ結びつける経路は示されていない。
- DW-G05により成果物の値・受理集合・参照への影響を示せないmust-fixは追加実装へ進めない。今回ユーザーの仮想リスク向けgate/検査追加scope外を優先し、比較候補へsignal回収基盤や検査を追加しない。通常完了の全waitと、catchable signal時の回収保証は別であり、後者を保証とは報告しない。
- 失敗rc2→下位非0はrealの表現変更。両reviewが既存consumerへの破れを見つけず、正例/負例の受理集合は不変。元失敗コード保持というauthor指示の範囲で採用。
- 親の変更test単独走は74passed/6.16s/rc0。比較用候補はGO、最終採用はafter効果と時間式整合が未了でNO-GO。
- 比較で不採用となればcode/test差分を撤回し、最終diffゼロのwaveとしてDW-S04の変異免除を適用する。採用する場合はM1/M2を実走し、時間式も別途裁定してから正式受入する。
