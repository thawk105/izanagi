// [T-155] write set 探索構造の crossover マイクロベンチ (単体・単一スレッド)
//
// 問い: CCBench silo の write_set_ 線形走査 (searchWriteSet) が、side index
// (hash / sorted / compact linear) に負ける set size の反転閾値 n* はどこか。
// 出口は selector-8b の workload descriptor 条件「set size > n* なら container
// 機構を候補化」の材料。本番 (external/ccbench) には一切触れない。
//
// layout の複製元 (2026-07-28、submodule gitlink 時点の実物から転写):
//   include/op_element.hh          OpElement<T>{storage_, key_, rcdptr_, op_}
//   cc/silo/include/silo_op_element.hh  WriteElement{body_, val_ptr_, val_length_}
//   include/tuple_body.hh          TupleBody{key_(std::string), val_(HeapObject)}
//   include/heap_object.hh         HeapObject{data_, size_, align_, owner_}
//   cc/silo/transaction.cc:342-350 searchWriteSet の線形走査 (verbatim)
//   include/ycsb.hh:129-133        write op = 4B payload heap 割当 + TupleBody 移動構築
// 実測済み事実 (login node probe): sizeof(WriteElement)=136、8B key は SSO 内、
// 走査が触るのは各要素の先頭 40B (storage_@0, key_@8..39)。
// static_assert で計測ノード上でも同一 layout を強制する (不一致 = コンパイル赤 = fail-closed)。

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <memory>
#include <new>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace {

// ---------- 忠実 layout 複製 ----------

enum class Storage : std::uint32_t { YCSB = 0 };
enum class OpType : std::uint8_t { NONE, READ, SCAN, INSERT, DELETE, UPDATE, RMW };

struct HeapObject {
  void* data_ = nullptr;
  std::size_t size_ = 0;
  std::align_val_t align_ = std::align_val_t(0);
  bool owner_ = false;

  HeapObject() = default;
  HeapObject(const HeapObject&) = delete;
  HeapObject& operator=(const HeapObject&) = delete;
  HeapObject(HeapObject&& rhs) noexcept { swap(rhs); }
  HeapObject& operator=(HeapObject&& rhs) noexcept {
    swap(rhs);
    return *this;
  }
  ~HeapObject() { reset(); }

  void swap(HeapObject& rhs) noexcept {
    std::swap(data_, rhs.data_);
    std::swap(size_, rhs.size_);
    std::swap(align_, rhs.align_);
    std::swap(owner_, rhs.owner_);
  }
  // ycsb.hh の write op 相当: allocate<YCSB>() = sizeof 4 / align 4 の heap 割当
  void allocate4() {
    data_ = ::operator new(4);
    size_ = 4;
    align_ = std::align_val_t(4);
    owner_ = true;
    std::memset(data_, 0, 4);
  }
  void reset() {
    if (owner_ && data_ != nullptr) ::operator delete(data_);
    data_ = nullptr;
    size_ = 0;
    owner_ = false;
  }
};

struct TupleBody {
  std::string key_;
  HeapObject val_;
  TupleBody() = default;
  TupleBody(std::string_view key, HeapObject&& val) : key_(key), val_(std::move(val)) {}
  TupleBody(TupleBody&&) = default;
  TupleBody& operator=(TupleBody&&) = default;
};

// rcdptr_ の指し先 (sizeof(Tuple)=128 実測)。中身は走査で触られない
struct TupleOpaque {
  unsigned char pad[128];
};

template <typename T>
struct OpElement {
  Storage storage_{};
  std::string key_;
  T* rcdptr_ = nullptr;
  OpType op_ = OpType::NONE;
};

template <typename T>
struct WriteElement : OpElement<T> {
  TupleBody body_;
  std::unique_ptr<char[]> val_ptr_;
  std::size_t val_length_ = 0;
};

using WE = WriteElement<TupleOpaque>;
static_assert(sizeof(std::string) == 32, "libstdc++ SSO layout premise");
static_assert(sizeof(OpElement<TupleOpaque>) == 56, "OpElement layout fidelity");
static_assert(sizeof(TupleBody) == 64, "TupleBody layout fidelity");
static_assert(sizeof(WE) == 136, "WriteElement layout fidelity");

// ---------- key (SimpleKey<8> 相当: u64 big-endian 8B) ----------

inline void encode_be(std::uint64_t v, char* out) {
  for (int i = 7; i >= 0; --i) {
    out[i] = static_cast<char>(v & 0xff);
    v >>= 8;
  }
}

// side index 用: 8B key bytes をそのまま u64 として載せる (等値判定のみに使用)
inline std::uint64_t load_raw(std::string_view key) {
  std::uint64_t v;
  std::memcpy(&v, key.data(), 8);
  return v;
}

// ---------- 候補 4 系 (要素本体 vector<WE> は全系共通 = 差分は探索構造のみ) ----------

TupleOpaque g_arena[256];

struct SetBase {
  std::vector<WE> ws;

  void emplace(Storage s, std::string_view key, std::size_t i) {
    HeapObject obj;
    obj.allocate4();
    WE we;
    we.storage_ = s;
    we.key_ = key;
    we.rcdptr_ = &g_arena[i & 255];
    we.op_ = OpType::UPDATE;
    we.body_ = TupleBody(key, std::move(obj));
    ws.push_back(std::move(we));
  }
};

// (L) 線形 verbatim: transaction.cc:342-350 と同一の走査・比較列
struct LinearSet : SetBase {
  static constexpr const char* name = "linear";
  WE* search(Storage s, std::string_view key) {
    for (auto& we : ws) {
      if (we.storage_ != s) continue;
      if (we.key_ == key) return &we;
    }
    return nullptr;
  }
  void insert(Storage s, std::string_view key, std::size_t i) { emplace(s, key, i); }
  void clear() { ws.clear(); }
};

// (H) hash side index: key u64 -> ws index
struct HashSet : SetBase {
  static constexpr const char* name = "hash_index";
  std::unordered_map<std::uint64_t, std::uint32_t> idx;
  WE* search(Storage s, std::string_view key) {
    auto it = idx.find(load_raw(key));
    if (it == idx.end()) return nullptr;
    WE* we = &ws[it->second];
    if (we->storage_ != s) return nullptr;
    return we;
  }
  void insert(Storage s, std::string_view key, std::size_t i) {
    emplace(s, key, i);
    idx.emplace(load_raw(key), static_cast<std::uint32_t>(ws.size() - 1));
  }
  void clear() {
    ws.clear();
    idx.clear();
  }
};

// (S) sorted side index: (key u64, ws index) を挿入ソート維持 + 二分探索
struct SortedSet : SetBase {
  static constexpr const char* name = "sorted_index";
  std::vector<std::pair<std::uint64_t, std::uint32_t>> idx;
  WE* search(Storage s, std::string_view key) {
    const std::uint64_t k = load_raw(key);
    auto it = std::lower_bound(
        idx.begin(), idx.end(), k,
        [](const std::pair<std::uint64_t, std::uint32_t>& e, std::uint64_t v) {
          return e.first < v;
        });
    if (it == idx.end() || it->first != k) return nullptr;
    WE* we = &ws[it->second];
    if (we->storage_ != s) return nullptr;
    return we;
  }
  void insert(Storage s, std::string_view key, std::size_t i) {
    emplace(s, key, i);
    const std::uint64_t k = load_raw(key);
    auto it = std::lower_bound(
        idx.begin(), idx.end(), k,
        [](const std::pair<std::uint64_t, std::uint32_t>& e, std::uint64_t v) {
          return e.first < v;
        });
    idx.insert(it, {k, static_cast<std::uint32_t>(ws.size() - 1)});
  }
  void clear() {
    ws.clear();
    idx.clear();
  }
};

// (C) compact linear side index: 12B entry の未ソート線形走査。
// 「fat 要素 (136B) の cache line 支配」と「線形走査というアルゴリズム」の寄与を分離する対照系
struct CompactLinearSet : SetBase {
  static constexpr const char* name = "compact_linear";
  std::vector<std::pair<std::uint64_t, std::uint32_t>> idx;
  WE* search(Storage s, std::string_view key) {
    const std::uint64_t k = load_raw(key);
    for (auto& e : idx) {
      if (e.first == k) {
        WE* we = &ws[e.second];
        if (we->storage_ != s) return nullptr;
        return we;
      }
    }
    return nullptr;
  }
  void insert(Storage s, std::string_view key, std::size_t i) {
    emplace(s, key, i);
    idx.push_back({load_raw(key), static_cast<std::uint32_t>(ws.size() - 1)});
  }
  void clear() {
    ws.clear();
    idx.clear();
  }
};

// ---------- 計測基盤 ----------

using Clock = std::chrono::steady_clock;

inline std::uint64_t now_ns() {
  return static_cast<std::uint64_t>(
      std::chrono::duration_cast<std::chrono::nanoseconds>(
          Clock::now().time_since_epoch())
          .count());
}

struct Rng {  // xorshift64*
  std::uint64_t s;
  explicit Rng(std::uint64_t seed) : s(seed ? seed : 0x9E3779B97F4A7C15ull) {}
  std::uint64_t next() {
    s ^= s >> 12;
    s ^= s << 25;
    s ^= s >> 27;
    return s * 0x2545F4914F6CDD1Dull;
  }
};

std::uint64_t g_sink = 0;

std::vector<char> g_pollute;  // 32 MiB。txn 間の cache 追い出し (untimed)

void pollute_walk() {
  std::uint64_t acc = 0;
  for (std::size_t i = 0; i < g_pollute.size(); i += 64) {
    acc += static_cast<unsigned char>(g_pollute[i]);
    g_pollute[i] = static_cast<char>(acc);
  }
  g_sink += acc;
}

// 1 txn: n 個の key を「miss 探索 -> 挿入」(searchWriteSet -> goto FINISH_WRITE 相当の
// 重複 skip 付き)。timed 区間は build + clear (index の clear コストは候補固有の実費)
template <class SetT>
std::uint64_t run_build_block(SetT& set, int n, int reps, std::uint64_t seed, bool pollute) {
  Rng rng(seed);
  char kb[8];
  std::uint64_t total = 0;
  for (int r = 0; r < reps; ++r) {
    const std::uint64_t t0 = now_ns();
    for (int i = 0; i < n; ++i) {
      encode_be(rng.next(), kb);
      std::string_view key(kb, 8);
      if (set.search(Storage::YCSB, key) != nullptr) continue;  // 重複は挿入 skip
      set.insert(Storage::YCSB, key, static_cast<std::size_t>(i));
    }
    g_sink += set.ws.size();
    set.clear();
    total += now_ns() - t0;
    if (pollute) pollute_walk();
  }
  return total;
}

// hit 経路: サイズ n の set を構築後 (untimed)、全 key を撹拌順で lookup する sweep を
// sweeps 回。read-own-write / RMW の再探索に相当
template <class SetT>
std::uint64_t run_hit_block(SetT& set, int n, int sweeps, std::uint64_t seed,
                            std::vector<std::string>& keys, std::vector<int>& order) {
  Rng rng(seed);
  keys.clear();
  set.clear();
  char kb[8];
  for (int i = 0; i < n; ++i) {
    encode_be(rng.next(), kb);
    keys.emplace_back(kb, 8);
    std::string_view key = keys.back();
    if (set.search(Storage::YCSB, key) == nullptr)
      set.insert(Storage::YCSB, key, static_cast<std::size_t>(i));
  }
  order.clear();
  for (int i = 0; i < n; ++i) order.push_back(i);
  for (int i = n - 1; i > 0; --i)
    std::swap(order[i], order[rng.next() % static_cast<std::uint64_t>(i + 1)]);

  const std::uint64_t t0 = now_ns();
  for (int sw = 0; sw < sweeps; ++sw) {
    for (int i = 0; i < n; ++i) {
      WE* we = set.search(Storage::YCSB, keys[static_cast<std::size_t>(order[i])]);
      g_sink += (we != nullptr);
    }
  }
  const std::uint64_t total = now_ns() - t0;
  set.clear();
  return total;
}

// ---------- self check (G01 生死確認: 4 系の意味論一致) ----------

template <class A, class B>
bool cross_check(A& a, B& b, int n, std::uint64_t seed) {
  a.clear();
  b.clear();
  Rng rng(seed);
  char kb[8];
  std::vector<std::string> keys;
  for (int i = 0; i < n * 2; ++i) {
    // 前半は新規 key、後半は既出 key の再 lookup (hit 経路) を混ぜる
    if (i < n) {
      encode_be(rng.next(), kb);
      keys.emplace_back(kb, 8);
    }
    const std::string& key = keys[static_cast<std::size_t>(i % n)];
    WE* ra = a.search(Storage::YCSB, key);
    WE* rb = b.search(Storage::YCSB, key);
    if ((ra == nullptr) != (rb == nullptr)) return false;
    if (ra != nullptr && rb != nullptr) {
      if (ra->key_ != rb->key_) return false;
      if (ra->body_.key_ != rb->body_.key_) return false;
    }
    if (ra == nullptr) {
      a.insert(Storage::YCSB, key, static_cast<std::size_t>(i));
      b.insert(Storage::YCSB, key, static_cast<std::size_t>(i));
    }
  }
  const bool size_ok = (a.ws.size() == b.ws.size());
  a.clear();
  b.clear();
  return size_ok;
}

bool self_check() {
  LinearSet l;
  HashSet h;
  SortedSet s;
  CompactLinearSet c;
  for (int n : {1, 2, 7, 33, 200}) {
    const std::uint64_t seed = 0xC0FFEEull + static_cast<std::uint64_t>(n);
    if (!cross_check(l, h, n, seed)) return false;
    if (!cross_check(l, s, n, seed)) return false;
    if (!cross_check(l, c, n, seed)) return false;
  }
  return true;
}

// ---------- sweep 本体 ----------

struct Cell {
  const char* cand;
  int n;
  int reps;
  std::vector<double> per_txn_ns;  // outer ごと
};

int reps_for(int n) {
  // 目標 ~30ms/block (linear の見積り per-txn ns ~= 0.75 n^2 + 45 n + 500)
  const double est = 0.75 * n * n + 45.0 * n + 500.0;
  const double r = 30e6 / est;
  return static_cast<int>(std::min(100000.0, std::max(200.0, r)));
}

template <class SetT>
void sweep_build(SetT& set, const std::vector<int>& ns, int outers, bool pollute,
                 std::vector<Cell>& out) {
  for (int n : ns) {
    Cell cell{SetT::name, n, 0, {}};
    int reps = reps_for(n);
    if (pollute) reps = std::max(30, reps / 200);  // walk (~1ms/txn, untimed) の分だけ絞る
    cell.reps = reps;
    for (int o = 0; o < outers; ++o) {
      const std::uint64_t seed =
          0xABCD1234ull ^ (static_cast<std::uint64_t>(n) << 32) ^ static_cast<std::uint64_t>(o);
      const std::uint64_t total = run_build_block(set, n, reps, seed, pollute);
      cell.per_txn_ns.push_back(static_cast<double>(total) / reps);
    }
    out.push_back(std::move(cell));
  }
}

template <class SetT>
void sweep_hit(SetT& set, const std::vector<int>& ns, int outers, std::vector<Cell>& out) {
  std::vector<std::string> keys;
  std::vector<int> order;
  for (int n : ns) {
    const int sweeps = std::max(50, static_cast<int>(2000000 / n));
    Cell cell{SetT::name, n, sweeps, {}};
    for (int o = 0; o < outers; ++o) {
      const std::uint64_t seed =
          0x5EED0000ull ^ (static_cast<std::uint64_t>(n) << 32) ^ static_cast<std::uint64_t>(o);
      const std::uint64_t total = run_hit_block(set, n, sweeps, seed, keys, order);
      cell.per_txn_ns.push_back(static_cast<double>(total) /
                                (static_cast<double>(sweeps) * n));  // ns/lookup
    }
    out.push_back(std::move(cell));
  }
}

double median(std::vector<double> v) {
  std::sort(v.begin(), v.end());
  const std::size_t m = v.size() / 2;
  return (v.size() % 2 != 0) ? v[m] : 0.5 * (v[m - 1] + v[m]);
}

void emit_cells(std::FILE* f, const char* section, const std::vector<Cell>& cells,
                bool* first_section) {
  if (!*first_section) std::fprintf(f, ",\n");
  *first_section = false;
  std::fprintf(f, "  \"%s\": [\n", section);
  for (std::size_t i = 0; i < cells.size(); ++i) {
    const Cell& c = cells[i];
    std::vector<double> v = c.per_txn_ns;
    std::fprintf(f, "    {\"cand\": \"%s\", \"n\": %d, \"reps\": %d, \"median_ns\": %.2f, "
                    "\"min_ns\": %.2f, \"outer_ns\": [",
                 c.cand, c.n, c.reps, median(v), *std::min_element(v.begin(), v.end()));
    for (std::size_t j = 0; j < v.size(); ++j)
      std::fprintf(f, "%s%.2f", j ? ", " : "", c.per_txn_ns[j]);
    std::fprintf(f, "]}%s\n", (i + 1 < cells.size()) ? "," : "");
  }
  std::fprintf(f, "  ]");
}

}  // namespace

int main(int argc, char** argv) {
  if (argc < 2) {
    std::fprintf(stderr, "usage: %s <out.json> [--selfcheck-only]\n", argv[0]);
    return 2;
  }
  const bool selfcheck_only = (argc >= 3 && std::string_view(argv[2]) == "--selfcheck-only");

  if (!self_check()) {
    std::fprintf(stderr, "SELFCHECK FAILED: candidates disagree\n");
    return 3;
  }
  std::fprintf(stdout, "selfcheck: pass\n");
  if (selfcheck_only) return 0;

  g_pollute.assign(32u << 20, 1);

  // timer overhead の実測 (差の解釈用)
  {
    std::uint64_t acc = 0;
    const std::uint64_t t0 = now_ns();
    for (int i = 0; i < 1000000; ++i) acc += now_ns() & 1;
    g_sink += acc;
    std::fprintf(stdout, "timer_pair_overhead_ns: %.2f\n", (now_ns() - t0) / 1e6);
  }

  const std::vector<int> ns_warm = {2, 5, 10, 15, 20, 30, 40, 60, 80, 100, 140, 200};
  const std::vector<int> ns_pol = {10, 30, 60, 100, 200};
  const int outers = 7;
  const int outers_pol = 5;

  LinearSet l;
  HashSet h;
  SortedSet s;
  CompactLinearSet c;

  std::vector<Cell> warm_build, hit, pol_build;
  // 候補間 interleave はブロック単位 (outer 内で全候補を回すとブロックが細り
  // timer 比率が上がるため、outer は候補ごとに連続で取り min/median で外乱を落とす)
  sweep_build(l, ns_warm, outers, false, warm_build);
  sweep_build(h, ns_warm, outers, false, warm_build);
  sweep_build(s, ns_warm, outers, false, warm_build);
  sweep_build(c, ns_warm, outers, false, warm_build);

  sweep_hit(l, ns_warm, outers, hit);
  sweep_hit(h, ns_warm, outers, hit);
  sweep_hit(s, ns_warm, outers, hit);
  sweep_hit(c, ns_warm, outers, hit);

  sweep_build(l, ns_pol, outers_pol, true, pol_build);
  sweep_build(h, ns_pol, outers_pol, true, pol_build);
  sweep_build(s, ns_pol, outers_pol, true, pol_build);
  sweep_build(c, ns_pol, outers_pol, true, pol_build);

  std::FILE* f = std::fopen(argv[1], "w");
  if (f == nullptr) {
    std::fprintf(stderr, "cannot open %s\n", argv[1]);
    return 2;
  }
  std::fprintf(f, "{\n");
  std::fprintf(f,
               "  \"meta\": {\"sizeof_write_element\": %zu, \"sizeof_op_element\": %zu, "
               "\"sizeof_tuple_body\": %zu, \"outers_warm\": %d, \"outers_polluted\": %d, "
               "\"pollute_mib\": 32, \"key_bytes\": 8, \"val_alloc_bytes\": 4}",
               sizeof(WE), sizeof(OpElement<TupleOpaque>), sizeof(TupleBody), outers,
               outers_pol);
  std::fprintf(f, ",\n");
  bool first2 = true;
  emit_cells(f, "warm_build_ns_per_txn", warm_build, &first2);
  emit_cells(f, "hit_ns_per_lookup", hit, &first2);
  emit_cells(f, "polluted_build_ns_per_txn", pol_build, &first2);
  std::fprintf(f, ",\n  \"sink\": %llu\n}\n", static_cast<unsigned long long>(g_sink));
  std::fclose(f);
  std::fprintf(stdout, "done\n");
  return 0;
}
