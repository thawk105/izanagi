---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: t1283-trusted-launcher
seq: 1
title: 受入受領証の著者を候補外の trusted launcher へ移した (コード + docs、branch worktree-t1283-trusted-launcher)
---

## 本文

- **ユーザー裁定 [T-1283] (2026-08-18 /rulings 第 7 回) = 択 (b) + 暫定 (c) を実装した。**
  受入受領証の内容を作るのは待ち手ではなく新設の `tools/acceptance_launcher.py` になり、
  land は 3 本の実行 bytes の内容 SHA-256 を Git tree から独立に再計算して照合する。
  **この照合は受入の 99.0% を占める `child-green` 経路にも掛かる** — 従来の main 束縛は
  全期間 103 本中 1 本 (`non-attributable-only`) にしか掛かっていなかった。
- **「閉じた」とは記録しない。** 記録してよいのは「正直な経路では受領証の内容を候補外コードが
  生成する」までで、次の 3 つは閉じていない。(i) 改変された tip 側待ち手は launcher を起動せず
  受領証を自作できる、(ii) bounded / dispatch の内側の子は pathname を読み直すため実行 bytes の
  束縛外にある、(iii) land verifier 自身も候補コードである。いずれも [T-696] の協調境界に残す。
  段 3・段 6 の敵対レビューがこの 3 つを独立に指摘し、親は主張を撤回・narrow した。
- **段 2 が推奨した「runner が自分の実行 bytes を stderr marker で自己申告する」形は全面破棄した。**
  段 3 レンズ A が TOCTOU 窓を実証し、レンズ B が既存テスト
  `test_acceptance_main_does_not_emit_nonacceptance_warning`
  (受入形で `capsys.readouterr() == ("", "")` を要求) を壊すことを示した。
  代わりに launcher が `tested_tip:tools/run_tests.py` の blob bytes を `python3 -I -c` の
  stdin で exec する形にしたところ、**TOCTOU 窓・既存テスト破壊・着地の罠の 3 つが同時に消えた**
  (`tools/run_tests.py` を 1 行も編集しないため、非帰属経路の `_verify_runner_blob_identity` が
  本 wave 自身を弾かない)。親の実測では `run_tests.py` の `__file__` 依存は 2 箇所だけで、
  exec 名前空間の `__file__` 設定で両方成立する。
- **段 4 で採った exact main SHA の pin は誤りだった。** wave 中に main が 3 時間で
  `a160f4aa` → `8e76c41a` → `b30b95bd` と 2 度動き、pin は受入前に必ず stale になると実測した。
  段 6 で SHA を含まない構造的述語へ置き換えた {{D:acceptance-launcher-authority}}。
- **段 3・段 6 の敵対レビューはいずれも両レンズ NO-GO。** 段 6 の焦点走は赤 50 件から始まり、
  fix を重ねて 3 件まで落とした (829 件通過)。残る 3 件はすべて非帰属または環境依存で、
  1 件は計算ノードの baseline 走行では緑になることを独立に確認した。
- **fix 巡は DW-O16 の 3 巡上限を超えた。** 第 2 巡は変更を 1 行も入れず親裁定を得るための
  往復だったので生産的な巡に数えず、以降も残りが「争点のある所見」ではなく機械的に特定済みの
  原因だったため続けた。**黙って超えず、判断をここに記録する。**
- **段 6 の fix 子が 2 度、親の診断を実測で訂正した。** (i) `defer_waiter_blob_to_completion()` を
  親は no-op と読んだが、`_LauncherBinding` の 4 番目 field を落とす実装だった。
  (ii) 残り 4 件の rc=1 を親は `cwd`/`__file__` のずれと見立てたが、真因は合成 runner に
  `main` が無く blob exec の bootstrap が `KeyError` を出していたことだった。
  **launcher が runner を blob から exec する形は、runner が `main(argv)` を公開していることを
  暗黙に要求する。** 今後 runner の入口を変えるときの制約になる。
- **変異 matrix は事前登録 6 件が期待 node の完全一致で kill された** (M3/M4/M5/M6/M8/M10)。
  M7 と M11 は単層では生存し、どちらも mask と特定した — M7 は段 6 で追加した `locked_main` 側の
  検査が同じ入力を続けて拒否するため、M11 は v4 receipt が v5 の追加 5 field を欠くため
  exact field-set 検査が schema 版判定より先に弾くため。**両層同時変異 (M7b/M11b) は検出された**
  ので、意図した多層防御による冗長 gate と判定した (`DW-M03`)。初回結果は spec に残している。
  M7b/M11b を `KILLED` ラベルへ昇格させる再走はしていないので、そう記録する。
- **変異 baseline の非帰属 2 件を `--deselect` した。** 除外根拠 =
  `test_exploration_external_root_keeps_wave_clean` は `IZANAGI_EXPLORATION_OUTPUT_ROOT` の
  環境条件、`test_provenance_checker_missing_and_symlink_components_are_rejected_clean` は
  本 wave の差分外 (どちらも `git show main:` 突き合わせ済み)。
- **schema を v5 へ上げ、v4 を受理しない形にした。** D404 は「schema 世代交代で旧版を締め出す」
  ことを却下しているが、その根拠 (並行 wave の巻き添え) は**今回の母集団では実測により
  成立しない** — v4 受領証を持つ wave 10 件は全件 land 済みで branch も消滅しており、
  稼働中 branch で v4 受領証を持つものは 0 件だった。D404 の一般則には触れていない。
  この判断はユーザーが差し戻せるよう明示する。
- 実務上の発見を 2 つ記録する。(i) **背景 job の `> file` redirect は長いテスト走行で早期に
  切られる** (4 回観測)。テスト走行も codex 子と同じ detached + `.done` + 待ち手の形にする。
  (ii) **dispatch 経路の `FAILED` 行には理由が付かず、行頭に `| ` が付く。**
  pytest の failure digest は 10 件しか描画しないので閉包の根拠にしない。

## 次の一手差分

### 更新

- [T-1283] **P1・段 (b) の第 1 段を実装。残余 3 件は未閉鎖**: 受領証の著者を候補外コードへ
  移し、land が実行 bytes 3 本を独立照合するところまで実装した。閉じていないのは
  (i) 起動権が tip 側待ち手にあること、(ii) bounded / dispatch の内側の子が未束縛であること、
  (iii) land verifier 自身の帰属。いずれも [T-696] の協調境界に残る。**「閉じた」とは記録しない。**
  成果物影響 = 未対処の残余がある限り、改変された tip は実走していない受入を `child-green` として
  台帳へ残せる。
  base: 42f6d136eca0298655286b07e6bcf145dacb87de9dc336546c6e27beee0afb9d
- [T-1195] **P1・記録条件を [T-1283] の裁定へ更新した**: F385 の恒久対応欄を本 wave の実装に
  合わせて supersede した。**「閉じた」とは書いていない。**
  成果物影響 = 対応欄が実装と食い違うと、恒真ゲートを閉じたと誤読される。
  base: dfaa9b48a438eaa58b21d3472773c85c45e7023cc727fc42b7bbfc7687bdcb0d

### 新規

- {{T:acceptance-launcher-outer-entrypoint}} **P1・新規 (段 3 レンズ A #1 / 段 6 レンズ A #1)**:
  親の固定起動点を main checkout 側の launcher 絶対 path へ移し、起動権を wave tip の外へ出す。
  lease の claim / release の主体が変わるため D253 の待ち札意味論に触れる。
  `.claude/commands/dev-wave.md` の逐語 2 行と `orchestrator/tests/test_check_docs.py:50,55` の
  同時改訂が要る (byte は 2 occurrence で 10 bytes 空く)。
  成果物影響 = 未実施なら、改変された tip 側待ち手が launcher を起動せず受領証を自作できる。
- {{T:acceptance-inner-child-binding}} **P2・新規 (段 6 レンズ B #3)**:
  bounded / dispatch の内側の子が `tools/run_tests.py` を pathname から読み直すため、
  `runner_executed_sha256` が束縛するのは外側 runner の bytes だけである。
  内側の子にも同じ blob bytes を渡す形にするか、field の意味を「外側 runner bytes」と明記する。
  成果物影響 = 未実施なら、実走 runner の digest 証拠なしで certified 選択が受理されうる。
- {{T:land-verifier-attribution}} **P2・新規 (段 6 レンズ A #3)**:
  land verifier 自身も候補コードである。D254 の provenance checker と同型に main へ束縛する。
  成果物影響 = 未実施なら、tip-only 改変で受領証検査そのものを迂回できる。
