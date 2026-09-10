## 実装の file:line

変更は [orchestrator/verifier/dsg.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py:524) の1行だけでよい。

```diff
-        for k in u_writes.keys() & v_writes.keys():
+        for k in sorted(u_writes.keys() & v_writes.keys()):
```

整列 key は key 文字列そのものを採用する。

- trace key は小文字16進文字列なので、文字列昇順が意図する key 順と一致する。
- `u_writes` と `v_writes` は `key -> Txn.commit` の dict であり、同一 transaction 内の同一 key の重複 write はここで1件に畳まれる。
- `_reasons(u, v)` は一つの共通 key について WW 条件を一度だけ判定し、成功しても `EdgeReason` を一つしか追加しない。`u_ver` と `v_ver` も transaction ごとの commit で固定される。

したがって、現行モデルでは「同一 key に複数の WW 理由」が生じる余地はなく、key 単独で全順序になる。`(key, u_ver, v_ver)` も決定的だが、先頭の key が一意なので結果は同じであり冗長である。

この変更は交差集合、WW 条件、追加される `EdgeReason` の集合を変えない。WW、wr、rw の枝順も維持される。また anomaly の検出と cycle 選択は `_reasons()` より前に完了しているため、検出条件、SCC、`total_cycles`、受理集合には影響しない。

## 正例テストの設計

親の provisional 裁定を支持する。異なる `PYTHONHASHSEED` で新しい interpreter を2本起動し、同一 trace の canonical report bytes とその SHA-256 が一致することを検査するのが適切である。

追加先は [orchestrator/tests/test_verifier.py:1591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py:1591) 付近、`test_structured_report_has_edge_detail()` の直後を推奨する。nodeid は次とする。

```text
orchestrator/tests/test_verifier.py::test_multi_ww_reason_report_is_hash_seed_deterministic
```

テストの構造は以下とする。

1. `0000000000000001` から `0000000000000006` までの6 keyを作る。
2. `_tmp_trace()` で親 probe と同じ2 transaction traceを一時生成する。
3. 各 subprocess で公開経路の `verify_trace_dir(trace_dir, workers=1)`、`result_to_dict()`、`json.dumps(sort_keys=True, separators=(",", ":"))` を実行する。
4. seed `"1"` と `"777"` の stdout bytes を直接比較する。
5. それぞれの bytes の SHA-256 も比較する。
6. report を parse し、各 seed で anomaly が1件、`total_cycles == 1`、辺 `0 -> 1` の理由が昇順の WW 6件であることを確認する。
7. `finally` で一時 trace を削除する。

実装骨格は次の形になる。

```python
def test_multi_ww_reason_report_is_hash_seed_deterministic():
    import shutil

    keys = [f"{value:016x}" for value in range(1, 7)]
    rows = []
    for txid, tid in ((0, 1), (1, 2)):
        rows.append(f"C {txid} {txid} 1 {tid} 6 6")
        rows.extend(f"R {txid} {key} 1 0" for key in keys)
        rows.extend(f"W {txid} {key} U 1 {tid}" for key in keys)
        rows.append(f"E {txid}")
    trace_dir = _tmp_trace("\n".join(rows) + "\n")

    script = (
        "import json,sys;"
        "from orchestrator.verifier import result_to_dict,verify_trace_dir;"
        "report=result_to_dict(verify_trace_dir(sys.argv[1],workers=1));"
        "sys.stdout.write(json.dumps("
        "report,sort_keys=True,separators=(',',':')))"
    )

    try:
        reports = []
        for seed in ("1", "777"):
            environment = dict(os.environ)
            environment["PYTHONHASHSEED"] = seed
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            reports.append(subprocess.run(
                [sys.executable, "-c", script, trace_dir],
                cwd=_REPO,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=30,
            ).stdout)

        assert reports[0] == reports[1]
        assert (
            hashlib.sha256(reports[0]).hexdigest()
            == hashlib.sha256(reports[1]).hexdigest()
        )

        for raw in reports:
            payload = json.loads(raw)
            assert payload["total_cycles"] == 1
            assert len(payload["anomalies"]) == 1
            edge = next(
                edge for edge in payload["anomalies"][0]["edges"]
                if (edge["from"], edge["to"]) == (0, 1)
            )
            assert [
                (reason["type"], reason["key"])
                for reason in edge["reasons"]
            ] == [("ww", key) for key in keys]
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)
```

`sort_keys=True` が整列するのは JSON object の field だけであり、`reasons` 配列の順序は保持される。したがって consumer 側で WW reason を正規化して欠陥を隠すテストにはならない。

同一 process 内の比較については、production の文字列 key と実 report 経路を使いながら false negative なく hash seed 差を作る方法はない。

- `PYTHONHASHSEED` は interpreter 起動時に確定する。テスト中に `os.environ` を変えても現在の文字列 hash は変わらない。
- `fork` も親の hash secret を継承する。
- write の挿入順を変える方法は set の衝突配置という CPython 実装詳細に依存し、未整列実装が同じ順を返す可能性を排除できない。
- source AST に `sorted` があることを assert する方法なら当該1行の削除は検出できるが、end-to-end の report 決定性を証明せず、死んだ `sorted` でも通るため代替にならない。

seed は `"1"` と `"777"` の2本で十分である。親 probe の CPython 3.10.12 では、未修正実装がそれぞれ次を返している。

```text
seed 1:   524136
seed 777: 213456
```

digest も `99dc7a...` と `e5a508...` で異なる。この実測環境と同じ入力では、元の集合走査へ戻す変異は bytes 比較で必ず赤になる。6 seed 全部を使うより2本の方が安く、既存の env matrix とも一致する。

所要時間は2 subprocess 合計で、おおむね0.2から0.5秒と見積もる。既存台帳では、同じ2 seed 型の `test_report_projection_is_hash_seed_deterministic` が0.33秒、より重い artifact 生成型が2.4秒である。今回の入力は2 transactionだけなので前者以下に近い。各 child の30秒 timeoutによる異常時上限は直列で60秒だが、通常経路は一秒未満で、pytest の serial markerや長時間 jobは増やさない。

fixture は新設せず `_tmp_trace()` を使うべきである。

- 新しい `trace_*.log` fixture を置くと、[test_verifier.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py:406) の `_V2_FIXTURE_FILES` に追加しない限り、同 file `:445-451` の exact inventory 検査が落ちる。
- `orchestrator/tests/fixtures/README.md` の fixture 一覧にも説明を足す必要があるが、README は本 wave の許可変更面に含まれない。
- 一時 trace なら fixture bytes pin、README、inventory の変更が不要で、probe 入力もテスト内から明瞭に読める。

新規 test file にはしない。既存 file の末尾にある [自走 runner:2794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py:2794) が引数なしの `test_` 関数を自動収集するため、pytest と素の runner の両方に届く。新規 file 固有の自走 harness と所要時間台帳登録も増やさずに済む。

## 変異事前登録の候補

段6では最低限、次を事前登録する。

- M1: `sorted(...)` を除去して元の集合走査へ戻す。

  ```python
  for k in u_writes.keys() & v_writes.keys():
  ```

  seed 1 と777で report bytesと digestが異なるため、`orchestrator/tests/test_verifier.py::test_multi_ww_reason_report_is_hash_seed_deterministic` が KILLED にする。

- M2: 降順へ変える。

  ```python
  for k in sorted(u_writes.keys() & v_writes.keys(), reverse=True):
  ```

  process 間比較だけなら生き残るが、同じ nodeid の WW key 昇順 assert が赤にする。

- M3: versionだけを整列 keyにする。

  ```python
  for k in sorted(
      u_writes.keys() & v_writes.keys(),
      key=lambda key: (u_writes[key], v_writes[key]),
  ):
  ```

  この edge では全 key の version tuple が同じなので、stable sort が入力 set 順を温存する。M1と同様に seed 間 bytes 比較で KILLED になる。

- M4: process依存の hash 順にする。

  ```python
  for k in sorted(
      u_writes.keys() & v_writes.keys(),
      key=hash,
  ):
  ```

  hash 自体が seed 依存なので、同じ nodeid が KILLED にする。

次は現行モデル上の等価変異であり、KILLED を要求しない。

- `sorted(..., key=lambda key: key)`
- `sorted(..., key=lambda key: (key, u_writes[key], v_writes[key]))`
- `sorted(v_writes.keys() & u_writes.keys())`
- `sorted(set(u_writes).intersection(v_writes))`

いずれも共通 key の文字列昇順を返す。特に `(key, u_ver, v_ver)` は key が先頭かつ一意なので、提案実装との出力差がない。

## 掛かる既存 pin と検査

静的再確認の結果は次のとおりである。

- [campaign_lock.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/campaign/campaign_lock.py:49) の現行 closure と `:118` 以降の歴史 closureでは、`dsg.py` はそれぞれ `:59` と `:128` の path memberとして列挙されている。
- `test_artifact_admission.py:56,82,1643`、`test_campaign_lock_codec.py:318`、`test_t671_source_binding.py:33,47` も literal pathまたは path parameterであり、現行 blob digestの固定値ではない。
- 現行 `dsg.py` の SHA-256 は `4e2f8a780a75da968fb0ede4ccb408b7b1e796dde6b26495ae530fd62324691c`。repo全体の exact検索は0件だった。liveの固定 digest literalはない。
- ただし closure処理は列挙された各 sourceの内容から digestを動的に作るため、`dsg.py` の commitでclosure epochが変わること自体は意図された挙動である。
- commit前の working-tree状態で焦点テストを走らせると `contract-loader-drift` が先に発火しうる。これは `_reasons()` の回帰判定ではない。D1388どおりbindingを緩めず、旧closureのcampaignは再走対象とする。
- executableな Python、shell、JSONを対象にした検索では、`dsg.py:<行番号>` または `test_verifier.py:<行番号>` を処理するconsumerや検査は見つからなかった。
- `test_skip_classification.py:354` は `test_verifier.py` をASTで読むが、参照単位はfile名と関数名であり行番号ではない。また対象は既存の実Silo fixture関数だけで、新テストはその登録対象ではない。
- `conftest.py` と `test_real_repo_serialization.py` の分類もnodeidによるものであり、行番号依存ではない。新テストは共有CCBenchを読まないため、そのreal-repo inventoryへの追加も不要である。
- repo文書には `docs/decisions.md:22125,22139` やarchive文書など、過去の `test_verifier.py:<行範囲>` を記した文章がある。ただし実行時consumerではなく歴史記録であり、すでに現行行と一致しないものもある。本waveで更新するpinではない。
- `acceptance_duration_ledger.json` はnodeid単位なので、新nodeは次回再計測まで未掲載になる。ただし現行検査は全nodeのexact一致ではなく90%以上のcoverageを要求しており、新規1nodeだけで失敗しない。台帳を本waveの変更面へ追加する必要はない。

## 残る不確実性

- 指示どおりpytest、素のrunner、subprocess probeはいずれも実走していない。上記は静的設計であり、緑とは報告しない。
- seed 1と777のKILLED保証は、親が実測したCPython 3.10.12と同じhash実装、入力順、現行trace経路に対する実証である。将来Pythonの文字列hashまたはset実装が変われば、同じ2 seedが偶然同順になる可能性までは形式的に排除できない。現行受入環境では6 seedすべて異なるため、今回の2 seed選択には十分な実測根拠がある。
- テスト挿入後は後続行番号がずれるため、実装段では関数名と周辺コードを基準に配置し、ここに示した行番号を絶対位置として扱わないこと。
- precommitのclosure driftと実際のテスト失敗を分離した最終実測は、親がcommit順序を守って行う必要がある。

## 総括

`dsg.py:524` のWW交差だけをkey文字列昇順にし、既存 `test_verifier.py` にseed 1と777の2 subprocessで同一report bytes、SHA-256、昇順WW 6理由、anomaly 1件を固定するテストを加える。fixture、wr/rw、consumer、closure bindingには触れない。元の集合走査への復帰変異は指定nodeidでKILLEDになる。