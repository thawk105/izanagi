## 総括

**real 2件。現状は受入未完了です。** 親ログは baseline 108 passed、焦点走 **117 passed / 2 failed**。本レビューではテストを起動していません。

**real**

- **P2 — `orchestrator/tests/test_backoff_sweep.py:140`**
  `prepare` の模擬実装が admission policy 未束縛の cfg を返すため、両ケースとも campaign identity 計算で停止します。**影響：候補 raw3000 の意味状態を検査できず、候補への宣言転送欠落を検出する証拠になりません。** 最小修正：実処理と同じ `ident.bind_admission_policy(cfg, kwargs["build_context"].policy)` を模擬準備へ追加し、期待値を維持して再走する。

- **P2 — `docs/b10-backoff-static-tail-preregistration.md:1095`**
  §5 の status を「旧探索走についての記述」としていますが、§5 は本格 cohort 用の機械可読 spec 正本です（同:444、同:465、同:623）。**影響：本格系列の規範 field の参照対象を旧探索走へ誤って読み替えます。** 最小修正：追補のこの文だけを「§5 の本格系列 spec は変更対象外として保持し、T2418 新走の status は本追補に従う」と直す。

**refuted**

- **author 無し実装ハンク**：code/tests 6ファイルの diff は `author.patch` と bytes 単位で一致。親変更は追補のみ。
- **旧出力の上書き・遡及昇格**：`backoff_extended_sweep.py:675` の v2 slug を同:1026 の loader が使用し、同:1264 の出力先も選択 campaign 配下。v1 fallback はなく、旧 output は diff 対象外。追加 create-only テストは不要。
- **metadata 不一致**：同:95、同:643、同:683 と JSON/DAT の共通 status 参照は v2 で整合。
- **共通 gate 緩和・乱択の静的化**：`screening_driver.py:228` は BACKOFF_FIXED へ既存宣言を転送するだけ。共通 gate は未変更。
- **既存 literal・歴史本文の変更**：s1 の 5/10/2、paper A2 の 10/5 は維持。事前登録の既存 bytes は追補前の prefix と完全一致。

変異結果は未確認であり、静的所見や焦点走を全受入・本走の証明へ一般化できません。