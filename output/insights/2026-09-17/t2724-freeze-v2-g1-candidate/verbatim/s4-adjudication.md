# 段 4 裁定 — [T-2724] freeze v2 g1 候補 (2026-09-17 01:40 JST)

裁定 inbox: main は wave 開始時 `1042a1bc9` から動いていない (実測)。

## レンズ A の所見

| # | 判定 | 採否 | 処置 |
|---|---|---|---|
| A-1 未退避 namespace の全所在 (should) | real | 採用 | 全 151 worktree を実測: official namespace を持つのは T-2698 (result 込み 1 run) と T-1851 (`journal.jsonl` + `launch_certificate.json` だけの 3 run、result.json 無し) の 2 本。T-1851 の 3 run は `_official_earlier_floor_results` (HF:1851〜1856、`missing_ok=True` → continue) が skip するので最早適格判定に影響しない。本 wave は T-2698 の namespace だけを退避し、T-1851 の失敗 run の退避は本題外の掃除として記録に残す (裁定パッケージの注記) |
| A-2 N7 の全 branch 一般化 (should) | real | 採用 | 「成果物を保持する checkout / それを継承する branch で clean scan が赤」に限定。clean scan 本体は `s8b_floor_campaign.py:5515` |
| A-3 hold 中の実 repo scan test がもう 1 本 (should) | real | 採用 | `test_s8b_repo_scan_invariant.py` と `test_s8c_preregistration_invariant.py::test_wave_files_…` の 2 本を併記。「受入は赤にならない」は「この 2 本は既定 hold で走らない。受入全走の結果は実走で確かめる」へ |
| A-4 guard 静的判定と実行の区別 (should) | real | 採用 | 実行結果を別に記録する |
| A-5 N4 / N5 の限定 (should) | real | 採用 | N4 = 観測時点の cwd 走査 0 件、evacuate 直前に再確認。N5 = 最初の拒否は `no-active-ratified-freeze`、active 成立後に `no-approved-spec` |
| A-6 隔離 restore は step 4 を代替しない (must-fix) | real | 採用 (記録の形) | 下記「P1 の裁定」 |

## レンズ B の所見

| # | 判定 | 採否 | 処置 |
|---|---|---|---|
| B-1 床値は現行 oracle の勝敗閾値でない (must-fix) | real | 採用 | judge は「floor は入力にも argmax の tie-break にも使わない」(`s8b_oracle_judge.py:463`)。D1985 で床値由来 3 述語を撤去、D2024 で残るのは driver の null 拒否・budget → 資源上限・report の解決経路。brief の「差の検出下限」は撤回。記述は「g1 は floor / budget / 出所を充填し、driver の `floor-null` / `budget-null` 拒否を解く。床値を性能差の閾値としては消費しない」 |
| B-2 採用推奨を数値だけで導かない (must-fix) | real | 採用 | (c) の推奨は「現行 formula v2 と protocol に従ったこの 1 走行の床を、現行契約の候補充填として採用する」に限定。between-run・誤判定率・検定力は保証しない |
| B-3 択一の代替案と依存関係 (must-fix) | real | 採用 | D1311 (最早適格 run 固定) により追加 run は床を差し替えない。択に「延期」「追加観測 (証拠の追加であって差し替えでない)」「protocol 再検討 (別件)」を足す |
| B-4 main 導入と A/X は技術上一体でない (should) | real | 採用 | 批准が要るのは G / A / X と H の履歴条件であって branch 名 main ではない。「同時承認を求める」は運用方針として書く |
| B-5 restore 前の授権 (must-fix) | real | 採用 (記録の形) | 下記「P1 の裁定」 |
| B-6 W-4 の呼び手の説明 (should) | real | 採用 | 「入口 = CLI、実行主体 = operator」。出力先は `output/s8b-oracle-manifest-candidates/` 配下固定 (`s8b_oracle_manifest.py:832`) |
| B-7 T-750 残余を落とさない (must-fix) | real | 採用 | R-3 / worklog の新文面は「本手順の残件」に限定し、T-750 package P-1〜P-4 への参照を残す (P-1 は pinned literal 形で暫定、P-3 は批准 proof chain に budget authorization field が無い構造が現行にも残る) |
| B-8 W-3「残る手番」の実施状態 (should) | real | 採用 | W-3 / R-3 / worklog / package を同じ実施状態 (隔離生成済み、打ち切り = main 導入は未裁定) に揃える |
| B-9 budget 入力 path の権威 (should) | real | 採用 | 「既存 fixture・過去計画に合わせ本 wave の保存先として採る」と明記。producer が比較するのは解析後 canonical bytes で、raw 末尾改行の有無は機構の要求でなく保存規則 |
| B-10 brief の観測 / 推論の混在 (should) | real | 採用 | insight で N1〜N7 を限定形に書き直す |
| B-11 「producer 全検証通過」の射程 (should) | real | 採用 | README にコード上の検査項目・実行で確認した事実・未検証を分けて書く |

## P1 の裁定 — restore 以降を隔離 chain で実施する

両レンズが一致して「保存 branch は D2077 step 4 (打ち切ると決めてから restore) の決定を代替しない」と指摘した。real として採用する。そのうえで親は次のとおり決める。

- **実施する。** 根拠は依頼文の逐語「完走した official 床値 result … を入力に … freeze v2 g1 候補 document を作る」「候補は … へ一度きりの追加で書き」「result の読取りは [T-2386] (D2077 / D2078 …) に従い」。候補生成は D2077 step 4〜6 (restore → commit → generate) 無しには機構上不可能であり、依頼は D2077 を引用したうえで生成を指示している。これを候補生成 (step 5〜6) の授権と読む。
- **打ち切り決定 (step 4) は本 wave では下さない。** 依頼は「人間承認の受領証発行まで進めるかを裁定パッケージで返す」としており、打ち切り = 成果物を main に載せて以後の official 床値を止める判断は裁定 (a) で人間が行う。restore と X1 / X2 を base から分岐した保存 branch に限定するのは、step 7 の帰結 (成果物を持つ checkout で clean scan 赤) を main へ及ぼさないための実施形であり、D2077 の例外を新設するものではない。
- **記録は「D2077 step 4 の打ち切り決定を未裁定のまま、候補生成を保存 branch に隔離して実施した」と事実で書き、「D2077 を満たした」とは書かない。** 固定退避先の bundle は restore 後も残る (EV:225〜) ので、chain branch を捨てても入力は再取得できる (可逆性の根拠は data であり、判断の取消しの根拠ではない)。
- 停止して裁定へ返す案は却下: ユーザーの常設指示 (裁定へ返さず codex と決める、可逆で低影響の判断は諮らない) に反し、隔離実施は main に不可逆な影響を残さない。

## plan v2 (確定)

1. EnterWorktree(path=T-2698 木) → evacuate 直前に writer 不在を再確認 → `python3 -m orchestrator.campaign.s8b_floor_evacuation evacuate --env-tag pegasus` → bundle の `manifest.json` を確認 (run 1 件、5 file の sha256)。
2. EnterWorktree(path=chain 木) → submodule 初期化 (`dev_wave_submodule_init.py`、木の中身で確認) → EINTR 欠落 2 file を `git checkout -- <path>` で戻す → `git status` clean → restore → budget 入力 `output/s8b-freeze-budget-inputs/g1.json` (承認文書 `budget` の canonical bytes、改行なし) → `git add` 6 file → commit X1 (AI-Agent role=integrator) → generate (argv は plan どおり) → 静的検証 (canonical bytes 一致、sha256、`_parse_generation_document`、`frozen_at_head == X1`、`resolve_active_generation` が `no-active` 例外) → commit X2 → `search` 走査 (rc=1、hit = 専用 path のみを期待) → 射影 (三軸を除く) を job dir へ。
3. EnterWorktree(path=wave 木) → docs 訂正 (runbook W-3 / W-4 / §5 R-3、budget 手順書 §2 の現況注記) → insight README + package.md + evidence → fragment (worklog: T-750 更新、decisions: D 2 件) → commit (role=manager) → `check_docs.py`、`spool_fold.py --dry-run`、`search` 走査 (wave 木 rc=0) → 段 8 → 段 9。

実装面差分ゼロ → 変異 matrix は `DW-S04` により免除。受入全走は免除しない。実 repo を読む test (`test_frozen_artifacts.py`) は段 7 前に wave 木で実走済み (5 passed) — docs commit 後に再走する。

## scope 外として裁定パッケージへ送る

- T-1851 の失敗 run 3 件の退避 (掃除)。
- growth hold 2 本の扱い。
- T-750 P-1 (pinned literal の恒久形) / P-3 (budget authorization の proof chain) の残余。
- `wired_min_rel_floor` の再検討 (protocol 変更 = 別件)。
