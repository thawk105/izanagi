# [T-541] + [T-507] — 資格判定 driver の attestation 成功経路を到達可能にした

2026-09-16。wave `t541-t507-attestation`、branch `worktree-dev-wave-t541-t507-attestation`。

## 何が起きていたか

資格判定 (T126) driver の環境 attestation は、**2 層の型不整合で成功経路へ一度も到達していなかった**。

| 層 | 実装 | 何が起きるか |
|---|---|---|
| 1 | `compare_profiles` の expected に `verified.calibration` (`CalibrationV2`) を渡していた | `AttestationError: expected が AttestationProfile でない` |
| 2 | 観測側 hash に `profile_sha256(observed)` を使っていた (expected 専用の関数) | `AttestationError: profile が AttestationProfile でない` |

層 1 は [T-507] として 2026-08-05 に記録済み、層 2 は [T-541] として 2026-08-05 に新たに確認された。
どちらも 2026-08-25 の /rulings で択 (a)（2 層とも直す・記録の版を上げる）が採用されていた。

**親が着手時に実データで両方を再現した** (login node、2026-09-16)。

## 直した内容

- 層 1: expected を `verified.calibration.attestation_profile` にする。
- 層 2: 観測を `observed_profile_to_dict` で dict 化し、exact 4 key の
  `pegasus-probe-output/v2` 文書へ落として既存 `parse_probe_output` に通し、
  既存 `observed_profile_sha256(parsed)` を使う。比較の observed 側も同じ parser 復元値にした。
- envelope を `t126-qualification-attestation/v2` へ上げ、exact 6 field にし、
  `observed_profile_projection_schema` を **parser の戻り値から** 記録する。

**判定条件は 1 つも変えていない。** `_recorded_verdict`、tolerance、比較 field 集合、
全行 pass 要求、非空要求はすべて維持した。広げたのは「型が合えば比較が実行される」ところまでである。

## 完了条件の実測 (計算ノード)

`attest.sh` (NQSV gen_S) で `_attest` を 1 回直接呼んだ。**逐語は `attest-861.stdout.json`。**

- Request `861.nqsv`、host `bnode005`、実行 7 秒 (13:15:19〜13:15:22)
- commit `dcace0db9b018df8314d4250f2b417edfa23ea9f`
- 較正 `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`
  (contract `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`)
- **`status: accepted`**、`schema_version: t126-qualification-attestation/v2`、
  `observed_profile_projection_schema: pegasus-probe-output/v2`
- **comparisons 21 行すべて `pass`**
- `expected_profile_sha256 = 1849e6cc169a1033…`、`observed_profile_sha256 = 241a0b954513f2d5…`

**この 1 回が証明するのは、実 probe と登録済み較正から `_attest` が payload を返す到達性だけである。**
fork 経由の evidence 保存、資格試行の完走、certified 選択の成立は含まない
(T126 result は `evidence-only/no-promotion`)。

### 測定環境の差 (login node との対比)

login node では同じ較正に対し 6 field が **正当に** fail する
(`cores.logical` / `cores.smt_active` / `cores.affinity_visible` / `cache_topology` / `numa` /
`effective_clock.samples_mhz`)。login は 96 論理コア・SMT 有効、較正は 48/48・SMT 無効である。
**型の問題ではない。** 計算ノード (gen_S は CPU 48/48 固定) で初めて全 21 field が一致した。

## 境界テスト

現挙動 (一致入力も型不整合で拒否する) を保存していた
`test_t452_attest_preserves_intentional_fail_closed_behavior` を、実比較・実 parser・実 hash を
通す受理／拒否の境界テストへ置き換えた (`test_t541_attest_*` 8 node)。

入力の `effective_clock.tolerance_pct` は `effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT`
へ揃えた。共有 fixture の 5.0 は現行 policy の 2.0 と不整合で、**その不一致だけで必ず落ちるため
帯判定に到達していなかった**。同型の先例が `test_env_attestation.py` に 2 箇所あり、
policy 外 tolerance を拒否する保護は同 file の既存テストが引き続き固定している。

## 変異 matrix

`mutation-result.json` (repo 外の job dir)。baseline PASSED (41 passed / 6.19s)。
**registered=5 / matching=5 / MISMATCH=0。**

| ID | 変異 | 結果 | 失敗 node |
|---|---|---|---|
| m1 | 層 1 だけ旧実装へ戻す | KILLED | 6 |
| m2 | 層 2 だけ旧実装へ戻す | KILLED | 7 |
| m3 | envelope を v1 へ戻す | KILLED | 1 |
| m4 | projection schema を literal 固定 | **SURVIVED** | 0 |
| m5 | 全行 pass 要求を外す | KILLED | 3 |

**m4 は同値変異である。** driver が生成文書の版を v2 に固定している以上、記録側を同じ literal に
しても出力が変わらない。段 6 のレビュー A が先に指摘し、親が事前登録を `positive` / `SURVIVED` へ
訂正した。**したがって「記録値の由来 (`parsed.schema_version`) への感度」は本 wave の検証範囲外である。**
実装は由来から取る形を維持しているが、それが保護されているとは主張しない。

m1 / m2 を**個別に**戻したのは、2 層同時変異では層 1 が先に拒否して層 2 の欠陥が隠れるためである。

## 段 3・段 6 が正した親の誤り

- **`attestation_records` list が未使用であることから「payload の載る先がない」と一般化したのは誤り**
  だった。`t126_driver.py` は attempt 配下へ保存し、evidence_manifest がその bytes 参照を収録する。
  list が未使用であることと、保存経路が無いことは別である。
- **完了条件に「attempt の evidence として書かれる」まで含めたのは誤り**だった。それは資格試行本走を
  伴い、本 wave の scope を超える。関数の到達性までに限定した。
- **不一致で終わった場合を「比較到達」で完了扱いにする退避案は成立しない**。不一致では payload が
  返らないためである (今回は該当しなかった)。
- **「計算ノードなら一致する見込み」という一般化は過剰**だった。CPU 構成が関係するのは 6 field の
  うち 3 field で、残りは実測するまで未知だった。結果として一致したが、事前に導けた主張ではない。

## scope 外として残したもの

1. **[T-506] / D155 の読み込み側 self-pass gate。** 一次裁定 (2026-08-25) は「同じ wave で扱う」と
   述べていたが、本 wave の起動引数が「2 層修正と記録版上げだけ」と限定した。carry は残る。
2. **拒否時の比較行の保存・伝達。** `t126_driver.py` は mismatch 時に比較行を捨てて固定文言の例外を
   出し、親子間も終了コードだけになる。既存の欠落であり、本 wave は新たな握り潰しを作っていない。
   今回は `attest.sh` 側の観測 wrapper で非 pass 行を出せるようにしたが、これは実測 script 限定で
   恒久 API は変えていない。
3. 計算ノードでも mismatch した場合の較正世代 ([T-419] U-2) の扱い。今回は一致したので発火せず。

## 一次資料

- 実測逐語: `attest-861.stdout.json` / `attest-861.stderr.txt`
- 投入 script: `attest.sh`
- 子の報告: `s5-author.md` (実装)、`s6-fix1.md` (fixture)、`s6-fix2.md` (観測 wrapper)
- 変異結果・段 2〜4・段 6 の逐語: repo 外 job dir
  `/work/1/SFC/tanab/dev-wave-jobs/t541-t507-attestation/`
