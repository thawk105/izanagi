---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t720-import-unify
seq: 1
title: orchestrator/campaign の import 形を canonical へ統一し、再発を機械検査で固定した ([T-720]) — 変異がレビュー 3 本を通った検出漏れを 2 件炙り出した (コード + docs、branch worktree-dev-wave-t720-import-unify)
---

## 本文

- **欠陥の再現を親が実測してから着手した。** `sys.path` に `orchestrator` を足して
  `import orchestrator.campaign.env_contract` と `import campaign.env_contract` を両方行うと、
  `__file__` が同一なのに module object の id が異なる。exact 型検査 (`type(x) is not Y`) を
  跨ぐ値がここで沈黙して弾かれる (F171 で 2 巡、F187 で 3 連続)。
- **親 brief の件数が過少だった。** 検索が `from campaign import X` (ドット無し) を落としており、
  campaign 内 52 → **53**、`orchestrator/tests` 47 → **82**。段 2 プランと段 3 レンズが独立に
  数え直して一致したので、段 4 で brief を訂正した。
- **段 3 の敵対相談 2 本 (sol / luna) はどちらも NO-GO。** 親が全 blocker を実ファイルで裏取りし、
  すべて real と確認した。とくに (i) `output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py`
  が受入テストから subprocess 実行される現役 consumer であること、(ii) Pegasus の校正・attestation
  正規経路 (`tools/pegasus/run_probe.py` の callable importer、`certify_calibration.sh` と
  `t141_region_profile.sh` の heredoc、`orchestrator/calibrate.py`) が閉包の外にあったこと。
  これらを scope に足さなければ、統一しただけで `attestation-*.json` が生成されなくなる。
- **親が自分で足した runtime guard を段 4 で取り下げた。** 「`campaign` と
  `orchestrator.campaign` の同居を `ImportError` にする」案は、(a) F187 が記録する再発検知契約
  (「両方が通り、両 namespace で module object が同一」) と逆を向き、(b) 受理集合を縮小し、
  (c) 既存テスト 2 本の期待値変更を強制する。しかも**ユーザーの依頼に含まれていない上乗せ**だった。
  依頼の「機械検査」は静的検査が満たす。恒久設計は {{T:dual-namespace-permanent-policy}} へ返す。
- **親の裁定 R7 が計算ノードの実測で 1 つ倒れた。** 「二重 namespace のテスト 2 本は完全に無編集で
  残す」は `test_campaign.py` について成立しない。同テストは module 冒頭の legacy import と
  対で成立しており、片方だけ canonical 化すると `layout_module._effective_uid` の差し替えが
  別 object に当たって静かに空振りする (2 件が実際に赤くなった)。最終形は「冒頭は canonical、
  別名テストの中だけで実 legacy namespace を読む」で、**assert は 1 つも変えていない**。
  合成 module への置換は段 6 レビューが「実 topology の退行を検出しなくなる」と正しく指摘し、撤回した。
- **段 6 の敵対レビュー 2 本と焦点再レビューもすべて NO-GO。** must-fix は延べ 10 件。
  最も重かったのは検査自身の恒真化で、違反も例外も 0 件の規則は走査の配線を切っても
  空集合同士で一致して緑のままだった。合成 repository に規則ごとの違反を仕込む end-to-end
  配線テストで塞ぎ、4 つの走査すべてについて「切れば赤」を実測した。
- **変異が、レビュー 3 本を通しても残っていた検出漏れを 2 件炙り出した。** これが本 wave で
  最も価値のある観測である。(i) `sys.path` への `<repo>/orchestrator` 挿入を `pathlib` 形でしか
  検出できず、**本 wave 以前に実コードが使っていた `os.path` 形**を素通りしていた。
  (ii) それを直した後も、module 別名 (`import os as _o`) 経由を素通りしていた。
  どちらも変異を素の形へ書き換えて逃がすのではなく、検査側を直した。
  詳細は {{F:mutation-found-what-review-missed}}。
- **変異 M7 の初回は親の設計ミスだった。** `KNOWN_EXCEPTIONS = () or (...)` は空 tuple が
  falsy なので右辺が返り、何も変わらない等価変異。DW-M02 に従い初回結果を消さず erratum を残した。
- **成果物影響 (両レンズが独立に確認)。** `env_contract.py` / `env_contract_activation.py` /
  `campaign_lock.py` は無編集で、contract loader の blob pin は不変。`FROZEN_MANIFEST` 23 path と
  変更集合の共通部分はゼロ。一方 `REQUIRED_CODE_IDENTITY_PATHS` との共通部分は 7 件あり、
  **新規 T-126 series の `code_identity` 7 blob hash と `qualification_series_id` は変わる**。
  既存 series は記録済み commit/blob に対して再検証されるので読み替えではない。
- **hook の拒否を迂回しなかった。** 親の CLI smoke で `demo.py` が実際に campaign を走らせ、
  その出力が untracked で残った。commit へは入れていないが、hook が campaign dir への
  `git rm --cached` / `git restore --staged` を拒否するため親は撤去できない。変異 harness が
  untracked を理由に停止したので、**削除ではなく wave tip から clean な専用 worktree を作って**走らせた。
  この untracked は残っている ({{T:t720-untracked-campaign-residue}})。
- **主戦場は Pegasus。** 実行はすべて計算ノードへ dispatch した (login node は hook が拒否する)。
  子は sandbox から queue へ届かず全員「実装済み・未実走」を正直に報告し、実測は親が行った。
- **受入の赤 20 件は「repo を複製・stage して subprocess で実行する harness」に集中した。**
  静的な台帳作りでは見えない consumer 群で、fix 11 巡のうち 4 巡をここに費やした。
  最後に残った 20 件は、親が**同一 worktree で ref だけ切り替える 3 走** (tip → main → tip) で
  帰属を確定してから直した。修正前 tip 20 failed / main 0 failed / tip 20 failed (再現性あり)、
  修正後 tip 347 passed / main 347 passed / tip 347 passed。
  **フレークとの区別を推測でなく実測で付けた。**
- **最後の取りこぼしは「二次波及」だった。** scope 列挙を `campaign` を import する箇所で作ったため、
  **`orchestrator/qualification/**` を canonical 化したことで壊れる消費者**
  (`submit_t126_qualification.sh` の heredoc 3 箇所、`collect_t126_qualification.py`) が漏れた。
  横断的な import 統一では、統一した package ごとに消費者を数え直す必要がある
  ({{F:secondary-fanout-missed-in-scope}})。
- **凍結成果物の違反は無かった。** 途中で `known_axes_freeze.json` が campaign source 7 本の
  sha256 を pin していることに気づき DW-O09 の取りこぼしを疑ったが、実測すると
  pin 済み 6 本は**本 wave 以前から**作業ツリーと不一致だった (harness が歴史 commit から
  復元する設計のため)。凍結の再発行は不要である。

## 次の一手差分

### 完了

- [T-720] `orchestrator/campaign/` の import 形を canonical (`orchestrator.campaign`) へ統一し、
  再発を受入全走の中の機械検査で固定した。package 内は相対、兄弟 package は `..calibrator` 等、
  外部 consumer は `orchestrator.campaign.X`。直接実行 CLI は逐語 3 行の bootstrap で
  `__package__` を確立する。検査は 4 規則 (legacy namespace / sys.path 形 / docs 起動形 /
  package 内の相対形) を、走査の配線ごと合成 repository で固定する。
  remaining: none
  base: 963b103a901a979327522297653c996b6625db9c5d92126a1a60b7c2370723c2

### 新規

- {{T:dual-namespace-permanent-policy}} **P2・新規・ユーザー裁定待ち**: 二重 namespace への
  恒久対応を (a) alias で両名を同一 module object に束縛、(b) 同居を `ImportError` で拒否、
  (c) 静的検査だけで足りるとして何もしない、のどれにするか。
  本 wave は (c) で終えた。(b) を選ぶなら F187 の再発検知文
  (「両方が通り、両 namespace で module object が同一」) と、二重 identity を前提とする
  既存テスト 2 本 (`test_campaign.py` の別名 pin 共有、`test_reflux_ir.py` の D149(5) peer 受理) の
  supersede が要る。成果物影響 = 現状は混在が再発しても import 時には落ちず、
  静的検査の次回走行まで検出が遅れる (取り逃しではなく遅延)。
- {{T:import-scan-non-source-artifacts}} **P3・新規**: 静的検査の走査対象を Makefile / CMake /
  qsub script / JSON 設定へ広げるか。段 6 レンズ B が提起し、両レンズと親が独立に全走査して
  **現 repo に該当する legacy module 名は 1 件も無い**ことを確認したため、DW-G04
  (発火条件を満たす既存 artifact path を書けない機能は設計メモに留める) により見送った。
  再訪条件 = それらの経路に module 名が実際に現れたとき。
- {{T:t720-untracked-campaign-residue}} **P3・新規**: wave worktree に
  `output/campaigns/wiring-silo-enumerate-1cb2c67f/` が untracked で残っている。
  親の CLI smoke で `demo.py` が実際に campaign を走らせたもので、2 variant とも
  `g++-13` 不在で abort した使い捨ての出力である。hook が campaign dir への git 操作を
  拒否するため AI は撤去できない。撤去はユーザー手番。
  成果物影響 = 無し (commit に入れていない)。放置すると当該 worktree での変異 harness が止まる。
