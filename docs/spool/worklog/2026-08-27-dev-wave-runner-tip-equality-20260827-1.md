---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-runner-tip-equality-20260827
seq: 1
title: 受入の実行器 tip 等値要求は単独では外せない — 受入は計算ノードで tip 側の実行器を走らせていた (実装差分ゼロ・裁定パッケージ、branch worktree-dev-wave-runner-tip-equality-20260827、変異 matrix = 実装面差分ゼロにより免除 (D95 決定 2))
---

## 本文

- ユーザー依頼は `/dev-wave 受入 launcher の runner byte 一致要求を外す。実行元を tested main の
  blob に固定する保護は維持し、tip との等値要求だけを落とす。D838 の代償 (当該 file を直す wave が
  受入を通せない) を解消する` (背景 job)。base として local main `c0b8fb7f`。
- **依頼の 2 条件がこの計算機では同時に成立しないことを実測したので、実装せずユーザー再裁定へ返した。**
  等値を落とす (条件 1) と、実行元を tested main の blob に固定する保護 (条件 2) が消える。
  しかも消えるのは、本変更が通そうとしている当の wave — 実行器を編集する wave — についてだけである。
- **理由は受入の実行形にある。** 受入全走の pytest を実際に駆動するのは tested tip 側の作業ツリー
  file であって、tested main の blob ではない。両者が今日一致しているのは、まさに落とそうとしている
  等値要求のためである。連鎖は 7 段すべて親が実測した — この host は `PEGASUS_LOGIN` で
  queue `gen_S` が `ENA=ENA` / `STS=ACT` (待ち 33・実行 41)、その条件下で待ち手は launcher へ
  shard 数 3 を渡し、launcher は main の blob を `exec` するが `__file__` に作業ツリーの
  canonical path を入れ、実行器はそこから `_REPO` を作業ツリーとして導き、shard mode の LOGIN 実行は
  必ず dispatch し、dispatch は `repo_root` に作業ツリーを渡し、計算ノード側の子は
  `[python, <repo_root> の実行器, *argv]` を pathname で起動する。
  launcher の main blob 実行が覆うのは、dispatch を決める外側の 1 プロセスだけである。
- **未見だったのは残余そのものではなく、残余と等値要求の相互作用である。** dispatch の内側の子が
  pathname を読み直すことは runbook が残余として既に記録している。記録が無いのは
  「等値要求こそがその残余の実害を消していた唯一の仕掛けである」という点で、
  D838 の裁定文にも実装 wave の記録にも書かれていない。
- **再開する脅威は D838 の裁定文が名指ししたものそのもの。** 等値を外すと、実行器を編集した wave は
  自分が編集した実行器に自分を判定させる。受領証の実行 digest は main の値のままなので、
  受領証・land 結果・worklog のどこを見てもこの差は現れない。D387 の事故モデルでも成立する。
- **順序のデッドロックがある。** dispatch 側の穴を塞ぐ実装は実行器そのものを編集するため、
  いま外そうとしている等値要求によって塞がれている。「穴を塞いでから外す」は現行契約では
  実行できない。選択肢と親の推奨は {{T:dispatch-child-main-blob-binding}} と insight に書いた。
- **段 3 の 2 レンズが独立に別の最重を出し、両方 real だった。** レンズ B が dispatch 経路
  (本裁定の根拠)、レンズ A が既存テストの検出力不足 3 件。親は両方を実体で裏取りした。
- **親 brief の主張を 2 件、レンズが正しく訂正した。** (i)「既存の受領証・過去の判定結果は 1 件も
  変わらない」は証明されていない。権威ある受領証は通常 repo 外に置かれるため全数は確認できず、
  正しくは「以前受理された受領証を新たに拒否することはない」。(ii) launcher を先例として引く類推は
  完全ではない。launcher には tip bootstrap mode があり tip 側の実在も要求しないが、
  実行器には bootstrap mode が無く提案後も tip 実在は要求する。
- **段 2 のプランは正確で、破棄せず保存した。** 削除 2 か所・残す述語・テストの 3 分類・
  runbook 文案まで実装可能な水準である。ユーザー裁定が実装側へ倒れれば、変更面の骨格が同一なので
  次 context は段 2・3 成果物を流用して段 4 から再開できる。
- **棄却しなかったが scope 外とした所見が 2 件ある。** `tools/check_acceptance_reds.py` の受理経路が
  D690 以降到達不能なのに runbook が 2 経路を現役として説明していること、および到達不能な
  `non-attributable-only` の land 検証枝の存廃。どちらも本変更が原因ではない既存の陳腐化で、
  次の一手へ起票した。
- 子は 3 本 (plan 1、敵対相談 2)。すべて `gpt-5.6-sol` / `xhigh` / `accepted`。
  実装子は起動していない。実測はすべて親が行った。
- **実 repo を読むテストは記録 commit の後に実走した。** 段 4 の規定は記録前なので順序を誤った。
  結果は緑で判断は変わらない — `test_s8b_repo_scan_invariant.py` と `test_check_docs.py` を
  計算ノードへ dispatch して 567 passed / 4 skipped / 11.81 秒。
- **受入全走 attempt 1 は非帰属の赤 1 件で戻り、land していない。** claimed main `b9d21206`、
  17700 collected / 17638 passed / 1 failed / 61 skipped、rc=70 (source_rc=1)。赤は
  `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
  だけで、所要時間台帳の被覆率が閾値 90% を割ったものである。**本 wave は docs と insight しか
  変えておらずテスト node を 1 つも足していないので、この判定の分母を動かさない。**
  並行 wave ([T-1629] 所有) が素の main worktree で 15912/17700 = 89.898% を独立に実測しており、
  本走の collected 17700 と分母が完全に一致する。決定的な赤なので再走はしていない
  (再走は lease 窓を捨てるだけである)。**対応する F も `orchestrator/tests/flaky_test_holds.py` の
  登録も存在しないことを親が確認したので、DW-O18 に従い保留登録をせず裁定へ送って停止した。**
  被覆率の是正そのものは [T-1629] の wave が所有し、ユーザー裁定へ上げている
  (台帳の全面再生成は 12 node の所要値 exact pin を壊し、閾値の引き下げは規律 2 に触れる、
  というのが同 wave の調査結果)。本 wave は重複起票しない。
- 受入 lease は取得しないまま終わったので `release` していない (`status` は `free` を実測)。
- **ユーザーは「推奨 B で進めて。ただ codex に相談し賛成をもらったら」と裁定し、賛成は得られなかった。**
  codex 相談 2 本の総括は `反対: B`。理由は「B を着地させる一度きりの land 認可が現行機構に
  存在せず、その機構を B の wave 自身へ足すと着地に同じ例外が要る」。D388 が受領証欠落時の
  bypass を明示的に禁じている点を根拠に挙げた。**したがって B は実行していない。**
- **codex の対案は三段ブリッジ P → Q → R で、親は codex の出力を見る前に同じ形へ独立到達していた。**
  親の根拠は環境変数の伝播経路 (launcher が実行器を起動する `subprocess.run` は `env=` を渡さず、
  `_dispatch_environment` が `os.environ` を複製する) で、実行器を 1 行も編集せずに
  束縛の材料を計算ノードまで運べる。二経路の独立一致。
- **codex が親の実測を 2 点補正した。** (i) dispatch しない bounded local 経路も作業ツリーの
  実行器を pathname 再実行するので、「必ず dispatch する」は言い過ぎだった。
  (ii) dispatcher 自身も束縛対象で、runner だけ束縛しても dispatcher は tip 側のままである。
- **親が新たに見つけた未解決点** — P の束縛を執行するコードが tip 側にあるため、
  実行器だけを編集した wave は捕まるが実行器と dispatcher の両方を編集した wave は捕まらない。
  よって等値を外す時期は Q-early / Q-late の二択になり、前者は規律 2 の残余を一定期間受け入れる
  判断、後者は D388 の land 権威に例外を作る判断で、どちらも親が単独で決めない。裁定へ返した。
- 逐語・実測表・選択肢は `output/insights/2026-08-27_runner-tip-equality-dispatch/`。

## 次の一手差分

### 更新

- [T-1932] **P1・ユーザー裁定待ち**: 受入の実行器束縛をどうするか。本 wave の実測で、
  等値要求を単独で外すと「実行元を tested main の blob に固定する保護」が
  実行器を編集する wave について消えることが分かった。3 択 — (A) 依頼どおり等値だけ外し
  dispatch 側の穴を残余として受容する、(B) 等値の撤去と dispatch 束縛を 1 wave に載せ、
  その wave だけ実行器編集 wave の land を明示的に一度だけ認める (親の推奨)、
  (C) 等値を維持し既定 shard 数の変更は別経路で解く。
  A と B の差は、実行器を触る wave が 1 本でも通る窓を開けるかどうかである。
  根拠と連鎖の実測は `output/insights/2026-08-27_runner-tip-equality-dispatch/`。
  base: 81b6b70730da35199f644ef44872112d1f85d96ca648936082650187217e565f

### 新規

- {{T:dispatch-child-main-blob-binding}} **P1・新規**: 計算ノード側の子の実行 bytes も
  tested main の blob へ束縛する。現状は `dispatch_compute` が `[python, <repo_root> の実行器, *argv]`
  を pathname で起動するため、受入の pytest を実際に駆動するのは tip 側の作業ツリー file である。
  claim 後の内部 merge が実行器を変えた main を取り込んだ場合も、受領証は古い claim main の
  実行器 digest を載せたままになる。**[T-1932] の裁定が A か B のときだけ着手できる**。
  B なら同じ変更単位、A なら直後の wave。
- {{T:acceptance-runner-binding-detection-power}} **P2・新規**: 実行器束縛の検出力不足 3 件を閉じる。
  (i) blob 読取の revision 指定を殺すテストが無い — unit test は reader を差し替えるので通らず、
  実 Git を通す E2E 2 本は main と tip の実行器が同一なので `HEAD` へ変えても通る。
  (ii) land の tip 側述語 (実在・blob type) が片側だけの fixture で殺されていない。
  (iii) v5 束縛の baseline helper が実行 digest を tested tip の blob と照合しており、
  main==tip の木でしか意味を持たない。(ii) は等値の可否と独立に今日の関門の穴である。
- {{T:d987-forward-main-runner-reacceptance}} **P1・新規**: D987 (取り込んだ main が実行器を
  変えた場合だけ受領証の再利用を拒否する) が未実装である。forward-main 経路は landing tip の
  topology を検査するが実行器を引かない。段 2 のプランはこの経路を positive test に固定する案を
  含んでいたので、そのまま実装していれば D987 が拒否を求める入力を成功として凍結していた。
- {{T:runbook-acceptance-paths-stale}} **P2・新規**: `docs/pegasus-runbook.md` の受入節が
  受理経路を 2 つとも現役として説明しているが、D690 以降 `tools/check_acceptance_reds.py` を
  使う経路は到達不能である。待ち手は completion の判定結果を常に空にし、child rc が 1 でも
  受領証を publish しない。本変更が原因ではない既存の陳腐化。
- {{T:unreachable-nonattributable-land-verifier}} **P2・新規・ユーザー裁定待ち**: land 側に残る
  到達不能な `non-attributable-only` 検証枝を残すか消すか。正規の待ち手では生成できない受領証だが、
  land は今も検証する。消せば受理集合が縮み、残せば到達不能な legacy verifier が残る。
