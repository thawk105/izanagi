## 変異とテストの対応表

**静的判定では M1〜M5 に未対応の変異はありません。実走による KILLED 確認は未実施です。**

以下、`T` は [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2565-certify-repo-root-binding/orchestrator/tests/test_pegasus_calibration_workload.py)、`S` は [submit_certify.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2565-certify-repo-root-binding/tools/pegasus/submit_certify.sh)。追加は **4関数・6ケース**です。K は静的に KILLED と予測、— は生存予測です。

| ケース（`test_submitter_` 以下） | M1 | M2 | M3 | M4 | M5 | 最初の殺傷点 |
|---|---:|---:|---:|---:|---:|---|
| `runs_qsub_in_repo_root[repo]` | — | — | — | — | — | 正常対照。C＝R のため変更行削除を検出しない |
| `runs_qsub_in_repo_root[outside]` | K | K | — | — | — | S:226 → T:1802、実 cwd が C のまま |
| `keeps_relative_attempts_in_caller` | K | K | — | — | K | M1/M2 は T:1818。M5 は T:1763 |
| `keeps_relative_job_script_bytes_from_caller[original]` | K | K | K | K | — | M1/M2 は T:1849。M3/M4 は T:1779 |
| `keeps_relative_job_script_bytes_from_caller[changed]` | K | K | K | K | — | 同上。payload は T:1834 で別値 |
| `preserves_qsub_failure_and_captures` | K | K | — | — | — | S:226 → T:1862、失敗時も cwd が C |

変異箇所と赤の理由：

- **M1/M2：S:226。** C≠R のケースでは、fake qsub の `os.getcwd()`（T:1733）が C を返す。
- **M3/M4：S:211–213。** 両木に存在する別 bytes の script（T:1844–1845）のうち R 側を読む。C 側を hash した pre-submit と不一致になり、T:1779 が落ちる。
- **M5：S:226。** `cd` 後の qsub コマンドへリダイレクトを移す変異では、R 側に相対 submission ディレクトリが無く、open が失敗する。S:227–232 が非ゼロを返し、T:1763 が落ちる。

**自己判定：refuted** — 「6ケース全体が恒真」。ただし `[repo]` 単独を修正の殺傷証拠として数えることはできません。

## 単一理由性

| 変異 | 判定 |
|---|---|
| M1/M2 | **real：cwd 不一致へ絞れる。** `[outside]` では絶対 script・絶対 attempts を使うので、script 読取りと capture は成立する。最初の不一致は T:1802。T:1804 は同じ cwd 条件の重複確認 |
| M3/M4 | **real：誤った script の選択へ絞れる。ただし assertion は多重。** 前段の存在確認 S:67、hash S:117、clean 検査 S:110 は通る。衝突 file は両方存在し、`output` は clean 検査対象外 |
| M5 | **real：リダイレクト先の解決基準へ絞れる。** C 側の staging 作成と preflight は通り、変更したリダイレクトで初めて失敗する。fake qsub は起動しない |

**厳密に「同じ不正状態を検出する別 assertion も無い」とするなら、M3/M4 は単一理由性を満たしません。** T:1779 のほか、T:1787、T:1850–1852 でも検出できます。したがって、末尾の bytes assertion を実際の殺傷点として登録するのは誤りです。登録先は先行する **T:1779 の submit-hash／qsub-read-hash 照合**です。

**自己判定：refuted** — 前段の別 gate が変異を拒否して対象機構まで届かない、という疑い。  
assertion の重複自体は **nit**。放置しても誤 script の受理集合は広がらず、must-fix にはしません。

## 機構を通らない緑

**自己判定：refuted — 今回の検査対象機構を stub が置き換えている。**

- 実 submit をコピーして実行する：T:1497–1501、1746–1748。
- `subprocess.run(cwd=caller)` で実際の投入元を変える：T:1759–1761。
- fake qsub は cwd を設定せず、実 cwd と実 argv 最終要素の file bytes を読む：T:1732–1736。
- fake-bin と observation は絶対 path：T:1720–1722、1755–1756。cwd 変更後も同じ観測器へ到達する。
- observation は qsub 自身が生成する。helper は終了後に読む：T:1764。期待 cwd を観測値として注入していない。
- 相対 script の負例は C／R の別 file を名指ししている：T:1843–1845。

preflight の4コマンドは成功 stub ですが、cwd 変更・script 解決・shell リダイレクトは実処理を通ります。

証明範囲は **qsub 起動プロセスまで**です。scheduler による `PBS_O_WORKDIR` 設定や job 実行の証明ではありません。これは段4裁定 `s4-adjudication.md:41–45` と一致します。

## 既存テストへの影響

**自己判定：refuted — 既存テストの弱体化。**

差分の旧 blob `24ddc4ec2` と現行ファイルを AST 比較し、**旧42関数すべて同一、新規4関数**を確認しました。期待値の反転・緩和、skip、削除はありません。

`_run_submit_dry_run_in_clean_fixture` は次を維持しています。

- 引数・既定値・返却型：T:1524–1532。
- dry-run コマンドと追加引数：T:1536–1548。
- rc 判定・表示 argv の処理：T:1555–1565。
- 5要素の返却順：T:1585–1591。

切り出した fixture 作成は T:1493–1521。旧処理と同じ順序でコピー、git 初期化・commit、staging 作成を行います。

## 揮発 payload

**自己判定：refuted — 揮発値の焼き込み。**

新規期待値に作業木 hash、時刻、nonce、環境固有の固定絶対 path はありません。

- cwd／script path は各ケースの `tmp_path` から導出：T:1802、1805–1806、1850。
- submission は実際に生成されたディレクトリを取得：T:1774–1776。
- script hash は実 bytes と入力 payload から計算：T:1732–1735、1852。
- `12345.server` と rc=7 は stub の制御入力であり、揮発値ではない：T:1741、1785、1860。

payload を2種類に変えて確認する構造はありますが、実測はしていません。入力だけを書き換えて配送 bytes が追従しなければ T:1851–1852 が赤になります。正しく追従する実装が入力変更後も緑になるのは期待どおりです。

## 波及と所要台帳

**自己判定：real — 追加6ケースは既存台帳に未登録。欠落即失敗という解釈は refuted。**

参照経路は次のとおりです。

| 対象 | 確認した参照・影響 |
|---|---|
| `test_pegasus_tools.py` | submit を直接検査する構文テスト :125–131、policy 検査 :177–184、modules 契約 :734–742、独立 fixture の dry-run :1669–1731。変更した helper の利用はない |
| 収集 | `pytest.ini:15` の `testpaths = orchestrator/tests` により新規ケースも収集対象 |
| xdist group | `conftest.py:2145–2152` は登録 node に group を付与。対象ファイル名の登録は無く、新規ケースにも明示 group はない。書込み先は各 `tmp_path` |
| 台帳 lookup | `conftest.py:1675–1695`。未登録は `None` を返し、欠落だけでは例外にしない |
| 台帳 schema meta-test | `test_update_acceptance_duration_ledger.py:306–325` は台帳内部の件数・型を検査。収集数との完全一致ではない |
| 固定 node 集合 meta-test | 同ファイル :364–388 の対象 suite に calibration workload は含まれない |

**赤になり得る node：**

`orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

根拠は同ファイル **:673–684** の全収集、**:704–712** の台帳照合と `coverage >= 0.90` です。

追加前の対象収集数を N、被覆数を K とすると、この追加だけなら被覆率は **K/N → K/(N+6)**。90%を割れば赤になります。**6件欠落だけで必ず赤になるわけではなく、現時点の被覆率は未実測です。**

放置時の影響は「6ケースの所要時間が未知となり、全体被覆率が低下する」。現状の証拠では **backlog／親の受入確認事項**であり、台帳更新を must-fix とはしません。

## scope 外の real

新規に追加すべき scope 外所見はありません。

既決の留保として、相対 PATH による qsub 解決先変更と CDPATH／相対 repo-root の問題は残ります（`s4-adjudication.md:72–82`）。本テストの絶対 fake-bin はこれらを検査しません。裁定どおり追加対応は要求しません。

## 総括

**must-fix は静的検査では見つかりませんでした。**

M1〜M5 はすべて殺傷経路があり、既存42関数も維持されています。親の変異検証では、M3/M4 の最初の殺傷点を **T:1779** として扱ってください。台帳欠落は実在しますが、赤の条件は全収集被覆率90%未満です。

pytest・変異・scheduler の実走、編集、commit は行っていません。