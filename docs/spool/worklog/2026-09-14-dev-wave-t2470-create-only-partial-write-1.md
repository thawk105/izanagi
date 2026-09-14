---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2470-create-only-partial-write
seq: 1
title: [T-2470] create-only writer の作りかけ file を撤去し、他者が追記した台帳は消さない条件を付けた (コード + テスト、branch worktree-dev-wave-t2470-create-only-partial-write、変異 matrix = baseline PASSED・11/11 KILLED・SURVIVED 0・MISMATCH 0、うち受理集合を変える M1-M9 が 9 件で残る 2 件は構造 pin)
---

## 本文

- ユーザーが引数で起票した wave。scope は「本題の修正だけ。仮想リスク向けの gate・検査・台帳・一般化の
  追加は scope 外」と明示された。全 9 段を回した (正しさ防壁に触り受理集合が動くため、`DW-C00` に従い
  敵対検証子を省かなかった)。
- **段 3 sol が、素朴な修正が現行より悪化することを掘り当てた (S-1)。** 「失敗したら無条件に消す」は、
  別 process が正当に追記した台帳ごと消しうる。親が現物で裏取りした根拠は 3 点。(1) 台帳への追記は
  台帳 file 自身への `flock(LOCK_EX)` で行うが、起点を書く writer は lock を取らない。(2) 追記側は起点が
  git に commit 済みであることを要求せず、履歴 append-only 検査は canonical path がどの commit にも
  無ければ拒否せず `None` を返す。(3) よって起点を全 bytes 書き終えてから `fsync` が失敗するまでの窓で、
  別 process の追記が正当に成立する。現行 main はこの時系列で file を残すので正しい。
- **裁定: 撤去してよいのは「この呼び出しが作成し、かつ誰も触っていない file」だけ。** 撤去の直前に
  書いた総 bytes 数と現在の size の一致、名前が指す `(st_dev, st_ino)` と作成した fd のそれの一致を
  確かめ、両方満たすときだけ撤去する。設計判断は {{D:create-only-discard-only-own-untouched-file}}。
- **`fcntl.flock` は足さなかった。照合と `unlink` の間の窓は閉じていない。** 足せば閉じられるが、残る窓は
  隣接する 2 syscall の間であり、追記側はその手前に全 ref の履歴走査を挟む。D205 に従って採らず、
  限界を主張せず明記した。
- **段 3 luna が変異の穴を予言した (L-1)。** 撤去条件を「1 byte でも書けた場合」に狭める変異が当初の
  テスト設計では生存する。注入点 `write_no_progress` (`os.write` が 0 を返す経路) を追加して塞いだ。
  本走で当該変異は 3 node を殺した。
- **親の (P1) を撤回した (段 3 luna L-3 を採用)。** 段 1 で「既存 writer が自らの create-only 契約を
  満たしていない正しさ欠陥だから、D205/D730 の『現行 claim への具体的影響が立証されない追加防御』
  除外に当たらない」と provisional に裁定したが、この一般論は近縁の [T-1854] との区別を立証していない。
  本 wave を進める直接の根拠はユーザーの明示指示である。一般的な堅牢化許可へ転用しない。
- **親の段 1 brief の誤りを 1 件、自分で訂正した。** 初版は「壊れた受領証を読む経路は無い」と書いたが
  誤りで、reader は実在する。ただし中身の sha256 を file 名と照合して落とすので、壊れた bytes が正当な
  受領証として受理されることはない。本件は可用性の欠陥であって規律 2 の直接侵害ではない。段 2 子も
  独立に同じ訂正を出した。
- **棄却した所見。** 段 3: S-2 (通常 writer 同士では敗者が完成物を消せない — open と書き込み try の分離で
  構造的に排除)、S-4 (受領証 digest 検査の迂回は今回の部分 write では参照行が作られないため誤受理に
  至らない)、S-6 (通常の cleanup 失敗は元例外を保つ)、L-5・L-6。段 6: sol の R-1〜R-6、luna の Q-1〜Q-4。
  段 6 の敵対レビュー 2 本とも **must-fix 0 件**。
- **scope 外と裁定した real 所見。** S-7 (外部から名前が別 inode へ差し替えられた後の残余窓)、
  S-8 / R-7 (`os.close` の失敗が元の診断を置換しうる — 今回の差分が作った経路ではない)。
  後者は新規項目として次の一手へ登録した。
- **「部分書き込みの実発生は 0 件」とは書けない (段 3 luna L-7)。** 検索語を変えても対象 writer の
  実障害記録は出なかったが、それは検索不検出であって測定ではない。実害不存在として一般化しない。
- **変異は 2 pass で行った。** nodeid が段 4 時点で存在しなかったため `DW-M07` に従い、全件 SURVIVED 期待の
  probe で観測 node を集めてから、その完全集合を KILLED 期待で本登録した。本走は baseline PASSED・
  KILLED 11・SURVIVED 0・MISMATCH 0・matching 11。`DW-M08` に従い、受理集合を変えない構造 pin 2 件
  (fsync 順序反転 / 絶対 path での unlink) は KILLED の数に数えない。段 6 luna の Q-6 も独立に同じ区別を
  要求した。受理集合または fail-closed 挙動を変える変異は 9 件で全件 KILLED。
- **自分の作りの誤り (erratum)。** probe の 1 回目は 1 件目の後に rc=2 で中止した。原因は harness の欠陥
  ではなく、**親が走行中に wave worktree へ段 7 の下書き file を書いたこと** (`DW-M05` の「変異中は親の
  編集を止める」に違反)。harness は各 runner 実行の前に untracked file を検出して fail-closed で止まる。
  file を worktree 外へ退避して clean に戻し再投入した。1 回目の観測は 2 回目と一致する。
  親は当初これを「実害なし」と誤って報告し、失敗本文を読んで訂正した。
- **実走の実測。** 実装子の自走が `test_trial_registry.py` 262 passed (login、1297 秒)。親の焦点走は
  裁定した consumer 13 file が 2313 passed / 8 skipped / 0 failed (計算ノード、135 秒、rc=0)、
  段 6 luna Q-5 が挙げた参照元 3 file の補完走が 237 passed (計算ノード、76 秒、rc=0)。
  provenance full 監査 rc=0。test 関数名は基底 202 から 209 へ増え、消失 0・改名 0 を親が機械照合した。
- 逐語・変異台帳・spec は `output/insights/2026-09-14/t2470-create-only-partial-write/`。

## 次の一手差分

### 完了

- [T-2470] 作りかけ file の撤去を実装し、他者が追記した台帳と同名の別 inode は消さない条件を付けた。
  変異 11/11 KILLED、焦点走 2 本を実走した。
  remaining: none
  base: a82e45769ce436a69c0770269b6a0db6c09ece1b62f11be4fd3fee9a09edb092

### 新規

- {{T:create-only-close-error-replaces-cause}} **P3・新規 (段 6 レビュー sol R-7 / 段 3 sol S-8)**:
  create-only writer の `os.close(fd)` / `os.close(parent_fd)` が失敗すると、元の write / fsync 例外や
  gate 付きエラーを置換しうる。今回の差分が作った経路ではなく既存経路であり、成果物の値・受理集合・
  参照がどう変わるかは立証されていない。直すかどうかは診断の質の問題として裁定する。
