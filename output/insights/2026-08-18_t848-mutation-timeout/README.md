# [T-848] 変異 TIMEOUT の意味を実行 timeout に限定する — wave 記録

wave: dev-wave-t848-mutation-timeout / branch: worktree-dev-wave-t848-mutation-timeout
base: 2a3b5055 / 実装 commit: bcd9c3e6
日付: 2026-08-17 22:40 JST 〜 2026-08-18 (JST)

## 何が問題だったか (台帳の前提は実測で覆った)

台帳項 [T-848] は「dispatch subprocess 全体に timeout が掛かるため、一度も走っていない変異が
terminal として `registered == recorded` を満たす」と書いていた。**dispatch 経路については
HEAD で再現しない。** D454 (`docs/decisions.md` の D454、2026-08-16) が
orphan-hold 停止を契約しており、`orchestrator/tests/test_mutation_harness.py` の
既存テストが rc=2・orphan-stop 記録・terminal record 非作成を固定している。

**生きていたのは local 経路である。**

- `--runner-mode local` は「実際に dispatch しない」ことを何も保証しない。
  `tools/run_tests.py` は `--force-dispatch` が無くても login headroom が不足すれば
  計算ノードへ dispatch する。
- harness は `--runner-mode` の申告と runner argv の実体を突き合わせていなかった
  (`grep -n "force-dispatch" tools/mutation_harness.py tools/mutation_worktree.py` は hit 0 件)。
- local 経路では orphan 防壁も receipt 束縛も 1 つも働かず、
  queue 待ちのまま harness 側 timeout に掛かった変異が terminal `TIMEOUT` として
  `completed` に数えられた。

## 規模と実害 (実測)

- 既存 spec 335 件のうち、実効 harness timeout が dispatch の queue 待ち上限 900 秒を
  下回る変異は 176 件 (25 spec)。
- `hang_risk` の変異は全史 20 件。`expected_status = "TIMEOUT"` の事前登録は全史 **0 件**。
- **台帳形式 (`status` 欄) の `TIMEOUT` 記録は全史 0 件** (repo 全体の JSON 2026 件 +
  JSONL 122 件、復号不能 0 の全件走査)。
  ただし schema 以前の手書き台帳 2 件が `verdict: "KILLED-BY-HANG"` /
  `"DIAGNOSTIC"` + `timed_out: true` を記録している (2026-07-27)。
  したがって「変異が timeout したことは一度もない」は誤りで、
  正しくは「harness 台帳形式では 0 件」である。

つまり実害はまだ出ていない潜在欠陥だった。

## 何をしたか

台帳 status は増やさない。決め手は「status を新設しても producer が 1 本も残らない」ことである
(dispatch 側は D454 が停止、local 側は本 wave が停止する)。死んだ語彙のために
schema を v5 へ上げると、既存 v4 台帳の `--resume` と v4 shard の再併合が全滅する。

代わりに local 側の queue timeout を、D454 が確立した停止 sidecar と同じ形へ寄せた。

- local でも dispatch submission inventory を走行前後で取る。
- timeout 時に、自分の走行へ束縛できる新規 submission があれば
  terminal record を書かずに停止する (rc=2、変異保全)。
- 束縛はこの走行だけの nonce (`secrets.token_hex(16)`) の一致で判定する。
  nonce は `PYTHONDONTWRITEBYTECODE` に載り、`tools/run_tests.py` を素通りして
  dispatch の `env_allowlist` 経由で `request.json` の `environment` に届く。
- 判定不能 (inventory が取れない・`request.json` が読めない) は必ず停止側へ倒す。
- local 側では D454 の create-only latch を張らない。
  D454 は latch の署名を receipt の `job_may_remain` だけと定めており、
  local はその署名を持たない。submission directory は qsub より前に作られるため、
  未投入でも latch を張ると解除に人手が要る 4 経路が止まる。
- local でも既存 hold を尊重して走行前に停止する。
- dispatch 経路の既存挙動は 1 bit も変えていない。その非回帰を回帰テストで固定した。

## 実測

- 焦点走 (6 file): 変更前 191 passed → 変更後 **196 passed / rc=0**。
- 変異 matrix: baseline **PASSED**、**5/5 KILLED**、MISMATCH 0、SURVIVED 0、期待一致 5/5。
  期待 node は probe 実走 (全件 SURVIVED 期待) で実測導出し、parameterize の suffix を含む
  完全集合で登録した。
- 全史 AI provenance 監査 rc=0。

### 変異と撃った実効ゲート

| ID | 変異 | 期待 node 数 |
|---|---|---|
| M1 | wave 前の形 (local を絶対に止めない) へ戻す | 4 |
| M2 | dispatch 側の submission inventory 収集を消す | 2 |
| M3 | 束縛を常に「自分のもの」にする | 1 |
| M4 | 判定不能を素通りさせる | 3 |
| M5 | D454 の dispatch latch を外す | 1 |

## 残件 (後続タスク候補)

1. **carrier 連鎖がテストで固定されていない。** テストは `request.json` を fixture 自身が
   書くため、「`run_tests.py` → dispatch が nonce を実際に運ぶ」1 段を pin していない。
   挙動は実コードで end-to-end に確認済みだが、将来この連鎖が壊れてもテストは緑のままになる。
2. **wrapper receipt の診断欄。** local 停止時、`tools/mutation_worktree.py` の receipt は
   `failure` を null のまま残す (wrapper の rc は child の 2 を返すので偽の緑ではない)。
   停止理由を機械検証できるようにするには wrapper 側の変更が要る (本 wave では no-touch)。
3. **DW-M06 の逐語**。「timeout は fail-open の証拠として記録し harness を落とさない」は
   queue 由来 timeout の扱いと食い違って読める。docs 予算の都合は段 7 で判定した。

## 成果物

- `mutation-spec.json` / `mutation-ledger.json`: 本走の spec と台帳。
- `mutation-spec-probe.json` / `mutation-ledger-probe.json`: 期待 node を実測導出した probe。
- `verbatim/`: brief、追補、段 2 プラン、段 3 敵対相談 2 本、段 4 裁定、実装子報告、
  段 6 敵対レビュー 2 本、fix 3 巡、裁定変更、焦点再レビューとその親裁定。
