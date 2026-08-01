# [T-276] 計算ノードでの role 実行の解禁 — 一次資料

2026-08-01 夜〜2026-08-02 未明。branch `worktree-dev-wave-t276-compute-role`、base = main `3c924bb`。
実装 anchor commit `9abed5d`。決定は D122 (D108 決定 (1) を supersede)。
**採番衝突の改番 1 件**: 本 wave は当初 D116 として起草・commit したが、land 直前に取り込んだ
local main が既に D116 ([T-295]) を持っていたため D122 へ改番した。anchor commit `9abed5d` と
記録 commit `ea7c0b7` の message 中の「D116」は改番前の呼称である。
worklog エントリ番号と新規 T 番号も同じ理由で改番した (詳細は当該 worklog エントリ)。

裁定 (worklog (102)) = 択 (b)「計算ノードでの role 実行を解禁する。解禁の前に
① 攻撃者制御 proxy の MITM / injection、② proxy 値の同一性 provenance、
③ 実装と同じ env から期待値を作る恒真な受入検査、の 3 件を閉じる。D96 手続を通す」。

## 実行環境

- 子はすべて `codex exec -m gpt-5.6-sol`。plan / 敵対相談 / レビュー / 焦点再レビューは
  `model_reasoning_effort=max` + `-s read-only`、実装 / fix は `high` + `-s workspace-write`。
- テストはすべて `tools/run_tests.py` 経由で Pegasus gen_S 計算ノードへ dispatch した。

## 逐語

| file | 内容 |
|---|---|
| `s1-brief.md` | 段 1 親 brief。前提実測 (request `877155`) を含む |
| `s1-probe.sh` / `s1-probe-out.txt` | 段 1 前提実測の probe と生出力 (bnode009) |
| `s2-plan.md` | 段 2 codex プラン起草。親 brief の過大表現 3 件を訂正した |
| `s3-lens-a.md` | 段 3 敵対レンズ A = 信頼境界 / MITM / 規律 6 (NO-GO) |
| `s3-lens-b.md` | 段 3 敵対レンズ B = 恒真性 / consumer 取り残し / 凍結波及 (NO-GO) |
| `s4-adjudication.md` | 段 4 親裁定 + plan v2 + 変異事前登録。**scope の正本** |
| `s5-impl.md` | 段 5 実装子 |
| `s6-review-c.md` | 段 6 敵対レビュー C = 実装の恒真性・受理集合・裁定履行 (NO-GO) |
| `s6-review-d.md` | 段 6 敵対レビュー D = 信頼境界・fail-open・consumer 取り残し (NO-GO) |
| `s6-fix.md` | 段 6 fix 1 巡目 (C/D の must-fix 9 件) |
| `s6-focus.md` | 段 6 焦点再レビュー。closed/partial/regressed 表 (NO-GO、N1〜N6) |
| `s6-fix2.md` | 段 6 fix 2 巡目 (N1〜N6) |
| `s6-fix3.md` | 段 6 fix 3 巡目 (親が実測した赤 2 本。いずれもテスト側の欠陥) |
| `mutate.py` / `mutations.json` | 変異 harness と spec (codex が作成) |
| `mutation-ledger.json` | **変異台帳 (本走)**。注入 diff・failed node・復元検査を含む |

### 逐語の可逆正規化 1 件 (`DW-S07`)

`s3-lens-b.md` の 87・140・142・144 行目に markdown の hard line break (行末の半角空白 2 つ) が在り、
`git diff --check` に抵触した。可視文字を変えない最小正規化として**行末空白のみ**を除去した。

- 原文 sha256 = `75e803c1562fbec5b2bf28ea04d9aa75e5598021fe96e1f8f1424a420ae730f1`、25586 bytes
- 正規化後 sha256 = `16fa4c2ee9639c88a107d7c9101cf10bb09da741574433bd66f3f049a79001aa`、25578 bytes
- 除去 = 8 bytes (4 行の各行末に半角空白 2 つ)
- 復元法: 87・140・142・144 行目の各行末へ半角空白 2 つを付け直すと原文 sha256 に一致する

## 変異本走 (`mutation-ledger.json` が正本)

anchor commit `9abed5d` に対して実施。全 27 entry で `injection_verified` と `restored` が真、
`SURVIVED` はゼロ。内訳は **KILLED 22 / DIAGNOSTIC-PINNED 2 / POSITIVE-GREEN 3**。

`M13-leaf` と `M13-trial` は受理集合を変えず診断文言だけを変える変異なので、`DW-M08` に従い
KILL 総数から外して diagnostic sensitivity pin として別枠に記録した。

`P1`〜`P3` は正例 (過剰拒否検出) であり、緑のままであること自体が結果である。
`P1` = flag 省略の `run_trial` E2E で transport I/O 呼出し 0 回かつ transport field 不在、
`P2` = compute + flag + 宣言一致 env + PBS witness で admission 成立、
`P3` = 従量経路 env 5 key が不在なら受理する (過剰拒否しない)。

### 変異事前登録からの変更 (`s4-adjudication.md` §5 → 最終 spec)

段 6 の焦点再レビューが、事前登録のうち 3 件が「登録どおりに実装すると root cause と等価でない」と
判定したため再照準した。経緯は `s6-focus.md` の N2〜N4 が正本。

- `M5` → `M5-leaf` / `M5-provider` に分割 (leaf の複製と provider env 配線の複製は別層)
- `M10` → 「4 回解決して最後を共有する」から「各 production provider が別 resolver 結果を受け取る」へ
- `M11` / `M12` / `M13` → 層別 nodeid へ分割 (単一理由性、`DW-M03`)
- `M14-report-drop` を追加 (journal には残るが report cell から receipt を落とす変異)
- `P1` / `P2` → unit 単体から親定義どおりの E2E 射程へ戻した

## 親が申告する契約逸脱 1 件

段 1 の前提実測に使った `s1-probe.sh` は**実行可能 probe = 実装面**であり、dev-wave の凍結境界では
Codex `role=author` が書くべきだった。親 (Claude) が直接書いて投入した。既に走って計測を生んでいるため
取り消せない。変異 harness (`mutate.py` / `mutations.json`) は同じ穴に気づいた時点で codex に書かせて
是正した。逸脱の内容と是正は worklog にも記録する。

## 親の操作ミス 1 件 (commit には到達していない)

変異本走中に親が `git add -A` を実行し、その時点で注入されていた `M3` 変異 (未受理 proxy 名の
拒否削除) が index に入った。**working tree は HEAD と一致しており復元は正常**で、
`git restore --staged` で index を戻してから記録 commit を作った。commit へは 1 度も到達していない。

## 閉じたもの / 閉じないもの

D122 決定 (7) が正本。**MITM を防止したとは主張しない。** 閉じたのは (96) が指摘した形
「proxy 値が無検査の外部制御面である」までであり、残るのは固定 proxy 自体の侵害、
実行体と `PATH`/`HOME` の trust root ([T-242])、`PBS_JOBID` の偽装可能性、
valid-schema な一行 C++ 注入と虚偽 auditor pass である。
最後の 1 件は `_site_admits_measurement` が Pegasus を拒否している間は build / run へ到達しないが、
**[T-277] を開ける前の blocker として登録した**。
