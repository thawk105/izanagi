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

二段で走らせた。1 段目は DW-M07 が定める **probe** で、全件 `SURVIVED` 期待で登録して
観測 node を集める。2 段目が本走で、probe の観測 node を**期待完全集合**として pin し
`KILLED` 期待で走らせる (DW-M08)。

- 本走 spec sha256: `e3ba8cc464ed148df4e8598614594cf48d2427e3056b6408f171a3b64514e3fa`
- 本走 repo_head: `caaa838cbfec459c5bc4958e07f3d11f1683573d`
- runner: `--runner-mode dispatch` / runner sha256 `2e69b62aea116bf1…`
- baseline: **PASSED** (rc=0, 所要 27.0 秒、失敗 node 0 件)
- wrapper: child_rc=0, shared_snapshot_matches=true, teardown_completed=true
- launcher の終了 rc: 0

**集計: KILLED 9 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0 (登録 9 件、記録 9 件)**

| 変異 | 無効化した gate | 本走 | 期待 node 数 | 実測 node 数 | 一致 | 所要 |
|---|---|---|---|---|---|---|
| M1 | stage5 contract kind の判定 | KILLED | 2 | 2 | はい | 42.6s |
| M2 | plan input hash の照合 | KILLED | 1 | 1 | はい | 27.0s |
| M3 | author output hash の照合 | KILLED | 1 | 1 | はい | 27.0s |
| M4 | downstream pin の role 別取得 | KILLED | 17 | 17 | はい | 27.0s |
| M6 | fix pass index の上限判定 | KILLED | 1 | 1 | はい | 27.4s |
| M7 | downstream receipt の model/effort 照合 | KILLED | 2 | 2 | はい | 27.9s |
| M8 | task acceptance の exact `unbound` 判定 | KILLED | 2 | 2 | はい | 57.9s |
| M9 | create-only wrapper (通常上書きへ) | KILLED | 3 | 3 | はい | 27.2s |
| M10 | validation receipt の post-apply tree hash 再照合 | KILLED | 1 | 1 | はい | 27.2s |

### 4.1 読み方

**登録した 9 件すべてが KILLED で、期待 node 完全集合と一致した。** 生存変異はゼロである。
gate を 1 つ無効化すると、その gate を狙った test だけが落ちる形になっている。

M4 だけ期待 node が 17 件と多い。`downstream_pins[expected_role]` を反対の role へ
入れ替えると、downstream receipt の検証が最初の `requested_model` 照合で落ちるため、
その先の leaf 検査を狙った parameterized case が**まとめて**赤くなる。
受理集合が変わる向きは正しく、kill としては成立しているが、**単一理由ではない** —
DW-M03 の「過剰決定」に当たるので、M4 単独の赤を「role 別 pin だけが効いた証拠」として
引用してはならない。role 別 pin の単独証拠は
`test_stage5_downstream_receipt_validator_binds_role_specific_pins` が持つ。

probe と本走で M4 の node 集合は 17 件で一致し、さらに 1 回目の probe で timeout した
孤児 job (942745) の `FAILED` 行から回収した 17 件とも完全一致した。**独立した 3 回の観測で
同じ完全集合が出ている**ため、この期待集合は決定的である。
