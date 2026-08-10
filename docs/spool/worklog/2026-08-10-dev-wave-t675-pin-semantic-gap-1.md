---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t675-pin-semantic-gap
seq: 1
title: whole-file SHA-256 pin の意味欠落 ([T-675]) の設計択一を裁定へ返した — 敵対 2 レンズが両方 NO-GO で親案を command の F26 edge 1 件まで縮めた (docs のみ、実装差分ゼロ、受入 8012 passed / 20 skipped / 486.83 秒 / rc=0、branch worktree-dev-wave-t675-pin-semantic-gap)
---

## 本文

- **ユーザー指示に基づく設計 wave** (「意味検査の機械化案と pin の役割限定案を実測付きで裁定へ
  返す。本番コードは編集しない」)。**実装差分ゼロ**で終端し、段 5・6 を飛ばして `4→7→8→9` を
  通った (`DW-S04` の「実装しない」裁定)。変異 matrix は同条項で免除。受入全走は免除せず実走した
  (実走根拠 nodeid = `orchestrator/tests/test_check_docs.py`、実 repo の pin 定数を読む)。
  裁定パッケージと逐語は `output/insights/2026-08-10_t675-pin-semantic-gap/`。
  受入は 2 走した。1 走目 = tip `ffe28565` で 8012 passed / 20 skipped / 511.08 秒 / rc=0
  (計算ノード `900548.nqsv`)。段 8 の記録 commit 2 本を足した後の**本走 (2 走目) =
  最終 tip `174b2d10` で 8012 passed / 20 skipped / 486.83 秒 / rc=0**。
- **[T-675] の主張を実 repo で実証した。**安全義務の文「正本は `docs/failures.md` F26。」を削り、
  pin 3 箇所 (checker 定数・test 定数・test 内の全文逐語コピー) を同時に再 pin した状態で
  `check_docs` **rc=0 / 違反なし**、`test_check_docs.py` **357 passed / rc=0**
  (計算ノード request `900462.nqsv`)。**失われた義務を名指す検査はゼロ。**
  probe は実編集 → 即時復元 (`DW-O19`)、復元後 sha256 は pin 定数と byte 一致。
- **段 3 の敵対 2 レンズはいずれも NO-GO** (A=sol / B=luna、両 rc=0)。親案と段 2 プランの
  両方を削り、推奨を `command の F26 edge 1 件` まで縮めさせた。
- **レンズ A の中心所見を親が実測で確定させた。**段 2 プランは必須要素を
  `docs/failures.md` と `F26` の別々の token に分解していたが、レンズ A が
  「token の存在検査であって参照 edge の検査ではない」と攻撃した。親が両形式を同時に probe 実装し
  4 状態を測ったところ、**安全文を削って `docs/failures.md` を別行へ足す攻撃で token 形は
  違反ゼロ、edge 共起形だけが赤**になった。正当な言い換え (「F26 (`docs/failures.md`) が正本。」)
  では両形とも緑で、**edge 形は日本語の文言を pin しない。**4 状態すべてで whole-file pin は緑。
- **(a) が新機構でないことを実測で確定した。**`tools/check_docs.py` は既に、pin 済みの
  cleanup-branches command に対して `docs/skill-self-improvement.md` への到達性を検査しており、
  `docs/archive/` には双方向の到達性 lint がある。**「到達性は機械が守り、意味は人間が守る」は
  既にこの repo の実装方針**で、`docs/skill-self-improvement.md` の「義務本文の文言と意味の保存は
  lint に固定せず」との衝突はレンズ A が **refuted** と判定した。
- **一次資料から、pin の費用が反対側にも出ていたことを発見した。**F26 本文に
  「運用則 = 1 worktree ずつ削除し、必要なら timeout を延ばす。command 本文への反映は
  whole-file SHA-256 parity 契約下にあり checker 定数の同時更新を要するため**未実施**
  (次の一手へ登録)」とある。**同じ pin が安全な追記を止め、その未反映が bare `F26` の
  到達先を非一意にして F173 の削除を許した。**
- **親の誤りを 4 件、敵対検証と親自身の裏取りが訂正した。**(i) 段 1 brief の
  「pin と意味検査は交差ゼロ」は誤りで、pin 済み command は既に正本ポインタ到達性を検査されている
  (段 2 プランが反例を出し親が実コードで確認)。(ii) pin 閉包は command 3 箇所ではなく族全体で
  6 箇所 (Skill 側 3 箇所、レンズ B も独立に指摘)。(iii) 必須 literal の token 分解案は迂回可能
  (レンズ A)。(iv) 段 2 プランの「実質上限 24 bytes は checker が強制する値ではない」は不正確で、
  `_assert_cleanup_digest_violation` の「違反ちょうど 1 件」assert により創発的に強制されている
  (親とレンズ B が独立に反証)。
- **`DW-G05` 上は backlog と明記した。**certified 選択・レポート・試行台帳のどの値も受理集合も
  変わらず、変わるのは AI 作業手順の受理集合だけである。このためだけの単独 wave も
  追加 review wave も起動しない。ただし「次の cleanup 系 wave へ相乗り」という先送りには
  上記の実再発例があるため、先送りにするなら所有 wave・発火条件・期限を裁定で明示する。
- **codex 子が 3 回、`.done` を書かずに無音で消えた。**原因は共有 16GiB user cgroup の OOM で、
  上限は session でなく **user 単位**であり同時に走る別 wave の子と食い合う
  (`memory.max` = 17179869184、`oom_kill` = 1308、自分の子ゼロ時点で `memory.current` 10.6 GB)。
  pid 監視の待ち手が 3 回とも検出し、巨大ファイルの全文表示を禁じた prompt へ差し替えた
  再投入 3 本はすべて完走した。詳細は {{F:codex-child-oom-under-shared-user-cap}}。
- **待ち手の pid 選択で 1 度誤報した。**投入直後の `pgrep -f <script>` が複数 pid を返し、
  一時的な pid を待ち条件にしたため、走行中の受入全走を「producer 死」と誤判定した。
  `ps -o cmd -p <pid>` で実体を確認して復旧した。既存 memory `waiter-death-check-by-pid` は
  自己マッチだけを扱っており、この形は射程外である。
- **背景 task の完了通知が 3 回、実体と食い違った。**`.done` 不在・producer 生存・
  計算ノード job が RUN のまま「ACCEPTANCE-DONE rc=0」が届いた。毎回 3 点照合で弾き、
  条件成立でのみ返る待ちへ切り替えて実完了を確認した (memory
  `background-task-notifications-can-be-fabricated` の再確認)。

## 次の一手差分

### 更新

- [T-675] **P2・ユーザー裁定待ち**: 裁定パッケージ
  `output/insights/2026-08-10_t675-pin-semantic-gap/package.md` の R1〜R4。
  要裁定の主項は **R3 = (a) を採るなら `.claude/commands/cleanup-branches.md` の
  `F26` × `docs/failures.md` 同一行共起 1 件だけに限る** (F51・helper path literal・Skill 側・
  全 path 実在性・全 F 番号到達性は `DW-G03` により 2 例目まで却下)。
  R1 = 呼称を「住所 (address edge) の構造 lint」へ、R2 = pin の責務限定を
  `docs/skill-self-improvement.md` の既存 2 行の精密化置換で明記、R4 = `DW-G05` 上は backlog。
  base: 4d6a93f061c02c3d1394a6e803be339e557fe190a0c1ae7b5802e7438f54f40c
