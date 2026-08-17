---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1275-lease-ticket-retry
seq: 2
---

## {{D:acceptance-retry-positive-evidence}}. 受入の同一 process 内再試行は、肯定的証拠の合議でだけ発火させる

**決定:** 受入待ち手は、受入 command が **pytest の判定を 1 つも産まずに戻った**走行に限り、
lease を保持したまま同一 process 内で 1 度だけ再投入する。発火条件は次の全成立とし、
1 つでも取れなければ terminal (fail-closed) とする。

1. 正規化後の child rc が 0 でも 1 でもない。
2. 捕獲 log に dispatch 由来の構造化 attestation が**ちょうど 1 件**あり、その `child_started` が
   偽である。relay prefix 付き・欠落・重複・payload 不正・duplicate key・未終端 EOF・
   内部矛盾はすべて拒否する。
3. 捕獲 log から pytest の判定痕跡が 1 件も導けない。**log に切り詰め・省略の framing があれば
   不在を確定不能として terminal に倒す。**
4. 走行後の clean / index flag / fingerprint 検査を通過している。
5. lease 所有が `ACQUIRED` で、cleanup 失敗が無い。
6. attempt 上限と、invocation 入口で一度だけ確定した共有 deadline の双方に余裕がある。
   deadline は attempt 2 の claim 前と**受入 command 起動直前**に再確認する。

producer 側では、`child_started` を偽にしてよいのは
**「対象 job がまだ待ち行列にいる」ことを判定時点の権威ある問い合わせで確かめられた
queue 待ち timeout」だけ**とする。保留・終了・状態不明・受領証永続化失敗はすべて真へ倒す。
「実行中を観測しなかった」ことだけを根拠に偽にしてはならない。

再試行の間 lease は release せず、attempt 境界で自 holder の claim により mtime を更新し、
`ownership` を `ACQUIRED` のまま保つ (release 権限を失わせない)。失敗 attempt の log は
sibling path へ上書き禁止で退避し、成功 attempt の受領証と log は呼び手の指定 path に置く。
受領証 schema の版と root field 集合、rc の意味論、受入の受理 2 経路、D253 の待ち札意味論は
いずれも変えない。attempt 番号・分類・rc・退避先・log hash・claim した main は
待ち手の stderr へ機械可読な 1 行として残す (成功終端でも消さない)。

**理由:**

- **raw rc は判定の有無を表さない。** dispatcher は受領証の永続化に失敗すると、child rc を
  得ているのに infra rc を返す。pytest が実走して赤を出しても待ち手には同じ rc に見えるため、
  rc だけを発火条件にすると**実走した赤を握りつぶして再走できる**。これは規律 2 が名指しする
  reward hacking そのものであり、実害の観測を待つ種類の欠陥ではない。
- **「観測しなかった」は不在の証拠にならない。** scheduler の実行中状態は観測を取り逃がしうる。
  短命な job は待ち行列から終了へ抜けるため、消極的判定では実走を「未開始」と誤認する。
  肯定的証拠を要求し、取れないときは再試行を許さない側へ倒すのが唯一の fail-closed である。
- **切り詰められた log は不在を支持しない。** 判定痕跡が落ちた log と、判定が無かった log は
  区別できない。区別できないことを確定として扱えば、1 と 2 の裏取りが恒真になる。
- **順番を手放すと目的が発効しない。** lease 取得の成功時に自分の待ち札は削除されるため、
  失敗後に release して再 claim すると、同一 process であっても**新しい到着時刻の札**になり
  後着の後ろへ回る。保持したまま再試行することだけが、待ち直しの代償を実際に取り除く。

**却下した選択肢:**

- **raw rc だけを発火条件にする** — 上記のとおり実走赤を再試行でき、規律 2 に反する。
- **dispatcher に pre-child failure 専用の rc を足す** — rc の意味論は runbook と land が
  依存する受理集合であり、そこへ新しい値を入れる影響が本来の目的に見合わない。
  構造化 attestation を足せば rc を 1 bit も変えずに同じ判別ができる。
- **失敗 attempt で lease を release して待ち行列へ戻る** — 先着順位が戻らないため、
  「フレーク 1 件の代償を 1 走ぶんに戻す」という目的が発効しない。
- **dispatcher が受入 command から書けない場所へ nonce 付き sidecar を置く** — 偽造耐性は
  上がるが、attestation と同格の新しい channel を作る設計であり、独立の敵対検証を要する。
  信頼済み中核の内側であること、attempt 上限のもとで偽造の利得が再試行 1 回に限られること、
  赤を緑に変えられないことから、限界として明記して受容する。
- **attempt 上限を 2 より増やす** — 再試行のたびに lease 占有が延び、偽造の利得も比例して
  増える。上限を上げるなら偽造耐性の channel と同時に裁定する。
- **走行中の受入 command を deadline で kill する** — 停止性は上がるが、正当に長時間走る
  受入を途中で捨てる。有界性の主張は「command が戻った後の再試行ループ」に限る。
