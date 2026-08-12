---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-login-unreclaimable
seq: 1
---

## 再発

### F217

- **再発: 2026-08-13** — 段 3 の敵対 2 レンズが**両方とも** web 検索を使い、
  `codex_exit_code=0` / 各 13,969 bytes・14,007 bytes の成果物 / 34 model call / 各 917 秒で
  完走したのに `evidence_status=invalid` / `accepted=false` になり、`-o` はゼロだった。
  2 レンズ分で約 30 分・約 750 万 token を失った。これで **3 度目**である。
  **一次原因は親の prompt 設計**で、運用レンズへ「実機の cgroup v2 で `file_dirty` が欠ける環境は
  存在するのか (kernel version・コンテナ等)」という**外部事実を問う設問**を置いたため子が
  素直に調べに行った。再走では検索禁止を明記し、当該設問を「この機械の `/sys/fs/cgroup` を
  実際に読んで確認し、それ以外は自分の知識の範囲で答え、不確かなら不確かと書け」へ書き換えて
  2 本とも成功した (rc=0、`check_codex_output` rc=0)。
- **恒久対応は依然として機械強制されていない (2026-08-11 の記述を追認)。** 本 wave の段 8 で
  `DW-O05` へ 2 行 (214 bytes) を足そうとしたが、`docs/dev-wave/**` の L1.5 unique footprint が
  9,780 bytes となり予算 9,566 bytes を超えて `check_docs` が赤になったため**編集を撤回した**。
  2026-08-11 の再発時は約 90 bytes でも赤だったと記録されており、**予算の余地は現在もゼロ**である。
  予算を上げる変更は通常の自己改善に含めないため、**裁定パッケージへ回す**
  (選択肢: L1.5 の圧縮で枠を作る / `tools/dev_wave_codex.py` が prompt に禁止文言が無ければ
  起動を拒む機械強制にする / memory + 本エントリのままとする)。
- **新しい情報**: 本 F の発火点は「子が勝手に検索する」だけでなく**親が外部事実を問う設問を
  書いた瞬間**にある。禁止文言の明記と同時に、設問を実機と repo で確かめられる形に保つことが要る。
