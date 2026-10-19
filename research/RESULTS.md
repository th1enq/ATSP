# Quyết định chọn đề tài và kết quả đã kiểm tra

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
| UzL nguyên gốc | 27/100 | 73 |
| Solver kết hợp đề xuất | **43/100** | 57 |

Có **16 instance thắng thêm và 0 instance mất đi** so với UzL
trong cặp lượt chạy này. Mọi nghiệm hoàn tất đã được kiểm tra khả thi;
objective trùng nhau ở mọi instance cả hai cùng giải xong. Danh sách thắng
và thua được lưu trong [summary.json](results/summary.json), không chỉ lưu số đếm.

## Nhóm nhỏ/dense: đủ 30 instance, cùng giới hạn 10 giây

Nhóm được xác định bằng n,m≤512, không chọn các ID dựa trên kết quả thắng.
Bảng dùng vòng xác nhận đã pin CPU; BIB chạy trên đồ thị DS gốc có ánh xạ
tương đương được kiểm tra đầy đủ, không chỉ trên đồ thị incidence lớn hơn.

| Solver / biến thể | Giải tối ưu | Timeout |
|---|---:|---:|
| bibco_native | 0/30 | 30 |
| biblp_native | 0/30 | 30 |
| dense | 17/30 | 13 |
| no_pair | 10/30 | 20 |
| uzl | 0/30 | 30 |

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
- 24/24 lượt lặp lại native và 24/24 lượt portable hoàn tất trên 8 instance đã định trước.
- Đổi nhãn đỉnh, thứ tự hyperedge và thứ tự phần tử: 24/24 lượt hoàn tất, mọi objective hoàn tất giữ nguyên và nghiệm hợp lệ.
- Đã kiểm tra lại độc lập 87 certificate từ hai thí nghiệm chính khi sinh báo cáo này.
- Verifier Python do nhóm UzL cung cấp chấp nhận đủ 17 certificate dense của pilot.

Với `private_exact_047`, trung vị 3 lượt native là **0.0382 giây**;
bản không dùng `-march=native` là **0.0402 giây**. UzL mất
98,568 giây ở một lượt pilot dài hơn trên máy này. Hai protocol khác nhau,
nên ví dụ này minh họa khoảng cách lớn, không dùng làm ước lượng tốc độ gộp.

Chương trình kiểm chứng độc lập đã vét cạn **6.843.880 bộ ba** để xác nhận
OPT=4 cho `private_exact_047`, và **1.137.691.170 bộ bốn** để xác nhận
OPT=5 cho `private_exact_001`. Nó không sử dụng oracle, pivot hay cận của
thuật toán đề xuất. Mã kiểm chứng và JSON kết quả đều có trong thư mục nghiên cứu.

## Dữ liệu mới sau khi cố định thuật toán

Sinh 8 đồ thị Watts–Strogatz mới với NetworkX, n∈{200,300}, k/n∈{0,2;0,5},
p∈{0,1;0,5} và seed đã lưu. Đổi nhãn trước khi chuyển closed neighborhoods
thành HS. Hash binary được lưu trước khi chạy; không sửa thuật toán theo kết quả này.

| Solver | Giải tối ưu trong 10 giây trên dữ liệu mới |
|---|---:|
| Dense bitset | 6/8 |
| UzL | 2/8 |

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
