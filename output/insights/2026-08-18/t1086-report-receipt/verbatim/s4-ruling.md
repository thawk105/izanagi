# 段 4 裁定 — [T-1086] oracle 実走後の store 再読を報告 receipt で塞ぐ

裁定 inbox を段 4 直前に再走査した (最新 = `2026-08-18-rulings-full7-15rulings.md`)。T-1086 / T-1103 に
関する更新は無く、2026-08-15 の裁定が有効。

## 親自身の実測訂正 (先に出す)

- **brief の DW-G05 記述は過大だった。** `orchestrator/campaign/layer3_report.py:576` が
  「No certified-selection consumer exists in this checkout」と明記している。現 checkout で本 wave が
  実際に変えるのは **observations report / oracle verdict / combined verdict** までであり、
  certified 選択値と台帳行は変わらない。以後この限定形を正本とする。
- **brief の「post-run の store 再読は repo 全体に 0 件」も不正確。**
  `s8b_floor_campaign.py:4350` `_verify_resume_store` は store を再読するが、これは resume の
  **実走前** gate である。正しくは「実走終了〜report 生成の窓については 0 件」。
- **brief の DW-O09 判定「pin 閉包 0 件」は成果物 bytes の pin についてのみ正しい。**
  generator source hash の pin 系統を見落としていた。下記 B-1 で訂正する。

## 所見の裁定

| # | 判定 | 採否 | 根拠と処置 |
|---|---|---|---|
| A-1 | real | 採用 (記述限定) | 保証は「report が各 store を読んだ瞬間の一致」であって連続不変性ではない。一時改変後の復元と読取後の差替えは検出しない旨を、receipt を作る helper の docstring と insight に明記する。実装追加は無し。 |
| A-2 / B-3 | real | **採用 (land blocker)** | M10 (resolve 後 containment 削除) の killer が絶対 path / `..` の字句拒否で先に赤くなり、変異行を通らない。**out_root 内の symlink が外を指す負例を 2 本追加** (親 component が symlink / leaf が symlink) し、M10 の期待 node をそれへ差し替える。DW-M01 の「同じ入力を拒否する層が前後に無いこと」に該当。 |
| A-3 | real | **部分採用** | report 側の新設 resolver は component ごとに `O_NOFOLLOW` で開き、leaf を `fstat` で regular file と確認し、chunk 単位で hash する (scope 内)。**`s8b_oracle_driver._store_sha256` の強化は scope 外** — driver は実走前 gate で本 wave の変更面でなく、DW-G03 (族一般化には独立 2 例) に照らし 1 例で族へ広げない。裁定パッケージへ回す。 |
| A-4 | real | **採用 (land blocker)** | 恒真性の負例を 7 本追加する (下記 plan v2 の 3)。 |
| A-5 / B-4 | real | 採用 (限定形) | `ReverifiedFreeze` は権威**値**であって偽造耐性トークンではない (`s8b_ratified_freeze.py:798` 自身がそう書いている)。型 seal の新設は T-1103 と同型の防御的堅牢化なので**採らない**。代わりに (a) `build_observations` の production caller が `main()` ちょうど 1 件であることを pin するメタテストを足し、(b) docstring に「certifying path は `main()` の直接配線のみ」と明記する。 |
| A-6 | real | 既知の非目標 | T-1103 の見送りと整合。receipt を「封印」「第三者向け証明」「report 後に独立再検証可能」と説明しない。実装追加は無し。 |
| A-7 | real | **採用 (land blocker)** | M1 の killer 条件が不足。正しい store root で全 cell が `match` になる CLI baseline を作り、出力 receipt の exact content を検査する形へ差し替える。 |
| A-8 | real | 採用 (登録から除外) | `s8b_oracle_judge.py:515` は `unknown = bool(top_reasons) or ...`、`:541` の overall も同様 (親が逐語確認)。top_reason を 1 本足せば indeterminate は確定するので、**M7 は受理ゲートの変異ではない**。DW-M01 の単一理由性が立たないため**事前登録から外す**。 |
| A-9 | real | 一部採用 | combined verdict への receipt 欠落 / mismatch の負 E2E を **1 本追加** (安価で scope 内)。certified 選択・台帳への効果は現 checkout に存在しないので主張しない (上記訂正)。n-pilot は scope 外のままとする。 |
| A-10 | **refuted** | 対応不要 | legacy manifest は既存の `manifest-kind` top reason で indeterminate になる (`s8b_oracle_judge.py:334`)。黙って緑にはならない。 |
| A-11 | **refuted** | 対応不要 | 期待 SHA の出所は run / WAL から独立している。ただし `reverify_published_freeze` は store の現在 bytes を読まない — その空白を本 receipt が埋めるという整理をそのまま採る。 |
| B-1 | real | **採用 (land blocker)、ただし影響を訂正** | `_validate_generators` (`s8b_oracle_manifest.py:430`) が report / judge / artifacts の**ファイル byte hash** を厳密照合する。ただし **production では発火しない** — `s8b_oracle_spec.APPROVED_SPEC_SHA256` は `None` で `load_approved_spec` は `no-approved-spec` を返す (親が実測)。実際に赤くなるのは test golden。**親が一時変異で実測した権威ある閉包 = `orchestrator/tests/test_s8b_oracle_manifest.py` 100 件中ちょうど 2 件**: `test_build_approved_valid_fixture_output_depends_only_on_spec_pin` と `test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`。`test_reviewed_spec_requires_canonical_bytes_without_trailing_lf` は**影響しない** (末尾 LF 拒否が先に発火)。同型は `docs/failures.md` の **F226** が記録済み。 |
| B-2 | real | 採用 | F226 の恒久対応どおり、report / judge を変異させる**全登録の期待 node に上記 pin テスト 2 件を必ず含める**。事前登録時に「この変異は source hash を変えるか」を 1 行で判定する。 |
| B-5 | nit | 記述訂正のみ | 上記の親実測訂正に反映済み。 |
| B-6 | real | **scope 外 → 裁定パッケージ** | store と receipt を同時に改変すれば determinate へ到達できる。これは T-1103 が明示的に見送った偽造耐性の面であり、本 wave では閉じない。 |

## plan v2 (段 5 へ渡す確定形)

1. 段 2 プランの編集面表・receipt schema・fail-closed 棚卸しを**基本そのまま採用**する
   (`ReverifiedFreeze` 自体を authority token として `build_observations` へ渡す形を含む)。
2. **PIN_GATE_SPEC の更新は必須**: `orchestrator/tests/test_s8b_oracle_manifest.py` の
   `PIN_GATE_SPEC_RAW` 内の `report` / `judge` の `sha256` literal を最終編集後の実 byte hash へ更新し、
   `PIN_GATE_SPEC_SHA256` を `hashlib.sha256(PIN_GATE_SPEC_RAW).hexdigest()` で再計算して更新する。
   golden の独立性 (production serializer を通さない手書き canonical bytes) は壊さない。
   **これは report / judge への最後の編集の後に行う。** 段 6 fix で再編集したら必ずやり直す。
3. **追加する負の対照** (すべて恒真にならないこと):
   - 恒真性 7 本: receipt が空 mapping / `cells=[]` / schedule から 1 件欠落 / cell 重複 /
     outer=`verified` かつ cell=`mismatch` / outer=`unverified` かつ全 cell=`match` /
     `mismatch` なのに expected=actual (および `missing` なのに actual 非 null)。
   - symlink escape 2 本: out_root 内の親 component が外を指す symlink / leaf が外を指す symlink。
   - CLI baseline 1 本: 正しい store root で全 cell `match`、receipt の exact content を検査 (A-7)。
   - combined verdict 負 E2E 1 本: receipt 欠落 / mismatch が combined verdict まで伝播する (A-9)。
   - production caller pin 1 本: `build_observations` の production 呼び出しが `main()` 1 件 (A-5)。
   - 段 2 プランの A (置換) / B (削除) / C (receipt 欠落) と正の対照はそのまま。
4. resolver は絶対 path・`..`・制御文字の字句拒否に加え、component ごとの `O_NOFOLLOW` open、
   leaf の `fstat` regular file 確認、chunk 単位 hash とする。
5. 変異事前登録は **M7 を外し**、残る M1〜M6・M8〜M10 の**期待 node に pin テスト 2 件を必ず加える**。
   M10 の killer は symlink escape 負例へ差し替える。M1 の killer は A-7 の CLI baseline へ差し替える。

## 裁定パッケージ (ユーザーへ返す、本 wave では実装しない)

- **[P-1]** `s8b_oracle_driver._store_sha256` の no-follow / regular-file / chunked 化 (A-3 の driver 側)。
  実走前 gate も同じ穴を持つが、本 wave の変更面ではなく DW-G03 の独立 2 例が揃っていない。
- **[P-2]** store と receipt の同時改変に対する耐性 (A-6 / B-6)。T-1103 が見送った面と同一。
