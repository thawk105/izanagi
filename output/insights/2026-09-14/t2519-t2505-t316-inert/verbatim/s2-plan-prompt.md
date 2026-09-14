単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert

## 必読事項の射影

下記の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、読めなかった path を
述べて終わること (自分で見つけた別 path の不在は停止理由にしない)。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/s1-brief.md` — 親の段 1 brief
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/measurement-1.md` — **本 wave が
   既に取った計算ノード実測の逐語**
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1936-item17.md`
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1856.md`
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1625.md`
6. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-d1849.md`
7. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2519-t2505-t316-inert/verbatim-tasks.md`
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.py`
   — 特に `_execute_ccbench_build` と `_require_condition_gate` (1826 行付近〜1975 行付近) と
   受理理由コード集合 (120 行付近) と `_condition_gate_receipt_summary` / `_condition_gate_family_valid`
   (320 行付近〜410 行付近)
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/tools/pegasus/probes/t316_sandbox_backend_probe.pbs`
10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/orchestrator/campaign/condition_meaning_gate.py`
    — 全文は大きいので、少なくとも `DEFINE_SPECS` (60 行付近〜160 行付近)、
    `capture_define_inputs`、`_run_configure` (1690 行付近)、`_capture_cmake_identity` (1491 行付近)、
    `evaluate_define_supply_effectuation` とその inert 分岐 (2600 行付近〜2710 行付近)、
    `require_condition_gate_family`、CLI の `main` (4155 行付近〜)
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/output/insights/2026-09-09/t2213-probe-condition-gate/README.md`

## 立場と権限

- あなたは **read-only** の plan 起草者である。file を書けない。出力は最終メッセージだけである。
- **commit しない。docs を書かない。`qsub` / `qstat` / `qdel` を実行しない。**
- 書込可能な tmp が無いため pytest 緑は要求しない。**静的検査でよい。** テストの実走は親が行う。
  実走していないものを緑と書かないこと。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終わること。無出力が最悪である。

## 依頼

本 wave の目的は **実測** である。関門を通すためだけの修正で偽の緑を作ることは絶対規律 2 違反として
禁じられている。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外である。
この前提で、次の 5 点を file:line 粒度で起草せよ。

1. **実測 1 の解釈。** 射影 2 の実測は T-2519 (「既存機構で inert 要求が stock 同等の緑へ到達するかを
   計算ノードで実測する」) と T-2505 (「t316 driver 自身が
   `stock-inert-preprocess-root-location-only` の緑に到達する環境を、本 commit を束縛した計算ノード
   probe で実測する」) のそれぞれについて、**何を確定させ、何を確定させていないか。**
   「到達しなかった」で両項が満たされるのか、それとも原因不明のままでは満たされないのかを、
   台帳本文と D1936 項17 / D1856 の逐語に照らして判定せよ。

2. **`supply=red/configure-failed` の原因候補の全列挙。** `condition_meaning_gate.py` の
   どの経路がこの reason code を出しうるかを file:line で列挙し、t316 が渡す実引数
   (`configure[5:]` から `-DCCBENCH_BACKOFF_FIXED=-1` を除いたもの、`stock_root` は
   `shutil.copytree` の複製) の下で**現実に起こりうるもの**と**起こりえないもの**に分けよ。
   起こりえないと判定した根拠は必ず code の行で示せ。

3. **各候補を弁別する最も安い手段。** 計算ノード 1 走あたりのコストを踏まえ、候補を潰す順序を示せ。
   **実装面 (コード・script・probe) の変更をまったく伴わずに弁別できる候補があるなら、それを最優先で
   示せ。** login node で実行できるものと、計算ノードの job でしか実行できないものを分けよ
   (login node には CCBench の依存 gflags / glog が無い — 射影 11 の実測)。

4. **実装面の変更が要る場合の最小の変更面。** 原因特定に実装面の変更が避けられないなら、
   file:line 粒度で最小の変更を示せ。次の制約を守ること:
   - D1849 は「`evidence` mapping 自体は受領証へ出さない」と決めている。受領証の schema と
     受理集合を変えない形にすること。
   - D1625 の受理集合 (inert 緑は 2 契約のどちらかに exact 一致) を緩めないこと。
   - probe の BOUND_PATHS (`.pbs` の `BOUND_PATHS` 配列) に載る file を変えると、次の投入は
     新しい commit を束縛することになる。その影響を書くこと。

5. **親の provisional 裁定への攻撃。** 親は次の 2 つを暫定で置いた。一次資料で裏づくか、
   崩れるかを判定せよ。崩れるなら、何をどう読み替えるべきかを書け。
   - **(P1-1)** T-2519 の「既存機構」は t316 probe の `BACKOFF_FIXED` inert 要求を指し、
     T-2505 と同じ probe 1 回で両方満たせる。T-2518 (t2187 の A+B+C patch 木) は D1936 が
     別項として維持しており重複しない。
   - **(P1-2)** 今の main の probe は無改変で S6 の条件関門まで到達し、実測が得られる (実装面ゼロ)。
     — 射影 2 の実測でこれは部分的に検証されている。どこまで検証され、どこが未検証かを述べよ。

## 出力形式

次の見出しを H2 で立てて書くこと。

```
## 実測 1 の解釈
## configure-failed の原因候補
## 弁別手段と順序
## 実装面の最小変更 (要る場合)
## (P1-1) (P1-2) の判定
## 総括
```

`## 総括` には、次の一手として親が取るべき行動を 3 行以内で書くこと。
