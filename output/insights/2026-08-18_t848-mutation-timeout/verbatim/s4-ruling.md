# 段 4 裁定 (親) — [T-848] / 2026-08-17 23:23 JST

base: 2a3b5055 / branch: worktree-dev-wave-t848-mutation-timeout

## 1. 所見の real / refuted と採否

| 出典 | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-0 | dispatch mode の閉鎖確認 | real | 前提として採用 |
| A-1 / B-1 | 段 2 プランは生存欠陥 (local 申告 × 実 dispatch) を直さない | real (blocker) | **採用。本 wave の中心 scope** |
| A-2 | timeout 時に receipt は永続化される保証が無い | real (blocker) | **採用。receipt を一次証拠にしない設計へ変更** |
| A-3 | fail-closed が逆向きの分岐 2 件 | real | 採用 (下記 2 の設計で自動的に消える) |
| A-4 | 新 status 自体から新しい偽の緑は開かない | real | 参考 |
| A-5 | 親の「全史 0 件」は測定範囲超え | real (must-fix) | **採用。親が v2 probe で測り直し済み** |
| A-6 | resume→history と fan-out history 拒否が矛盾 | real | 採用 (status 新設を見送るので発生しない) |
| A-7 | 択一は即停止 (a) | real | 採用 |
| B-2 | status 束縛点は brief の列挙より多い | real | 採用 (status 新設を見送るので発生しない) |
| B-3 | v5 は全 v4 resume/remerge を拒否する | real (must-fix) | **採用。裁定の決め手** |
| B-4 | v5 fixture の監査範囲不足 | real | 採用 (同上) |
| B-5 | M6 は後段 gate に mask される | real | 採用 (変異を組み直す) |
| B-6 | expected node は parameterize 後の完全集合が要る | real | 採用 (親が実測で導出) |
| B-7 | docs は無変更では済まない | real | 採用 (下記 4) |
| B-8 | dispatch へ queue 上限を渡す対案は seam が無い | real | 採用 (対案は不採用) |
| B-9 | D289 は緩めない | real | 採用 |

## 2. 中心裁定 — 台帳 status を増やさず、既存の停止 sidecar で fail-closed に閉じる

**決定的な実測: status を新設しても、その producer が 1 本も残らない。**

- dispatch 申告の timeout は D454 により `OrphanHoldStop` で先に止まる
  (`tools/mutation_harness.py:1822-1832` の raise が `:1841` の status 算出より前、
  `docs/decisions.md:18982` 以降、既存 pin は
  `orchestrator/tests/test_mutation_harness.py:900-970`)。
- local 申告の timeout は、本 wave が下記のとおり停止させる。
- したがって `QUEUE_TIMEOUT` を台帳語彙へ入れても、**書き込む経路がゼロになる**。
  死んだ語彙のために schema v5 へ上げると、B-3 のとおり
  既存 v4 台帳の `--resume` と v4 shard の再併合が全滅する。

**よって本 wave は台帳 status を増やさない。** local 側の queue timeout は、
D454 が既に確立した「別 file の停止記録 + rc=2 + 変異保全」という**実証済みの形**へ寄せる。
これは `TIMEOUT` の意味を「実行 timeout」に限定するという台帳項の目的を満たす
(queue 由来の timeout は `TIMEOUT` にならなくなる) 一方、
受理集合を増やさず、v4 互換を 1 件も壊さない。

### 実装する内容

1. `tools/mutation_harness.py:1589-1594` — dispatch submission inventory の before snapshot を
   `runner_mode` と `attempt_recorder` に依らず常に取る。
2. `_run_tests` の timeout 分岐 (`:1628-1634`) — local mode でも after inventory を取り、
   **新規 submission が 1 件以上現れていたら** その事実を result へ載せる。
   receipt の読取・解釈は行わない (A-2 により receipt は保証されないため、
   一次証拠は「submission directory が新しくできた」ことだけとする)。
3. 変異・baseline・collection の各段で、local mode の timeout かつ新規 submission ありなら
   **terminal record を書かずに停止する**。停止記録は既存の停止 sidecar と同じ経路へ、
   区別できる理由コード (例 `runner-mode-violation`) で書く。rc は既存の停止と同じ 2。
4. **非 timeout の local 走行は一切変えない** (dispatch されたが正常終了した走行は
   正しい結果なので、受理集合を狭めない)。
5. D454 の閉鎖を pin する回帰テストを足す
   (dispatch timeout が terminal record を 1 件も作らないこと)。

### 不変条件

- 証拠が無い・判定できない場合は必ず停止側 (非 terminal) へ倒す。
- 既存テストの期待値を変更・反転・skip しない。local hang の `TIMEOUT` 期待
  (`orchestrator/tests/test_mutation_harness.py:881,893-894`) はそのまま緑でなければならない。
- 台帳 schema は `izanagi-dev-wave-mutation/v4` のまま。summary 欄・status 集合・
  `_MERGEABLE_STATUSES`・D289 の TIMEOUT 全面拒否はいずれも変更しない。
- `tools/mutation_fanout_contract.py` と `tools/mutation_worktree.py` は**変更しない**。

### 成果物影響 (DW-G05)

これを実装しないと、local 申告の変異走行が queue 待ちのまま timeout したとき、
一度も実行されていない変異が `TIMEOUT` として `completed` に数えられ、
`registered == recorded == completed` が成立する。変異台帳が出す「N/M KILLED」という
検出力の値そのものが、実行されていない変異を分母・分子に含んだまま緑になる。

## 3. ユーザーへ返す裁定パッケージ (scope 外・実装しない)

台帳項 [T-848] は「queue timeout を別 status にする」と書いており、これはユーザーの指示である。
本 wave はそれを**実装せず**、次の新事実を添えて再裁定を仰ぐ。

- (新事実 1) 台帳項が名指しした dispatch 経路は、D454 (2026-08-16) で既に閉じており、
  既存テストが固定している。台帳項が書かれた時点では存在しなかった決定である。
- (新事実 2) 生き残っている経路は local 申告 × 実 dispatch であり、そこでは
  「RUN 開始を receipt で確認」が原理的に成立しない。dispatch は polling 中に receipt を書かず、
  harness は SIGTERM の 5 秒後に SIGKILL するため、receipt が残らないことがある。
- (新事実 3) 新 status を台帳語彙へ入れると schema v5 が必要になり、
  既存 v4 台帳の `--resume` と v4 shard の再併合が全て拒否される。
- (新事実 4) 本 wave の実装後、新 status の producer は 1 本も残らない (上記 2)。

**親の推奨: 台帳へ新 status を足さない。** 別 status の目的 (走っていない変異を terminal に
数えない) は停止 sidecar で達成でき、v4 互換を壊さない。台帳項 [T-848] は
「dispatch 経路は D454 で決着、local 経路は本 wave で決着」として閉じるのが妥当と考える。

## 4. docs

B-7 は v5 前提の指摘なので、v5 を採らない本裁定では runbook の v4 逐語変更は不要になる。
DW-M06 の逐語 (`docs/dev-wave/mutation.md:37-40`) は「timeout は fail-open の証拠」と読める。
本 wave 後も dispatch/local とも queue 由来の timeout は停止になるため、
この逐語が誤読を生むかを段 7 で再評価し、**docs 予算 (3 層とも満杯) に入らなければ
変更せずユーザー裁定へ返す** (DW-S08)。

## 5. 変異事前登録 (DW-M01 / DW-M08)

wave 前の実コードの形を必ず含める。期待 node は実装後に親が焦点走の実測で完全集合を導出する
(B-6 のとおり parameterize 後の suffix を含める)。

| ID | 変異 | 意図 |
|---|---|---|
| M1 | local timeout を wave 前の形 (無条件 `TIMEOUT`) へ戻す | 本 wave の中心。wave 前の形 |
| M2 | inventory snapshot を `runner_mode == "dispatch"` 条件へ戻す | 証拠収集の無効化 |
| M3 | 「新規 submission が 1 件以上」の判定を常に偽へ倒す | 判定器の無効化 |
| M4 | 停止せず terminal record を書いて続行させる | 即停止 (A-7) の無効化 |
| M5 | `tools/mutation_harness.py:1830` 相当の `raise pending_stop` を削る | D454 pin の検出力 |

各変異について、同じ入力を落とす層が前後に無いことを実装子に確認させる (F28/F377 の型)。
