## 作った file の一覧

すべて [output/runs/moccfix-b/tools](/work/1/SFC/tanab/izanagi/.codex/worktrees/moccfix-b/output/runs/moccfix-b/tools) 配下です。SHA-256 は最終状態で取得しました。

| file | 役割 | SHA-256 |
|---|---|---|
| `mocc-g2-probe-F.patch` | F 用計器 | `cf9a62f5f60d5141e1e7c0218dda6023576616b22602de171466b24989a19c2b` |
| `mocc-g2-probe-X.patch` | X 用計器、再読 abort 計数 | `6df9e83356922fd89c5575f7b38516067eca6fa413bb920ef027140cbad20464` |
| `moccfix_probe.py` | 6 arm runner、join、判定 | `e0c620edf4d60583f39482d4bf8afcf9cf14d0443777ae6f9ebc4222f55380d5` |
| `arms-moccfix.json` | arm・source OID・patch 定義 | `09551de6cbd2c9716aae22776abd7eb5be927e0f9bfc2dd603fb9a2a118acc83` |
| `smoke-launch.sh` | 1 batch 投入 | `dd2e617dd50549e33cf8cb9086eb99fe45413367af68ecdcd73e02d91f58ec67` |
| `main-a-launch.sh` | 本走 job A 投入 | `8f2a8d34cf8f15ce70631934a82e97aa7228cec7183695ecd21b1c53855713f4` |
| `main-b-launch.sh` | 本走 job B 投入 | `9057e09d1f29566fc10efc168086b2368e76b7f102e3065fedd2bea2cad96dd4` |
| `run_ci_build.sh` | F 親固定の CI image build 本体 | `56fe18d4e672d99813949176fba3ded97b194acf62151b4d2d0aeaa4cbc09a9d` |
| `ci-build-launch.sh` | CI build 投入 | `4ed86f4b0e6ffdb9ab4daac812f250278330a55000230b67606ef0bbb4ad334c` |
| `run_judge.sh` | F→X の D297 判定本体 | `ae05e404e6c97710ac67fe8815a58faa681c3f32945c9bf60b049311d75d5629` |
| `judge-launch.sh` | D297 投入 | `4470e0b4e5904ac36a28137525eac569cde1ebf0554eb46b80be3445e0b90d5` |

## 検査の実走結果

- template 適用済み F/X の別展開木で `git apply --check mocc-g2-probe-{F,X}.patch`：**両方 rc=0**。
- `g++-11 -E -P`、`RWLOCK`・`TRACE=0`・計器 off、依存 include と source path の prefix 正規化を指定した近似比較：**F の P/N 相当、X の P/N 相当とも `cmp` rc=0**。
- `python3 -m py_compile .../moccfix_probe.py`：**rc=0**。
- `python3 .../moccfix_probe.py selftest`：**8/8、rc=0**。
- `bash -n .../tools/*.sh`：**全 7 本 rc=0**。

## 親が実行する手順

親が `tools` を repo 外へ写した後、以下の変数に実際の絶対パスを設定してください。job A/B は別 checkout から投入します。

```bash
T=<repo外へ写したtoolsディレクトリ>
W_A=<job-Aのizanagi-checkout>
W_B=<job-Bのizanagi-checkout>
C=<FとXを含むCCBench-clone>
B=<Xをheadとするbundle>
X=f4a5169ede52630d9357444e3412ffe9aed7c78f
SIF=<照合済みCI-ci-image>
CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache
PREFIX=/work/1/SFC/tanab/izanagi-a2-deps

bash "$T/smoke-launch.sh" "$W_A" "$T" "$C" <smoke-output> <smoke-scratch> <walltime> "$CACHE" 48
bash "$T/main-a-launch.sh" "$W_A" "$T" "$C" <main-a-output> <main-a-scratch> <walltime> "$CACHE" 48
bash "$T/main-b-launch.sh" "$W_B" "$T" "$C" <main-b-output> <main-b-scratch> <walltime> "$CACHE" 48

python3 "$T/moccfix_probe.py" join \
  --input-dir <main-a-output> --input-dir <main-b-output> --output-dir <joined-output>

bash "$T/ci-build-launch.sh" "$W_A" "$T" "$B" "$X" "$SIF" "$CACHE" /scr <ci-output> <walltime>
bash "$T/judge-launch.sh" "$W_A" "$T" "$B" "$X" "$CACHE" "$PREFIX" /scr <judge-output> <walltime>
```

本走前の費用判定には smoke の `builds.json` の `fixed_cost_seconds` と batch の `benchmark_seconds`・`verify_seconds` を使用します。format は親の実施済み [format-ci-X.log](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/format-ci-X.log) を記録に用います。対象 argv は `git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$' | xargs clang-format --dry-run --Werror` です。

## 未実走・近似の範囲

build・benchmark・verifier・dispatch・D297 本判定は実行していません。前処理一致は実 build の `compile_commands.json` を使わない近似です。runner は実走時に各 arm の source を照合し、同一 commit 内の macro off 前処理一致を再検査します。

## 総括

指定の使い捨て計器、6 arm runner、投入 script、CI build、D297 判定を作成しました。結合後の `summary.json` は、**2 job × 14 batch の充足、R0、T_X の G2、T_X＋N_X の commit 側 class A** を機械判定し、F 側対照と X の `recheck_abort` を別に報告します。