# 親の独立実測 (段 4 裁定の材料) — [T-1140]

段 2・3 の子には渡していない。子が独立に同じ結論へ到達するかを見るため控えている。

## M1 — (P2) resume 経路は狭まらない (確定)

`orchestrator/campaign/env_contract.py` の `IsolationPolicy(...)` 構築は repo 全体で 2 箇所だけ:

- `:252` `IsolationPolicy(single_process=True, allow_resume=False)` (Pegasus 登録段)
- `:292` `IsolationPolicy(single_process=False, allow_resume=True)` (OTHER / linux-baremetal)

claim 取得は `is_reservation_required(isolation_policy)` = `single_process` が真のときだけ発火する
(`reservation.py:270-277`)。よって **claim を取る契約は必ず `allow_resume=False`** であり、
claim identity を protocol 単位へ変えても、正当な resume 経路は 1 つも狭まらない。
→ 親の (P2) は成立。子がこれを「受理集合が狭まる」と主張したら、この 2 行を根拠に refute する。

## M2 — (P3) 予約照合には既存の設計制約がある (確定)

2026-07-25 [T-088] の段 4 裁定 A-03 (`output/insights/2026-07-25_t088-official-unlock-design.md:49`):

> `script_sha256` は env 自己申告ゆえ wrapper hash 照合は恒真化可能 →
> **real・親が独立確認・採用**。`reservation.py:118-126` の `_ENV_FIELDS` が
> `IZANAGI_RESERVATION_SCRIPT_SHA256` から読み、検証は 64 桁 hex 形式のみ。
> **環境変数同士の一致を authorization gate に数えない**を設計制約とする

同趣旨の再確認が `output/insights/2026-08-11_t8b-restart-integration/verbatim-plan.md:100`:
「既存の `IZANAGI_RESERVATION_SCRIPT_SHA256` は環境自己申告なので admission の根拠に数えない」。

**帰結:** S2 の 3 照合は、照合先が env のままなら恒真ゲートの新設になり、F321/F322 と同じ型の
事故を自分で起こす。照合先は caller の支配外にある実体でなければならない。

| 照合 | 現実側の source 候補 | caller 支配外か | 判定 (親の provisional) |
|---|---|---|---|
| host | `socket.gethostname()` / `os.uname().nodename` | **はい** (OS が返す) | 実装する。boot_id 検査と重なるが独立に効く |
| script_sha256 | 実行中 script ファイルの実体 SHA256 | 部分的 (どの script を走らせるかは caller 次第) | **drift 検出としては実装可、authorization とは呼ばない** |
| nonce | scheduler 所有の create-only receipt | source が実在するか未確認 | 実在しなければ DW-G04 により設計メモへ |

nonce の照合先が実在しないなら、**実装せずに設計メモへ落とすのが正しい** (DW-G04:
発火条件を満たす既存 artifact path か計測 ID を書けないものは実装しない)。
「3 件全部やる」を目的化して恒真ゲートを 1 つ増やすのは、本 wave が直している欠陥そのものである。

## M3 — F321 の実行再現 (probe)

`premise_probe.py` の出力:

```
identity(t)     = 20260816T030000Z-aaaaaaaa
identity(t+1s)  = 20260816T030001Z-aaaaaaaa
same protocol -> same identity? False
claim 1 acquired: 20260816T030000Z-aaaaaaaa.claim
claim 2 ALSO acquired: 20260816T030001Z-aaaaaaaa.claim -> 排他が成立していない
```

**この probe が測っていないもの (子に攻撃させる点):**
- 実際の `run_campaign` 経路を通していない (leaf を直接叩いた)。前段で別の検査が
  二重投入を落とす可能性は、この probe では否定できていない。
- 同一 out_root を前提にしている。別 out_root の場合は identity を変えても排他できない。
- 単一ホスト・単一 filesystem。Lustre/NFSv4 の O_EXCL 意味論は測っていない。

## M4 — 予約照合の authority は「無い」のではなく「shell wrapper の中に既にある」(新事実)

段 2 プランは「script SHA と nonce は独立 authority が Python leaf まで届かない」と結論した。
親が `tools/pegasus/` を独立に読んだところ、**照合そのものは既に実装されている — ただし
Python ではなく shell wrapper の中に**。

信頼の連鎖 (実測):

1. `submit_floor.sh:282-291` — login 側で NONCE (32 hex) を生成し、
   `$SUBMISSIONS_ROOT/$NONCE/` を submission dir にする。
2. `submit_floor.sh:466-495` — `submit-receipt.json` を **`"x"` モード (create-only)** で書く。
   中身に `job_id` (qsub が返した request ID)、`nonce`、`job_script_sha256`、`source_commit` を含む。
3. `submit_floor.sh:411` — `qsub -v IZANAGI_SUBMISSION_NONCE=$NONCE` で
   **scheduler 経由で** nonce を計算ノードへ届ける。
4. `floor_campaign.sh:406-475` — 計算ノード側で receipt を読み、
   - `document["nonce"] != nonce` を拒否 (`:446`)
   - **`normalize_request_id(document["job_id"]) != normalize_request_id(PBS_JOBID)` を拒否 (`:452`)**
   - `job_script_path`、`source_commit`、`job_script_sha256` の形状・値を検査
5. `floor_campaign.sh:740` — `IZANAGI_RESERVATION_NONCE="$IZANAGI_SUBMISSION_NONCE"` を export。

**帰結 (段 4 の争点の書き換え):**

- `:452` の `PBS_JOBID` 照合が **scheduler 所有の錨** である。create-only receipt 単独では
  偽造できる (nonce を自分で決めて dir を作ればよい) が、`PBS_JOBID` と一致させる必要がある以上、
  submitter 所有であっても恒真ではない。裁定材料が言う「scheduler 所有の create-only receipt」は
  厳密には存在しないが、**scheduler 所有の錨に束縛された create-only receipt は存在する**。
- したがって問いは「照合できるか」ではなく
  **「Python leaf は wrapper の照合を信じてよいのか」** である。
  F322 の型 (宣言と強制を別レイヤに置いた結果、強制が抜けた) がここに当てはまる。
  `check_reservation` の caller は wrapper 経由の床値だけではない
  (`s8b_oracle_driver.py`、将来の `loop.py`)。wrapper を通らない caller には照合が無い。
- 逆に、Python 側へ同じ照合を写すと **production では冗長 gate** になる (床値経路では
  wrapper が先に落とす)。DW-M01 の「同じ入力を拒否する層が前後に無いこと」に抵触しうる。
  ただし unit test では wrapper を通らないため変異の帰属は成立する。

親の provisional 裁定 (段 3 の結果を見て確定する): **3 件すべてを 1 wave で扱うという
ユーザー既裁定は、この経路なら満たせる可能性がある。** 「authority が無いから縮小する」という
段 2 の推奨は、wrapper 内の実装を見落とした上での結論であり、そのままでは採らない。
