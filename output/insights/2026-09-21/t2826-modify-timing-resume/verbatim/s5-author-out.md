## 実装した内容

所有する次の 3 ファイルを実装しました。

- `tools/t2826_modify_timing_probe.sh`: 11 セル、環境初期化、node-local 出力、資源・memo file 記録、rc 回収。
- `tools/t2826_probe_plugin.py`: A/B/C 計時、委譲 wrapper、collection-only scheduler、canonical 実行中だけの resolve memo。
- `tools/t2826_modify_timing_aggregate.py`: 有効性判定、R1〜R8、Markdown・JSON 出力、欠測処理。

## 実走した検査 (command と出力の逐語)

すべて rc=0。実行場所は login、範囲は構文・import・関数単位・合成入力です。

```bash
bash -n tools/t2826_modify_timing_probe.sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/t2826r-pycache python3.10 -m py_compile tools/t2826_probe_plugin.py tools/t2826_modify_timing_aggregate.py
```

両 command とも出力なし。py_compile の出力先は `/tmp` です。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools" python3.10 -c 'import t2826_probe_plugin; print("plugin import: PASS")'
```

```text
plugin import: PASS
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools" python3.10 /tmp/t2826r-check-plugin.py
```

```text
delegated/common: return identity and exception identity PASS
HookImpl/_multicall: positional args, modern send/throw, old outcome, zero/double yield PASS
real Path.resolve: first result, cross-pass hit, strict key, uncached exceptions, outside flag, restoration PASS
helper: delegation, records flag success/failure, selection/state CPU boundaries PASS
install/common: registered-object lookup, thread-time global delegation, missing conftest rejection PASS
hook metric identity: stable across worker instance IDs; actual plugin names retained PASS
LIMIT: fake callables/HookImpl; real shard plugin and conftest NOT exercised
```

実装した wrapper、実際の pluggy `_multicall`、実際の `Path.resolve` を呼びました。正常復帰・例外同一性、generator protocol、flag 復元、初回委譲、例外非保存、flag 外の非計測を正例・負例で確認しました。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools" python3.10 /tmp/t2826r-check-aggregate.py
```

```text
positive: 11 valid; R1 residual=0; R4=true; R6 fit/prediction=true; R5=(10,10,0,0) PASS
validity negatives: rc, complete, mismatch, errors, node, A/B/C, digests, report, malformed PASS
R1 negative: residual=-10, median(abs)=10, threshold=2, pass=false PASS
R4 negative: coherent but different cf sample => invalid cf, R5 all n/a PASS
R6: memo/worker branches positive+negative and missing=n/a PASS
missing OUT_ROOT cells: markdown+JSON represent n/a without exception PASS
R8: overlap and missing interval PASS
SYNTHETIC_ROOT=/tmp/t2826r-synthetic-riq5ysg_
```

2 worker の合成標本です。判定関数を stub せず、有効性・R1・R4・R6 の正例と負例を実行しました。

```bash
PYTHONDONTWRITEBYTECODE=1 python3.10 tools/t2826_modify_timing_aggregate.py /tmp/t2826r-synthetic-riq5ysg_ --markdown /tmp/t2826r-synthetic.md --json /tmp/t2826r-synthetic.json --acceptance-root /tmp/t2826r-synthetic-riq5ysg_/external-synthetic
```

出力なし。生成物: [Markdown](/tmp/t2826r-synthetic.md)、[JSON](/tmp/t2826r-synthetic.json)。

## 設計上の判断と限界 (原裁定 §3 / §4 と違えた点があれば理由つきで)

書きかけの runner、A 計器、scheduler、委譲 wrapper、集計骨格を流用し、流用部分も上記検査に含めました。環境・argv、flag 復元、選択中の deselected 帰属、集合照合、欠測判定、集計キー、表出力を修正しました。

- 実登録名は保存し、worker ごとに変わる xdist instance ID を集計キーから除外しました。
- 区間は `perf_counter()`、公開・到着境界は epoch。CPU は大区間だけ取得します。
- state の終端は最後の `_digest` 復帰で取り、その後の処理は shard impl 残りへ計上します。
- R6 の予測判定は本 prompt 指定式に従い、待ちの伸長は別列でも示します。
- memo は成功した実 resolve 結果の再利用だけです。一般的同値性は主張しません。

**本物の shard plugin / conftest では未検証です。** 計算ノードでの実走は不能であり、runner 本体・pytest collection・xdist は起動していません。子の検査は親の実走を代替しません。

## 所有外への波及

所有外 caller・共有 fixture・consumer test の変更は**無し**。`git status` は所有 3 ファイルの追加だけでした。docs・handoff・既存ファイルの編集、`git add` / `git commit` は行っていません。

probe 自身による deselect・skip・hold・verifier・選択結果の変更はありません。既存関数へ委譲し、scheduler は collection 一致検査と失敗通知を残して配布だけ省きます。

## 総括

**実装済み・未実走。** 許可された構文・import・関数単位・合成入力検査は通過しました。実 shard/conftest の配線確認と計算ノードでの本走は親側に残ります。