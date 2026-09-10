# 段 1 brief — [T-1984] D906 の外部署名主体を実装する

wave: `dev-wave-t1984-external-signer` / base = local main `08a17b3b3`

## 1. 確定済みユーザー裁定 (親は不採用にできない)

- **D906 (ユーザー裁定):** 着地ツールが読む受領証に発行元の証明と再送防止を設計する。
  **署名鍵と発行権限は候補および AI が書ける領域の外に置く。** 署名対象には
  検査した main と tip、実行器と検査器の bytes、排他権の世代、判定を含める。
- **D1197:** D906 を実装する。D387 は適用範囲の違う一般則であり D906 を覆せない。
  着手できない部分が残る間は、着地受領証を根拠にした主張を**未閉鎖と明記**する。
- **D431:** 恒真にしない。実在 production 値を自分の述語へ通す positive control を同じ変更単位で入れる。
- **D95:** 実装面は Codex `role=author` が書く。親は brief・裁定・統合・全走・記録・land だけ。
- ユーザー指示: 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外 (DW-G05)。

## 2. 対象機構 (実アンカー)

| 役割 | 実体 | 現状 |
|---|---|---|
| 受領証の発行 | `tools/acceptance_launcher.py::_receipt_bytes` (v5, 27 field) | launcher blob を待ち手が `python3 -I -c` で exec |
| 受領証の検証 | `tools/dev_wave_land.py::_verify_acceptance_receipt` | blob SHA・等値・形式・構造的自己無矛盾のみ |
| launcher の起動 | `tools/dev_wave_wait.py` (`_LAUNCHER_PATH`, 2570 行付近) | **tip 側待ち手が起動権を持つ** |
| launcher source | `_SOURCE_REVISIONS = {tested-main, tested-tip-bootstrap}` | main にあれば main を使う |

D583 が現行の穴を逐語で記録済み: land の独立検証は
**「launcher が実際に起動されたこと」を独立に証言する field を持たない**。
launcher が独立に再計算するのは `child_rc` / `log_sha256` / `runner_executed_sha256` の 3 値だけ。

## 3. scope (本 wave で実装する)

**S1. 外部署名主体 (issuer) を repo 外へ置き、launcher 起動権をそこへ移す。**
D583 §2 の「設計方向」の実装にあたる。issuer は (a) 自分の鍵で署名し、(b) launcher blob を
`tested_main` から自ら exec し、(c) 独立に再導出できる field は再導出してから署名する。

**S2. 受領証へ発行元証明と再送防止を足す。** 署名対象は D906 の 4 項目 —
検査した main と tip / 実行器と検査器の bytes / 排他権の世代 / 判定 — を必ず含む。

**S3. land を fail-closed にする。** 署名の不在・不正・再送は main を 1 bit も進めずに拒否する。
flag・環境変数・警告化の逃がし道を作らない (D906、規律 2)。

**S4. positive control (D431)。** 実在 production 受領証を tracked fixture として取り込み、
自分の述語へ通す。期待値を `os.environ`・production 定数・戻り値自身・loader から作らない。
負例と対にする (署名なし / 鍵違い / field 改竄 / 再送)。

**S5. 未閉鎖の明記。** 閉じない範囲を decisions と worklog へ書く (下記 §6)。

## 4. 不変条件 (破ってはいけない)

- **I1.** 規律 2。受理集合を緩める方向の変更をしない。署名検証は追加の拒否であって受理の追加ではない。
- **I2.** `orchestrator/tests/test_dev_wave_land.py` を編集しない (稼働 2 単位が未 commit で編集中)。
  新規 test file へ逃がし、DW-O26 の file 集合列挙メタテストも焦点走に含める。
- **I3.** `artifact_admission.py` / `campaign_lock.py` / `contract_loader_binding.py` に触れない ([T-733] 稼働中)。
- **I4.** land の既存権威 (協調 lock、ff-only、全史 provenance 監査、fold) を 1 bit も変えない。
- **I5.** 鍵の bytes を log・receipt・commit・報告のどこにも出さない。
- **I6.** 追加の gate・検査・台帳・一般化を足さない (DW-G05、ユーザー明示)。

## 5. 割れうる前提 = 攻撃対象 (親の provisional 裁定)

- **(P1) 「AI が書ける領域の外」は、この環境では hooks (`guard_write`/`guard_bash`、Claude と Codex
  の両方へ配線済み) による repo 外 path の write 拒否として機械化するのが上限である。**
  OS 上の別 uid・別ホスト・ハードウェアトークンは利用できない。したがって完全な防壁にはならず、
  D387/D1128 の限界はそのまま残る。→ **未閉鎖として明記する**。
- **(P2) issuer が独立に再導出できるのは git 由来の値 (ref の実在、launcher/waiter/runner の blob
  SHA)、および自分が exec した launcher の観測値 (`child_rc`、log hash) までである。**
  `pre_fingerprint` / `post_fingerprint` / `effective_scheduler` / checker 系 field は
  依然として待ち手の自己申告であり、issuer はそれを再現できない。→ **未閉鎖**。
- **(P3) 「排他権の世代」に対応する field は現行 v5 受領証に存在しない。** `lease_holder` は
  世代ではなく、D662 で lease の待ち行列は廃止済み。新設が要る。DW-O13 に従い、実環境で
  取りうる値を実測してから述語を採る。
- **(P4) 本 wave 自身の land が成立する。** launcher source は tested_main を優先するため、
  main 側 launcher (署名非対応) が走ると受領証は無署名になり、tip 側 land が自分で拒否する
  = **bootstrap 死** の危険がある。起動権を待ち手 (tip 側) から issuer へ移す形なら本 wave の tip に
  実装が載るので回避できる、というのが親の provisional 裁定。**段 2 で経路を file:line で確定させる。**
- **(P5) 稼働中の他 wave の land を壊す量は、受領証 schema 版上げの既存前例 (v3→v4、v4→v5) と
  同じ範囲に収まる。** 前例では「本 wave 以前に発行された受領証は拒否される」ことが受容されている。

## 6. 未閉鎖として記録する範囲 (D1197 の明記義務)

1. (P1) 鍵の生成と設置は AI が起動した process で行われる。人手のみの鍵儀式と uid 分離は未実装。
2. (P2) 判定 (`verdict` / `child_rc` 以外の待ち手自己申告 field) の真正性は署名で閉じない。
   署名が証明するのは「issuer を通ったこと」と「再送でないこと」であって「判定が正しいこと」ではない。
3. D583 §4 の残余 — 親の起動点自体が issuer を省略する経路、issuer 自身の trust root、
   bootstrap 例外、completion protocol の自己申告面 — は本 wave では閉じない。
4. land verifier 自身が候補コードであること (T-696 の協調境界) は対象外のまま。

## 7. 成果物の形

- 実装面: issuer 本体 + 設置 script + 署名検証 module + `dev_wave_land.py` / `acceptance_launcher.py` /
  `dev_wave_wait.py` の配線 + 新規 test file (`test_dev_wave_land.py` は不可)。
- docs: decisions fragment (未閉鎖の明記を含む)、worklog fragment、insight (逐語 + 変異台帳)。
- 変異事前登録を段 4 で行い、段 6 で matrix を回す。

## 8. 分割方針

段 2 は read-only codex 1 本。段 3 は敵対 2 レンズ (レンズ A = 恒真化・bootstrap 死、
レンズ B = 未閉鎖の過小記載・受理集合の緩み)。段 5 は issuer + 配線で 1〜2 単位。
producer/consumer 契約が単位を跨ぐため、契約を持つ面は 1 子に持たせる。
