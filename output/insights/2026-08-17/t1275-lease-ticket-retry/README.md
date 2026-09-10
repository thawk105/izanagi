# [T-1275] 受入待ち手の同一 process 内 attempt 再試行

wave: `dev-wave-t1275-lease-ticket-retry` / 2026-08-17 / base main = e6306848

ユーザー裁定 (2026-08-17 /rulings 全件 第 5 回、択 (a)) の実装。
受入 command が pytest の判定を 1 つも産まずに戻った走行を、lease を保持したまま
同一 process 内で 1 度だけ再投入する。D253 の待ち札意味論には触れていない。

設計判断の正本は decisions の
「受入の同一 process 内再試行は、肯定的証拠の合議でだけ発火させる」。

## 何が問題だったか (一次資料)

`docs/failures.md` F365 と `output/insights/2026-08-17_t650-lease-release/ruling-package.md` R-A。

待ち札は稼働中 process の `claim` 呼び出しでしか heartbeat されず、最後の claim から
300 秒で失効して**新しい到着時刻**の札に作り直される。待ち手 process が attempt ごとに
終了する設計だったため、赤や argv 誤りを踏むたびに解析・再投入で 300 秒を超え、
行列の最後尾へ落ちていた。実測: t1180-pilot-approval が `queued_at_ns` を
20:50:17 → 21:42:28 へ書き換えられ、**52 分の先着順位を失って**後着 3 本に追い越された
(通算 79 分待ち)。

## 敵対検証が変えたもの

段 3 (2 レンズ) と段 6 (2 レンズ) が計 21 件の所見を出し、親は**全件を real** と裁定した。
refuted はゼロ。設計を実際に変えたのは次の 3 点である。

1. **親の当初案「rc が 0/1 以外なら判定なし」は規律 2 違反だった。**
   `tools/pegasus/dispatch_compute.py` は受領証の永続化に失敗すると、**child rc を得ているのに
   infra rc を返す**。pytest が実走して rc=1 の赤を出しても待ち手には同じ rc に見えるため、
   raw rc を発火条件にすると実走赤を再試行できた。親が一次資料で再現手順を確認して採用し、
   肯定的証拠の合議へ設計を変えた。段 3 の 2 レンズが独立に指摘した。
2. **その肯定的証拠自体も弱かった。** `child_started` は scheduler の実行中状態を
   観測できたかに依存しており、短命な job は観測を取り逃がして「未開始」と誤認された。
   log が切り詰められて赤痕跡が落ちれば裏取りも素通りする。producer 側で
   「まだ待ち行列にいる」肯定証拠を要求し、consumer 側で切り詰め framing を
   不在確定不能へ倒す形で閉じた。段 6 レンズ C の指摘。
3. **失敗後に lease を手放す設計では目的が発効しなかった。** lease 取得成功時に自分の待ち札は
   削除されるため、同一 process から即座に再 claim しても新しい到着時刻の札になり、
   後着の後ろへ回る。保持したまま再試行する形へ変えた。段 3 レンズ A と親の事前実測が一致。

## 併走裁定を取り下げた判断

[T-1172] (land 直前の lease renew) は「[T-1275] と同じ作業で扱ってよい」と裁定されていたが、
段 3 の 2 レンズが**独立に**、land 側で `wave_land_window.claim` を renew として流用すると
**lease と待ち札を新規生成する** (land が retryable 終端なら最大 2400 秒 / 300 秒残る) ことを
実コードから成立させた。安全な形には `wave_land_window.py` へ非取得型 renew primitive の
新設が要り、それは D253 の実装面そのものである。絶対規律 5 (段階導入) に従い別 wave へ送った。

## 本 wave が閉じない残余

- **lease 取得後・受入 command 投入前に落ちる型** (実測 t1180 の 52 分喪失はこの型)。
  同じ argv の即時再試行では直らず、親が修正済み message path を供給する協調点の設計が要る。
  worklog の次の一手へ新規起票した。
- **attestation の偽造耐性**。attestation は受入 command と同じ stdout/stderr channel にあり、
  repo 内 runner を書き換えれば偽造できる。[T-1299] の信頼済み中核の内側であり、
  偽造で得られるのは attempt 上限 2 のもとでの再試行 1 回だけ (赤を緑に変えられない) なので
  本 wave では受容し、限界として明記した。worklog の次の一手へ新規起票した。
- **rc=16 型の発火率と節約時間は未計測**である。本 wave が入れた retry journal で以後測れる。

## 変異 matrix

`--runner-mode dispatch`、runner argv に `--force-dispatch`。固定 HEAD は本 wave の統合 commit。

| 走行 | spec | 結果 | 成果物 |
|---|---|---|---|
| 観測走 | 15 変異を全件 SURVIVED 期待で登録 | baseline PASSED、12 件が kill (MISMATCH)、3 件 SURVIVED | `mutation-probe.json` |
| 本走 | 12 件を観測完全 node 集合で KILLED 期待 + 両層同時 2 件 | **13 KILLED / MISMATCH 0**、baseline PASSED、R13 のみ SURVIVED | `mutation-spec.json` / `mutation-result.json` |
| 再照準走 | R13 の実効 gate へ単発再照準 | **1 KILLED / MISMATCH 0**、baseline PASSED | `mutation-spec-reaim.json` / `mutation-result-reaim.json` |

**合計 14/14 KILLED、MISMATCH 0。**

### 生存した変異の扱い (DW-M02 / DW-M03 / DW-M04)

観測走で生存した 3 件は、いずれも**他層に覆われた冗長 gate** であることを実コードで確認した。

- **relay 付き attestation の拒否**: relay 付き marker は payload 集合へ追加されないため、
  この gate を外しても「attestation 欠落」で terminal になる。**診断理由の細分化**であって
  終端挙動の保証層ではない。実効 gate まで外す両層同時変異へ再照準し、KILLED を確認した。
- **「attestation が 0 件」の拒否**: 「ちょうど 1 件でない」の拒否に完全に含まれる。
  `DW-M03` に従い**冗長 gate と明記して単独変異の証拠から外した**。
- **退避後の検査**: 退避の実装が `os.link` の排他性に守られており、path 事前検査と
  後検査の**両方**を外しても上書きは起きない。三重に守られていた。実効 gate
  (`os.link` → `os.replace`) へ再照準し、KILLED を確認した (`R13B`)。

## 実測 (すべて親が実走)

- 段 5 後の焦点走 15 file: 2314 passed / 1 failed。赤は実装子が新設したテストの期待値の誤りで、
  production の欠陥ではなかった (red-check 失敗経路は受領証発行前に止まるので
  receipt-reclaim の 2 回目 claim へ到達しない)。
- 段 6 fix 後の焦点走 17 file: **2438 passed / 0 failed (rc=0)**。
- 全史 provenance 監査: 3856 件・新規違反なし (rc=0)。
- `check_docs`: 違反なし。
- 変異 matrix: 上表のとおり。

## 工数

codex 子 8 本すべて `stop_reason=completed`。
段 2 プラン 15 分 / 段 3 敵対 2 本 (sol 18 分・luna 15 分) / 段 5 実装 2 単位 (9 分・23 分) /
段 6 レビュー 2 本 (11 分・15 分) / 段 6 fix 19 分。
