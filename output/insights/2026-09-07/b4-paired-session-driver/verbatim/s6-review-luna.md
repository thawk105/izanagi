## 所見

- **id**: review-01
- **対象**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:483`
- **主張**: spec v2 の拒否をテストが守っていない。schema 定数は pin しているが、誤った schema 値を loader に渡す負例がない。
- **具体例**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1202-1204` の schema 一致検査を削除しても、全 fixture は `F.SPEC_SCHEMA` を使い、schema 欠落試験は top-level exact-key 検査で赤になるため、この欠陥を検出できない。結果として、v3 構造の document が `"schema":"floor-pair-spec/v2"` を名乗っても受理される。
- **成果物影響**: candidate_floor の数値は同じ測定値なら変わらないが、受理集合が旧 schema 識別子を名乗る入力まで広がり、v2 spec に基づく window と summary が生成される。
- **確度**: 高。全テスト現物を確認し、誤った非空 schema 値を投入する負例が存在しないことを確認した。

- **id**: review-02
- **対象**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2588`、`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1686`
- **主張**: 3 role 構造の用語がエラー文言とテスト名に残っている。
- **具体例**: ある sample の第1 side session が droppable になった後、第2 side session の raw status を不正に `complete` とすると、finalizer は「落ちた標本の後続 role の因果が不整合」と報告する。現 schema に top-level role はなく、問題なのは後続 side session である。対応テスト名も `drops_remaining_roles` のままである。
- **成果物影響**: candidate_floor と受理集合の値は変わらない。不正 raw は従来どおり拒否され summary は生成されないが、診断とテスト台帳が旧構造を指す。
- **確度**: 高。限定検索で残存箇所を特定し、該当分岐へ到達する具体的な raw 状態をコード上で確認した。

## 所見が無い領域

- DW-M01 の M1からM8は、それぞれ四入力 D 計算、中間 probe の順序と汚染、reference 数、D 式、exact 2 measurement、plan による role 束縛、header の rep 定義を検査する試験へ対応している。恒真になる共通 helper 依存は review-01 を除いて見つからなかった。
- 差分で削除された test 定義はなく、改名された5件は旧 assertion を新しい2 side構造へ移していた。旧検査の脱落や明確な弱体化は見つからなかった。
- driver は `pre → 測定1 → mid → 測定2 → post` を実行し、3 probe のいずれかが非 clear なら complete にしない。finalizer も同じ因果を再導出する。
- `reps_per_session` は成果物から除去され、`reps_per_measurement` に置換されている。旧4 schema 識別子や単一 reference の成果物構造も残っていない。
- spec、plan、window、summary の版上げ、NOT_PROVEN 2行、callable 引数 seam を追加しないことを確認した。
- rep 単位の交互測定はない。各 `measure_point` が全 rep を完了してから次の candidate/reference 測定へ進む。
- `impl.diff` は `provenance.source_commit` 経路と runner を変更していない。既知の source_commit 不動点問題も裁定どおり未修正である。
- 現実装自体は spec v2 を拒否し、window header を exact 比較するため、現時点で旧版を直接受理する経路は見つからなかった。

## 総括

テスト防護の欠落1件と、旧3 role用語の取り残し1件を確認した。  
床値計算、2 reference、3 probe、schema出力の現実装に値を誤らせる欠陥は見つからなかった。  
テストは実走せず、指定資料と repo 内現物の静的照合のみを行った。