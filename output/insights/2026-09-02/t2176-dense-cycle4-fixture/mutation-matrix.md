# 変異 matrix — [T-2176] clean な長さ 4 巡回の負例

harness は `tools/mutation_harness.py`、`--runner-mode dispatch`。本 wave は production 差分 0 の
**テスト強化だけの wave** なので、`DW-M08` に従い**変更前 HEAD の木**と**変更後の木**の双方へ
同じ変異を当て、新テストだけが検出する差分を示す。

## 走らせた 2 アーム

| アーム | repo HEAD | 木 |
|---|---|---|
| before | `24b31d2a37353d63a4f715ed2170d13e25df3fe3` | 新 fixture と新テストが無い状態 |
| after | `dd43f92e2cc277d2f3d9ae9dbe8a60c3221f9c32` | 新 fixture と新テストを足した状態 |

spec は `mutation-before.json` / `mutation-after.json`。変異位置はいずれも
`orchestrator/verifier/dsg.py` の `DSG.anomalies`。

## 分母と、そこから外した 97 node

分母は verifier を参照するテスト 17 file、1562 node。そのうち **97 node を deselect した**。
理由は次のとおりで、根拠は本 wave の probe 走の実測である。

`orchestrator/campaign/campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` は
`orchestrator/verifier/dsg.py` を **disk bytes と HEAD blob の一致**で束縛する。変異 harness は
commit せずに disk を書き換えるので、**dsg.py を 1 byte でも変えると**
`IdentityMismatch: contract-loader-drift: disk bytes が HEAD blob と不一致` が発火する。

probe 走で観測した失敗 node 集合は次のように入れ子だった。

- M3 (等価変異、挙動は不変) … 97 node が赤。全件が `contract-loader-drift`。
- M1 … 99 node = 上の 97 + `test_verifier.py` の 2 件。
- M2 … 98 node = 上の 97 + `test_verifier.py` の 1 件。

M3 の 97 node は M1・M2 の**部分集合**であり、M1・M2 で赤くなって M3 で赤くならない node は
`test_verifier.py` のものしか無かった。つまりこの 97 node は「壊した変異」と「何も変えない変異」を
区別できない。絶対規律 7 が「弱体化の検出は同一性でなく挙動で行う」と定める理由の実物であり、
D1422 / worklog 1176 が別の分母で測った現象を本 wave が再現したことになる。

deselect は 86 個の node id と 2 個の関数名 (parametrize された 11 node を含む) の計 88 引数で行い、
`--collect-only` で **1465/1562 (97 deselected)** になることを確かめた。

## 結果

| 変異 | 内容 | before の期待/実測 | after の期待/実測 |
|---|---|---|---|
| M1-drop-len4-unconditional | 最短巡回長 4 以上の SCC を報告と `total` から**無条件に**落とす | KILLED / KILLED | KILLED / KILLED |
| M2-drop-len4-when-clean | 同じ処理を `self.integrity.clean()` が真のときだけ行う | **SURVIVED** / **SURVIVED** | **KILLED** / **KILLED** |
| M3-equivalent-sort-key | `sccs.sort(key=len)` → `sccs.sort(key=lambda comp: len(comp))` | SURVIVED / SURVIVED | SURVIVED / SURVIVED |

両アームとも baseline は PASSED (失敗 0)、`matching` は 3/3。

失敗 node の実測値。

- before / M1 … `orchestrator/tests/test_verifier.py::test_nonlatest_read_caught_via_ww_transitivity`
- after / M1 … 上に加えて `orchestrator/tests/test_verifier.py::test_dense_cycle4_clean_g2`
- after / M2 … `orchestrator/tests/test_verifier.py::test_dense_cycle4_clean_g2` **のみ**

## この matrix が示していること

1. **M2 は既存スイート全体を素通りしていた。** 変更前の木では、verifier が clean な入力の長さ 4 の
   巡回を落として `certified=True` を返すようになっても、分母のどのテストも赤にならなかった。
2. **新テストがその穴を単独で塞ぐ。** 変更後の木で M2 が殺され、赤くなったのは新テスト 1 件だけである。
   既存テストが先に殺しているのではない (反実仮想として M2 が before で SURVIVED であることが示す)。
3. **新テストは何でも赤にする恒真な assert ではない。** 挙動を変えない M3 では赤にならない。
4. **M1 との対で射程が見える。** 無条件版 M1 は変更前から既存の r5 テストが殺していた。
   M1 だけを見て「この穴は既に塞がっていた」と読むのは誤りで、r5 が担っていたのは
   `non-serializable` というグラフ事実の検出までである。r5 は `missing_txids=46` で integrity が
   unclean なため、certified へ倒れる経路そのものは担っていなかった。M2 がその区別を分離する。

## 再現

```
python3 tools/mutation_harness.py \
  --repo <木> --spec <spec> --expected-spec-sha256 <sha> \
  --out <out> --attempt-out <attempt> --wrapper-attempt 1 \
  --runner-mode dispatch --detached \
  -- python3 tools/run_tests.py --force-dispatch -rf -p no:cacheprovider <17 file> <88 個の --deselect>
```

spec の sha256 は `mutation-after.json` =
`d937d20735dd3c1b920c401fb3090759a58004dd24f62c6f791d7b14c353e281`、
`mutation-before.json` =
`6e8e280ed89e535f56cf96c29b6fccad9d603f3e50bc2f7f1a517984fb3d2d51`。
