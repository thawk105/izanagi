---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-acceptance-user-site-gate
seq: 1
title: 受入全走が全 wave で取れなくなった障害を 3 セッション協働で特定し、束縛 runner へ検証済み xdist root を渡して復旧した (コード + テスト、branch worktree-dev-wave-acceptance-user-site-gate、受入 child-green / loadgroup 到達)
---

## 本文

**2026-08-27 の午後、受入全走が全 wave で取れなくなり、少なくとも 3 つの dev-wave
(t2010 / t1981 / t2001) が land 前で停止した。** 本 wave はその原因を特定して修理したものである。

### 症状と根因

`tools/dev_wave_wait.py acceptance` が `rc=70 / source_rc=16` で失敗する。
計算ノードの子が `pytest-xdist` を import できず `_PEGASUS_DISPATCH_RC` (=16) を返していた。

根因は **`b93861570` が導入した `runner_binding` 経路**である。同 commit は
計算ノードの内側 runner に **`-I` を新規追加**した。`-I` は `-s` を含むので user site が
`sys.path` から落ちる。本環境の `pytest-xdist` は **user site にしか無い**ため import できない。

**実 pytest 子は元から `-I` 無しで起動されている** (`tools/run_tests.py` の
`cmd = [python_executable, "-m", "pytest"]`)。テスト本体は user site を見えており、
壊れていたのは**可用性を判定する gate が隔離側にあった**点だけである。

**機構は自分の受入で一度も実行されないまま着地していた。** `b93861570` の commit message 自身が
「manifest が 1 key も無ければ現行の pathname 起動を維持する (段階 P 自身の受入がこの経路を通る)」
と書いており、`git merge-base --is-ancestor b93861570 98f61815c` は偽である。
memory `gate-tools-need-parent-live-dogfood` の型そのものである。

### 3 セッション協働と、その過程で潰れた誤り

ユーザー指示により並行 2 セッションおよび Codex 計 4 レンズと相互検査した。
**過程で 6 つの誤りが実測で潰れた。うち 4 つは本 wave の親のものである。**

- (親) 「計算ノードごとに xdist の有無が違う」— **反証**。時間順が逆転した対で否定された。
- (親) 「880 走行の分割表と 11 ノードの対応ペアがノード仮説を反証する」— **反証**。
  `runner_binding` は `b93861570` 以後にしか存在せず、ノード内でも bound は常に後で交絡が残る。
  t1981 が自分の 855 件で**逆転対 0 件**を実測して確認した。
  交絡の無いノード反証は**逆転対 2 例だけ** (t2001 の bnode007、親の bnode004 =
  job 952713 rc=16 -> 952718 rc=0、同一 interpreter、5 番違い)。
- (親) 「`-I` は前からあったので引き金ではない」— **反証**。外側 launcher の `-I` は
  `28b186e9e` で前からあるが、**内側 runner の `-I` は `b93861570` が新規追加**。別 surface である。
- (親) 「修理は `site.getusersitepackages()` で user site を復元する」— **反証**。後述。
- (t2001) 「束縛起動はテスト被覆ゼロ」— **反証**。`_bound_runner` で grep して実体の
  `_run_bound_tests_child` を落とした別名束縛の取りこぼし。機構には正例 3 本が既にあった。
- (t1981) 「最後の緑受入は 14:28」— **反証**。それは 41 failed。緑は t1974 の 14:27。

**因果の中核は統計ではなく機構の直接証明である** (`-I` = `-E`+`-s` / xdist は user site のみ /
bound 経路は `-I` を使う)。880 件の分割表は**修理前の負例の一次資料**としてのみ役割を持つ。

### 修理の設計と、`site` を使わない理由

Codex は (e)「xdist gate を実 pytest 子へ移す」を推奨した。**設計論としては (e) が正しい。**
しかし `tools/dev_wave_land.py` は受入 receipt の検証で `run_tests.py` の
**main と tip の blob 一致を要求する**ため、`run_tests.py` を変える wave は land できない。
この制約は相談投入後に親が発見したもので Codex へ渡せていなかった。
**(e) は land 契約を変える別 wave の課題として残す。**

land が pin する 3 path (`run_tests.py` / `acceptance_launcher.py` / `dev_wave_wait.py`) の外で
修理を置けるのは `tools/pegasus/dispatch_compute.py` だけであり、
**D1184 が「`dispatch_compute.py` 編集 wave は現段階の束縛外」と既に明記している**ため
例外規定を必要としなかった。

**親が最初に推した `site.getusersitepackages()` は穴だった。** 倒れ方が逆である。

```
PYTHONUSERBASE=/tmp/evil python3 -I -c "import site; print(site.getusersitepackages())"
  -> /tmp/evil/lib/python3.10/site-packages     <- fail-open。攻撃者の path を黙って返す
PYTHONUSERBASE=/tmp/evil python3 -c "from importlib import metadata; \
    print(metadata.distribution('pytest-xdist').locate_file(''))"
  -> PackageNotFoundError                        <- fail-closed
```

`-I` は startup の環境解釈を止めるが `site._getuserbase()` の `os.environ` 読取りは止めない。
子の中で `site` に問い合わせると **`-I` が閉じた注入面を開き直す**。
3 セッションのうち 2 つが独立に同じ穴を指摘し、親が実測して撤回した。

採用した形は {{D:bound-runner-user-site-gate}} に書く。

### 検証

**正例が恒真でないことを実測の対で固定した。** 注入行を `pass` へ一時変異させると
正例 `test_bound_child_imports_xdist_from_validated_appended_root` が赤になり、
復元すると緑に戻る (`DW-O19` の復元規律に従い、変異前後で作業ツリーの一致を確認)。

焦点走 312 passed。`tools/check_docs.py` と `tools/check_subprocess_bytecode_guard.py` は rc=0。
途中 1 件落ちた `test_pending_orphan_hold_survives_external_sigkill` は
単独緑・同一 tip での再走緑の偽赤であり、実装差分に帰属しない。

**受入全走は `verdict=child-green` / `child_rc=0` / `effective_scheduler=loadgroup`。**
`loadgroup` 到達は xdist が計算ノードで動いた証拠であり、修理前の bound 経路 30/30 が
rc=16 だったのと対になる。`tested_main` は修理を含まない `9aea38046` のままで、
修理は tip にしかない — 自己適用が成立している。

**ただしこの緑が証明したのは tip 作業木の dispatcher が使われる経路だけである** (t2001 の指摘)。
`tested_main` が修理を含む状態、すなわち **main 側の dispatcher が使われる経路**は、
本 wave の land 後に他 wave が取る最初の受入が最終正例になる。
**両方が緑になって初めて両経路が通ったと言える。**

## 次の一手差分

### 新規

- {{T:acceptance-gate-in-pytest-child}} **P2・新規**:
  Codex が推奨した (e)「xdist gate を実 pytest 子へ移す」を実施する。
  本 wave は `tools/run_tests.py` が land の blob 一致 pin に掛かるため採れなかった。
  **land 契約 (`dev_wave_land.py` の `main_runner_entry[1] != tip_runner_entry[1]`) を
  どう扱うかが本体**であり、pin を緩めるのではなく「runner を変える wave の
  受入をどう取るか」の設計が要る。実装面のため Codex `role=author` が要る。
- {{T:bound-runner-pth-dependency}} **P3・新規**:
  末尾 `append` では user site の `.pth` が追加する path は復元されない
  (`site.addsitedir()` を禁じた副作用)。今回対象の xdist は素の package なので届くが、
  **将来 `.pth` 経由でしか入らない依存が要求されたとき同じ無言 rc=16 が再発する。**
  再発時は `.pth` の要否を先に確かめ、`addsitedir` の可否を改めて裁定する。
  現時点では設計メモに留める (`DW-G04`: 発火条件を満たす artifact が無い)。
