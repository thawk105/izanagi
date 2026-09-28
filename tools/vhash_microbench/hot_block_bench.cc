#include <immintrin.h>
#include <time.h>
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <random>
#include <regex>
#include <stdexcept>
#include <string>
#include <vector>

enum State : uint8_t { PENDING, ABORTED, COMMITTED, DELETED };
enum Kind : uint8_t { NOT_FOUND, WAIT, FOUND, REMOVED };
struct Version { uint64_t wts; State state; uint64_t id; const uint8_t* value; };
struct Result { Kind kind; uint64_t id; const uint8_t* value;
  bool operator==(const Result& x) const { return kind == x.kind && id == x.id; }
};
struct alignas(64) Node { Version v; Node* next = nullptr; };
static constexpr size_t NODE_HEADER_BYTES = offsetof(Node, next) + sizeof(Node*);
static_assert(NODE_HEADER_BYTES == 40);
static size_t round_up(size_t n,size_t align) { return (n+align-1)&~(align-1); }
static size_t node_stride(size_t bytes, bool inlined) {
  return round_up(NODE_HEADER_BYTES + (inlined ? bytes : 0), 64);
}
static uint8_t* node_inline(Node* node) {
  return reinterpret_cast<uint8_t*>(node) + NODE_HEADER_BYTES;
}
using AlignedBytes = std::unique_ptr<uint8_t,decltype(&std::free)>;
struct SoA {
  const uint64_t* wts = nullptr;
  const uint64_t* ids = nullptr;
  const uint8_t* states = nullptr;
  const uint8_t* const* values = nullptr;
  size_t count = 0;
  Node* const* cold_slot = nullptr;
};
struct Layout {
  AlignedBytes nodes{nullptr,&std::free};
  std::vector<uint8_t> block;
  std::vector<uint64_t> times, ids;
  std::vector<uint8_t> states;
  std::vector<const uint8_t*> refs;
  Node* first = nullptr;
  std::unique_ptr<Node*> cold_head = std::make_unique<Node*>(nullptr);
  SoA soa;
  std::vector<std::vector<uint8_t>> payload;
  std::vector<uint8_t> inline_payload;
  std::vector<Version> original;
};

static Result decide(const Version& v) {
  switch (v.state) {
    case PENDING: return {WAIT, 0, nullptr};
    case COMMITTED: return {FOUND, v.id, v.value};
    case DELETED: return {REMOVED, v.id, nullptr};
    case ABORTED: break;
  }
  return {NOT_FOUND, 0, nullptr};
}
static Result reference(const std::vector<Version>& a, uint64_t ts) {
  for (const auto& v : a) {
    if (v.wts > ts || v.state == ABORTED) continue;
    return decide(v);
  }
  return {NOT_FOUND, 0, nullptr};
}
extern "C" __attribute__((noinline)) Result select_linked_scattered(Node* p, uint64_t ts) {
  for (; p; p = p->next) {
    if (p->v.wts > ts || p->v.state == ABORTED) continue;
    return decide(p->v);
  }
  return {NOT_FOUND, 0, nullptr};
}
extern "C" __attribute__((noinline)) Result select_linked_local(Node* p, uint64_t ts) {
  return select_linked_scattered(p, ts);
}
static Result cold_select(Node* p, uint64_t ts) {
  return select_linked_scattered(p, ts);
}
extern "C" __attribute__((noinline)) Result select_contig_scalar(const SoA& a, uint64_t ts) {
  for (size_t i = 0; i < a.count; ++i) {
    if (a.wts[i] > ts || a.states[i] == ABORTED) continue;
    return decide({a.wts[i], static_cast<State>(a.states[i]), a.ids[i], a.values[i]});
  }
  return cold_select(*a.cold_slot, ts);
}
extern "C" __attribute__((noinline)) Result select_contig_simd(const SoA& a, uint64_t ts) {
  const __m256i sign = _mm256_set1_epi64x(static_cast<int64_t>(0x8000000000000000ULL));
  const __m256i target = _mm256_set1_epi64x(static_cast<int64_t>(ts ^ 0x8000000000000000ULL));
  for (size_t base = 0; base < a.count; base += 4) {
    const size_t count = std::min<size_t>(4, a.count - base);
    const __m256i data = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(a.wts + base));
    const __m256i gt = _mm256_cmpgt_epi64(_mm256_xor_si256(data, sign), target);
    unsigned mask = (static_cast<unsigned>(_mm256_movemask_pd(_mm256_castsi256_pd(gt))) ^ 15U) & ((1U << count) - 1U);
    while (mask) {
      const unsigned lane = static_cast<unsigned>(__builtin_ctz(mask));
      mask &= mask - 1U;
      const size_t i = base + lane;
      if (a.states[i] == ABORTED) continue;
      return decide({a.wts[i], static_cast<State>(a.states[i]), a.ids[i], a.values[i]});
    }
  }
  return cold_select(*a.cold_slot, ts);
}

static Layout make_layout(std::vector<Version> versions, size_t k, bool scattered, size_t value_bytes = 0, bool inline_values = false) {
  Layout out;
  if (inline_values) out.inline_payload.resize(versions.size() * value_bytes);
  else out.payload.resize(versions.size());
  for (size_t i = 0; i < versions.size(); ++i) {
    const uint8_t content = static_cast<uint8_t>((versions[i].id * 17 + i) & 255);
    if (inline_values) {
      std::fill(out.inline_payload.begin() + i * value_bytes,
                out.inline_payload.begin() + (i + 1) * value_bytes, content);
      versions[i].value = out.inline_payload.data() + i * value_bytes;
    } else {
      out.payload[i].assign(value_bytes, content);
      versions[i].value = out.payload[i].data();
    }
  }
  out.original = versions;
  const size_t hot = std::min(k, versions.size());
  const size_t padded = (hot + 3) & ~size_t(3);
  out.times.assign(padded, UINT64_MAX);
  out.states.resize(padded);
  out.ids.resize(padded);
  out.refs.resize(padded);
  for (size_t i = 0; i < hot; ++i) {
    out.times[i] = versions[i].wts;
    out.states[i] = versions[i].state;
    out.ids[i] = versions[i].id;
    out.refs[i] = versions[i].value;
  }
  out.soa = {out.times.data(),out.ids.data(),out.states.data(),out.refs.data(),hot,nullptr};
  std::vector<size_t> order(versions.size());
  for (size_t i = 0; i < order.size(); ++i) order[i] = i;
  if (scattered) std::shuffle(order.begin(), order.end(), std::mt19937_64(0x51caDAULL));
  std::vector<Node*> by_index(versions.size());
  const size_t stride=node_stride(value_bytes,inline_values);
  out.nodes.reset(static_cast<uint8_t*>(std::aligned_alloc(64,std::max<size_t>(64,stride*versions.size()))));
  if (!out.nodes) throw std::bad_alloc();
  size_t slot = 0;
  for (size_t i : order) {
    by_index[i] = new(out.nodes.get() + (scattered ? slot++ : i)*stride) Node();
    by_index[i]->v = versions[i];
  }
  for (size_t i = 0; i < versions.size(); ++i)
    by_index[i]->next = i + 1 < versions.size() ? by_index[i + 1] : nullptr;
  out.first = versions.empty() ? nullptr : by_index[0];
  *out.cold_head = hot < versions.size() ? by_index[hot] : nullptr;
  out.soa.cold_slot = out.cold_head.get();
  return out;
}

struct WriteSet {
  WriteSet() = default;
  WriteSet(const WriteSet&) = delete;
  WriteSet& operator=(const WriteSet&) = delete;
  WriteSet(WriteSet&&) noexcept = default;
  WriteSet& operator=(WriteSet&&) noexcept = default;
  struct Arena {
    std::unique_ptr<uint8_t,decltype(&std::free)> memory{nullptr,&std::free};
    size_t capacity=0,offset=0;
    explicit Arena(size_t bytes):capacity((bytes+63U)&~size_t(63)) {
      memory.reset(static_cast<uint8_t*>(std::aligned_alloc(64,capacity)));
      if (!memory) throw std::bad_alloc();
    }
    void* allocate(size_t bytes,size_t alignment) {
      const size_t pos=(offset+alignment-1)&~(alignment-1);
      if (pos+bytes>capacity) throw std::runtime_error("write arena exhausted");
      offset=pos+bytes;
      return memory.get()+pos;
    }
  };
  std::unique_ptr<Arena> arena;
  AlignedBytes node_pool{nullptr,&std::free};
  size_t node_slot = 0;
  size_t node_capacity = 0;
  Version* hot=nullptr;
  size_t k=0;
  Node* cold_head = nullptr;
  Node* linked_head = nullptr;
  size_t head = 0;
  size_t value_bytes = 0;
  bool inline_value = false;
  uint8_t* hot_payload=nullptr;
};
static constexpr size_t WRITE_SLOTS=32768;
static size_t write_arena_capacity(size_t k,size_t bytes,bool inlined,const std::string& arm,size_t slots=WRITE_SLOTS) {
  const size_t count=k+3;
  const bool linked=arm=="linked_prepend";
  const size_t initial=(linked?0:k*sizeof(Version)+7+(inlined?k*bytes:0))+
                       (inlined?0:count*bytes);
  const size_t per_insert=(arm=="block"?k*sizeof(Version)+7+(inlined?k*bytes:0):0)+
      (inlined?0:bytes);
  return round_up(std::max<size_t>(64,initial+slots*per_insert),64);
}
static size_t write_capacity(size_t k,size_t bytes,bool inlined,const std::string& arm,size_t slots=WRITE_SLOTS) {
  const size_t initial_nodes=arm=="linked_prepend"?k+3:3;
  return write_arena_capacity(k,bytes,inlined,arm,slots)+
         (slots+initial_nodes)*node_stride(bytes,inlined);
}
static void prepend_node(WriteSet& a, Node*& head, Version v) {
  if (a.node_slot>=a.node_capacity) throw std::runtime_error("write node pool exhausted");
  auto* node=new(a.node_pool.get()+a.node_slot++*node_stride(a.value_bytes,a.inline_value)) Node();
  node->v=v;
  node->next=head;
  head=node;
}
static void save_overflow(WriteSet& a, size_t tail) {
  if (!a.inline_value) return;
  const uint8_t* begin = a.hot_payload + tail * a.value_bytes;
  std::memcpy(node_inline(a.cold_head), begin, a.value_bytes);
  a.cold_head->v.value=node_inline(a.cold_head);
}
extern "C" __attribute__((noinline)) void insert_shift(WriteSet& a, Version v) {
  prepend_node(a,a.cold_head,a.hot[a.k-1]);
  save_overflow(a,a.k-1);
  for (size_t i=a.k-1;i>0;--i) a.hot[i]=a.hot[i-1];
  a.hot[0] = v;
  if (a.inline_value) {
    std::memmove(a.hot_payload+a.value_bytes,a.hot_payload,(a.k-1)*a.value_bytes);
    std::memcpy(a.hot_payload,v.value,a.value_bytes);
    for (size_t i=0;i<a.k;++i) a.hot[i].value=a.hot_payload+i*a.value_bytes;
  }
}
extern "C" __attribute__((noinline)) void insert_ring(WriteSet& a, Version v) {
  const size_t tail=(a.head+a.k-1)%a.k;
  prepend_node(a,a.cold_head,a.hot[tail]);
  save_overflow(a, tail);
  a.head = tail;
  a.hot[a.head] = v;
  if (a.inline_value) {
    std::memcpy(a.hot_payload+a.head*a.value_bytes,v.value,a.value_bytes);
    a.hot[a.head].value=a.hot_payload+a.head*a.value_bytes;
  }
}
extern "C" __attribute__((noinline)) void insert_block(WriteSet& a, Version v) {
  prepend_node(a,a.cold_head,a.hot[a.k-1]);
  save_overflow(a,a.k-1);
  auto* next=static_cast<Version*>(a.arena->allocate(a.k*sizeof(Version),alignof(Version)));
  next[0] = v;
  std::copy(a.hot,a.hot+a.k-1,next+1);
  if (a.inline_value) {
    auto* next_payload=static_cast<uint8_t*>(a.arena->allocate(a.k*a.value_bytes,1));
    std::memcpy(next_payload,v.value,a.value_bytes);
    std::memcpy(next_payload+a.value_bytes,a.hot_payload,(a.k-1)*a.value_bytes);
    a.hot_payload=next_payload;
  }
  a.hot=next;
  if (a.inline_value)
    for (size_t i=0;i<a.k;++i) a.hot[i].value=a.hot_payload+i*a.value_bytes;
}
extern "C" __attribute__((noinline)) void insert_linked_prepend(WriteSet& a, Version v) {
  prepend_node(a,a.linked_head,v);
  if (a.inline_value) {
    std::memcpy(node_inline(a.linked_head),v.value,a.value_bytes);
    a.linked_head->v.value=node_inline(a.linked_head);
  }
}
static std::vector<uint64_t> ids(const WriteSet& a, const std::string& arm) {
  std::vector<uint64_t> out;
  if (arm == "linked_prepend") {
    for (Node* p = a.linked_head; p; p = p->next) out.push_back(p->v.id);
  } else {
    for (size_t i = 0; i < a.k; ++i) out.push_back(a.hot[(a.head + i) % a.k].id);
    for (Node* p = a.cold_head; p; p = p->next) out.push_back(p->v.id);
  }
  return out;
}
static std::vector<std::pair<uint64_t,std::vector<uint8_t>>> values(const WriteSet& a,const std::string& arm) {
  std::vector<std::pair<uint64_t,std::vector<uint8_t>>> out;
  auto append=[&](const Version& v) {
    out.push_back({v.id,a.value_bytes?std::vector<uint8_t>(v.value,v.value+a.value_bytes):std::vector<uint8_t>()});
  };
  if (arm=="linked_prepend") {
    for (Node* p=a.linked_head;p;p=p->next) append(p->v);
  } else {
    for (size_t i=0;i<a.k;++i) append(a.hot[(a.head+i)%a.k]);
    for (Node* p=a.cold_head;p;p=p->next) append(p->v);
  }
  return out;
}
static WriteSet write_initial(size_t k, size_t bytes = 0, bool inline_value = false,
                              const std::string& arm = "block",size_t slots=WRITE_SLOTS) {
  WriteSet a;
  a.k=k;
  a.value_bytes = bytes;
  a.inline_value = inline_value;
  a.arena=std::make_unique<WriteSet::Arena>(write_arena_capacity(k,bytes,inline_value,arm,slots));
  const size_t initial_nodes=arm=="linked_prepend"?k+3:3;
  a.node_capacity=slots+initial_nodes;
  a.node_pool.reset(static_cast<uint8_t*>(std::aligned_alloc(
      64,a.node_capacity*node_stride(bytes,inline_value))));
  if (!a.node_pool) throw std::bad_alloc();
  const bool linked=arm=="linked_prepend";
  if (!linked) {
    a.hot=static_cast<Version*>(a.arena->allocate(k*sizeof(Version),alignof(Version)));
    if (inline_value) a.hot_payload=static_cast<uint8_t*>(a.arena->allocate(k*bytes,1));
  }
  for (size_t i = k + 3; i-- > 0;) {
    Version v{1000 - i, COMMITTED, 1000 - i, nullptr};
    if (linked) prepend_node(a,a.linked_head,v);
    else if (i >= k) prepend_node(a,a.cold_head,v);
  }
  if (!linked)
    for (size_t i = 0; i < k; ++i) a.hot[i]={1000-i,COMMITTED,1000-i,nullptr};
  for (size_t i=0;i<k+3;++i) {
    const uint8_t content=static_cast<uint8_t>((i*7+3)&255);
    if (!inline_value) {
      auto* value=static_cast<uint8_t*>(a.arena->allocate(bytes,1));
      std::memset(value,content,bytes);
      if (linked) {
        Node* node=a.linked_head;
        for (size_t j=0;j<i;++j) node=node->next;
        node->v.value=value;
      } else if (i<k) a.hot[i].value=value;
      else {
        Node* cold=a.cold_head;
        for (size_t j=k;j<i;++j) cold=cold->next;
        cold->v.value=value;
      }
    } else {
      if (linked) {
        Node* node=a.linked_head;
        for (size_t j=0;j<i;++j) node=node->next;
        std::memset(node_inline(node),content,bytes);
        node->v.value=node_inline(node);
      } else if (i<k) {
        std::memset(a.hot_payload+i*bytes,content,bytes);
        a.hot[i].value=a.hot_payload+i*bytes;
      } else {
        Node* cold=a.cold_head;
        for (size_t j=k;j<i;++j) cold=cold->next;
        std::memset(node_inline(cold),content,bytes);
        cold->v.value=node_inline(cold);
      }
    }
  }
  return a;
}
static void insert(WriteSet& a, const std::string& arm, Version v) {
  if (!a.inline_value && a.value_bytes) {
    auto* owned=static_cast<uint8_t*>(a.arena->allocate(a.value_bytes,1));
    std::memcpy(owned,v.value,a.value_bytes);
    v.value=owned;
  }
  if (arm == "shift") insert_shift(a, v);
  else if (arm == "ring") insert_ring(a, v);
  else if (arm == "block") insert_block(a, v);
  else if (arm == "linked_prepend") insert_linked_prepend(a, v);
  else throw std::runtime_error("unknown arm");
}
static Result select(const Layout& a, const std::string& arm, uint64_t ts) {
  if (arm == "linked_scattered") return select_linked_scattered(a.first, ts);
  if (arm == "linked_local") return select_linked_local(a.first, ts);
  if (arm == "contig_scalar") return select_contig_scalar(a.soa, ts);
  if (arm == "contig_simd") return select_contig_simd(a.soa, ts);
  throw std::runtime_error("unknown arm");
}
static const std::array<std::string, 4> read_arms = {"linked_scattered", "linked_local", "contig_scalar", "contig_simd"};
static const std::array<std::string, 4> write_arms = {"shift", "ring", "block", "linked_prepend"};
static uint64_t field(const std::string& s,const std::string& name,uint64_t fallback) {
  std::smatch m;
  if (std::regex_search(s,m,std::regex("\\\""+name+"\\\"\\s*:\\s*([0-9]+)"))) return std::stoull(m[1]);
  return fallback;
}
static std::string strfield(const std::string& s,const std::string& name,const std::string& fallback) {
  std::smatch m;
  if (std::regex_search(s,m,std::regex("\\\""+name+"\\\"\\s*:\\s*\\\"([^\\\"]*)\\\""))) return m[1];
  return fallback;
}
static uint64_t now_ns() {
  timespec t{}; clock_gettime(CLOCK_MONOTONIC_RAW,&t);
  return static_cast<uint64_t>(t.tv_sec)*1000000000ULL+t.tv_nsec;
}
static void perf_command(const std::string& control,const std::string& ack,const char* command) {
  if (control.empty()) return;
  std::ofstream out(control); out << command << '\n'; out.flush();
  std::ifstream in(ack); std::string line; std::getline(in,line);
  if (!out || !in || line.find("ack") == std::string::npos) throw std::runtime_error("perf control ack failed");
}
static size_t version_count(size_t k,size_t depth) { return std::max(k+4,depth+2); }
static size_t stride_bytes(size_t k,size_t bytes,bool inlined) {
  const size_t kp=round_up(k,4);
  const size_t ids=round_up(kp*8+kp,8);
  return round_up(ids+k*8+k*8+8+(inlined?k*bytes:0),64);
}
static size_t footprint(size_t k,size_t depth,size_t bytes,const std::string& mode,
                        const std::string& side,const std::string& arm,size_t slots=WRITE_SLOTS) {
  const size_t count=version_count(k,depth);
  if (side=="read") {
    const size_t payload=mode=="external"?count*bytes:0;
    if (arm=="linked_scattered" || arm=="linked_local") return 8+count*node_stride(bytes,mode=="inline")+payload;
    if (arm=="contig_scalar" || arm=="contig_simd")
      return stride_bytes(k,bytes,mode=="inline")+(count-k)*node_stride(bytes,mode=="inline")+payload;
  } else {
    if (arm=="linked_prepend" || arm=="block" || arm=="shift" || arm=="ring")
      return write_capacity(k,bytes,mode=="inline",arm,slots)+sizeof(WriteSet);
  }
  throw std::runtime_error("unknown arm for footprint");
}
struct ReadBatch {
  size_t k,count,nkeys,bytes,stride=0;
  std::string arm,mode,pattern;
  std::vector<Node*> heads;
  AlignedBytes nodes{nullptr,&std::free};
  std::unique_ptr<uint8_t,decltype(&std::free)> arena{nullptr,&std::free};
  const uint8_t* values;
  const std::vector<size_t>* value_slots;
  ReadBatch(size_t k_,size_t depth,size_t n,size_t b,const std::string& m,
            const std::string& p,const std::string& a,const uint8_t* shared,
            const std::vector<size_t>* slots=nullptr);
  State state_at(size_t i) const {
    if (pattern=="candidate_pending" && i==1) return PENDING;
    if (pattern=="pending_newer_than_ts" && i==0) return PENDING;
    if (pattern=="aborted_then_committed" && i==1) return ABORTED;
    if (pattern=="candidate_deleted" && i==1) return DELETED;
    return COMMITTED;
  }
  const uint8_t* value_at(size_t key,size_t i,uint8_t* storage) const {
    if (mode=="none") return nullptr;
    const uint8_t content=static_cast<uint8_t>((key*31+i*17+11)&255);
    if (mode=="external") return values+(*value_slots)[key*count+i]*bytes;
    std::memset(storage,content,bytes);
    return storage;
  }
  SoA soa_at(size_t key) const {
    const uint8_t* block=arena.get()+key*stride;
    const size_t kp=round_up(k,4);
    const auto* wts=reinterpret_cast<const uint64_t*>(block);
    const auto* states=block+kp*8;
    const auto* ids=reinterpret_cast<const uint64_t*>(block+round_up(kp*8+kp,8));
    const auto* refs=reinterpret_cast<const uint8_t* const*>(reinterpret_cast<const uint8_t*>(ids)+k*8);
    const auto* cold=reinterpret_cast<Node* const*>(reinterpret_cast<const uint8_t*>(refs)+k*8);
    return {wts,ids,states,refs,k,cold};
  }
};
ReadBatch::ReadBatch(size_t k_,size_t depth,size_t n,size_t b,const std::string& m,
                     const std::string& p,const std::string& a,const uint8_t* shared,
                     const std::vector<size_t>* slots)
    :k(k_),count(version_count(k_,depth)),nkeys(n),bytes(b),arm(a),mode(m),pattern(p),
     values(shared),value_slots(slots) {
  const bool linked=arm=="linked_scattered" || arm=="linked_local";
  const size_t hot=linked?0:k;
  const size_t per_key=count-hot;
  const size_t node_bytes=node_stride(bytes,mode=="inline");
  nodes.reset(static_cast<uint8_t*>(std::aligned_alloc(64,std::max<size_t>(64,n*per_key*node_bytes))));
  if (!nodes) throw std::bad_alloc();
  std::vector<size_t> order(n*per_key);
  for (size_t i=0;i<order.size();++i) order[i]=i;
  if (arm!="linked_local") std::shuffle(order.begin(),order.end(),std::mt19937_64(0x51caDAULL));
  if (!linked) {
    stride=stride_bytes(k,bytes,mode=="inline");
    auto* ptr=static_cast<uint8_t*>(std::aligned_alloc(64,stride*n));
    if (!ptr) throw std::bad_alloc();
    arena.reset(ptr);
    std::memset(ptr,0,stride*n);
  } else heads.resize(n);
  std::vector<Node*> by_index(n*count,nullptr);
  size_t slot=0;
  for (size_t key=0;key<n;++key) for (size_t i=hot;i<count;++i) {
    const size_t logical=key*per_key+i-hot;
    Node* node=new(nodes.get()+(arm=="linked_local"?logical:order[slot++])*node_bytes) Node();
    node->v={100000-i,state_at(i),1000+i,nullptr};
    node->v.value=value_at(key,i,node_inline(node));
    by_index[key*count+i]=node;
  }
  for (size_t key=0;key<n;++key) {
    if (linked) heads[key]=by_index[key*count];
    else {
      uint8_t* block=arena.get()+key*stride;
      const size_t kp=round_up(k,4);
      auto* wts=reinterpret_cast<uint64_t*>(block);
      auto* states=block+kp*8;
      auto* ids=reinterpret_cast<uint64_t*>(block+round_up(kp*8+kp,8));
      auto* refs=reinterpret_cast<const uint8_t**>(reinterpret_cast<uint8_t*>(ids)+k*8);
      auto* cold=reinterpret_cast<Node**>(reinterpret_cast<uint8_t*>(refs)+k*8);
      for (size_t i=0;i<kp;++i) wts[i]=UINT64_MAX;
      for (size_t i=0;i<k;++i) {
        wts[i]=100000-i; states[i]=state_at(i); ids[i]=1000+i;
        uint8_t* inline_ptr=reinterpret_cast<uint8_t*>(cold+1)+i*bytes;
        refs[i]=value_at(key,i,inline_ptr);
      }
      *cold=by_index[key*count+k];
    }
    for (size_t i=hot;i<count;++i)
      by_index[key*count+i]->next=i+1<count?by_index[key*count+i+1]:nullptr;
  }
}
static Result select_scattered_view(const ReadBatch& a,size_t idx,uint64_t ts) { return select_linked_scattered(a.heads[idx],ts); }
static Result select_local_view(const ReadBatch& a,size_t idx,uint64_t ts) { return select_linked_local(a.heads[idx],ts); }
static Result select_scalar_view(const ReadBatch& a,size_t idx,uint64_t ts) { return select_contig_scalar(a.soa_at(idx),ts); }
static Result select_simd_view(const ReadBatch& a,size_t idx,uint64_t ts) { return select_contig_simd(a.soa_at(idx),ts); }
using SelectView=Result(*)(const ReadBatch&,size_t,uint64_t);
static SelectView select_function(const std::string& arm) {
  if (arm=="linked_scattered") return select_scattered_view;
  if (arm=="linked_local") return select_local_view;
  if (arm=="contig_scalar") return select_scalar_view;
  if (arm=="contig_simd") return select_simd_view;
  throw std::runtime_error("unknown read arm");
}
static uint64_t contribution(Result r,size_t bytes,bool read_value) {
  uint64_t value_sum=0;
  if (read_value && r.kind==FOUND && r.value)
    for (size_t i=0;i<bytes;++i) value_sum+=r.value[i];
  return r.id*8+static_cast<uint64_t>(r.kind)+value_sum;
}
// Hull-Dobell full-period LCG modulo a power of two. Cycle-walking skips the
// unused tail, so every n consecutive selections visit each key exactly once.
static size_t read_sequence_mask(size_t n) {
  size_t power=1;
  while (power<n) {
    if (power>SIZE_MAX/2) throw std::runtime_error("read key count too large");
    power*=2;
  }
  return power-1;
}
static size_t next_read_index(size_t idx,size_t n,size_t mask,
                              uint64_t selected_id,uint64_t zero) {
  do { idx=(idx*1664525ULL+1013904223ULL)&mask; } while (idx>=n);
  return idx ^ (selected_id & zero);
}
static int key_sequence_check(size_t n) {
  if (!n) throw std::runtime_error("read key count must be positive");
  const size_t mask=read_sequence_mask(n);
  std::vector<uint8_t> seen(n,0);
  size_t idx=0,other=0,visited=0;
  bool independent=true;
  for (size_t i=0;i<n;++i) {
    if (!seen[idx]) { seen[idx]=1; ++visited; }
    idx=next_read_index(idx,n,mask,1000,0);
    other=next_read_index(other,n,mask,2000+i,0);
    independent &= idx==other;
  }
  const bool passed=visited==n && idx==0 && independent;
  std::cout << "{\"n_keys\":" << n << ",\"visited\":" << visited
            << ",\"repeats\":" << (idx==0?"true":"false")
            << ",\"id_independent\":" << (independent?"true":"false")
            << ",\"passed\":" << (passed?"true":"false") << "}\n";
  return passed?0:1;
}
static uint64_t expected_read(size_t nkeys,size_t k,size_t depth,size_t bytes,
                              const std::string& mode,const std::string& pattern,uint64_t ops) {
  uint64_t total=0,idx=0;
  const size_t mask=read_sequence_mask(nkeys);
  const uint64_t ts=100000-depth;
  for (uint64_t op=0;op<ops;++op) {
    Result r{NOT_FOUND,0,nullptr};
    const size_t count=version_count(k,depth);
    for (size_t i=0;i<count;++i) {
      if (100000-i>ts) continue;
      State state=COMMITTED;
      if (pattern=="candidate_pending" && i==1) state=PENDING;
      if (pattern=="pending_newer_than_ts" && i==0) state=PENDING;
      if (pattern=="aborted_then_committed" && i==1) state=ABORTED;
      if (pattern=="candidate_deleted" && i==1) state=DELETED;
      if (state==ABORTED) continue;
      r={state==PENDING?WAIT:(state==DELETED?REMOVED:FOUND),
         state==PENDING?0:1000+i,nullptr};
      if (r.kind==FOUND && mode!="none") total+=((idx*31+i*17+11)&255)*bytes;
      break;
    }
    total+=r.id*8+static_cast<uint64_t>(r.kind);
    idx=next_read_index(idx,nkeys,mask,0,0);
  }
  return total;
}
static int selfcheck() {
  std::vector<std::string> failed, names;
  unsigned random_cases = 0;
  auto check = [&](const std::string& name, const std::vector<Version>& vv, size_t k, uint64_t ts, Result expected) {
    names.push_back(name);
    Layout scattered = make_layout(vv, k, true), local = make_layout(vv, k, false);
    if (!(reference(vv, ts) == expected)) failed.push_back(name + ":reference");
    for (const auto& arm : read_arms) {
      const auto& layout = arm == "linked_local" ? local : scattered;
      if (!(select(layout, arm, ts) == expected)) failed.push_back(name + ":" + arm);
    }
  };
  auto v = [](std::initializer_list<std::pair<uint64_t, State>> seq) {
    std::vector<Version> out;
    uint64_t id = 1;
    for (auto [ts, state] : seq) out.push_back({ts, state, id++, nullptr});
    return out;
  };
  check("newest_committed", v({{90,COMMITTED},{80,COMMITTED}}), 2, 90, {FOUND,1,nullptr});
  check("hot_tail_committed", v({{90,COMMITTED},{80,COMMITTED},{70,COMMITTED}}), 3, 70, {FOUND,3,nullptr});
  check("first_cold_committed", v({{90,COMMITTED},{80,COMMITTED},{70,COMMITTED}}), 2, 70, {FOUND,3,nullptr});
  check("deep_cold_committed", v({{90,COMMITTED},{80,COMMITTED},{70,COMMITTED},{60,COMMITTED}}), 1, 60, {FOUND,4,nullptr});
  check("all_newer_than_ts", v({{90,COMMITTED},{80,PENDING}}), 1, 70, {NOT_FOUND,0,nullptr});
  check("candidate_pending", v({{90,PENDING},{80,COMMITTED}}), 2, 90, {WAIT,0,nullptr});
  check("pending_newer_than_ts_skipped", v({{90,PENDING},{80,COMMITTED}}), 2, 80, {FOUND,2,nullptr});
  check("pending_between_committed", v({{90,COMMITTED},{80,PENDING},{70,COMMITTED}}), 3, 80, {WAIT,0,nullptr});
  check("aborted_then_committed", v({{90,ABORTED},{80,COMMITTED}}), 2, 90, {FOUND,2,nullptr});
  check("hot_all_aborted_then_cold_committed", v({{90,ABORTED},{80,ABORTED},{70,COMMITTED}}), 2, 90, {FOUND,3,nullptr});
  check("aborted_then_cold_pending", v({{90,ABORTED},{80,ABORTED},{70,PENDING}}), 2, 90, {WAIT,0,nullptr});
  check("aborted_then_cold_deleted", v({{90,ABORTED},{80,ABORTED},{70,DELETED}}), 2, 90, {REMOVED,3,nullptr});
  check("candidate_deleted", v({{90,DELETED},{80,COMMITTED}}), 2, 90, {REMOVED,1,nullptr});
  check("equal_ts", v({{90,COMMITTED},{80,COMMITTED}}), 2, 80, {FOUND,2,nullptr});
  names.push_back("hot_does_not_read_cold_slot");
  {
    const uint64_t wts[4] = {90,UINT64_MAX,UINT64_MAX,UINT64_MAX};
    const uint64_t id[1] = {7};
    const uint8_t state[4] = {COMMITTED,0,0,0};
    const uint8_t* value[1] = {nullptr};
    const SoA hot{wts,id,state,value,1,nullptr};
    if (!(select_contig_scalar(hot,90)==Result{FOUND,7,nullptr}))
      failed.push_back("hot_does_not_read_cold_slot:contig_scalar");
    if (!(select_contig_simd(hot,90)==Result{FOUND,7,nullptr}))
      failed.push_back("hot_does_not_read_cold_slot:contig_simd");
  }
  names.push_back("k_boundary_each_K");
  for (size_t k : {1U,2U,3U,4U,8U,16U}) {
    std::vector<Version> a;
    for (size_t i = 0; i < k+1; ++i) a.push_back({1000-i,COMMITTED,i+1,nullptr});
    for (size_t depth : {k-1,k}) {
      Layout s=make_layout(a,k,true), l=make_layout(a,k,false);
      for (const auto& arm : read_arms)
        if (!(select(arm == "linked_local" ? l : s,arm,1000-depth) == Result{FOUND,depth+1,nullptr}))
          failed.push_back("k_boundary_each_K:"+std::to_string(k)+":"+arm);
    }
  }
  std::mt19937_64 rng(0x5eed1234ULL);
  for (unsigned c=0;c<256;++c) {
    const size_t k=1+rng()%16, n=k+5;
    std::vector<Version> a;
    for (size_t i=0;i<n;++i) a.push_back({1000-i,static_cast<State>(rng()%4),i+1,nullptr});
    const uint64_t ts=1000-rng()%(n+3);
    Layout s=make_layout(a,k,true),l=make_layout(a,k,false);
    for (const auto& arm:read_arms)
      if (!(select(arm=="linked_local"?l:s,arm,ts)==reference(a,ts)))
        failed.push_back("random:"+std::to_string(c)+":"+arm);
    ++random_cases;
  }
  names.push_back("write_version_ids");
  for (size_t k : {1U,2U,3U,4U,8U,16U}) for (const auto& arm:write_arms) {
    WriteSet a=write_initial(k,0,false,arm);
    std::vector<uint64_t> want;
    for (size_t i=0;i<k+3;++i) want.push_back(1000-i);
    for (uint64_t n=0;n<k+3;++n) {
      Version newer{2000+n,COMMITTED,2000+n,nullptr};
      insert(a,arm,newer);
      want.insert(want.begin(),newer.id);
      if (ids(a,arm)!=want) failed.push_back("write_version_ids:"+arm+":"+std::to_string(k));
    }
  }
  names.push_back("write_value_bytes");
  for (size_t k : {1U,3U,8U}) for (bool inlined : {false,true})
    for (const auto& arm:write_arms) {
      WriteSet a=write_initial(k,16,inlined,arm);
      std::vector<std::pair<uint64_t,std::vector<uint8_t>>> want;
      for (size_t i=0;i<k+3;++i)
        want.push_back({1000-i,std::vector<uint8_t>(16,static_cast<uint8_t>((i*7+3)&255))});
      for (uint64_t n=0;n<k+3;++n) {
        std::array<uint8_t,16> incoming{};
        incoming.fill(static_cast<uint8_t>(n*7+17));
        insert(a,arm,{2000+n,COMMITTED,2000+n,incoming.data()});
        want.insert(want.begin(),{2000+n,std::vector<uint8_t>(incoming.begin(),incoming.end())});
        if (values(a,arm)!=want)
          failed.push_back("write_value_bytes:"+arm+":"+std::to_string(k));
      }
    }
  for (const auto& pattern : {"candidate_pending","pending_newer_than_ts",
                              "aborted_then_committed","candidate_deleted"}) {
    const std::string name=std::string("state_cell_")+pattern;
    names.push_back(name);
    Result expected{FOUND,1001,nullptr};
    if (std::string(pattern)=="candidate_pending") expected={WAIT,0,nullptr};
    else if (std::string(pattern)=="aborted_then_committed") expected={FOUND,1002,nullptr};
    else if (std::string(pattern)=="candidate_deleted") expected={REMOVED,1001,nullptr};
    for (const auto& arm:read_arms) {
      ReadBatch batch(3,1,1,0,"none",pattern,arm,nullptr);
      if (!(select_function(arm)(batch,0,99999)==expected))
        failed.push_back(name+":"+arm);
    }
  }
  std::cout << "{\"passed\":" << (failed.empty()?"true":"false") << ",\"random_cases\":" << random_cases << ",\"vectors\":[";
  for (size_t i=0;i<names.size();++i) std::cout << (i?",":"") << "\"" << names[i] << "\"";
  std::cout << "],\"failures\":[";
  for (size_t i=0;i<failed.size();++i) std::cout << (i?",":"") << "\"" << failed[i] << "\"";
  std::cout << "]}\n";
  return failed.empty()?0:1;
}

struct RepData { uint64_t elapsed,checksum; unsigned pos; };
struct ArmData {
  std::string name;
  size_t footprint_per_key;
  std::vector<RepData> reps;
};
static void print_cell(uint64_t ops,uint64_t expected,size_t nkeys,size_t shared_value_pool_bytes,
                       const std::vector<ArmData>& measured) {
  std::cout << std::setprecision(17);
  std::cout << "{\"ops\":" << ops << ",\"expected_checksum\":" << expected
            << ",\"shared_value_pool_bytes\":" << shared_value_pool_bytes << ",\"arms\":[";
  for (size_t a=0;a<measured.size();++a) {
    if (a) std::cout << ",";
    const auto& arm=measured[a];
    std::cout << "{\"arm\":\"" << arm.name << "\",\"footprint_bytes\":"
              << arm.footprint_per_key*nkeys << ",\"footprint_per_key_bytes\":"
              << arm.footprint_per_key << ",\"reps\":[";
    for (size_t rep=0;rep<arm.reps.size();++rep) {
      if (rep) std::cout << ",";
      const auto& r=arm.reps[rep];
      std::cout << "{\"rep\":" << rep << ",\"order_pos\":" << r.pos
                << ",\"elapsed_ns\":" << r.elapsed
                << ",\"ns_per_op\":" << static_cast<double>(r.elapsed)/ops
                << ",\"checksum\":" << r.checksum << "}";
    }
    std::cout << "]}";
  }
  std::cout << "]}\n";
}
using InsertFn=void(*)(WriteSet&,Version);
static InsertFn insert_function(const std::string& arm) {
  if (arm=="shift") return insert_shift;
  if (arm=="ring") return insert_ring;
  if (arm=="block") return insert_block;
  if (arm=="linked_prepend") return insert_linked_prepend;
  throw std::runtime_error("unknown write arm");
}
static uint64_t write_batch(std::vector<WriteSet>& keys,const std::string& arm,
                            InsertFn fn,uint64_t ops,size_t bytes,
                            const std::vector<uint8_t>& source) {
  const size_t nkeys=keys.size();
  const bool linked=arm=="linked_prepend";
  uint64_t checksum=0,idx=0;
  for (uint64_t i=0;i<ops;++i) {
    const uint8_t content=static_cast<uint8_t>((i*7+17)&255);
    const uint8_t* data=source.data()+static_cast<size_t>(content)*bytes;
    WriteSet& key=keys[idx];
    Version v{200000+i,COMMITTED,200000+i,data};
    if (!key.inline_value && bytes) {
      auto* owned=static_cast<uint8_t*>(key.arena->allocate(bytes,1));
      std::memcpy(owned,data,bytes);
      v.value=owned;
    }
    fn(key,v);
    const Version& front=linked?key.linked_head->v:key.hot[key.head];
    checksum+=front.id+(bytes?front.value[0]:0);
    idx=(idx*1664525ULL+front.id+1013904223ULL)%nkeys;
  }
  return checksum;
}
static size_t maximum_write_inserts(size_t nkeys,uint64_t ops) {
  std::vector<size_t> counts(nkeys,0);
  size_t maximum=0,idx=0;
  for (uint64_t i=0;i<ops;++i) {
    maximum=std::max(maximum,++counts[idx]);
    idx=(idx*1664525ULL+(200000+i)+1013904223ULL)%nkeys;
  }
  return maximum;
}
static std::vector<std::deque<std::pair<uint64_t,uint8_t>>>
reference_write_model(size_t nkeys,size_t k,uint64_t ops) {
  std::vector<std::deque<std::pair<uint64_t,uint8_t>>> model(nkeys);
  for (auto& key:model) for (size_t i=0;i<k+3;++i)
    key.push_back({1000-i,static_cast<uint8_t>((i*7+3)&255)});
  uint64_t idx=0;
  for (uint64_t i=0;i<ops;++i) {
    const uint64_t id=200000+i;
    model[idx].push_front({id,static_cast<uint8_t>((i*7+17)&255)});
    idx=(idx*1664525ULL+id+1013904223ULL)%nkeys;
  }
  return model;
}
static int write_cell(size_t k,size_t nkeys,size_t bytes,const std::string& mode,
                      const std::vector<std::string>& arms,unsigned reps,uint64_t requested_ops,
                      const std::string& control,const std::string& ack,size_t memory_limit) {
  if (bytes>256) throw std::runtime_error("value bytes exceed inline capacity");
  auto check_capacity=[&](size_t slots) {
    for (const auto& arm:arms) {
      const size_t per_key=footprint(k,0,bytes,mode,"write",arm,slots);
      if (memory_limit && (per_key>memory_limit/nkeys ||
          (slots>memory_limit/nkeys)))
        throw std::runtime_error("write capacity exceeds memory limit");
    }
  };
  std::vector<uint8_t> source(256*bytes);
  for (size_t value=0;value<256;++value)
    std::memset(source.data()+value*bytes,static_cast<int>(value),bytes);
  uint64_t ops=requested_ops;
  if (!ops) {
    const uint64_t trial=200;
    const size_t trial_slots=maximum_write_inserts(nkeys,trial);
    check_capacity(trial_slots);
    double fastest=1e100;
    for (const auto& arm:arms) {
      std::vector<WriteSet> keys;
      for (size_t key=0;key<nkeys;++key) keys.push_back(write_initial(k,bytes,mode=="inline",arm,trial_slots));
      const uint64_t begin=now_ns();
      volatile uint64_t check=write_batch(keys,arm,insert_function(arm),trial,bytes,source);
      (void)check;
      fastest=std::min(fastest,static_cast<double>(now_ns()-begin)/trial);
    }
    ops=std::max<uint64_t>(trial,static_cast<uint64_t>(100000000.0/std::max(1.0,fastest))+1);
    for (unsigned attempt=0;attempt<3;++attempt) {
      uint64_t shortest=UINT64_MAX;
      const size_t slots=maximum_write_inserts(nkeys,ops);
      check_capacity(slots);
      for (const auto& arm:arms) {
        std::vector<WriteSet> keys;
        keys.reserve(nkeys);
        for (size_t key=0;key<nkeys;++key)
          keys.push_back(write_initial(k,bytes,mode=="inline",arm,slots));
        const uint64_t begin=now_ns();
        volatile uint64_t check=write_batch(keys,arm,insert_function(arm),ops,bytes,source);
        (void)check;
        shortest=std::min(shortest,now_ns()-begin);
      }
      if (shortest>=100000000ULL) break;
      if (attempt==2) throw std::runtime_error("write batch below 0.1 s");
      ops=static_cast<uint64_t>(static_cast<double>(ops)*105000000.0/
                                std::max<uint64_t>(1,shortest))+1;
    }
  }
  const size_t slots=maximum_write_inserts(nkeys,ops);
  check_capacity(slots);
  std::vector<ArmData> measured;
  for (const auto& arm:arms)
    measured.push_back({arm,footprint(k,0,bytes,mode,"write",arm,slots),{}});
  uint64_t expected=0;
  for (uint64_t i=0;i<ops;++i)
    expected+=200000+i+static_cast<uint8_t>((i*7+17)&255);
  for (unsigned rep=0;rep<reps;++rep) for (size_t pos=0;pos<arms.size();++pos) {
    const size_t a=(rep+pos)%arms.size();
    std::vector<WriteSet> keys;
    keys.reserve(nkeys);
    for (size_t key=0;key<nkeys;++key) keys.push_back(write_initial(k,bytes,mode=="inline",arms[a],slots));
    perf_command(control,ack,"enable");
    const uint64_t begin=now_ns();
    const uint64_t checksum=write_batch(keys,arms[a],insert_function(arms[a]),ops,bytes,source);
    const uint64_t elapsed=now_ns()-begin;
    perf_command(control,ack,"disable");
    if (checksum!=expected) throw std::runtime_error("write checksum mismatch: "+arms[a]);
    const auto model=reference_write_model(nkeys,k,ops);
    for (size_t key=0;key<nkeys;++key) {
      const auto actual=values(keys[key],arms[a]);
      if (actual.size()!=model[key].size()) throw std::runtime_error("write version count mismatch");
      for (size_t i=0;i<actual.size();++i) {
        if (actual[i].first!=model[key][i].first ||
            actual[i].second!=std::vector<uint8_t>(bytes,model[key][i].second))
          throw std::runtime_error("write value mismatch");
      }
    }
    measured[a].reps.push_back({elapsed,checksum,static_cast<unsigned>(pos)});
  }
  print_cell(ops,expected,nkeys,0,measured);
  return 0;
}
static int cell(const std::string& json,const std::vector<std::string>& arms,unsigned reps,
                uint64_t requested_ops,const std::string& control,const std::string& ack) {
  const size_t k=field(json,"K",4),nkeys=field(json,"n_keys",64);
  const size_t depth=field(json,"depth",0),bytes=field(json,"value_bytes",0);
  const std::string side=strfield(json,"side","read"),mode=strfield(json,"value_mode","none");
  const std::string pattern=strfield(json,"state_pattern","");
  if (!k || !nkeys || arms.empty() || !reps || (control.empty()!=ack.empty()))
    throw std::runtime_error("invalid cell parameters");
  if (side=="write") return write_cell(k,nkeys,bytes,mode,arms,reps,requested_ops,control,ack,
                                        field(json,"memory_limit_bytes",0));
  if (side!="read") throw std::runtime_error("unknown cell side");
  std::vector<uint8_t> shared;
  std::vector<size_t> value_slots;
  const size_t count=version_count(k,depth);
  if (mode=="external") {
    shared.resize(nkeys*count*bytes);
    value_slots.resize(nkeys*count);
    for (size_t i=0;i<value_slots.size();++i) value_slots[i]=i;
    std::shuffle(value_slots.begin(),value_slots.end(),std::mt19937_64(0x5eeda11ULL));
    for (size_t key=0;key<nkeys;++key) for (size_t i=0;i<count;++i)
      std::memset(shared.data()+value_slots[key*count+i]*bytes,
                  static_cast<int>((key*31+i*17+11)&255),bytes);
  }
  std::vector<std::unique_ptr<ReadBatch>> owners;
  std::vector<ReadBatch*> batches;
  std::vector<ArmData> measured;
  for (const auto& arm:arms) {
    ReadBatch* shared_contig=nullptr;
    if (arm=="contig_scalar" || arm=="contig_simd")
      for (const auto& owned:owners)
        if (owned->arm=="contig_scalar" || owned->arm=="contig_simd") shared_contig=owned.get();
    if (!shared_contig) {
      owners.emplace_back(std::make_unique<ReadBatch>(k,depth,nkeys,bytes,mode,pattern,arm,
                                                      shared.data(),&value_slots));
      shared_contig=owners.back().get();
    }
    batches.push_back(shared_contig);
    measured.push_back({arm,footprint(k,depth,bytes,mode,side,arm),{}});
  }
  std::vector<size_t>().swap(value_slots);
  const uint64_t ts=100000-depth;
  const size_t sequence_mask=read_sequence_mask(nkeys);
  volatile uint64_t opaque_zero=0;
  const uint64_t zero=opaque_zero;
  auto run_read=[&](size_t arm_index,uint64_t ops)->uint64_t {
    const auto& batch=*batches[arm_index];
    const SelectView fn=select_function(arms[arm_index]);
    uint64_t checksum=0,idx=0;
    for (uint64_t i=0;i<ops;++i) {
      const Result r=fn(batch,idx,ts);
      checksum+=contribution(r,bytes,mode!="none");
      idx=next_read_index(idx,nkeys,sequence_mask,r.id,zero);
    }
    return checksum;
  };
  uint64_t ops=requested_ops;
  if (!ops) {
    double fastest=1e100;
    for (size_t a=0;a<arms.size();++a) {
      const uint64_t begin=now_ns();
      volatile uint64_t result=run_read(a,2000);
      (void)result;
      fastest=std::min(fastest,static_cast<double>(now_ns()-begin)/2000.0);
    }
    ops=std::max<uint64_t>(2000,static_cast<uint64_t>(100000000.0/std::max(1.0,fastest))+1);
    for (unsigned attempt=0;attempt<3;++attempt) {
      uint64_t shortest=UINT64_MAX;
      for (size_t a=0;a<arms.size();++a) {
        const uint64_t begin=now_ns();
        volatile uint64_t check=run_read(a,ops);
        (void)check;
        shortest=std::min(shortest,now_ns()-begin);
      }
      if (shortest>=100000000ULL) break;
      if (attempt==2) throw std::runtime_error("read batch below 0.1 s");
      ops=static_cast<uint64_t>(static_cast<double>(ops)*105000000.0/
                                std::max<uint64_t>(1,shortest))+1;
    }
  }
  const uint64_t expected=expected_read(nkeys,k,depth,bytes,mode,pattern,ops);
  for (unsigned rep=0;rep<reps;++rep) {
    for (size_t pos=0;pos<arms.size();++pos) {
      const size_t a=(rep+pos)%arms.size();
      perf_command(control,ack,"enable");
      const uint64_t begin=now_ns();
      const uint64_t checksum=run_read(a,ops);
      const uint64_t elapsed=now_ns()-begin;
      perf_command(control,ack,"disable");
      if (checksum!=expected) throw std::runtime_error("checksum mismatch: "+arms[a]);
      measured[a].reps.push_back({elapsed,checksum,static_cast<unsigned>(pos)});
    }
  }
  print_cell(ops,expected,nkeys,shared.size(),measured);
  return 0;
}
int main(int argc,char** argv) {
  try {
    if (argc==2 && std::string(argv[1])=="--selfcheck") return selfcheck();
    if (argc==3 && std::string(argv[1])=="--key-sequence-check")
      return key_sequence_check(std::stoull(argv[2]));
    std::string json,arms_text,control,ack,footprint_json; unsigned reps=1; uint64_t ops=0;
    for (int i=1;i<argc;++i) {
      std::string arg=argv[i];
      if (i+1>=argc) throw std::runtime_error("missing argument");
      if (arg=="--cell") json=argv[++i];
      else if (arg=="--footprint") footprint_json=argv[++i];
      else if (arg=="--arm" || arg=="--arms") arms_text=argv[++i];
      else if (arg=="--reps") reps=static_cast<unsigned>(std::stoul(argv[++i]));
      else if (arg=="--ops") ops=std::stoull(argv[++i]);
      else if (arg=="--perf-ctl-fifo") control=argv[++i];
      else if (arg=="--perf-ack-fifo") ack=argv[++i];
      else throw std::runtime_error("unknown option: "+arg);
    }
    if (!footprint_json.empty()) {
      const size_t k=field(footprint_json,"K",4),depth=field(footprint_json,"depth",0);
      const size_t bytes=field(footprint_json,"value_bytes",0);
      const auto mode=strfield(footprint_json,"value_mode","none");
      const auto side=strfield(footprint_json,"side","read");
      const size_t nkeys=field(footprint_json,"n_keys",64);
      const uint64_t query_ops=field(footprint_json,"ops",0);
      const size_t slots=side=="write" && query_ops?maximum_write_inserts(nkeys,query_ops):WRITE_SLOTS;
      std::cout << "{\"footprint_per_key_bytes\":"
                << footprint(k,depth,bytes,mode,side,arms_text,slots) << "}\n";
      return 0;
    }
    if (json.empty() || arms_text.empty()) throw std::runtime_error("--cell and --arms required");
    std::vector<std::string> arms;
    size_t start=0;
    while (start<arms_text.size()) {
      const size_t end=arms_text.find(',',start);
      arms.push_back(arms_text.substr(start,end==std::string::npos?end:end-start));
      if (end==std::string::npos) break;
      start=end+1;
    }
    return cell(json,arms,reps,ops,control,ack);
  } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 2; }
}
