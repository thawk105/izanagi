---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1131-checker-main-blob
seq: 1
title: 受入の赤を帰属/非帰属へ分ける判定の権威を tested main の blob へ束縛した — 待ち手と land の両層で塞ぎ、判定コード自身は編集しない (コード + テスト、branch worktree-dev-wave-t1131-checker-main-blob)
---

## 本文

**塞いだもの・塞がなかったものを先に書く。** 本 wave が閉じるのは
**`tools/check_acceptance_reds.py` 単独差し替え**の集合だけである。
wave が `tools/dev_wave_wait.py` 自身を書き換えて偽の受領証を直接作る経路は**閉じていない**。
「悪意ある wave を閉じた」と読める記述をしてはならない (段 3 レンズ A の明示要求)。

- **裁定の前提はコードで確認できた。** 待ち手は wave working tree の checker を起動し
  (blob ですらなく working tree の bytes)、受領証の `checker_blob_sha` を `tested_tip` から採り、
  land も `tested_tip` としか照合していなかった。tested main 側と比べる検査は 0 件。
- **親 brief の (P1)「land を編集しない」を段 4 で撤回した。** 段 3 レンズ A が
  「2 file scope では全層が入らない」を real で挙げ、scope 外に分類した。
  親は**技術的主張を real、scope 分類を refuted**と裁定した。根拠は [T-1131] の本文自身が
  land の照合欠落を欠陥の構成要素として名指ししていることである。
- **D403 との非対称を意図的に残した。** D403 (2026-08-15) は待ち手について同じ main 束縛を
  **明示的に却下**している (同 file を編集する wave の受入を永久に拒否するため)。
  checker では [T-1131] の裁定がその代償を受容したので入れた。この非対称の維持可否は
  {{T:waiter-self-authority}} としてユーザー裁定へ返す。
- **D403 は「受領証へ実行 bytes の field を足す」も却下済み**だった。したがって受領証 schema は
  変更していない。land の exact field 集合にも触れていない。
- **裁定文の rc=2 は実行できないので採らなかった。** 裁定の控えは「判定不能 (rc=2)」と書くが、
  本 gate は checker を**起動する前**に発火するため checker の rc=2 を作れない。偽造すると
  「checker が走って判定不能を返した」と誤記録することになり規律 3 に反する。
  実行した手順は `_StageFailure("acceptance-red-check")` (待ち手 rc=70) で、
  受領証を発行せず非帰属の根拠にならない点で効果は同一である。
- **段 3 の敵対 2 本はいずれも NO-GO**、段 6 の敵対 2 本もいずれも NO-GO で、
  **両段とも 2 レンズが独立に同じ blocker へ収束した**。段 6 の blocker は
  「実行される判定コードの内側 git が固定されていない」で、判定コードは受け取った
  別名解決の無効化設定を自ら取り除いていた。修正は判定コード本体を編集せず、
  bootstrap から `command_runner` を注入する形にした。
  **判定コード側に注入 seam を迂回する外部コマンド実行は 0 件**であることを親と焦点再レビューが
  独立に確認した (実呼び出し 52 箇所すべてが同 seam 経由、`subprocess.run` の出現は既定値 2 箇所のみ)。
- **変異 matrix は 3 走した。** 走 1 は runner 範囲が 2 file のとき baseline が赤になり
  harness が本走前に中止した (選択範囲依存の非帰属赤。**fail-closed が正しく効き 60 分を節約**)。
  走 2 は範囲を 4 file へ広げて probe とし、**baseline PASSED・13 変異すべて rc=1・
  SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0**、KILLED 6 / MISMATCH 7。
  MISMATCH はすべて**期待 node 集合の不足**であって検出力の欠如ではない (`DW-M08` の
  probe + erratum 経路)。走 3 で実測 node へ再登録した。
  **M7b (別名解決の無効化を外す) と M7c (内側への注入を外す) がいずれも
  `test_red_checker_internal_git_ignores_replace_ref` を殺した** — 段 6 レビューの blocker が
  実効的に閉じていることの実証である。
  走 3 (権威走) は baseline PASSED、**KILLED 10 / MISMATCH 3 / SURVIVED 0 / TIMEOUT 0**。
  **13 変異すべてで登録した期待 node は 1 件も欠けずに落ちた** (missing 全件ゼロを実測)。
  検出力は 13/13 で成立している。
- **MISMATCH 3 件 (M1 / M7a / M8) の余剰 node は [T-1169] の既知フレークだった。**
  3 件とも余剰は 1 件で、`test_public_main_real_signal_after_success_uses_restored_handler`
  または `test_public_main_failure_restores_handler_without_release`。後者は [T-1169] が
  名指ししている nodeid と完全一致し、前者も同じ `test_public_main_*` 実シグナル族である。
  **[T-1169] の観測はこれで 2 件から 4 件になり、文脈も「受入全走」だけでなく「変異走」へ広がった。**
  並列負荷下で確率的に出る、待ち合わせ欠如の族という診断が補強された。
  再走はしていない — フレークは確率的で、走り直しても別の変異に付きうるため
  50 分を投じる価値がないと親が裁定した。
- **変異登録を段 6 で 2 度是正した。** (i) 「絶対 git」「別名解決の無効化」「内側への注入」を
  1 変異に束ねていたため単一理由性 (`DW-M01`) を満たさず、3 つへ分割した。
  (ii) 過剰拒否の正例 (commit 一致まで要求する変異) の期待 node を 1 件と登録していたが、
  焦点再レビューが**完全集合 9 件**を特定した。先行レビューの「少なくとも 2 件」も不足だった。
- **fix 第 1 巡の codex 子が上流の安全分類器に遮断され、報告を失った** (F102 の再発として記録)。
  実装作業は完走しており差分は working tree に残っていたので回収した。
- **段 5 実装子は pytest を 1 件も実走できなかった** (計算資源不足と dispatch 失敗)。
  「実装済み・未実走」と正しく申告しており、緑の偽申告はない。実測はすべて親が行った。
- **[T-1116] は本 fragment で更新していない。** base 陳腐化の面を [T-1131] 1 件へ絞るための
  親の判断であり、内容上の理由ではない。本項の完了により [T-1116] は着手可能になった。

### 工数

codex 子 9 本、合計 6,673 秒 / 415 model call / CLI reported 2,095,097 token
(receipt.json の実測。段 6 の fix 1 は成果物不受理だが差分は回収した)。

| 段 | 子 | model / effort | wall s | calls | outcome |
|---|---|---|---|---|---|
| 2 | plan | gpt-5.6-sol / max | 889.0 | 55 | accepted |
| 3 | consult sol | gpt-5.6-sol / max | 1145.5 | 54 | accepted (NO-GO) |
| 3 | consult luna | gpt-5.6-luna / max | 915.6 | 36 | accepted (NO-GO) |
| 5 | author | gpt-5.6-sol / high | 1340.2 | 104 | accepted、pytest 実走 0 |
| 6 | review A | gpt-5.6-sol / high | 561.2 | 34 | accepted (NO-GO) |
| 6 | review B | gpt-5.6-sol / high | 600.4 | 44 | accepted (NO-GO) |
| 6 | fix 1 | gpt-5.6-sol / high | 526.5 | 34 | **not_accepted** (分類器遮断)、差分は回収 |
| 6 | focus | gpt-5.6-sol / high | 410.4 | 28 | accepted (GO) |
| 6 | fix 2 | gpt-5.6-sol / high | 284.5 | 26 | accepted、pytest 実走 0 |

## 次の一手差分

### 完了

- [T-1131] 判定の権威を tested main の blob へ束縛した。待ち手が
  「tested main blob == tested tip blob == 実行 bytes」を強制し、land も受領証を信用せず
  main/tip の checker blob を独立比較する。実行 bytes は tested main の blob content から取り、
  隔離した Python の stdin へ渡すため pathname 経由の差し替えが成立しない。
  残余 (待ち手自身の権威) は {{T:waiter-self-authority}} へ分離した。
  remaining: none
  base: 3e7e379a3ea6c392e8063aa1ac951954d77af74117850a7fb96b398ce3b07e81

### 新規

- {{T:waiter-self-authority}} **P1・新規・要裁定**:
  **待ち手 (`tools/dev_wave_wait.py`) 自身の権威が wave tip 側のままである。**
  [T-1131] は checker を tested main へ束縛したが、受領証を作るのは待ち手自身であり、
  land は待ち手を `tested_tip:tools/dev_wave_wait.py` としか照合しない。したがって wave が
  待ち手を書き換えれば、checker を一度も起動せずに偽の `non-attributable-only` 受領証を作れる。
  段 3 レンズ A と段 6 レビュー A が独立に実証した。
  **D403 (2026-08-15) はこの main 束縛を明示的に却下している** — 理由は「待ち手は wave 版を
  実行するため、同 file を編集する wave では main 版と恒久的に不一致になり、その wave の受入を
  永久に拒否する」。checker では [T-1131] が同じ代償を受容したのに対し、待ち手では却下されている。
  **この非対称を維持するかがユーザー裁定事項。** 択 (a) 現状維持 (checker のみ main 束縛)、
  択 (b) 待ち手も main 束縛し、待ち手を直す wave は受入を通せないと割り切る、
  択 (c) land 側に待ち手非依存の独立検証層を設計する (trust root 問題に接続)。
  **親の推奨は択 (a) 現状維持。** 理由は D403 の却下理由が今も生きており、待ち手は
  checker と違って wave 運用の中核で改修頻度が高いため、恒久拒否の代償が checker より重いこと。
  ただし「閉じた」と記録しないことを条件とする。
  成果物影響 = 未対処なら、受理集合を守る受領証の発行者を被判定側が差し替えられる状態が残り、
  台帳の非帰属 verdict と後続の certified 選択が汚染されうる。

- {{T:indeterminate-signal-kinds}} **P2・新規**:
  **「判定不能」が 2 種類できたのに、運用者が区別できる記述が無い。**
  `DW-O18` は「`tools/check_acceptance_reds.py` は rc=1 なら停止。rc=2 は判定不能で非帰属の
  根拠にしない」と checker の rc=2 だけを定義する。本 wave は checker を**起動する前**に
  権威を確立できない場合の判定不能を作り、これは待ち手 rc=70 (`stage=acceptance-red-check`、
  `source_rc` なし) で出る。両者は「受領証を発行せず非帰属の根拠にならない」点で同じだが、
  前者は「checker が走って判定できなかった」、後者は「checker を走らせる資格が確認できなかった」で
  意味が違う。運用者が後者を checker 判定と誤記すると台帳の verdict 根拠を誤る。
  成果物影響 = 誤記のまま台帳へ入ると、非帰属 verdict の根拠が実際の判定と食い違う。
