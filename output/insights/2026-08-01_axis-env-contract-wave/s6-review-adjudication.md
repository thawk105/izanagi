# 段 6 レビュー裁定 (fix 1 の指示)

入力は段 6 レビュー C (`s6-fidelity/output.md`、裁定忠実性・正しさ防壁) と
レビュー D (`s6-teeth/output.md`、テストの歯・変異帰属・回帰)。**両者 NO-GO**。
両者とも指定 SHA-256 の一致を確認し、追跡差分が所有 2 ファイルだけであることを独立に確認した。

受入 1 回目は計算ノード request `876263.nqsv` で 6 ファイル **409 passed / 9 skipped**、rc=0。
**緑は検出力の証拠ではない**という前提で以下を裁定する。

fix は単一 Codex 単位とする。理由: 全所見が同じ 2 ファイル (大半はテストファイル) に集中し、
所有を素集合に割れないため (`DW-S06-B`)。

## 1. real / must-fix (fix 1 で閉じる)

### R1 [BLOCKER] 実 selector 条件付き復帰が全テストを生存する (D 固有。C も親も未検出)

`clocks_per_us=(L.CLK if contract.env_tag == ENV_TAG else contract.clocks_per_us)` の形の変異は、
sentinel が `env_tag="sentinel-env"` なので else 側に入って緑になり、
literal scan も `L.CLK` 参照のため `1800` を見つけられない。
**親が裏取り済み**: `T.L.CLK = 1800` / `T.L.NUMA = ['numactl','--interleave=all']` は
driver から literal 無しで到達可能 (`p3_s4_loop.py` は本 wave の scope 外で未変更)。
*成果物影響*: contract 再校正後も stale な launch 条件が WAL と材料レポートの `run_cmd` に残り、
無効な計測から certified 選択されうる。
*修正*: **same-selector sentinel** を追加する。`env_tag` は `T.ENV_TAG` と同値、
`clocks_per_us` と `numactl` だけ registry と異なる contract を流し、実引数を照合する。

### R2 [BLOCKER] `ENV_TAG` selector 自体が固定されていない (C1 = D2)

`ENV_TAG = "pegasus"` へ変異しても受入集合 6 ファイルを丸ごと生存する。
**親が裏取り済み**: 受入テストに literal `"linux-baremetal"` は 0 件。
`test_p3_s4_loop.py` も `TRIGGER_LOOP.ENV_TAG` を値として通すだけ。`pegasus` は registry 登録済み。
*成果物影響*: `OTHER` site で Pegasus contract の 2100 と空 numactl を attestation なしに使い、
WAL と材料レポートを `pegasus` として生成する。terminal abort の誤タグ化で certified 選択集合が変わる。
*修正*: `assert T.ENV_TAG == "linux-baremetal"` を追加する。selector は解決値ではないので
literal 固定が正しい。

### R3 [BLOCKER] reject 負例が 3 branch のうち syntax しか通らない (D3)

`_reject_case` は `_FORBIDDEN_IMPL` 固定なので syntax branch だけ。
diff-quarantine branch と auditor branch の callsite だけ helper を迂回する変異は生存する。
*成果物影響*: hole-escape / auditor reject が Pegasus 上で偽タグ WAL 2 行を生成し材料レポートを汚染する。
*修正*: reject 負例を diff-quarantine / syntax / auditor の 3 入力で parameterize し、
各々で `ExecutionGuardError` かつ WAL 0 行を固定する。

### R4 [HIGH] reject helper の contract provenance と lookup 失敗が無歯 (C2 = D4)

admission を残したまま `env_tag=ENV_TAG` へ戻す変異、および reject helper 内だけで
`EnvContractError` を握り潰して fallback する変異が、どちらも生存する。
*成果物影響*: contract 解決失敗時や tag 正規化後に reject WAL だけが stale selector を記録し、
台帳と材料レポートの環境帰属が分裂する。
*修正*: `_reject_case` に `_lookup` 注入を通し、(a) distinct sentinel tag が WAL 2 行へ流れる正例、
(b) lookup 例外時に同一例外が伝播し WAL 0 行、の両方を固定する。

### R5 [HIGH] M7 の帰属が偽 (D5)

M7 (`_admit_env_contract()` → `_lookup(ENV_TAG)`) は、fixture の `_lookup` が `pytest.fail` を投げるため
campaign 到達前に赤くなる。これは「measurement guard が効いた」kill ではない。
*成果物影響*: 変異台帳が measurement guard を検証済みと誤記し、Pegasus 計測の fail-open を見逃す。
*修正*: measurement 負例の `_lookup` は正常な sentinel contract を返させ、
guard 削除時に campaign spy へ到達して「期待した `ExecutionGuardError` が無い」の一理由で赤くする。

### R6 [HIGH] M8 は挙動でなく関数 identity を見ている (D6)

*成果物影響*: M8 を behavior kill と記録すると、既定経路が Pegasus を拒否することを台帳が証明しない。
*修正*: identity assert は diagnostic sensitivity pin として残し (`DW-M08`)、
別に「既定 seam のまま `site_policy.current_site` が Pegasus を返す状況で admission が拒否する」
挙動テストを足す (`site_policy.current_site` 側を sentinel 化する)。

### R7 [MEDIUM] admission 非到達の既存 2 テストまで `OTHER` 固定している (D7)

clean pass と digest mismatch は admission に到達しないので宣言不要。
`OTHER` 固定は、admission を `_quarantine_and_audit` 冒頭へ誤移動する回帰を隠す。
*成果物影響*: dry / auditor preflight の受理集合を Pegasus でだけ不必要に縮める回帰を見逃す。
*修正*: この 2 件は `PEGASUS_COMPUTE` を明示し、それでも clean pass / `AuditorGateFailure` が
先行することを固定する。reject 系 5 件と drive 系 2 件の `OTHER` 宣言は元の検査対象を弱めていないため維持する。

### R8 [nit→採用] clean dry-pass の `pytest.fail` は握り潰されうる (D)

`pytest.fail` の例外は `BaseException` 系なので通常の `except Exception` では握り潰せないが、
bare `except` / `BaseException` で握り潰して dry-pass を返す変異は緑になる。
*修正*: `_lookup` 呼出しの副作用カウンタを併用し、「呼ばれていないこと」を正の assert で固定する。

## 2. 親の文言訂正 (親が docs 側で行う。実装子は触らない)

### R9 [HIGH] 「production caller override はない」は過大 (C3)

レビュー C の計数: 関数引数 0 / CLI 0 / 環境変数由来 1 (`PATH` — `pegasus0N` で
`qsub`/`qstat` を隠すと `OTHER` になる) / 明示 module 面 3 (`_current_site`、`_lookup`、可変 `ENV_TAG`)。
同一 process 内のコード書換えまで含めれば有限保証自体が成立しない。
*修正*: 保証を「**関数引数と CLI に supported な override はない**」へ訂正し、
段 4 §5 の保証文言をレビュー C が提示した精密版へ差し替える (下記 §4)。

## 3. nit / backlog (must-fix にしない — `DW-G05`)

- C4: guard 例外時に entry 無しの provenance header と campaign lock が残る。
  env-tag WAL と certified 選択は変わらないため成果物影響を 1 行で書けない。backlog。
- site matrix が未知文字列 site を許す変異を検査しない。現 `current_site` の codomain は 4 定数なので
  直ちに blocker ではない。backlog。
- import-time lookup 不在の専用非回帰 assert がない。成果物影響を書けないため backlog。

## 4. 段 4 §5 の保証文言を差し替える (レビュー C 提示版を採用)

> 未改変の `p3_s4_loop_trigger_gating.run_one_iteration` を通る正規経路では、
> reject WAL の `env_tag` と `run_campaign` の `env_tag` / `clocks_per_us` / `numactl` が
> `_lookup(ENV_TAG)` の返値から供給される。`site_policy.current_site()` が既知 Pegasus 状態を
> 返す場合、それら sink の前で停止する。既存 WAL の env 射影、正の machine attestation、
> 同一 process の module 書換え、兄弟 driver は保証しない。

## 5. 変異事前登録 v2 (erratum を含む)

初回登録 (段 4 §3) の M7 / M8 は**帰属不成立**だった。初回結果は消さず erratum として残す (`DW-M02`)。
M3 の kill 元も親の初回宣言が誤りで、実装子とレビュー D が独立に訂正した (clean dry-pass は
admission 非到達なので kill 元でない。正しい kill 元は site matrix と reject 正例)。

| ID | 変異 | 期待 kill |
|---|---|---|
| M1 | reject helper から admission を外す | reject 負例 (missing exception を主 kill と記録) |
| M2 | `_site_admits_measurement` を allow-all | site matrix + 両 sink 負例 (reject 負例を canonical) |
| M3 | `_site_admits_measurement` を always-false | site matrix + reject 正例 |
| M4 | lookup 結果を無条件破棄し literal 復帰 | sentinel flow |
| M5 | 空 numactl を `["numactl"]` 化 | empty-numactl sentinel |
| M6 | `EnvContractError` を fallback | measurement lookup-error |
| M7-R | measurement admission を `_lookup` へ置換 | **正常 lookup 版**の measurement 負例 (R5 修正後) |
| M8-R | 既定 site を固定 `OTHER` 化 | 挙動版 default-path テスト (R6 修正後) |
| M9 | `ENV_TAG = "pegasus"` | selector exact テスト (R2) |
| M10a | syntax callsite の helper 迂回 | syntax reject 負例 |
| M10b | diff-quarantine callsite の helper 迂回 | diff-quarantine reject 負例 (R3) |
| M10c | auditor callsite の helper 迂回 | auditor reject 負例 (R3) |
| M11 | helper が `contract.env_tag` を捨て `ENV_TAG` を使う | reject sentinel-tag flow (R4) |
| M12 | reject helper だけ lookup error fallback | reject lookup-error (R4) |
| M13 | WAL 書込み後に admission を移動 | reject 負例の WAL 0 assert |
| M14 | 実 selector 時だけ `L.CLK` を使う | same-selector sentinel (R1) |
| M15 | 実 selector 時だけ `L.NUMA` を使う | same-selector sentinel (R1) |

`DW-M08` により、受理集合を変えず構造シグナルだけを pin する変異
(例外の包み直し、seam の同値 wrapper) は kill でなく **diagnostic sensitivity pin** として別枠に記録する。

## 6. 受入集合の追加

`orchestrator/tests/test_real_repo_serialization.py` を受入集合へ追加する
(直列化 collection meta-test が 6 ファイル外にあるため。レビュー D 指摘)。

---

# 段 6 焦点再レビュー 1 の裁定 (fix 2 の指示)

焦点再レビュー (`s6-focused/output.md`) は **NO-GO / BLOCKER 2**。
対応表は **closed 17 / partial 8 / regressed 0**。driver SHA は fix 1 前後で不変
(`ab6af01d...`) であり、production 非変更の報告が正しいことを独立確認した。

## 根本原因 (partial 8 件に共通)

生存変異は「**production 既定 seam で走っているか**」を条件にできる。
sentinel テストはすべて `T._lookup` を差し替えるので、
`... if _lookup is env_contract.lookup else ...` 型の変異は必ず else 側に入って緑になる。
値ベースの sentinel をいくら足してもこの族は閉じない。**構造検査でしか閉じられない。**

## 7. fix 2 の must-fix (テストファイルのみ。production は変更しない)

親は driver の現物で次を実測した。`ENV_TAG` の出現は代入 (`:76`)、
`_admit_env_contract` 内のエラーメッセージ (`:287`)、同関数内の `_lookup(ENV_TAG)` (`:289`) の
3 箇所だけ。`_lookup` の出現は代入 (`:79`) と `:289` の 2 箇所だけ。
したがって次の 3 つの target-local な AST 構造検査で生存族を閉じられる。

### R10 [BLOCKER] selector 宣言の構造 pin

`ENV_TAG` への代入が**単一の `ast.Constant` で値が `"linux-baremetal"`** であることを source AST で固定する。
実行時の値比較 (`T.ENV_TAG == "linux-baremetal"`) は残すが、それだけでは
`os.environ.get("IZANAGI_ENV_TAG", "linux-baremetal")` を殺せない (未設定の受入環境で緑になる)。
*成果物影響*: 環境変数 1 つで WAL と材料レポートが `pegasus` を名乗り、
required attestation を経ない terminal record が certified 選択集合を変える。

### R11 [BLOCKER] 旧定数経路の構造禁止

driver source に `L.CLK` / `L.NUMA` (= 属性名 `CLK` / `NUMA` の `ast.Attribute`) が
現れないことを固定する。`p3_s4_loop` は本 wave の scope 外で `CLK = 1800` /
`NUMA = [...]` を保持しているため、driver からは **literal 無しで**旧値へ到達できる。
条件が何であれ (selector 一致でも既定 seam identity でも) 参照自体を禁じれば族ごと閉じる。
*成果物影響*: 再校正後も stale な clocks / NUMA が WAL と材料レポートの `run_cmd` へ入り、
無効な計測から certified 選択されうる。

### R12 [BLOCKER 派生] selector と resolver の参照範囲 pin

`ENV_TAG` と `_lookup` の参照が、**module-level の代入と `_admit_env_contract` の本体の中だけ**で
あることを source AST で固定する。これにより
`env_tag=(ENV_TAG if _lookup is env_contract.lookup else contract.env_tag)` 型
(焦点再レビューの X4) を構造的に殺す。
*成果物影響*: reject WAL だけが既定経路で stale selector を記録し、台帳と材料レポートの環境帰属が分裂する。

## 8. 構造検査の限界を明記する (過大表現の防止)

R10〜R12 は **source の構造検査**であり、`getattr(L, "C" + "LK")` のような難読化には防壁を主張しない。
これは `env_contract.find_env_literals` の docstring が既に明記している方針
(「偶発 hardcode の防止を狙いとし、故意の難読化には防壁を主張しない」) と同じ立場である。
テストの docstring にこの限界を書くこと。

## 9. C4 の再裁定 (backlog 理由を訂正)

焦点再レビューは「C4 の backlog 理由『レポート影響を書けない』は成立しない」と指摘した。**これは正しい。**
`drive_iteration` は guard より前に provenance header を書き、`layer3_report` はその SHA を
`artifact_refs` に取り込む。したがって影響は次のとおり書ける。

> guard で停止した試行についても provenance header と campaign lock が残り、
> 後で材料レポートを生成すると `artifact_refs` にそのヘッダの SHA が載る。

ただし記録される内容は**虚偽ではない** (entry の無いヘッダが実在するという事実の記録である)。
env_tag 付きの値も certified 選択も変わらない。よって **must-fix にはせず、
影響を明記した既知残余として記録する** (production 変更を伴い scope を広げるため)。
親の初回 backlog 理由は誤りだったので訂正する。

## 10. 変異登録の追補

焦点再レビューが提示した M1〜M15 の具体的 old / new 置換 spec を採用する
(同レビュー総括の表が正本)。X1〜X4 は R10〜R12 の実装後に
**M16 (env-var selector)、M17 (既定 seam 条件の `L.CLK`)、M18 (同 `L.NUMA`)、
M19 (同 `ENV_TAG` reject tag)** として登録する。
`DW-M03` により、構造検査と挙動テストの両方で赤くなる変異は
canonical kill を挙動側とし、構造検査は冗長 gate と明記する。

---

# 段 6 焦点再レビュー 2 の裁定 (fix 3 の指示 — `DW-O16` の最終巡)

焦点再レビュー 2 (`s6-focused2/output.md`) は **NO-GO / BLOCKER 2 / HIGH 2 / MEDIUM 1**。
fix は本巡が 3 巡目であり、以後は親が裁定して閉じる (`DW-O16`)。

## 根本原因 (BLOCKER 2 件に共通)

R10〜R12 は**名前と形**を pin するが、`_admit_env_contract` の**意味**を検査していない。
また R11 は `ImportFrom` の alias を見ず、R12 は `_current_site` を追跡しない。
そのため次の 4 変異が生存する。いずれも難読化ではなく、素直に読める通常のコードである。

- M20 `return _lookup(os.environ.get("IZANAGI_ENV_TAG", ENV_TAG))`
- M21 guard 条件へ `and not os.environ.get("IZANAGI_ALLOW_PEGASUS")` を追加
- M22 `from campaign.p3_s4_loop import CLK as LEGACY_CLK` + `_current_site is site_policy.current_site` で分岐
- M23 reject tag を `_current_site is not site_policy.current_site` で分岐

*成果物影響*: M20/M21 は環境変数 1 つで `OTHER` 上の Pegasus contract 選択または
認識済み Pegasus の通過を許し、偽 env の WAL・材料レポート・certified 選択を生む。
M22/M23 は再校正後も stale clock が `run_cmd` に入り、reject WAL が canonical tag と分裂する。

## 11. fix 3 の must-fix (テストファイルのみ。production は変更しない)

### R13 [BLOCKER] admission 本体の意味を exact-shape で pin する

`_admit_env_contract` の AST で、guard 条件が**厳密に** `not _site_admits_measurement(site)`
(追加の boolean 項なし)、return が**厳密に** `_lookup(ENV_TAG)` (追加の呼出し・引数加工なし)
であることを固定する。M20 / M21 を殺す。

### R14 [BLOCKER] 旧定数の import alias も禁止する

R11 を拡張し、`ast.Attribute` の `CLK` / `NUMA` に加えて、
`Import` / `ImportFrom` が `CLK` / `NUMA` を (別名を含めて) 束縛することも禁止する。M22 を殺す。

### R15 [BLOCKER] `_current_site` も参照範囲 pin の対象に加える

R12 の追跡名に `_current_site` を足し、module-level 代入と `_admit_env_contract` 本体の中だけに
限定する。M22 / M23 を殺す。

### R16 [BLOCKER] 既定束縛のまま実 sink を通す挙動テスト

依存を monkeypatch してから driver を fresh module としてロードし、
`_current_site` / `_lookup` が**既定に束縛されたまま**、measurement sink と reject sink の
**実経路**へ distinct contract を流す。既存の fresh-module テストは `_admit_env_contract()` を
単体で呼ぶだけなので、実 sink の条件分岐を踏まない。M22 / M23 の挙動側 canonical kill を作る。

## 12. HIGH の裁定

### U5 (新設) — C4 の順序問題は scope 外の既知残余へ昇格

レビュー 2 の指摘は正しい。親の §9 は過小だった。
report 生成**後**に guard 拒否が起きると provenance header は書き換わるが、
既存の材料レポートは上書きされないため、その `artifact_refs` の SHA が現 header bytes と一致しなくなる。
*成果物影響*: 材料レポートの proof chain が、実在する現在の campaign artifact を指さなくなる。
*裁定*: **real**。ただし修正は production の transactional 復元か既存 report の明示 invalidation を
要し、本 wave の 2 ファイル scope を超える。**U5 として裁定パッケージへ送る**。

### M13 の逐語 spec を親が確定する (レビュー 2 の HIGH)

`s6-focused/output.md` の M13 は自然言語だった。次の逐語で固定する。

old:

```
    contract = _admit_env_contract()
    return L.record_diff_reject(
        layout, genome, implementation, res, env_tag=contract.env_tag
    )
```

new:

```
    contract = _lookup(ENV_TAG)
    variant = L.record_diff_reject(
        layout, genome, implementation, res, env_tag=contract.env_tag
    )
    site = _current_site()
    if not _site_admits_measurement(site):
        raise execution_guard.ExecutionGuardError(
            f"{ENV_TAG} の env bytes は site={site!r} では生成できない"
        )
    return variant
```

`ExecutionGuardError` は依然として送出されるので、赤理由は **WAL 0 行 assert の不一致だけ**に絞られる。
M17 / M18 の canonical は R11、冗長は R12 と明記する。

## 13. 受入の一次資料 (段 7 はこの数値を使う)

レビュー 2 の MEDIUM 指摘どおり「7 ファイルを 3 回」とは書かない。実測は次のとおり。

| request | ファイル数 | items | 結果 | 所要 | workers |
|---|---:|---:|---|---:|---:|
| `876263.nqsv` | 6 | 418 | 409 passed / 9 skipped | 2.63s | 48 |
| `876299.nqsv` | 7 | 432 | 423 passed / 9 skipped | 7.89s | 48 |
| `876344.nqsv` | 7 | 435 | 426 passed / 9 skipped | 4.30s | 48 |

変更前 baseline は `875911.nqsv` (`bnode002`、3 ファイル、183 passed、2.33s)。
site 実測 probe は `875967.nqsv` (`bnode114`)。
