# [T-139] 代替 X probe — submission receipt (append-only、qsub より前に作成)

事前登録 `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md` §3 が要求する
study identity の凍結値である。**結果を見る前に作成し、全 submission を追記する。**
本 receipt は repo 外に置く — repo 内へ置くと receipt の commit が HEAD を進め、
job の期待 commit 検査と衝突するためである。段 7 で insights へ畳む。

## 1. 期待 commit

```text
85b892ce476064a0953c0a1aa6614bc33a057b85
```

branch = `worktree-dev-wave-t139-alt-x-probe`、
worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe`。
直前に local main `cfda4abe` を `--ff-only` で取り込み済み (incoming 32 件、provenance 違反なし)。

## 2. 凍結 blob の sha256

| path | sha256 |
|---|---|
| `tools/pegasus/probes/t139_positive_control.patch` | `3b9cdf1635c2afdbfa24af2b5e84e841773144147fe0d00c8b5e794817051951` |
| `tools/pegasus/probes/t139_positive_control_probe.sh` | `560bd0d7a70340787504ac77de5f76f6ee649b2af4d31ff3535b4be72c43ff94` |
| `tools/pegasus/probes/t139_positive_control_probe.pbs` | `fe2553720fcde44d3c54671fd2d3a5627575594b60148a4decea6bfc540fce2c` |
| `tools/pegasus/policy.json` | `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac` |
| `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md` | `a01fb93554630bf1d66102bd974f5fd9c6d4ee8fc3ccea7e89955c48ab21f257` |

policy の sha256 は凍結済み rung1 証拠が pin している値と一致する = 共有 policy を変更していない。

## 3. 依存 source

| source | root | pin |
|---|---|---|
| CCBench | `external/ccbench` (submodule) | `d706650cdb31e442bef45b9b4216951d4fb40969` |
| gflags | `/work/1/SFC/tanab/izanagi-thirdparty-deps/gflags` | `e171aa2d15ed9eb17054558e0b3a6a413bb01067` |
| glog | `/work/1/SFC/tanab/izanagi-thirdparty-deps/glog` | `8f9ccfe770add9e4c64e9b25c102658e3c763b73` |
| masstree | `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` | `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38` |
| mimalloc | `/work/1/SFC/tanab/izanagi-thirdparty-cache/mimalloc` | `02a2f5df9d7d46d30263b83832eebeeab62dc5fe` |
| glogtest 系 googletest | `/work/1/SFC/tanab/izanagi-thirdparty-cache/googletest` | `f8d7d77c06936315286eb55f8de22cd23c188571` |

tree SHA は job が `dependency-witness` として raw へ記録する (投入前に親が読める形では
snapshot を作らないため、値の凍結は job 側で行う)。

## 4. qsub の env

```text
IZANAGI_T139_EXPECTED_COMMIT=85b892ce476064a0953c0a1aa6614bc33a057b85
IZANAGI_T139_PREREGISTRATION_RELATIVE_PATH=output/insights/2026-08-05_t139-alt-x-probe/preregistration.md
IZANAGI_T139_DEPENDENCY_SOURCE_ROOT=/work/1/SFC/tanab/izanagi-thirdparty-deps
IZANAGI_THIRDPARTY_SOURCE_ROOT=/work/1/SFC/tanab/izanagi-thirdparty-cache
```

## 5. submission 台帳 (append-only)

| # | request ID | 投入時刻 | replacement-of | 理由 | terminal state |
|---|---|---|---|---|---|
| 1 | `892032.nqsv` | 2026-08-06 (gen_S、投入時 QUE 14 / RUN 48) | — | 初回 (study 1) | `pre_performance_infra_failure` (rc=1、5 秒。`local` 一文内依存による `set -u` 停止。性能値は 1 つも生成されていない) |
| 2 | `892039.nqsv` | 2026-08-06 | study 1 | **study 2** — bytes を直したので事前登録 §6-5 により新しい study | `pre_performance_infra_failure` (rc=3、6 秒。前 job の scheduler 出力が repo root に残り clean-tree 検査が発火。性能値ゼロ) |
| 3 | `892042.nqsv` | 2026-08-06 | 2 の予備置換 (§6-3) | scheduler 出力を repo 外へ向けた。**bytes 不変**なので study 2 のまま | **`verdict_true`** (`exact_primary_verdict_true`) |

## 6. study 2 の凍結値 (bytes 変更に伴う再発行)

**期待 commit: `425ed1908dfd78cda97c48c2b248cdf6b83b1e91`**

| path | sha256 |
|---|---|
| `tools/pegasus/probes/t139_positive_control.patch` | `3b9cdf1635c2afdbfa24af2b5e84e841773144147fe0d00c8b5e794817051951` (study 1 と同一) |
| `tools/pegasus/probes/t139_positive_control_probe.sh` | `9e19b92eecc951fa011b11f4b1bad72f07b23a3e0a519299ea26accb2967ed92` |
| `tools/pegasus/probes/t139_positive_control_probe.pbs` | `e2838fa2fac85f205453380105d4c9e91a6ff500a13f00ba858f957f2113ad1e` |
| `tools/pegasus/policy.json` | `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac` (不変) |
| `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md` | `a01fb93554630bf1d66102bd974f5fd9c6d4ee8fc3ccea7e89955c48ab21f257` (不変) |

**事前登録の内容 (候補・受理条件・schedule・閉表・分岐) は 1 文字も変えていない。**
変わったのは shell の宣言 4 行だけであり、study 2 は study 1 と同じ問いに答える。
依存 6 source の root と pin も §3 から不変である。

**規則:** exact verdict (true / false) が出たら終端で retry 禁止。性能 run 開始前の infra failure に
限り、結果を見る前に外部証拠で確定した場合のみ予備 1 本まで置換可。全 ID をここへ残す。
