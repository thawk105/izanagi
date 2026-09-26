# [T-2853] 残り (1') 保全口の inventory に R1 の入力一式の残りを足した / (5') 生成器のある 17 図を描き直して値の一致を確かめた

- 作成: 2026-09-26 JST。wave `worktree-t2853-archive-inventory-figure-redraw` (背景 job)、着手時の基準 = local main `74e6d2f23` (開始 gate fresh rc=0、`verbatim/startup-gate.log`)。
  段 7 の前に local main `510aaf39d` (docs と ComSys 原稿の前進) を取り込んだ (`4425be4c2`)。依頼の逐語は `verbatim/request.md`。
- 正本の前段: 写し稿 `output/insights/2026-09-23/t2853-repro-package-archive/README.md` (§5 R1 の入力一式)、計画稿 `output/insights/2026-09-23/t2853-figure-rerun-plan/README.md` (§5 項 1 描き直し)、
  保全口の実装記録 `output/insights/2026-09-23/t2849-comparison-harness-impl/README.md` (D2233)。設計判断は同 wave の decisions fragment。
- 位置づけ: 実装記録。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。計算は開発の検査 (焦点走・変異・受入) だけで、測定はしていない。

## 0. 要約

1. **(1')** 標準評価経路の trace 保全口 (env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in) の `inventory.json` に、保存 trace を後で verifier に掛け直す (R1) ための入力 — verifier の等価 argv・repo commit・pin (完全 SHA と宣言値)・patch (bytes と sha256)・verifier module の sha256 — を D2160・B-8 の runner v5 と同じ名前で足した。
   保全時に source の HEAD と patch を build 時の source evidence と照合し、合わなければ inventory を `failed` にする。評価結果・verdict・WAL・受領証は変えていない (D2233 項 4、規律 2)。
2. **(5')** 生成器のある 17 図を login `pegasus02` (計測機の外) で描き直した。17 図とも rc=0、図の値の差は 0、PNG は 17 図とも着地 file と bytes まで一致した。node 時間 0。
3. 段 6 でレビュー 2 本が同じ must-fix (照合の欠如) を、親の実測と焦点再レビューが同じ must-fix (短縮 pin への完全一致) を独立に出し、fix 2 巡で閉じた (§3)。

## 1. (1') 保全口の inventory に R1 の入力一式の残りを足した

### 1.1 何を足したか

env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in (D2233) が検証 1 反復ごとに書く `inventory.json` に、保存 trace を後で verifier に掛け直す (R1) ための入力を、
D2160・B-8 の runner v5 (`verify_phase_runner.py`、写し稿 §5.1) と同じ名前で足した。既存の key・配置・status 規則はそのまま。

| key | 中身 | 出所 |
|---|---|---|
| `verifier_invocation` | `"in-process"` | 標準経路の判定は CLI でなく `verify_trace_dir_with_capability` の in-process 呼出しだったことの明記 |
| `verifier_argv` | `[python の realpath, -B, -m, orchestrator.verifier, <元の一時 dir>, --json, --expected-commits, <N>, --protocol, <P>, --ccbench-root, <source root>]` | runner v5 の `verifier_argv` と同じ形。N は反復の commit witness (in-process 呼出しに渡した値)、P は genome の protocol、source root は `SourceEvidence.source_root`。trace が witness まで届かなかった反復は `null` |
| `repo_head` | orchestrator を含む repo の `git rev-parse HEAD` | runner v5 と同じ。dirty は記録しない (D320)、verifier の bytes は下の module sha256 が束縛 |
| `ccbench_pin` / `ccbench_pin_declared` | 解決済みの完全 SHA (source root の HEAD) / 呼び手が宣言した pin (現行 `pin.CURRENT_PIN` は 7 桁) | |
| `patch_sha256`・`patch_bytes`・`patch_path` | source root の `git diff --binary HEAD --` の sha256・長さと、その bytes を zstd で保全した `patch/ccbench.diff.zst` | 標準経路の patch の実体。`source_digest._tracked_diff_sha256` と同じ argv・sanitized env・source root |
| `tracked_diff_sha256` | `SourceEvidence.tracked_diff_sha256` (build 時に束縛した diff の hash) | |
| `verifier_module_sha256` | `orchestrator/verifier/*.py` の名前 → sha256 (非再帰) | runner v5 と同じ |

- 保全時に **source root の HEAD が宣言 pin で始まること** (build 側 `buildcache._verify_ccbench_commit` と同じ前方一致) と **patch の sha256 が `tracked_diff_sha256` と一致すること** を確かめ、どちらか違えば inventory を `failed` にする。
  照合は保全の status だけに効き、評価結果・verdict・例外・WAL・受領証は変えない (D2233 項 4)。標準評価経路の反復は常に `SourceEvidence` を保全へ渡すので、その経路の `complete` の inventory は「build 時の source と同じ pin + patch」を持つ。
  evidence が渡らない呼出し (関数の直接呼出し。試験 `test_multiple_archives_and_streaming_counts` が使う) では R1 の source 系の項目 (`verifier_argv`・`ccbench_pin`・`ccbench_pin_declared`・`patch_*`・`tracked_diff_sha256`) を null にしたまま `complete` になり、この保証は無い。
- 取得はすべて env が設定されたときの保全処理の内側で行う。env 未設定なら、追加した保全処理では git・hash・zstd を一切呼ばない (試験で確認)。
- git の起動は `pipeline._archive_git` の 1 箇所 (固定 argv `rev-parse HEAD` / `diff --binary HEAD --`、CCBench を実行しない) に寄せ、`test_ccbench_spawn_sites.py` の review 済み起動箇所の登録簿に理由つきで登録した。
- 変えていないもの: 判定 (`_execute_verification_repetition` の abort 理由・verdict)、verify fan-out の remote 反復 (兄弟 node の反復は従来どおり保全対象外)、job body の opt-in 配線、WAL・proof chain・受領証・campaign lock の schema。

### 1.2 R1 の組み方 (この inventory 1 件から。実行はしていない)

1. `files[].archive_path` の zstd を戻し、`files[].sha256`・`bytes` と照合する (元の一時 dir は `original_directory`、argv の trace dir と同じ path)。
2. `repo_head` を detached worktree で取り出し、`orchestrator/verifier/*.py` の sha256 を `verifier_module_sha256` と照合する。
3. CCBench を `ccbench_pin` (完全 SHA) で checkout し、`patch_path` を戻して `git apply` し、sha256 が `patch_sha256` と一致することを確かめる。
4. `verifier_argv` の trace dir を手順 1 の復元 dir、`--ccbench-root` を手順 3 の checkout に読み替えて CLI を実行する。新しい版で掛けた結果は旧判定を置き換えない (規律 7)。

試験 `test_inventory_records_r1_inputs` は、tmp の git repo を source root にした評価で、手順 3 (pin の checkout に復元 patch を当てると source と同じ内容になる) まで実際に通す。

## 2. (5') 生成器のある 17 図の描き直しと一致の確認

計画稿 (`output/insights/2026-09-23/t2853-figure-rerun-plan/README.md`) §5 項 1 の実行。node 時間 0。

### 2.1 方法

- 場所: Pegasus の login node `pegasus02` (計測機の外、`tools/plotting/FIGURE_CONVENTIONS.md` §7)。python 3.10.12、matplotlib 3.10.9、numpy 2.2.6。
- 対象: 計画稿 §0 項 1 の 17 図 (fig2b・fig2c・fig3b・fig3c・fig4〜fig15 と fig8b)。fig1 (生成器なし) と対象外の fig2・fig3 は含めない。
- コマンド: `docs/paper-story/figures/README.md` の各図の「再現」節の逐語から、出力 prefix だけを repo 外の job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-archive-inventory-figure-redraw/redraw/`) に替えた。
  fig2c の `MEASUREMENT_ROOT` は着地 provenance の `external_source_locator.root_at_generation` (`/work/1/SFC/tanab/b10-backoff-grid-runs5`)。
  fig15 は生成器の既定の入力 (`dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/`) が現存したのでそのまま使った。
- **fig2c と fig4 の生成器は出力 prefix が repo の外だと拒否する** (fig2c `repo artifact path leaves repository` rc=2、fig4 `FigureDataError: path leaves repository` rc=1、`verbatim/redraw.log`)。
  この 2 図は wave の worktree 内の一時 dir `redraw-tmp/` に描き、job dir へ移して一時 dir を消した (移した後の `git status --porcelain` は 0 行)。他の 15 図は job dir へ直接描けた。
- 実行: fig3b を 14:00 JST に単独で、残り 16 図を 14:01〜14:02 JST に script (`redraw.sh`、sha256 `497a5d69…`) で、fig2c・fig4 を 14:02 JST に一時 dir で。17 図とも rc=0 で png・pdf・provenance の 3 出力が出た
  (script 内の 14 図の rc は `verbatim/redraw.log`、log の外で実行した 3 回の rc と出力時刻は `verbatim/redraw-extra-runs.md`)。
- 照合: 着地済みの `docs/paper-story/figures/<図>.provenance.json` と描き直しの provenance を JSON の leaf ごとに比べ、違う leaf を**除外せず全部**列挙した (`compare_provenance.py`、sha256 `866b9b2b…`)。
  列挙した差を path の形で 8 種に分類し、どの種にも入らない差が 1 件でもあれば rc=1 にした (`classify_diff.py`、sha256 `2cef37ef…`、rc=0)。script はどちらも repo 外の job dir に置いた親の使い捨てで、repo へは入れない。
  あわせて PNG は実 file の sha256 を着地 file と比べた。

### 2.2 結果

- **17 図すべてで、図の値 (数値・系列・軸・caption・可視文字・判定) に差は無かった。** provenance の値を持つ key (`data`・`cells`・`artist_series`・`text_contract`・`caption` など、図ごとに名前は違う) は、下の表の「verifier 版の説明文」(fig2c の `data[]` の下にある説明の文字列 3 件で、判定値ではない) を除いて leaf 単位で全部一致した。
- **PNG は 17 図とも着地 file と bytes まで一致した** (実 file の sha256、17/17、対照表 `verbatim/png-sha256.txt`)。bytes が違ったのは PDF だけで、PDF は matplotlib が生成日時を埋めるので時刻依存である (図 README の「再現できるのは値であってバイト列ではない」のとおり)。
- 違った leaf は 17 図で計 142 件、分類は次の 8 種で未分類 0 件 (`verbatim/classify.log`)。

| 種類 | 件数 | 中身 |
|---|---|---|
| 生成時刻 | 17 | `generated_utc` |
| 出力の path / sha256 | 51 | 出力 prefix の違いと PDF の bytes |
| 再現 argv | 33 | 出力 prefix の違いと、生成器が自分の位置から決めた `--repo-root` (実行した worktree の path) の違い (fig9・fig10・fig13・fig14・fig15 の 5 件、`verbatim/compare.log`) |
| 生成器の sha256 | 9 | 着地後に生成器の source が変わった (記録であり現行 source を縛る pin ではない、図 README) |
| 依存・検査器の sha256 | 5 | fig2c の依存 `tools/plotting/plot_backoff.py`、fig4 の入力 admission の validator 4 件 |
| 入力 file の sha256 | 2 | fig12 の `.claude/agents/planner-v4.md` (D2233 で T-2849 K0 の任意入力の節を足した改訂)。図が描くのは役割名と流れで、図の内容の差は 0 |
| verifier 版の説明文 | 24 | fig2b・fig2c・fig4 の campaign の `campaign_verifier_epoch` の scope 文 (25/27 path → 96 path の説明) と `verifier_assessment_basis` (値 `recorded-at-original-verifier-epoch`) の追加。当時の判定をそのまま使う旨の説明で、判定値ではない |
| 付帯 field の追加 | 1 | fig6 の `study` (`paper-story-a2-certification`) |

- したがって、生成器のある 17 図は保存データから値の一致で再現できる。R2 (測り直し) と G は本 wave では行っていない (計画稿 §5 項 3・4 のまま)。

### 2.3 言わないこと・残り

- 描き直した図を着地 file に置き換えていない (凍結規則。出力は job dir にだけある)。
- fig1 の生成器の作成と fig15 の repo 外入力の写しは本 wave の外 (依頼どおり)。fig15 の入力は今回まだ既定の path に現存した。
- 生成器の説明文の更新 (`campaign_verifier_epoch`) で着地 provenance と現行生成器の出力が文面上ずれているが、着地 bytes の同一性は各図の着地 test が守っており、本 wave は provenance を書き換えない。

## 3. 段の経過 (実装面は Codex author、D95)

- 段 1 brief (`verbatim/s1-brief.md`): 親の provisional 裁定 P1〜P6。段 2・3 は軽量版で省いた (設計の択一は段 4 で親が決めた)。評価経路の file なので段 6 の敵対レビュー 2 本・変異・受入は残した。
- 段 4 裁定 (`verbatim/s4-ruling.md`): plan v2、test 4 本、変異 M1〜M9 と対照 C0 の事前登録。
- 段 5 実装 (`verbatim/s5-author-a.md`、Codex author 1 本、14:12〜14:18 JST): production 51 行・test 106 行。統合 commit `3962394dd`。
- 焦点走 1 回目 (22 file、`verbatim/focus-1.log`): 10 failed / 3,933 passed。test の fixture (tmp git repo) に Silo の proof source が無く certified が偽になった 8 件と、`test_ccbench_spawn_sites.py` の起動箇所の登録漏れ 2 件。
- 段 6 レビュー (`verbatim/s6-review-A.md` 正しさ・整合、`verbatim/s6-review-B.md` 実効性・過剰・削除): 両方 NO-GO、共通の must-fix は「patch と HEAD を検証の後に生きた checkout から取るので、build 時の source とずれても complete になる」。裁定 1 (`verbatim/s6-ruling-1.md`) で段 4 の「一致を gate にしない (記録だけ)」を撤回し、照合を入れた。削除候補は両レンズとも「削らない」。B の nit (test の広い差し替え) は成果物を変えないので採用しない。
- fix 1 (`verbatim/s6-fix-1.md`、14:29〜14:34 JST): 照合、git 起動の 1 helper 化と登録、fixture の修正、test 2 本の追加。commit `d6290aece`。焦点走 2 回目 (`verbatim/focus-2.log`): 3,945 passed / 0 failed / 14 skipped。
- 焦点再レビュー 1 巡目 (`verbatim/s6-focus-1.md`) と親の実測 (`pin.CURRENT_PIN = "6810666"`、campaign lock 30 件の `ccbench_commit` はすべて 7 桁、build 側は前方一致) が独立に「完全一致の照合は本番で恒常的に failed」を出した。裁定 2 (`verbatim/s6-ruling-2.md`)。
- fix 2 (`verbatim/s6-fix-2.md`、14:44〜14:48 JST): 前方一致・完全 SHA と宣言値の記録・test 1 本。commit `a8282c4fe`。基準からの追加行は production 64・test 191 (上限 120・280 の内。test の上限は裁定 1 で 200 から上げた)。
- 焦点再レビュー 2 巡目 (`verbatim/s6-focus-2.md`): GO、新規所見なし (DW-O16 の 3 巡の内)。
- 単独走 (D325、M1 形): `test_t2853_trace_preservation.py` 18 passed (`verbatim/focus-3.log`)、`test_ccbench_spawn_sites.py` 73 passed / 2 skipped (`verbatim/focus-4.log`)。
- 段 7 の記録レビュー (Codex read-only 1 本、`verbatim/s7-review-record.md`): NO-GO (must-fix 2・should 2・nit 1)。親が一次資料で裏取りし 5 件とも real と裁定して直した — (1) `complete` の保証を evidence が渡る標準経路に限定、
  (2) 再現 argv の差に `--repo-root` の 5 件を含める、(3) PNG の実 file の対照表・変異 job の Elapse の一覧・log の外で実行した 3 図の rc を逐語に追加、(4) worklog の carry から落ちていた R2 の見積りの未了 (fig10 は要確認、fig13・fig4 は単価が無く未判定) を戻す、(5) env 未設定の無呼出しを「追加した保全処理では」に限定。

## 4. 変異 matrix (DW-M01〜M08)

- 対象 commit `a8282c4fe` (fix 2 の後の実装の最終 commit)。同じ commit に固定した detached worktree `t2853-mut` で `tools/mutation_harness.py --runner-mode dispatch` を走らせた。
  runner は `tools/run_tests.py --force-dispatch orchestrator/tests/test_t2853_trace_preservation.py -q -rf` に限った (pipeline.py は campaign の contract loader 閉包にあり、未 commit の変異は他の test を drift 層が一律に殺すため。t2849 insight §6 と同じ理由)。
- 事前登録: 段 4 の M1〜M9、段 6 裁定 1 の M10・M11、裁定 2 の M12 と、docstring だけを変える対照 C0。置換アンカーは生成 script (`mutation/make_specs.py`、sha256 `5412daba…`、job dir) が対象 file でちょうど 1 回現れることを assert した。
  M8 は「env 未設定の経路に verifier module の hash を 1 行足す」、M9 は「呼出し側の保全の例外境界を `OSError` に狭める」(git の失敗が評価へ漏れる) とした。
- probe (全件 SURVIVED 期待で観測 node を集める、15:10〜15:28 JST、`verbatim/mutation-spec-probe.json`・`verbatim/mutation-probe-summary.txt`): baseline PASSED、12 変異すべてで名指しの test を含む赤、C0 は SURVIVED。
  名指しの外の赤は同じ 1 行の変異から来る同じ理由のもの (M4: evidence 無しの直接呼出し test でも同じ行が落ちる、M5: pin を見る他の 2 test、M6: patch の hash 不一致で保全が failed になり complete を期待する 4 test、M9: 既存の保全失敗の test 群も同じく境界の外へ漏れる)。
- 本走 (観測 node の完全集合を KILLED 期待に登録、15:29〜16:07 JST、`verbatim/mutation-spec-final.json`・`verbatim/mutation-final-summary.txt`): baseline PASSED、**M1〜M12 の 12 件すべて KILLED (期待 node と完全一致)、C0 は SURVIVED**。変異の木は走行後も clean (dirty 0)。
- 結果 JSON の原本は job dir (`mutation/probe-results.json` sha256 `7943ce1d…`、`mutation/final-results.json` sha256 `e2a2db26…`)。大きいので逐語には要約だけを置いた。

## 5. 計算の費用 (D2212 項 4)

- 図の描き直しは login で node 時間 0。
- 開発の検査の job Elapse (実測、いずれも 1 node): 焦点走 1 回目 353 s・2 回目 380 s、単独走 13 s・104 s、変異 30 job 計 348 s (各 job の `.e` file の Elapse の和、一覧 `verbatim/mutation-job-elapse.txt`)。合計 1,198 s ≈ **0.33 node 時間**。
- 受入全走は記録 commit の後に走るので、ここには書かない。

## 6. 残り

- (1'') 今後の論文根拠の実験 (P0・P1・P3・TPC-C) の実行経路 (job body) で保全口の opt-in を有効にする。verify fan-out の兄弟 node の反復は保全対象外のまま。
- (5'') fig1 の生成器の作成、fig15 の repo 外入力の写し、R2 の投入単位の決定と見積り (2 node 時間以上ならユーザー確認)。
- 段 6 レビュー B の nit (test の `subprocess.run`・`Path.read_bytes` の広い差し替え) は採用しなかった。

## 7. 記録

`verbatim/` に、依頼、開始 gate、段 1 brief、段 4 裁定、段 5 実装子の報告、段 6 レビュー 2 本・裁定 2 本・fix 子の報告 2 本・焦点再レビュー 2 本、焦点走 4 回の log、描き直しの log・log の外の 3 回の rc・差の分類・差の全列挙・PNG の実 file の sha256 対照、変異の spec 2 本と結果の要約 2 本と job ごとの Elapse、段 7 の記録レビューを置く。
使い捨て script (描き直し `redraw.sh`・照合 `compare_provenance.py`・分類 `classify_diff.py`・変異 spec の生成 `mutation/make_specs.py`) と描き直した図の 51 file は、親が書いた repo 外の物として wave の job dir
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2853-archive-inventory-figure-redraw/`) に置き、repo へは入れない。
焦点走の log 4 本 (`verbatim/focus-*.log`) は行末空白だけを除いた可逆の最小正規化である (可視文字は不変)。原文の sha256・byte 数・除いた行は `verbatim/normalization.json`、原文は同じ job dir の `focus-*.log`。
Codex 出力の逐語 8 本 (`s5-author-a.md`・`s6-*.md` 8 本のうち裁定 2 本を除く 6 本・`s7-review-record.md`) は末尾改行の無い原文のまま置いた。
