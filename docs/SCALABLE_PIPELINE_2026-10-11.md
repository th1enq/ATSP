# Chế độ thực nghiệm không phụ thuộc vét cạn

Đường chạy mặc định trước đây bắt buộc đo tất cả lát cắt ở từng vòng và cây
cuối, nên bị giới hạn 16 đỉnh. Benchmark nhỏ cũng luôn gọi bộ dựng cây vét
cạn và tối ưu tour bằng DP. Những bước này không phù hợp cho thử nghiệm lớn.

CLI `scripts/experimental_tree.py` và API `construct` hiện mặc định dùng
`exact_measurements=False`. Các bất đẳng thức tải mọi lát cắt được xác nhận
qua PSD hữu tỉ; packing được xác nhận bằng danh sách cây rời cạnh. Chọn cây
cuối trực tiếp từ packing, không dùng oracle đo mọi lát cắt. Tệp JSON dùng
schema v2, có `beta_exact=null`, ghi các cận thay cho kết quả tối ưu chưa đo.
Bộ xác minh vẫn đọc được chứng chỉ v1 của chiến dịch nhỏ.

Với mẫu số chung rút gọn `D`, nếu đa đồ thị ban đầu có ít bản sao hơn đồ thị
nén, dùng trực tiếp các bội số nguyên của `D z`; chỉ mở rộng khi số bản sao
nhỏ hơn cận nén `<n^4`. Kiểm tra HK cho độ kết nối ít nhất `2D`, nên packing
ban đầu có `D` cây. Hệ số chiếu cận tải về `z` là `D`. Nếu bội số quá lớn,
tiếp tục dùng phép nén Mục 6 với hệ số chiếu `n^2`, tránh cấp phát theo giá
trị của số nguyên đầu vào.

Các vòng vẫn tìm shortcut Laplacian, khung, dấu và kiểm tra PSD, packing như
bản thực nghiệm trước. Padding ký dấu có thể biểu diễn ngầm: mọi cột trong
một phân rã PSD có chuẩn bình phương không vượt trace của phần bù. Các dấu
padding triệt tiêu theo cặp bất kể phân rã. Dùng cận trace được tính chính
xác, thay cho mở rộng toàn bộ phân rã hữu tỉ. Nếu cận Frobenius đã chứng minh
chuẩn ký dấu đạt ngưỡng, không lặp lại hai phép kiểm tra PSD trên cùng ma
trận ký dấu. Bất đẳng thức PSD của đồ thị giữ lại vẫn được kiểm tra độc lập.

`round-supported-tree` là đường C++ không liệt kê lát cắt. Nó kiểm tra HK
bằng min-cut nguyên, kiểm tra cây bao và support dương, rồi xác nhận cận

`beta <= min(D,(n-1)/2)`.

Cận này hợp lệ với mọi cây có hỗ trợ: mỗi lát cắt HK đối xứng có tải ít nhất
2, cây đi qua tối đa `n-1` cạnh; đồng thời mỗi cạnh cây có bội số nguyên dương
trong `D z`. Chỉ nhận beta được cung cấp không nhỏ hơn cận đã xác nhận ấy.
AKS tính capacity bằng số nguyên chính xác. Đường C++ này không gọi DP tính
tối ưu tour, kể cả khi đầu vào nhỏ.

Cận từ chuỗi PSD vẫn được ghi riêng. AKS hiện dùng cận support được C++ xác
nhận độc lập; đây có thể là cận lỏng hơn chuỗi PSD và không phải bảo đảm
hằng số độc lập đầu vào. Bản này tiếp tục là triển khai thực nghiệm có kiểm
chứng, chưa hoàn tất thuật toán strong thin tree tổng quát trong bản thảo.

## Chạy lại

```bash
g++ -std=c++20 -O2 -Iinclude src/main.cpp -o /tmp/kltn-batsp
python3 benchmarks/bench_scalable_tree.py --batsp /tmp/kltn-batsp --sizes 20 32
python3 scripts/experimental_tree.py --verify results/scalable_tree/mixture20.json
```

Seed `20261012`; mỗi đồ thị là tổ hợp đều của bốn chu trình Hamilton có
hướng. Đầu vào HK có mẫu số 4. Campaign lưu JSON và bảng CSV trong
`results/scalable_tree/`, không chạy bộ vét cạn, không đo độ mỏng chính xác,
và không ghi tối ưu tour chưa biết. Đồ thị metric được tạo bằng khoảng cách
có hướng từ các cung giá 1; bottleneck tour được đo trực tiếp.

Đối chứng nhỏ được bật rõ ràng bằng `--exact-small` hoặc script
`bench_experimental_tree.py`. Giới hạn 16 đỉnh chỉ thuộc phép đo mọi lát cắt;
bộ dựng và bộ kiểm tra chứng chỉ mặc định đã bỏ giới hạn này. Số học hữu tỉ,
packing tường minh và các giới hạn bước vẫn có thể gây chậm hoặc dừng sớm.

## Kết quả đã chạy

| Mẫu | Cạnh đầu vào → sau làm thưa | Vòng | Cây cuối | Cận beta dùng cho AKS | Bottleneck tour | Thời gian tổng |
|---|---:|---:|---:|---:|---:|---:|
| mixture20 | 80 → 38 | 1 | 19 cạnh | 4 | 3 | 5.607 s |
| mixture32 | 128 → 62 | 1 | 31 cạnh | 4 | 4 | 38.604 s |

Cả hai dừng ở packing 2 cây và qua kiểm tra chứng chỉ. Số cạnh nén Mục 6
tương ứng là 8000 và 32768; dùng bội số ban đầu đã rút gọn tránh mở rộng
những đồ thị lớn hơn này. `tree_cuts_exact=0` và
`tree_bound=universal_support` trong đầu ra C++ xác nhận đường kiểm tra được
chọn. Không có số liệu tối ưu tour để suy ra tỉ lệ ALG/OPT cho hai mẫu này.
Thời gian là một lần đo, bao gồm xác minh và AKS; không phải thống kê hiệu
năng hay chứng minh giới hạn thời gian.

## Kiểm chứng

54 phép thử Python và bộ thử C++ đã qua. Phép thử mới thay oracle lát cắt bằng
hàm luôn báo lỗi, sau đó chạy cả dựng và xác minh ở chế độ mặc định để bảo
đảm không gọi vét cạn. Có phép thử 20 đỉnh vượt giới hạn cũ, phát hiện sửa
cận AKS và từ chối gọi đối chứng vét cạn trong chế độ mặc định. Bộ thử C++
kiểm tra cây 20 đỉnh và từ chối một cận nhỏ hơn cận support được xác nhận.
