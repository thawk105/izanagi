---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: rulings-full4-land
seq: 1
title: /rulings 全件 第 4 回 — ユーザー裁定 11 件 (docs、branch worktree-rulings-full4-land)
---

## 本文

`/rulings 全件` の第 4 回。収集は local main worklog 末尾 (609) の生存 474 項を carry 解決した
実体 (未解決 0)、repo 外の裁定 inbox 76 件、稼働 2 wave (`t650-lease-release` /
`t1180-pilot-approval`) の未 land fragment、`docs/phase3.md` 見送り台帳の発火条件
(直近 wave が触った語で照合、発火 0 件)。受入 lease は収集時点で free だった。

**ユーザーは 11 件すべてを裁定し、そのうち 3 件で親 (rulings) の推奨を採らなかった。**

1. **perf は要らない ([T-1253])。** 逐語の要旨:「ここの計算ノードには perf は要らない。だからと
   言ってここを使わないとか研究を進めないとかはない。何度も言わせるな。perf がなくても izanagi は
   有意なものとして作り込んでいく」。rulings の推奨「正式系列だけ perf 実在を要求」は却下された。
   **perf 不在を閂として記録しない**という運用方針でもある。
2. **保留は永遠のスルーではない ([T-1222])。** 逐語の要旨:「永遠にスルーなんてしません。テストが
   間違っていればテストを直す。テストされているものが間違っていればそれを直す。**リワードハック禁止**」。
   rulings の推奨「既知漏れ 4 件を恒久保留へ登録」は却下された。保留は費用構造への対処であって
   欠陥を見ないことの許可ではない、という原則が確認された。既存の恒久保留 59 件も同じ目で見直す
   射程に入る (一括解除の指示ではない — 個別に判断する)。
3. **AI ができる操作をユーザー手番にしない ([T-1255])。** 逐語:「床値の操作？あなたでできるものを
   私にやらせないで」。台帳が「実凍結はユーザーの対話 shell 手順」としていたのが誤りと裁定された。

**[T-1255] を親がその場で実行できなかった理由 (実測)。** `s8b_floor_campaign.freeze_protocol` が
`sys.stdin.isatty() is True` を必須にしており、背景 job の stdin は tty でない。同関数の docstring
自身が「isatty は actor 認証ではなく、PTY 割当・module 直呼びで迂回可能な**誤操作防壁**である」と
書いている。**PTY を偽装して通すのは迂回にあたるため行わず、防壁を AI が正規に満たせる形へ
変える設計変更として [T-1255] を書き換えた。**

**[T-1269] は親がその場で実施した。** `/tmp/.git` (空ディレクトリ、2026-07-28 作成) を
`rmdir` し、不在を確認した。

**収集面の実測 — 裁定済みの 4 項が「新規」のまま台帳に残っていた。** [T-1242] / [T-1243] /
[T-1244] / [T-1246] は 2026-08-16 第 3 回 #24〜#27 で裁定済みだが、控えの「同 wave の land 時に
本文へ反映すること」が実行されず label が「新規」のままだった。**未採番のまま裁定した項は、
起票 wave の land で反映されないと裁定が消える**ため、本 fragment で 4 項の label を是正する。

**運用の道具を repo 外へ集約した (ユーザー指示)。** 毎回書き起こしていた補助スクリプトを
`/work/1/SFC/tanab/scripts/` へ置き、`next-tasks` の入口がその path を参照するようにした。
`next_tasks_snapshot.sh` / `next_tasks_carry_p1.py` は `dev-wave-jobs/bin` から移し、旧 path は
symlink で残した (稼働中の別セッションが旧 path を参照していても壊れない)。新規に
`worklog_carry_resolve.py` (carry stub の連鎖を辿って実体へ解決する) と
`spool_base_digest.py` (carry 解決後の実体から `base:` の sha256 を計算する) を置いた。
`next-tasks` の入口には自己改善 gate も新設した (実測したときだけ発火し、routing は
`docs/skill-self-improvement.md` へ委譲、repo 内へ及ぶ変更は裁定へ返す)。

一次資料 = repo 外の裁定控え `rulings-inbox/2026-08-17-rulings-full4-11rulings.md`。

## 次の一手差分

### 完了

- [T-1269] 2026-08-17 /rulings 全件 第 4 回で「削除する」と裁定され、親がその場で実施した。
  本ログインノードの `/tmp/.git` (空ディレクトリ、2026-07-28 作成) を `rmdir` し、不在を
  確認した。これで `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` の
  決定的な赤の原因は取り除かれた (赤の消失そのものは次の走行で観測する)。
  remaining: none
  base: 718ac91eb875f672e8ae5d0ec6d9abb3d0a0e236ad6fddc5e6f53c995219c5a2
- [T-1274] 2026-08-17 /rulings 全件 第 4 回で**現状維持**と裁定され終端した。本 wave が入れた
  signal mask の autouse guard は module scope に留め、`conftest.py` へは一般化しない。独立 2 例目が
  出ていない段階での一般化は全テストへ毎回コストを乗せる予防的な保険であり、成長比例のコストを
  テスト経路へ入れない方針と逆を向く。将来 2 例目を観測したら、その時点で新しく起票する。
  remaining: none
  base: ff3bf2df6ea2085f084ee4e3ec88d04ebda12a38214de528a07d54ab6dbe95f1

### 更新

- [T-419] **P1・裁定済み (2026-08-17 /rulings 全件 第 4 回、(1)(2) 見送り・(3) 実施)**: 較正
  artifact の世代有効化で返した 3 件のうち、(1) 実行時 attestation の `effective_clock.method` を
  実体一致にする案と (2) 既に ever-active な第 1 世代の自己不整合へ gate を置く案は**見送り**と
  裁定された。前者は Pegasus の全 attestation が即座に落ち、後者は live campaign の COMMIT 監査を
  含む 6 consumer が止まる。どちらも受理を厳しくする側で、既定方針 (粗い provenance で足りる /
  凍結チェーン検証は保留 / 防御的堅牢化は見送り) と衝突する。**(3) 床値 protocol path の
  shell 層・driver 層の配線だけを実施する** — 受理集合を変えない配線漏れであり、[T-1255] の
  床値 v2 系が同じ path 解決に依存する。一次資料 =
  `output/insights/2026-08-16_t419-seam-checknet/ruling-package.md`。
  base: a35490b9a581d621a5e826f293d4f65bb892733efc8564ed66d005f0b3a6194c
- [T-1253] **P1・裁定済み (2026-08-17 /rulings 全件 第 4 回、perf 無しで進める)**: 正式系列
  (official) も perf 不在の計算ノードで進める。**親の推奨「正式系列だけ perf 実在を要求」は却下**。
  要求している実箇所は 2 つで、`orchestrator/campaign/s8b_floor_campaign.py` の `_assert_perf_mode`
  (official では perf_preflight receipt が存在するだけで `CampaignAbort`、`use_perf` が偽でも
  `CampaignAbort`) と、`orchestrator/campaign/pipeline.py` の qualification opt-in 評価形状検査
  (`use_perf is not True` を拒否)。両方を外す。**条件** — これは受理集合を広げる変更なので、
  degrade した事実 (`use_perf=False` と perf 不在の根拠) が成果物から必ず読めることを実装の
  受入条件にする。「perf 有りで測った」と読めてしまう成果物を作らない。degrade の入口は既存契約
  (`use_perf_from_receipt` が唯一の入口) を使い、新しい迂回路を作らない。2026-08-16 裁定 #1
  (探索経路のみ degrade) の射程を正式系列へ広げるもので、#1 と矛盾しない。
  base: 1ca4dbc686e838106fc4c26e133b8ccb2591669c69ead376634608b5816b2b07
- [T-1222] **P1・裁定済み (2026-08-17 /rulings 全件 第 4 回、保留せず直す)**: 成長比例の既知漏れ
  4 件 (`test_codex_agents.py` 7 / `test_dev_waves_integration.py` 1 /
  `test_s8c_preregistration_invariant.py:257` 1 / `test_check_ai_provenance.py` 2) を恒久保留へ
  登録する案は**却下**された。各件について「テスト側の書き方が悪いのか、テスト対象の設計が
  悪いのか」を判定し、該当する側を直す。D451 の個別裁定は「保留するか」ではなく「どちらを
  直すか」の判定へ置き換わる。**保留は費用構造への対処であって、欠陥を見ないことの許可ではない**
  (検査を消して緑を買う形は規律 2 が禁じる)。残る母集合の問題 (段 2 の全件走査が
  `module.func(ROOT)` 形の in-process 呼び出しを拾えず 11 top-level node を落としている) は
  変わらず未了で、探索の実装が要る。
  base: eeabf80284df0744d8304bba459c3cc0eed4969ca8c5b993058bf9dccbf8c69e
- [T-1255] **P1・裁定済み (2026-08-17 /rulings 全件 第 4 回、AI 実行可能へ設計変更してから凍結)**:
  床値 v2 protocol の実凍結は**ユーザー手番ではない**と裁定された (「あなたでできるものを私に
  やらせないで」)。実測では `freeze_protocol` が `sys.stdin.isatty() is True` を必須にしており
  背景 job から実行できないが、同関数の docstring 自身が isatty を「actor 認証ではなく迂回可能な
  誤操作防壁」と定義している。**PTY 偽装による通過は迂回にあたるため行わない。** したがって
  本項は「tty 判定を、明示フラグ + AI provenance 記録 (誰がどの承認値で凍結したかが監査に残る形)
  へ置き換え、そのうえで凍結を実行する」へ改める。凍結の中身は変わらない — 自由値ゼロ、差分は
  `ccbench_pin` 1 欄、前提ゲート 3 つは通過済みで、実行後は `ccbench_pin` 以外が 1 byte も
  動いていないことを確認する。create-only のため旧 protocol を退ける手順を含める。
  base: b83ce5b99c534d7d090757caff8da01e8ac0509851ed7bd8f69afa68b74074f7
- [T-1245] **P2・裁定済み (2026-08-17 /rulings 全件 第 4 回、既裁定 #10 を適用)**: dev-wave 手順書の
  予算超過で差し戻された是正 3 件は、2026-08-16 第 3 回 #10 の方針 (述語にできる義務は機械検査へ
  移送するのを主、文章でしか書けないものは別 reference 新設を従、**上限は上げない**) をそのまま
  適用して閉じる。新しい判断は要らない。同じ壁を報告している [T-1260] / [T-1265] / [T-1273] と
  1 wave にまとめる。
  base: 9ed83b4f78c374521cdd6249742781ced37de5e646e69f5cf04a51a2f6d4d48b
- [T-1260] **P3・裁定済み (2026-08-17 /rulings 全件 第 4 回、既裁定 #10 を適用)**: `DW-O01` へ
  `--lane` が段 3 専用である旨を入れる件は、[T-1245] と同じ #10 の方針で処理する。予算値の
  引き上げはしない。model 権威行の exact 1 件検査に抵触した点は、移送先を機械検査側に取れば
  回避できるかを実装時に判定する。
  base: ed5378f8178efb6f43143618aa0888c550c289fd112b83fe79861444ce208e28
- [T-1265] **P3・裁定済み (2026-08-17 /rulings 全件 第 4 回、既裁定 #10 を適用)**: codex 子が
  `git merge` を起動できないための分担 (親が merge、子は working tree の競合解決だけ、`add` と
  commit は親) を `DW-O17` へ書く件は、[T-1245] と同じ #10 の方針で処理する。親が推した
  「submodule pin の理由説明を削って空ける」は、既存文の削除が意味等価な縮約でないため採らない。
  base: 96117c47fa6a2efc6dff7c7bda445855a65961c6c1ba27f99f70d7a697a766dc
- [T-1273] **P2・裁定済み (2026-08-17 /rulings 全件 第 4 回、既裁定 #10 を適用)**: `DW-O02` へ
  「子へ Web 検索を禁じる」義務を入れる件は、[T-1245] と同じ #10 の方針で処理する。**この 1 件は
  述語化しやすい** — 子の argv / 設定側で Web 検索を落とせるなら機械検査へ移送する側の典型で、
  実害 (子の成果物 1242 秒・38 model call ぶんが `evidence_status=invalid` で全損) も測れている。
  base: 94d9d94a9fd270edc4885fead01013b4cf994edac31acfaba5a8db8b054f3d11
- [T-1239] **P2・裁定済み (2026-08-17 /rulings 全件 第 4 回、機械検査にする)**: 取り残し branch の
  着地判定を機械検査にする。代理指標での誤判定が 3 例 (path 実在 / lease 混雑の worktree 数推定 /
  三点 diff の行数) あり、`DW-G03` の「族一般化には独立 2 例」を満たしている。判定材料は
  `git cherry` の patch-id、branch 名**とタスク ID の両方**での台帳・archive 検索、内容逐語の
  照合の 3 点で、いずれも機械化できる。誤判定の帰結は「着地済みの成果を二重採番する」か
  「未着地の成果を捨てる」のどちらかで、復旧が高くつく。実装面のため Codex author が要る。
  base: fca64225e722ad876439ba1fac67525b90d426e02f59973e159be10550dd42c7
- [T-327] **P2・裁定済み (2026-08-17 /rulings 全件 第 4 回、U-2 は失効)**: U-2 の「署名 tag で
  ユーザー手番」は**失効**として閉じる。2026-08-12 方針 (論文主張に要るのは粗い provenance のみ、
  署名・束縛機構の新設は既定で見送り) と衝突し、例外を作る理由が台帳に無い。同方針により
  2026-08-16 第 3 回 #24 / #25 が同型の署名機構を却下している。12 述語の充足判定から U-2 を外す。
  残件は変わらず「条件ごとの充足判定器 (述語 green 化段)」で、evidence evaluator と contract JSON は
  名前だけで readiness を偽昇格させないため未編集のまま (SATISFIED 0 件を維持)。
  base: ac0de57eb145d7e55436b155ae4a90030afc891cb144522fe56298bbe8859099
- [T-1242] **P2・裁定済み (2026-08-16 /rulings 全件 第 3 回 #24、作らない)**: SWO receipt を
  「oracle が実際に走った」証明にする署名機構は**新設しない**。「bytes 級の凍結証拠・署名・束縛
  機構は既定で見送り」に正面から当たるため。**条件** = 「閉じた」と書かず、既知の未閉鎖として
  failures 台帳へ登録し [T-696] に束ねる。本項は起票 wave の land で label が反映されておらず
  「新規」のまま残っていたのを 2026-08-17 第 4 回で是正した。
  base: 3f1b8327d51d356a124935b296968874a81511a7398a46014d551bb6823b5b26
- [T-1243] **P2・裁定済み (2026-08-16 /rulings 全件 第 3 回 #25、作らない)**: admission 台帳を
  削除して同一 bytes で再構成する攻撃への耐性機構は**新設しない**。[T-1242] と同じ理由・同じ条件
  (既知の未閉鎖として failures 台帳へ登録し [T-696] に束ねる)。1 つの裁定が両項を覆う。本項も
  label が「新規」のまま残っていたのを 2026-08-17 第 4 回で是正した。
  base: 9a174f0b82165c7de85305fae59a842113a099f09e81caa0cb5a7ee2d92ce318
- [T-1244] **P3・裁定済み (2026-08-16 /rulings 全件 第 3 回 #26、非権威のまま)**: `measurement_head` は
  **非権威 field のまま**とし、位置づけを明記する。commit 束縛の新設は「計測は HEAD でなく内容
  ハッシュに束縛する。HEAD 等値要求は偽の結合」という既定の考え方に反して偽の結合を作るため。
  本項も label が「新規」のまま残っていたのを 2026-08-17 第 4 回で是正した。
  base: dc4ac4c2d071a9afae5269fa4eed3346a4b65aee79e6b424aa5ddf2738dd8ca1
- [T-1246] **P3・裁定済み (2026-08-16 /rulings 全件 第 3 回 #27、保留を維持)**: holdout 凍結の
  generator source pin の hold は**保留を維持**する。床値 v2 再測定の束縛を記録基準へ緩めた裁定
  (第 3 回 #7) の決着後に、同じ基準で再訪する。先に開けると #7 の判断と干渉する。本項も label が
  「新規」のまま残っていたのを 2026-08-17 第 4 回で是正した。
  base: 446d4c62d97fc127129f0a69857d7e7b83c635d0719885e6d905b15a2f286835
