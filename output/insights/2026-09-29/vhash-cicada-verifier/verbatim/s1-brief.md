# 段 1 brief — [md_3] Cicada を izanagi の正しさ検査器に通せるようにする (2026-09-29)

wave: dev-wave-vhash-cicada-verifier / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-verifier` (branch `worktree-dev-wave-vhash-cicada-verifier`) / 起点 local main `51f896352` (開始 gate fresh rc=0、03:2x JST) / CCBench gitlink は動かさない。依頼逐語 = `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_3.txt` + `common.txt`。台帳 item は main 未登録 (段 9 後に再探索)。

**研究前進:** VHash 論文系列 (docs-snapshot `2026-09-29.md` §8「前提: Cicada の正しさ検査 = 未整備」) の前提 G0 を満たす。これが無いと forwarding 試作の性能値は「未検証の診断値」のまま (規律 2)。完了判定 = (i) stock Cicada の小さい YCSB 走行の trace が現行 verifier に受理され巡回 0・integrity 違反 0、(ii) 壊した Cicada 2 本以上が巡回 (G0/G1c/G2) として検出され、どの txn 間のどの依存かが構造化出力に出る、(iii) TRACE=0 で trace 差分が命令列に残らない、を実測した insight。

**親の実測 (brief 前、file:line は worktree のもの):**
- Cicada に `TRACE` は 0 件。版 = `Version::wts_` (64bit、`(rdtscp()<<8)|thid`、`cc/cicada/include/time_stamp.hh:24-40`)。txn の書く版は全部 `this->wts_.ts_`。初期版の wts は起動時刻 `param->initial_wts` (`cc/cicada/include/tuple.hh:20,77-89`) で 0 ではない。verifier の genesis は `(1,0)` (`orchestrator/verifier/model.py:26`)。
- 流れ: read_internal `cc/cicada/transaction.cc:79-138` (可視版選択、pending は待つ、read_set_ へ `ver_`)、validation `:463-609` (版 install の CAS `:481-531`、rts 更新 `include/transaction.hh:295-307`、read set 再検査 `:543-570`、write set 検査 `:576-593`)、commit `:919-958` (**read-only は writePhase を通らず `:934-937` で即 return**)、writePhase `:895-917` → cpv `:687-721`。
- trace 共通 header `external/ccbench/include/trace.hh` の emit 引数は uint64。verifier は protocol 非依存 (parse/dsg に分岐なし)。`--protocol` が silo/si/mocc 以外なら X/P/I は unavailable → certification gate 不成立 → 巡回なし = indeterminate、巡回あり = non-serializable (`model.py:37,77-82,246-247,501-519`)。si と同じ上限。
- 先例: si の trace v2 は `patches/instr-si-trace-v2.patch` (27 行、`#if TRACE` 内だけ、無マクロ)。本来の置き場 (D16 の `izanagi-trace` 枝) への移送と pin 前進は人間判断として out-of-tree patch に置いた (`patches/README.md` [T-2847] 節)。D16 の T-109 一回限り例外は D579 が「流用には再裁定が要る」と判断済み (docs/decisions.md D579)。実走記録 `output/insights/2026-09-26/t2847-si-run/README.md`、repo 外起動器 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/launch_si_run.py` (Pegasus `dispatch_compute.py --task generic`、job ごと detached 計測用 checkout)。
- 裸マクロ付き壊し patch は条件 gate (`orchestrator/campaign/condition_meaning_gate.py`) と test allowlist への登録が要る (si brief の実測)。これは本 wave の所有外。
- `patches/ledger.json` は 1 件限定 (`orchestrator/campaign/silo_ladder_rung1_contract.py:516-517`)。登録は `patches/README.md` だけ。
- `patches/*.patch` を全件走査する test が 2 本: `orchestrator/tests/test_p3_s4_loop.py:8682` (`IZANAGI_[A-Z0-9_]+` を含む未登録 patch を赤、登録表は所有外) と `orchestrator/tests/test_mocc_template_proof.py:95,106` (mocc marker)。→ 新 patch は `IZANAGI_` の語を一切含めない (診断文字列も)。bytes pin (sha256・README 行) は検索で 0 件 (条件 09 は成立せず、10 も不成立)。条件 08 (oracle gate に隣接) は submodule 初期化済・`cc/cicada/` 実在を確認。条件 13 (検証の新設) は成立: 段 2 で trace に要る field の実在と実値域を確かめ、生死確認で実測する。
- 検査器 source の変更は campaign lock・artifact admission 等の束縛に波及しうる (`git grep` で `orchestrator/campaign/campaign_lock.py`・`artifact_admission.py` 等が参照)。

**(P1) 親の provisional 裁定・攻撃対象:** trace hook は `patches/instr-cicada-trace.patch` (無マクロ、`cc/cicada/` の `#if TRACE` 内だけ、共有 header 不変)。置き場は si 先例と同じ根拠で out-of-tree patch、D は fragment で記録。
**(P2)** 版の写像: `wts == initial_wts` の初期版 → `(1,0)`、それ以外 → `(wts>>32, wts&0xffffffff)` (辞書順 = 数値順、int64 超過を避ける)。emit は commit 確定後 (writePhase 直前) と read-only commit 経路の両方。read-own-write・update による read set の扱いを明記。
**(P3)** verifier の production code は変えない (共通書式で読める)。「検査器側の読み込み」は Cicada 形の fixture trace テスト (初期版写像・read-only の古い snapshot 読み・lost update / write skew の巡回) を `orchestrator/tests/` に足して担保する。
**(P4)** 壊し patch は無マクロの無条件 patch 2〜3 本 (例: 古い版を読んで commit、rts を更新しない、read set 再検査を飛ばす) を instr patch の上に重ねる。条件 gate を通らない経路 (マクロ build をしない) なので gate 登録は不要。発火診断 (reached/changed/committed を stderr へ 1 行) を付ける。
**(P5)** 範囲外: 範囲読み取りの phantom、insert/delete、INLINE_VERSION_OPT/PROMOTION 有効ビルド (既定 0。D1464 は「内部の版昇格 write を workload write と区別して見せる」を要求するので、区別を実装しない代わりに TRACE=1 かつ昇格経路が compile される組合せを `#if TRACE` 内の `#error` で fail-closed にする案を攻撃対象とする)、certified 化 (X/P 相当の証拠面の設計)。

**進め方:** DW-G01 に従い段 5 の先頭で生死確認 1 job (stock Cicada + instr patch、1/4 thread) を行い、verifier が framing violation 0 で verdict を出すまで壊し patch を作らない。不成立なら事実を返して止める。

**不変条件:** 規律 2 (verifier・parser・条件 gate・既存 protocol の判定を変えない、壊し patch を baseline に混ぜない)。規律 1 (変更は `#if TRACE` 内だけ、性能値を取らない、TRACE=0 の preprocess 同一性 / objdump 同一性で確かめる)。gitlink を動かさない。仮想リスク向けの gate・台帳・一般化を足さない。テスト全体 5 分上限。

**成果物:** `patches/instr-cicada-trace*.patch`・`patches/broken-cicada-*.patch` + `patches/README.md` 節 (親)、`orchestrator/tests/` の fixture テスト、repo 外起動器 (job dir)、insight `output/insights/2026-09-29/vhash-cicada-verifier/README.md`、worklog / decisions fragment。

**分割 (段 5):** 単位 A = patches/*.patch + repo 外起動器 (Codex author)。単位 B = orchestrator/tests の fixture テスト (Codex author)。所有は素集合。

**計算:** 生死確認 1 job ≈ 3 分、本走 (build 3〜4 本 × cell 2〜3) 2 job ≈ 10 分、焦点走・受入・変異 matrix を含め合計 ≈ 1 node 時間の見込み (< 2)。

**実測環境:** Pegasus 計算ノード、`tools/pegasus/dispatch_compute.py --task generic` を計測用 detached worktree から。受入は `tools/dev_wave_wait.py acceptance --lease-optional`。
