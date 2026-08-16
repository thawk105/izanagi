# [T-936] 段 4 裁定

2026-08-16 JST / base = main `ab3feb04` / branch `worktree-dev-wave-t936-rollout-identity`

入力 = 段 2 プラン (`verbatim/s2-plan-v1.md`)、段 3 レンズ A (`verbatim/s3-consult-a-sol2.md`)、
段 3 レンズ B (`verbatim/s3-consult-b-luna.md`)。両レンズとも **NO-GO**。
裁定 inbox は 09:20 JST に再走査し、[T-936] に関する更新なし
(最新 = `2026-08-16-rulings-full-43rulings.md`、07:29 JST)。

## 0. 親が撤回する主張

- **brief の不変条件 2「受理集合は現行の真部分集合。緩和はゼロ」は誤り。撤回する。**
  file 単位の候補述語は真部分集合だが、`_find_rollout` の成功条件は「候補ちょうど 1 件」であり、
  候補集合の縮小に対して単調ではない。候補を減らすことは resolver の成功を**広げる**。
  レンズ A 所見 1 とレンズ B が独立に同じ指摘をした。
  **正しい記述:** (i) 候補述語 `M_new ⇒ M_old` は成立する。(ii) resolver の成功集合は
  ユーザー裁定 #41 が命じたとおり拡大する — 実 corpus の 2 id が `RC_SESSION` から
  正しい親の解決へ変わる。この拡大が本 wave の目的であり、「緩和ゼロ」ではない。
- **brief の (P4) が引いた D75 は命名規則ではない。** D75 の決定文は freeze 族恒久設計である。
  ただし D75 本文は「検証時 HEAD と生成基準 commit を同名で混同した」事故を記録しており、
  repo 全体および `DW-O13` が「D75 の趣旨」として同名識別子の二義化回避に引いている。
  **P4 の根拠は D75 ではなく本 wave の根本原因そのもの**とする (下記 A6)。

## 1. 所見の裁定

| # | レンズ | 要旨 | 判定 | 処置 |
|---|---|---|---|---|
| A1 | A / B | 受理集合の定義が誤り | **real** | 採用。上記 0 で撤回・再定義 (A1) |
| A2 | A | veto が正当な候補を消して別候補を昇格させる | **real** | 採用。判定式を修正 (A2) |
| A3 | A | decode / 読取失敗が silent skip で不確実性が消える | **real** | **scope 外** → 裁定パッケージ R2 |
| A4 | A / B | probe が実装と実 scanner を束縛していない | **real** | 採用。段 6 の実測を差し替え (A4) |
| A5 | A | 非 str `id` の fallback が壊れた file を一意候補にする | **real** | 採用。fallback を締める (A5) |
| A6 | A / B | 4 file から将来 schema を一般化できない | speculative | 部分採用。記録に限定 (A7)。追加規則は入れない |
| A7 | A | pin fast path は全走査と同値でない / SHA 不一致の抜け道 | **real (既存)** | 記述訂正は採用。抜け道は **scope 外** → R3 |
| A8 | A / B | 変異の帰属が未成立、既存テストの先殺しと生存変異 | **real** | 採用。事前登録で閉じる (A8) |
| B1 | B | 消費側 `len(meta)!=1` で実害が残る | **real (半分)** | 下記 B1 で精密化。残余は **scope 外** → R1 |
| B2 | B | pin 経路の変異被覆が無い | **real** | 採用。pin 付き型 A/B fixture を追加 (A8) |
| B3 | B | `distinct-fields` 反転の一般化根拠が薄い | speculative | 反転は採用、根拠の書き方を是正 (A7) |
| B4 | B | P3 の `session-id-only` 維持が曖昧な互換を残す | speculative | A5 の締めで実質解消。key 欠落のみ維持 |
| B5 | B | P4 改名は scope を広げる | speculative | **不採用**。A6 の理由で採用する |

## A1. 受理集合の定義 (確定)

以後、次の 2 語を分けて使う。両者を混同した記述は書かない。

- **候補述語の受理集合** = `_rollout_matches_session(F, X)` が真になる `(F, X)` の集合。
  本 wave の変更でこれは**真部分集合になる**。
- **resolver の成功集合** = `_find_rollout(root, X)` が例外を投げずに path を返す `X` の集合。
  本 wave の変更でこれは**拡大する**。拡大分は実 corpus で実測した 2 id
  (`019f690c…`、`019fd52d…`) であり、いずれも「曖昧として拒否」から「観測された正しい親」への変換である。
  これはユーザー裁定 #41 が明示的に命じた変更であり、規律 2 に反しない。

## A2. 判定式 (確定・凍結)

レンズ A 所見 2 の反例を fail-closed へ戻すため、**プラン v1 の判定式を修正して採用する**。

```
own(r)  = r.payload["id"]         ("id" が非空 str のとき)
        = r.payload["session_id"] ("id" key が存在しないとき)
        = 同一性を与えない        (それ以外: null / 数値 / bool / 空文字)

owns_X        = ∃r ∈ meta(F): own(r) == X
first_owns_X  = own(meta(F)[0]) == X
declares_X    = ∃r ∈ meta(F): own(r) != X かつ r.payload["session_id"] == X

F が X を名乗る ⇔ owns_X ∧ (first_owns_X ∨ ¬declares_X)
```

`first_owns_X` の disjunct が **プラン v1 からの唯一の変更**である。意味は
「**先頭 session_meta 行が自分を X だと名乗っている file からは、後続行を根拠に同一性を剥奪しない**」。

**なぜこれで所見 2 が閉じるか。** レンズ A の反例は、同一 bytes の P/P file 2 本のうち片方へ
`{"id":"C","session_id":"P"}` を追記して、そちらを veto させ他方を一意にするものだった。
修正後は追記された file の先頭行が依然 P を名乗るため veto が発火せず、候補 2 件のまま
`RC_SESSION` になる。**現行と同じ拒否**であり、昇格は起きない。

**なぜ実 corpus の fork が依然直るか。** fork / thread_spawn の子 file は
**先頭行が自分 (子) を名乗り、親行のコピーは 2 行目以降**である (実測: 3 file すべて)。
先頭行が親を名乗らないので `first_owns_X` は偽、`declares_X` が真で veto が発火する。

**実測 (実 corpus 3,602 file、cache 経由)。** プラン v1 の判定式と本判定式は
**全 3,602 id で結果が完全に一致**し、いずれも件数 1。差分 id は 0 件
(`/home/SFC/tanab/.claude/jobs/47eaa767/tmp/probe_t936e.py`)。
つまり `first_owns_X` の追加は実データに対して no-op であり、反例だけを閉じる。
**この実測は cache 由来なので確定根拠にしない** — 確定は A4 の実装後実測で行う。

**凍結。** この判定式は `DW-O12` により凍結する。段 5・6 で受理集合を変える指示を出す直前に
本節を再読する。

## A3. 走査構造 (不変)

- pin 無し経路は `sessions_root.rglob("rollout-*.jsonl")` の全走査を維持する。
- 探索打ち切り・head 打ち切り・件数上限・filename による同一性判定を導入しない。
- 候補件数が 1 でないときの `RC_SESSION` fail-closed を残す。
- pin fast path の構造と `_verify_rollout_sha` の必須性を変えない。

## A4. 実測の差し替え (probe の束縛)

両レンズの指摘どおり、親が段 1 で使った probe は
(i) 正規化済み cache を読み、(ii) `cand_E` が確定判定式と異なり、(iii) 例外境界が production と違う。
**段 1 の probe 結果は仮説であり、裁定の確定根拠にしない。**

確定は段 6 で次のとおり行う。

- 実装後の repo から `tools/codex_reasoning_ab.py` を **import して production の
  `_rollout_matches_session` / `_find_rollout` を直接呼ぶ** probe を親が書く (repo 外、[T-317] 裁定)。
- 実 corpus `~/.codex/sessions` を直接走査し、cache を使わない。
- 記録する: 全 id の解決件数ヒストグラム、件数 1 でない id の全列挙、
  読取・parse 例外の発生 file と種別、symlink 件数、重複 inode 件数、corpus の file 数と digest、
  取得時刻 (JST)、pin 付き 5 label の解決先。
- 判定: 全 id で件数 1、かつ実装前述語が解決できた id では返り path が一致すること。
  一致しない id があれば `DW-STOP`。

## A5. 非 str `id` の締め (確定)

`own(r)` は次のとおり。プラン v1 の `isinstance(payload_id, str) else fallback` から締める。

- `id` key が**存在しない** → `session_id` へ fallback する (既存 `session-id-only` /
  `reordered-keys` variant を維持するため)。
- `id` が**非空 str** → それを own とする。
- `id` が**存在するが非空 str でない** (null / 数値 / bool / 空文字) → **その行は同一性を与えない**。

実 corpus で `id` を欠く行・非 str の行はいずれも 0 件なので、この締めは実データに対して no-op。
レンズ A は key 欠落 fallback も落とせと推奨したが、既存 2 variant の期待反転を伴い
裁定 #41 の射程を超えるため**採らない**。この差はレンズ推奨からの意図的な逸脱として記録する。

## A6. 改名 (P4) — 採用

`_rollout_matches_session` と `_find_rollout` の第 2 引数を `target_session_id` へ改名する。

- **根拠は D75 ではなく本 wave の根本原因**である。バグは「引数の `session_id` (探している識別子) と
  payload の `session_id` (所属 root session)」という同名別義が述語の中で衝突したことに起因する。
  名前を分けなければ同じ誤りが再発する。
- 影響ゼロの実測: プランが全呼出元を列挙し (production 3、テスト 31)、すべて positional で
  `session_id=` keyword caller は repo 内に無い。`:3070` / `:3093` の payload 側 `session_id` は改名しない。
- レンズ B は「別 cleanup へ延期」を推奨したが、**根本原因の一部なので本 wave で閉じる**。

## A7. 記録上の是正 (実装ではなく書き方)

- `distinct-fields` variant の期待反転は「Codex の subagent 行が root 参照を持つ形であり、
  親検索で子 file を返すのは誤仕様固定である」として記録する。単なる OR 条件の破壊として書かない。
- 実 corpus の fork 4 file は**回帰 fixture の由来**として記録し、
  「fork は必ず親行コピーを持つ」という普遍規則としては記録しない。
  観測 3 file が同一親由来の兄弟であることも明記する。
- [T-886] は「現行 pin で実測一致した SHA 認可付きの限定 fast path」と記録し、
  「全走査と普遍的に同値」とは書かない (既存テスト `:2366` が反例を固定している)。

## B1. 実害の精密化 (親の独立実測)

レンズ B は「消費側 `:3090` の `len(meta)!=1` が残るので実害は消えない」とした。
**親が実測して半分だけ正しいと裁定する。**

- `019fd52d…` (thread_spawn の親、子 3 file) — 親 file の `session_meta` は **1 行**。
  修正後は `_find_rollout` が親を返し、消費側 `:3090` も通る。**実害は完全に消える。**
  T-936 が述べた実害 (「codex 子が subagent を産むと正当な作業を拒否しうる」) はこの型である。
- `019f690c…` (vscode の圧縮由来、meta 4 行) — 修正後も `:3090` で
  `session_meta count is 4, expected 1` により拒否される。これは subagent とは別の欠陥であり、
  **scope 外** → 裁定パッケージ R1。

## 2. 実装 scope (確定)

**production** — `tools/codex_reasoning_ab.py`

1. `_rollout_matches_session` を A2 + A5 の判定式へ書き換える。
2. `_rollout_matches_session` / `_find_rollout` の第 2 引数を `target_session_id` へ改名 (A6)。
3. これ以外の production 変更をしない。`_session_meta_rows`、fast path、全走査、件数検査、
   `_verify_rollout_sha`、消費側 `:3067-3125` は 1 byte も変えない。

**テスト** — `orchestrator/tests/test_codex_reasoning_ab.py`

4. `test_find_rollout_session_meta_encoding_and_payload_field_equivalence` を
   `..._payload_identity_semantics` へ改名し、`distinct-fields` variant の期待を
   `RC_SESSION` / `rollout count is 0, expected 1` へ反転する。他 9 variant は不変。
5. 型 A (取り違え): 親 P/P + 子 C/P。親検索が親を返し、子検索が子を返す。
6. 型 B (親行コピー): 親 P/P + 子 [C/P, P/P] (**正順のみ**)。親検索が親を返し、子検索が子を返す。
6b. **型 B 逆順の負例** (下記 erratum E1): 親 P/P + 子 [P/P, C/P]。
   子の先頭行が P を名乗るので veto は発火せず、候補 2 件で
   `RC_SESSION` / `rollout count is 2, expected 1` になることを固定する。
   実 corpus の fork は先頭行が自分を名乗るのでこの形は観測されていない。
   **これは A2 の順序感受性そのものを仕様として明示する負例である。**
7. **片側 veto の負例** (レンズ A 所見 2): 同一 P/P の file 2 本のうち片方に C/P を**追記**し、
   `RC_SESSION` / `rollout count is 2, expected 1` のままであることを固定する。
   先頭行が P を名乗るので veto は発火しない。
   6b とは fixture が異なる (6b は fork marker を持つ子、7 は追記された同一 bytes の複製)。
8. **非 str `id` の負例**: `{"id":null,...}` / `{"id":0,...}` / `{"id":"",...}` の各行が
   同一性を与えず、`session_id` へ落ちないこと (`rollout count is 0`)。
9. **真の重複の負例**: P/P を持つ file 2 本で `rollout count is 2` のまま。
10. **pin 経路の型 A/B fixture** (レンズ B 所見 2): pin 付き呼出しで
    子 file が親 label の candidate になっても新判定式が拒否し、全走査へ落ちること。
    `_verify_rollout_sha` が成功するまで返さないことも固定する。

**これ以外を実装しない。** 既存テストの期待は 4 番の 1 variant を除いて変更しない。

## 3. 変異事前登録 (`DW-M01`)

位置はすべて `tools/codex_reasoning_ab.py` の `_rollout_matches_session` 内。
期待 killer node の**完全集合**は、実装 commit 確定後に `--junitxml` の権威一覧から再導出する
(`DW-M08`、既存 memory「期待 node は fix 後に完全集合を再導出」)。
ここでは**位置・単一理由性・期待する最初の killer**を凍結する。

| ID | 変異 | 単一理由性 | 期待する最初の killer | 種別 |
|---|---|---|---|---|
| M1 | wave 前の形へ復帰 (`id == X or session_id == X` で即 return) | 前後に同入力を拒否する層なし | 反転した `..._payload_identity_semantics` の `distinct-fields` | 純増 (期待反転が先殺し) |
| M2 | `declares_X` の項を落とす (veto 無効化) | 同上 | 型 B (正順) | 純増 |
| M3 | `first_owns_X` の disjunct を落とす (= プラン v1 の形) | 同上 | 片側 veto の負例 (scope 7) | 純増 |
| M4 | `own(r) == X` で即 `return True` (行順依存) | 同上 | 型 B (正順) | 純増 |
| M5 | 非空 str 検査を外し全非 str を `session_id` へ fallback | 同上 | 非 str `id` の負例 (scope 8) | 純増 |
| M6 | key 欠落時の fallback を削除 | 同上 | 既存 `session-id-only` / `reordered-keys` | **共有** (既存が先殺し) |
| M7 | 件数検査を `!= 1` から `< 1` へ | `_find_rollout` 側 | 既存 `..._preserves_zero_and_duplicate_failure` | **共有** |
| M8 | **正例 (過剰拒否検出)**: `owns_X` を常に偽にする | 同上 | 既存 `_find_rollout` 群の大半 | **正例** |

- `DW-M01` の「受理集合を縮小する wave では承認外の過剰拒否を検出する正例も登録する」を M8 が担う。
- M6 / M7 は既存テストが先に殺すので **shared と記録し、新テストの純増検出力には数えない**
  (レンズ A 所見 8 の指摘に従う)。
- 型 B fixture の `source` / `forked_from_id` はコードが読まないため、それらを消す変異は
  観測不能である。**登録しない** (レンズ A 所見 8 の最終項)。fixture には実 corpus 由来の
  現実性のために残すが、検出力の根拠にしない。
- 本走は `--runner-mode dispatch`、runner argv へ `--force-dispatch` を入れる (`DW-M07`)。

## 4. 裁定パッケージ (scope 外・ユーザーへ返す)

いずれも本 wave では触らない。

- **R1** — 消費側 `tools/codex_reasoning_ab.py:3090` は `len(meta) != 1` を拒否理由にする。
  compaction / resume で `session_meta` が複数行になる親 rollout (実在: `019f690c…`、4 行、
  vscode) は、`_find_rollout` が直っても拒否され続ける。
  選択肢 = (a) fail-closed のまま維持、(b) 完全一致する重複行だけ 1 行として扱う、
  (c) 先頭行を権威とする。**受理集合を広げる方向なので独立の敵対検証を受入条件にすべき。**
- **R2** — `_session_meta_rows` は decode 失敗・`OSError` を silent skip する。
  読めなかった file は「一致しない」として扱われ、不確実性が失われる
  (`MATCH / NO_MATCH / INDETERMINATE` の 3 値でない)。既存テスト `:2049` と `:2170` が
  この fail-open を仕様として固定しているため、閉じるには 2 本の期待反転が要る。
- **R3** — pin fast path (`:323`) が `_verify_rollout_sha` の失敗を握り潰し、
  その後の全走査が同じ file を SHA 未検証で返しうる。既定の production caller は後段で
  再検証するが、`verify_source_sha=False` 系の seam では防壁がない。[T-886] の範囲。
- **R4** — [T-937] (`_scan_session_rows` の全行 parse) は本 wave で触らない。

## 4b. erratum E1 — 段 5 実装子が検出した裁定内の矛盾 (2026-08-16 09:19 JST)

段 5 第 1 走の実装子は**何も実装せず fail-closed で停止し、裁定の矛盾を報告した。正しい挙動である。**

- **矛盾:** 旧 scope 6 は型 B の**逆順** variant (子 = `[P/P, C/P]`) にも
  「親検索が親を返す」を要求していた。しかし A2 の `first_owns_X` により、
  この子 file は先頭行が P を名乗るため veto が発火せず候補に残る。
  親と合わせて 2 件になり `RC_SESSION` が正しい。旧 scope 7 は実質同形について
  `RC_SESSION` を要求しており、両立しない。
- **原因:** 逆順 variant はプラン v1 の**順序非依存** veto を前提に置かれた期待値である。
  親が A2 で `first_owns_X` を足した際、この期待値を再導出しなかった。
- **処置:** **A2 の判定式は凍結どおり変更しない** (`DW-O12`)。矛盾していたのはテストの期待値の側なので、
  逆順 variant を scope 6 から分離し、`RC_SESSION` を期待する負例 6b とする。
- **意味:** A2 は意図的に**行順に感受性がある**。「先頭 session_meta 行が file の自己同一性を決める」
  という codex の書き出し規約に依拠しており、実 corpus の fork 3 file すべてでこれが成立している。
  規約が破れた file は解決されず fail-closed になる — 安全側である。この性質を 6b が仕様として固定する。
- 変異 M3 (`first_owns_X` を落とす = プラン v1 の形) は 6b と scope 7 の両方が殺す。
  M4 (先頭一致で即 return) は正順型 B が殺す。事前登録表は変更しない。

## 4c. erratum E2 — 段 6 敵対レビューが見つけた凍結式の欠陥 (2026-08-16 09:52 JST)

段 6 レビュー A / B とも **NO-GO**。A2 の凍結式そのものに反例が残っていた。**判定式を再裁定する。**

### E2-1 — 同一性が確定できない行が veto を立てて別候補を昇格させる (real, must-fix)

レビュー A 所見 1 の再現:

```
rollout-0: [ {"id": null, "session_id":"P"}, {"id":"P","session_id":"P"} ]
rollout-1: [ {"id":"P","session_id":"P"} ]
```

A2 + A5 では `own(row0)` が「同一性を与えない」= `None` になるため
`first_owns_P` が偽、`declares_P` が真 (None != P かつ session_id == P) となり
rollout-0 が veto され、**rollout-1 が一意に昇格する**。現行実装は 2 件で拒否していた。
先頭 payload が dict でない場合も `index == 0` を満たす行が飛ばされて同じ形になる。

これは段 3 レンズ A 所見 2 と**同型の穴**であり、`first_owns_X` の追加で閉じたはずのものが
「同一性を確定できない行」の経路で再び開いていた。

### E2-2 — 修正 (A2 を上書きする確定形)

```
own(r) = payload["id"]         ("id" が非空 str)
       = payload["session_id"] ("id" key が存在しない)
       = 未確定                 (それ以外: null / 数値 / bool / 空文字 / payload が dict でない)

determinable(F) = own(r) が未確定でない meta 行の列 (元の行順を保つ)

owns_X       = ∃r ∈ determinable(F): own(r) == X
first_owns_X = determinable(F) が空でなく own(determinable(F)[0]) == X
declares_X   = ∃r ∈ determinable(F): own(r) != X かつ r.payload["session_id"] == X

F が X を名乗る ⇔ owns_X ∧ (first_owns_X ∨ ¬declares_X)
```

A2 からの変更は 2 点だけである。

1. **`first_owns_X` は raw index 0 ではなく「同一性を確定できた最初の行」で評価する。**
2. **同一性が未確定の行は `declares_X` に寄与しない。**

いずれも veto の発火条件を**狭める**方向であり、候補集合は A2 実装より大きくなりうる。
大きくなる先は「曖昧なので `RC_SESSION`」であり、fail-closed 側である。

反例の再検査: rollout-0 の determinable 先頭は 2 行目 (P/P) なので `first_owns_P` が真、
veto は発火せず候補 2 件 → `RC_SESSION`。**現行と同じ拒否に戻る。**
レビュー A が挙げた `[非 dict, P/P, C/P]` と `[C/C, P/P, {"id":null,"session_id":"P"}]` も同様に閉じる。

実 corpus では `id` を欠く行・非 str の行・payload 非 dict の行がいずれも 0 件なので、
この修正は**実データに対して no-op** である (段 6 の A4 再測定で確定する)。

### E2-3 — 追加するテスト (レビュー A 所見 4 の登録漏れ)

- `id` が `false` (bool) の行 — A5 が禁じているが既存 fixture が null / 0 / 空文字だけだった。
- **先頭 payload が dict でない** file の型 A / 型 B。
- `own` が立った**後**に現れる子孫宣言 (`[C/C, P/P, C/P]` 型) で veto が正しく発火すること。
- **ineligible pin** (`pinned_label` 指定だが `eligible=False`) の型 A / 型 B。
  レビュー A が「既定経路だけ新述語、ineligible pin の全走査だけ旧 OR 述語」という
  条件付き配線を新テストが通り抜けると指摘したため。
- E2-1 の反例そのもの (rollout-0 / rollout-1) の回帰。

### E2-4 — 変異事前登録の是正 (レビュー A 所見 2)

- **M3 の最初の killer は「片側 veto の負例」ではなく「型 B 逆順」である** (収集順)。
  完全集合には両方を登録する。
- **M8 は具体的 node が未登録**だった。runner argv を確定し、
  実測 (`--junitxml`) から完全集合を導出してから本走する (`DW-M08`)。
- レビュー A 所見 3: 型 B 逆順 / 片側 veto / 真の重複の 3 本は **wave 前実装でも通る**。
  保存回帰および M3 の killer として記録し、「wave 前実装を倒す新規テスト」には数えない。

### E2-5 — A4 実測の差し替え (レビュー B 所見 1)

初回 A4 (`a4-corpus-measurement.json`) は erratum として保存し、**land 根拠にしない**。理由は
(i) `_session_meta_rows` を memo 化し候補を絞ったため production の全走査経路を通っていない、
(ii) `_session_meta_rows` が読取・parse 失敗を内部で捨てるので「例外 0」が異常の不在を意味しない、
(iii) 旧述語との返り path 完全一致を測っていない、
(iv) 09:42 と 09:43 の 2 走で corpus digest が変わっており live corpus が安定していない。

**再測定の要件** (段 6 で親が実施する):

- 走査対象 file 集合を開始時に固定し、開始・終了で内容 digest を取って**安定性を実測**する。
  走行中に増減した file を列挙する。
- **raw bytes を独立に走査**し、session_meta に見える行の parse 失敗、file の open 失敗を
  `_session_meta_rows` を通さずに数える。
- **旧述語 (wave 前の形) と新述語の解決集合を全 id で比較**し、差分 id を全列挙する。
- 差分 id と pin 5 label と T-936 の 2 id については、**memo も絞り込みも使わず
  production の `_find_rollout` を直接呼ぶ**。
- 全 id への `_find_rollout` 直接呼出しは O(id 数 × file 数) の file I/O となり実行不能である
  (単走 225 秒 × 3,646 id)。**この不可能性を明記し**、上記の差分駆動 + 抽出検証で代替する。
  抽出は無作為 30 id 以上とし、絞り込みなしの全 file 評価と一致することを確認する。
- fork / subagent file を producer・親 ID・meta 行順・lineage 深さで分類する (レビュー B 所見 6)。

### E2-6 — 記録の是正 (レビュー B 所見 2・3・5)

- 「実害が完全に消えた」とは書かない。**「観測済みの thread_spawn 型では T-936 由来の
  rollout 解決・meta 件数・identity の拒否が消える」**と限定して書く。
  compaction / resume 型 (`019f690c…`) は R1 として残る。
- commit `2e2cb838` の message にある「テスト caller 31」は**改名前の値**である。
  commit 後の tree では 43 である。段 7 の記録で是正する (commit message は書き換えない)。
- R3 (pin fast path の SHA 失敗後 fallback) は既存欠陥として scope 外に維持し、
  「今回直した」とは記録しない。

## 5. 段 5 の分割

実装単位は 1 本 (単一 file の単一述語 + 同 file 内のテスト)。所有は
`tools/codex_reasoning_ab.py` と `orchestrator/tests/test_codex_reasoning_ab.py` の 2 file で素集合。
並列化しない。
