---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1431-floor-pilot-rerun
seq: 1
title: [T-1431] 床値 pilot を再投入し、3 セルの build 到達と 2 blocker を実測した (実測のみ、実装差分ゼロ、branch worktree-dev-wave-t1431-floor-pilot-rerun)
---

## 本文

- 床値 pilot を再投入した (request `940170.nqsv`、nonce `841537990c502065fb92c79655f47fe7`、
  投入元 commit `c301c4fdb0bc7997d729fe0de80f8b99356a6012`)。実測記録の正本は
  `output/insights/2026-08-23_t1431-floor-pilot-rerun/README.md`。
- **前回 (`926261.nqsv`) の閂 2 本は実際に外れていた。** checkpoint に前回不在だった
  `fetchcontent-staging` 段が現れ、masstree が期待 HEAD のまま計算ノードへ届いた。
  12 セル中 3 セルの binary が build 完了した (sha256 は 3 本とも相異)。**ただし計測到達セルは
  0 で、床値の実測値は得られていない。**
- **投入パラメータ表に無い前提が 1 つあった。** [T-1461] の staging は third-party 永続 cache が
  worktree へ hydrate 済みであることを前提とするが、その cache は本 wave の worktree・
  main checkout・[T-1461] 自身の worktree のいずれにも不在だった (`.gitignore` 対象の機体
  ローカル path)。`tools/pegasus/README.md` §6 の標準供給経路で hydrate してから投入した
  (`verify` / `hydrate` とも rc=0)。裁定控え
  `rulings-inbox/2026-08-04-t340-guard-bash-sanctioned-path.md` は当該ツールを admission
  registry へ `local-ok` 登録済みと確定しており、hook 拒否なしで走った事実がその着地を裏づけた。
- 停止点は 2 つで、いずれも本 wave では**直さず記録に留めた** (scope は再投入と実測であり、
  fail-closed の回避を含まない)。
  - blocker A (一次): `sort_best` セル build が約 7 秒で失敗したが、
    `s8b_floor_campaign.py` の `except Exception as exc:` が元例外を構造化 error へ差し替える
    ため、**失敗理由がどこにも永続化されない**。build は計算ノードローカルの scratch で
    行われジョブ終了とともに消えるので、本試行の記録からは根本原因を確定できない。
  - blocker B (潜在・確定): `floor_masstree_payload_v1.json` の `archive_sha256` は
    ビルド成果物 `libkohler_masstree_json.a` の sha256 だが、生成器は毎回異なる temp dir で
    ビルドし、`-g` により object へ `DW_AT_comp_dir` が入る。**期待値は構造的に再現不能**で、
    実測でも不一致だった (`0a6514a0…` vs `9c1034fa…`)。pin と `config.h` は一致しており、
    食い違うのはビルド成果物だけである。最小 probe (同一 source・同一 g++ 11.4.0・同一 flag、
    directory だけ変更) で object と archive の sha256 が変わることを実証した。
    compiler は計算ノード・ログインノードとも同一版で、環境差では説明できない。
- blocker B は失敗台帳の新規エントリに相当するが、`docs/spool/failures/README.md` が
  恒久対応に実体へのポインタを要求するため、**是正が裁定で決まるまで F は起票しない**。
  裁定と実装が済んだ時点で同じ事象として起票する。
- **admission チケットの消費は 0 枚**だった (admission root 配下に 2026-08-23 以降の
  作成・更新 file が 0 件)。`retry_slots_per_cell=2` は全 12 セル満枠のまま維持している。
- 本 wave は実装面ゼロの実測 wave として軽量版で回した (設計択一なし・正しさ防壁非接触・
  受理集合不変)。段 5・6 の実装子は起動していない。

## 次の一手差分

### 更新

- [T-1431] **P1**: 床値 pilot は 3 セル build 到達・0 セル計測で停止した。次は
  {{T:floor-build-diagnostics-persist}} で失敗理由を取れるようにし、
  {{T:floor-masstree-archive-pin}} の裁定を得てから再投入する。再投入時の
  パラメータは `output/insights/2026-08-23_t1431-floor-pilot-rerun/README.md` の
  「環境・実行パラメータ」節をそのまま使える。
  base: cdcda157c4e6dbd5e7b53419b835d8954d4cc5e053852914c8efbe48fd8dd22a

### 新規

- {{T:floor-build-diagnostics-persist}} **P1・新規**: floor cell build の失敗理由を計算ノード外へ
  永続化する。`s8b_floor_campaign.py` が構造化 error へ差し替える際に握り潰している元例外の
  本文と、可能なら configure/build の stderr 末尾を失敗 record へ載せる。これが無い限り
  blocker A の再投入は情報を増やさない。
- {{T:floor-masstree-archive-pin}} **P1・ユーザー裁定待ち・新規**: masstree payload の
  `archive_sha256` pin が構造的に再現不能である件の裁定。再現可能へ寄せる方向
  (ビルド path の正規化、`ar` の決定的 mode、期待値を計算ノード上で生成) と、述語自体を
  変える方向 (成果物 bytes でなくソース同一性 + toolchain manifest で束縛) は受理集合が
  変わるため親が決めない。`config_sha256` は再現するので束縛を弱めずに直せる余地がある。
