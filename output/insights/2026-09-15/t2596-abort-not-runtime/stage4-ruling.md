# 段 4 裁定 — [T-2596] CampaignAbort が測定側 except に飲まれる件

段 2 plan (`tmp/out/stage2-plan.md`) と段 3 敵対 2 本 (`tmp/out/stage3-sol.md`,
`tmp/out/stage3-luna.md`) を親が裁定した結果。**この文書が実装子への正本である。**

## 1. 採否の結論

**plan の最小差分とテスト 2 本を採用する。** 2 レンズとも「局所 2 行修正は成立する」で一致し、
停止伝播を覆す欠陥は出なかった。

```diff
             scale_point = self.measure_fn(
                 cell_id, attempt_id, binary, cell["records"], cell["threads"],
                 cell["workload"],
             )
+        except CampaignAbort:
+            raise
         except (RuntimeError, subprocess.TimeoutExpired) as exc:
             measure_error = exc
```

継承が `CampaignAbort → FloorCampaignError → RuntimeError` (C:360, C:408) なので、
節の**順序が必須**である。bare `raise` で元の例外オブジェクトを保つ。

## 2. (P1) 射程 — `CampaignAbort` だけを再送出する (確定)

2 レンズとも支持。既定の実装経路から非 `CampaignAbort` の `FloorCampaignError` は
対象 except に到達しない (予約段の C:7924 は対象 try の外)。
注入 callback が親型を投げれば到達しうるが、それは本 wave の局所修復を超える
(**real / scope 外**)。

## 3. (P2) β-7 — post-probe を走らせず即時送出する (確定。ただし根拠を差し替える)

結論は 2 レンズとも支持。**親の当初の根拠「admission abort は常に測定前だから post-probe は
不要」は退ける。** sol の指摘どおり、再送出は「callback が測定後に投げる abort」にも掛かるため、
この根拠では足りない。採用する根拠は次の 2 つ。

1. 失われる情報 (post-probe の競合有無) は、abort した実行を有効な測定へ戻す材料ではない。
2. post-probe (`strict_probe`) 自身が `CampaignAbort` を投げる (C:1711, 1713, 1717)。
   先に走らせると、そこで出た別の abort が元の停止理由を置き換え、
   C:7955-7961 が journal へ書く `terminal/status=aborted` の `reason` が失われうる。

**β-7 の全称表現 (C:33-34「measure が例外を投げた経路でも必ず」) との不一致は、
解釈上の未解消点として記録し、docs は変更しない (scope 外)。**

## 4. 親 brief の訂正 (real として採用)

| # | 誤 | 正 | 出所 |
|---|---|---|---|
| 1 | A3「非 certified 経路で該当する唯一の except」 | 「この measure 呼出しを包む except として唯一」。非 certified 経路全体の唯一ではない (runner 内にも捕捉がある) | sol・luna 一致 |
| 2 | A4「C:6334-6341」 | 条件行は **C:6333**、代入が C:6334。表が条件行を 1 行落としていた | luna |
| 3 | A7 の根拠を launcher:1400 に置いた | 決定的な根拠は **C:6259 の早期 return**。launcher:1400 は capture 例外の捕捉箇所にすぎない | sol・luna 一致 |
| 4 | A8「runner:963, 1184 が measure_point の起動失敗」 | **963 は `open_measurement_point` (定義 936)、1184 が `measure_point` (定義 1072)**。どちらも捕捉節で、plain RuntimeError の送出は 967 / 1188 / 1281 | sol・luna 一致 (親が現物で検算済み) |
| 5 | plan の `_run_certified_floor_session` 定義位置 C:8874 | **C:8889** (親が現物で検算済み)。呼出し C:8998 は正しい | sol |
| 6 | 「凍結 bytes の pin は無い」と断言 | 「**確認範囲で該当 pin 未発見**」。path・basename・行番号・source hash・glob を検索した範囲での結論であり、完全な不在証明ではない | sol |
| 7 | 「受理集合を変えない」 | 「**certified と最終 inspection の受理条件は不変。非 certified の実行継続条件は厳しくなる**」。これは意図した変更である | sol |
| 8 | 「retry 枠を消費して継続する」 | 可能な結果の説明であって、wrapper の全 abort について必ず成立する説明ではない。retry 発行は C:6170-6188 の admission verdict に依存する。**既に開始した retry の枠は abort 後も消費済みのまま**である (C:6123-6134 は session-start から使用済み ordinal を数える) | luna |

## 5. real だが scope 外 (実装しない)

- **族一般化しない。** 「どこで発生した `CampaignAbort` でも停止する」は成立しない。
  `runner.py:1184` や `s8b_floor_attempt_launcher.py:1400 / 1443` にも捕捉がある。
  ただし本件の 3 つの abort はその外側で起きる。DW-G03 は族一般化に独立 2 例を要求する。本件は 1 例。
- **注入 callback が非 abort の `FloorCampaignError` を投げる経路。** 現在も捕捉される。
  親型全体の扱いを変えるのは局所修復を超える。
- **wrapper 内の 3 つの拒否条件それぞれの到達性は本 wave の検査範囲外。** 負例は admission 通過後の
  callback abort を注入する。機構 (except 節の順序) は実体を通して検査できるが、
  3 条件それぞれのテストは足さない (ユーザー裁定「本題の修正だけ」)。
- **未特定の外部 report consumer 全体の保証。** 既存経路 (resume / checkpoint / liveness /
  artifact verify / report / 結果候補の列挙) に破損は見つからなかった。

## 6. 変異事前登録 (DW-M01。実装前に確定)

| ID | 変異内容 | 位置 | 期待して赤くなる node |
|---|---|---|---|
| M1 | 追加した `except CampaignAbort: raise` の 2 行を削除する | C:6283 の直前に入れた節 | 新設負例 `test_measure_campaign_abort_propagates_without_launch_failure` |
| M2 | 追加節を `except RuntimeError: raise` へ拡大する | 同 | 新設正例 `test_measure_runtime_error_records_launch_failure` **および既存 `test_post_probe_runs_on_launch_error_and_competing_takes_precedence`** |
| M3 | 追加節の bare `raise` の前に `strict_probe(self.probe_fn)` を実行する | 同 | 新設負例 (callback 到達後の probe 回数が 0 でなくなる) |

- **M2 の帰属**: luna の指摘どおり、既存テストが先に赤くなるため、全走の赤だけでは新設正例への
  帰属を示せない。**新設正例を個別指定した走行**で帰属を示す。
- M2 は DW-M01 が要求する「受理集合を縮小する wave の、承認外の過剰拒否の正例」を兼ねる。
- 登録から外す変異とその理由: freeze / binary / admission の入力を事前に壊す変異は先行 gate が
  必ず捕まえるため対象差分の証拠にならない。`FloorCampaignError` への拡大は本 2 本では殺せない。
- 実装後に F820 の単一理由性 (同じ入力を拒否する層が前後にも内側にも無いこと) を確認する。

## 7. 実装の範囲 (段 5 の所有)

- 編集してよい file は 2 つだけ。
  - `orchestrator/campaign/s8b_floor_campaign.py` (2 行の追加のみ)
  - `orchestrator/tests/test_s8b_floor_campaign.py` (新設テスト 2 本の追加のみ)
- 新設テストの配置は既存 `test_post_probe_runs_on_launch_error_and_competing_takes_precedence`
  (T:9885) の直後、次の parametrize decorator より前。
- 既存テストの期待値を変えない。反転・緩和・skip・削除を禁じる。
- certified 経路・`s8b_floor_attempt_launcher.py`・`orchestrator/calibrator/runner.py`・
  precedence の閉表 (`s8b_floor_stats.py`)・artifact schema・CLI・docs は触らない。
