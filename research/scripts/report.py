"""Build the final report only from explicitly selected, completed runs."""
import collections,csv,hashlib,json,pathlib,statistics,subprocess
from analyze import ROOT,read_hgr
from benchmark import verify
def read(name,expected=None):
 rows=list(csv.DictReader((ROOT/'results'/name/'runs.csv').open()))
 if expected is not None:assert len(rows)==expected,(name,len(rows),expected)
 assert all(r['status'] in ('ok','timeout') for r in rows),(name,'invalid run')
 return rows
def scores(rows,key='solver'):
 out={}
 for name in sorted(set(r[key] for r in rows)):
  rr=[r for r in rows if r[key]==name];out[name]={'solved':sum(r['status']=='ok' for r in rr),'runs':len(rr),'timeouts':sum(r['status']=='timeout' for r in rr)}
 return out
def main():
 dense=read('confirmation-dense-uzl',60);full=sum([read(f'full-private-shard{i}',68 if i==0 else 66) for i in range(3)],[])
 no_pair=read('ablation-no-pair',30);bibco=read('bibco-native-corrected',30);biblp=read('biblp-native-corrected',30)
 repeat=read('repeats-native',24);portable=read('ablation-portable-v2',24);perms=read('permutations',24)
 holdout=sum([read(f'holdout-shard{i}',8) for i in range(2)],[])
 sf=scores(full);sd=scores(dense+no_pair+bibco+biblp)
 a={r['instance']:r for r in full if r['solver']=='portfolio'};b={r['instance']:r for r in full if r['solver']=='uzl'}
 wins=sorted(i for i in a if a[i]['status']=='ok' and b[i]['status']!='ok');losses=sorted(i for i in a if a[i]['status']!='ok' and b[i]['status']=='ok')
 for i in a:
  if a[i]['status']==b[i]['status']=='ok':assert a[i]['objective']==b[i]['objective'],i
 # Recheck every completed certificate in the two primary experiments.
 checked=0
 for name in ['confirmation-dense-uzl']+[f'full-private-shard{i}' for i in range(3)]:
  for r in read(name):
   if r['status']!='ok':continue
   n,es=read_hgr(ROOT/'data/pace2025/private/hs/exact'/(r['instance']+'.hgr'))
   f=ROOT/'results'/name/f"{r['instance']}-{r['solver']}-r{r['repeat']}.stdout"
   vals=list(map(int,f.read_text().split()));assert vals[0]==len(vals)-1 and verify(n,es,vals[1:]),str(f);checked+=1
 med47=statistics.median(float(r['wall_s']) for r in repeat if r['instance']=='private_exact_047')
 med47portable=statistics.median(float(r['wall_s']) for r in portable if r['instance']=='private_exact_047')
 tests={name:json.loads((ROOT/'results'/name).read_text()) for name in ['check-exact-v3.json','check-regressions.json','check-bib-adapter.json','certify-047.json','certify-001.json']}
 summary={'full_private':sf,'small_dense_private':sd,'paired_wins':wins,'paired_losses':losses,'rechecked_primary_certificates':checked,'permutation_status':dict(collections.Counter(r['status'] for r in perms)),'native_repeats':scores(repeat),'portable_repeats':scores(portable),'median_047_native_s':med47,'median_047_portable_s':med47portable,'fresh_ws_holdout':scores(holdout),'tests':tests,'invalidated_runs':['bibco-native-dense','biblp-native-dense']}
 (ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2))
 dense_table='\n'.join(f"| {name} | {v['solved']}/{v['runs']} | {v['timeouts']} |" for name,v in sd.items())
 h=scores(holdout)
 text=f'''# Quyết định chọn đề tài và kết quả đã kiểm tra

**Chọn: Thuật toán chính xác cho Minimum Hitting Set với kiểm tra hoàn tất
hai đỉnh bằng bitset đối ngẫu.**

Đây là hướng có bằng chứng thực nghiệm mạnh nhất trong các hướng đã
hiện thực ở phiên nghiên cứu này. Có thuật toán hoàn chỉnh, chứng minh,
solver kết hợp, kiểm chứng độc lập và kết quả trên dữ liệu chính thức.
Không dựa vào một lời hứa sẽ thử benchmark sau.

## Kết quả chính: đủ 100 private instances của PACE HS 2025

Mỗi lượt có 10 giây wall time; mỗi solver được pin vào một logical CPU.
Hai solver được chạy xen kẽ theo thứ tự cố định bằng seed. Ba shard chạy
trên ba lõi vật lý khác nhau. Toàn bộ **200 lượt** đã kết thúc.

| Solver | Giải tối ưu trong 10 giây | Timeout |
|---|---:|---:|
| UzL nguyên gốc | {sf['uzl']['solved']}/100 | {sf['uzl']['timeouts']} |
| Solver kết hợp đề xuất | **{sf['portfolio']['solved']}/100** | {sf['portfolio']['timeouts']} |

Có **{len(wins)} instance thắng thêm và {len(losses)} instance mất đi** so với UzL
trong cặp lượt chạy này. Mọi nghiệm hoàn tất đã được kiểm tra khả thi;
objective trùng nhau ở mọi instance cả hai cùng giải xong. Danh sách thắng
và thua được lưu trong [summary.json](results/summary.json), không chỉ lưu số đếm.

## Nhóm nhỏ/dense: đủ 30 instance, cùng giới hạn 10 giây

Nhóm được xác định bằng n,m≤512, không chọn các ID dựa trên kết quả thắng.
Bảng dùng vòng xác nhận đã pin CPU; BIB chạy trên đồ thị DS gốc có ánh xạ
tương đương được kiểm tra đầy đủ, không chỉ trên đồ thị incidence lớn hơn.

| Solver / biến thể | Giải tối ưu | Timeout |
|---|---:|---:|
{dense_table}

`no_pair` bỏ thủ tục hoàn tất hai đỉnh, giữ khung tìm kiếm và bitset.
Vì thế ablation cho thấy phần cải thiện không chỉ do đổi ngôn ngữ hay
dùng một biểu diễn bitset chung.

Các pilot khác ở cùng ngưỡng 10 giây: Shadoks exact, findminhs v2.1.0,
SAT + sequential counter và HiGHS MILP đều được chạy trên 30 input này.
Đây là đối chứng phụ; metadata của các pilot không đầy đủ như vòng xác
nhận chính nên không dùng chúng để tính một tỷ lệ tăng tốc gộp.

## Kiểm chứng và độ bền

- 1.500 lượt đối chiếu với vét cạn trên 300 hypergraph nhỏ, qua 5 cấu hình.
- 317 lượt kiểm tra các biên 64 bit, n/m tới 512 và đường fallback.
- 120 lượt đối chiếu adapter BIBCO/BIBLP với vét cạn trên 60 bài nhỏ.
- {sum(r['status']=='ok' for r in repeat)}/24 lượt lặp lại native và {sum(r['status']=='ok' for r in portable)}/24 lượt portable hoàn tất trên 8 instance đã định trước.
- Đổi nhãn đỉnh, thứ tự hyperedge và thứ tự phần tử: {sum(r['status']=='ok' for r in perms)}/24 lượt hoàn tất, mọi objective hoàn tất giữ nguyên và nghiệm hợp lệ.
- Đã kiểm tra lại độc lập {checked} certificate từ hai thí nghiệm chính khi sinh báo cáo này.
- Verifier Python do nhóm UzL cung cấp chấp nhận đủ 17 certificate dense của pilot.

Với `private_exact_047`, trung vị 3 lượt native là **{med47:.4f} giây**;
bản không dùng `-march=native` là **{med47portable:.4f} giây**. UzL mất
98,568 giây ở một lượt pilot dài hơn trên máy này. Hai protocol khác nhau,
nên ví dụ này minh họa khoảng cách lớn, không dùng làm ước lượng tốc độ gộp.

Chương trình kiểm chứng độc lập đã vét cạn **6.843.880 bộ ba** để xác nhận
OPT=4 cho `private_exact_047`, và **1.137.691.170 bộ bốn** để xác nhận
OPT=5 cho `private_exact_001`. Nó không sử dụng oracle, pivot hay cận của
thuật toán đề xuất. Mã kiểm chứng và JSON kết quả đều có trong thư mục nghiên cứu.

## Dữ liệu mới sau khi cố định thuật toán

Sinh 8 đồ thị Watts–Strogatz mới với NetworkX, n∈{{200,300}}, k/n∈{{0,2;0,5}},
p∈{{0,1;0,5}} và seed đã lưu. Đổi nhãn trước khi chuyển closed neighborhoods
thành HS. Hash binary được lưu trước khi chạy; không sửa thuật toán theo kết quả này.

| Solver | Giải tối ưu trong 10 giây trên dữ liệu mới |
|---|---:|
| Dense bitset | {h['dense']['solved']}/8 |
| UzL | {h['uzl']['solved']}/8 |

Đây là kiểm tra bổ sung, **không phải benchmark PACE** và không gộp vào
bảng 100 instance chính thức. Tám mẫu không đủ để khái quát hiệu quả cho
mọi graph nhỏ/dense.

## Cách đọc đúng các con số

Máy: Intel i9-9980HK, 8 nhân vật lý/16 luồng, RAM 16 GB, không GPU.
Các công việc khác và các shard khác cùng tồn tại trên máy; không giả định
máy idle. Thời gian chính trong bảng là wall time. Cột CPU time thô có
thể thiếu thời gian của tiến trình cháu trong những lượt timeout của
wrapper; không dùng cột đó làm số đo chính cho portfolio.

Ngân sách chính thức PACE là **1800 giây**, không phải 10 giây. Vì chưa
chạy đầy đủ protocol 1800 giây cho tất cả solver, không gọi bảng này là
đánh bại điểm 79/100 lịch sử của UzL, không tuyên bố SOTA toàn diện, và
không tuyên bố đã giải một instance mà mọi đội trước đây đều thất bại.

Bộ private đã được giải mật và được dùng trong phát triển, nên không phải
holdout mù. Các phép đổi nhãn chỉ kiểm tra độ bền, không tạo ra 24 graph
độc lập mới. Solver chuyên biệt vẫn timeout ở một phần của nhóm dense;
fallback giữ tính đúng đắn, không bảo đảm nhanh trên mọi input.

Bản portfolio chuẩn hóa thứ tự phần tử trong hyperedge. Thứ tự tìm kiếm
vì vậy có thể khác bản binary đọc trực tiếp dữ liệu gốc; số instance hoàn
tất của hai bảng không cần bằng nhau theo phép cộng đơn giản.

## Các hướng đã loại và ranh giới tính mới

Phép co cặp sang MaxSAT không thắng encoding gốc trong pilot đã thử.
Học witness thất bại cho phần hoàn tất hai đỉnh gây thêm overhead và không
được chọn. Các log âm tính vẫn được giữ để không chỉ báo cáo thử nghiệm thắng.

Branch-and-bound, cận gain, bitset và portfolio đều đã biết. Nội dung cần
trình bày như đóng góp là thủ tục hoàn tất trên incidence kép, tích hợp
tìm kiếm chính xác và đánh giá vùng hiệu quả so với baseline công bố.
Có bằng chứng để chọn làm khóa luận; không thể cam kết tính mới tuyệt đối
hay paper được nhận chỉ từ khảo sát và benchmark.

## Kiểm soát lỗi thí nghiệm

Hai thư mục `bibco-native-dense` và `biblp-native-dense` đã bị **loại khỏi
mọi kết luận**: runner cũ để tiến trình native con sống sau timeout wrapper.
Đã dừng đủ 60 tiến trình sót, sửa runner để dừng cả process group và chạy
lại đủ 30 input cho mỗi baseline trong các thư mục `*-native-corrected`.
Bảng phía trên chỉ dùng lượt đã sửa. Không có tiến trình đó còn chạy sau
khi kết thúc nghiên cứu.

Xem [phương pháp và chứng minh](notes/METHOD.md), [related work](notes/LITERATURE.md),
[hướng dẫn tái lập](README.md), và [manifest](manifest.json).
'''
 (ROOT/'RESULTS.md').write_text(text)
 # Freeze provenance after all scripts have been finalized.
 repos={}
 for name in ['uzl','findminhs','schidler','shadoks','bib']:
  p=ROOT/'vendor'/name
  repos[name]={'commit':subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip(),'url':subprocess.check_output(['git','-C',str(p),'remote','get-url','origin'],text=True).strip()}
 manifest={'date':'2026-10-19','upstream_repositories':repos,'dataset_commit':subprocess.check_output(['git','-C',str(ROOT/'data/pace2025'),'rev-parse','HEAD'],text=True).strip(),'sources_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'scripts').glob('*')) if p.is_file()},'binary_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'bin').iterdir()) if p.is_file()}}
 manifest['compiler_flags']={'dense_v1':'-O3 -march=native -std=c++20','dense_portable':'-O3 -std=c++20','bib':'-O3 -std=c++17 -DNDEBUG -DLOG_LEVEL=2 -DNO_ASSERT','uzl':'cargo build --release --locked; upstream native CMake Release'}
 manifest['input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['data/pace2025/hs/exact','data/pace2025/private/hs/exact','data/holdout'] for p in sorted((ROOT/folder).glob('*.hgr'))}
 (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
