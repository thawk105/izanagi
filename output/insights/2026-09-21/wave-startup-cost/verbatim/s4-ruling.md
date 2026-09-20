# 段 4 裁定 (2026-09-21 07:5x JST) — 段 3 相談 A (sol、`codex/s3-consult-A.md`) の所見 13 件への裁定と plan v2

裁定 inbox (`dev-wave-jobs/rulings-inbox/`、最新 2026-09-21 01:21) を再走査: 本題 (worktree / submodule / 起動) の裁定なし。main は 5efd69367 のまま。

## 所見別

| # | 判定 | 採否 | 処置 |
|---|---|---|---|
| 1 中央値 70 s の算式が再現しない | real / must-fix | 採用 | diag-login-check-wall は `index` 07:34:06 (81 s)。代理区間 10 本 = 18 / 39 / 51 / 65 / 75 / 75 / 81 / 82 / 90 / 96、中央値 75 s。表と本文を訂正 |
| 2 mtime は処理境界でない | real / must-fix | 採用 | 「`commondir`→`index` は worktree add の代理区間 (add 前半を含まず、後続の index 更新で過大になりうる)」と明記。直接計測 (自 wave: EnterWorktree 85 s、submodule 7.46 s、gate 6.70 s) を判断の中心にする |
| 3 submodule 代理区間が過小 | real / must-fix | 採用 | 自 wave の代理 6 s に対し直接 7.46 s。代理区間は「下界寄り」と書き、比率は直接計測で出す |
| 4 昨日の標本は単独でない | real / must-fix | 採用 | submit-tree (21:53:38〜21:54:59) と mutation-source (21:54:11〜21:55:19) は 48 s 重なる。「単独」を撤回し「昨日 21:5x の 2 木並走」と書く |
| 5 「大半でない」は観測条件に限定 | real / should | 採用 | P1 を「今回の直接計測 7.46 / (85 + 7.46 + 6.70) = 7.5%、他標本の代理指標も大半を支持しない → 条件成立と判断しない」に限定。nlink は採取時刻付きで 155 (07:4x、20 本) → 157 (07:4x、verbatim 採取時、22 本)。16 本は job dir の mtime 順である旨を書く |
| 6 `--reference` は local clone の hardlink 複製を省かない | real / must-fix | 採用 | git 2.34 `clone.c` の `clone_local()` は `--shared` でない限り `copy_or_link_directory()` を実行し、`--reference` は alternates 行を足すだけ。「≤1〜2 s」を撤回し「現行 argv (URL = 主 store の絶対 path) への `--reference` 追加で省ける処理は示せない → 正の短縮は未実証」と書く。object 36 file は ccbench store のみ、3 段の tracked file は 405 + 790 + 245 = 1,440 (`git ls-files`) |
| 7 alternates 不採用理由の精密化 | real / should | 採用 | insight「導入しない理由」を所見 7 の 4 条件 (gc/prune、deinit は store を保持、主 store 撤去、cleanup の nlink 検査は `objects/info/*` の hardlink を rc 20) で書く。runbook への 1 行は実装しないので書かない |
| 8 P3 の 20 s と起動→段 1 の帰属 | real / must-fix | 採用 | 20 s は「未分解残差」。EnterWorktree 前→gate 後 331 s のうち直接計測 3 処理 99.2 s、残り 232 s は親の読取り・handoff 執筆 (機械的固定費でない)。wall-decomp の S1 は startup-gate 後が起点なので、gate 以前の固定費は S1 11.7 分の「うち」でなく**外側 (加算)**。brief と insight を訂正 |
| 9 metadata / bytes 未分離、木の本数 | real / should | 採用 | 「file 数 (metadata) と bytes の律速は本資料では分離できない」と明記。木は 1 + (1〜3) + 1 + 1 = 4〜6 本 (t2797 = 4 本を実測)、換算は 45〜96 s × 4〜6 本 = 3〜10 分の**条件付き概算**で、並走分は wave wall の短縮量ではない |
| 10 「+60 秒」の同定 | 判定不能 | 採用 | 「受入は git の木を作らない (静的確認)。ユーザーの +60 秒に対応しうる既知区間は T-2817 の受入 `pre` 61.9 s と test 内部の base copy 64.2 s の 2 候補で、同定は未了」と書く。scope 外 |
| 11 次候補の分類 | real / should | 採用 | (a) `checkout.workers` = 既存 git 機構の local config 1 行 (主 checkout の config は共有 worktree に及ぶが独立 clone には継承されない)、(b) sparse = 実在 file を変える設計変更で scope 外、(c) 同一 unit の fix 木再利用は既存手順 (DW-S05-A)、wave 間流用・D1009 廃止は scope 外。`tools/pegasus/README.md:327` / `fetch_third_party.py` の sparse / alternates 拒否は third-party source 側の規則で superproject を禁じない (親の懸念は refuted) |
| 12 ABA probe は追加実験 | real / should | 一部採用 | probe は相談と並走で既に完走 (`probe/probe.log`、07:50:27〜07:53:54)。**追加の probe・設定変更はしない。** 結果 (workers=1: 50.6 s / workers=8: 20.4 s / workers=1: 45.3 s、各 1 回、混雑下、cache 温まりと負荷変動は未分離) は「候補 (a) の予備診断」として限定付きで記録し、採用効果や一般的短縮率にはしない。採否は裁定パッケージ |
| 13 scope / 受入全走は過剰でない、DW-G05 行が不十分 | refuted (過剰) / real should (G05) | 採用 | DW-G05 行に「誤った内訳・見積りが insight と裁定根拠に残る」を足す。変異免除・受入全走必須は維持 |

## plan v2

1. 実装しない (条件不成立)。段 5・6 の実装子なし。`4→(insight 起草)→6 (独立 read-only レビュー 1 本)→7→8→9`。
2. 成果物: `output/insights/2026-09-21/wave-startup-cost/README.md` + `verbatim/` (一次資料の写し = 出力 text のみ。採取 script は実装面 (D95) なので repo へ入れず `verbatim/scripts.sha256` で束縛)、worklog fragment 1 本、decisions fragment 1 本 (却下案: `--reference` / alternates を採用しない理由と、次候補の裁定パッケージ)。
3. 変異 matrix: 実装面差分ゼロ → 免除 (DW-S04)。受入全走: 免除しない。実 repo を読むテスト: `python3 tools/check_docs.py` と、insight / spool を読む test を焦点走 (login) で通してから段 7。
4. 裁定パッケージ (実装せず insight §に置く): (a) `checkout.workers` を主 checkout の local config に置くか (効果は予備診断 1 回のみ、採用判断は別 wave の実測が要る)、(b) sparse-checkout で `output/insights` を外すか (設計変更)、(c) 木の本数を減らす運用。推奨は (a) の別 wave 実測。
