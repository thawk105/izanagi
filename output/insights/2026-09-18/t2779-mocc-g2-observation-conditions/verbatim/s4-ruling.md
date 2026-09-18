# 段 4 裁定 — [T-2779] (2026-09-18 15:30 JST 起草、本走の結果を見る前に確定)

裁定 inbox (`dev-wave-jobs/rulings-inbox/`) を再走査: 本 wave 開始後の新規は受入門番契約 (manager thread、14:53 JST) のみ → 受入投入時に従う。他に本 wave の前提を覆す裁定なし。

## 所見の裁定 (段 2 plan / 段 3 レンズ A / レンズ B)

| # | 所見 | real/refuted | 採否 | 反映先 |
|---|---|---|---|---|
| plan-1 | brief P1 の 0.05 (直接対応 arm) と 0.058 (合算) の混同。K=120 は 0.058 対 0 で 83%、0.05 対 0 で 72% | real | 採用 | 事前登録 (下記)、insight §4、brief 訂正 |
| plan-2 | 現行 S emitter に `stored ≠ txid` の abort は無い (decode 失敗 = magic 不一致でのみ abort、不一致は discriminator が検出) | real | 採用 | 静的設計 (insight §3)、operational-facts の誤記を裁定で明示 (原文は保持) |
| plan-3 | 2 番目以降の write の stamp は先行 publish の窓内に入る → 「stamp は窓を伸ばさない」は単一 write 限定 | real | 採用 | insight §3 |
| plan-4 | generic dispatch の後段 argv は `/bin/python3.10 -B` を明示 | real | 採用 | launcher (親) |
| plan-5 | dispatcher の時限は投入時刻基準・RUN 初観測時に再設定 | real | 記述訂正 | operational-facts |
| A-MF1 | = plan-2 (親資料の訂正) | real | 採用 | 同上 |
| A-MF2 | = plan-1 | real | 採用 | 同上 |
| A-S1 | L 行の I/O が W の lock 保持を伸ばし R の validation が `W_LOCKED` を見て拒否する率を上げる別経路 = 未実測の候補として併記 | real | 採用 | insight §3・§6 |
| A-S2 | 診断 arm の結果別の主張範囲表 (低下 / 差なし / 正例あり) と「受理集合を縮小」の限定 | real | 採用 | insight §1・§6 (表を逐語で) |
| A-S3 | BACK_OFF の問いを「witness off 固定で BACK_OFF だけの変更による検出率差」に限定、0 件は不在証明でなく同率は同等性証明でない、Q1 の 0/56 は歴史的参考 | real | 採用 | 事前登録、insight §1・§6 |
| A-S4 | thread_local 保持先の生存期間の静的論証 (validation 失敗は writePhase に入らない、INSERT/DELETE/decode 失敗はプロセス終了、unlockCLL は CLL だけ) | real | 採用 | insight §3 |
| A-S5 | 結果表の注記に「CP / Fisher は独立・同率試行を仮定した参考値、block 別件数を併記」 | real | 採用 | insight §5 |
| A-N1 | 「窓内 decode だけ」→「publish 直後は共有 body の decode・既存失敗判定・確保済み領域への保存」、短縮量は未実測 | real | 採用 | insight §3 |
| A-N2 | witlight と診断の併用は本設計の対象外と 1 文 | real | 採用 | insight §3 |
| B-MF1 | `defines` の値形式の拒否 (空文字・空白・`;`・`-D…` 文字列) | real | 採用 | runner v5: 値は `re.fullmatch(r"-?[0-9]+\|ON\|OFF", v)` に限定 (本 wave の 7 key の値域はすべて整数か ON/OFF)、selftest に不正値 4 例 |
| B-MF2 | 打切り・queue 未起動 block の標本会計 | real | 採用 | 事前登録 (下記「欠測規則」) |
| B-MF3 | 実走 runner の path + sha256 を block binding に保存 | real | 採用 | runner v5: `bindings["runner"] = {"path", "sha256", "bytes"}` を `run` 開始時に `__file__` から計算 |
| B-S1 | 親の集計手順で block 一覧・binding (pin / patch sha / defines / witness / runner sha) の照合を明記 | real | 採用 | 親の手順 (下記) |
| B-S2 | 投入前に 4 base_dir で e9e477ca の解決を確認、解析単位は B1〜B4 + 実 hostname | real | 採用 | 親の手順 |
| B-S3 | smoke の成功条件 = 3 走の退避済み JSON + summary の読戻し、G2 経路未発火はその旨、本走後は 4 result.json を列挙して summarize | real | 採用 | 親の手順 |
| B-S4 | masstree warmup への define 非流入 | real | **親が静的に確認済み**: `cmake/ThirdParty.cmake` 55〜78 の `masstree_build` は `bootstrap.sh → configure → make CXXFLAGS=…` の固定 command (VERBATIM)、`CCBENCH_*` は渡らない | insight §2 |
| B-S5 | 一時版での確認は selftest に限定、byte 同一で job dir へ退避してから smoke / 本走、commit 前に working tree と index の両方で不在確認 | real | 採用 | 親の手順 |
| B-S6 | 実測値の出所 (所要は v3 Q2 の外挿、queue 待ちは 1 例) を明記 | real | 採用 | insight §4 |
| B-N1 | 3 checkout・3 build + warmup 1 回として費用を記す | real | 採用 | insight §4 |
| B-N2 | arms 逐語に誤り無し | real | 記述 | — |

refuted: 0。scope 外の real 所見: 0 (gate・台帳・一般化の追加提案なし)。

## 設計の確定 (plan v2 = plan §2〜§8 + 上記の採用分)

1. **runner v5** (`probe/t2779_probe.py`、v4 起点、Codex author): plan §2 のとおり `BASE_CCBENCH_DEFINES` 抽出・`validate_defines` (key は固定列の 7 key に限定、**値は `-?[0-9]+|ON|OFF` に限定** [B-MF1])・`configure_argv(defines=)` は既存項の置換だけ・arm ごとの `configure_defines` を arm 自身の argv から・**`bindings["runner"] = {path, sha256, bytes}`** [B-MF3]・selftest に defines 受理 1 + 拒否 7 (未知 key / 接頭辞違い / 非文字列 / 空文字 / 空白含み / `;` 含み / `-D` 始まり) を追加。schema 据え置き、legacy 経路据え置き、`classify` / manifest / verifier・discriminator 呼出し / 逐次保存は不変。
2. **arms** (`probe/arms-t2779.json`): plan §3 の逐語 (3 arm、path は本 job dir の `verbatim/`)。
3. **標本**: 4 block (B1〜B4) × 30 round × 3 arm = 各 arm 120 走。smoke は別 block (`--rounds 1`)、本走に合算しない。**結果を見て増減しない。** launcher は `--rounds 30` を固定。
4. **投入**: generic dispatch、後段 argv は `/bin/python3.10 -B`、walltime 02:30:00、queue-wait 3600、grace 4200。投入元 = wave worktree (B1) + `t2779-node2/3/4` (B2〜B4)。投入前に 4 base_dir で `git rev-parse e9e477ca^{commit}` を確認 [B-S2]。
5. **witness 軽量化の静的設計**: plan §6 (S 出力を `M:1207` 直後へ、`M:1197〜1200` は共有 body の decode + 既存失敗判定 + thread_local vector への保存、publish 前に reserve、WriteElement に field を足さない、`stored ≠ txid` の abort は追加しない、不一致値は保持) + A-S1 / A-S4 / A-N1 / A-N2 / plan-3 を反映。本 wave では commit も実走もしない (P4 維持)。
6. **主解析の事前登録 (逐語、plan §5 + A-S3 + B-MF2)**:

   > 本走は 4 block (B1〜B4)、各 block 30 round、各 round に 3 arm を 1 回ずつ実行する。計画標本は各 arm 120 走とし、結果を見て増減しない。smoke、T-2774 Q1 / Q2 は本走に合算しない。
   > 主比較は ① `e9-diag-nowit` 対 `e9-instr-nowit`、② `e9-instr-nowit-bo1` 対 `e9-instr-nowit` の 2 本に固定する。②の問いは「witness off に固定した条件で、`BACK_OFF` だけの変更による検出率差」であり、0 件は不在証明でなく、同率・非有意も同等性証明でない。いずれも介入側の G2 signal 検出率が低下する方向の片側 Fisher を参考値として示す。主表示は arm 別の検出数・分母・Clopper-Pearson 両側 95% 区間。2 比較の未調整 p 値を示し、どちらか 1 つの p<.05 をもって family 全体の有意な効果とは判定しない。
   > CP 区間と Fisher は独立・同率 Bernoulli 試行を仮定する。node 内相関、決定的な回転順、時間変動はモデル化していない。block 別の arm 別件数を併記し、合算値だけから node 一般の効果を主張しない。検出力は独立試行・等標本・完全抑制・単一比較の片側 α=.05 の設計仮定で、基準率 0.058 なら 83%、直接対応 arm の点推定 0.05 なら 72% (計算値であり実測ではない)。
   > 計画数 120、保存済み走数 N、有効 verifier 判定数 m、G2 signal 数 k、failure、indeterminate、未開始数を分ける。主区間は k/m。failure・未開始を no-G2 と数えず、indeterminate も certified no-G2 と同一視しない。
   > **欠測規則**: 集計締切は 4 block の dispatch `.done` が揃った時点、または最初の投入から walltime + grace (13,200 秒) 経過時点の早い方。block ごとに (a) 保存済み (`result.json.runs` に収載)、(b) 開始証拠あり・未収載 (`runs/<ordinal>-<arm>/run.json` はあるが `result.json.runs` に無い、または `run.json` 不在で dir だけある)、(c) 未開始確認済み (dispatcher が QUE のまま終端、または `result.json` 不在で job の受理証拠あり)、(d) 状態不明、を区別して親の会計表に載せる。主解析は (a) だけを使い、(b) は「未完了」として分母に入れず、(c)(d) は計画数からの不足として明示する。揃わない block は補充せず、完走 block だけを事後選択したとは書かず、不足を明示する。原本は書き換えない。
   > 固定 cell で instr-nowit は k/N、diag-nowit は k′/N、bo1 は k″/N と報告できるのは分母条件を明示した場合に限る。診断 patch / backoff の寄与は検出率の比較まで。実行順序の直接観測ではなく、根因・必要性は確定しない。陰性は G2 不在の証拠でない。certified 昇格・pin 前進・変異探索の扱いは変えない。

7. **診断 arm の結果別の主張範囲 (A-S2、逐語で insight へ)**: 低下 → 「固定条件で、2 変更を束ねた介入と検出率低下が整合する」まで (cold 検査と validation 再読の寄与、(i)/(ii) の寄与、実装 / hook / verifier 仮定の三分岐は識別できない)。差なし → 「この標本・条件では低下を検出できない」(効果ゼロ・候補経路の不在・診断の無効性は言えない)。diag でも正例 → 「当該 producer / 計器条件で signal が残る」(元と同じ実行経路かは不明)。
8. **親の手順** (B-S1 / S2 / S3 / S5): author の一時版は unit1 worktree の `probe/` (untracked) → 親は login で `selftest` と `python3.10 -c` の構文・import 確認だけ → byte 同一 (sha256 一致) で job dir `probe/` へ退避 → 以後の smoke / 本走は job dir の版だけを使う → unit1 worktree の一時版を消し `git status --porcelain --untracked-files=all` と `git diff --cached --stat` で不在を確認。集計は `summarize --inputs <B1..B4 の result.json>` を列挙して 1 回、その前に各 block の `bindings.arms[*].{pin, patches[].sha256, configure_defines, witness}` と `bindings.runner.sha256` を 4 block で照合し一致を insight に記す。
9. **記録**: insight `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md` (+ verbatim)、worklog fragment 1、decisions fragment 0、failures fragment は新規欠陥が出た場合のみ。
10. **順序**: author → 親 selftest → 退避 → 4 base_dir の e9e477ca 解決確認 → compute smoke (1 node、`--rounds 1`) → 本走 4 block 同時投入 → 集計 → 段 6 review 2 本 (A = runner v5 + 静的設計、B = 実行・収集・集計) → 段 7。

## 変異事前登録 (DW-M01)

repo の実装面差分 0 (runner・arms は job dir、insight は docs) → DW-S04 により免除。runner v5 の fail-closed 挙動は `--selftest` に置き親が login で実走する。受入全走は免除しない。

## 親 brief の訂正

- P1: 「0.05〜0.058 対 0 で K=120 は 0.83」→「0.058 対 0 で 0.83、直接対応 arm の 0.05 対 0 で 0.72」。所要 22 秒/走は v3 Q2 (5 arm block) の外挿で上限ではない。
- P3: 「`stored == txid` 自己検査」→ 現行は decode 失敗 (magic / 長さ) でのみ abort、不一致値は S 行に残り discriminator が検出。「stamp は publish 前で窓を伸ばさない」→ 単一 write または当該要素自身の publish との関係に限定。「E 行は 058d0c4e にも同位置」→ 運用事実からの引用で独立照合は未実施、E の時間寄与がゼロとは言えない。
- 環境: dispatcher の時限は投入時刻基準で RUN 初観測時に再設定。
