# [T-2519] [T-2505] t316 実経路の inert 要求は inert 比較の手前で赤になる — 計算ノードで実測した

- wave: `dev-wave-t2519-t2505-t316-inert` / branch `worktree-dev-wave-t2519-t2505-t316-inert`
- 起点 main: `3b80b5a96589e30bd22410c9e2d7b4cb77d9e13a`
- 日付: 2026-09-14
- 実測環境: Pegasus 計算ノード (`gen_S`、1 node、walltime 01:30:00)。投入元は本 wave の worktree。

## 一行で言うと

**t316 driver 自身の実経路では、条件関門の inert 要求は `stock-inert-*` の比較に到達しない。**
その手前で `supply=red/configure-failed` になる。CMake configure 自体は rc=0 で成功しており、
未使用変数の警告が stderr に出たことで赤になっている。**「新しい理由コードで t316 の関門を通せる」は、
現状の t316 実経路では成立しない。**

**これは新しい失敗型ではない。** F934 の独立 3 例目であり、F855 の同型再発でもある。
親は段 1 の一次資料に `docs/failures.md` を含めず、段 3 のレンズにも渡さなかったため、
段 7 の記録を書く直前までこの位置づけに気づかなかった。訂正の経緯は
`verbatim/s4-adjudication-addendum.md` に残した。

## 依頼と、確かめよと言われたこと

- **[T-2519]** (D1936 項17、2026-09-10 裁定): D1856 の繰延べを維持し、まず既存機構で inert 要求が
  stock 同等の緑へ到達するかを計算ノードで実測する。
- **[T-2505]**: t316 driver 自身が `stock-inert-preprocess-root-location-only` の緑に到達する環境を、
  本 commit を束縛した計算ノード probe で実測する。現在の根拠は A-5 の別 driver が同じ evaluator で
  到達した記録にすぎず、t316 実経路の実測ではない。

依頼は「2 件は同じ probe で満たせる見込みなので 1 wave にまとめ、満たせないと段 1 で分かった時点で
分ける」と定めた。**段 1 では分からず、実測で分かった。完了判定を分けた。**

## 実測 1 — 無改変の probe で、条件関門は拒否した

probe を 1 byte も変えずに投入した。

| field | 値 |
|---|---|
| `PBS_JOBID` | `0:996644.nqsv` |
| `hostname` | `bnode040` |
| `observed_commit` | `3b80b5a96589e30bd22410c9e2d7b4cb77d9e13a` |
| `bound_paths_clean` | `True` |
| `login_node_rejected` | `True` |
| probe 内 elapsed | 26.3 秒 (PBS Elapse 32S) |

- S1〜S5 は go。**S6 は `S6_BUILD_NOT_ATTEMPTED` で blocked**、S7 も blocked、overall no-go。
- S6 の観測 (逐語):
  `{"attempted": false, "error": {"message": "condition gate rejected t316 CCBench build:
  supply=red/configure-failed, meaning=unestablished/meaning-witness-undeclared",
  "type": "RuntimeError"}, "reason": "S6 raised"}`
- **`stock-inert-preprocess-root-location-only` にも `stock-inert-preprocess-identical` にも
  `stock-inert-mismatch` にも到達していない。** inert 比較そのものの手前で落ちている。
- 既存の受領証 2 件 (2026-08-10、`0:900383.nqsv` / `0:900427.nqsv`) には `condition_gates` が
  **0 件**である。**t316 実経路での条件関門の実測は、本 wave が最初である。**

受領証: `output/env/pegasus/t316-sandbox-backend/0:996644.nqsv/receipt.json`
逐語: `verbatim/measurement-1.md`、生ログ: `evidence/job-996644.*`

## 実測 2 — 拒否理由の直接証拠を取った

実測 1 の受領証には reason code しか残らない。`evidence` は D1849 により受領証へ出さず、probe の
`RuntimeError` も `terminal_status/reason_code` しか載せていなかったため、**計算ノードで実際に何が
起きたかが失われていた**。段 4 で、拒否の直前に `evidence` の `detail` を job stderr へ出す局所変更を
裁定し (受理集合・receipt schema・拒否そのものは一切変えない)、新しい commit を束縛して再投入した。

| field | 値 |
|---|---|
| `PBS_JOBID` | `0:996829.nqsv` |
| `hostname` | `bnode016` (実測 1 とは別ノード) |
| `observed_commit` | `fecb4f709e40cf0119940d760aa80b38b1ceafae` |
| probe 内 elapsed | 25.7 秒 (PBS Elapse 31S) |

受領証の S6 は実測 1 と**完全に同一**である (reason code・stage verdict・文面)。
新たに job stderr へ出たのが次である。

```
condition gate rejected t316 CCBench build: supply detail=successful process wrote stderr=b'CMake Warning:\n  Manually-specified variables were not used by the project:\n\n    CCBENCH_BACKOFF_FIXED\n    IZANAGI_GFLAGS_SRC_HEAD\n    IZANAGI_GLOG_SRC_HEAD\n    RULE_LAUNCH_COMPILE\n\n\n'; argv=/usr/bin/cmake -S <worktree>/external/ccbench -B /tmp/izanagi_condition_supply_gh4nt2dh/requested -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_CXX_COMPILER=/usr/bin/x86_64-linux-gnu-g++-11 -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF -DCCBENCH_TRACE=0 -DCCBENCH_BACK_OFF=0 -DCCBENCH_NO_WAIT_LOCKING_IN_...<argv truncated; limit=500 bytes; original=1202 bytes; sha256=acb67b71c0ee05ae535d04f057aed96b5340bb10d891c1719e739baa7e6364de>
condition gate rejected t316 CCBench build: meaning detail=<no detail>
```

受領証: `output/env/pegasus/t316-sandbox-backend/0:996829.nqsv/receipt.json`
逐語: `verbatim/measurement-2.md`、生ログ: `evidence/job-996829.*`

## 原因 — 4 つの事実で構成される

1. **gate は configure が rc=0 でも stderr が非空なら `configure-failed` にする。**
   `orchestrator/campaign/condition_meaning_gate.py:1617-1622` (呼び出しは
   `_configure_compile_commands:1713-1715`)。detail の先頭が `successful process wrote stderr=`
   であることから、今回がまさにこの分岐である。起動失敗でも rc≠0 でも timeout でも
   identity drift でもない。
2. **素の CCBench には `CCBENCH_BACKOFF_FIXED` の CMake option が無い。**
   `external/ccbench/cmake/Options.cmake` にあるのは `CCBENCH_BACK_OFF` だけである。
   `BACKOFF_FIXED` は izanagi の patch が供給する変数である。gate は requested 側で必ず
   `-DCCBENCH_BACKOFF_FIXED=<値>` を足すので、**patch 未適用の木では必ず未使用警告が出る。**
3. **t316 は CCBench が参照しない変数をさらに 3 件渡している。**
   `IZANAGI_GFLAGS_SRC_HEAD` / `IZANAGI_GLOG_SRC_HEAD` / `RULE_LAUNCH_COMPILE`。
   いずれも CCBench の CMake で grep hit 0 である。
4. **落ちたのは requested 側である。** argv の `-B` が `/requested` を指す。
   stock 側の configure は実行されていない。

## 既知の失敗型との関係 — F934 の独立 3 例目、F855 の同型再発

- **F934「patch 由来 define の条件関門が、patch を materialize しない driver では構造的に通らない」**
  — 認定 launcher (`certify_calibration.sh`) と A-1 driver
  (`paper_story_a1_paired.py`) で既に独立 2 例が記録されている。detail の文面まで一致する。
  **関門は fail-closed で正しく拒否している。** D1198 が義務化した関門の射程に、patch を当てない
  driver が入っていた、という構図も同じである。
- **F855「condition gate は configure 成功でも stderr 非空を red にし、driver が渡した未使用 CMake
  変数の警告で compute 走が停止した」** — `RULE_LAUNCH_COMPILE` を gflags / glog の install build から
  流用する点まで一致する。F855 の恒久対応「driver から未使用変数を除去」は t316 へ未適用だった。
- **D1864** が「patch が供給する define を、その patch を materialize しない経路で新しい protocol へ
  広げない。`BACKOFF_FIXED` はこれに当たる。**silo の現行挙動は据え置き、扱いはユーザー裁定へ返す**」
  と定めている。t316 はその据え置き対象側にある driver である。

## 判定 — 2 件を分けた

| 対象 | 判定 | 根拠 |
|---|---|---|
| **[T-2505]** | **未完** | 台帳は「`stock-inert-preprocess-root-location-only` の緑に到達する環境」の実測を求める。到達していない。旧契約の緑でも CLI の緑でも代用しない |
| **[T-2519]** | **先行観測を得たが完了としない** | D1936 項17 の逐語は「到達する**か**」であり緑限定ではない。今回の赤は指定条件での有効な回答である。しかし「既存機構」は t316 と一意に名指されておらず、t316 だけで閉じる根拠が無い。backoff_sweep 経路は 2026-09-07 に bnode039 で同じ evaluator の緑へ到達している |
| **D1856 の繰延べ** | **解除しない** | 解除条件 2 件 (13 macro の runtime witness、patch stack 適用木の inert 緑の計算ノード実測) のどちらも満たしていない。D1936 項17 の「繰延べを維持」に従う |

## 直し方は本 wave で実装していない

原因が分かっても、その修正 (未使用変数の削除、関門へ patch 木を渡す、警告抑制) は
**本 wave の scope 外**とした。A-2 insight
(`output/insights/2026-09-02/a2-condition-gate-patched-root/README.md`) の
「一般化できる教訓」が逐語で警告しているとおりである。

> **「関門だけを通す」修正は偽の緑を作りうる.** 当初の既定方針は「patch 由来の cache 変数を、
> 定義しない木へ渡さない」だった。それを採ると requested と control の configure が構成上同一になり、
> inert 比較が自明に緑になる。さらに関門だけを patch 文脈へ入れると、関門は patch 済みの木を検査し
> campaign は素の木を build するという乖離が生まれる。**検査した木と build する木を一致させる**
> ことが、この族の修正の不変条件である。

t316 は素の木を build する probe である。したがって (a) 未使用変数を削るだけでは
`CCBENCH_BACKOFF_FIXED` が残り、(b) 関門へ patch 木を渡すと検査する木と build する木が食い違う。
**この設計択一は起票して次へ送る。** F934 が既に独立 2 例を持ち本件が 3 例目なので、
族一般化の前提 (DW-G03) は揃っているが、その中身は D1864 が「ユーザー裁定へ返す」と定めた
論点そのものであり、親が実装で先回りする領域ではない。

## 実装した変更 (受理集合は 1 mm も動かしていない)

`tools/pegasus/probes/t316_sandbox_backend_probe.py` の `_require_condition_gate` で、
admission 拒否の直前に supply と meaning の `evidence.get("detail")` を job stderr へ出す。
診断の出力が失敗しても従来の `RuntimeError` がそのまま送出されるようにし、出力側の障害は
`__cause__` に残す (握り潰していない)。

守った不変条件:

- receipt の `_condition_gate_receipt_summary` と `SCHEMA_VERSION` は不変。
  **receipt へ `evidence` mapping を載せる経路を作っていない** (D1849)。
- inert 緑の 2 契約 exact 一致は不変 (D1625)。
- `RuntimeError` のメッセージは 1 文字も変えていない。**実測 1 と実測 2 の receipt の
  `observations.S6.error.message` が完全一致することで実証されている。**
- `orchestrator/campaign/condition_meaning_gate.py` は 1 byte も変えていない。

テストは実 CMake と実 gate を通す正例を 2 系統足した。configure を故意に失敗させて detail が
stderr へ出ることを検査するものと、stderr の `write` が `OSError` / `ValueError` / `RuntimeError` を
投げる 3 型で拒否が維持されることを検査するものである。機構を stub で迂回していない。

**F855 が根本原因に挙げた「driver は gate の status しか出力しないため理由が見えなかった」という
側面は、これで t316 について閉じた。** F855 の恒久対応は「login で `_require_condition_gate` と
同じ関数列を呼ぶ probe で読む」だったが、本 wave は**計算ノードの実走そのものから読めるように**した。

## 変異 — 3 走、最終 3/3 KILLED

`mutation/` に spec と台帳の全 3 走分を置いた。

| ID | 変異 | probe 走 | 本走 | 最終走 |
|---|---|---|---|---|
| M1 | `if not admission.admitted:` → `if False:` (拒否を消す) | MISMATCH (赤、4 node) | KILLED | **KILLED** |
| M2 | 受理理由コード組へ `("stock-inert-mismatch", ...)` を追加 | **SURVIVED** | (再照準のため取り下げ) | — |
| M2B | 受理判定そのものを恒真化 (`... in _INERT_CONDITION_GATE_PAIRS or True`) | — | MISMATCH (赤、3 node) | **KILLED** |
| M3 | 拒否時の診断出力を丸ごと削除 | MISMATCH (赤、4 node) | KILLED | **KILLED** |

最終走: `KILLED 3 / MISMATCH 0 / SURVIVED 0 / matching 3`、baseline PASSED、
`repo_head=77b0792510f8a3cc6aee6da1f8abc5058eb923ba`。

**erratum — M2 の SURVIVED (DW-M02 に従い初回結果を残す)。** 受理組へ
`("stock-inert-mismatch", "stock-inert-root-location-only")` を足しても誰も検出しなかった。
再照準した M2B が検出した node は
`test_s6_rejects_crossed_inert_condition_gate_pair[...]` 2 件と
`test_s6_rejects_requested_default_preprocess_difference` 1 件で、**D1625 の exact 一致は
既存 test が守っている**ことが分かった。M2 が生き残ったのは、追加した組の第 1 座標
`stock-inert-mismatch` が gate 側では赤の reason code であり、**その組へ到達する入力を通す経路が
production に無い**ためである。equivalent に近い変異であって、判定そのものの恒真ではない。
本 wave の変更に起因する穴ではないので、塞ぐことは scope 外とした。

**M3 の扱い (DW-M03 / DW-M08)。** M3 は受理集合を変えず構造化シグナルだけを pin する変異なので、
台帳の status は KILLED だが**正しさの kill としては数えない**。診断出力の
diagnostic sensitivity pin として別枠に記録する。M1 と M2B の 2 件が受理集合・fail-closed 挙動に
対する kill である。

**M1 と M3 が検出した 4 node は、いずれも本 wave が追加した test である。**
既存 test は `_require_condition_gate` の拒否を 1 件も pin していなかった。

## 実測値

- 焦点走 8 file (`test_t316_sandbox_probe.py`、`test_ccbench_spawn_sites.py`、`test_hooks.py`、
  `test_official_perf_closure.py`、`test_pytest_collection_config.py`、
  `test_acceptance_schedule_order.py`、`test_real_repo_serialization.py`、
  `test_plain_runner_coverage.py`): **890 passed, 2 skipped in 111.14s**、rc=0。
- probe test 単独: 145 passed in 4.61s。追加 test 単体: 1 passed in 4.44s。
- 基底と現行の test 関数名集合: **削除ゼロ・追加 2 件** (parametrize 前)。
- 全史 provenance 監査: 9795 件、新規違反なし。

## 段 3 / 段 6 が親を訂正した点

- 段 3 (2 レンズ) は親の分析へ 12 件の所見を出し、**親が現物で検算して全件 real と裁定した**
  (refuted ゼロ)。主なものは「原因を特定したという断定は成立しない (直接証拠を見ていない)」、
  「requested / stock のどちらで落ちたか未確定」、「`RULE_LAUNCH_COMPILE` の警告発生は裏づけ無し」、
  「引数は 22 ではなく 23 件」、「情報欠落の理由は D1849 ではなく例外経路」、
  「brief の『唯一の計算ノード driver』は親自身の証拠と矛盾する」。
  **実測 2 は、このうち「`RULE_LAUNCH_COMPILE`」と「requested 側」の 2 点を実測で決着させた。**
- 段 6 レンズ A は must-fix を 1 件出した。「診断出力が失敗すると従来の拒否例外が置換され、
  receipt の error が拒否情報から出力障害へ変わる」。real と裁定し fix した。
- 段 5 の実装子と段 6 の fix 子は、いずれも sandbox で runner が `rc=16` になり、
  **2 名とも「実装済み・未実走」と正直に申告した**。実走はすべて親が行った。

## この insight が保証しないこと

- **stock 側が単独で緑になるかは未測定である。** requested が先に落ちるため到達していない。
  stock 側は `-DCCBENCH_BACKOFF_FIXED` を渡されないので警告は 3 件になるが、3 件でも stderr は
  非空であり同じ分岐で赤になると読める。**これは推論であって実測ではない。**
- 失われた実測 1 の stderr 逐語そのものは復元できない。実測 2 は別 commit・別ノードでの再現走であり、
  同じ reason code・同じ stage verdict を示した。
- 1 allocation・2 ノード・2 commit での観測であり、全計算ノード・将来の main へは一般化しない。
- 本 wave は D1856 を解除していない。t316 の条件関門配線の設計択一も決めていない。
- 変異の M2 が示した過剰許容の穴は塞いでいない。
