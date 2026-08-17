---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: t963-stranded-branch-closure
seq: 1
title: 取り残し branch 3 本に land すべきものは無いと内容判定で確定させた — 回収済みを主張した wave が受け手 dir の索引を落としていた 1 件だけを追記で閉じた (docs のみ、branch worktree-t963-stranded-branch-closure、計測なし)
---

## 本文

- **依頼と結論。** `[T-963]` の残余として、未 merge の 3 branch に land すべきものが残っているかを
  内容で判定した。結論は **3 本とも land 不要**である。ただし判定の途中で、`[T-950]` が
  「回収済み」と記録した 2 file が**受け手 dir の索引から漏れていた**ことが分かったので、そこだけ
  main 版を base に追記型で閉じた。branch・worktree の削除と push は行っていない。
- **未着地量は `git cherry` の patch-id で測った。** 4 commit である
  (`backup-rulings-land-20260812-first-attempt` 37ec30e8 に 01af18f8 と 20202cac、
  `backup-rulings-land-20260812-second-attempt` b686757e に 2f1861c8、
  `worktree-dev-wave-t139-addendum-b` 84217161 に 84217161 自身)。**`git diff main...<branch>` の
  行数は未着地量ではない** — addendum-b では 177KB 分の stat が出るが、その大半は branch 基点以降に
  main が進んだ差であって branch 側の内容ではない。
- **系統 (1) backup 2 本 = 回収不要。** 生 blob は `FOLDED.md` の receipt と一致しないが、
  **`FOLDED.md` の `content_sha256` は carry 解決後の実体**なので生 blob の不一致は未着地の根拠に
  ならない。そこで本文の固有語を全件検索した (`grep -rln` で file 名を出してから file ごとに
  `grep -n`、`head` で切らない)。`landed-fold-owned-path` と
  `backup-rulings-land-20260812-first-attempt` の hit から、**land は第 3 の branch
  `worktree-dev-wave-rulings-land-20260812` (tested_tip `7157b7ca`) で成功しており、着地本文は
  `docs/archive/worklog-phase3-0813-506.md`** と特定できた。
- **その上で 9 fragment を行単位で機械照合した。** frontmatter と `base:` / `remaining:` の機械欄
  (fold が消費する欄) を除き、`FOLDED.md` の `allocations` で遅延採番記号 (`T:codex-hook-trust` →
  `[T-983]` 等 10 個) を実 ID へ解決してから、canonical 3 台帳 + `docs/archive/` 全体 (318,804 行) へ
  照合した。**未着地行は 9 本中 8 本で 0 行**、残る 1 本 (first-attempt 版の記録 fragment) の 1 行も
  着地版が同じ事実を言い換えた形で持っている (branch「seq 1 を落とした」/ 着地「seq 1 は取り込まない
  ことにした」)。第 5 束の裁定本体 6 fragment は receipt の wave・seq とも完全一致で、
  再 fold すれば T/D の二重採番で `rc=26` になる側である。
- **系統 (2) addendum-b = branch 固有 bytes は非ゼロだった。** `output/insights/2026-08-09_t139-addendum-b/`
  の tree 照合では、branch 13 file / main 14 file、内容差 5 file + main 単独 1 file である。
  **「main に無い bytes はゼロ」は成り立たない。**内訳を 1 件ずつ分類した結果は次のとおりで、
  1 件を除きすべて既裁定で覆われている。
  1. `s6-refocus.md` — 差は末尾改行 1 byte のみ。内容差ゼロ。
  2. `s4-adjudication.md` — branch は実測 4 を限定形で直接書き、main は無限定形 + それを限定形へ
     訂正する `erratum 1` を別節で積む。**事実は main 側に完全にある**うえ、branch 版で上書きすると
     「原文は変更しない」という erratum の規律が退行する (`[T-950]` の判断どおり)。
  3. `addendum-b.md` — branch 版は `b03` が受領証の必須項目と validator の照合条件を持ったままの
     修正**前**の版で、段 6 焦点再レビューが core §12 の必須 schema と受理集合を変えると判定して
     main 側で外したものである。**回収は反証済みの欠陥を戻すことになる。**
  4. `package.md` — branch 固有は B4 の第 5 案と B9 の 2 つ。第 5 案は `[T-962]` が (c)「今は足さない」で
     決着済み。B9 (公表台帳にも追補 A と同型の受領証記録を課すか) は、main 側の `addendum-b.md` が
     「受領証にどの field を置くかは producer 実装 wave の責務」と書き切り、2026-08-10 の裁定 Q-A
     (受領証 schema の digest 固定はこの後) と同じ向きで既に解決している。
  5. `README.md` — **ここだけが実質的な取り残しだった** (次項)。
- **唯一の取り残し: `[T-950]` が回収した 2 file が受け手 dir の索引に無かった。** `[T-950]` は
  `s6-refocus2.md` (5,735 bytes) と `s6-refocus3.md` (7,052 bytes) を byte 保存で main へ足したが、
  同 dir の `README.md` の一次資料表へは載せていない。結果として **5 日間、この 2 file を参照する
  文書が repo 内に 1 つも無い**状態だった (`grep -rln "s6-refocus2\|s6-refocus3" docs/ output/` の hit は
  他 study の同名 file と `docs/archive/` の worklog だけで、当該 dir 内は 0 件)。
  `[T-950]` 自身が「これが失われると追補 B を将来再提出する wave が `b03` の foreign key を落とした
  理由を再導出できない」と書いた file が、索引から辿れないままだった。
- **索引 2 行 + 断り書きだけを追記した。** branch の fragment は cherry-pick せず (未 land branch の
  merge は land の fold 形状検査が機械拒否する)、main 版 `README.md` を base に一次資料表へ 2 行を足し、
  出典 (`docs/archive/worklog-phase3-0812-499.md`) を注記した。**巡の番号が文書ごとに基準違いである
  ことも同じ注記へ書いた** — 表の「第 2 巡 / 第 3 巡」は引き取り側の数え方、回収した 2 file の本文が
  言う「1 巡目 / 2 巡目」は branch 側の数え方で、`s6-refocus-3.md` (ハイフン付き) と `s6-refocus3.md`
  (ハイフン無し) は別文書・別結論である。2 file の bytes と他の記述は 1 byte も変えていない。
- **凍結 pin は無いことを確認してから編集した。** `grep -rln "2026-08-09_t139-addendum-b" --include=*.py .`
  の唯一の hit は `orchestrator/publication/approval_d291.py` で、pin 対象は同 dir の `addendum-b.md` を
  (path, commit `8e9a5b4d`, sha256) の三つ組で指す historical rejected ref であり、`README.md` も
  live bytes も見ない (`orchestrator/tests/test_t793_approval_d291.py` に live 読取なし)。
  `orchestrator/tests/test_frozen_artifacts.py` が pin する insights 5 file にも当該 dir は含まれない。
- **一般化はしない。** 「回収を主張する wave は受け手 dir の索引を確認する」は再現性のある手順だが、
  独立 2 例で再現していない単発事故であり、`DW-G03` に従って局所修復に留める。
  `docs/dev-wave/**` は 3 層とも予算満杯でもある。
- **受入の要否 — 判定手順と証拠。** 本 wave の差分は
  `output/insights/2026-08-09_t139-addendum-b/README.md` と `docs/spool/**` だけで実装面ゼロ。
  実 repo の当該 path を読む test node は**不存在** — `grep -rn "2026-08-09_t139-addendum-b"
  orchestrator/tests/` と `grep -rln "s6-refocus" orchestrator/ tools/` がいずれも 0 件、
  `tools/check_docs.py` の placeholder 検査は `INSIGHTS_DIR.glob("*.md")` で
  **非再帰**につき subdirectory 配下の本 file を対象にしない。`docs/spool/` 配下は
  `orchestrator/tests/test_check_docs.py::test_spool_tree_is_excluded_from_all_legacy_doc_scans` が
  legacy doc scan の対象外と固定している。**したがって焦点走は不要である。**
- **ただし受入全走は docs-only でも省けない。** `tools/dev_wave_land.py` は
  `--acceptance-receipt` を必須引数とし、receipt の `resolved_runner_path` が
  `tools/run_tests.py` であることまで照合する。**docs-only の免除口は land 側に存在しない。**
  直近の docs-only land (`rulings-full6-20260817`、tested_tip `15d69394`) の receipt も
  `argv=["python3","tools/run_tests.py"]` / `verdict=child-green` で実走を示している。
  「受入は docs-only 免除」という過去エントリの言い回しは**焦点走と変異 matrix の側にだけ効く**。
  安い関門 (`python3 tools/check_docs.py` rc=0、`python3 tools/spool_fold.py --dry-run` rc=0
  status=planned、全史 provenance 監査 3,952 件で新規違反なし) を先に全部緑にしてから
  受入全走へ入る。

## 次の一手差分

### 更新

- [T-963] **P3・branch 側は判定完了 / push 側は据え置き (第 6 回から変わらず)**: 削除条件だった 2 件は
  解けた — `[T-949]` は 2026-08-17 のユーザー発話で (β) 確定、`[T-962]` は第 5 案を今は足さないで
  (c) 決着。残る 3 本 (`backup-rulings-land-20260812-first-attempt` 37ec30e8、
  `backup-rulings-land-20260812-second-attempt` b686757e、`worktree-dev-wave-t139-addendum-b` 84217161)
  には **land すべきものが無い**ことを本エントリで内容判定した。branch 側に残るのは削除の可否だけで、
  **削除はユーザー指示があるときのみという規律に従い 3 本とも残してある。** tip SHA は本エントリの
  実測値を使ってよい。**未 push 98 commit は今回も送らない** — 送らないことで失われているものは無く、
  送信は AI が行わない取り決めのままとする。
  base: ad9592bf5ac856dd4acffa186710b723f67d61e307be6e6165bfe30d6a3fedcb
