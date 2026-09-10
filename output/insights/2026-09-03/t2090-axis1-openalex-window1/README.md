# [T-2090] 軸 1 OpenAlex — 新 epoch の 1 窓目の取得 (2026-09-03)

新 epoch `AX1-20260902-E1` で OpenAlex の取得を初めて実行した記録。
**条件 1 の修正は効いた。塞ぎは 1 段先の条件 5 へ移った。**

凍結した実行記録は `docs/related-work/claim-survey/2026-09-03-axis1-search-execution.md`。
本 directory は逐語成果物と部分 mirror を置く。

## 中身

| file | 中身 |
|---|---|
| `stage2-plan.md` | 段 2 の実装プラン起草 (codex, read-only, reasoning=xhigh) の逐語 |
| `stage3-consult-correctness.md` | 段 3 敵対相談 lane sol (正しさ境界) の逐語 |
| `stage3-consult-reachability.md` | 段 3 敵対相談 lane luna (実効性と経路の完全性) の逐語 |
| `fetch-window1.jsonl` | 起動した leaf ごとの argv 結果 (state, request_count, 起動前残量) |
| `leaf-order.txt` | 起動順に並べた leaf ID |
| `mirror/` | 生 bundle の部分複製 (`pages` / `checkpoints` / `state` / `wal` / `manifest.json` / `MANIFEST.sha256`) |

## 生 bundle の所在

**live bundle root (再開と検証はここで行う):**
`/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle`

`manifest.json` の SHA-256 = `ff25f09af3840d35b4bc3cb36c0fa8b9df283f0cce055c6c117b71707832e9ca`

`mirror/` は同 bundle の `raw/` と `ledgers/` を除いた複製である (合計 102 MB のうち
raw 48 MB・ledgers 52 MB を除いた約 2.3 MB)。**mirror 単独では `verify_bundle` を通らない。**
理由は 2 つある。(1) checkpoint が記録する `bundle_root` は上の絶対 path であり、
`validator.py` は検証先 path との一致を要求する。(2) manifest の path 集合に raw と ledgers が
含まれる。**取得が完了した時点で bundle 全体を repo へ commit する。**
走行途中の 102 MB を窓ごとに commit すると repo が膨らむため、本 wave では見送った。

## 何を測ったか

### 1. 条件 1 は現行実装で通る (生応答で確認)

新 epoch の初回取得で、取得した全 93 頁の条件 1 が `可` だった。
事前のオフライン診断でも、旧 epoch の唯一の OpenAlex 生応答に対して
旧の完全一致比較が `不一致`、現行の順序非依存比較が `一致` を返した
(この診断は bundle の外で行い、旧生応答を新 epoch の証拠へ再包装していない)。

### 2. 塞ぎは条件 5 へ移った — U11 が実データで発火した

頁ごとの条件 1〜6 が全頁で `可` でも、leaf 全体の条件 5
(`distinct_work_id_total_mismatch`) が落ちる leaf がある。破れ方は次のとおり。

| leaf | 索引の申告総数 | 取得行数 | distinct | 重複 | distinct − 申告 |
|---|---|---|---|---|---|
| `Q1@openalex` (1 回目) | 736 | 736 | 736 | 0 | 0 |
| `Q2@openalex` (1 回目) | 1606 | 1607 | 1605 | 2 | −1 |
| `Q4@openalex` | 4698 | 4705 | 4694 | 11 | −4 |
| `Q5@openalex` | 6122 | 6130 | 6116 | 14 | −6 |

結果集合が大きいほど cursor の頁境界で重複が増え、distinct が申告総数を下回る。
これは amendment §8 の未決項目 **U11**「索引が同じ work ID を頁境界で 2 回返しつつ
総件数では 1 回しか数える場合の条件 5 の扱い。現契約では `未完走` になる」が
想定した状況そのものである。

### 3. 条件 5 は走行間で非決定的である (両方向の反転を実測)

親の driver の重複除去条件が壊れており、`Q1` と `Q2` を意図せず再走した。
その結果、**判定が両方向に反転した**。

| leaf | 1 回目 | 2 回目 |
|---|---|---|
| `Q1@openalex` | `branch_complete` | `blocked_on_ruling` / `distinct_work_id_total_mismatch` |
| `Q2@openalex` | `blocked_on_ruling` / `distinct_work_id_total_mismatch` | `branch_complete` |

**同じ登録 request を同じ日に 2 回投げて、条件 5 の判定が逆になった。**
索引側の申告総数と返却集合が走査中に動くためであり、実装の欠陥ではない。
条件 5 は現行の形では OpenAlex に対して安定した判定にならない。

この再走は親のミスだが、機構は正しく扱っている — 2 回目は `attempt_number=2`・
別 raw file (`.a02`) として記録され、1 回目の証拠は上書きされていない。
検査器は `bundle_validation_complete: true` を返し、構造は健全である。
検査器の leaf 判定は**最後の attempt を採る**ため、`Q1` は `incomplete_with_evidence`、
`Q2` は `complete` になっている。

### 4. 無償枠の自己施錠は発火しなかった

`permits_next` は残量だけを見るので、窓を使い切った走行の観測 (`remaining < 40`) が
持続化されたときにだけ次窓を止める。本走行は leaf の起動と起動の間で残量を読み、
残量 200 で新規起動を止めたため、施錠状態に入っていない (終了時の残量 60)。
**runner を変えずに「窓に収める」が達成できた。**

窓をまたぐ継続取得の設計 (U12) と、証拠を「登録 commit の後に取得された」事実へ
束縛する方式 (U13) は、いずれも未決のまま残る。段 3 lane sol は、
枠の発行規範 (`remaining - 30 >= cost`) を緩める実装は凍結契約 §4.1 の改訂に当たり、
U12 の裁定なしに採ってはならないと判定した。親はこれを採用し、本 wave では実装しない。

## 費用

生死確認 1 request + 取得 93 request = 合計 94 request (1 request = 10 credits)。
1 窓の上限は 97 request (`limit=1000`、`credits_per_request=10`、`quota_credit_reserve=30`、
`remaining - 30 >= 10` すなわち残量 40 以上で発行可)。
