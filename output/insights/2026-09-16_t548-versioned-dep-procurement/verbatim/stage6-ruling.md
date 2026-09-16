# 段 6 裁定 — レビュー A (正しさ境界) / B (実効性と整合) の所見

親 (claude) が段 6 の敵対レビュー 2 本を裁定した。**本文書が fix の正本である。**
対象 HEAD = merge commit `99c9b9222` (実装 `0165027e0` + local main `e667c8c13`)。

親は must-fix 候補をすべて現物で検算してから裁定した (file:line は本文に記す)。

---

## 0. 結論

**must-fix は 4 件。** B1 (silo)・B2 (T-126 submit)・B3 (mocc、B の should-fix から格上げ)・P-1 (親の持ち越し)。
**A-1 は must-fix にしない** (§2)。変異は M2・M7 を取り下げ、M1・M3 を再照準し、fix 用に 4 件を新規登録する (§4)。

---

## 1. must-fix (real・採用)

### B1 — silo の job と submit が gflags / glog を運ばない

- **job:** `tools/pegasus/silo_ladder_rung1.sh:348-383` は `third_party_policy()` の **3 本だけ**を
  `$RUNTIME/thirdparty-src` から `$TMPDIR/thirdparty-src` へコピーし、`:383` で
  `export IZANAGI_THIRDPARTY_SOURCE_ROOT="$THIRD_PARTY_SCRATCH"` と上書きする。
  wave が入れた `:443` の解決はこの env を優先するので、**存在しない `scratch/gflags`** を読み、
  `:466` の `git -C "$dep_source"` で止まる。
- **submit:** `tools/pegasus/submit_silo_ladder_rung1.sh:150-178` は `fetch_third_party.py` を使わず、
  **自前で 3 本だけ**を clone して `[[ ${#third_party_rows[@]} -eq 3 ]]` を assert する。
  永続 root にも gflags / glog は入らない。
- **成果物影響:** 正常な調達入力でも silo rung1 の新規走行が dependency stage で必ず失敗し、
  成功 evidence を追加できない。
- **本 wave が持ち込んだ回帰である。** 変更前は policy の絶対 path を読んでいたので scratch 上書きに影響されなかった。

### B2 — T-126 の submit helper が一時展開先を repo root と誤認する

- `tools/pegasus/submit_t126_qualification.sh:142-145` は `orchestrator` と `policy.json` だけを
  一時 directory へ archive 展開し、そこから helper を実行する (`:368`、`--repo-root "$REPO_ROOT"` は渡す)。
- 単位 C が入れた `orchestrator/qualification/submission.py:163-164` は、env が無ければ
  **`Path(__file__).resolve().parents[2]`** (= 一時展開先) を root にする。渡された `repo_root` を使わない。
- **成果物影響:** 標準 submit が series identity / toolchain manifest の生成前に失敗し、
  新規 qualification 試行と certified 候補を追加できない。
- **本 wave (単位 C) が持ち込んだ回帰である。**

### B3 — mocc の自己 hydrate が gflags 参照より後にある (should-fix → **must-fix へ格上げ**)

- mocc は submit で cache だけを要求し (`tools/pegasus/submit_mocc_trace.sh:361-366`)、
  job が計算ノード上で自分で hydrate する設計である (`tools/pegasus/mocc_trace_pilot.sh:1636`、
  `$TMPDIR/thirdparty-src` へ)。
- wave が入れた解決 (`:893`) は env か checkout 既定の staging を見て、`:1531` で gflags を要求する。
  **どちらも自己 hydrate より前で、mocc の流れが一度も埋めない場所**である。
- **成果物影響:** 5 本入りの cache だけを用意した投入は依存段で停止し、mocc の新規材料を生成できない。
  成果物影響を具体的に書けるので `DW-G05` により must-fix とする。
- **本 wave が持ち込んだ回帰である。**

### P-1 — `_resolve_cache_root` の fail-closed の検査が乗り物ごと消えた (親の持ち越し)

- 単位 A が消した `test_cache_root_must_be_explicit_or_environment` は `verify-deps` を
  **乗り物に使っていただけ**で、生き残る `_resolve_cache_root` の挙動
  (「`--cache-root` か `IZANAGI_PEGASUS_THIRDPARTY_CACHE` のどちらかが必須」「無ければ rc=2・
  stderr 1 行・env 名を含む」「env で与えれば rc=0 でその root を使う」) を検査していた。
- **成果物影響:** cache root の fail-closed が無検査になり、誤った cache から pin されていない
  source を build して certified evidence へ混ぜる退行を検出できない。
- レビュー A も同じ判定 (§3、「生き残る挙動。既知 P-1」)。

### 他の job body に同じ型は無い (親の実測)

全 15 本で「解決行・env 上書き・自己 hydrate」の行順を機械的に洗った。
env 上書きは silo (`:383`) だけ、自己 hydrate は mocc (`:1636`) だけである。
certify は submit が checkout 既定の staging の存在を fail-closed で要求し (`submit_certify.sh:52-56`)、
floor は env を渡さず checkout 既定を使う。いずれも「submit 前に checkout へ hydrate」の前提と整合する。

---

## 2. must-fix にしないもの

### A-1 (レビュー A の must-fix) — 引渡し境界での `_verify_source` 相当の検証 → **不採用 (scope 外)**

**所見の事実は正しい。** job 側の使用直前検査は HEAD 一致と porcelain だけで、hydrate 後に
`assume-unchanged` を立てて tracked source を改変すると検出しない。

**しかし must-fix にしない。理由は 4 つ。**

1. **本 wave による弱体化ではない。** レビュー A 自身が §1 で全 15 本について「変更前の検査を
   消していない」と結論している。変更前も job は絶対 path の clone に対して同じ HEAD + porcelain
   だけを見ており、同じ改変を同じように見逃していた。
2. **段 4 の R5 は親の過剰採用だった。** R5 の出所の sol A1 は、原文で
   「これは現行 floor の最低線より弱くなると確認できた回帰ではありません」と書いていた。
   親はそれを scope 判定せずに採った。**本裁定で R5 を訂正する** (§5)。
3. **仮想リスクへの検査新設にあたる。** 通常の調達・投入の流れで hydrate 済み tree に
   `assume-unchanged` を立てる経路は無い。ユーザーは本依頼で「仮想リスク向けの一般化・互換層の
   追加は scope 外」と明示し、D1736 は名指し外の gate・検査を足さないと決めている。
   `DW-G05` も「要求外の仮想リスクで gate・検査を足さない」と定める。
4. **規律 2 には触れない。** 規律 2 が禁じるのは正しさゲートを**緩める**ことである。
   既存の検査は 1 つも緩めていない (レビュー A §1、15 本すべて「維持」)。

**やらない理由の最も強い反論 (記録):** 「新経路は hydrate で強い検査を掛けるのに、使う直前には
弱い検査しか掛けない。強い検査の結果を job が使う時点まで保証されたものとして扱うのは、
正しさシグナルを実態より強く見せる」。
**これを退ける根拠:** 本 wave は「hydrate 時の検査が job 使用時まで保証される」とは
どこにも主張しない。insight と worklog にこの限界を**明示的に書く** (段 7)。
名乗りを実装に合わせる。

### レビュー A の P-2 候補 (metadata 4 case の削除) → **refuted**

レビュー A 自身が「代替なく検出力が消えたという攻撃は不成立」と判定している。
dangerous config / commondir / sparse / index bit の拒否は
`test_pegasus_thirdparty_fetch.py:566`, `:642`, `:684` に残る。

### レビュー B §7 — 手順書の残存 → **親が段 7 で直す (docs のみ)**

- `docs/pegasus-runbook.md:330` (gflags / glog は helper 管理外・旧 `*_source_path` が正本) — 直す
- `docs/pegasus-runbook.md:797` (build 元を旧 locator で案内) — 直す
- `docs/pegasus-runbook.md:679` (測定表の `verify-deps`) — 歴史記録なので触らない
- `docs/decisions.md` / archive の旧名 — 過去の決定・観測記録なので触らない

### レビュー B §8 — F88 に該当する既存の import → **scope 外 (本 wave 由来ではない)**

`certify_calibration.sh:227-235`、`mocc_trace_pilot.sh:1496-1507`、`t141_region_profile.sh:1104-1112` 等は
**変更前から**既定 `python3` で orchestrator を import している。本 wave は増やしていない
(レビュー B も「今回の差分による新規導入ではありません」)。調達経路の本題でもない。
段 7 の「次の一手」に既知の限界として記録するだけにする。

---

## 3. fix の単位と所有 (DW-S06-B)

テストの参照を**名前で引いて**所有を確定した。silo と mocc は `test_pegasus_tools.py` を共有し、
mocc と調達テストは `test_mocc_trace_job_contract.py` を共有するので、**1 単位にまとめる**。
T-126 は独立。

### 単位 F1「Pegasus shell 側」 — B1・B3・P-1・変異 M1 の再照準

- `tools/pegasus/submit_silo_ladder_rung1.sh`
- `tools/pegasus/silo_ladder_rung1.sh`
- `tools/pegasus/mocc_trace_pilot.sh`
- `orchestrator/tests/test_pegasus_tools.py`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py`
- `orchestrator/tests/test_p3_s4_loop.py`
- `orchestrator/tests/test_mocc_trace_job_contract.py`
- `orchestrator/tests/test_pegasus_thirdparty_fetch.py`
- `orchestrator/tests/test_hooks.py` — **必要が生じた場合だけ**。触ったら理由を報告
- **期待赤:** `orchestrator/tests/test_silo_ladder_rung1_evidence.py` —
  `pbs_job` と `submitter` の sha256 pin。**F1 は触らない。親が差分を読んで値を与え、別投入で直す** (D200)。

### 単位 F2「T-126 Python 側」 — B2

- `orchestrator/qualification/submission.py`
- `orchestrator/tests/test_t126_pegasus_tools.py`
- `orchestrator/tests/test_official_perf_closure.py` — **必要が生じた場合だけ**

---

## 4. 変異の再登録 (DW-M01、fix 前)

### 取り下げ

- **M2** (新列挙の pin を `fullmatch` → `search`) — **取り下げ。** 直後の `_dependency_pins()`
  (`silo_ladder_rung1.py:859`, `:862-863`) が pin 形式と上位 pin との一致を先に/別に拒否するので、
  単一理由にならない。新列挙の pin 形式検査は**冗長 gate**であり、単独変異の証拠に数えない (DW-M03)。
- **M7** (使用直前検証の除去) — **取り下げ。** §2 で R5 を訂正したので、対象の gate は存在しない。

### 再照準

- **M1** (新列挙の `.git` 終端要求を外す) — 現行テストは policy の URL だけを変えて `verify` を
  走らせるため、`fetch_third_party.py:440` の origin 不一致も同じ入力を拒否し、単一理由にならない。
  → **`_build_dependency_sources()` を直接呼ぶ単体テスト**で、`.git` 終端を欠く URL が
  `OperationalError` になることを検査する node を F1 が足す。期待 node はその node。
- **M3** (`allow_shallow=True`) — 呼出し位置を **`_verify_cache` の `fetch_third_party.py:546`** に確定し、
  `verify` 命令経路の shallow 拒否 node を期待 node にする。`_fetch` の `:564` / `:577` は二重検査のため対象外。

### 維持

- **M4** (gflags を列挙から落とす)、**M5** (p3_s4 の解決を固定 path へ)、**M6** (現行 golden を旧値へ)。

### 新規 (fix で入る検査に対して)

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M8 | `fetch_third_party.py` の `_resolve_cache_root` | `IZANAGI_PEGASUS_THIRDPARTY_CACHE` を読まない (env を無視) | KILLED — P-1 の復元 node の「env で与えれば rc=0」側 |
| M9 | `submission.py` の依存解決 | 渡された `repo_root` でなく `Path(__file__).parents[2]` を root にする (B2 の回帰を戻す) | KILLED — F2 が足す「helper を一時展開先から実行しても checkout の staging を読む」node |
| M10 | `silo_ladder_rung1.sh` | gflags / glog の解決元を scratch 上書き後の env へ戻す (B1 の回帰を戻す) | KILLED — F1 の silo 契約 node |
| M11 | `mocc_trace_pilot.sh` | 自己 hydrate を gflags 段より後ろへ戻す (B3 の回帰を戻す) | KILLED — F1 の mocc 契約 node |

**M8〜M11 の期待 node の nodeid は fix 完了後に確定する** (fix 前には存在しない node なので)。
`DW-M07` に従い、fix 後の最終 commit で anchor と期待 node を再検証してから本走する。
単一理由性も fix 後の現物で確認し、成立しなければ取り下げて erratum に残す。

---

## 5. 段 4 裁定の訂正 (erratum)

- **R5 を訂正する。** 「新 2 依存の引渡し境界で `_verify_source` 相当を適用する」は、
  回帰ではない仮想リスクへの検査新設であり、ユーザー明示の scope 外・D1736・`DW-G05` に反する。
  親が段 4 で scope 判定をせずに採用した誤りである。**本 wave では実装しない。**
  限界として insight と worklog に明記する。
- **R9 の一部を訂正する。** 「job 側の変異は正常 hydrate 後の引渡し境界へ投入する」は R5 を
  前提にしていたので、M7 と合わせて取り下げる。

---

## 6. 不変条件 (fix 子へ継承)

- **規律 2 を緩めない。** HEAD 完全一致・dirty 拒否・不在の fail-closed・origin 照合・非 shallow を
  1 つも弱めない。
- **既存テストの期待値を反転・緩和・skip・削除しない。** 既存の test 関数を消さない。
- **fallback・互換層・旧 locator へ戻る分岐・新しい env 変数を足さない。**
- **仮想リスク向けの gate・検査を足さない。** (A-1 の検証層を足してはならない。)
- **`tools/pegasus/` 配下に新しい file を作らない** (F660)。
- **job body の inline python から orchestrator を import しない** (F88)。既存の import には触らない。
- **FetchContent の 3 本集合 (`THIRD_PARTY_NAMES`・`third_party_policy()`) を 5 本へ広げない。**
  gflags / glog は別の列挙のまま運ぶ。
- **凍結 evidence・歴史定数・`output/` 配下を書き換えない。** sha256 pin の値は親が与える。
