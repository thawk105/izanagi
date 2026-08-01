# 段 4 裁定 — [T-248]

## 裁定の結論

**実装しない。新事実付きでユーザー再裁定へ返す (`4→7→8→9`)。**

根拠は `DW-STOP` の停止条件「承認済み裁定の前提を覆す未見の新事実がある」に該当することである。
`DW-S04` により、親は不採用にせず再裁定待ちへ戻す。実装差分が無いため、
**変異 matrix と受入全走は本 wave の射程外**とする (baseline 全走は前提実測として実施済み)。

## 裁定の前提を覆した新事実 (裁定時点で未記録)

1. 症状 (dispatch 経由で T-126 submitter 系が偽赤) が main tip `7b24f81` で再現しない。
   単発 `876518` = 1 passed / rc=0、全走 `876520` = 4709 passed / 19 skipped / rc=0。
   **いずれも bnode002 の 2 走**であり、ノード群全体への一般化はしない (レンズ A-6 採用)。
2. 裁定の一次資料 `s6-ruling-package.md` は、同じ文書の §2 で当該 wave の全走 `874775`
   (bnode042) を 3710 passed / rc=0 と記録しながら、§6-3 で「この経路では偽赤になる」と
   断定している。赤を観測した run の request ID・ノード・生ログは記録されておらず**追跡不能**。
3. 「3.9 fallback」の帰属は成り立たない。PATH 前置 (`dirname($selected)` = `/usr/bin`) は
   T-188 `a34266d` 由来で観測時点より前から在り、計算ノードの `/usr/bin/python3` は
   実測 3.10.12 (2026-07-19 insight、bnode097)。intelpython の 3.9.13 は前置で shadow される。

## 所見の裁定 (real/refuted・採否)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-1 | 「受理集合は縮むだけ」が非単調で自己矛盾 | real | 採用 (実装するなら軸定義が前提) |
| A-2 | PATH shim は束縛でなく上書き可能な既定値。「全孫を塞ぐ」は偽 | real | 採用 (再裁定の説明へ反映) |
| A-3 | `_job_run` 版数 gate 単独削除を殺す pin が無い (M5 は両層同時のみ) | real | 採用・scope 外 (既存問題、別 ID) |
| A-4 | mismatch test が helper を mock すると恒真になる | real | 採用 (実装時の必須条件として記録) |
| A-5 | symlink/TOCTOU/権限。shim dir が PATH 先頭 = 他 command 注入面 | real | 採用 (full shim のコストとして計上) |
| A-6 | 親の非再現主張は bnode002 一台にしか成立しない | real | 採用 (記録の表現を訂正) |
| A-7 | P1 の現物 chain が brief に閉じていない | real | 採用 (chain を記録へ追加) |
| B-1 | P1 は裁定後の目的差し替え。再裁定へ返すべき | real | **採用 = 本裁定の中核** |
| B-2 | 親測定は現行緑を証明するが shim の必要性も過去の赤も証明しない | real | 採用 |
| B-3 | 被覆主張は誇大 (継承 PATH を保つ子にしか効かない) | real | 採用 (A-2 と同型) |
| B-4 | wrapper は再入 poison と共有 FS exec 要件を新設する | real | 採用 (full shim のコスト) |
| B-5 | P4 は P1 前提の循環、P5 は人工 control で実在証拠にならない | real | 採用 |
| B-6 | F46/runbook が要求するのは shim でなく実行環境側の assert | real | 採用 (択 (b) の根拠) |
| B-7 | closure wave の赤の記録訂正は T-248 から切り離せない | real | 採用 (本 wave で記録訂正) |
| A-P2 | `_job_script` に裸 `python3` は無い (P2 は反証できず) | real | P2 維持 |
| A-P4 | 軽量版にしない判断自体は契約どおり | real | P4 維持 (ただし B-5 の条件付き性を認める) |

refuted はゼロ。**両レンズとも NO-GO**、判断は一致している。

## 変異事前登録 (`DW-M01`)

実装差分が無いため事前登録は行わない。段 2 プランの候補 5 件は、レンズ A の帰属批判
(共有 helper の巻き添え、複合変異、既存 test との重複) を含めて再裁定パッケージへ添付し、
実装が承認された場合に単一理由性を取り直す。

## ユーザーへ返す択一 (T-248 再裁定)

| 択 | 内容 | 得 | 損 |
|---|---|---|---|
| (a) | 段 2 プランの full shim (submission dir 配下に create-only の透明 wrapper `python3`、PATH 先頭、identity 検査、`stage="interpreter-shim"` で fail-closed) | 継承 PATH を保つ子孫では裸 `python3` が検証済み実体に固定される | 新 dir・wrapper・共有 FS の exec 要件・新 stage・再入 poison・6 本超のテスト。PATH を上書きする子には効かず「一箇所で塞ぐ」は達成できない。PATH 先頭の書込可能 dir という新しい注入面 |
| (b) | 最小 assert (推奨) — child PATH 確定直後に**裸の `python3`** で版数だけを検査し、3.10 未満なら既存 `stage="interpreter"` / rc=16 で停止する | F46 の恒久対応 (実行環境側で assert として束縛する) と同型。黙って古い interpreter で走る経路を大声の失敗に変える。新概念ゼロ | 症状を治さない (該当ノードでは job が落ちる)。受理集合を縮めるため D96 の手続が要る。task probe (`pytest`/`xdist` を要求) をそのまま流用すると過剰拒否になるので**版数のみ**にする必要がある |
| (c) | 実装しない (設計メモに留める) | 未観測リスクにコストを払わない。再発を観測した時点で再開できる | 穴は残る。ノード画像が変わった時に再び静かに踏む |

親の推奨は **(b)**。理由: 実測で症状が非再現であり、(a) の被覆は本人が謳うほど広くない一方、
(b) は F46 の一般則そのもので、コストが小さく、記録も誇大にならない。

## scope 外の real 所見 (別 ID 候補、本 wave では実装しない)

1. `tools/pegasus/certify_calibration.sh` / `submit_certify.sh` は計算ノードで裸 `python3` を
   多用し版数 gate を持たない (F46 family)。
2. `tools/pegasus/t141_region_profile.sh:357` は `python3` の**存在**だけを検査し版数を見ない。
3. `orchestrator/qualification/submission.py:73,107` は toolchain の version を**記録するだけ**で
   floor を課さない (F46 の「記録するだけの値」型)。
4. `_job_run` の版数 gate 単独削除を殺す sensitivity pin が無い (M5 は両層同時変異のみ)。
5. `output/pegasus-dispatch/` root の owner/mode/symlink を誰も検査していない (脅威モデル未定義)。
6. closure wave (2026-07-31) の T-126 submitter 赤は**原因不明・再現不能・追跡不能**。
   「偽赤」「3.9 fallback」の断定は撤回し、原因究明を独立 ID にする。
