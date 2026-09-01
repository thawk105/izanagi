---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t1905-b10-formal-run
seq: 1
title: [T-1905] B-10 正式走を投入し write-heavy だけ完走した。機構の欠陥 4 件を実測で潰し、残り 2 workload はユーザー裁定で並列化設計へ差し戻した (code + docs + insight、branch worktree-dev-wave-t1905-b10-formal-run、変異 4/4 KILLED)
---

## 本文

- 発効版 prereg commit は `77b33e37d`。本文 blob `ea910de32` はこの commit で初出し、着手時の
  local main 先端まで不変。直前の 2 commit は別 bytes なので発効版ではない。投入前に祖先性・
  本文 bytes・patch bytes・式 SHA・物理残差表の再計算 (最大絶対偏差 0.5616942857142844%)・
  登録 calibration の適合を login node で全部通してから投げた。

- **write-heavy だけが完走した。** campaign `...-write-heavy-formal-e3de15eb`、request
  `965564.nqsv`、`verify-perf` 相、`driver_rc=0`、所要 3 時間 50 分。**45 cell 全部が
  `correctness_certified=true` / `missing=false`** で、正しさ検証は 15 変種すべて anomaly ゼロ・
  verdict `serializable`。**本 wave はこの数値から何も結論しない** — 事前登録 §5 の判定は
  3 族の Holm 補正を前提とし、1 workload では族が揃わない。

- **read-heavy はユーザー裁定で撤去された。** 5 時間 5 分で 15 点中 3 点しか終わらず、
  **CPU/経過 = 1.0、すなわち 48 コア確保のうち 47 コアが遊休**だった。空きノードは 108/149。
  裁定は「性能測定で計算ノード上を 5 時間走るのはありえない。複数ノードへ分散して投げる」。
  balanced は未投入。**次の正式系列は並列化した設計をユーザーへ出してから投入する。**

- **親の失敗を記録する。** 親は CPU/経過 = 1.0 を何度も観測しながら「この相は検査器が単一
  スレッドなので正常」と説明し、「なぜ 47 コア遊ばせて 1 ノードを占有し続けるのか」を問わなかった。
  ユーザーの「遊びすぎでは」という指摘はここを指していた。ほかに、45 cell 全滅の可能性を
  1 cell の安い試し打ちで潰さずに本走を投げた、workload ごとの所要を見積もらず 6 時間枠へ
  投入して balanced の 15 変種目を失った、「全部やり直す (16 時間)」という筋の悪い案を出した。

- **実行でしか出ない機構の欠陥を 4 件見つけた。** 詳細は
  `output/insights/2026-08-31_t1905-b10-formal-run/`。

  1. **official 出力 root が未配線で verify が起動しない** (D641)。probe 相と build 相は
     `campaign_layout` の手前で終わるため、**verify が初回の露見点**だった。env を設定するだけでは
     足りず、外部 root を承認する `DurableRootPolicy` の注入が要る。これが無いと**どんな形の
     正式走を設計しても verify が 20 秒で落ちる。**
  2. **binary に job 固有 path が入り、認証と測定の SHA が一致しない。** 事前登録 §7 の
     「性能 binary は正しさを認証した binary と SHA 完全一致」は、相を別 job に分けた時点で
     構造的に満たせない。perf は 45 cell 全滅した。path が入る経路は `.rodata` の `__FILE__`、
     RUNPATH、buildcache の staging path の 3 つで、完走 binary の解剖で全数確定した。
     **path 非依存化は 2 巡実装したが収束しなかった** (差分 149 → 56 → 45,454 bytes、
     `-g -O3` の完全な debug 情報が相手)。codex 相談も同結論で、**同一 job・同一 checkout で
     認証と測定を行う `verify-perf` 相**を採り、write-heavy 45/45 はこの形で得た。
     **cell を別ノードへ分散する設計ではこの面が再燃する。**
  3. **壁時計の固定値が 4 か所に散っている。** 1 か所でも食い違うと job が起動時の自己検査で落ちる。
  4. **シグナル処理が壊れており、強制終了の理由が毎回失われる。**
     `local name=$1 number=$2 rc=$((128 + number))` は語展開時に `number` が未設定で
     `set -u` により落ち、`write_failure` へ到達しない。実測: `965996.nqsv` の scheduler.stderr。
     balanced の打ち切りで記録が残らなかったのも同じ理由。**本 wave では未修正。**

- **打ち切りからの再開は 2 段で塞がれる。** balanced は 6 時間枠で 14/15 まで進んで打ち切られた。
  (1) crash が残した claim は「stale 判定も自動削除も release も意図的に持たない」設計なので、
  所有者の死亡を scheduler の応答で確定させ bytes を保全してから操作者判断で除去した。
  (2) D193 は「build 完了後の record がある中断 attempt は自動回復しない」と定める。これは
  正しさゲートそのものなので迂回せず、**この WAL は再開不能と判定した。**

- **ユーザーが束縛設計の欠陥を指摘し、実測で裏が取れた。** `PreregistrationBinding` に
  `analysis_commit` (投入ツリーの HEAD) が入っており、`assert_resumable_binding` は完全一致を
  要求する。**測定に無関係な commit を 1 つ打つだけで再開が拒否される。** 同じ束縛に
  `analysis_code_sha256` (内容ハッシュ) があり意味のある保証はそちらが担うので、
  `analysis_commit` は偽の無効化を足すだけである。絶対規律 7 に反する。**別タスク候補。**

- 所要の内訳を実測した。1 反復は取引試行数に対し約 25.6 マイクロ秒/件で 175 秒あたり頭打ち。
  **ベンチマーク実体は 1 workload で 4.5 分**、残りはトレース書き出しと直列化可能性検査である。
  read-heavy を「中止が少ないから速い」と予測したのは外れで、commit が 1690 万件あり
  検査対象の合計は write-heavy とほぼ同じだった。**655 万件超で所要が頭打ちになる観察は
  未確認で、トレース切り捨ての可能性がある** (正しさ主張に関わるので別タスク候補)。

- 事前登録した変異 3 件は実装前に登録し、A5 の fix に対する 1 件は事後登録であることを明記する。
  本走は baseline PASSED、**4/4 KILLED、期待 node 完全一致、SURVIVED 0、MISMATCH 0**。
  途中で A5 の 2 テストが「値をそのまま固定する行」で先に落ちて挙動の検査へ到達していないことを
  変異が暴いたので、その 1 行を外して赤の理由を挙動 1 つに絞った。

## 次の一手差分

### 更新

- [T-1905] **P1・write-heavy のみ完走 → 並列化設計をユーザー裁定へ**: 発効版 `77b33e37d` を指した
  正式走で write-heavy 45 cell が完走した (`driver_rc=0`、全 cell 認証済み・欠測なし)。
  read-heavy は 15 点中 3 点でユーザー裁定により撤去 (CPU/経過 = 1.0、47 コア遊休)、balanced は未投入。
  事前登録 §5 の 3 族 Holm 判定は 1 workload では成立しないので何も結論していない。
  次は cell / thread / workload を複数ノードへ分散する設計をユーザーへ出してから投入する。
  分散時は §7 の SHA 一致要求 (認証と測定が別 job になる) をどう満たすかを設計に含める。
  base: 7d71e369cbee5b98635be20f9caff4b373da34dc67127225dcd7b651fbc6913a
