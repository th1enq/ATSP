# Pipeline thực nghiệm nhiều vòng từ Held–Karp đến tour AKS

**Cập nhật tiếp theo:** chế độ mặc định đã bỏ việc liệt kê mọi lát cắt và
đối chứng tối ưu bắt buộc; xem `SCALABLE_PIPELINE_2026-10-11.md`. Chiến dịch
16 mẫu trong báo cáo này giữ nguyên để làm đối chứng nhỏ, tương ứng tùy chọn
`--exact-small` của CLI hiện tại.

Ngày triển khai: 2026-10-11. Nguồn đã đọc trực tiếp từ bản clone `math`, commit
`adc7f1241b42e322a6451854ab7e4b4c146bf78a`:
`preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/build/source/sections/iteration.tex`
và các giao diện extraction, normalization, signing. Không sửa bản clone.

## Đường thực thi mới

`scripts/experimental_tree.py` nhận chứng chỉ HK hữu tỉ. Chương trình kiểm tra
bậc và subtour bằng min-cut nguyên, nén bội số theo Mục 6, rồi mở rộng đồ thị
nén đã có cận `<n^4` cạnh. Packing ban đầu có `floor(n^2/2)` cây; cận kết nối
`n^2` của phép nén bảo đảm packing này tồn tại.

Trong mỗi vòng, thử `X=c L_H` với `c=1,2,3`, chọn `s` là lũy thừa hai nhỏ nhất
có `s^4>=r`, và đặt `Q=r`. Mọi shortcut phải qua oracle phân hoạch cho
`u_e+kappa`, kiểm tra nón shortcut và điều kiện terminal. Đây là cách tìm
shortcut thực nghiệm trên đầu vào cụ thể; không dùng cận bán kính trong để
khẳng định Proposition 3.1 cho mọi đồ thị.

Nếu toàn bộ packing hiện tại nằm trên cạnh điện trở thấp, dùng lại packing
đó làm hợp cây `B`. Nếu không, dùng bộ packing cạnh điện trở thấp hiện có.
Tìm trọng số khung bằng cân bằng các nhóm cạnh song song: phép cập nhật theo
Sherman–Morrison đưa leverage của một nhóm về `count/q`. Trọng số được chuẩn
hóa, làm tròn xuống lưới nhị phân 48 bit và giữ dương. Trước khi dùng khung,
kiểm tra chính xác từng leverage `<= (1+4/r)/q`. Phương pháp này có giới hạn
200 vòng; không khẳng định định lý hội tụ phổ quát cho cách cập nhật mới.

Ký dấu Frobenius trên các cột xếp chồng đã chuẩn hóa. Thử thứ tự theo cặp đỉnh
trước, rồi theo cây nếu cách đầu thất bại; với mỗi cách, kiểm tra cả dấu ban
đầu lẫn dấu đảo toàn bộ. Đảo toàn bộ giữ nguyên chuẩn ma trận ký dấu. API vẫn
hỗ trợ Appendix A, nhưng chiến dịch dưới đây dùng Frobenius.

Với tập cạnh giữ lại `A`, tìm cận sai số nhị phân bằng kiểm tra PSD chính xác:

`L_A <= L_B/2 + epsilon X`.

Sai số có độ phân giải `2^-16` và luôn lấy phía trên được chứng nhận. Vì
`X=c L_H`, mọi lát cắt thỏa tải mới không vượt `1/2+c*epsilon` lần tải cũ.
Sau đó tìm packing bị chặn ở `floor(r/2)` và chỉ nhận vòng khi
`r/4 <= r_next <= r/2`. Kiểm tra lại mọi lát cắt để ghi hệ số tải thực tế,
không dùng số thực trong phép so sánh.

Ngưỡng dừng thực nghiệm mặc định là `r<=2`; chọn cây có độ mỏng tốt nhất trong
packing cuối bằng kiểm tra mọi lát cắt. Đây chỉ là so sánh các cây đã dựng,
không liệt kê tất cả cây bao. Khi bước tiếp theo không được chứng nhận hoặc
chạm giới hạn, trả cây từ packing cuối và ghi lý do dừng. Số vòng tối đa 32.

Chiếu cây về support HK và tính lại độ mỏng chính xác đối với `z=x+x^T`.
Tích các hệ số tải cho hai cận riêng: cận từ PSD và cận từ mọi lát cắt.
Phép nén cho `a(delta S)<=n^2 z(delta S)`, nên nhân tích đó với `n^2` là một
cận hợp lệ cho cây cuối trên instance hiện tại. Các cận này không được gọi
là hằng số xấp xỉ phổ quát.

## Chứng chỉ và kiểm tra độc lập

Mỗi tệp JSON chứa đầu vào HK, chứng chỉ nén, packing ban đầu, ma trận shortcut,
hợp cây, tập cạnh giữ lại, packing tiếp theo, sai số PSD, hệ số tải, lát cắt
cực trị, cây cuối và độ mỏng hữu tỉ. ID cạnh giữ nguyên theo đồ thị nén ban
đầu, tránh nhầm bản sao khi đổi đồ thị giữa các vòng.

`--verify` kiểm tra lại nén, các PSD, điện trở, phân hoạch, cây bao rời cạnh,
mọi lát cắt và phép chiếu cây. Nó không chạy lại bộ tìm khung, ký dấu hay
thuật toán dựng packing. Chứng chỉ xác nhận tập cạnh đầu ra đủ các bất biến;
không cần tin vào cách bộ dựng đã tìm tập cạnh đó.

`round-supplied-tree HK_FILE TREE_FILE` ở C++ kiểm tra HK bằng min-cut nguyên,
support của cây, chu trình, và mọi bất đẳng thức độ mỏng trước khi chạy AKS.
TREE_FILE gồm `n beta_num beta_den edge_count`, sau đó là các cặp `u v`.
So sánh phân số dùng thuật toán Euclid thay vì tích chéo có nguy cơ tràn.
Python rút gọn mẫu số chung trước khi chuyển sang C++; các số nguyên còn lại
phải nằm trong miền số học 64 bit được giao diện C++ chấp nhận.

## Chạy lại

```bash
# Build bằng CMake nếu môi trường có Make/Ninja.
cmake -S . -B build-local -DCMAKE_BUILD_TYPE=Release
cmake --build build-local -j2
ctest --test-dir build-local --output-on-failure

# Hoặc biên dịch trực tiếp khi không có Make/Ninja.
g++ -std=c++20 -O2 -Iinclude src/main.cpp -o /tmp/kltn-batsp
g++ -std=c++20 -O2 -Iinclude tests/test_core.cpp -o /tmp/kltn-test-core
/tmp/kltn-test-core
python3 -m unittest discover -s tests -p 'test_*.py'

python3 scripts/experimental_tree.py instances/regression/witness6_hk.txt \
  --exact-small --batsp /tmp/kltn-batsp --output /tmp/witness6_tree.json
python3 scripts/experimental_tree.py --verify /tmp/witness6_tree.json
python3 benchmarks/bench_experimental_tree.py --batsp /tmp/kltn-batsp
```

Seed chiến dịch: `20261011`. Có 16 instance: witness6, họ tách đỉnh split7,
chu trình và đồ thị có hướng đầy đủ `n=3..6`, cùng hai tổ hợp lồi của bốn
chu trình Hamilton cho mỗi `n=4..6`. Mỗi mẫu được đối chiếu với baseline
đa thức và bộ dựng cây tối ưu vét cạn C++; tối ưu cây ứng với chính nghiệm HK
được cung cấp. Metric dùng cho đánh giá tour là bao đóng khoảng cách có hướng
của đồ thị đầu vào, không phải bộ metric ngẫu nhiên trong chiến dịch cũ.

Dữ liệu ở `results/experimental_tree/summary.csv` và 16 tệp JSON cùng thư mục.
`construction_seconds` là thời gian dựng cây; `seconds` gồm cả xác minh và
đối chiếu AKS/baseline/vét cạn. Mỗi cấu hình đo một lần, không phải thống kê
hiệu năng. `--reuse` xác minh và dùng lại chứng chỉ đã lưu để đối chiếu C++;
trong chế độ đó `seconds` không chứa thời gian dựng lại cây.

## Kết quả chiến dịch đã chạy

Tất cả 16 mẫu hoàn tất, tổng cộng 40 vòng làm thưa được chứng nhận. Có 12 mẫu
dừng ở ngưỡng packing `r=2`, bốn mẫu đạt `r=1`; không có mẫu dừng vì thiếu
chứng chỉ trong chiến dịch cuối. Cây trả về luôn có đúng `n-1` cạnh, kể cả
khi đồ thị làm thưa cuối còn nhiều cạnh hơn một cây.

| Mẫu | Cạnh nén → cạnh sau làm thưa | Vòng | Độ mỏng cây cuối | Độ mỏng tối ưu vét cạn | Bottleneck / tối ưu |
|---|---:|---:|---:|---:|---:|
| witness6 | 216 → 10 | 3 | 3/2 | 4/3 | 2 / 2 |
| split7 | 339 → 9 | 4 | 2 | 4/3 | 2 / 2 |
| complete4 | 60 → 6 | 2 | 3/2 | 9/8 | 1 / 1 |
| complete6 | 210 → 10 | 3 | 3/2 | 25/18 | 1 / 1 |
| mixture4_0 | 64 → 6 | 2 | 1 | 1 | 2 / 1 |
| mixture6_1 | 213 → 10 | 3 | 2 | 6/5 | 2 / 1 |

Witness6 có lịch `(r,m)`: `(18,216) → (9,45) → (4,22) → (2,10)`.
Hai cây cuối mỗi cây có 5 cạnh; cây được chọn có độ mỏng `3/2`. AKS tạo
tour `0 4 1 2 3 5 0`, bottleneck 2 bằng tối ưu. Cận power AKS của cây này là
11; không suy ra power tối ưu 2 từ cận 11.

Trong cả chiến dịch, `14/16` tour đạt bottleneck tối ưu của instance, tỉ lệ
lớn nhất quan sát được là 2. Có `7/16` cây đạt độ mỏng tối ưu cho nghiệm HK
đã cung cấp. Độ mỏng đo nằm trong `[1,2]`. Các số này chỉ mô tả 16 instance,
không phải định lý xấp xỉ 2 hay hằng số mỏng 2 cho mọi đồ thị.

Thời gian dựng cây đo một lần nằm trong khoảng 0.035–65.437 giây; tổng
149.380 giây. Thời gian cao nhất thuộc `mixture6_0`, cho thấy chi phí số học
hữu tỉ phụ thuộc cấu trúc đồ thị và trọng số, không chỉ số đỉnh. Môi trường
Python 3.13.12; C++ biên dịch bằng `g++ -std=c++20 -O2`.

Kiểm chứng sau triển khai: 52 phép thử Python đều qua; bộ thử lõi C++ qua,
bao gồm từ chối cây có chu trình, độ mỏng khai thấp, chứng chỉ HK sai và
kiểm tra số học mẫu số lớn. Phép thử Python mới kiểm tra nhiều vòng, phát
hiện sửa chứng chỉ, đối chiếu leverage chính xác và mẫu số hơn 4096 bit.
Đường Python → C++ cũng đã chạy trên chứng chỉ có mẫu số 4096 bit sau khi
rút gọn, với tour có bottleneck 1 bằng tối ưu.

## Phạm vi

Hai bộ kiểm tra mọi lát cắt giới hạn `2<=n<=16`; chiến dịch đã đo `n=3..7`.
Việc liệt kê lát cắt là lũy thừa theo `n`. Shortcut Laplacian, cân bằng khung
và Frobenius là các lựa chọn thực nghiệm có kiểm tra đầu ra; chưa bảo đảm
chúng thành công cho mọi input. Bản thực nghiệm này hoàn thiện việc nối và
kiểm chứng nhiều vòng trên mẫu nhỏ, không hoàn tất kiểm toán các bổ đề sâu
hay tái hiện toàn bộ thuật toán đa thức với hằng số phổ quát của Theorem 1.1.
