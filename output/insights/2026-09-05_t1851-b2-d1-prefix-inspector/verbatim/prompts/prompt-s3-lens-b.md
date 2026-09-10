単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md` — 親 brief。**これ自身も検査対象である。**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md` — 段 2 plan。**守らずに攻撃する対象である。**
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md` — 確定裁定 11 件の逐語
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/s2-plan-v2.md` — 設計 wave の plan v2 (「単位 B」「単位 D」節と「赤になる既存 test」節)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/s4-adjudication-r2.md` — 設計 wave の 13 blocker と 6 段分割
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/a1-README.md`、`refs/a2alpha-README.md`、`refs/a2beta-README.md` — 直前 3 wave の規模実測 (2 wave 連続で見積りが下振れした) と閉じていない窓

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a`、HEAD `50dbf9158`。コードはすべてこの worktree の中を読む。

## レンズ B — 規模・所有・consumer 漏れ・変異の帰属

plan と親 brief を、**実装可能性・所有範囲・既存 test への波及・変異の帰属**の観点で攻撃せよ。plan の推奨を採用するかどうかは問わない。次を必ず検査する。

1. **規模の実測の検算。** plan の依頼 1 の表 (production 行数、test node 数) を現物で数え直せ。特に `result_keys_for_mode` の 22 呼出し、`RESULT_SCHEMA` を参照する production 6 file / test 5 file、`verify_floor_artifact` と `verify_floor_artifact_with_live_admission` の呼び手 (production / test / fixture)。plan が数え落とした consumer を全件列挙せよ。A1' / A2α では見積りが約半分に下振れした — 同じ型の下振れが無いか。
2. **所有範囲の漏れ。** plan の変更 file が本 wave の編集面 (s8b_attempt_registry / s8b_holdout_admission / attempt_registry_core / s8b_floor_contract / s8b_floor_stats とその test) を越えて単位 C (`s8b_floor_campaign.py`) や D2 (`s8b_holdout_freeze.py` / `s8b_ratified_freeze.py`) の file に触れていないか。触れる必要があるなら、それは本 wave の scope 外であり分割の再考が要る。fixture (`s8b_v2_freeze_fixture.py`、`s8b_floor_evidence_fixture.py`) 経由の transitive 赤を現物で追え。
3. **既存 test の赤の列挙。** plan の依頼 2-7 の赤リストを検算し、supersede してよい pin / してはならない pin (`test_s8b_floor_contract.py:180`、`test_s8b_floor_stats.py:596,1323-1325`、A2α の S5 / S6 pin、A1' の v2 空集合 pin) の分類が正しいか。
4. **(P2) の import 関係。** `s8b_attempt_registry` → `s8b_holdout_admission` → `s8b_floor_stats` の import 方向を現物で確かめ、plan の inspector 置き場所が循環 import・遅延 import・test の monkeypatch 到達性のどれを生むかを示せ。
5. **(P3) の到達可能性。** v2 世代に現在積める行 (genesis、reservation、classification、consumption marker) を `reserve_attempt_slot` と A2α の S11 / S12 の現物で確かめ、prefix inspector の正例 (N >= 2、chain が 1 本以上進んだ状態) が test 内で組めるか。組む手順に単位 C の carrier や E1 の validator が要るなら、それは本 wave の正例が genesis-only に退化することを意味する — その場合の変異の帰属 (M-chain 系の KILLED が本当に観測できるか) を評価せよ。
6. **変異事前登録候補の帰属。** plan の依頼 3 の各候補について「他の gate が同じ入力を拒否しない」が本当か。上流の exact key 検査や既存 `_assert_chain` が先に拒否して変異が SURVIVED になる候補を全件挙げ、再照準案を書け。
7. **1 wave に収まるか。** 実装子 1 本 + fix 3 巡以内で、テスト node の追加・既存赤の修正・変異 matrix・受入全走が収まるか。収まらないなら plan の分割案を検算し、代案があれば 1 つに絞れ。
8. **親の実測値とその一般化。** brief の実アンカー表の行番号、DW-O09 節の件数、「両親が共に触った file 0」「main 側の実装面変更が編集面に交差しない」を現物で検算せよ。

## 出力形式

所見ごとに `所見 N` の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか 1 行、(d) 修正案、(e) 親 brief の (P) 番号との対応、を書け。各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。scope 外だが real な所見は「裁定パッケージ候補」として別節にまとめろ。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker 件数、must-fix 件数、規模判定、(P1)〜(P6) の独立評価を 10 行以内で書け。
