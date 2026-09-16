## 総括

**現証拠だけで、2026-09-15 cohort を事前登録どおりの valid な cohort と確定し、「済」にしてはならない。**  
ただし、§7 の特定項目に実際に抵触したと断定できるデータも、今回の射影にはない。未確認と `invalid` は区別する。  
§7-9 の時間検査と §7-11 の探索標本排除は実装されており、v1 探索 campaign の mode 読取も追補は禁止していない。  
一方、追補は §0 の更新契約に違反しており、親の「失敗条件に1つも当たっていない」という断定は確認範囲を超える。  
以下は静的検査と親の実測の射影に基づく。ファイル変更・commit・テスト実行はしていない。

## 攻撃 1 — §7 の 19 項目と driver の対応

以下の `F:行` は `orchestrator/campaign/b10_backoff_static_tail_formal.py:行`、`P:行` は `docs/b10-backoff-static-tail-preregistration.md:行` を指す。

| §7 | 失敗条件 | 実際の検査・防止経路と限界 |
|---|---|---|
| 1 | 正しさ5 rep不足・非 certified・anomaly | `F:342–348`、`:418`。集団解析でも `:609–613`。trace の実体は admitted WAL／ビルド経路に依存し、boolean の報告値だけでは証明しない。 |
| 2 | 正しさ不合格 cell が性能測定へ到達 | `F:418`、`:425–426` が採用 attempt の正しさと bench より前の順序を検査。実行経路では `pipeline.py:2436–2454` が不合格時に戻る。**formal loader 単独では過去の全失敗 attempt の到達履歴を監査していない。** |
| 3 | rep ごとの整数カウンタ欠落 | `F:323–338`、`:433`。必要キー、件数、整数型を検査。 |
| 4 | 丸めた abort_rate を解析入力に使用 | `F:336` で整数から再計算し、`:607`、`:618` がその値を解析へ渡す。丸めた率を使う分岐はない。 |
| 5 | 静的8 genome の性能ビルド不足・束縛／hash異常 | 実行前 `F:311–320`、`:758`。報告側でも `:597–598`、`:605`。報告側の digest 検査だけで実バイナリの再検証をしたことにはならない。 |
| 6 | workload・点・rep の欠測／重複／非有限／集合外 | `F:326–337`、`:414`、`:439`、`:575–576`、`:596`、`:607`。 |
| 7 | abort率または throughput の CV ≥ 0.02 | `F:526–536`、`:618–621`。両方を検査し、失敗を追加。 |
| 8 | 支持された上昇 `qL > 0` | `F:567`、`:624–625`。 |
| 9 | sweep >11700秒、または job が18000秒以内に完了しない | **検査あり。** 実行時 `F:739–750`、締切処理 `:679–694`。報告時 `:599–602` が経過秒の有限性・非負性・上限を検査。後述の終了時点の限界あり。 |
| 10 | 別 identity／束縛／source／toolchain で resume、cell継ぎ合わせ | `F:295–306` で構成へ束縛し、`:761` から `loop.py:553–557` の identity 照合付き resume に入る。読取側は `F:388–449` で単一 campaign の採用 attempt を読む。**formal report 自体は全再開操作の独立した履歴証明ではない。** |
| 11 | 探索標本が本格の rep・CV・区間・判定へ入る | `F:351–358` は mode 文字列だけを返す。数値 loader は `:391–398` で formal run kind を必須とし、`:404–438` でその WAL から数値を構成する。通常の入力経路で探索数値を混ぜる fallback はない。 |
| 12 | commit・blob・spec の未記録／bytes不一致 | `F:232–242` で祖先性と文書 bytes を照合し、`:399–400` で lock の束縛を照合。`:660`、`:770` が成果物へ記録。**§0 の更新手続の遵守までは検査しない。** |
| 13 | カウンタ型・範囲・throughput・rep添字違反 | `F:326–337`、`:607`。 |
| 14 | 左端全rep abort 0、右端正値 | `F:543` が対数計算より前に拒否し、`:631–632` で失敗へ。 |
| 15 | provenance 欠落／WAL envelopeとの不一致 | `F:373–385` の snapshot照合、`:425`、`:427–436` の出所導出、`:614–617` の検査。**`analyze_cohort` だけに任意の dict を渡した場合、全 provenance の実 WAL 照合は行わない。正規 loader を通す必要がある。** |
| 16 | 動作点・順序・label／物理値／raw／genome不一致 | `F:245–259`、`:414`、`:439–443`、`:589–596`、`:605`。登録値から対応を生成し、WAL の genome と bench 順序を照合する。 |
| 17 | 3 job の同一性／workload集合不一致 | `F:575–578`。なお、submit receipt の **group id** はこの検査対象ではなく、submission `:71–73` に従う人の確認も必要。 |
| 18 | mode未記録／探索走と不一致 | `F:351–358` で探索 WAL の mode を読み、`:418` → `:348` で照合。`:612` は本走 identity とも照合する。**探索 source の特定 path／lock digest 自体は `config_for` の記録項目にない。** |
| 19 | rep throughput と既存配列の不一致 | `F:335`。解析時も `:607` で再検査。 |

検査例外は `F:464–468`、`:580`、`:631–635` を通じて失敗／`invalid` へつながる。ただし実行前の拒否は、必ず集団 report を生成するという意味ではない。

**「§7-9 を driver が検査しない」という攻撃は成立しない。** 一方、記録する `job_elapsed_s` は `F:767–773` の実行 receipt 作成直前の時刻であり、その後に job script の cleanup・freeze確認・artifact hashing・ルート `completion.json` 作成がある（`tools/pegasus/b10_backoff_grid.sh:642–727`）。したがって driver の秒数だけでは、job 最終終了時刻まで証明しない。既存 insight `:89–91` は833〜838秒と記録しており、今回の超過を示す証拠はないが、親はこの値の測定終点を確認すべきである。

**19項目すべてが未実装という穴は見つからない。しかし、driver と委譲先・実行履歴を合わせて成立する項目がある。** ルート `completion.json` は8 genomeの commit と execution fileの存在を確認するだけである（job script `:694–707`）。それ単独では、CV、非単調性、集団同一性などを排除できない。

## 攻撃 2 — 探索走の版

**追補は、本走 driver が旧 v1 探索 campaign から mode を読むことを禁じていない。**

逐語の対象は次のように限定されている。

- `P:1087`：「**この変更後の `t2418-explore` 新走は**」
- `P:1093`：「**新走の loader は v2 の campaign を選び、v1 への fallback は設けない。**」
- `P:1095`：「**§5 の本格系列 spec は変更対象外として保持し、T-2418 新走の status は本追補に従う。**」
- `P:1098–1100`：旧 campaign と記録された測定事実を保持し、本格系列 spec の bytes・停止基準を変更しない。

「新走」は直前に指定された **T-2418 の変更後の探索走**である。実装上の対応先も特定できる。

- `backoff_extended_sweep.py:643`、`:675`、`:683` は新探索走の scale／spec_slug／trial を v2 にする。
- 同 `:1023–1032` の `_load_t2418_report_points` は、その v2 構成から campaign を選ぶ。
- 対して `F:351–358` は明示指定された campaign を `HISTORICAL_RAW` として読み、`run_kind == t2418-explore` と mode の一意性を確認するだけである。

さらに `P:392–395` は、比較する座標を `payload.workload.tag` と定め、探索実測値を `legacy` と明記している。**比較対象は campaign の版番号ではなく mode の値である。**

親の射影では3 campaign の slug が v1。既存 insight `:96–98` では本走120記録の mode が全件 `legacy`、探索 WAL と一致している。これらから **§7-18 違反は導けない**。v2 directory が深さ4までに無かったことも、v2新走の不在を示す範囲限定の観測であり、本走の無効理由ではない。

## 攻撃 3 — 追補の地位

**§0 の更新契約違反はある。**

`P:20` は変更理由・変更時点を「**本節へ明記する**」と要求する。しかし §0（`:13–36`）に追補の記載はなく、変更は末尾 `:1081–1100` にしかない。Git差分でも末尾21行の追加だけであり、§0 は変更されていない。

ローカル Git の raw bytes から、次を実測した。

| 版 | commit | 文書 bytes | 文書 SHA-256 |
|---|---|---:|---|
| 初版 | `9e97d27b85912c1ce93e9552c7f587bee0d0bb13` | 69,575 | `b9b1f88834a2312841ba6d24c8428febf6490e68cfe6537543462e6b02e6decc` |
| 追補込み・本走の束縛先 | `cad6f46d86ae4dc31edadfbdfad39c65ed73d70a` | 71,231 | `8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a` |

§5 spec の SHA-256 は両版とも同じ：

`08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef`

したがって、**初版と本走が束縛した文書 bytes は違うが、本格の機械可読 spec は同じ**である。追補込み文書も `P:15` では「v1」と名乗っているため、依頼の「v1・発効済み」という名称だけでは初版 commit を一意に指定できない。

親 brief `:35` の「当時から1 bitも動いていない」は、**09-15の束縛 bytes と今回の bytes の比較なら正しい。初版発効時から不変という意味なら誤り**である。既存 insight `:160–164` 自身が、初版 commit では bytes 不一致で停止したはずだと記録している。

ただし、この更新手続違反を **§7-12 の hash不一致に読み替えてはならない**。射影された3件の束縛は追補込み commit／blob／spec で一致している。§4.5（`P:353`）が `invalid` と定義するのは§7への該当であり、§0の記載場所違反を自動的にそのどれかへ当てる規定はない。追補を黙って適法扱いすることも、存在しない失敗条件を追加することも避けるべきである。

## 攻撃 4 — 親の実測の一般化

親 brief には次の修正が必要である。

1. **「5条件はどれも不成立ではない」は、5条件の成立確認ではない。**  
   brief `:38–41` 自身が条件1を未確認としている。正確には「条件2〜5は今回の確認範囲で成立、条件1は今回未実測」。なお、過去の repo root 投入記録は既存 insight `:165–168` にあるため、「投入操作時にしか判定できない」とするのも強すぎる。保存された scheduler 情報から事後確認できる可能性がある。

2. **「§7の失敗条件に1つも当たっていない」は射影された確認範囲を超える。**  
   brief `:58` は全19項目についての断定だが、`prompt-plan.md:48–88` が直接示すのは manifest と report の scalar 値である。全WAL・execution receipt・過去の再開履歴を今回検査した証拠ではない。plan `:28–31` はこの限界を正しく記している。

3. **3探索 directory の実在と、実際に採用された探索 source は別である。**  
   submit script `:239–247` は単一の `B10_EXPLORE_CAMPAIGN` を3 jobへ渡す。3 directoryが存在するだけでは、どれを起動・報告に使ったかは分からない。mode比較に3本とも必要という仕様でもない。

4. **1 cohortの成功から一般的な投入保証・再実験禁止は導けない。**  
   `P:1052` の「初回の本格投入時」は束縛記録の要求であり、二度目の禁止ではない。plan `:4` の指摘は正しい。

## 親が追加で実測すべきこと (1 コマンド単位)

以下は親側で実行する手順であり、ここでは実行していない。

**1. 既存 report と、3 jobの完了 manifest が指す現物を照合する。**  
固定 group のみを対象とし、hash・経過秒・scheduler座標・束縛を表示する。

```bash
python3 -B - <<'PY'
import hashlib, json
from pathlib import Path

base = Path('/work/1/SFC/tanab/b10-backoff-grid-t2500-formal')
group = 'b10-backoff-grid-20260915T061814Z-545445'
stem = 't2500-backoff-static-tail-formal'
report_dir = base / 'group-report-20260915'

def check_manifest(root, manifest):
    for relative, expected in manifest['artifacts'].items():
        actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        assert actual == expected, (str(root / relative), expected, actual)

manifest = json.loads((report_dir / (stem + '-complete.json')).read_bytes())
check_manifest(report_dir, manifest)
report = json.loads((report_dir / (stem + '.json')).read_bytes())
print('verdict:', report['verdict'], 'failures:', report['failures'])

for workload in ('write-heavy', 'balanced', 'read-heavy'):
    root = base / (group + '-' + workload)
    completed = json.loads((root / 'completion.json').read_bytes())
    check_manifest(root, completed)
    campaign = root / 'campaigns' / completed['campaign_id']
    execution = json.loads((campaign / 'reports' / (stem + '-execution.json')).read_bytes())
    print(workload, 'campaign=', campaign, 'job=', completed['pbs_jobid'])
    print(json.dumps(execution, ensure_ascii=False, sort_keys=True))
    assert execution['status'] == 'complete'
    assert 0 <= execution['sweep_elapsed_s'] <= 11700
    assert 0 <= execution['job_elapsed_s'] <= 18000
print('Manifest hashes and recorded elapsed times checked; final job exit time not checked.')
PY
```

**2. 実際の投入元・探索 source・scheduler時刻を保存情報から確認する。**  
出力が無い項目は未確認として残す。探索 path は、その後のWAL再読取に使う。

```bash
rg -n -C 2 'PBS_O_WORKDIR|B10_EXPLORE_CAMPAIGN|Started Request Time|start_time|Elapse|Exit|Finish|End' /work/1/SFC/tanab/b10-backoff-grid-t2500-formal/b10-backoff-grid-20260915T061814Z-545445-{write-heavy,balanced,read-heavy}/qstat-f.stdout
```

**3. 正規 loader から既存WALを再読取し、集団判定をメモリ上で再計算する。**  
下の `EXPLORE_CAMPAIGN` は、手順2または保存された投入argvで確認した**実際の入力**を設定する。推測したv1 directoryを代入してはならない。成果物は作成しない。

```bash
python3.10 -B - <<'PY'
import json, os
from pathlib import Path
from orchestrator.campaign import b10_backoff_static_tail_formal as f

repo = Path.cwd()
base = Path('/work/1/SFC/tanab/b10-backoff-grid-t2500-formal')
group = 'b10-backoff-grid-20260915T061814Z-545445'
binding = f.load_preregistration(repo, 'cad6f46d86ae4dc31edadfbdfad39c65ed73d70a')
explore = os.environ['EXPLORE_CAMPAIGN']
mode = f.load_explore_correctness_mode(explore)
campaigns = []
for workload in ('write-heavy', 'balanced', 'read-heavy'):
    root = base / (group + '-' + workload)
    receipt = json.loads((root / 'completion.json').read_bytes())
    path = root / 'campaigns' / receipt['campaign_id']
    campaigns.append(f.load_formal_campaign(
        binding.spec, binding, path, correctness_mode=mode))
result = f.analyze_cohort(binding.spec, campaigns)
print(json.dumps({
    'explore_campaign': explore, 'mode': mode,
    'verdict': result['verdict'], 'failures': result['failures'],
    'performance_certified': result['performance_certified']
}, ensure_ascii=False, indent=2))
PY
```

これは**現行 reader による再解析**である。当時の実行コード・再開操作の監査を代替しない。§7-2／10について疑義が残れば、同じ3 campaignの全 attempt 履歴と保存された実行情報を追加確認する。

**4. 初版と追補の差分を確認する。**

```bash
git diff 9e97d27b85912c1ce93e9552c7f587bee0d0bb13 cad6f46d86ae4dc31edadfbdfad39c65ed73d70a -- docs/b10-backoff-static-tail-preregistration.md
```

## 親へ返す判断

**P1の「§7全項不該当が確認済みだから、有効な本走として済」は、そのまま承認しない。** 成果物の存在・記録された verdict・今回確認した範囲へ主張を狭め、上記の現物照合を行うべきである。

v1探索 modeの使用を理由とする `invalid` 判定と、v2探索再走の要求は却下する。§0の更新契約違反は明記するが、結果後の文書修正で遡及的に解消したことにはしない。

**現時点では再投入せず、既存 cohort の確認を完了させる。** 具体的な§7違反が実測された場合に、その証拠をもって既存 cohort の扱いを改める。