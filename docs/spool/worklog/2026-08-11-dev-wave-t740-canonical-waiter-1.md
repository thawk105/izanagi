---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t740-canonical-waiter
seq: 1
title: 待ち手の正本 script を新設し、自己マッチによる無音死と lease 誤判定を構造的に塞いだ ([T-740]) — 敵対レビュー 3 本が blocker 4 件を出し fix を 2 巡した (コード + docs、branch worktree-dev-wave-t740-canonical-waiter)
---

## 本文

- **起票根拠 = [T-740] のユーザー裁定 (a) (2026-08-10 /rulings)。** 受入 lease の待ち手の正本
  script を `tools/` に新設し、runbook §7.3 から参照する。command 引数により scope を
  背景 producer の待ち手へ拡張した (`DW-C00`「command 引数は worklog 候補より優先する」)。
- **裁定の前提は実測で成立した。** `tools/` に待ち手 script は存在せず、各 wave が散文から
  書き起こしていた。実際に現存する 2 例を確認した — `dev-wave-t683-caller-closure/run_acceptance.sh`
  は `claim` の JSON 出力を `case "$out" in *acquired*)` の glob で判定しており (F192 の型)、
  `t139-addendum-b` の汎用待ち手は `until ! pgrep -f "$PAT"` で自己マッチしていた (F32 の再発)。
- **poll 間隔の provisional 裁定 (10 秒) は撤回した。** F196 が「待ち周期を 120 → 30 → 10 秒へ
  詰めても、追い越しの原因は周期ではなく待ち行列長なので消えない」と実測しており、
  効くのは待ち手内での取り込みである。runbook 正本の 30〜120 秒・既定 30 秒を採った。
- **敵対検証子を省かなかった理由。** 散文で書かれた「いつ受入を投入してよいか」の判定を
  機械化するため受理集合の表現が変わる (`DW-C00` の carve-out)。段 2 プラン起草、段 3 敵対 2 レンズ、
  段 6 敵対レビュー 2 本 + 焦点再レビュー 1 本を回した。**3 本すべてが NO-GO を返した。**
- **blocker 4 件。** (i) 受入成功後に lease を保持したまま返る経路で、signal handler の
  復元区間に SIGTERM 等が入ると `_SignalReceived` が外側の捕捉対象外になり、非成功終了なのに
  lease を解放しない。(ii) `finally` が無条件に release するため、claim へ到達する前の
  preflight 失敗でも release が走り、**同一 wave slug の別 invocation が保持中の lease を
  削除できた** (`wave_land_window.py` の `release` は holder digest の一致だけで unlink する)。
  (iii) 段 2 プランは受入直後に release する設計で、現行 runbook・command の
  「受入と land の終端で release」と非同値だった。(iv) 1 巡目の fix が「成功時は handler を
  復元しない」で (i) を塞ごうとし、**古い cleanup closure を process-global handler として
  延命する退行**を作り込んだ。焦点再レビューが検出し、2 巡目で方針を反転した。
- **親自身が検査穴を 1 件見つけた。** 変異 spec の anchor を実コードへ合わせる作業中に、
  「merge 後の再検査が rc=0 かつ count>0 (待機中に main がさらに進んだ) のとき投入しない」という
  受理条件に対応するテストが無いことが分かった。既存の `[postcheck]` case は rc≠0 しか
  見ていない。fix 2 巡目で専用テストを足した。
- **変異 matrix は 8/8 KILLED、生存ゼロ。** 走行は 3 本で、1 本目と 2 本目は erratum として残す
  (`DW-M02`)。1 本目は M1 を**実の `pgrep -f`** で書いたため pytest が hang し、harness の
  hang timeout (300 秒) が dispatch を SIGTERM して `rc=16 / _SignalAbort: signal 15` になり、
  artifact の path field が埋まらず matrix 全体が abort した (残り 7 変異は未実行)。
  **これは「wave 前の形が本当に無音で止まる」ことの実証でもある。** M1 を注入 seam 経由の
  決定的な形へ再照準して 2 本目を完走させ、期待 node 集合を実測へ揃えた 3 本目で 8/8 一致とした。
  M4 と M5 は 2 本目の時点で単一理由 (失敗 node 1 件) で殺せている。
- **ユーザー裁定へ返す 2 件**を裁定パッケージに分離した (下記 新規)。段 3 レンズ B が
  「正本を作っても consumer が読まなければ F191/F192/F32 は止まらない」と指摘したもので、
  正しい。本 wave の scope は裁定 (a) の文言どおり「script の新設 + runbook §7.3 からの参照」まで
  である。
- **受入は 3 走した。成果物自身を待ち手に使ったので、1・2 走目が実地検証になった。**
  1 走目は待機中に main が 19 commit 進み、待ち手内 merge が `docs/pegasus-runbook.md` で競合した。
  script は設計どおり merge を中止し (`MERGE_HEAD` なし・tree clean)、lease を release して
  rc=70 で止まった — 無音で進まず壊れた状態も残さなかった。
  2 走目は 1 件だけ赤で `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
  (他は 8354 passed / 20 skipped)。新設テストに自走 harness も allowlist 記載も無いと
  `python3 file.py` が 0 件実行の偽緑になる、という機械強制である。**この赤は親の指示不足で出た**
  — 実装子プロンプトは `DW-S05-C` の「meta-test も走らせる」を書いたうえで
  `test_campaign_import_invariant.py` だけを名指ししており、子は名指しされた方だけを走らせた。
  3 走目が緑である。
- **1 走目の競合が新しい実装要件を運んできた。** 待機中に別 wave が §7.3 へ
  「merge の前に所有実装面の overlap を見て、非空なら待ち手では merge せず親へ戻す」を
  land させていた (88a5c1a3、`DW-O17` が両親と異なる実装面に Codex `role=author` を要求するため)。
  正本 script が正本文書に反したままになるので fix 3 巡目で実装し (`--owned-path` は
  repeatable で外から渡す)、新設 gate として変異 M9 を事前登録して matrix を 9 件へ広げた。
- **受入した tip と land する tip は 1 commit 違う。** 受入は `5cbcf077` (待ち手が lease 取得後に
  作った main 取り込み merge) で走らせ、land するのはその上に本 fragment の受入値を積んだ
  docs のみの tip である。実装面は 1 byte も動いていない。
- 逐語は `output/insights/2026-08-11_t740-canonical-waiter/` に凍結した。

## 次の一手差分

### 完了

- [T-740] 待ち手の正本 script `tools/dev_wave_wait.py` を新設し、runbook §7.3 を canonical
  invocation 中心へ書き換えた。受入 lease の待ち手と背景 producer の待ち手を 1 script の
  2 サブコマンドに収め、自己マッチ (`pgrep` pattern を受け取る CLI 面を持たない)、
  claim の exact JSON 判定、各段の rc 個別判定、待ち手内での main 取り込み、
  成功時の lease 保持と全失敗経路での release を構造的に固定した。
  受入 8389 passed / 20 skipped / 517.82 秒 / rc=0、変異 9/9 KILLED (生存ゼロ)。
  remaining: none
  base: 160aa03f853fdbfd23db9b38a98ff1b328f7a2bcb5348526fe8b0fb9ca71915d

### 新規

- {{T:waiter-consumer-binding}} **P2・新規・ユーザー裁定待ち**: 待ち手の正本 script を
  consumer へ機械的に結線するか。現状 `.claude/commands/dev-wave.md` の段 6 / 段 9 と
  `docs/dev-wave/` の `DW-C00` / `DW-O01` は従来どおり手書き待ち手を許したままで、
  参照は runbook §7.3 だけである。選択肢 = (a) command と `DW-O01` を canonical invocation へ
  結線する (L1 に触れるため [T-738] (c) の再訪が要る) / (b) runbook 参照だけで留め、
  実害の再発を待つ。成果物影響 = (b) のままなら手書き loop が残り、
  無音死と誤判定の再発経路が閉じない。段 3 レンズ B と段 6 レンズ A/B が独立に指摘した。
- {{T:waiter-acceptance-shape}} **P3・新規・ユーザー裁定待ち**: 待ち手が受入 command の
  identity を強制するか。現状は `-- <argv>` を任意に受けるため `-- true` でも rc=0 になる。
  選択肢 = (a) `tools/run_tests.py` の acceptance shape であることを検査する /
  (b) 任意 argv のまま親の記録責任に委ねる (本 wave の実装)。
  成果物影響 = (b) のままなら待ち手 rc を受入完了の証拠として誤読する余地が残る。
- {{T:dev-wave-l15-budget-exhausted}} **P2・新規・ユーザー裁定待ち**: 段 8 の自己改善候補 2 件が
  `docs/dev-wave/**` の L1.5 予算 (上限 9566 bytes) の**余白 0** に阻まれ、実装せず止めた。
  候補 = (i) `DW-S05-C` の「meta-test も走らせる」へ「**親の名指しを網羅と見なさず子が自分で
  洗い出す**」を足す (本 wave で親が `test_campaign_import_invariant.py` だけを名指しし、
  `test_plain_runner_coverage.py` が受入で赤になった実害がある)、
  (ii) `DW-M08` へ「KILLED 判定は失敗 node 集合の完全一致なので予測を実測へ揃える走行を
  見込む」を足す (本 wave で変異 matrix を 2 度余分に走らせた)。
  (i) だけでも 60 bytes 超過する。意味を保った縮約の余地は無く、
  `docs/skill-self-improvement.md` の「予算に収まらなければ変更を止めてユーザー裁定へ返す」
  「予算値を上げる変更は独立審査対象」に従って起票する。
  選択肢 = (a) L1.5 予算の独立審査を行う / (b) 既存 L1.5 節のうち陳腐化したものを
  テスト化して空ける / (c) 現状維持で候補を破棄する。
  成果物影響 = (c) のままなら、親が meta-test を部分列挙するたびに同型の受入赤が出る。
- {{T:mutation-harness-hang-artifact}} **P3・新規**: 変異 harness の dispatch 経路で
  変異が hang timeout に掛かると、receipt が `outcome.kind=infra` になり
  `job_stdout_path` が埋まらないため、`artifact dispatch path field が文字列でない` で
  **matrix 全体が abort する**。当該変異を TIMEOUT として記録して残りを続行できない。
  本 wave の 1 本目で実測 (M1、残り 7 変異が未実行のまま終了)。
  成果物影響 = hang しうる変異を含む matrix が部分実行のまま終わり、
  変異台帳の被覆が黙って縮む。
