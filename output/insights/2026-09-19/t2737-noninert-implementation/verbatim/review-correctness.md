## 総括

**NO-GO（現状の受入完了）。** 実装範囲は妥当ですが、追加テストの置換と計器保存・変異検出の確認が必要です。静的レビューのみ実施し、pytest・build・probeは実走していません。

**must**

- **追加2テストが実装文字列の照合に留まる。**  
  `orchestrator/tests/test_ss2pl_lock_study.py:65,79`  
  呼出し文字列やディレクティブが存在すれば通り、helperの実効性やtest seamの成立を確認しません。上位指示にも抵触します。最小修正は、この追加分だけを実挙動の検査へ置換することです。pristineからのproduction `build_target(phase1)`、既存C++テストのIMPL=0/1実行を使い、既存テストは変更しないでください。

- **TU差分の保存は計器保存の判定になっていない。**  
  `tools/test_t2737_live_probe.py:71,74`  
  assertはTU集合だけで、呼出し削除・引数変更・制御構造変更があっても差分を書いて続行します。M5を検出したとは数えられません。author報告がこの限界を明記している点は適切です。  
  最小の実検証は、保存した全4 TUの旧新差分を読み、計器呼出し・引数・包含する分岐／ループ、study lockとWFG本体の保存を確認することです。その後、`patches/ss2pl-lock-protocol-study.patch:1567`の実`publish_wait`呼出し一箇所を削除して再前処理し、**同じ保存判定が不一致になること**を確認してください。旧binary buildや新gateは不要です。

**should**

- **M6の検出帰属を修正する。**  
  `tools/test_t2737_live_probe.py:79,81`、`patches/ss2pl-lock-protocol-study.patch:693,2267`  
  `wfg.cc`を無条件追加すると、WFG=0ではheaderの型宣言が消えるため、既存不在検査へ到達する前にコンパイル失敗する見込みです。「WFG不在検査が拒否」と事前断定せず、実際の失敗箇所を記録してください。build失敗を不在validatorの検出力へ計上しないことが必要です。

- **旧新TUの完全一致を期待しない。**  
  `patches/ss2pl-lock-protocol-study.patch:30,2223`  
  DLR1固定化により、phase1でも旧来の表示文字列が`DLR0`から`DLR1`へ変わります。数値`SS2PL_DLR=0`とは別です。これは差分として個別説明し、パス・行番号と一緒に広く正規化して隠さないでください。

**nit：なし。**

確認できた境界は以下です。

- 実装4ファイルは指定author commitとbyte一致。親による追加実装ハンクはありません。
- a〜d、e維持に収まり、f/g・inert target・KIND従属・比較条件・abort所有権は不変です。
- test seamは既存`study_lock_test`限定のdefineを利用し、productionのIMPL guardを保存しています。実build成立は未確認です。
- helperのmanifest観測とtimeout配分は裁定に沿っています。
- 親READMEはphase1、runtime meaning、controls全体を区別し、未検証を成立済みとしていません。過去revSの数値を今回の成功証拠へ流用していない点も妥当です。