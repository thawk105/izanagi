# [T-481] Pegasus 実行体の admission 再設計 — 逐語と実測

wave = `dev-wave-t481-pegasus-admission`、branch = `worktree-dev-wave-t481-pegasus-admission`。
台帳の正本は worklog / decisions / failures であり、本 directory は逐語の凍結である。

## 実測 (親が実 hook を subprocess として起動。site = PEGASUS_LOGIN、機体 = pegasus02)

| ファイル | 内容 |
|---|---|
| `probe_baseline.json` | 変更前の受理・拒否。`tools/pegasus/` の全 entry と [T-482] / [T-483] の綴り |
| `probe_attached_m.json` | `-m` の密着形と分離形の対照。借用が起きる綴りの特定 |
| `probe_lens_claims.json` | 段 3 レンズの受理集合主張の裏取り。**6 系統が変更前から通っていた** |
| `probe_fix4_result.json` | 変更後の 69 綴り照合 (mismatch 0)。期待値は変更前実測から導いた |
| `feasibility.txt` | 計算ノード (bnode008) で §7.0 の測定手順が成立しないことの実測 |

**変更前から通っていた 6 系統** (`probe_lens_claims.json`):
`python3 -m cProfile <pegasus path>` / `-m pytest.__main__` / `-m _pytest.main` /
`python3 -W ignore <pegasus path>` / `bash -O extglob <job body>` /
`cd hooks && python3 ../tools/pegasus/...` / `systemd-run --user --scope -- pytest -q` /
`bash -lc` 3 段ネスト。前 4 系統は本 wave で閉じ、後 4 系統は裁定へ返した。

## 段別の逐語

`s2-plan.md` (段 2 プラン) / `s3-lensA.md` `s3-lensB.md` (段 3 敵対レンズ、両者 NO-GO、real 19) /
`s4-ruling.md` (段 4 裁定) / `s5-impl.md` (段 5 実装報告) /
`s6-revA.md` `s6-revB.md` (段 6 敵対レビュー、両者 land 不可、real 各 4) /
`s6-fix2.md` (fix 2 巡目) / `s6-refocus.md` (焦点再レビュー、closed 2 / partial 4 / regressed 2) /
`s6-fix3.md` (fix 3 巡目) / `s6-fix4.md` (land 済みテスト 2 本の赤に対する最小是正)。

fix 1 巡目は編集ゼロで停止した (親 prompt が「既存テスト」を tracked 限定と書かなかったため、
子が同 wave の新設 assert を保護対象と解釈して fail-closed。F112 の再発)。逐語は
`s6-fix.md` として job directory に残るが、編集が無いため本 directory へは凍結しない。

## 変異

| ファイル | 内容 |
|---|---|
| `mutation-spec.json` / `mutation-ledger-v1-erratum.json` | 初回。M4 / M5 = KILLED、M1 / M3 / M6 = MISMATCH (期待 node の過小登録)、**M2 = SURVIVED** |
| `mutation-spec-v2.json` / `mutation-ledger-v2.json` | 再照準。M1 / M3 / M6 = KILLED、M2b = MISMATCH (期待 node 3 本中 2 本が赤) |

**M2 の生存は等価変異ではなく他層の mask だった。** `_is_sanctioned` を借用可能へ広げても、
fix で入った残余走査が同じ入力を先に拒否するため受理集合が動かない。`DW-M02` に従い初回結果を
消さずに erratum として残し、両層同時変異 (M2b = 残余走査の pytest 検出を無効化 +
`_is_sanctioned` の借用復活) へ再照準した。M2b で赤になった 2 node は借用保護の pin そのもので、
kill の意味論 (受理集合が期待方向へ変わる) は成立している。3 本目に登録した
`test_bash_nonrefusing_sites_allow_module_and_prefix_matrix` は非拒否 site の検査で、
そもそも重量判定が走らないため赤にならない — 親の過大登録である。

## この wave が主張しないこと

- **族の症状は解けていない。** `collect_receipt.py` は拒否のまま残る。仕組み (三値 registry と
  fail-closed) は入ったが、許可へ反転した entry は 1 つも無い。
- **防壁の網羅は主張しない。** 変更後も 4 系統の迂回が残る (上記)。hook は第二防壁であり、
  script file 越し・変数展開・`python3 -c`・Codex 子・ユーザー端末は原理的に見えない (D103 決定 5)。
- **inventory meta-test が保証するのは inventory 同期だけである。** 分類の正しさや資源証拠は
  保証しない。危険な entry と `local-ok` 行を同時に足せば、test 側 golden も同時に更新される限り
  緑のままになりうる。
