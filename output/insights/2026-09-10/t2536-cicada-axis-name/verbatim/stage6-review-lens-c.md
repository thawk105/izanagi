## 所見 C1 — 偽 genome を受理できる

判定: **real / must-fix**

[model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/model.py:112) の未知名 fallback と、[cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/calibrator/cli.py:467) の `missing_axes` が不足だけを調べることの組合せで、余剰 define が無条件に genome へ入る。

全必須軸と正しい `CCBENCH_INLINE_VERSION_OPT_CICADA` に加え、次のいずれかを渡すと受理される。

- 別 protocol: `-DCCBENCH_INLINE_VERSION_OPT_OZE=66`
- 表外: `-DCCBENCH_DOES_NOT_EXIST=77`
- 紛らわしい二重接頭辞: `-DCCBENCH_CCBENCH_REUSE_VERSION=88`

いずれも逆変換で未知の論理軸となり、forward fallback が元の物理名を再構成するため通る。`missing_axes` も全必須軸が既にあるので通り、余剰軸を含む canonical genome が生成される。これらの値は対象 cicada TU へ届かない。

同じ物理名の反復は duplicate として拒否されるが、正規名と別 protocol 名は別論理軸扱いで併存できる。順序を変えても canonical はソートされ、受理結果は変わらない。

成果物影響: accepted calibration JSON の `genome` に、対象バイナリへ届かなかった値を記録でき、D1864 の忠実写像を破る。

最小追加テスト: `test_cicada_receipt_rejects_unmapped_cache_variable_even_with_all_axes` を上記3トークンで parameterize する。

## 所見 C2 — 追加8 nodeidを通過する非等価 forward 変異

判定: **real / must-fix**

次の変異を構成できる。

```python
def cmake_cache_variable_for_axis(protocol, axis, *, mapping=...):
    _protocol_axis_cache_variables(protocol, mapping)
    if (protocol, axis) == ("mocc", "KEY_SORT"):
        return "CCBENCH_TEMPERATURE_RESET_OPT"
    return mapping.get((protocol, axis), f"CCBENCH_{axis}")
```

静的到達解析では追加8 nodeidの期待値はすべて不変である。表検査は定数しか見ず、単射性負例と fallback は silo、producer と受領証検査は cicada しか通らないためである。実走はしていない。

この変異では mocc の `KEY_SORT` と `TEMPERATURE_RESET_OPT` が同じ cache 変数へ出力され、`KEY_SORT` の値が対象 TU へ届かない。

成果物影響: mocc の canonical genome と実バイナリが不一致になり、configure argv には同一 cache 変数が重複する。

最小追加テスト: `test_genome_axis_cache_mapping_roundtrips_every_declared_entry` で表の全17項目について forward と inverse を表の値へ照合する。この検査は「表と consumer の接続」を見るもので、CCBench 側 oracle は既存の独立検査に任せれば恒真化しない。

## 所見 C3 — 単射性検査は protocol 横断の変異を殺せない

判定: **real / must-fix**

`_protocol_axis_cache_variables` を「silo のときだけ重複値を拒否」に変えても、追加テストの唯一の衝突入力が silo なので静的には全追加 nodeidを通過する。mocc、tictoc、cicada の custom mapping に対する forward の fail-close は失われる。

inverse 内の `len(matches) > 1` は曖昧な逆引きを止めるが、forward 側の非単射写像は通るため代替防壁にならない。

成果物影響: 非 silo protocol で複数論理軸が同一 cache 変数へ潰れ、記録値の一部がコンパイラへ届かなくなる。

最小追加テスト: `test_genome_axis_cache_mapping_rejects_non_injective_copy_for_every_protocol` として、4 protocol を parameterize し各 protocol の2軸を衝突させ、forward と inverse の双方を確認する。

## 所見 C4 — inverse の alias 拡張変異が生き残る

判定: **real / must-fix**

exact match 後に次を足す変異は、実体名の正例と旧汎用名の負例をともに通過する。

```python
candidate = cache_variable.removeprefix("CCBENCH_")
if protocol == "cicada" and candidate.endswith("_CICADA"):
    return candidate.removesuffix("_CICADA")
```

これにより `CCBENCH_REUSE_VERSION_CICADA` を `REUSE_VERSION` として受理できる。現実の mapping は `CCBENCH_REUSE_VERSION` なので、置換入力の値は cicada TU へ届かない。

成果物影響: suffix を alias とする将来の誤修正で、必須軸を偽 cache 名から充足できる。

最小追加テスト: `test_cicada_receipt_rejects_unmapped_cicada_suffix_alias` で、正しい `REUSE_VERSION` を `REUSE_VERSION_CICADA` に置換した受領証を拒否させる。

## 所見 C5 — cli の他 protocol 復元は未検査

判定: **real / must-fix**

cli 側だけで mocc の `CCBENCH_KEY_SORT` を `TEMPERATURE_RESET_OPT` へ復元する変異も、追加された受領証テストが cicada 専用なので生き残る。正しい mocc 受領証では本来の `TEMPERATURE_RESET_OPT` と論理重複し、誤拒否になる。

成果物影響: 現行認定対象 mocc の正しい受領証が `receipt-genome-invalid` になり、認定成果物を生成できない。

最小追加テスト: `test_mocc_receipt_accepts_real_cache_names`。より堅くするなら4 protocol の表駆動正例を1 nodeidにまとめる。

## 所見 C6 — screening の2消費点は追加テストから完全に不可視

判定: **real / must-fix**

追加8 nodeidは `screening_driver.py` を呼ばない。したがって次の独立変異はいずれも静的には通過する。

- CMake cache route で `present = True` とする。必要な configure 引数が無くても gate が通る。
- `domain_arguments = set()` とする。要求が再供給するはずの domain define が base argv に残る。

成果物影響: 前者は build 引数との不一致を受理し、後者は同一 cache 変数を複数回供給して後勝ち依存のバイナリを作りうる。

最小追加テスト:

- `test_screening_rejects_missing_cmake_cache_argument`
- `test_condition_gate_base_configure_args_strips_domain_arguments`

## 所見 C7 — 既存4拒否の死亡

判定: **refuted**

静的には4経路とも維持されている。

- `missing_axes`: inverse 後の論理軸集合との差を取る。cicada 実体名は論理名へ戻り、軸省略は引き続き拒否される。
- duplicate define: [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/calibrator/cli.py:452) で逆変換後の論理軸を重複判定する。旧汎用名と実体名の組合せは、旧汎用名の正規往復不一致で順序によらず拒否される。
- build argv 内の CCBENCH define: build command を先に走査する拒否が変更されていない。
- `TRACE`: fallback で論理名 `TRACE` へ戻る。欠落、非0、2回以上はいずれも拒否され、1回だけの0のみ `pop` まで到達する。

非単射な表は各 token の逆変換開始時に protocol 全体の検査で停止するため、duplicate 検査より前に fail-close する。

成果物影響: この4拒否について、従来受理集合を広げる差分は認めない。

## 所見 C8 — drift 検査の現在の正例と負例

判定: **refuted**

CCBench 側期待値は宣言表から生成されていない。[test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_pegasus_calibration_workload.py:38) は実 Options と protocol CMake を既存 parser へ渡し、`cache_by_macro` から RHS を得ている。

現在の負例も非空である。

- CCBench 側 rename は、内側の supplied、bare、宣言済み cache 名の assert を通過した後、旧宣言表との exact 比較で落ちる。
- Izanagi 側 rename は、実体から再構成した旧値との exact 比較で落ちる。
- 表そのものの追加、削除、値変更は exact 比較、17件、非恒等1件のいずれかで落ちる。

成果物影響: 現在の cicada mapping の片側 drift は検査で検出される。

## 所見 C9 — drift helper の部分恒真化変異

判定: **real / must-fix**

helper を「cicada だけ parser の RHSを使い、他 protocol は常に `CCBENCH_<axis>` を生成」に変えても、現在の3 protocolはすべて恒等写像で、2本の rename 負例も cicada 専用なので追加 nodeidは静的に通過する。

この変異後に mocc の `KEY_SORT` を CCBench 側だけ rename しても、helper は旧恒等名を捏造し、宣言表との比較が恒真になる。

成果物影響: 非 cicada protocol の将来の CCBench drift を偽緑にできる。

最小追加テスト: `test_genome_axis_cache_table_rejects_non_cicada_ccbench_side_rename`。mocc の `KEY_SORT` を Options と mocc CMake の両方で rename し、照合失敗を要求する。

## 所見 C10 — screening 2置換による現行 argv の byte 差

判定: **refuted**

1箇所目は既存 argv の membership を検査するだけで、argv を生成・変更しない。

2箇所目は `Genome.cmake_defines()` と同じ forward 関数で除外対象を作る。変更前は汎用名を生成して汎用名を除外し、変更後は写像後の名前を生成して同じ写像後名を除外するため、元 tuple の残存要素と順序は変わらない。

silo、mocc、tictoc の全表項目と補助 define fallback は文字列自体も従来どおりである。cicada の `INLINE_VERSION_OPT` が producer で1 token変わるのは本変更の意図そのもので、screening の2置換が追加する差ではない。

成果物影響: screening の2置換に起因する余分な argv byte 差はない。

## 実行状況

判定: **判定不能**

sandbox 制約に従い pytest は実走していない。「追加 nodeidを通過する」という変異評価は、各 nodeid の到達先と期待式に基づく静的判定である。

成果物影響: runtime の緑は本レビューでは主張しない。

## 総括

- must-fix: 表外、別 protocol、二重接頭辞の cache define を canonical genome へ載せる偽受理を閉じる。
- must-fix: 全17項目の forward/inverse、全 protocol 単射性、他 protocol 受領証、非 cicada rename の検査を追加する。
- must-fix: screening の missing-argument fail-close と domain 引数除去を直接検査する。