# 段 1 brief — [T-2632] 順序 (2) precheck: B-4 事前登録 §5 の 2 欄 (校正済み PerfConfig / env_tag) を今日記入できるか

wave `dev-wave-t2632-b4-s5-precheck`、起点 local main `38353207f`。実装面差分ゼロ (P2 precheck)。記入はしない。

## 研究前進

論文 §8 の B-4 (還流 on/off ablation) の事前登録を発効へ近づける。完了判定 = 2 欄それぞれについて
「今日記入できるか / できないなら何が要るか」を一次資料の現物で確定し、裁定パッケージにする。
floor 欄 (A-5 裁定待ち) と順序 (3) の campaign 起動には触れない。

## 確定済みユーザー裁定 (現物で読んだ)

- D1483 (2026-09-02、D1510 で再確認、以後改訂なし): **§5 全欄の記入は「床値の 12 行裁定・測定・成果物の採用裁定」の後に順序どおり個別に閉じる。3 者の指名は §5 の他欄 (実行 site・校正済み PerfConfig・…) を解禁しない。**
- D1641 決定 3: 床値の凍結 12 行。実行 site = Pegasus 計算ノード (gen_S)、env_tag = site resolver から機械導出、校正済み PerfConfig = calibrator の出力を採り AI が委任の下で承認。
- D2088 / D2089 / D2090: 床値 spec の perf_config。records = 採用較正の saturation.records、threads 48、extime 3 (取得構成から復元)、ycsb_max_ope 10、**reps 5 は AI の選択 (床値 spec 用)**。3 cell = rr95 5c836a22… / rr50 94a4b79f… / rr5 2b7ba072…。
- D1854: §5 PerfConfig 欄が 1 セルであることは意味上の個数を 1 に固定しない。
- D1484: 環境世代 g2 の発行・発効は鎖の末尾 (床値正式測定の後)。D1537: 自己整合しない較正 (g1 の calibration_ref) は健全な世代の発効まで床値に使わない。
- §5.1 (規範): PerfConfig 欄は「calibrator が決めた値へ差し替えるまで記入しない」。env_tag 欄は「driver と site 確定 → 同じ site resolver から機械導出して確認 → driver・site・tag の 3 つ組、環境契約の artifact path と hash、確認者を発効版へ併記」。§0: 値セルに説明文・条件を書かない。実走前検査 (`p3_b4_admission_record.py`) は非空・予約 sentinel 無しだけを見る。

## 親の実測 (本 wave)

- 較正 3 件: tracked、sha256 一致、`threads=48`、`env_tag=pegasus`、`clocks_per_us=2100`、records 1M/1M/2M、workload 3 key (`ycsb_rmw="0"`)。**key に `extime` 無し。`reps` は cost formula 文字列内のみ**。取得 argv (job-staging 3 件、tracked) に `--extime` 無し → CLI 既定 3 (`calibrator/cli.py`)。
- site resolver: login で `current_site()=PEGASUS_LOGIN`。base driver の resolver `p3_s4_loop._admit_env_contract(PEGASUS_COMPUTE)` → `pegasus`、contract_sha256 `e576e9cd…`。registry 属性 `lookup_required_attestation_contract()` と同一 object。base driver は site→tag を literal dict で持つ (registry 属性からは導かない) が値は一致。
- 契約世代: active = g1 `e576e9cd…` (calibration_ref = `753f535a…`)、g2 `1346c20b…` (calibration_ref = `94a4b79f…`) 登録済み未発効。活性化 artifact `env_contract_activations/00000001.json` sha256 `6a44b5b1…`、`env_contract.py` sha256 `292bbed3…`。契約に JSON artifact は無く code + activation で定義される。
- 既存 base campaign lock: records 100000 / threads 4 / pin 028f34d / measurement_env 無し (= 較正済み動作点でも Pegasus でもない)。
- `PerfConfig` (pipeline.py): records / threads / workload / extime=3 / reps=5。`performance_correctness_workload` は workload 4 key (`ycsb_max_ope` 含む) を要求。`default_perf()` は `ycsb_rmw="false"`、較正は `"0"`。

## 親の provisional 裁定 (攻撃対象)

- (P1) **今日は 2 欄とも記入できない。第一の理由は D1483 の順序** (床値の測定・採用裁定が未了)。値の実在とは独立に効く。
- (P2) 順序を除いても PerfConfig 欄は閉じない: records / threads / workload は較正 3 件から供給できる、extime は取得構成からの復元 (D2088 と同じ導出、較正の出力値ではない)、**reps は出所が無く B-4 用の承認が無い** (D2088 の 5 は床値 spec 用の AI 選択、B-4 転用は未認可)。欄の形 (3 較正 pin + argv pin + reps の出所を 1 セルにどう置くか) と記入者の指名も未裁定。
- (P3) env_tag 欄: tag `pegasus` は機械導出できる (実測)。閉じないのは (a) B-4 本走の site が明文で裁定されていない (D1641 決定 3 は床値の site。床値が対象動作点である以上 同 site・同 tag が必要なので実質一意、ただし読み)、(b) 「環境契約の artifact path と hash」がどの世代を束ねるか — g1 (active、自己不整合 calibration_ref) を書けば g2 発効 (D1484、鎖の末尾) で書き直し、g2 を書けば resolver が導出しない前方参照 pin、(c) 確認者が未指名 (D1483 が 3 者指名の他欄への波及を明文で否定)、(d) 併記の形 (§0 と `key=value; ` 複合値の先例 = 対象 driver 欄・model snapshot 欄)。
- (P4) live の site 判定 (`current_site()=PEGASUS_COMPUTE`) は計算ノードでしか出ないが、site が既決なら login からの静的導出で「同じ resolver から機械導出」は満たせる。計算ノード dispatch は本 precheck に不要。
- (P5) 推奨: 確認者・記入者はいずれも thawk105 名義の AI 委任 (D1266 / D1641 決定 1 と同型) を新 D で指名。reps は B-4 用に別途裁定 (候補 5、根拠は PerfConfig 既定・床値 spec と同値; AI 候補を無裁定の既定にしない)。

## scope / 不変条件 / 成果物

- scope: 記入可否の確定と裁定パッケージだけ。§5 の bytes・実装面・gate・台帳を変えない。floor 欄・campaign 起動・供給増加基盤に触れない。規律 2 を緩めない。
- 成果物: `output/insights/2026-09-17/t2632-b4-s5-precheck/README.md` (+ verbatim)、spool fragment (worklog 1 本、decisions は裁定パッケージを D にしない — 未裁定を既成事実化しない)。
- 分割: 段 3 敵対相談 2 本 (read-only codex): lens A = 裁定整合 (D1483 / D1641 / D1484 / D1537 / §5.1 の読み違い、P1〜P5 の反証)、lens B = 機械導出と現物 (resolver・契約世代・較正 key・argv・PerfConfig 型の再計数、親の実測の誤り)。
