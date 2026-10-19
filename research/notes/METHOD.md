# Thuật toán đã hiện thực và lập luận đúng đắn

Xét Minimum Hitting Set không trọng số với tập đỉnh V và các hyperedge E.
Ở dạng đối ngẫu Set Cover, mỗi đỉnh v có cột C(v) là các hyperedge chứa v.
Tại một nút tìm kiếm, R là các hyperedge chưa được hit, A là các đỉnh còn
được xét trong nhánh chính và k là số đỉnh được phép chọn thêm.

## Kernel hoàn tất với hai đỉnh

Ở đây “kernel” chỉ một thủ tục tính toán ở cuối nhánh, không phải một
kernelization theo nghĩa lý thuyết FPT. Tên đề tài nên dùng “thủ tục hoàn
tất hai đỉnh” để tránh nhập nhằng.

Chọn một hyperedge e trong R có ít đỉnh nhất. Một nghiệm hoàn tất gồm nhiều
nhất hai đỉnh phải chứa ít nhất một đỉnh v trong e. Với mỗi v, đặt

    R_v = R \ C(v)
    P_v = giao của tất cả các hyperedge f thuộc R_v.

Nếu R_v rỗng, v đủ để hoàn tất. Nếu P_v không rỗng, lấy bất kỳ w trong P_v;
{v,w} hoàn tất nghiệm. Nếu không có v nào đạt một trong hai điều kiện,
không tồn tại nghiệm hoàn tất kích thước ≤2. Đây là kiểm tra chính xác,
không phải heuristic hay điều kiện đủ một chiều.

Hai biểu diễn bitset cùng được dùng: cột C(v) có m bit, còn hyperedge f có
n bit. Do đó phép trừ R\C(v) và phép giao P_v đều thực hiện trên các từ máy.
Giao dừng ngay khi rỗng; không cần tính toàn bộ giao. Bản được chọn không
sắp xếp lại các cột/hyperedge trong từng lần gọi kernel, vì chi phí này đã
làm bản đầu chậm đáng kể.

Một lần gọi có cận trên
O(|e| (ceil(m/w) + |R| ceil(n/w))) phép toán từ máy; bộ nhớ hai ma trận
incidence là O(n ceil(m/w) + m ceil(n/w)) từ. Khi giao rỗng sớm, số hyperedge
thực sự được duyệt thường nhỏ hơn |R|. Không suy diễn từ đây một cải thiện
độ phức tạp tiệm cận cho Hitting Set tổng quát.

## Vì sao kernel có thể bỏ qua tập loại trừ A?

Kernel kiểm tra hai đỉnh trên toàn bộ V, kể cả các đỉnh đã bị loại trong
nhánh đang xét. Nếu tìm được một cặp, ghép với nghiệm bộ phận tạo ra một
nghiệm hợp lệ của bài toán ban đầu. Một đỉnh đã được chọn trước đó không
thể hit hyperedge còn trong R, nên không tạo ra đỉnh trùng có ích.

Nếu kernel trả lời không, không có cặp nào ngay cả trên V, vì vậy cũng
không có cặp trên A. Kết quả âm tính có thể cắt nhánh an toàn. Kết quả dương
tính có thể trùng với một nhánh khác, nhưng không thể tạo nghiệm sai.
Đây là sự nới lỏng có kiểm soát phạm vi nhánh, không phải bỏ điều kiện khả thi.

## Tìm kiếm khi k>2

1. Tính gain(v)=|C(v)∩R| với v∈A. Nếu tổng k gain lớn nhất nhỏ hơn |R|,
   không k cột nào phủ được R; cắt nhánh.
2. Chọn một hyperedge chưa hit có ít đỉnh còn trong A nhất. Nếu không có
   đỉnh nào, nhánh vô nghiệm.
3. Xét các đỉnh của hyperedge đó theo gain giảm dần. Với mỗi v, chọn v,
   xóa C(v) khỏi R và đệ quy với k-1. Sau khi xử lý v, loại v khỏi các
   nhánh sau để tránh lặp cách chọn đỉnh đầu tiên của hyperedge này.
4. Khi k=1, kiểm tra giao tất cả hyperedge còn lại. Khi k=2, gọi kernel trên.

Mọi nghiệm phải hit hyperedge được chọn ở bước 2. Phân nhánh ở bước 3 phủ
đủ các khả năng. Cận tổng gain là điều kiện cần. Hai trường hợp kết thúc
đều chính xác, nên thủ tục quyết định đúng. Tăng k từ 1 đến dưới cận trên
greedy; nghiệm đầu tiên tìm được là tối ưu. Nếu không có nghiệm nhỏ hơn
greedy, chính nghiệm greedy đã được chứng minh tối ưu.

## Solver kết hợp

`scripts/solve.py` thử kernel tìm kiếm cho n,m≤512 và mật độ incidence≥1/16,
với ngân sách mặc định 10 giây. Đây là giới hạn kỹ thuật của bản hiện thực,
không phải điều kiện toán học của bài toán. Nếu không hoàn thành, gọi UzL
nguyên gốc. Đối với các instance khác, gọi thẳng UzL.

Timeout luôn có nghĩa là **chưa kết luận**, không bao giờ được dùng như
chứng minh vô nghiệm. Solver kết hợp chỉ xuất nghiệm khi một thuật toán
chính xác hoàn thành. So với chạy UzL một mình, chi phí thêm trên instance
không giải được bằng bộ tìm kiếm dense được chặn bởi ngân sách probe cộng
chi phí đọc/chuyển tiếp dữ liệu. Không có bảo đảm tăng tốc trên mọi instance.

## Biến thể đã thử và không chọn

- Pair-packing contraction sang MaxSAT: phép biến đổi bảo toàn tối ưu,
  nhưng pilot không tốt hơn encoding gốc trên tập đã thử. Không dùng.
- Học các tập hyperedge không thể hit bằng hai đỉnh: các witness an toàn
  nhưng chi phí xây dựng và tra cứu cao; kết quả pilot kém hơn bản không học.
  Mã thử còn trong `scripts/dense.cpp --learn` để kiểm tra lại kết luận.
- `--no-pair` giữ khung tìm kiếm nhưng loại kernel hai đỉnh, dùng để đo
  phần cải thiện đến từ kernel, thay vì quy toàn bộ tốc độ cho bitset.

## Ranh giới đóng góp

Branch-and-bound, bitset, cận tổng degree/gain, rút gọn domination, và
portfolio đều là kỹ thuật đã biết. Không tuyên bố phát minh các kỹ thuật này.
Đối tượng nghiên cứu cụ thể là kernel hoàn tất nghiệm trên incidence kép,
cách tích hợp nó vào tìm kiếm chính xác và vùng instance mà nó bổ sung
được cho các solver đã công bố. Tính mới ở mức một paper cần được đánh giá
với related work và phản biện chuyên ngành; không thể chứng minh chỉ bằng
một kết quả tìm kiếm web.
