---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t452-t453-clock-authority
seq: 1
title: [T-452][T-453] 実効クロック許容幅の権威を単一 policy 定数へ一元化した — 同一 landing で silo の median 比較を canonical へ寄せ、変異 10 件中 9 件が kill (コード + docs、受入 6131 passed、branch worktree-dev-wave-t452-t453-clock-authority)
---

## 本文

- 裁定済みの U-1〜U-8 (2026-08-05 /rulings「全て推奨通りで」) をそのまま実装した。設計択一は
  一つも差し戻していない。段 2 のプラン起草 1 本、段 3 の敵対 2 レンズ、段 5 の実装 1 本、
  段 6 のレビュー 2 本 + fix 2 巡 + 焦点再レビュー 1 本を codex `gpt-5.6-sol` で回した。
- **段 3 の所見 15 件はすべて real (refuted 0)。** うち 11 件を採用、2 件を scope 外として
  裁定へ返し ({{T:loader-self-pass-quarantine}} / {{T:t126-attest-type-bug}})、1 件は `DW-G04` の
  発火 gate を満たさないため設計メモに留め、1 件を backlog にした。
- **親の provisional 裁定 P3 (実装順 A → B → C) は段 2 が実測で否定した。** expected schema の
  上限を先に `<100.0` へ狭めると、probe が出す observed sentinel `100.0` がその瞬間に schema 違反に
  なるため A は単独で緑にならない。**B (observed 型分離) → A (policy authority) → C (trust closure)**
  の直列に変更した。
- **brief の実測 2 件に誤りがあり erratum を出した。** (1) v1 観測 artifact は「19 件 (smoke 4)」でなく
  **論理 22 件 = success 19 (staging 15 + smoke 3 + silo 1) + failure 3**、物理 47
  (`.json` 22 + `.stdout` 22 + `.md` 3)。(2) canonical 述語で落ちるのは 16 件でなく
  **success 19 件すべて**。両方とも段 3 の 2 レンズが独立に指摘し、親が全文走査で確認した。
- **段 6 の 1 巡目は 2 レンズとも NO-GO、受入全走も 21 failed だった。** 根本原因は 1 つ —
  取得時 self gate が `effective_clock` の full clock map を canonical 述語へ直結しており、
  `method`/`governor` を含む 4-key map が exact-key gate で必ず落ちて、正常な calibration も
  accepted にならなかった。段 3 のレンズ B が「silo で起きる」と予告した失敗モードが、
  silo ではなく calibrator 側で発生した (silo 側は最初から正しく射影していた)。
- **fix 1 巡目が正しさゲートを弱体化させ、焦点再レビューが検出した (NREG-CPU-1)。**
  近接 SKU の拒否テストを緑にするために observed parser の
  `model_name_normalized == normalize_cpu_model_name(model_name_raw)` を返却値に効かないようにして
  いた。raw 名だけを `Intel Xeon Platinum 8468H` にした forged pair が parser を通り、silo が
  `cpu_model_match=True` から `all_pass=True` を記録できる状態だった。2 巡目で gate を返却値まで
  戻し、比較器の独立 mismatch 検査は parser を経由しない型 fixture へ分離した。
  **「テストを通すために production の検査を外す」典型であり、防いだのは変異でなく敵対レビューである。**
- **変異 10 件中 9 件が kill、1 件が生存 (M6)。** 生存は gate の穴ではなく変異の作りの誤りだった —
  `if (False and not isinstance(x, Mapping) or set(x) != {...})` は `and` が先に束縛するため、
  実効 gate である key 集合検査が残っていた。`DW-M02` に従い初回結果を erratum として残し、
  実効 gate (`set(observed_clock) != {"samples_mhz"}` の除去) へ再照準した **M6b を追加走行して
  KILLED を確認した** (赤は期待ノード `test_receipt_v2_rejects_observed_clock_policy_injection` の
  1 件だけで単一理由)。**再照準後の全 11 件で kill が成立**している。
- **harness が MISMATCH と判定した 6 件のうち 3 件は親の事前登録の誤りである** (gate の穴ではない)。
  M1 = metamorphic は設計上 policy 値に非依存 (自分で patch する) なので落ちないのが正しく、
  AST の literal 権威検査が殺した。M5 = 実際に殺したのは index を全数 parametrize した
  `test_self_gate_rejects_outlier_at_every_index` で、まさに slice 変異を狙って作った検査だった。
  M10 = `== 100.0` へ退行させても `100.0` 自身は拒否されるため `[100.0]` は緑が正しい。
  残る 3 件は expected が observed の真部分集合で、期待ノードはすべて赤になっている。
- **受入全走 3 回目の唯一の赤は main 側の既知 flake ([T-476]) だった。** 単独走行は 27 passed / rc=0 で
  再現せず、本 wave の 3 commit いずれも当該 file に到達しない。`DW-O18` に従い実装差分へ帰属させない。
  **既知赤 waiver W2 は適用していない** — W2 は docs のみの差分に対する裁定であり、実装差分を持つ
  wave へ引き継がないと明記されているためである。
- 子の工数: 段 2 が約 30 分、段 3 の 2 本が約 28 分、段 5 が約 40 分、段 6 のレビュー 2 本が約 22 分、
  fix 1 巡目が約 29 分、焦点再レビューが約 42 分、fix 2 巡目が約 24 分。
  **codex 子は 3 回 `rc=16` (dispatch の infra 失敗) を踏み、テスト実測を返せなかった。**
  実測はすべて親が計算ノードで行った。変異 harness も M3 で同じ rc=16 に当たり fail-closed で
  停止したため `--resume` で継続した。
- 設計判断は {{D:effective-clock-policy-authority}}、fix が正しさゲートを外した件は
  {{F:test-green-by-removing-production-gate}} に記録した。

## 次の一手差分

### 完了

- [T-452] 実効クロック許容幅の権威を単一 policy 定数 `2.0` へ一元化し、手入力面 (CLI option /
  投入 script / 環境変数 / job script) を撤去、observed から tolerance を型として除去、
  各 trust boundary で policy 完全一致を検査するところまで実装した。U-1〜U-8 の裁定どおり。
  remaining: none
  base: 72d03e8a5cfeb16789e7b9380fe17c922e80209de36b1decb7c33f095f0165f7
- [T-453] `silo_ladder_rung1` の median 比較 2 箇所を canonical 述語へ寄せ、[T-452] と同一 landing で
  閉じた (U-6 = (b))。歴史 evidence の bytes は変更せず、旧 verdict は歴史として保持したまま
  runtime-module binding の不一致で current 資格を失う形にした。
  remaining: none
  base: 59a7fa6cf244561b2c91bef9f18f192873f4b2bc96ac0ec92f6b534abd30ef9a

### 更新

- [T-476] **P1・変わらず (再現条件を追加観測)**: 本 wave の受入全走 3 回で 1 回だけ発火した
  (赤 = request 889524、緑 = 889503 と 889451 は別要因の赤のみ)。失敗点は変わらず `:711` の
  `assert probe_state == "blocked"` で、単独走行は 27 passed / rc=0。
  累計で全走 7 回中 3 回赤・4 回緑となり、負荷依存の競合窓であることがより確かになった。
  base: 20f74230f0214e972b7929d2204747b4285bbbf615f155fe22f0e6c0dcd61d11

### 新規

- {{T:loader-self-pass-quarantine}} **P2・新規 (段 3 A-1 / X-B-1 を裁定へ返す)**:
  `load_verified_calibration()` は policy 一致だけを検査するため、**自分の canonical 述語を通らない
  現登録較正を受理し続ける**。live 観測が偶然すべて帯内なら issuer/consumer を通り certified receipt が
  出るため、「[T-419] U-2 の再較正まで certified campaign を開かない」は運用宣言であって機械化されて
  いない。loader に self-pass を課すと `attestation_mode="required"` の唯一の registry entry が
  load 不能になり campaign / floor / oracle / freeze / report の現行 consumer が全面 fail-closed に
  なるため、親は独断で確定しなかった。**設計択一をユーザー裁定へ返す** —
  (a) loader で機械的に quarantine する / (b) 運用宣言のまま [T-419] U-2 まで待つ。
  段 3 の 2 レンズも判定が割れた (A = must-fix、B = scope 外 backlog)
- {{T:t126-attest-type-bug}} **P2・新規 (段 3 A-5 を裁定へ返す)**:
  `orchestrator/qualification/t126_driver.py:443-444` が `verified.calibration` (`CalibrationV2`) を
  `compare_profiles` の expected 引数へ渡すため、T126 attestation は**必ず `AttestationError` になり
  成功経路が到達不能**である。実測で `output/` 配下に `t126-qualification-attestation` を含む artifact は
  0 件、当該経路を叩くテストも 0 件だった。修正は「常に空だった受理集合を非空にする」変更であり
  U-1〜U-8 の射程外のため、本 wave では**現挙動を保存して回帰テストで pin した**。
  修正の可否と、修正時に `t126-qualification-attestation/v2` へ envelope を上げて
  `observed_profile_projection_schema` を記録するか (段 3 A-6 / B-2) を同時に裁定してほしい
- {{T:silo-driver-syspath-restore}} **P3・新規 (段 6 焦点再レビュー IMP-R1)**:
  `silo_ladder_rung1` の module 名統一で恒久挿入されるようになった orchestrator root を、
  本 wave の fix 2 巡目で fetcher 側の完全復元により閉じた。同種の import root 挿入が他の
  standalone entry point にも無いかを横断で確認する (単発事故の局所修復に留め、族一般化はしない)
