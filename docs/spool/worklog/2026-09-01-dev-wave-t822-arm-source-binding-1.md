---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t822-arm-source-binding
seq: 1
title: [T-822] 第 2 条件の残余は [T-1994] だけと確定し、読み取り専用束縛の生死を計算ノードで確認した — 閉じるには稼働 wave が所有する 1 file が要る (insight のみ、branch worktree-dev-wave-t822-arm-source-binding、実装面の差分ゼロ・変異 matrix 免除)
---

## 本文

- ユーザー依頼は `/dev-wave [T-822] の残る第 2 条件を実装する` (背景 job)。裁定は D863。
  依頼は「残るのは第 2 条件 = 宣言 arm から実 CCBench source への因果束縛だけ」と書いたが、
  **この記述は 2 方向に誤っていた。** 文字列としての因果束縛は `[T-1749]` が 2026-08-26 に、
  実行到達性は `[T-1805]` が 2026-08-27 に、契約 C10 の追随は `[T-1806]` が 2026-09-01 に
  閉じている。残るのは `[T-1994]` (所有者自身による A→B→A) 1 件だけである。
- **親が段 1 で逆向きに間違えた。** D1289 の理由文「D863 が着手条件とした証拠欠落 3 件のうち
  唯一の未解決項」を状態確定の根拠に使い、「第 2 条件は全部閉じた」と結論した。
  段 3 のレンズ A が D1201 を出して反証した。D1289 の決定本文は層 3 の hard failure だけで、
  対象固有の後発裁定 D1201 を supersede していない。親は D1201 を原文で裏取りして
  brief を v2 へ差し替え、段 2 から回し直した。旧 brief は流用していない。F67 の再発項。
- **段 3 の 2 レンズは別の射影で走らせ、独立に同じ辺へ到達した。** レンズ B には親の結論を
  見せず、D863 の逐語と「未着手」と書いてある当時の台帳だけを渡した。B は現行コードから
  束縛の鎖を 7 段で書き出し、7 番目 (WAL source identity から実 compiler input と bench binary)
  が `producer-execution-contract` 止まりで mutable source の ABA 窓が残ると判定した。
  A が D1201 経由で名指しした対象と同じである。
- **D1201 が明示要求する「計算ノードでの実証」を取った。** 機構を作る前の生死確認 (DW-G01)
  として、計算ノード `bnode024` で読み取り専用束縛が所有者自身の `chmod u+w` を EROFS で
  拒否することを実測した。`bwrap --ro-bind` と `unshare --mount --map-root-user` +
  `mount --bind -o ro` の**独立な 2 経路**が成立した。login node は kernel 5.15.0-190、
  計算ノードは 5.15.0-173 で版が違うため、転移を仮定せず測った。
- **段 2 の分岐点判定が段 3 で覆った。** 段 2 は「`buildcache.py` 無変更で実装できる」と
  判定したが、レンズ A が 4 経路を挙げて否定した。とくに **cache への publish が
  context manager の cleanup より前**に起きるため、防護の破れを `__exit__` で検出しても
  publish 済み binary を取り消せない。親が現物 (`os.rename` による publish) で裏を取った。
- **本 wave では実装しないと裁定した。** must-fix 4 件が `orchestrator/campaign/buildcache.py`
  を要求し、同 file は稼働中の別 wave (t441 系 5、t1905) が所有している。依頼は重なる file を
  触らずに報告することを求めている。**部分実装は採らなかった** — 脅威を閉じない機構に防護の
  名を付けるのは D1201 が却下した「検出だけ入れて拒否しない」と実質同じで、恒真な保証になる。
- **塞いでいるのは 1 file だけである。** `s8b_expected_materialization.py`、
  `s8b_binary_admission.py`、その consumer 5 module、対応する test 3 file は、branch の
  三点 diff でも全 worktree の未 commit 差分でも重複 0 件だった。
- 段 3 が出した所見のうち、親が **refuted / scope 外**に裁定したもの: (a) `do_build=False` の
  no-build 受理で全 field が unbound のまま receipt が出る — receipt は `certifying=False` で
  `no-build` 理由が明示され、certified 受入の経路ではない (D536 が意図的に維持)。
  (b) predicate digest equality が mask 等式に含意されて恒真 — 冗長 gate であって穴ではなく、
  `[T-1749]` の wave が同型を実測して両層同時変異へ再照準済み。(c) cross-binding 受領証の
  本体を後段が再検証しない — `[T-1807]` として既に起票済み。(d) provider raw response から
  proposal coder wire への辺が consumer 独立照合でない — 第 2 条件の残余ではない別の辺。
- **受領証 v3 の費用を実測した。** 発行済みの実 v2 受領証は現 worktree / main / 既知 mainprobe の
  成果物置き場に 0 件で、失われる正式成果物は無い。凍結成果物・campaign lock・契約 C10 の
  再発行も不要。ただし中央 validator の production consumer は 9 箇所ある。
- **実 CMake canary を受入へ足す案を却下した。** 現 canary が受入台帳で `0.0` 秒なのは速いから
  ではなく `gcc-13` 不在で skip しているためである。同型実測 (D665) は cold build 単独
  17.96〜18.16 秒、受入並列負荷下 42.90〜50.39 秒で、2 configuration でも受入換算
  86〜101 秒、全 12 cell なら 515〜605 秒になる。D311 と D678 に抵触する。
- 子の工数: codex 5 本 (plan 1・consult 4)。model は全段 `gpt-5.6-sol`、reasoning は `xhigh`。
  採用 gate (`check_codex_output.py`) は 5 本とも rc=0。
- 一次資料は `output/insights/2026-09-01_t1994-readonly-snapshot-design/`。
  設計択一 4 件をユーザー裁定へ返す (下記 `[T-1994]` の項)。

## 次の一手差分

### 更新

- [T-822] **P2・裁定済み (D863) → 残るのは第 2 条件の一部だけ**: 3 条件のうち第 1 条件
  (層 3 鎖の必須経路化) は `[T-2075]` が 2026-09-01 に D1289 で、第 3 条件 (レポート間で
  計測対象の一致) は 2026-08-26 に閉じた。**第 2 条件 (宣言 arm と実走 arm の同一性) は
  3 段で縮み、残りは `[T-1994]` 1 件だけである** — 文字列としての因果束縛は `[T-1749]`
  (2026-08-26、commit `1e10a081f`、D955)、実行到達性は `[T-1805]` (2026-08-27、D966/D1134)、
  契約 C10 の追随は `[T-1806]` (2026-09-01、D967) が閉じた。**本項の第 2 条件の実体は
  以後 `[T-1994]` が持つ。** 8c 正式系列の着手条件は `[T-1994]` が閉じた時点で満たされる。
  base: f93b23974ae98eaa9df2e524fc0bfb92a20e1bfdd7fede24ab5ecf514beaa45d
- [T-1994] **P2・裁定済み (D1201) → 設計と生死確認は済み、実装は 1 file の所有待ち**:
  **本項は D863 第 2 条件の残る実体である** (D966 が「build 中の source 差し替え」を閉じる
  対象として逐語で名指しし、D1201 が閉じると裁定した)。2026-09-01 に次を確定した。
  (i) 読み取り専用の束縛は計算ノード `bnode024` で成立する — 所有者自身の `chmod u+w` が
  EROFS で拒否されることを `bwrap --ro-bind` と `unshare` + `mount -o ro` の独立 2 経路で実測。
  D1201 が要求する計算ノードでの実証の機構面はこれで取れた。
  (ii) 設計は「identity user/mount namespace + 匿名 tmpfs への exact copy + digest 再照合 +
  recursive read-only seal」。単純な read-only bind は同一 uid の別 namespace から下層 inode を
  書けるため不足。`squashfuse` は `/dev/fuse` 不在、`chattr +i` は初期 userns 権限が必要で不可。
  (iii) **実装には `orchestrator/campaign/buildcache.py` の変更が要る** — cache publish が
  context manager の cleanup より前、build 子孫の nested userns 禁止、既存 full tree 再照合の
  受理集合拡大、user namespace の build 後残留、の 4 件。同 file は稼働中の別 wave が所有。
  (iv) 他の編集面 (`s8b_expected_materialization.py` ほか 9 file) は重複 0 件。
  **ユーザー裁定へ返す設計択一 4 件**: (a) user namespace の残留を許すか、build だけを fork した
  子で隔離するか (後者は `buildcache.py` を要する)。(b) `buildcache.py` の所有が空いた後に
  段 3 の修正条件を織り込んで実装へ進めてよいか。(c) 実 CMake の qualification を毎回の受入から
  外し計算ノードで一度きりの artifact にするか。(d) `proof.source_protection_kind` を型
  (exact capability) で受け渡すか — 固定 literal は恒真なので採らない。
  一次資料は `output/insights/2026-09-01_t1994-readonly-snapshot-design/`。
  base: 2b6a3890c9028e07282a5729a26ba32c12db4873f0aef3b50bef4db804d2454f
