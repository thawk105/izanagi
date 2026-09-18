# T-2686 回収の変異検査具体化

元s4のm01〜m17を引き継ぐ。mutation-probe.jsonの各oldは回収anchorで一意、置換後AST parseを全17件確認した。
初回は失敗nodeの完全集合を未確認のためDW-M08のprobeとし、期待SURVIVED/空nodeで観測してから
erratumと共に期待nodeを固定して再走する。probeのMISMATCHを正式KILLEDに数えない。

- m01〜m08: それぞれrename、gitlink、directory prefix、候補順、limit+1、merge、full history、root。
- m09: 未飽和の再走査。既存fixtureは再走査本数の契約を検査する。候補欠落の検出力と混同しない。
- m10: 正常parse後、初回streamのentry境界を数えてbound比較に使い、同じcommitの親別entryを重複カウントする変異。
  old/new逐語はJSON。候補列のdistinct化は保ち、上限判定の計数単位だけ壊す。無関係なSyntaxErrorをkillに数えない。
- m11/m12: log.follow/argv fallback。
- m13: name先頭LFを取り過ぎる。
- m14/m15: tip絞込/失敗memoの契約。
- m16: docstringだけの等価対照、SURVIVED期待。
- m17: per-pathへ戻す。候補意味論のSURVIVEDとprocess/供給契約の検出を分ける。

意味論・fail-closedの変化と、process/方式/構造化シグナルだけの変化は別分類で記録する。
m09/m12/m14/m15/m17を件数だけで正しさ受理集合のkillと呼ばない。
本走前にfix後HEADで一意置換・node名・baseline緑を再検査し、runner/timeoutの契約を維持する。
本体runnerを変異させないので既存mutation taskで計算ノード1jobに束ねることは許容される（runbook §7）。
本走中に親編集/書込み子を重ねない。scratchはregistered worktree外、成果物と同deviceに置く。

実行見積り: estimated_run_secondsは1走あたりだった。plan-onlyの1200秒指定は全体見積りとの
取り違えで6時間表示になったため、本走用の別spec mutation-probe-run1.jsonは80秒/走にする。
根拠は元4file焦点65.75秒と修正後52.10秒（本走はその部分集合1file、同じ既定並列度）。
18走で24分、checkout/復元/収集の余裕を含め計算nodeの外枠45分とする。
timeout_seconds7200は据置き。意味論の変異・期待node/分類は変更しない。
