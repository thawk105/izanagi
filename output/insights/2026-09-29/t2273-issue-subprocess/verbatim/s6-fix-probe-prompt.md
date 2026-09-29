単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2273-issue-subprocess

作業木 (あなたが書いてよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-probe (branch fix-t2273is-probe-1)
所有 path (これ以外を編集しない): 作業木内の `probe-t2273is/` の下だけ (repo の tracked file は 1 byte も変えない。使い捨ての計測 probe)。
docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s4-ruling.md — 計測の事前登録と **erratum E1' (仕様の正本)**。
- /work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/codex/s6-e1-consult-common.md、s6-e1-pro-out.md、s6-e1-con-out.md — 経緯と賛否。
- 作業木の probe-t2273is/t2273is_ab_analyze.py (`e1_pair_check`、`pair_metrics`、`analyze`、`markdown`)、t2273is_run_series.sh (投入前検査が analyze を呼ぶ)。

**計測値 (/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/runs/ 以下) は読むな・走らせるな。** 検査は合成入力か前 wave の系列の読み取り専用コピーで行え。

## 作ること (erratum E1' の実装。他の挙動・有効性条件・判定量・門番・台帳は変えない)

1. `e1_pair_check`: 共通 node の割付一致の要求を shard-0 だけにする。shard-1・shard-2 の一致/不一致は無効理由にせず、診断 field (例 `e1_full_shard`: 旧 E1 の成否と各 shard の不一致件数) として対の結果に残す。collection 差の条件は不変。
2. 結果 JSON と markdown に、旧 E1 (3 shard 全一致) で判定した場合の land 区分を `undetermined` 等として並記する field を足す (旧 E1 が全対で成立していればその区分)。改訂 E1' による land 区分・5 分判定は既存の計算のまま。
3. 各走の 3 shard の実行 host (既存の hostname 記録) を対ごとに並べ、同じ host に 2 shard 以上が載った走があれば数を出す (判定には使わない)。
4. W_1・W_2・pre の対差の見出し・注記を「shard の test 集合が A/B で異なるので実装効果として読まない」旨に変える (値の計算は残してよい)。
5. 同一条件内の走同士の E1 (analyze 内の `same_condition` の比較) は変えない (同じ木の走同士は 3 shard 全一致のはず)。

## 検査

- `python3 -m py_compile` を全 .py に、`bash -n` を全 .sh に。
- 前 wave の系列 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/runs/` と同 job dir の `expected-added-nodes.json`・`measurement-tips.json`・`input/` を**読み取り専用で**作業木内の一時 dir に写して集計器を走らせ、前 wave の値 (対差 +55.355 / +46.001 / +47.740 秒、中央値 12.7 %、区分 land、5 分 not-met) が変わらず、旧 E1 の並記も成立 (全 shard 一致) を示すことを確かめる。**移植元の job dir へは書かない。**
- 合成入力で「shard-0 一致・shard-1/2 不一致」の対が有効になり、「shard-0 不一致」の対が無効になることを確かめる (最小の fixture を一時 dir に作ってよい)。

## 報告

見出し「## 修正」「## 検査」「## 未実走・懸念」「## 総括」。「## 総括」は 5 行以内。
