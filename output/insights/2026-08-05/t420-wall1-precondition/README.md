# [T-420] 壁 1 の着手条件は成立していない — 実測と裁定パッケージ (2026-08-05)

- `authority: none`
- `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` の該当エントリであり、本ファイルは一次資料を凍結する。

anchor = `a1265453` (local main)、branch = `worktree-dev-wave-t420-wall1-driver`

## 何を問うたか

[T-420] の next-move 本文 (worklog entry (160)、2026-08-04 執筆) はこう書かれていた。

> attestation の裁定が付いた後、`output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/`
> の使い捨て driver をそのまま再走させ、build → verify → bench が計算ノードで 1 周通るかを確かめる。
> 追加実装は要らない。通れば壁 1 の生死確認が初めて完了する。

attestation の裁定は entry (208) で付いた ([T-419] R-0 追認 + R-1 = 方式 α)。
そこで DW-S01 に従い「そのまま再走させれば通る」という前提を実測した。

## 判定

**着手条件は成立していない。** 付いたのは*方式の選択*であって、その方式で取り直した較正は
まだ存在しない。現行 probe 方式のままでは attestation は通らず、driver を再走させても
2026-08-04 と同一地点で落ちる。

**ただし阻んでいるものは「登録済み較正の自己不整合」ではない。** 親は段 1 でそう述べたが、
敵対検証で誤りと判明した。真の阻害要因は **probe の観測者効果**である (§機序)。

## 実測 1 — 述語は expected の外れ値を検査しない (親の当初主張の反証)

`campaign.execution_guard.effective_clock_comparison_passes` は、expected の**中央値**から
帯を作り、**observed の全標本**が帯内かだけを検査する
(`orchestrator/campaign/execution_guard.py` の `_effective_clock_band_math_passes`)。
expected 側の外れ値は帯の中心 (中央値) を動かさないかぎり無害である。

実行時と同じ射影 (`{samples_mhz, tolerance_pct}` のちょうど 2 key) で測った結果:

| # | observed | 結果 |
|---|---|---|
| A | 登録済み較正の標本をそのまま observed とする (自己受理) | **False** |
| B | 48 標本すべて 2101.0 (静穏な機械) | **True** |
| C | 47 標本 2101.0 + 1 標本 3076.13 (1 コアがブースト) | **False** |

- 帯 = [2058.98, 2143.02] (median 2101.0、tolerance_pct 2.0)。
- 登録済み artifact の標本は 47 個が 2101.0、1 個が 3080.935。

**B が True であることが決定的である。** gate は構造的に壊れてはいない。静穏な機械なら
現在の登録済み較正のままでも受理される。したがって「較正が自己不整合だから必敗」は**誤り**である。

### 親の当初測定が誤っていた理由 (記録として残す)

親は段 1 で `effective_clock` mapping を**そのまま** expected として渡した。しかしこの mapping は
`governor` / `method` を含む 4 key を持ち、述語は expected に
`{samples_mhz, tolerance_pct}` の**ちょうど 2 key** を要求する。よって親の 3 回の測定はすべて
**値ではなく形で** False を返していた。実行時の射影 (`env_attestation._clock_value`) を通して
測り直して初めて A/B/C が分離した。**形の検査と値の検査を分離せずに測ると、gate が
「必ず落ちる」ように見える。**

## 実測 2 — 真の機序は probe の観測者効果

production probe は `/proc/cpuinfo` の `cpu MHz` を全 CPU 分読んで observed 列を作る
(`orchestrator/campaign/env_attestation.py` の `probe`)。[T-419] の実機因果実験が確定させた事実:

| 事前登録条件 | 実測 |
|---|---|
| `pinned_hit_rate` (走行 CPU が帯外になる率) | **1.0 (240/240)** |
| `nonpinned_out_of_band_rate` | 8.87e-05 (1/11,280) |
| paired contrast が正の CPU 数 | 48/48 |

さらに機序の精密化 — 同じコアに **sleep する子 (sham)** と **spin する子 (busy)** を置き分けると:

| 条件 | 対象 CPU が帯外 |
|---|---|
| sham (sleep) | **0/40** |
| busy (spin) | **40/40** |

つまり帯外化の原因は「そのコアがその瞬間 busy であること」であり、
**probe の走行 CPU は定義上必ず busy なので、必ず 1 個以上の帯外標本が出る。**

一次資料 = `output/insights/2026-08-04_t419-probe-causality/README.md`

**これが実測 1 の C の状況であり、2026-08-04 の失敗そのものである** (当時の observed idx 34 =
3076.13 が帯外)。すなわち落ちた原因は observed 側であって expected 側ではない。

## 実測 3 — 較正は contract に hash pin されている

`orchestrator/campaign/execution_guard.py` の `attest_and_build_receipt` が
`verified_calibration.sha256 != contract.calibration_ref.sha256` を拒否し、
loader も contract の path を解決して bytes の SHA-256 が pin と一致することを要求する
(`orchestrator/campaign/env_attestation.py` の `load_verified_calibration`)。
registry は静的で register API を持たず、D125 は「環境変数 override を作らない」を明記する。
さらに `run_campaign` は Pegasus compute では登録済み pegasus 契約との完全一致を要求する
(`orchestrator/campaign/loop.py` の `_authorize_measurement`)。

**防壁を緩めずに別の較正へ向ける production seam は存在しない** (敵対検証も同結論)。

## 実測 4 — 登録段の自己整合 gate は現行 artifact を「既知例外」として pin している

`9bffa06a` (`[T-419]` 較正は自分自身の実行時述語を通るときだけ登録できるようにする) は publish
経路に自己整合 gate を置き、加えて registry が参照する全 calibration を走査して
**自己整合を満たさない entry の集合が既知例外 1 件と厳密に一致すること**を検査する。
commit message は「既知例外が直ったときにもテストは赤くなるため、**将来の probe 是正 wave が
pin の反転を強制される**」と述べる。system 自身が是正 wave を待っている。

なお実測 1 の A が False であること自体は事実であり、この既知例外の中身である。
ただし §実測 1 のとおり、それは実行時の失敗原因ではない。

## 実測 5 — [T-422] / F98 はもう blocker ではない

`IZANAGI_EXPLORATION_OUTPUT_ROOT` が landed している。campaign を実走した wave が正規経路で
land できない問題は解消済みで、[T-420] の障害ではない。障害は attestation ただ 1 点に絞られた。

## 実測 6 — 本日 land した裁定が独立に同じ運用結論を与えた

本 wave の作業中に `782e242d` が land した。

- **[T-506]**: canonical 述語 self-pass は [T-419] U-2 wave に同梱。
  **「それまでは『再較正まで certified campaign を開かない』の運用宣言を維持する」**
- **[T-507]**: T126 attestation の到達不能な成功経路の修正も、実施は較正チェーン (U-2) 後。

## 帰結 — 通す道

| 案 | 内容 | 可否 |
|---|---|---|
| (a) | attestation gate を緩める / 環境タグを偽装する | **不可。規律 2 違反** |
| (b) | 方式 α で較正を取り直し、再登録し、pin を更新する | **U-2 の所有作業** |

(208) 裁定は U-2 を [T-478] と [T-452]+[T-453] の後に置き、**「受理集合・凍結 bytes・pin は
方式実装 wave まで不変」**と明記した。[T-506]/[T-507] も U-2 に積まれている。
本 wave が (b) を先取りすれば裁定順序に反する。

**したがって [T-420] は U-2 着地後に初めて着手できる。** それまで計算ノードジョブを投げても
attestation で落ちるだけで、壁 1 の答えは得られない。

## 敵対検証

中核主張「今日 build へ到達できる sanctioned 経路は無い」を独立 codex に read-only で反証させた
(`check_codex_output.py` rc=0)。判定は **partially-refuted**。親の裁定は以下のとおり。

逐語と prompt は本 insight 配下へ凍結した (F20 — セッションを跨ぐ成果物を repo 外にだけ置かない)。

- `evidence/adversarial-refutation.md` — 子の出力全文
- `evidence/adversarial-refutation.prompt.txt` — 投入した prompt 全文

| # | 所見 | 裁定 |
|---|---|---|
| 1 | 述語は expected の外れ値を検査せず、observed が全て帯内なら現登録較正でも受理される | **real・採用**。親の因果説明を撤回し §実測 1 に置き換えた。親が自分で再測して確認 (B = True) |
| 2 | `env_contract=None` の legacy driver は attestation を素通りし、Pegasus 実行を `linux-baremetal` と記録しうる | **real・scope 外**。ただし **[T-331] が既に裁定済み (択 (a)) で実装待ち**。重複起票せず、機序確認の記録だけ残す |
| 3 | exploration lane の型分離だけでは proof chain 非流入を保証できない (`artifact_admission` が文字列 path を `CampaignLayout` に包み直す) | **real・採用**。下記 軸 2 の必須条件に反映した |
| 4 | 「Pegasus 全ノードで物理的に絶対不可能」は未証明 (外的妥当性は bnode138 の構成に限定) | **real・採用**。本書は「必ず落ちる」ではなく「現行 probe 方式では should-pass が実質 0」と書く |
| 5 | sanctioned な別手段は今日は無い | **confirmed**。親の結論と一致 |

所見 2 の裏取り: `orchestrator/campaign/loop.py` の `_authorize_measurement` は
`env_contract is None` で即 `return None` し、attestation を一切行わない。
D125 は兄弟 driver / legacy caller の COMPUTE 拒否を「実装して撤去した」と記録し、
防壁を通らない legacy driver がさらに 7 本残ることを明記している。[T-331] の射程内である。

所見 3 の裏取り: `ExplorationCampaignLayout` は「official CampaignLayout と継承関係を持たない」と
宣言されているが、`artifact_admission._layout` は `str | Path` を受けて
`CampaignLayout(root=...)` に包み直す。**型分離は文字列 path 経由で迂回できる。**

## この wave が変えていないもの

attestation 述語、`execution_guard`、contract の pin、登録済み較正の bytes、受理集合、
使い捨て driver の 3 ファイル、`pipeline.py` の numactl gate。いずれも未変更である。
**正しさゲートは 1 つも緩めていない。** 実装差分が無いため変異 matrix と受入全走は対象外である。

## ユーザーへ返す設計軸

### 軸 1 — 壁 1 の生死確認をいつ行うか

- **推奨 = (i) U-2 後まで送る。** [T-420] を U-2 の下流として明示的に繋ぎ直す
  (本 wave の next-move 是正がこれに当たる)。
- (ii) U-2 を待たず本 wave で較正を取り直す → (208)/[T-506]/[T-507] の裁定順序に反する。
- (iii) 本文を現状のまま残す → 次のセッションが同じ誤読で計算ノードジョブを投げ、
  attestation で落ちて終わる。

### 軸 2 — 非認証 transport probe lane を設けるか

壁 1 が問うているのは *transport* (build → verify → bench が 1 周繋がるか) であって*認証*ではない。
しかし現状その死活確認は attestation の背後にあり、較正チェーンが直るまで観測できない。
そこで **gate を緩めるのではなく lane を分ける**案を返す。

**敵対検証で判明した必須条件:** 型分離 (`ExplorationCampaignLayout`) だけでは足りない。
`artifact_admission` が文字列 path を official layout へ包み直せるため、
**consumer / admission 側で exploration marker を明示的に拒否する防壁**が要る。
これが設計できなければ採るべきでない。

- 利点: 較正チェーンの完成を待たずに壁 1 の transport 側を潰せる。U-2 着地時に残る未知が
  較正だけになる。
- 危険: 「認証を通らない実行経路」を 1 本増やすこと自体が攻撃面である。しかも
  §敵対検証 所見 2 のとおり、**同型の無防壁経路は既に 7 本存在し [T-331] で閉じ待ちである。**
  閉じる前に新しい lane を足すのは順序が逆になりうる。
- **親の推奨 = 設計として起票するが本 wave では実装しない。** DW-G01 が「確認前の専用機構構築」を
  却下する。

### 軸 3 — 使い捨て driver を恒久機構化するか

依頼引数は「使い捨て driver を正規経路へ」であった。**親の推奨 = 現時点では却下。**
壁 1 の生死確認が一度も成功していない段階で driver を恒久機構化するのは、DW-G01 が明示的に
却下する「確認前の専用機構構築」である。生死確認が通ってから、通った構成を正規化するのが順序である。
