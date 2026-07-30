# T-180 段 6 レビュー裁定 (fix round 1)

レビュー A (fail-open / 証拠偽装) と B (検出力 / 変異帰属 / 仕様適合) はともに NO-GO。
must-fix 計 17 件を裁定した。fix 前統合 snapshot = `s6-pre-fix-integrated.patch`
(sha256 `89ce3c9af2f80d21645516ade6ab243e683bd537972d87ae4906e7f26a2dcca2`)。

## 親自身が独立に見つけた所見 (レビュー外)

- **F-P1 [must-fix]**: `_append_manifest` は attempt 完了後 (launch:1345) に呼ばれ、
  R9 が要求した「thread ID を rollout と照合できた直後」ではない。launcher が途中で殺されると
  費消済み session が manifest に残らず、台帳の受理集合から消える。

## 裁定表

| # | 所見 | 裁定 | fix 単位 |
|---|---|---|---|
| A-1 | 同一 poll 内の usage 巻き戻しで token 上限を迂回 | **real / 採用** | A + B |
| A-2 | `token_count.info=null` が model call を不可視化 | **real / 採用** | A |
| A-3 | receipt 改変だけで limit-stop を accepted へ昇格 | **real / 採用 (射程限定)** | A |
| A-4 | receipt 後の rollout 追記が checker を通り ledger 値を変える | **部分 real / 限定採用** | A |
| A-5 | `/proc` 読取不能を residual=0 と解釈 | **real / 採用** | A |
| A-6 | manifest 1 entry に複数 rollout が一致しても非 strict で rc=0 | **real / 採用** | B |
| A-7 | wall-clock が preflight/postflight を含まない | **real / 採用** | A |
| A-8 | 完全 receipt の上書き拒否が TOCTOU | **real / 採用** | A |
| A-9 | manifest header が実体へ束縛されない | **real / 採用 (bounded)** | A |
| A-10 | manifest への foreign entry 後追記 | **scope 外** (seal ceremony は plan v2 で除外済み) | — |
| A-11 | `limit_trigger && accepted` 分岐が到達不能 | **real / 採用 (nit)** | A |
| B-1 | post-spawn 失敗で process 残存 + receipt 欠落 | **real / 採用** | A |
| B-2 | 「wall-clock hard cap」の名称が射程過大 | **real / 採用** | A |
| B-3 | 最終 drain 後の超過を accepted 公開してから self-check で落とす | **real / 採用** | A |
| B-4 | M1/M8/M9/M11 が単一理由 kill でない、M2/M3/M10 は anchor 要再登録 | **real / 採用** | A + 変異再登録 |
| B-5 | fake が incremental tail を再現せず実 CLI event 形も pin していない | **real / 採用** | A |
| B-6 | `possible_unobserved_overshoot` の意味が拘束されていない | **real / 採用** | A |
| B-7 | `termination_verified` が identity 未取得時に恒真化 | **real / 採用** | A |
| B-8 | `codex_version` が checker で再束縛されない | **real / 採用 (nit)** | A |
| F-P1 | manifest 追記が rollout 相関直後でない | **real / 採用** | A |

## 射程を限定した裁定の理由

- **A-3**: receipt 単体からは「limits が改竄されたか」を原理的に判定できない
  (外部期待値が無いため)。よって fix は (a) `check-receipt` が sealed artifact から
  actuals を**再計算**し receipt の自己申告と突き合わせる、(b) `--expect-*` で
  外部期待値を渡せる、(c) 外部期待値なしのときは limits が self-asserted である事実を
  出力・receipt に明示する、の 3 点までとする。「外部期待値なしで改竄を検出できる」とは主張しない。
- **A-4**: 「receipt と台帳が同じ rollout snapshot を参照する」は元々の約束ではない
  (ledger は実消費を測る別系統)。採用するのは「`check-receipt` が prefix しか見ずに
  黙って通る」点だけで、fix は seal 時の `rollout_sha256` / `rollout_bytes` を記録し、
  以後に伸びていれば `rollout_grew_since_seal: true` を明示することまで。
  ledger を receipt に合わせて EOF 未満で止めることはしない。
- **A-9**: HEAD との一致まで要求すると正当な過去 base での再実行を壊す。
  採用するのは (a) `--cwd` が `--repo-root` 配下、(b) `--base-commit` が当該 repo に実在
  (`git cat-file -e`)、(c) `check-receipt` が header 3 field を再照合、の bounded 版。
- **B-2**: 実体は「launcher process の supervised deadline」であり、
  `setsid()` 脱出子まで覆う保証はない。名称と receipt の
  `wall_clock_scope` を実体に合わせ、hard cap の主張範囲を縮小する。

## 変異の再登録 (DW-M07 / B-4)

fix 後に anchor を再検証したうえで、次を差し替える。

| ID | 変更 |
|---|---|
| M1 | 三重化した acceptance gate のうち**単層のみ**の変異は生存するため、`_seal_attempt` の latch を単一の実効 gate へ再照準し、他層は冗長 gate と明記して単独証拠から外す (DW-M03) |
| M2 | 単一 conjunct 削除で生存するため、metering 判定の early return を実効 gate として再照準 |
| M3 | CLI-reported 定義の複製 4 箇所を単一 helper へ寄せ、helper への単一変異で kill |
| M8 | barrier を manifest の load/replace critical section へ移す |
| M9 | test が helper 直呼びのため、receipt writer の call-site を変異対象にする |
| M10 | attempt output hash 再計算の削除も kill されるよう負例を追加 |
| M11 | checker が先に赤くするため、append gate 単独の kill を測れる負例へ再照準 |
| M17 (新) | manifest 追記を rollout 相関直後でなく attempt 完了後へ戻す変異 (F-P1) |
| M18 (新) | `/proc` 読取失敗を residual=0 として扱う変異 (A-5/B-7) |
| M19 (新) | 累積 usage の巻き戻しを許す変異 (A-1) |

## 実データ受入 (R17) の扱い

レビュー B が read-only で実走し、`--manifest` 経路が
**rc=0 / issues={} / 10 session / 434 model_calls / 2,757,982 cli_reported** と
stage 別 6 値の全一致を報告した。ただしこれは子の実走であり、
**親が再実測するまで緑と数えない** (DW-O05)。fix 後に親が再走し、回帰テストとしても固定する。

## scope 外 (裁定パッケージへ)

1. manifest の seal ceremony と foreign entry の後追記検出 (A-10)。
2. `setsid()` 脱出子の完全封じ込め (cgroup / bwrap)。
3. stdout / artifact bytes の上限。
4. DW-O01 の結線と stage 別上限値 (T-184)。
