## 所見ごとの判定 (表: ID・closed/partial/regressed・根拠 file:line)

以下の `scripts-v2/` は指定された fix 後の snapshot を指す。判定は静的点検による。

| ID | 判定 | 根拠 file:line |
|---|---|---|
| R1・B-02 | closed | [run_judge.sh](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/run_judge.sh:30) は検査器 rc を保存し、51–55 行で非ゼロ rc を返す。合格は 46 行で `rc=0` かつ report の `result=pass` に限定される。 |
| R2・B-01 | closed | [launch_one.py](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/launch_one.py:95) は E1 の新しい `#if TRACE` 枝を末尾に作り、120–128 行で rc・`pass`・32 文脈を確認する。計算 job での実データ判定は未実走。 |
| R3・B-08 | closed | [check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/tools/check_trace0_preprocess_identity.py:1173) は既存の上位 key を維持し、1178–1180 行に path 別期待数を追加。file 別の期待数と実数も 681–683 行に残る。 |
| R4 | closed | [check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/tools/check_trace0_preprocess_identity.py:615) は Cicada の場合だけ 4 macro の値をタグに足し、623–646 行の不一致文にそのタグを使う。Cicada 以外は従来の `_context_tag(overlay)` のまま。 |
| R5 | **partial** | [run_judge.sh](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/run_judge.sh:25) は F→A の path 集合を確認するが、26–29 行の blob 照合は合成 bundle から clone した repo 内の修正 tip を参照する。[mk_synth.sh](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/mk_synth.sh:39) の A→B は F を親に作られ、57 行の bundle は B だけを head とするため、修正 tip commit はその履歴に含まれない。照合はそこで停止する見込み。 |
| B-03 | closed | [dispatch_one.sh](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/dispatch_one.sh:7) の EXIT trap は rc・終了時刻を `.done` に書く。[submit_one.sh](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/submit_one.sh:11) は使用済み tag を拒否し、12–25 行で失敗済み job の新 tag による再投入と成功済み job の拒否を扱う。 |
| B-04 | **partial** | [mk_receipt.py](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/mk_receipt.py:10) は request ID・実行ノード・Elapse を抽出し、無ければ明示する。ただし実 dispatch は未実走なので、6 件の実 receipt や同時稼働はまだ確認できない。 |
| B-05 | closed | [launch_one.py](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/launch_one.py:40) は段別の秒数を `result.json` に保存し、161–165 行で clone・依存準備、182–185 行で configure・build、209–218 行で run・verify、246–247 行で登録検査を記録する。MOCC の cell は 31 行で 1 秒のまま。 |
| B-06 | closed | [launch_one.py](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/launch_one.py:48) は timeout 時に段名・上限・経過秒・専用 rc=124 を構造化記録し、失敗にする。 |
| B-07 | closed | [mk_index.py](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/mk_index.py:15) は bundle・合成成果物・manifest・検査器を索引化し、32–43 行で各 job の report／result／receipt と SHA-256 を JSON・Markdown にまとめる。 |

## 新しい所見 (ID・重大度・file:line・放置時の影響・推奨)

- **F-01・must-fix・[run_judge.sh:20–29](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/run_judge.sh:20)、[mk_synth.sh:51–57](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/mk_synth.sh:51)**：R5 の再照合は、合成 bundle から clone した repo に修正 tip commit があることを前提にしている。B→A→F の履歴にはそれらの tip がないため、両 D297 job は検査器の起動前に失敗する見込み。**推奨:** job が既に `verify_inputs.sh` で clone した修正 bundle 側の各 tip blob と A の blob を照合する。両入力の同一性も固定したまま確認する。
- **F-02・should・[mk_index.py:24–37](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/mk_index.py:24)**：索引は `synth.oids` をファイルとして記録するが、A・B′の commit OID を独立した欄には展開しない。また D297 の `decision.json` を索引対象に含めない。放置すると索引表だけで合成 commit と最終合否を追いにくい。**推奨:** `synth.oids` の値と `decision.json` の path・SHA-256 を索引に追加する。

fix 前後の差分では、事前登録の合格条件、MOCC cell、Cicada 以外のタグ・文言、検査器の受理集合を弱める変更は見つからなかった。EXIT／INT／TERM の trap は [dispatch_one.sh:9–16](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/dispatch_one.sh:9) で再入を解除しており、通常の終了経路で `.done` を二重に書く形ではない。再投入も [submit_one.sh:34–39](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/submit_one.sh:34) から元の job script を呼ぶため、照合を迂回しない。

## 投入可否

**NO-GO。** [submit_all.sh:6–12](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/submit_all.sh:6) は指定の 6 job を待たずに投入する構成で、[submit_one.sh:34–39](/work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v2/submit_one.sh:34) の引数・出力先と walltime は D297 各 `01:30:00`、CI `00:15:00`、正しさ 3 本各 `00:30:00` に一致する。repo root は呼出側から渡され、dispatch 時の `cd` と各 job の引数に使われる。ただし F-01 により D297 2 本が検査前に止まる見込みなので、このまま 6 job を投入できる完成形ではない。実際の配置・完走も未確認。

## 総括

R1–R4 と B-03・B-05–B-08 の修正は静的に確認できた。R5 は再照合の参照元に欠陥があり、B-04 は実 dispatch の証拠待ち。親の焦点テスト 4 file は **337 passed** だが、計算 job は未実走である。F-01 を直してから投入可否を再判定する。