# 段4裁定・plan v2

consult A/Bはいずれもrc=0、check_codex_output rc=0。mainは32603d385、追加は裁定記録だけ。
段4直前の裁定inboxに本日の新規fileはなく、mainの50件裁定項6/43をmain-update.mdへ反映した。

## 採否

- planの4file意味差分合成を採用。旧file全置換、559bcbc29と旧spoolの取り込みは不採用。
- 両相談のT-2535 consumer保持はreal・scope内。CALIBRATE_PYTHON前倒しに合わせた2抽出helperとproduction関数harnessの環境注入を直す。
- Bのinterpreter stub同一化はreal・scope内。既存_protocol_shell_observationで記録用python3.10と裸python3（exit 97）を分離し、CALIBRATE_PYTHONへ記録用絶対pathを渡す。
  放置すると未smokeのinterpreterへの退行を実起動consumerが検出できず、今回の修正の受入証拠が成立しない。新たなproduction gateは作らない。
- AのM5/M6後続関門maskはreal・scope内。既存負例を同fileのclean repo・三者staging・dry-run helperへ寄せる。
  baselineではrc=2かつ投入成果物なし、正規化変異では後続前提を満たしてrc=0/receipt生成へ到達する形にする。
  既存の署名違いだけでkillしたと数えず、期待値を緩めない。新規test fileやfixture共有化は不要。
- M7はdocs整合pin、M3/M4は受理集合の構造検査でもある。全8件をruntime実効性検査とは呼ばない。
- F934の失敗観測は採用。旧条件が今も必要と承認されたという一般化はrefuted。
  指定/宣言/専用条件要求の整合撤去は裁定済みだが本wave範囲外。元の失敗記録は無効にしない。
- source内の「calibrator resolver below」と未裁定を示す古いコメントだけは局所訂正可。resolver統合とBACKOFF撤去はしない。
- T-2536追加変更、一般化、schema拡張、patch materialize、新規測定、fixture共有化は不採用・範囲外。
- T-1851/T-2417との4file重複0はBも独立確認。実装所有は4fileの単一authorで、共有所要台帳等には触れない。

## 不変条件と正負例

- 受理はshell 2経路のexact {5,20,50,80,95}。5/95は投入記録・receipt・qsub envを持つ正例。
- +5/05/空白/全角/51等はrratio関門で副作用前拒否。offline前提不在を同拒否の代用にしない。
- macro・timeout・meaning・silo条件、offline引数、pristine verifier、receipt schemaは現mainのまま。
- 許可したrratio期待値変更以外を緑のために変更せず、テストの削除・skip・xfailをしない。

## 変異事前登録

- reference-mutation-spec.jsonの8対象を採用。M1/M2/M3/M4=受理集合増減、M5/M6=非canonical正規化、M8=未smoke interpreterへの退行、M7=docs整合pin。
- M8は既存consumerの局所修正で失敗nodeが増えるので、初回は全件SURVIVED期待のprobeとして完全集合を取得し、観測から本走expected_nodesを機械生成する。
- M1〜M6/M8は値・受理集合・起動先への影響を検査、M7は別枠のdocs整合として報告する。
- baseline緑、replacement一意、単一変異差分、固定commit、復元一致を既存harnessで確かめる。模擬の挙動を新規測定と呼ばない。
- コード/テストの追加上限は既存差分と上記局所fixture修正に限る。4fileを越える必要が出たら編集前に親へ返す。
