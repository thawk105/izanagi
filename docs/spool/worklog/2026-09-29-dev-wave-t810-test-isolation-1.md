---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-t810-test-isolation
seq: 1
title: t810 coordinator の登録走査を、他 wave の撤去途中 (gitdir も locked も無い管理 dir) で止めないようにした。受入の live 3 node は実 repo が検証の本質なので live のまま残した (コード + test + insight、branch dev-wave-t810-test-isolation)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/git-maint-2026-09-29/md_4.txt` と、ユーザー追加指示「末尾の (任意) 本番の関数も直す案も実施する。これが本文の『本番の fail-closed 不変』『scope 外: t810_coordinator.py の本番』に優先する」。本番側の判断は {{D:t810-skip-unlocked-absent-registration}}。一次資料は `output/insights/2026-09-29/t810-test-isolation/README.md`。
- 台帳: 本文に「t810 coordinator テストの共有 worktree 登録依存」を含む item は次の一手に無かった。本件は本 wave で閉じ、残る DW-O11 の改訂だけを新規 item にした。
- 対象 3 node (`test_prepare_group_rejects_forged_git_identity_before_any_mkdir`・`..._rejects_self_consistent_foreign_git_identity_before_any_mkdir`・`..._accepts_external_root_with_anchor_union`) は、coordinator が設置先から anchor を導き caller / config の偽 identity で外せないことの検査で、実 repo が本質と判定した (D1101 と同じ理由)。テスト側の切り離しはせず、理由を一次資料に書いた。共有 repo への依存は本番修正で撤去途中の状態についてだけ外れた。add 途中と読み中変化 (F670) は従来どおり拒否で、テストは既存の再試行で吸収し、本番の coordinator は止まりうる。
- 段 3 の裁定: 相談 A の「手で gitdir だけ消した生きた木が roots から落ちる」「小さい roots で受理が広がる」は real としてユーザー裁定で受容し、D に受理集合の変化として明記した。「列挙→open→lock 確認の競合」は、列挙後に作られた管理 dir と同じ roots になるだけで現行の timing を超えないので refuted。md_4 案より狭く locked を見る判断と、`lexists` でなく `os.lstat` を使う判断は plan と相談 B の指摘で採った。
- 段 6: 敵対レビュー 2 本 (正しさ境界 GO、過剰・削除 NO-GO は insight の一般化の限定と台帳登録確認だけで、どちらも親の docs で閉じた)。コードの fix は 0 巡。変異は独立 clone で probe (request 36268.nqsv) → final (request 36291.nqsv、Elapse 275 秒) で baseline 緑・6/6 KILLED (表は一次資料の「検証」節)。
- 焦点走 (wave 木 `83ac3f959`、計算ノード request 36204.nqsv、Elapse 76 秒): `test_t810_coordinator.py`・`test_t810_pbs_wrapper.py`・`test_real_repo_serialization.py` で 193 passed・1 skipped・1 failed。赤は `test_real_repo_serialization.py::test_real_repo_writers_do_not_materialize_oracle_environment_candidates` (内部で呼ぶ `test_p3_s4_loop` の campaign lock identity 不一致) で、lock identity の計算は変更 file を参照せず、同 tip の単独再走 (下位 node 込み 2 件) は 2 passed。非帰属とした。
- セッション異常: EnterWorktree の name 形が `Could not read the repository git config` で失敗し、手動 add + path 形で入った (既知)。実装子用の子木は submodule 初期化が `runtime-io-failure` で 1 回落ち、再実行で通った。変異用 clone の起動で親が SHA を 1 文字誤り、自作 script が `{ }` 内の exit で `.done` を書かず待ちが空転した (約 10 分)。

## 次の一手差分

### 新規

- {{T:dwo11-removal-window-revise}} **P3・新規**: `docs/dev-wave/operations.md` の DW-O11 にある「撤去途中で gitdir を欠く管理 dir は t810 coordinator の登録走査で他 wave の受入を赤にしうるので、受入の走行中は撤去を避ける」は、{{D:t810-skip-unlocked-absent-registration}} の着地で撤去途中の不在については理由が消えた。add 途中 (locked あり・gitdir 無し) と読み中変化の窓は残るが、テストは再試行で吸収する。撤去と受入の窓分けを外すか、残差だけを書く文へ改める。exact pin と節予算を確かめてから直す。
