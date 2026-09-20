# claim-evidence 稿 2026-09-20 版の作成 — wave 記録

`authority: none`

`docs/paper-story/claim-evidence/2026-09-20.md` を、2026-09-19 版 (`docs/paper-story/2026-09-19.md`、git blob
`bde3c0c6643288706878499cd238a2c73787f1a0`) の §3 / §6 / §7 / §8 / §9 全体から、数値・日付・判定の出所を一次資料に限って
作り直して追加した wave の記録である。**新規計測はしていない。** 前稿 `claim-evidence/2026-08-26.md`・版 9 本・`results/` 13 稿・
`figures/`・`docs/paper-story-backoff/` は 1 byte も変えていない。

- wave: `dev-wave-claim-evidence-2026-09-20`、branch `dev-wave-claim-evidence-2026-09-20`、job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-claim-evidence-2026-09-20/`
- 起点: local main `b7f970dfa507558f7fb669a5ab38958d6c76b57c` (2026-09-20、worklog entry 1711 までの fold を含む)。fresh worktree を
  `git worktree add` で作り submodule 3 層を初期化 (`dev_wave_submodule_init.py` rc=0、`git submodule status --recursive` に `-` 無し)。
  起動 gate `check_wave_startup.py --mode fresh --external-handoff` rc=0。wave 中に main は `efb0dee78` へ進んだ (peer 通知、[T-2789] の
  docs wave の land) が `docs/paper-story/` への差分は無く、導出起点は変えていない。
- 成果物: `docs/paper-story/claim-evidence/2026-09-20.md` (新規、706 行 / 210,524 bytes) と `docs/paper-story/README.md` の
  claim-evidence 系列表への 1 行。実装面ゼロ。版の履歴表には登録していない (系列の規則)。
- 依頼: 「論文の claim-evidence 稿 2026-09-20 版を作る (docs のみ)。着手直前の local main から fresh worktree。規則は README の
  『claim-evidence 系列』節: append-only、新稿は着手時点の最新版 (2026-09-19 版) の §3 / §6 / §7 / §8 / §9 全体から作り直す、
  出所は一次資料だけ、版の履歴表には登録しない。3 表と限定レジストリ (L01〜L28 を継承し、A-2 observed-positive・A-6・T-1998・
  A-1 attempt-0001・B-10 cohort 1/2・検証相・B-7 fixed5 の限定を追加採番)、limitations 節の統制稿を更新する。未着地の図・結果
  (fig10・cohort 2 後継図・裁定待ち T-2792 / T-2795 / T-2797) は完成済みとして取り込まない。README の系列表へ 1 行、README は受入の
  owned-path に入れない。段 6 は独立 read-only レビュー 1 本 (D2148 項 11)。規律 2 を緩めない。新規計測・gate・台帳の追加は scope 外」

## 1. 段 1 — brief と provisional 裁定

- 軽量版 (`DW-C00`): 段 2・3 を省き、段 5 は親の docs 編集、段 6 は read-only review 1 本 + 焦点再レビュー 1 本、変異 matrix は
  実装面ゼロで免除 (`DW-S04`)、受入全走は免除しない。brief の逐語は `verbatim/brief-s1.md`。
- 実測した前提: ストーリー 09-20 版は main に無い (README の「最新 = 2026-09-19.md」)。claim-evidence / README に byte pin する test は
  無し (`orchestrator/tests` と `tools` を grep して 0 件)。`figures/` に fig10 / fig8b は無い。[T-2792] / [T-2795] / [T-2797] は
  worklog archive (entry 1687 / 1691 / 1692) で「ユーザー裁定待ち」として起票され、裁定 D は無い。裁定 inbox
  (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) に本件の新裁定なし。`DW-O08` / `O09` / `O10` / `O11` / `O13` は不成立。
- **(P1)** 前稿 C12 (単回 4 cell の緑) は A-2 attempt `t2364-20260907b` が別 attempt として正式 protocol を完走したため行として残さず
  C2 / C18 へ吸収し、§7 の対応表と L24 で明示する。**(P2)** 採用候補の検証相は B-8 の要件本文に対する仕分けを本稿で行わず「次版で
  仕分ける」を継承し、L40 で限定を採番する。**(P3)** `results/` 稿は `[導出索引]`、certification.json / result.json / WAL / 事前登録の
  blob が `[権威 bytes]`。**段 6 の 2 本は (P1)〜(P3) を攻撃し、いずれも維持可能と判定した** (所見 12 = refuted。P2 は状態語の統一で足りる)。
- (c) 欄の閉語彙は前稿の 6 値から、2026-09-19 版 §9 の 7 種に合わせて「固定条件で certified な correctness」を足した 7 値にした
  (§1.3 に理由を明記)。この種別に置いた行は C2 (A-2 / A-6 の correctness。段 6 所見 4 で前稿の「実証済み」から移した) と C25 (検証相)。

## 2. 稿の作り方と一次資料

- 入力 5 節を全文読み (§3 1147〜1288 行、§6 1751〜2037、§7 2038〜2338、§8 2339〜3071、§9 3072〜3208)、前稿を全文読み、README の
  stale 注記 11 件 (09-19 版の導出起点 `a99425b66` より後に着地した事実) が指す一次資料を読んだ。
- 値の出所 (repo 内の権威 bytes): A-2 / A-6 の `certification.json` (`effects` / `status` / `source_commit` / `request_ids` /
  `a4_noise_floor_status`)、A-1 公開 leaf `result.json` (sha256 `372f199e…`、`workloads[].statistics`) と policy v3-sized
  (`authority`、arm 定義、`pairing.estimand`)、B-7 fixed5 の `certification.json` (`effects`、6 cell の `legacy_repetitions_observed` 1 /
  `performance_repetitions_observed` 5)、`between_run_noise_*.json` の `between_run.cv` 3 値、B-10 待ち方 grid の
  `b10_backoff_shape_provenance.json`、`output/s6-rounds/tally.json` (S-2 / S-3 の名目 p)、`calibration/registered/` の 8 file、
  `output/campaigns/*/reports/layer3_report.json` の 8 件、A-2 / A-6 policy の `scheduler.nodes` (= 5)。
- repo 外の権威 bytes (B-10 cohort 1 / 2 の集団報告、A-6 / [T-1998] / A-1 の WAL と raw、検証相の集計 JSON、official 床値の原本) は
  各 results 稿が起草時に SHA-256 を実計算して現物と照合した記録を引き、本 wave は directory / file の実在を `ls` で確かめた (9 path)。
  **本 wave はそれらを再計算していない** (稿 §6 に明記)。段 6 のレビュー子は独立に durable WAL・集団報告 JSON・summary JSON を開いて
  件数と値を数え直した (§3)。
- 前稿が引く権威 bytes / 導出索引の path の実在を `ls` で全数確認した。1 件だけ path が変わっていた —
  `output/insights/2026-07-10_s8a-axis-proposer-design-review.json` は `.json.gz` に圧縮されている (C9 の (b) に注記)。
- 稿が引く repo 内 path 93 件を script で実在検査し、欠は `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` の 1 件
  (保存 branch にあり main に無い、稿がそう書いている) だけだった。

## 3. 段 6 — read-only レビュー 1 本と焦点再レビュー 1 本

- **review-1** (Codex `gpt-6-astra`、effort `medium` (docs 権威)、sandbox read-only、08:02:49〜08:14:19 JST、38 model call、
  wall 688 秒、出力 16,417 bytes = `verbatim/review-out.md`、prompt = `verbatim/prompt-review.md`): **NO-GO、所見 12 件
  (must-fix 8 / should-fix 2 / nit 1 / refuted 1)。** 親が一次資料で検算し 1〜11 を real、12 をレビュー自身の判定どおり refuted とした。
  - 所見 1 (must-fix): §5.2 が B-7 fixed5 の correctness を legacy だけに縮めていた。権威 bytes は 6 cell とも legacy 1 + performance 5
    (計 36 記録) → 文を分けた。
  - 所見 2 (must-fix): 検証相の「30 verify」「未完走 2 件」は候補ごと、C2 (b) の「`verify_done` 12 件」は A-6 だけの件数 → 「各候補 30」
    「A-2 24 件 / A-6 12 件」へ。
  - 所見 3 (must-fix): G5 が右 tail まで「信頼区間を持たない」に含めていた (事前登録 §4.4 の Bonferroni 同時区間がある) → 書き分け。
  - 所見 4 (must-fix): C2 の (c) が「実証済み (科学的主張)」のままで、稿自身が導入した第 5 種と不一致 → 「固定条件で certified な
    correctness」へ移し、§1.3・§7 を追随。
  - 所見 5 (must-fix): C21 (d) / L34 の「再投入・再認可は判定されていない」が D2156 (attempt-0002 の 1 attempt 認可) と衝突 → 認可済みの
    過去 (gate で停止) と、次回の再認可待ち ([T-2792]) を分けた。
  - 所見 6 (must-fix): C15c (a) が「静的候補 (a) が G2 signal として再現した」と機序へ踏み込んでいた (t2774 §1 は「cycle 形は候補 (a) と
    整合」まで) → 観測と整合と未同定を分離。
  - 所見 7 (must-fix): §7 冒頭の「前稿の執筆時点の誤りは無い」と、C11 / L18 の「前稿の『screening は対象外』は誤り」が自己矛盾 →
    1 巡目は「例外 1 件」と書いたが、焦点再レビューが regressed (保存済み 7 件についての限定として読めば真) と判定し、
    最終形は「読みを分ける 1 箇所 (事実としては真、機構一般の制限としては偽)。執筆時点の誤りとして確定したものは無い」。
  - 所見 8 (must-fix): 2026-09-19 版 §7 からの脱落 5 件 (D1529 の欠測母集団の但し書き単位、D2090 の較正選別規則の事前性、D1637 の
    系列間で数値・図を共有しないこと、調整済み adaptive の認証と性能値の分離、定数 K の積モデル不成立) → L04 の復元と L51〜L53 の新設。
    §3 末尾と §6 の「落とした項目は無い」を「確認された脱落 5 件は復元、全数保持は未確定」へ。
  - 所見 9 (should-fix): B-8 の状態語「未取得」と末尾の留保が不一致 → 「充足未判定 (要件との対応は仕分け待ち)」に統一、C25 (e) の
    `要裁定` を「未起票 (次版)」と凍結解除の人間手番に分けた。
  - 所見 10 (should-fix): C5b / C5c の `[権威 bytes]` が「凍結値の再掲」を自称する insight だった → `output/s6-rounds/tally.json`
    (`nominal_p_s2_main_vs_c4` = 0.11538461538461539、`nominal_p_s3_main_vs_c5` = 1.0、`eligible_counts` 20 / 17 / 20) へ。
  - 所見 11 (nit): claim 行に紐づかない限定は L49 を含めて 5 つ → 表と §6 を訂正。
  - 所見 12 (refuted): (P1) / (P3) を理由とする差し戻しは不要 (レビュー自身の判定)。「上位互換」の語だけ「別 attempt で正式 protocol を
    完走した観測」へ改めた。
  - fix は job dir の `fix1.py` (置換ごとに出現 1 回を assert) で当てた。実装面ではない (docs の置換 script、repo には入れない)。
- **focus-1** (同 model / effort、08:21:47〜08:27:33 JST、18 model call、wall 341 秒、出力 6,846 bytes = `verbatim/focus-out.md`、
  prompt = `verbatim/prompt-focus.md`): 所見対応表は **closed 10 / partial 1 (所見 8: §6 に「落とした項目は無い」が残存) / regressed 1
  (所見 7: 「執筆時点で既に偽」の断定は保存集合の限定と機構の対応範囲を分けていない)**、新規 must-fix 2 (同じ 2 点)。
  レビュー子は権威 bytes を独立に数え直した — B-7 fixed5 36 記録、A-2 / A-6 の WAL 24 / 12 件、検証相の候補ごと 30 判定・未完走 2・
  未実走 1、右 tail 2 cohort の `qL` / `qU` 各 18 組、`tally.json` の `rounds` の再集計、claim 43 行・L 53 個・紐づかない 5 個。
- 残る 2 件は親が real と裁定し `fix2.py` で直した (§7 冒頭・L49・§7 表・C11 (d)・L18 の書き分け、§6 の全数保持の断定の除去)。
  `DW-O16` の上限 (3 巡) 内であり、前回の paper-story wave と同じく 3 巡目は起動せず、禁止句 (「執筆時点で既に偽」「落とした項目は無い」
  「例外 1 件」) の残存 0 件を grep で、行 43・L 53・path 93 件の実在・`check_docs` 違反なし・`git diff --check` rc=0 を再走して閉じた。

## 4. 検査

- `python3 tools/check_docs.py`: 違反なし (稿の作成後・README 追記後・fix1 後・fix2 後・fragment 追加後)。
- 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search`: rc=0、両 holdout (rr20 / rr80) の `conjunction_hits` は空、
  陽性対照 227 (結果 JSON = job dir `scan-1.json`)。
- 稿が引く D 番号 (D12〜D2164 の引用) が `docs/decisions.md` に 1 件ずつ実在することを grep で確認 (fix で加わった D1529 / D1866 /
  D2020 / D2021 / D2026 / D2080 / D2090 も)。
- 凍結物の不変: `git status --short` の変更は `docs/paper-story/README.md` (M)、`docs/paper-story/claim-evidence/2026-09-20.md`
  (新規)、spool fragment 2 片、本 insight のみ。README の版の履歴表に変更なし (レビュー子が `git diff` で確認)。
- 受入全走と land: **本 README の執筆時点 (記録 commit の前) では未実施。** 記録 commit 後の tip で `tools/dev_wave_wait.py acceptance`
  を投入し、結果はこの README には書かず worklog fragment と land の受領証に残す。README は owned-path に入れない (依頼)。

## 5. 工数

- codex 子 2 本 (review 1、focus 1)、author / fix 子 0 (docs-only、実装面ゼロ)。親の実走: fresh worktree 作成 (約 2 分)、一次資料の
  読み込みと稿の起草 (07:34〜07:57 JST)、fix 2 回。計算ノード job は受入全走のみ。

## 6. 言わないこと

- 本 wave は新規計測をしておらず、どの行の実証状態も進めていない。稿の (c) 欄は 2026-09-19 版 §9 と README の stale 注記が指す
  一次資料の分類であり、本 wave が判定したものではない。
- B-8 (種を変えた長時間実行による最終候補の検証) に対する検証相の仕分けは行っていない。[T-2792] / [T-2795] / [T-2797] の採否も
  予想していない。
- 前稿 (2026-08-26) の執筆時点の誤りを確定していない。前稿 C11 の「screening は対象外」は読みを分けて扱い (保存済み 7 件についての
  事実としては真、機構一般の制限としては偽)、それ以外の食い違いはいずれも「当時は真で後続が古くした」型と読んだ (探索した範囲での
  判断であり、誤りが無いことの証明ではない)。
- 段 6 の未照合範囲 (入力版 §8 の全節逐条照合、継承行すべての raw 再計算、全 repo 外 WAL・receipt・host 束縛の独立照合、76 項の限定の
  脱落の全数確定) はレビュー子が明記したとおり残っており、本 wave はそれを「確認済み」へ繰り上げない。

## 7. 逐語の可逆最小正規化 (DW-S07)

`verbatim/review-out.md` と `verbatim/focus-out.md` は Codex の最終メッセージで、`## 総括` の各行末に markdown の改行用の
半角空白 2 個があり `git diff --check` に抵触する。可視文字を変えない最小正規化として行末の空白列だけを除去した。復元は、下の行番号の
行末に `'  '` (半角空白 2 個) を戻す。

| file | 原文 sha256 / bytes | 正規化後 sha256 / bytes | 除去した行 (1 始まり) |
|---|---|---|---|
| `verbatim/review-out.md` | `af4f3e2a066128b98570ffc30b7c46ff6ff10c2cefe176f53197d75129a48f2b` / 16,417 | `672b8ba088e100fc86dcc2eac80c588f9187f7f19db91db3eeea23a9c804a7fb` / 16,407 | 152, 153, 154, 155, 156 (各 `'  '`) |
| `verbatim/focus-out.md` | `7819a9e8ebf3a518e562f39616603f78e13570bbe44db2d0038b8f90dc0bcaa3` / 6,846 | `b111056a0458a7609f2c49b0e17730a3a3485cd0fe5b8b918421ce638a1e9255` / 6,840 | 41, 42, 43 (各 `'  '`) |

原文は job dir (`review-out.md` / `focus-out.md`) と launcher の receipt (`artifacts/dev-wave-claim-evidence-2026-09-20/{review-1,focus-1}/`)
に残る。`verbatim/brief-s1.md` / `prompt-review.md` / `prompt-focus.md` は NFC・結合文字なし・行末空白なしで無変更。
