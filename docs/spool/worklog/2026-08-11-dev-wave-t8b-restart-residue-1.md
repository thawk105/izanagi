---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t8b-restart-residue
seq: 1
title: 8b 再開の残余 — 床値実測・freeze v2 再凍結・oracle 実走はいずれも着手不可で、toolchain 束縛は段 3 の blocker 4 件で再裁定へ返した (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t8b-restart-residue)
---

## 本文

- **起票根拠 = worklog 403 の [T-747] R-4 = (B) / [T-748] / [T-770]、404 の [T-781] / [T-782]、
  402 が返した新事実。** 依頼は「床値実測 → freeze v2 再凍結 → oracle 実走の再開」だったが、
  **3 段とも着手できなかった。** 実施できたのは docs 訂正だけである。
  裁定パッケージ = `output/insights/2026-08-11_t8b-restart-residue/package.md`
- **preflight は P1〜P3 とも期待どおり** (gitlink `d706650c…` 一致、凍結成果物 manifest
  2 passed / rc=0、oracle gate-check rc=2 で拒否 2 件 exact。`holdout-freeze-verify:` 混入なし)。
  local main 取り込み後に再測しても同一で、peer wave の `s8c_preregistration` NUL 検査追加は
  8b の受理集合を動かしていない
- **床値実測 (W-2) が投入できない機械的事実を 3 点実測した。** (i)
  `_assert_official_permitted` (`:207-217`) が official を無条件拒否する (既記録)。(ii)
  `assemble_result` (`:2453`) が `eligible_for_refreeze=True` を official 限定にするため
  **pilot 実測は再凍結に使えない**。(iii) `tools/pegasus/floor_campaign.sh:962` は
  `--mode official` 固定で pilot 経路を持たない。**(ii)(iii) は裁定文にも worklog にも
  記録が無かった。** W-1 = [T-781] は「択保留・調査先行」で実装不可、
  W-3 / W-4 = [T-750] は未裁定のままであり、freeze v2 と oracle も着手できない
- **段 4 で scope A (toolchain 束縛) を「実装しない」と裁定した。** 決め手は段 4 で気づいた
  非対称性で、段 2 プランも段 3 の 2 レンズも指摘していない — **[T-783] 単独は
  fail-closed 障壁を緩めるだけである**。床値 build の `gcc-13`/`g++-13` 固定要求は
  Pegasus で現に効いている障壁であり、compiler 解決を site 依存へ寄せると
  gcc 11.4.0 で build が通るようになる。束縛検査が無ければ
  「認可されていない compiler で床値を測れるようにする」だけの変更になる。
  [T-783] の起票文自身が (B) の実装単位と条件付けており、単独実装を意図していない
- **段 3 の敵対 2 レンズ (max) がいずれも NO-GO** (blocker は A が 2 件、B が 2 件)。
  (1) 裁定文が指定する三者照合の **attempt 実測値の脚が配線されていない** —
  `floor_campaign.sh:769-778` が `$ATTEMPT_DIR/{compiler,cxx,cmake}.{path,version}` へ書くが
  driver へ渡らず `job-result.json` にも入らない。(2) 現行 calibration に **cmake の path と
  cxx の version が無く**、wrapper 差し替えが通る。閉じるには新 calibration 世代が要り
  事前登録に触る。(3) floor 限定の gate では同 contract の他 producer が無防備。
  (4) gate に**本番の発火経路が無い** (`DW-G04`)
- **親の実測がプランの照合設計を破った。** calibration の `compiler_version` 先頭行は
  `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`、`buildcache._tool_version('gcc','cc')` の
  実測 `version_first_line` は `x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`。
  **gcc は argv0 を先頭 token に出すため同一 compiler でも逐語一致しない。**
  逐語一致にすると Pegasus の正規 run が恒常的に赤になる。realpath 同士は完全一致する。
  設計判断は {{D:toolchain-binding-and-unlock-are-inseparable}}
- **親 brief の主張 4 件をレンズと実測で訂正した。** (i) M-6「calibration toolchain の
  consumer が無い」は refuted — `silo_ladder_rung1.py:3554-3588` に同型の束縛が既にあり、
  正しいのは「floor / `build_v2` 経路に無い」という狭い形だけ。親は grep 結果に
  `silo_ladder_rung1.py:3580` を見ていながら producer と読み違えた。(ii) M-1「投入できない」は
  誤りで、`submit_floor.sh` に mode 分岐は無く qsub は実行される — 正しくは
  「enqueue はできるが official run は rc=2 で再凍結適格 artifact を完遂できない」。
  **キュー資源は消費されうる。** (iii) M-4「driver source の pin が無い」は広すぎ、
  submission receipt の `source_commit` と実行時 imported module bytes 照合という
  submission→execution の commit pin は在る。(iv) M-3「計算ノードの既定は 11.4.0」は
  登録済み 2 世代 (bnode011 / bnode048) の観測であって `gen_S` 全ノードの現在値ではない
- **[T-770] は並行 wave に先を越され、本 wave の分は census 側だけに縮んだ。**
  本 wave も R1 (b) + R2 (a) を `orchestrator/tests/README.md` へ実装していたが、
  受入 3 走目の merge 段 (rc=70) で `dev-wave-t770-conditional-unrun` の land
  (main `04e99891`) と衝突して発覚した。**相手の実装は上位互換**である —
  `skiputil.skip_conditional_unrun()` と `test_skip_classification.py` で分類の結線を
  機械固定し、変異 4/4 KILLED で裏取りしている。**本 wave 側の同 file 変更は全面取り下げ、
  main の版をそのまま採った。** 相手が触れなかった census
  (`output/insights/2026-08-11_known-red-exceptions/README.md`) の分類語訂正と erratum だけを残す。
  **census の実測値 (件数・rc・request ID・変異結果) は 1 つも変えていない。**
  R1 (c) 相当は相手の [T-790] が持つため、本 wave の起票予定は取り下げた
- **先を越された機序は「同じ裁定を 2 つの wave が独立に拾った」ことである。**
  [T-770] は worklog 403 で裁定済み・着手可の状態にあり、本 wave は 8b 再開残余の一部として、
  相手は専用 wave として、それぞれ起票した。着手前の main 確認 (`0c336b8e` 時点) では
  相手の branch は存在せず、稼働 worktree 一覧にも無かった
- **旧裁定の導線を塞いだ。** `output/insights/2026-08-11_t8b-restart-integration/package.md` の
  R-4 節へ superseded 表示を追記した。レンズ B が「実装子が同 package を読むと
  [T-747] (a) の contract field 追加を選び、別 contract hash を生む」と指摘したため
- **変異 matrix は免除。** `DW-S04` の「実装差分ゼロの『実装しない』裁定」に該当する。
  受入全走は免除していない — `orchestrator/tests/README.md` は
  `test_plain_runner_coverage.py` / `test_verifier.py` / `tools/check_docs.py` /
  `tools/run_tests.py` の 4 者が読むため、実 repo を読むテストは**存在する**
- **凍結前の機械走査**: 変更・新規 docs 13 file に holdout 三軸語の conjunction hit
  **0 件 / rc=0** (両 holdout とも)
- **検査の実測**: 受入全走 1 走目 **8483 passed / 20 skipped / 547.73 秒 / rc=0**
  (受入 lease 取得後に local main を取り込んだ tip `ba73d199` で実走)。
  `check_docs` 違反なし、`spool_fold --dry-run` = planned、provenance 全史監査 rc=0 (2388 件、
  新規違反なし)。**skip 件数 20 は変更前と同一**で、本 wave は skip を増やしていない
- **受入 2 走目で F57 が再発した。** docs 2 commit だけを積んだ tip `73c8ba95` の全走で
  `test_codex_worker_launch.py::test_fake_stdout_matches_observed_cli_event_shape` が 1 件落ちた
  (**1 failed / 8482 passed / 20 skipped / 538.44 秒**、
  `failed_predicates=["process_group_residual","termination_verified"]`、
  `loadavg=(12.92, 3.66, 1.90)`)。同 file の単独再走は **97 passed / 6.27 秒 / rc=0** で再現しない。
  本 wave の差分は docs のみで launcher 実装にも同 test file にも到達しえず、
  `DW-O18` により帰属しない。**同一 wave で docs 2 commit しか違わない 2 tip の全走が
  緑 → 赤と割れた対照は F57 では初出**で、台帳へ再発として記録した
- **並走ガード 3 条件を遵守した。** 本 wave は**計測系のキュー投入を 1 件も行っていない**
  (床値投入が不可のため)。投入したのは検査系の dispatch だけで、
  provenance 監査 (request `901529.nqsv`、Elapse 17 秒) と受入全走である。
  投入の直前に毎回 `qstat` で確認し、**T-139 の pilot / 本走 job は一度も queue に無かった**
  (見えたのは第 3 波の受入全走と本 wave 自身の検査 dispatch だけ)。ノード同居なし。
  裁定要求は A 系の後ろに並べる。
  なお `tools/check_ai_provenance.py` は login では完走せず計算ノードへ自動 dispatch する。
  「投入ゼロの wave」を名乗る場合、検査系がこれを破ることを親が見落としていた
- **エージェント工数**: codex 子 3 本 (プラン 1 = max / 敵対相談 2 = max)。
  実装子とレビュー子は「実装しない」裁定により起動していない。
  親は brief・実測・裁定・docs・記録
- **段 8 自己改善**: 候補 3 件を裁定した。(1) 「投入ゼロの wave」で検査系の自動 dispatch を
  数え落とす件は**採用**し、8b 再開手順書の並走ガード節へ 1 段落統合した (dev-wave 入口ではなく
  発火元の runbook が正本のため)。(2) 性質検索の hit 行を producer / consumer に分類せず
  結論した件は、`DW-G03` の「単発事故は局所修復」に従い**不採用** — 本エントリの記録で閉じる。
  (3) 「単位へ割ったとき片方だけ land した場合の受理集合の向きを `DW-G05` で問う」案は
  **予算超過で起票へ回した**。追記 258 bytes に対し `docs/dev-wave/**` の L1 unique footprint は
  予算 10625 bytes に対し余白がほぼゼロで、追記すると 10883 bytes になる。
  「予算のために安全義務を削除・弱化しない」に従い撤回し、下記「新規」へ起票する
- **本 wave の裁定要求 S-1〜S-4 は、受入 4 走目の走行中に全問推奨どおり裁定された**
  (2026-08-11 /rulings 第 5 回、worklog 412)。rulings 側が「台帳の [T-783] 実体は残余 wave の
  未 land の旧文のままなので本 fragment では更新しない — 残余 wave land 後の記録で台帳へ反映する」
  と明記したため、**台帳への反映は本エントリが担う**。結論は変わらない — 束縛検査は
  W-1 の実装 wave が持ち、本 wave では実装しない
- **ユーザー手番**: 残るのは [T-750] (未裁定のまま据え置き) と、W-1 = [T-781] の Q1〜Q4
  (第 5 回の索引が main 取り込み前の worklog から作られたため落ちた、と rulings が自己申告済み)。
  push は行わない

## 次の一手差分

### 更新

- [T-747] **P1・裁定 (B) は維持だが実装単位が再裁定へ戻った (B 系)**: 束縛層を contract の外へ置く
  方針は正しい。しかし実装単位 [T-783] が段 3 の blocker 4 件で止まったため、
  (B) を実装可能にする前提の裁定が S-1〜S-4 として要る。
  材料 = `output/insights/2026-08-11_t8b-restart-residue/package.md`
  base: 08015aa92bc508f76bb7869510c7d073c03a61ba69335ad69c94e04eb06a0fbf
- [T-748] **P1・床値実測は W-1 待ちのまま停止 (B 系)**: 「(B) の束縛検査実装後に投入できる」は
  成立しない。塞いでいるのは R-4 ではなく **W-1** であり、pilot 実測は
  `assemble_result` が再凍結適格から除外するため代替にならない。投入 script も official 固定。
  第 1 世代で実測する方針自体は変わらない。
  base: 923e6902ba7062b0baa20971c6809d873b1f62c0cbd47a089269510ea58daee2
- [T-783] **P1・S-1〜S-4 が裁定済み (2026-08-11 /rulings 第 5 回、全問推奨) → 実装は W-1 の
  wave が持つ (B 系)**: 単独実装は不可で、compiler 解決の site 依存化は toolchain 束縛検査と
  不可分である ({{D:toolchain-binding-and-unlock-are-inseparable}})。裁定は
  **S-1 = 共通 pure helper を作り floor と silo ladder の 2 者を先に寄せる /
  S-2 = 現行 calibration の範囲で作り、cmake path と cxx version が非束縛であることを明示受諾し
  手順書と成果物へ穴を明記する / S-3 = shell の `$ATTEMPT_DIR` の値を driver へ渡して三者照合にする /
  S-4 = 束縛検査は W-1 の実装 wave に含める**。よって本項は単独では起票せず、
  W-1 ([T-781] の Q1〜Q4 裁定後) の wave の必須要件として持ち込む。
  一次控えは `rulings-inbox/2026-08-04-rulings-session-5rulings.md` §84、
  材料は `output/insights/2026-08-11_t8b-restart-residue/package.md`。
  base: a193805da2f295faa9ae225b24e55ae58d3cabd32984f022d48923d4bb1d447c

### 新規

- {{T:dw-g05-partial-land-direction}} **P3・新規 (段 8 発、ユーザー裁定待ち)**:
  `DW-G05` (成果物影響) は「実装しない・放置した場合」しか問わないため、
  **scope を単位へ割って片方だけ land した場合**に受理集合がどちらへ動くかが問われない。
  本 wave はこの非対称性 (site 解決化だけを land すると fail-closed 障壁が外れる) に
  段 4 まで気づかなかった。追記 258 bytes が `docs/dev-wave/**` の L1 unique footprint 予算
  10625 bytes を超える (追記後 10883 bytes、余白はほぼゼロ) ため入口・reference へ入らない。
  [T-786] の docs 予算棚卸し wave の対象へ加えるのが自然。
  **予算のために安全義務を削除・弱化する案は採らない。**
