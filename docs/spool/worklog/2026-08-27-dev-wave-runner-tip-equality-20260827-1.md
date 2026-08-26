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
- **ユーザーの再指示「codex に相談してどちらも判断してください」を受け、相談 2 本 (判断役・反対役) を
  投入して親が決定した。決定は「P に着手する」「Q-early」。**
  判断役は `P: 着手すべき` / `Q: early`、反対役は「三段ブリッジに致命的欠陥あり」で戻ったが、
  内容は「実装前に潰すべき 4 件」であって放棄勧告ではなく、判断役の条件と一致した。
- **決定の土台になった母集団を親が独立に実測した。** dispatcher 導入日 2026-07-30 以降、
  main 上で実行器を触った commit は 24 件、dispatcher を触ったのは 22 件、
  **両方を触ったのは 6 件 (実行器を触った commit の 25.0%)** である
  (`16df3e4e` `532635b4` `9e81501f` `a34266d2` `d26b345c` `fee55899`、codex の列挙と SHA 完全一致)。
  したがって「同時編集は稀だから tip 側執行で足りる」は成立せず、
  **申告を main 束縛コードが要求する形 (仮説 H) は任意ではなく必須**である。
- **Q-late は選好ではなく実行不能だから落ちた。** land は受領証を必須引数とし、その検証は
  `already-landed` と merge の双方より前に走る。D388 は flag・環境変数・互換 bypass を
  逐語で禁じている。手動 ff-only は受領証だけでなく provenance・fold・postcondition も
  まとめて迂回する。
- **反対役が出した「launcher に dispatcher の main/tip 等値検査を足す」案は親が不採用にした。**
  D838 の代償を別 file へ移すだけであり、上記実測どおり dispatcher も同程度に触られている。
  仮説 H が成立すれば等値検査なしで同じ保護が得られる。
- 逐語・実測表・選択肢は `output/insights/2026-08-27_runner-tip-equality-dispatch/`。

## 次の一手差分

### 更新

- [T-1932] **P1・裁定済み・段階 R で解く**: 受入の既定 shard 数 2→3 は、実行器を編集する
  wave が受入を通せるようになった後、段階 R ({{T:runner-and-dispatcher-authority-to-main}}) で
  入れる。本 wave の実測で「等値要求を単独で外すと実行元の main 束縛が消える」ことが分かり、
  ユーザーは「推奨 B で進めて。ただし codex の賛成が条件」と裁定した。codex は B に反対し
  (一度きりの land 認可が現行機構に存在しない)、代わりに三段ブリッジ P → Q → R が採られた。
  ユーザーの再指示「codex に相談してどちらも判断してください」により、親が
  **P 着手・Q-early** を決定した。根拠と連鎖の実測は
  `output/insights/2026-08-27_runner-tip-equality-dispatch/`。
  base: 81b6b70730da35199f644ef44872112d1f85d96ca648936082650187217e565f

### 新規

- {{T:dispatch-child-main-blob-binding}} **P1・新規・次の wave (段階 P)**: 計算ノード側の子の
  実行 bytes を tested main の blob へ束縛する。**実行器を 1 byte も変えずに実装する**ので
  通常の受入・land で着地でき、一度きりの認可を要しない。確定した設計は 6 点。
  (i) **執行は launcher、機構は dispatcher**。main 束縛の launcher が全 shard の申告を無条件に
  要求し、dispatcher は launcher 所有の manifest がある走行にだけ束縛を適用する。これで P 自身の
  受入 (旧 launcher が動くので申告を要求しない) が落ちず、恒久的な暗黙 fallback も作らない。
  (ii) **同一 buffer 束縛**。hash する bytes と子の stdin へ渡す bytes を不可分にする。
  期待 digest の転記は恒真になる。(iii) launcher が session nonce と exact K を所有し、
  `0..K-1` の完全一致を要求する。(iv) dispatch しない authoritative 受入は R まで fail-closed
  (bounded local 経路も作業ツリーの実行器を pathname 再実行するため)。(v) 申告は既存の repo 外
  shard artifact 経路に載せる (作業ツリーの無変更要求に触れない)。(vi) 欠落・不一致・転記変異・
  非 dispatch 走の negative control を launcher のテストへ置く。
  **dispatcher の main/tip 等値検査は採らない** — D838 の代償を別 file へ移すだけで、
  実測では dispatcher も同程度 (22 commit) 触られている。
- {{T:runner-equality-removal-after-binding}} **P1・新規・段階 Q**: {{T:dispatch-child-main-blob-binding}}
  が main へ入った後、launcher と land の実行器 main/tip 等値要求だけを外す。Q も実行器を
  触らないので通常経路で着地できる。**Q 自身の受入が新機構の production activation control になる**
  — Q の受入は P の main launcher が動くので、申告検査が実際に発火した証拠が受領証として残る。
  段 2 のプラン (`verbatim/s2-plan.md`) がそのまま使える。
- {{T:runner-and-dispatcher-authority-to-main}} **P2・新規・段階 R**: 実行器を初めて編集し、
  (i) bounded local 再入も main blob 実行へ移す、(ii) 外側の dispatcher import を main 側へ束縛する、
  (iii) [T-1932] の既定 shard 数 2→3 を入れる。R の受入は P/Q の main 束縛 launcher が判定する。
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
