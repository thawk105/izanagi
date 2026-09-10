## 総括

[probe 本体](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-probe/orchestrator/campaign/t2224_producible_protocols_probe.py)を作成しました。既存ファイルは変更せず、commit・push もしていません。

実行形式:

```bash
python3 -m orchestrator.campaign.t2224_producible_protocols_probe --out <dir>
```

## probe の構造

- whitelist にある protocol ごとに `configure → 軸到達 → build → trace 分離 → genome 導出` を記録。
- 各段を厳格に赤/緑判定。
- `reached` は先頭から連続して緑だった最終段。物理的前提があれば、先行段が赤でも後段を実測。
- protocol が赤でも exit 0。launcher parse や probe 自身の失敗は理由を JSON に残して exit 2。
- 最終 JSON は `<out>/t2224-producible-protocols-probe.json` の1本。
- acquisition candidate/receipt は一時配置して writer 通過後に削除し、内容を最終 JSON に収録。
- `--deps-prefix` の既定値は `/work/1/SFC/tanab/izanagi-a2-deps`。

## launcher から読む箇所と parse 規則

[certify_calibration.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2224-probe/tools/pegasus/certify_calibration.sh:162)から以下を読みます。

- 163–169行: `CALIBRATION_PROTOCOL != ...` の conjunction を whitelist として抽出。
- 546–575行: protocol ごとの `ccbench_define_argv=(...)`。各要素を `-DCCBENCH_<AXIS>=<整数>` として厳密解析。
- 576–581行: configure が define 配列をちょうど一度展開することを確認。
- 589–593行: `build_argv` から唯一の `--target ycsb_<protocol>.exe` を抽出。
- 596行: `BINARY` 式を、`BUILD_DIR`、`CALIBRATION_PROTOCOL`、`build_argv[index]` だけ許可して評価。
- 645–729行: acquisition candidate の field 構造と、`shlex.split(configure_text) + ["&&"] + shlex.split(build_text)` の規則を踏襲。

whitelist、define case、build case の protocol 集合が一致しなければ fail-closed です。

## 実走した検査

- `python3 -m py_compile`: rc=0
- module の `--help`: rc=0
- trailing whitespace 検査: 問題なし
- `cmake`、build、`nm` は login node では未実走

既存の5ファイルにあった未コミット変更には触れていません。

## 測れないこと (probe の射程外)

- 2時間の較正計測本体
- `registered/calibration-*.json` の発行可能性
- submit launcher から PBS job までの全伝播
- condition meaning gate の成否
- full acquisition admission。測るのは既存 writer の schema 通過と canonical genome 導出まで
- 各 protocol の実際の赤/緑結果。これは親による計算ノード実走後に確定します。