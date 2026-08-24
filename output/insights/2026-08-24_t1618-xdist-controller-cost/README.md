# T-1618 xdist controller cost replay harness

状態は「pilot と本計測を実走済み・本計測結果を durable 昇格済み」である。production、既存 test、
pytest 設定、duration ledger は変更しない。本 directory の source、compact 入力 snapshot、gzip した
lossless raw result、人向け summary は tracked promotion 対象だが、attempt ごとの checkpoint、trace、
raw result、success receipt は ignored runtime root に残す。

## 一次量と主張境界

経路 A は実 `LoadGroupScheduling` の `worker_collection.index()` を通常 list と O(1) index map
control で駆動する。値は gross CPU cost ではなく whole-replay の
`marginal_replay_cpu_saving_vs_o1_control_s` である。slot probe 数は一次量として別に残す。

経路 B は実 `_pending_of` と incremental oracle を caller ごとに差し替える。all-real と
all-oracle の総差、caller 条件付き marginal、interaction residual は別 field であり、caller 値を
加法内訳とは扱わない。`protocol-only` と `pass-event` は、保存されていない DSession event 列と
同時刻 workerfinished tie order を範囲化する別 scenario である。

61.3 秒は historical single-run hybrid residual の診断値に限り、占有率の分母や物理的費目には
使わない。全 replay は hot replay である。128 MiB touch を使う値は
`pre_touch_memory_pressure_diagnostic` とし、cold lookup を主張せず、採用不可に固定する。

## 入力 snapshot と provenance

`input-manifest.json` は同じ nodeid を record と複数 collection に展開しない v2 compact schema で
ある。item table を population ごとに一度だけ保存し、controller order は integer index で表す。
20,664,520 bytes の v1 から 4,387,959 bytes へ縮小した。外部 K=1 groupmap/JUnit と K=2 session
artifact が失われても replay に必要な nodeid、group、duration、outcome、order、occupancy はこの
snapshot 内に残る。

K=1 の groupmap 挿入順は歴史的 collection 順へ束縛できない。その controller は
`reference-k1-groupmap-order-conditional` とし、歴史的 K=1 値への接続を禁止する。K=2 も実走時
HEAD、ledger bytes、conftest bytes、ordered worker digest の同時束縛が無いため
`provenance_closed=false` である。

production `_reorder_acceptance_items_by_duration` を直接使い、別に事前登録した expected order digest
へ exact 照合する。pre/order と post/order が同一なら停止する。failed-pair common-prefix sum は
並び順の gate ではなく、同一 multiset 上の数学的不変量としてのみ記録する。

`login-collection.log` は `command=` を exact JSON list として照合し、nodeid は `stdout:` と
`stderr:` の間からだけ採る。section 外の nodeid 風行は拒否する。

## certification と event replay

全 4 controller と全 2 scenario、計 8 certification を性能 block より先に完了する。oracle 値、
behavior transcript、clone control は replay の正しさの certification であり、一つでも失敗すれば
全体を停止して性能値を生成しない。K=2 occupancy はこれらと別の Path B 採用 gate である。48 worker
の sorted item-count vector と group-to-workers を exact 比較し、不一致ならその controller/scenario
の Path B を `adopted=false` とするが、他の計測を含む走行は
継続する。許容幅は設けない。不一致時も expected/observed の両 vector、missing/unexpected、両分布、
group-to-workers の expected/observed と一致判定を raw result の `occupancy_gate` にすべて残す。

Path A の `adoption_gate_results` は primary measurement status、minimum pairs、ABBA/BAAB balance、
order-effect、negative-control CI、negative-control order、non-pilot を原子的に記録する。
Path A/B とも採否を表す field は各 leaf の `adopted` だけである。
Path B の `adoption_gate_results` は occupancy exact match、total measurement、全 caller measurement、
negative control、non-pilot の各判定を分けて記録する。`adopted=true` は従来どおり全項目が true の
場合だけである。global certification の status は正しさだけを表す
`correctness-passed-before-performance` とし、occupancy の passed/failed/not-applicable 件数は別の
`occupancy_adoption_summary` に記録する。

worker collection の decode、string clone、O(1) control 構築、manifest load は clock 前に行う。
clock 内は production schedule と event replay だけで、diagnostic transcript は certification 走だけが
生成する。各 worker の最後の protocol 完了後に workerfinished を virtual-time heap へ入れ、他 worker
event と時刻順に処理する。

certification 前に import 済み xdist 3.8.0 の package root、loadscope、loadgroup、dsession の
resolved path と SHA-256 を manifest へ exact 照合する。さらに pin package を提供する
`sys.path` entry より前の directory、module file、zip entry に xdist provider がないことを直接検査し、
一つでもあれば停止する。`PYTHONPATH` の有無自体は採否条件にせず、raw result の environment へ
`absent`、`empty`、`set` の区別と値を逐語で記録する。

## 完走設計と統計

freshness の単位は一 replay ではなく paired block process である。一つの fresh fork が ABBA または
BAAB の 4 replay を実行して終了する。親は compact manifest と replay input を一度だけ decode し、
最大 48 paired block を別 core で並列実行する。各 block は attempt 固有 checkpoint へ atomic 保存する。

本計測は各採用候補を最低 30 balanced block で測り、95 percent CI が 0 を跨がず相対半幅 0.20 以下
なら停止する。未収束なら 60 block までを一括並列追加する。negative-control CI 全体と ABBA/BAAB
order-effect CI 全体が、事前登録した絶対 noise 範囲 `[-0.010, +0.010]` 秒に入ることを別 gate にする。

K=1,2,4,8 は各 K で同じ 30/60 block 規則を使う。block ごとの四点から slope を作り、その 95 percent
CI が 0 を跨がず、全 K の採用 gate と最大相対残差 0.10 gate が通る場合だけ
`beta_hot_repetition_s` を生成する。失敗時は slope field 自体を出さない。

full run は開始時に full-size path A と worst-case K=8 path B の calibration sample を実測する。
raw result の `estimated_wall_s` は「最大 observed sample wall x planned maximum sample count /
effective parallelism x 1.50 + certification + calibration」で作る。上限 sample 数は 21,632、48 CPU
node 上の保守的 effective parallelism は 30 である。見積もりが 10,800 秒以上なら性能 block 前に
fail-closed する。完了後の実時間は `observed_wall_s` に残す。

## pilot

pilot は full と同じ 4 controller、2 scenario、全 caller、negative control、K=1,2,4,8、global
certification、validator、receipt を通す。規模だけを controller あたり最大 256 item、8 worker、2
paired block、最大 4 process へ落とす。

    PYTHONDONTWRITEBYTECODE=1 \
      python3 output/insights/2026-08-24_t1618-xdist-controller-cost/measure.py \
      --pilot

この手順は login shell の `PYTHONPATH` が設定された状態でも通る契約である。空環境との比較確認が
必要な場合だけ、同じ command を `env -u PYTHONPATH` で追加実行する。

## tracked artifact allowlist

本 directory の非 ignored file は `artifact-allowlist.json` で SHA-256、bytes、class を束縛する。
検査は全 entry の実体を再計算し、entry の欠落、値の不一致、allowlist に無い非 ignored file の混入を
すべて非 0 で拒否する。tracked artifact を意図して変更した場合だけ、repository root から再生成して
直後に検査する。allowlist 自身は stable self hash を持てないため entry から除外するが、file count と
directory 全体の bytes には含める。

    python3 output/insights/2026-08-24_t1618-xdist-controller-cost/verify_artifact_allowlist.py \
      --regenerate
    python3 output/insights/2026-08-24_t1618-xdist-controller-cost/verify_artifact_allowlist.py \
      --verify

fix4 段では同じ最終 source を `PYTHONPATH` set と absent の 2 条件で実走した。
`pilot-fix4-pythonpath-set-20260825-a` は oneAPI の値を逐語記録して 12.141 秒、
`pilot-fix4-pythonpath-absent-20260825-a` は `state=absent,value=null` を記録して 11.443 秒で完走した。
各 run は 800 replay sample、8 certification、4 controller result を含み、shared validator を通った。
raw result は `pilot=true`、
`performance_values_emitted=true`、全 leaf `adopted=false`、全 aggregate blocked、
`selected_next_experiment=inconclusive` を自記する。pilot 値は性能証拠に使えない。

## 本計測、attempt、promotion

計算ノード投入は親だけが repository root から行う。

    python3 output/insights/2026-08-24_t1618-xdist-controller-cost/submit_t1618.py

submitter は local dispatcher import より先に自分の `os.environ` から `PYTHONPATH` を除き、repository
root を `sys.path` へ追加して、resolved module path が repository の `tools/` 配下であることを検査する。
bytecode を全 local import 前に禁止し、明示 child environment からも `PYTHONPATH` と非採用の tests
allowlist 値を除く。ただし計算ノード側で再設定される `PYTHONPATH` は許容し、上記の実体 pin と shadow
検査で安全性を直接確定する。attempt ID は environment ではなく pytest argv の absolute
`--basetemp=<attempt-root>/pytest-tmp` で計算ノードへ渡す。
entrypoint は pytest config の basetemp を読み、その親 directory 名を attempt ID として取り出し、
`measure.resolve_attempt_dir()` と basetemp 全体を exact 照合する。欠落、相対 path、leaf の違い、
owned runtime root との不一致はすべて計測開始前に拒否する。run root は毎回
`output/runs/t1618-xdist-controller-cost/<attempt-id>/` となり、PBS walltime は 03:00:00、harness
deadline は 10,500 秒である。

full run 成功時だけ同一 attempt 内に `success-receipt.json` を作る。receipt は attempt ID、PBS job
ID、raw result SHA-256、manifest SHA-256、全 measurement source SHA-256 を束縛する。promotion は
attempt と job ID を明示し、Draft 2020-12 schema、shared deep validator、trace、receipt、現 durable inputと計測時 source の
exact 一致を再検査する。計測後に改訂できるのは promotion utility 自身だけで、その計測時 hash は
raw result と receipt に残し、他の measurement source は現在の bytes と exact 一致させる。

    python3 output/insights/2026-08-24_t1618-xdist-controller-cost/promote_result.py \
      --attempt-id <attempt-id> --job-id <PBS-job-id>

pilot promotion は常に拒否する。durable 成果物の作成は runtime 計測とは別の tracked mutation
であり、create-only である。

durable raw result は `measurement-result.json.gz` とし、検証済み `raw-result.json` の bytes を情報を
落とさず gzip level 9 で圧縮する。promotion は gzip を展開して非圧縮 bytes の SHA-256 を再計算し、
receipt が束縛する raw SHA-256 と exact 一致しなければ成果物を残さない。
`measurement-summary.json` は 64 KiB を上限とする人向け summary で、per-sample `blocks` と
event ごとの巨大列を除く。population/controller、n、worker 数、Path A/B の値と採否、slot probe、
caller count と item/scope visit、occupancy gate summary、K=2 aggregate、decision rule、isolation、
environment、raw/gzip/receipt/manifest/source の hash 束縛を収録する。両 file は一組で create-only
生成する。非圧縮 `measurement-result.json` は durable 構成に含めない。

本計測 `attempt-20260824T163114Z-3212024-f1301e32`、PBS job `0:944585.nqsv` の raw result は
14,341,162 bytes、SHA-256 は
`78ebad1d3bb0192fec80986d11c972a73c10a64469bfce5837ac72de6a300e30` である。promotion 実走で
`measurement-result.json.gz` は 476,890 bytes、`measurement-summary.json` は 57,741 bytes となり、
gzip 展開後の SHA-256 が raw result と exact 一致した。fix6 最終 source の `--pilot` も
`pilot-20260824T165905Z-2` として 11.110 秒で完走し、その promotion は拒否された。

## schema、採否、次の一手

`raw-result.schema.json` の result v4 は sample、block、CI、path A/B、linearity、occupancy、aggregate、attempt、
environment まで nested object を閉じる。生成直後と promotion 直前の両方で、宣言された Draft 2020-12
schema 全体を実データへ適用する。Pegasus の jsonschema 3.2 では named Draft 2020-12 class が無いため、
この schema が使う両 draft 共通 vocabulary を Draft 7 engine で評価する compatibility path を持つ。
dialect URI は exact 検査し、schema 自体と instance の不一致はいずれも fail-closed である。

続いて同じ意味検査を `measure.validate_raw_result` が共有し、controller 集合、population 対応、有限数、
trace record、Path A の全 gate と採否、occupancy、Path B の全 gate と採否を leaf から再計算する。
さらに K=2 aggregate、decision rule、top-level status を再構成して raw と exact 比較する。
occupancy の vector、multiset 差分、分布、group map と exact 採用判定も再計算し、どの派生 field でも
leaf と矛盾する raw result は拒否する。

top-level の `performance_values_emitted=true` は値が JSON に存在するという事実だけを表し、採否を
表さない。top-level status は pilot と isolation/authoritative envelope から決まり、採否は Path A/B
leaf の `adopted` だけで決まる。summary は primary の `abba_baab_balanced` と order-effect gate/CI、
negative-control の CI/order gate、Path A の `adoption_gate_results` を残すため、summary 単独で
不採用理由を追跡できる。

K=2 aggregate は全 shard `adopted=true` の場合だけ数値 field を生成する。そうでなければ status と
`all_shards_adopted=false` だけを残す。次の実験は K=2 path A の adopted aggregate CI と事前 threshold
0.500 秒から一つだけ機械選択し、CI が threshold と重なるか aggregate が不採用なら
`inconclusive` とする。D747 の削除反実仮想は本 wave では閉じない。

## 書込み境界と限界

prepare の `--output` はこの directory の `input-manifest.json` exact path に限る。runtime は attempt
directory 内だけへ書く。README、allowlist、compact input、`measurement-result.json.gz`、
`measurement-summary.json` の tracked promotion は runtime とは別 mutation である。`pytest.ini` の
`testpaths=orchestrator/tests` と
`norecursedirs` の `output` により通常受入 collection への静的 delta は 0 である。

exclusive placement は証明できないため full result も `isolation-unverified`、`authoritative=false`
のままである。process evidence は `whole-run pre/post snapshots only` であり、短命 peer を連続監視
したとは主張しない。
