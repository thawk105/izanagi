## 規律 2 と fail-closed

**関門の受理規則を広げる変更、関門未到達のまま S6 go になる経路は確認しなかった。** 静的レビューのみ実施した。親ログは F1 が **180 passed／271.18 秒**、F2 が **897 passed・2 skipped／710.98 秒**。変異実走・計算ノード受入の証拠とは区別する。

基準 commit `38353207…` と現物を AST 比較し、以下の不変を確認した。

- `_require_condition_gate`、`_INERT_CONDITION_GATE_PAIRS`
- `_condition_gate_family_valid`、`verdict_s6`
- `_git_source_identity`、`_condition_gate_receipt_summary`
- `_run_command`、`ReceiptPublisher`

[probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2654-t316-hydrate-base/tools/pegasus/probes/t316_sandbox_backend_probe.py:1885) の制御経路は次のとおり。

| 経路 | 停止位置と verdict |
|---|---|
| hydrate 失敗 | 2125–2137 行で return。identity=false → `S6_SOURCE_IDENTITY_INVALID` |
| prepare 失敗 | 1932–1944 行で failure 設定。**prepare 後の1945行**が関門を遮断。family 空 → `S6_CONDITION_GATE_UNPROVEN` |
| hydrate 前・prepare 前・build 前の残時間不足 | `failure_stage="walltime"` → `S6_WALLTIME_RESERVE_REACHED` |
| S6 開始時の reserve 不足 | 2094 行の既存早期 return。attempted=false → `S6_BUILD_NOT_ATTEMPTED` |
| 関門例外 | build に進まず伝播。外側の observer 捕捉でも go にならない |

`trace_disabled` は引き続き両 build の検査結果の AND。D1995 の stderr 診断も不変である。

hydrate の記録形についても fail-closed である。

- 起動失敗は `executed=False, rc=None`。`None != 0` で拒否する。
- timeout は終了時 rc が仮に 0 でも `timed_out=True` で拒否する。
- `stdout.truncated` 自体は検査していない。ただし現行 CLI は単一 JSON object のみを出力するため、その先頭を失った16 KiBの末尾は JSON として解読できず、`third-party-hydrate` になる。正常 hydrate を拒否する可能性はあるが、現行出力契約下の fail-open ではない。
- `except Exception` は KeyboardInterrupt／SystemExit を捕捉しない。既存の制御信号伝播方針と一致する。contextmanager の巻戻しは行われるが、完成受領証の生成は保証しない。

## 裁定整合 (plan v2 1〜10)

以下の行番号は統合後の現物。

| 項 | 照合結果 |
|---|---|
| 1 | 一致。2115 行で実 hydrate CLI を1回、`-I -B` 付きで実行。timeout と30秒境界も一致。Python は `sys.executable` の canonical path。 |
| 2 | 一致。2051 行は `scratch.resolve(strict=True).parent`。context が hydrate〜両 build を包み、2215 行で S を readonly roots に追加。追加 pristine gate／`<name>-src` 複製なし。 |
| 3 | 一致。依存6 command の後、outside のみ prepare。canonical base、manifest、prefix、3 source、site 省略を確認。関門直前の再判定あり。共有 configure に BASE_DIR なし。 |
| 4 | 一致。Python／PBS と test 独立 literal が同じ9 path。 |
| 5 | identity の順序・採取先、成功時の観測内容は一致。失敗時 argv の記録に下記 RA-1。 |
| 6 | この射影では計算ノード実経路の実証は未確認。login の緑を代用できない。 |
| 7 | hydrate／prepare の拒否 verdict と内部 failure 名は一致。トップレベル failure 名には下記の留意点。 |
| 8 | 一致。5 Git repo、実 hydrate、FetchContent、2 OUTPUT、package config、header include、prepare 専用失敗分岐を確認。 |
| 9 | 一致。build／gate／command 境界に inline assertion、prepare call/return と identity path を記録。最初の赤理由は一部事前登録と異なる。 |
| 10 | 提示3差分に変更禁止ファイルの編集なし。既存 helper を呼ぶ変更に収まる。 |

**[RA-1] should-fix — prepare 失敗時、実行された configure／build の argv が受領証から失われる。**
成果物影響：S6 verdict は変わらないが、prepare 失敗受領証から、実際の source override・prefix・configure 抑制条件を検算できない。

1889 行で両 argv を `None` に初期化し、1929–1930 行の成功 return 後しか埋めない。configure 成功後の target 失敗でも両方 `None`。[test.py:2282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2654-t316-hydrate-base/orchestrator/tests/test_t316_sandbox_probe.py:2282) がその欠落を固定している。plan 5 の記録要件として、失敗時に得られる実行情報を残すか、親裁定で成功時限定と明記すべき。共有 helper の変更禁止を破って修正する提案ではない。

**[RA-2] nit — prepare 失敗のトップレベル `failure_stage` は `outside-control` になる。**
成果物影響：受領証のトップレベルだけでは原因を識別できない。ただし原因は `outside_build` と `masstree_prepare` に残り、verdict・受理集合は変わらない。

2229 行の inside 未実行記録を2244 行が優先するためである。これは既存の集約方式を踏襲しており、既存 field 不変の裁定もある。plan 7 の名前が**nested record に記録される**ことを明記する程度でよい。

段3の real 所見について、A-7 の2置換、A-8 の inline assertion、A-13 の束縛拡張は反映されている。A-4／A-10／A-11／A-15 の文言是正は s4 に存在するが、後続 insight への反映は今回の射影外である。

## 変異の帰属 (M0〜M12 の old/new 提案)

以下は**静的予測**。KILLED／SURVIVED の実測報告ではない。`old` は現物の行からインデントを省略して示す。複数出現するものは記載した場所に限定する。

| ID | old → new | 最初の赤理由の予測 |
|---|---|---|
| M0 | `# A later writable scratch bind must never cover the requested source.` → `# Keep the requested source outside writable scratch.` | 等価変更。SURVIVED 期待。 |
| M1 | 下記コード参照 | test 2020 行の source override 集合比較。**最初の gate call 境界**で発火し、command 境界まで進まない。 |
| M2 | `if not inside and failure_stage is None:` → `if False:` | 最初の gate call で test 2114 行「成功 prepare return が1回」。header preprocess より前。 |
| M3 | 下記コード参照 | gate は S のまま通過。outside configure の command 境界で test 2020 行。 |
| M4 | `prefix="t316-s6-thirdparty-", dir=scratch.resolve(strict=True).parent,` → `prefix="t316-s6-thirdparty-", dir=scratch.resolve(strict=True),` | 最初の build call、test 2082 行「scratch 外」。 |
| M5 | `(*profile.readonly_roots, requested_root, staging_root), runner=profile.runner,` → `(*profile.readonly_roots, requested_root), runner=profile.runner,` | 最初の build call、test 2083 行「readonly roots に S」。 |
| M6 | `_BOUND_RELATIVE_PATHS` 内の `"tools/pegasus/fetch_third_party.py",` → 行削除 | 独立 literal 比較の test 1754 行。dirty 拒否 node も拒否欠落を検出。 |
| M6b | PBS の `  orchestrator/campaign/buildcache.py` → 行削除 | test 1752 行。shell dirty node では test 1678 行の exit/stdout 比較。 |
| M7 | 下記2置換 | test 2252 行の `failure_stage == "third-party-hydrate"`。実際には `dependency-pins` が返る。 |
| M7b | M7 の1本目のみ | 空 stdout の JSON 解読失敗で元と同じ拒否。SURVIVED 期待。 |
| M8 | `if not inside and failure_stage is None:` → `if failure_stage is None:` | 正常系 test 2173 行の prepare call 数 exact 1。 |
| M9 | 共有 configure 内の `f"-DCMAKE_PREFIX_PATH={prefix}",` → 同行の次に `f"-DFETCHCONTENT_BASE_DIR={staging_root}",` を追加 | 最初の gate call で test 2025 行の BASE_DIR 禁止。 |
| M10 | **1945行の** `if failure_stage is None:` → `if True:` | prepare 失敗 fixture の gate call、test 2112 行「gate reached after failed prepare」。 |
| M11 | `dependency_prefix=str(prefix),` → 行削除 | prepare configure 失敗後、gate call の test 2114 行。**outside_success assertion より前**。 |
| M12 | 下記コード参照 | 正常系 test 2193 行の identity path 集合。 |

M1 の具体的置換：

```python
# old
f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={staging_root / 'masstree'}",
# new
f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={Path(os.environ['IZANAGI_PEGASUS_THIRDPARTY_CACHE']).resolve(strict=True) / 'masstree'}",
```

M3 は共有 configure を変更せず、実 build に渡す argv だけを変える：

```python
# old
("ccbench-configure", configure, 300),
# new
("ccbench-configure", [arg.replace(str(staging_root), str(Path(os.environ["IZANAGI_PEGASUS_THIRDPARTY_CACHE"]).resolve(strict=True))) for arg in configure], 300),
```

M12 は `observe_s6` 内なので、現存する `cache_root` を直接使える：

```python
# old
else (source if name == "ccbench" else staging_root / name),
# new
else (source if name == "ccbench" else cache_root / name),
```

環境変数から構成するなら、その `cache_root / name` を次に置き換えてもよい。

```python
Path(os.environ["IZANAGI_PEGASUS_THIRDPARTY_CACHE"]).resolve(strict=True) / name
```

いずれも未定義 `cache_root` を `_execute_ccbench_build` で参照する必要はない。

M7 の **old 2本は現物の逐語で**次のとおり。

```python
# 2125行 old
if command.get("rc") != 0 or command.get("timed_out"):
# new
if False:

# 2129行 old
failure_stage = "third-party-hydrate"
# new
failure_stage = None
```

glog origin 不一致は `_hydrate` 冒頭の全 cache 検証で発生するため、S に repository は生成されない。rc 検査と JSON 例外時の failure 設定を外すと、`source_heads` 採取へ進み、S の3 HEAD が `None` になる。2154 行で不一致となり、`dependency-pins` を返す。**`_git_source_identity` までは到達しない。** fixture helper の `assert not requested_roots` は通り、2252 行が最初の赤になる。

M2／M8 は同じ old でも、上記の別 new なら分離できる。M2 は prepare 0回、M8 は2回。別 anchor への再照準は不要。

**[RA-3] nit — M1／M2／M9／M11 の事前登録は、実際に最初に発火する assertion へ記述を訂正する。**
成果物影響：production の受領証・受理集合は変わらない。訂正しないと、変異台帳が command 境界や preprocess／outside_success に帰属させた説明と実測 traceback が一致しない。

特に M11 は失敗した prepare の return が `None` と観測されるため、「成功 prepare return が1回」という gate observer が先行する。指定された `requested_gate_and_both_build_roots_match` も同じ observer を通る。

## test の弱さ

新規の主要 assertion に、候補抽出だけで必ず真になる検査や、実行時刻・一時 path・固定 HEAD の焼き込みは確認しなかった。生成した pin／path をその実行内で比較している。

懸念された stale header は実際に参照経路へ接続されている。

- test 1916 行：コンパイル対象 `transaction.cc` に `#include <config.h>`。
- 1936 行：同 target の include directory が `${masstree_SOURCE_DIR}`。
- 1937 行：`masstree_build` への依存。
- 2175／2177 行：prepare 前に2生成物がなく、成功 return 後に両方存在。
- 2219／2220 行：outside／inside の双方が成功。
- 2222／2223 行：元 cache の毒入り生成物が変更されていない。

したがって「毒入り header をどこからも include しないため緑」という偽緑ではない。archive は実ライブラリのリンク検証ではなく、**第2 OUTPUT の事前生成と再生成回避の配線検証**に限定される。

読み取り専用 test も profile の一覧比較だけでなく、sandbox 内で読めることと書込みが `EROFS` になることを確認する。

弱点は RA-1 の失敗 argv 欠落を test が固定している点、および RA-3 の最初の赤理由の説明である。hydrate timeout／起動失敗／truncation 専用 test はないが、今回の静的追跡では拒否側へ倒れる。

## 規律 7 と受領証

旧5受領証を読み直して無効化する処理・記述は、提示差分にない。束縛追加は新実行の9 path に対する記録拡張であり、旧受領証への遡及要求ではない。

新2 key は JSON 化できる値で構成されている。内部 `_masstree_prepare` は nested build から取り除かれ、既存 `_condition_gate_family` も verdict 判定後に除去される。`verdict_s6` と `_condition_gate_receipt_summary` は新 key に依存せず、writer の AST も不変。指定 consumer の親焦点走にも新たな失敗は報告されていない。

ただし、旧5受領証本文を個別再検算したという意味ではない。

## 総括

**must-fix なし。**

should-fix：

- **[RA-1]** prepare 失敗時の実行 argv 記録を補うか成功時限定と裁定する。現状では失敗受領証の供給 path・configure 条件の検算が欠ける。

nit：

- **[RA-2]** prepare の具体的 failure 名は nested record に残り、トップレベルは `outside-control` になる点を明記する。
- **[RA-3]** M1／M2／M9／M11 の最初の赤理由を現物の observer 順序に合わせる。

補足：変異案をメモリ上で構文検査する追加コマンドは、PreToolUse hook に「クォート不整合等で解析不能」として拒否された。その構文検査と変異実走は未実施。上記 old/new と帰属は静的提案である。