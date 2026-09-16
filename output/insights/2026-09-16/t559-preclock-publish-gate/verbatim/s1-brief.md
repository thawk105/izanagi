# 段 1 brief — [T-559] 凍結 pre profile と post observed clock の publish 前 canonical 比較

## 研究前進 (土台)

止めている研究: 較正 (calibration) は campaign の records 数と環境前提を決める土台であり、
`orchestrator/campaign/env_contract.py:263-277` が登録済み 2 件を束縛して certified 選択と
材料レポートの環境主張を支える。現状、benchmark 後に実効クロックが帯外へ振れた較正でも
publish されて registered に入り、同じ資格で下流に使われる。最小差分は publish transaction の
**直前**に「凍結した pre profile の effective clock」対「benchmark 後に観測した clock」の
canonical 比較を 1 本足すことだけである。

## 確定済みユーザー裁定 (覆さない)

- 択 (a) 採用 (2026-08-25 /rulings 全件、推奨どおり)。凍結した事前状態と事後の観測値の照合を
  publish 前に課す。
- **publish transaction 自体を後ろへ移す案は採らない** (影響範囲が広い)。
- [T-560] (別 process verifier の完全形) は scope 外。D218 が同一 process 内再読を充足形と定めている。
- D155 決定 (4): probe の観測者効果 (F108) の是正は本 wave で行わない (ユーザー再裁定待ち)。
- D191 決定 1: 帯計算を再実装しない。判定は canonical 述語 `effective_clock_comparison_passes` を経由する。

## scope

`orchestrator/calibrator/cli.py` の `_certify_main` に、publish 前の pre→post effective clock
比較を 1 本足し、失敗を既存 `reasons` 経路へ積んで `status="rejected"` に落とす。
post observed clock の供給源は **既に取得している** `static_post = _profile_dict(probe_fn())`
(cli.py:1005) とし、新しい probe を足さない。付随する診断の記録先は attempt staging 配下に限る。

## scope 外 (足さない)

一般化・framework・新 gate 族・新台帳・別 process verifier・外側 wrapper
(`tools/pegasus/certify_calibration.sh`) の改修・canonical 述語の改訂・observer effect の是正・
publish 順序の変更・benchmark **中**の clock 検査。仮想リスク向けの防壁は足さない。

## 不変条件

1. 規律 2 を緩めない。新 gate は受理を**狭める**方向にだけ効き、既存 reason を消さない。
2. **通る attempt の published bytes を変えない。** `docs/b10-backoff-shape-preregistration.md:241`
   の sha256 pin と `env_contract.py:263-277` の登録 2 件束縛に波及させない。
3. canonical 述語 (`execution_guard.py:324`) と policy 定数 (`effective_clock_policy.py`) を変更しない。
4. publish (rename) の位置と `_published_self_comparison_receipt` (cli.py:1081) を動かさない。
5. 比較の expected 側は **凍結した pre profile** (`profile["effective_clock"]`、tolerance_pct は
   attempt 開始時に policy から焼いた値) とし、post 側で上書きしない。

## (P1) 親の provisional 裁定 — 段 2/3 の攻撃対象

- (P1a) post observed clock は `static_post` の `effective_clock.samples_mhz` で足りる。
  別 probe を足す必要はない。
- (P1b) 新 reason は `reasons` へ積むだけでよく、artifact schema を拡張しなくてよい
  (不変条件 2 を守るため)。
- (P1c) 新 gate は cli.py:1014 の既存 late self 照合の直後、`status=` 決定 (cli.py:1016) の前に置く。

## 実測 (親が段 1 前に取得、DW-O13)

- 実 attempt 7 件の pre/post を実測。直近 6 件は post 48 sample すべて厳密に 2101.0 MHz、
  乖離 0.000% で **新 gate は通る (到達可能)**。
- 唯一 `0:867876.nqsv` が cross で落ちる (idx44=3077.7、46.49%) が、**同 attempt は既存の
  早期 self 照合でも落ちる**。よって「self が通って cross だけ落ちる」歴史的実例は 0 件であり、
  新 gate の価値は実例ではなく「benchmark 後の状態を見る gate が現在 1 つも無い」構造的欠落にある。
- 模擬/実の差: 上表の post は外側 wrapper の `attestation-post.json` (CLI 終了後) であり、
  新 gate が使う CLI 内 `static_post` (benchmark 直後) とは観測時点が違う。同じ probe 実装
  (`env_attestation`) だが時点は同一でない。

## DW-G05 成果物影響

放置すると、benchmark 後に clock が帯外へ振れた較正が accepted で registered に入り、
certified 選択と材料レポートの環境前提が破れたまま参照される。受理集合は「post clock が帯外でも
accepted」から「reject」へ狭まる。published 集合の既存 bytes は 1 件も変わらない。

## 成果物の形

`cli.py` の差分 1 箇所 + 新 reason code + attempt staging への診断 receipt (任意) +
`orchestrator/tests/test_calibrator_certify.py` の正例・負例 + 変異 matrix + 受入全走。

## 分割方針

段 2 = plan 子 1 本 (read-only)。段 3 = 敵対 2 本 (レンズ: 恒真化/受理集合、凍結 bytes と pin 波及)。
段 5 = 実装子 1 本 (Codex role=author、編集面は cli.py と同 test のみ)。段 6 = 敵対レビュー 2 本 + fix。
