## 推奨案と確認した前提

**既存 late self 照合の直後、`status` 決定の前に、凍結 pre → post の canonical 比較を追加する。** 失敗は既存 `reasons` 経路へ流し、比較入力の診断は attempt staging にだけ保存する。編集対象は `cli.py` と `test_calibrator_certify.py` の 2 ファイルとする。

以下の行番号は現在の実ファイル基準。brief の番号にはずれがあり、post 取得は `cli.py:1006`、status 決定は `:1017`、publish 後再読は `:1079` である。

また、依頼にある「fixture の `tolerance_pct=100.0`」は現在の内容と一致しない。`_pegasus_shaped_probe` は tolerance を持たない observed profile を返し、CLI が policy の `2.0` を焼く。`100.0` は旧 CLI override の拒否テストにだけ現れる（`test_calibrator_certify.py:1570`）。既存 fixture を変更してこの前提に合わせることはしない。

## 1. 挿入位置と制御フロー

挿入点は [cli.py:1017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/cli.py:1017) の**直前**。`:1015–1016` の self 照合を残し、概念上次を追加する。

```python
expected_clock = {
    "samples_mhz": profile["effective_clock"]["samples_mhz"],
    "tolerance_pct": profile["effective_clock"]["tolerance_pct"],
}
observed_clock = {
    "samples_mhz": static_post["effective_clock"]["samples_mhz"],
}
if not effective_clock_comparison_passes(expected_clock, observed_clock):
    reasons.append("effective-clock-post-comparison-failed")
    # この比較入力の診断を staging に保存する
```

canonical 述語は既に `cli.py:47–50` で import 済み。clock 全体には `method` 等があるため、丸ごと渡さず上記の key 集合へ射影する。`execution_guard.py:368–379` は expected 2 keys、observed 1 key を要求する。

制御フローは次のままになる。

1. benchmark 完了 `:991–1003` → post 取得 `:1006` → static 比較・isolation・品質判定 `:1007–1014`。
2. 既存 self 照合 `:1015–1016` → **新比較** → `status = "accepted" if not reasons else "rejected"` `:1017`。
3. rejected artifact と report を staging に保存 `:1018–1032`。
4. rejected なら `:1033–1035` で非 0 終了。
5. accepted の場合だけ registered 準備、policy 同一性検査、publish `:1067`、公開 bytes 再読 `:1079` へ進む。

したがって新比較の拒否は、registered ディレクトリ作成よりも前に停止する。publish の位置・順序、公開後の検査、公開物の削除規則を変更しない。

## 2. post observed clock の供給源

**既存 `static_post["effective_clock"]["samples_mhz"]` で足りる。追加 probe は不要。**

根拠は以下。

- `cli.py:1006` は `calibrate_fn` の完了後に取得する 3 回目の profile。
- `_profile_dict`（`:479–483`）は observed profile の dict 化経路を使う。
- [schema_v2.py:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/schema_v2.py:243) の `ObservedEffectiveClockProfile` は、非空の正数標本列・method・governor を持ち、tolerance は持たない。
- [execution_guard.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/campaign/execution_guard.py:324) の canonical 述語に必要な observed 入力は標本列だけ。
- 既存 `_static_profile_bytes`（`cli.py:515–519`）は `effective_clock` を削除する。`:1007` の比較では今回の穴を塞げない。

expected は `cli.py:877–882` で dynamic pre を deepcopy し、実測 TSC と開始時 policy を焼いた **`profile`** とする。最初の `static_pre` や post の中央値・policy へ置き換えない。

## 3. reason code と既存 reason との関係

新 reason は **`effective-clock-post-comparison-failed`** とする。

| 既存 reason | 判定対象 | 新 reason との関係 |
|---|---|---|
| `effective-clock-self-comparison-failed` | 凍結 profile 自身。`cli.py:745–746`、`:1015–1016` | 名前・入力とも異なる |
| `post-attestation-mismatch` | clock を除いた static profile。`report.py:127–128` | clock 不一致を含まない |
| `effective-clock-policy-changed` | publish 直前の policy 同一性。`cli.py:1044–1053` | 別の検査時点・目的 |

`report.py:87–129` と `_acquisition_reasons`（`cli.py:707–749`）に同名 reason はない。policy が benchmark 中に変わった場合は、既存 self と新比較がともに失敗し、両 reason が出る可能性がある。これは原因の重なりであり、既存 reason を消したり統合したりしない。

`schema_v2.py:473–482` は reason の列挙型ではなく文字列リストを検証するため、新 code のための schema 編集は不要。`CertificationEvidence`（`model.py:223–231`）への field 追加も不要。

## 4. 拒否成果物と D191 の射程

[D191:13–15](/home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D191.md:13) は明示的に「**early 拒否の成果物には**」と限定している。さらに `:36–37` は benchmark 後 clock を対象外としている。したがって、**決定 5 が今回の late 拒否へ直接適用される、とまでは逐語から言えない。**

ただし `:28–29` の「導出値だけでは再計算できない」という理由は今回にも当てはまる。brief `:71` が許す任意の診断として、**新比較の失敗時だけ**自己完結する sidecar を残す案を推す。

保存先は `cli.py:831–834` の staging 配下：

```text
attempts/<safe-job-id>/effective-clock-post-comparison.json
```

新比較の失敗分岐内、`:1017` より前で、既存 `_write_exclusive`（`:302`）を使用する。内容は次に限定する。

- `passed: false`。
- 凍結 `attestation_profile` 全体、その SHA-256、既存 canonicalization 識別子（`:90–92`）。
- canonical 述語へ渡した `expected` と `observed` の実入力。
- `effective_clock_comparison_diagnostics(expected, observed)` の診断値。**受理判断には使わない。**

hash は既存 `_canonical_json_bytes`（`:522–526`）で計算する。新 helper・台帳・schema validator は作らない。

通常の late 拒否では既存経路が `calibration.json`、`calibration.md`、`window-probes.json` を残す（`:1021–1032`）。この経路は例外を投げず return するため、`rejection_diagnostics` に代入するだけでは保存されない点に注意する。

early 拒否の未評価一覧（`cli.py:75–86`）には `pre-post-effective-clock-comparison` を追加し、新検査も未実施だったと記録する。late 拒否に early 用一覧を流用しない。

## 5. published bytes の影響

[cli.py:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/cli.py:752) の `_assemble_v2` は `profile`、receipt、genome、quality を組み、`:770` で全体を JSON bytes にする。

| 案 | schema・bytes への影響 | 判断 |
|---|---|---|
| calibration artifact に post／比較結果 field を追加 | top-level、profile、quality は exact keys（`schema_v2.py:553–569, 776–790`）。現状では拒否される。schema を拡張して accepted に書けば bytes・hash が変わる | 不採用 |
| artifact に field を追加せず、失敗 reason と staging sidecar のみ追加 | 合格時の `_assemble_v2` 入力と serialization が同じ。拒否時だけ quality と staging 成果物が変わる | **採用** |

合格時は `profile`、result、receipt、`reasons` を変更しないので、**同じ既存入力に対する published bytes を維持できる**。既存登録 artifact や pin の更新は発生しない。

## 6. テスト設計と変異 matrix

既存 helper `_pegasus_shaped_probe`（[test_calibrator_certify.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/tests/test_calibrator_certify.py:253)）、`_expect_48_physical_cores`（`:286`）、`_invoke`（`:379`）、`_fake_calibrate`（`:367`）をそのまま使用する。

新 gate だけが落とす主要負例は、次の 3 行を probe に渡す。

```python
sample_rows = [
    [2101.0] * 47 + [2095.0],  # static pre
    [2101.0] * 47 + [2110.0],  # dynamic pre → 凍結 expected
    [2101.0] * 48,            # post。ここだけ変更する
]
sample_rows[2][outlier_index] = 3079.456
```

`outlier_index` は `[0, 24, 47]`。凍結 pre の中央値は 2101、2% 帯は 2058.98–2143.02 MHz なので、2110 を含む pre 全標本は帯内であり、early／late self は通る。post の 1 標本だけが帯外となる。static 項目は同じなので既存 static 比較も通る。

期待する検証内容：

- probe 呼び出しは `[0, 1, 2]`、benchmark stub は 1 回実行。
- `quality.reasons == ["effective-clock-post-comparison-failed"]`。
- staging の rejected v2 artifact は schema valid、pre 標本と tolerance は元のまま。
- registered は未作成、publish receipt と公開後 self receipt は未作成。
- sidecar だけから profile hash と canonical 判定を再計算できる。

追加する正例・変異対策は以下。

| テスト入力・確認 | 捕捉する誤実装 |
|---|---|
| 既存 `:1287` の 3 種の帯内標本を維持して成功 | 新 gate の恒偽化、probe 追加 |
| post を `[2300.0] * 48` にする。post 自身の self は通るが pre→post は落ちる | post 自己照合への取り違え、expected の post 上書き |
| static pre を `[2300.0] * 48`、dynamic pre／post を `[2101.0] * 48` にして成功 | expected に static pre を使う誤り |
| post に低側の帯外値を 1 個置く | 上側だけの検査 |
| 帯外 post と `bad_cv=True` を組み合わせ、両 reason を保持 | 新 gate による既存 reason の上書き |
| canonical 関数を実関数へ委譲する spy で expected／observed を記録 | self 入力の再利用、canonical 経由の欠落 |

accepted bytes は、親が変更前の決定的 fixture の bytes／SHA-256 を取得し、変更後と一致させる。さらに post だけを別の帯内標本に変えた 2 attempt で公開 bytes が同一であることを検証する。これにより post 情報が artifact に混入していないことを確認する。

既存 early 未評価一覧のテスト定数（`:34–45`）だけは新検査名を加える。48 標本・3 回取得・tolerance-free probe の形は変えない。

## 7. 編集対象と行数見積り

| 編集対象・現在の行 | 内容 | 編集行数の目安 |
|---|---|---:|
| `orchestrator/calibrator/cli.py:81` 付近 | early 未評価一覧に新比較名を追加 | 1 行 |
| `orchestrator/calibrator/cli.py:1017` 直前 | canonical 比較、reason、失敗時 staging sidecar | 35–50 行 |
| `orchestrator/tests/test_calibrator_certify.py:40` 付近 | 未評価一覧の期待値更新 | 1 行 |
| `orchestrator/tests/test_calibrator_certify.py:1153` 付近 | 正負例、入力取り違え、診断再計算、bytes 回帰テスト | 180–240 行 |

合計は約 217–292 行。`report.py`、`model.py`、`schema_v2.py`、canonical 述語、policy 定数は編集しない。

## 8. 最も弱い点と検証状況

最も弱い点は **D191 決定 5 の射程解釈**。決定本文は early に限定する一方、理由の段落は「拒否成果物」と広く書いている。late にも同じ再計算要件を求める解釈はあり得る。そのため推奨案では、義務の拡張とは断定せず、失敗 sidecar に preimage と実入力を残して実質的な再計算可能性を確保する。

確認は静的読解のみ。ファイル変更、git 操作、pytest 実走は行っていない。

## 総括

- **推奨：late self 直後・status 決定前に canonical pre→post 比較を追加し、失敗 reason と staging 診断を残す。** calibration schema と合格 artifact bytes は変更しない。
- 編集箇所：`orchestrator/calibrator/cli.py:81,1017`、`orchestrator/tests/test_calibrator_certify.py:40,1153`。
- 最も弱い点：D191 決定 5 を early 限定と読む解釈。ただし推奨 sidecar は late 拒否の hash・判定再計算も可能にする。