---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-known-reds
seq: 1
title: 既知赤の機序を 20 回以上ぶりに完全確定させ、唯一残った修理経路が受理集合の意味を変えることを示して裁定へ返す (docs、branch worktree-dev-wave-known-reds、実装差分ゼロ)
---

## 本文

依頼は「既知赤のテストがあれば適切に直す。テストが間違っていればテストを直す。テストされている
ものが間違っていればそれを治す。**リワードハック禁止**」だった。

**決定的な赤は存在しなかった。** 本 wave の全走 (Pegasus request `915134.nqsv`、bnode、113.95 秒) は
12271 passed / 95 skipped / **0 failed**、`tools/check_docs.py` rc=0、`tools/check_ai_provenance.py`
rc=0 (3853 件、新規違反なし)。95 skipped は環境条件 skipif と D335 恒久保留だけで、壊れて skip に
なっている隠れ赤は無い。`pytest.ini` の `testpaths` は `orchestrator/tests` で、test file 212 本
すべてが全走の収集対象である。**ただしこの実測から言えるのは「その tip・その収集集合・その worker
割当・その負荷で常時必敗する赤は無い」までで**、順序依存・attempt 2 依存・負荷依存の決定的な赤や
低頻度 flake は否定できない (敵対レンズ A の指摘を採用)。

したがって既知赤の実体は、ユーザーが 2026-08-16 に「同一 wave にまとめよ」と裁定した
[T-1005] (F57 族) と [T-1164] (signal 転送族) の 2 つの非決定テスト族である。

**[T-1298] の機序が完全に確定した。** 本エントリ以前、F57 は 20 回以上の再発で原因未確定が続き、
2026-08-17 の [T-190] 計装で「retry の attempt 2 で preflight が 3.6 倍になり evidence grace
1.0 秒を食い切る」ところまで分かっていた。本 wave はその先を静的に詰めた。

- 台帳が挙げた容疑者 2 つのうち **codex executable 再 hash は計測区間の外にある**。
  `_hash_file` は `tools/codex_worker_launch.py:1670`、計時起点 `attempt_started_ns` は `:1698`。
  sidecar の `phase_duration_s.attempt_preflight` はこの起点以降しか測らない。
  **計測区間の中身は `_require_attempt_hook_installation` (`:1764`) ただ 1 つ**であり、
  容疑者は hook / guard 再検証だけに縮んだ。
- **本当の欠陥は 3.6 倍そのものではなく、evidence grace の起点である。**
  `evidence_deadline_ns = state.started_ns + evidence_grace_s` (`:1797-1800`) の起点は
  preflight の**前**で、子の spawn は preflight の**後** (`:1778`)。強制停止条件 (`:1882-1891`) は
  spawn 直後の最初の poll で必ず成立する。よって **preflight 所要が evidence grace を超えた瞬間、
  子は生まれた直後に必ず殺される。子の挙動は一切関係しない。**
  [T-190] が保存した 3 bundle は preflight 完了と SIGTERM が 1 ミリ秒差で並んでおり、これと一致する。
  さらに preflight が正常な 0.29 秒でも子が得る猶予は公称 1.0 秒でなく 0.71 秒であり、
  **この gate の実効閾値は最初から負荷依存**である。本番既定 `--evidence-grace-s 90` でも構造は同じで、
  余裕が大きいだけである。

**唯一残った修理経路が受理集合の意味を変えるため、実装せず裁定へ返した。** 起点を spawn 後へ移すと、
現行で強制停止されていた attempt が accepted の 7 条件へ到達しうる。敵対レンズ A はこれを
「高速化ではなく受理集合の拡張」と判定し、親はこの分類を受け入れた。`--evidence-grace-s` の意味を
定義した decision も help 文も repo に存在しないことを実測しており、**意図が未確定の契約を親が
一方的に決めることになる**。裁定は {{T:evidence-grace-origin}} へ分離した。

**他のあらゆる修理経路は不採用にした。** 予算引き上げは台帳 [T-1298] 自身が「上げるだけだと
『遅くなっても通る』方向に受理集合を広げる」と警告済み。hook / guard 再検証の頻度削減は
`test_hook_preflight_is_rechecked_before_each_retry` と guard drift 時の `codex_spawns == []` が
守っている attempt 間 drift の門であり NO-GO。待ち合わせと称した sleep、fixture の real repo を
tmp mirror へ逃がす案、受入での xdist 直列化、再 hash 削除もすべて不採用とした。
**すなわち依頼された「直す」は、リワードハック禁止という同じ依頼の下では実行不能である。**

**F57 と S2 はどちらも D362 の 3 条件を同時には満たさない** (単独再走が緑なので「main 単独で再現」が
不成立)。過去この族を通して land できていたのは D362 例外の適用ではなく、全走を再投入して緑を
得ていたからである。「既知赤」という呼称は受領証の状態を誤記している。これは棄却でなく記録として残す。

**親の provisional 裁定は 3 つとも子に否定された。** (P1) 3 秒の wall 予算説は計測で否定、
(P2) signal 族の全面解消は mutation 側の帰属欠落で過大、(P3) 「ready file が handler 設置完了を
含意しない」は誤りで、fake child は SIGINT/SIGTERM handler を設置してから ready を書く
(`orchestrator/tests/test_mutation_worktree.py:97-104`)。

**エージェント工数:** codex 子 3 本 (段 2 plan × 1、段 3 敵対 × 2、いずれも `reasoning=max`、
`sandbox=read-only`)。実装子・fix 子は裁定により起動していない。段 3 の 2 本は独立に
「予算引き上げはリワードハック」へ収束した。

## 次の一手差分

### 更新

- [T-1298] **P2・機序確定済み、修理は {{T:evidence-grace-origin}} の裁定待ち**: 容疑者だった
  codex executable 再 hash は sidecar の計測区間外 (`tools/codex_worker_launch.py:1670` vs `:1698`)
  であり構造的に除外された。計測区間の中身は `_require_attempt_hook_installation` (`:1764`) だけ。
  ただし **3.6 倍の内訳を詰めても修理には届かない** — 実際の欠陥は evidence deadline の起点が
  launcher 自身の preflight を含むこと (`:1797-1800`) であり、preflight が grace を超えれば
  子は spawn 直後に必ず殺される。3.6 倍は引き金であって欠陥ではない。
  内訳の分離は hook 再検証内部の個別 timer を要するが、**再検証の頻度削減は NO-GO** (attempt 間
  drift の門) なので、内訳が分かっても採れる手が増えない。本項は
  {{T:evidence-grace-origin}} が裁定されるまで待つ。
  base: 2341d31f94dc5c049be2950e9c9dd959005c3181d7f93aeffe63813af7233ee5
- [T-1005] **P2・裁定条件が不成立、{{T:evidence-grace-origin}} へ従属**: 裁定文が名指しした共有状態
  3 経路は実測で全て否定された — `~/.codex/sessions` は `CODEX_HOME` と `--sessions-root` が
  tmp へ差し替え済み (`orchestrator/tests/test_codex_worker_launch.py:1575,1626-1627,1642`)、
  receipt / manifest は node ごとの `tmp_path`、docs authority は不一致なら rc=2 で silent rc=1 に
  ならない。よって「fixture 側で断てない共有 mutable state」は存在せず、**裁定文が直列化を許す条件は
  成立しない**。本族の赤は [T-1298] の evidence-grace 型であり、修理経路は
  {{T:evidence-grace-origin}} に一本化された。
  base: aa40efc32c8191313e65c74e18d31aa717c7b1472475b966a6a6b5a9500ac7e4
- [T-1164] **P3・dev_wave_wait 側は支持、mutation 側は未帰属のまま**: `test_dev_wave_wait.py` の
  3 node は `2da49c56` が production の mask 汚染を閉じ、`_handled_signals_are_unblocked`
  (`orchestrator/tests/test_dev_wave_wait.py:75-95`) が test 入口で blocked を fail、出口で漏れを
  assert する正例対照になっている。親の実測では `2da49c56` の子孫 tip 上に受入受領証 18 本があり、
  うち 14 本が `child-green`、signal 族の再発記録は無い。**ただし「再発が確認されない」と
  「構造的に排除済み」は別物**であり、`test_mutation_worktree.py` 側は `2da49c56` の射程外で、
  過去の赤を「同じ xdist worker の先行 polluter」で説明するのは実測でなく仮説である
  (`--dist loadgroup` は同居を可能にするが保証せず、赤 node と polluter の `gwN` 対応が資料に無い)。
  閉じるには mutation 側の帰属実測が要る。
  base: 0d99f62c58f75b22e1fbac5e76be23a38f24c3cc3e607052d92f6be735cda10f
- [T-190] **P2・機序は完全確定、F57 は未閉鎖**: 「1 つ確定したが内訳未分離」だった状態から、
  evidence-grace 型については**機序が完全に確定した** ([T-1298] 参照)。残るのは F285 の走 A / 走 B 型の
  帰属である。本項の計装が無ければ本 wave の確定は不可能だったので、D249 の「計装が先」は正しかった。
  base: 7c8cb3787f9e796ecb994b9c7f55676d6b9b831a5de0ececa02b48a036f24942

### 新規

- {{T:evidence-grace-origin}} **P1・ユーザー裁定待ち**: `--evidence-grace-s` の deadline 起点を
  どこにするか。現状 (a) は attempt state 作成時で、**launcher 自身の preflight が子の猶予を食う**。
  (b) spawn 完了時へ移す (親の推奨)。子が公称どおりの猶予を必ず得て gate が決定的になり、
  総時間は `max_wall_clock_s` が引き続き有界化する。代償は、現行で preflight 中に期限切れとなっていた
  attempt が子起動後まで生存すること。(c) 起点据え置きで preflight 所要を控除する — 控除量が
  観測値依存になり閾値が再び可変になるため親は推奨しない。
  **親の推奨は (b)。** 現行 (a) の実効閾値は既に `grace - preflight` で非決定的であり、
  「負荷が高い日は子の猶予が短くなる」gate は測ろうとしている性質を測っていない。(b) は緩和ではなく
  gate を宣言どおりの意味へ戻す是正だと親は考える。**ただし敵対レンズ A の「受理集合の拡張」という
  分類は正しく、この択一は親の権限を超える。** [T-1298] / [T-1005] / F57 はこの裁定に従属する。
