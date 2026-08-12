---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t184-followup
seq: 1
title: 打ち切られた 5 job を上限を外して追走し、上限軸そのものが run 間で 4 倍動くことを実測した — 択一に「calls だけ段別化」を追加した (docs のみ、branch worktree-dev-wave-t184-followup)
---

## 本文

2026-08-12 のユーザー裁定 (第 4 束、測定先行 1c+2a+5a)「追走 5 件 + CLI 版固定を先行、
sweep は不足時のみ、§17 は (c)」を執行した。実装面差分ゼロ。集計器・運転 script は repo 外に置いた。
実測は `output/insights/2026-08-12_t184-followup/`。

**再現の同一性を先に固めた。** prompt bytes 5/5 を sha256 一致で確保し、当時の path 名で
worktree を再作成して base commit・CLI 版 (0.146.0 のバイナリが残っていた)・model・effort・
sandbox・submodule pin を揃えた。生成 argv の job_id が原観測と **7/7 完全一致**した
(model / effort / base / authority snapshot は replay worktree の base commit の docs から
launcher が導出するため、手で揃えたのではなく当時の設定がそのまま再現される)。
打ち切られた t786 plan の prompt だけは job dir から失われており、rollout から復元した
({{F:truncated-job-prompt-absent-from-job-dir}})。

**段 3 の敵対相談 2 本がいずれも「そのまま投入するな」と勧告し、親の検算で全て支持された。**
最大の指摘は estimand の誤りである — 追走は原 run の続きではなく独立した別の 1 回であり、
**原の censoring は解けない**。得られるのは「原は cap を超えた」と「新走はこれだけ使った」の
独立した 2 事実の組である。あわせて (a) `cli_reported = input - cached + output` が原観測 5/5 で
厳密成立し cache が値を数倍動かすこと、(b) 当初の wall 7200 では wall が先に binding して
測定が成立しないこと (外挿で plan の 1000 calls 到達は 9,900〜13,700 秒)、
(c) 5 件中 1 件の prompt が `external/ccbench` の 4 file を名指ししており submodule 未初期化は
treatment 変更であること、(d) 0.147.0 対照走は裁定の scope 外であること、を採用して
設計を作り直した。wall を 14400 へ上げ、事前登録の repeat 対 (consult=A, plan=D) を足して 7 走とした。

**第 1 走は並行 session の worktree 掃除に走行中の worktree 5 本を削除され、7 走中 6 走が汚染された**
({{F:running-worktree-deleted-by-cwd-scan}})。施錠して再走した第 2 走と比べると汚染は
消費量を**系統的に下振れ**させており (7 cell 中 6 cell で第 2 走の calls が大きい、最大 2.0 倍)、
気づかず報告していれば上限を実際より低く見積もる提案になっていた。
削除した session から申告があり、**根本原因は施錠漏れだけではなく検出側にもあった** —
掃除の生存判定 `/proc/*/cwd` は launcher 型の子を構造的に検出できない
({{D:worktree-liveness-by-cmdline}})。稼働中の第 2 走で親が独立検算し、
cwd 一致 0 件・cmdline 一致 14 件を実測した。往復の中で、規律 6 の**送り手側の対称義務**も
言語化した ({{D:sendside-no-instruction-shaped-artifacts}})。

**第 2 走 7/7 が有効で、3 cap のいずれにも当たらず完走した。** 打ち切りが本物だった cell が 2 つ
(E は 128 calls、原 cap 100 / A は 1,500,868 tokens、原 cap 1e6)、原 cap 以下で完走した cell が 5 つ。
**最も重要なのは、事前登録した sweep 発火条件 (iii) が発火したこと**である。
同一 prompt・同一 base・同一 batch の repeat 対 A/A2 で、**calls は 1.05 倍 (58 対 61) しか違わないのに
`cli_reported` は 4.07 倍 (1,500,868 対 368,744) 違った**。cache 比率が 0.790 と 0.954 で異なるためである。
すなわち **`max_cli_reported_tokens` は仕事量ではなく cache 状態を測っており、段別の値を置くことは
同じ仕事が走るたびに 4 倍動く量に線を引くことになる。** `model_calls` は同条件で 1.05 倍しか動かない。

これを受けて択一の軸 4 へ選択肢 **4d (`model_calls` だけ段別化)** を追加し、親推奨を
**1a + 2a + 3a + 4d + 5a** とした。前 wave の推奨 3b (段別既定表) からは**後退させた** —
段・lane・model・base・prompt の交絡は本追走でも解けておらず、段別化の根拠が無いためである。
sweep は (iii) で発火したが、事前登録した設計を**走らせず**再提示に載せる (本 wave の終端は
択一の再提示であり sweep は独立した測定)。§4 により token 軸 sweep の価値は下がったことも添えた。

§17 は裁定どおり (c) を実装し、`docs/README.md` の地図へ `receipt.json` の所在と主要 field を
書いた。ただし **navigation pointer であって resource authority ではなく**
(authority を置けば 2a と衝突する)、`docs/dev-wave/**` の読み込み導線には乗らないため
「探索欠陥を解消した」とは書いていない。

エージェント工数: 段 3 の 2 本 (sol 12,333 bytes / luna 15,302 bytes、両 rc=0)。
追走は 14 走 (第 1 走 7 + 第 2 走 7) で、うち有効は第 2 走 7 走と第 1 走の 1 走。
段 3 の luna prompt に親 handoff の絶対 path を渡し忘れ、luna は前 wave の改善候補を評価した
(`DW-O02` の適用漏れ、親の誤り)。dry-run argv の再利用で 7 走が起動前 rc=2 になった件も記録した
({{F:dryrun-argv-missing-artifact-parent}}、空費ゼロ)。
汚染判定器が sandbox の方針拒否を誤検知し、有効な 1 cell を危うく捨てるところだった
({{F:contamination-detector-false-positive-on-rejected}})。

受入全走は実施していない。本 wave は docs のみで実装面差分がゼロであり、
repo を読むテストに影響する変更を含まない。`python3 tools/check_docs.py` は rc=0。

## 次の一手差分

### 更新

- [T-184] **P1・ユーザー裁定待ち (追走完了)**: 打ち切られた 5 job を同一 prompt bytes・同一 base・
  CLI 0.146.0 pin・submodule 一致で追走した (repeat 対 2 走を含む 7 走、3 cap を緩和)。
  7/7 が cap 未発火で完走。打ち切りが本物だった cell は 2 件 (128 calls / 1,500,868 tokens)、
  原 cap 以下で完走した cell が 5 件。**事前登録 sweep 条件 (iii) が発火** — 同一 prompt の
  repeat 対で `model_calls` は 1.05 倍しか動かないのに `cli_reported` が 4.07 倍動いた
  (cache 比率 0.790 対 0.954)。**上限軸そのものが run 間で不安定である**ことが本追走の主結果。
  択一の軸 4 へ 4d (`model_calls` だけ段別化) を追加し、親推奨を 1a+2a+3a+4d+5a とした
  (前 wave の 3b からは交絡未解決を理由に後退)。sweep 設計は事前登録済みだが**走らせていない** —
  発令はユーザー裁定。0.147.0 対照走は scope 外として実施せず、転移の測定案として返す。
  原 censoring は解けない (追走は独立した別の 1 回) という estimand の制約は不変。
  reasoning 面 (D266) 不変、retry policy は [T-183] 依存のまま。
  本項を他タスクの待ち解除根拠にしない規定も不変。
  base: 524a149c1c0e3b0a573b27ae1492155aa379eb5b6a78123ccf8e1b3ac4bfdfd1
