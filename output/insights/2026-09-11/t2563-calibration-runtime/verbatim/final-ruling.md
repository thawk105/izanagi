# T-2563 比較後の裁定

- before991694 (bnode038): scheduler186s、start→結果182s、static→pre33s、pre→post143s。
- after991727 (bnode064): scheduler182s、start→結果178s、static→pre29s、pre→post143s。
- 両方accepted、3点×3sweep標本+noise10=19標本、scale not-measured。要求7200/各timeout/標本設計不変。
- raw file mtimeの粗い区間ではglog-install.stderr→third-party-source-verify.stderrが両方1s。これはinstall/copy/付帯処理込みの秒精度区間でcp単独の正確な計時ではない。
- copyより前から、gflags-build開始が1s、glog-build開始が3s違う。全体4sの差を3copy並行化へ帰属できない。各1回・別ノード、同じenv/workload/threads/source/toolchain契約であって同一host対照ではない。
- 採否: 不採用。効果なしの証明ではなく、ユーザーが必要とした短縮効果を示せなかったため。追加測定は増やさない。
- ユーザー明示の「短縮効果を示せなければ実装を残さず」に従い、候補のproduction+追加testの2fileをD95 authorで起点d85bbb211のbytesへ戻す。これは通常fixのテスト緩和ではなく候補全体の撤回である。
- 時間式/要求時間/timeout/標本数へ変更を足さない。最終構成は既存逐次処理へ戻る。最大経路の既存不整合は未解決と記録し、T-2563をremaining:noneとして消さない。
- 最小実行構成: 既存mocc rr50 t48のfresh依存/CCBench build各1、3copy+pristine1、sweep9/noise10。今回成功186sを実績とし、将来の保証時間とは呼ばない。
- 最終実装面diffゼロによりDW-S04の変異免除を適用。正式受入・docs/codex/provenance検査とmain landは実施する。
