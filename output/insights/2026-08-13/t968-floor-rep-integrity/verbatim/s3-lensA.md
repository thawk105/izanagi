[severity: must-fix]  
[攻撃シナリオ: プランどおり `s8b_holdout_freeze.py` の v2 固定エラーメッセージだけを編集 → hold 中は検査が保留されるため見逃す → hold 解除時に active v1 freeze の generator hash が不一致となり拒否される。実際、凍結記録 `1910fff3…` に対して現行 bytes は既に `2204ac5e…` であり、追加編集は閉包をさらに変える。]  
[根拠: s2-plan.md:103; output/s8b-freeze/holdout_freeze.json:1; orchestrator/campaign/freeze_verification_hold.py:14-25; orchestrator/campaign/s8b_holdout_freeze.py:870-891,939-950,1315-1318]  
[提案: `s8b_holdout_freeze.py` を編集面から外す。1317 行目は imported `RESULT_SCHEMA` で既に v3 を受理でき、変更対象は診断文だけである。診断文更新は hold 解決・再凍結裁定と同梱する。]

[severity: must-fix]  
[攻撃シナリオ: 同じ seal 済み protocol bytes・同じ `FORMULA_ID=v2`・同じ raw benchmark 出力を旧実装と新実装へ渡す → counter 欠落 rep の採否が変わり、一方だけ session median が成立する。protocol hash だけを見る consumer には異なる受理集合が同一契約として見える。]  
[根拠: output/s8b-freeze/floor_protocol.json:1; orchestrator/campaign/s8b_floor_stats.py:16-18,158-191; s2-plan.md:28,98,184]  
[提案: 段 4 で「既存 formula の実装是正」なのか「受理集合を変える新 formula」なのかを明示裁定する。前者なら result/journal v3 を acceptance-contract version として proof chain に固定し、後者なら protocol/formula 改版と人間による再 seal が必要である。bytes 不変だけで凍結安全と結論しない。]

[severity: must-fix]  
[攻撃シナリオ: official result、または perf-enabled pilot の全 observation を `returncode=0, counter_status=not_required` とする → プラン上は complete/not-required を良好値として再導出するが、verifier には信頼できる `use_perf` 入力がない → counter を一件も採れていない session が有効になる。]  
[根拠: s2-plan.md:53-60,107-119,140; orchestrator/campaign/s8b_floor_stats.py:403-408,434-484; orchestrator/campaign/s8b_floor_campaign.py:2625-2644,2762-2763; orchestrator/campaign/s8b_holdout_freeze.py:1317-1321]  
[提案: `verify_floor_artifact` に必須の `expected_use_perf` を渡し、campaign は正規化済み receipt、ratified/holdout official consumer は `True` から供給する。perf-required 文脈の `not_required` を拒否する正例・負例を追加する。protocol bytes の変更は不要である。]

[severity: must-fix]  
[攻撃シナリオ: observation を `counter_status=complete, missing_perf_events=["cycles"]` とする → status と subset はそれぞれ合法で、failure count は status だけから 0 になる → cycles 欠落 rep の tps が median へ入る。逆向きの `incomplete + []` も都合のよい除外に使える。]  
[根拠: s2-plan.md:34-40,53-58,107-119,129-140]  
[提案: `counter_status` を `missing_perf_events` と `expected_use_perf` から一意に再導出し、申告値は照合対象にする。全 status と missing-list の矛盾を拒否する verifier テストと変異を事前登録する。]

[severity: must-fix]  
[攻撃シナリオ: `measure_point` が opt-in sink を正しく埋める一方、従来どおり bare `ScalePoint` を返す → floor closure もその値だけを返す → `_Runner._project_scalepoint` に sink が届かず全 observation が unknown になる。runner 単体テストと observation 付き fake campaign テストは双方緑になり得るため、production 結線だけが未検査になる。]  
[根拠: orchestrator/calibrator/model.py:54-73; orchestrator/campaign/s8b_floor_campaign.py:2381-2393,3418-3429; orchestrator/tests/test_s8b_floor_campaign.py:399-460; s2-plan.md:42,64-69,125,154-157,180-181]  
[提案: optional field を持つ `ScalePoint`、または floor 専用の型付き戻り値として carrier を明記する。実際の default closureで、spy `measure_point` が sink を埋めて bare point を返し、その証跡が journal まで届く結線テストを追加する。]

[severity: must-fix]  
[攻撃シナリオ: v2 journal が campaign-start 直後で、session-start/session がまだ一件もない状態から resume → 復元不能な旧測定は存在しないのに schema 一括拒否で落ちる。これは正当な resume 経路の過剰縮小であり、「全 v2 は証跡を復元できない」という一般化が偽である。]  
[根拠: s2-plan.md:9,96-101,134,174,183; orchestrator/campaign/s8b_floor_contract.py:405-448; orchestrator/campaign/s8b_floor_campaign.py:3593-3604]  
[提案: v2 を拒否する境界を「session-start/session が一件でもある journal」に限定する。測定前 v2 には明示的 v3 transition を定義し、その正例を追加する。混在 schema を許さない裁定なら、受理集合変更としてユーザーへ返す。]

[severity: should-fix]  
[攻撃シナリオ: perf CSV の4 eventをすべて `-1` とする → `_to_int` は負値を int として採用し、全属性が非 None なので `complete` になる → 実在しない counter を持つ rep の tps が有効化される。また `inf` は `OverflowError` となり、予定した incomplete 分類ではなく campaign 全体を非構造化停止させる。]  
[根拠: orchestrator/calibrator/perfparse.py:47-56,59-76; orchestrator/calibrator/runner.py:461-486; s2-plan.md:51]  
[提案: counter 完備条件を exact int かつ 0 以上とし、`OverflowError` も欠損へ正規化する。負値・inf・不正指数表記の positive control を追加する。]

[severity: should-fix]  
[攻撃シナリオ: operator が `PATH` の先頭へ別の `perf` を置く → preflight と benchmark はともに literal `perf` を実行し、policy candidate は evidence にしか使われない → wrapper の出力次第で counter 完備性を on/off できる。official permit 解除後も perf の realpath/hash は toolchain binding に含まれない。]  
[根拠: orchestrator/calibrator/runner.py:325-335,376-379; orchestrator/calibrator/perf_preflight.py:88-133,249-258; orchestrator/campaign/s8b_floor_campaign.py:204-216,228-237,1184-1209,3194-3215; brief.md:9-10]  
[提案: scope 外の real 所見として T-967 の裁定パッケージへ送り、official enable の必須依存にする。実行した perf の realpath・identityを固定しない限り、T-968 単独で operator-controlled exclusion を閉じたとは報告しない。]

[severity: must-fix]  
[攻撃シナリオ: 完備で低い tps の session を `excluded_reason=competing_process`、`probe_before/probe_after=null`、`valid=false` に書き換え、result 側も同じ journal から再生成する → ratified verifier は probe が null なら何も検査せず、stats も competing/launch の自己申告を信頼し、プランも precedence 例外として integrity 証跡要求を外す → 任意 session を捨てて retry を選べる。]  
[根拠: orchestrator/campaign/s8b_floor_stats.py:398-402,518-545; orchestrator/campaign/s8b_ratified_freeze.py:1906-1913,2220-2262; s2-plan.md:72-81,90,112]  
[提案: pre-probe skip、post-probe competing、measure launch error を別状態として機械導出する。ratified verifier で保存 rc/stdout/stderr を共有 classifier に再投入し、reason・precedence・証跡の有無を照合する。別 wave が必要なら「scope 外の real 所見」として裁定へ返し、certified closure を主張しない。]

## 総括

- protocol の4理由 pin 自体を維持する判断は正しいが、`s8b_holdout_freeze.py` という逆向き source pin を見落としている。

- 最大の correctness blocker は、verifier が perf-required 文脈と status/missing の相互関係を独立確定できない点である。

- observation sink の production carrier が未設計で、分割テストだけでは結線欠落を検出できない。

- v2 journal の一括拒否は、測定前 resume まで禁止する F82 型の過剰縮小である。

- formula/protocol v2 を維持したまま受理集合を変える点は、段 4 で明示裁定が必要である。

- perf identity と competing/launch 真正性は scope 外にも残る real 所見であり、official 化前の依存として扱うべきである。

- 検査は base `01487bb4` の静的確認のみで、pytest・build は実走しておらず、緑の主張はない。