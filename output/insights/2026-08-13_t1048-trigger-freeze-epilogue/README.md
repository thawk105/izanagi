# [T-1048] trigger-gating の凍結領域を post-END の gated call まで拡大した — wave 記録

branch `worktree-dev-wave-t1048-trigger-freeze-epilogue` / 2026-08-13 17:15 〜 (JST)。
ユーザー裁定 = 2026-08-13 rulings 第 10 回 #5 の **(b)**。設計正本 =
`output/insights/2026-08-13_t897-trigger-admission/README.md` の RP-2。

## 何を直したか

build gateway の trigger axis 検査は EVOLVE-BLOCK の BEGIN..END しか見ておらず、**END の直後 1 byte も
検証していなかった。** T-897 が残した R2 (block 外での `izanagi_gate_pass` 再代入) は、END 行末と
gated call の間へ 1 行差し込むだけで成立した。

END 行末の直後に凍結 epilogue が**隣接**することを、受理条件へ論理積で足した。

```
#if BACKOFF_TRIGGER_GATING
  if (izanagi_gate_pass) {
    Backoff::backoff(FLAGS_clocks_per_us);
  }
#endif
```

patch 由来の逐語 108 bytes を `axis_trigger_gating.FROZEN_TEMPLATE_EPILOGUE_BYTES` として置き、
`patches/silo-backoff-trigger-gating-variant.patch` との一致を独立テストで固定した。

## 変更後の受理言語

marker がある source は、次を**すべて**満たすときだけ受理する。

1. BEGIN と END が各 1 件だけ存在し、BEGIN が END より前。
2. BEGIN 行頭から END 行末までの block が pristine (`FROZEN_TEMPLATE_BLOCK_BYTES`) か、
   hole 1 行だけ異なり その hole が `PREDICATE_HOLE_INDENT + emit_predicate(TriggerGateIR(mask))`
   (mask 0..31) と exact 一致する形。
3. **`raw[END.end() : END.end() + len(E)] == E`。**

**epilogue より後の bytes は凍結しない。** 後続空行・`#if ADD_ANALYSIS`・その他の正当な後続コードは
受理する。source 不在 (`FileNotFoundError`)、marker も skeleton token も無い source (stock) の
受理も従来どおりで、三分岐は変えていない。**受理集合は狭くなるだけである。**

## 閉じたもの、閉じていないもの

**閉じたのは「END 行末と gated call の間での `izanagi_gate_pass` 再代入」だけである。**
凍結領域の拡大では gate の**意味論**は固定できない。段 3・段 6 の敵対検証が、block と epilogue を
逐語一致させたまま gate を無効化する差分を 4 種類、実際に書いて示した。

| ID | 残存限界 | 実証 |
|---|---|---|
| R1 | block 全体のコメント化・raw string の囮 | T-897 段 6 (既知) |
| R3 | derive/require から compiler read までの ABA 窓 | T-897 (既知) |
| **R4** | prologue での `izanagi_gate_pass` 再宣言 (`operator=(bool)` を無視する型へ差し替えると、pristine も 32 hole も no-op になり `if` は常に false) | 段 3 レンズ B 所見 1 |
| **R5** | 宣言と BEGIN の間の制御流変更 (`return;`) による hole/gated call の非到達化 | 段 3 レンズ A 所見 2 |
| **R6** | epilogue 直後への dangling `else` 付加 (preprocess 後に `if...else` が結合し常時 backoff) | 段 3 レンズ A 所見 3 |
| **R7** | call target / 引数の名前解決差し替え (`FLAGS_clocks_per_us` の local shadowing で `backoff(0)`) | 段 6 レンズ B 所見 2 |

R4〜R7 は**実装せず起票した。** ユーザー scope が「post-END の `if` まで」と明示されており、
かつ本 wave の指示が「scope 外の発見は次の一手へ起票し、差分へ帰属させない」だったためである。
4 件はいずれも実装 docstring に明記した — **守っていない範囲を守っていると読ませないことが、
この gate の価値の半分である。**

C++ 字句解析器は再建していない (T-897 段 6 が自前字句解析の偽受理と過剰拒否を両方向で実証済み)。

## 落とした設計 — `END + E + E` の直結重複拒否

段 2 プランは「END 直後に同じ epilogue が 2 本連結された場合を拒否する」検査を提案した。**落とした。**

epilogue より後を凍結しない設計なので、`E + E` が生む「backoff 二重実行」は、**受理する**
`E + #if ... else { backoff(); } #endif` (R6) や `E + 無条件 backoff` と同じ結果である。片方だけを
拒否する理由を成果物の値の差として書けない (DW-G05 は「書けない must-fix は nit/backlog」とする)。
段 6 の 2 レンズもともに nit と評価した。代わりに **`E + E` を受理することを正例テストで固定**し、
受理言語に「epilogue より後の bytes は凍結しない」を明記した。

## 純増検出力 (段 1 brief の誤りを訂正)

段 1 brief は「S8b oracle / floor / S-1 extime calibration は quarantine 非経由」と書いた。**誤りだった。**
段 3 レンズ B の指摘を親が実測して確認した — `s1_verify_extime_calibration.py:341` と
`s1_direct_comparison.py:593-602` (`prepare_cell`、S8b floor / oracle が共有) はいずれも
`p3_s4_loop.quarantine` を呼び `passed` を検査する。

**訂正後:** 純増は、build gateway が quarantine の実行有無と独立に、**compiler が読む直前の source
そのもの**へ epilogue の逐語隣接を要求するようになったこと。quarantine が覆わないのは
(i) 実装文字列を挿入しない pristine / characterization 経路、(ii) diff の baseline 側に既に混入した
改変、の 2 つで、純増はこの 2 つに限る。quarantine も admission も通らない非認証 build は元から
admission 外であり、純増の対象ではない。

## 凍結 pin の実測 (DW-O09 の探索漏れと是正)

段 6 レンズ A が、親の DW-O09 探索漏れを 1 件出した。`orchestrator/campaign/axis_trigger_gating.py` は
`output/s1-freeze/known_axes_freeze.json`、`output/s1-freeze/measurement_freeze.json`、
`output/s8b-freeze/holdout_freeze.json` から **source sha256 で間接 pin** されている。親の当初の探索は
`FROZEN_MANIFEST` の key と `.py` の path 検索だけで、凍結 JSON 本体を検索していなかった。

**実測:** pin 値 `47507d9b…` に対し、着手前 (main 48b2caab) の実値は既に `72371560…` で、
**wave 前から不一致だった。** 本 wave はこれを不一致のまま維持し、**凍結 JSON を再 pin していない**
(既存の凍結チェーン検証はユーザー裁定 `freeze-verification-hold` で保留中であり、同裁定は
「凍結 bytes は書き換えない」を条件にしている)。既存不一致は起票した。

## 実測

| 何 | 結果 |
|---|---|
| 焦点走 (9 file、1 回目) | 1 failed / 790 passed / 10 skipped (計算ノード 909555.nqsv、18.71 秒) |
| 同一集合の再走 | **791 passed / 10 skipped / rc=0** (17.56 秒) |
| 赤の帰属 | 単独走 1 passed。非決定的で差分に帰属しない。既知 [T-1049] の再発 |
| 変異 1 巡目 (probe) | baseline PASSED、MUT-1 KILLED / MUT-2 MISMATCH / MUT-3 KILLED |
| 変異 2 巡目 (中止) | 全結果は KILLED だったが、走行中に親が README を書いたため共有木の事後検査が rc=125 で中止した (F106 の 6 度目) |
| 変異 3 巡目 (本走) | **baseline PASSED、3/3 KILLED、期待 node 完全一致、MISMATCH 0 / SURVIVED 0、rc=0** (tip 7b15aff6) |
| 受入全走 (1 回目) | 走行前に `preflight-submodule-ready` rc=2 (入れ子 `third_party/googletest` 未初期化)。再帰初期化で解いた |
| 受入全走 (2 回目) | **2 failed / 10782 passed / 65 skipped (140.16 秒)**、計算ノード、tip 56836799 |
| 赤 2 件の帰属 | 単独再走 **6 passed / rc=0** で再現せず。既知 [T-1066] と F57 の再発で、本 wave の差分に帰属しない |
| AI provenance | 全史 rc=0、新規違反なし (既知 known-violations=39) |

**非帰属 checker は使えなかった。** `tools/check_acceptance_reds.py` は裁定済み・未実装の [T-1053]
(dispatch の env allowlist に `PYTHONDONTWRITEBYTECODE` を足す) により、**赤を 1 件でも含む実 log に
対して必ず `rc=2` (probe worktree is not clean, including ignored files) になる。** `DW-O18` は
「rc=2 は判定不能で非帰属の根拠にしない」と定めているため、帰属は単独再走の実測で確定した。
受入前に ignored 生成物を撤去しても、checker 自身の子が probe worktree の中で pytest を dispatch して
`__pycache__` を再生成するため、親側の掃除では解けない。

焦点走の赤 `test_p3_autonomous_workload_trial.py::test_origin_public_result_distinguishes_partial_from_completed`
(`operation_id was already used with different payload bytes`) は、`_OPERATION_REPLAY_CACHE` が
module 変数で process 全体に残る既知欠陥 ([T-1049]、archive worklog 535-536 に起票済み) の再発である。
新規起票はしない。

## 変異の帰属 — 期待 node は probe で再導出した

段 6 レンズ B が「MUT-2 は `test_build_admission.py` 内だけで**少なくとも** 37 node を赤にするので、
単数の期待では `MISMATCH` になる」を must-fix で出した。「少なくとも」という留保が付く以上、静的列挙は
完全集合の根拠にならない。DW-M08 が許す probe 経路を採り、1 巡目を probe と明記して回し、実測した
失敗 node の完全集合で再登録して本走した。1 巡目の生 ledger は
`/work/1/SFC/tanab/dev-wave-jobs/2026-08-13_t1048-trigger-freeze-epilogue/mutation/` に残す。

- **MUT-1** (epilogue 隣接検査の削除): 3 node。負例 `deleted` / `modified` / `gap-before` はいずれも
  canonical pristine block を使うので、検査を消すと block の早期 return に入り**他層は拒否しない**。
- **MUT-2** (`raw[start:] == E` への過剰強化・正例): 37 node。32 mask + pristine + post-epilogue 2 +
  read-once + runtime-recheck。受理集合を縮小する wave の必須正例 (DW-M01) であり、承認外の過剰拒否を
  検出する。
- **MUT-3** (凍結定数を patch と食い違う値へ差し替え): **1 node のみ**。定数はテスト入力の生成源でも
  あるため入力と期待が同時に動き、**patch 整合テストだけが独立照合として効いている**ことの実証である。

登録しなかったもの: BEGIN/END の順序検査 arm (後段の frame 比較が同じ入力を拒否する。T-897 の
M4-prime と同型)。`deleted` / `modified` / `gap-before` を別々の変異として数えること (いずれも MUT-1 が
消す同一分岐への異なる入力であり、負例テストとしては 3 入力とも持つ)。

## 子の工数

| 段 | model / effort | 結果 |
|---|---|---|
| 段 2 plan | gpt-5.6-sol / max | accepted、model call 53、16908 bytes |
| 段 3 consult A (1 回目) | gpt-5.6-sol / max | **not_accepted** — model call 上限 100 で SIGTERM、出力 0 bytes |
| 段 3 consult A (2 回目) | gpt-5.6-sol / max | accepted、10769 bytes (探索予算の規律を prompt へ足し上限 300 で再投入) |
| 段 3 consult B | gpt-5.6-luna / max | accepted、7684 bytes |
| 段 5 author | gpt-5.6-sol / high | accepted |
| 段 6 review A | gpt-5.6-sol / high | accepted、must-fix ゼロ |
| 段 6 review B | gpt-5.6-sol / high | accepted、コード must-fix ゼロ |
| 段 6 fix | gpt-5.6-sol / high | accepted (docstring のみ) |

## 運用で踏んだもの

- **`codex_worker_launch.py` は `--artifact-dir` と `--receipt` の親ディレクトリの実在を要求するが、
  `dev_wave_codex.py` は `<root>/<wave>/` までしか作らない。** launcher を直接叩く運用
  (`--evidence-grace-s` を足すため argv を dry-run で取り出す形) では必ず空振りする。本 wave は
  2 回失敗した。`.done` は消さず別名で再投入した。
- `--evidence-grace-s` の既定は今も 5 秒 (`codex_worker_launch.py:3104`)。
- 変異 spec の `hang_risk` field 欠落で harness が起動前に停止し、使い捨て worktree が
  prunable な残骸として残った。撤去 + `git worktree prune` で即時回収した。

## 逐語

`verbatim/` に段 2〜段 6 の子成果物を置く。`mutation/` は job dir 側に生 ledger を残す。
