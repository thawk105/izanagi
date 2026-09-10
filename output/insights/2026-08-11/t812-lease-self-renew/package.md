# 裁定パッケージ — 受入 lease の invocation 識別と TTL 越え受入 ([T-812] 返却分)

本 wave はユーザー裁定済みの 3 点セット (自己保持で TTL を更新して `held-self` を返す / 待ち手の
受理集合を `{acquired, held-self}` へ / 自己保持で進めないときは理由付き fail-closed) を実装した。
以下は**実装せずに返す**設計択一である。いずれも受入結果を受理してよいかの条件に触れるため、
wave 側で凍結しなかった。

正本の所見は `verbatim/` (段 3 敵対 2 レンズ + 段 6 レビュー 2 本)、裁定は `verbatim/s4-ruling.md`。

## 事実 (実読・実測で確認済み)

- `holder` は **wave slug の SHA-256 先頭 12 桁**である (`tools/wave_land_window.py` の
  `_holder_for`)。invocation を識別しない。
- **`tools/run_tests.py` に flock は無い。** 並行受入を後段で直列化する層は存在しない
  (親が実測)。
- 待ち手の identity preflight は「branch 名が wave slug で終わること」しか要求しない。
  **別 worktree でも同一 slug を持てる。**
- `release` の権限証明も wave slug の digest だけである。
- 受入 1 走は 1055〜1273 秒、lease TTL は 2400 秒。**2 走で TTL を超える。**
- 待ち手は受入 command に timeout を掛けない (意図的)。TTL 超過時は `ttl_remaining=0` を
  印字して **rc=0 を返す**。

## Q1 — invocation capability を導入するか (最重要)

`held-self` は「同一 slug の別 invocation」も通す。逐次の再実行 (裁定が想定する正常系) と
重複起動の並行実行を、現在の情報では区別できない。

- **(a) 導入する。** claim 時に生成した capability を lease payload へ束縛し、`held-self` と
  `release` は capability 一致を要求する。逐次再実行のために capability は wave の artifact へ
  保存し、待ち手が読む。重複起動は capability 不一致で fail-closed になる。
  代償 = lease payload schema の変更、待ち手の argv 追加、capability 紛失時の復旧手順。
- **(b) 導入せず、運用前提として文書化する (現状)。** 「1 slug につき active な待ち手は 1 本」を
  runbook に明記済み。機械保証は無い。
- **(c) 弱い形にする。** capability ではなく pid + starttime + host を lease へ記録し、
  `held-self` のとき **生存している別 invocation が同一 slug で走っていないこと**を待ち手が
  検査する。逐次再実行では前 invocation が既に死んでいるので通る。
  代償 = ノードを跨ぐと生死判定ができない (共有 lease dir は複数ノードから触られる)。

**親の推奨 = (c) を第一候補、次点 (a)。** (b) は実害が既に 4 例あり、重複 job も実測されている
(過去に同一タスクの背景 job 2 本が同じ worktree を共有した事例がある)。(c) は payload を増やさず
逐次再実行を壊さない一方、ノード跨ぎでは検査が縮退するため、縮退時に (b) と同じ運用前提へ落ちる。
(a) は完全だが、capability の受け渡しが増える分だけ「待ち手を書き起こさない」規律の面が広がる。

## Q2 — 受入が TTL を跨いだとき rc=0 を返してよいか

TTL 超過後は他 wave が stale として回収でき、**排他は失われている**のに、現在は成功を返す。

- **(a) 現状維持** (警告を印字して rc=0)。fencing が無い以上、事後に取り消せないため。
- **(b) 受入中に heartbeat renewal を回す。** 別 process か待ち手内の thread が定期的に
  `claim` して自己更新する。TTL 超過そのものを起こさない。
- **(c) 完走時に経過を検査し、TTL を超えていたら rc を非 0 にして結果を受理しない。**

**親の推奨 = (b)。** 本 wave の renewal 機構をそのまま使えば実装は小さく、(c) のように
「20 分走らせた結果を捨てる」損失も出ない。(a) は「排他を保持して完走した」という受理集合に
実際には重なった走行が混ざり続ける。

## Q3 — stale な自己保持をどう扱うか

現状は unlink → 再取得 (`acquired`) に倒す。新 inode の取得は**旧 invocation の受入が止まった
証拠ではない**。

- **(a) 現状維持。** 本機構が無かった場合と同じ競合であり、悪化はしない。
- **(b) `lost-exclusivity` として fail-closed で止める。** 排他が失われた事実を明示する。

**親の推奨 = (a) 維持だが Q1(c) 採用時は (b) へ移す。** 単独で (b) にすると、旧 invocation が
既に死んでいる正常系まで止めてしまう。生死を見られるなら (b) が正しい。

## Q4 — 自己更新の上限 (owner 優先と FIFO の折り合い)

自己更新は待ち行列を追い越す。lease を持つ wave が更新を繰り返す限り、後続は待ち続ける。

- **(a) 上限なし (現状)。** owner 優先を明示的な意味論として認め、FIFO 保証は
  「後着が先着を追い越さない」だけだと明記する (実装済み・runbook 記載済み)。
- **(b) 連続 renew 回数か累積保持時間に上限を設ける。** 超過したら `held-self` を返さず、
  release して並び直させる。

**親の推奨 = (a) 維持。** 保持している wave の仕事 (受入 → land) は有界であり、無限に更新する
経路は「同じ wave が受入を延々やり直す」異常系だけである。異常系は上限より可視化で捕まえる方が
安い。ただし飽和が観測されたら (b) を再検討する。

## Q5 — 版混在時の未確定 cleanup

旧待ち手が新しい `held-self` を未知状態として拒否したとき、所有権が未確定 (`UNKNOWN`) のままなので
cleanup が **同一 slug の lease を release** しうる。「未知状態は安全側」という想定は、この
cleanup 経路と両立していない。

- **(a) 現状維持 + 配備を atomic にする** (待ち手と lease primitive は同じ commit で land される
  ため、同一 worktree 内では混在しない。混在するのは land 前の別 worktree だけ)。
- **(b) `UNKNOWN` の release 権限を外す。** 代償 = 本当に取得済みだった場合の lease leak が
  TTL まで残る。
- **(c) claim helper の出力に schema version を持たせ、未知 version は release せず fail-closed。**

**親の推奨 = (a)。** 実際の混在窓は「land 前の他 worktree が古い待ち手を使う」場合に限られ、
その待ち手は古い lease primitive を呼ぶので新しい `held-self` を見ない。(b) は leak へ問題を
移すだけで、(c) は本 wave の scope を越える。

## Q6 — docs-only fold の隣接 race (裁定 425 付帯 2 から本 wave へ委譲)

docs-only の fold は lease を取らずに main を進めるため、受入全走 (約 9〜21 分) の最中に main が
進み、land が rc=23 / rc=10 stale-main で拒否される。t756 で 2 度、本 wave の稼働中にも
[T-813] が同型を踏んだ。

- **(a) docs-only land にも lease 取得を課す。** 直列化は完全になるが、rulings セッションの
  高頻度 land が受入窓を奪い合う。
- **(b) 待ち手内の再試行 loop を正本化する** (lease を離さず merge → 受入 → land を反復)。
  t756 と T-813 が手作業でやった回避を機械化する。
- **(c) 祖先条件を限定緩和する** (差分が docs-fold のみなら再検証して land を継続)。
- **(d) 現状維持** (手作業の再試行)。

**親の推奨 = (b)。** 本 wave の `held-self` は (b) の前提条件だった「保持したまま 2 走目を回す」を
初めて機械的に可能にした。(a) は窓の取り合いを増やし、(c) は受理集合の意味論に触れる
(「受け入れる main に対して検査する」が緩む) ため最後の手段である。

## Q7 — dev-wave reference の L1.5 予算に余白が無い (段 8 の自己改善が入らない)

段 8 で「読む量の多い codex 子は観測トークン上限を明示的に上げる」という 1 行 (約 250 bytes) を
`DW-O01` へ統合しようとしたところ、`docs/dev-wave/**` の **L1.5 unique footprint が予算
9566 bytes に対し既に 9566 bytes** で、**余白 0** だった (追記後 9816 bytes で rc=1)。
自己改善契約は「予算のために安全義務を削除・弱化してはならない」「収まらなければ変更を止めて
ユーザー裁定へ返す」と定めているため、追記を取り下げて failures にだけ記録した。

- **(a) 現状維持。** dev-wave の作法追加は今後も reference へ入らない。実測した罠は failures と
  memory にだけ残り、**手順の正本には反映されない**。
- **(b) 陳腐化した L1.5 記述を削って空ける。** 削除候補の選定と「発火実績なし × 機械代替済み」の
  立証が要る (契約が要求する条件)。
- **(c) 予算値を上げる。** 契約上「通常の自己改善に含めず、理由付きの独立審査対象」。

**親の推奨 = (b) を独立 wave で。** (a) は「実測した罠が正本へ入らない」状態を恒久化し、
自己改善の経路そのものを詰まらせる。(c) は先例 (2026-08-02 のユーザー裁定) があるが、
今回は「削れる陳腐化記述があるか」を先に測っていないため、順序として (b) が先である。
