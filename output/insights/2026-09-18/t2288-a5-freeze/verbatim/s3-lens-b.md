**生成 JSON の構造・既決値に loader 拒否を招く不一致は見つかりませんでした。ただし、生成器への暫定修正の反映と、時間・HEAD に関する運用説明の訂正が必要です。** 静的照合とメモリ上の hash 再計算のみ実施しました。ファイル変更、binder 実走、測定はしていません。

参照略号：

- **F** = [floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/campaign/floor_pair_driver.py)
- **I** = [p3_b4_floor_artifact_issuer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/campaign/p3_b4_floor_artifact_issuer.py)
- **R** = [runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/calibrator/runner.py)
- **C** = [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/calibrator/cli.py)
- **G / P / V** = 指定 job directory の `make_specs.py` / `s2-plan.out.md` / `verbatim/`

**1.［must-fix］採用予定の命名・窓を生成器と記録へ同期する**

現状の G:54 は campaign 成分のない spec 名、G:42 は旧 w2 です。親の追記を採るなら、以下へ変更してから実 bytes の期待 hash を確定してください。

- spec 名：`__campaign-t2288-f1-<wl>-c1c2` を追加。
- w2：`[2026-09-29T00:00:00Z, 2026-10-07T00:00:00Z)`。
- G:39 の隙間コメントも 48 h に変更。

spec path 変更は seed に効きます。日時変更だけなら seed は変わりませんが、spec SHA-256 が変わるため **HMAC の計画順序も変わります**。P:434 の旧 hash 表を流用できません。根拠：G:47、G:138、F:1356、F:1381。

親 OID が `d2ebef7a407dc6be61622ed596cf08b8b518f606` のままで、上記修正だけを反映した場合の再計算値です。binder 成功の証拠ではありません。

| spec | 修正後 SHA-256 |
|---|---|
| rr95 | `990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619` |
| rr50 | `b582d20c37268f491e4c47bb7436731197c18e737cdcca43694c64fa3e0d5e37` |
| rr5 | `d13c384473a5d24170e929f7e17aad9cc24479a5487ed0da21d06bc45430d8c4` |

**2.［情報］loader の静的検査鎖は適合する**

| 検査 | 結果・残条件 |
|---|---|
| exact key 集合 | root の 11 key と全入れ子 object が適合。説明用の未知 key は追加不可。F:403、F:639–1047、F:1240 |
| 型・定数 | 正整数、exact bool、統計式、format ID、failure policy が一致。F:775、F:937、F:996、F:1033 |
| ID | `_ID_RE` は **F:92**。ドットを許すため `s0.9` は適合。今回の ID は 128 文字以内。 |
| path | `__`、`c1c2`、名前中の `0.9` は拒否要因ではない。禁止する dot component は単独の `.` / `..`。F:460 |
| 日時 | 現案・48 h 修正案とも Z 表記、非空、非重複。F:470、F:869 |
| 参照閉包 | cell/artifact/pair 参照と、2 件の `closed_strata` が一致。F:1060 |
| 出力相異 | 各 spec 内の窓 2＋summary 1 が相異。3 spec 横断でも 9 出力すべて相異。F:1276 |
| 出力親・symlink | 同居 directory が実在し、途中 component と leaf が symlink でないことが必要。静的 JSON では証明できない。F:489、F:517 |
| checkout 束縛 | spec・較正・receipt の実 hash と tracked blob、binary 現物、accepted 較正の exact 一致は親の実走で確認する。F:614、F:1122、F:1197 |
| source_commit | `P → C` と commit すれば P は真の祖先。commit 前の HEAD=P では不成立。F:1290 |

campaign 成分追加後の leaf 長は、rr95/rr50 が spec **103**、window **104**、summary **106** 文字、rr5 は各 2 文字短くなります。**3 spec＋9 出力は 12 件すべて相異**です。ファイル名全体に `_ID_RE` の 128 文字制限を適用する実装ではありません。

なお、loader は既存の通常出力 leaf を拒否しません。`--validate-only` 成功でも、実行時の create-only 成功は未確認です。F:527、F:1685。

**3.［情報］既決値の転記と JSON 直列化に訂正不要**

G:30 の較正 path・64 桁 SHA-256 は V/D2089.md:11 の表と全桁一致し、D2090.md:33 の選択結果とも一致します。

- records：rr95/rr50 は `1000000`、rr5 は `2000000`。
- workload：文字列 `"0"`、`"95"/"50"/"5"`、`"0.9"` を維持。
- `extime=3`、`reps=5`、`ycsb_max_ope=10`：D2088.md:8 に適合。
- binary SHA・receipt path/SHA・artifact 2 entry：指定 placeholder JSON と全値一致。

**D2069 自体は具体的な binary/receipt SHA を掲載していません。** その全桁照合の直接資料は placeholder JSON です。D2069.md:5 が裏付けるのは配置規則と同一 bytes の共有です。

`json.dumps(indent=2, sort_keys=True) + "\n"` は受理可能です。spec loader は canonical JSON bytes を要求せず、実 bytes の hash と tracked blob 一致を要求します。canonical 要求がある summary と混同しないでください。F:363、F:1229、I:859。

**4.［must-fix］21.5 分を session 全体の厳密な上限と説明しない**

計算した **1290 秒＝21.5 分**は、10 rep の subprocess timeout と 3 probe の timeout の合計です。

- `run_once` の timeout は bench subprocess 全体へ渡されるので、bench 内の **load と extime の両方を含みます**。R:662。
- `settle_first=False` が明示され、settle 待ちは入りません。F:1599。
- timeout で残り rep を採用して続行せず、`require_all_reps=True` により測定が失敗します。session の第 2 測定も省略される場合があります。R:1194、F:2150。
- 一方、binary hash・trace symbol 検査、tmp 作成・削除、結果解析、プロセス起動・終了処理等は、この timeout 和で覆われません。session 全体の deadline はありません。F:2110、R:633、R:747。

したがって **48 h の隙間への拡大は余裕を増やしますが、終了→次開始の 24 h 分離を機械保証しません**。実 timestamp による確認を残す必要があります。V/D1974.md:14。

1 spec・1 窓の時間は、提示された rep wall を前提に次のとおりです。

| 計算対象 | 時間 |
|---|---:|
| 124 session × 10 rep × 3.5–4.5 秒 | 1.21–1.55 h |
| 上記＋全 372 probe に各 30 秒を計上 | 4.31–4.65 h |
| 全 rep/probe の timeout 合計 | 44.43 h |

いずれも全体の厳密な wall 上限ではありません。**8 日は通常走行を包む運用余裕としては理解できますが、未着地 job body と queue 待ちを包む保証はありません（推測）。** session 開始が窓外になると FATAL で残りが未実行になります。窓直前の投入や途中再開を前提にしないでください。F:2091、F:2295。

**5.［must-fix］w1・w2・finalize の HEAD 固定を申し送る**

finalize は両窓 header の `loaded_head` と `runtime_head` を、finalize がロードした `spec.loaded_head` と exact 比較します。**spec bytes が同じだけでは足りません。** F:2694、F:2700、F:2721。

後続 job body が着地した後、実行 commit **H** を決め、同一 spec の w1・w2・finalize を H に固定してください。別 checkout でも同一 H と必要入力があればよく、同一 directory の必須条件ではありません。測定途中に成果物記録の commit を積む運用は、この条件と衝突します。

**6.［情報］集約対応と予測名は成立する**

P:570 の対応表は必要項目を揃えています。期待 spec の **最終 relpath/hash 3 組**、summary 3 path、output_dir を、結果を見る前に記録すればよい構成です。I:1036、I:1069、I:1140。

receipt の `binding.genome_canonical` は：

```text
silo|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
```

I:799 は共有 helper へ渡します。[genome.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/campaign/genome.py:223) は `|` で分割し、flags の canonical 再構成一致を確認して `silo` を返せます。receipt の該当 field は `rr20--stock_common.json:3007` です。

canonical bytes 順の workload は **rr5、rr50、rr95**。campaign は文字列順に全 6 件を並べ、末尾改行込みの canonical JSON を SHA-256 化して先頭 20 hex を取りました。親の予測名と一致します。I:189、I:749、I:1189。

```text
b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json
```

**［情報］campaign 一意性の要求範囲には訂正が必要です。** spec 内の重複は F:889 が拒否しますが、spec 間の重複を issuer が拒否するわけではありません。I:1194 は集合和で重複を消します。今回の `t2288-f1-<wl>-c1/c2` は全 6 件相異なので問題ありませんが、「issuer が spec 間一意性を検査する」とは記録しないでください。

**7.［情報］実行設定は維持可能。ただし較正との同一性を限定する**

- `timeout_s=120`：C:65 と同値。提示 rep wall に対して約 27–34 倍ですが、成功率の証明ではありません。短縮による timeout は sample を落とし、62 sample 中 **4 件の欠落で 5% 超過**となります。根拠なく短縮する理由はありません。I:1125。
- `probe_timeout_s=30`：R:252 の composite probe 既定 10 秒より長い設定。ただし floor は専用 competing probe を呼ぶため、同じ probe 構成の転記ではありません。F:1623、F:1730。
- `numactl_argv=[]`：C:937 の 1 NUMA node 時の `None` と、**生成するコマンドの numactl prefix が空である点で同等**です。R:539。将来の割当て・affinity 同一性までは保証しません。
- `extra_env={}`：親環境を空にする意味ではありません。runner は親環境を継承し、`FLAGS_` を除去します。R:646。
- `use_perf=false`：floor の必須値です。較正 CLI は perf receipt から決めるため、較正時と同値だとこのコードだけでは断定できません。F:708、C:868。

**8.［情報］spec-only commit C と後続記録 commit の案は整合する**

親案の **P → C（spec 3 本）→ D（fragment・insight・worklog）** は成立します。`source_commit=P`、期待 hash は C の実 bytes、C の OID は D に記録できます。fragment を wave branch に commit し、fold は land 時という提示条件とも衝突しません。

plan 案の「spec＋決定記録を C」も、C 自身の OID を本文へ埋め込まなければ成立します。**loader は決定記録の同時 commit を要求しません。** 親案を採るなら、D に期待集合を記録し終えるまで測定を開始しないことを明記すれば十分です。F:1229、F:1290、V/prereg-5.1-floor-bullet.md:17。

**［nit］生成器の create-only は atomic ではありません。** G:175 の `exists()` と G:177 の `write_bytes()` の間に競合余地があり、dangling symlink も `exists()` では捕捉できません。今回の親による単独生成を blocker とはしませんが、強い create-only 保証とは呼べません。

## 総括

**(a) must-fix 一覧**

- G:42・54 に採用した窓／命名を反映し、seed・最終 spec hash・期待集合の記録を同期する。
- 「1.6 h 上限」「21.5 分の厳密上限」「48 h 隙間で人手分離確認を代替できる」という説明を採らない。
- 同一 spec の w1・w2・finalize を同じ実行 HEAD に固定する条件を後続へ明記する。

**(b) 後続の測定 wave への注意点**

- F660 の登録欠如を前提に、専用 job body、実行体登録、所要 admission と単独性確認、`current_site(require_evidence=True)` が受理する証拠付き起動経路を用意する。`--validate-only` は代替にならない。F:1666、F:3127。
- job body 着地後の H を固定し、両窓と finalize を実行する。
- 各測定 checkout で binary を `place` する。ignored binary は merge されず、配置には現行 policy 一致が必要。V/D2069.md:18、:21。
- queue 待ちと走行時間を見込み、窓末ぎりぎりに開始しない。欠落・窓逸脱後の再実行で create-only 出力を置き換えない。
- 実 campaign の時間分離、n=62、欠落率を証拠確認者が確認する。
- 集約は事前記録した 3 pin と全 summary を渡し、正常入力だけに間引かない。

**(c) 生成器の値で訂正が要る箇所**

G:42 の w2、G:54 の spec 名、G:39 のコメント。それに伴う seed／期待 hash の更新が必要です。**較正 SHA、binary/receipt SHA、records、workload 文字列、既決 perf 値に訂正箇所はありません。**