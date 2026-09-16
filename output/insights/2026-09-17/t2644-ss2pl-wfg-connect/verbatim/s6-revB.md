## runner 変更の閉包

以下、`R` は `tools/pegasus/run_ss2pl_lock_study.py`、`P` は `tools/t2644_wfg_probe.py`、`T` は `orchestrator/tests/test_ss2pl_lock_study.py`、`D` は `tools/pegasus/dispatch_compute.py`。

**所見：正常戻りの閉包を壊す問題は該当なし。**

- `binary.resolve()` は実行対象と SHA 検査対象を同じ実体へ揃える。受領証は従来どおり `argv[1:]` なので、実行ファイルの絶対化による形式変更はない（R:2528、2856、2908）。
- trial dir は binary の実体の親に作る。今回の probe は自分で作った scratch 内へ build するため、build 後に権限・容量が変わらない限り書込み前提は成立する（P:185、R:2107、2858）。
- `FileNotFoundError` を先に捕まえ、その後の `OSError` を `read_error` にする順序は正しい。UTF-8 不正と JSON 構文不正も `invalid_json` になる（R:2878）。
- 追加 path は `str`、SHA・error は文字列、読んだ bytes は受領証へ入らない。今回の整数主体の serializer 出力では、probe の `allow_nan=False` にも適合する（R:2874、2915、P:130）。

**所見：本文保全は `_run_process` の正常戻り後に限定される。**  
現物の根拠：R:2706〜2715 は本文を返さず例外化し、書込みは R:2872。  
成立条件：stage deadline、phase2 の timeout 契約不一致、自然終了時の非ゼロ終了など。今回の probe は runner の stage deadline を設定せず、phase1 の `expected_timeout=None` なので、前二者は通常の probe 経路にはない。  
影響：該当時には stdout 本文を失い、probe は例外・scratch path・既に存在する durable file までしか保全できない。  
是正案：今回の保全説明を「正常戻り後」に限定する。例外時の本文も要求する場合は、回収済み本文を例外送出前に保全する。  
区分：nit。

**所見：`json.loads` の捕捉集合は任意の壊れた入力を網羅しない。**  
現物の根拠：R:2887〜2889、P:130。  
成立条件：過大な入れ子による `RecursionError`、非有限数を含む入力など。現 serializer が出す通常の v2 JSON では成立しない。  
影響：観測用 file の異常が trial 戻りや厳密 JSON 保存を止める場合がある。  
是正案：`invalid_json` が全種類の不正入力を吸収するとは説明しない。今回の実出力については変更不要。  
区分：nit。

## 既存消費者への波及

該当なし。

- 全 trial が完了すれば、phase1/phase2 × 2 点 × 3 trial で12個の dir を作る。途中例外ならそこで止まる（R:2942）。
- `validate_phase_matrix` の閉じた集合検査は `(phase, point, trial)` の組合せであり、受領証の key 集合ではない（R:531）。
- `validate_mode_document`、`validate_single_occasion` に追加 field を拒否する検査はない（R:557、587）。
- plotting は `phase`、`accepted_cycle` 等の必要 field を選択して読むため、追加 field は影響しない（`tools/plotting/plot_ss2pl_lock_study.py:613`）。
- 既存 T:1101 は `_run_process` と `_admit_output` を差し替えるが、実 `_run_phase_trial` を呼ぶ。T:1139 は `_run_phase_trial` 自体を差し替える。今回の変更と静的な矛盾はない。
- phase2 の `acquisition_paths` 不在による拒否は既存のままで、この probe は phase2／matrix 検査へ進まない。

## probe の到達性

**所見：前段に確定的な到達阻害は見つからない。ただし計算ノードの command 解決は未実測。**  
現物の根拠：D:349、1442、1631、408、R:106、728、782、802、2976。  
成立条件：dispatcher が計算ノードで選んだ Python と、そのプロセスの PATH 上の依存 command が利用可能であること。  
影響：不足 command があれば `required_commands` 段で停止し、build／検証器へ到達しない。  
是正案：投入済み走行の dispatcher 結果と `required_commands` 記録で確定する。  
区分：nit。

確認した内容：

- clean env は **PATH を保持する**。ただし保持元は計算ノードの dispatcher 環境であり、コードが login の PATH を明示転送するわけではない。さらに選択した Python の実体ディレクトリを先頭へ追加する（D:1442、1631）。
- dispatcher の interpreter 候補自体が `python3.10`、`/usr/bin/python3.10`、`/bin/python3.10`。選択・probe に成功して子を起動する経路なら、通常は指定の `python3.10` を解決できる（D:408、892）。
- 必須 command は `git, cmake, cc, c++, make, as, ld, ar, ranlib, nm, strings` の11個（R:106）。
- thirdparty 検査対象は policy の **masstree・mimalloc・googletest の3本**。gflags／glog が同じ root に追加されても拒否しない。3本とも現物の HEAD が policy pin と一致し、porcelain 出力は空だった。prefix ディレクトリも存在する。
- wave の `external/ccbench` は実ディレクトリで、HEAD と gitlink はともに `511c9538e4e8efa54b45cda62e72389ed3b706ec`、porcelain 出力は空。canonical 検査の条件を満たす。
- clone は `--local --no-hardlinks --no-recurse-submodules`。`--shared` や `file://` は使わず、`protocol.file.allow=always` と `GIT_ALLOW_PROTOCOL=file` を明示する（R:772、802）。
- Lustre 上の writable scratch に対する `--parallel 48` 自体に、静的に断定できる到達阻害はない。所要・容量・実行時資源は別途実測事項。

**所見：01:00:00 以内の完了は静的に保証できない。**  
現物の根拠：R:2006、2120、2128、`orchestrator/campaign/condition_meaning_gate.py:1889`、同:3335。  
成立条件：configure・build・前処理の累積時間が長い場合。  
影響：検証器へ到達する前に外側の walltime を使い切り得る。  
是正案：今回の `stage_seconds` で見積りを確定する。1800秒を build 全体の上限として扱わない。  
区分：nit。

通常成功経路では、1 arm あたり supply の4軸 × requested/control で8 configure、最後の `_configure` が1回、計9回。2 arm で計18回。`declaration=None` の runtime-meaning は configure せず `unestablished` を返し、raw-measurement は supply が green ならこれを許容する。`timeout=1800` は各 `cmake --build` 単体だけで、condition gate・configure・S の absence 前処理は含まない。

## probe の保全

**所見：通常の Python 例外と外側からの強制終了で、保全能力が異なる。**  
現物の根拠：P:119、214、221、228、236。  
成立条件：通常例外なら catch へ進む。walltime によるプロセス終了では、その経路を通る保証がない。  
影響：強制終了時には、完了済み build record を含め probe JSON が一度も書かれない可能性がある。  
是正案：途中段階も残す要求なら、既存の `write_result` を段階境界でも呼び、同じ出力へ途中状態を保存する。  
区分：nit。

通常例外なら `document["stage"]`、失敗段の経過秒、既に代入済みの結果、例外 type/message、scratch path が JSON に残る。ただし `build_target`／trial は戻ってから一括代入するので、失敗した呼出し内部の部分 record は残らない。build tree は scratch に残る。

**所見：出力親 dir 不在では JSON file を保存できない。**  
現物の根拠：P:128〜138、237〜239。  
成立条件：`--output` の親が存在しない、または書込み不能。指定された job dir は現物で存在するため、今回の確定 argv では不在条件は成立しない。  
影響：結果は stderr へ退避されるが、指定 JSON file は残らない。  
是正案：今回の既存 job dir を出力先に使う。  
区分：nit。

**所見：PBS ID の glob は通常 submission 配置には一致するが、split 配置には一致しない。**  
現物の根拠：P:101、D:3387〜3405、3509、846。  
成立条件：通常は `<repo>/output/pegasus-dispatch/<nonce>`。`artifact_root`／別 `output_root` を指定した場合は marker が別位置になる。  
影響：`unknown`、または同一 hostname の古い別 job ID を記録し得るが、検証器の受理値は変わらない。  
是正案：裁定どおり dispatcher receipt の実 job ID を親が対応づける。  
区分：nit。

## test (e) の実効性

該当なし。

- fake は flag を必須抽出し、個数1、絶対 path、file 名、親 dir、prefix、過去 path との非重複を確認する（T:1564）。
- present 2回に加え、missing／invalid JSON／invalid UTF-8／read error の計6回を実 `_run_phase_trial` へ通す（T:1585）。
- path・本文・SHA・parsed JSON・error・stdout 証拠による受理・`json.dumps(result)` を確認する（T:1591〜1619）。
- 性能経路も実 `_run_performance_once` を呼び、flag 不在を検査する（T:1627）。
- monkeypatch は実関数が参照する `driver` module global に効く。
- `_admission_fixture` は要求される cache、compile definitions、binary SHA を持ち、test が `binary` を補う（T:280、1557）。
- 確認時の login `/tmp` は symlink ではなかった。指定された通常の tmp_path 前提では T:1570 と runner の resolve に不一致はない。
- timeout・flush・C++ serializer の実効性はこの fake では検証しない。docstring もその射程を明記している。

## fixture 差し替えの成立

**所見：正常完了時の実 stdout への導線は成立する。**  
現物の根拠：P:185〜193、221、R:2858、2872、2915。  
成立条件：trial が戻り、probe JSON の保存に成功すること。  
影響：`trial.stdout_path` から job dir 配下の本文へ辿れ、実行終了後も残る。  
是正案：既定手順どおり、受理に使われた連続3 snapshot の生行と軸・workload 行を本文から写す。JSON の再直列化を逐語コピーの代用にしない。  
区分：nit。

`mkdtemp` に自動削除はなく、build と本文は UUID scratch 配下に残る。閉路が4枚以上出た場合、採取対象は受領証の `snapshot_indexes` と対応させる。未受理なら正例 fixture 取得済みとは扱えない。

**所見：実 fixture では test (c) の先頭要素変更が負例を作らない可能性がある。**  
現物の根拠：T:1536 は `held_locks[0]` だけを変更する。一方、R:2381 は保持一覧全体から edge と一致する lock を探す。  
成立条件：実 snapshot で複数 lock を保持し、閉路 edge の lock が先頭以外にある場合。  
影響：正しい実 fixture に差し替えた結果、(c) の `lock_id`／`mode` case が期待どおり拒否されなくなる。  
是正案：edge の holder と lock_id に対応する保持要素を変更する。拒否の期待値は維持する。  
区分：nit。

## 変異の帰属 (m1〜m10 の anchor と期待 node)

**所見：裁定は変異の意味までの登録で、逐語 old の完成 spec はまだない。m6〜m8 の期待 node は拡張が必要。**  
現物の根拠：`s4-ruling.md` §4、T:1494、1516、1530、1602、1645。  
成立条件：共有 `_wfg_stdout_fixture` を変異させる場合。  
影響：単一 node だけを期待すると、正当な波及失敗を帰属不一致と扱う。  
是正案：以下の範囲で old と期待 node を確定する。  
区分：nit。

以下の `lines(a,b)` は、指定 file の **a〜b 行の全文をインデント込みで逐語採取**する指定。省略文字列を old に使う意味ではない。

| 変異 | 現物に対応する old／範囲 | 一意性・期待 |
|---|---|---|
| m1 | R:2862 `argv.append(f"-ss2pl_wfg_output={output_path}")` | 1箇所。E |
| m2 | R `lines(2858,2860)` | 1箇所。E。固定 dir を実際に作り、prefix を保たないと、非一意性より先の失敗になる |
| m3 | R:2885 `wfg_output["sha256"] = _sha256_bytes(raw_output)` と R:2887 `wfg_output["json"] = json.loads(raw_output.decode("utf-8"))` | 各1箇所。E。両方を変えるなら2編集 |
| m4 | R:2872 `stdout_path.write_text(stdout, encoding="utf-8")` | 1箇所。E |
| m5 | R `lines(2353,2354)` の top-level `elif` と append | 1箇所。集合 S |
| m6 | T `lines(1489,1489)`、tick=2 の event 全行 | 全行なら1箇所。node 0 の counter を10→11。集合 S |
| m7 | T `lines(1488,1490)`、3 event 全体 | block として1箇所。全 node の保持一覧を削除。集合 S |
| m8 | T `lines(1488,1490)`、3 event 全体 | block として1箇所。全 edge の compatible を削除。集合 S |
| m9 | T:1543 `stdout = "\n".join(_wfg_stdout_fixture().splitlines()[:6]) + "\n"` | 1箇所。(d) 内で軸行を除去するなら D |
| m10 | R:2740 `argv = [str(binary), *_workload_argv(workload, threads=thread_num, clocks_per_us=clocks_per_us, extime=10)]` | 1箇所。E |

m6 の `"commit_count":10`、m7 の保持一覧断片、m8 の `"compatible":false` 単独は複数出現するため、一意 old にならない。m9 を共有 fixture の軸行削除として実施すると、D 単独ではなく S にも波及する。

期待 node の完全名は、すべて `orchestrator/tests/test_ss2pl_lock_study.py::` を接頭辞とする。

**集合 S（9 node）：**

- `test_wfg_stdout_fixture_accepts_actual_holders`
- `test_wfg_stdout_legacy_fields_are_rejected[wait_lock_id]`
- `test_wfg_stdout_legacy_fields_are_rejected[waiter_thread_id]`
- `test_wfg_stdout_legacy_fields_are_rejected[holder_thread_id]`
- `test_wfg_stdout_missing_held_locks_is_rejected[missing]`
- `test_wfg_stdout_missing_held_locks_is_rejected[lock_id]`
- `test_wfg_stdout_missing_held_locks_is_rejected[mode]`
- `test_phase_trial_passes_unique_wfg_output_and_collects_file`（E）
- `test_wfg_exclusive_mode_write_is_accepted_and_read_read_is_rejected`

**D：** `test_wfg_startup_axes_without_terminal_output`

m5 は既存3件（T:1432、1440、1447）を赤にしない。これらは snapshot を直接検証器へ渡し、`_extract_snapshots` を通らない。m6 では (b)(c)(f) が受理前提 assertion で失敗し、(e) は `accepted_cycle` の参照で失敗する。以上は静的予測であり、変異実走の観測結果ではない。

## 総括

**must-fix：該当なし。静的レビューは GO。**

正常経路の到達・判定・受領証を確定的に壊す問題は見つからなかった。実機接続の完了判定は、投入済み走行の結果待ち。walltime 内完了、計算ノードの command 解決、S の不在性、実 stdout の受理は本レビューでは実証していない。

段6では、test (c) の変更対象と、m5〜m8 の期待9 nodeを確認する。ファイル変更・pytest・build・計測は実行していない。

自動 PreToolUse 審査が、command 所在確認と読取り専用の anchor 集計を重量処理と判定して拒否したため、その2コマンドは未実行。権限昇格は求めず、許可された静的読取り・検索で確認した。