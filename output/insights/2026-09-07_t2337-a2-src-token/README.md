# [T-2337] A-2 の canonical identity を pin + patch 束縛の src_token で計算する

2026-09-07、wave `dev-wave-t2337-a2-src-token`。D1644 案 1 と裁定 3 / 裁定 4 の実装。

## 何が壊れていたか

`orchestrator/campaign/paper_story_a2_certification.py` の `_raw_cell_from_wal` が
`expected_variant = variant_id(expected_genome)` と書いており、src_token を既定の `stock` に
固定していた。patch を当てた木で走った正しい cell の variant id は `stock` 前提の値と異なるため、
driver は **patch が効いていない木を通し、効いた木を拒む**向きに倒れていた。

## 段 1 の実測

使い捨て probe を Codex author に書かせ、親が login node で実走した。
A-2 の関門文脈と同じ手順 (`patchharness.checkout` → `patchharness.applied` →
`source_digest.resolve_evidence`) で 4 cell を測った。

| cell | 役割 | patch 無し | patch 有り |
|---|---|---|---|
| rr5-stock | stock | `stock` | `stock` |
| rr5-fixed10 | adopted | `stock` | `955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9` |
| rr50-stock | stock | `stock` | `stock` |
| rr50-fixed5 | adopted | `stock` | `21def77c944b1b855ea2da5516a7280858957888ec1b0644b80d9ae51e73c98a` |

variant id は rr5-fixed10 が patch 有りで `1f2762881fcb`、stock 前提だと `09a3e222ce49`。
rr50-fixed5 は patch 有りで `47e599584695`、stock 前提だと `b0e5ae3f1d70`。
stock cell は両条件で `960e57e1aeba`。ccbench の pin は `511c953`。

**測定条件の限界:** 本番の cxx は `g++-13` だが、この機体には login node にも計算ノードにも
存在しない (`docs/pegasus-runbook.md` に明記)。probe は `/usr/bin/g++-12` を明示指定して測った。
patch 前後を同一 preprocessor で一貫比較するので stock / 非 stock の判定には答えられるが、
digest の値そのものは本番と異なる。**本番条件での値域は未実測である。**

この実測により、D1644 が定めた述語 (stock cell は `stock`、adopted cell は非 `stock`) は
到達可能であり、現行 driver の期待値は「patch 未適用の木」と一致することが確かめられた。

## 段 3 が変えた設計

段 2 のプランは、凍結成果物からの再構成で raw 自身が持つ `src_token` を期待値にしていた。
段 3 のレンズがこれを「D1644 が却下した案 2 (driver が独立な期待値を持たず、記録された値の
とおりを確かめる恒真判定) へ戻る」と指摘した。

親はこれを採り、裁定 3 が求める「campaign より前に保存する受領証」をそのまま独立した
期待値の出所にする形へ変えた。2 つの裁定が 1 つの機構になった。詳細は decisions を参照。

## 段 6 が見つけた must-fix

- **受領証 authority の失敗が、成果物を作った後の停止になっていた。** 空 cells の判定不能を
  正規の置き場所へ書き出してから終了しており、一度書かれると修復版を同じ場所へ置けなくなる。
- **同じ「token 欠落」が出所で分類が違った。** raw 側なら確定的な拒否、受領証側なら判定不能。
- **schema 名 `paper-story-a2-raw-manifest/v4` が 2 義だった。** 新 full 版 (受領証込みの inventory) と
  旧 partial 版 (受領証なしの 5 件) が同じ名前を名乗っていた。

3 件とも fix で閉じた。新 full 版は `paper-story-a2-full-raw-manifest/v4` へ改名した。

## 実走した検査

すべて親が実走した。

| 対象 | 件数 | 所要 | rc |
|---|---|---|---|
| 単位 A 単独 (`test_paper_story_a2_certification.py`) | 127 passed | 68.18 s | 0 |
| 単位 B 単独 (`test_t2337_dispatch_timeout_overrides.py`) | 13 passed | 4.45 s | 0 |
| 統合後の焦点走 (直接消費者 5 file) | 644 passed | 17.71 s | 0 |
| 段 6 fix 後の焦点走 (同 5 file) | 652 passed | 20.45 s | 0 |
| main 取り込み後の合成検査 (6 file) | 763 passed | 19.59 s | 0 |

焦点走は計算ノードへ投入された。

## 変異の事前登録

段 4 で 16 本を照準したが、段 6 のレンズの静的判定により、単一の理由で赤にできるのは 10 本
(M2 M3 M5 M6 M9 M11 M12 M13 M14 M15) だけだった。残り 6 本 (M1 M4 M7 M8 M10 M16) は複数 node が
同時に落ちるため「その変異を殺した」と帰属できない。段 4 裁定 §7 の定めどおり、
確定できないものは登録しない。

## 段 5 実装子の中断

単位 A の実装子は model call 上限 100 回に達して打ち切られ、完了報告を書かずに終わった
(`control_limit_trigger=max_model_calls`、28 分、29.5 万トークン)。成果は保全して実走で
127 件緑を確認し、裁定 8 項目がすべて実装済みであることを親が照合した。
driver 本体は 4400 行あり、既定の予算では 1 巡で終わらない。以後の子は上限を上げた。

## 残した項目

- 新しい identity での A-2 attempt 取り直し (本 wave の scope 外)。
- `tools/plotting/plot_a2_certification.py` の新 schema 対応。同 file は schema を厳密一致で
  要求するため、凍結済みの旧版は読めるが新版の certification では図を作れない。取り直しの前段。
- full certification の materializer への exact 再導出。partial 側は再導出して一致を要求するのに
  full 側は外形と identity しか見ない非対称が既存で残っている。本 wave が作った欠陥ではない。

## 段 9 準備で見つけた 2 件 (どちらも本 wave が作り込んだ)

### 変異試験の道具が自分の検査対象を取り込んでいた

`tools/mutation_harness.py` が module 読み込み時に `tools/check_ai_provenance.py` から
待ち時間の解釈処理を import していた。このため `check_ai_provenance.py` へ変異を注入すると
変異を注入する道具自身の挙動が変わる。DW-M07 が名指しする自壊型であり、裁定 4 の実装が
変異試験で検査できない状態だった。段 6 のレビューは結合そのものを検査項目に挙げていたが、
この帰結までは出ていない。

import を除去して harness を自己完結させ、両実装の受理集合が一致することを機械照合する
検査を足した (空値・有効値・`nan`・`inf`・負値・負のゼロの 8 例)。
`PEGASUS_DISPATCH_RC = 16` と同じ先例に倣った形である。

### role 述語に、発火する検査が無かった

probe 走で `_require_cell_src_token_role` の live 事前評価での呼び出しを丸ごと消す変異 (M6) が
**SURVIVED した。** 実装は在るが、外しても既存テストは 1 件も赤にならなかった。
D1644 が「adopted が `stock` なら patch 未適用として赤」と定めた fails-closed の要求に、
実際に発火する検査が付いていなかった。

**段 6 の静的レビュー 2 本はこれを「充足」と判定しており、変異だけが反証した。**
検査を 3 本足した (実装は無変更、テストのみ 126 行追加)。

- 正しい 2 cell について production 述語が exact 2 回呼ばれること。
- adopted の src_token が `stock` のとき campaign へ到達せず停止すること。
- stock の src_token が非 `stock` のときも停止すること (述語は双方向に fails-closed)。

負例の入力値は段 1 の実測 (patch 済み隔離木での実際の token) から取った。

## 変異 matrix

probe 走 (全件 SURVIVED 登録で観測 node を集める) → 修正 → 本走の 3 段で行った。

| 変異 | probe 走 | 本走 |
|---|---|---|
| M2 patch 済み木でなく元の木で解決する | MISMATCH (1 node) | **KILLED** |
| M6 role 述語の呼び出しを消す | **SURVIVED** | **KILLED** |
| F2 full manifest の schema 名を二義へ戻す | MISMATCH (1 node) | **KILLED** |
| M11 `--queue-wait-timeout` を落とす | MISMATCH (1 node) | **KILLED** |
| M12 `--overall-grace` を落とす | MISMATCH (1 node) | **KILLED** |
| M14 provenance の転送を落とす | MISMATCH (5 node) | **KILLED** |

本走は 6/6 KILLED、SURVIVED 0、MISMATCH 0、baseline 緑 (rc=0)。
台帳は同 dir の `mutation-ledger.json`、spec は `mutation-spec-final.json` と
`mutation-spec-probe.json`。段 1 の probe 実測は `src-token-probe-result.json`。

probe 走では M1 (本題の token 束縛を外す) が 100 node を赤にした。単一帰属が成立しないため
段 4 裁定 §7 のとおり本走の登録から外した。本題の束縛は M2 と M6 が別経路から押さえている。

## 実走した検査 (追記)

| 対象 | 件数 | rc |
|---|---|---|
| 結合を切った後の焦点走 | 771 passed | 0 |
| role 検査を足した後の焦点走 | 773 passed | 0 |
| 変異本走 | 6/6 KILLED | 0 |
