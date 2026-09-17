# 段 4 裁定 — [T-2757] mocc の auditor-live 相当の機械実証の設計

裁定者: dev-wave 親 (Claude)。入力: 親 brief、段 2 plan (codex read-only)、段 3 レンズ A (正しさ境界・恒真性) / レンズ B (実効性・整合)。
主 checkout main `38353207f` (段 4 直前に再確認、不変)。裁定 inbox: `docs/handoff/` に新規なし、`docs/spool/` に残 fragment なし。

## 1. plan の採否

**修正して採用。** hole 候補 = 温度述語 (4 site → file-scope helper の 1 hole) を「proof の接続先候補」として採用し、
正式な軸としての採用 (axis-onboarding 段階 A / B) は本設計で行わない (B1)。設計の主張を「既存防壁 (validation・CLL/RLL・X/P
計装) を骨格で固定し、その保存と発火範囲を検査する設計」へ限定し、「hot/cold は正しさの入力ではない」を定理として置かない (A1)。
後続は B 総括の 2 wave 分割を採用する。

## 2. 所見の裁定 (real / refuted、採用 / 不採用、scope 内 / 外)

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| A1 | F-b「torn read は validation で必ず捕まる」は版 (1010〜1013) と counter (1024) の別読みに観測間隙があり証明不成立 | **real、採用、scope 内** | F-b の還元主張と plan:33 の二分論証を撤回。cold 読みも 322 (counter) → 347 (body) → 350 (版) の順で、writer の施錠→memcpy→未 publish が重なると torn body を受理しうる。これは **stock mocc (RWLOCK 版) の性質**であり温度述語の hole とは独立。insight に「静的反例候補、実走未確認」として構造化し (CLAUDE.md 作業の進め方 4)、D2114 が未確定とする G2 anomaly 5/42 の**根因候補 (仮説)** として記す。実走検証は新規 T (下記) へ。親の現物確認: 322 / 347〜348 / 350〜352 / 1010〜1013 / 1024 |
| A2 | hot-update 負例の再取得は `rwlock_.w_lock()` 直接 (`TxExecutor::lock()` は stale CLL で省略され末尾 unlock が 0→1 を作る)、U の成立条件、timeout は失敗 | real、採用 | 設計へ明記。U = `ycsb_rratio=0, ycsb_rmw=false, ycsb_max_ope=1` が `Ope::WRITE` → `tx.update()` 直接呼出 (親確認 `include/ycsb.hh:65〜73, 128〜133`) で read_set_ を作らず 1 update/txn になる |
| A3 | hot 負例の発火は update 分岐の到達と X の歯だけを示す。read 側 hot 経路・RLL 再試行・候補ごとの型 4 は別 | real、採用 | 保証名を「stock 等価述語における hot-update 負例の到達と既存 X の検出」に固定。4 site 全被覆を今回必須にしない。read 側 witness は「設計上の選択肢 (未設計)」として残し要求しない (DW-G05) |
| A4 / B4 | P2 の鍵 (template / 軸 module 登録) は登録を通らない経路 (別配置 template、driver 直書き PIN・定数) を閉じない | real、採用 (限定つき) | gate = 「mocc の mutation consumer (loop driver) が実際に使う source / template / PIN と proof JSON の束縛を、consumer 導入時テストで必須検査する」+ 対照 3 種 (別名 template / 軸 module なし直接指定 / marker 導入済み別 PIN) が「拒否」または「同じ proof 要求へ到達」。**任意の直書き経路を機械的に閉じたとは主張しない**。既存 NON_ADMISSIBLE 診断経路 (T-2294 driver) と区別。汎用台帳・全経路解析は作らない (scope 外) |
| A5 | 契約違反 A/B は D48 型の弁別であり D38 点 5 (lockskip の独立検出) と同一視できない。DQ 拒否は DQ の positive control で auditor 実証に算入しない | real、採用 | n=1 定性を 3 候補に: A1' = 既存 lockskip patch の diff (正しさ違反型、D38 点 5 相当。DQ が先に拒否するが auditor の独立監査は別記録)、A2' = hole 内の `FLAGS_clocks_per_us` 読取 (契約違反型)、B' = `!(temp < threshold)` (benign)。fresh・read-only・入力射影・告白コメントなし |
| A6 | I 行を要求しない根拠を「許可述語の作用範囲と固定骨格」に置く。write-set 登録行 (477) 侵食を DQ 対照へ | real、採用 | P3 の根拠を書き換え。DQ 対照に 477 (write_set_ emplace) と 905〜913 (RLL 構築) の侵食を追加 |
| A7 | 過去実測と今回初めて要求する保証を分離。「全 cold」→「温度述語 false」。abort 0 は親の推論 | real、採用 | F-a の「1 thread は abort 0」を「単一 thread では競合が無く温度が上がらない、という code からの推論 (実測値ではない)」へ。旧 14 check は歴史的結果として保持し新保証に転用しない |
| A8 | 非解禁の文言は十分 | nit、採用 | insight と D fragment の両方に維持 |
| B1 | proof 用 template と正式な軸 A/B/C の境界が未確定 | **real、採用** | 上記 §1。証拠を「経路共通 (固定 producer 上の X/P、hot/cold、負例)」と「template 依存 (4 callsite、読取契約、DQ、identity、auditor A/B、template SHA)」に分ける。軸変更時は依存部分だけ再検証 |
| B2 | 同一性の比較対象 4 種と patch 積層順・`#line` 整合が未設計 | **real、採用** | 比較表 (無 template↔OFF = `src_token="stock"`、OFF↔ON-B = 別 identity + 実供給、同一 template 状態の計装なし↔あり = D1687 論理行列、旧 pin↔候補 = D297 別 T) を設計へ。計装 patch の `#line` は template 適用後の論理行に合わせて**再生成** (template 依存部分)。旧 instr patch SHA は旧 JSON の束縛のため不変で保持。D1687 の例外は TRACE 計装向けで、CC-native 骨格の承認根拠にしない |
| B3 | 36 走の期待表と check 集合が不一致。JSON 生成元 (argv・終了状態) の記録処理が新規 | **real、採用** | 各 run を「受入必須」「観測のみ」に二分し、必須 run → check の対応を全件表にする。observation-only の正数を要求しない。hang / 欠落 / 別 integrity 異常は赤。新 producer が argv・終了状態・`certified`・txn 数を記録。旧 JSON に無い field を旧証拠へ要求しない。`condition_gates` は実 producer の構造 (`supply` / `meaning` / `admission`) を参照 |
| B5 | 4 site 同一分類の契約明示。RLL / DELETE の未実証を表に | real、採用 | 契約 = 「4 site で同じ温度分類を使う」。効果・静的確認・動的確認の表を置く。再試行だけ独立政策にする案は別軸設計 |
| B6 | 費用の内訳。新 driver の特殊化 (`_require_condition_gate` の driver ID 固定、`_apply_owned_patch` の transaction 単独 touch) | real、採用 | build / trace+verifier 走 / condition gate / 変異 / 再走に分けて概算。template (Options.cmake も touch) は新 driver 側で 2 file touch を許し、負例 patch は transaction 単独のまま。旧 driver は変更しない |
| B7 | F-d は「現行 pin を前進させず実施可能」であって pin 非依存ではない。loop の PIN 説明を訂正 | real、採用 | F-d の文言を訂正。proof 用 OID (e9e477ca + patch SHA) と探索用の承認済み OID を別契約として記す。軸 module の PIN 方式は現行承認契約に従い `axis_trigger_gating.py` を機械転写しない |
| B8 | docs-only に価値あり。採用文を狭める。worklog は設計確定 / 実測未了 / 未解禁を区別 | real、採用 | 反映 |
| B 総括 | 2 wave 分割 (wave 1 = 経路共通の実証、wave 2 = template 接続の実証) | 採用 | wave 1 は template 不要で今すぐ投げられる。wave 2 は wave 1 + 軸の A/B を前提 |

refuted: なし。親 brief の誤り (段 3 が訂正): F-b の一般化 (A1)、「同じ鍵では恒真」は前件が常時 true であって含意全体の恒真ではない (A4 注、plan:217)、「pin 非依存」(B7)、「全 cold」(A7)、P4 の `thid_`/`result_` 負例は file-scope helper では未宣言識別子になる (plan)。

## 3. plan v2 (設計の骨子 — insight へ展開)

1. 位置づけと非解禁 (D579 / D2114 項 3 / D1373 不変。proof 完了も探索の認可ではない)。
2. 既存証拠 (T-2294 / D1686) と今回の純増。過去実測と新保証の分離 (A7)。
3. 現物検算と安全論拠の限定 — F-b 撤回、観測間隙 (A1) と absent 非対称 (plan) を静的反例候補として構造化。
4. hole 候補比較と採用案 (proof 接続先候補、正式軸ではない、B1)。
5. template と読取契約 (4 site 同一分類、B5) — 実装 wave 2 の要件。
6. hot 専用負例 (balanced、`rwlock_.w_lock()` 直接、U workload) と実行証拠の保証名 (A2/A3)。
7. 実証 matrix (36 走) と check 契約 — 受入必須 / 観測のみの二分 (B3)、JSON schema、producer の記録処理。
8. 同一性の比較表と patch 積層順 (B2)。
9. auditor 入力 (mocc 節の 5 分類、既存型番号の mocc 説明) と n=1 定性 3 候補 (A5)。
10. mutation 面の gate — consumer 束縛検査 + 対照 3 種、閉じないことの明記 (A4/B4)。
11. I・P・pin の境界 (A6/B7)。
12. 実装成果物・登録箇所・費用 (B6)、2 wave 分割と各完了判定。
13. 未確定事項 (実装時確認) と scope 外。

## 4. 変異事前登録

実装面の差分ゼロ (docs-only) のため変異 matrix は免除 (DW-S04)。受入全走は免除しない。

## 5. 成果物

- `output/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md` + `verbatim/` (brief、plan、レンズ A/B、本裁定、prompt 3 本、MANIFEST.json)
- `docs/spool/decisions/2026-09-17-dev-wave-t2757-mocc-mutation-proof-design-2.md` ({{D:mocc-mutation-proof-design}})
- `docs/spool/worklog/2026-09-17-dev-wave-t2757-mocc-mutation-proof-design-1.md` ([T-2757] 完了、新規 T 3 本: wave 1 実証 (P1)、wave 2 template 接続 (P1、前提つき)、stock 観測間隙の実走検証 (P1))
- `docs/phase3.md` は編集しない (準備 T の進捗は worklog 末尾が正本、B8)
