## 受理集合の判定

- `[real]` 受理集合は拡大していない。raw `fetchcontent_base_dir` は `s8b_floor_campaign.py:7234` で `None` のまま入り、`:7262-7276` で分類、`:7277-7279` で eligibility が固定される。`repo_root` の正規化は後段の `:7313`、binding の取得・検証は `:7418-7441`、既定 staging はさらに後段の `:4289-4293` である。
- fresh と resume の build 呼出しはそれぞれ `:7627-7635` と `:7695-7703`。両方とも raw 引数を渡し、導出 base が classifier へ戻る経路はない。
- pilot は式の `mode == "official"`、resume は `resume_dir is None` により常に不適格 (`:7126-7131`)。直接 core 呼出しも `:7304` の official 無条件拒否を通り、テスト専用 monkeypatch が無ければ true の成果物へ到達しない。
- CLI official 拒否 (`:8602-8608`)、core 拒否 (`:465-475`, `:7304`)、18 名集合 (`s8b_floor_contract.py:42-50`)、判定式 (`s8b_floor_campaign.py:7126-7131`) は差分上 literal 無変更。
- 外部取得への既定 fallback はない。`_canonical_floor_fetchcontent_base(None)` は `:2992-3040` に温存されているが、床値既定経路は `:4290` から `_stage_default_floor_fetchcontent_payload` へ進む。現ファイル内の同 helper 呼出しは、`:3264` と `:4295` のいずれも非 `None` 引数である。
- 疑い: なし。

## 恒真な検査

- `[real]` `s8b_floor_campaign.py:3252-3255` の copied root に対する `lstat()` 判定は、事前不在の子へ `shutil.copytree()` が成功した直後という候補生成上、外部からの同時置換を除けば必ず実 directory になる。さらに `:3264-3266` と `:3403-3407` が再検査するため、独立した防壁には数えられない。
- `test_s8b_floor_campaign.py:4303-4305` は生成結果の性質だけを見るため、この検査を削除しても緑のままである。
- binding 不在、ancestor symlink、repo 内 destination、事前存在、排他作成は入力次第で偽になるため恒真ではない。

## must-fix

- `[real]` `orchestrator/tests/test_s8b_floor_campaign.py:4607-4667` — MU6 の test は実効 dataflow を固定できていない。core 内で導出値を同名変数 `fetchcontent_base_dir` へ再代入してから classifier を呼んでも、classifier/build の引数名と呼出し順、および独立した helper/classifier 正例はすべて通る。

  成果物影響: この回帰では fresh official の report が `eligible_for_refreeze=false` となり、certified 選択への昇格対象が消えるのに登録済み mutation test が緑のままになる。

## 直すべきだが must-fix でない

- `[real]` `s8b_floor_campaign.py:3382-3391,3403-3407,3420-3435,3471-3472` — payload policy loader が失敗しても例外を保留し、pristine 検査後に prebuild を実行してから拒否する経路が残る。したがって「payload policy を成功通過せず prebuild へ到達しない」は成立しない。certified 値・公開 report・台帳は後段例外で作られないため must-fix にはしない。
- `[real]` `test_s8b_floor_campaign.py:3519-3597` は policy の正常読出しと binding を確認するが、policy 失敗時に prebuild が未発火であることを確認しない。
- `[real]` `test_s8b_floor_campaign.py:4367-4411` の `staging-exists` / `staging-symlink` は、`:3228-3235` の事前 `lexists` 検査を削除しても `:3237` の排他 `mkdir` が同じ入力を拒否するため緑のまま。受理集合は排他作成で維持されるため must-fix ではない。
- 差分上、既存期待値への skip 追加・テスト削除・真偽反転はない。base-only から source-dir への改訂と failure fixture の更新は新契約に対応しており、実質的な緩和ではない。

## 実装子の報告との食い違い

- `[real]` `s5-author.md:70` の「MU6 は単一理由へ照準」「raw 引数から claim seam basis までの AST dataflow を検査」は過大申告。実際の test は同名変数の再代入を追跡せず、完全な dataflow 検査ではない。
- それ以外の主要記述、すなわち binding nonce の使用、shell staging 削除、3 source-dir、protected literal 不変はコードと一致する。

## scope 外候補

なし。仮想リスク向けの追加 gate・台帳・一般化は提案しない。

## 総括

現実装の受理集合と `eligible_for_refreeze` の意味は裁定どおり維持されている。  
導出 staging は classifier 後にのみ発生し、床値既定経路から外部取得へ落ちない。  
must-fix は MU6 test が同名再代入による回帰を kill できない点の 1 件。  
コピー直後の root 判定は恒真で、独立防壁には数えられない。  
payload policy 失敗後にも prebuild へ進む経路は実在するが、公開成果物の受理には至らない。  
テスト実走は再実行せず、親実測の 482 passed / 3 skipped、rc=0 を前提とした。