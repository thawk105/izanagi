# [T-1259] 段 1 brief — qsub -v の 2 本目以降の env 到達と ambient 継承の実測

wave = `dev-wave-t1259-qsub-env-delivery` / branch `worktree-dev-wave-t1259-qsub-env-delivery`
着手時 local main = `442cb549c84d4df40f8cace2039626b4b4548dec`
一次資料 = `docs/archive/worklog-phase3-0816-603.md` の [T-1259]、
`output/insights/2026-09-07_t2324-official-approval-binding/README.md`

## 1. scope (確定)

計算ノードで次の 4 点を実測する。official 床値走行は投入しない。

1. `qsub -v "A=..,B=..,C=.."` の **3 本すべて**が計算ノード job へ届くか。
   値の形は `submit_floor.sh` が実際に組む形 (32 桁 hex 2 本 + 絶対 path 1 本) に合わせる。
2. `-v` に列挙しない ambient env を NQSV が継承するか。投入側 shell に固有名の変数を
   export し、job 側でその不在/存在を観測する。**継承するなら承認 env が投入側 shell から
   漏れて届きうる**ので、承認束縛の前提そのものに関わる。
3. 承認あり (`IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` を渡す) / なしの双方で、job 側の
   env 到達状況を観測する。
4. `floor_campaign.sh` §8 の判定が env 到達に対してどう分岐するかを、実測した env から示す。

## 2. 確定済みユーザー裁定

- official 床値走行の投入は禁止。`floor_campaign.sh` と
  `s8b_floor_campaign.py --mode official` の campaign 本体は起動しない。観測用の短い job だけ。
- 稼働中の床値 wave と競合させない。
- 着手直前の local main から fresh worktree。編集面の重なり検査は起動時に実施済み。
- 規律 2 を緩めない。Codex author = D95。
- 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

## 3. 不変条件

- **計算ノード job は repo へ 1 byte も書かない。** 成果物は repo 外の evidence dir へ書く。
  (`floor_campaign.sh` は `OUTPUT_ROOT="$REPO_ROOT/output"` と束縛されており、
  これを走らせると repo が汚れて他 wave の受入・変異走が全損する。)
- probe は compute-only (`hostname` が `bnode[0-9]+`) で、login では実行しない。
- 承認 env を投入側 shell へ export したまま放置しない (2 の観測でだけ使い、job 単位で閉じる)。
- 実装面は Codex `role=author` の子が書く。親は docs だけ編集する。

## 4. 既存被覆 (純増だけを本 wave の主張にする)

- **[T-2228] の probe が 2026-09-07 に `-v` 2 本渡しで計算ノード job を 2 回実走させている**
  (request `980554.nqsv` / `980676.nqsv`)。2 本目 `IZANAGI_T2228_EVIDENCE_DIR` は
  probe 側で必須 (不在なら exit 2) で、その値の先へ evidence が実際に書かれている。
  よって「2 本目が届く」ことの**間接証拠は既にある**。
- したがって本 wave の純増は (a) **3 本目**の直接観測、(b) **ambient 継承**の有無、
  (c) 承認あり/なしの対比、(d) `submit_floor.sh` が組む値の形での確認である。

## 5. 成果物影響 (DW-G05)

放置すると、official 床値の投入が gen_S の 10 時間確保を消費したうえで driver の CLI 関門で
拒否され、床値が 1 件も出ない。certified 選択が使う床値入力が永久に materialize しない。

## 6. (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a)** [T-2228] の 2 本渡し実績は本件の「2 本目は届く」を実質的に被覆している。
  本 wave は 3 本目・ambient・承認対比に絞ってよい。
- **(P1-b)** driver argv の**実バイト**観測は official 走行なしでは到達できない
  (`floor_campaign.sh` の argv 組立ては build・claim の後段にあり、かつ repo へ書く)。
  よって argv 側は「承認 flag なしで実 driver が CLI 関門で拒否されること」の観測に限定し、
  承認ありの argv は**観測しない**。この非対称を正直に書く。
- **(P1-c)** probe を repo 内 `tools/pegasus/probes/` に置き、
  `tools/pegasus/admission_registry.json`・`orchestrator/tests/test_hooks.py` の 2 箇所の辞書・
  `docs/pegasus-runbook.md` の分類表へ登録する。追加だけで赤になる登録簿が他に無いことを
  段 2 で閉包検査する。
- **(P1-d)** ambient 継承の観測には、投入側 shell で export し `-v` に載せない固有名の変数が要る。
  名前は `IZANAGI_` 接頭辞を避ける (既存 consumer と衝突させない)。
- **(P1-e)** 実 driver (`s8b_floor_campaign.py --mode official --protocol <p>`、承認 flag なし)
  を承認なしで 1 回だけ起動しても、CLI 関門が protocol loader より前に拒否するため
  state を 1 件も変えない。これが成り立つなら「承認なし側」は模擬でなく実バイトで観測できる。
  成り立たなければ (P1-e) は捨てて模擬に落とし、その差を記録する。

## 7. 変更面 (実アンカー)

| # | file | 位置 | 変更 |
|---|---|---|---|
| 1 | `tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs` | 新規 | 観測 job 本体 |
| 2 | `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py` | 新規 | 計算ノード側の観測・記録 |
| 3 | `tools/pegasus/admission_registry.json` | `entries` の probe 群 | 新規 2 件を分類登録 |
| 4 | `orchestrator/tests/test_hooks.py` | 3064 付近 / 3291 付近 | 期待辞書 2 箇所へ 2 件追加 |
| 5 | `docs/pegasus-runbook.md` | 524-525 付近の分類表 | 新規 2 行 |
| 6 | `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` | 新規 | probe の単体検査 |

## 8. 分割方針

実装単位は 1 つ (probe 対 + 登録簿 + 単体検査)。Codex author 子 1 本。
段 2 は read-only codex 1 本、段 3 は異なるレンズ 2 本。
