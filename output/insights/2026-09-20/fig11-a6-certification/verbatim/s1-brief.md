# 段 1 brief — fig11 (A-6 read-heavy certification reject、attempt a6-20260908b の exact 2 cell 図)

- **研究前進:** 論文ストーリー 2026-09-20 版 §8 第 2 (A-6、outer `reject`) に fig6 (A-2) と同型の結果図を与える。完了判定 = `docs/paper-story/figures/fig11_a6_certification_reject.{png,pdf,provenance.json}` が着地し、figures README に一覧行 + 節 (fig10 型)、`docs/paper-story/README.md` の results 表 2026-09-18 A-6 行「図は無い」→ 図 11 と追補段落、`test_plot_a2_certification.py` の着地 closure・`check_docs.py` が緑で land。
- **scope (実装面、Codex author D95):** `tools/plotting/plot_a2_certification.py` を study 別 profile 表で A-6 に一般化し、`orchestrator/tests/test_plot_a2_certification.py` の exact pin を更新して A-6 の実寸 fixture・実データ test・着地 test を足す。**A-2 (fig5/6/7) の caption・provenance 射影・挙動は 1 byte も変えない** (fig5/6/7 の landed closure test が守る)。
- **scope (docs、親):** figures README (一覧行 + fig11 節)、paper-story README (表行 + 追補段落)、plotting README (`plot_a2_certification` 節へ A-6 再現 1 行、**受入直前に local main 取り込み後**)。A-6 単独稿の bytes は不変。
- **scope 外:** 仮想リスク向け gate・検査・台帳・一般化、B-10 との pool、反復 attempt、認証昇格、稿の改訂、fig5/6/7 の変更、push。
- **確定済み裁定 (依頼):** Codex author (D95)、着手直前 local main `947fd160a` から fresh worktree、性能 `reject` と正しさ `certified` を混同しない (D1993 項 2)、B-10 近接条件 (T-2430) は本文で触れるだけで pool しない、provenance は単独稿を caption_source として SHA-256 束縛 (F36 型 = fig9/fig10 先例)、計測機の外で作図 (FIGURE_CONVENTIONS §7)。
- **(P1) 稿の「限定 11 の更新」は稿 bytes を変えずに行う (親の provisional 裁定・攻撃対象):** 稿は results 系列の凍結物 (稿冒頭・README 規則「append-only。書いた後は更新しない」) で、かつ fig11 provenance が caption_source として稿の現 SHA-256 (`34a968428f867ce26479abe37320946b6eb8149007244dfe1d18a18446633850`) を束縛する。更新は `docs/paper-story/README.md` の results 表行と「A-6 単独稿の限定 11 への追補 (2026-09-20)」段落で行う (先例: 同 README の T-1998 単独稿の読解上の追補・C14a 追記、fig8b / fig10 wave は稿を触っていない)。
- **(P2) 生成器は新 file でなく in-place 一般化 (攻撃対象):** fig6 と同型で validator ~500 行を共有するため。study → {label, caption_source, 表示名} の小さな profile 表を持ち、受理 study を `paper-story-a2-certification` / `paper-story-a6-certification` の exact 2 件にする (D75: 同名識別子の二義化なし、DW-O13: `study` field の実値と workload 数 1・file 数 6 は一次資料で実測済み)。
- **(P3) fig11 caption の固定文 (攻撃対象、レビューで稿 §0 / §4 と照合):** 生成器が data から書式化する値 (attempt / status / request / host / created_utc / effect / median 条件 / pin) と、固定文 = (a) 単一 workload なので outer status はその workload の判定そのもの、(b) 性能 reject は正しさ証拠の欠落ではなく、正しさ certified は性能の認証ではない、(c) 1 attempt・5 標本の median 比較で有意差・floor 超・研究の失敗は判定しない、(d) read-heavy のこの 1 点で一般化しない、(e) B-10 近接条件との同符号は履歴的照合で独立再現ではなく pool しない、A-2 とも pool せず前後比較しない、(f) 正しさ限定 (L01 point-key trace、D1257 argv 未記録)、(g) 条件関門は「記録された受領証の束縛」まで、(h) CI は標本の記述、(i) abort 率は代表 rep 1 点。A-2 固有の末文「older series is not a comparator / sign difference」は A-6 に入れない。
- **不変条件:** 値は再計算せず certification から写し `effect_crosschecks` で照合 (abs_tol 1e-12)・median は 5 標本から再計算して一致要求; pin は CLI から渡せない; layout 検査は保存前 fail-closed (2×N axes); 外部入力は raw-manifest の 6 file と SHA-256 一致; fig5/6/7 の bytes・caption・provenance 不変; 稿 bytes 不変; 新規 gate・台帳なし; push なし。
- **DW-G05 成果物影響:** 放置時、論文の A-6 結果は表だけで図が無く (稿 限定 11)、§8 第 2 の材料が A-2 (fig6) と非対称のまま。must-fix = fig11 3 成果物 + README 節 + 着地 closure test。他は nit/backlog。
- **DW-G01 生死:** 現行生成器 + A-6 入力 → rc=2「path is not in repository-owned pin table」・出力 0 件を実測 (13:3x JST)。実装後、親が real root で 1 回実走し rc=0 + 3 成果物を確かめてから完了と申告する (FIGURE_CONVENTIONS §10)。
- **DW-O09/O13 の実測:** fig11 既存 0 件; 稿 sha の pin 0 件; 生成器 sha は fig7 provenance の記録欄のみ (live pin でない); test 側 exact pin = `len(CANONICAL_SHA256)==2`、twelve-file closure ×2、four axes、t2364 のみの current-full 一覧; 受入所要台帳は新 node 不要。
- **受入・実測環境:** 作図・焦点走は login node (計測機の外)。焦点走は `orchestrator/tests/test_plot_a2_certification.py` 1 file (bounded local、MemoryMax に当たれば `--force-dispatch`)。受入は `tools/dev_wave_wait.py acceptance --lease-optional`。owned-path に `docs/paper-story/README.md` / `tools/plotting/README.md` を入れない。
- **並列分割:** 実装子 1 本 (生成器 + test は同一 file 群で密結合)。docs は親。

## 変更面の実アンカー表 (main 947fd160a)

| file | 行 | 現状 | 変更 |
|---|---|---|---|
| `tools/plotting/plot_a2_certification.py` | 43 | `STUDY = "paper-story-a2-certification"` | study profile 表 (2 study exact) |
| 同 | 48-57 | `CANONICAL_SHA256` 2 entry | A-6 entry 追加 (cert `3a9505b0…`, manifest `8d179535…`) |
| 同 | 274 | `expected_count = 10 if legacy else 12` | current-full は `6 * len(workloads)` |
| 同 | 528 | `certification.get("study") != STUDY` | profile 表の key 判定 |
| 同 | 568, 575 | label 既定 / `!= 2` の一意検査 | `len(workloads)` |
| 同 | 619-651 | current-full caption (A-2 固有文) | study 別: A-2 は逐語不変、A-6 は (P3) |
| 同 | 709-755 | `subplots(2, 2)`、suptitle、`all 4 cells` | `2 × N`、study 別表示名、N |
| 同 | 763-767 | `len(plot_axes) != 4` | `2 * ncols` (現行 4 は A-2 で不変) |
| 同 | 795-811 | current-full は caption_source 無し | A-6 は稿を caption_source に (A-2 current-full は不変) |
| `orchestrator/tests/test_plot_a2_certification.py` | 516-529, 686-731, 1050-1058, 1524-1540 | exact pin (12 file / t2364 のみ / len==2) | A-6 を含む形へ; 既存 A-2 fixture 挙動は不変 |
| 同 | 新規 | — | A-6 実寸 fixture (1 workload × 2 cell × 5 標本、6 file、本物 Figure を layout へ)、A-6 real-root test (skip 時は root 不在のみ)、`test_landed_fig11_…` |
| `docs/paper-story/figures/README.md` | 一覧表末尾 / 末尾 | fig10 行・節 | fig11 行・節 (親、生成後) |
| `docs/paper-story/README.md` | results 表 2026-09-18 A-6 行、results 系列規則の前 | 「図は無い」 | 「図 11」+ 追補段落 (親) |
| `tools/plotting/README.md` | `plot_a2_certification` 節 | A-2 のみ | A-6 再現 1 行 (親、受入直前) |
