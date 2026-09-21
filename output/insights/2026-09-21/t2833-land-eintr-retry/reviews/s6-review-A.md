# [T-2833] 段 6 敵対レビュー — レンズ A (過剰・削除)、Claude 代替子 (Plan / opus)、read-only 静的検査

(親注: Codex 利用上限 (2026-09-26 19:35 まで) のため、Codex review 子の代わりに独立 context の Claude 子が同じ prompt `s6-review-A-prompt.md` で実施した。以下は子の最終報告の転記。)

必読 path はすべて読めました。`a1.patch` は wave 木の `git diff d99c556df 2a29a2381` と同一です (diff 出力が空)。pytest は走らせていません。テストの実測値は親の焦点走 log (focus-1.log) と handoff に書かれた変異 probe の結果を参照しました。

**A1 — should — brief の DW-G05 行が、是正済みの復旧手順と矛盾する**
- 根拠: brief.md:17「放置すると land (台帳 fold) が他 wave の登録 path の一過性 EINTR で rc=31 拒否され、受入の取り直しまで着地が遅れる。」/ 一次資料 README.md:105「同じ tested tip / landing tip / receipt で再投入すると `_register_land_turn` (2881 行〜) が新しい seq で新規登録し、検査を再実行する」「F672 の復旧文「受入を取り直して新しい request を作るしかない」は現行 source と合わず、従うと受入 1 走 (10〜25 分) を無駄にする」/ docs/failures.md:20356 (F672 の 09-20 追記)「k2-loop は拒否の 31 秒後に再投入して landed (受入不要、失うのは順番)」/ rulings-all-20260921c/materials-1786.md:22「見送ると rc=31 のたびに land を往復する」。
- 放置した場合の影響: 段 7・8 の failures fragment (恒久対応の追記) と insight がこの文を写すと、台帳上で F672 の是正済みの復旧が打ち消され、再試行を使い切って rc=31 になるたびに受入 1 走 (10〜25 分) を捨てる運用に戻る。
- 推奨: DW-G05 を「rc=31 で拒否されて順番票の entry を失い、同じ receipt で再投入するまで着地が遅れる (k2-loop の実測: 拒否の 31 秒後に再投入して landed)」に直し、fragment と insight ではこちらを使う。code と test の修正は不要。

**A2 — should — 研究前進行と「恒久対応の追記」が、実測で言える以上の効果を述べている**
- 根拠: brief.md:3「研究成果の着地 (台帳 fold) を一過性の syscall 中断で止めない最小差分」/ brief.md:16「worklog / failures (F672 再発ではなく恒久対応の追記)」/ 一次資料 README.md:142「383〜609 秒 = 6.4〜10.2 分」(候補区間の割当て)、README.md:190「修正 A の効果見積りは「同経路の 7 例が消える」前提で、EINTR の発生源が別なら再試行の効き方は変わりうる」/ tools/dev_wave_land.py:4099-4105 (sleep なし)、4439-4440 (`interval = min(self.seconds, 0.1)` / `signal.setitimer(signal.ITIMER_REAL, interval, interval)`)。
  静的推論: 仮説 (§3.2) が正しい場合、sleep なしの再試行 4 回は次の周期の SIGALRM と同じ条件で走る。metadata の待ちが周期を超え続ける間は 5 回とも中断されうる。実測は無い。
- 放置した場合の影響: F672 の「恒久対応: 未実施」(failures.md:20319) を「実施済み (EINTR 型は解消)」と書き換えると、再試行を使い切ったときに同じ文言の rc=31 が出ても F672 の再発として拾われない。
- 推奨: fragment と insight は「有界再試行 (1 path あたり呼び出し最大 5 回、sleep なし) を実装。効果は未実測 (6.4〜10.2 分は候補区間の割当てで、削減量ではない)。使い切ると同じ文言の rc=31 が残り、その扱いは F672 の再発検知と是正済みの復旧 (同じ receipt で再投入) のまま」と書く。新しい gate や検査は求めない。

**A3 — nit — brief (P2) と s4 §0 の受理集合の記述が「EINTR の後に FileNotFoundError」の拡大を書き落としている**
- 根拠: brief.md:15、s4-adjudication.md:6 は「再試行で解決できた登録 path」だけ広がると書く。s4-adjudication.md:23 は「1〜4 回返した後に成功または `FileNotFoundError` になれば」と正確。source では再試行中の FNF は `except FileNotFoundError:` / `path = path.absolute()` (4106-4107) で受理 (従来は 1 回目の EINTR で拒否)。T4 が pin。
- 影響: insight の受理集合の開示が 1 類を書き落とす。推奨: insight は s4 §2 の文言を使う。

**A4 — nit — T3 の permission と eio は M4 に対して同じ性質を 2 回 pin している (eagain は残す)**
- 根拠: test 10818-10826 の params。permission・eagain・eio を殺すのは M4 だけ。permission の拒否自体は既存 `[permission]` (10719-10758) が pin 済みで、新設が加えるのは呼び出し回数の assert だけ。eagain は F672 の再発検知 (failures.md:20321-20322「`Errno 4` / `Errno 11` などの一時エラー」) との関係で残すべき。
- 影響: なし (受入 1 node 分)。推奨: 任意。

**A5 — nit — 他の assert から導ける assert と結果の変わらない計算**
- T2 10814 行の `isinstance(... __cause__, InterruptedError)` は 10815 行の `is interruption` から導ける。T4 10866-10870 の `expected` の内包は基準値と同じ tuple になり、10886 行の `in` は 10885 行から導ける。影響なし。任意。

**A6 — nit — 一次資料 §5.1 の「SIGALRM handler 下で `InterruptedError` を 1 回注入する」正例に 1 対 1 の node は無い (T1[1] と T5 の組で満たす)**
- 合成注入の `InterruptedError` は handler を通らず、`_alarm` (4419-4424) は期限前に何もしないので armed かどうかで分岐は変わらない。M1 は両方を殺す。推奨: insight の対応表に「T1[1] と T5 の組」と書く。

## 総括

**判定: GO (レンズ A)。** production の差分は裁定と一次資料 §5.1 の範囲に収まり最小。変更は resolve 1 箇所と直前の定数だけで、別の resolve (4460 行)、`_git`、例外クラス、rc、watchdog 本体は不変。`_FoldGateInfrastructureFailure` は `RuntimeError` 系なので `except InterruptedError` にも `except (OSError, UnicodeError)` にも捕まらない。CPython は EINTR のとき InterruptedError を作る前に signal handler を走らせるので、期限超過なら handler の例外が先に上がり、再試行が期限監督を越えることはない。所見はどれも記録の文言か任意の削除で、code / test の fix は不要 (D95 の停止条件に当たらない)。

| ID | 重大度 | 1 行 |
|---|---|---|
| A1 | should | DW-G05 の「受入の取り直しまで遅れる」は是正済みの F672 復旧 (同じ receipt で再投入) と矛盾。fragment に写さない |
| A2 | should | 効果は未実測。枯渇時に同じ文言の rc=31 が残ることと F672 の再発検知を台帳に残す |
| A3 | nit | 受理集合の拡大に「EINTR → FNF で absolute を受理」が抜けている |
| A4 | nit | T3 の permission と eio は M4 に対して同じ性質を 2 回 pin (eagain は残す) |
| A5 | nit | T2 の isinstance、T4 の expected と `in` は他から導ける |
| A6 | nit | §5.1 の正例は T1[1] と T5 の組で満たされる |

攻撃したが不成立: 定数の削除 (M2/M3 の単一点)、loop の形 (for-else は呼び出し 2 箇所)、T1[1] の削除 (`break` を消す変異を殺すのは T1[1] の `calls == interruptions + 1` だけ)、T5 (M5 を殺す唯一の node)、(P1) 5 回 (読みの差は「EINTR 5 連続後 6 回目成功」の 1 類だけで範囲内)、(P2) 段 2・3 省略、変異 M0〜M7 の過不足。親の DW-M03 懸念はレンズ B の領分 (fake を「1 回目だけ失敗、以降は実物へ委譲」に変えても過剰にならない)。

照合した数値: EINTR 型 7 例 (一致)、20 wave で 2 回 (一致)、追加 wall 10.2 分 (一致、修正 A の候補は 6.4〜10.2 分)、受入 1 走 10〜25 分 (一致)、F672 復旧に従った回は受入を捨てた (一致)、DW-G05「受入の取り直しまで」(**不一致 = A1**)、production 呼び手 1 箇所 (一致、基点 4446 行・現在 4455 行)、行アンカー 4083〜4107 / 4446 / 10723 (一致)、4094〜4098 (実際は 4095〜4098、1 行ずれ・実害なし)、outer 145 秒 / 100 ms (一致)、規模 +10/−1・+170 (一致)、5 関数 / 9 node (一致)、kill 数 M1=6/M2=2/M3=1/M4=5/M5=1/M6=1/M7=1 (静的追跡と一致)、焦点走 1,824 passed / 4 skipped (一致、skip は flaky hold 1 と growth hold 3)、a1.patch と 2a29a2381 (同一)、brief (P2)「review 1 本」と s4「2 本」(表記不一致、実害なし)、裁定控えの mtime 14:46 (追記は「着地」節だけで項 1 不変)。
