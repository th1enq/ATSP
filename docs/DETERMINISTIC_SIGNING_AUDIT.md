# Nhánh ký dấu xác định và phạm vi bảo đảm

**Ngày:** 2026-10-09. Nguồn đích là [Appendix A và Lemma 5.2 của bản thảo strong thin tree](https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf).

## Thuật toán đã cài

`scripts/deterministic_signing.py` xử lý các cột hữu tỉ `v_i` bằng quy tắc xác định. Đặt `H_i=v_i v_i^T`, `S_0=0`; ở bước `i`, chọn dấu làm cho `sigma_i (v_i^T S_{i-1} v_i) <= 0`. Mọi phép tính là hữu tỉ. Do đó

`||S_i||_F^2 = ||S_{i-1}||_F^2 + ||v_i||^4 + 2 sigma_i v_i^T S_{i-1} v_i <= ||S_{i-1}||_F^2 + ||v_i||^4`.

Đầu ra có `||S_N||_op^2 <= ||S_N||_F^2 <= B := sum_i ||v_i||^4`. Hàm kiểm tra thêm hai bất đẳng thức PSD `T I ± S_N >= 0` chính xác, với `T=2^15 d_0` và `d_0` là lũy thừa hai nhỏ nhất thỏa `d_0^2 >= Delta`, `Delta=max_i ||v_i||^2`. Nếu kiểm tra thất bại, hàm báo lỗi và không trả dấu không được chứng nhận.

Với padding của Lemma 5.2, `sign_stacked_data` không mở rộng `4r^2` bản sao cho mỗi cột phần bù. Trong từng nửa có cùng dấu `tau`, số bản sao là `2r^2`, luôn chẵn. Gán dấu `sigma` luân phiên `+1,-1` trong mỗi nửa. Khi đó cả `sum sigma` lẫn `sum sigma*tau` bằng không; toàn bộ ma trận ký dấu của padding triệt tiêu chính xác. Chỉ cần ký dấu các cột dữ liệu và kiểm tra PSD trên khối của chúng. Phân rã phần bù `I-Sigma` vẫn được kiểm tra bằng số hữu tỉ.

`automatic_sparsification_step` nối trọng số khung, cột xếp chồng, ký dấu này, phép kiểm tra phổ và packing cây. Nó trả kết quả chỉ khi mọi bất biến cuối cùng qua kiểm tra chính xác.

## Nhánh Appendix A

`appendix_a_potential.py` chuẩn hóa ma trận hạng một thực đối xứng (kể cả ma trận âm), tìm khoảng phổ của `sum A_i^2` bằng phép thử PSD hữu tỉ, rồi chọn `nu`, `epsilon`, `lambda`, `sigma` hữu tỉ theo A.1. Căn bậc ba của `1-x_i^2` được bao bởi hai số nhị phân. `appendix_a_value_oracle.py` tạo hai LMI Schur và bốn ràng buộc hộp, tách siêu phẳng bằng véc tơ PSD âm hữu tỉ, và dùng ellipsoid để trả một khoảng chứa giá trị SDP cùng nghiệm trên khả thi chính xác. Lập luận bán kính trong của A.3 là cơ sở cho cận dưới của khoảng; mã không tạo chứng chỉ đối ngẫu SDP độc lập.

`appendix_a_signing.py` cài lịch A.4: đóng băng tọa độ gần đầu mút, thử cả hai đầu mút, lấy sai phân hữu tỉ, thử bước gradient, tìm véc tơ cong âm bằng loại trừ PSD chính xác, làm tròn hướng về lưới nhị phân, và chọn ứng viên có giá trị thế năng nhỏ nhất. Các hằng số `C0`, `M`, `a`, `s`, `h`, `rho` theo đúng công thức phụ lục. Đầu ra chỉ được trả sau khi kiểm tra PSD chính xác `1600 D^2 nu_lower I - (sum sigma_i H_i)^2 >= 0`; ở đây `nu_lower <= ||sum A_i^2||`, nên chứng chỉ kéo theo cận 40 của Theorem A.1 cho dữ liệu thực đối xứng.

`sign_stacked_data_appendix_a` dùng nhánh này cho các cột dữ liệu, gán dấu triệt tiêu padding như trên, rồi kiểm tra lại ngưỡng của Lemma 5.2. `automatic_sparsification_step(..., signing_method="appendix_a")` nối nó vào một bước làm thưa. Nhánh Frobenius vẫn là mặc định vì các cận hữu tỉ của A.3–A.4 dẫn tới số bit và thời gian rất lớn ngay cả trên ví dụ nhỏ.

Kiểm thử đã đi hết đường ký dấu trên ma trận 1×1, so sánh oracle SDP với nghiệm giải tích `2 sqrt(2)`, và thử riêng công thức sai phân cùng phép làm tròn hướng cong âm. Chưa có kiểm thử chạy hết vòng giảm thế năng qua nhánh cong âm với oracle SDP thật, hay kiểm chứng độc lập các cận đạo hàm, bán kính trong, và định lý covariance được viện dẫn trong nguồn. Vì vậy mã thể hiện thuật toán phụ lục và kiểm tra chứng chỉ đầu ra, nhưng chưa đủ bằng chứng thực nghiệm để khẳng định backend chạy được trên miền tham số lớn của khóa luận.

## Giới hạn của nhánh Frobenius

Nếu `Sigma_data <= I` trong chiều `d`, thì `B <= Delta tr(Sigma_data) <= d Delta`. Vì `T^2 >= 2^30 Delta`, nhánh tham lam **chắc chắn** đạt ngưỡng kiểm tra của Lemma 5.2 khi `d <= 2^30`; điều kiện mạnh hơn và được kiểm tra trực tiếp là `B <= T^2`. Khi điều kiện này không đúng, thuật toán vẫn có thể qua kiểm tra PSD, nhưng không có bảo đảm thành công cho mọi đầu vào.

Nhánh Frobenius là lối chạy nhanh có điều kiện kiểm tra được. Nhánh Appendix A mới là đường giảm thế năng theo bản thảo; kiểm thử và kiểm toán độc lập của đường này vẫn còn giới hạn như trên.
