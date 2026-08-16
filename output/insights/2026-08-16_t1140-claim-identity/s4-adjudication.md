# 段 4 裁定 — [T-1140] 床値 claim identity を protocol 単位の排他にする

2026-08-16 08:40 JST / wave dev-wave-t1140-claim-identity / base main tip 10813338

## 裁定の結論

**実装しない。ユーザー再裁定へ返す (4→7→8→9)。**

指示された修正の「正しい形」が、実測により**一意に定まらないこと**が判明した。
どちらの形を採るかで受理集合が逆向きに変わり、片方は床値 campaign を恒久的に使用不能にする。
これは裁定時に見えていなかった事実であり、DW-S04 の
「承認済み裁定は裁定時の未見事実でだけ止め、親は不採用にせず新事実を添えて再裁定へ返す」に従う。

**ユーザー裁定 #14 (3 つを 1 wave へ) を不採用にしたのではない。**
その裁定を実行しようとした結果、裁定文が前提にしていた 2 つの事実が偽だと分かったので返す。

## 決め手 — 実測 D1: protocol 単位の claim は床値 campaign を 1 回で永久停止させる

`campaign_claim.acquire_claim` は **release も stale 回収も持たない永久 one-shot** である
(`campaign_claim.py:167-174` の docstring が「claim は crash 後も残す。stale 判定、自動削除、
release は意図的に存在しない」と明記)。identity が run 単位である今は、run ごとに別 claim が
できるため、crash も preflight 失敗も次の run を妨げない。

identity を protocol 単位にすると、この性質が反転する。親の実測:

| 実測 | 値 | 出所 |
|---|---|---|
| production wrapper の protocol | **固定 1 本** | `floor_campaign.sh:947` `PROTOCOL_PATH="output/s8b-freeze/floor_protocol.json"` |
| production wrapper の mode | **pilot 固定** | `floor_campaign.sh:962-964` `--mode pilot` |
| official mode | **core で無条件拒否** | `s8b_floor_campaign.py:342-352` |
| 既存の投入回数 | **3 件** | `output/env/pegasus/floor/attempts/submissions/` (873200.nqsv 他) |

つまり床値 campaign の実運用は「**同一 protocol・pilot mode を繰り返し投入する**」である。
protocol 単位の永久 claim を入れると、**最初の 1 回**が (成功でも crash でも preflight 失敗でも)
その protocol を永久に占有し、以後の投入はすべて拒否される。回復手段は手動の claim 削除だけで、
それは `campaign_claim` が意図的に持たないと明記した経路である。

これは規律 2 違反ではない (受理を広げていない) が、**承認外の過剰拒否**であり、
DW-S04 が「受理集合を縮小する wave では、承認外の過剰拒否を検出する正例も登録する」と
要求している当のものである。段 2 プランは mode も時刻も preimage から除外しており
(`s2-plan.md:12-22`)、この帰結を検討していない。レンズ A 所見 1 が独立に指摘した。

**この 1 点だけで、指示どおりの実装は land できない。**

## 所見の裁定 (real / refuted・採否・scope)

### レンズ A (正しさ境界・reward hack)

| ID | 判定 | 裁定 |
|---|---|---|
| **A-1** 排他の lifetime と root が未裁定 | **real・採用・本 wave の停止理由** | 上記 D1 で親が独立に実測確認。段 2 プランの設計は採れない。ユーザー再裁定へ返す |
| **A-2** host は caller 支配外でない (非特権 UTS namespace で hostname/FQDN を変更でき boot_id は不変) | **real・採用** | 子が login ノードで read-only probe により実測 (`/proc/sys/kernel/unprivileged_userns_clone=1`、`max_user_namespaces=2147483647`)。**親の M2 表の「host = caller 支配外: はい」は誤りであり撤回する。** host 照合は drift 検出であって authority ではない。計算ノードでの可否は未実測 |
| **A-3** script SHA の authority は既に存在し nonce にも scheduler 錨がある | **real・採用** | 親の M4 と独立に一致。加えて子は `certified_writer_admission.py:177-204,297-381` に **Python 側の receipt 検査が既に実在する**ことを発見した。これは段 2 プランの「authority が Python leaf まで届かない」を直接反証する |
| **A-4** 専用 leaf の再検算は caller 入力同士の一致に留まる | **real・採用** | 親の (P5) を**否定**する。`acquire_protocol_claim(record, protocol_sha256, freeze_sha256)` は caller が 3 つを同期して偽装すれば通る。「leaf が protocol 単位でない claim を拒否する」は過大表現だった |
| **A-5** S2 の変異 kill は production の純増検出力でない | **real・採用** | wrapper が Python より先に拒否する (`floor_campaign.sh:406-555,571-722`)。変異 matrix を「leaf 単体 / wrapper bypass consumer / sanctioned end-to-end」に三分する必要がある。再設計時の必須条件として持ち越す |

### レンズ B (scope 整合・実効性)

| ID | 判定 | 裁定 |
|---|---|---|
| **B-1** host-only 縮小は既裁定と衝突する | **real・採用** | だから縮小せずに返す。段 2 プランの推奨 (択 1) は採らない |
| **B-2** 「authority がない」と「artifact がない」の混同 | **real・採用** | 実 receipt が `output/env/pegasus/floor/attempts/submissions/f29f559a81afd2d3ba5dde05000a3471/submit-receipt.json` に実在する (親も確認: job_id=873200.nqsv)。ただし submitter 所有である点も正しい |
| **B-3** P5 は現行 generic leaf では成立しない | **real・採用** | A-4 と合流。加えて `s8b_oracle_driver.py:1015` が generic `acquire_claim` を呼び続ける点を採用 |
| **B-4** 別 out_root では protocol identity でも排他できない | **real・採用** | `campaign_claim.py:170-173` が明記済み。hash 変更では塞がらない。**「protocol 単位の global 排他」と表現してはならない**を設計制約として確定する |
| **B-5** 効く層の scope 境界が成果物説明から分離できていない | **real・採用 (scope 外)** | `loop.py` は本 wave の scope 外という親 brief の判断を維持。裁定パッケージへ同梱する |
| **B-6** Unit A / Unit B の素集合は完全な S2 では維持できない | **real・採用** | 3 項目を本当に照合するなら `s8b_floor_campaign.py:4693` と `s8b_oracle_driver.py:920` へ波及し、親 brief の分割は成立しない |
| **B-7** `(True, True)` contract は現行 registry に無いが型では可能 | **real・採用 (設計メモ)** | 現行値は不変。将来登録時の受理集合を裁定パッケージへ |
| **B-8** D75 は floor の local name だけでは閉じない | **real・採用** | `ClaimRecord.campaign_identity` が run ID も受け取れる限り、名前の分離だけでは閉じない |

### 親 brief の誤り (子が倒した。訂正して記録する)

1. `brief.md` の (P5) — **誤り。撤回する。** leaf は identity 文字列しか持たず、
   protocol 単位かどうかを判定できない (A-4 / B-3)。この誤りは実害があった:
   親はこれを根拠に「t523 との merge で意味が黙って戻っても安全」と述べたが、**成立しない**。
2. `brief.md` の DW-O13 充足主張 — **過大**。binding に field が在ることと、独立した現実側
   authority が在ることは別である (A / B 双方が指摘)。
3. `brief.md` の resume 拒否理由 — **誤り**。直接の拒否理由は元 run の claim 残存ではなく
   `s8b_floor_campaign.py:4658-4662` の `allow_resume=False` である。
4. `brief.md` の probe 一般化 — **過大**。probe が示したのは「同一 root・同一 process・逐次で
   異なる filename なら generic leaf は両方作る」までである。2 つの PBS job の競合は測っていない。
   欠陥自体は `s8b_floor_campaign.py:4715-4742` の静的追跡と合わせれば成立する。
5. `brief.md` の Unit A / Unit B 分割 — **不完全** (B-6)。
6. `brief.md` の成果物影響 — **射程が広すぎた**。official は現在無条件拒否され pilot は
   `eligible_for_refreeze=True` にできない (`s8b_floor_campaign.py:4198-4201`)。
   certified 選択への即時影響ではなく、**pilot 材料と将来 official に対する防壁**である。

### 親の M2 表の撤回

`parent-measurements.md` の M2 表は host を「caller 支配外: はい」としたが、A-2 の実測で偽と
判明した。**撤回する。** 予約照合 3 件のうち、caller の支配を完全に外れる source は
現時点で 1 つも確認できていない。最も強い錨は `PBS_JOBID` (scheduler が付与) であり、
それに束縛された create-only receipt が次に強い。

## 変異事前登録 (DW-M01)

**免除。** DW-S04 の「『実装しない』と裁定済みで実装差分ゼロの wave だけ変異 matrix を免除する」に
該当する。実装差分はゼロである。
**受入全走は免除しない** (同節)。段 7 の記録前に実走する。

## 次 wave への必須条件 (再裁定でどの択を採っても効く)

1. 変異 matrix を「leaf 単体 / wrapper bypass consumer / sanctioned end-to-end」に三分する (A-5)。
2. 「protocol 単位の global 排他」と表現しない。共有 out_root 時に限る旨を成果物へ書く (B-4)。
3. `s8b_oracle_driver.py` の generic `acquire_claim` 呼び出しを取り残さない (B-3)。
4. host 照合を authority と呼ばない。drift 検出として計上する (A-2)。
5. 過剰拒否を検出する正例を事前登録する (D1)。
