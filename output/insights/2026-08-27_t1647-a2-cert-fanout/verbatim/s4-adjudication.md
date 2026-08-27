# 段 4 裁定 — [T-1647] A-2 certification の投入分割

基準: 段 1 brief、段 2 plan (s2/out.md)、段 3 sol (正しさ境界) / luna (束縛の実効性)。
親の実測を含む。

## 0. 本 wave の終端を決めた既裁定 — D646

**D646 (2026-08-22 ユーザー裁定)** は、新設の Pegasus login-side 実行体を registry へ登録する wave は
**同じ wave 内でその実行体を実機から起動できない**と定め、「実装 + land」と「実機初回検証」を
最初から 2 wave に分けて計画せよと明記している。理由は hook が repo root を primary checkout に
固定して解決するため、worktree 側の未 land な registry entry を反映しないことである。

したがって **本 wave の終端は「実装 + land」であり、実機投入は行わない。**
これは段 1 brief が置いた「分割した投入を実機へ 1 回投げて配線を実測する」を覆す。
親の当初計画は D646 を見落としていた。

同じ結論へ段 3 sol が別経路から到達している (所見 1)。**D1070** は批准検査を dispatch へも
広げると裁定しており、未批准の closure で scheduler request を作ることはその向きに反する。
2 つの独立な理由が同じ終端を指す。

## 1. 親の前提のうち撤回するもの

- **(撤回) 「途中で切れても失うのは 1 workload = 2 cell」。** 段 3 sol 所見 3 が real。
  attempt は `automatic_retry: false`、raw は create-only、resume は scope 外であるため、
  片方が落ちたら成功した側も正式 certification には使えず 4 cell 全再走になる。
  **分割の効用は待ち時間の短縮とノード隔離であって、損失の削減ではない。**
- **(撤回) 「実機へ 1 回投げて gate 手前までの配線を実測する」。** 上記 D646 と D1070。
- **(見送り) 枠 (elapstim) の右寸法化。** 段 2・段 3 の双方が同じ理由で据え置きを推す。
  正式な全工程 (build + 小構成 correctness 4 回 + 5 反復 + 性能 20 回 + cooldown) の所要は
  一度も測っていない。現に手元にあるのは 4 cell 各 1 反復の verifier 時間だけで、
  5 反復 58 分は線形換算である。縮小は受理集合を未測定のまま狭める。**6 時間を維持する。**
  RSS のほうが逼迫している (rr50-stock で 20.29 GB / 閾値 32 GB) が、これは分割しても
  rr50 job 内のピークとして残り、時間枠では解けない。

## 2. real と裁定し採用する所見

| # | 出所 | 所見 | 採否 |
|---|---|---|---|
| R1 | luna 1 / sol 4 | 2 job が `raw/`・`campaigns/`・claim namespace を共有し、finalizer が親を走査するため、並行投入の独立条件 1 を満たさない | 採用 |
| R2 | 両者 | preregister と compute-preflight が同じ `raw/$workload` の作成権を主張し自己矛盾 | 採用 |
| R3 | sol 2 + 親検算 | 4 cell を別ノード・別時刻の 2 campaign から作るのは受理集合の拡大であり policy に規則が無い | 採用 |
| R4 | plan / luna 9 | 6 wire contract の bump が要る。consumer 取り残しの列挙が不足 | 採用 |
| R5 | sol 5 | raw manifest が lock/WAL しか凍結せず、campaign と request/node の事後束縛が閉じていない | 採用 |
| R6 | luna 4 | group receipt の job 取り違えは、交差照合を明文化すれば拒否できる | 採用 |
| R7 | luna 5 | group completion / acquisition の**正規 producer が存在しない** | 採用 |
| R8 | sol 1 / D1070 | login 側に批准 precheck が無い | 採用 |
| R9 | luna 10 | `docs/failures.md` の直接編集は規則違反 | 採用 |
| R10 | luna 11 | 計画された負例では変異の帰属が立たない (層が互いを mask する) | 採用 |

### R1 の解 — job 所有 subtree

`jobs/$workload/` を完全な job 所有 subtree とし、`raw`・campaign output root・cache root・
`reservation.json`・`compute-result.json`・`scheduler/` をすべてその下へ置く。
finalizer は親 directory を列挙せず、**policy から導いた exact path を直接開く**。
これで「親 directory を検査する consumer を共有しない」を満たす。

### R2 の解 — 作成権の一本化

preregister は `jobs/` 親と各 `jobs/$workload/` container までを作る。
**`jobs/$workload/raw` の唯一の create-only owner は compute-preflight の原子的 mkdir とする。**
`exist_ok=True` への緩和は採らない (同一 cell の再取得面が開く)。

### R3 の解 — 論理積を hash へ入れる

policy に「各 workload は独立に環境契約された campaign であり、外側の certification は
その論理積である」旨を明記する。**ただし親の検算により、`_protocol_preimage`
(`paper_story_a2_certification.py:261-271) は `scheduler` を含まず、policy に書き足すだけでは
`protocol_sha256` が動かない。** 書いただけで発火しない飾りになる。
**規則は必ず `_protocol_preimage` の対象へ入れ、policy schema を v1 → v2 へ上げる。**
段 2 plan の「policy は変更しない」は落とす。

### R4 の解 — 7 つの版上げ

submission v3→v4 / completion v2→v3 / acquisition v2→v3 / certification result v2→v3 /
compute result v1→v2 / raw manifest v2→v3 / **policy v1→v2** の 7 つ。
現行値は現物 (定数定義と policy JSON) で確認済み。consumer の追随は次のとおり。
- `test_paper_story_a2_certification.py:727` の submission v3 golden を更新する。
- 既存 qstat fixture (`fixtures/paper_story_a2/qstat-visibility-945411.stdout`) は
  **歴史物として書き換えない。** 新 layout 用の fixture は合成で足す
  (実機由来の fixture 追加は実機初回検証 wave の仕事)。
- `acceptance_duration_ledger.json` は新規 test node を含めて正規生成器で再生成する。
  推測値を手書きしない。
- `output/insights/2026-08-25_…-run-defects.md:78` の「v3 据え置き」は過去記録であり
  書き換えず、後継文書から supersede する。

### R7 の解 — finisher を作る

同じ login 側実行体に create-only な `finish-group` mode を設け、submission receipt が持つ
exact な request ID だけを対象に、終端観測・log hash・compute/reservation hash の採取から
`finalize-raw`・completion・acquisition の生成までを一続きで行う。
**これは fan-out 固有の不足ではなく、単一 job の現行 chain にも存在した欠落である。**
すなわち T-1647 は批准とは別に、この欠落でも塞がっていた。

### R8 の解 — 批准 precheck

login 側 entry point の先頭で `capture_contract_loader_binding()` →
`verify_ratified_contract_loader_binding()` を呼び、失敗したら **qsub を 1 件も出さずに終える。**
親はこの経路が現に発火することを実測した (本 worktree で
`enforcement-source-closure-unratified: closure digest is absent from the read-only ledger`)。
DW-O13 の「入力が実環境で取りうる値を実測できるか」を満たす。
T-1629 所有 file (`campaign_lock.py` / `contract_loader_binding.py` / `artifact_admission.py`) は
**呼ぶだけで変更しない。**

## 3. scope 外の real 所見 — 裁定パッケージとしてユーザーへ返す

- **(P-1) 新設 login-side 実行体の admission 分類が、先例と規則で食い違う。**
  runbook は「grandfather は当該 4 本限りで、他 entry を `local-ok` にするには実測が要る」と
  書いている。しかし B-10 の 2 本は実測なしに `local-ok` +
  `static login-side submitter classification` で登録されている。
  本 wave は B-10 と同形で登録するが、**規則と先例のどちらが正かはユーザー裁定に返す。**
  どちらに倒れても本 wave は land できる (実機投入は D646 により次 wave のため)。
- **(P-2) attempt 単位の測定値選別の余地が既存機構に残っている。**
  `automatic_retry: false` は記録されるだけで consumer が無く、attempt を何個でも preregister し、
  良い attempt だけ materialize できる。fan-out の交差束縛は「rr5 を attempt A、rr50 を B から
  混ぜる」ことは防ぐが、attempt 全体の選別は防がない。**別 wave の設計課題。**
- **(P-3) A-2 の実走そのものは、D905 の執行主体 (T-1629 の broker) が main へ着地し、
  その主体が現行 closure digest `a14a2612…` を批准するまで開かない。** 本 wave は解かない。

## 4. 反証として確定したもの

- 5 反復と枠は段 2 計画で緩められていない (sol 6 / luna 8)。6 時間維持でよい。
- `IZANAGI_A2_WORKLOAD` の到達可能性は既存実走と B-10 の先例で裏付く (luna 7)。
  ただし実機で両値を観測するまでは「配線済み」とだけ書き「実測済み」と書かない。
- request 別 dependency prefix が build identity に入るため、rr5-stock と rr50-stock の
  build cache 衝突は起きない (sol 8)。契約テストで固定する。
- 別 wave 所有物への越境は無い (luna 12)。A-2 の driver / job / policy は
  enforcement closure 25 path に含まれず、本変更は批准 digest を動かさない。
- workload 単位の選択的取り直しは、R2 の形にすれば成立しない (luna 3)。

## 5. 変異の事前登録 (DW-M01)

R10 に従い、**各変異は 1 field だけを不整合にし、それ以前の全 field は canonical に保つ fixture**
を用意する。層が互いを mask する 2 箇所は別帰属にする。

| ID | 変異 | 帰属を守るための条件 |
|---|---|---|
| M1 | policy の論理積規則を `_protocol_preimage` の対象から外す | policy 内容を変えても `protocol_sha256` が動かない負例を直接 unit call で当てる |
| M2 | group validator の request ID 相異検査を外す | 同一 request ID を 2 entry に持つ payload。他 field は canonical |
| M3 | workload の順序検査を集合一致へ緩める | rr50, rr5 の順の payload。ID・path は正しいまま |
| M4 | compute-preflight の raw create-only を `exist_ok=True` へ | **shell 層の fresh 検査を通さない直接 unit call**。shell 側が先に落ちると帰属しない |
| M5 | finalizer を親 directory 走査へ戻す | 余分な workload directory を置いた attempt。exact path 経路だけを見る |
| M6 | raw manifest の campaign claim 交差照合を外す | 別 request の claim を貼った manifest。他 field は canonical |
| M7 | login 側の批准 precheck を外す | 未批准状態で qsub 直前まで到達する負例 (qsub 自体は stub) |
| M8 | completion の「全 driver_rc が 0」を「1 件でも 0」へ緩める | 片側 nonzero の group completion |

**受理集合を縮小する wave であるため、承認外の過剰拒否を検出する正例も登録する。**

| ID | 正例 |
|---|---|
| P1 | canonical な 2-job group receipt が完全に通ること (全 validator を通過) |
| P2 | 批准済みを模した closure では precheck が通り qsub 経路へ進むこと |
| P3 | 単一 workload の job が自分の subtree だけを作り、他方の subtree の存在で拒否されないこと |

## 6. 実装単位 (段 5 の順序)

1. **U1** policy v2 — 論理積規則を文書化し `_protocol_preimage` へ入れる。schema 定数の 7 bump。
2. **U2** attempt layout — `jobs/$workload/` job 所有 subtree。preregister と compute-preflight の
   作成権の分離。job body の workload 径数化 (`IZANAGI_A2_WORKLOAD`)、compute result v2、
   job body から `finalize-raw` を除去。
3. **U3** group receipt — submission / completion / acquisition / result を exact 2-job group へ。
   workload 集合・順序・request ID 相異・log path 相異の交差照合。
4. **U4** raw manifest v3 — nested layout、exact path 直接 open、campaign claim の交差照合。
5. **U5** login 側実行体 — 批准 precheck、preregister、exact 2 qsub、submission receipt、
   `finish-group` mode。
6. **U6** 追随 — admission registry、runbook 投影表、`tools/pegasus/README.md`、test_hooks の
   3 golden、契約テストと負例・正例、acceptance ledger の再生成。

## 7. 成果物影響 (DW-G05)

実装しない場合、A-2 certification は (a) 批准が開いても group completion の producer が無いため
chain を閉じられず、(b) 4 cell を 1 本の 6 時間 job で直列に取るしかなく、(c) 未批准のまま
計算ノードの枠を消費する経路が残る。certified な cell の集合そのものは本変更で変わらない。
変わるのは、到達できるかどうかと、到達までに消費する計算資源である。
