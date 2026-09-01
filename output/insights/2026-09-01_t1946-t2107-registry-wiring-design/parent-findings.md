# 親の独立実測 — 段 2 plan の照合と、plan が引いていない既裁定

base = `2bf9cf387`。すべて本 worktree 内の静的検査。

## plan の主要所見のうち、親が独立に再現できたもの

| # | 所見 | 親の確認 |
|---|---|---|
| 1 | やり直し可能な失敗の集合が空 | `s8b_attempt_profile.py:395` `S8B_RETRYABLE_FAILURE_REASONS = frozenset()`。**再現** |
| 2 | ordinal > 0 は前終端が `retryable-failure` のときだけ開く | `attempt_registry_core.py:1081-1119`。`require_previous_terminal=True` と status 検査を確認。**再現** |
| 3 | 消費 marker の置き場所が食い違う | adapter は `root/"consumed"/…` (`s8b_attempt_registry.py:1458-1460`)、admission は `measurement-generation-consumed` dir (`s8b_holdout_admission.py:90`)。schema 文字列自体は両者とも `s8b-holdout-attempt-consumption/v1`。**再現 (食い違いは path 側)** |
| 4 | 回復権限の pin 集合は空 | `s8b_holdout_admission.py:109`。理由が同 file の直上コメントに明記。**再現** |
| 5 | 分類権限に production source が無い | `ClassificationAuthority(` の構築は test 6 箇所のみ。**再現** |
| 6 | slot 軸 | slot = `(freeze_holdout_key, configuration_id, repetition, attempt_ordinal)`、series = 先頭 3、budget = 先頭 2 (`s8b_attempt_profile.py:26-35`)。予算 cap 10 = `n_sessions 8 + retry_slots_per_cell 2` は protocol 実値と整合。**再現** |
| 7 | campaign の retry は cell-wide | `s8b_floor_campaign.py:6169-6187` `_retry_round` が `_next_retry_ordinal(cell_id)` で採番。registry の ordinal は (cell, repetition) 内。**再現** |

## plan が引いていない既裁定 (親が主題検索で発見)

**D880 (2026-08-25) が、所見 1・2 の不整合を既に記録し、別裁定へ回している。**

- D880 は床値 retry trigger を排他的二択に定めた。旧経路 = 同 cell/round の planned `session` が
  一意で `valid is False`。新経路 = attempt registry の検証済み recovery。
- D880 の理由節は「8b の retryable 集合は空なので `retryable-failure` の terminal を作れない。
  検証済み recovery は 8b で唯一の再走経路」と明記する。
- D880 の却下欄は「**registry の空 `retryable_failure_reasons` との不整合は既知で、別裁定へ回す。
  本 wave はその不整合を増やさない**」と書いている (`docs/decisions.md:32412`)。
- 回復権限の pin 集合を空にしたのも D880 の決定であり、「今日は発火しないをコードで強制する」ため。
  「scheduler accounting collector を作る作業がここへ登録する」と後続作業の所在まで指定している。
- campaign 側には既に `source == "verified-registry-recovery"` の分岐が実在する
  (`s8b_floor_campaign.py:6186-6188`)。D880 の新経路は campaign 側だけ配線済みである。

**含意:** 所見 1・2 は本 wave が発見した新しい欠陥ではなく、**D880 が意図的に残し別裁定へ送った
既知の不整合**である。したがって本 wave の裁定は「この不整合を解消する」ではなく
「**増やさない**形で配線できるか」を問うべきである。

## 未解決の設計上の問い (段 4 で裁定する)

床値 campaign は round 末尾に失敗 cell を retry する (`_retry_round`)。配線後、その retry は
registry の ordinal 1 以上を開こうとする。しかし前終端は必ず `terminal-failure` になるため
(所見 1・2)、registry が拒否する。すなわち:

- (i) 配線を planned attempt (ordinal 0) だけに限ると、正当な retry で campaign が止まる。
- (ii) retryable 集合を非空にすると D880 が別裁定へ回した判断を本 wave が先取りする。
- (iii) 旧 retry 経路を閉じると campaign の受理集合が変わる。

いずれも本 wave 単独では選べない。段 3 の 2 レンズの判定を待って段 4 で確定する。

## 追記 — T-1851 が本 wave の実装前提であることが判明 (親が主題検索で発見)

`output/insights/2026-08-27_t1851-floor-retry-ordinal-axis/s4-adjudication.md` が、
本 wave の配線を含む縦切りを既に設計している。

- **D1032 (ユーザー裁定, 2026-08-26)** が retry 軸の形を確定済み。
  「事前登録した別の試行番号軸を同じ耐久台帳の中に置き、性能量に到達する前に理由を固定する。
  受理する理由の集合を広げる場合も外部 scheduler の証拠が付いた場合に限る」。
- T-1851 の段 4 は、この「限る」が `S8B_RETRYABLE_FAILURE_REASONS` に掛かると読み、
  **理由が sealed な session record から機械的に導出されるなら「集合を広げる」に当たらない**
  (自由選択が存在しないため) と裁定した。所見 11 で「凍結 4 語を再利用せず台帳専用の閉じた語彙を持つ」
  ことも決めている。
- T-1851 の段 4 が次 wave へ引き継いだ骨格の**前半**が、本 wave の配線そのものである。
  逐語: 「前半 = legacy 統計的測り直しの縦切り 1 本。schema v2 + readable 方針、sealed な理由 authority、
  terminal 理由の再導出、二台帳の crash 整合、launcher / campaign 配線、final inspector / verifier
  までを同時に land する。planned attempt には既に production 呼び手があるため、死んだ gate にならない。」
  後半 = `verified-registry-recovery` 側は別 wave と明記されている。
- 同 wave の所見 12・13: 「実装子 1 本では閉じない」「規模見積もり 1,360-2,075 行は**下限**」。
- T-1851 の worklog 状態は「裁定済み (D1193/D1194) → 実装待ち」。

**含意:** T-2107 の配線は T-1851 の前半と同一の作業であり、T-1946 の束縛と合わせて 3 件が
1 つの land 単位を成す。設計はすべて裁定済みで、開いている設計択一は無い。
残るのは**規模**の問題だけである (T-1851 前半 1,360-2,075 行 + 本 plan の 600-900 行)。
