# [T-1647] A-2 certification の投入を workload 単位の独立 job へ分割する

- 日付: 2026-08-27
- wave: `dev-wave-t1647-a2-cert-fanout`
- branch: `worktree-dev-wave-t1647-a2-cert-fanout` (base `dd6621397`)
- 実装 commit: `c8eb45cb4` (実装)、`6d7697b95` (レビュー fix)
- **4-cell certification の実走はしていない。** 本文書は「投入を分割し、批准 gate の手前で
  fail-closed する形を実装して land するまで」の記録である。

## 依頼と、着手前の実測で覆った前提

依頼は「A-2 の 4-cell certification を実走して回収する」+ ユーザー補足
「時間がかかりすぎ。可能な限り計算ジョブとして分割してどかっと計算ノードに投げるべき」。

着手前に 2 点を実測し、依頼の前提が 2 つ覆った。

1. **批准の終端は今も出る。** 現行 closure digest は
   `a14a261280e60a25ca28135695fc80c0bfeee2071922d03da4b7225b65190ab3`。批准台帳
   `hooks/enforcement-source-closure-ratifications.v1.jsonl` は 1 行のみで
   `db511c3d84…` (A-1 が 2026-08-25 に批准した別版) である。
   `require_ratified_closure()` は `enforcement-source-closure-unratified` を送出する。
2. **原因は D1028 / D1038 の非認証成果物型ではない。** D1070 が「D1028 が批准 gate の定義域の
   外へ意図的に出した非認証成果物型は、対象に含めない」と明記している。非認証経路で回しても
   certified を名乗れない (絶対規律 2)。**真の原因は D905 の執行主体が main へ未着地であること。**
   その実装は branch `worktree-dev-wave-t1629-ratification-broker` に存在し、main 未着地である。

## 「時間がかかりすぎ」の実体は 2 つだった

一次資料 `output/insights/2026-08-26_a2-4cell-walltime-cost.md` を読み直した結果、
起票時から引き継がれていた数値の読み方を 1 点訂正する。

**695.95 秒は 1 cell あたりではなく、4 cell 合計の 1 反復あたりである。**
5 反復で 3479.75 秒 ≒ 58 分。ビルドと性能測定 20 回を足しても 4 cell 全体で約 1 時間である。
そこへ 6 時間 (21600 秒) の枠を予約している。cell 別 (1 反復) は
rr5-stock 164.89s / rr5-fixed10 75.58s / rr50-stock 335.67s / rr50-fixed5 119.81s。
**律速は walltime ではなく RSS** で、rr50-stock のピークは 20.29 GB (閾値 32 GB の 63%) である。

したがって「時間がかかりすぎ」の実体は、直列実行ではなく
**(a) 枠が実コストの 5〜6 倍であること**と**(b) 批准 gate が閉じていて 1 秒も測れないこと**だった。
分割で削れる計算時間そのものは、もともと 1 時間しかない。

## 分割は既定の規範だった

`docs/pegasus-runbook.md` に 2026-08-11 のユーザー裁定がある —
「計算ノードへ投げられる仕事が互いに独立なら、**既定で並行投入する**。
『同じ protocol を別の workload / 別のパラメータで回す』は fan-out してよい典型である」。
**A-2 の 1 本直列のほうが逸脱だった。** 同節の「独立」3 条件を A-2 に当てると次のとおり。

| 条件 | 着手前 | 本 wave 後 |
|---|---|---|
| 1. 共有して奪い合うものが無い | **不成立** — 2 job が `raw/`・`campaigns/`・claim namespace を共有し、finalizer が親 `raw/` を走査する | 成立 — `jobs/<workload>/` を job 所有 subtree にし、finalizer は policy 由来の exact path を直接開く |
| 2. protocol が順序・単一テナント・同一 campaign 内比較を要求しない | 成立 (workload 内だけ stock→adopted) | 不変 |
| 3. 固定費が見合う | 成立 (正味 rr5 ≒ 1202 秒 / rr50 ≒ 2277 秒 に対し prologue は 100 秒台) | 不変 |

**並列度の上限は 2 である。** cell 単位に割ると `run_workload` が要求する
stock → adopted の対照条件が壊れる。反復 5 回を別 job へ割る案は各反復を別 campaign・別 lock へ
束縛し直すことになり proof chain を変えるため採らない。

## 本 wave の終端は「実装 + land」— 実機投入はしない

2 つの独立した既裁定が同じ終端を指した。

- **D646 (2026-08-22 ユーザー裁定)**: 新設の Pegasus login-side 実行体を registry へ登録する wave は
  同じ wave 内でそれを実機から起動できない。hook が repo root を primary checkout へ固定して
  解決するため、worktree 側の未 land な registry entry を反映しないからである。
  「実装 + land」と「実機初回検証」を最初から 2 wave に分けて計画せよと明記されている。
- **D1070**: 批准検査を dispatch へも広げる。未批准の closure で scheduler request を作ることは
  その向きに反する。

段 1 brief が置いた「分割した投入を実機へ 1 回投げて配線を実測する」は、この 2 点により撤回した。

## 実測 2 件 (親が実物を通した結果)

```
$ python3 -B -m orchestrator.campaign.paper_story_a2_certification submission-precheck
paper-story A-2 indeterminate: submission ratification precheck failed:
enforcement-source-ratification: enforcement-source-closure-unratified:
closure digest is absent from the read-only ledger
rc=2
```

**qsub へ進む前に止まる。** これが本 wave の中核の実証である。

```
$ bash tools/pegasus/submit_paper_story_a2_certification.sh --attempt-id t1647-fanout-probe-20260827
[guard_bash] 拒否: 未登録 Pegasus 実行体
(tools/pegasus/submit_paper_story_a2_certification.sh) を拒否します
```

registry entry は本 wave の commit にあるが hook は primary checkout の main を見る。
**D646 の実物である。** 迂回はしない (手動 qsub は D141 が禁じる)。

## 批准とは別の、記録されていなかった 2 つ目の障壁

段 6 のレビューが、A-2 の chain には **group completion / acquisition を作る正規 producer が
存在しない**ことを摘出した。`record-completion` は呼び手が用意した JSON を検証して保存するだけで、
その payload を作る経路が repo に無い。したがって **批准が開いても、そのままでは chain を
閉じられなかった。** 本 wave は同じ login 側実行体へ create-only な `finish-group` mode を設けて
この欠落を埋めた。

## 段 6 レビューが出した所見と裁定

敵対レビュー 2 本 (レンズ = 防壁が発火するか / 受理集合と取り残し) が must-fix 6 件と
「裁定へ返す」1 件を出した。親は **7 件すべてを real** と裁定し、1 件を nit とした。
「裁定へ返す」1 件は返さずに親が裁定した。

- **最重 (実 producer が動かない)**: campaign の出力 root が二重化しており
  (`jobs/<workload>/campaigns/campaigns/<cid>`)、実 producer は測定後の raw cell 生成へ到達
  できなかった。**焦点走が緑だったのは、テストが実 producer を通さず期待側の layout を
  手で組み立てていたためである。** `A2.run_workload()` を直接通す正例を足して塞いだ。
- campaign claim の `protocol_digest` が値として束縛されておらず、64 桁 hex であることしか
  見ていなかった。再構成した `CampaignConfig` から再計算して一致を要求する形にした。
- `finish-group` が投入専用の関門 (qsub / quota / queue / clean-tree) を継承しており、
  完走済み 2 job の成果物を取り出せない過剰拒否があった。
- 合成 qstat fixture が実機 94 行に対し 7 行の抜粋だった。歴史 fixture の全文から
  request ID と canonical log path だけを置換した形へ作り直した。歴史 fixture 自体は
  SHA-256 `55bc7a63…830d` のまま 1 byte も変えていない。
- `materialize()` が certification result の版を検査せず、旧 v2 形式や不完全な report を
  `certification.json` として publish できた。
- 変異 M4 の帰属が立っていなかった。負例が手前の存在検査で落ちるため、原子的な create-only の
  行そのものを殺せていなかった。
- **親裁定 (レビューが「裁定へ返す」としたもの)**: job-local な raw の closure 検査が落ちて
  余分 file が受理される件は、**返さずに must-fix へ格上げした。** 禁じたのは 2 job が共有する
  親の走査であって、1 job だけが所有する `jobs/<workload>/raw/` の closure 検査は
  独立条件を壊さない。旧版と同じ厳密さを job-local で復活させた。
- **nit**: group helper の workload 順序・log path 相異の述語は production 経路では前段の検査に
  含意されて恒真である。冗長検査であることをコメントで明記し、独立防壁として数えない。

## 変異台帳 (逐語)

- harness: `tools/mutation_worktree.py` (`--runner-mode dispatch`、`--detached`、固定 commit の
  使い捨て worktree)
- runner argv: `python3 tools/run_tests.py
  orchestrator/tests/test_paper_story_a2_certification.py
  orchestrator/tests/test_paper_story_a2_job_contract.py -rf`
- spec SHA-256: `5eaf67b5d5eeed2912ab47dbaadad326b8a554267ab310fc827e3b19b6d74a10`
- repo head: `6d7697b952fcd7f31ae94c7ede6bb4da903aff71`
- baseline: `PASSED` (86 passed)
- 集計: **`KILLED 8 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0`**
- spec と結果 digest: `mutation-spec.json`、`mutation-result-digest.json`

| ID | 単一変異 | 判定 | 落ちた node |
|---|---|---|---|
| M1 | policy の論理積規則を `_protocol_preimage` の対象から外す | KILLED | `test_policy_is_the_exact_literal_four_cell_protocol` |
| M2 | group の request ID 相異検査を外す | KILLED | `test_m10_full_submission_and_completion_receipts_are_cross_bound` |
| M3 | group の workload 順序検査を外す | KILLED | 同上 |
| M4 | raw の原子的 create-only を `exist_ok=True` へ | KILLED | `test_compute_preflight_rejects_each_m7_boundary[stale-raw]` |
| M5 | job-local raw の closure 検査を外す | KILLED | `test_raw_manifest_binds_campaign_lock_and_wal_and_freezes_raw_bytes` |
| M6 | campaign claim の protocol digest 照合を外す | KILLED | 同上 |
| M7 | login 側の批准 precheck を外す | KILLED | `test_m10_full_submission_and_completion_receipts_are_cross_bound` |
| M8 | 「全 driver_rc が 0」を「1 件でも 0」へ緩める | KILLED | `test_raw_manifest_binds_campaign_lock_and_wal_and_freezes_raw_bytes` |

**M1 は「policy に書いた規則が飾りではない」ことの機械的証明である。** 規則を hash の対象から
外すと落ちるので、書いただけで発火しない状態にはなっていない。

### erratum — 変異走行の中断 3 件

いずれも変異の結果ではなく親の手順不備である。記録として残す。

1. 1 回目: runner argv に `-rf` が無く preflight で停止 (DW-M08 の要求)。変異は 1 件も走っていない。
2. 2〜3 回目: 親が scratch を `rm -rf` した結果、git に「登録済みだが実体がない worktree」が残り、
   共有木の事後検査が停止した。`git worktree prune` とコンテナごとの作り直しで解消した。
   他 wave の scratch 登録には触れていない。
3. 4 回目: M4 の回で計算ノードの投入が受領証を出さず (rc=1、stdout 空)、harness が
   「rc≠0 なのに落ちた node を抽出できない」を fail-closed で停止した。`--resume` で M4 から
   再開し、8/8 が完走した。**M1〜M3 の判定は resume を跨いで保存されている。**

## 作業中に前提が覆った — D1139 で批准機構が廃止された

**本 wave の段 8 が終わった時点で、main が 93 commit 進み、批准機構そのものが撤去されていた。**

**D1139 (2026-08-27、ユーザー裁定)「enforcement source closure の批准突き合わせを廃止する」。**
逐語は「なんかその突き合わせ？廃止でいいよ。私何度も言ってなかったっけ？トップジャーナルで
『この文字列で実行したプログラムで測った性能です。』なんて厳密な束縛見たことないって。…
一定時間以降誰にも性能測定ができなくなってしまうルールに囚われている？不必要だねそんなものは」。

実測した main の状態は次のとおり。

- `orchestrator/campaign/enforcement_source_ratification.py` は **削除済み**。
- `contract_loader_binding.verify_ratified_contract_loader_binding` は **存在しない**
  (`capture_contract_loader_binding` は残る)。
- D1139 は **D905 / D1039 / D1070 / D1071 を明示的に上書き**している。
  D905 が命じた執行主体は「今後も作らない」と明記された。

本 wave への影響は 2 つある。

1. **着手時に実測した終端 `enforcement-source-closure-unratified` は、main ではもう発火しない。**
   「A-2 は D905 の着地待ち」という本 wave の当初の結論は無効になった。
2. **段 4 で採用した R8 (login 側の批准 precheck) は呼び先を失った。** 追随して撤去した。
   撤去したのは批准集合との照合だけで、D1139 が「残す」と定めた検査 (disk bytes と記録
   commit blob の自己整合、記録 commit blob と記録 digest の照合、activation tuple の真正性)
   には触れていない。`ratified_qsub` は `exact_qsub` へ改名し、**qsub argv の exact 検査は残した**。
   保護対象 5 file (`contract_loader_binding.py` / `artifact_admission.py` / `ident.py` /
   `campaign_lock.py` / `buildcache.py`) と `hooks/` の差分がゼロであることを親が実測した。

**分割そのものは D1139 の影響を受けない。** workload 単位の独立 job、job 所有 subtree、
exact 2-job group receipt、raw manifest の交差束縛、`finish-group` はいずれも不変である。

### 変異台帳 v2 (main 取り込み + 批准撤去の後)

- spec: `mutation-spec-v2.json` (M7 を撤回した 7 変異)
- spec SHA-256: `9604fc332b616a6636547e602fe695fdcf58fef5d0ac9cd9db3233e7d245c534`
- repo head: `8b169bec6be6014620d7de4fcc131cfc8cdab1b3`
- baseline: `PASSED`
- 集計: **`KILLED 7 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0`**
- 結果 digest: `mutation-result-digest-v2.json`

**M7 の撤回理由は「殺せなかったから」ではない。** 対象の機構が D1139 で廃止され、
変異させる行が存在しなくなったためである。撤回前の走行 (8/8 KILLED) の記録は
`mutation-spec.json` と `mutation-result-digest.json` にそのまま残す。

## 残る障壁 (本 wave では解かない)

1. ~~**D905 の執行主体が main へ未着地。**~~ **解消した。** D1139 が批准機構ごと廃止し、
   D905 を明示的に上書きした。A-2 の実走を塞いでいた批准の壁は無い。
2. **実機初回検証は次 wave。** D646 により、registry の追加が main へ land するまで
   新 submitter を起動できない。**批准の壁が消えたため、次 wave は
   「配線の確認」ではなく 4 cell certification の実走そのものに進める。**
3. **新設 login-side 実行体の admission 分類は規則と先例が食い違う。** runbook は
   「grandfather は当該 4 本限りで、他 entry を `local-ok` にするには実測が要る」と書くが、
   B-10 の 2 本は実測なしに `local-ok` + `static login-side submitter classification` で
   登録されている。本 wave は B-10 と同形で登録した。**どちらが正かはユーザー裁定に返す。**
4. **attempt 単位の測定値選別の余地**が既存機構に残る。`automatic_retry: false` は記録される
   だけで consumer が無く、attempt を何個でも preregister して良い attempt だけ materialize
   できる。fan-out の交差束縛は「rr5 を attempt A、rr50 を B から混ぜる」ことは防ぐが、
   attempt 全体の選別は防がない。別 wave の設計課題である。

## 逐語

- `verbatim/s1-brief.md` — 段 1 brief
- `verbatim/s4-adjudication.md` — 段 4 裁定 (変異事前登録を含む)
