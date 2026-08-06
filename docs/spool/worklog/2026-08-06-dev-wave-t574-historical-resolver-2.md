---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t574-historical-resolver
seq: 2
title: [T-574] 記録 contract hash からの世代解決を read-only 再検証へ配線した — live 実走 admission とは別入口にし、述語の世代分岐は名乗らない (コード + docs、受入 6806 passed / 20 skipped、変異 12/12 一致 (KILLED 9 / SURVIVED 3)、branch worktree-dev-wave-t574-historical-resolver)
---

## 本文

- **段 1 の前提実測が D196 を consumer 水準で裏取りした。** registry へ 2 世代目を実編集で足すと
  (`git checkout --` で即復元、復元後 blob 一致)、publish 済み `output/s8b-freeze/floor_protocol.json`
  が `FloorCampaignError` で、記録 hash を持つ manifest が `ReportError` で拒否された。
  同じ document を「記録 hash から解決した契約」で検証すると通る。
  逐語と復元証跡は `output/insights/2026-08-06_t574-historical-resolver/parent-measured.md`。
- **段 3 の 2 レンズが独立に同じ blocker を出し、親 brief の分類が誤りだと確定した。**
  親は 4 consumer を「read-only 再検証」と書いたが、うち 3 つを含む `launch_validate` は
  oracle driver の**実走 admission と共用**で、通過後に marker・WAL・予算が書かれる。
  親が呼び出し元をたどって裏取りした。設計は {{D:historical-reverify-entry-split}}。
  分類を誤った型は {{F:readonly-entry-shared-with-live-admission}}。
- **保証の名前を縮めた。** 正当な後継世代が変えられるのは calibration 参照の path/sha だけなので、
  clock・numactl・attestation mode は世代間で必ず同値になり、解決世代の値を使う実装と current を
  引く実装は正当な世代では観測的に区別できない。よって `versioned predicate dispatch` の語を
  成果物で使わず、保証を「記録 hash からの世代解決」と「解決世代の calibration 選択」に限った。
  {{D:generation-guarantee-scope-limit}}。**T-574 の題が指す後半は実装していない。**
- **変異が「新設した検査が冗長だった」ことを暴いた。** 実装子が足した hash 再検査 2 箇所は
  どちらを消しても両方消しても緑で、実際に落としていたのは既存の等値検査だった。3 層すべてを
  外す変異で KILLED になり実効 gate を確定した。run 1 は erratum として残し、run 2 を採用値とする。
  型は {{F:redundant-gate-counted-as-new-guarantee}}。
- **段 1 の DW-O09 判定は偽だった。** 「publish 済み artifact に旧 hash を pin したものは 0 件」と
  書いたが、`env_contract.py` の旧 sha は path key (silo artifact) と **role 名 key**
  (`env_contract_sha256`、t419 manifest) の双方に存在した。本 wave は同 file を変更しないため
  実害はない。F30 の三度目の再発として台帳へ送る。
- **既存の fail-open を 1 件見つけたが直していない。** oracle report は `run_contract` が宣言
  されていても `env_tag` / `contract_sha256` が欠落・空・非文字列なら legacy 扱いで receipt 検査を
  課さない。親が `fac84353^` で同一分岐の既存を確認しており、直すと未承認の受理集合縮小になる。
  択一として返す。
- **ユーザー裁定待ちの択一が 7 件ある。** 表と根拠は insights の README に置いた。骨格を決めるのは
  (1) 記録 hash を世代選択の権威にしてよいか (非偽造性の主張を弱めるか、活性化 record を先に実装するか、
  外部 trust root を導入するか)、(2) silo の `verify-result` は歴史 proof verifier か current 互換
  verifier か (今日すでに赤である)、(3) 世代更新を跨いだ resume を失ってよいか、の 3 つ。
  残る 4 件のうち 3 件 (真の世代別述語 dispatch、historical calibration の保存契約、
  oracle report の `repo_root` 分裂) は insights に記録するだけで起票しない。
- **段 8 の改善候補は 2 件で、1 件を実施し 1 件を予算で見送った。** 実施したのは、親が段 1 の前提実測用に
  書いた probe の `.py` を insights へ凍結して provenance の実装面 Codex author 契約に抵触した件で、
  既存 F75 と同型のため**再発**として台帳へ送り、F75 の判別条件を「段 6 で harness を書く前」から
  「親が実行可能ファイルを書くとき常に」へ広げた。見送ったのは、worktree 隔離された背景 job で
  codex 起動を launcher script 経由にする作法で、`docs/dev-wave/**` の合計が
  25,187 / 25,200 bytes と**残り 13 bytes** しかなく 1 行が入らない。**同じ理由での見送りは 3 例目**で、
  予算飽和そのものを択一 R8 として返す (上限引き上げも dev-wave 系の外出しも既裁定で封じられている)。

## 次の一手差分

### 更新

- [T-574] **P2・一部完了**: 記録 contract hash からの世代解決を read-only 再検証
  (`reverify_published_freeze` と oracle report の manifest 再検証) へ配線し、live 実走 admission は
  current 束縛のまま分離した。**題が指す `versioned predicate dispatch` は実装していない** —
  正当な世代遷移では観測差を作れず、名ばかりの保証になるため
  {{D:generation-guarantee-scope-limit}} で保証範囲を縮めた。真の世代別述語 dispatch を起こすかは
  `output/insights/2026-08-06_t574-historical-resolver/README.md` の択一 R4。
  残件はこの R4 だけで、[T-529] の前提としての blocker は外れた。
  base: f287da0e241eef48f8cfc900e7f18c3b0c952d4aa24e500f5ac0acc57bf7e119

### 新規

- {{T:silo-verify-result-semantics}} **P1・ユーザー裁定待ち**: silo の `verify-result` が
  committed artifact の `contract_sha256` を **current** lookup と比較する層をどう扱うか決める。
  親の実走では**今日すでに赤**である (`current binding mismatch: driver`)。
  歴史 proof verifier として記録 hash からの解決を配線するのか、current 互換検査だと明示して
  「全 certified 成果物を再検証可能」という表現から除外するのかが未裁定。
  根拠は `output/insights/2026-08-06_t574-historical-resolver/README.md` の択一 R2。
- {{T:generation-resume-availability}} **P1・ユーザー裁定待ち**: 契約世代を跨いだ campaign resume を
  失ってよいかを決める。resume admission は current 束縛のままにしたため、世代更新後は旧世代で
  始めた campaign を再開できない。`linux-baremetal` は resume を許す設定であり、
  「pegasus は禁止だから実害なし」という当初の一般化は段 3 の両レンズが否定した。
  受容して回帰試験で固定するか、記録契約を resume 実行辺まで伝播する別 scope を起こすか。択一 R3。
- {{T:oracle-run-contract-legacy-fallopen}} **P2・ユーザー裁定待ち**: oracle report が、
  `run_contract` を宣言していても `env_tag` / `contract_sha256` が欠落・空・非文字列なら
  legacy 扱いで execution receipt 検査を課さない既存挙動を直すか決める。契約・calibration・receipt の
  束縛なしに行が completed へ到達しうる。直すと受理集合の縮小になるため未承認では動かせない。択一 R7。
