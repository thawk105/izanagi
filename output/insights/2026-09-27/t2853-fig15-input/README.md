# [T-2853] 残り (5'') fig15 の生成器が追跡下の逐語写しを既定入力に取るようにし、描き直して旧図と値の差 0 を確かめた

- 作成: 2026-09-27 JST。wave `worktree-dev-wave-t2853-fig15-input` (背景 job)、着手時の基準 = local main `ad114fba0` (開始 gate fresh rc=0、`verbatim/startup-gate.log`)。依頼の逐語は `verbatim/request.md`。
- 正本の前段: 再実行計画 `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` §2.3 の fig15 行・§3.2・§5 項 2、前回の 17 図の描き直し `output/insights/2026-09-26/t2853-archive-inventory-figure-redraw/README.md` §2、作図規約 `tools/plotting/FIGURE_CONVENTIONS.md`。
- 位置づけ: 実装記録。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。新規計測は 0 で、計算は開発の検査 (焦点走・変異・受入) だけ。R2 の投入と fig15 の観測の再実施はしていない (scope 外、再実施には改めて認可が要る)。

## 0. 要約

1. fig15 (`mocc_witlight_four_arm`) の生成器 `tools/plotting/plot_mocc_witlight_four_arm.py` の既定入力を、repo 外の job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/`) から
   追跡下の逐語写し `output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/` に替えた (Codex author、D95、commit `779b984e4`)。job dir が撤去されても、既定の再現コマンドで図の値を再導出できる。
2. 描き直す前に、写しの 5 file (`summary.json`・`W1-result.json`〜`W4-result.json`) の sha256 が生成器の pin (`EXTERNAL_SHA256`) と 5 件とも一致することを確かめた (§1)。
3. login `pegasus02` (計測機の外) で `--evidence-root` を渡さずに描き直し、着地済み `docs/paper-story/figures/fig15_mocc_witlight_four_arm.provenance.json` と leaf ごとに全部比べた。
   **図の値を持つ key (arms・blocks・comparisons・exposure_ratios・measurement_conditions・artist_series・caption) を含む 11 key は leaf 差 0。** 差が出た 9 leaf は生成時刻・生成器 sha256・出力 path・PDF bytes・再現 argv だけで、**PNG は着地 file と bytes まで一致した** (§2)。
4. 着地 fig15 の 3 file の bytes は変えていない (凍結物。描き直しは repo 外 job dir にだけ置いた)。

## 1. 入力の sha256 の照合 (描き直しの前)

| 論理名 (生成器の pin の key) | 追跡下の写し | sha256 (写しの実測 = 生成器の pin) |
|---|---|---|
| `summary.json` | `summary.json` | `b1be3ebde10c20ea26de3956495f927d2baa8c06ecc1b7e2d7222f2795310698` |
| `W1/result.json` | `W1-result.json` | `ca8ab3ff579e3fb55b97447ebb7b647d34806a6fd452ad410051aca9e5bd4b50` |
| `W2/result.json` | `W2-result.json` | `473063aa741cc4c349931d987c902facbc5dcf6499b3692ea2cad3a27ac1e584` |
| `W3/result.json` | `W3-result.json` | `f68876600f1cd5b7300b030fb3cfa75509cc7a687858d6f12985051ce46e3642` |
| `W4/result.json` | `W4-result.json` | `197a2798de5ef53a7f6a32460f7ecfa5adbba8e853778b315d3b6e1839c36a6c` |

- 実測: 着手時 (14:4x JST、`sha256sum`) と描き直しの直前 (`verbatim/redraw-new.log` の `input sha256` 節) の 2 回、5/5 一致。写しの dir の `NORMALIZATION.md` が正規化した file に JSON 5 件は含まれない (正規化は行末空白のある log・md・patch だけ)。
- 原保存先の job dir は 2026-09-27 時点でまだ現存する。生成器は階層の名前が無い場所では写しの名前を読むので、写しの dir (階層の `W1/` などが無い) を指した描き直しは写しの file を読んでいる (provenance の `reproduction.argv` の `--evidence-root` が写しの絶対 path)。

## 2. 旧図との照合

### 2.1 方法

- 場所: Pegasus の login node `pegasus02` (計測機の外、FIGURE_CONVENTIONS §7)。python 3.10.12、matplotlib 3.10.9、numpy 2.2.6 (前回の 17 図の描き直しと同じ版)。
- 本番: 変更後の生成器 (commit `779b984e4`) を `--evidence-root` なしで実行し、出力は repo 外 job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-fig15-input/redraw-new/`)。14:56 JST、rc=0、png・pdf・provenance の 3 出力 (`verbatim/redraw-new.log`)。
- 対照: 変更前の生成器 (base `ad114fba0`) で原保存先から描いた (14:49 JST、rc=0、`verbatim/redraw-control.log`)。生成器の変更と入力の場所の変更を分けて見るため。
- 照合: 着地 provenance と描き直し provenance を JSON の leaf ごとに比べ、違う leaf を**除外せず全部**列挙した。png・pdf は実 file の sha256 を着地 file と比べた。script は repo 外 job dir の親の使い捨て `compare_fig15.py` (sha256 `795dba4e…`、前回の `compare_provenance.py` と同じ再帰比較) で、repo へは入れない。描き直しの script は `redraw-new.sh` (sha256 `384ccb18…`) と `redraw-control.sh` (sha256 `f5a0ba7d…`)。

### 2.2 結果

- 本番 (写しから): provenance の top-level 15 key のうち、差のある leaf を持つのは `generated_utc`・`generator`・`outputs`・`reproduction` の 4 key、計 9 leaf (`verbatim/compare-new.json`)。
  残る 11 key (`arms`・`artist_series`・`blocks`・`caption`・`comparisons`・`exposure_ratios`・`external_inputs`・`measurement_conditions`・`schema`・`source_inputs`・`tracked_inputs`) は leaf 差 0。

| 種類 | leaf 数 | 中身 |
|---|---|---|
| 生成時刻 | 1 | `generated_utc` |
| 生成器の sha256 | 1 | 着地後に生成器の source が変わった (着地時 `fba1c0af…` → 本 wave の `187bc762…`。記録であり現行 source を縛る pin ではない、図 README) |
| 出力の path / sha256 | 3 | 出力 prefix の違い (png・pdf の path) と PDF の bytes |
| 再現 argv | 4 | `--repo-root` (実行した worktree)、`--evidence-root` (原保存先 → 写しの絶対 path)、出力 prefix、それらを連ねた `command` |

- png の sha256 は着地 file と一致 (`11f28201…e966`)。pdf は不一致 (着地 `4af67848…`、描き直し `47206150…`)。PDF は matplotlib が生成日時を埋めるので時刻依存で、対照の描き直しでも不一致だった (図 README の「再現できるのは値であってバイト列ではない」のとおり)。
- 対照 (変更前・原保存先から): 差は 8 leaf で、着地図に対して差の出た leaf の path の集合は、本番より `--evidence-root` の 1 path が少ないだけ (対照は原保存先のまま。生成器 sha256・出力 path・PDF の値は本番と対照で別)。png は同じく bytes 一致 (`verbatim/redraw-control.log`)。
- 着地 fig15 の 3 file の sha256 は描き直しの前後で同じ (`verbatim/redraw-new.log` の `landed bytes before / after`)。
- したがって、fig15 は、観測の入力 5 file を追跡下の写しから読み (caption の言い方は追跡下の稿 `docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md` を `caption_source` として読む)、repo 外の job dir なしで値の差 0 で再現できる。

### 2.3 言わないこと

- 描き直した図を着地 file に置き換えていない。着地 provenance の `reproduction` は着地時 (2026-09-21) の argv のまま (`--evidence-root` に原保存先)。
- 観測そのもの (240 走) の再実施と R2 はしていない。値の一致は保存された 5 file からの再導出の一致であって、観測の再現ではない。

## 3. 何を変えたか

- 生成器 (+12 行、505 行): 写しの repo 相対 path の定数と、論理名 → 写しの file 名の固定対応 (`W1/result.json` → `W1-result.json` など 5 件) を足した。
  読み出しは file ごとに、`--evidence-root` 配下に階層の名前があればそれを、無ければ写しの名前を読み、どちらも既存の SHA-256 pin で照合する。
  `load_evidence` の `evidence_root` 既定と CLI `--evidence-root` 既定を `--repo-root` 配下の写しにした。原保存先も `--evidence-root` で渡せば従来どおり読める。
  pin の値と key 集合、`summary.json.inputs` の exact 照合 (原保存先の絶対 path)、`external_inputs` の論理名、統計・書式・作図・レイアウト検査・`validate_repo_closure` の argv 検査は変えていない。
- test (+10 行、535 行): 原保存先の root が無い環境で skip していた実データの 2 本 (`test_real_evidence_matches_results_document_when_root_present`・`test_landed_fig15_external_closure_when_root_present`) は、
  写しを読んで常に走る (test 名は docs・記録が名前で参照しているので変えていない)。合成 fixture を写しの位置へ平坦な名前で置き、`--evidence-root` を渡さずに `main()` を引数列で呼ぶ test を 1 本足した
  (公開 CLI のプロセス実行ではない。プロセス実行は §2 の描き直しが実データで行った)。
- docs (親): 図 README の fig15 節 (入力・再現・検査の 2 層の説明・§6 の適合・proof chain) と `tools/plotting/README.md` の入力の説明。着地 bytes の SHA-256 3 行は変えていない。

## 4. 段の経過 (実装面は Codex author、D95)

- 段 1 brief (`verbatim/s1-brief.md`): 親の provisional 裁定 P1 (論理名 → 写しの名前の固定対応、既定を写しに、原保存先も読める) と P2 (skip していた実データ 2 本は写しを読む)。
  brief 前に写しの sha256 と pin の一致 (5/5)、原保存先の現存、pin 閉包 (DW-O09: 生成器・test・図 README の変更前 sha256 の git grep は過去の insight 記録 2 件だけで、現行 source を縛る pin 無し) を実測した。
  段 2・3 は軽量版で省いた (DW-C00)。
- 段 4 裁定 (`verbatim/s4-ruling.md`): P1・P2 を採用、変異 M1〜M3 を事前登録。着地 fig15 の 3 file と図 README の着地 SHA-256 3 行は変えない。
- 段 5 実装 (`verbatim/s5-author-a.md`、Codex author 1 本、14:48〜14:53 JST): 生成器 +12 行・test +10 行 (上限 530・580 の内)。子の自走 harness で 28 PASS。統合 commit `779b984e4`。
- 親の描き直し (14:49 対照、14:56 本番): §2。
- 焦点走 1 回目 (変更 test file、DW-O26 の inventory 4 群、自走 harness のメタテスト、`verbatim/focus-1-summary.txt`、Elapse 42 s): 142 passed / 1 failed。
  赤は `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` で、作業ツリーの `git status` に親の未 commit の docs 編集 (`docs/paper-story/figures/README.md`・`tools/plotting/README.md`) が載っていたため。
  実装差分ではなく親の作業ツリーの状態に起因し (assertion の左辺の余剰は docs の 2 path だけ)、docs を記録 commit に入れた後の受入で再確認する。
- 段 6 レビュー (`verbatim/s6-review-A.md`、read-only 1 本で正しさ・整合と過剰・削除の 2 レンズ): NO-GO、所見 4 件はすべて docs と brief の記述。実装・test・値の比較・変異の見込みは静的に支持された。
  裁定 1 (`verbatim/s6-ruling-1.md`) で 4 件とも採用し、親が docs を直した (実装面の fix は無し)。
- 焦点再レビュー 1 巡目 (`verbatim/s6-focus-1.md`、記録の差分と一次資料を照合): 検算は全項目一致、NO-GO。`tools/plotting/README.md` に「外部原本の閉包」が残る (前回 M1 の partial) ほか、insight の限定 2 件。
  裁定 2 (`verbatim/s6-ruling-2.md`) で 3 件とも採用し、親が直した。
- 焦点再レビュー 2 巡目 (`verbatim/s6-focus-2.md`): GO。前回の全所見 (最初のレビューの M1 を含む) が closed、新規所見なし (DW-O16 の 3 巡の内)。
- 着手後に local main へ入った dev-wave 手順の改訂 (段 5 投入の直後に段 1 の consumer 検索を local main で再走する) を遡って当てた。
  生成器名と写しの path で `tools`・`orchestrator`・`docs`・`.claude` を git grep した consumer 集合は、base `ad114fba0` と local main `cc2e9672a` で同じ 8 file (差 0。うち `docs/paper-story/` の日付版 3 本は凍結スナップショットで触らない)。
- 記録前の三軸語の機械走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc=1 だが、hit の file 集合は前回の fig1 wave の走査と同じ (既存の較正記録 3 file と既存図の provenance) で、本 wave の file は 0 件。
- 段 7 の記録の前に local main を 2 回取り込んだ (`cc2e9672a` を merge commit `85429603c` で、`40a88da99` を `e43cb74c1` で。いずれも編集 file の重なり無し)。

### 4.1 段 1 brief の訂正 (レビュー S1)

- brief の「受理集合は広がらない」は不正確だった。広がらないのは受理される**内容** (5 file の bytes は SHA-256 pin で固定) で、受理される**配置**は広がった
  (平坦な名前だけの dir と、階層と平坦が混在する dir を新たに読める)。段 2・3 を省いた理由は「内容と正しさ防壁を変えない」に限る。

## 5. 変異 matrix (DW-M01〜M08)

- 対象 commit `779b984e4` (実装の最終 commit。段 6 に実装面の fix は無い)。同じ commit に固定した detached worktree `t2853-fig15-mut` で `tools/mutation_harness.py --runner-mode dispatch` を走らせた。
  runner は `tools/run_tests.py --force-dispatch orchestrator/tests/test_plot_mocc_witlight_four_arm.py -q -rf` に限った (生成器を import する test はこの file だけ、consumer 検索 §4)。
- 事前登録: 段 4 の M1〜M3 と、docstring だけを変える対照 C0。置換アンカーは生成 script (`mutation/make_specs.py`、sha256 `738b8043…`、job dir) が対象 file でちょうど 1 回現れることを assert した。
- probe (全件 SURVIVED 期待で観測 node を集める、15:05〜15:24 JST、`verbatim/mutation-spec-probe.json`・`verbatim/mutation-probe-summary.txt`): baseline PASSED、M1〜M3 は段 4 の kill 期待どおりの node が赤、C0 は SURVIVED。
- 本走 (観測 node の完全集合を KILLED 期待に登録、15:25〜15:52 JST、`verbatim/mutation-spec-final.json`・`verbatim/mutation-final-summary.txt`): baseline PASSED、**M1〜M3 の 3 件すべて KILLED (期待 node と完全一致)、C0 は SURVIVED**。変異の木は走行後も clean (dirty 0)。
- 結果 JSON の原本は job dir (`mutation/probe-results.json` sha256 `adcfac66…`、`mutation/final-results.json` sha256 `e5749015…`)。

| ID | 変異 | 殺した test | 単一理由 |
|---|---|---|---|
| M1 | 写しの名前の対応で `W1/result.json` の行き先を `W2-result.json` に | 平坦 fixture の既定入力 test、写しを読む実データ 2 本 | W1 の SHA-256 照合 (対応表の値だけが変わる) |
| M2 | `--evidence-root` の既定を原保存先に戻す | 平坦 fixture の既定入力 test だけ | 既定の読み出し場所。実データ 2 本は `load_evidence(REPO)` の関数既定を使うので影響を受けない (原保存先も現存) |
| M3 | 階層に無いときの写しの名前への fallback を外す | 平坦 fixture の既定入力 test、写しを読む実データ 2 本 | 読み出し 1 箇所 (写しの dir に階層の file は無い) |

## 6. 計算の費用 (D2212 項 4)

- 図の描き直し (本番・対照) は login で node 時間 0。新規計測は 0。
- 開発の検査の job Elapse (実測、いずれも 1 node): 焦点走 42 s、変異 12 job 計 149 s (各 job の `.e` file の Elapse の和、一覧 `verbatim/mutation-job-elapse.txt`)。合計 191 s ≈ **0.053 node 時間**。
- 受入全走は記録 commit の後に走るので、ここには書かない。

## 7. 残り

- (5'') の fig15 の入力はこれで閉じた。R2 (論文投稿前に投げる単位を決めて見積り、2 node 時間以上ならユーザー確認)、(1'') job body での保全口 opt-in、(4)、(6) は残り (worklog の T-2853)。
- 原保存先の job dir は撤去していない (本 wave の scope 外)。

## 8. 記録

- `verbatim/`: 依頼の逐語、段 1 brief、段 4 裁定、段 6 裁定、実装子の報告、レビュー、開始 gate、描き直しと対照の log、比較結果 JSON、焦点走・変異の要約。
  レビューの逐語 1 本は行末空白を除く可逆最小正規化をした (`verbatim/NORMALIZATION.md`)。Codex 出力の逐語 (`s5-author-a.md`・`s6-review-A.md`) はそれ以外は原文のまま。
- repo 外 job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-fig15-input/`: 描き直しの 3 出力 (`redraw-new/`・`redraw-control/`)、比較 script、codex の prompt・log・receipt、変異の spec と結果。
