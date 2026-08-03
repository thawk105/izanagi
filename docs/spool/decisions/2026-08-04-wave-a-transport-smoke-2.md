---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: wave-a-transport-smoke
seq: 2
---

## {{D:pegasus-attestation-blocks-wall1}}. 壁 1 を塞いでいるのは transport ではなく実行時 attestation である — 述語と凍結較正の択一はユーザー裁定へ返す

**決定 (1): 生死確認は実施し、壁 1 は越えられていないと確定した。**
使い捨て driver + job script を計算ノードの 1 ジョブで走らせた (request 882490、bnode002)。
2 脚 (`legacy+s2` / `legacy` 単独) とも **build へ到達せず**、`build_done` / `verify_done` /
`bench_done` は WAL に 1 件も書かれていない。**したがって transport 自体については肯定・否定
いずれの証拠も得ていない。** 逐語と一次資料は
`output/insights/2026-08-04_wave-a-campaign-transport-smoke/`。

**決定 (2): 塞いでいる原因を特定した。実行時 attestation である。**
両脚とも `execution_guard` の `effective_clock.samples_mhz` 比較で停止した。述語は
「期待列の中央値を中心に、**観測列の全要素**が ±`tolerance_pct` に入ること」であり、
Pegasus 契約は `attestation_mode="required"` なので campaign の全実行がここを通る。
詳細と自己不整合の実測は {{F:pegasus-attestation-self-rejecting}}。

**決定 (3): 述語と凍結較正のどちらを正とするかは実装せずユーザー裁定へ返す。**
これは正しさ防壁と凍結成果物の bytes に同時に触れるため AI が既成事実にしない。択一:

- **(a) 較正側を正とし、述語を「観測の分布」対「期待の分布」の比較へ変える。**
  例: 両側の中央値差を見る、または外れ値を 1 件許容する。
  **有利材料:** 凍結 bytes を変えない。ブーストは実機に常在する現象なので、
  「1 コアでも外れたら不合格」は環境ノイズで恒常的に落ちる。
  **不利材料:** 受理集合が広がる。どこまで緩めるかの根拠を別途要する。
- **(b) 述語を正とし、較正を取り直して登録し直す。**
  **有利材料:** 述語 (全コアが定格帯) は「計測時に余計な負荷が無い」ことの検査として意味を持つ。
  **不利材料:** 凍結成果物の再登録は proof chain の参照を動かす。しかも取り直した較正が
  再びブースト混じりなら同じ穴が再発する — 取得手順側に「全要素が帯内であること」の
  受入検査を同時に入れない限り閉じない。
- **(c) attestation を campaign 実行から外す。** — **却下。** 規律 2 に反する。
  計測環境が登録時と同じであることの検査を、通らないという理由で外してはならない。

**推奨: (b) + 取得時受入検査。** 述語の意図 (計測時に定格から外れたコアが無い) は正当であり、
壊れているのは「その検査を満たさない較正を登録できてしまった」側だからである。
ただし凍結成果物の再登録はユーザー裁定事項である。

**決定 (4): D131 の共通前提のうち 2 件は既に閉じていた。**
- `total_deadline` が順番待ちを実行時間から差し引く欠陥は解消済み。`dispatch_compute.py` は
  RUN を初観測した時刻へ deadline を rebase する。
- 走行中ジョブへの qdel は fresh qstat gate が禁じている (`_QDEL_CLEANUP_POLICY`)。
一方 **D117 決定 (4)(b) は未解消**である。`_job_run` は `os.environ.copy()` を継承したうえで
request の environment を上書きするだけで、`_TaskSpec.env_allowlist` を**子側で強制していない**。
allowlist が効くのは親が request に載せる値の絞り込みだけである。

**決定 (5): 恒久実装の設計は、この wave で判明した 3 つ目の面を加えて設計する。**
D131 は (a) `TASKS` へ task 追加 / (b) `submit_*.sh` を 1 本足す、の 2 択だった。
本 wave はここに**第 3 の面**を加える: **8c の CLI (`p3_autonomous_workload_trial.py`) は
`--provider fixture` と実 build が排他であり、計算ノードの build opt-in は `claude-headless`
provider 専用で LLM transport receipt を要求する。** したがって「LLM を使わずに計算ノードで
build する」経路はあの CLI に存在しない。恒久実装はこの排他をどう解くかを含めて設計する必要がある。
本 wave は `drive_iteration` を直接呼ぶ使い捨て driver でこれを回避したが、これは
sanctioned な形ではない。

**理由:**
- `DW-G01` は本格実装前の最安の生死確認を義務づける。
- `DW-S04` は「scope 外の real 所見は実装せず、設計択一・所見・推奨案を裁定パッケージで返す」と定める。
- F84 の「sanctioned job script の正規化を逐語で再利用する」の射程には、環境正規化だけでなく
  **投入インタフェース (qsub 引数の受け渡し形) も含む**。今回そこを発明して投入前に止めた
  ({{F:qsub-positional-args-invented}})。

**却下した選択肢:**
- **8c CLI を `--allow-pegasus-compute-transport` 付きで使う** — 計算ノードで LLM を起動する形になり、
  分割線の議論 (D122 と inbox の再裁定待ち) の帰結を先取りしてしまう。本 wave は LLM を経路から
  完全に外し、どちらに転んでも成立する形を採った。
- **numactl を偽装して S2 verify を通す** — 規律 2 に反する。契約が宣言した空 prefix をそのまま使い、
  落ちるなら落ちたまま記録する方針を採った。
- **attestation を迂回して transport だけ測る** — 同上。防壁を外して得た「通った」は証拠にならない。

**この決定が保証しないこと:** build / verify / bench の transport が計算ノードで通るかは
**依然として未知**である。本 wave はそこへ到達していない。attestation の裁定が付いた後に
同じ使い捨て driver を再走させれば、追加実装なしで確かめられる。

## {{D:pegasus-numactl-single-node}}. Pegasus 計算ノードは単一 NUMA ノードであり、契約の空 numactl には根拠がある — ただし S2 verify は代理条件で塞がれている

**決定 (1): 実測を記録する。** bnode002 は `available: 1 nodes (0)`、48 CPU が node 0、127476 MB。
`numactl` は計算ノードに存在する (`/bin/numactl`) が、**ログインノードには存在しない**。
単一ノードでは `--interleave=all` は交互配置する相手がおらず実質的に恒等である。
したがって `env_contract` の Pegasus 契約 `numactl=()` には実質的な根拠がある。

**決定 (2): S2 verify が Pegasus で塞がれている件は、静的確認に留める。**
`pipeline.py` は「S2 相当 (`fullscale_isolated=True`) を含む verify 構成で `numactl` が空なら
build 前に `ValueError`」と定める (D36 決定4-4)。Pegasus 契約は空なので必ず発火する。
**gate が見ているのは「numactl prefix が非空か」という代理条件**であり、本来の目的である
「verify と bench でメモリ配置を揃える」は単一 NUMA ノードでは自明に満たされている。
本 wave では attestation が先に落ちたため**実機ではこの gate に到達していない**。

**決定 (3): gate は変更しない。** 代理条件を「配置が揃っているか」の直接判定へ置き換える案は
正しさ防壁に触るため、attestation の裁定と併せてユーザーへ返す。

**理由:** 規律 2 は正しさゲートを緩める変異を禁じる。代理条件が過剰に厳しいという主張は、
実機で発火を確認してから出すべきであり、本 wave はそこへ到達していない。

**却下した選択肢:**
- **契約の numactl を非空へ書き換えて S2 を通す** — 単一ノードで `--interleave=all` を付けても
  意味は変わらないが、契約 bytes は proof chain に束縛されており勝手に動かせない。
