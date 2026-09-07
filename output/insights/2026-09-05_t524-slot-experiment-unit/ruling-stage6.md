# 段 6 裁定 — レビュー所見の real / refuted と fix2 の範囲

## 1. 所見の裁定

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| R1 | A blocker | **legacy downgrade。** v1〜v4 の receipt が attempt registry 検査を通らずに `VerifiedAcceptanceReceipt` へ到達する。`require_current_verified_receipt` に schema-current 条件が無い。追加テスト自身が v4 へ落とした receipt を verified にしている | **real / 採用 (最優先)** |
| R2 | A blocker | **事前固定が下流で未証明。** v5 verifier は registry の自己整合性しか見ず、その genesis が結果観測前に外側 receipt の manifest / P へ固定されたものかを証明しない。履歴検査も最初の blob が genesis のみだったことを要求しない | **real / 採用** |
| R3 | A must-fix | **第二 root を見逃す。** 下流の履歴検査は `HEAD` の ancestry しか見ず、同一 repo の別 ref にある第二 root を検出しない。issuer 側は `rev-list --all` と全 tree path を見ている | **real / 採用** |
| R4 | A nit | `attempt_registry_prefix_bytes` (byte 数) も PID・starttime・時刻の桁数で変わりうるのに揮発化されていない。lifecycle の byte 数は既に同理由で揮発扱い | **real / 採用** |
| R5 | B must-fix | **projection 再照合に変異 killer が無い。** `s8c_acceptance_receipt.py:1545` を `if False:` にしても赤くなるテストが無い。M3 は terminal 欠落だけを作るので消費検査側で拒否され、再照合側は素通りする | **real / 採用** |

**refuted はゼロ。** 5 件すべて file:line で裏付けられている。

## 2. なぜこれらは scope 内か

R1〜R3 は「既に作ると決めたもの (b) が実際には効いていない」という指摘であり、
新しい機構の追加ではない。とくに R1 を放置すると、下流は旧 schema を選ぶだけで
新しい検査を丸ごと迂回できるので、D1269 の後半は**飾りになる**。

R2・R3 の対処は **issuer 側に既に在る gate を verifier からも使う**形に限る
(`trial_registry.py:3555` の P 時点 initial blob 照合、`trial_registry.py:2586-2626` の
`rev-list --all` 第二 root 検査)。新しい機構を発明しない。これは最小形の範囲である。

R5 は段 3 で指摘された「変異が生き残るテスト」の型そのものであり、DW-M01 の
単一理由性を満たすために必要である。

## 3. fix2 の範囲 (これだけを直す)

1. **R1:** 下流の消費入口 (`require_current_verified_receipt`) が current schema (v5) と
   attempt registry 束縛を**必須**にする。旧 schema の読取・parse は残してよいが、
   下流が使う verified capability には到達させない。
2. **R2:** v5 の検査で、registry が外側 receipt の `manifest_sha256` / `prereg_commit` へ
   束縛されていることを exact に照合する。履歴検査は issuer と同じく、P 時点の initial blob が
   genesis のみであることを要求する。**issuer の既存 gate を再利用する。**
3. **R3:** 下流の履歴検査を issuer と同じ `rev-list --all` + 全 tree path の第二 root 検査に揃える。
4. **R4:** `("acceptance", "attempt_registry_prefix_bytes")` を同じ根拠で揮発 leaf に足す。
5. **R5:** projection 再照合だけを無効化したときに赤くなる負例を足す。
   generation / slot_id / unit_count / units のいずれか 1 つだけを receipt 側で改変し、
   tracked registry と食い違わせる形にする。terminal は全件そろえ、消費検査では拒否されないようにする。

## 4. 変異事前登録の更新 (DW-M01)

M3 を 2 つに割る。R5 の指摘どおり、現状の M3 は消費検査の証拠にはなるが再照合の証拠にならない。

| M | 位置 | 無効化する述語 | 同じ入力を拒否する前後層 | 期待する赤 |
|---|---|---|---|---|
| M1 | v3 reader の root 単一 generation 検査 | generation 混在の拒否 | 無し (series key は generation を含まない) | 混在 genesis の負例が赤 |
| M2 | genesis 作成器の引数 ↔ 全 slot exact 一致 | 引数と slot の不一致拒否 | 無し | 不一致 genesis の負例が赤 |
| M3a | v5 の全 unit 消費検査 | 宣言済み unit の終端欠落の拒否 | 無し | terminal 欠落の負例が赤 |
| M3b | v5 の projection 再照合 | receipt 記載 projection と現物の不一致拒否 | 無し (消費検査は全件そろっているので発火しない) | projection 改変の負例が赤 |
| M4 | 下流入口の current schema 要求 (R1 の対処) | 旧 schema での下流到達の拒否 | 無し (現状は素通り) | v4 receipt が verified になる負例が赤 |

過剰拒否の正例は据え置き (P1: 単一世代・6 unit 全消費・`observed` と `terminal-failure` 混在が
verified になる。P2: `retryable-failure` の後に同 series の次 attempt が正常終端した形が受理される)。

## 5. 裁定パッケージへ追加する項目

- **独立 clone / repository を跨ぐ best-of-N は本 wave でも閉じない。** R3 を直しても
  同一 repository 内に閉じる。D1269 が全世代一般化を却下しているため対象外のままとする。
