# 裁定パッケージ — 8b 再開の統合 wave が返す 4 件

wave = dev-wave-t8b-restart-integration、base main = `118feb6d`。
`DW-S04`「承認済み裁定を止めてよいのは裁定時点で未見の新事実がある場合だけ。止めるときも親が
不採用にせず、新事実付きのユーザー再裁定待ちへ戻す」に従う。

| # | 対象 | 状態 |
|---|---|---|
| **R-4** | [T-747] toolchain 束縛 | 実装前提が段 1 実測で覆った (本文 §前半) |
| **R-5** | W-1 [T-088] official 解禁 | D86 §4 の中核前提が敵対検証で崩れた (§R-5) |
| **R-6** | W-3 freeze v2 producer | producer identity と budget authority が未定 (§R-6) |
| **R-7** | W-4 oracle manifest CLI | schedule authority 不在で certified 選択を改変しうる (§R-7) |

本 wave が実装したのは [T-749] (verify CLI の受領証参照) の 1 件だけである。

---

# R-4 — [T-747] (a) の実装前提が段 1 実測で覆った

> **superseded (2026-08-11、wave `dev-wave-t8b-restart-residue` による追記)。**
> 本節が扱う **(a) 「env contract へ toolchain を束縛する field を足す」は、
> その後のユーザー裁定で採られなかった。** 現行の正本は
> **[T-747] = (B)** (worklog 403、2026-08-11 /rulings) —
> toolchain 束縛は env contract へ field を足さず契約の外へ置き、contract 内
> `calibration_ref` の実 calibration bytes を derived toolchain authority として、
> attempt 実測値と `build_v2` toolchain manifest を照合する。
> 実装単位は [T-783]。**本節を実装の根拠にしてはならない** — 以下は
> 「(a) がなぜ採れないか」の記録として読むこと。
> なお (B) 自身も `output/insights/2026-08-11_t8b-restart-residue/package.md` の
> 4 blocker により再裁定へ戻っている。

## 何が裁定されていたか

[T-747] = **(a)**: 「env contract へ toolchain を束縛する field を足し、Pegasus 世代は system compiler を
実体・版数つきで焼き込む。既存 `linux-baremetal` 床値との混用は不可。(c) 固定要求の緩和は
計測条件の同一性を崩すため不採用。gcc-13 module の存否確認は wave の段 1 実測に含める。」

裁定の材料は `docs/phase3-8b-restart-runbook.md` §1.2 であり、そこには **pin 連鎖の分析が無い**。
覆ったのはこの分析の欠落部分である。

## 段 1 実測 (すべて一次資料・実挙動から採取)

### M1 — gcc-13 はユーザー権限では入手できない (裁定が要求した実測)

login ノード `pegasus02` で実測した。

- `MODULEPATH` の全 dir を再帰列挙しても **gcc の module は 1 件も無い** (compiler module は cuda /
  intel / nvhpc のみ。hit するのは openmpi / hdf5 の `gcc11.4.0` ビルド名だけ)。`/system/apps` 配下にも無い
- `module spider` サブコマンド自体が存在しない。spack・conda・個人 modulefiles
  (`~/privatemodules` 等) もすべて不在
- 既定は `gcc 11.4.0`。ほかに `gcc-12` / `gcc-11` / `gcc-9` があり、`gcc-13` / `g++-13` は不在。
  計算ノードは `g++-12` (runbook §7 の既記録)
- **ただし完全には閉じていない**: `apt-cache policy gcc-13` は候補
  `13.4.0-6ubuntu1~22~ppa2` を返す (ubuntu-toolchain-r/test PPA が既に設定済み)。導入には root が要り、
  ユーザー権限では入れられない。また `singularity` / `apptainer` / `docker` が実在するため
  コンテナ経由の経路も残る

→ 択 (b) は「物理的に不可能」ではなく「**管理者への依頼かコンテナ化なしにはユーザー権限で入手できない**」。
コンテナ化は計測環境そのものを変えるため、env 契約・attestation の前提を作り直すことになる。
**(b) を採るかどうかはユーザーの判断事項として残る** (親は「閉じている」と断定した当初の書き方を訂正する)。

### M2 — contract へ field を足すと import 時点で fail-closed する (実編集で実測)

`ExecutionEnvironmentContract` へ `toolchain` field を 1 つ足して実測した (模擬でなく実編集。F29)。

```
campaign.env_contract.EnvContractError:
  pegasus g2 contract_sha256 が reviewed golden と一致しない: 082bf755ba14c32b29393e11729f090e26f1532b2889f4a62fc5860cd17eeb4e
```

`contract_sha256` は **全 field の canonical JSON の sha256** であり (`env_contract.py` の同名 property)、
`_build_registry()` が **import 時に** reviewed golden literal と照合する。
したがって field 追加は `campaign.env_contract` を import 不能にし、orchestrator 全体が停止する。
編集は即時復元済み (`git diff` 空、commit と一致)。

### M3 — 現行 hash は 3 つの pin に同時に束縛されている

pegasus g1 の `e576e9cd…` は次の 3 箇所が同時に握っている。

1. `orchestrator/campaign/env_contract_activations/00000001.json` の `active_contracts` と、
   それを包む `activation_state_sha256`
2. `output/s8b-freeze/floor_protocol.json` の `.contract_sha256` (**凍結成果物**)
3. selector 予測封印 — `s8b_prediction_runner` が `protocol_sha256` を pin し、
   さらに承認定数からの protocol 再導出 bytes と committed bytes の一致を要求する

`linux-baremetal` g1 の `1b2ee853…` も同じ dataclass から導出されるため、
**Pegasus だけを変えるつもりでも linux-baremetal 側の hash が動く**。
「既存 linux-baremetal 床値との混用不可」という裁定は値の混用を禁じたものだが、
実装は値だけでなく**契約 hash そのもの**を過去に遡って変えてしまう。

### M4 — 偽 hit の危険は legacy 経路に限られる (床値経路は保護されている)

**訂正**: 当初この項を「既定を替えると偽 hit する」と一般に書いたが、床値経路には当たらない。

- **legacy `cache_key`** は cc/cxx を pre-image に織り込む一方、**既定 toolchain は省いて旧キーを温存**する
  後方互換規則を持つ (同関数の docstring が明記)。したがって `DEFAULT_CC`/`DEFAULT_CXX` を替えると、
  新既定のビルドが**旧 `g++-13` ビルドと同一 key になり偽 hit する**。
  legacy `buildcache.build()` の production caller は `pipeline` / `s2_verify_calibration` /
  `s5_permutation_coverage` / `backoff_profile` / `between_run_floor` / `pegasus_floor_scoping` 等に実在する
- **床値 campaign は `build_v2` を使う** (`s8b_floor_campaign.py` の build 呼び出し)。
  `_v2_identity` の pre-image は `cc` / `cxx` に加えて **toolchain manifest の hash**
  (compiler と cmake の実 `--version` 出力) を含むため、compiler を替えれば key は必ず変わる。
  **床値の binary identity は保護されている**

→ 対策が要るのは legacy 経路だけであり、床値実測の可否を左右する blocker ではない。

### M4-b — site 別 compiler 解決の機構は既に repo にある

`buildcache.compilers_for_current_site()` は「実 site が Pegasus compute のときだけ system compiler を
選ぶ」と実装済みで、`("gcc", "g++")` を返す。`pegasus_floor_scoping.py` / `pipeline.py` /
`loop.py` / `screening_driver.py` は既にこれを使っている。
**床値 campaign だけがこの解決を使わず `DEFAULT_CC`/`DEFAULT_CXX` を直接渡している。**

つまり「Pegasus では system compiler を使う」という挙動は既存機構で表現でき、
足りないのは**どの compiler で測ったかを契約側で束縛・検査すること**である。
これは択 (B) の実装コストを大きく下げる。

### M5 — compiler の事実は既に記録されている (束縛されていないだけ)

`tools/pegasus/floor_campaign.sh` は attempt ごとに `compiler.path` / `compiler.version` /
`cxx.path` / `cxx.version` / `cmake.version` を実測して書き出している。
欠けているのは記録ではなく、**それを検査する束縛**である。

### M6 — `g++-13` は床値 driver だけの要求ではない

`source_digest` は D23 により preprocess を `g++-13` で行い (既定引数 8 箇所)、
`buildcache` の既定も `gcc-13`/`g++-13` である。source digest 値は proof chain に入る。
toolchain を替える影響は floor campaign に閉じない。

## 何が問題か (1 行)

**裁定文言どおり contract に field を足すと、床値実測が走るために必要な floor protocol と
selector 予測封印を作り直さねばならず、事前登録性 (式 3) に触れる。**
手順書 §4 はこの経路を「事前登録性を守る正しい挙動であって、迂回してはならない」と書いている。
つまり [T-747](a) と [T-748] (第 1 世代のまま床値実測) は、文言どおりには両立しない。

## 択一 (親は決めない)

- **(A) 協調再凍結**: contract に field を足し、reviewed golden・activation record・floor protocol・
  selector 予測封印をすべて作り直す。**事前登録性への影響をユーザーが受諾するかが論点**。
  実凍結は AI が行えないため、人間手番が複数回要る。[T-657] の世代交代と合流させれば再凍結は 1 回で済むが、
  [T-748]「待たない」と衝突する
- **(B) 束縛層を contract の外へ置く (親の推奨)**: toolchain を execution receipt / admission 側へ束縛する。
  contract hash は不変なので 3 つの pin が生き、床値実測を第 1 世代のまま走らせられる ([T-748] と両立)。
  M5 のとおり実測値は既に記録されており、足すのは検査だけである。
  **裁定文言「env contract へ field を足し」からは外れる**ため、文言の読み替えをユーザーが認めるかが論点
- **(C) 実測を先送り**: [T-657] の世代交代 + 恒久 freeze 機構 (v3) の発効を待ち、そこで toolchain を
  最初から contract に入れる。[T-748] の「待つと B 線が無期限停止する」という判断を覆すことになる

択 (B) は敵対レンズ A-11 の指摘で具体化した。**contract の `calibration_ref` は既に hash 束縛されており、
その実 calibration bytes は gcc の path / version と C/CXX build argv を保持している。**
これを derived toolchain authority として、wrapper が attempt ごとに書く実測値
(`compiler.version` / `cxx.version`) および `build_v2` の toolchain manifest と照合すれば、
**active contract hash を変えずに toolchain を束縛できる**。

legacy `cache_key` の後方互換規則 (既定は key から省く) の手当ては、択に関わらず legacy 経路にだけ必要である。

## この裁定が出るまで止まるもの

- W-2 床値実測 (手順書 §3 が「R-4 の裁定なしに投入してもビルド段で fail-closed に倒れる」と明記)
- W-5 oracle 実走 (床値と、人間による実凍結手番が先)

---

# R-5 — W-1 (official 解禁) は D86 §4 の設計のままでは実装できない

D86 (2026-07-25) は U-1〜U-4 を一括承認し、§4 に「単一 admission predicate」の最小案を置いた。
本 wave の段 2 で file:line 粒度のプランを起こし、段 3 の 2 レンズ (max) が独立に **NO-GO** を返した。
D86 §7 自身が「guard 無効状態でのテスト実行を harness の permission classifier が拒否したため、
**解除後の実挙動は未実測であり根拠は静的読解と模擬にとどまる**」と限界を明記していた部分が、
実装設計の段で表に出た。

## 新事実 1 — scheduler が spool した bytes を独立取得する経路が無い (A-1)

D86 §4 の設計制約は「wrapper hash は scheduler が返す job record / spool された script bytes /
committed blob を**独立取得**して照合する」と要求する。プランはこれを
「job script が `9<"$0"` で自分自身を固定 FD に渡し、Python が FD から読む」で満たそうとした。

**これは恒真化である。** `9<"$0"` は呼び出し側が選んだファイルを開くだけで、scheduler 由来である証明にならない。
有効な floor job の計算ノード内で nonce・`PBS_JOBID`・reservation 環境を継承した子が、
wrapper を経ずに `python3 ... --mode official ... 9<tools/pegasus/floor_campaign.sh` と起動すれば、
FD・receipt・committed blob の三者はすべて同じ committed bytes になり admission を通る。
現行 admission が scheduler identity として読むのも環境の nonce / job ID だけである。

**scheduler-owned な spool 証拠をどう取るかは、新しい設計判断である。**

## 新事実 2 — receipt を unlock にすると D86(8) の禁止に抵触する (A-2)

D86(8) erratum は「認可の**実体**はユーザーの明示指示であり、submission artifact はその指示が
実行された**記録**にとどまる。artifact の存在を認可の証明として扱ってはならない」と定めた。

プランの revision gate は `HEAD == receipt.source_commit` であり、承認済み revision・main ancestry・
ユーザーが指した revision のいずれとも比較しない。`submit_floor.sh` は現在の任意の clean HEAD を
`SOURCE_COMMIT` として receipt に書く。したがって **任意の clean revision で実 qsub すれば全条件を通る**。
official の受理集合が「ユーザーが指示した revision」ではなく「receipt を自己生成できる全 clean revision」へ広がる。

D86(3) は「新しい Git launch receipt は作らない」と裁定しており、
**現在の裁定の枠内には「ユーザーが指した revision」を機械的に束縛する authority が存在しない。**

## 新事実 3 — admission が下流の proof chain に一切残らない (A-5)

certificate v1 が持つのは freeze SHA / clean digest / protocol SHA / 時刻 / run ID の 5 値だけで、
journal の exact schema にも submission receipt・source commit・spool hash は無く、
ratified verifier の equality chain にも対応する edge が無い。
プランは certificate v1 と resume schema を不変とし (D86 §4 の「不変」条項どおり)、
snapshot も直列化しない。

したがって **下流は「本当に admit された artifact」と「自己整合な偽物」を区別できない。**
certificate v2 / journal 拡張 / ratified verifier 追加は D86(5) が明示的に先送りした項目であり、
本 wave の scope 外である。

## 併せて閉じる必要がある real 所見 (実装時に同時対処)

- **A-3**: `_run_campaign_core` は public wrapper の 13 seam 拒否を迂回して直接呼べ、
  `measure_fn` 等の注入で任意 throughput を official result に流せる
- **A-4**: `VerifiedFreeze` は公開 constructor を持ち `document` が mutable dict のため、
  検証した bytes と実行に使う document の同一性が保証されない (既登録 [T-090] と同型)
- **B-1**: 現行は `acquire_claim` を campaign の最初の副作用にする意図的設計で、
  official preflight はその後にある。admission を副作用ゼロのまま claim より前へ出す必要がある

## 択一 (親は決めない)

- **(A) spool 証拠の取得方式を設計し直す** — caller が開いた FD 以外の方法
  (scheduler の job record 照会、spool directory の直接読み等) を新規に設計する。
  D86 §4 の「独立取得」要求を満たす唯一の道だが、実現可能性は未調査
- **(B) 認可を機械化せず運用前提に留める** — admission は「clean・revision 整合・freeze allowlist」
  までを機械化し、「ユーザーが指した revision であること」は運用規律に委ねると明記する。
  受理集合が「全 clean revision」へ広がることを**明示的に受諾する**ことになる
- **(C) ユーザーが指した revision を束縛する authority を新設する** — D86(3) の「新しい Git launch
  receipt は作らない」を覆す。署名付き allowlist (D86 の U-3(c)) が該当する
- **(D) admission 証拠を proof chain へ通す** — certificate v2 / journal / ratified verifier を拡張する。
  D86(5) の先送りを解除することになる。(A)〜(C) のいずれと組んでも独立に必要である

**親の推奨は無い。**(B) は規律 2 に対する受理集合の実質的拡大であり、(C)(D) は D86 の明示裁定を覆す。
いずれも親が決めてよい範囲を超える。

---

# R-6 — W-3 (freeze v2 producer) は実 producer を記録できず budget の権威源も無い

## 新事実 1 — transition table が実 producer の記録を禁じる (A-7)

v1→g1 の transition table は `/generator/sha256` の変更だけを許し、`/generator/path` の変更を拒否する。
したがって新 module (`s8b_freeze_candidate.py` 等) が v2 を生成しても、成果物は
**旧 `s8b_holdout_freeze.py` を generator として記録する**。verifier は記録された旧 path の blob hash
だけを検査するため、実際に bytes を作った module はどの edge にも束縛されない。

**択一:** (a) producer を旧 module 内へ置いて記録を真実にする / (b) 新しい producer record と
path transition を追加する (transition table = 凍結契約の変更)。

## 新事実 2 — budget に権威源が無い (A-10)

producer が受け取る budget は「有限非負・key 集合 exact」しか検査されない。
全 holdout に `10^15` 秒を割り当てた JSON も、全値ゼロの JSON も同じく通る。
候補単体は発効しないが、通常の approval / active 手順の後は driver がその値をそのまま limit として読み、
ledger reservation に使う。巨大値なら事前登録された探索予算が実質無効化され、
ゼロなら全行が budget refusal となって certified 選択が空になる。

**択一:** (a) 後段の人間承認が budget 数値そのものを承認する契約とする /
(b) 別の凍結済み authority から導出する。

## 併せて必要な手当て

- **A-8 / B-9**: 出力 path の containment が無く、`--output` に
  `output/s8b-freeze/active/<64hex>.json` 等を渡せば active loader を停止させられる。
  symlink 経由で凍結 namespace へ書く経路も塞がれていない
- **B-8**: candidate を canonical namespace 配下へ書くと、検査結果は `no-active` ではなく
  `namespace-dirty` になる
- **A-12**: W-3 は W-1 を通過した `mode=official` かつ `eligible_for_refreeze=true` の floor result を
  必要とする。**R-4/R-5 が未裁定のうちは、生成できるのは synthetic fixture だけである**
- g2 以降の candidate は構造上作れるが `launch_validate` が `generation_number==1` 以外を必ず拒否する。
  g2 を承認・active 化すると現行 oracle 全体が launch refusal になる

---

# R-7 — W-4 (oracle manifest CLI) は縮小 schedule で certified 選択を作り替えられる

## 新事実 — exact key 検査は schedule の内容を束縛しない (A-9)

`_validate_schedule` は「与えられた cell 集合の中での完全性」しか検査しない。
builder は holdout が freeze の部分集合であることしか要求しない。したがって
**active freeze の全 holdout を含めつつ、各 holdout について 1 configuration だけを置き、
`n=1` の完全 block schedule を作る**ことができる。

report は manifest の行だけから `expected_cells` を作り、judge は候補が 1 件なら `unique-best` を返す。
結果として **本来比較すべき configuration を走らせないまま、選んだ 1 件が各 holdout の winner になる。**
これは certified 選択の直接改変である。

module 自身の docstring は「official CLI は active ratified freeze を束縛する」と約束しているが、
プランは任意の `--freeze PATH` を builder へ直接渡すだけだった。

## 択一 (親は決めない)

- **(a)** manifest CLI を「active ratified freeze 限定 + freeze の全 cell 積 + 承認済み
  `n` / `master_seed` への束縛」まで含めて実装する (scope 拡大)
- **(b)** reviewed spec を凍結成果物として先に作り、CLI はその bytes を hash 照合するだけにする
- **(c)** W-4 を oracle 結線 wave へ送る

**参考**: schedule / run contract / campaign ID の production source は現在 repo に存在しない
(テスト fixture のみ)。どの案でも「reviewed spec は誰がいつ承認するか」を決める必要がある。
