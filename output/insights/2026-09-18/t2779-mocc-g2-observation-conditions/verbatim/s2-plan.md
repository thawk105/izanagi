## 1. 推奨と参照の表記

**各 arm 120 走、4 node × 30 round × 3 arm を採用する。P2・P4 は採用、P1 の検出力の説明と P3 の自己検査・窓の説明は修正する。** 本 wave は率の比較と witness 軽量化の静的設計までとする。

以下の略記は、すべて今回指定された現物を指す。行番号は改版前のもの。

- `V`：job dir `verbatim/t2774_probe-v4.py`
- `M`：同 `mocc-transaction-e9e477ca.cc`
- `R`：同 `t2774-README.md`
- `O`：同 `operational-facts.md`
- `X`：同 `instr-mocc-lock-coverage.patch`
- `D`：同 `mocc-close-version-counter-gap.patch`
- `G`：repo `orchestrator/campaign/mocc_g2_discriminator.py`
- `H`：repo `orchestrator/campaign/s3_mocc_lock_coverage.py`
- `P`：repo `orchestrator/campaign/patchharness.py`
- `C`：repo `tools/pegasus/dispatch_compute.py`

必読資料はすべて読取可能だった。書込み・pytest・build・ベンチ実走は行っていない。検出力だけは標準ライブラリによる有限和で再計算した。

## 2. runner v5 の最小差分設計

**`V:365–390`：`defines` の追加と検証。**

既存必須項は維持し、任意項を `{"observational_only", "defines"}` にする。省略時は `{}`、明示的な `null`・配列・文字列は拒否する。正規化済み arm に `"defines": dict(defines)` を持たせる。

固定列との二重管理を避けるため、`V:420–422` の七つの define を次の tuple に抽出し、`configure_argv` と validator が共有する。argv 上の順序は現行と同じにする。

```python
BASE_CCBENCH_DEFINES = (
    "-DCCBENCH_TRACE=1",
    "-DCCBENCH_BACK_OFF=0",
    "-DCCBENCH_BACKOFF_FIXED=-1",
    "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
    "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
    "-DCCBENCH_WAL=0",
    "-DCCBENCH_CCACHE=OFF",
)
CONFIGURE_DEFINE_KEYS = frozenset(
    item[2:].split("=", 1)[0] for item in BASE_CCBENCH_DEFINES
)

def validate_defines(value):
    if not isinstance(value, dict):
        raise ValueError("arm defines must be an object")
    for key, val in value.items():
        if (
            not isinstance(key, str)
            or not key.startswith("CCBENCH_")
            or key not in CONFIGURE_DEFINE_KEYS
            or not isinstance(val, str)
        ):
            raise ValueError("invalid arm configure define")
    return dict(value)
```

`validate_arms` 内の追加は次の形にする。

```python
defines = validate_defines(entry.get("defines", {}))
```

これにより `CCBENCH_KEY_SORT` も、接頭辞は正しいが固定列にないため拒否される。本 wave の値は下記 JSON に固定し、一般的な値域検査は追加しない。

**`V:415–433`：既存項の置換だけを許す。**

署名末尾に `defines=None` を追加する。固定 argv を作り、上書き対象がその argv に存在することを再確認してから置換する。追加 append は行わない。

```python
def configure_argv(
    source, build, policy, toolchain, dependencies, defines=None
):
    overrides = validate_defines({} if defines is None else defines)
    argv = [
        # 現行 V:418–433 の列。
        # V:420–422 の七つの CCBENCH 項だけ
        # *BASE_CCBENCH_DEFINES に置き換える。
    ]
    present = {
        arg[2:].split("=", 1)[0]
        for arg in argv if arg.startswith("-DCCBENCH_")
    }
    if overrides.keys() - present:
        raise ValueError("configure define is absent from fixed argv")
    return [
        f"-D{arg[2:].split('=', 1)[0]}="
        f"{overrides[arg[2:].split('=', 1)[0]]}"
        if arg.startswith("-DCCBENCH_")
        and arg[2:].split("=", 1)[0] in overrides
        else arg
        for arg in argv
    ]
```

固定列には各 key が一回ずつ存在する。上書き時も列長・位置を維持する。CMake・toolchain・dependency 引数の変更は対象外。

**`V:519–532`：arm 自身の argv を binding の根拠にする。**

warmup は現状どおり基底 define のままとする。arm build のループを `for definition in arms:` とし、次のように変更する。

```python
arm = definition["name"]
build = scratch / f"build-{arm}"
binding = bindings["arms"][arm]
binding["configure_argv"] = configure_argv(
    sources[arm], build, policy, toolchain, dependencies,
    defines=definition["defines"],
)
binding["configure_defines"] = [
    arg for arg in binding["configure_argv"]
    if arg.startswith("-DCCBENCH_")
]
binary = build_variant(binding["configure_argv"], build, driver, jobs)
binding.update(binary=str(binary), binary_sha256=sha(binary))
```

`V:521` のトップレベル `configure_defines` は互換のため残すが、**warmup の基底列**と説明する。bo1 の束縛確認には `bindings.arms[arm].configure_defines` を使う。

warmup の build target は `masstree_build` のみであり、各 arm の `ycsb_mocc.exe` は別 build directory で必ず build する（`V:436–443,519–532`）。dependency source も共通 staging を参照する（`H:224–254`）。この構造から、今回の BACK_OFF 差だけを理由に warmup を三回に増やす必要はない。

ただし、Masstree の CMake 定義自体は射影に含まれておらず、BACK_OFF がその target に流入しないことの完全な依存関係証明は不確実。smoke で arm 別 configure と生成 binary の束縛を確認する。warmup は benchmark の予備走ではない。

**`V:616–636`：selftest。**

既存の省略時正規化期待値に `"defines": {}` を追加する。追加する独立チェックは次の四つ。

| ケース | 入力 | 期待 |
|---|---|---|
| 受理 | `{"CCBENCH_BACK_OFF": "1"}` | 正規化後保持、argv の BACK_OFF が一個だけ `"1"` |
| 未知 key | `{"CCBENCH_KEY_SORT": "0"}` | `ValueError` |
| 接頭辞違い | `{"BACK_OFF": "1"}` | `ValueError` |
| 非文字列 value | `{"CCBENCH_BACK_OFF": 1}` | `ValueError` |

受理チェックには、無指定 argv が基底と一致すること、上書き前後で変更される引数が BACK_OFF 一個だけであることも含める。object 型の検証は `defines=[]` と `defines=None` の拒否を同じ validation チェック内で確認する。四チェックを増やす構成なら、成功数は `13` から `17` に更新する。

**schema と legacy。**

`V:466` の `t2774-probe/v1`、`V:186` の `t2774-summary/v1` は据え置く。出力構造と既存 field の意味を維持し、誤って記録していた arm define の根拠を是正する変更だからである。「v5」は runner の改版番号として SHA とともに insight に束縛する。

`reclassify_block` は保存済み run/verifier JSON から分類を再構成し、define を参照しない（`V:219–245,677–692`）。旧 JSON は読み直せるが、旧 binding の誤記録を補修する機能ではない。旧成果物は書き換えない。

legacy `--instr-patch/--diag-patch/--pairs` は残す。`V:393–407` の排他条件も維持し、省略された defines が `{}` になるだけとする。

**変更禁止箇所。**

- `classify`：`V:94–134`
- discriminator 結果の解釈：`V:137–153`
- CP・集計・再分類：`V:156–245`
- manifest：`V:248–261`
- verifier/discriminator の argv・起動条件：`V:306–341`
- witness off 環境、逐次保存、raw 保持条件：`V:284–288,346–361,539–556`
- checkout・patch touch set・適用順・hash 照合：`V:498–517`
- workload、policy、toolchain、X/P、診断 patch、verifier/discriminator 本体

規律2を維持し、runner の分類境界を今回の改版に混ぜない。

## 3. arms-t2779.json と回転順

`probe/arms-t2779.json` は次の逐語とする。診断 patch は X/P 適用後 source 用なので、patch の順序を維持する（`D:4–35`、`V:506–513`）。

```json
[
  {
    "name": "e9-instr-nowit",
    "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290",
    "patches": [
      "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/verbatim/instr-mocc-lock-coverage.patch"
    ],
    "witness": false,
    "observational_only": false,
    "defines": {}
  },
  {
    "name": "e9-diag-nowit",
    "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290",
    "patches": [
      "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/verbatim/instr-mocc-lock-coverage.patch",
      "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/verbatim/mocc-close-version-counter-gap.patch"
    ],
    "witness": false,
    "observational_only": true,
    "defines": {}
  },
  {
    "name": "e9-instr-nowit-bo1",
    "pin": "e9e477ca1b55348ab4530de0b1cf663ce4555290",
    "patches": [
      "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/verbatim/instr-mocc-lock-coverage.patch"
    ],
    "witness": false,
    "observational_only": false,
    "defines": {
      "CCBENCH_BACK_OFF": "1"
    }
  }
]
```

`observational_only: false` は既存 arm 定義との整合であり、本 wave の certified 利用を認可しない（`arms-q2.json:4–6`、D2114・D2134）。

A/B/C を上記順序とすると、`round_order` は ABC、BCA、CAB の三周期（`V:410–412`）。30 round は三の倍数なので、**各 node で各 arm が各位置に10回**現れる。ただし全六順列を試す設計ではなく、直前 arm の影響や非線形な時間変動を完全に除去する設計でもない。

## 4. 標本・block・投入設計

**K=120 を採用するが、「80%検出力」の条件を限定する。**

独立な `X~Bin(K,p_control)`、`Y~Bin(K,p_treatment)` について、片側 Fisher の下側確率が0.05以下となる `(X,Y)` の二項確率を加算した。`O:20–28` の表は丸め精度で一致した。

| K/arm | 0.058 対 0 | 0.119 対 0 | 0.058 対 0.02 | 0.075 対 0 | **0.05 対 0** |
|---:|---:|---:|---:|---:|---:|
| 40 | .080 | .525 | .039 | .178 | .048 |
| 56 | .224 | .812 | .091 | .412 | .147 |
| 80 | .498 | .968 | .184 | .725 | .371 |
| 112 | .784 | .998 | .277 | .929 | .664 |
| 120 | .831 | .999 | .302 | .951 | **.722** |
| 140 | .914 | 1.000 | .366 | .982 | .834 |

P1 の「0.05、0.058 対0」の説明は分ける。T-2774 の直接対応 arm は `2/40=0.05`、`0.058` は異なる witness off arm を合算した設計用仮定である（`R:29–35,117`）。

したがって K=120 は費用との釣合いを取った観測計画として採用する。**instr-nowit の歴史的点推定0.05に対して80%を保証する計画とは書かない。** 二比較について Bonferroni 相当の各α=.025を使えば、0.058対0でも K=120 は約.702である。部分抑制・node 内依存ではさらに不足し得る。

**block。**

- 本走：B1〜B4、各 block 30 round × 3 arm＝90走。
- 計画総数：360走、各 arm 120走。
- smoke：別 block、1 round＝3走。本走分母に含めない。
- 各 node 内では逐次実行し、四つの投入元 worktree から並行 dispatch。
- arm source は runner がそれぞれ独立 checkout する（`V:498–504`、`P:346–383`）。

launcher は各 block に `--rounds 30` を明記し、同一 arms JSON を使う。K・block 数・smoke 除外・二つの比較方向・欠測規則を `s4-ruling.md` に固定する。結果を見た増減、低発生 block の置換、失敗走を埋める追加走は行わない。未完走の場合は計画数と実現数を分けて報告する。

**時間。**

`90×22=1,980秒＝33分`。build三本・warmup・hydrate を加え、**約40分/block**を中心見積とする（`O:10,16`）。前 wave の最大 verify 22.7秒に run 3.07秒を加えた計算でも、90走で約38.7分＋準備であり、02:30:00には通常時の余裕がある。ただし per-run timeout の総和まで収まる保証ではない（`V:667–668`）。

投入形は既存 generic dispatch を使い、後段 argv の先頭に `/bin/python3.10 -B` を明示する。`C:1880–1893` は generic argv をそのまま実行するため、**dispatcher 自身の interpreter 選択だけでは任意の子 argv の Python 版を保証しない**。

`--walltime 02:30:00 --queue-wait-timeout 3600 --overall-grace 4200` は採用する。`O:33` の時限説明には補足が必要で、現物は初期 deadline を投入時刻基準にし、RUN 初観測時に再設定する（`C:4155–4158,4201–4211`）。

smoke の緑は G2 の有無で決めず、三 arm の configure/binding、三走の保存、verifier 正常実行、集計までの到達で判断する。

## 5. 段4に置く主解析の事前登録文案

> 本走は4 block、各 block 30 round、各 roundに3 armを一回ずつ実行する。計画標本は各 arm 120走とし、結果を見て増減しない。smoke、T-2774 Q1/Q2は本走に合算しない。
>
> 主比較は、① e9-diag-nowit 対 e9-instr-nowit、② e9-instr-nowit-bo1 対 e9-instr-nowit の二本に固定する。いずれも介入側のG2 signal検出率が低下する方向の片側 Fisher を参考値として示す。主表示は arm 別の検出数・分母・Clopper–Pearson両側95%区間とする。二比較の未調整p値を示し、どちらか一つのp<.05をもって family 全体の有意な効果とは判定しない。
>
> CP区間と Fisher は独立Bernoulli試行を仮定する。node内相関、決定的な回転順、時間変動はモデル化していないため、検出力・区間・p値はその仮定下の記述に限る。各blockのarm別件数も併記し、合算値だけからnode一般の効果を主張しない。
>
> 計画数120、保存済み走数N、有効verifier判定数m、判定確定数decisive_m、G2 signal数k、failure、indeterminate、未開始数を分ける。既存summaryの主区間はk/mに対応する。failure・未開始をno-G2と数えず、indeterminateもcertified no-G2と同一視しない。欠測があれば計画120走を分母とする確定率として表示しない。
>
> 固定cellでinstr-nowitはk/N、diag-nowitはk′/N、bo1はk″/Nだった、と報告できるのは分母条件を明示した場合に限る。診断patch／backoffの寄与は検出率の比較までであり、実行順序の直接観測ではない。根因・必要性は確定しない。陰性はG2不在の証拠でない。certified昇格・pin前進・変異探索の扱いは変えない。

分母規則の根拠は `V:185–215,555`。runner の `N` は保存済み走数であって計画数ではない。また `classify` は正の cycle を現象名の検査なしに `g2` とする（`V:131`、`R:167–169`）。レビューBは正例の anomaly 内容を照合し、G2以外があれば区別して記述する。分類器は変更しない。

三 arm とも witness off なので、正例でも discriminator は `not-run: witness-off` となる（`V:319–327`）。本 wave で payload lineage の `supported/contradicted` を得たとは主張しない。

3秒固定走では commit 機会数が arm ごとに変わり得る。保存済み `commit_count` を曝露量の補助表示に使い、commit当たりの独立試行とは扱わない（`V:293`、`R:40–46`）。診断 patch は既存観測に対する追加拒否であり、実行全体の commit 数の単調減少は保証しない。

Fisher は既存 runner に実装されていないため、親の集計で算出し、入力2×2表・方向・算出式を insight に残す。runner v5 の改版に統計機能を足さない。

## 6. witness 軽量化の静的設計

**採用する。ただし「stored≠txidでabortする既存自己検査」は存在しないため、設計前提を修正する。**

`M:100–110` の現行 helper は、decode に失敗すれば abort するが、decode した producer と writer txid を比較していない。不一致値も S 行へ書き、`G:378–380` が `witness-post-store-token-mismatch` として検出する。`O:39` と親案のこの部分は現物に反する。

したがって、不一致による新しい producer abort は追加しない。**decode失敗時の既存abortをpublish直後に維持し、不一致は実測値のまま保存・出力する。**

**保持先と変更箇所。**

| 現物位置 | 変更案 |
|---|---|
| `M:13–16` | `#if TRACE` 内に `<vector>` を明示追加 |
| `M:100–110` | S emitter を保存済み producer の出力専用にする |
| `M:1134–1135` | thread-local vector を宣言し、witness有効時にclear/reserve |
| `M:1197–1200` | 共有bodyのdecodeとproducerのpushだけにする |
| `M:1207` 直後 | write_set_を同順再走査してSを出力 |
| `M:1208–1212` | 既存cleanupの順序を維持 |

`WriteElement` に field は足さない。以下が patch 化の核となる逐語案。

```cpp
// M:100–110 の helper を置換。共有 record は読まない。
void izanagi_mocc_g2_emit_post_store(
    std::size_t thid,
    std::uint64_t writer_txid,
    const WriteElement<Tuple>& write,
    const Tidword& version,
    std::uint64_t stored_producer) {
  izanagi_mocc_g2_stream(thid)
      << "S " << writer_txid << ' '
      << izanagi_trace::key_to_hex(write.key_) << ' ' << version.epoch << ' '
      << version.tid << ' ' << stored_producer << '\n';
}
```

```cpp
// M:1134 の #if TRACE 内、最初の publish より前。
thread_local std::vector<std::uint64_t> izanagi_stored_producers;
const bool izanagi_witness_enabled = izanagi_mocc_g2_enabled();
if (izanagi_witness_enabled) {
  izanagi_stored_producers.clear();
  izanagi_stored_producers.reserve(write_set_.size());
}
```

```cpp
// M:1197–1200 を置換。publish直後の共有bodyを読む位置は維持。
#if TRACE
    if (izanagi_witness_enabled) {
      std::uint64_t stored_producer = 0;
      if (!izanagi_mocc_g2_decode((*itr).rcdptr_->body_, stored_producer))
        std::abort();
      izanagi_stored_producers.push_back(stored_producer);
    }
#endif
```

```cpp
// M:1207 unlockCLL(); の直後、RLL_/GC/read_set_のcleanupより前。
#if TRACE
  if (izanagi_witness_enabled) {
    std::size_t index = 0;
    for (const auto& write : write_set_) {
      izanagi_mocc_g2_emit_post_store(
          thid_, izanagi_txid, write, maxtid,
          izanagi_stored_producers[index++]);
    }
    izanagi_stored_producers.clear();
  }
#endif
```

reserve を最初の publish より前に行い、publish後のpushで再確保しない。容量は thread ごとに再利用する。今回の固定cellの完走経路では UPDATEだけであり、witness有効時の INSERT/DELETE は既存どおり abort する（`M:1173–1183`）。

**文法・内容・被覆の保存。**

- H/L/S 文法と S の五つの値は変更しない（`M:58,90–110`）。
- `stored_producer` は `M:1195–1196` のpublish直後に、従来と同じ共有 `rcdptr_->body_` から取得する。unlock後には共有bodyを再読しない。
- write_set_ は二つの走査の間に変更されない。`unlockCLL()` が消すのは CLL_ である（`M:1094–1113`）。一要素につき一push・一Sを維持する。
- witness有効の完走経路はUPDATEのみなので、`maxtid.epoch/tid` は全要素で共通。再走査時にも同じ値を使える（`M:1131,1163–1183`）。
- 不一致producerをwriter txidで置換せず保持するので、`witness-post-store-token-mismatch` の被覆を維持する。重複を集合で潰さず全Sを出すので、`witness-duplicate-store` の被覆も維持する（`G:367–390`）。
- discriminatorはSの計数・identityを検査し、実store順を検証しない（`G:330–390,648–653`）。ただし、これは任意のタイミング移動を正当化するものではなく、**採取位置・値・件数を維持する本案**に限った論証である。
- 異常終了時の出力済みprefixは変わり得る。完全出力を得た走の同値性と、異常終了時のログprefix同値性は区別する。後者は未実測。

**L・stamp・Eを動かさない理由の修正。**

L は全writeのpublishより前であり、同transactionの `[publish, unlock]` の直接内側にはない（`M:1141–1147`）。ただしlock保持時間や他threadのスケジュールへの影響まで無いとは言えない。

stamp は各要素自身のpublishより前だが、**二番目以降のwriteのstampは、先行要素のpublishからunlockまでの区間内に入る**（`M:1160–1207`）。親案の「stampは窓を伸ばさない」は単一write、または当該要素自身のpublishとの位置関係に限定する。今回は介入をS出力に絞り、stampは動かさない。

E は現物でunlock前（`M:1203–1207`）。058d0c4e側にも同位置にあるという根拠は `O:39` の運用事実であり、今回の射影には058のsource本体がないため、その同一性の独立照合は未実施。同位置であってもEの時間寄与がゼロとは言えない。今回の差分では固定する、という説明にする。

**静的な負荷見積。**

現行の要素ごとのpublish後処理は、8byte decode・形式確認に加え、stream取得、keyのhex化、五値の書式化、区切り・改行出力を含む（`M:68–75,100–110`）。案ではdecode・既存失敗判定・確保済みvectorへのpushに縮小する。

数値的な短縮時間は未実測。残る後続write・X/P検査・E出力・CLL順のunlockがあるため、窓全体が8byte memcpyだけになるとは書かない。lock解放も `unlockCLL()` 内で逐次行われる（`M:1097–1102`）。

**D16上の扱いと後続。**

変更は `#if TRACE` 内の計器で、validation・publish・CC lock操作を変えない。D16のtrace-hook分類として、後続の正式な実装先は `izanagi-t1943-mocc-g2-readfrom-witness`。本 wave は設計までとし、commit・実走しないP4を採用する。TRACE=1の観測者効果低減は仮説であり、未実測である。

後続arm名は `e9-instr-witlight`。job dirで試験用patchを作るなら、e9に **X/P → witlight** の順で適用し、そのpreimageに対してdiffを作る。X/Pの三検査点とPの被覆を維持し、挿入行に伴う `#line` を整える（`X:48–116`、D1686）。正式hook commitにはX/Pを混入させない。

hook branchへの新commitをpinに使う追試では、runnerの `pin != PIN` によるdiscriminator対象外条件にも注意が要る（`V:323–326`）。本waveでこの条件は変更しない。

## 7. insight の構成と fragment

T-2774と同じ§0〜§11で、以下の内容を置く。

| § | 内容 |
|---:|---|
| 0 | 問い・固定cell・非certifying・範囲外 |
| 1 | 結論と主張上限。三armの率、識別未達、witness案は未実走 |
| 2 | 実行束縛。outer HEAD、pin、patch/source/binary/runner/arms SHA、argv、node |
| 3 | witness静的設計。採取と出力の分離、不一致検査の実際、複数writeの窓 |
| 4 | K=120、4 block、回転順、検出力仮定、二比較、欠測規則 |
| 5 | arm別・block別の結果、CP、Fisher、commit数、smoke別掲 |
| 6 | node内依存、順序、曝露量、根因・必要性・陰性の限界 |
| 7 | CCBench側への扱い。D16、witlight追試候補、pin不変 |
| 8 | 発見した欠陥。新規欠陥がなければその旨 |
| 9 | 段2〜6の所見・裁定・検証結果 |
| 10 | job dirのrunner・JSON・dispatch・raw・manifestへの参照 |
| 11 | brief、plan、consult、ruling、author、review等のverbatim一覧 |

decisions fragmentは**0**を推奨する。標本・runner・計器設計のwave内裁定は `s4-ruling.md` に残し、D2114/D2134の方針は変えない。worklog fragmentは1。failures fragmentは新しい欠陥が見つかった場合のみとし、既知のpilot欠陥や今回是正するbinding問題を新規発見として重複登録しない（`R:178–186`）。

## 8. 実装子・レビューの分割と親の確認

段5はCodex author一本文に限定する（D95）。所有ファイル案は次の二つ。

- `tools/t2779_probe.py`：v4起点のv5一時ファイル。
- `tools/arms-t2779.json`：上記三armの機械設定。

子はjob dirへ直接書かない。親が一時ファイルを実行・確認し、内容を変えずjob dirの `probe/t2779_probe.py` と `probe/arms-t2779.json` へ退避してrepoから消す。実装修正はauthorへ戻す。launcherも新規コードが必要なら同authorへ所有範囲を明示し、親の代筆にしない（D95:10–19）。

段6レビューは二本。

| レンズ | 確認対象 |
|---|---|
| A：runner・静的設計 | 固定項だけの上書き、fail-closed、arm別binding、基底warmup、legacy/schema互換、分類・manifest不変、witness採取位置と値・件数の保存、stored不一致abortを追加しないこと |
| B：実行・収集・集計 | 四blockとsmokeの分離、node・argv・SHA束縛、各90走と未開始会計、各位置10回、欠測分類、G2 anomaly内容、raw/manifest照合、CP/Fisher再計算、二比較と主張上限 |

親の実測確認は、runner selftest、既存patchの適用確認、compute smoke、本走四block、保存JSONからの集計とする。smoke時点でbo1のarm bindingが `BACK_OFF=1`、他二armが0であることを確認する。基底warmupが0なのは正常である。

本waveのverifier/discriminator・patches・gitlink不変を確認し、既存の受入・文書・provenance検査は親が所定経路で実施する。このplanでは未実測であり、緑とは報告しない。

## 総括

- **Kとblock：** 各arm120走、4 node×30 round×3 armを推奨。各nodeで位置は各10回。検出力83%は独立試行・基準率0.058・完全抑制・未調整α=.05の条件付き。直接対応armの率0.05では約72%。
- **runner v5：** `V:365–390`でdefinesをfail-closedに検証、`415–433`で固定項だけ置換、`526–532`でarm自身のargvからdefineを記録、`616–636`でselftestを追加する。warmup・schema・legacy・判定系は維持する。
- **witness設計：** Sの出力を`M:1207`直後へ移し、`1199`では共有bodyのdecodeと保存だけにする案を採用。publish前にreserveする。既存のabortはdecode失敗時であり、stored≠txidのabortは追加しない。複数writeでは後続stampも先行publishの窓に含まれる。
- **親briefへの異議：** P1の0.05と0.058の混同、P3の不一致abortの前提、stampが窓外という一般化を修正する。P2・P4、三armのscope、decisions fragment 0には賛成。generic子のPythonとdispatcher時限の説明も現物に合わせる。
- **予算：** 全段のCodex子はplan1＋consult2＋author1＋review2＝基本6本、fixは必要時のみ。computeはsmoke1＋本走4＝5 job、計363走。本走約40分/blockを四並列、実使用約2時間40分のnode時間＋smoke。各job walltimeは02:30:00。queue待ち・レビュー・親の受入全走は別枠で、今回の所要は未実測。
