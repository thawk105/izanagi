## 変更内容 (file ごと、sha256 付き)

U1 計装は F から **3 file、計 103 行の追加**です。変更と新規作成は指定された `R` 配下に限りました。

| file | 内容 | sha256 |
|---|---|---|
| [trace.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/include/trace.hh) | gate file、Q/V 出力、pending txid、刻印の境界検査 | `6a4b42afb84cb907c681a4d7f9dbe57b0148d95a23f90d0a987cab565a2e7c6e` |
| [ycsb.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/include/ycsb.hh) | R/W/M 手順と刻印、retry 時の破棄、commit 後の Q | `0d02047f5ed05efa47678adfd2380680fafb896d47c92511a8e589c80c4a8923` |
| [transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/cc/silo/transaction.cc) | Silo YCSB/v2 の有効化と txid 受け渡し、UPDATE 直前の V | `f2d21f8e02802efd1dd9e9e6c13be02af7b514a95b81f083aa3939ac87541cb3` |
| [commit-msg.txt](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/commit-msg.txt) | trailer なしの英語 commit message | `b7457cf0e29d49357960a5ed9428fd62388fee1a4e933b4d0e60726a54437f7f` |

## 計装の配置

[trace.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/include/trace.hh:79) に `gate_<thid>.log` と Q/V emitter を置きました。刻印は同 file の 107 行で `thid < 0xFFFF` と `seq < 2^48` を書込み前に検査します。[ycsb.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/include/ycsb.hh:115) は retry 直後に手順と pending txid を破棄し、203 行で Silo 有効時だけ Q を出します。[transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/cc/silo/transaction.cc:612) は YCSB/v2 の C 行で txid を渡し、703 行で `memcpy` 直前の値を V に記録します。

追加した `#line` は `ycsb.hh` の **17、108、109、127、132、142、166** です。V は `transaction.cc` の既存 `#line 658` より前に置きました。

## TRACE=0 同一性・format・id_ 読み手・login 実走の結果

- **TRACE=0 同一性は未確認です。** `cc/silo/ycsb_silo.cc`、`cc/mocc/ycsb_mocc.cc`、`cc/tictoc/ycsb_tictoc.cc` の `g++-11 -E -DTRACE=0` は各 rc=1 で、いずれも `gflags/gflags.h` が見つからず停止しました。F と変更後の出力比較には到達しておらず、差分行数は未算出です。失敗後は推測で同一と判定せず、ここで検査を止めました。
- clang-format 14 の CI 対象 **213 file** は、整形後の `check_format_ci.sh` で **rc=0** です。初回は新規行の違反で rc=123 でした。
- 全 protocol の YCSB 経路に対する `rg` では、load 後に `id_` をキーや処理入力として読む呼出しは見つかりませんでした。残る参照は [ycsb.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/include/ycsb.hh:54) の未使用 instance `createKey()`、143・155・169・174 行の TRACE 記録、152・170 行の刻印代入、225 行の初期 load 代入です。
- login での TRACE=1 build、2 thread・1 秒の実走、Q/V と C…E の 1 対 1 照合は**未実走**です。

## patch と起動器・job script

| file | 内容 | sha256 |
|---|---|---|
| [broken-silo-b1-u1.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/patches/broken-silo-b1-u1.patch) | 省略読みと reached/committed 計数 | `afebe882d609dc819b9248357af865e17679c6d9ef1a0989e89975b62bdff628` |
| [stamp-off-u1.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/patches/stamp-off-u1.patch) | `id_` 代入 2 か所だけを除去 | `1326ac312db8c819dc408ce610483b96c0aa50cafab18977359b6b3dd690ab4a` |
| [gate_check_u1.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/gate_check_u1.py) | Q の `-` を受け、枠との不一致として扱う診断版 | `05ccad0a49a879be842557026c6cdc981f1660fea20f8216d3b64cd22a3cfe14` |
| [launch_gate_liveness_v3.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/launch_gate_liveness_v3.py) | 1 job・1 条件、2 workload、prereg と結果保存 | `9094a578ca064da6a034485c236a951d825e1d4e007675fdd7b8544dc8aaa89b` |
| [run_judge_v3.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/run_judge_v3.sh) | F→U1、GCC 11/12 の D297 | `cb8a7c43de1bb88fd71546227f01cf816f123237bf40d7f89e7744cbd8bef22e` |
| [run_ci_build_v3.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/run_ci_build_v3.sh) | Release 全体 build と YCSB binary ごとの記号検査 | `045ceecdc106849eeef2ec4759d3cd7381a2e2687fe55783496b9dca2ffa0b92` |
| [run_ci_then_judge_v3.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/run_ci_then_judge_v3.sh) | CI と D297 を順に実行し、それぞれの rc を保存 | `9705a609f046cdd2d1c2a42f04eb63a5bd3b0412674ce71d297fce201e82491b` |

一時 U1 commit `aefb15692` 上で、修正案・B1-U1・stamp-off の各 patch を**個別に** `git apply --check` し、すべて rc=0 でした。検査後、clone の HEAD は F `25898d00…` detached に戻し、作業ツリーの変更は指定の 3 file だけです。

## 実走した command と rc

- `git apply --check`／`git apply`（F 版計装 patch）: ともに rc=0。
- `check_format_ci.sh … /usr/bin/clang-format`: 初回 rc=123、整形後 rc=0（213 file）。
- 一時 commit 上の 3 patch の `git apply --check`: 各 rc=0。
- v3 shell script 3 本の `bash -n`: rc=0。Python 2 本の構文 compile: rc=0。
- `g++-11 -E -DTRACE=0`（Silo、MOCC、TicToc の各 YCSB TU）: **各 rc=1**、`gflags/gflags.h` 欠落。
- `git reset --mixed F`: rc=0。commit は残していません。

## 未実走・残る懸念

TRACE=0 の F 対 U1 比較、login の TRACE=1 build・trace 照合、計算ノードの 4 条件、D297、CI Release build と記号検査は未実走です。v3 起動器の production verifier 用 `gate_witness` JSON field 名と `--require-gate-witness` は、同時実装中の CLI と実物で照合する必要があります。所有外の tracked file・docs・repo `patches/` への編集はありません。

## 総括

U1 の計装、使い捨て patch、起動器、job script を配置し、format と patch の厳密適用は確認しました。**TRACE=0 同一性は依存 header 欠落で判定できていないため、U1 を受入済みとは報告しません。**