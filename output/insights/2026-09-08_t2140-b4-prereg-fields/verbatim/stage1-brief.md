# 段 1 brief — [T-2140] B-4 事前登録 §5 の残り欄と §10/§11 の記述矛盾訂正

対象文書: `docs/phase3-b4-reflux-ablation-preregistration.md` (worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2140-b4-prereg-fields`、base commit 240ee6360)。

## scope

1. §5 の未記入欄のうち floor 以外を、§5.1 の解除条件が**実際に充足されている欄だけ**埋める。
2. §10 [T-2398] と §11 [T-2424] の記述矛盾を追記で訂正する。
3. §11 の凍結 commit を作る (= 本 wave の記入 commit)。

scope 外: floor 行 ([T-2412]/[T-2423] 待ち)、新規 gate・検査・台帳・一般化の追加、
§5.1 と §5.1.1 の規範本文の変更、`docs/phase3-main-experiment.md` の bytes。

## 確定済みユーザー裁定・引数

- floor 行には手を付けない。規律 2 は緩めない。Codex author = D95。本題の実装だけ。
- 記入者 = レビュー者 = `thawk105` (D1266、D1638 の委任により AI が名義で操作する)。

## 親が段 1 で実測した事実 (引数の前提を一部覆す)

引数は「実走前に要る裁定 2 件が land 済みなので前提は解けている」とするが、その 2 件 (D1694 / D1695)
は floor 欄にだけ掛かる追記であり、他欄の解除条件を 1 つも解いていない (§5.1 floor 項の逐語が
「それでも本欄の解除条件は 1 つも緩まない」と自ら述べている)。欄ごとの実測は次のとおり。

|欄|§5.1 が要求するもの|実測した現在地|親の provisional 裁定|
|---|---|---|---|
|赤 precursor の母集合|`analysis_manifest` の path+sha256+行数、`scheduled_attempt_registry` の path+sha256 (**実体**。規則への参照だけでは不可)|生成器 `p3_b4_prerun_issuer.py` は在るが、実体は repo に 1 件も無い (find で 0 件)|**(P1) 埋めない**|
|primary outcome|adapter 実装 + §5.1.1 一致検査 consumer が実在し、その artifact path と sha256|`p3_b4_analysis_path.py:67 _SOURCE_CLOSURE_PATHS` の 5 member が実在。consumer は §5.1.1 の raw bytes を pin して live 挙動まで検査する。関連 test 51 件緑 (2026-09-08 実測)|**(P2) 5 member の path+sha256 で埋める**|
|校正済み `PerfConfig`|calibrator が決めた値へ差し替えるまで記入しない|`p3_s4_loop.py:1330 default_perf()` は未校正のまま (records=100_000/threads=4/extime=1/reps=2)。pegasus 側に registered calibration (threads=48, rr50, skew0.9) は在る|**(P3) 埋めない** (差し替えは実装面かつ他 campaign へ波及、scope 外)|
|総計測予算|arm 対称、失敗も消費、再試行禁止|数値の出所が repo に無い。§5.1.1 自身が「`n = 201` は総計測予算を超える見込みが高い」と書く|**(P4) 埋めない** (資源裁定はユーザー)|
|env_tag|driver・site・tag の 3 つ組を同じ site resolver から機械導出 + 環境契約の path/hash + 確認者|resolver 実在 (`p3_s4_loop.py:117 _SITE_ENV_TAGS`)。tag は site で `pegasus` / `linux-baremetal` に分岐し、**実走 site が未確定**|**(P5) 埋めない** (site 裁定が先)|
|model snapshot / prompt / projection|4 点 (宣言源・承認する人間・時点・不一致時の扱い) を別 commit で先に固定|§10 が「人間の指名を含むため AI が確定できない」と明記|**(P6) 埋めない**|
|開始時刻|timezone 付きの**予定**開始時刻|他欄が未了で実走できず、書けば虚偽の予定になる|**(P7) 埋めない**|

したがって本 wave が実際に埋められるのは **11 欄中 1 欄 (primary outcome)** である。
残り 6 欄は「解除条件が未充足」であり、これは段 4 でユーザーへ返す裁定パッケージになる。

## 不変条件 (破ったら停止)

- §5 の表は `p3_b4_admission_record.py:87 _SECTION5_LABELS` が exact 10 行 + header 2 行で機械検査する。
  行数・label・`|欄|値|` の書式を変えない。値セルに sentinel (`未記入` 等) を残す欄はそのまま残す。
- §5 の値セルへ説明文・条件・解除条件を書かない (§0)。規範は §5.1 と §7 だけが持つ。
- §5.1.1 の raw bytes は `p3_b4_analysis_prereg_consumer.py:47` が sha256 で pin する。
  「#### 5.1.1」の見出しから §6 直前までを 1 byte も変えない。
- §10 / §11 の訂正は**追記**で行い、既存の記述を削除・書き換えしない (§1 の「発効後の変更は旧版を
  git 履歴に残したまま新しい commit で行う」に倣う)。
- 規律 2: 正しさゲートを緩める変更をしない。欄を埋めることで実走前検査が通りやすくなる方向の
  緩和 (sentinel 回避目的の穴埋め) をしない。

## 成果物の形

- `docs/phase3-b4-reflux-ablation-preregistration.md` の 1 file 変更 (docs-only の見込み)。
- §5 の primary outcome 行 1 行の記入、§10 と §11 への追記各 1 か所。
- 段 7 で spool fragment (worklog / decisions)、段 9 で land。

## 分割方針

docs-only なら実装子は起動しない (親が編集)。段 2 で file:line 粒度の plan、
段 3 で敵対 2 レンズ。実装面 (コード・テスト) の差分が必要と判明した時点で Codex `role=author` へ回す。
