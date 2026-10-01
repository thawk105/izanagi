# 段 6 裁定 — acceptance-pyc-warm (2026-09-30 JST、fix 前に固定)

入力: codex/review-a-out.md (過剰・削除、NO-GO)、codex/review-b-out.md (正しさ・process 寿命、NO-GO)。対象 commit 19634caab。

## 所見の裁定

| 所見 | 判定 | 採否 |
|---|---|---|
| A1 log の復号 (旧 `text=True` = locale 厳密 + 改行正規化、新 UTF-8 replace) で bytes と rc が変わりうる | real (must) | 採用。前倒し経路の復号を subprocess の `text=True` と同一にする (`locale.getpreferredencoding(False)` 厳密復号 + `\r\n`/`\r` → `\n`)。復号例外は下の R3 で従来経路へ |
| A2 main 全体の try/finally 再インデント (+229 行、目安 +150 超過) | real (should) だが不採用 | 超過理由 (約 128 行は再インデント) を受理。受理集合・rc に影響なし (DW-G05)。fix で構造を小さくできるなら可、必須にしない |
| A3 成功後の子孫停止が未検証 | refuted | 従来経路 (`subprocess.run`) も成功後の子孫を扱わない。現行と同じで新しい性質ではない |
| A4 採算・集合不変が未実測 | real | 事前登録の同時刻対照と受入全走で判定 (予定どおり) |
| B1 Popen 直後〜所有権設定の signal 窓で子が残る | real (must) | R1 で解消 (自前 handler を廃止し従来と同じ process group) |
| B2 cleanup 中の signal で cleanup が中断 | real (must) | R1 で解消 (SIGTERM は従来どおり既定動作、SIGINT は KeyboardInterrupt で finally が走る。子は同じ group なので group 宛ての signal を従来どおり受ける) |
| B3 `/tmp` の一時出力の失敗が新しい rc 16 経路 (F1083 型) | real (must) | R3 で解消 (前倒しが成功しなければ従来 collection で取り直す) + R4 (`/tmp` 直書きをやめ tempfile 既定の置き場) |
| B4 reap 済み pid を pgid として killpg | real (should) | R2 で解消 (killpg をやめ Popen の terminate/kill/wait。Popen は reap 済みには signal を送らない) |
| B5 SIGTERM の終了形式が SystemExit(143) に変わる | real (should) | R1 で解消 (handler 廃止で従来と同じ既定動作) |
| B6 統合 test の代役が実 worker 寿命を通らない | real (should) | 採用。実 `fork` の run_parallel を通す test を 1 本足す (report merge だけ代役可) |

段 4 の plan v2 項 5 (「前倒し起動から run_parallel の handler 設置までの SIGINT/SIGTERM も finally が走る形」) は本裁定で改める。理由: 従来経路は handler を持たず、collection 子は親と同じ process group で走っていた。自前 handler と新 session が B1・B2・B4・B5 を生んだので、従来と同じ signal 意味論に戻すのが「現行と同じ」の最短である。

## plan v3 (fix の規定)

- R1: `main` の一時 signal handler (abort_early) を削除する。前倒し起動の条件から handler 設置の成否を外し、s4 項 2 の条件だけにする。
- R2: collection 子は `start_new_session` を使わず、従来の `subprocess.run` と同じく親の process group で起動する。未回収の後始末は `process.poll() is None` なら `terminate()` → 短い猶予 → `kill()` → `wait()`、一時 file を close。`os.killpg` を使わない。
- R3: 回収 (`collect`) は、前倒し子の rc が 0 で、出力の復号と parse が成功した場合だけ前倒しの結果を使い、`login-collection.log` を書く。それ以外 (非 0 rc・timeout・復号/parse 例外・一時 file の読取失敗) は前倒し子を後始末したうえで従来の `_collect_login_universe(session, exclusions, deadline_at)` を呼び、その結果 (log を含む) を返す。log は create-only なので、前倒し側は失敗時に log を書かない。これで結果は常に「従来経路が返したであろう値」と同じになる (前倒しは成功時の近道に限る)。
- R4: 一時 file は `tempfile.TemporaryFile()` の既定の置き場 (TMPDIR 準拠) を使い、`dir="/tmp"` を外す。
- R5: 復号は A1 のとおり `text=True` と同一。
- R6: test — (a) 既存の新 test を R1〜R5 に合わせる (M4 の test は「preflight 赤で前倒し子が terminate/wait されて消え、一時 file が閉じる」。孫 process の検査は外す = 従来と同じ範囲)、(b) 前倒し子が非 0 rc のとき従来経路で取り直して universe と log が従来と同じになる test、(c) CRLF と不正 byte を含む出力で、前倒し経路と従来経路の rc と log bytes が一致する test、(d) 実 `fork` の run_parallel を通す test 1 本 (B6)。既存 test (19634caab より前からあるもの) の期待値は変えない。
- 規模: fix 後の run_tests.py の差分は d79fd3524 比で +200 行以内を目安 (再インデント込み)。

## 変異の事前登録 (追加・改訂。M1〜M3・M5・M6 は s4 のまま)

| ID | 変異 | kill 期待 |
|---|---|---|
| M4 (改訂) | 未回収の後始末で terminate/kill/wait をしない | preflight 赤で前倒し子が消えることを検査する test |
| M7 | 前倒し子が非 0 rc のとき従来経路へ戻らず rc 16 を返す | R6(b) の test |
| M8 | 前倒し経路の復号を UTF-8 errors=replace に戻す | R6(c) の test |

nodeid は fix 後に確定し、単一理由性 (F820) を確認してから走らせる。

## 追記: 焦点再レビュー 1 巡 (codex/focus1-out.md、NO-GO) の裁定 (2026-09-30、変異の前に固定)

対象 f4920ddb3。DW-O16 の上限 (3 巡) の前に、fix を重ねず親の裁定と変異で閉じる。

| 所見 | 判定 | 採否 |
|---|---|---|
| 対応表 A1・B4・B5 closed、A2・A3 n/a | 受理 | — |
| N1 失敗時の取り直しで、従来の 1 回走と結果が変わりうる (fail_first) | real (主張の言い過ぎ)、コード不変 | 本裁定 plan v3 R3 の「結果は常に従来経路が返したであろう値と同じ」を次に訂正する: 「採る universe と log は常に、同じ木を同じ command・env で最後まで collection した 1 回の結果である。前倒しが失敗したときだけ従来形で 1 回取り直す」。差が出るのは collection が走るたびに成否の変わる基盤障害 (一時 file の容量など) のときだけで、従来はその走が rc 16 (infra) になり門番が受入を再投入していた。gate 3 (独立 login collection と shard universe の一致) は弱まらない |
| N2 log 公開後の例外で create-only が取り直しと衝突 | refuted (must として) | 衝突時は rc 16 で、従来経路でも同じ例外は rc 16。成功後の一時 file close の例外は nit (backlog) |
| N3 起動が try の直前にあり、親だけへの SIGINT で子が残る窓・cleanup 中の二重割込み | real (should)、backlog | 子は親と同じ process group で、端末の割込みは group 全体に届く。親だけへの割込みで残った子は collection を終えて自ら終了し、一時 file は unlink 済み。受理集合・rc に影響しない (DW-G05) |
| N4 timeout 後の取り直しは残り時間 0 で rc 16 | refuted | 従来経路も deadline 切れは rc 16。救済範囲に timeout を含めないと明記する |
| N5 復号 test の locale 依存・前倒し使用の明示検査なし・/proc 前提 | real (should)、backlog | Pegasus の login / 計算ノードは UTF-8 locale で、計算ノードの焦点走は緑。前倒し未実行は M1 の test が殺す |

変異は f4920ddb3 で s4 の M1〜M3・M5・M6 と本裁定の M4 (改訂)・M7・M8 を走らせる。
