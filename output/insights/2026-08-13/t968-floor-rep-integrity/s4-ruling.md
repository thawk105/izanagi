# 段 4 — 親の裁定と plan v2 ([T-968])

判定日時: 2026-08-13 02:31 JST / base commit `01487bb4`

## 0. 全体裁定

段 2 の第 3 案 (rep 証跡 `rep_observations` を保存し、完備な rep の tps だけを統計入力へ射影する
二層設計) を **採用**する。ただし段 3 の両レンズが挙げた must-fix を plan v2 へ全件取り込む。

**受理集合の性質 (レンズ A #2 への裁定):** 本 wave は統計式を一切変えない。
`FORMULA_ID = s8b-floor-stats/v2`、`assess_session`、cell 集計、CV 判定、閾値は 1 行も触らない。
変わるのは「統計へ入る rep の集合」であり、これは wave 前は**そもそも検査されていなかった**。
受理集合は**縮む方向のみ** (壊れた rep を含む session が invalid になる)。
`protocol` / `formula` の改版と人間による再 seal は行わない。同一 protocol hash で受理集合が
違って見える問題は、`RESULT_SCHEMA` / `JOURNAL_SCHEMA` を v3 にすることで artifact 側に刻み、
consumer が識別できるようにする。**ユーザー再裁定は不要**と判断する — ユーザー裁定
「採用 (除外区分の追加で)」は定義上、受理集合を縮める変更を認めている。
ただし DW-M01 に従い、**承認外の過剰拒否を検出する正例**を変異事前登録に必ず含める。

## 1. 所見の裁定表

| # | レンズ | 所見 | 判定 | 扱い |
|---|---|---|---|---|
| A1 | A | `s8b_holdout_freeze.py` は `holdout_freeze.json` の `generator` として sha256 `1910fff3…` で pin されており、編集すると凍結閉包を壊す | **real (親が裏取り済み)** | 採用。**同 file を編集面から外す。** 1317 行の比較は `s8b_floor_contract.RESULT_SCHEMA` を参照しており診断文だけが "v2" なので機能変更は不要 |
| A2 | A | formula v2 のまま受理集合が変わる点に明示裁定が要る | real | 採用 → §0 で裁定 |
| A3 | A | verifier に信頼できる `use_perf` 入力が無く、`not_required` 詐称が通る | **real (親が裏取り済み: official は receipt=None 必須で `use_perf_from_receipt(None)=True`)** | 採用。`verify_floor_artifact` に `expected_use_perf` を**必須引数**で追加 |
| A4 | A | `counter_status` と `missing_perf_events` の矛盾が検出されない | real | 採用。status は missing 列と `expected_use_perf` から一意再導出し、申告値は照合対象にする |
| A5/B2 | A+B | 証跡 carrier が未設計で、production 結線だけが未検査になる | real | 採用。`ScalePoint` に optional 証跡 field を持たせ、既定 closure で journal まで届く結線テストを足す |
| A6 | A | v2 journal の一括拒否は測定前 resume まで禁じる過剰縮小 (F82 型) | real | 採用。拒否境界を「`session-start` か `session` が 1 件でもある journal」に限定し、測定前 v2 → v3 transition の正例を足す |
| A7 | A | counter 値が負・`inf` でも complete になる | real | 採用。完備条件は `type(v) is int and v >= 0`。`OverflowError` は欠損へ正規化 |
| A8 | A | `PATH` 先頭の偽 `perf` で完備性を operator が on/off できる | **real だが scope 外** | 実装しない。T-967 / T-970 (F89 未裁定) の領域。**裁定パッケージ候補として返す。「T-968 単独で operator 制御の除外を閉じた」とは報告しない** |
| A9 | A | `competing_process` 自己申告で任意 session を捨てられる | **wave 前から在る穴、scope 外** (`s8b_floor_stats.py:182-184` が F7 wave の責務と明記) | 悪化させないことだけ本 wave の義務とする: **measure が完了した session は competing/launch を主張しても rep 証跡の提出を免除しない。** 証跡なしを許すのは pre-probe skip と measure 例外だけ。残余は裁定パッケージへ |
| B1 | B | `rep_returncodes` の append は例外・timeout の rep でずれる | real | 採用。reps 分を事前確保した indexed record に、成功・timeout・例外・未知を必ず格納。sink 指定時は `subprocess_runner` を常に同じ seam へ渡す |
| B3 | B | perf parser は欠損値で既存値を消さず、重複行で complete に化ける | **real (親が裏取り済み: `perfparse.py:72-76` は `val is not None` のときだけ setattr)** | 採用。event ごとの raw 値を証跡に保存し、有効値と欠損値の混在・重複を不整合として扱う。verifier は status を信用せず raw から独立再導出 |
| B4 | B | positive control が production の runner / parser を通らない | real | 採用。positive control は既定の `measure_point` 経路を使い、**実 subprocess だけ**を差し替える。期待値はリテラル固定 |
| B5 | B | `int()` / `bool()` 変換が不正証跡を成功へ変換する | real | 採用。`type(x) is int` かつ非負、bool 除外。既定値で「違反なし」を表さない |
| B6 | B | precedence テストが pre-probe competing / measure 例外を使うと先取りで帰属不成立 | real | 採用。実測完了 + 証跡ありの session に **post-probe** competing / launch を注入する。検査対象は reason 文字列でなく `valid` / median / cell 投影 |
| B7 | B | v2 resume 変異の期待 node が schema 検査に先取りされる | real | 採用。v2 version reject は独立テスト。新設 field の検査は schema v3 + observation 欠落 journal で行う |
| B8 | B | `s8b_ratified_freeze` の re-projection 更新漏れで正しい v3 artifact が拒否される | real | 採用 (ただし A1 により `s8b_holdout_freeze.py` は除外) |
| B9 | B | `exclusion_class` だけの変異は受理集合を変えない (F86 型) | real | 採用。変異表から外し、診断テストとして分離 |

## 2. plan v2 — 確定した編集面

**編集してよい:**
- `orchestrator/calibrator/runner.py` (rep 証跡の収集 seam)
- `orchestrator/calibrator/model.py` (`ScalePoint` の optional 証跡 field)
- `orchestrator/campaign/s8b_floor_campaign.py` (射影・precedence・journal/result・resume)
- `orchestrator/campaign/s8b_floor_stats.py` (`SessionRecord`・verifier)
- `orchestrator/campaign/s8b_floor_contract.py` (`RESULT_SCHEMA` / `JOURNAL_SCHEMA` を v3 へ)
- `orchestrator/campaign/s8b_ratified_freeze.py` (exact key consumer の追随)
- 上記の対応テスト

**編集してはならない (no-touch):**
- `orchestrator/campaign/s8b_holdout_freeze.py` (**凍結 generator pin**, A1)
- `orchestrator/campaign/s8b_approved.py` / `s8b_experiment_numbers.py`
- `s8b_floor_stats.ALLOWED_EXCLUDED_REASONS` (4 件・固定順)
- `s8b_floor_contract._APPROVED_REASONS` (4 件・固定順) と `validate_protocol` の pin 検査
- `s8b_floor_campaign.py` の protocol builder が書く `allowed_excluded_reasons`
- `FORMULA_ID` / `PROTOCOL_SCHEMA` / `MANIFEST_SCHEMA`
- `output/` 配下の全 artifact (特に `s8b-freeze/` の 2 file)
- `orchestrator/calibrator/perfparse.py` の parser 本体
  (**証跡は raw を保存する側で持ち、parser の意味論は変えない**。既存 consumer への波及を避ける)

## 3. 不変条件 (実装子への拘束)

1. **規律 2:** 除外の発火条件は rc と counter 完備だけ。throughput / median / CV / 値の大小を
   条件に入れてはならない。raw tps は証跡保存と既存 partial / performance 判定にだけ使う。
2. **fail-closed:** 証跡欠落・`unknown`・型違反・件数不一致・index 重複は、すべて違反側へ倒す。
   既定値 (`0` / `[]` / `None`) が「違反なし」を意味する経路を作らない。
3. **session 全体無効:** 1 rep でも違反があれば、残りの良い rep だけで median を作らない。
4. **precedence:** competing → launch → rep integrity → partial → performance → valid。
   ただし measure が完了した session では、competing / launch でも証跡の提出を免除しない。
5. **凍結不可侵:** §2 の no-touch を 1 byte も触らない。

## 4. 変異事前登録 (DW-M01)

`DW-M03` に従い、**受理集合か fail-closed 挙動が期待方向へ変わる変異だけ**を登録する。
診断文字列だけの赤は kill に数えない。`exclusion_class` 表示のみの変異 (B9) は登録しない。

### negative 層 (検査を無効化する変異 — 赤になるべき)

| ID | 変異位置 | 変異内容 | 落ちるべき node |
|---|---|---|---|
| M1 | `s8b_floor_campaign.py` 射影 | **wave 前の実コードの形**に戻す (`throughputs = [float(t) for t in scale_point.throughputs]` の無条件コピー) | positive control (production 経路) |
| M2 | 同上 | 違反 rep だけを除き、残り rep で median を許す | positive control |
| M3 | `runner.py` rc 収集 | 例外・timeout の rep の record を格納せず、成功分だけ append する (B1 の壊れた形) | runner の rc 整列テスト |
| M4 | rep 完備性判定 | 4 event の `all` を `any` にする | perf event 欠落テスト (event ごとに parametrize) |
| M5 | 同上 | 完備条件から `v >= 0` を外す (負値を許す) | 負値 counter テスト |
| M6 | 同上 | `unknown` を違反でなく良好として扱う | 証跡欠落 fail-closed テスト |
| M7 | precedence | partial を rep integrity より先に評価する | precedence テスト (post-probe 注入版) |
| M8 | verifier (a) | 証跡 / count / qualified tps の突合を削除し wave 前の検査だけに戻す | verifier (a) テスト |
| M9 | verifier (b) | 申告 `rep_integrity_failures` を再導出せず信用する | verifier (b) テスト |
| M10 | verifier | `expected_use_perf` 検査を外し `not_required` を無条件で良好にする | perf-required 文脈の `not_required` 拒否テスト |
| M11 | verifier | `counter_status` を `missing_perf_events` から再導出せず申告値を信用する | status / missing 矛盾テスト |
| M12 | 型検査 | `type(x) is int` を `isinstance(x, int)` に緩め bool を通す | 型違反 fail-closed テスト |
| M13 | resume | schema v3 の observation 欠落を count 0 で補う | v3 observation 欠落テスト (v2 version reject とは別 node) |

### positive 層 (過剰拒否を検出する正例 — 緑のままであるべき)

| ID | 検査対象 | 内容 |
|---|---|---|
| P1 | no-perf pilot | `use_perf=False` の全 rep が `not_required` + rc 0 のとき session が **有効**であること |
| P2 | 測定前 v2 resume | `session-start` / `session` を 1 件も持たない v2 journal からの resume が **通る**こと (A6) |
| P3 | 正常 official | 全 rep が rc 0 かつ 4 event complete のとき session が **有効**で median が cell に入ること |
| P4 | counter 値 0 | counter 値が `0` の rep は「取得済み」であり **complete** と扱われること |
| P5 | 非 floor consumer | `measure_point` を証跡 sink なしで呼ぶ既存経路 (calibrator sweep 等) が **無影響**であること |

### 単一理由性の確認 (DW-M01)

- M1 / M2 は positive control が唯一の落ち先。既存 partial / CV gate は
  `[100, 100, 101, 103, 103]` の入力に対して**初めから発火しない**ので前後の層に mask されない。
- M7 は post-probe 注入版でのみ帰属が成立する (B6)。pre-probe 版は使わない。
- M13 は v2 version reject と**別 node** にする (B7)。
- M4 は event ごとに parametrize し、1 event 欠落でも落ちることを個別に示す。

## 5. 段 5 の分割

実装面は 1 単位 (編集面が相互依存しており分割すると patch 衝突が確実)。
Codex `role=author`、`sandbox=workspace-write`、`reasoning=high` を 1 本。
