# 段 1 brief — [T-1156] oracle 判定後の材料再取得を禁止する

## scope

floor (床値) campaign の `sort_best` cell における SWO oracle。oracle が依存材料の内容
(masstree HEAD + `config.h` sha256 + archive sha256) を判定した**後**に、cell build の cmake
configure が同じ FetchContent base に対して再 populate (再 fetch) を起こしうる経路を、
**事前拒否 (fail-closed)** で塞ぐ。現状は事後検知しか無い (D425 が明示的に「検知に留める」と裁定し、
禁止側は別審査へ送った。その別審査が本 wave)。

## 確定済みユーザー裁定

- 2026-08-25 /rulings 全件 (暫定): **禁止側へ倒す。** 判定後に材料が変わる経路は正しさの関門の穴である。
  正本 = archive worklog entry 956 の [T-1156] 本文。起票は entry 569
  (`FETCHCONTENT_FULLY_DISCONNECTED=ON` 等の可否を審査する / download 権威の変更)。
- D425 却下枝「依存 tree を書込み不能にして再 fetch を禁止する — download / 書込み権威の変更であり
  別審査が要る。本 wave は検知して fail-closed に留める」。
- 実装は Codex author (D95)。author / fix 子は commit しない。

## 親が段 1 前に実測した前提 (probe: job dir 外 `~/.claude/jobs/5bd37480/tmp/fcprobe`)

cmake 3.22.1 (login node)、CCBench と同じ 1 引数 `FetchContent_Populate(name)` 形で測った。

1. **populated + `FETCHCONTENT_FULLY_DISCONNECTED=ON`** → configure rc=0、source tree は無改変
   (故意に置いた `tampered.txt` が生存)。禁止は効く。
2. **source 削除 + flag なし** → 再 fetch が発火し tree が置き換わった (`tampered.txt` 消失)。
   判定後に材料が変わる経路は実在する。
3. **source 削除 + flag ON** → **configure は rc=0 で成功し、source を再作成しない。**
   CMake 3.22 の本 flag は「存在しない source を黙って通す」。
   → **flag 単独では fail-closed でない。** 恒真化を避けるには izanagi 側の事前 populate 検査と
   対で実装するしかない。これが本 wave の設計上の核心である。

## 閉包 — oracle 判定後に材料へ触れうる経路 (実アンカー)

| # | 経路 | file:anchor | 扱い |
|---|---|---|---|
| A | cell build の fresh configure (実行) | `orchestrator/campaign/buildcache.py` `_v2_commands` (def 1537) / 呼出 2087 / 実行 2108・2111 | **禁止対象 (主)** |
| B | 同 argv の記録側の双子 (cache hit 経路) | `buildcache.py` `_v2_result` → `_v2_commands` 1692 | A と同一生成器を保つ |
| C | oracle 前の populate | `buildcache.py` `prepare_masstree_fetchcontent` (def 1601) / 呼出 `s8b_floor_campaign.py` 3078 | 禁止対象外。ただし oracle 後に再入しないことを機械で言う |
| D | 既存の事後検知 (実効 root 照合 + 内容再観測) | `buildcache.py` 2124–2151 | 残す。禁止を足し、検知は引かない |
| E | configure argv の exact 述語 consumer | `paper_story_a1_paired.py` 1338 (`len == 10 + defines` と位置固定 index)、`paper_story_a2_certification.py` `_exact_trace0_configure_argv` 1295、`s8b_floor_campaign.py` `_portable_argv` 4188 (位置非依存の置換のみ) | token 追加で壊しうる側。守る |

`build_v2` の呼び手は `pipeline.py` 1074–1081 と floor の `build_fn` の 2 系統。base を渡すのは
floor の `sort_best` だけ (`s8b_floor_campaign.py` 3980–3991)。legacy `build()` (2254) は base を
取らず oracle も無い。

## 不変条件

- 絶対規律 2 / 3 を緩めない。既存の事後照合 (D) を削らない — **禁止を足し、検知を引かない。**
- FetchContent base を束縛しない build (pipeline / A1 paired / A2 certification) の configure argv を
  1 byte も変えない。
- 凍結成果物の bytes を変えない。凍結 manifest (`test_frozen_artifacts.py`) は s1 freeze 2 本 /
  v1 holdout freeze / floor protocol / selector prediction 証拠 / 裁定資料であり、build configure
  argv を pin していない — **段 2 で裏取りする**。
- `_v2_identity` の preimage を変えない (材料の同一性は既に dependency receipt + archive sha256 が
  担っている)。(P4) として攻撃対象。

## 親の provisional 裁定 (すべて攻撃対象)

- **(P1)** 禁止の実体は 2 枚で 1 組。(a) post-oracle configure argv へ
  `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` を足す。(b) その configure の直前に izanagi 側で
  「base が oracle 判定済みの内容で既に populated である」ことを検査し、不成立なら raise する。
  実測 3 により (b) が無ければ (a) は恒真になる。
- **(P2)** 新 token は `fetchcontent_base_dir` が束縛されたときだけ付ける (E の exact 述語を守る)。
- **(P3)** C は禁止対象外だが、oracle 後に呼ばれたら拒否する順序 gate を置く。
- **(P4)** cache identity (`_v2_identity`) は変えない。
- **(P5)** 「材料の再取得」の射程は fetch (FetchContent populate) とする。cell build が
  `masstree_build` target を source tree 内で作り直す**再生成**経路は別型であり、本 wave では
  所見として段 4 へ上げるだけで実装しない。

## positive control (恒真化しないための必須要件)

- (b) に対し: `masstree-src` 不在 / `config.h` sha 不一致 / archive sha 不一致 の 3 負例で
  実際に raise すること。
- (a) に対し: base 束縛時に flag が argv へ**ちょうど 1 本**、非束縛時に**0 本**。
  A1 / A2 の exact 述語が緑のまま通る正例を 1 つ添える。
- A と B が同一生成器から出ることを、実行経路と記録経路の両方で照合する。
- 変異事前登録は段 4 (`DW-M01`)。

## 成果物影響 (DW-G05)

禁止しない場合: certified な床値の `sort_best` 数値が、oracle が判定したのとは別の masstree で
作られた binary から出うる。現状の防壁は build **後**の内容再観測だけなので、configure が tree を
置換してから照合までの window が受理集合を広げる。床値は certified 選択の下限として使われるため、
依存の同一性を主張できない測定値が下限に入ると選択結果そのものが根拠を失う。

## 成果物の形

コード + テスト (実装面はすべて Codex author)。docs は spool fragment (worklog / decisions)。

## 並列分割 / 軽量版の可否

正しさ防壁 (oracle gate) に触り受理集合を変えるため、`DW-C00` により**軽量版にしない**。
段 2 プラン 1 本、段 3 敵対 2 レンズ (正しさ防壁 / 受理集合と exact 述語)、段 5 実装 1 本
(編集面が `buildcache.py` に集中するため所有分割の利が無い)、段 6 敵対レビュー 2 本 + fix。

## 受入・実測の環境

login node で pytest。計算ノードの実走は要求しない (本 wave は argv 生成と検査述語の変更であり、
実 cmake 実行は上記 probe で測り済み)。
