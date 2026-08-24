# [T-1480] stage5 author downstream replayer — 変異台帳と dispatch timeout の切り分け

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は探索の妥当性文書
(measurement record) であり、裁定台帳ではない。

- 起点: `docs/archive/worklog-phase3-0822-811.md` の T-1480、
  `docs/phase3-t189-model-routing-preregistration.md` §5.3、段4裁定
  (`dev-wave-jobs/dev-wave-t1480-stage5-author-replayer/s4-verdict.md`)。
- 測った checkout: branch `worktree-dev-wave-t1480-stage5-author-replayer`。
  実装 commit `687253ac`、main 取り込み後の tip `5f9bc54b`。
- 実行環境: Pegasus 計算ノード dispatch (`--runner-mode dispatch --force-dispatch`)。

---

## 1. この wave が作ったもの

`tools/codex_reasoning_ab.py` へ stage2 とは別系統の `stage5-author-replayer` 契約族を足した
(production 1 file + 直接 test 1 file、main 比 +2940 / -6 行)。

- 固定 plan 入力、author の `git diff` patch、適用先 snapshot、git 実行体を run-root 配下へ
  create-only で凍結し、source path / descriptor / SHA-256 を照合する。
- 適用は private validation clone の中だけで `git apply --check` → `git apply` を pin 済み argv で
  行い、live checkout と ambient cwd を触らない。
- review / fix の model・effort pin を role 別の exact-key object として持ち、stage2 の値や
  fallback を参照しない。`fix_pass_limit` は stage5 固有の独立定数で検証する。
- downstream receipt validator は純粋関数で、process を起動しない。

---

## 2. 最大の設計上の含意 — acceptance を unbound のまま出す

意味的な受理を判定する task-specific oracle が無い。したがって receipt は
`task_acceptance_status="unbound"`、`fix_gate_eligible=false`、`routing_evidence_eligible=false`
を exact に出し、generic な `accepted` / `success` / `passed` を全深さで拒否する。
詳細と却下した選択肢は同 wave の decisions fragment に置いた。

段3の敵対相談 2 本が独立に「machine receipt を semantic acceptance に使う案」を blocker として
挙げ、段4でこれを採用して runtime の review/fix loop 自体を本 wave の scope から外した。
**「形式が整えば受理」に化ける経路を、機能を足す前に閉じた**のがこの wave の主要な成果である。

---

## 3. dispatch 経路の TIMEOUT は変異の性質を語らない

本 wave で最も転用価値のある実測はここである。

変異 probe の 1 回目 (spec `timeout_seconds: 300`) で M4 だけが TIMEOUT になり、harness が停止した。
M4 は `contract["downstream_pins"][expected_role]` の添字を反対の role へ入れ替えるだけの変異で、
ループを作る余地が無い。scheduler の逐語を読むと理由が確定した。

| 項目 | 値 |
|---|---|
| Created Request Time | Mon Aug 24 14:14:30 2026 |
| Started Request Time | Mon Aug 24 14:19:47 2026 |
| Ended Request Time | Mon Aug 24 14:19:53 2026 |
| Elapse | 10S |
| child_rc | 1 |

**queue 待ちが 317 秒、テスト本体は 10 秒。** 同じ spec の M1 / M2 / M3 は queue が空いていたため
27〜30 秒で完走している。混雑した瞬間に投入された 1 件だけが timeout になった。

これが安全側でない誤りである理由は、F32 の恒久対応 3 が timeout を
「その変異が fail-closed から fail-open へ倒れた証拠」として扱うと定めているからである。
queue 由来の timeout をそのまま読むと、**実際には 17 件の test に検出されている変異を
「gate をすり抜けた」と台帳へ書く**ことになる。

切り分けは job stderr の 2 つの差で足りる。`Started - Created` が queue 待ち、`Elapse` が実行時間。
`Elapse` が小さければ変異は無実で、spec の timeout が短すぎただけである。

### 3.1 二次障害 — hold 未解除の resume は投入側の異常を変異側の言葉で記録する

1 回目の abort が残した orphan-hold を解除しないまま `--resume` を投入した結果、dispatch は
即座に拒否し、harness からは `receipt 表示行が exactly one でない: 0` / `rc=16` /
所要 **0.113 秒** の PARSE_ERROR としてしか見えなかった。記録には
「canonical stdout から failed node を確実に抽出できない」という変異側の言葉が残った。

所要 0.113 秒 (baseline は 32 秒) だけが投入側の異常を示していた。**PARSE_ERROR を見たら
`duration_s` を先に読む**のが最短の切り分けである。

### 3.2 timeout した job の成果物は諦めた後に届く

harness が 14:19 に諦めた後、14:20 に submission dir へ `receipt.json` と 96260 bytes の
job stdout が書かれていた。`IZANAGI FAILURE DIGEST` の抜粋部は budget で切り詰められ
(`failures=17 selected=14 omitted_failures=3`)、そこから node を数えると 3 件落ちる。
一方 `short test summary info` の `FAILED` 行は 17 件すべて残っており、F71 の抽出経路は
完全集合を取れる。**切り詰められるのは抜粋であって FAILED 行ではない。**

---

## 4. 変異 matrix

(本走の結果をこの節へ追記する)
